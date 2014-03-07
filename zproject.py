#!/usr/bin/python

import Image
import sys
import os
import numpy as np
from multiprocessing import Pool, cpu_count

class Zproject:

    def __init__(self, img_dir):
        self.img_dir = img_dir


    def run(self):

        files = []

        for fn in os.listdir(self.img_dir):
            if fn.endswith(('spr.bmp', 'spr.BMP')):
                continue
            if fn.endswith(('.bmp', '.BMP', '.tif', '.TIF')):
                files.append(os.path.join(self.img_dir, fn))
        if len(files) < 1:
            sys.exit("no image files found in" + self.img_dir)

        im = Image.open(files[0])
        self.imdims = im.size
        #make a new list by removing every second image
        files = files[0::5]

        poolsize = cpu_count()
        p = Pool(poolsize)
        chunksize = int(len(files)/poolsize) +1
        chunks = [files[i:i+chunksize]
                  for i in range(0, len(files), chunksize)]

        # this returns an array of (len(files)/chunksize, 4000, 4000)
        proc = Process(self.imdims)
        max_arrays = np.array(p.map(proc, chunks))
        maxi = np.amax(max_arrays, axis=0) #finds maximum along first axis
        img = Image.fromarray(np.uint8(maxi)) #should be of shape (4000, 4000)
        img.save("max_intensity.tif")


class Process:

    def __init__(self, imdims):
        self.imdims = imdims

    def __call__(self, chunk):
        max_ = np.zeros(self.imdims)
        for im in chunk:
            im_array = np.asarray(Image.open(im))
            max_ = np.maximum(max_, im_array)
        print "chunk done"
        return max_


if __name__ == "__main__":
    z = Zproject(sys.argv[1])
    z.run()




