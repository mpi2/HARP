#!/usr/bin/env python

"""
In order to try and move away from dependency on ImageJ, we will try to implement the scaling functionality using
Python/numpy
"""

import numpy as np
import SimpleITK as sitk
import os
import scipy.ndimage
import shutil


class Rescaler(object):
    def __init__(self, img_path_list):
        """

        :param img_path_list:
        :param scalefactor: int, the shrink factor
        :return:
        """
        self.img_path_list = sorted(img_path_list)
        self.TEMP_XY_DIR = 'tempxy'
        self.YSCALED_DIR = 'y_scaled'

        if os.path.isdir(self.TEMP_XY_DIR):
            shutil.rmtree(self.TEMP_XY_DIR)
        os.mkdir(self.TEMP_XY_DIR)

        if os.path.isdir(self.YSCALED_DIR):
            shutil.rmtree(self.YSCALED_DIR)
        os.mkdir(self.YSCALED_DIR)



    def scale_by_integer_factor(self, scale_factor):
        self.SCALE_FACTOR = scale_factor
        self.scale_xy()
        self.scale_z()

    def scale_by_pixel_size(self, input_voxel_size, output_voxel_size):
        self.INPUT_VOXEL_SIZE = input_voxel_size
        self.OUTPUT_VOXEL_SIZE = output_voxel_size

        TEMP_CHUNKS_DIR = 'tempChunks_delete'

        if os.path.isdir(TEMP_CHUNKS_DIR):
            shutil.rmtree(TEMP_CHUNKS_DIR)
        os.mkdir(TEMP_CHUNKS_DIR)

        print('scaling to voxel size')
        #find the smallest remainder when divided by these numbers. Use that number to chop up the z-slices into chunks
        # If can't divid fully, if it's a prime for eg, we just ommit one of the bottom slices
        remainder, divisor = self.get_chunk_size()
        voxel_scale_factor = self.INPUT_VOXEL_SIZE / self.OUTPUT_VOXEL_SIZE

        chunk_number = 0
        for chunk_end in range(divisor, len(self.img_path_list), divisor):
            print divisor, chunk_end
            images_to_read = self.img_path_list[chunk_end - divisor: chunk_end]
            img_chunk = sitk.ReadImage(images_to_read)
            arr_chunk = sitk.GetArrayFromImage(img_chunk)
            interpolated_arr_chunk = scipy.ndimage.zoom(arr_chunk, voxel_scale_factor, order=3)
            interpolated_img_chunk = sitk.GetImageFromArray(interpolated_arr_chunk)
            outname = os.path.join(TEMP_CHUNKS_DIR, str(chunk_number) + '.tif')

            sitk.WriteImage(interpolated_img_chunk, outname)
            chunk_number += 1

        self.stitch_chunks(TEMP_CHUNKS_DIR)

    def stitch_chunks(self, temp_chunks_dir):
        chunk_list = sorted(hil.GetFilePaths(temp_chunks_dir))
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



    def scale_xy(self):
        """
        Read in slices one at a time, scale in the XY dimesions. Save to a temporary directory
        :return: xy_dir
        """
        print('doing xy-scaling')
        for unscaled_xy_slice in self.img_path_list:

            array = self.get_array_from_image_file(unscaled_xy_slice)
            scaled_array = scipy.ndimage.zoom(array, 1.0 / self.SCALE_FACTOR, order=0)
            scaled_img = sitk.GetImageFromArray(scaled_array)
            img_id = os.path.splitext(os.path.basename(unscaled_xy_slice))[0]
            outpath = os.path.join(self.TEMP_XY_DIR, "{}.tif".format(img_id))
            sitk.WriteImage(scaled_img, outpath)


    def scale_z(self):
        """
        :param: xy_scaled_dir, path to directory containing xy-scaled images
        :return:
        """

        print('doing z-scaling')

        imgpath_list = sorted(hil.GetFilePaths(self.TEMP_XY_DIR))

        last_img_index = 0
        out_count = 0  # For naming the outputs
        for i in range(self.SCALE_FACTOR, len(imgpath_list), self.SCALE_FACTOR):

            array_list = []
            for j in range(last_img_index, i):
                array_list.append(self.get_array_from_image_file(imgpath_list[j]))

            last_img_index = i

            first_array = array_list[0].astype(np.uint16)  # Needs a larger type to do the calculations
            for ar in array_list[1:]:  # Skip the first
                first_array += ar

            average_slice = (first_array / self.SCALE_FACTOR).astype(np.uint8)  # Should go back to original dtype!
            average_img = sitk.GetImageFromArray(average_slice)

            #Writeout the result
            filename_counter = '0' * (4 - (len(str(out_count)))) + str(out_count)
            sitk.WriteImage(average_img, os.path.join(self.YSCALED_DIR, filename_counter + '.tif'))
            out_count += 1


        return
        #The code below adds another slice from the reamining slices. But this will result in a non-isotropic last slice
        # So I've decided to skip that last slice for now
        #Process an extra slice if the filelist is not divisible by scalfactor
        num_remaining = len(imgpath_list) % self.SCALE_FACTOR
        if num_remaining != 0:
            remaining_files = sorted(imgpath_list[-num_remaining:])

            array_list = []
            for left_over in remaining_files:
                array_list.append(self.get_array_from_image_file(left_over))

            first_array = array_list[0].astype(np.uint16)  # Needs a larger type to do the calculations
            for ar in array_list[1:]:  # Skip the first
                first_array += ar

            average_slice = (first_array / num_remaining).astype(np.uint8)  # Should go back to original dtype!
            average_img = sitk.GetImageFromArray(average_slice)

            #Writeout the result
            filename_counter = '0' * (4 - (len(str(out_count)))) + str(out_count)
            sitk.WriteImage(average_img, os.path.join(self.YSCALED_DIR, filename_counter + '.tif'))


    def get_array_from_image_file(self, img_path):

        img = sitk.ReadImage(img_path)
        arr = sitk.GetArrayFromImage(img)
        return arr



if __name__ == '__main__':
    import harwellimglib as hil
    import argparse
    if __name__ == "__main__":

        parser = argparse.ArgumentParser("Image resampler (downscale)")
        parser.add_argument('-ip', '--input_voxel_size', dest='input_voxel_size', help='Original voxel size')
        parser.add_argument('-i', '--input_folder', dest='input_dir', help='Input folder')
        parser.add_argument('-o', '--output_folder', dest='output_dir', help='Output folder')
        parser.add_argument('-sf', '--scale_factor', dest='scale_factor', help='downscaling factor (int)')
        parser.add_argument('-op', '--output_voxel_size', dest='output_voxel_size', help='downscaling voxel size (um)')
        args = parser.parse_args()

        img_list = hil.GetFilePaths(args.input_dir)

        rescaler = Rescaler(img_list)

        if args.scale_factor:
            rescaler.scale_by_integer_factor(int(args.scale_factor))
        elif args.output_voxel_size:
            rescaler.scale_by_pixel_size(float(args.input_voxel_size), float(args.output_voxel_size))