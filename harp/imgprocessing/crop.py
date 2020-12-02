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

import argparse
import os
import sys
import numpy as np
from SimpleITK import ReadImage, WriteImage, GetImageFromArray, GetArrayFromImage, OtsuThreshold, ConnectedComponent, \
    RelabelComponent, LabelStatisticsImageFilter
from harp.imgprocessing import zproject
sys.path.append("..")
from harp.imgprocessing.io_ import Imreader, Imwriter
from harp.appdata import HarpDataError


class Crop():

    def __init__(self, in_dir, out_dir, callback, configOb,
                 thread_terminate_flag, app_data, def_crop=None, repeat_crop=None):
        """
        :param in_dir:
        :param out_dir:
        :param callback:
        :param num_proc:
        :param def_crop:
        :param repeat_crop:
        :return:
        """
        self.callback = callback
        self.configOb = configOb
        self.thread_terminate_flag = thread_terminate_flag
        self.app_data = app_data
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.imdims = None
        self.def_crop = def_crop
        self.repeat_crop = repeat_crop
        self.skip_num = 10  # read every n files for determining cropping box
        self.threshold = 0.01  # threshold for cropping metric

    def calc_manual_crop(self):
        # Repeat crop variable is for when an autocrop has already been performed for a channel of OPT and the user
        # wants to use the same cropping box
        if self.repeat_crop:
            self.crop_box = self.repeat_crop
        # self.def_crop is the crop box manually selected by the user
        elif self.def_crop:
            self.crop_box = self.convertXYWH_ToCoords(self.def_crop)
            # Will save the manual crop box here as well as it will be in the correct coordinate system
            self.callback(self.crop_box)
        # If no crop box has been manually selected something has gone wrong
        else:
            self.callback("Processing Cancelled!")
            return
        return self.crop_box

    def run(self, auto=False):
        """
        Perform a crop based on previously selected bounding box
        :return:
        """
        # Get list of files
        #imglist = processing.getfilelist(self.in_dir)
        imglist = self.app_data.getfilelist(self.in_dir)

        if len(imglist) < 1:
            raise HarpDataError("no image files found in " + self.in_dir)

        # Get cropbox either automatically or manually
        cb = self.auto_bounding_box(imglist) if auto else self.calc_manual_crop()
        print(cb)

        # Rearrange dimensions for numpy slicing
        cropbox = (cb[2], cb[3], cb[0], cb[1])
        print(cropbox)

        first = True
        outpathslist = []

        reader = Imreader(imglist)

        for count, file_ in enumerate(imglist):

            try:
                im = reader.imread(file_)
            except IOError as e:
                raise HarpDataError("failed to read {}".format(file_))

            else:
                if im.shape[0] < 1 or im.shape[1] < 1:
                    raise HarpDataError('Cannot read file, {}'.format(file_))

            if first:
                dimcheck = im.shape
                first = False

            else:
                if im.shape != dimcheck:
                    raise HarpDataError("Input files have different shapes {} and {}".
                                        format(dimcheck, imglist[0], file_))
                # try:
                #     pass
                #     #im[dimcheck] Check for indexing error as .shape is derived from header only

            if count % 20 == 0:
                if self.thread_terminate_flag.value == 1:
                    raise HarpDataError('Cancelled')
                self.callback(
                    "Cropping: {0}/{1} images".format(count, str(len(imglist))))

            filename = os.path.basename(file_)
            crop_out = os.path.join(self.out_dir, filename)

            try:
                imcrop = im[cropbox[0]:cropbox[1], cropbox[2]: cropbox[3]]
            except IndexError as e:
                raise HarpDataError("Crop box out of range. Is {} corrupted?".format(filename))

            if count < 1:
                # Set up the correct writer based on the first image to be written
                imwriter = Imwriter(crop_out)

            imwriter.imwrite(imcrop, crop_out)
            outpathslist.append(crop_out)

        self.callback("Success")

        return outpathslist

    def auto_bounding_box(self, filelist):

        self.callback("Determining crop bounding box")
        z_proj_path = os.path.join(self.configOb.meta_path, "max_intensity_z.png")

        # Start with a z-projection
        zp = zproject.Zproject(filelist, z_proj_path, force=True)
        zp.update.connect(self.update_slot)

        zp.run_onthisthread()

        zp_im = ReadImage(z_proj_path)
        reader = Imreader(filelist)
        try:
            testimg = reader.imread(filelist[0])
        except IOError as e:
            raise HarpDataError('Failed to read {}. Is it corrupt'.format(filelist[0]))

        datatype = testimg.dtype
        if datatype is np.uint16:
            outval = 65535
        else:
            outval = 255

        # Apply otsu threshold and remove all but largest component
        seg = OtsuThreshold(zp_im, 0, outval, 128)
        seg = ConnectedComponent(seg)  # label non-background pixels
        seg = RelabelComponent(seg)  # relabel components in order of ascending size
        # seg = seg == 1  # discard all but largest component

        # Get bounding box
        label_stats = LabelStatisticsImageFilter()
        label_stats.Execute(zp_im, seg)
        bbox = list(label_stats.GetBoundingBox(1))  # xmin, xmax, ymin, ymax (I think)

        # Padding
        self.imdims = testimg.shape
        padding = int(np.mean(self.imdims) * 0.04)
        bbox = self.pad_bounding_box(bbox, padding)

        # Callback!
        self.callback(tuple(bbox))

        # Crop the z-projection and write to metadata
        zp_arr = GetArrayFromImage(zp_im)
        zp_crop = GetImageFromArray(zp_arr[bbox[2]:bbox[3], bbox[0]:bbox[1]])
        WriteImage(zp_crop, os.path.join(self.configOb.meta_path, "crop_result.png"))

        return bbox


    def pad_bounding_box(self, bbox, padding):

        bbox[0] -= padding  # xmin
        if bbox[0] < 0:
            bbox[0] = 0

        bbox[1] += padding  # xmax
        if bbox[1] > self.imdims[0] - 1:
            bbox[1] = self.imdims[0] - 1

        bbox[2] -= padding  # ymin
        if bbox[2] < 0:
            bbox[2] = 0

        bbox[3] += padding  # ymax
        if bbox[3] > self.imdims[1] - 1:
            bbox[3] = self.imdims[1]

        return bbox


    def zp_callback(self, msg):
        pass
        #print msg

    def convertXYWH_ToCoords(self, xywh):
        """
        The input dimensions from the GUI needs converting for PIL
        """
        x1 = xywh[0] + xywh[2]
        y1 = xywh[1] + xywh[3]
        return xywh[0], x1, xywh[1], y1  # James fix - Jan 2016

    def update_slot(self, msg):
        self.callback(msg)


def dummy_callback(msg):
    """use for cli running"""
    print(msg)


def cli_run():
    """
    Parse the arguments.
    This is not workign at the moment
    """
    parser = argparse.ArgumentParser(description='crop a stack of bitmaps')
    parser.add_argument('-i', dest='in_dir', help='dir with bmps to crop', required=True)
    parser.add_argument('-o', dest='out_dir', help='destination for cropped images', required=True)
    parser.add_argument('-t', dest='file_type', help='tif or bmp', default="bmp")
    parser.add_argument('-d', nargs=4, type=int, dest='def_crop', help='set defined boundaries for crop x,y,w,h',
                    default=None)
    parser.add_argument('-p', dest="num_proc", help='number of processors to use', default=None)
    args = parser.parse_args()
    ac = Crop(args.in_dir, args.out_dir, args.num_proc, args.def_crop)
    ac.run()


if __name__ == '__main__':
    cli_run()
