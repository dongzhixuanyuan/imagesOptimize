import os
import json
import shutil
import pdb
from itertools import combinations
from json import JSONDecoder
import CommonUtil

# 功能：
# 过滤出项目内的相似图片；
# 删除相似的图片，并更新代码中的图片引用。

# 方案原理：
# 对项目内的所有图片两两组合，计算出相似度（https://cloud.tencent.com/developer/article/1096158）（项目中做了一些边界情况处理和优化，降低误报的概率），如果相似度大于阈值，则认为是相似图片，并将相似文件的信息来填充特定的数据模型中。使用这个
# 数据模型来做后续的重复图片处理工作，可能是删除或者是替换。
# 执行步骤：
# 1、读取相似图片信息，并保存到文件中。生成的位置为脚本执行目录，目录名[resultFilePath]的值。
# 2、人工确认过滤第一步中生成的结果，因为相似图片的检测可能出现误报，需要人工剔除。
# 3、针对过滤后的结果，进行删除替换操作。至于删除替换的方式，需要根据项目实际情况进行定制（脚本中默认是进行图片名称替换）。如果图片属于不同的Pod，那么不同Pod如何访问公用图片，就看各个项目的实现方式了。
import img_similarity_calculate

resultFilePath = "similarImagesDir"  # 过滤出的相似图片的信息的存储目录
root_path = "/XXX/iOSProject"  # 工程项目所在目录,请替换为你的工程目录


# 相似图片的缓存信息的数据格式。
class ImageSetInfo:

    def __init__(self):
        self.dirName = ""
        self.sampeImagesetPath = ""
        self.pictures = set()

    def to_json(self, imageInfo):
        return {
            "dirName": imageInfo.dirName,
            "sampeImagesetPath": imageInfo.sampeImagesetPath,
            "pictures": json.dumps(list(imageInfo.pictures), ensure_ascii=False)
        }

    def from_json(json_object):
        info = ImageSetInfo()
        info.dirName = json_object['dirName']
        info.sampeImagesetPath = json_object['sampeImagesetPath']
        info.pictures = json.loads(json_object['pictures'])
        return info


# 相同图片替换处理-前端(过滤项目内的相同图片，并保存信息)

similarImageHashAndStorePathMap = {}
similarImageStoreInfoList = []


def filterTheSameImageAndStoreInfo():
    if os.path.exists(resultFilePath):
        shutil.rmtree(resultFilePath)

    # 路径样式1（imageset目录）:  ~/XXXX.xcassets/yyyy.imageset
    # 路径样式2（png图片的全路径样式）: ~/XXXX.xcassets/yyyy.imageset/zzzz@2x-1.png
    allImagesets = []  # imageset目录，其元素格式为[路径样式1]

    assetsList = []
    CommonUtil.find_xcassets(root_path, assetsList)
    for xcassets in assetsList:
        allImagesets += CommonUtil.getAllImageAssets(xcassets)

    imageNameAndPathMap = {}  # map：key为路径样式1，value为路径样式2
    for imageset in allImagesets:
        images = os.walk(imageset)
        for path, dir_list, file_list in images:
            list2x = list(filter(lambda x: "@2x.png" in x, file_list))
            if len(list2x) > 0:
                imageNameAndPathMap[path] = os.path.join(path, list2x[0])
            else:
                pngList = list(filter(lambda x: x.endswith(".png"), file_list))
                if len(pngList) > 0:
                    imageNameAndPathMap[path] = os.path.join(path, pngList[0])

    resultList = imageNameAndPathMap.items()
    combinationList = list(combinations(resultList, 2))  # 转化为两两的排列组合
    hitCount = 0
    for item in combinationList:
        img1 = item[0][1]
        img2 = item[1][1]
        if img_similarity_calculate.calculate2ImageDiff(img1, img2):
            generateSameImageInfo(img1, img2)
            hitCount += 1

    writeImageInfoFile()

    print("统计到相似图片数量为:%d" % hitCount)


# 将匹配到的相似图片复制到结果目录中，用于后续人工确认。
def generateSameImageInfo(img1_path, img2_path):
    # 1、map保存图片路径的hash已经对应的存储目录
    # 2、当检测到相似图片时，分别通过2张图片路径的hash从map获取是否存在存储目录，如果存在目录的话，则需要将图片放在已存在目录下，如果不存在则创建目录
    # 3、创建目录时，构建imageSetInfo对象，并放到一个List中，每当向目录中添加图片时，需要更新info对象的pictures字段
    # 4、遍历完毕后，将info的List内容，根据prefix写入到各个相似图片的目录下。供后续处理使用。
    resultFolder = os.path.exists(resultFilePath)
    if not resultFolder:
        os.makedirs(resultFilePath)

    img1_hash = hash(img1_path)
    img2_hash = hash(img2_path)
    subDir1 = similarImageHashAndStorePathMap.get(img1_hash)
    subDir2 = similarImageHashAndStorePathMap.get(img2_hash)
    subDir = subDir1 if subDir1 != None else (subDir2 if subDir2 != None else None)
    if subDir == None:
        subDir = ""
        pathDivisionList = img1_path.split('/')
        sampleImagesetPath = img1_path[0:(len(img1_path) - len(pathDivisionList[-1]) - 1)]

        for unit in pathDivisionList:
            if unit.endswith(".imageset"):
                subDir = unit.split('.')[0]
                similarImageHashAndStorePathMap[img1_hash] = subDir
                similarImageHashAndStorePathMap[img2_hash] = subDir
                storeImageInfo = ImageSetInfo()
                storeImageInfo.dirName = subDir
                storeImageInfo.sampeImagesetPath = sampleImagesetPath
                storeImageInfo.pictures.add(img1_path)
                storeImageInfo.pictures.add(img2_path)
                similarImageStoreInfoList.append(storeImageInfo)
    else:
        for item in similarImageStoreInfoList:
            if item.dirName == subDir:
                storeImageInfo = item
                storeImageInfo.pictures.add(img1_path)
                storeImageInfo.pictures.add(img2_path)

    imageDir = os.path.join(resultFilePath, subDir)
    if not os.path.exists(imageDir):
        os.makedirs(imageDir)

    print(imageDir)

    destinationImg1 = os.path.join(imageDir, '_'.join(img1_path.split("/")[-5:]))
    destinationImg2 = os.path.join(imageDir, '_'.join(img2_path.split("/")[-5:]))
    shutil.copyfile(img1_path, destinationImg1)
    shutil.copyfile(img2_path, destinationImg2)

    print("[img1:%s,\nimg2:%s ]" % (img1_path, img2_path))


# 将最终的相似图片信息写入到json文件中，用于后端处理。
def writeImageInfoFile():
    similarImageDir = os.walk(resultFilePath)
    for path, dir_list, file_list in similarImageDir:
        for dir in dir_list:  # 遍历目录，找到对应的info
            for similarImageInfo in similarImageStoreInfoList:
                if dir == similarImageInfo.dirName:
                    infoFilePath = os.path.join(path, dir, "image_info.txt")
                    if os.path.exists(infoFilePath):
                        os.remove(infoFilePath)
                    f = open(infoFilePath, "x")
                    data = json.dumps(similarImageInfo, default=similarImageInfo.to_json)
                    f.write(data)
                    f.close()
                    break


# 相同图片替换的处理-后端。执行该函数时，需要直接在命令行执行，不能在IDE中直接点击运行，否则的话，ag搜索命令会失效。

indexWhenReturn = 0  # 当前处理的图片的索引
countOfPatchExcute = 5  # 每次处理的图片数量，前期可以调整为1，处理多个之后，判断是否有意外情况，后续可以调高一点，提高处理效率。

extensions = ['xxxExtension']  # 项目中的Extension

ydCommonResDir = "~/CommonResource/Assets/Media.xcassets"  # 项目内图片公共库路径


def searchAndReplaceImageName():
    g = os.walk(resultFilePath)
    print("当前序号 %d" % indexWhenReturn)
    count = 0
    for path, dir_list, file_list in g:
        for file in file_list:
            if file == "image_info.txt":
                # 控制每次只执行指定数量的图片替换
                count += 1
                if count < indexWhenReturn:
                    continue
                if count >= (indexWhenReturn + countOfPatchExcute):
                    return

                f = open(os.path.join(path, file))
                info = JSONDecoder(object_hook=ImageSetInfo.from_json).decode(f.read())
                #     1、使用samplePath中的.imageset覆盖picture中的跟samplePath不同的imageset
                #     2、根据图片是否属于同一个Pod来选择处理方式。如果图片在同一个Pod里面，那么只需要删除图片即可；如果在不同Pod里面，那么就需要将图片拷贝到公共库中。
                #     3、执行ag搜索命令，列出使用该图片的swift文件或者.m 文件
                #     4、针对步骤3中的文件进行字符串替换。
                if not os.path.exists(info.sampeImagesetPath):
                    print("sampleImagePath不存在.dir: %s , sampleImagePath: %s" % (path, info.sampeImagesetPath))
                    pathSegment = info.sampeImagesetPath.split('/')
                    imageSetName = ""
                    for segment in pathSegment:
                        if segment.endswith(".imageset"):
                            imageSetName = segment
                            break
                    if not os.path.exists(os.path.join(ydCommonResDir, imageSetName)):
                        print("sampleImagePath不存在.dir: %s , sampleImagePath: %s" % (path, info.sampeImagesetPath))
                        continue

                (sampleImgSetDir, sampleImageSetName) = getImageSetDir(info.sampeImagesetPath)
                inSamePod = imageSetInSamePodOrAllInProject(info)
                # print("图片inSamePod: %s \n " % ( "YES" if inSamePod else "NO"))
                #
                # break
                if not inSamePod:
                    # 复制sample到CommonRes
                    try:
                        shutil.move(info.sampeImagesetPath, ydCommonResDir)
                        print("拷贝资源到CommonRes成功： %s" % sampleImageSetName)
                    except:
                        print("拷贝资源到CommonRes失败： %s" % sampleImageSetName)
                for picture in info.pictures:
                    inExtension = checkImageInExtension(picture)
                    if inExtension:
                        continue
                    imgPathSegments: list = picture.split('/')
                    # pictrue为png图片路径，需要先获取其imageset文件夹路径
                    imgSetDir = ""
                    imgSetName = ""
                    for segment in imgPathSegments:
                        if segment != '':
                            imgSetDir += ("/" + segment)
                        if segment.endswith(".imageset"):
                            imgSetName = segment.split('.')[0]
                            break
                    # 步骤1
                    if not inSamePod:
                        # 删除Pod中现有的
                        if os.path.exists(imgSetDir):
                            shutil.rmtree(imgSetDir)
                            print("imageset删除成功")
                    else:
                        if os.path.exists(imgSetDir) and imgSetDir != info.sampeImagesetPath:
                            shutil.rmtree(imgSetDir)
                            print("删除同一个Pod里面的重复图片")
                    # # 步骤2
                    for searchCommand in CommonUtil.allsearchCommand:
                        command = (searchCommand % (imgSetName, root_path))
                        searchResultFile = os.popen(command)
                        findFileName = searchResultFile.readline()
                        while findFileName:
                            print(
                                "搜索到文件:" + findFileName + ",imageset: " + imgSetName + ",sampleImageset: " + sampleImageSetName)
                            # 使用sed命令进行替换 sed -i 's/原字符串/替换字符串/g' filename
                            replaceCommand = " sed -i \"\" 's/\"%s\"/\"%s\"/g' %s" % (
                            imgSetName, sampleImageSetName, findFileName)
                            # 执行该命令时，需要直接在命令行执行脚本，不能在IDE中直接点击运行，否则的话，ag搜索命令会失效，无法搜索出结果。
                            os.system(replaceCommand)
                            print("command: %s" % replaceCommand)
                            if not inSamePod:
                                print("不在同一个Pod，需要修改调用方式")
                            findFileName = searchResultFile.readline()
                            # pdb.set_trace()
                if count >= (indexWhenReturn + countOfPatchExcute):
                    return


#  将图片全路径转化为(imagesetDir,imagesetName)
def getImageSetDir(absolutePath):
    imgPathSegments: list = absolutePath.split('/')
    # pictrue为png图片路径，需要先获取其imageset文件夹路径
    imgSetDir = ""
    imgSetName = ""
    for segment in imgPathSegments:
        if segment != '':
            imgSetDir += ("/" + segment)
        if segment.endswith(".imageset"):
            imgSetName = segment.split('.')[0]
    return (imgSetDir, imgSetName)


#   判断相似图片所属的组件。可能属于不同Pod，也可能属于同一个Pod，也有可能属于Project.
#   只有当这一组相似图片全属于同一个Pod，或者全属于Project时，才返回True;否则返回False.
def imageSetInSamePodOrAllInProject(imageInfo: ImageSetInfo):
    podnamelist = set()
    hasImageInProject = False
    for picAbsolutePath in imageInfo.pictures:
        pathSegments = picAbsolutePath.split('/')
        if "Pods" in pathSegments or "local_pods" in pathSegments or "developing_pods" in pathSegments: #此处代码的作用是获取图片所在的Pod名称，用于判断图片是否属于同一个Pod。根据项目的不同，可能需要修改。
            for index in range(0, len(pathSegments)):
                if pathSegments[index] == "Pods" or pathSegments[index] == "local_pods" or pathSegments[
                    index] == "developing_pods":
                    podnamelist.add(pathSegments[index + 1])
        else:
            hasImageInProject = True

    inSamePod = len(podnamelist) <= 1
    if hasImageInProject:
        if len(podnamelist) > 0:
            print("主工程和Pod中各存在一份 %s" % imageInfo.sampeImagesetPath)
            return False
        else:
            print("全在主工程中： %s", imageInfo.sampeImagesetPath)
            return True
    if inSamePod:
        print("属于相同Pod,dir name : %s" % imageInfo.sampeImagesetPath)
    else:
        print("属于不同Pod,dir name : %s" % imageInfo.sampeImagesetPath)
    return inSamePod


# 判断图片是否在Apple官方的Extension组件中，譬如Today、Action、Share.这些组件中的图片是不需要进行图片复用处理的。
def checkImageInExtension(imagePath: str):
    imgPathSegments: list = imagePath.split('/')
    result = False
    for segment in imgPathSegments:
        for extensionName in extensions:
            if segment == extensionName:
                result = True
                return result
    return result


if __name__ == '__main__':
    print("清理相似图片")
    CommonUtil.enviroment_check()
    # 1、先过滤出相似图片
    # filterTheSameImageAndStoreInfo()
    # 2、打开结果生成目录[resultFilePath],人工确认是否有误报的图片。
    # 3、再进行图片复用处理
    # 建议先调整[indexwhenreturn]和[countofpatchexcute]的值，以便控制执行的次数。在源代码管理软件（SourceTree）中查看当前的文件变化，判断执行是否正确。
    # searchAndReplaceImageName()
