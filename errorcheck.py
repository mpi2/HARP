from PyQt4 import QtGui, QtCore
import os
import pickle
import re

def errorCheck(self):
    ''' To check the required inputs for the processing to be run  '''
    # Get input and output folders (As the text is always from the text box it will hopefully keep track of
    #any changes the user might have made
    inputFolder = str(self.ui.lineEditInput.text())
    outputFolder = str(self.ui.lineEditOutput.text())
    self.stop = None


    # Check input and output folders assigned
    if not inputFolder :
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input directory not defined')
        self.stop = True
        return

    if not outputFolder :
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: output directory not defined')
        self.stop = True
        return

    # Check if input folder exists
    if not os.path.exists(inputFolder):
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not exist')
        self.stop = True
        return

    #Check if folder is empty
    if os.listdir(inputFolder) == []:
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty')
        self.stop = True
        return

    #Check if input folder contains any image files
    prog = re.compile("(.*).(bmp|tif|jpg|jpeg)",re.IGNORECASE)

    file_check = None
    # for loop to go through the directory
    for line in os.listdir(inputFolder) :
        line =str(line)
        #print line+"\n"
        # if the line matches the regex break
        if prog.match(line) :
            file_check = True
            return

    if file_check:
        self.stop = None
    else:
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not contain image files')
        self.stop = True
        return


    # Check if scan folder available if compression is required
    if self.ui.checkBoxScansReconComp.isChecked():
        if self.scan_folder == "":
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Scan folder not defined')
            self.stop = True
            return
        elif not os.path.exists(self.scan_folder):
            message = QtGui.QMessageBox.warning(self, 'Message', "Warning: Scan folder does not exist")
            self.stop = True
            return

    # Check pixel size is a number
    if self.ui.checkBoxPixel.isChecked() :

        try:
            testing = float(self.ui.lineEditPixel.text())
        except ValueError:
            if not self.ui.lineEditPixel.text():
                message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: User has not specified a new pixel size value')
            else :
                message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: User defined pixel is not a numerical value')
                self.stop = True
                return

    # Check user has not selected to scale by pixel without having a recon folder
    if self.ui.checkBoxPixel.isChecked() and self.pixel_size == "" :
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Pixel size could not be obtained from original recon log. Scaling "By Pixel (um) is not possible')
        self.stop = True
        return

    # Check cropping parameters ok
    if self.ui.radioButtonMan.isChecked() :
        try:
            testing = float(self.ui.lineEditX.text())
            testing = float(self.ui.lineEditY.text())
            testing = float(self.ui.lineEditW.text())
            testing = float(self.ui.lineEditH.text())
        except ValueError:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Cropping dimensions have not been defined')
            self.stop = True
            return

    # Check input directory contains something
    if os.listdir(inputFolder) == []:
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty, please check')
        self.stop = True
        return

    # Check if item is already on the list
    count = 0
    while True:
        twi0 = self.ui.tableWidget.item(count,1)
        if not twi0:
            self.stop = None
            break
        if twi0.text() == outputFolder:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Output folder is already on the processing list')
            self.stop = True
            return
        count = count+1

    # seeing if outpu folder exists
    if self.ui.checkBoxRF.isChecked():
        # I think it is too dangerous to delete everything in a folder
        # shutil.rmtree(outputFolder)
        # os.makedirs(outputFolder)
        self.stop = None
    # Check if output folder already exists. Ask if it is ok to overwrite
    elif os.path.exists(outputFolder):
        # Running dialog box to inform user of options
        message = QtGui.QMessageBox.question(self, 'Message', 'Folder already exists for the location:\n{0}\nCan this folder be overwritten?'.format(outputFolder) , QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if message == QtGui.QMessageBox.Yes:
            self.stop = None
        if message == QtGui.QMessageBox.No:
            self.stop = True
            return
    else :
        os.makedirs(outputFolder)
        self.stop = None

    # Check if a crop folder is available if UseOldCrop is used
    if self.ui.radioButtonUseOldCrop.isChecked():
        if not os.path.exists(os.path.join(str(self.ui.lineEditOutput.text()),"cropped")):
            self.stop = True
            message = QtGui.QMessageBox.warning(self,
                                                'Message',
                                                 'Warning: Use old crop option selected. This requires a previous crop to have been performed')




