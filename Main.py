#!/usr/bin/python
# Import PyQT module
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSlot,SIGNAL,SLOT
# Import MainWindow class from QT Designer
from MainWindow import *
from Progress import *
from ErrorMessage import *
import zproject
import crop

#from RunProcessing import *
import sys
import subprocess
import os
import re
# cPickle is faster than pickel and is pretty much the same
import pickle
import pprint
import time
import shutil
import uuid


class MainWindow(QtGui.QMainWindow):
    '''
    Class to provide the main window for the Image processing GUI.
    Basically extend the QMainWindow class (from MainWindow.py) generated by QT Designer

    Also shows a dialog box after a submission the dialog box will then keep a track of the
    image processing (not yet developed).
    '''

    def __init__(self):
       '''  Constructor: Checks for buttons which have been pressed and responds accordingly. '''

       # Standard setup of class from qt designer Ui class
       super(MainWindow, self).__init__()
       self.ui=Ui_MainWindow()
       self.ui.setupUi(self)

       # Make unique ID if this is the first time mainwindow has been called
       self.unique_ID = uuid.uuid1()
       print "ID for session:"+str(self.unique_ID)
       self.ID_folder = os.path.join("/tmp","siah",str(self.unique_ID))
       # Make a unique folder in the tmp directory which will store tracking information
       os.makedirs(self.ID_folder)

       # Initialise modality variable
       self.modality = "Not_selected"
       self.selected = "Not_selected"
       self.error = "None"
       self.stop = None

       # get input folder
       self.ui.pushButtonInput.clicked.connect(self.selectFileIn)

       # Get output folder
       self.ui.pushButtonOutput.clicked.connect(self.selectFileOut)

       # OPT selection
       self.ui.radioButtonOPT.clicked.connect(self.getOPTonly)

       # uCT selection
       self.ui.radioButtonuCT.clicked.connect(self.getuCTonly)

       # auto-populate based on input folder and modality selection
       self.ui.pushButtonAutopop.clicked.connect(self.autopop)

       # If Go button is pressed move onto track progress dialog box
       self.ui.pushButtonGo.clicked.connect(self.processGo)

       # Set cropping options
       # Auto crop (disable buttons)
       self.ui.radioButtonAuto.clicked.connect(self.manCropOff)
       # No crop (disable buttons)
       self.ui.radioButtonNo.clicked.connect(self.manCropOff)
       # Man crop (enable buttons).
       self.ui.radioButtonMan.clicked.connect(self.manCropOn)
       # If the get dimensions button is pressed the
       self.ui.pushButtonGetDimensions.clicked.connect(self.getDimensions)

       # to make the window visible
       self.show()

    def callback(box):
        print box

    def getDimensions(self):
        ''' Perform a z projection and then allows user to crop based on z projection'''
        #zp = zproject.Zproject(img_dir)
        #self.getDimensions = crop()
        #app = QtGui.QApplication(sys.argv)

        window = MyMainWindow(self.callback, "/home/tom/Desktop/HyperStack0000.bmp")
        window.show()

        #crop.run(self.callback, "/home/tom/Desktop/HyperStack0000.bmp")


    def manCropOff(self):
        ''' disables boxes for cropping manually '''
        self.ui.lineEditX.setEnabled(False)
        self.ui.lineEditY.setEnabled(False)
        self.ui.lineEditW.setEnabled(False)
        self.ui.lineEditH.setEnabled(False)
        self.ui.pushButtonGetDimensions.setEnabled(False)

    def manCropOn(self):
        ''' enables boxes for cropping manually '''
        self.ui.lineEditX.setEnabled(True)
        self.ui.lineEditY.setEnabled(True)
        self.ui.lineEditW.setEnabled(True)
        self.ui.lineEditH.setEnabled(True)
        self.ui.pushButtonGetDimensions.setEnabled(True)


    def getOPTonly(self):
        ''' unchecks uCT box (if checked) and checks OPT group box and creates or edits self.modality '''
        self.ui.groupBoxOPTOnly.setChecked(True)
        self.ui.groupBoxuCTOnly.setChecked(False)
        self.modality = "OPT"

    def getuCTonly(self):
        ''' Simply unchecks OPTT box (if checked) and checks group uCT box and creates or edits self.modality '''
        self.ui.groupBoxOPTOnly.setChecked(False)
        self.ui.groupBoxuCTOnly.setChecked(True)
        self.modality = "MicroCT"

    def folderSizeApprox(self):
        '''
        Gets the approx folder size of the original recon folder and updates the main window with
        this information. Calculating the folder size by going through each file takes a while on janus. This
        function just checks the first recon file and then multiples this by the number of recon files.

        Updates the following qt objects: labelFile, lcdNumberFile

        Creates self.f_size_out_gb: The file size in gb
        '''

        # Get the input folder information
        input = str(self.ui.lineEditInput.text())

        # create a regex get example recon file
        prog = re.compile("(.*)_rec\d+\.bmp")

        try:
            filename = ""
            # for loop to go through the directory
            for line in os.listdir(input) :
                line =str(line)
                print line+"\n"
                # if the line matches the regex print
                if prog.match(line) :
                    filename = line
                    break

            filename = input+"/"+filename
            file1_size = os.stat(filename).st_size

            num_files = len([f for f in os.listdir(input) if ((f[-4:] == ".bmp") or (f[-4:] == ".tif")) and
                          ((f[-7:] != "spr.bmp") or (f[-7:] != "spr.tif"))])

            approx_size = num_files*file1_size

            # convert to gb
            f_size_out =  (approx_size/(1024*1024*1024.0))

            # Save file size as an variable to be used later
            self.f_size_out_gb = "%0.4f" % (f_size_out)

            #Clean up the formatting of gb mb
            self.sizeCleanup(f_size_out,approx_size)
        except:
            self.error = "Unexpected error in folder size calc:", sys.exc_info()[0]
            print "Unexpected error in folder size calc:", sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)


    def sizeCleanup(self,f_size_out,approx_size):
        # Check if size should be shown as gb or mb
        # Need to change file size to 2 decimal places
        if f_size_out < 0.05 :
            # convert to mb
            f_size_out =  (approx_size/(1024*1024.0))
            # make to 2 decimal places
            f_size_out =  "%0.2f" % (f_size_out)
            # change label to show mb
            self.ui.labelFile.setText("Folder size (Mb)")
            # update lcd display
            self.ui.lcdNumberFile.display(f_size_out)
        else :
            # display as gb
            # make to 2 decimal places
            f_size_out =  "%0.2f" % (f_size_out)
            # change label to show mb
            self.ui.labelFile.setText("Folder size (Gb)")
            # update lcd display
            self.ui.lcdNumberFile.display(f_size_out)


    def getName(self):
        '''
        Gets the id from the folder name. Then fills out the text boxes on the main window with the relevant information

        Updates the following qt objects: lineEditDate, ...   ...

        Creates ...
        '''
        # Get input folder
        input = str(self.ui.lineEditInput.text())

        # Get the folder name
        path,folder_name = os.path.split(input)

        try:
            # Need to have exception to catch if the name is not in correct format.
            # If the name is not in the correc format it should flag to the user that this needs to be sorted
            print folder_name.split("_")
            name_list = folder_name.split("_")
            date = name_list[0]
            group = name_list[1]
            age = name_list[2]
            litter = name_list[3]
            zygosity = name_list[4]

            #print date,group,age,litter,zygosity
            self.ui.lineEditDate.setText(date)
            self.ui.lineEditGroup.setText(group)
            self.ui.lineEditAge.setText(age)
            self.ui.lineEditLitter.setText(litter)
            self.ui.lineEditZygosity.setText(zygosity)
            self.ui.lineEditName.setText(folder_name)

            # The full name should be made changable at some point..
            self.full_name = folder_name

        except IndexError as e:
            pass
            self.error = "Warning: Name ID is not in the correct format.\nAutocomplete of name is not possible."
            print "Name incorrect", sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)
            self.full_name = ""

        except:
            self.error = "Auto-populate not possible. Unexpected error:", sys.exc_info()[0]
            print "Auto-populate not possible. Unexpected error:", sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)


    def autouCTOnly(self):
        ''' Automatically fills out the uCT only section    '''
        self.ui.lineEditCTRecon.setText(str(self.recon_log_path))

    def getReconLog(self):
        '''
        Gets the recon log from the original recon folder and gets the pixel size information

        Updates the following qt objects: ... ...   ...

        Creates ...
        '''

        input = str(self.ui.lineEditInput.text())

        # Get the folder name
        path,folder_name = os.path.split(input)

        try:
            # This will change depending on the location of the program (e.g linux/windows and what drive the MicroCT folder is set to)
            recon_log_path = os.path.join(path,folder_name,folder_name+".log")

            # To make sure the path is in the correct format (not sure if necessary
            self.recon_log_path = os.path.abspath(recon_log_path)

            # Open the log file as read only
            recon_log_file = open(self.recon_log_path, 'r')

            # create a regex to pixel size
            prog = re.compile("Pixel Size \(um\)\=(\w+.\w+)")

            # for loop to go through the recon log file
            for line in recon_log_file:
                # "chomp" the line endings off
                line = line.rstrip()
                # if the line matches the regex print the (\w+.\w+) part of regex
                if prog.match(line) :
                    self.pixel_size = prog.match(line).group(1)
                    break
            # Display the number on the lcd display
            self.ui.lcdNumberPixel.display(self.pixel_size)

        except IOError as e:
            self.error = "Error finding recon file. Error:",sys.exc_info()[0]
            print "Error finding recon file",sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)
        except:
            self.error = "Unexpected error:", sys.exc_info()[0]
            print "Unexpected error:", sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)


    def autoFileOut(self):
        ''' Get info for the output file and create a new folder NEED TO ADD CREATE FOLDER FUNCTION
        '''
        try :
            input = str(self.ui.lineEditInput.text())
            # Get the folder name
            path,folder_name = os.path.split(input)

            output_path  = path.replace("recons", "processed recons")
            output_full = os.path.join(output_path,self.full_name)
            print "TESTT"+output_full
            self.ui.lineEditOutput.setText(output_full)

        except:
            self.error = "Unexpected error in getting new folder output name", sys.exc_info()[0]
            print "Unexpected error in getting new folder output name:", sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)

    def autopop(self):
        ''' Runs methods for autopopulation button '''
        input = str(self.ui.lineEditInput.text())

        self.getName()

        if self.error == "None" :
            self.getReconLog()

        if self.error == "None" :
            self.autouCTOnly()

        if self.error == "None" :
            self.autoFileOut()

        if self.error == "None" :
            self.folderSizeApprox()


    def selectFileIn(self):
        ''' Get the info for the selected file'''
        self.fileDialog = QtGui.QFileDialog(self)
        self.ui.lineEditInput.setText(self.fileDialog.getExistingDirectory(self, "Select Directory"))

    def selectFileOut(self):
        ''' Select output folder (this should be blocked as standard'''
        self.fileDialog = QtGui.QFileDialog(self)
        self.ui.lineEditOutput.setText(self.fileDialog.getExistingDirectory(self, "Select Directory"))


    def processGo(self):
        '''
        This will set off all the processing scripts and shows the dialog box to keep track of progress
        '''
        print "\nOpen progress report for user"

        # Get the directory of the script
        dir = os.path.dirname(os.path.abspath(__file__))

        # Perform some checks before any processing is carried out
        self.errorCheck()

        if self.stop != True :

            self.close()

            self.getParamaters()

            # Perform analysis
            subprocess.Popen(["python", dir+"/RunProcessing.py", "-i",self.config_path])

            # Show progress dialog window to keep track of what is being processed
            self.pro = Progress(self.configOb)

            # Run the programs. A script needs to be written to run on linux to run the back end processing



    def errorCheck(self):
        '''
        To check the required inputs for the processing to be run
        '''
        # Get input and output folders (As the text is always from the text box it will hopefully keep track of
        #any changes the user might have made
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        # Input folder contains image files

        if self.ui.checkBoxRF.isChecked():
            print "CheckBox has been checked so file will be replaced\nCreating Output folder"
            shutil.rmtree(outputFolder)
            os.makedirs(outputFolder)
            self.stop = None
        # Check if output folder already exists. Ask if it is ok to overwrite
        elif os.path.exists(outputFolder):
            print "Output folder already exists and user has not approved overwrite"
            # Running dialog box to inform user of options
            self.errorDialog = ErrorMessage("Output folder already exists\n Tick the 'Replace folder button' in the options sections if files are to be replaced")
            self.stop = True
        else :
            print "Creating output folder"
            os.makedirs(outputFolder)
            self.stop = None


        # Check if name has been completed




    def getParamaters(self):
        '''
        Creates the config file for future processing
        '''
        # Get input and output folders (As the text is always from the text box it will hopefully keep track of
        #any changes the user might have made
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        # OS path used for compatibility issues between Linux and windows directory spacing
        self.config_path = os.path.join(outputFolder,"configObject.txt")
        self.log_path = os.path.join(outputFolder,"config4user.log")

        # Create config file and log file
        config = open(self.config_path, 'w')
        log = open(self.log_path, 'w')

        ##### Get cropping option #####
        if self.ui.radioButtonMan.isChecked() :
            xcrop = str(self.ui.lineEditX.text())
            ycrop = str(self.ui.lineEditY.text())
            wcrop = str(self.ui.lineEditW.text())
            hcrop = str(self.ui.lineEditH.text())
            crop = "Manual"
        elif self.ui.radioButtonAuto.isChecked() :
            crop = "Automatic"
        elif self.ui.radioButtonNo.isChecked() :
            crop = "No_crop"

        ##### Get Scaling factors ####
        if self.ui.checkBoxSF2.isChecked() :
            SF2 = "yes"
        else :
            SF2 = "no"

        if self.ui.checkBoxSF3.isChecked() :
            SF3 = "yes"
        else :
            SF3 = "no"

        if self.ui.checkBoxSF4.isChecked() :
            SF4 = "yes"
        else :
            SF4 = "no"

        # If using windows it is important to put \ at the end of folder name
        # Combining scaling and SF into input for imageJ macro
        imageJconfig = outputFolder+'/cropped/:'+outputFolder+'/'

        #### Write to config file ####
        self.configOb = ConfigClass()

        # ID for session
        self.configOb.unique_ID = str(self.unique_ID)
        self.configOb.full_name = self.full_name
        self.configOb.input_folder = inputFolder
        self.configOb.output_folder = outputFolder
        self.configOb.crop_option = str(crop)
        if crop =="Manual" :
            self.configOb.crop_manual = xcrop+" "+ycrop+" "+wcrop+" "+hcrop
        else :
            self.configOb.crop_manual = "Not_applicable"
        self.configOb.imageJ = imageJconfig
        self.configOb.SF2 = SF2
        self.configOb.SF3 = SF3
        self.configOb.SF4 = SF4
        self.configOb.recon_log_file = self.recon_log_path
        self.configOb.recon_folder_size = self.f_size_out_gb
        self.configOb.recon_pixel_size = self.pixel_size

        # write the config information into an easily readable log file
        log.write("Session_ID    "+self.configOb.unique_ID+"\n");
        log.write("full_name    "+self.configOb.full_name+"\n");
        log.write("Input_folder    "+self.configOb.input_folder+"\n");
        log.write("Output_folder    "+self.configOb.output_folder+"\n");
        log.write("Crop_option    "+self.configOb.crop_option+"\n");
        log.write("Crop_manual    "+self.configOb.crop_manual+"\n");
        log.write("Downsize_by_factor_2?    "+self.configOb.SF2+"\n");
        log.write("Downsize_by_factor_3?    "+self.configOb.SF3+"\n");
        log.write("Downsize_by_factor_4?    "+self.configOb.SF4+"\n");
        log.write("ImageJconfig    "+self.configOb.imageJ+"\n");
        log.write("Recon_log_file    "+self.configOb.recon_log_file+"\n");
        log.write("Recon_folder_size   "+self.configOb.recon_folder_size+"\n");
        log.write("Recon_pixel_size  "+self.configOb.recon_pixel_size+"\n");

        # Pickle the class to a file
        pickle.dump(self.configOb, config)

        config.close()
        log.close()

class Progress(QtGui.QDialog):
    '''
    Class to provide the dialog box to monitor current Image processing jobs.
    Basically extend the QDialog class (from Progress.py) generated by QT Designer
    '''

    # Create a constructor
    def __init__(self,param):
       super(Progress, self).__init__()
       self.ui=Ui_Progress()
       self.ui.setupUi(self)
       self.show()

       self.ID_folder = os.path.join("/tmp","siah",str(param.unique_ID))
       print "Check folders"+str(os.listdir(self.ID_folder))
       self.ui.label_1.setText(param.full_name)


       while True:
            time.sleep(0.05)
            value = self.ui.progressBar_1.value() + 1
            self.ui.progressBar_1.setValue(value)
            QtGui.qApp.processEvents()
            if (value >= 30):
                break




class ErrorMessage(QtGui.QDialog):
    '''
    Class to provide the dialog box to show error messages
    '''

    # Create a constructor
    def __init__(self,error):
       super(ErrorMessage, self).__init__()
       self.ui=Ui_DialogErrMessage()
       self.ui.setupUi(self)
       self.show()
       self.replace_folder = None
       # Stop further processing
       self.stop = True

       self.ui.objectNameErrMessage.setText(str(error))

       self.ui.pushButtonOK.clicked.connect(self.errorOK)


    def errorOK(self):
        ''' Action to take place after OK button has been pressed for error message '''
        print "errorOK button has been pressed"

        self.hide()



class ConfigClass :
    '''
    A simple Class is used to transfer config information
    '''
    def __init__(self):

        print "ConfigClass init"



def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
