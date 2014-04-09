#!/usr/bin/python

try:
	import Image
except ImportError:
	from PIL import Image

import argparse
import os
import fnmatch
import numpy as np
from multiprocessing import Pool, cpu_count, freeze_support
import sys
import time
import math
from collections import Counter
from matplotlib import pyplot as plt


imdims = None

class Processor:
	'''Processes each image file individually
	Implements __call__() so it can be used in multithreading by '''

	def __init__(self, threshold):
		self.threshold = threshold

	def __call__(self, filename):
		'''
		@param: filename path of an image to process
		@returns: tuple of bounding box coords

		Reads image into array. Flips it around each time
		with column/row of interest as the top top row
		'''
		try:
			im = Image.open(filename)
		except OSError as e:
			print "Processor can't open file. {0}".format(e)
		matrix = np.array(im)
		crops = {}
		crops["x"] = np.std(matrix, axis=0)
		crops["y"] = np.std(matrix, axis=1)

		return(crops)


class Cropper:
	'''
	Runs as a seperate process and performs the crop on a slice and saves it
	'''
	def __init__(self, crop_box, out_dir):
		'''
		@param cropbox: tuple (x,y,width,height)
		@param out_dir: str(where to save the cropped imgs)
		'''
		self.crop_box = crop_box
		self.out_dir = out_dir

	def __call__(self, img):
		try:
			im = Image.open(img)
			imcrop = im.crop((self.crop_box[0], self.crop_box[1], self.crop_box[2], self.crop_box[3] ))
			filename = os.path.basename(img)
			crop_out = os.path.join(self.out_dir,filename)
			imcrop.save(crop_out)
		except:
			#Catches corrupt files
			print "Error cropping file. The last file was {0}".format(img)


def do_the_crop(images, crop_vals, out_dir,  padding=0):
	'''
	@param: images list of image files
	@param: crop_vals tuple of the crop box (x, y, w, h)
	@param: out_dir str dir to output cropped images
	'''
	global imdims

	#Get the distances of the box sides from the sides of the image
	lcrop = crop_vals[0] - padding
	if lcrop < 0: lcrop = 0
	tcrop = crop_vals[1] - padding
	if tcrop < 0: tcrop = 0
	rcrop = crop_vals[2] + padding
	if rcrop > imdims[0] -1: rcrop = imdims[0] -1
	bcrop = crop_vals[3] + padding
	if bcrop > imdims[1] -1: bcrop = imdims[1] -1

	print("cropping with the following box x1, y1, x2, y2 ({0},{1},{2},{3});".format(
		lcrop, tcrop, rcrop, bcrop))
	print("Imagej: makeRectangle({0},{1},{2},{3});".format(
		lcrop, tcrop, rcrop - lcrop, bcrop - tcrop))
	print lcrop, tcrop, rcrop, bcrop
	cropper = Cropper((lcrop, tcrop, rcrop, bcrop), out_dir)
	pool = Pool()
	pool.map(cropper, images)
	return


def get_cropping_box(slices, side, threshold, rev = False):
	'''
	'''
	vals = [lowvals(x[side]) for x in slices]

	#filterout low values
	means = map(np.std, zip(*vals))
	#plt.plot(means)
	#plt.show()

	if rev == True:
		return next((i for i, v in enumerate(reversed(means)) if v > threshold ), -1)
	else:
		return next((i for i, v in enumerate(means) if v > threshold ), -1)



def entropy(array):
	'''
	not currently used
	'''
	p, lns = Counter(round_down(array, 4)), float(len(array))
	return -sum( count/lns * math.log(count/lns, 2) for count in p.values())


def round_down(array, divisor):
	for n in array:
		yield n - (n%divisor)


def lowvals(array, value=20):
	'''
	Values lower than value, set to zero
	'''
	low_values_indices = array < value
	array[low_values_indices] = 0
	return array




def run(in_dir, out_dir, file_type="bmp", def_crop=None, num_proc=2):
	'''
	'''
	files = []


	for fn in os.listdir(in_dir):
		if (fnmatch.fnmatch(fn, '*spr.bmp') or fnmatch.fnmatch(fn, '*spr.BMP') or fnmatch.fnmatch(fn, '*spr.tif') or
			fnmatch.fnmatch(fn, '*spr.TIF') or fnmatch.fnmatch(fn, '*spr.jpg') or fnmatch.fnmatch(fn, '*spr.JPG') or
			fnmatch.fnmatch(fn, '*spr.jpeg') or fnmatch.fnmatch(fn, '*spr.JPEG')):
			continue
		if (fnmatch.fnmatch(fn, '*rec*.bmp') or fnmatch.fnmatch(fn, '*rec*.BMP') or fnmatch.fnmatch(fn, '*rec*.tif') or
			fnmatch.fnmatch(fn, '*rec*.TIF') or fnmatch.fnmatch(fn, '*rec*.jpg') or fnmatch.fnmatch(fn, '*rec*.JPG') or
			fnmatch.fnmatch(fn, '*rec*.jpeg') or fnmatch.fnmatch(fn, '*rec*.JPEG')):
				files.append(os.path.join(in_dir, fn))

	if len(files) < 1:
		out_message = "no image files found in ", in_dir
		print out_message
		return out_message
		#sys.exit("no image files found in" + in_dir)


	#get image dimensions from first file
	img = Image.open(files[0])
	global imdims
	imdims = img.size

	if def_crop:
		do_the_crop(files, concertXYWH_ToCoords(def_crop), out_dir)
		#sys.exit()
	else:
		print("Doing autocrop")
		threshold = 0.01
		proc = Processor(threshold)
		pool_num = 0
		if num_proc:
			pool_num = int(num_proc)
		else:
			pool_num = cpu_count() / 2
		pool = Pool(pool_num)

		#Take a subset of files and farm off to processes to determine crop vals
		sparse_files = files [0::10]
		slices = pool.map(proc, sparse_files)

		#Distances of cropping boxes from their respective sides
		ldist = get_cropping_box(slices, "x", threshold)
		tdist = get_cropping_box(slices, "y", threshold)
		rdist = get_cropping_box(slices, "x", threshold, True)
		bdist = get_cropping_box(slices, "y", threshold, True)
		cropBox = convertDistFromEdgesToCoords((ldist, tdist, rdist, bdist))

		padding = int(np.mean(imdims)*0.025)
		do_the_crop(files, cropBox, out_dir, padding)
		return
		#sys.exit(0)


def convertDistFromEdgesToCoords(distances):
	'''
	Convert distances from sides(which comes from auto detection) sides into x,y,w,h
	PIL uses actual coords not width height
	'''
	global imdims
	x1 = imdims[0] - distances[2]
	x2 = imdims[1] - distances[3]
	return((distances[0], distances[1], x1, x2))


def concertXYWH_ToCoords(xywh):
	'''
	The input dimensions from the GUI needs converting for PIL
	'''
	global imdims
	x1 = xywh[0] + xywh[2]
	x2 = xywh[1] + xywh[3]
	return((xywh[0], xywh[1], x1, x2))


def cli_run():
	'''
	Parse the arguments
	'''
	parser = argparse.ArgumentParser(description='crop a stack of bitmaps')
	parser.add_argument('-i', dest='in_dir', help='dir with bmps to crop', required=True)
	parser.add_argument('-o', dest='out_dir', help='destination for cropped images', required=True)
	parser.add_argument('-t', dest='file_type', help='tif or bmp', default="bmp")
	parser.add_argument('-d', nargs=4, type=int, dest='def_crop', help='set defined boundaries for crop x,y,w,h')
	parser.add_argument('-p', dest="num_proc", help='number of processors to use')
	args = parser.parse_args()
	run(args.in_dir, args.out_dir, args.file_type, args,def_crop, args.num_proc)
	#sys.exit()


if __name__ == '__main__':
	freeze_support()
	cli_run()
