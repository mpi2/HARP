#!/usr/bin/python

"""
Neil: 12/04/19. Adapted from batch.py. But just to reprocess the failed bz2 uploads
"""


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
import os
from filelock import FileLock, Timeout



TIMEOUT = 20

def batch(root, csv_path):
    """
    Script to automatically generate crops, scled images and compressed files
    :param recon_list:
    :param mount:
    :return:
    """

    with open(csv_path, 'r') as fh:
        recon_list = [row[0] for row in csv.reader(fh)]

    done_list = csv_path + 'done'

    app = AppData()

    lock_path = join(done_list + '.lock')
    lock = FileLock(lock_path, timeout=TIMEOUT)

    try:
        with lock.acquire():

            with open(done_list, 'a+') as df:
                done = [x.strip() for x in df.readlines()]

            found_new_recon = False
            for pr_subpath in recon_list:

                if pr_subpath in [x for x in done[0]]:
                    continue

                else:
                    done.write('{},{},\n'.format(pr_subpath, 'in_progress'))
                    found_new_recon = True
                    break
    except Timeout:
        sys.exit('Timed out')

    if not found_new_recon:
        return

    proc_recon_path = join(root, pr_subpath)
    cropped_dir = join(proc_recon_path, 'cropped')

    if not isdir(cropped_dir):
        status = "can't find cropped dir"

    img_list = app.getfilelist(cropped_dir)

    if len(img_list < 100):
        status = "Can't dfind enough images"

    # Get recon log and pixel size
    # Compression
    bz2_file = join(proc_recon_path, 'IMPC_cropped_{}.nrrd.bz2'.format(pr_subpath))

    print "Generating missing bz2 file for '{}'".format(pr_subpath)
    try:
        bz2_nnrd(img_list, bz2_file, 'Compressing cropped recon', update)
    except IOError as e:
        print('Failed to write the compressed bzp2 file. Network issues?\n{}'.format(e))
        status = 'falied compression'

    with lock.aquire():
        with open(done_list, 'a+') as df:
            df.write([pr_subpath, status])



if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-r', '--root', help="root dir with mousedat mount", required=True, dest='root')
    parser.add_argument('-c', '--csv', help="path to csv with processed_recon_name", required=True, dest='csv_path')

    args = parser.parse_args()
    batch(args.root, args.csv_path)
