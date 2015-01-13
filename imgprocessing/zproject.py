#!/usr/bin/python

import sys
import os
import numpy as np
import re
from multiprocessing import cpu_count, Value, freeze_support
import threading
import Queue
import cv2
import scipy.ndimage
import skimage.io as io
from PyQt4 import QtCore


class Zproject:

    def __init__(self, imglist, zprojection_output, callback):
        self.skip = 10
        self.imglist = imglist
        self.callback = callback
        self.zprojection_output = zprojection_output
        self.skip_num = 10

    def run(self):
        """
        Run the Zprojection
        @return in 0 on success
        @return string with error message (TODO)
        """
        if len(self.imglist) < 1:
            return "no images in list"

        try:
            im = scipy.ndimage.imread(self.imglist[0])
        except IOError as e:
            return "Cant load {}. Is it corrupted?".format(self.imglist[0])

        imdims = im.shape

        # make a new list by removing every nth image
        sparse_filelist = sorted(self.imglist)[0::self.skip_num]

        max_array = self.max_projection(sparse_filelist, imdims)

        cv2.imwrite(self.zprojection_output, max_array)
        return 0  # Change

    def max_projection(self, filelist, imdims):

        maxi = np.zeros(imdims)
        count = 0
        for file_ in filelist:
            count += 1

            im_array = scipy.ndimage.imread(file_)

            #im_array = cv2.imread(file_, cv2.CV_LOAD_IMAGE_UNCHANGED)
            #max_ = np.maximum(max_, im_array[:][:])
            inds = im_array > maxi
            maxi[inds] = im_array[inds]
            if count % 10 == 0:
                self.callback("Z project: {0} images".format(count * self.skip))
        return maxi

def zproject_callback(msg):
    print(msg)


class ZProjectThread(QtCore.QThread):
    """
    Runs the Zprojection on a seperate thread
    """
    def __init__(self, imglist, zprojection_output):
        QtCore.QThread.__init__(self)
        self.imglist = imglist
        self.zprojection_output = zprojection_output


    def run(self):

        # Get the directory of the script. Maybe we can get rid of this, NH
        if getattr(sys, 'frozen', False):  # James - I don't know what this is for. Neil - Me neither
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        # Set up a zproject object
        zp = Zproject(self.imglist, self.zprojection_output, self.z_callback)
        # run the object
        zp_result = zp.run()

        # An error has happened. The error message will be shown on the status section
        if zp_result != 0:
            self.emit(QtCore.SIGNAL('update(QString)'),
                      "Z projection failed. Error message: {0}. Contact the DCC if it happens again".format(
                          zp_result))
            return
        # let the user know what's happened
        self.emit(QtCore.SIGNAL('update(QString)'), "Z-projection finished")

    def z_callback(self, msg):
        self.emit(QtCore.SIGNAL('update(QString)'), msg)


if __name__ == "__main__":

    z = Zproject(sys.argv[1], sys.argv[2], zproject_callback)
    zp_img = z.run()





