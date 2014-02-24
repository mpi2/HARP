#!/usr/bin/python
# Import PyQT module
from PyQt4 import QtGui
# Import MainWindow class from QT Designer
from MainWindow import *
from Progress import *
import sys
import subprocess
import os
import re


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
       self.ui.pushButtonGo.clicked.connect(self.process)

       # to make the window visible
       self.show()


    def getOPTonly(self):
        ''' Simply unchecks uCT box (if checked) and checks OPT group box '''
        self.ui.groupBoxOPTOnly.setChecked(True)
        self.ui.groupBoxuCTOnly.setChecked(False)

    def getuCTonly(self):
        ''' Simply unchecks OPTT box (if checked) and checks group uCT box '''
        self.ui.groupBoxOPTOnly.setChecked(False)
        self.ui.groupBoxuCTOnly.setChecked(True)

    def folderSize(self):
        '''
        Gets the folder size of the original recon folder and updates the main window with
        this information.

        Updates the following qt objects: labelFile, lcdNumberFile

        Creates self.f_size_out_gb: The file size in gb
        '''

        # Get the input folder information
        input = str(self.ui.lineEditInput.text())

        # initialise folder size
        folder_size = 0

        # For loop through the input folder
        for (path, dirs, files) in os.walk(input):
            # go through each file in the directories (Takes a while on Janus may have to speed up some how or give a dialog
            # box to show what is happening)
            for file in files:
                filename = os.path.join(path, file)
                folder_size += os.path.getsize(filename)

        # convert to mb
        f_size_out =  (folder_size/(1024*1024*1024.0))

        # Save file size as an object to be used later
        self.f_size_out_gb = "%0.4f" % (f_size_out)

        # Check if size should be shown as gb or mb
        # Need to change file size to 2 decimal places
        if f_size_out < 0.05 :
            # convert to mb
            f_size_out =  (folder_size/(1024*1024.0))
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

        # Not sure whether to have name changeable...
        full_name = date+"_"+group+"_"+age+"_"+litter+"_"+zygosity

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

        # This will change depending on the location of the program (e.g linux/windows and what drive the MicroCT folder is set to)
        recon_log_path = "N:\\MicroCT\\project-IMPC_MCT\\recons\\"+folder_name+"\\"+folder_name+".log"
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

    def autopop(self):
        ''' Runs methods for autopopulation button '''
        input = str(self.ui.lineEditInput.text())
        self.folderSize()
        self.getName()
        self.getReconLog()
        self.autouCTOnly()


    def selectFileIn(self):
        ''' Get the info for the selected file'''
        self.fileDialog = QtGui.QFileDialog(self)
        self.ui.lineEditInput.setText(self.fileDialog.getExistingDirectory(self, "Select Directory"))


    def selectFileOut(self):
        ''' Get info for the output file
        NOTE: !!!!This needs to change in ligh of the 21 Feb meeting!!!!
        '''
        self.fileDialog = QtGui.QFileDialog(self)
        self.ui.lineEditOutput.setText(self.fileDialog.getExistingDirectory(self, "Select Directory"))


    def process(self):
        '''
        This will set off all the processing scripts and shows the dialog box to keep track of progress
        '''
        self.close()
        print "\nOpen progress report for user"
        self.pro = Progress()

        self.getParamaters()


    def getParamaters(self):
        '''
        Creates the config file for future processing
        '''

        # Get input and output folders
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        # OS path used for compatibility issues between Linux and windows directory spacing
        config_path = os.path.join(outputFolder,"config.txt")

        # Create config file
        config = open(config_path, 'w')


        ##### Get cropping option #####
        crop = self.ui.comboBoxCrop.currentText()

        if crop == "Manual" :
            xcrop = str(self.ui.lineEditX.text())
            ycrop = str(self.ui.lineEditY.text())
            wcrop = str(self.ui.lineEditW.text())
            hcrop = str(self.ui.lineEditH.text())

        ##### Get Scaling factors ####
        if self.ui.checkBoxSF2.isChecked:
          SF = "2"
        if self.ui.checkBoxSF3.isChecked:
          SF = SF+"^"+"3"
        if self.ui.checkBoxSF3.isChecked:
          SF = SF+"^"+"4"

        # If using windows it is important to put \ at the end of folder name
        # Combining scaling and SF into input for imageJ macro
        imageJconfig = inputFolder+'^'+outputFolder+'^'+SF

        #### Write to config file ####
        config.write("Input_folder "+inputFolder+"\n");
        config.write("Output_folder "+outputFolder+"\n");

        config.write("Crop_option "+crop+"\n");
        if crop =="Manual" :
            config.write("Crop_manual "+xcrop+" "+ycrop+" "+wcrop+" "+hcrop+"\n");
        else :
            config.write("Crop_manual Not_applicable\n");

        config.write("ImageJ "+imageJconfig+"\n");

        config.write("Recon_log_file "+self.recon_log_path+"\n")

        config.write("Recon_folder_size "+str(self.f_size_out_gb)+"\n")

        config.write("Recon_pixel_size "+str(self.pixel_size)+"\n")


class Progress(QtGui.QDialog):
    '''
    Class to provide the dialog box to monitor current Image processing jobs.
    Basically extend the QDialog class (from Progress.py) generated by QT Designer
    '''

    # Create a constructor
    def __init__(self):
       super(Progress, self).__init__()
       self.ui=Ui_Progress()
       self.ui.setupUi(self)
       self.show()



def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
