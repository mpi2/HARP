from PyQt4 import QtGui, QtCore
import sys
import subprocess
import os, signal
import re
try:
    import cPickle as pickle
except ImportError:
    import pickle
import pprint
import time
import shutil
import tarfile
import autocrop
import datetime
import cPickle as pickle
import config
from multiprocessing import freeze_support
from sys import platform as _platform
import copy
#from Segmentation import watershed_filter

class ProcessingThread(QtCore.QThread):
    def __init__(self,configOb,memory, parent=None):
        QtCore.QThread.__init__(self, parent)
        #self.exec_() #need thos for self.quit() to work
        filehandler = open(configOb, 'r')
        self.configOb = copy.deepcopy(pickle.load(filehandler))
        self.memory = copy.deepcopy(memory)
        self.scale_array = []
        self.kill_check = 0
        self.imagej_pid = ""

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


        #===============================================
        # Setup logging files
        #===============================================
        self.session_log_path = os.path.join(self.configOb.meta_path,"session.log")
        self.scale_log_path = os.path.join(self.configOb.meta_path,"scale.log")

        self.session_scale = open(self.scale_log_path, 'w+')
        self.session_log = open(self.session_log_path, 'w+')

        self.session_log.write("########################################\n")
        self.session_log.write("### HARP Session Log                 ###\n")
        self.session_log.write("########################################\n")
        # start time
        self.session_log.write("Time"+str(datetime.datetime.now())+"\n")
        #self.session_log.flush()
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

        self.session_log.write("Crop started\n")
        ts = time.time()
        stime = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.session_log.write("Time"+stime+"\n")
        self.auto_crop = autocrop.Autocrop(self.configOb.input_folder, self.configOb.cropped_path, self.autocrop_update_slot,  def_crop=dimensions_tuple)
        self.auto_crop.run()


    def autocrop_update_slot(self, msg):
        #print("autocrop all done")
        #         crop_result = acrop.run()

        self.emit( QtCore.SIGNAL('update(QString)'), msg)

        if msg == "success":

            self.session_log.write("Crop finished\n")
            self.session_log.write("Time"+str(datetime.datetime.now())+"\n")
            #self.emit( QtCore.SIGNAL('update(QString)'), "crop finished")

            #===============================================
            # Scaling
            #===============================================
            if self.kill_check== 1 :
                return
            else :
                self.scaling()
                self.session_log.write("Time"+str(datetime.datetime.now())+"\n")

            #===============================================
            # Masking/Segmentation
            #===============================================
            #self.masking()

            #===============================================
            # Copying
            #===============================================
            if self.kill_check== 1 :
                return
            else :
                self.copying()
                self.session_log.write("Time"+str(datetime.datetime.now())+"\n")

            #===============================================
            # Compression
            #===============================================
            if self.kill_check== 1 :
                return
            else :
                self.compression()

            self.session_log.close()
            return

        elif re.search("error",msg):
            #self.emit( QtCore.SIGNAL('update(QString)'), msg)
            self.session_log.write("Error in cropping see below:\n")
            self.session_log.write(msg)
            return

    def kill_slot(self):
        # Kills autocrop
        print("Kill all")
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing Cancelled!" )
        autocrop.terminate()
        # Kills the Work_Thread_Run_Processing thread (hopefully)
        self.kill_check =  1


        try :
            if self.imagej_pid :
                if _platform == "linux" or _platform == "linux2":
                    print "Killing"
                    print self.imagej_pid
                    os.kill(int(self.imagej_pid),signal.SIGKILL)
                elif _platform == "win32" or _platform == "win64":
                    proc = subprocess.Popen(["taskkill", "/f", "/t", "/im",str(self.imagej_pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (out, err) = proc.communicate()
                    if out:
                        print "program output:", out
                    if err:
                        print "program error output:", err
        except OSError as e:
                print("os.kill could not kill process, reason: {0}".format(e))

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
        self.session_log.write(str(os.listdir(self.configOb.input_folder)))
        self.session_log.write("\n")
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
            self.execute_imagej("^0.5^x2^","2")

        if self.configOb.SF3 == "yes" :
            self.execute_imagej("^0.3333^x3^","3")

        if self.configOb.SF4 == "yes" :
            self.execute_imagej("^0.25^x4^","4")

        if self.configOb.SF5 == "yes" :
            self.execute_imagej("^0.2^x5^","5")

        if self.configOb.SF6 == "yes" :
            self.execute_imagej("^0.1667^x6^","6")

        if self.configOb.pixel_option == "yes" :
            self.execute_imagej("^"+str(self.configOb.SF_pixel)+"^x"+str(self.configOb.SFX_pixel)+"^","Pixel")


    def execute_imagej(self, scaleFactor,sf):
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
        self.session_log.write("Scale by factor:\n")
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
        self.imagej_pid = str(process.pid)
        out, err = process.communicate()
        self.imagej_pid = ""

        self.session_log.write("Finished scaling\n")

    def copying(self):
        '''
        Copying
        '''
        self.session_log.write("***Copying other files from original recon***\n")
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
                self.session_log.write("File copied:"+file+"\n")

    def compression(self):
        '''
        Compression
        '''
        if self.configOb.scans_recon_comp == "yes" or self.configOb.crop_comp == "yes" :
            self.session_log.write("***Performing Compression***")

        if self.kill_check== 1 :
            return
        else:
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

                    if self.kill_check== 1 :
                        return
                    else :
                        # compression for scan
                        self.emit( QtCore.SIGNAL('update(QString)'), "Performing compression of original recon folder" )
                        self.session_log.write("Compression of original recon folder")
                        path_scan,folder_name_scan = os.path.split(self.configOb.input_folder)

                        out = tarfile.open(str(self.configOb.input_folder)+".tar.bz2", mode='w:bz2')
                        out.add(path_scan, arcname="Input_folder")
                        out.close()
                        self.emit( QtCore.SIGNAL('update(QString)'), "Compression of recon folder finished" )

        # compression for crop folder
        if self.kill_check== 1 :
            return
        else :
            if  self.configOb.crop_comp == "yes":
                if self.configOb.crop_option != "No_crop":
                    self.emit( QtCore.SIGNAL('update(QString)'), "Compression of cropped recon started" )
                    out = tarfile.open(self.configOb.cropped_path+"_"+self.configOb.full_name+".tar.bz2", mode='w:bz2')
                    out.add(self.configOb.cropped_path, arcname="Cropped")
                    out.close()

        self.session_scale.close()
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished" )

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
