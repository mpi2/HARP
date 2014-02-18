#!/usr/bin/python

import Image
import argparse
import sys
import os
import fnmatch
import numpy as np
from numpy.core.fromnumeric import mean
from multiprocessing import Pool
import re
#from matplotlib import pyplot as plt

imdims = None

class Processor:
    '''Processes each image file individually
    Implements __call__() so it can be used in multithreading by '''

    def __init__(self, threshold):
        self.threshold = threshold

    def __call__(self, filename):
        '''
        @param: filname path of an image to process
        @returns: tuple of bounding box coords

        Reads image into array. Flips it around each time
        with column/row of interest as the top top row
        '''
        im = Image.open(filename)
        matrix = np.array(im)

        tcrop = self.search_threshold(matrix)
        lcrop = self.search_threshold(matrix.T)
        bcrop = self.search_threshold(np.flipud(matrix))
        rcrop = self.search_threshold(np.flipud(matrix.T))

        return((lcrop, tcrop, rcrop, bcrop))


    def search_threshold(self, matrix):
        '''
        @param matrix 2D numpy array
        @return int column number where average intensity > threshold
        '''

        for i, col in enumerate(matrix):
            if mean(col) > self.threshold:
                #add the column index that is over the threshold
                return i
        #for now just return a big number
        return 100000



def do_the_crop(images, crop_vals, out_dir):
    '''
    @param: images list of image files
    @param: crop_vals tuple of the crop box coords
    @param: out_dir str dir to output cropped images

    '''
    print("doing the crop")
    global imdims
    #Get the crop values. Add a padding of 10 pixels
    lcrop = crop_vals[0] - 10
    if lcrop < 0: lcrop = 0
    tcrop = crop_vals[1] - 10
    if tcrop < 0: tcrop = 0
    rcrop = imdims[0] - crop_vals[2] + 10
    if rcrop > imdims[0] -1: rcrop = imdims[0] -1
    bcrop = imdims[1] - crop_vals[3] + 10
    if bcrop > imdims[1] -1: bcrop = imdims[1] -1
    print("cropping with the following box: left:{0}, top:{1}, right:{2}, bottom{3}".format(
        lcrop, tcrop, rcrop, bcrop))
    #Crop and save
    for img in images:
        im = Image.open(img)
        im = im.crop((lcrop, tcrop, rcrop, bcrop))
        filename = os.path.basename(img)
        crop_out = os.path.join(out_dir,filename)
        im.save(crop_out)


def main():
    parser = argparse.ArgumentParser(description='crop a stack of bitmaps')
    parser.add_argument('-i', dest='in_dir', help='dir with bmps to crop', required=True)
    parser.add_argument('-o', dest='out_dir', help='destination for cropped images', required=True)
    parser.add_argument('-t', dest='file_type', help='tif or bmp', default="bmp", required=True)
    parser.add_argument('-d', nargs=4, type=int, dest='def_crop', help='set defined boundaries for crop')
    args = parser.parse_args()


    #Get the file list exclude ones we dont want
    #Note fnmatch is case insensitive by default so with fnd BMP and bmp
    files = []

    for fn in os.listdir(args.in_dir):
        if fnmatch.fnmatch(fn, '*spr.bmp'):
            continue
        if fnmatch.fnmatch(fn, '*.BMP'):
            files.append(fn)
    if len(files) < 1:
        sys.exit("no image files found in" + args.in_dir)

    #get image dimensions from first file
    img = Image.open(files[0])
    global imdims
    imdims = img.size

    if args.def_crop:
        do_the_crop(files, args.def_crop, args.out_dir)
    else: #Do the autocrop
        print("No region specified. Trying autocrop")
        threshold = 6
        proc = Processor(threshold)
        pool = Pool()
        potential_crops = pool.map(proc, files)
        crop = map(min, zip(*potential_crops))
        do_the_crop(files, crop, args.out_dir)

if __name__ == '__main__':
    main()