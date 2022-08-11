

import os

import CommonUtil

# 有损压缩项目内图片


# 方案原理：使用imageOptim工具工具针对项目的所用png jpg jpeg gif图片进行压缩。压缩方式为有损压缩，质量建议选择为80%，这种损失率的情况下，肉眼基本看不出区别，图片大小压缩率为50%~60%
# 执行步骤：
# 1、安装imageOptim（https://github.com/ImageOptim/ImageOptim）和imageOpCli（https://github.com/JamieMason/ImageOptim-CLI）。
# 2、打开imageOptim的设置页面，选择"启用有损压缩"，质量调整为80
# 2、直接调用命令行压缩工具接口。
rootPath = "/XXX/iOSProject"

def doCompressOperationForXCAssets(xcassetPath):
    imageOptimCommand = "imageoptim %s" % xcassetPath
    os.system(imageOptimCommand)


if __name__ == '__main__':
    oldsize = CommonUtil.calAllImageSize(rootPath)
    doCompressOperationForXCAssets(rootPath)
    newsize = CommonUtil.calAllImageSize(rootPath)
    print("压缩前图片的总大小 {} kb".format(oldsize / 1e3))
    print("压缩后图片的总大小 {} kb".format(newsize / 1e3))
    print("压缩率 {} ".format( (newsize) / oldsize))