import pdb
import shutil

import CommonUtil

import threading

import os
import re

# 功能：清除未使用的图片

# 方案原理：
# 通过对图片名称(xxx.imageset)在项目内进行搜索，如果未匹配到字符串，则认为是未使用的图片
# 执行步骤：
# 1、调用[find_unused_images_at_path]生成处理扫描结果并保存到[initUnusedImageInfo]文件中。
# 2、调用[doubleCheckUnusedImage]，排除一些被误报的情况。
# 3、执行删除操作。


# 忽略的图片名称正则数组
ignores = {}

initUnusedImageInfo = "unused_images.txt"
finalUnusedImageInfo = "unused_images_filter.txt"
root_path = "/XXXX/Project" #换成项目路径

def find_unused_images_at_path(root):
    xcassets = []
    CommonUtil.find_xcassets(root, xcassets)
    print("xcassets个数: %d" % len(xcassets))
    allimages = []
    for xcasset in xcassets:
        images = CommonUtil.getAllImageAssets(xcasset)
        allimages += images
    n = 4  # thread count
    resultList = []  # 总结果
    imageCount = len(allimages)
    print("所有imageset的数量: %d" % imageCount)
    step = int(imageCount / n) + 1
    threads = []
    for i in range(0, imageCount, step):
        unused_list_segment = []  # 分段结果
        resultList.append(unused_list_segment)
        t = threading.Thread(target=find_unused_images, args=(allimages[i:i + step], unused_list_segment))
        threads.append(t)
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()

    unused_images = []
    for list in resultList:
        unused_images.extend(list)
    text_path = initUnusedImageInfo
    text = '\n'.join(sorted(unused_images))
    os.system('echo "%s" > %s' % (text, text_path))
    print("unused image count: %d" % len(unused_images))

# 使用ag搜索工具进行字符串匹配搜索，为了提高查询速度，只对.m和.swift文件进行搜索。
def find_unused_images(images, resultList):
    image_names = [os.path.basename(image)[:-len(".imageset")] for image in images]
    count = len(images)
    print("当前分段图片的数量:%d" % count)
    for i in range(0, count):
        print("当前进度: %d / %d " % (i, count))
        image_name = image_names[i]
        if is_ignore(image_name):
            continue
        used = True
        findFileName = ""
        for searchCommand in CommonUtil.allsearchCommand:
            used = True
            command = (searchCommand % (image_name, root_path))
            searchResultFile = os.popen(command)
            findFileName = searchResultFile.readline()
            if findFileName == '':
                used = False
            else:
                break
        if not used:
            resultList.append(images[i])
            print("搜索到未使用图片:" + findFileName + ",imageset: " + image_name)

# 判断图片是否属于忽略的图片，譬如一些通过字符串拼接的图片，或者是服务端动态下发图片名称的图片
def is_ignore(image_name):
    for ignore in ignores:
        if re.match(ignore, image_name):
            return True
    return False

# 因为初步搜索只匹配了.m和.swift文件，所以需要针对初步生成的未使用图片列表，再次进行确认。有可能图片被使用在plist中或者datastore中。
def doubleCheckUnusedImage(unusedImagesFileName):
    f = open(unusedImagesFileName, 'r')
    content = f.readline()
    originalCount = 1
    filterResult = []
    while content:
        originalCount += 1
        imgsetName = content.split('/')[-1].split('.')[0]
        command = ("ag -l %s  %s" % (imgsetName, root_path))
        searchResultFile = os.popen(command)
        result = searchResultFile.readline()
        used = False
        if result != '':
            while result:
                fileName = result.split('/')[-1].strip()
                if fileName != "Contents.json".strip():
                    #      图片本身的imageset中的contents.json文件
                    used = True
                    print("被引用的图片: %s, 查询的结果： %s" % (imgsetName, fileName))
                result = searchResultFile.readline()
        else:
            used = False
        if not used:
            filterResult.append(content)
            print(imgsetName)
        content = f.readline()
    f.close()
    text = '\n'.join(sorted(filterResult))
    os.system('echo "%s" > %s' % (text, finalUnusedImageInfo))
    print("原始个数: %d,过滤后的个数： %d" % (originalCount, len(filterResult)))


def removeUnUsedImage(filename):
    f = open(filename, 'r')
    imagePath = f.readline()
    removeCount = 0
    while imagePath:
        imagePath = imagePath.strip()
        if os.path.exists(imagePath):
            shutil.rmtree(imagePath)
            print("删除Image成功: %s" % imagePath)
            removeCount += 1
        imagePath = f.readline()
    f.close()
    print("清理结束，总共删除图片数量: %d" % removeCount)



if __name__ == '__main__':
    print("执行无用图片检查和清理工作")
    CommonUtil.enviroment_check()
    # find_unused_images_at_path(root_path)
    # doubleCheckUnusedImage(unusedImagesFileName=initUnusedImageInfo)
    # removeUnUsedImage(finalUnusedImageInfo)