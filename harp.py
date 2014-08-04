#!/usr/bin/python
# title           :harp.py
# description     :Runs the HARP GUI
# author          :SIG
# date            :2014-08-04
# version         :2.0.0 (OPT update)
#usage            :python harp.py or if using executable in windows .\harp.exe or clicking on the harp.exe icon.
#formatting       :PEP8 format is used where possible. QT classes in C++ standard format.
#python_version   :2.7
#=============================================================================

# Import PyQT module
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSlot,SIGNAL,SLOT
import datetime
from multiprocessing import freeze_support
import os
import signal
import re
import subprocess
import sys
import tempfile
import time
import uuid
import psutil
import autofill
import errorcheck
import getpickle
from mainwindow import Ui_MainWindow
from processing import ProcessingThread
from zproject import ZProjectThread
import crop


class MainWindow(QtGui.QMainWindow):
    """
    Class to provide the main window for the Image processing GUI.
    Basically extend the QMainWindow class (from MainWindow.py) generated by QT Designer

    Also shows a dialog box after a submission the dialog box will then keep a track of the
    image processing (not yet developed).

    QT Designer automatically uses mixed case for its class object names e.g radioButton this format
    is not PEP8 but has not been changed
    """

    def __init__(self, app):
        """  Constructor: Checks for buttons which have been pressed and responds accordingly. """
        # Standard setup of class from qt designer Ui class
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.app = app

        #         # style sheet
        #         app.setStyle("plastique")
        #         style_file = "darkorange.stylesheet"
        #         with open(style_file, "r") as sf:
        #             self.setStyleSheet(sf.read())

        # Make unique ID if this is the first time mainwindow has been called
        self.unique_ID = uuid.uuid1()

        # Initialise various switches
        self.modality = "MicroCT"
        self.selected = "Not_selected"
        self.stop = None
        self.count_in = 0
        self.current_row = 0
        self.list_for_processing = []
        self.crop_pickle_path = "NA"
        self.stop_pro_switch = 0

        # initialise some information
        self.scan_folder = ""
        self.recon_log_path = ""
        self.f_size_out_gb = ""
        self.pixel_size = ""
        self.ui.lcdNumberPixel.display(self.pixel_size)

        # get current directory
        if getattr(sys, 'frozen', False):
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        # Temp folder for pre-processing log (if in use) and z-project
        self.tmp_dir = tempfile.mkdtemp()

        # get input folder
        self.ui.pushButtonInput.clicked.connect(self.select_file_in)

        # Get output folder
        self.ui.pushButtonOutput.clicked.connect(self.select_file_out)

        # OPT selection
        self.ui.radioButtonOPT.clicked.connect(self.get_OPT_only)

        # uCT selection
        self.ui.radioButtonuCT.clicked.connect(self.get_uCT_only)

        # If Go button is pressed move onto track progress dialog box
        self.ui.pushButtonGo.clicked.connect(self.add_to_list)

        # Set cropping options
        # Auto crop (disable buttons)
        self.ui.radioButtonAuto.clicked.connect(self.man_crop_off)

        # Crop button on
        self.ui.checkBoxCropYes.clicked.connect(self.crop_switch)
        #self.ui.radioButtonNo.clicked.connect(self.man_crop_off)

        # Use Old crop (disable buttons)
        self.ui.radioButtonUseOldCrop.clicked.connect(self.man_crop_off)

        # Man crop (enable buttons).
        self.ui.radioButtonMan.clicked.connect(self.man_crop_on)

        # derived crop (enable buttons).
        self.ui.radioButtonDerived.clicked.connect(self.derive_on)

        # If the get dimensions button is pressed
        self.ui.pushButtonGetDimensions.clicked.connect(self.get_dimensions)

        #Get the output folder name when manually changed in box
        self.ui.lineEditOutput.textChanged.connect(self.output_folder_changed)

        #Get the input folder name when manually changed in box
        self.ui.lineEditInput.textChanged.connect(self.input_folder_changed)

        # Get recon file manually
        self.ui.pushButtonCTRecon.clicked.connect(self.get_recon_man)

        # Get scan file manually
        self.ui.pushButtonScan.clicked.connect(self.get_scan_man)

        # Get SPR file manually
        self.ui.pushButtonCTSPR.clicked.connect(self.get_SPR_man)

        # Update name
        self.ui.pushButtonUpdate.clicked.connect(self.update_name)

        # Get scan file manually
        self.ui.checkBoxPixel.clicked.connect(self.scale_by_pixel_on)

        # Resize for smaller monitors
        self.ui.actionResize.triggered.connect(self.resize_screen)

        # Reset screen size to standard
        self.ui.actionReset_screen_size.triggered.connect(self.reset_screen)

        # Start processing recons
        self.ui.pushButtonStart.clicked.connect(self.start_processing)

        # Stop processing recons
        self.ui.pushButtonStop.clicked.connect(self.stop_processing)

        # Add more recons to the list
        self.ui.pushButtonAdd.clicked.connect(self.add_more)

        # About HARP message
        self.ui.actionAbout.triggered.connect(self.about_message)

        # Documentation PDF
        self.ui.actionPDF_user_guide.triggered.connect(self.user_guide)

        # Example Data for testing purposes
        self.ui.actionExample_data.triggered.connect(self.example_data)

        # need to monitor when the tab is changed as it determines what qtable uses key commands
        self.connect(self.ui.tabWidget, SIGNAL('currentChanged(int)'), self.tab_change)

        # Decide which channel to be used for autocrop (this table is on the first tab)
        self.ui.tableWidgetOPT.__class__.keyPressEvent = self.choose_channel_for_crop

        # When user double clicks on OPT alternative channel open it on the parameter tab
        self.ui.tableWidgetOPT.doubleClicked.connect(self.change_opt_chn)

        #Accept drag and drop
        self.setAcceptDrops(True)

        # to make the window visible
        self.show()

    def dropEvent(self, event):
        volList = [str(v.toLocalFile()) for v in event.mimeData().urls()]
        vol1 = volList[0]
        self.ui.lineEditInput.setText(vol1)
        self.reset_inputs()
        self.autofill_pipe()


    def dragEnterEvent(self, event):
        event.accept()


    def tab_change(self):
        # Update OPT Channel list. As something may have changed on the processing list
        autofill.get_channels(self)


        if self.ui.tabWidget.currentIndex() == 0:
            # Decide which channel to be used for autocrop
            self.ui.tableWidgetOPT.__class__.keyPressEvent = self.choose_channel_for_crop
        elif self.ui.tabWidget.currentIndex() == 1:
            # delete some recons
            self.ui.tableWidget.__class__.keyPressEvent = self.delete_rows

    def example_data(self):
        """ loads in data for tesing purposes """
        self.ui.lineEditInput.setText(os.path.join("D:", "fakedata", "recons", "20140408_RCAS_17_18.4e_wt_rec"))
        self.reset_inputs()
        self.autofill_pipe()

    def about_message(self):
        """ Short description about what HARP is and its version"""
        QtGui.QMessageBox.information(self, 'Message', (
            'HARP v1.0: Harwell Automated Recon Processor\n\n'
            'Crop, scale and compress reconstructed images from microCT  or OPT data.\n'))

    def user_guide(self):
        """ Loads up pdf help file"""
        user_man = os.path.join(self.dir, "HARP_user_guide.pdf")

        if sys.platform == "win32" or sys.platform == "win64":
            if not os.path.exists(user_man):
                #if HARP run from exe
                user_man = os.path.join("..", "..", "HARP_user_guide.pdf")
            os.startfile(user_man)
        else:
            opener = "evince"
            subprocess.call([opener, user_man])

    def resize_screen(self):
        """ Resize screen for smaller monitors"""
        self.resize(1300, 700)
        self.ui.scrollArea.setFixedSize(1241, 600)

    def reset_screen(self):
        """ Reset screen back to default"""
        self.resize(1300, 1007)
        self.ui.scrollArea.setFixedSize(1241, 951)

    def select_file_out(self):
        """ Select output folder"""
        output_folder = str(self.ui.lineEditOutput.text())

        # Check input and output folders assigned
        if output_folder:
            self.fileDialog = QtGui.QFileDialog(self, 'Open File', output_folder)
        else:
            self.fileDialog = QtGui.QFileDialog(self, 'Open File')

        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")
        # Check if folder variable is defined (if it not the user has pressed cancel)
        if not folder == "":
            self.ui.lineEditOutput.setText(folder)

    def select_file_in(self):
        """ User selects the folder to be processed and some auto-fill methods are carried out """
        input_folder = str(self.ui.lineEditInput.text())

        # Check input and output folders assigned
        if input_folder:
            self.fileDialog = QtGui.QFileDialog(self, 'Open File', input_folder)
        else:
            self.fileDialog = QtGui.QFileDialog(self, 'Open File')

        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")

        # if folder is not defined user has pressed cancel
        if not folder == "":
            # Reset the inputs incase this is not the first time someone has selected a file
            self.reset_inputs()
            # Set the input folder
            self.ui.lineEditInput.setText(folder)
            # run all the autofill functions
            self.autofill_pipe()



    def autofill_pipe(self,suppress=False):

        # Remove the contents of the OPT table
        print "clearing opt table"
        self.ui.tableWidgetOPT.clearContents()
        self.crop_box_use = False
        self.ui.radioButtonAuto.setChecked(True)
        self.ui.lineEditDerivedChnName.setText("")

        # check if uCT or opt data
        print "checking if uct or opt"
        autofill.opt_uCT_check(self,suppress)

        # Autocomplete the name
        print "autocompleting name"
        autofill.get_name(self, str(self.ui.lineEditInput.text()),suppress)

        # Get the reconLog and associated pixel size
        print "geting recon log"
        autofill.get_recon_log(self)

        # Get the output folder location
        print "getting output folder"
        autofill.auto_file_out(self)

        # See what OPT channels are available
        print "getting channels"
        if self.modality == "OPT":
            autofill.get_channels(self)
            autofill.auto_get_derived(self)

        # Automatically identify scan folder
        print "getting scan folder"
        autofill.auto_get_scan(self)

        # Automatically get SPR file
        print "getting spr folder"
        autofill.auto_get_SPR(self)

        print "deteriming size of input folder"
        # Determine size of input folder
        autofill.folder_size_approx(self)

    def reset_inputs(self):
        """ Reset the inputs to blank"""
        self.ui.lineEditDate.setText("")
        self.ui.lineEditGroup.setText("")
        self.ui.lineEditAge.setText("")
        self.ui.lineEditLitter.setText("")
        self.ui.lineEditZygosity.setText("")
        self.ui.lineEditSex.setText("")
        self.ui.lineEditName.setText("")
        self.ui.lineEditCTRecon.setText("")
        self.ui.lineEditCTSPR.setText("")
        self.ui.lineEditScan.setText("")
        self.ui.lineEditOutput.setText("")
        self.ui.lcdNumberFile.display(0.0)
        self.ui.lcdNumberPixel.display(0.0)

    def input_folder_changed(self, text):
        """ When user changes the name of the folder manually"""
        self.input_folder = text

    def output_folder_changed(self, text):
        """ When user changes the name of the folder manually"""
        self.output_folder = text

    def scale_by_pixel_on(self):
        """ enables boxes for scaling by pixel"""
        if self.ui.checkBoxPixel.isChecked():
            self.ui.lineEditPixel.setEnabled(True)
        else:
            self.ui.lineEditPixel.setEnabled(False)

    def crop_switch(self):
        """ turns crop options on or off depending on the status of the check """
        if self.ui.checkBoxCropYes.isChecked():
            self.ui.radioButtonAuto.setEnabled(True)
            self.ui.radioButtonMan.setEnabled(True)
            self.ui.radioButtonUseOldCrop.setEnabled(True)
            self.ui.radioButtonDerived.setEnabled(True)
            if self.ui.radioButtonMan.isChecked():
                self.ui.lineEditX.setEnabled(True)
                self.ui.lineEditY.setEnabled(True)
                self.ui.lineEditW.setEnabled(True)
                self.ui.lineEditH.setEnabled(True)
                self.ui.pushButtonGetDimensions.setEnabled(True)
        else:
            self.ui.radioButtonAuto.setEnabled(False)
            self.ui.radioButtonMan.setEnabled(False)
            self.ui.radioButtonUseOldCrop.setEnabled(False)
            self.ui.radioButtonDerived.setEnabled(False)
            self.ui.lineEditX.setEnabled(False)
            self.ui.lineEditY.setEnabled(False)
            self.ui.lineEditW.setEnabled(False)
            self.ui.lineEditH.setEnabled(False)
            self.ui.pushButtonGetDimensions.setEnabled(False)

    def man_crop_off(self):
        """ disables boxes for cropping manually """
        self.ui.lineEditX.setEnabled(False)
        self.ui.lineEditY.setEnabled(False)
        self.ui.lineEditW.setEnabled(False)
        self.ui.lineEditH.setEnabled(False)
        self.ui.pushButtonGetDimensions.setEnabled(False)
        self.ui.lineEditDerivedChnName.setEnabled(False)

    def man_crop_on(self):
        """ enables boxes for cropping manually """
        self.ui.lineEditX.setEnabled(True)
        self.ui.lineEditY.setEnabled(True)
        self.ui.lineEditW.setEnabled(True)
        self.ui.lineEditH.setEnabled(True)
        self.ui.pushButtonGetDimensions.setEnabled(True)
        self.ui.lineEditDerivedChnName.setEnabled(False)

    def derive_on(self):
        self.ui.lineEditDerivedChnName.setEnabled(True)

    def get_OPT_only(self):
        """ edits self.modality """
        self.modality = "OPT"
        self.ui.lineEditChannel.setEnabled(True)
        self.ui.labelChannel.setEnabled(True)
        self.ui.tableWidgetOPT.setEnabled(True)
        self.ui.radioButtonDerived.setEnabled(True)
        self.ui.checkBoxInd.setEnabled(True)
        if self.ui.radioButtonDerived.isChecked():
            self.ui.lineEditDerivedChnName.setEnabled(True)
        autofill.get_channels(self)



    def get_uCT_only(self):
        """ edits self.modality """
        self.modality = "MicroCT"
        self.ui.lineEditChannel.setEnabled(False)
        self.ui.labelChannel.setEnabled(False)
        self.ui.tableWidgetOPT.setEnabled(False)
        self.ui.radioButtonDerived.setEnabled(False)
        self.ui.lineEditDerivedChnName.setEnabled(False)
        self.ui.checkBoxInd.setEnabled(False)

    def update_name(self):
        """ Function to update the name of the file and folder"""
        self.full_name = str(self.ui.lineEditName.text())

        autofill.get_name(self, self.full_name)

        # Get output folder name, to start off with this will just be the input name
        output = str(self.ui.lineEditOutput.text())
        path, output_folder_name = os.path.split(output)
        self.ui.lineEditOutput.setText(os.path.join(path, self.full_name))

    def get_recon_man(self):
        """ Get the recon folder manually"""
        self.file_dialog = QtGui.QFileDialog(self)
        file = self.file_dialog.getOpenFileName()
        self.pixel_size = ""
        self.ui.lcdNumberPixel.display(self.pixel_size)
        if not file == "":
            try:
                self.ui.lineEditCTRecon.setText(file)
                self.recon_log_path = os.path.abspath(file)

                # Open the log file as read onlypyt
                recon_log_file = open(self.recon_log_path, 'r')

                # create a regex to pixel size
                # We want the pixel size where it starts with Pixel. This is the pixel size with the most amount of decimal places
                if self.modality == "OPT":
                    prog = re.compile("^Image Pixel Size \(um\)=(\w+.\w+)")
                else:
                    prog = re.compile("^Pixel Size \(um\)=(\w+.\w+)")

                # for loop to go through the recon log file
                for line in recon_log_file:
                    # "chomp" the line endings off
                    line = line.rstrip()
                    # if the line matches the regex print the (\w+.\w+) part of regex
                    if prog.match(line):
                        # Grab the pixel size with with .group(1)
                        self.pixel_size = prog.match(line).group(1)
                        break

                # Display the number on the lcd display
                self.ui.lcdNumberPixel.display(self.pixel_size)

                # Set recon log text
                self.ui.lineEditCTRecon.setText(str(self.recon_log_path))
            except IOError as e:
                # Python standard exception identifies recon file not found
                self.ui.lineEditCTRecon.setText("Error identifying recon file")


    def get_scan_man(self):
        """ Get the scan folder manually"""
        self.file_dialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")
        if not folder == "":
            self.ui.lineEditScan.setText(folder)  #

    def get_SPR_man(self):
        """ Get the SPR file manually"""
        self.file_dialog = QtGui.QFileDialog(self)
        file = self.fileDialog.getOpenFileName()
        if not file == "":
            self.ui.lineEditCTSPR.setText(file)

    #======================================================================
    # Functions for get Dimensions (z projection)
    #======================================================================
    def get_dimensions(self):
        """
        Perform a z projection which allows user to crop based on z projection.
        Two important files used. crop.py and zproject.py
        zproject peforms the zprojection and displays the image. crop.py then gets the dimensions to perform the crop
        NOTE: The cropping is not actually done here
        """
        self.zcheck = 0
        # Opens MyMainWindow from crop.py
        input_folder = str(self.ui.lineEditInput.text())

        # Check input folder is defined
        if not input_folder:
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: input directory not defined')
            return
        # Check input folder exists
        if not os.path.exists(input_folder):
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not exist')
            return
        #Check if folder is empty
        elif os.listdir(input_folder) == []:
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty')
            return

        # Get folder to store the zprojection. Stored in a temp folder untill processing is fully completed
        zproj_path = os.path.join(str(self.tmp_dir), "z_projection")
        self.stop = None

        # Let the user know what is going on
        self.ui.textEditStatusMessages.setText("Z-projection in process, please wait")
        #Run the zprojection
        self.start_z_thread()

    def start_z_thread(self):
        """ starts a thread to perform all the processing in the background."""
        input_folder = str(self.ui.lineEditInput.text())

        self.z_thread_pool = []
        self.z_thread_pool.append(ZProjectThread(input_folder, self.tmp_dir))
        self.connect(self.z_thread_pool[len(self.z_thread_pool) - 1], QtCore.SIGNAL("update(QString)"),
                     self.zproject_slot)
        self.z_thread_pool[len(self.z_thread_pool) - 1].start()

    def zproject_slot(self, message):
        """
        This listens to the child process and displays any messages.
        It has records the start and stop time of the processing and starts a new
        thread after the processing has finished
        """
        self.ui.textEditStatusMessages.setText(message)
        if message == "Z-projection finished":
            # Get the crop dimensions and save the file
            self.run_crop(os.path.join(self.tmp_dir, "max_intensity_z.tif"))


    def crop_call_back(self, box):
        """ Method to get crop dimension text (used in getDimensions)"""
        self.ui.lineEditX.setText(str(box[0]))
        self.ui.lineEditY.setText(str(box[1]))
        self.ui.lineEditW.setText(str(box[2]))
        self.ui.lineEditH.setText(str(box[3]))
        self.ui.textEditStatusMessages.setText("Dimensions selected")
        self.ui.pushButtonGetDimensions.setText("Get Dimensions")

    def run_crop(self, img_path):
        """ Method to create Crop object (used in getDimensions)"""
        cropper = crop.Crop(self.crop_call_back, img_path, self)
        cropper.show()

    #======================================================================
    # Functions for processing
    #======================================================================
    def start_processing(self):
        """ Starts a thread for processing after the user has pressed the 'start button' (GUI click only) """
        self.ui.pushButtonStart.setEnabled(False)
        self.ui.pushButtonStop.setEnabled(True)
        self.start_processing_thread()

    def add_to_list_action(self):
        # This adds a recon folder to be processed.
           # Get the directory of the script
        dir = os.path.dirname(os.path.abspath(__file__))

        # get the input name for table
        input_name = str(self.ui.lineEditInput.text())

        # Perform some checks before any processing is carried out
        errorcheck.errorCheck(self)

        # If an error has occured self.stop will be defined. if None then no error.
        if self.stop is None:
            # Get the parameters needed for processing
            getpickle.get_pickle(self)

            # Set up the table. 300 rows should be enough!
            self.ui.tableWidget.setRowCount(300)

            # Set the data for an individual row
            # Set up the name data cell
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setItem(self.count_in, 0, item)
            item = self.ui.tableWidget.item(self.count_in, 0)
            item.setText(input_name)

            # Set up the output folder cell
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setItem(self.count_in, 1, item)
            item = self.ui.tableWidget.item(self.count_in, 1)
            item.setText(self.configOb.output_folder)

            # Set up the status cell
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setItem(self.count_in, 2, item)
            item = self.ui.tableWidget.item(self.count_in, 2)
            # Status is pending untill processing has started
            item.setText("Pending")

            # count_in is the counter for the row to add data
            self.count_in += 1

            # Reszie the columns to fit the data
            self.ui.tableWidget.resizeColumnsToContents()

            # Go to second tab
            self.ui.tabWidget.setCurrentIndex(1)


    def add_to_list(self):
        """
        This will set off all the processing scripts and shows the dialog box to keep track of progress
        """
        in_dir = str(self.ui.lineEditInput.text())
        path,folder_name = os.path.split(in_dir)
        # Check if multiple channels will be added to the list at the same time
        # Standard microCT run
        if self.modality == "MicroCT":
            self.add_to_list_action()
        # Individual OPT run
        elif self.ui.checkBoxInd.isChecked():
            self.add_to_list_action()
        # Batch OPT run
        else:
            # Save the initial settings to be displayed again after all processing has been added
            # Recon log
            recon_log = self.ui.lineEditCTRecon.text()
            # SPR (should prob get rid of this
            spr = self.ui.lineEditCTSPR.text()
            # Scan folder
            scan = self.ui.lineEditScan.text()
            # Output folder
            out_dir_original = self.ui.lineEditOutput.text()
            # Input folder
            in_dir_orignal = self.ui.lineEditInput.text()
            # derived name
            derive = self.ui.lineEditDerivedChnName.text()
            # crop option
            if self.ui.radioButtonAuto.isChecked():
                crop_option = "auto"
            elif self.ui.radioButtonDerived.isChecked():
                crop_option = "derived"
            elif self.ui.radioButtonUseOldCrop.isChecked():
                crop_option = "old"
            elif self.ui.radioButtonMan.isChecked():
                crop_option = "man"

            # go through list and get the channel names
            for name in self.chan_full:
                chan_path = os.path.join(path,name)

                # Check if the input director is already set the channel in the loop
                # if the current channel is not the same as the loop then perform autofill before adding to the list
                if chan_path != in_dir:
                    self.ui.lineEditInput.setText(chan_path)
                    self.reset_inputs()
                    self.autofill_pipe(suppress=True)

                self.add_to_list_action()

            # reset the parameters tab back to what originally was for the user.
            # Save the initial settings to be displayed again after all processing has been added
            # Input folder
            self.ui.lineEditInput.setText(in_dir_orignal)
            self.autofill_pipe(suppress=True)

            # The following may have been changed from the user so have to be changed after the autofill
            # Recon log
            self.ui.lineEditCTRecon.setText(recon_log)
            # SPR (should prob get rid of this
            self.ui.lineEditCTSPR.setText(spr)
            # Scan folder
            self.ui.lineEditScan.setText(scan)
            # Output folder
            self.ui.lineEditOutput.setText(out_dir_original)
            # derived name
            self.ui.lineEditDerivedChnName.setText(derive)
            # crop option
            if crop_option == "auto":
                self.ui.radioButtonAuto.setChecked(True)
                self.man_crop_off()
            elif crop_option == "derived":
                self.ui.radioButtonDerived.setChecked(True)
                self.derive_on()
            elif crop_option == "old":
                self.ui.radioButtonUseOldCrop.setChecked(True)
                self.man_crop_on()
            elif crop_option == "man":
                self.ui.radioButtonMan.setChecked(True)
                self.man_crop_on()




    def processing_slot(self, message):
        """
        This listens to the child process and displays any messages.
        It has records the start and stop time of the processing and starts a new
        thread after the processing has finished
        """
        if self.stop_pro_switch:
            return

        item = QtGui.QTableWidgetItem()
        self.ui.tableWidget.setItem(self.current_row, 2, item)
        item = self.ui.tableWidget.item(self.current_row, 2)
        item.setText(message)

        if message == "Started Processing":
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setItem(self.current_row, 3, item)
            item = self.ui.tableWidget.item(self.current_row, 3)
            item.setText(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        if re.search("Processing finished", message) or re.search("error", message):
            print message
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setItem(self.current_row, 4, item)
            item = self.ui.tableWidget.item(self.current_row, 4)
            item.setText(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            # Processing has finished, lets do another one!
            self.start_processing_thread()
            # update the opt channels table
            autofill.get_channels(self)

        self.ui.tableWidget.resizeColumnsToContents()

    def start_processing_thread(self):
        """ starts a thread to perform all the processing in the background.
        The add function then listens to any messages the thread makes
        """
        self.stop_pro_switch = 0
        # Get memory of the computer (can't seem to do this in the thread)
        mem_summary = psutil.virtual_memory()
        prog = re.compile("total=(\d+)")
        self.memory = re.search(prog, str(mem_summary)).group(1)
        self.p_thread_pool = []

        # A while loop is used to go through the processing table and decides which file to process
        count = 0
        while True:
            # This gets the status text
            status = self.ui.tableWidget.item(count, 2)
            if not status:
                # if not defined it means there are no recons left to process
                self.ui.pushButtonStart.setEnabled(True)
                self.ui.pushButtonStop.setEnabled(False)
                return
            if re.search("Processing finished", status.text()) or status.text() == "Processing Cancelled!" or re.search(
                    "error", status.text()):
                # this row has finished, move on
                count = count + 1
                continue
            if status.text() == "Pending":
                # this row needs processing, record the row and break out
                folder = self.ui.tableWidget.item(count, 1)
                self.folder_from_list = str(folder.text())
                self.current_row = count
                break
            count += 1


        # Get the configobject for the row which has been identified from the previous while loop
        self.configOb_path_from_list = os.path.join(self.folder_from_list, "Metadata", "configobject.txt")

        # Finally! Perform the analysis in a thread (using the WorkThread class from Run_processing.py file)
        wt = ProcessingThread(self.configOb_path_from_list, self.memory, self)
        self.connect(wt, QtCore.SIGNAL("update(QString)"), self.processing_slot)
        self.connect(self, QtCore.SIGNAL("kill(QString)"), wt.kill_slot)
        self.p_thread_pool.append(wt)
        self.p_thread_pool[len(self.p_thread_pool) - 1].start()

    def add_more(self):
        """
        When the add more button is pressed, just go back to the first tab
        """
        # change tab
        self.ui.tabWidget.setCurrentIndex(0)
        # need opt table to handle key press events
        self.ui.tableWidgetOPT.__class__.keyPressEvent = self.choose_channel_for_crop

        in_dir = str(self.ui.lineEditInput.text())
        path_in,folder_name = os.path.split(in_dir)
        print path_in


        #Check if user wants to use the next opt channel available
        if self.modality == "OPT":
            # check if a channel which has not been analysed
            n = self.ui.tableWidgetOPT.rowCount()
            for i in range(n):
                processed = self.ui.tableWidgetOPT.item(i, 2)
                if processed:
                    print processed.text()
                    if processed.text() == "No":
                        reply = QtGui.QMessageBox.question(self, 'Message', 'Would you like to setup the next '
                                                                            'OPT Channel?',
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                        if reply == QtGui.QMessageBox.Yes:
                            name = self.ui.tableWidgetOPT.item(i, 1)
                            self.ui.lineEditInput.setText(os.path.join(path_in, str(name.text())))
                            self.reset_inputs()
                            self.autofill_pipe()
                            return
                        if reply == QtGui.QMessageBox.No:
                            return




    def stop_processing(self):
        """ Stop processing, kill the current process """
        print "Stop!!"
        item = QtGui.QTableWidgetItem()
        self.ui.tableWidget.setItem(self.current_row, 2, item)
        item = self.ui.tableWidget.item(self.current_row, 2)
        item.setText("Processing Cancelled!")

        self.kill_em_all()

        self.ui.pushButtonStart.setEnabled(True)
        self.ui.pushButtonStop.setEnabled(False)

        self.p_thread_pool = None

        self.stop_pro_switch = 1


    def delete_rows(self, event):
        """If the delete button is pressed on a certain row the recon is taken off the list to be processed"""
        if event.key() == QtCore.Qt.Key_Delete:

            selected = self.ui.tableWidget.currentRow()
            status = self.ui.tableWidget.item(selected, 2)
            if status:
                print "status", status.text()
                if (status.text() == "Pending" or re.search("Processing finished", status.text())
                    or status.text() == "Processing Cancelled!" or re.search("error", status.text())):

                    print "Deleted row"
                    self.ui.tableWidget.removeRow(selected)
                    # The count_in will now be one less (i think...)
                    self.count_in = self.count_in - 1
                    # I think the thread will be empty fo next time already
                    #self.pthread_pool = []
                else:
                    QtGui.QMessageBox.warning(self, 'Message',
                                                  'Warning: Can\'t delete a row that is currently being processed.'
                                                  '\nSelect "Stop", then remove')

    #======================================================================
    # Kill HARP functions
    #======================================================================
    def closeEvent(self, event):
        """
        Function for when the program has been closed down
        Function name has to be mixed case format as it is from qt
        Performs a loop through the item list and checks if any process still running
        """
        print "Close event"
        # First check if a process still running
        switch = ""
        count = 0
        while True:
            # This gets the status text
            status = self.ui.tableWidget.item(count, 2)
            if not status:
                #print "status dead"
                switch = "dead"
                break
            if status:
                if (status.text() != "Pending" and not re.search("Processing finished", status.text())
                    and status.text() != "Processing Cancelled!" and not re.search("error", status.text())):
                    #print "Status message", status.text()
                    switch = "live"
                    break
            count += 1

        count = 0
        #print "switch", switch
        if switch == "live":
            QtGui.QMessageBox.warning(self, 'Message',
                                          'Warning: Processing still running.\nStop processing and then close down')
            event.ignore()
            switch == "live"
        else:
            reply = QtGui.QMessageBox.question(self, 'Message', 'Are you sure to quit?',
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            event.accept()
            if reply == QtGui.QMessageBox.Yes:
                # Kill_em_all class to try and kill any processes
                self.kill_em_all
            else:
                event.ignore()
        #reset stop
        switch = ""

    def kill_em_all(self):
        """ Function to kill all processes """
        print "starting kill em all"
        # First kill the thread and autocrop
        self.emit(QtCore.SIGNAL('kill(QString)'), "kill")

    #======================================================================
    # User keyboard options for OPT channels
    #======================================================================
    def choose_channel_for_crop(self,event):
        """
        If the return button is pressed on a certain row of the
        opt list this recon will be used for the automatic crop
        """
        if event.key() == QtCore.Qt.Key_Return:
            print "key pressed"
            selected = self.ui.tableWidgetOPT.currentRow()
            name = self.ui.tableWidgetOPT.item(selected, 1)
            # check if anythin on the OPT list
            if not name:
                print "Selected a row with no opt info"

            elif self.ui.radioButtonOPT.isChecked() and self.ui.radioButtonDerived.isChecked():

                pro = self.ui.tableWidgetOPT.item(selected, 2)
                if pro.text() == "No":
                    QtGui.QMessageBox.warning(self, 'Message',
                                              'Warning: Chosen channel to derive dimensions (cropbox) has either\n'
                                              'not been analysed or has not been added onto the processing list')
                if pro.text() == "On list":
                    in_dir = str(self.ui.lineEditInput.text())
                    path,folder_name = os.path.split(in_dir)
                    if name.text() == folder_name:
                        QtGui.QMessageBox.warning(self, 'Message',
                                                'Warning: Chosen channel to derive dimensions (cropbox) cannot be\n'
                                                'the current channel unless already processed')
                else:

                    self.ui.lineEditDerivedChnName.setText(name.text())

            else:
                QtGui.QMessageBox.warning(self, 'Message',
                                          "Warning: Derived dimension options has not been chosen")


    def change_opt_chn(self):
        in_dir = str(self.ui.lineEditInput.text())
        path_out,folder_name = os.path.split(in_dir)
        selected = self.ui.tableWidgetOPT.currentRow()
        name = self.ui.tableWidgetOPT.item(selected, 1)

        # check if anythin on the OPT list
        if not name:
            print "Selected a row with no opt info"
        else:
            print "change channel"
            self.ui.lineEditInput.setText(os.path.join(path_out,str(name.text())))
            self.reset_inputs()
            self.autofill_pipe()



def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()