#!/usr/bin/python

import numpy as np
import SimpleITK as sitk
import sys
import os
import cv2

dir_ = sys.argv[1]
first_img = True

#print os.listdir(dir)
array_3d = None
for file_ in sorted(os.listdir(dir_)):
    if file_.endswith(('tiff', 'tif', 'TIFF', 'TIF', 'BMP', 'bmp')):
        print file_
        array_2d = cv2.imread(os.path.join(dir_, file_), cv2.CV_LOAD_IMAGE_GRAYSCALE)
        if array_3d is None:
            array_3d = array_2d
            continue
        array_3d = np.dstack((array_3d, array_2d))
print 'final', array_3d.shape, 'dtype', array_3d.dtype
array_3d = np.swapaxes(array_3d, 0, 2)
array_3d = np.swapaxes(array_3d, 1, 2)

image_3d = sitk.GetImageFromArray(array_3d)

sitk.WriteImage(image_3d, 'test_stack.tiff')
