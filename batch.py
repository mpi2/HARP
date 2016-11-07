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


SCALING = {'E9.5': None, 'E14.5': (2, 14.0), 'E18.5': (28.0, 56.0)}
ext = 'nrrd'


def batch(recon_list, mount=None):

    app = AppData()
    auto = Autofill(None)
    update = FakeUpdate()

    for recon_path in recon_list:

        recon_name = basename(recon_path)
        stage = get_stage(recon_name)

        cropped_dir = join(recon_path, 'cropped')
        if not isdir(cropped_dir):
            mkdir(cropped_dir)

        scaled_dir = join(recon_path, 'scaled_stacks')
        metadata_dir = join(recon_path, 'Metadata')
        input_dir = get_input_folder(join(metadata_dir, 'config4user.log'))

        if mount:
            input_dir = find_recon(mount, input_dir.replace('\\', '/'))

        # Performing cropping if directory does not exist or is empty
        if len(listdir(cropped_dir)) == 0:

            fake_config = lambda: None
            fake_config.meta_path = metadata_dir
            fake_config.value = 0

            cropper = Crop(input_dir, cropped_dir, update.emit, fake_config, fake_config, app, def_crop=None, repeat_crop=None)
            img_list = cropper.run(auto=True)

        else:
            img_list = app.getfilelist(cropped_dir)

        # Get recon log and pixel size
        log_paths = [f for f in listdir(input_dir) if f.endswith("_rec.log")]
        log = join(input_dir, log_paths[0])

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

            out_name = join(scaled_dir, '{}_scaled_{}_pixel_{:.2f}.{}'.format(recon_name, sf, new_pixel_size, ext))

            if scaled_stack_exists(scaled_dir, sf, new_pixel_size):
                continue

            resample(img_list, sf, out_name, scale_by_int, update)

        # Compression
        bz2_file = join(recon_path, 'IMPC_cropped_{}.nrrd'.format(recon_name))
        if not isfile(bz2_file + '.bz2'):

            print "Generating missing bz2 file for '{}'".format(recon_name)
            bz2_nnrd(img_list, bz2_file, 'Compressing cropped recon', update)


def find_recon(search_path, head):

    combined = []
    while True:

        head, tail = split(head)
        combined.insert(0, tail)

        combined_path = join(search_path, *combined)
        if isdir(combined_path):
            return combined_path


def get_stage(recon_name):

    for s in SCALING.keys():
        if s in recon_name:
            return s


def get_input_folder(config_file):

    with open(config_file, 'rb') as f:
        for line in f.readlines():
            split_line = line.split()
            if 'Input_folder' in split_line[0]:
                return split_line[1]
    return None


def scaled_stack_exists(folder, sf, pixel_size):

    for im_path in listdir(folder):

        im_name, im_ext = splitext(im_path)
        if im_ext != '.nrrd':
            continue

        split_path = im_name.split('_')

        sf_index = split_path.index('scaled') + 1
        pixel_index = split_path.index('pixel') + 1

        im_sf = strconv.convert(split_path[sf_index])
        im_pixel = float(split_path[pixel_index])

        if abs(im_sf - sf) < 0.1 and abs(im_pixel - pixel_size) < 0.1:
            return True

    return False


class FakeUpdate(object):

    def emit(self, str_):
        print str_

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-r', '--recons', help="CSV file of recons to process", required=True, dest='recons')
    parser.add_argument('-m', '--mount', help="Path to drive where recons are located (e.g. /mousedata)", required=False,
                        dest='mount', default=None)

    args = parser.parse_args()

    with open(args.recons, 'rb') as f:
        recons = [row[0] for row in csv.reader(f)]

    batch(recons, mount=args.mount)
