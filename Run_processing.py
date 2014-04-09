from PyQt4 import QtGui, QtCore
import sys
import subprocess
import os, signal
import re
import pickle
import pprint
import time
import shutil
import uuid
import logging
import logging.handlers
import tarfile
import autocrop
import cPickle as pickle
import ConfigClass
from multiprocessing import freeze_support
from sys import platform as _platform


class WorkThread(QtCore.QThread):
    def __init__(self,configOb,memory):
        QtCore.QThread.__init__(self)
        filehandler = open(configOb, 'r')
        self.configOb = pickle.load(filehandler)
        self.memory = memory

    def __del__(self):
        self.wait()

    def run(self):

        self.emit( QtCore.SIGNAL('update(QString)'), "Started Processing" )
        # Get the directory of the script
        if getattr(sys, 'frozen', False):
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        # Get the session log files
        self.session_log_path = os.path.join(self.configOb.meta_path,"session.log")
        self.pid_log_path = os.path.join(self.configOb.meta_path,"pid.log")
        self.scale_log_path = os.path.join(self.configOb.meta_path,"scale.log")

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(self.session_log_path)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logging.debug("########################################")
        logging.debug("### HARP Session Log                 ###")
        logging.debug("########################################")

        #if os.path.exists(self.session_log_path):
            #os.remove(self.session_log_path)

        logging.debug("Creating files")
        #session = open(self.session_log_path, 'w+')
        session_pid = open(self.pid_log_path, 'w+')
        session_scale = open(self.scale_log_path, 'w+')



        ###############################################
        # Cropping
        ###############################################
        # Make crop folder
        # get cropped path from config object (shorten it so it is easier to read)
        logging.debug("*****Performing cropping******")
        cropped_path = self.configOb.cropped_path

        if not os.path.exists(cropped_path):
            os.makedirs(cropped_path)

        crop_run = os.path.join(self.dir, "autocrop.py")
        #print crop_run
        if self.configOb.crop_option == "Manual" :
            logging.debug("manual crop")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing manual crop" )
            dimensions_tuple = (int(self.configOb.xcrop), int(self.configOb.ycrop), int(self.configOb.wcrop), int(self.configOb.hcrop))
            #print dimensions_tuple
            crop_result = autocrop.run(self.configOb.input_folder,cropped_path,def_crop=dimensions_tuple)
            if crop_result :
                logging.debug("Error in cropping see below:")
                logging.debug(crop_result)
                self.emit( QtCore.SIGNAL('update(QString)'), "Cropping Error, see session log file")
                return

            self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )
            logging.debug("Crop finished")

        # Perform the automatic crop if required
        if self.configOb.crop_option == "Automatic" :
            logging.debug("autocrop")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing autocrop" )

            crop_result = autocrop.run(self.configOb.input_folder,cropped_path)

            if crop_result :
                logging.debug("Error in cropping see below:")
                logging.debug(crop_result)
                self.emit( QtCore.SIGNAL('update(QString)'), "Cropping Error, see session log file")
                return

            self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )
            logging.debug("Crop finished")

        # Do not perform any crop as user specified
        if self.configOb.crop_option == "None" :
            self.emit( QtCore.SIGNAL('update(QString)'), "No Crop carried out" )
            #print "No crop carried out"
            logging.debug("No crop carried out")
            session_pid.close()

        ###############################################
        # Compression
        ###############################################
        if self.configOb.scans_recon_comp == "yes" or self.configOb.crop_comp == "yes" :
            logging.debug("***Performing Compression***")

        if self.configOb.scans_recon_comp == "yes" :
            if self.configOb.scan_folder:
                self.emit( QtCore.SIGNAL('update(QString)'), "Performing compression of scan folder" )
                logging.debug("Compression of scan folder")
                path_scan,folder_name_scan = os.path.split(self.configOb.scan_folder)

                out = tarfile.open(str(self.configOb.scan_folder)+".tar.bz2", mode='w:bz2')
                out.add(path_scan, arcname="Scan_folder")
                out.close()
                self.emit( QtCore.SIGNAL('update(QString)'), "Compression of scan folder finished" )

            self.emit( QtCore.SIGNAL('update(QString)'), "Performing compression of original recon folder" )
            logging.debug("Compression of original recon folder")
            path_scan,folder_name_scan = os.path.split(self.configOb.input_folder)

            out = tarfile.open(str(self.configOb.input_folder)+".tar.bz2", mode='w:bz2')
            out.add(path_scan, arcname="Input_folder")
            out.close()
            self.emit( QtCore.SIGNAL('update(QString)'), "Compression of recon folder finished" )

        if  self.configOb.crop_comp == "yes":
            if self.configOb.crop_option != "No_crop":
                self.emit( QtCore.SIGNAL('update(QString)'), "Compression of cropped recon started" )
                out = tarfile.open(cropped_path+"_"+self.configOb.full_name+".tar.bz2", mode='w:bz2')
                out.add(cropped_path, arcname="Cropped")
                out.close()

        ###############################################
        # Scaling
        ###############################################
        logging.debug("*****Performing scaling******")
        # First make subfolder for scaled stacks
        if not os.path.exists(self.configOb.scale_path):
            os.makedirs(self.configOb.scale_path)

        # Memory of computer being used will depend on how much memory will be used in imageJ
        # e.g 70% of total memory
        self.memory_4_imageJ = (int(self.memory)*.7)*0.00000095367
        self.memory_4_imageJ = int(self.memory_4_imageJ)
        logging.debug("Memory of computer:"+str(self.memory))
        logging.debug("Memory for ImageJ:"+str(self.memory_4_imageJ))

        # Perform scaling as subprocess with Popen (they should be done in the background)

        if self.configOb.SF2 == "yes" :
            proSF2 = self.executeImagej("^0.5^x2^",session_pid,session_scale,"2",)

        if self.configOb.SF3 == "yes" :
            proSF3 = self.executeImagej("^0.3333^x3^",session_pid,session_scale,"3")

        if self.configOb.SF4 == "yes" :
            proSF4 = self.executeImagej("^0.25^x4^",session_pid,session_scale,"4")

        if self.configOb.SF5 == "yes" :
            proSF5 = self.executeImagej("^0.2^x5^",session_pid,session_scale,"5")

        if self.configOb.SF6 == "yes" :
            proSF6 = self.executeImagej("^0.1667^x6^",session_pid,session_scale,"6")

        if self.configOb.pixel_option == "yes" :
            propixel = self.executeImagej("^"+str(self.configOb.SF_pixel)+"^x"+str(self.configOb.SFX_pixel)+"^",session_pid,session_scale,"Pixel")


        ###############################################
        # Copying of other files from recon directory
        ###############################################
        logging.debug("Copying other files from recon")
        for file in os.listdir(self.configOb.input_folder):
            if os.path.isdir(file):
                continue
            path,file = os.path.split(file)
            if not os.path.exists(os.path.join(cropped_path,file)):
                logging.debug("File copied:"+file)
                file = os.path.join(self.configOb.input_folder,file)
                #check if folder before cpoyinng
                shutil.copy(file,cropped_path)

        session_scale.close()
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished" )
        session_pid.close()
        # Presume processes finished so clear PID file
        open(self.pid_log_path, 'w').close()

        session_scale.close()
        logging.debug("Processing finished")
        logging.debug("########################################")
        logger.handlers[0].stream.close()
        logger.removeHandler(logger.handlers[0])
        logging.shutdown()


    def executeImagej(self, scaleFactor,session_pid,session_scale,sf):
        '''
        @param: str, scaleFactor eg ":0.5"
        '''
        if (self.configOb.recon_pixel_size) and sf != "Pixel":
            new_pixel = float(self.configOb.recon_pixel_size)*float(sf)
            new_pixel = str(round(new_pixel,4))
            interpolation = "default"
        elif self.configOb.pixel_option == "yes" :
            new_pixel = self.configOb.user_specified_pixel
            interpolation = "yes"
        else :
            new_pixel = "NA"
            interpolation = "default"


        # for saving pid again (used to kill processes)
        session_pid = open(self.pid_log_path, 'a+')

        if _platform == "linux" or _platform == "linux2":

            logging.info("Scale by factor:")
            logging.info(str(sf))
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(str(sf)) )

            process = subprocess.Popen(["java", "-Xmx"+str(self.memory_4_imageJ)+"m", "-jar", "/usr/share/java/ij.jar", "-batch", os.path.join(self.dir, "siah_scale.txt"),
                                    self.configOb.imageJ+ scaleFactor + "^" +new_pixel+"^"+interpolation],stdout=session_scale,stderr=session_scale)
            session_pid.write(str(process.pid)+"\n")
            session_pid.close()
            out, err = process.communicate()

            logging.info("Finished scaling")

        elif _platform == "win32" or _platform == "win64":

            logging.info("Scale by factor:")
            logging.info(str(sf))
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(str(sf)) )

            ijpath = os.path.join(self.dir, 'ImageJ', 'ij.jar')

            ij_macro_path = os.path.join(self.dir, 'ImageJ', 'macros',"siah_scale.txt")
            process = subprocess.Popen(["java", "-Xmx"+str(self.memory_4_imageJ)+"m", "-jar","-jar", ijpath, "-batch", os.path.join(self.dir, "siah_scale.txt"),
                                    self.configOb.imageJ + scaleFactor + "^" +new_pixel+"^"+interpolation],stdout=session_scale,stderr=session_scale)
            session_pid.write(str(process.pid)+"\n")
            session_pid.close()
            out, err = process.communicate()
            logging.info("Finished scaling")


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()
