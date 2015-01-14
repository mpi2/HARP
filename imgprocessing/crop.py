#!/usr/bin/python

import argparse
import os
import fnmatch
import numpy as np
import cv2
import scipy.ndimage
import SimpleITK as sitk
from imgprocessing import zproject
import sys
sys.path.append("..")
import processing


class HarpDataError(Exception):
    """
    Raised when some of the supplied data is found to be faulty
    """
    pass


class Crop():
    def __init__(self, in_dir, out_dir, callback, configOb,
                 thread_terminate_flag, num_proc=None, def_crop=None, repeat_crop=None):
        """
        :param in_dir:
        :param out_dir:
        :param callback:
        :param num_proc:
        :param def_crop:
        :param repeat_crop:
        :return:
        """

        #call the super
        self.callback = callback
        self.configOb = configOb
        self.thread_terminate_flag = thread_terminate_flag
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.imdims = None
        self.def_crop = def_crop
        self.num_proc = num_proc
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
        self.run_crop_process()

    def run_crop_process(self):
        """
        Perform a crop based on previously selected bounding boxter
        :return:
        """
        first = True
        count = 0

        for file_ in sorted(self.files):
            count += 1
            try:
                im = scipy.ndimage.imread(file_)
            except IOError as e:
                raise HarpDataError("failed to read {}".format(file_))

            if first:
                dimcheck = im.shape
                first = False

            else:
                if im.shape != dimcheck:
                    raise HarpDataError("Cropping. First file had shape of {}. {} has shape {}".
                                        format(dimcheck, file_, im.shape))
                # try:
                #     pass
                #     #im[dimcheck] Check for indexing error as .shape is derived from header only

            if count % 20 == 0:
                if self.thread_terminate_flag.value == 1:
                    self.callback("Processing Cancelled!")
                    return
                self.callback(
                    "Cropping: {0}/{1} images".format(count, str(len(self.files))))

            try:
                imcrop = im[self.crop_box[1]:self.crop_box[3], self.crop_box[0]: self.crop_box[2]]
            except IndexError as e:
                raise HarpDataError("Crop box out of range. Is {} corrupted".format(file_))

            filename = os.path.basename(file_)
            crop_out = os.path.join(self.out_dir, filename)
            cv2.imwrite(crop_out, imcrop)

        self.callback("cropping finished")

    def pad_bounding_box(self, bbox, padding):

        bbox[0] -= padding  # xmin
        if bbox[0] < 0:
            bbox[0] = 0

        bbox[1] += padding  # xmax
        if bbox[1] > self.imdims[0] - 1:
            bbox[1] = 0

        bbox[2] -= padding  # ymin
        if bbox[2] < 0:
            bbox[2] = 0

        bbox[3] += padding  # ymax
        if bbox[3] > self.imdims[1] - 1:
            bbox[3] = 0

        return bbox

    def run_auto_mask(self):

        # Get list of files
        imglist = processing.getfilelist(self.in_dir)
        self.files = sorted(imglist)

        if len(imglist) < 1:
            return "no image files found in " + self.in_dir

        if self.def_crop:
            self.calc_manual_crop()
            self.callback("success")
        else:
            self.callback("Determining crop bounding box")
            z_proj_path = os.path.join(self.configOb.meta_path, "max_intensity_z.png")

            # Start with a z-projection
            zp = zproject.Zproject(imglist, z_proj_path)
            zp.run_onthisthread()

            zp_im = sitk.ReadImage(z_proj_path)

            try:
                testimg = scipy.ndimage.imread(imglist[0])
            except IOError as e:
                raise HarpDataError('Failed to read {}. Is it corrupt'.format(imglist[0]))

            datatype = testimg.dtype
            if datatype is np.uint16:
                outval = 65535
            else:
                outval = 255

            # Apply otsu threshold and remove all but largest component
            seg = sitk.OtsuThreshold(zp_im, insideValue=0, outsideValue=outval, numberOfHistogramBins=128)
            seg = sitk.ConnectedComponent(seg)  # label non-background pixels
            seg = sitk.RelabelComponent(seg)  # relabel components in order of ascending size
            # seg = seg == 1  # discard all but largest component

            # Get bounding box
            label_stats = sitk.LabelStatisticsImageFilter()
            label_stats.Execute(zp_im, seg)
            bbox = list(label_stats.GetBoundingBox(1))  # xmin, xmax, ymin, ymax (I think)

            # Padding
            self.imdims = testimg.shape
            padding = int(np.mean(self.imdims) * 0.025)
            bbox = self.pad_bounding_box(bbox, padding)
            self.crop_box = tuple(bbox)

            dimsx = self.crop_box[1] - self.crop_box[0]
            dimsy = self.crop_box[3] - self.crop_box[2]

            print self.crop_box

            if dimsx < 10 or dimsy < 10:
                raise HarpDataError('Autocrop failed, cropbox too small! Try manual cropping')

            # Actually perform the cropping
            count = 0

            for slice_ in self.files:

                try:
                    im = scipy.ndimage.imread(slice_)
                except IOError as e:
                    raise HarpDataError('Failed to read {}. Is it corrupt'.format(slice_))

                if count % 20 == 0:
                    if self.thread_terminate_flag.value == 1:
                        self.callback("Processing Cancelled!")
                        return
                    self.callback(
                        "Cropping: {0}/{1} images".format(count, str(len(self.files))))

                count += 1

                imcrop = im[self.crop_box[2]:self.crop_box[3], self.crop_box[0]: self.crop_box[1]]
                filename = os.path.basename(slice_)
                crop_out = os.path.join(self.out_dir, filename)
                cv2.imwrite(crop_out, imcrop)

            self.callback("success")

    def zp_callback(self, msg):
        pass
        #print msg

    def convertXYWH_ToCoords(self, xywh):
        """
        The input dimensions from the GUI needs converting for PIL
        """
        x1 = xywh[0] + xywh[2]
        y1 = xywh[1] + xywh[3]
        return xywh[0], xywh[1], x1, y1


def dummy_callback(msg):
    """use for cli running"""
    print msg


def cli_run():
    """
    Parse the arguments
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

#sys.exit()


if __name__ == '__main__':
    cli_run()
