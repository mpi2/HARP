#!/usr/bin/python

try:
    import Image
except ImportError:
    from PIL import Image
import crop
import tempfile
import sys
import os
import numpy as np
from multiprocessing import Pool, cpu_count

class Zproject:

    def __init__(self, img_dir, out_dir):
        self.img_dir = img_dir
        self.out_dir = out_dir

    def run(self,tmp_dir):
        '''
        Run the Zprojection
        @return img, PIL Image on success
        @return string with error message
        '''
        files = []

        for fn in os.listdir(self.img_dir):
            if fn.endswith(('spr.bmp', 'spr.BMP')):
                continue
            if fn.endswith(('.bmp', '.BMP', '.tif', '.TIF')):
                files.append(os.path.join(self.img_dir, fn))
        if len(files) < 1:
            return("no image files found in" + self.img_dir)

        im = Image.open(files[0])
        self.imdims = (im.size[1], im.size[0])

        #make a new list by removing every second image
        files = files[0::5]

        poolsize = cpu_count()
        p = Pool(poolsize)
        chunksize = int(len(files)/poolsize) +1
        #print "chunk {0}".format(chunksize)
        chunks = [files[i:i+chunksize]
                  for i in range(0, len(files), chunksize)]

        # this returns an array of (len(files)/chunksize, 4000, 4000)
        proc = Process(self.imdims)
        max_arrays = np.array(p.map(proc, chunks))
        maxi = np.amax(max_arrays, axis=0) #finds maximum along first axis
        img = Image.fromarray(np.uint8(maxi))

        #something wrong with image creation
        if img.size == (0.0,0.0):

            return("something went wrong creating the Z-projection from {}".format(self.img_dir))
        else:
            #img.save(os.path.join(str(self.out_dir), "z_projection", "max_intensity_z.tif"))

            # Save th file to the temp directors tmp_dir
            img.save(os.path.join(tmp_dir, "max_intensity_z.tif"))


            return(0)


class Process:

    def __init__(self, imdims):
        self.imdims = imdims

    def __call__(self, chunk):
        max_ = np.zeros(self.imdims)
        #print "imdims: ", self.imdims

        for im in chunk:
            #Numpy is flipping the coordinates around. WTF!. So T is for transpose
            im_array = np.asarray(Image.open(im))
            #print "im: ", im_array.shape
            max_ = np.maximum(max_, im_array)
        #print "chunk done"
        return max_


if __name__ == "__main__":
    z = Zproject(sys.argv[1],sys.argv[2])
    zp_img = z.run()
    #assert zp_img.__class__ == "Image.Image"
    try:
        zp_img.save(os.path.join(str(z.out_dir), "z_projection", "max_intensity_z.tif"))

    except IOError as e:
        print("cannot save the z-projection: {0}".format(e))





