#!/usr/bin/python

import os
from PyQt4 import QtCore
import sys

import numpy as np
import cv2

sys.path.append('..')
from imgprocessing.io import imread, imwrite


class Zproject(QtCore.QThread):

    def __init__(self, imglist, zprojection_output, force=False):
        super(Zproject, self).__init__()
        self.skip = 10
        self.imglist = imglist
        self.zprojection_output = zprojection_output
        self.skip_num = 10
        self.force = force

    def run(self):
        self.run_onthisthread()

    def run_onthisthread(self):
        """
        Run the Zprojection
        This is not in run, so we can bypass run() if we don't want to start a new thread
        """
        print 'zproject thread id', QtCore.QThread.currentThreadId()

        if os.path.isfile(self.zprojection_output) is False or self.force:

            print "Computing z-projection..."

            if len(self.imglist) < 1:
                self.emit(QtCore.SIGNAL('update(QString)'),  "No recon images found!")
            try:
                print self.imglist[0]
                im = imread(self.imglist[0])
            except IOError as e:
                self.emit(QtCore.SIGNAL('update(QString)'), "Cant load {}. Is it corrupted?".format(self.imglist[0]))

            imdims = im.shape
            dtype = im.dtype

            # make a new list by removing every nth image
            sparse_filelist = sorted(self.imglist)[0::self.skip_num]

            print "performing z-projection on sparse file list"

            max_array = self.max_projection(sparse_filelist, imdims, dtype)
            imwrite(self.zprojection_output, max_array)

        self.emit(QtCore.SIGNAL('update(QString)'), "Z-projection finished")

    def max_projection(self, filelist, imdims, bit_depth):

        maxi = np.zeros(imdims, dtype=bit_depth)

        for count, file_ in enumerate(filelist):

            im_array = imread(file_)

            #im_array = cv2.imread(file_, cv2.CV_LOAD_IMAGE_UNCHANGED)
            #max_ = np.maximum(max_, im_array[:][:])
            inds = im_array > maxi
            maxi[inds] = im_array[inds]
            if count % 10 == 0:
                self.emit(QtCore.SIGNAL('update(QString)'), "Z-project: " + str(count * 10) + "/" + str(len(self.imglist))
                                                            + " images processed")
                #self.callback("Z project: {0} images".format(count * self.skip))
        return maxi







