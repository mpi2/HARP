#!/usr/bin/env python

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
import shutil
import cv2
from guppy import hpy
from scipy.stats import nanmean as mean


class Resampler(object):
    def __init__(self, img_path_list):
        """

        :param img_path_list:
        :param scalefactor: int, the shrink factor
        :return:
        """
        self.img_path_list = sorted(img_path_list)
        self.scaled_vols_dir = self.mkdir_force('scaled_volumes')



    def scale_by_integer_factor(self, scale_factor):

        self.yscaled_dir = self.mkdir_force('y_scaled')

        self.bin_shrink(scale_factor) # This works
        #self.scale_z(scale_factor)

    def scale_by_pixel_size(self, input_voxel_size, output_voxel_size):
        self.INPUT_VOXEL_SIZE = input_voxel_size
        self.OUTPUT_VOXEL_SIZE = output_voxel_size


        #self.memory_map()
        #self.shrink_memmap()
        #self.shrink_memmap()
        self.map_coordinates()
        return
        # Try the memory map



        #TEMP_CHUNKS_DIR = 'tempChunks_delete'

        print('scaling to voxel size')

        # Save the interpolated chunks here
        shrunk_chunks = []


        #find the smallest remainder when divided by these numbers. Use that number to chop up the z-slices into chunks
        # If can't divid fully, if it's a prime for eg, we just ommit one of the bottom slices

        voxel_scale_factor = float(self.INPUT_VOXEL_SIZE / self.OUTPUT_VOXEL_SIZE)

        chunksize = len(self.img_path_list) // NUM_CHUCKS
        last_chunk_size = len(self.img_path_list) % NUM_CHUCKS

        chunk_number = 0
        for i in range(chunksize, len(self.img_path_list) + chunksize, chunksize):
            
            images_to_read = self.img_path_list[chunk_end - divisor: chunk_end]
            img_chunk = self.get_array_from_image_file(sitk.ReadImage(images_to_read))
            arr_chunk = sitk.GetArrayFromImage(img_chunk)
            interpolated_arr_chunk = scipy.ndimage.zoom(arr_chunk, voxel_scale_factor, order=3)
            interpolated_img_chunk = sitk.GetImageFromArray(interpolated_arr_chunk)
            outname = os.path.join(TEMP_CHUNKS_DIR, str(chunk_number) + '.tif')

            sitk.WriteImage(interpolated_img_chunk, outname)
            chunk_number += 1

        self.stitch_chunks(TEMP_CHUNKS_DIR)


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

    def map_coordinates(self):
        """
        Unfinished. But does not produce satisfactory results as it's very very slow (5s /pixel) and uses loads of RAM
        1.2GB for 150mb  for 150MB stack
        :return:
        """
        dims = (824, 514, 362)
        scale_factor = 2
        new_dimensions = tuple(x//scale_factor for x in dims)
        raw_file = '/home/neil/work/harp_test_data/out/tempMemapDelete.raw'
        #mapped_array = np.memmap(raw_file, dtype=np.uint8, mode='r', shape=dims)
        mapped_array = np.fromfile(raw_file, dtype=np.uint8).reshape(dims)
        print mapped_array.max()
        print mapped_array.min()
        print mapped_array.dtype
        #return



        new_array = np.zeros(new_dimensions, dtype=np.uint8)
        count = 0
        for z in range(len(mapped_array[0])):
            # Get the coordinates to interpolate for this z slice
            x_array = np.linspace(1.0/scale_factor, dims[2] - (1.0/scale_factor), dims[2]/scale_factor)
            y_array = np.linspace(1.0/scale_factor, dims[1] - (1.0/scale_factor), dims[1]/scale_factor)
            #x1, y1 = np.meshgrid(x_array, y_array)

            coords = []
            for y in y_array:
                for x in x_array:
                    count += 1
                    coords.append((z, y, x))
                coords = zip(*coords)

                interpolated_voxel = scipy.ndimage.interpolation.map_coordinates(mapped_array, coords)
                print interpolated_voxel
                #print interpolated_voxel
                #new_array[0, 0, 0] = int(interpolated_voxel[0])
        # img_out = sitk.GetImageFromArray(new_array)
        # sitk.WriteImage(img_out, 'interolated.nrrd')








    def memory_map(self):
        """
        Save the slices as a raw file so it can be memory-mapped by numpy
        :return:
        """

        temp_memmap = 'tempMemapDelete.raw'
        if os.path.isfile(temp_memmap):
            os.remove(temp_memmap)

        with open(temp_memmap, 'a') as fh:
            for a in self.array_generator(self.img_path_list):
                a.tofile(fh)


    def array_generator(self, file_list):
        for impath in file_list:
            array = cv2.imread(impath, cv2.CV_LOAD_IMAGE_GRAYSCALE)
            yield array

    def stitch_chunks(self, temp_chunks_dir):
        chunk_list = Resampler.get_img_paths(temp_chunks_dir)
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


    def get_chunk_size(self):
        smallest_chunk_size = 'first'
        divisor = None

        for i in range(50, 100):
            test = len(self.img_path_list) % i
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
        img_list = Resampler.get_img_paths(img_dir)
        # Sitk reads a list of images and creates a stack
        img_3d = sitk.ReadImage(img_list)
        #The origin and spacing is changed sometimes. Reset it. We could set this baed on recon log pixel size?
        img_3d.SetSpacing((1, 1, 1))
        img_3d.SetOrigin((0, 0, 0))
        sitk.WriteImage(img_3d, fname)

    def get_array_from_image_file(self, img_path):
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

    @staticmethod
    def get_img_paths(folder):
        """
        Returns a sorted list of image files found in the gien directory
        :param folder: str
        :return: list of image file paths
        """
        extensions = ('.tiff', '.tif', '.bmp')
        return sorted([os.path.join(folder, x) for x in os.listdir(folder) if x.lower().endswith(extensions)])

    def mkdir_force(self, path):

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
        args = parser.parse_args()

        img_list = Resampler.get_img_paths(args.input_dir)
        resampler = Resampler(img_list)

        if args.scale_factor:
            resampler.scale_by_integer_factor(int(args.scale_factor))
        elif args.output_voxel_size:
            resampler.scale_by_pixel_size(float(args.input_voxel_size), float(args.output_voxel_size))
