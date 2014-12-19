#!/usr/bin/env python

"""
In order to try and move away from dependency on ImageJ, we will try to implement the scaling functionality using
Python/numpy
"""
from _ast import Raise

import numpy as np
import SimpleITK as sitk
import os
import scipy.ndimage
import shutil
import cv2
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

        self.bin_scale_xy_first(scale_factor)
        #self.scale_z(scale_factor)

    def scale_by_pixel_size(self, input_voxel_size, output_voxel_size):
        self.INPUT_VOXEL_SIZE = input_voxel_size
        self.OUTPUT_VOXEL_SIZE = output_voxel_size

        TEMP_CHUNKS_DIR = 'tempChunks_delete'
        NUM_CHUCKS = 15

        if os.path.isdir(TEMP_CHUNKS_DIR):
            shutil.rmtree(TEMP_CHUNKS_DIR)
        os.mkdir(TEMP_CHUNKS_DIR)

        print('scaling to voxel size')
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

        return smallest_chunk_size, divisor



    def bin_scale_xy_first(self, scale_factor):

        out_path = os.path.join(self.scaled_vols_dir, "{}.nrrd".format(scale_factor))
        print('doing xy-scaling')
        first_chunk = True
        last_img_index = 0
        z_chuncks = []

        first = True
        for img_p in self.img_path_list:
            array = cv2.imread(img_p, cv2.CV_LOAD_IMAGE_GRAYSCALE)
            img = sitk.GetImageFromArray(array)
            array =  sitk.GetArrayFromImage(sitk.BinShrink(img, (scale_factor, scale_factor)))
            if first:
                assembled = array
                first = False
            else:
                assembled = np.dstack((assembled, array))






        #Write the image
        imgout = sitk.GetImageFromArray(assembled)
        sitk.WriteImage(imgout, out_path)



    def bin_scale(self, scale_factor):
        """
        Read in slices one at a time, scale in the XY dimesions. Save to a temporary directory
        :return: xy_dir
        """
        print('doing xyz avergae scaling')

        first = True
        last_img_index = 0
        for i in range(scale_factor, len(self.img_path_list) + scale_factor, scale_factor):

            # Get the slices for the subsampling
            img_paths = self.img_path_list[last_img_index:i]

            last_img_index = i

            img_chunk = sitk.ReadImage(img_paths)

            # Now we need to determine whether we need to pad in order for the BinShrink filter tow work correctly
            lower_pad_values = [p % scale_factor for p in img_chunk.GetSize()]

            if lower_pad_values != (0, 0, 0):
                # Zero pad lower dimensions so that they are all divisible by scale factor. Leave upper sides alone
                img_chunk = sitk.ConstantPad(img_chunk, (0, 0, 0), lower_pad_values, 0)

            shrunk_chunk = sitk.BinShrink(img_chunk, (scale_factor, scale_factor, scale_factor))
            if first:
                assembled_array = sitk.GetArrayFromImage(shrunk_chunk)
                first = False
            else:
                assembled_array = np.vstack((assembled_array, sitk.GetArrayFromImage(shrunk_chunk)))

        # Writeout the final image
        sitk.WriteImage(sitk.GetImageFromArray(assembled_array),
                        os.path.join(self.scaled_vols_dir, "{}.nrrd".format(scale_factor)))


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
        parser.add_argument('-i', '--input_folder', dest='input_dir', help='Input folder')
        parser.add_argument('-o', '--output_folder', dest='output_dir', help='Output folder')
        parser.add_argument('-sf', '--scale_factor', dest='scale_factor', help='downscaling factor (int)')
        parser.add_argument('-op', '--output_voxel_size', dest='output_voxel_size', help='downscaling voxel size (um)')
        args = parser.parse_args()

        img_list = Resampler.get_img_paths(args.input_dir)
        resampler = Resampler(img_list)

        if args.scale_factor:
            resampler.scale_by_integer_factor(int(args.scale_factor))
        elif args.output_voxel_size:
            resampler.scale_by_pixel_size(float(args.input_voxel_size), float(args.output_voxel_size))
