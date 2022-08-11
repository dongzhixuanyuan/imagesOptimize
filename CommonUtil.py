import os
import re

swiftSearch = ' ag  -l -G ".+\.swift"  %s  %s '
mFileSearch = ' ag -l  -G \".+\.m\"  %s  %s'
allsearchCommand = [swiftSearch, mFileSearch]


def enviroment_check():
    if os.popen("ag --version").read().find('ag version') == -1:
        raise Exception('ag not found,please install ag: https://github.com/ggreer/the_silver_searcher')
    return True


# 获取项目的的所有的xcassets
def find_xcassets(root, resultList: [], needPrint=False):
    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if is_xcassets_dir(item):
            resultList.append(path)
            if needPrint:
                print('[+] %s' % path)
        elif os.path.isdir(path):
            find_xcassets(path, resultList)


def is_xcassets_dir(dir):
    return re.search(r'.xcassets', dir)


# 获取传入的xcassets目录下的所有imageset
# dir:传入的xcassets目录
def getAllImageAssets(dir, need_filter=True):
    result = []
    g = os.walk(dir)
    for path, dir_list, file_list in g:
        for dir_name in dir_list:
            if dir_name.endswith('.imageset'):
                dir_name_withnot_ext = str(dir_name).split(".")[0]
                if need_filter:
                    if not checkStartEndWithNums(dir_name_withnot_ext):
                        result.append(os.path.join(path, dir_name))
                else:
                    result.append(os.path.join(path, dir_name))
    return result


# 匹配以数字开头或结尾的图片名字，排除gif动画，或者动态拼接图片名的情况。可以根据项目情况修改。
def checkStartEndWithNums(imageName):
    matchs = {r'\d+.+', r'.+\d+'}
    for item in matchs:
        if re.match(item, imageName):
            return True
    return False


# 计算当前目录下所有的图片的大小
def calAllImageSize(imageDir):
    total_size = 0
    g = os.walk(imageDir)
    for path, dir_list, file_list in g:
        for file in file_list:
            if file.endswith('.png') or file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.gif'):
                fileAbsolutePath = os.path.join(path, file)
                total_size += calImageSize(fileAbsolutePath)
    return total_size


# 计算图片存储空间大小
def calImageSize(imagePath):
    with open(imagePath, "rb") as f:
        size = len(f.read())
        print("{}图片的大小 {} kb".format(imagePath, size / 1e3))
        return size
