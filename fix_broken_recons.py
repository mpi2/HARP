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
import pandas as pd
import numpy as np
from datetime import datetime
import socket


TIMEOUT = 20

def batch(root, job_file):
    """
    Script to automatically generate crops, scled images and compressed files
    :param recon_list:
    :param mount:
    :return:
    """
    update = FakeUpdate()

    app = AppData()

    lock_path = join(job_file + '.lock')
    lock = FileLock(lock_path, timeout=TIMEOUT)

    while True:
        try:
            with lock.acquire():

                df_jobs = pd.read_csv(job_file, index_col=0)
                df_jobs['status'] = df_jobs['status'].astype(str)

                # Get an unfinished job
                jobs_to_do = df_jobs[df_jobs['status'] == 'nan']

                if len(jobs_to_do) < 1:
                    print("No more jobs left on jobs list")
                    raise SystemExit()

                indx = jobs_to_do.index[0]

                dir_ = indx

                df_jobs.at[indx, 'status'] = 'running'

                df_jobs.at[indx, 'start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                df_jobs.at[indx, 'host'] = socket.gethostname()

                df_jobs.to_csv(job_file)
        except Timeout:
            sys.exit('Timed out')

        proc_recon_path = join(root, dir_)
        cropped_dir = join(proc_recon_path, 'cropped')

        if not isdir(cropped_dir):
            status = "can't find cropped dir"

        img_list = app.getfilelist(cropped_dir)

        if len(img_list) < 100:
            status = "Can't dfind enough images"

        # Get recon log and pixel size
        # Compression
        bz2_file = join(proc_recon_path, 'IMPC_cropped_{}.nrrd'.format(os.path.split(dir_)[1]))
        if os.path.exists(bz2_file + '.bz2'):
            print('removing bz2 file')

            try:
                os.remove(bz2_file + '.bz2')
            except OSError as e:
                print('cannot delete bz2 file {}'.format(bz2_file + '.bz2'))

        print "Generating missing bz2 file for '{}'".format(dir_)
        #IMPC_cropped_20190220_GRM1_E18.5_8.4c_hom_XY_REC.nrrd.bz2
        try:
            bz2_nnrd(img_list, bz2_file, 'Compressing cropped recon', update, center='har')
        except IOError as e:
            print('Failed to write the compressed bzp2 file. Network issues?\n{}'.format(e))
            status = 'falied compression'
        else:
            status = 'success'

        with lock.acquire():
            df_jobs = pd.read_csv(job_file, index_col=0)
            df_jobs.at[indx, 'status'] = status
            df_jobs.at[indx, 'end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_jobs.to_csv(job_file)


class FakeUpdate(object):

    def emit(self, str_):
        print str_


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-r', '--root', help="root dir with mousedat mount", required=True, dest='root')
    parser.add_argument('-c', '--csv', help="path to csv with processed_recon_name", required=True, dest='csv_path')

    args = parser.parse_args()
    batch(args.root, args.csv_path)
