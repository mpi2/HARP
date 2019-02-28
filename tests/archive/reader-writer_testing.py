#!/usr/bin/env python


import SimpleITK as sitk
import cv2
from matplotlib import pyplot as plt
import os

TEST_16bit_TIFF = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.tif')

def test_cv2():
    im = cv2.imread(TEST_16bit_TIFF)
    plt.imshow(im)
    plt.title('cv2')
    plt.show()

