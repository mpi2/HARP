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

import autocrop
from config import ConfigClass
#from vtkRenderAnimation import Animator
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
        self.session_log = open(self.session_log_path, 'w+')

        #logging if there is an error with scaling
        self.scale_error = None


        self.session_log.write("########################################\n")
        self.session_log.write("### HARP Session Log                 ###\n")
        self.session_log.write("########################################\n")
        # start time
        self.session_log.write(str(datetime.datetime.now())+"\n")
        #self.session_log.flush()
        #===============================================
        # Cropping
        #===============================================
        self.cropping()

        # scaling, compression file copying is then done after the cropping finished signal is
        # caught in the function "autocrop_update_slot"


    def cropping(self):
        '''
        Performs cropping procedures. If the option "no crop" or "old crop" was used by the user no cropping will be peformed
        '''
        # Make crop folder
        self.session_log.write("*****Performing cropping******\n")
        self.folder_for_scaling = self.configOb.cropped_path

        # Do not perform any crop as user specified
        if self.configOb.crop_option == "No_crop" :
            self.emit( QtCore.SIGNAL('update(QString)'), "No Crop carried out" )
            #print "No crop carried out"
            self.session_log.write("No crop carried out\n")
            self.autocrop_update_slot("success")

            self.folder_for_scaling = self.configOb.input_folder

            return

        if self.configOb.crop_option == "Old_crop" :
            self.emit( QtCore.SIGNAL('update(QString)'), "No Crop carried out" )
            #print "No crop carried out"
            self.session_log.write("No crop carried out\n")
            self.autocrop_update_slot("success")
            return

        # Make new crop directory
        if not os.path.exists(self.configOb.cropped_path):
            os.makedirs(self.configOb.cropped_path)

        # Setup for manual crop (e.g. given dimensions)
        if self.configOb.crop_option == "Manual" :
            self.session_log.write("manual crop\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing manual crop" )
            dimensions_tuple = (int(self.configOb.xcrop), int(self.configOb.ycrop), int(self.configOb.wcrop), int(self.configOb.hcrop))
            derived_cropbox = None

        # Setup for automatic
        if self.configOb.crop_option == "Automatic" :
            self.session_log.write("autocrop\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing autocrop" )
            dimensions_tuple = None
            derived_cropbox = None

        # setup for derived crop
        if self.configOb.crop_option == "Derived" :
            self.session_log.write("Derived crop\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing crop from derived cropbox" )
            dimensions_tuple = None
            try:
                filehandler = open(self.configOb.cropbox_path, 'r')
                cropbox_object = copy.deepcopy(pickle.load(filehandler))
                derived_cropbox = cropbox_object.cropbox
            except IOError as e:
                self.session_log.write("error: Cropbox not available for derived dimension crop:\n"
                                   +"Exception traceback:"+
                                   traceback.format_exc()+"\n")
                self.emit( QtCore.SIGNAL('update(QString)'), "error: Could not open cropbox dimension file for "
                                                             "derived dimension crop: "+str(e))
            except Exception as e:
                self.session_log.write("error: Unknown exception trying to get derived dimension:\n"
                                   +"Exception traceback:"+
                                   traceback.format_exc()+"\n")
                self.emit( QtCore.SIGNAL('update(QString)'), "error: Unknown exception trying to get derived dimension"
                                                             " (see log): "+str(e))

        self.session_log.write("Crop started\n")
        self.session_log.write(str(datetime.datetime.now())+"\n")

        # make autocrop object
        self.auto_crop = autocrop.Autocrop(self.configOb.input_folder, self.configOb.cropped_path,
                                           self.autocrop_update_slot,  def_crop=dimensions_tuple,
                                           repeat_crop = derived_cropbox )

        # WindowsError is an execption only available on Windows need to make a fake WindowsError exception for linux
        if not getattr(__builtins__, "WindowsError", None):
            class WindowsError(OSError): pass

        try:
            # Run autocrop and catch errors
            self.auto_crop.run()

        except WindowsError as e:
            self.session_log.write("error: HARP can't find the folder, maybe a temporary problem connecting to the network. Exception message:\n"
                                   +"Exception traceback:"+
                                   traceback.format_exc()+"\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "error: HARP can't find the folder, see log file" )

        # except TypeError as e:
        #     # This is referring to an error in either the functions run_crop_process or init_cropping. Possibly the exception would be more beneficial
        #     # placed directly in autocrop....
        #     self.session_log.write("error: HARP most likely can't find the folder, maybe a temporary problem connecting to the network. Exception message:\n"
        #                            +"Exception traceback:"+
        #                            traceback.format_exc()+"\n")
        #     self.emit( QtCore.SIGNAL('update(QString)'), "error: HARP can't find the files, see log file" )
        #
        # except Exception as e:
        #     self.session_log.write("error: Unknown autocrop exception. Exception message:\n"
        #                            +"Exception traceback:"+
        #                            traceback.format_exc()+"\n")
        #     self.emit( QtCore.SIGNAL('update(QString)'), "error: Unknown autocrop exception (see log): "+str(e))


    def autocrop_update_slot(self, msg):
        """
        Listens to autocrop. If autocrop sends a signal with the message "success" then the next steps in the processing will occur
        """
        # check if a tuple. If it is a tuple it means that the crop box has been sen from the autocrop. Then make
        # a pickle object of the object so it can be used at another point
        if type(msg) == tuple:
            # create our generic class for pickles
            crop_box_ob = ConfigClass()

            # get path
            crop_box_path = os.path.join(self.configOb.meta_path,"cropbox.txt")

            # save cropbox tuple to cropbox object
            crop_box_ob.cropbox = msg

            # save the pickle
            with open(crop_box_path, 'w+') as config:
                pickle.dump(crop_box_ob, config)

            # that's the end of this callback
            return

        else:
            self.emit( QtCore.SIGNAL('update(QString)'), msg)

        if msg == "success":
            print "crop finished"
            print msg
            print self.kill_check
            self.session_log.write("Crop finished\n")
            #self.emit( QtCore.SIGNAL('update(QString)'), "crop finished")

            #===============================================
            # Scaling
            #===============================================
            self.scaling()

            #===============================================
            # Masking/Segmentation
            #===============================================
            #self.masking()

            #===============================================
            # Movies
            #===============================================
            #self.movies()

            #===============================================
            # Copying
            #===============================================
            if not self.configOb.crop_option == "No_crop" or  self.configOb.crop_option == "Old_crop" :
                self.copying()

            #===============================================
            # Compression
            #===============================================
            self.compression()


            if self.scale_error:
                self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished (problems creating some of the scaled stacks, see log file)" )
            else:
                self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished" )

            self.session_log.write("Processing finished\n")
            self.session_log.write("########################################\n")
            self.session_log.close()
            return


        elif re.search("error",msg):
            #self.emit( QtCore.SIGNAL('update(QString)'), msg)
            self.session_log.write("Error in cropping see below:\n")
            self.session_log.write(msg)
            self.session_log.close()
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
                print "Killing imagej"
                if _platform == "linux" or _platform == "linux2":
                    print "Killing"
                    print self.imagej_pid
                    os.kill(int(self.imagej_pid),signal.SIGKILL)
                    self.emit( QtCore.SIGNAL('update(QString)'), "Processing Cancelled!" )
                elif _platform == "win32" or _platform == "win64":
                    proc = subprocess.Popen(["taskkill", "/f", "/t", "/im",str(self.imagej_pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (out, err) = proc.communicate()
                    if out:
                        print "program output:", out
                    if err:
                        print "program error output:", err
                self.emit( QtCore.SIGNAL('update(QString)'), "Processing Cancelled!" )
        except OSError as e:
                print("os.kill could not kill process, reason: {0}".format(e))


    def scaling(self):
        '''
        Scaling
        '''
        if self.kill_check == 1 :
            return

        print "Scaling started"
        self.session_log.write("*****Performing scaling******\n")
        self.session_log.write(str(datetime.datetime.now())+"\n")

        # First make subfolder for scaled stacks
        if not os.path.exists(self.configOb.scale_path):
            os.makedirs(self.configOb.scale_path)

        # Memory of computer being used will depend on how much memory will be used in imageJ
        # e.g 80% total memory of the computer
        self.memory_4_imageJ = (int(self.memory)*.9)
        self.memory_4_imageJ = self.memory_4_imageJ*0.00000095367
        self.memory_4_imageJ = int(self.memory_4_imageJ)
        memory_mb = int(int(self.memory)*0.00000095367)
        self.session_log.write("Total Memory of Computer(mb):"+str(memory_mb)+"\n")
        self.session_log.write("Memory for ImageJ(mb):"+str(self.memory_4_imageJ)+"\n")


        # Perform scaling as subprocess with Popen
        if self.configOb.SF2 == "yes" :
            memory_result = self.memory_check(2)
            if memory_result:
                print "scale by 2 norm"
                self.execute_imagej(2.0)

        if self.configOb.SF3 == "yes" :
            memory_result = self.memory_check(3)
            if memory_result:
                self.execute_imagej(3.0)

        if self.configOb.SF4 == "yes" :
            memory_result = self.memory_check(4)
            if memory_result:
                self.execute_imagej(4.0)

        if self.configOb.SF5 == "yes" :
            memory_result = self.memory_check(5)
            if memory_result:
                self.execute_imagej(5.0)

        if self.configOb.SF6 == "yes" :
            memory_result = self.memory_check(6)
            if memory_result:
                self.execute_imagej(6.0)

        if self.configOb.pixel_option == "yes" :
            memory_result = self.memory_check(self.configOb.SFX_pixel)
            if memory_result:
                self.execute_imagej("Pixel")



    def memory_check(self,scale):
        #self.memory_4_imageJ
        scale_div = float(1.0/scale)

        # If no crop option the memory check is done using data extrapolate from the original recon folder
        if self.configOb.crop_option == "No_crop" :
            crop_folder_size_mb = float(self.configOb.recon_folder_size)*1024.0
            print "Recon folder size to downsize (mb)",crop_folder_size_mb
        else :

            prog = re.compile("(.*)_rec\d+\.(bmp|tif|jpg|jpeg)",re.IGNORECASE)

            filename = ""
            # for loop to go through the directory
            for line in os.listdir(self.folder_for_scaling) :
                line =str(line)
                #print line+"\n"
                # if the line matches the regex break
                if prog.match(line) :
                    filename = line
                    break

            # get the number of files, ignore any non recon files
            num_files = len([f for f in os.listdir(self.configOb.cropped_path) if ((f[-4:] == ".bmp") or (f[-4:] == ".tif") or (f[-4:] == ".jpg") or (f[-4:] == ".jpeg") or
                          (f[-4:] == ".BMP") or (f[-4:] == ".TIF") or (f[-4:] == ".JPG") or (f[-4:] == ".JPEG") and
                          (f[-7:] != "spr.bmp") and (f[-7:] != "spr.tif") and (f[-7:] != "spr.jpg") and (f[-7:] != "spr.jpeg") and
                          (f[-7:] != "spr.BMP") and (f[-7:] != "spr.TIF") and (f[-7:] != "spr.JPG") and (f[-7:] != "spr.JPEG"))])

            # get the size of the file matched previously
            filename = os.path.join(self.folder_for_scaling,filename)
            file1_size = os.path.getsize(filename)

            # approx folder size
            approx_size = num_files*file1_size

            # convert to mb
            crop_folder_size_mb =  (approx_size/(1024*1024.0))


        # Get the approx size of the statck by dividing by x,y ans z of the folder size. e.g. for scaling by 2
        # will be divided by 0.5, 0.5 and 0.5
        memory_for_scale = crop_folder_size_mb*(scale_div*scale_div*scale_div)

        # Based on a very approximate estimate I have said it will take imagej 4x that of the memory of the approx scaled stack
        memory_for_scale = memory_for_scale*4

        self.num_files = num_files

        # Check if there is enough memory  available.
        if self.memory_4_imageJ < memory_for_scale:
            print "not enough memory"
            self.session_log.write("Not enough memory for this scaling\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Not enough memory for scaling\n" )
            fail_file_name = os.path.join(self.configOb.scale_path,"insufficient_memory_for_scaling_"+str(scale))
            fail_file = open(fail_file_name, 'w+')
            fail_file.close()
            self.scale_error = True
            return False
        else :
            # enough memory
            return True



    def execute_imagej(self, sf):
        '''
        Part of scaling function
        @param: str, scaleFactor for imagej eg "^0.5^x6"
        @param: str, sf for calculating new pixel size
        '''
        print "kill check"
        if self.kill_check == 1 :
            return

        # Setup a logging file
        self.scale_log_path = os.path.join(self.configOb.meta_path,str(sf)+"_scale.log")
        self.session_scale = open(self.scale_log_path, 'w+')

        print "pixel check"
        # Gets the new pixel numbers for the scaled stack name (see in imagej macro)
        if (self.configOb.recon_pixel_size) and sf != "Pixel":
            new_pixel = float(self.configOb.recon_pixel_size)*float(sf)
            new_pixel = str(round(new_pixel,4))
            interpolation = "default"

        elif self.configOb.pixel_option == "yes" :
            sf = self.configOb.SFX_pixel
            new_pixel = self.configOb.user_specified_pixel

            interpolation = "yes"
        else :
            new_pixel = "NA"
            interpolation = "default"

        # Dont think this is required
        #new_pixel = str(new_pixel).replace('.', '-')

        # Get the scaling factor in decimal
        dec_sf = round((1/sf),4)

        print "ij path check"
        # ij path if run from executable
        ijpath = os.path.join('..','..','ImageJ', 'ij.jar')
        if not os.path.exists(ijpath):
            #ij path if ran from script
            ijpath = os.path.join(self.dir,'ImageJ', 'ij.jar')

        if not os.path.exists(ijpath):
            self.emit( QtCore.SIGNAL('update(QString)'), "Error: Can't find Imagej" )
            self.kill_check =  1
            return

        # Macro path if run from exectutable
        ij_macro_path = os.path.join('..','..', "siah_scale.txt")
        if not os.path.exists(ij_macro_path):
            ij_macro_path = os.path.join(self.dir, "siah_scale.txt")

        ij_macro_path_low_mem1 = os.path.join('..','..', "siah_scale_low_mem1.txt")
        if not os.path.exists(ij_macro_path_low_mem1):
            ij_macro_path_low_mem1 = os.path.join(self.dir, "siah_scale_low_mem1.txt")

        ij_macro_path_low_mem2 = os.path.join(self.dir, "siah_scale_low_mem2.txt")
        if not os.path.exists(ij_macro_path_low_mem2):
            ij_macro_path_low_mem2 = os.path.join('..','..', "siah_scale_low_mem2.txt")

        if not os.path.exists(ij_macro_path):
            self.emit( QtCore.SIGNAL('update(QString)'), "error: Can't find Imagej macro script" )
            self.kill_check =  1
            return

        # detail scaling in log
        self.session_log.write("Scale by factor:\n")
        self.session_log.write(str(sf))
        self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(str(sf)) )

        print "norm scaling"
        # file name
        file_name = os.path.join(self.configOb.scale_path,self.configOb.full_name+"_scaled_"+str(sf)+"_pixel_"+new_pixel+".tif")
        # Subprocess call for imagej macro
        process = subprocess.Popen(["java", "-Xmx"+str(self.memory_4_imageJ)+"m", "-jar", ijpath, "-batch", ij_macro_path,
                                    self.configOb.imageJ + "^" + str(dec_sf) + "^" + interpolation + "^" + file_name],
                                   stdout=self.session_scale,stderr=self.session_scale)
        #record a process ID incase we need to kill imagej
        self.imagej_pid = str(process.pid)

        #NOTE: process.communicate catches when processing is finished
        # I dont think the out and error variables work here as we already assigned stderr and stdout in the subprocess call
        out, err = process.communicate()

        print process.returncode

        # check if there was a memory problem then repeat as low memory version
        result = self.scale_error_check("norm",sf)

        # If a non-memory error occured call it a day for this one
        if self.scale_error == True:
            return

        if result == "repeat":
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing low memory scaling ({})".format(str(sf)) )
            # reset the scaling log
            self.session_scale.close()
            self.session_scale = open(self.scale_log_path, 'w+')
            print "low mem version"
            # Subprocess call for imagej macro
            # First x and y scaling and save a temp stack
            temp_folder = os.path.join(self.configOb.scale_path,"tmp")
            if not os.path.exists(temp_folder):
                os.mkdir(temp_folder)

            process = subprocess.Popen(["java", "-Xmx"+str(self.memory_4_imageJ)+"m", "-jar", ijpath, "-batch", ij_macro_path_low_mem1,
                                    self.configOb.imageJ + "^" + str(dec_sf) + "^" + interpolation + "^" + temp_folder+os.sep + "^"],
                                   stdout=self.session_scale,stderr=self.session_scale)
            # record a pid so we can kill
            self.imagej_pid = str(process.pid)
            # recognises when the process has finished and then continues with script
            out, err = process.communicate()
            # check if any erros occured
            print "done first part"
            self.scale_error_check("low",sf)
            if self.scale_error == True:
                print "error"
                shutil.rmtree(temp_folder)
                return

            print "second part of scaling"
            file_name = os.path.join(self.configOb.scale_path,self.configOb.full_name+"_scaled_"+str(sf)+"_pixel_"+new_pixel+".tif")

            process2 = subprocess.Popen(["java", "-Xmx"+str(self.memory_4_imageJ)+"m", "-jar", ijpath, "-batch", ij_macro_path_low_mem2,
                                    temp_folder+os.sep + "^" + str(dec_sf) + "^" + interpolation + "^" + file_name + "^" + str(self.num_files) + "^"],
                                   stdout=self.session_scale,stderr=self.session_scale)

            self.imagej_pid = str(process2.pid)
            # recognises when the process has finished and then continues with script
            out, err = process2.communicate()
            # check if any erros occured
            self.scale_error_check("low",sf)
            shutil.rmtree(temp_folder)
            self.session_scale.close()



    def scale_error_check(self,mem_opt,sf):

        # But we reopen for just reading, also goes back to the start
        self.session_scale_check = open(self.scale_log_path, "r")

        # reset processing ID, as processing has finished.
        self.imagej_pid = ""

        # Check the self.session_scale file for memory or any other problem messages
        prog1 = re.compile("<Out of memory>")
        prog2 = re.compile(">>>>>>>>>>>>>>>>>>>>>>>>>>>")
        out_of_memory = None
        other_ij_problem = None

        print "check mem prob"
        # First check for memory problems
        for line in self.session_scale_check:
            # "chomp" the line endings off
            line = line.rstrip()
            # if the line matches the regex print the (\w+.\w+) part of regex
            if prog1.match(line) :
                # Grab the pixel size with with .group(1)
                out_of_memory = True
                break

        print "check other probs"
        # Then check for any other problems.
        for line in self.session_scale_check:
            # "chomp" the line endings off
            line = line.rstrip()
            # if the line matches the regex print the (\w+.\w+) part of regex
            if prog2.match(line) :
                # Grab the pixel size with with .group(1)
                other_ij_problem  = True
                break


        if out_of_memory and mem_opt=="norm":
            # Dont use the word "error" in the signal message. If "error" is used HARP might skip any further processing for this
            # HARP processing list.
            self.emit( QtCore.SIGNAL('update(QString)'),
                       "Problem in scaling. Not enough memory will try low memory version\n" )
            self.session_scale.write("Error in scaling will try low memory version\n")
            # return "repeat" so processing starts again with low memory
            return "repeat"

        elif out_of_memory and mem_opt== "low":
            self.emit( QtCore.SIGNAL('update(QString)'), "Problem in scaling. Not enough memory\n" )
            self.session_log.write("Error in scaling\n")
            fail_file_name = os.path.join(self.configOb.scale_path,"insufficient_memory_for_scaling_"+str(sf))
            fail_file = open(fail_file_name, 'w+')
            fail_file.close()
            self.scale_error = True

        elif other_ij_problem:
            self.emit( QtCore.SIGNAL('update(QString)'), "Problem in scaling. Check log file\n" )
            self.session_scale.write("Error in scaling\n")
            fail_file_name = os.path.join(self.configOb.scale_path,"error_performing_scaling_by_"+str(sf))
            fail_file = open(fail_file_name, 'w+')
            fail_file.close()
            self.scale_error = True
        else:
            self.session_log.write("Finished scaling\n")


    def movies(self):
        '''
        movies: todo
        '''
        movie_path = os.path.join(self.configOb.output_folder,"movies")
        if not os.path.exists(movie_path):
            os.makedirs(movie_path)

        print "starting movies"

        for file in range(len(self.scale_array)):

            print self.scale_array[file]
            movie = Animator(str(file),movie_path)

        #self.scale_array.
        #movie = Animator(self., out_dir)

    def masking(self):
        '''
        masking: todo
        '''
        print "masking"


    def copying(self):
        '''
        Copying
        '''
        if self.kill_check == 1 :
            return

        self.emit( QtCore.SIGNAL('update(QString)'), "Copying files\n" )

        self.session_log.write("***Copying other files from original recon***\n")
        self.session_log.write(str(datetime.datetime.now())+"\n")
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
        if self.kill_check == 1 :
            return

        if self.configOb.scans_recon_comp == "yes" or self.configOb.crop_comp == "yes" :
            self.session_log.write("***Performing Compression***")
            self.session_log.write(str(datetime.datetime.now())+"\n")

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

        if  self.configOb.crop_comp == "yes":
            if self.configOb.crop_option != "No_crop":
                self.emit( QtCore.SIGNAL('update(QString)'), "Compression of cropped recon started" )
                out = tarfile.open(self.configOb.cropped_path+"_"+self.configOb.full_name+".tar.bz2", mode='w:bz2')
                out.add(self.configOb.cropped_path, arcname="Cropped")
                out.close()





def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()
