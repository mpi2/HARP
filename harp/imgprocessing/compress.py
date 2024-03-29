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
from datetime import datetime
from collections import OrderedDict

import bz2
import tarfile
import numpy as np

from harp.imgprocessing.io_ import Imreader
from nrrd.writer import _TYPEMAP_NUMPY2NRRD, _NUMPY2NRRD_ENDIAN_MAP, _NRRD_FIELD_ORDER, _format_field_value
from nrrd.reader import _get_field_type
from harp import version
from harp.imgprocessing import orientations

def bz2_nnrd(img_list, outfile, scan_name, update, center=''):
    """
    Given a list of 2D image paths create nrrd in a temp file and then write this to a bz2 compressed nrrd.
    """
    reader = Imreader(img_list)
    first_image = reader.imread(img_list[0])
    shape = list(first_image.shape)
    shape = [shape[1], shape[0]]

    if center.lower() == 'tcp':
        # The X and Y are determined from the dimensions of a Z slice
        # TCP data is on it's side so we need to reverese these shape dimensions
        shape.reverse()

    shape.append(len(img_list))

    compressor = bz2.BZ2Compressor()
    compressed_name = outfile + '.bz2'

    with open(compressed_name, 'wb') as fh_w:

        header_str = nrrd_header_from_dict(shape, first_image.dtype, 3, header=orientations.RAS_HEADER_OPTIONS)
        fh_w.write(compressor.compress(header_str))

        print(center)

        for i, f in enumerate(img_list):

            if i % 20 == 0:
                done = int((100.0 / len(img_list)) * i)
                update.emit('{} {}%'.format(scan_name, done))

            img_arr = reader.imread(f)

            if center.lower() == 'tcp':
                img_arr = np.rot90(img_arr, k=3)
                img_arr = np.fliplr(img_arr)

            elif center.lower() == 'ucd':
                img_arr = np.rot90(img_arr, k=2)

            elif center.lower() == 'ccp':
                pass # No flip needed for compressor

            else: # Get the rest ofthe data into RAS format
                img_arr = np.fliplr(img_arr)

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


def nrrd_header_from_dict(shape, npdtype, ndim=3, header={}) -> str:
    """
    Adaptred from nrrd.write() and keeping only the bits needed in order to create a ascii-encoded byte string
    header for using in the compressed nrrds
    """

    # Infer a number of fields from the NumPy array and overwrite values in the header dictionary.
    # Get type string identifier from the NumPy datatype
    header['type'] = _TYPEMAP_NUMPY2NRRD[npdtype.str[1:]]

    # If the datatype contains more than one byte and the encoding is not ASCII, then set the endian header value
    # based on the datatype's endianness. Otherwise, delete the endian field from the header if present
    if npdtype.itemsize > 1 and header.get('encoding', '').lower() not in ['ascii', 'text', 'txt']:
        header['endian'] = _NUMPY2NRRD_ENDIAN_MAP[npdtype.str[:1]]


    # If space is specified in the header, then space dimension can not. See
    # http://teem.sourceforge.net/nrrd/format.html#space
    if 'space' in header.keys() and 'space dimension' in header.keys():
        del header['space dimension']

    # Update the dimension and sizes fields in the header based on the data. Since NRRD expects meta data to be in
    # Fortran order we are required to reverse the shape in the case of the array being in C order. E.g., data was read
    # using index_order='C'.
    header['dimension'] = ndim
    header['sizes'] = list(shape)

    # The default encoding is 'gzip'
    #if 'encoding' not in header:
    # force RAW for embryo preprocessing
    header['encoding'] = 'raw'

    header_str = ('NRRD0005\n'
                 '# This NRRD file was generated by HARP with the help of pynrrd\n'
                 '# on ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + '(GMT).\n'
                 f'# harp: version={version.__version__}\n'                                                        
                 '# Complete NRRD file format specification at:\n'
                 '# http://teem.sourceforge.net/nrrd/format.html\n')

    # Copy the options since dictionaries are mutable when passed as an argument
    # Thus, to prevent changes to the actual options, a copy is made
    # Empty ordered_options list is made (will be converted into dictionary)
    local_options = header.copy()
    ordered_options = []

    # Loop through field order and add the key/value if present
    # Remove the key/value from the local options so that we know not to add it again
    for field in _NRRD_FIELD_ORDER:
        if field in local_options:
            ordered_options.append((field, local_options[field]))
            del local_options[field]

    # Leftover items are assumed to be the custom field/value options
    # So get current size and any items past this index will be a custom value
    custom_field_start_index = len(ordered_options)

    # Add the leftover items to the end of the list and convert the options into a dictionary
    ordered_options.extend(local_options.items())
    ordered_options = OrderedDict(ordered_options)

    for x, (field, value) in enumerate(ordered_options.items()):
        # Get the field_type based on field and then get corresponding
        # value as a str using _format_field_value
        field_type = _get_field_type(field, header)
        value_str = _format_field_value(value, field_type)

        # Custom fields are written as key/value pairs with a := instead of : delimeter
        if x >= custom_field_start_index:
            header_str += ('%s:=%s\n' % (field, value_str))
        else:
            header_str += ('%s: %s\n' % (field, value_str))

    # Write the closing extra newline
    header_str += '\n'

    return header_str.encode('ascii')

if __name__ == '__main__':

    bz2_nnrd()
