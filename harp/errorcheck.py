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

"""


from PyQt5 import QtCore, QtGui, QtWidgets
import os
import re
import shutil


def errorCheck(mainwindow):
    """ To check the required inputs and parameters. Gives messages for problems encountered


    :param obj mainwindow from harp.py
    :ivar Boolean self.stop: Switch. True if adding to the processing list should be stopped. None if it is ok
    """

    # Get input and output folders (As the text is always from the text box it will hopefully keep track of
    #any changes the user might have made
    inputFolder = str(mainwindow.ui.lineEditInput.text())
    outputFolder = str(mainwindow.ui.lineEditOutput.text())

    # flag for use old crop
    use_old = False

    # reset the stop switch
    mainwindow.stop = None

    # Check input and output folders assigned
    if not inputFolder :
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: input directory not defined')
        mainwindow.stop = True
        return

    if not outputFolder :
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: output directory not defined')
        mainwindow.stop = True
        return

    # Check if input folder exists
    if not os.path.exists(inputFolder):
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: input folder does not exist')
        mainwindow.stop = True
        return

    # Check if a directory
    if not os.path.isdir(inputFolder):
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: input folder is not a directory')
        mainwindow.stop = True
        return

    #Check if folder is empty
    if os.listdir(inputFolder) == []:
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: input folder is empty')
        mainwindow.stop = True
        return

    #Check if input folder contains any image files
    prog = re.compile("(.*).(bmp|tif|jpg|jpeg)",re.IGNORECASE)

    file_check = None
    # for loop to go through the directory
    for line in os.listdir(inputFolder) :
        line =str(line)
        #print line+"\n"
        # if the line matches the regex break
        if prog.match(line):
            file_check = True
            break

    if file_check:
        mainwindow.stop = None
    else:
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: input folder does not contain image files')
        mainwindow.stop = True
        return


    # Check if scan folder available if compression is required
    if mainwindow.ui.checkBoxScansReconComp.isChecked():
        if mainwindow.scan_folder == "":
            QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: Scan folder not defined')
            mainwindow.stop = True
            return
        elif not os.path.exists(mainwindow.scan_folder):
            QtWidgets.QMessageBox.warning(mainwindow, 'Message', "Warning: Scan folder does not exist")
            mainwindow.stop = True
            return

    # Check pixel size is a number
    # if mainwindow.ui.checkBoxPixel.isChecked() :
    #
    #     try:
    #         float(mainwindow.ui.lineEditPixel.text())
    #     except ValueError:
    #         if not mainwindow.ui.lineEditPixel.text():
    #             QtGui.QMessageBox.warning(mainwindow, 'Message', 'Warning: User has not specified a new pixel size value')
    #             mainwindow.stop = True
    #             return
    #         else :
    #             QtGui.QMessageBox.warning(mainwindow, 'Message', 'Warning: User defined pixel is not a numerical value')
    #             mainwindow.stop = True
    #             return

    # Check user has not selected to scale by pixel without having a recon folder
    pixel_size_count = mainwindow.ui.tableWidgetPixelScales.rowCount()
    if pixel_size_count > 0:

        if mainwindow.pixel_size == "":
            QtWidgets.QMessageBox.warning(mainwindow, 'Unable to scale by pixel',
                                      'Pixel size could not be obtained from original recon log. Unable to scale '
                                      '"By Pixel (um)"')
            mainwindow.stop = True
            return
        elif any(float(mainwindow.pixel_size) > float(mainwindow.ui.tableWidgetPixelScales.item(i, 0).text())
                 for i in range(0, pixel_size_count)):
            QtWidgets.QMessageBox.warning(mainwindow, 'Unable to scale by pixel',
                                      'Specified pixel sizes must be greater than '
                                      'the recon pixel size ({} um)'.format(mainwindow.pixel_size))
            mainwindow.stop = True
            return

    # Check cropping parameters ok
    if mainwindow.ui.radioButtonMan.isChecked():
        try:
            testing = float(mainwindow.ui.lineEditX.text())
            testing = float(mainwindow.ui.lineEditY.text())
            testing = float(mainwindow.ui.lineEditW.text())
            testing = float(mainwindow.ui.lineEditH.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: Cropping dimensions have not been defined')
            mainwindow.stop = True
            return

    # Check input directory contains something
    if os.listdir(inputFolder) == []:
        QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: input folder is empty, please check')
        mainwindow.stop = True
        return

    # Check if item is already on the processing list
    count = 0
    while True:
        twi0 = mainwindow.ui.tableWidget.item(count, 1)
        if not twi0:
            mainwindow.stop = None
            break
        if twi0.text() == outputFolder:
            QtWidgets.QMessageBox.warning(mainwindow, 'Error adding job', 'Output folder is already on the processing list!')
            mainwindow.stop = True
            return
        count = count+1

    # Check if a crop folder is available if UseOldCrop is used
    if mainwindow.ui.radioButtonUseOldCrop.isChecked() and mainwindow.ui.checkBoxCropYes.isChecked():

        use_old = True
        if not os.path.exists(os.path.join(str(mainwindow.ui.lineEditOutput.text()),"cropped")):
            mainwindow.stop = True
            QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: Use old crop option selected. '
                                            'This requires a previous crop to have been performed')
            return

    if mainwindow.ui.radioButtonuCT.isChecked() and mainwindow.ui.radioButtonDerived.isChecked():
            mainwindow.stop = True
            QtWidgets.QMessageBox.warning(mainwindow, 'Message', 'Warning: Derived Dimension crop option is not available for'
                                            ' uCT processing')
            return

    # seeing if output folder exists
    if mainwindow.ui.checkBoxRF.isChecked() and not use_old:
        remove_folder_contents(mainwindow, outputFolder)  # WARNING: THIS DELETES THE OUTPUT FOLDER AND ITS CONTENTS
    # Check if output folder already exists. Ask if it is ok to overwrite
    elif os.path.exists(outputFolder):

        if len(os.listdir(outputFolder)) > 0:

            # Warning box to inform user
            message = QtWidgets.QMessageBox.warning(mainwindow, 'Warning',
                                                 'The specified output folder already exists! '
                                                 'Is it OK to overwrite files in this folder?\n\n'
                                                 '(NOTE: If you are using the "old crop" option you will not overwrite the '
                                                 'original cropped recon.)'.format(outputFolder),
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if message == QtWidgets.QMessageBox.Yes and not use_old:
                remove_folder_contents(mainwindow, outputFolder)  # WARNING: THIS DELETES THE OUTPUT FOLDER AND ITS CONTENTS
            if message == QtWidgets.QMessageBox.No:
                mainwindow.stop = True
                return

    else:
        os.makedirs(outputFolder)
        mainwindow.stop = None


def remove_folder_contents(mainwindow, outputFolder):

    print("Removing output folder")
    # WARNING: this function will delete the folder and its contents, before creating a new folder

    try:
        shutil.rmtree(outputFolder)
        os.makedirs(outputFolder)
        mainwindow.stop = None
    except OSError:
        mainwindow.stop = True
        error_box = QtWidgets.QMessageBox()
        error_box.setWindowTitle("Error")
        error_box.setText("Unable to overwrite folder contents. Please specify a different output folder.")
        error_box.setIcon(QtWidgets.QMessageBox.Critical)
        error_box.exec_()





