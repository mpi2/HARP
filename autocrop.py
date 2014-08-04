#!/usr/bin/python

# Comment for neil_test branch
import argparse
import os
from sys import platform as _platform
import fnmatch
import numpy as np
import math
from collections import Counter
#from matplotlib import pyplot as plt
import threading
import cv2
import multiprocessing as mp
from time import sleep

shared_terminate = mp.Value("i", 0)
msg_q = mp.Queue()


class Autocrop():
    def __init__(self, in_dir, out_dir, callback, num_proc=None, def_crop=None,repeat_crop=None):
        # freeze support (windows only)
        if _platform == "win32" or _platform == "win64":
            mp.freeze_support()

        #call the super
        self.callback = callback
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
        self.skip_num = 10  #read evey n files for determining cropping box
        self.threshold = 0.01  #Threshold for cropping metric
        shared_terminate.value = 0


    def metricFinder(self):
        '''Processes each image file individually
		Implements __call__() so it can be used in multithreading by '''
        '''
		@param: filename path of an image to process
		@returns: tuple of bounding box coords

		Reads image into array. Flips it around each time
		with column/row of interest as the top top row
		'''

        global shared_terminate

        while True:
            try:
                if shared_terminate.value == 1:
                    self.callback("Processing Cancelled!")
                    return

                matrix = self.metric_file_queue.get(block=True)

                self.yield_python()

                if matrix == 'STOP':  #Found a sentinel
                    break
            except Exception as e:
                print("metric queue error:",e)
            else:
                #matrix = np.array(im)
                crops = {}
                crops["x"] = np.std(matrix, axis=0)
                crops["y"] = np.std(matrix, axis=1)
                self.crop_metric_queue.put(crops)
                self.yield_python()
            #self.metric_file_queue.task_done()


    def calc_auto_crop(self, padding=0):
        '''
		'''
        #Distances of cropping boxes from their respective sides
        ldist = self.get_cropping_box("x")
        tdist = self.get_cropping_box("y")
        rdist = self.get_cropping_box("x", True)
        bdist = self.get_cropping_box("y", True)
        crop_vals = self.convertDistFromEdgesToCoords((ldist, tdist, rdist, bdist))

        #Get the distances of the box sides from the sides of the image
        lcrop = crop_vals[0] - padding
        if lcrop < 0: lcrop = 0
        tcrop = crop_vals[1] - padding
        if tcrop < 0: tcrop = 0
        rcrop = crop_vals[2] + padding
        if rcrop > self.imdims[0] - 1: rcrop = self.imdims[0] - 1
        bcrop = crop_vals[3] + padding
        if bcrop > self.imdims[1] - 1: bcrop = self.imdims[1] - 1

        print("cropping with the following box x1, y1, x2, y2 ({0},{1},{2},{3});".format(
            lcrop, tcrop, rcrop, bcrop))
        print("Imagej: makeRectangle({0},{1},{2},{3});".format(
            lcrop, tcrop, rcrop - lcrop, bcrop - tcrop))
        print lcrop, tcrop, rcrop, bcrop
        self.crop_box = (lcrop, tcrop, rcrop, bcrop)
        self.callback(self.crop_box)
        self.yield_python()

        # do the cropping in cv2
        self.run_crop_process()

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
        global shared_terminate
        # Perform the cropping using cv2
        for file_ in self.files:
            if shared_terminate.value == 1:
                self.callback("Processing Cancelled!")
                return
            im = cv2.imread(file_, cv2.CV_LOAD_IMAGE_GRAYSCALE)
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


    def init_cropping(self, msg_q):
        for file_ in self.files:
            if shared_terminate.value == 1:
                self.callback("Processing Cancelled!")
                return
            im = cv2.imread(file_, cv2.CV_LOAD_IMAGE_GRAYSCALE)
            self.shared_crop_count.value += 1
            if self.shared_crop_count.value % 20 == 0:
                msg_q.put("Cropping: {0}/{1} images".format(str(self.shared_crop_count.value), str(len(self.files))))

            imcrop = im[self.crop_box[1]:self.crop_box[3], self.crop_box[0]: self.crop_box[2]]
            filename = os.path.basename(file_)
            crop_out = os.path.join(self.out_dir, filename)
            cv2.imwrite(crop_out, imcrop)
            self.yield_python()
        msg_q.put("STOP")  #sentinel


    def get_cropping_box(self, side, rev=False):
        '''
		Given the metrics for each row x and y coordinate, calculate the point to crop given a threshold value
		@param slices dict: two keys x and y with metrics for respective dimensions
		@param side str: x or y
		@param threshold int:
		'''
        #print metric_slices
        vals = [self.lowvals(x[side]) for x in self.metric_slices]

        #filterout low values
        means = map(self.entropy, zip(*vals))
        #For testing the threshold
        #plt.plot(means)
        #plt.show()
        if rev:
            return next((i for i, v in enumerate(reversed(means)) if v > self.threshold ), -1)
        else:
            return next((i for i, v in enumerate(means) if v > self.threshold ), -1)

        self.yield_python()


    def entropy(self, array):
        '''
		not currently used
		'''
        p, lns = Counter(self.round_down(array, 4)), float(len(array))
        return -sum(count / lns * math.log(count / lns, 2) for count in p.values())


    def round_down(self, array, divisor):
        for n in array:
            yield n - (n % divisor)


    def lowvals(self, array, value=15):
        '''
		Values lower than value, set to zero
		'''
        low_values_indices = array < value
        array[low_values_indices] = 0
        return array


    def run(self):
        '''
		'''
        #get a subset of files to work with to speed it up

        sparse_files, files = self.getFileList(self.in_dir, self.skip_num)
        self.files = files

        if len(sparse_files) < 1:
            return ("no image files found in " + self.in_dir)

        #get image dimensions from first file
        self.imdims = cv2.imread(sparse_files[0], cv2.CV_LOAD_IMAGE_GRAYSCALE).shape
        padding = int(np.mean(self.imdims) * 0.025)

        if self.def_crop:
            self.calc_manual_crop()
            if shared_terminate.value == 1:
                self.callback("Processing Cancelled!")
                return
            self.callback("success")
        else:
            print("Doing autocrop")
            pool_num = 2
            mThreads = []
            for i in range(pool_num):
                t = threading.Thread(target=self.metricFinder)
                t.setDaemon(True)
                mThreads.append(t)
                t.start()

            #setup the file queue for finding metric
            for file_ in sparse_files:
                if shared_terminate.value == 1:
                    self.callback("Processing Cancelled!")
                    return

                self.shared_auto_count.value += (1 * self.skip_num)
                if self.shared_auto_count.value % 40 == 0:
                    self.callback("Getting crop box: {0}/{1} images".format(str(self.shared_auto_count.value),
                                                                            str(len(self.files))))
                im = cv2.imread(file_, cv2.CV_LOAD_IMAGE_GRAYSCALE)
                self.metric_file_queue.put(im)
                self.yield_python()

            #Add some sentinels and block until threads finish
            for i in range(pool_num):
                self.metric_file_queue.put('STOP')
            for t in mThreads:
                t.join()
            print("cropping box determined")
            self.crop_metric_queue.put('STOP')
            self.metric_slices = [item for item in iter(self.crop_metric_queue.get, 'STOP')]


            #Die if signalled from gui
            if shared_terminate.value == 1:
                self.callback("Processing Cancelled!")
                return

            # Perform the actuall cropping
            self.calc_auto_crop(padding)

            if shared_terminate.value == 1:
                return

            self.callback("success")
            return


    def getFileList(self, dir, skip):
        '''
		Get the list of files from dir. Exclude known non slice files
		'''
        files = []
        for fn in os.listdir(dir):
            if any(fn.endswith(x) for x in
                   ('spr.bmp', 'spr.BMP', 'spr.tif', 'spr.TIF', 'spr.jpg', 'spr.JPG', '*spr.jpeg', 'spr.JPEG')):
                continue
            if any(fnmatch.fnmatch(fn, x) for x in (
                    '*rec*.bmp', '*rec*.BMP', '*rec*.tif', '*rec*.TIF', '*rec*.jpg', '*rec*.JPG', '*rec*.jpeg', '*rec*.JPEG' )):
                files.append(os.path.join(self.in_dir, fn))
        return (tuple(files[0::skip]), files)


    def convertDistFromEdgesToCoords(self, distances):
        '''
		Convert distances from sides(which comes from auto detection) sides into x,y,w,h
		PIL uses actual coords not width height
		'''
        x2 = self.imdims[0] - distances[2]
        y2 = self.imdims[1] - distances[3]
        return ((distances[0], distances[1], x2, y2))


    def convertXYWH_ToCoords(self, xywh):
        '''
		The input dimensions from the GUI needs converting for PIL
		'''
        x1 = xywh[0] + xywh[2]
        y1 = xywh[1] + xywh[3]
        return ((xywh[0], xywh[1], x1, y1))

    def yield_python(self, seconds=0):
        sleep(seconds)

def terminate():
    global shared_terminate
    shared_terminate.value = 1


def init_cropping_win(self):
    global msg_q
    print "init crop win"
    for file_ in self.files:
        if shared_terminate.value == 1:
            return
        im = cv2.imread(file_, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        self.shared_crop_count.value += 1
        if self.shared_crop_count.value % 20 == 0:
            print "Cropping: {0}/{1} images".format(str(self.shared_crop_count.value), str(len(self.files)))
            msg_q.put("Cropping: {0}/{1} images".format(str(self.shared_crop_count.value), str(len(self.files))))

        imcrop = im[self.crop_box[1]:self.crop_box[3], self.crop_box[0]: self.crop_box[2]]
        filename = os.path.basename(file_)
        crop_out = os.path.join(self.out_dir, filename)
        cv2.imwrite(crop_out, imcrop)
    msg_q.put("STOP")  #sentinel


def dummy_callback(msg):
    '''use for cli running'''
    print msg


def cli_run():
    '''
	Parse the arguments
	'''
    parser = argparse.ArgumentParser(description='crop a stack of bitmaps')
    parser.add_argument('-i', dest='in_dir', help='dir with bmps to crop', required=True)
    parser.add_argument('-o', dest='out_dir', help='destination for cropped images', required=True)
    parser.add_argument('-t', dest='file_type', help='tif or bmp', default="bmp")
    parser.add_argument('-d', nargs=4, type=int, dest='def_crop', help='set defined boundaries for crop x,y,w,h',
                        default=None)
    parser.add_argument('-p', dest="num_proc", help='number of processors to use', default=None)
    args = parser.parse_args()
    ac = Autocrop(args.in_dir, args.out_dir, args.num_proc, args.def_crop)
    ac.run()

#sys.exit()


if __name__ == '__main__':
    mp.freeze_support()
    cli_run()
