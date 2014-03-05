#!/usr/bin/python

import Image
import argparse
import sys
import os
import numpy as np
import multiprocessing
import ctypes
from scipy import misc



#from matplotlib import pyplot as plt

#Once this is working, implement in C++/Qt http://qt-project.org/doc/qt-4.8/qimage.html

parser = argparse.ArgumentParser(description='get a z-projection from a stack of bitmaps')
parser.add_argument('-i', dest='in_dir', help='dir with bmps to project', required=True)

args = parser.parse_args()



files = []

for fn in os.listdir(args.in_dir):
    if fn.endswith(('spr.bmp', 'spr.BMP')):
        continue
    if fn.endswith(('.bmp', '.BMP', '.tif', '.TIF')):
        files.append(os.path.join(args.in_dir, fn))
if len(files) < 1:
    sys.exit("no image files found in" + args.in_dir)

#get dimensions from first image and create shared array for storing max values
im = Image.open(files[0])
imdims = im.size
shared_array_base = multiprocessing.Array(ctypes.c_byte, imdims[0]*imdims[1])
shared_array = np.ctypeslib.as_array(shared_array_base.get_obj())
shared_array = shared_array.reshape(imdims[0], imdims[1])



def processChunk(filelist):

    first = True
    maxi = None
    for img in filelist:
        im = Image.open(img)
        array = np.array(im)
        if first:
            maxi = array
            first = False
        maxi = np.maximum(array, maxi)
    return maxi


def process(filename):
    '''
    @param: filename path of an image to process
    @returns:

    Reads image into array. Flips it around each time
    with column/row of interest as the top top row
    '''
    im = Image.open(filename)
    matrix = np.array(im)
    max_array = np.maximum(matrix, shared_array)
    shared_array[:,:] = max_array[:,:]



if __name__ == '__main__':

    pool = multiprocessing.Pool(processes=8)
    #Chop list into chunks
    file_chunks = []
    chunk_size = 100
    ranges = range(0, len(files), chunk_size)

    for chunk_idx in ranges:
        file_chunks.append(files[chunk_idx:chunk_idx+chunk_size])

    first = True
    maxi = None
    max_arrays = pool.map(processChunk, file_chunks )
    for array in max_arrays:
        if first:
            maxi = array
            first = False
        maxi = np.maximum(array, maxi)
    img = Image.fromarray(maxi)
    img.save("max_intensity.tif")


#     pool.map(process, files)
#     img = Image.fromarray(shared_array)
#     img.show()
#     img.save("max_intensity.tif")

