import scipy.ndimage
import cv2
import sys


def imread(imgpath):
    if sys.platform == "win32" or sys.platform == "win64":
        return _read_cv2(imgpath)
    else:
        return _read_ndimage(imgpath)


def _read_cv2(imgpath):
    return cv2.imread(imgpath, cv2.CV_LOAD_IMAGE_UNCHANGED)


def _read_ndimage(imgpath):
    return scipy.ndimage.imread(imgpath)


def imwrite(imgpath, img):
    cv2.imwrite(imgpath, img)

