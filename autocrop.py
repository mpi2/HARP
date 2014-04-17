#!/usr/bin/python

#Comment for neil_test branch
try:
	import Image
except ImportError:
	from PIL import Image
from PyQt4 import QtGui, QtCore
import argparse
import os
import fnmatch
import numpy as np
from multiprocessing import Pool, cpu_count, freeze_support, Value
from multiprocessing.pool import ThreadPool
import sys
import time
import math
from collections import Counter
from matplotlib import pyplot as plt
import threading


shared_terminate = Value("i", 0)

class Autocrop(QtCore.QThread):
	def __init__(self, in_dir, out_dir, callback, num_proc=None, def_crop=None):
		super(Autocrop, self).__init__()
		#call the super
		self.callback = callback
		self.in_dir = in_dir
		self.out_dir = out_dir
		self.shared_auto_count = Value("i", 0)
		self.shared_crop_count = Value("i", 0)
		self.imdims = None
		self.def_crop = def_crop
		self.num_proc = num_proc

	def processor(self, filename):
		'''Processes each image file individually
		Implements __call__() so it can be used in multithreading by '''
		'''
		@param: filename path of an image to process
		@returns: tuple of bounding box coords

		Reads image into array. Flips it around each time
		with column/row of interest as the top top row
		'''

		global shared_terminate
		if shared_terminate.value == 1:
			return
		try:
			im = Image.open(filename)
		except OSError as e:
			print "Processor can't open file. {0}".format(e)
		matrix = np.array(im)
		crops = {}
		crops["x"] = np.std(matrix, axis=0)
		crops["y"] = np.std(matrix, axis=1)


		self.shared_auto_count.value += (1 * self.skip_num)
		#Report back every 20 images
		if self.shared_auto_count.value % 40 == 0:
			self.callback("Autocrop: {0} images".format(str(self.shared_auto_count.value)))
		del im
		return(crops)


	def cropper(self, img):
		'''
		Runs as a seperate process and performs the crop on a slice and saves it
		@param cropbox: tuple (x,y,width,height)
		@param out_dir: str(where to save the cropped imgs)
		'''
		global shared_terminate
		if shared_terminate.value == 1:
			return
		try:
			im = Image.open(img)
			imcrop = im.crop((self.crop_box[0], self.crop_box[1], self.crop_box[2], self.crop_box[3] ))
			filename = os.path.basename(img)
			crop_out = os.path.join(self.out_dir,filename)
			imcrop.save(crop_out)
			del im

			self.shared_crop_count.value += 1
			#Report back every 20 images
			if self.shared_crop_count.value % 10 == 0:
				self.callback("Cropping: {0} images".format(str(self.shared_crop_count.value)))
		except:
			#Catches corrupt files
			print "Error cropping file. The last file was {0}".format(img)


	def do_the_crop(self, images, crop_vals,  padding=0):
		'''
		@param: images list of image files
		@param: crop_vals tuple of the crop box (x, y, w, h)
		@param: out_dir str dir to output cropped images
		'''

		#Get the distances of the box sides from the sides of the image
		lcrop = crop_vals[0] - padding
		if lcrop < 0: lcrop = 0
		tcrop = crop_vals[1] - padding
		if tcrop < 0: tcrop = 0
		rcrop = crop_vals[2] + padding
		if rcrop > self.imdims[0] -1: rcrop = self.imdims[0] -1
		bcrop = crop_vals[3] + padding
		if bcrop > self.imdims[1] -1: bcrop = self.imdims[1] -1

		print("cropping with the following box x1, y1, x2, y2 ({0},{1},{2},{3});".format(
			lcrop, tcrop, rcrop, bcrop))
		print("Imagej: makeRectangle({0},{1},{2},{3});".format(
			lcrop, tcrop, rcrop - lcrop, bcrop - tcrop))
		print lcrop, tcrop, rcrop, bcrop
		self.crop_box = (lcrop, tcrop, rcrop, bcrop)
		pool_num = 0
		print("cropping")
		if self.num_proc:
			pool_num = int(num_proc)
		else:
			pool_num = cpu_count()
			if pool_num < 1:
				pool_num = 1
		pool = ThreadPool(processes=pool_num)
		pool.map(self.cropper, images)
		return


	def get_cropping_box(self, slices, side, rev = False):
		'''
		Given the metrics for each row x and y coordinate, calculate the point to crop given a threshold value
		@param slices dict: two keys x and y with metrics for respective dimensions
		@param side str: x or y
		@param threshold int:
		'''

		#get rid of the low values in the noise
		vals = [self.lowvals(x[side]) for x in slices]

		#filterout low values
		means = map(self.entropy, zip(*vals))
		#For testing the threshold
		#plt.plot(means)
		#plt.show()
		if rev:
			return next((i for i, v in enumerate(reversed(means)) if v > self.threshold ), -1)
		else:
			return next((i for i, v in enumerate(means) if v > self.threshold ), -1)


	def entropy(self, array):
		'''
		not currently used
		'''
		p, lns = Counter(self.round_down(array, 4)), float(len(array))
		return -sum( count/lns * math.log(count/lns, 2) for count in p.values())


	def round_down(self, array, divisor):
		for n in array:
			yield n - (n%divisor)


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
		self.skip_num = 10
		sparse_files, files = self.getFileList(self.in_dir, self.skip_num)

		if len(sparse_files) < 1:
			out_message = "no image files found in ", self.in_dir
			print out_message
			return out_message

		#get image dimensions from first file
		self.imdims = Image.open(sparse_files[0]).size

		if self.def_crop:
			self.do_the_crop(files, self.convertXYWH_ToCoords(def_crop))
			#sys.exit()
		else:
			print("Doing autocrop")
			self.threshold = 0.01
			pool_num = 0
			if self.num_proc:
				pool_num = int(num_proc)
			else:
				pool_num = cpu_count()
				if pool_num < 1:
					pool_num = 1
			pool = ThreadPool(processes=pool_num)
			slices = pool.map(self.processor, sparse_files )
			if shared_terminate.value == 1:
				del slices
				return

			#Distances of cropping boxes from their respective sides
			ldist = self.get_cropping_box(slices, "x")
			tdist = self.get_cropping_box(slices, "y")
			rdist = self.get_cropping_box(slices, "x", True)
			bdist = self.get_cropping_box(slices, "y", True)
			cropBox = self.convertDistFromEdgesToCoords((ldist, tdist, rdist, bdist))

			padding = int(np.mean(self.imdims)*0.025)
			self.do_the_crop(files, cropBox, padding)
			self.emit( QtCore.SIGNAL('cropFinished(QString)'), "success" )
			return


	def getFileList(self, dir, skip):
		'''
		Get the list of files from dir. Exclude known non slice files
		'''
		files = []
		for fn in os.listdir(dir):
			if any(fn.endswith(x) for x in ('spr.bmp','spr.BMP','spr.tif', 'spr.TIF', 'spr.jpg', 'spr.JPG', '*spr.jpeg', 'spr.JPEG')):
				continue
			if any(fnmatch.fnmatch(fn, x) for x in ('*rec*.bmp', '*rec*.BMP', '*rec*.tif', '*rec*.TIF', '*rec*.jpg', '*rec*.JPG', '*rec*.jpeg', '*rec*.JPEG' )):
				files.append(os.path.join(self.in_dir, fn))
		return(tuple(files [0::skip]), files)


	def convertDistFromEdgesToCoords(self, distances):
		'''
		Convert distances from sides(which comes from auto detection) sides into x,y,w,h
		PIL uses actual coords not width height
		'''
		x1 = self.imdims[0] - distances[2]
		x2 = self.imdims[1] - distances[3]
		return((distances[0], distances[1], x1, x2))


	def convertXYWH_ToCoords(self, xywh):
		'''
		The input dimensions from the GUI needs converting for PIL
		'''
		x1 = xywh[0] + xywh[2]
		x2 = xywh[1] + xywh[3]
		return((xywh[0], xywh[1], x1, x2))


def terminate():
		global shared_terminate
		shared_terminate.value = 1


def cli_run():
	'''
	Parse the arguments
	'''
	parser = argparse.ArgumentParser(description='crop a stack of bitmaps')
	parser.add_argument('-i', dest='in_dir', help='dir with bmps to crop', required=True)
	parser.add_argument('-o', dest='out_dir', help='destination for cropped images', required=True)
	parser.add_argument('-t', dest='file_type', help='tif or bmp', default="bmp")
	parser.add_argument('-d', nargs=4, type=int, dest='def_crop', help='set defined boundaries for crop x,y,w,h', default=None)
	parser.add_argument('-p', dest="num_proc", help='number of processors to use', default = None)
	args = parser.parse_args()
	ac = Autocrop(args.in_dir, args.out_dir, args.num_proc, args.def_crop)
	ac.run()
		#sys.exit()


if __name__ == '__main__':
	freeze_support()
	cli_run()
