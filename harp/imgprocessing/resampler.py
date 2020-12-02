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



Part of the HARP package.
Scale a stack of 2D images.
For an integer factor, use SimpleITK's binshrink.
For an arbitrary voxel output size we scale in XY and then in XY using opencv.resize with interpolation

For scaling to an arbitray pixel value, a memory-mapped numpy array is created, which needs a raw file creating that
resides on disk during processing. This will take up (volume size / scale factor)

"""

import numpy as np
from SimpleITK import ReadImage, WriteImage, BinShrink, GetImageFromArray, GetArrayFromImage
import os
import shutil
import sys
sys.path.append('..')
if sys.platform == "win32" or sys.platform == "win64":
    windows = True
else:
    windows = False
if windows:
    from harp.lib import cv2
else:
    import cv2
import harp.lib.nrrd as nrrd

from harp.imgprocessing.io_ import Imreader
from multiprocessing import Value
import tempfile
from . import orientations


def resample(images, scale, outpath, scaleby_int, update_signal, thread_terminate_flag=Value('i', 0), center=''):
    """
    :param images: iterable or a directory
    :param scale: int. Factor to scale by
    :param outpath: path including image file extension
    :param scaleby_int bool: True-> scale by binning. False-> use cv2 interpolated scaling
    :return:
    """
    temp_xy = tempfile.TemporaryFile(mode='wb+')

    temp_xyz = tempfile.TemporaryFile(mode='wb+')

    #Check if we have a directory with images or a list with images
    if type(images) is str:
        if os.path.isdir(images):
            img_path_list = get_img_paths(images)

    elif type(images) in [list, tuple]:
        img_path_list = images
    else:
        raise HarpDataError("HARP Resampler: resampler needs a direcory of images or a list of images")

    if len(img_path_list) < 1:
        raise HarpDataError("HARP Resampler: There are no images in the list or directory")

    # Get dimensions for the memory mapped raw xy file
    xy_scaled_dims = [len(img_path_list)]

    img_path_list = sorted(img_path_list)

    datatype = 'uint8'  # I think this can be deleted as it's overridden?

    first = True
    count = 0
    reader = Imreader(img_path_list)

    for img_path in img_path_list:
        print(img_path)
        count += 1
        if count % 50 == 0:
            if thread_terminate_flag.value == 1:
                return
            pcnt_done = int(((100 / len(img_path_list)) * count) / 2)
            update_signal.emit("rescaling by {}: {}% done".format(scale, pcnt_done))

        # Rescale the z slices
        z_slice_arr = reader.imread(img_path)

        # This might slow things down by reasigning to the original array. Maybe we just need a different view on it
        if scaleby_int:
            z_slice_arr = _droppixels(z_slice_arr, scale, scale)

        z_slice_resized = cv2.resize(z_slice_arr, (0, 0), fx=1/scale, fy=1/scale, interpolation=cv2.INTER_AREA)

        if center.lower() == 'tcp':
            z_slice_resized = np.rot90(z_slice_resized, k=3)

        elif center.lower() == 'ucd':
            z_slice_resized = np.rot90(z_slice_resized, k=2)
            z_slice_resized = np.fliplr(z_slice_resized)

        elif center.lower() == 'ccp':
            z_slice_resized = np.fliplr(z_slice_resized)

        if first:
            xy_scaled_dims.extend(z_slice_resized.shape)
            datatype = z_slice_resized.dtype
            first = False

        if windows:
            z_slice_resized.tofile(temp_xy.file)
        else:
            z_slice_resized.tofile(temp_xy)

    # create memory mapped version of the temporary xy scaled slices
    xy_scaled_mmap = np.memmap(temp_xy, dtype=datatype, mode='r', shape=tuple(xy_scaled_dims))

    # Get dimensions for the memory mapped raw xyz file
    xyz_scaled_dims = []
    first = True

    # Scale in x_z plane
    count = 0

    for y in range(xy_scaled_mmap.shape[1]):

        count += 1
        if count % 50 == 0:
            if thread_terminate_flag.value == 1:
                return
            pcnt_done = int(((100 / xy_scaled_mmap.shape[1]) * count) / 2) + 50
            update_signal.emit("rescaling by {}: {}% done".format(scale, pcnt_done))

        xz_plane = xy_scaled_mmap[:, y, :]

        if scaleby_int:
            xz_plane = _droppixels(xz_plane, 1, scale)

        scaled_xz = cv2.resize(xz_plane, (0, 0), fx=1, fy=1/scale, interpolation=cv2.INTER_AREA)

        if first:
            first = False
            xyz_scaled_dims.append(xy_scaled_mmap.shape[1])
            xyz_scaled_dims.append(scaled_xz.shape[0])
            xyz_scaled_dims.append(scaled_xz.shape[1])

        if windows:
            scaled_xz.tofile(temp_xyz.file)
        else:
            scaled_xz.tofile(temp_xyz)

    # create memory mapped version of the temporary xyz scaled slices
    xyz_scaled_mmap = np.memmap(temp_xyz, dtype=datatype, mode='r', shape=tuple(xyz_scaled_dims))

    ras_volume = orientations.orient_for_impc(xyz_scaled_mmap)

    nrrd.write(outpath, ras_volume, orientations.RAS_HEADER_OPTIONS)

    temp_xy.close()  # deletes temp file
    temp_xyz.close()


def _remove_temp_files(file_list):
    for file_ in file_list:
        try:
            os.remove(file_)
        except OSError:
            pass


def _droppixels(a, scaley, scalex):
    """
    Make an array divisible by integer scale factors by dropping pixels from the right and bottom of the image
    """

    #If New dimension not integral factors of original, drop pixels to make it so they are
    y1, x1 = a.shape
    changed = False

    # Get the shape of the old array after dropping pixels

    dropy = y1 % scaley
    if dropy != 0:
        y1 -= dropy
        b = a[0:-dropy]
        changed = True

    dropx = x1 % scalex
    if dropx != 0:
        x1 -= dropx
        b = a[:, 0:-dropx]
        changed = True

    if not changed:
        b = a

    return b


def _binshrink(img_dir, scale_factor, outpath):
    """
    Shrink the image by an integer factor. Confirmed only on even-dimension images currently. May need to add
    padding. This is working!
    Produces almost exactly same output as CV2 method but seems to round 0.5 values down to 0
    :param scale_factor:
    :return:
    """
    print('scaling by int')
    img_path_list = get_img_paths(img_dir)
    last_img_index = 0
    z_chuncks = []

    scale_factor = int(1/ scale_factor)

    for i in range(scale_factor, len(img_path_list) + scale_factor, scale_factor):
        slice_paths = [x for x in img_path_list[last_img_index: i + 1]]
        slice_imgs = ReadImage(slice_paths)
        z_chuncks.append(BinShrink(slice_imgs, [scale_factor, scale_factor, scale_factor]))
        last_img_index = i

    first_chunk = True
    for j in z_chuncks:
        array = GetArrayFromImage(j)
        if first_chunk:
            assembled = array
            first_chunk = False
        else:
            assembled = np.vstack((assembled, array))

    #Write the image
    imgout = GetImageFromArray(assembled)
    WriteImage(imgout, outpath)


def get_img_paths(folder):
    """
    Returns a sorted list of image files found in the gien directory
    :param folder: str
    :return: list of image file paths
    """
    extensions = ('.tiff', '.tif', '.bmp')
    print('here ' + folder)
    return sorted([os.path.join(folder, x) for x in os.listdir(folder) if x.lower().endswith(extensions)])

def mkdir_force(path):

    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)
    return path


class HarpDataError(Exception):
    """
    Raised when some of the supplied data is found to be faulty
    """
    pass


if __name__ == '__main__':

    class DummyUpdate():
        def emit(self, msg):
            print(msg)

    import argparse
    if __name__ == "__main__":

        parser = argparse.ArgumentParser("Image resampler (downscale)")
        parser.add_argument('-i', '--input_folder', dest='input_dir', help='Input folder')
        parser.add_argument('-o', '--output_path', dest='output_path', help='Output path')
        parser.add_argument('-sf', '--scale_factor', dest='scale_factor', type=int, help='downscaling factor (int)')
        parser.add_argument('-si', '--scale_byint', dest='scaleby_int', action='store_true', default=False)

        args = parser.parse_args()

        update = DummyUpdate()
        #scale_by_integer_factor(args.input_dir, int(args.scale_factor), args.output_path)
        resample(args.input_dir, args.scale_factor, args.output_path, args.scaleby_int, update)
