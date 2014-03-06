#!/usr/bin/python

import Image
import argparse
import sys
import os
import numpy as np
from multiprocessing import Pool, cpu_count


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

#make a new list by removing every second image
files = files[0::5]
im = Image.open(files[0])
imdims = im.size

def process(chunk):

    max_ = np.zeros(imdims)
    for im in chunk:
        im_array = np.asarray(Image.open(im))
        max_ = np.maximum(max_, im_array)
    print "chunk done"
    return max_



if __name__ == '__main__':

    poolsize = cpu_count()
    p = Pool(poolsize)

    chunksize = int(len(files)/poolsize) +1
    chunks = [files[i:i+chunksize]
              for i in range(0, len(files), chunksize)]

    # this returns an array of (len(files)/chunksize, 4000, 4000)
    max_arrays = np.array(p.map(process, chunks))
    maxi = np.amax(max_arrays, axis=0) #finds maximum along first axis
    img = Image.fromarray(np.uint8(maxi)) #should be of shape (4000, 4000)
    img.save("max_intensity.tif")

