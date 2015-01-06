#!/usr/bin/env python
from __future__ import division

"""
In order to try and move away from dependency on ImageJ, we will try to implement the scaling functionality using
Python/numpy
"""
from _ast import Raise
from gtk.gdk import pixbuf_new_from_array
import numpy as np
import SimpleITK as sitk
import os
import scipy.ndimage
import scipy.misc
import shutil
import cv2
#from interpolator import interpolate

#from guppy import hpy
from scipy.stats import nanmean as mean

def scale_by_integer_factor(self, scale_factor):

    self.yscaled_dir = self.mkdir_force('y_scaled')

    self.bin_shrink(scale_factor) # This works
    #self.scale_z(scale_factor)


def zoom_chunks(img_path_list, input_voxel_size, output_voxel_size):

    scale = input_voxel_size / output_voxel_size
    resampled_zs = []

    temp_z = 'tempZ'
    mkdir_force(temp_z)
    resized_temp_file_list = []
    temp_raw = 'tempXYscaled.raw'

    #Resample z slices
    for img_path in img_path_list:
        # Rescale the z slices
        z_slice_arr = cv2.imread(img_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        z_slice_resized = cv2.resize(z_slice_arr, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        #resampled_zs.append(z_slice_resized)
        img_out_name = os.path.join(temp_z, os.path.basename(img_path))
        cv2.imwrite( img_out_name, z_slice_resized)
        resized_temp_file_list.append(img_out_name)

    #create memory mapped version of the temporary slices
    memmap = get_memmap(resized_temp_file_list, temp_raw)

    # Resample xz at y
    #temp_arr = np.array(resampled_zs)
    final_scaled_slices = []

    for y in range(memmap.shape[1]):
        xz_plane = memmap[:, y, :]
        scaled_xz = cv2.resize(xz_plane, (0, 0), fx=1, fy=scale, interpolation=cv2.INTER_AREA)
        final_scaled_slices.append(scaled_xz)

    final_array = np.array(final_scaled_slices)

    img = sitk.GetImageFromArray(np.swapaxes(final_array, 0, 1))  # Convert from yzx to zyx
    sitk.WriteImage(img, 'scaled_by_pixel.nrrd')


def get_memmap(img_path_list, raw_name):
    """
    Save the slices as a raw file so it can be memory-mapped by numpy
    :return:
    """

    if os.path.isfile(raw_name):
        os.remove(raw_name)

    dims = [len(img_path_list)]
    first = cv2.imread(img_path_list[0], cv2.CV_LOAD_IMAGE_GRAYSCALE)
    dims.extend(first.shape)

    with open(raw_name, 'a') as fh:
        for a in array_generator(img_path_list):
            a.tofile(fh)

    print dims
    mapped_array = np.memmap(raw_name, dtype=np.uint8, mode='r', shape=tuple(dims))
    return mapped_array


def scale_by_pixel_size(img_path_list, input_voxel_size, output_voxel_size, use_c):

    scaled_vols_dir = mkdir_force('scaled_volumes')
    zoom_chunks(img_path_list, input_voxel_size, output_voxel_size)



def shrink_memmap(self):
    """
    Creates a memory-mapped array from a raw file, and performs scaling on this using scipy zoom.#
    However it seems to take up just as musch memory as when the array is in memory. -> Around 1,3GB for 150mb stack
    :return:
    """

    dims = (824, 514, 362)
    #dims = (329, 205, 144)

    raw_file = '/home/neil/work/harp_test_data/out/tempMemapDelete.raw'
    #mapped_array = np.memmap(raw_file, dtype=np.uint8, mode='r', shape=dims)
    mapped_array = np.fromfile(raw_file, dtype=np.uint8).reshape(dims)

    shrunk = scipy.ndimage.zoom(mapped_array, 0.2, order=1)
    # h = hpy()
    # heap = h.heap()
    # import pdb; pdb.set_trace()
    print shrunk.shape, shrunk.dtype, type(shrunk)
    sh_img = sitk.GetImageFromArray(shrunk)

    sitk.WriteImage(sh_img, '/home/neil/work/harp_test_data/out/shrunk_test.tiff')


def map_coordinates(img_path_list,  input_voxel_size, output_voxel_size):
    """
    This works, B
    but does not produce satisfactory results as it's very very slow (5s /pixel) and uses loads of RAM
    1.2GB for 150mb  for 150MB stack
    :return:
    """
    dims = get_dimensions(img_path_list)  # !
    scale_factor = 2
    new_dimensions = tuple(x//scale_factor for x in dims)
    print new_dimensions
    raw_file = '/home/neil/work/harp_test_data/out/tempMemapDelete.raw'
    #mapped_array = np.memmap(raw_file, dtype=np.uint8, mode='r', shape=dims)
    mapped_array = np.fromfile(raw_file, dtype=np.uint8).reshape(dims)


    new_array = np.zeros(new_dimensions, dtype=np.uint8)

    z_array = np.linspace(1.0/scale_factor, dims[0] - (1.0/scale_factor), dims[0]/scale_factor)
    x_array = np.linspace(1.0/scale_factor, dims[2] - (1.0/scale_factor), dims[2]/scale_factor)
    y_array = np.linspace(1.0/scale_factor, dims[1] - (1.0/scale_factor), dims[1]/scale_factor)

    #grid = np.meshgrid(z_array, y_array, x_array, sparse=True)
    count = 0
    y_ccords = np.repeat(y_array, len(x_array)).astype(np.float32)
    x_coords = np.tile(x_array, len(y_array)).astype(np.float32)




    # Get the coordinates to interpolate for this z slice
    for i, z in enumerate(z_array):

        z_coords = np.repeat(z, (x_array.size * y_array.size)).astype(np.float16)

        interpolated_slice = scipy.ndimage.interpolation.map_coordinates(mapped_array, (z_coords, y_ccords, x_coords), order=3)

        #print 'new', interpolated_slice.size
        #print type(interpolated_slice)
        r = interpolated_slice.reshape(new_dimensions[1:3])

        #print interpolated_voxel
        new_array[i, :, :] = r
    img_out = sitk.GetImageFromArray(new_array)
    sitk.WriteImage(img_out, 'interolated.nrrd')


def get_dimensions(img_path_list):
    array = cv2.imread(img_path_list[0], cv2.CV_LOAD_IMAGE_GRAYSCALE)
    dims = (len(img_path_list), array.shape[0], array.shape[1])
    return dims


def array_generator(file_list):
    for impath in file_list:
        array = cv2.imread(impath, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        yield array


def stitch_chunks(self, temp_chunks_dir):
    chunk_list = get_img_paths(temp_chunks_dir)
    first = True
    for chunk_path in chunk_list:
        arr = self.get_array_from_image_file(chunk_path)
        if first:
            assembled = arr
            first = False
        else:
            assembled = np.vstack((assembled, arr))
            print 'stack', chunk_path
    img = sitk.GetImageFromArray(assembled)
    sitk.WriteImage(img, 'test_interpoloation.nrrd')


def get_chunk_size(img_path_list):
    smallest_chunk_size = 'first'
    divisor = None

    for i in range(50, 100):
        test = len(img_path_list) % i
        if smallest_chunk_size == 'first':
            smallest_chunk_size = test
        if test % i < smallest_chunk_size:
            smallest_chunk_size = test
            divisor = i

    print smallest_chunk_size, divisor
    return smallest_chunk_size, divisor



def bin_shrink(self, scale_factor):
    """
    Shrink the image by an integer factor. Confirmed only on even-dimension images currently. May need to add
    padding. This is working!
    :param scale_factor:
    :return:
    """

    out_path = os.path.join(self.scaled_vols_dir, "{}.nrrd".format(scale_factor))
    print('Bin shrinking')

    last_img_index = 0
    z_chuncks = []

    for i in range(scale_factor, len(self.img_path_list) + scale_factor, scale_factor):
        slice_paths = [x for x in self.img_path_list[last_img_index: i + 1]]
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
    sitk.WriteImage(imgout, out_path)


def create_volume_file(self, img_dir, fname):
    """
    Write a 3d volume given a list of 2D image
    :param img_dir: Where the input images are
    :param fname: The output filename
    :return:
    """
    print('Writing volume')
    img_list = get_img_paths(img_dir)
    # Sitk reads a list of images and creates a stack
    img_3d = sitk.ReadImage(img_list)
    #The origin and spacing is changed sometimes. Reset it. We could set this baed on recon log pixel size?
    img_3d.SetSpacing((1, 1, 1))
    img_3d.SetOrigin((0, 0, 0))
    sitk.WriteImage(img_3d, fname)

def get_array_from_image_file(img_path):
    """
    We use CV2 to read images as it's much faster than SimpleITK or PIL
    :param img_path:
    :return:
    """
    im = cv2.imread(img_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
    if im == None:
        raise IOError("CV2 Cannot read file: {}".format(img_path))
    else:
        return im


def get_img_paths(folder):
    """
    Returns a sorted list of image files found in the gien directory
    :param folder: str
    :return: list of image file paths
    """
    extensions = ('.tiff', '.tif', '.bmp')
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
        parser.add_argument('-ip', '--input_voxel_size', dest='input_voxel_size', help='Original voxel size')

        parser.add_argument('-if', '--input_folder', dest='input_dir', help='Input folder')
        parser.add_argument('-ii' '--input_image', dest='input_image', help='Input image')  # Not implemented yet
        parser.add_argument('-o', '--output_folder', dest='output_dir', help='Output folder')
        parser.add_argument('-sf', '--scale_factor', dest='scale_factor', help='downscaling factor (int)')
        parser.add_argument('-op', '--output_voxel_size', dest='output_voxel_size', type=float, help='downscaling voxel size (um)')
        parser.add_argument('-c', '--cython', dest='use_c', action='store_true')
        args = parser.parse_args()

        if args.use_c:
            use_c = True
        else:
            use_c = False

        img_list = get_img_paths(args.input_dir)
        import cProfile

        if args.scale_factor:
            scale_by_integer_factor(int(args.scale_factor))
        elif args.output_voxel_size:
            #cProfile.run('resampler.scale_by_pixel_size(float(args.input_voxel_size), float(args.output_voxel_size))')
            scale_by_pixel_size(img_list, float(args.input_voxel_size), float(args.output_voxel_size), use_c)