from functools import reduce
import math
from PIL import Image


# 功能：检测2张图片的相似性。

scaleNum = 16

def avhash(im):
    if not isinstance(im, Image.Image):
        # print(im)
        im = Image.open(im)
    im = im.resize((scaleNum, scaleNum), Image.ANTIALIAS).convert('L')
    avg = reduce(lambda x, y: x + y, im.getdata()) / (scaleNum * scaleNum)
    return reduce(lambda x, y_z: x | (y_z[1] << y_z[0]),
                  enumerate(map(lambda i: 0 if i < avg else 1, im.getdata())),
                  0)


def hamming(h1, h2):
    h, d = 0, h1 ^ h2
    while d:
        h += 1
        d &= d - 1
    return h


# img1,img2是图片文件路径
def calculate2ImageDiff(img1, img2):
    img1_path = img1
    img2_path = img2
    img1 = Image.open(img1)
    img2 = Image.open(img2)
    img1_width, img1_height = img1.size
    img2_width, img2_height = img2.size
    img1_wh = img1_width / img1_height
    img2_wh = img2_width / img2_height
    # 图片比例相差超过0.2，直接认定为不同图片
    if abs(img1_wh - img2_wh) > 0.2:
        return False
    # 两张图片宽度差或者高度差超过0.2，认定为不同图片
    if (abs(1 - img1_width / img2_width) > 0.2) or (abs(1 - img1_height / img2_height) > 0.2):
        return False
    h1 = avhash(img1)
    h2 = avhash(img2)

    diff = hamming(h1, h2)
    if diff <= 5:
        #   从图片中取出5个点，比较这5个点的rgb值，如果其中4个点的rgb粗略相等，那么判断通过。
        #   ******

        rgb_img1 = Image.open(img1_path)
        rgb_img2 = Image.open(img2_path)
        # if rgb_img1.mode != rgb_img2.mode:
        #     return  False
        img1_hasAlpha = False
        img2_hasAlpha = False
        img1_has_transparency = rgb_img1.info.get("transparency") is not None
        img2_has_transparency = rgb_img2.info.get("transparency") is not None
        if rgb_img1.mode == "RGBA":
            rgb_img1 = rgb_img1.convert("RGBA")
            img1_hasAlpha = True
        elif (rgb_img1.mode == "RGB" or rgb_img1.mode == "P") and img1_has_transparency:
            rgb_img1 = rgb_img1.convert("RGBA")
            img1_hasAlpha = True
        else:
            rgb_img1 = rgb_img1.convert("RGB")

        if rgb_img2.mode == "RGBA":
            rgb_img2 = rgb_img2.convert("RGBA")
            img2_hasAlpha = True
        elif (rgb_img2.mode == "RGB" or rgb_img2.mode == "P") and img2_has_transparency:
            rgb_img2 = rgb_img2.convert("RGBA")
            img2_hasAlpha = True
        else:
            rgb_img2 = rgb_img2.convert("RGB")

        img1_width, img1_height = rgb_img1.size
        # img2_width,img2_height = rgb_img2.size
        img_width_unit = int(img1_width / 3)
        img_height_unit = int(img1_height / 3)

        point_samples = [(img_width_unit, img_height_unit), (img_width_unit * 2, img_height_unit),
                         (img_width_unit, img_height_unit * 2), (img_width_unit * 2, img_height_unit * 2),
                         (img1_width / 2, img1_height / 2)]
        diff_list = []
        white_or_black = False

        def isWhiteOrBlack(pixelValue):
            return (244 <= pixelValue <= 256) or (0 <= pixelValue <= 12)

        for point in point_samples:
            r1, g1, b1 = calculateAvgRgb(point, rgb_img1, img1_hasAlpha)  # rgb_img1.getpixel((point))
            r2, g2, b2 = calculateAvgRgb(point, rgb_img2, img2_hasAlpha)  # rgb_img2.getpixel((point))
            img1_full_white_black = isWhiteOrBlack(r1) and isWhiteOrBlack(g1) and isWhiteOrBlack(b1)
            img2_full_white_black = isWhiteOrBlack(r2) and isWhiteOrBlack(g2) and isWhiteOrBlack(b2)
            white_or_black = white_or_black and (img1_full_white_black or img2_full_white_black)
            diff_r = abs((r2 - r1) / 256)
            diff_g = abs((g2 - g1) / 256)
            diff_b = abs((b2 - b1) / 256)
            diff = math.sqrt(diff_r * diff_r + diff_g * diff_g + diff_b * diff_b)
            diff_list.append(diff)
        # diff_avg  = reduce(lambda x,y:x+y,diff_list) / (len(diff_list))
        limit = 10 / 128
        exceed_limit_diff = list(filter(lambda x: x > limit, diff_list))
        if len(exceed_limit_diff) > 1:  # 如果有2个点不太相同的话，就认为是不同图片
            return False
        # 如果碰到全白或者全黑的图片，那么必须5个点都完全一致
        if white_or_black:
            if len(exceed_limit_diff) > 0:
                return False
        return True
    return False


# 取某个点周围4个像素的rgb值的平均值
def calculateAvgRgb(point, img, hasAlpha):
    point_x, point_y = point
    img_width, img_height = img.size
    r, g, b = 0, 0, 0
    start_x = int(max(0, point_x - 4))
    end_x = int(min(img_width, point_x + 4))
    start_y = int(max(0, point_y - 4))
    end_y = int(min(img_height, point_y + 4))
    sampleCount = 0
    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            if hasAlpha:
                img_r, img_g, img_b, img_a = img.getpixel((x, y))
            else:
                img_r, img_g, img_b = img.getpixel((x, y))
            r += img_r
            g += img_g
            b += img_b
            sampleCount += 1
    return (r / sampleCount, g / sampleCount, b / sampleCount)
