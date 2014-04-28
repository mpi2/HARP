#!/usr/bin/python

#Comment for neil_test branch
import argparse
import os
import fnmatch
import numpy as np
from multiprocessing import cpu_count, freeze_support, Value
import math
from collections import Counter
from matplotlib import pyplot as plt
import threading
import Queue
import cv2
import subprocess
import contextlib
import signal


shared_terminate = Value("i", 0)
#the pids of the c++ croppers. For killing
cropper_pids = []


class Autocrop():
	def __init__(self, in_dir, out_dir, callback, finishedCallback, num_proc=None, def_crop=None):

		#call the super
		self.callback = callback
		self.finishedCallback = finishedCallback
		self.in_dir = in_dir
		self.out_dir = out_dir
		self.shared_auto_count = Value("i", 0)
		self.imdims = None
		self.def_crop = def_crop
		self.num_proc = num_proc
		self.metric_file_queue = Queue.Queue(maxsize=30)
		self.crop_metric_queue = Queue.Queue()
		self.skip_num = 10 #read evey n files for determining cropping box
		self.threshold = 0.01 #Threshold for cropping metric
		self.shared_crops_done = Value("i", 0)


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
		if shared_terminate.value == 1:
			return
		while True:
			try:
				matrix = self.metric_file_queue.get(block=True)
				if matrix == None: #Found a sentinel
					break
			except Queue.Empty:
				pass
			else:
				#matrix = np.array(im)
				crops = {}
				crops["x"] = np.std(matrix, axis=0)
				crops["y"] = np.std(matrix, axis=1)
				self.crop_metric_queue.put(crops)
				self.metric_file_queue.task_done()


	def calc_auto_crop(self,  padding=0):
		'''
		'''
		#Distances of cropping boxes from their respective sides
		ldist = self.get_cropping_box( "x")
		tdist = self.get_cropping_box( "y")
		rdist = self.get_cropping_box( "x", True)
		bdist = self.get_cropping_box( "y", True)
		crop_vals = self.convertDistFromEdgesToXYWH((ldist, tdist, rdist, bdist))

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
		print(lcrop, tcrop, rcrop, bcrop)
		self.crop_box = (lcrop, tcrop, rcrop, bcrop)
		self.init_cropping()


	def calc_manual_crop(self):
		self.crop_box = self.def_crop
		self.init_cropping()

	def init_cropping(self):
		#self.emit(QtCore.SIGNAL('update(QString)'),"cropping")
		#Increasing  number of threads should not increase speed as it's CPU/bound
		#Spawning processes might help though. Mixing threads and processes can be bad apparently though

		#Setup cropping threads
		fileList1 = open("filelist1", "w")
		for name in self.files:
			fileList1.write(name + "\n")
		fileList1.close()

# 		fileList2 = open("filelist2", "w")
# 		for i in range(len(self.files)/2, len(self.files)):
# 			fileList2.write(self.files[i] + "\n")
# 		fileList2.close()
		thread1 = threading.Thread(target=self.runCropBin, args=("filelist1",))
		thread1.setDaemon(True)
		thread1.start()
# 		thread2 = threading.Thread(target=self.runCropBin, args=("filelist2",))
# 		thread2.setDaemon(True)
# 		thread2.start()
		thread1.join()
# 		thread2.join()


	def runCropBin(self, fileList):
		global shared_terminate
		crop_binary = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cropper")
		x, y, w, h = self.crop_box
		cmd = [crop_binary, fileList, str(x), str(y), str(w), str(h), self.out_dir]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
		self.crop_proc = p
		global cropper_pids
		cropper_pids.append(p.pid)
		for line in self.unbuffered(p):
			if shared_terminate == 1:
				return
			try:
				int(line)
			except ValueError:#Not an int so it's a finished message
				self.finishedCallback(line)
				break
			else:
				num = int(line)
				with self.shared_auto_count.get_lock():
					self.shared_auto_count.value += num
				self.callback("cropping:{self.shared_auto_count.value}/{self.num_files}".format(**locals()))



	def unbuffered(self, proc, stream='stdout'):
		'''
		Get real time unbuffered output from cropper
		'''
		newlines = ['\n', '\r\n', '\r']
		stream = getattr(proc, stream)
		with contextlib.closing(stream):
			while True:
				out = []
				last = stream.read(1)
				# Don't loop forever
				if last == '' and proc.poll() is not None:
					break
				while last not in newlines:
					# Don't loop forever
					if last == '' and proc.poll() is not None:
						break
					out.append(last)
					last = stream.read(1)
				out = ''.join(out)
				yield out


	def get_cropping_box(self, side, rev = False):
		'''
		Given the metrics for each row x and y coordinate, calculate the point to crop given a threshold value
		@param slices dict: two keys x and y with metrics for respective dimensions
		@param side str: x or y
		@param threshold int:
		'''
		#get rid of the low values in the noise
		metric_slices = [item for item in self.crop_metric_queue.queue]
		#print metric_slices
		vals = [self.lowvals(x[side]) for x in metric_slices]

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

		sparse_files, files = self.getFileList(self.in_dir, self.skip_num)
		self.files = files
		self.num_files = len(self.files)

		if len(sparse_files) < 1:
			return("no image files found in " + self.in_dir)

		#get image dimensions from first file
		self.imdims = cv2.imread(sparse_files[0], cv2.CV_LOAD_IMAGE_GRAYSCALE).shape
		padding = int(np.mean(self.imdims)*0.025)

		if self.def_crop:
			self.calc_manual_crop()
			if shared_terminate.value == 1:
				self.crop_proc.kill()
				return
			self.finishedCallback("success" )
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
				self.shared_auto_count.value += (1 * self.skip_num)
				if self.shared_auto_count.value % 40 == 0:
					print("self.metric_file_queue.qsize", self.metric_file_queue.qsize())
					self.callback("Getting crop box: {0}/{1}".format(str(self.shared_auto_count.value), str(len(self.files))))
				im = cv2.imread(file_, cv2.CV_LOAD_IMAGE_GRAYSCALE)
				self.metric_file_queue.put(im)

			#Add some sentinels and block until threads finish
			for i in range(pool_num):
				self.metric_file_queue.put(None)
			for t in mThreads:
				t.join()
			print("metric done")


			#Die if signalled from gui
			if shared_terminate.value == 1:
				return

			self.calc_auto_crop(padding)
			if shared_terminate.value == 1:
				return
			else:
				self.finishedCallback("success")
				return


	def getFileList(self, dir_, skip):
		'''
		Get the list of files from dir. Exclude known non slice files
		'''
		files = []
		for fn in os.listdir(dir_):
			if any(fn.endswith(x) for x in ('spr.bmp','spr.BMP','spr.tif', 'spr.TIF', 'spr.jpg', 'spr.JPG', '*spr.jpeg', 'spr.JPEG')):
				continue
			if any(fnmatch.fnmatch(fn, x) for x in ('*rec*.bmp', '*rec*.BMP', '*rec*.tif', '*rec*.TIF', '*rec*.jpg', '*rec*.JPG', '*rec*.jpeg', '*rec*.JPEG' )):
				files.append(os.path.join(self.in_dir, fn))
		return(tuple(files [0::skip]), files)


	def convertDistFromEdgesToXYWH(self, distances):
		'''
		Convert distances from sides(which comes from auto detection) sides into x,y,w,h
		PIL uses actual coords not width height
		'''
		w = distances[2] - self.imdims[0]
		h = distances[3] - self.imdims[1]
		return((distances[0], distances[1], w, h))


	def convertXYWH_ToCoords(self, xywh):
		'''
		The input dimensions from the GUI needs converting for PIL
		'''
		x1 = xywh[0] + xywh[2]
		y1 = xywh[1] + xywh[3]
		return((xywh[0], xywh[1], x1, y1))


def terminate():
	print("terminate")
	global cropper_pids
	global shared_terminate
 	for pid in cropper_pids:
 		os.kill(int(pid), signal.SIGQUIT)
	shared_terminate.value = 1





def reset():
	# Global value needs to be reset before next processing task on the list
	global shared_terminate
	shared_terminate.value = 0


def dummy_callback(msg):
	'''use for cli running'''
	print(msg)

def dummy_finishedCallback(msg):
	'''use for cli running'''
	print(msg)

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
	ac = Autocrop(args.in_dir, args.out_dir, dummy_callback, dummy_finishedCallback, def_crop=args.def_crop)
	ac.run()


if __name__ == '__main__':
	freeze_support()
	cli_run()
