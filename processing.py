"""
Copyright 2015 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

E-mail the developers: sig@har.mrc.ac.uk


**Summary:**

Performs the following processing:

    * Cropping
    * Scaling
    * Compression

Performs all processing on QThread. All analysis is based on a config file generated using harp.py and other
associated modules.

-------------------------------------------------------
"""

from PyQt4 import QtGui, QtCore
import sys
import subprocess
import os
import signal
import re
from imgprocessing import compress
try:
    import cPickle as pickle
except ImportError:
    import pickle
import shutil
import bz2
from lib import nrrd
import datetime
import copy
from multiprocessing import freeze_support
import traceback
import fnmatch
from config import Config
from imgprocessing import resampler, crop
from appdata import HarpDataError


class ProcessingThread(QtCore.QThread):
    """  Class to provide the processing end of HARP

    When class is initialised and run is called a Qthread iss started. All the main processing is performed
    on this QThread.

    """
    update = QtCore.pyqtSignal(QtCore.QString, name='update')

    def __init__(self, config_paths, thread_terminate_flag, appdata, parent=None):
        """Gets the pickle config file and initialises some instance variables

        :param obj parent: This is a way to pass the "self" object to the processing thread.
        :param str config_path: Path to where config file is. Contains all the parameter information.
        :ivar obj self.configOb: Not strictly a variable... This is an object containing all the parameters.
                                    Setup at _init_ here from the config file path given.
        :ivar int self.kill_check: Switch for the kill signal. Initialised at 0, when switched to 1 processing killed.
        """

        #QtCore.QThread.__init__(self, parent)
        super(ProcessingThread, self).__init__(parent)
        self.config_paths = config_paths
        self.thread_terminate_flag = thread_terminate_flag
        self.app_data = appdata
        self.crop_status = ''
         # List of file extensions to ignore


    def __del__(self):
        print "Processing stopped"

    def run(self):
        """ Starts the QThread, processing then performed.

        Performs the following:

        * makes the session log file (saved in the metadata folder)
        * Calls the following methods for the processing tasks
            * Cropping
            * Scaling
            * copying
            * compression
        """

        # Get the directory of the script
        if getattr(sys, 'frozen', False): # Do we need this? NH
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        #=================================================
        # Start for loop, loading each config file in turn
        #=================================================
        for job in iter(self.config_paths.get, None):

            print job

            self.update.emit("Started Processing")

            filehandler = open(job, 'r')
            self.config = copy.deepcopy(pickle.load(filehandler))

            #===============================================
            # Setup logging files
            #===============================================
            session_log_path = os.path.join(self.config.meta_path, "session.log")
            self.session_log = open(session_log_path, 'w+')

            self.session_log.write("########################################\n")
            self.session_log.write("### HARP Session Log                 ###\n")
            self.session_log.write("########################################\n")
            # start time
            self.session_log.write(str(datetime.datetime.now()) + "\n")

            #===============================================
            # Cropping
            #===============================================
            try:
                cropped_imgs_list = self.cropping()
            except Exception as e:
                self.update.emit("Cropping failed!: {}".format(e))
                self.session_log.write("Cropping failed!: {}\n".format(e))
                continue

            try:
                self.scaling()
            except Exception as e:
                self.update.emit("Scaling failed!: {}".format(e))
                self.session_log.write("Scaling failed!: {}\n".format(e))
                continue

            # Cropping function only copies over image files. Need to copy over other files now scaling and cropping
            # finished
            if self.config.crop_option == "Automatic" or self.config.crop_option == "Manual":
                self.copying()

            # If the old crop was used the non valid image files will have been hid in self.cropping. Now scaling and
            # cropping finished, files can be shown again (taken out of temp folder).
            if self.config.crop_option == "Old_crop":
                self.show_files()

            try:
                self.compression(cropped_imgs_list)
            except HarpDataError as e:
                self.update.emit("compression failed")
                self.session_log.write("compression failed: {}".format(e))
                continue
            else:
                self.update.emit("Processing finished")

            self.session_log.write("Processing finished\n")
            self.session_log.write("########################################\n")
            self.session_log.close()

        return

    def cropping(self):
        """ Performs cropping procedures. Decides what and how to crop based on the paramters in the config file

        The majority of this method is to determine what parameters are in the config file and setup the autocrop
        accordingly.

        Once the cropping is setup the crop.py module is called and a callback autocrop_update_slot method
        is used to monitor progress

        :ivar obj self.session_log: python file object. Used to record the log of what has happened.
        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        :ivar str self.folder_for_scaling: Updated here, depending on the cropping option this will change.

        .. seealso::
            :func:`hide_files()`,
            :func:`autocrop_update_slot()`,
            :func:`autocrop.Autocrop`,
            :func:`autocrop.run()`
        """
        # document in log
        self.session_log.write("*****Performing cropping******\n")

        #===============================================
        # Cropping setup
        #===============================================
        # Also setup the scaling folder here as well. Defaulted to the cropped folder
        self.folder_for_scaling = self.config.cropped_path

        # Cropping option: NO CROP
        if self.config.crop_option == "No_crop":
            # Do not perform any crop as user specified
            self.update.emit("No Crop carried out")
            self.session_log.write("No crop carried out\n")
            self.autocrop_update_slot("success")
            self.folder_for_scaling = self.config.input_folder
            return

        # Cropping option: OLD CROP
        if self.config.crop_option == "Old_crop":
            # Use a previous folder already ran through HARP. No cropping needed here.
            self.update.emit("No crop carried out")
            # Need to hide non recon files. Puts them in a temp folder until scaling has finished
            self.hide_files()
            self.session_log.write("No crop carried out\n")
            self.autocrop_update_slot("success")
            # Still need the cropped files list for compression (if it is to take place)
            cropped_list = self.app_data.getfilelist(self.config.cropped_path)
            return cropped_list

        # Make new crop directory
        if not os.path.exists(self.config.cropped_path):
            os.makedirs(self.config.cropped_path)

        # Cropping option: MANUAL CROP
        if self.config.crop_option == "Manual":
            doauto = False
            self.session_log.write("manual crop\n")
            self.update.emit("Performing manual crop")
            # Get the dimensions from the config object
            dimensions_tuple = (
                int(self.config.xcrop), int(self.config.ycrop), int(self.config.wcrop), int(self.config.hcrop))
            # The cropbox is not derived so should be None when given to the autocrop
            derived_cropbox = None

        # Setup for automatic
        if self.config.crop_option == "Automatic":
            doauto = True
            self.session_log.write("autocrop\n")
            self.update.emit("Performing autocrop")
            # cropbox is not derived and dimensions will be determined in autocrop
            dimensions_tuple = None
            derived_cropbox = None

        # setup for derived crop
        if self.config.crop_option == "Derived":
            doauto = False
            self.session_log.write("Derived crop\n")
            self.update.emit("Performing crop from derived cropbox")
            dimensions_tuple = None
            try:
                # Cropbox dimensions are stored as pickle object. So need to extract
                filehandler = open(self.config.cropbox_path, 'r')
                cropbox_object = copy.deepcopy(pickle.load(filehandler))
                derived_cropbox = cropbox_object.cropbox
            except IOError as e:
                self.session_log.write("error: Cropbox not available for derived dimension crop:\n"
                                       + "Exception traceback:" +
                                       traceback.format_exc() + "\n")
                self.update.emit("error: Could not open cropbox dimension file for derived dimension crop: " + str(e))
            except Exception as e:
                self.session_log.write("error: Unknown exception trying to get derived dimension:\n"
                                       + "Exception traceback:" +
                                       traceback.format_exc() + "\n")
                self.update.emit("error: Unknown exception trying to get derived dimension (see log): " + str(e))

            print "Derived cropbox: ", derived_cropbox

        #===============================================
        # Perform the crop!
        #===============================================
        # Can now finally perform the crop
        self.session_log.write("Crop started\n")
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        # make autocrop object

        cropper = crop.Crop(self.config.input_folder, self.config.cropped_path,
                                           self.autocrop_update_slot, self.config,
                                           self.thread_terminate_flag, self.app_data, def_crop=dimensions_tuple,
                                           repeat_crop=derived_cropbox)

        # WindowsError is an execption only available on Windows need to make a fake WindowsError exception for linux

        if not getattr(__builtins__, "WindowsError", None):
            class WindowsError(OSError): pass

        # Catch all the potential errors which may come
        # It may be better to add the exceptions closer to the event as these can catch a broad range
        try:
            # Run autocrop and catch errors
            croppedlist = cropper.run(auto=doauto)  # James - new version of autocrop

        except WindowsError as e:
            self.session_log.write("error: HARP can't find the folder, maybe a temporary problem connecting to the "
                                   "network. Exception message:\n Exception traceback:" +
                                   traceback.format_exc() + "\n")
            self.update.emit("error: HARP can't find the folder, see log file")
            self.session_log.flush()
            raise

        except HarpDataError as e:
            self.session_log.write("Error: {}".format(e))
            self.update.emit("error: {}".format(e))
            self.session_log.flush()
            raise

        except Exception as e:
            self.session_log.write("error: Unknown exception. Exception message:\n"
                                   + "Exception traceback:" +
                                   traceback.format_exc() + "\n")
            self.update.emit("error:(see log): " + str(e))
            self.session_log.flush()
            raise
        else:
            return croppedlist


    def logger(self, message):
        pass


    def autocrop_update_slot(self, msg):
        """ Listens to autocrop.

        If autocrop sends a signal with the message "success" then the next steps in the processing
        will occur.

        Importantly also displays the messages on the GUI processing tab using self.emit

        Also takes the cropping box used by the autocrop and saves it as a pickle file.

        :param str/tuple msg: A message sent back from the autocrop. Will either be a string or a tuple (the crop box)
        :ivar obj self.session_log: python file object. Used to record the log of what has happened.
        :ivar str self.crop_status: The crop status used to assess whether any more processing should occur.
        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        """

        # check if a tuple. If it is a tuple it means that the crop box has been sen from the autocrop. Then make
        # a pickle object of the object so it can be used again if derived crop option is used
        if type(msg) == tuple:
            # create our generic class for pickles
            crop_box_ob = Config()

            # get path
            crop_box_path = os.path.join(self.config.meta_path, "cropbox.txt")

            # save cropbox tuple to cropbox object
            crop_box_ob.cropbox = msg

            # save the pickle
            with open(crop_box_path, 'w+') as config:
                pickle.dump(crop_box_ob, config)

            # that's the end of this callback
            return

        else:
            # Message not a tuple so send a message to display on the HARP
            self.update.emit(msg)

        # Check what the message says
        if msg == "success":
            print "crop finished"
            print msg
            # The run() checks crop_status variable, if "success" lets other processing occur
            self.crop_status = "success"
            self.session_log.write("Crop finished\n")
        elif re.search("error", msg):
            # Somethings gone wrong, don't let any other processing occur.
            self.session_log.write("Error in cropping see below:\n")
            self.session_log.write(msg)
            self.session_log.close()
            self.crop_status = "error"
        elif re.search("Cancelled", msg):
            self.crop_status = "error"

    def scaling(self):
        """

        """
        # Check if HARP has been stopped
        if self.thread_terminate_flag.value == 1:
            return

        # Record started
        print "Scaling started"
        self.session_log.write("*****Performing scaling******\n")
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        # First make subfolder for scaled stacks
        if not os.path.exists(self.config.scale_path):
            os.makedirs(self.config.scale_path)

        # Perform scaling for all options used.
        if self.config.SF2 == "yes":
            self.downsample(2)

        if self.config.SF3 == "yes":
            self.downsample(3)

        if self.config.SF4 == "yes":
            self.downsample(4)

        if self.config.SF5 == "yes":
            self.downsample(5)

        if self.config.SF6 == "yes":
            self.downsample(6)

        if self.config.pixel_option == "yes":
            scale_factor = self.config.SFX_pixel
            self.downsample(scale_factor, scaleby_int=False)


    def downsample(self, scale, scaleby_int=True):
        """
        """
        if self.thread_terminate_flag.value == 1:
            return

        #===============================================================================
        # Setup
        #===============================================================================
        # Setup a logging file specifically for this scaling
        self.scale_log_path = os.path.join(self.config.meta_path, str(scale) + "_scale.log")
        self.session_scale = open(self.scale_log_path, 'w+')

 
        if (self.config.recon_pixel_size) and scale != "Pixel":
            new_pixel = float(self.config.recon_pixel_size) * float(scale)
            new_pixel = str(round(new_pixel, 4))
            interpolation = "default"

        elif self.config.pixel_option == "yes":
            scale = self.config.SFX_pixel
            new_pixel = self.config.user_specified_pixel

            interpolation = "yes"
        else:
            new_pixel = "NA"
            interpolation = "default"

        # Get the scaling factor in decimal
        dec_sf = round((1.0 / scale), 4)

        # detail scaling in log
        self.session_log.write("Scale by factor:\n")
        self.session_log.write(str(scale))

        self.update.emit("Performing scaling ({})".format(str(scale)))

        #===============================================================================
        # Normal scaling
        #===============================================================================
        print "normal scaling"

        out_name = os.path.join(self.config.scale_path,
                                self.config.full_name + "_scaled_" + str(scale) + "_pixel_" + new_pixel + ".nrrd")

        try:
            files_for_scaling = self.app_data.getfilelist(self.folder_for_scaling)
            if len(files_for_scaling) < 1:
                self.update.emit("Rescaling failed. No images found:")

            resampler.resample(files_for_scaling, scale, out_name, scaleby_int, self.update,
                               self.thread_terminate_flag)
        except HarpDataError as e:
            self.update.emit("Rescaling the image failed: {}".format(e))
            raise



    def resampler_callback(self, msg):
        self.update.emit(msg)


    def hide_files(self):
        """ Puts non-image files non-valid image files into a temp folder so will be ignored for scaling

        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        :raises OSError: Raised if the temp folder can't be made
        """
        # mv non recon image files into a temp folder
        print "hide files"

        crop_path = self.config.cropped_path
        # Make a temp folder
        tmp_crop = os.path.join(crop_path, "tmp")

        # Probably need to put error catching for this
        try:
            # check if tmp folder is there. If it is, then remove.
            if os.path.isdir(tmp_crop):
                shutil.rmtree(tmp_crop)
            #(if a tmp file is there remove as well)
            if os.path.exists(tmp_crop):
                os.remove(tmp_crop)

            print "make temp folder"
            os.makedirs(tmp_crop)

        except OSError as e:
            print "OSError Problem making temp folder", e
            return

        # loop through crop path
        for fn in os.listdir(crop_path):
            #print fn
            fnlc = fn.lower()
            full_fn = os.path.join(crop_path, fn)
            # Known non image files
            if any(fnlc.endswith(x) for x in self.app_data.files_to_ignore):
                shutil.move(full_fn, tmp_crop)
                continue
            # Check if known image file

            if any(fnmatch.fnmatch(fnlc, x) for x in self.app_data.files_to_use):
                # a standard image file so ignore
                continue
            else:
                # Not in the the known non image files but also not a standard image file. Presume not wanted and move
                # to tmp folder
                shutil.move(full_fn, tmp_crop)
                # Not standard image file will be copied over to temp folder

    def show_files(self):
        """ Moves the non-image files, and non-valid image files out of the cropped temp folder

        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified here.
        """
        crop_path = self.config.cropped_path
        tmp_crop = os.path.join(crop_path, "tmp")

        # for loop through list of temp files
        for line in os.listdir(tmp_crop):
            # copy files back to cropped path
            shutil.copy(os.path.join(tmp_crop, line), crop_path)

        # remove temp folder
        shutil.rmtree(tmp_crop)


    def masking(self):
        """ todo """
        print "masking"


    def copying(self):
        """ Copys the non-image and non-valid images files from the original recon and places them into the cropped
        folder

        :ivar int self.kill_check: if 1 it means HARP has been stopped via the GUI. Not modified here.
        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified here.
        """
        # Check if GUI has been stopped
        if self.thread_terminate_flag.value == 1:
            return

        # Tell the GUI what's going on
        self.update.emit("Copying files")

        # Record the log
        self.session_log.write("***Copying other files from original recon***\n")
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        # For loop through the input folder
        for file in os.listdir(self.config.input_folder):

            #check if folder before copying
            if os.path.isdir(os.path.join(self.config.input_folder, file)):
                # Dont copy the sub directory move to the next itereration
                continue

            elif not os.path.exists(os.path.join(self.config.cropped_path, file)):
                # File exists so copy it over to the crop folder
                # Need to get full path of original file though
                file = os.path.join(self.config.input_folder, file)
                shutil.copy(file, self.config.cropped_path)
                self.session_log.write("File copied:" + file + "\n")

    def compression(self, cropped_img_list):
        """ Compresses either scans and the original recons or the cropped folder

        :ivar int self.kill_check: if 1 it means HARP has been stopped via the GUI. Not modified here.
        :ivar obj self.configOb: Simple object which contains all the parameter information. Not modified here.
        """
        # Check if stop button pressed on GUI
        if self.thread_terminate_flag.value == 1:
            return

        if self.config.scans_recon_comp == "yes" or self.config.crop_comp == "yes":
            self.session_log.write("***Performing Compression***")
            self.session_log.write(str(datetime.datetime.now()) + "\n")

        if self.config.scans_recon_comp == "yes":

            if self.config.scan_folder:
                #============================================
                # Compression for scan
                #============================================
                self.update.emit("Performing compression of scan folder")
                self.session_log.write("Compression of scan folder")
                #scan_list = getfilelist(self.config.scan_folder,
                #                        self.app_data.files_to_use, self.app_data.files_to_ignore)

                scan_name = os.path.split(self.config.scan_folder)[1]
                outfile = os.path.join(
                    self.config.output_folder, 'IMPC_scan{}'.format(self.config.full_name))

                compress.bz2_dir(self.config.scan_folder, outfile, self.update, 'scan',
                                 self.thread_terminate_flag)
                #scan_nrrd = os.path.join(self.config.output_folder, '{}.nrrd'.format(scan_name))
                #compress.bz2_nnrd(scan_list, scan_nrrd, "Compressing scan", self.update)

                self.update.emit("Compression of scan folder finished")

                # Check if stop button pressed on GUI
                if self.thread_terminate_flag.value == 1:
                    return

                #============================================
                # compression for original recon
                #============================================
                self.update.emit("Performing compression of original recon folder")
                self.session_log.write("Compression of original recon folder")
                # recon_list = getfilelist(self.config.input_folder,
                #                         self.app_data.files_to_use, self.app_data.files_to_ignore)
                recon_outfile = os.path.join(
                    self.config.output_folder, 'IMPC_recon{}'.format(self.config.full_name))
                compress.bz2_dir(self.config.input_folder, recon_outfile, self.update, 'recon',
                                 self.thread_terminate_flag)

                self.update.emit("Compression of recon folder finished")

        if self.thread_terminate_flag.value == 1:
            return

        if self.config.crop_comp == "yes":
            if self.config.crop_option != "No_crop":
                # #============================================
                # # compression for cropped image sequence
                # #============================================

                self.update.emit("Compression of cropped recon started")
                outfile = os.path.join(
                    self.config.output_folder, 'IMPC_cropped_{}.nrrd'.format(self.config.full_name))

                compress.bz2_nnrd(cropped_img_list, outfile, 'Compressing cropped recon', self.update)





def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()
