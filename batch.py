#!/usr/bin/python
from argparse import ArgumentParser
from os import listdir, mkdir
from os.path import isdir, join, isfile, basename, splitext
from imgprocessing.resampler import resample
from imgprocessing.compress import bz2_nnrd
from appdata import AppData
from autofill import Autofill
import csv


SCALING = {'E9.5': None, 'E14.5': (2, 14.0), 'E18.5': (28.0, 56.0)}
ext = 'nrrd'


def batch(recon_list):

    app = AppData()
    auto = Autofill(None)
    update = FakeUpdate()

    for recon_path in recon_list:

        recon_name = basename(recon_path)
        stage = get_stage(recon_name)

        # Cropping
        cropped_dir = join(recon_path, 'cropped')
        scaled_dir = join(recon_path, 'scaled_stacks')

        if not isdir(cropped_dir):
            # DO THE CROP
            pass

        # Get recon log and pixel size
        img_list = app.getfilelist(cropped_dir)
        log_paths = [f for f in listdir(cropped_dir) if f.endswith("_rec.log")]
        log = join(cropped_dir, log_paths[0])

        with open(log, 'rb') as log_file:
            original_pixel_size = float(auto.get_pixel(stage, log_file))

        # Scaling
        if not isdir(scaled_dir):
            mkdir(scaled_dir)

        for scale in SCALING[stage]:

            if type(scale) is int:
                sf = scale
                new_pixel_size = original_pixel_size * float(scale)

            else:
                sf = float(scale) / float(original_pixel_size)
                new_pixel_size = sf * original_pixel_size

            out_name = join(scaled_dir, '{}_scaled_{}_pixel_{:.2f}.{}'.format(recon_name, sf, new_pixel_size, ext))

            if scaled_stack_exists(scaled_dir, new_pixel_size):
                continue

            resample(img_list, sf, out_name, False, update)

        # Compression
        bz2_file = join(recon_path, 'IMPC_cropped_{}.nrrd'.format(recon_name))
        if not isfile(bz2_file + '.bz2'):

            print "Generating missing bz2 file for '{}'".format(recon_name)
            bz2_nnrd(img_list, bz2_file, 'Compressing cropped recon', update)


def get_stage(recon_name):

    for s in SCALING.keys():
        if s in recon_name:
            return s


def scaled_stack_exists(folder, pixel_size):

    for im_path in listdir(folder):

        if splitext(im_path)[1] != 'nrrd':
            continue

        split_path = im_path.split('_')
        pixel_index = split_path.index('pixel') + 1
        im_pixel = float(split_path[pixel_index])

        if abs(im_pixel - pixel_size) < 0.1:
            return True

    return False


class FakeUpdate(object):

    def emit(self, str_):
        print str_

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-r', '--recons', help="CSV file of recons to process", required=True, dest='recons')
    args = parser.parse_args()

    with open(args.recons, 'rb') as f:
        recons = [row[0] for row in csv.reader(f)]

    batch(recons)
