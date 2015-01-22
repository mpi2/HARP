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
import sys
sys.path.append('..')
if sys.platform == "win32" or sys.platform == "win64":
    from lib import cv2
else:
    import cv2
import os
import skimage.io as io

from appdata import HarpDataError


class Imreader():
    def __init__(self, pathlist):
        if sys.platform in ["win32", "win64"]:
            self.reader = self._read_skimage
        elif sys.platform in ["linux", 'linux2', 'linux3']:
            self.reader = self._read_skimage
        elif sys.platform in ['darwin']:
            self.reader = self._read_cv2

        self.expected_shape = self.imread(pathlist[0], False)

    def imread(self, imgpath, shapecheck=True):

        im = self.reader(imgpath)
        if shapecheck:
            if im.shape == self.expected_shape:
                return im
            else:
                raise HarpDataError("{} has unexpected dimensions").format(imgpath)
        else:
            return im.shape

    def _read_cv2(self, imgpath):
        try:
            im = cv2.imread(imgpath, cv2.CV_LOAD_IMAGE_UNCHANGED)
        except Exception:
            raise HarpDataError('failed to load {}'.format(im_name))

        if im == None:  #CV2 fails silently sometimes
            im_name = os.path.basename(imgpath)
            raise HarpDataError('failed to load {}'.format(im_name))
        else:
            return im

    def _read_skimage(self, imgpath):
        try:
            im = io.imread(imgpath)
        except Exception:
            im_name = os.path.basename(imgpath)
            raise HarpDataError('failed to load {}'.format(im_name))
        else:
            return im


    # def _read_ndimage(self, imgpath):
    #     return scipy.ndimage.imread(imgpath)


def imwrite(imgpath, img):
    cv2.imwrite(imgpath, img)

def imread():
    pass