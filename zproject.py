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
import re
from multiprocessing import Pool, cpu_count, Value
from multiprocessing.pool import ThreadPool
import threading
import Queue
import cv2


class Zproject:

    def __init__(self, img_dir, out_dir, callback):
        self.img_dir = img_dir
        self.out_dir = out_dir
        self.shared_z_count = Value("i", 0)
        self.callback = callback
        self.im_array_queue = Queue.Queue(maxsize=20)
        self.maxintensity_queue = Queue.Queue()

    def run(self):
        '''
        Run the Zprojection
        @return img, PIL Image on success
        @return string with error message
        '''
        files = []

        for fn in os.listdir(self.img_dir):
            if fn.endswith(('spr.bmp', 'spr.BMP','spr.tif','spr.TIF','spr.jpg','spr.JPG','spr.jpeg','spr.JPEG')):
                continue
            if fn.endswith(('.bmp', '.BMP', '.tif', '.TIF','.jpg','.JPG','jpeg','JPEG')):
                prog = re.compile("rec")
                if prog.search(fn):
                    files.append(os.path.join(self.img_dir, fn))
        if len(files) < 1:
            return("no image files found in" + self.img_dir)

        im = Image.open(files[0])
        self.imdims = (im.size[1], im.size[0])

        #make a new list by removing every nth image
        self.skip_num = 10
        self.files = files[0::self.skip_num]

        #Start the file reader
        read_thread = threading.Thread(target=self.fileReader)
        read_thread.setDaemon(True)
        read_thread.start()

        #Start the thread to determine max intensities
        max_threads = []
        self.num_max_threads = 2
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
        maxi = reduce(np.maximum, max_arrays)

        img = Image.fromarray(np.uint8(maxi))
        #something wrong with image creation
        if img.size == (0.0,0.0):
            return("something went wrong creating the Z-projection from {}".format(self.img_dir))
        else:
            img.save(os.path.join(self.out_dir, "max_intensity_z.tif"))
            return(0)

    def fileReader(self):
        for file_ in self.files:
            #im = PythonMagick.Image(file_)
            im_array = cv2.imread(file_, cv2.CV_LOAD_IMAGE_GRAYSCALE)
            self.shared_z_count.value += (1 * self.skip_num)
            #im_array = np.asarray(Image.open(file_))
            self.im_array_queue.put(im_array)
        #Insert sentinels to signal end of list
        for i in range(self.num_max_threads):
            self.im_array_queue.put(None)


    def maxFinder(self):
        max_ = np.zeros(self.imdims)
        while True:
            try:
                print(self.im_array_queue.qsize())
                im_array = self.im_array_queue.get(block=True)
                #print("write queue size:", self.write_file_queue.qsize())
            except Queue.Empty:
                pass
            else:
                self.im_array_queue.task_done()
                if im_array == None:
                    break
                max_ = np.maximum(max_, im_array[:][:])
                if self.shared_z_count.value % 10 == 0:
                    self.callback("Z project: {0} images".format(str(self.shared_z_count.value)))
                #self.maxintensity_queue.put(max_)

        self.maxintensity_queue.put(max_)
        return


def dummyCallBack(msg):
    print(msg)


if __name__ == "__main__":
    z = Zproject(sys.argv[1],sys.argv[2], dummyCallBack)
    zp_img = z.run()





