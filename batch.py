#!/usr/bin/python
from argparse import ArgumentParser
from os import listdir, mkdir
from os.path import isdir, join, split, isfile, basename, splitext, realpath
import csv
import strconv
from imgprocessing.resampler import resample
from imgprocessing.compress import bz2_nnrd
from imgprocessing.crop import Crop
from appdata import AppData
from autofill import Autofill
import sys


SCALING = {'E9.5': None, 'E14.5': (2, 14.0), 'E18.5': (28.0, 56.0)}
ext = 'nrrd'


def batch(recon_root, proc_recon_root, csv_path):
    """
    Script to automatically generate crops, scled images and compressed files
    :param recon_list:
    :param mount:
    :return:
    """

    with open(csv_path, 'r') as fh:
        recon_list = [row[0] for row in csv.reader(fh)]


    app = AppData()
    auto = Autofill(None)
    update = FakeUpdate()

    for recon_id in recon_list:

        stage = get_stage(recon_id)
        proc_recon_path = join(proc_recon_root, recon_id)
        cropped_dir = join(proc_recon_path, 'cropped')

        if not isdir(cropped_dir):
            mkdir(cropped_dir)

        scaled_dir = join(proc_recon_path, 'scaled_stacks')
        metadata_dir = join(proc_recon_path, 'Metadata')

        recon_id = get_input_id(join(metadata_dir, 'config4user.log'))
        recon_path = join(recon_root, recon_id)

        # Performing cropping if directory does not exist or is empty
        if len(listdir(cropped_dir)) == 0:

            fake_config = lambda: None
            fake_config.meta_path = metadata_dir
            fake_config.value = 0

            cropper = Crop(recon_path, cropped_dir, update.emit, fake_config, fake_config, app, def_crop=None, repeat_crop=None)
            img_list = cropper.run(auto=True)

        else:
            img_list = app.getfilelist(cropped_dir)

        # Get recon log and pixel size
        log_paths = [f for f in listdir(cropped_dir) if f.endswith("_rec.log")]
        if len(log_paths) < 1:
            print('Cannot find log in cropped directory for {}'.format(recon_id))
            continue
        log = join(cropped_dir, log_paths[0])

        with open(log, 'rb') as log_file:
            original_pixel_size = float(auto.get_pixel(stage, log_file))

        # Scaling
        if not isdir(scaled_dir):
            mkdir(scaled_dir)

        for scale in SCALING[stage]:

            scale_by_int = False
            if type(scale) is int:
                sf = scale
                new_pixel_size = original_pixel_size * float(scale)
                scale_by_int = True

            else:
                sf = float(scale) / float(original_pixel_size)
                new_pixel_size = sf * original_pixel_size

            out_name = join(scaled_dir, '{}_scaled_{:.4f}_pixel_{:.2f}.{}'.format(recon_id, sf, new_pixel_size, ext))

            if scaled_stack_exists(scaled_dir, sf, new_pixel_size):
                continue

            resample(img_list, sf, out_name, scale_by_int, update)

        # Compression
        bz2_file = join(proc_recon_path, 'IMPC_cropped_{}.nrrd'.format(recon_id))
        if not isfile(bz2_file + '.bz2'):

            print "Generating missing bz2 file for '{}'".format(recon_id)
            try:
                bz2_nnrd(img_list, bz2_file, 'Compressing cropped recon', update)
            except IOError as e:
                print('Failed to write the compressed bzp2 file. Network issues?\n{}'.format(e))


# def find_recon(search_path, head):
#
#     combined = []
#     while True:
#
#         head, tail = split(head)
#         combined.insert(0, tail)
#
#         combined_path = join(search_path, *combined)
#         if isdir(combined_path):
#             return combined_path


def get_stage(recon_name):

    for s in SCALING.keys():
        if s in recon_name:
            return s


def get_input_id(config_file):
    """
    Get the 
    :param config_file: 
        path to the HARP config file
    :return: 
        the id of the original recon. Rarely, it may be different than the processed recon id
    """
    with open(config_file, 'rb') as f:
        for line in f.readlines():
            split_line = line.split()
            if 'Input_folder' in split_line[0]:
                recon_path = split_line[1]
                recon_id = basename(recon_path.replace('\\', '/'))
                return recon_id

    return None


def scaled_stack_exists(folder, sf, pixel_size):

    for im_path in listdir(folder):

        im_name, im_ext = splitext(im_path)
        if im_ext not in ['.nrrd', '.tiff', '.tif']:
            continue

        split_path = im_name.split('_')

        sf_index = split_path.index('scaled') + 1
        pixel_index = split_path.index('pixel') + 1

        im_sf = strconv.convert(split_path[sf_index])
        try:
            float(im_sf)
        except ValueError:
            print("Scaled image {} has a non-deafult scaling format within its name".format(im_name))
            return False
        im_pixel = float(split_path[pixel_index])

        if abs(im_sf - sf) < 0.1 and abs(im_pixel - pixel_size) < 0.1:
            return True

    return False


class FakeUpdate(object):

    def emit(self, str_):
        print str_

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-r', '--recons', help="path to recons folder", required=True, dest='recons_path')
    parser.add_argument('-p', '--processed_recons', help="path to processed recons folder", required=True, dest='proc_recons_path')
    parser.add_argument('-c', '--csv', help="path to csv with processed_recon_name", required=True, dest='csv_path')

    args = parser.parse_args()
    batch(args.recons_path, args.proc_recons_path, args.csv_path)
