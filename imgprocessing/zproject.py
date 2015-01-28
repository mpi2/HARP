"""
Copyright 2015 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

E-mail the developers: sig@har.mrc.ac.uk

"""

from __future__ import division
import os
from PyQt4 import QtCore
import sys
import numpy as np
sys.path.append('..')
from appdata import HarpDataError
from imgprocessing.io import Imreader, imwrite



class Zproject(QtCore.QThread):

    update = QtCore.pyqtSignal(str, name='update')

    def __init__(self, imglist, zprojection_output, callback=None, force=False):
        super(Zproject, self).__init__()
        self.skip = 10
        self.imglist = imglist
        self.zprojection_output = zprojection_output
        self.skip_num = 10
        self.force = force
        if callback is None:
            self.callback = self.z_callback
        else:
            self.callback = callback

    def run(self):
        self.run_onthisthread()

    def run_onthisthread(self):
        """
        Run the Zprojection
        This is not in run, so we can bypass run() if we don't want to start a new thread
        """
        print 'zproject thread id', QtCore.QThread.currentThreadId()

        if os.path.isfile(self.zprojection_output) is False or self.force:

            print "Computing z-projection..."

            if len(self.imglist) < 1:
                self.emit(QtCore.SIGNAL('update(QString)'),  "No recon images found!")

            reader = Imreader(self.imglist)
            try:
                im = reader.imread(self.imglist[0])
            except HarpDataError as e:
                self.update.emit(e.message)  # emit back to differnt thread. or...
                raise   # reraise for autocrop, on same thread

            imdims = im.shape
            dtype = im.dtype

            # make a new list by removing every nth image
            sparse_filelist = sorted(self.imglist)[0::self.skip_num]

            print "performing z-projection on sparse file list"

            max_array = self.max_projection(sparse_filelist, imdims, dtype)
            imwrite(self.zprojection_output, max_array)

        self.emit(QtCore.SIGNAL('update(QString)'), "Z-projection finished")

    def max_projection(self, filelist, imdims, bit_depth):

        maxi = np.zeros(imdims, dtype=bit_depth)

        reader = Imreader(filelist)
        for count, file_ in enumerate(filelist):

            try:
                im_array = reader.imread(file_)
            except HarpDataError as e:
                self.update.emit(e.message)
                raise

            inds = im_array > maxi
            maxi[inds] = im_array[inds]
            status_str = "Z-project: " + str(count * 10) + "/" + str(len(self.imglist)) + " images processed"
            self.emit(QtCore.SIGNAL('update(QString)'), status_str)
            self.callback("Determining crop box ({:.1%})".format(count / len(filelist)))
        return maxi

    def z_callback(self, msg):  # this is just a dummy callback
        pass


