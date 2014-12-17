#!/usr/bin/python


import scipy.ndimage
import os
import sys
import cv2
import SimpleITK as sitk




def scale_xy(img_path, scale_factor):
    """
    Read in slices one at a time, scale in the XY dimesions. Save to a temporary directory
    :return: xy_dir
    """
    print('doing xy-scaling')

    array = cv2.imread(img_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)

    #This would do a interpolation of nearest neighbour. Not the same as average subsampling?
    scaled_array = scipy.ndimage.zoom(array, 1.0 / scale_factor, order=0)

    #Try to write own function instead
    #scaled_array = self.rebin_factor(array, scale_factor)

    outpath = '/home/neil/work/harp_test_data/test_xy_scaling/resampler_out/resample2.nrrd'
    # cv2.imwrite(outpath, scaled_array)  # TODO: Write uncompressed, should be quicker
    sitk.WriteImage(sitk.GetImageFromArray(scaled_array), outpath)


img_path = '/home/neil/work/harp_test_data/test_xy_scaling/20141120_GABARAPL2_E14.5_16.3h_WT_XX_rec1104.BMP'
scale_factor = 2

scale_xy(img_path, scale_factor)