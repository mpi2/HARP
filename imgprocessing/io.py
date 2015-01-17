"""
Copyright 2015 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import scipy.ndimage
import cv2
import sys


def imread(imgpath):
    if sys.platform == "win32" or sys.platform == "win64":
        return _read_cv2(imgpath)
    else:
        return _read_cv2(imgpath)
        return _read_ndimage(imgpath)


def _read_cv2(imgpath):
    return cv2.imread(imgpath, cv2.CV_LOAD_IMAGE_UNCHANGED)


def _read_ndimage(imgpath):
    return scipy.ndimage.imread(imgpath)


def imwrite(imgpath, img):
    cv2.imwrite(imgpath, img)

