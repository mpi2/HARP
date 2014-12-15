#!/usr/bin/env python

"""
In order to try and move away from dependency on ImageJ, we will try to implement the scaling functionality using
Python/numpy
"""

import numpy as np
import SimpleITK as sitk
import os
import scipy.ndimage
import shutil


class Rescaler(object):
    def __init__(self, img_path_list, scalefactor=2):
        """

        :param img_path_list:
        :param scalefactor: int, the shrink factor
        :return:
        """

        self.TEMP_XY_DIR = 'tempxy'
        self.YSCALED_DIR = 'y_scaled'
        self.SCALE_FACTOR = scalefactor


        if os.path.isdir(self.TEMP_XY_DIR):
            shutil.rmtree(self.TEMP_XY_DIR)
        os.mkdir(self.TEMP_XY_DIR)

        if os.path.isdir(self.YSCALED_DIR):
            shutil.rmtree(self.YSCALED_DIR)
        os.mkdir(self.YSCALED_DIR)

        self.scale_xy(img_path_list)
        self.scale_z()

    def scale_xy(self, img_path_list):
        """
        Read in slices one at a time, scale in the XY dimesions. Save to a temporary directory
        :return: xy_dir
        """
        print('doing xy-scaling')
        for unscaled_xy_slice in img_path_list:

            array = self.get_array_from_image_file(unscaled_xy_slice)
            scaled_array = scipy.ndimage.zoom(array, 1.0 / self.SCALE_FACTOR, order=0)
            scaled_img = sitk.GetImageFromArray(scaled_array)
            img_id = os.path.splitext(os.path.basename(unscaled_xy_slice))[0]
            outpath = os.path.join(self.TEMP_XY_DIR, "{}.tif".format(img_id))
            sitk.WriteImage(scaled_img, outpath)


    def scale_z(self):
        """
        :param: xy_scaled_dir, path to directory containing xy-scaled images
        :return:
        """

        print('doing z-scaling')

        imgpath_list = sorted(hil.GetFilePaths(self.TEMP_XY_DIR))

        last_img_index = 0
        out_count = 0  # For naming the outputs
        for i in range(self.SCALE_FACTOR, len(imgpath_list), self.SCALE_FACTOR):

            array_list = []
            for j in range(last_img_index, i):
                array_list.append(self.get_array_from_image_file(imgpath_list[j]))

            last_img_index = i

            first_array = array_list[0].astype(np.uint16)  # Needs a larger type to do the calculations
            for ar in array_list[1:]:  # Skip the first
                first_array += ar

            average_slice = (first_array / self.SCALE_FACTOR).astype(np.uint8)  # Should go back to original dtype!
            average_img = sitk.GetImageFromArray(average_slice)

            #Writeout the result
            filename_counter = '0' * (4 - (len(str(out_count)))) + str(out_count)
            sitk.WriteImage(average_img, os.path.join(self.YSCALED_DIR, filename_counter + '.tif'))
            out_count += 1

        #Process an extra slice if the filelist is not divisible by scalfactor
        num_remaining = len(imgpath_list) % self.SCALE_FACTOR
        if num_remaining != 0:
            remaining_files = sorted(imgpath_list[-num_remaining:])

            array_list = []
            for left_over in remaining_files:
                array_list.append(self.get_array_from_image_file(left_over))

            first_array = array_list[0].astype(np.uint16)  # Needs a larger type to do the calculations
            for ar in array_list[1:]:  # Skip the first
                first_array += ar

            average_slice = (first_array / num_remaining).astype(np.uint8)  # Should go back to original dtype!
            average_img = sitk.GetImageFromArray(average_slice)

            #Writeout the result
            filename_counter = '0' * (4 - (len(str(out_count)))) + str(out_count)
            sitk.WriteImage(average_img, os.path.join(self.YSCALED_DIR, filename_counter + '.tif'))


    def get_array_from_image_file(self, img_path):

        img = sitk.ReadImage(img_path)
        arr = sitk.GetArrayFromImage(img)
        return arr



if __name__ == '__main__':
    import sys
    import harwellimglib as hil
    img_list = hil.GetFilePaths(sys.argv[1])
    scalefactor = sys.argv[2]
    rescaler = Rescaler(img_list, int(scalefactor))