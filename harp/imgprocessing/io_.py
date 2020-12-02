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

E-mail the developers: sig@har.mrc.ac.uk

"""
import sys
sys.path.append('..')
import skimage.io as skim_io
import cv2
import os
from harp.appdata import HarpDataError
import tifffile
import time


class Imreader():
    def __init__(self, pathlist):

        if pathlist[0].lower().endswith(('tif', 'tiff')):
            usetiffile = True
            print("Using tiffile")
        else:
            usetiffile = False

        if sys.platform in ["win32", "win64"]:
            if usetiffile:
                self.reader = self._read_tiffs
            else:
                self.reader = self._read_skimage

        elif sys.platform in ["linux", 'linux2', 'linux3']:
            if usetiffile:
                self.reader = self._read_tiffs
            else:
                self.reader = self._read_skimage

        elif sys.platform in ['darwin']:
            self.reader = self._read_cv2

        self.expected_shape = self.imread(pathlist[0], False)

    def imread(self, imgpath, shapecheck=True):

        attempts = 0
        if not os.path.isfile(imgpath):
            raise HarpDataError("Cannot find file {}".format(imgpath))
        while True:
            try:
                im = self.reader(imgpath)
            except HarpDataError:
                if attempts < 4:
                    attempts += 1
                    time.sleep(5)
                else:
                    raise HarpDataError("Cannot load: {}. Network problems/courrpted file?".format(imgpath))
            else:
                break

        # Fix ofr RGBA OCT images where all the color values are the same and the opacity chaneel is ignored
        if len(im.shape) > 2:
            im = im[:, :, 0]  # Assuming we have RGBA and all the color values are the same, extract the R component
        if shapecheck:
            if im.shape == self.expected_shape:
                return im
            else:
                raise HarpDataError("{} has unexpected dimensions\nShould be: {}, got {}".format(
                    imgpath, self.expected_shape, im.shape))

        else:
            return im.shape

    def _read_cv2(self, imgpath):
        try:
            im = cv2.imread(imgpath, cv2.CV_LOAD_IMAGE_UNCHANGED)
        except Exception as e:
            im_name = os.path.basename(imgpath)
            raise HarpDataError('failed to load {}'.format(im_name))

        if im == None:  #CV2 fails silently sometimes
            im_name = os.path.basename(imgpath)
            raise HarpDataError('failed to load {}: {}'.format(im_name, e))
        else:
            return im

    def _read_skimage(self, imgpath):
        try:
            im = skim_io.imread(imgpath)
        except Exception as e:
            im_name = os.path.basename(imgpath)
            raise HarpDataError('failed to load {}: {}'.format(im_name, e))
        else:
            return im

    def _read_tiffs(self, imgpath):
        try:
            im = tifffile.imread(imgpath)
        except Exception as e:
            im_name = os.path.basename(imgpath)
            raise HarpDataError('failed to load {}: {}'.format(im_name, e))
        else:
            return im



class Imwriter():
    def __init__(self, img_path):
        if img_path.lower().endswith(('tif', 'tiff')):
            self.writer = self.tiff_writer
        elif img_path.lower().endswith('png'):
            self.writer = self.png_writer
        else:
            self.writer = self.skimage_write

    def tiff_writer(self, img, path):
        tifffile.imsave(path, img)

    def png_writer(self, img, path):
        print('png write')
        cv2.imwrite(path, img)

    def skimage_write(self, img, path):
        skim_io.imsave(path, img)

    def imwrite(self, img, path):
        self.writer(img, path)


def imread():
    pass