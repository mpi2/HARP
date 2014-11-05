"""
**Summary:**

Performs the following processing:

    * Cropping
    * Scaling
    * Compression

Performs all processing on QThread. All analysis is based on a config file generated using harp.py and other
associated modules.

NOTE: QT Designer automatically uses mixed case for its class object names e.g radioButton. This format is not PEP8 but
has not been changed.

-------------------------------------------------------
"""
from PyQt4 import QtGui, QtCore
import sys
import subprocess
import os, signal
import re

try:
    import cPickle as pickle
except ImportError:
    import pickle
import shutil
import tarfile
import datetime
import copy
from multiprocessing import freeze_support
from sys import platform as _platform
import traceback
import fnmatch
import autocrop
from config import ConfigClass
import numpy as np
import cv2
import SimpleITK as sitk

# from vtkRenderAnimation import Animator
#from Segmentation import watershed_filter


class ProcessingThread(QtCore.QThread):
    """  Class to provide the processing end of HARP

    When class is initialised and run is called a Qthread iss started. All the main processing is performed
    on this QThread.

    """

    def __init__(self, config_path, memory, parent=None):
        """ **Constructor**: Gets the pickle config file and initialises some instance variables

        :param str memory: Path to where config file is. Contains all the parameter information.
        :param obj parent: This is a way to pass the "self" object to the processing thread.
        :param str config_path: Path to where config file is. Contains all the parameter information.
        :ivar obj self.configOb: Not strictly a variable... This is an object containing all the parameters.
                                    Setup at _init_ here from the config file path given.
        :ivar int self.kill_check: Switch for the kill signal. Initialised at 0, when switched to 1 processing killed.
        :ivar float self.memory: Taken from the memory param. Saved as instance variable to be used later
        """
        QtCore.QThread.__init__(self, parent)
        filehandler = open(config_path, 'r')
        self.configOb = copy.deepcopy(pickle.load(filehandler))
        self.memory = memory
        self.kill_check = 0
        self.imagej_pid = ''
        self.crop_status = ''

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

        Overrides the run method in QThread
        :param obj self:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :ivar obj self.session_log: python file object. Used to record the log of what has happened.
        :ivar boolean self.scale_error: Initialised scale_error to none here. If an error will be True
        :ivar str self.crop_status: The crop status modified in the autocrop_update_slot.

        .. seealso::
            :func:`cropping()`,
            :func:`scaling()`,
            :func:`copying()`,
            :func:`show_files()`,
            :func:`compression()`,
        """
        #===============================================
        # Start processing!
        #===============================================
        self.emit(QtCore.SIGNAL('update(QString)'), "Started Processing")
        # Get the directory of the script
        if getattr(sys, 'frozen', False):
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        #===============================================
        # Setup logging files
        #===============================================
        session_log_path = os.path.join(self.configOb.meta_path, "session.log")
        self.session_log = open(session_log_path, 'w+')

        #logging if there is an error with scaling
        self.scale_error = None

        self.session_log.write("########################################\n")
        self.session_log.write("### HARP Session Log                 ###\n")
        self.session_log.write("########################################\n")
        # start time
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        #===============================================
        # Cropping
        #===============================================
        self.cropping()
        # A callback function is used to monitor if autocrop was run sucessfully. This modifies the self.crop_status
        # instance variable. Has to be success to continue
        if self.crop_status != "success":
            print "Cropping failed!"
            print ""
            return

        #===============================================
        # Scaling
        #===============================================
        self.scaling()

        #===============================================
        # Space for other methods e.g. masking or movies
        #===============================================
        #self.masking()

        #===============================================
        # Copying
        #===============================================
        # Cropping function only copies over image files. Need to copy over other files now scaling and cropping
        # finished
        if self.configOb.crop_option == "Automatic" or self.configOb.crop_option == "Manual":
            self.copying()

        # If the old crop was used the non valid image files will have been hid in self.cropping. Now scaling and
        # cropping finished, files can be shown again (taken out of temp folder).
        if self.configOb.crop_option == "Old_crop":
            self.show_files()

        #===============================================
        # Compression
        #===============================================
        self.compression()

        if self.scale_error:
            self.emit(QtCore.SIGNAL('update(QString)'),
                      "Processing finished (problems creating some of the scaled stacks, see log file)")
        else:
            self.emit(QtCore.SIGNAL('update(QString)'), "Processing finished")

        self.session_log.write("Processing finished\n")
        self.session_log.write("########################################\n")
        self.session_log.close()
        #===============================================
        # Finished!!
        #===============================================
        return


    def cropping(self):
        """ Performs cropping procedures. Decides what and how to crop based on the paramters in the config file

        The majority of this method is to determine what parameters are in the config file and setup the autocrop
        accordingly.

        Once the cropping is setup the autocrop.py module is called and a callback autocrop_update_slot method
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
        self.folder_for_scaling = self.configOb.cropped_path

        # Cropping option: NO CROP
        if self.configOb.crop_option == "No_crop":
            # Do not perform any crop as user specified
            self.emit(QtCore.SIGNAL('update(QString)'), "No Crop carried out")
            self.session_log.write("No crop carried out\n")
            self.autocrop_update_slot("success")
            self.folder_for_scaling = self.configOb.input_folder
            return

        # Cropping option: OLD CROP
        if self.configOb.crop_option == "Old_crop":
            # Use a previous folder already ran through HARP. No cropping needed here.
            self.emit(QtCore.SIGNAL('update(QString)'), "No Crop carried out")
            # Need to hide non recon files. Puts them in a temp folder until scaling has finished
            self.hide_files()
            self.session_log.write("No crop carried out\n")
            self.autocrop_update_slot("success")
            return

        # Make new crop directory
        if not os.path.exists(self.configOb.cropped_path):
            os.makedirs(self.configOb.cropped_path)

        # Cropping option: MANUAL CROP
        if self.configOb.crop_option == "Manual":
            self.session_log.write("manual crop\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "Performing manual crop")
            # Get the dimensions from the config object
            dimensions_tuple = (
                int(self.configOb.xcrop), int(self.configOb.ycrop), int(self.configOb.wcrop), int(self.configOb.hcrop))
            # The cropbox is not derived so should be None when given to the autocrop
            derived_cropbox = None

        # Setup for automatic
        if self.configOb.crop_option == "Automatic":
            self.session_log.write("autocrop\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "Performing autocrop")
            # cropbox is not derived and dimensions will be determined in autocrop
            dimensions_tuple = None
            derived_cropbox = None

        # setup for derived crop
        if self.configOb.crop_option == "Derived":
            self.session_log.write("Derived crop\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "Performing crop from derived cropbox")
            dimensions_tuple = None
            try:
                # Cropbox dimensions are stored as pickle object. So need to extact
                filehandler = open(self.configOb.cropbox_path, 'r')
                cropbox_object = copy.deepcopy(pickle.load(filehandler))
                derived_cropbox = cropbox_object.cropbox
            except IOError as e:
                self.session_log.write("error: Cropbox not available for derived dimension crop:\n"
                                       + "Exception traceback:" +
                                       traceback.format_exc() + "\n")
                self.emit(QtCore.SIGNAL('update(QString)'), "error: Could not open cropbox dimension file for "
                                                            "derived dimension crop: " + str(e))
            except Exception as e:
                self.session_log.write("error: Unknown exception trying to get derived dimension:\n"
                                       + "Exception traceback:" +
                                       traceback.format_exc() + "\n")
                self.emit(QtCore.SIGNAL('update(QString)'), "error: Unknown exception trying to get derived dimension"
                                                            " (see log): " + str(e))

        #===============================================
        # Perform the crop!
        #===============================================
        # Can now finally perform the crop
        self.session_log.write("Crop started\n")
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        # make autocrop object
        self.auto_crop = autocrop.Autocrop(self.configOb.input_folder, self.configOb.cropped_path,
                                           self.autocrop_update_slot, def_crop=dimensions_tuple,
                                           repeat_crop=derived_cropbox)

        # WindowsError is an execption only available on Windows need to make a fake WindowsError exception for linux
        if not getattr(__builtins__, "WindowsError", None):
            class WindowsError(OSError): pass

        # Catch all the potential errors which may come
        # It may be better to add the execptions closer to the event as these can catch a broad range
        try:
            # Run autocrop and catch errors
            self.auto_crop.run()

        except WindowsError as e:
            self.session_log.write("error: HARP can't find the folder, maybe a temporary problem connecting to the "
                                   "network. Exception message:\n Exception traceback:" +
                                   traceback.format_exc() + "\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "error: HARP can't find the folder, see log file")

        except TypeError as e:
            # This is referring to an error in either the functions run_crop_process or init_cropping. P
            # ossibly the exception would be more beneficial placed directly in autocrop....
            self.session_log.write("error: HARP most likely can't find the folder, maybe a temporary problem connecting"
                                   " to the network. Exception message:\n Exception traceback:" +
                                   traceback.format_exc() + "\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "error: HARP can't find the files, see log file")

        except Exception as e:
            self.session_log.write("error: Unknown exception. Exception message:\n"
                                   + "Exception traceback:" +
                                   traceback.format_exc() + "\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "error: Unknown exception (see log): " + str(e))

    def tiffstack_from_slices(self, in_dir, outfile):
        """
        Create a tiff stack a directory containing single 2D images
        :param in_dir, str, directory where single images are
        :param outfile, str, path to output tiff stack
        :return:
        """
        array_3d = None
        for file_ in sorted(os.listdir(in_dir)):
            if file_.endswith(('tiff', 'tif', 'TIFF', 'TIF', 'BMP', 'bmp')):
                print file_
                array_2d = cv2.imread(os.path.join(in_dir, file_), cv2.CV_LOAD_IMAGE_GRAYSCALE)
                if array_3d is None:
                    array_3d = array_2d
                    continue
                array_3d = np.dstack((array_3d, array_2d))

        # Need to do some swapping of axes as cv2/numpy treat them differently to sitk
        array_3d = np.swapaxes(array_3d, 0, 2)
        array_3d = np.swapaxes(array_3d, 1, 2)

        image_3d = sitk.GetImageFromArray(array_3d)
        sitk.WriteImage(image_3d, outfile)


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
            crop_box_ob = ConfigClass()

            # get path
            crop_box_path = os.path.join(self.configOb.meta_path, "cropbox.txt")

            # save cropbox tuple to cropbox object
            crop_box_ob.cropbox = msg

            # save the pickle
            with open(crop_box_path, 'w+') as config:
                pickle.dump(crop_box_ob, config)

            # that's the end of this callback
            return

        else:
            # Message not a tuple so send a message to display on the HARP
            self.emit(QtCore.SIGNAL('update(QString)'), msg)

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
        """  Sets up a series of scaling methods depending on memory and scaling options.

        Scaling perform using **execute_imagej()** and memory check performed using **memory_check()**.

        :ivar obj self.session_log: python file object. Used to record the log of what has happened.
        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        :ivar int self.memory: Memory calculated before processing started
        :ivar int self.memory_4_imageJ: Use 90% of available memory for imageJ. Calculated as 0.9*self.memory
        :ivar int self.kill_check: if 1 it means HARP has been stopped via the GUI

        .. seealso::
            :func:`execute_imagej()`,
            :func:`memory_check()`,
        """
        # Check if HARP has been stopped
        if self.kill_check:
            return

        # Record started
        print "Scaling started"
        self.session_log.write("*****Performing scaling******\n")
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        # First make subfolder for scaled stacks
        if not os.path.exists(self.configOb.scale_path):
            os.makedirs(self.configOb.scale_path)

        # Memory of computer being used will depend on how much memory will be used in imageJ
        # e.g 80% total memory of the computer
        self.memory_4_imageJ = (int(self.memory) * .9)
        self.memory_4_imageJ = self.memory_4_imageJ * 0.00000095367
        self.memory_4_imageJ = int(self.memory_4_imageJ)
        memory_mb = int(int(self.memory) * 0.00000095367)
        self.session_log.write("Total Memory of Computer(mb):" + str(memory_mb) + "\n")
        self.session_log.write("Memory for ImageJ(mb):" + str(self.memory_4_imageJ) + "\n")

        # Perform scaling for all options used. Do a memory check before performing scaling.
        if self.configOb.SF2 == "yes":
            memory_result = self.memory_check(2)
            if memory_result:
                self.execute_imagej(2.0)

        if self.configOb.SF3 == "yes":
            memory_result = self.memory_check(3)
            if memory_result:
                self.execute_imagej(3.0)

        if self.configOb.SF4 == "yes":
            memory_result = self.memory_check(4)
            if memory_result:
                self.execute_imagej(4.0)

        if self.configOb.SF5 == "yes":
            memory_result = self.memory_check(5)
            if memory_result:
                self.execute_imagej(5.0)

        if self.configOb.SF6 == "yes":
            memory_result = self.memory_check(6)
            if memory_result:
                self.execute_imagej(6.0)

        if self.configOb.pixel_option == "yes":
            memory_result = self.memory_check(self.configOb.SFX_pixel)
            if memory_result:
                self.execute_imagej("Pixel")

    def memory_check(self, scale):
        """ Rough attempt to see how much memory to use for ImageJ

        2 Outcomes:
            * Enough memory to perform as standard
            * Not enough memory: No scaling will occur

        The approximate amount of memory required is 4x that of the memory of the approx scaled stack

        :param int scale: The scaling factor used.
        :ivar obj self.session_log: python file object. Used to record the log of what has happened.
        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        :ivar int memory_4_imageJ: Use 90% of available memory for imageJ. Calculated as 0.9*self.memory
        :ivar int self.kill_check: if 1 it means HARP has been stopped via the GUI

        :return boolean: True if memory is sufficient, False if not sufficient and scaling wont occur
        """
        # Get the scale in decimal equivalent
        scale_div = float(1.0 / scale)

        # If no crop option the memory check is done using data extrapolated from the original recon folder
        if self.configOb.crop_option == "No_crop":
            crop_folder_size_mb = float(self.configOb.recon_folder_size) * 1024.0
            print "Recon folder size to downsize (mb)", crop_folder_size_mb
            num_files = len([name for name in os.listdir(self.configOb.input_folder) if os.path.isfile(name)])

        else:

            prog = re.compile("(.*)_rec\d+\.(bmp|tif|jpg|jpeg)", re.IGNORECASE)
            filename = ""
            # for loop to go through the directory
            for line in os.listdir(self.folder_for_scaling):
                line = str(line)
                #print line+"\n"
                # if the line matches the regex break
                if prog.match(line):
                    filename = line
                    break

            # get the number of files, ignore any non recon files
            num_files = len([f for f in os.listdir(self.configOb.cropped_path) if
                             ((f[-4:] == ".bmp") or (f[-4:] == ".tif") or (f[-4:] == ".jpg") or (f[-4:] == ".jpeg") or
                              (f[-4:] == ".BMP") or (f[-4:] == ".TIF") or (f[-4:] == ".JPG") or (f[-4:] == ".JPEG") and
                              (f[-7:] != "spr.bmp") and (f[-7:] != "spr.tif") and (f[-7:] != "spr.jpg") and (
                                 f[-7:] != "spr.jpeg") and
                              (f[-7:] != "spr.BMP") and (f[-7:] != "spr.TIF") and (f[-7:] != "spr.JPG") and (
                                 f[-7:] != "spr.JPEG"))])

            # get the size of the file matched previously
            filename = os.path.join(self.folder_for_scaling, filename)
            file1_size = os.path.getsize(filename)

            # approx folder size
            approx_size = num_files * file1_size

            # convert to mb
            crop_folder_size_mb = (approx_size / (1024 * 1024.0))


        # Get the approx size of the statck by dividing by x,y ans z of the folder size. e.g. for scaling by 2
        # will be divided by 0.5, 0.5 and 0.5
        memory_for_scale = crop_folder_size_mb * (scale_div * scale_div * scale_div)

        # Based on a very approximate estimate I have said it will take imagej 4x that of the memory of
        # the approx scaled stack
        memory_for_scale = memory_for_scale * 4

        self.num_files = num_files

        # Check if there is enough memory  available.
        if self.memory_4_imageJ < memory_for_scale:
            print "not enough memory"
            self.session_log.write("Not enough memory for this scaling\n")
            self.emit(QtCore.SIGNAL('update(QString)'), "Not enough memory for scaling\n")
            fail_file_name = os.path.join(self.configOb.scale_path, "insufficient_memory_for_scaling_" + str(scale))
            fail_file = open(fail_file_name, 'w+')
            fail_file.close()
            self.scale_error = True
            return False
        else:
            # enough memory
            return True

    def execute_imagej(self, sf):
        """ Runs the imagej scaling using a subprocess call

        The method does the following:

            1. Setup: Deterimines some settings used in imagej (e.g. interpolation)
            2. Normal scaling: Performs scaling as per the imagej macro siah_scale.txt
            3. Low memory scaling: If the the normal scaling failed due to memory reasons. The scaling is repeated
                using a low memory imagej macro

        :param float sf: Scaling factor chosen by the user
        :ivar str self.scale_log_path: Path to scale log
        :ivar str self.session_scale: python file object. Used to record the log of what has happened for scaling.
        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        :ivar int memory_4_imageJ: Use 90% of available memory for imageJ. Calculated as 0.9*self.memory
        :ivar int self.kill_check: if 1 it means HARP has been stopped via the GUI

        .. seealso::
            :func:`scale_error_check()`,
        """
        if self.kill_check:
            return

        #===============================================================================
        # Setup
        #===============================================================================
        # Setup a logging file specifically for this scaling
        self.scale_log_path = os.path.join(self.configOb.meta_path, str(sf) + "_scale.log")
        self.session_scale = open(self.scale_log_path, 'w+')

        # Gets the new pixel numbers for the scaled stack name (see in imagej macro)
        if (self.configOb.recon_pixel_size) and sf != "Pixel":
            new_pixel = float(self.configOb.recon_pixel_size) * float(sf)
            new_pixel = str(round(new_pixel, 4))
            interpolation = "default"

        elif self.configOb.pixel_option == "yes":
            sf = self.configOb.SFX_pixel
            new_pixel = self.configOb.user_specified_pixel

            interpolation = "yes"
        else:
            new_pixel = "NA"
            interpolation = "default"

        # Get the scaling factor in decimal
        dec_sf = round((1 / sf), 4)

        # ij path if run from executable
        ijpath = os.path.join('..', '..', 'ImageJ', 'ij.jar')
        if not os.path.exists(ijpath):
            #ij path if ran from script
            ijpath = os.path.join(self.dir, 'ImageJ', 'ij.jar')

        if not os.path.exists(ijpath):
            self.emit(QtCore.SIGNAL('update(QString)'), "Error: Can't find Imagej")
            self.kill_check == 1
            return

        # Setup macro path
        # If run run as an executable the path will be different
        ij_macro_path = os.path.join('..', '..', "siah_scale.txt")
        if not os.path.exists(ij_macro_path):
            ij_macro_path = os.path.join(self.dir, "siah_scale.txt")

        ij_macro_path_low_mem1 = os.path.join('..', '..', "siah_scale_low_mem1.txt")
        if not os.path.exists(ij_macro_path_low_mem1):
            ij_macro_path_low_mem1 = os.path.join(self.dir, "siah_scale_low_mem1.txt")

        ij_macro_path_low_mem2 = os.path.join(self.dir, "siah_scale_low_mem2.txt")
        if not os.path.exists(ij_macro_path_low_mem2):
            ij_macro_path_low_mem2 = os.path.join('..', '..', "siah_scale_low_mem2.txt")

        if not os.path.exists(ij_macro_path):
            self.emit(QtCore.SIGNAL('update(QString)'), "error: Can't find Imagej macro script")
            self.kill_check == 1
            return

        # detail scaling in log
        self.session_log.write("Scale by factor:\n")
        self.session_log.write(str(sf))
        self.emit(QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(str(sf)))

        #===============================================================================
        # Normal scaling
        #===============================================================================
        print "norm scaling"
        file_name = os.path.join(self.configOb.scale_path,
                                 self.configOb.full_name + "_scaled_" + str(sf) + "_pixel_" + new_pixel + ".tif")

        # Subprocess call for imagej macro
        process = subprocess.Popen(
            ["java", "-Xmx" + str(self.memory_4_imageJ) + "m", "-jar", ijpath, "-batch", ij_macro_path,
             self.configOb.imageJ + "^" + str(dec_sf) + "^" + interpolation + "^" + file_name],
            stdout=self.session_scale, stderr=self.session_scale)

        #record a process ID incase we need to kill imagej
        self.imagej_pid = str(process.pid)

        #NOTE: process.communicate catches when processing is finished
        # I dont think the out and error variables work here as we already assigned stderr and stdout in the
        # subprocess call
        out, err = process.communicate()
        print process.returncode

        # check if there was a memory problem then repeat as low memory version
        result = self.scale_error_check("norm", sf)

        # If a non-memory error occured call it a day for this one
        if self.scale_error == True:
            return

        if result == "repeat":
            #===============================================
            # Low memory scaling
            #===============================================
            # Low memory version splits the processing done in imagej into two parts.
            # The first part scales by x and y, and does this in batch mode (slice by slice). This saves the output
            # as an image sequence. The image sequence is stored in a temp folder.
            # The second part does the z scale (has to load in the whole stack for this)
            # The temp folder is then deleted
            print "low mem version"
            self.emit(QtCore.SIGNAL('update(QString)'), "Performing low memory scaling ({})".format(str(sf)))

            # reset the scaling log
            self.session_scale.close()
            self.session_scale = open(self.scale_log_path, 'w+')

            # Subprocess call for imagej macro
            # First x and y scaling and save a temp stack
            temp_folder = os.path.join(self.configOb.scale_path, "tmp")
            if not os.path.exists(temp_folder):
                os.mkdir(temp_folder)

            # Subprocess call to do the x and y scaling
            process = subprocess.Popen(
                ["java", "-Xmx" + str(self.memory_4_imageJ) + "m", "-jar", ijpath, "-batch", ij_macro_path_low_mem1,
                 self.configOb.imageJ + "^" + str(dec_sf) + "^" + interpolation + "^" + temp_folder + os.sep + "^"],
                stdout=self.session_scale, stderr=self.session_scale)

            # record a pid so we can kill
            self.imagej_pid = str(process.pid)

            # recognises when the process has finished and then continues with script
            out, err = process.communicate()

            # check if any errors occured.
            self.scale_error_check("low", sf)
            if self.scale_error == True:
                print "error"
                # Remove the temp folder
                shutil.rmtree(temp_folder)
                return

            print "second part of scaling"
            file_name = os.path.join(self.configOb.scale_path,
                                     self.configOb.full_name + "_scaled_" + str(sf) + "_pixel_" + new_pixel + ".tif")

            # Subprocess call to do the z scaling
            process2 = subprocess.Popen(
                ["java", "-Xmx" + str(self.memory_4_imageJ) + "m", "-jar", ijpath, "-batch", ij_macro_path_low_mem2,
                 temp_folder + os.sep + "^" + str(dec_sf) + "^" + interpolation + "^" + file_name + "^" + str(
                     self.num_files) + "^"],
                stdout=self.session_scale, stderr=self.session_scale)

            self.imagej_pid = str(process2.pid)
            # recognises when the process has finished and then continues with script
            out, err = process2.communicate()
            # check if any errors occured
            self.scale_error_check("low", sf)
            shutil.rmtree(temp_folder)
            self.session_scale.close()

    def scale_error_check(self, mem_opt, sf):
        """ Check the session log from imagej scaling

        Used by execute_imagej() to check if a low memory repeat is to be performed.

        :param str mem_opt: What memory option was used "norm" or "low" memory version.
        :param float sf: Used for logging purposes
        :return str: Will return the string "repeat" if a memory problem has occured
        """
        self.session_scale_check = open(self.scale_log_path, "r")

        # reset processing ID, as processing has finished.
        self.imagej_pid = ""

        # Check the self.session_scale file for memory or any other problem messages
        prog1 = re.compile("<Out of memory>")
        prog2 = re.compile(">>>>>>>>>>>>>>>>>>>>>>>>>>>")
        out_of_memory = None
        other_ij_problem = None

        # First check for memory problems
        for line in self.session_scale_check:
            # "chomp" the line endings off
            line = line.rstrip()
            # if the line matches the regex print the (\w+.\w+) part of regex
            if prog1.match(line):
                # Grab the pixel size with with .group(1)
                out_of_memory = True
                break

        # Then check for any other problems.
        for line in self.session_scale_check:
            # "chomp" the line endings off
            line = line.rstrip()
            # if the line matches the regex print the (\w+.\w+) part of regex
            if prog2.match(line):
                # Grab the pixel size with with .group(1)
                other_ij_problem = True
                break

        if out_of_memory and mem_opt == "norm":
            # Dont use the word "error" in the signal message. If "error" is used HARP might skip any further
            # processing for this HARP processing list.
            self.emit(QtCore.SIGNAL('update(QString)'),
                      "Problem in scaling. Not enough memory will try low memory version\n")
            self.session_scale.write("Error in scaling will try low memory version\n")
            # return "repeat" so processing starts again with low memory
            return "repeat"

        elif out_of_memory and mem_opt == "low":
            # Out of memory BUT already attempted to repeat using low memory imagej macro.
            # Can't do anythin else!
            self.emit(QtCore.SIGNAL('update(QString)'), "Problem in scaling. Not enough memory\n")
            self.session_log.write("Error in scaling\n")
            fail_file_name = os.path.join(self.configOb.scale_path, "insufficient_memory_for_scaling_" + str(sf))
            fail_file = open(fail_file_name, 'w+')
            fail_file.close()
            self.scale_error = True

        elif other_ij_problem:
            # other problem we can't do anythin about...
            self.emit(QtCore.SIGNAL('update(QString)'), "Problem in scaling. Check log file\n")
            self.session_scale.write("Error in scaling\n")
            fail_file_name = os.path.join(self.configOb.scale_path, "error_performing_scaling_by_" + str(sf))
            fail_file = open(fail_file_name, 'w+')
            fail_file.close()
            self.scale_error = True
        else:
            self.session_log.write("Finished scaling\n")

    def hide_files(self):
        """ Puts non-image files non-valid image files into a temp folder so will be ignored for scaling

        :ivar obj self.configOb: Simple Object which contains all the parameter information. Not modified.
        :raises OSError: Raised if the temp folder can't be made
        """
        # mv non recon image files into a temp folder
        print "hide files"

        crop_path = self.configOb.cropped_path
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

        non_image_suffix = ('spr.bmp', 'spr.tif', 'spr.tiff', 'spr.jpg', 'spr.jpeg', '.txt', '.text', '.log', '.crv')
        image_list = ('*rec*.bmp', '*rec*.BMP', '*rec*.tif', '*rec*.tiff', '*rec*.jpg', '*rec*.jpeg')

        # loop through crop path
        for fn in os.listdir(crop_path):
            print fn
            fnlc = fn.lower()
            full_fn = os.path.join(crop_path, fn)
            # Known non image files
            if any(fnlc.endswith(x) for x in non_image_suffix):
                shutil.move(full_fn, tmp_crop)
                continue
            # Check if known image file
            if any(fnmatch.fnmatch(fnlc, x) for x in image_list):
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
        crop_path = self.configOb.cropped_path
        tmp_crop = os.path.join(crop_path, "tmp")

        # for loop through list of temp files
        for line in os.listdir(tmp_crop):
            # copy files back to cropped path
            shutil.copy(os.path.join(tmp_crop, line), crop_path)

        # remove temp folder
        shutil.rmtree(tmp_crop)


    def movies(self):
        """ todo
        """
        movie_path = os.path.join(self.configOb.output_folder, "movies")
        if not os.path.exists(movie_path):
            os.makedirs(movie_path)

        print "starting movies"
        for file in range(len(self.scale_array)):
            print self.scale_array[file]
            movie = Animator(str(file), movie_path)

            #self.scale_array.
            #movie = Animator(self., out_dir)

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
        if self.kill_check:
            return

        # Tell the GUI what's going on
        self.emit(QtCore.SIGNAL('update(QString)'), "Copying files\n")

        # Record the log
        self.session_log.write("***Copying other files from original recon***\n")
        self.session_log.write(str(datetime.datetime.now()) + "\n")

        # For loop through the input folder
        for file in os.listdir(self.configOb.input_folder):

            #check if folder before copying
            if os.path.isdir(os.path.join(self.configOb.input_folder, file)):
                # Dont copy the sub directory move to the next itereration
                continue

            elif not os.path.exists(os.path.join(self.configOb.cropped_path, file)):
                # File exists so copy it over to the crop folder
                # Need to get full path of original file though
                file = os.path.join(self.configOb.input_folder, file)
                shutil.copy(file, self.configOb.cropped_path)
                self.session_log.write("File copied:" + file + "\n")

    def compression(self):
        """ Compresses either scans and the original recons or the cropped folder

        :ivar int self.kill_check: if 1 it means HARP has been stopped via the GUI. Not modified here.
        :ivar obj self.configOb: Simple object which contains all the parameter information. Not modified here.
        """
        # Check if stop button pressed on GUI
        if self.kill_check:
            return

        # Record the log
        if self.configOb.scans_recon_comp == "yes" or self.configOb.crop_comp == "yes":
            self.session_log.write("***Performing Compression***")
            self.session_log.write(str(datetime.datetime.now()) + "\n")

        if self.configOb.scans_recon_comp == "yes":

            if self.configOb.scan_folder:
                #============================================
                # Compression for scan
                #============================================
                self.emit(QtCore.SIGNAL('update(QString)'), "Performing compression of scan folder")
                self.session_log.write("Compression of scan folder")
                path_scan, folder_name_scan = os.path.split(self.configOb.scan_folder)

                out = tarfile.open(str(self.configOb.scan_folder) + ".tar.bz2", mode='w:bz2')
                out.add(path_scan, arcname="Scan_folder")
                out.close()
                self.emit(QtCore.SIGNAL('update(QString)'), "Compression of scan folder finished")

                # Check if stop button pressed on GUI
                if self.kill_check:
                    return

                #============================================
                # compression for original recon
                #============================================
                self.emit(QtCore.SIGNAL('update(QString)'), "Performing compression of original recon folder")
                self.session_log.write("Compression of original recon folder")
                path_scan, folder_name_scan = os.path.split(self.configOb.input_folder)

                out = tarfile.open(str(self.configOb.input_folder) + ".tar.bz2", mode='w:bz2')
                out.add(path_scan, arcname="Input_folder")
                out.close()
                self.emit(QtCore.SIGNAL('update(QString)'), "Compression of recon folder finished")

        # compression for crop folder
        # Check if stop button pressed on GUI
        if self.kill_check:
            return

        if self.configOb.crop_comp == "yes":
            if self.configOb.crop_option != "No_crop":
                #============================================
                # compression for cropped image sequence
                #============================================
                self.emit(QtCore.SIGNAL('update(QString)'), "Compression of cropped recon started")

                # Create a tiff stack from the individual tiff slices
                temp_stack_path = os.path.join(self.configOb.tmp_dir, 'tiffstack_temp.tiff')
                self.tiffstack_from_slices(self.configOb.cropped_path, temp_stack_path)

                #Now compress the tiff and add to the archive
                out = tarfile.open(os.path.join(self.configOb.output_folder, 'IMPC_{}.tar.bz2'.format(
                    self.configOb.full_name)), mode='w:bz2')


                out.add(temp_stack_path, arcname='{}_cropped.tiff'.format(self.configOb.full_name))
                # remove the tem tiff stack
                try:
                    os.remove(temp_stack_path)
                except Exception:
                    pass # Not sure which excption to catch if temp file is gone

                # Add the recon log file
                log_name = os.path.basename(self.configOb.recon_log_file)
                try:
                    out.add(self.configOb.recon_log_file, arcname=log_name)
                except OSError:
                    pass  # No recon log available

                out.close()

    def kill_slot(self):
        """ This method is called every time a user presses stop

        This slot is connected to the emission command self.emit(QtCore.SIGNAL('kill(QString)'), "kill") when called
        in harp.py

        See harp.kill_em_all() and harp.processing_thread() for how the kill slot was setup.

        It should kill any python processes by changing switches which are checked regularly in the methods used.

        Calls a method autocrop.terminate() which sends stop signals to stop the multithreaded processing running
        for the autocrop

        """
        print("Kill all")
        # Update the GUI with what has happened
        self.emit(QtCore.SIGNAL('update(QString)'), "Processing Cancelled!")

        # Kill the processes in autocrop
        autocrop.terminate()

        # Kills any processes in the ProcessingThread.run() method
        self.kill_check == 1

        try:
            # If imagej pid is defined, means imagej is still running
            if self.imagej_pid:
                print "Killing imagej"

                # Different kill methods for windows and linux
                if _platform == "linux" or _platform == "linux2":
                    print "Killing"
                    print self.imagej_pid
                    os.kill(int(self.imagej_pid), signal.SIGKILL)
                    self.emit(QtCore.SIGNAL('update(QString)'), "Processing Cancelled!")

                elif _platform == "win32" or _platform == "win64":
                    proc = subprocess.Popen(["taskkill", "/f", "/t", "/im", str(self.imagej_pid)],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (out, err) = proc.communicate()
                    if out:
                        print "program output:", out
                    if err:
                        print "program error output:", err

                # Update the GUI again just in case it took a while.
                self.emit(QtCore.SIGNAL('update(QString)'), "Processing Cancelled!")
        except OSError as e:
            print("os.kill could not kill process, reason: {0}".format(e))


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()
