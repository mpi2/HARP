#!/usr/bin/env python

import sys
import os
import cv2
import SimpleITK as sitk


path_to_test_dir = '/home/neil/work/speed_test'



img_path_list = os.listdir(path_to_test_dir)

if sys.argv[1] == 'cv':
    for impath in img_path_list:
        print impath
        img = cv2.imread(os.path.join(path_to_test_dir, impath), cv2.CV_LOAD_IMAGE_GRAYSCALE)
        print img.shape



elif sys.argv[1] == 'sitk':
    for impath in img_path_list:
        print impath
        img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
        print img.GetSize()





elif sys.argv[1] == 'sitk_write':
        impath = img_path_list[0]
        print impath
        img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
        arr = sitk.GetArrayFromImage(img)
        for i in range(100):
            sitk.WriteImage(img, os.path.join(path_to_test_dir, 'testout.tif'))


elif sys.argv[1] == 'cv_write':
        impath = img_path_list[0]
        print impath
        img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
        arr = sitk.GetArrayFromImage(img)
        for i in range(100):
            cv2.imwrite(os.path.join(path_to_test_dir, 'testout.tif'), arr)

