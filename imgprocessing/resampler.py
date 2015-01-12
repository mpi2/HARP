#!/usr/bin/env python
from __future__ import division

"""
Part of the HARP package.
Scale a stack of 2D images.
For an integer factor, use SimpleITK's binshrink.
For an arbitrary voxel output size we scale in XY and then in XY using opencv.resize with interpolation

For scaling to an arbitray pixel value, a memory-mapped numpy array is created, which needs a raw file creating that
resides on disk during processing. This will take up (volume size / scale factor)
"""

import numpy as np
import SimpleITK as sitk
import os
import shutil
import cv2
import collections#
import lib.nrrd as nrrd
import sys


def resample(images, scale, outpath, scaleby_int):
    """
    :param images: iterable or a directory
    :param scale: int. Factor to scale by
    :param outpath: path including image file extension
    :param scaleby_int bool: True-> scale by binning. False-> use cv2 interpolated scaling
    :return:
    """

    temp_xy = 'tempXYscaled.raw'
    temp_xyz = 'tempXYZscaled.raw'

    #Just in case they didn't previously get deleted
    _remove_temp_files(temp_xy, temp_xyz)

    if os.path.isfile(temp_xy):
        os.remove(temp_xy)

    if os.path.isfile(temp_xyz):
        os.remove(temp_xyz)

    #Check if we have a directory with images or a list with images
    if type(images) is str:
        if os.path.isdir(images):
            img_path_list = get_img_paths(images)

    elif type(images) in [list, tuple]:
        img_path_list = images
    else:
        raise ValueError("HARP Resampler: resampler needs a direcory of images or a list of images")

    if len(img_path_list) < 1:
        raise ValueError("HARP Resampler: There are no images in the list or directory")

    #Get dimensions for the memory mapped raw xy file
    xy_scaled_dims = [len(img_path_list)]

    img_path_list = sorted(img_path_list)

    datatype = 'uint8'

    with open(temp_xy, 'ab') as xy_fh:
        first = True
        for img_path in img_path_list:

            # Rescale the z slices
            z_slice_arr = cv2.imread(img_path, cv2.CV_LOAD_IMAGE_UNCHANGED)

            # This might slow things doen by reasigning to the original array. Maybe we jsut need a differnt view on it
            if scaleby_int:
                z_slice_arr = _droppixels(z_slice_arr, scale, scale)

            z_slice_resized = cv2.resize(z_slice_arr, (0, 0), fx=1/scale, fy=1/scale, interpolation=cv2.INTER_AREA)

            if first:
                xy_scaled_dims.extend(z_slice_resized.shape)
                datatype = z_slice_resized.dtype
                first = False
            z_slice_resized.tofile(xy_fh)

    #create memory mapped version of the temporary xy scaled slices
    xy_scaled_mmap = np.memmap(temp_xy, dtype=datatype, mode='r', shape=tuple(xy_scaled_dims))

    #Get dimensions for the memory mapped raw xyz file
    xyz_scaled_dims = []
    first = True

    final_scaled_slices = []

    with open(temp_xyz, 'ab') as xyz_fh:
        for y in range(xy_scaled_mmap.shape[1]):

            xz_plane = xy_scaled_mmap[:, y, :]

            if scaleby_int:
                xz_plane = _droppixels(xz_plane, 1, scale)

            scaled_xz = cv2.resize(xz_plane, (0, 0), fx=1, fy=1/scale, interpolation=cv2.INTER_AREA)

            if first:
                first = False
                xyz_scaled_dims.append(xy_scaled_mmap.shape[1])
                xyz_scaled_dims.append(scaled_xz.shape[0])
                xyz_scaled_dims.append(scaled_xz.shape[1])

            final_scaled_slices.append(scaled_xz)
            scaled_xz.tofile(xyz_fh)

    #create memory mapped version of the temporary xy scaled slices
    xyz_scaled_mmap = np.memmap(temp_xyz, dtype=datatype, mode='r', shape=tuple(xyz_scaled_dims))

    nrrd.write(outpath, np.swapaxes(xyz_scaled_mmap.T, 1, 2))

    _remove_temp_files(temp_xy, temp_xyz)


def _remove_temp_files(file_list):
    for file_ in file_list:
        try:
            os.remove(file_)
        except OSError:
            pass


def _droppixels(a, scaley, scalex):
    """
    Make an array divisible by integar scale factors by dropping pixels from the right and bottom of the image
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
    Produces almost exactly sane output as CV2 method but seems to round 0.5 values down to 0
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
        slice_imgs = sitk.ReadImage(slice_paths)
        z_chuncks.append(sitk.BinShrink(slice_imgs, [scale_factor, scale_factor, scale_factor]))
        last_img_index = i

    first_chunk = True
    for j in z_chuncks:
        array = sitk.GetArrayFromImage(j)
        if first_chunk:
            assembled = array
            first_chunk = False
        else:
            assembled = np.vstack((assembled, array))

    #Write the image
    imgout = sitk.GetImageFromArray(assembled)
    sitk.WriteImage(imgout, outpath)



def get_dimensions(img_path_list):
    array = cv2.imread(img_path_list[0], cv2.CV_LOAD_IMAGE_UNCHANGED)
    dims = (len(img_path_list), array.shape[0], array.shape[1])
    return dims


def array_generator(file_list):
    for impath in file_list:
        array = cv2.imread(impath, cv2.CV_LOAD_IMAGE_UNCHANGED)
        yield array


def get_img_paths(folder):
    """
    Returns a sorted list of image files found in the gien directory
    :param folder: str
    :return: list of image file paths
    """
    extensions = ('.tiff', '.tif', '.bmp')
    print 'here ' + folder
    return sorted([os.path.join(folder, x) for x in os.listdir(folder) if x.lower().endswith(extensions)])

def mkdir_force(path):

    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)
    return path


if __name__ == '__main__':

    import argparse
    if __name__ == "__main__":

        parser = argparse.ArgumentParser("Image resampler (downscale)")
        parser.add_argument('-i', '--input_folder', dest='input_dir', help='Input folder')
        parser.add_argument('-o', '--output_path', dest='output_path', help='Output path')
        parser.add_argument('-sf', '--scale_factor', dest='scale_factor', type=int, help='downscaling factor (int)')
        parser.add_argument('-si', '--scale_byint', dest='scaleby_int', action='store_true', default=False)

        args = parser.parse_args()

        #scale_by_integer_factor(args.input_dir, int(args.scale_factor), args.output_path)
        resample(args.input_dir, args.scale_factor, args.output_path, args.scaleby_int)