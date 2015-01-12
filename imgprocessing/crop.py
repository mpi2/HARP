#!/usr/bin/python

import argparse
import os
from sys import platform as _platform
import fnmatch
import numpy as np
import multiprocessing as mp
from time import sleep
import cv2
import SimpleITK as sitk
from imgprocessing import zproject

class Crop():
    def __init__(self, in_dir, out_dir, callback, ignore_exts, configOb, num_proc=None, def_crop=None, repeat_crop=None):
        """
        :param in_dir:
        :param out_dir:
        :param callback:
        :param ignore_exts: tuple, file extension names to miss from cropping, such as *.spr.tiff
        :param num_proc:
        :param def_crop:
        :param repeat_crop:
        :return:
        """
        # freeze support (windows only)
        if _platform == "win32" or _platform == "win64":
            mp.freeze_support()

        #call the super
        self.callback = callback
        self.configOb = configOb
        self.ignore_exts = ignore_exts
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.shared_auto_count = mp.Value("i", 0)
        self.shared_crop_count = mp.Value("i", 0)
        self.imdims = None
        self.def_crop = def_crop
        self.num_proc = num_proc
        self.repeat_crop = repeat_crop

        self.metric_file_queue = mp.Queue(30)
        self.crop_metric_queue = mp.Queue()
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
        for file_ in self.files:
            im = cv2.imread(file_, cv2.CV_LOAD_IMAGE_UNCHANGED)
            if im == None:
                print "dodgy file"
                self.callback("failed to read {}".format(file_))

            self.shared_crop_count.value += 1
            if self.shared_crop_count.value % 20 == 0:
                self.callback(
                    "Cropping: {0}/{1} images".format(str(self.shared_crop_count.value), str(len(self.files))))

            imcrop = im[self.crop_box[1]:self.crop_box[3], self.crop_box[0]: self.crop_box[2]]
            filename = os.path.basename(file_)
            crop_out = os.path.join(self.out_dir, filename)
            cv2.imwrite(crop_out, imcrop)
            self.yield_python()

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
        sparse_files, files, cropped_files = self.getFileList(self.in_dir, self.skip_num)
        self.files = files

        if len(sparse_files) < 1:
            return ("no image files found in " + self.in_dir)

        if self.def_crop:
            self.calc_manual_crop()
            self.callback("success")
        else:

            # Start with a z-projection
            zp = zproject.Zproject(self.in_dir, self.configOb.meta_path, self.zp_callback)
            zp.run()

            # Load z projection image
            z_proj_path = os.path.join(self.configOb.meta_path, "max_intensity_z.png")
            zp_im = sitk.ReadImage(z_proj_path)

            testimg = cv2.imread(sparse_files[0], cv2.CV_LOAD_IMAGE_UNCHANGED)
            if testimg == None:
                self.callback('Failed to read {}. Is it corrupt'.format(sparse_files[0]))
                return

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

            if self.crop_box[1] - self.crop_box[0] < 10 or self.crop_box[3] - self.crop_box[2] < 10:
                self.callback('Autocrop failed! Try manual cropping')
                return

            # Actually perform the cropping
            crop_count = 1

            for slice_ in self.files:

                im = cv2.imread(slice_, cv2.CV_LOAD_IMAGE_UNCHANGED)
                if im == None:
                    self.callback(self.callback('Failed to read {}. Is it corrupt'.format(slice_)))
                    return

                if crop_count % 20 == 0:
                    self.callback(
                        "Cropping: {0}/{1} images".format(str(crop_count), str(len(self.files))))

                crop_count += 1

                imcrop = im[self.crop_box[2]:self.crop_box[3], self.crop_box[0]: self.crop_box[1]]
                filename = os.path.basename(slice_)
                crop_out = os.path.join(self.out_dir, filename)
                cv2.imwrite(crop_out, imcrop)

            self.callback("success")

    def zp_callback(self, msg):
        pass
        #print msg

    def getFileList(self, filedir, skip):
        """
        Get the list of files from filedir. Exclude known non slice files
        """
        files = []
        cropped_files =[]
        for fn in os.listdir(filedir):
            if any(fn.endswith(x) for x in self.ignore_exts):
                continue
            if any(fnmatch.fnmatch(fn, x) for x in (
                    '*rec*.bmp', '*rec*.BMP', '*rec*.tif', '*rec*.TIF', '*rec*.jpg', '*rec*.JPG', '*rec*.jpeg', '*rec*.JPEG' )):
                files.append(os.path.join(self.in_dir, fn))
                cropped_files.append(os.path.join(self.out_dir, fn))
        return tuple(files[0::skip]), files, cropped_files


    def convertXYWH_ToCoords(self, xywh):
        """
        The input dimensions from the GUI needs converting for PIL
        """
        x1 = xywh[0] + xywh[2]
        y1 = xywh[1] + xywh[3]
        return xywh[0], xywh[1], x1, y1

    def yield_python(self, seconds=0):
        sleep(seconds)

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
    mp.freeze_support()
    cli_run()
