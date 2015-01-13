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

# For QThread class
from PyQt4 import QtCore

#TODO: add HarpDataError exception handling


class Zproject:

    def __init__(self, imglist, out_dir, callback):
        self.img_dir = img_dir
        self.out_dir = out_dir
        self.shared_z_count = Value("i", 0)
        self.callback = callback
        self.im_array_queue = Queue.Queue(maxsize=20)
        self.maxintensity_queue = Queue.Queue()
        self.max_intensity_file_name = "max_intensity_z.png"  # Qt on windows is funny about tiffs
        self.skip_num = 10

    def run(self):
        """
        Run the Zprojection
        @return in 0 on success
        @return string with error message (TODO)
        """
        if len(imglist) < 1:
            return "no images in list"

        try:
            im = scipy.ndimage.imread(files[0])
        except IOError as e:
            return "Cant load {}. Is it corrupted?".format(files[0])

        imdims = im.shape

        # make a new list by removing every nth image
        sparse_filelist = files[0::self.skip_num]

        max_array = max_projection(sparse_filelist, imdims)

        io.imsave(os.path.join(self.out_dir, self.max_intensity_file_name), max_array)
        return 0  # Change

    def file_reader(self):
        for file_ in self.files:
            #im_array = cv2.imread(file_, cv2.CV_LOAD_IMAGE_UNCHANGED)
            im_array = scipy.ndimage.imread(file_)
            self.shared_z_count.value += (1 * self.skip_num)
            self.im_array_queue.put(im_array)
        # Insert sentinels to signal end of list
        for i in range(self.num_max_threads):
            self.im_array_queue.put(None)

    def max_projection(self, filelist, imdims):

        max_ = np.zeros(imdims)
        count = 0
        for file_ in filelist:
            count += 1
            im_array = scipy.ndimage.imread(file_)
            max_ = np.maximum(max_, im_array[:][:])
            if count % 10 == 0:
                self.callback("Z project: {0} images".format(str(self.shared_z_count.value)))
        return max_


def zproject_callback(msg):
    print(msg)


class ZProjectThread(QtCore.QThread):
    """
    Runs the Zprojection on a seperate thread
    """
    def __init__(self, imglist, tmp_dir):
        QtCore.QThread.__init__(self)
        self.input_folder = input_folder
        self.tmp_dir = tmp_dir

    def __del__(self):
        self.wait()

    def run(self):

        # Get the directory of the script
        if getattr(sys, 'frozen', False):  # James - I don't know what this is for. Neil - Me neither
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        # Set up a zproject object
        zp = Zproject(self.input_folder, self.tmp_dir, self.z_callback)
        # run the object
        zp_result = zp.run()

        # An error has happened. The error message will be shown on the status section
        if zp_result != 0:
            self.emit(QtCore.SIGNAL('update(QString)'),
                      "Z projection failed. Error message: {0}. Give Tom or Neil a Call if it happens again".format(
                          zp_result))
            return
        # let the user know what's happened
        self.emit(QtCore.SIGNAL('update(QString)'), "Z-projection finished")

    def z_callback(self, msg):
        self.emit(QtCore.SIGNAL('update(QString)'), msg)


if __name__ == "__main__":
    z = Zproject(sys.argv[1], sys.argv[2], zproject_callback)
    zp_img = z.run()





