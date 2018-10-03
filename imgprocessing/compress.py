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

import os
from imgprocessing.io_ import Imreader
from lib import nrrd
import bz2
import tarfile
import tempfile
import orientations
import numpy as np
from skimage.io import imshow
import matplotlib.pyplot as plt

# options ={
# 'space': 'right - anterior - superior',
# 'space directions': '(1,0,0) (0,1,0) (0,0,1)'
# }

# Todo
# Get correct header
# Add appropriate flips

def bz2_nnrd(img_list, outfile, scan_name, update, center=None):
    """
    """
    reader = Imreader(img_list)
    print '++++==== bzp'
    tempnrrd = tempfile.TemporaryFile(mode="wb+")

    compressor = bz2.BZ2Compressor()

    first = True
    for i, f in enumerate(img_list):

        if i % 20 == 0:
            done = int((50.0 / len(img_list)) * i)
            update.emit('{} {}%'.format(scan_name, done))

        img_arr = reader.imread(f)
        img_arr = orientations.orient_slice_for_impc(img_arr, center, i)

        if first:
            shape = [img_arr.shape[1], img_arr.shape[0], len(img_list)]
            nrrd.write_nrrd_header(tempnrrd, shape, img_arr.dtype, 3, options=orientations.RAS_HEADER_OPTIONS)
            first = False

        rawdata = img_arr.T.tostring(order='F')
        tempnrrd.write(rawdata)

    BLOCK_SIZE = 52428800 # Around 20 MB in memory at one time
    # TODO: Check its smaller than image size
    compressed_name = outfile + '.bz2'

    file_size = os.fstat(tempnrrd.fileno()).st_size
    tempnrrd.seek(0)
    bytes_read = 0

    with open(compressed_name, 'wb') as fh_w:
        while True:
            block = tempnrrd.read(BLOCK_SIZE)
            bytes_read += BLOCK_SIZE
            done = int(50 + (50.0 / file_size) * bytes_read)
            if done >= 100: # The getsize might not be accurate?
                done = 99
            update.emit('{} {}%'.format(scan_name, done))

            if not block:
                break

            compressed = compressor.compress(block)

            if compressed:

                try:
                    fh_w.write(compressed)
                except IOError:
                    update.emit("Error in compression - job terminated")
                    print('failed to write bzp chunk')
                    return

        # Send any data being buffered by the compressor
        remaining = compressor.flush()
        while remaining:
            to_send = remaining[:BLOCK_SIZE]
            remaining = remaining[BLOCK_SIZE:]

            fh_w.write(to_send)


def bz2_dir(dir_, outfile, update, update_name, terminate):

    tar = tarfile.open(outfile + '.tar.bz2', mode='w:bz2')
    file_names = os.listdir(dir_)
    toadd = [os.path.join(dir_, x) for x in file_names]

    for i, (file_, name) in enumerate(zip(toadd, file_names)):
        if i % 5 == 0:
            if terminate.value == 1:
                return
            done = int((100.0 / len(toadd)) * i)
            update.emit("{} compression: {}%".format(update_name, done))

        tar.add(file_, arcname=name)
    tar.close()


