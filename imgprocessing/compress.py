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
from imgprocessing.io import Imreader
from lib import nrrd
import bz2
import tarfile


def bz2_nnrd(img_list, outfile, scan_name, update):
    """
    Given a list of 2D image paths create nrrd in a temp file and then write this to a bz2 compressed nrrd.
    """

    reader = Imreader(img_list)
    first_image = reader.imread(img_list[0])
    shape = list(first_image.shape)
    shape = [shape[1], shape[0]]
    shape.append(len(img_list))

    compressor = bz2.BZ2Compressor()
    compressed_name = outfile + '.bz2'

    with open(compressed_name, 'wb') as fh_w:

        header_read = nrrd.GetNrrdHeader(shape, first_image.dtype, 3)
        header = header_read.header
        fh_w.write(compressor.compress(header))

        for i, f in enumerate(img_list):

            if i % 20 == 0:
                done = int((100.0 / len(img_list)) * i)
                update.emit('{} {}%'.format(scan_name, done))

            img_arr = reader.imread(f)
            rawdata = img_arr.T.tostring(order='F')
            compressed = compressor.compress(rawdata)
            fh_w.write(compressed)
        # Send any data being buffered by the compressor
        remaining = compressor.flush()
        if remaining:
            fh_w.write(remaining)

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


if __name__ == '__maim__':

    bz2_nnrd()
