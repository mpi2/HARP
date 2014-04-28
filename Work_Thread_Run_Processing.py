from PyQt4 import QtGui, QtCore
import sys
import subprocess
import os, signal
import re
import pickle
import pprint
import time
import shutil
import logging
import logging.handlers
import tarfile
import autocrop
import cPickle as pickle
import ConfigClass
from multiprocessing import freeze_support
from sys import platform as _platform
#from Segmentation import watershed_filter

class WorkThreadProcessing(QtCore.QThread):
    def __init__(self,configOb,memory, parent=None):
        QtCore.QThread.__init__(self, parent)
        #self.exec_() #need thos for self.quit() to work
        filehandler = open(configOb, 'r')
        self.configOb = pickle.load(filehandler)
        self.memory = memory
        self.scale_array = []

    def __del__(self):
        print "Processing stopped"

    def run(self):
        #===============================================
        # Start processing!
        #===============================================
        self.emit( QtCore.SIGNAL('update(QString)'), "Started Processing" )
        # Get the directory of the script
        if getattr(sys, 'frozen', False):
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        # Need to reset global parameter
        autocrop.reset()

        #===============================================
        # Setup logging files
        #===============================================
        self.session_log_path = os.path.join(self.configOb.meta_path,"session.log")
        self.pid_log_path = os.path.join(self.configOb.meta_path,"pid.log")
        self.scale_log_path = os.path.join(self.configOb.meta_path,"scale.log")

        self.session_pid = open(self.pid_log_path, 'w+')
        self.session_scale = open(self.scale_log_path, 'w+')
        self.session_log = open(self.session_log_path, 'w+')


        self.session_log.write("########################################\n")
        self.session_log.write("### HARP Session Log                 ###\n")
        self.session_log.write("########################################\n")

        #===============================================
        # Cropping
        #===============================================
        self.cropping()

        # scaling, compression file copying is then done after the cropping finished signal is
        # caught in the function "autocrop_finished_slot"


    def cropping(self):
        '''
        Cropping
        '''
        # Make crop folder
        self.session_log.write("*****Performing cropping******\n")

        # Do not perform any crop as user specified
        if self.configOb.crop_option == "None" :
            self.emit( QtCore.SIGNAL('update(QString)'), "No Crop carried out" )
            #print "No crop carried out"
            self.session_log.write("No crop carried out\n")
            return

        # Make new crop directory
        if not os.path.exists(self.configOb.cropped_path):
            os.makedirs(self.configOb.cropped_path)

        # Setup for manual crop (e.g. given dimensions)
        if self.configOb.crop_option == "Manual" :
            self.session_log.write("manual crop\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing manual crop" )
            dimensions_tuple = (int(self.configOb.xcrop), int(self.configOb.ycrop), int(self.configOb.wcrop), int(self.configOb.hcrop))

        # Setup for automatic
        if self.configOb.crop_option == "Automatic" :
            self.session_log.write("autocrop\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing autocrop" )
            dimensions_tuple = None

        self.autoCropThread = autocrop.Autocrop(self.configOb.input_folder, self.configOb.cropped_path, self.autocropUpdateSlot, self.autocrop_finished_slot,  def_crop=dimensions_tuple)
        self.autoCropThread.run()
        self.session_log.write("Crop started\n")


    def autocropUpdateSlot(self, msg):
        self.emit( QtCore.SIGNAL('update(QString)'), msg )


    def autocrop_finished_slot(self, msg):
        #print("autocrop all done")
        #         crop_result = acrop.run()

        if msg == "success":

            self.session_log.write("Crop finished\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "crop finished")

            #===============================================
            # Scaling
            #===============================================
            self.scaling()

            #===============================================
            # Masking/Segmentation
            #===============================================
            #self.masking()

            #===============================================
            # Copying
            #===============================================
            self.copying()

            #===============================================
            # Compression
            #===============================================
            self.compression()

            self.session_log.close()
            return
        else :
            self.emit( QtCore.SIGNAL('update(QString)'), msg)
            self.session_log.write("Error in cropping see below:\n")
            self.session_log.write(msg)

    def killSlot(self):
        # Kills autocrop
        print("Kill all")
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing Cancelled!" )
        autocrop.terminate()
        # Kills the Work_Thread_Run_Processing thread (hopefully)
        self.quit()
        #self.wait() #this was hanging the GUI


#     def masking(self):
#         '''
#         Masking
#         '''
#         #watershed_filter()
#         print self.scale_array


    def scaling(self):
        '''
        Scaling
        '''
        self.session_log.write("*****Performing scaling******\n")
        # First make subfolder for scaled stacks
        if not os.path.exists(self.configOb.scale_path):
            os.makedirs(self.configOb.scale_path)

        # Memory of computer being used will depend on how much memory will be used in imageJ
        # e.g 70% of total memory
        self.memory_4_imageJ = (int(self.memory)*.7)*0.00000095367
        self.memory_4_imageJ = int(self.memory_4_imageJ)
        self.session_log.write("Memory of computer:"+str(self.memory)+"\n")
        self.session_log.write("Memory for ImageJ:"+str(self.memory_4_imageJ)+"\n")

        # Perform scaling as subprocess with Popen (they should be done in the background)

        if self.configOb.SF2 == "yes" :
            self.executeImagej("^0.5^x2^","2")

        if self.configOb.SF3 == "yes" :
            self.executeImagej("^0.3333^x3^","3")

        if self.configOb.SF4 == "yes" :
            self.executeImagej("^0.25^x4^","4")

        if self.configOb.SF5 == "yes" :
            self.executeImagej("^0.2^x5^","5")

        if self.configOb.SF6 == "yes" :
            self.executeImagej("^0.1667^x6^","6")

        if self.configOb.pixel_option == "yes" :
            self.executeImagej("^"+str(self.configOb.SF_pixel)+"^x"+str(self.configOb.SFX_pixel)+"^","Pixel")


    def executeImagej(self, scaleFactor,sf):
        '''
        Part of scaling function
        @param: str, scaleFactor for imagej eg "^0.5^x6"
        @param: str, sf for calculating new pixel size
        '''
        # Gets the new pixel numbers for the scaled stack name (see in imagej macro)
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

        # Linux or win32 imagej jar location
        if _platform == "linux" or _platform == "linux2":
            ijpath = os.path.join("/usr","share","java","ij.jar")
        elif _platform == "win32" or _platform == "win64":
            ijpath = os.path.join(self.dir, 'ImageJ', 'ij.jar')

        # detail what is happening
        self.session_log.write("Scale by factor:")
        self.session_log.write(str(sf))
        self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(str(sf)) )

        # Make an array of the names to be masked
        file_name = self.configOb.output_folder+self.configOb.full_name+"_scaled_"+scaleFactor+"pixel"+new_pixel+".tif"
        self.scale_array.append(file_name)


        #out_path[1]+arg_array[2]_scaled+arg_array[3]_pixel_+arg_array[4].tif

        # Subprocess call for imagej macro
        process = subprocess.Popen(["java", "-Xmx"+str(self.memory_4_imageJ)+"m", "-jar", ijpath, "-batch", os.path.join(self.dir, "siah_scale.txt"),
                                    self.configOb.imageJ+ scaleFactor + "^" +new_pixel+"^"+interpolation],stdout=self.session_scale,stderr=self.session_scale)

        #Get pid of imagej macro so we can kill if the user finds a problem
        self.session_pid.write(str(process.pid)+"\n")
        out, err = process.communicate()

        logging.info("Finished scaling")

    def copying(self):
        '''
        Copying
        '''
        logging.debug("Copying other files from original recon")
        for file in os.listdir(self.configOb.input_folder):
            #check if folder before copying
            if os.path.isdir(os.path.join(self.configOb.input_folder,file)):
                # Dont copy the sub directory move to the next itereration
                continue
            elif not os.path.exists(os.path.join(self.configOb.cropped_path,file)):
                # File exists so copy it over to the crop folder
                # Need to get full path of original file though
                file = os.path.join(self.configOb.input_folder,file)
                shutil.copy(file,self.configOb.cropped_path)
                self.session_log.write("File copied:"+file)

    def compression(self):
        '''
        Compression
        '''
        if self.configOb.scans_recon_comp == "yes" or self.configOb.crop_comp == "yes" :
            self.session_log.write("***Performing Compression***")

        if self.configOb.scans_recon_comp == "yes" :
            # Compression for scan
            if self.configOb.scan_folder:
                self.emit( QtCore.SIGNAL('update(QString)'), "Performing compression of scan folder" )
                self.session_log.write("Compression of scan folder")
                path_scan,folder_name_scan = os.path.split(self.configOb.scan_folder)

                out = tarfile.open(str(self.configOb.scan_folder)+".tar.bz2", mode='w:bz2')
                out.add(path_scan, arcname="Scan_folder")
                out.close()
                self.emit( QtCore.SIGNAL('update(QString)'), "Compression of scan folder finished" )

            # compression for scan
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing compression of original recon folder" )
            self.session_log.write("Compression of original recon folder")
            path_scan,folder_name_scan = os.path.split(self.configOb.input_folder)

            out = tarfile.open(str(self.configOb.input_folder)+".tar.bz2", mode='w:bz2')
            out.add(path_scan, arcname="Input_folder")
            out.close()
            self.emit( QtCore.SIGNAL('update(QString)'), "Compression of recon folder finished" )

        # compression for crop folder
        if  self.configOb.crop_comp == "yes":
            if self.configOb.crop_option != "No_crop":
                self.emit( QtCore.SIGNAL('update(QString)'), "Compression of cropped recon started" )
                out = tarfile.open(self.configOb.cropped_path+"_"+self.configOb.full_name+".tar.bz2", mode='w:bz2')
                out.add(self.configOb.cropped_path, arcname="Cropped")
                out.close()

        self.session_scale.close()
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished" )
        self.session_pid.close()
        # Presume processes finished so clear PID file
        open(self.pid_log_path, 'w').close()

        self.session_scale.close()
        self.session_log.write("Processing finished\n")
        self.session_log.write("########################################\n")


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()
