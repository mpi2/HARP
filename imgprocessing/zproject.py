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

# For QThread class
from PyQt4 import QtCore

#TODO: add HarpDataError exception handling


class Zproject:
    def __init__(self, img_dir, out_dir, callback):
        self.img_dir = img_dir
        self.out_dir = out_dir
        self.shared_z_count = Value("i", 0)
        self.callback = callback
        self.im_array_queue = Queue.Queue(maxsize=20)
        self.maxintensity_queue = Queue.Queue()
        self.max_intensity_file_name = "max_intensity_z.png"  # Qt on windows is funny about tiffs

    def run(self):
        '''
        Run the Zprojection
        @return in 0 on success
        @return string with error message (TODO)
        '''
        files = []

        for fn in os.listdir(self.img_dir):
            if fn.endswith(('spr.bmp', 'spr.BMP', 'spr.tif', 'spr.TIF', 'spr.jpg', 'spr.JPG', 'spr.jpeg', 'spr.JPEG')):
                continue
            if fn.endswith(('.bmp', '.BMP', '.tif', '.TIF', '.jpg', '.JPG', 'jpeg', 'JPEG')):
                prog = re.compile("rec")
                if prog.search(fn):
                    files.append(os.path.join(self.img_dir, fn))
        if len(files) < 1:
            return "no image files found in" + self.img_dir

        #im = cv2.imread(files[0], cv2.CV_LOAD_IMAGE_UNCHANGED)
        im = scipy.ndimage.imread(files[0])
        if im == None:
            return "Cant load {}. Is it corrupted?".format(files[0])

        self.imdims = im.shape

        # make a new list by removing every nth image
        self.skip_num = 10
        self.files = files[0::self.skip_num]

        self.num_max_threads = 2

        #Start the file reader
        read_thread = threading.Thread(target=self.fileReader)
        read_thread.setDaemon(True)
        read_thread.start()

        #Start the thread to determine max intensities
        max_threads = []

        for i in range(self.num_max_threads):
            t = threading.Thread(target=self.maxFinder)
            t.setDaemon(True)
            t.start()
            max_threads.append(t)
        for th in max_threads:
            th.join()
        print("maxes done")

        max_arrays = []
        while True:
            try:
                max_arrays.append(self.maxintensity_queue.get_nowait())
            except Queue.Empty:
                break
        #Process the max intensities from the separate threads
        try:
            maxi = reduce(np.maximum, max_arrays)
        except TypeError as e:
            return "Can't do the Z-projection. Make sure all image files are of the same dimension"

        #something wrong with image creation
        if maxi.shape == (0, 0):
            return "something went wrong creating the Z-projection from {}".format(self.img_dir)
        else:
            cv2.imwrite(os.path.join(self.out_dir, self.max_intensity_file_name), maxi)
            return (0)

    def fileReader(self):
        for file_ in self.files:
            #im_array = cv2.imread(file_, cv2.CV_LOAD_IMAGE_UNCHANGED)
            im_array = scipy.ndimage.imread(file_)
            self.shared_z_count.value += (1 * self.skip_num)
            self.im_array_queue.put(im_array)
        # Insert sentinels to signal end of list
        for i in range(self.num_max_threads):
            self.im_array_queue.put(None)

    def maxFinder(self):
        max_ = np.zeros(self.imdims)
        while True:
            try:
                # print(self.im_array_queue.qsize())
                im_array = self.im_array_queue.get(block=True)
                #print("write queue size:", self.write_file_queue.qsize())
            except Queue.Empty:
                pass
            else:
                self.im_array_queue.task_done()
                if im_array is None:
                    break
                max_ = np.maximum(max_, im_array[:][:])
                if self.shared_z_count.value % 10 == 0:
                    self.callback("Z project: {0} images".format(str(self.shared_z_count.value)))
                    # self.maxintensity_queue.put(max_)

        self.maxintensity_queue.put(max_)
        return


def dummyCallBack(msg):
    print(msg)


class ZProjectThread(QtCore.QThread):
    def __init__(self, input, tmp_dir):
        QtCore.QThread.__init__(self)
        self.input_folder = input
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
    z = Zproject(sys.argv[1], sys.argv[2], dummyCallBack)
    zp_img = z.run()





