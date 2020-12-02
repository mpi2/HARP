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


**Summary:**

The following functions are used to update the parameters tab based on the input file used.


--------------
"""

from PyQt5 import QtGui, QtWidgets
import sys
import os
import re
import datetime


class Autofill(object):
    def __init__(self, mainwindow):
        self.mainwindow = mainwindow


    def get_recon_log(self):
        """ Gets the recon log from the original recon folder, also gets the pixel size information using **get_pixel()**

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :ivar str self.mainwindow.pixel_size: Pixel size. Modified here.
        :raises IOError: Can't find recon log
        :raises Exception: Custom python exception. Can't fin recon log

        .. seealso::
            :func:`get_pixel()`
        """
        input = str(self.mainwindow.ui.lineEditInput.text())

        # Get the folder name and path name
        # path, folder_name = os.path.split(input)

        try:
            # # I think some times the log file is .txt and sometimes .log, a check for both types and other
            # # old formats of log files is checked as follows:
            # if os.path.exists(os.path.join(path,folder_name,folder_name+".txt")):
            #     recon_log_path = os.path.join(path,folder_name,folder_name+".txt")
            # elif os.path.exists(os.path.join(path,folder_name,folder_name+"_rec.txt")):
            #     recon_log_path = os.path.join(path,folder_name,folder_name+"_rec.txt")
            # elif os.path.exists(os.path.join(path,folder_name,folder_name+".log")):
            #     recon_log_path = os.path.join(path,folder_name,folder_name+".log")
            # elif os.path.exists(os.path.join(path,folder_name,folder_name+"_rec.log")):
            #     recon_log_path = os.path.join(path,folder_name,folder_name+"_rec.log")
            # else:
            #     raise Exception('No log file')

            log_paths = [f for f in os.listdir(input) if f.endswith("_rec.log")]

            if len(log_paths) == 1:
                recon_log_path = os.path.join(input, log_paths[0])

            # To make sure the path is in the correct format (prob not necessary..)
            self.mainwindow.recon_log_path = os.path.abspath(recon_log_path)

            # Open the log file as read only
            recon_log_file = open(self.mainwindow.recon_log_path, 'r')

            # get pixel size from get_pixel method
            self.mainwindow.pixel_size = self.get_pixel(self.mainwindow.modality, recon_log_file)

            # Display the number on the lcd display
            self.mainwindow.ui.lcdNumberPixel.display(self.mainwindow.pixel_size)

            # Set recon log text
            self.mainwindow.ui.lineEditCTRecon.setText(str(self.mainwindow.recon_log_path))

        except IOError as e:
            # Python standard exception identifies recon file not found
            print("exception re")
            self.mainwindow.ui.lineEditCTRecon.setText("Not found")
            self.mainwindow.pixel_size = ""
            self.mainwindow.ui.lcdNumberPixel.display(self.mainwindow.pixel_size)
        except Exception as inst:
            # Custom exception identifies recon file not found
            self.mainwindow.pixel_size = ""
            self.mainwindow.ui.lcdNumberPixel.display(self.mainwindow.pixel_size)
            self.mainwindow.ui.lineEditCTRecon.setText("Not found")
        except:
            self.mainwindow.pixel_size = ""
            self.mainwindow.ui.lcdNumberPixel.display(self.mainwindow.pixel_size)
            QtWidgets.QMessageBox.warning(self.mainwindow, 'Message', 'Warning: Unexpected error getting recon log file',sys.exc_info()[0])
            self.mainwindow.ui.lineEditCTRecon.setText("Not found")


    def get_pixel(self, modality, recon_log_file):
        """ Gets the pixel size from the recon log. Different regex required for OPT or uCT

        :param str modality: OPT or uCT
        :param str recon_log_file: recon log file full path
        :return:
        """
        # Regex is different for opt and uct as they have different recon files
        # if modality == "OPT":
        prog = re.compile("^Image Pixel Size \(um\)=\s*(\w+.\w+)")
        # else:
        #     prog = re.compile("^Pixel Size \(um\)\=(\w+.\w+)")

        # for loop to go through the recon log file
        for line in recon_log_file:
            # "chomp" the line endings off
            line = line.rstrip()
            # if the line matches the regex print the (\w+.\w+) part of regex
            if prog.match(line) :
                # Grab the pixel size with with .group(1)
                pixel_size = prog.match(line).group(1)
                return pixel_size
                break

    def get_name(self, name, suppress=False):
        """ Gets the id from the folder name. Then fills out the text boxes on the main window with the relevant information

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :param str name: Full folder name with path
        :param boolean suppress: True warning messages are sent. False they are not.

        :raise IndexError: Missing descriptor completely
        :raise ValueError: Incorrect format of descriptor

        NOTE: Gather error messages from exceptions to display one combined error message at the end
        """
        # Get the folder name and path
        path,folder_name = os.path.split(name)

        # first split the folder into list of identifiers
        name_list = folder_name.split("_")
        # the full name will at first just be the folder name
        self.mainwindow.ui.lineEditName.setText(folder_name)
        self.mainwindow.full_name = folder_name

        # Need to have exception to catch if the name is not in correct format.
        # If the name is not in the correct format it should flag to the user that this needs to be sorted
        # Added additional regex which the user has to check
        error_list = []

        # Checking Date
        try:
            self.mainwindow.ui.lineEditDate.setText(name_list[0])
            datetime.datetime.strptime(name_list[0], '%Y%m%d')
        except IndexError:
            error_list.append("- Date not available")
        except ValueError:
            error_list.append("- Incorrect date format should be = [YYYYMMDD]")

        # Checking gene name/group
        try:
            self.mainwindow.ui.lineEditGroup.setText(name_list[1])
        except IndexError:
            error_list.append("- Gene name info not available")

        # Checking age/stage
        try:
            self.mainwindow.ui.lineEditAge.setText(name_list[2])
        except IndexError:
            error_list.append("- Stage/age info not available")

        # Litter
        try:
            self.mainwindow.ui.lineEditLitter.setText(name_list[3])
        except IndexError:
            error_list.append("- Litter info not available")

        # Zygosity
        try:
            self.mainwindow.ui.lineEditZygosity.setText(name_list[4])
            prog = re.compile("HOM|HET|WT|ND|NA",re.IGNORECASE)
            if not prog.search(name_list[4]):
                error_list.append("- Zygosity should be either HOM,HET,WT,ND or NA")

        except IndexError:
            error_list.append("- Zygosity info not available")

        # Sex
        try:
            self.mainwindow.ui.lineEditSex.setText(name_list[5])

            prog = re.compile("XX|XY|ND",re.IGNORECASE)
            if not prog.search(name_list[5]):
                error_list.append("- Sex should be either XX,XY or ND")

        except IndexError:
            error_list.append("- Sex info not available")

        # Channel (OPT only)
        try:
            if self.mainwindow.modality == "OPT":
                self.mainwindow.ui.lineEditChannel.setText(name_list[6])
                if name_list[6].lower() == "rec" :
                    error_list.append("- IMPORTANT: OPT needs to include channel information. e.g. UV")


        except IndexError as e:
            error_list.append("- IMPORTANT: OPT needs to include channel information. e.g. UV")

        # Show the user all the error messages together.
        if error_list:
            error_string = os.linesep.join(error_list)
            if not suppress:
                QtWidgets.QMessageBox.warning(self.mainwindow, 'Message', 'Warning (Naming not canonical):'+os.linesep+error_string)


    def auto_file_out(self, reprocess_mode):
        """ Auto fill to make output folder name. Just replaces 'recons' to 'processed recons' if possible

        if reprocess_mode is True the input folder should be a previous cropped folder
        the output folder will then be set to the parent folder in order to remake the scaled stacks and bz2s

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :param reprocess_mode
            bool
            If True keep the output folder the same as input
        """

        input_path = str(self.mainwindow.ui.lineEditInput.text())
        path, folder_name = os.path.split(input_path)

        if reprocess_mode:
            output_path = os.path.abspath(os.path.join(input_path, os.pardir))
            self.mainwindow.ui.lineEditOutput.setText(os.path.abspath(output_path))
            return

        try:
            pattern = re.compile("recons", re.IGNORECASE)
            if re.search(pattern, input_path):
                output_path = pattern.sub("processed_recons", path)
                output_path = os.path.join(output_path, self.mainwindow.full_name)
                self.mainwindow.ui.lineEditOutput.setText(os.path.abspath(output_path))
            else:
                print("autofill set output folder")
                output_path = os.path.join(path, "processed_recons", folder_name)

                self.mainwindow.ui.lineEditOutput.setText(os.path.abspath(output_path))
        except:
            QtWidgets.QMessageBox.warning(self.mainwindow, 'Message', 'Warning: Unexpected getting and auto file out', sys.exc_info()[0])


    def auto_get_scan(self):
        """ Auto find scan folder. Just replaces 'recons' to 'processed recons' if possible

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        """
        input = str(self.mainwindow.ui.lineEditInput.text())
        pattern = re.compile("recons", re.IGNORECASE)
        if re.search(pattern, input):
            self.mainwindow.scan_folder = pattern.sub("scan", input)
            if os.path.exists(self.mainwindow.scan_folder):
                self.mainwindow.ui.lineEditScan.setText(self.mainwindow.scan_folder)
            else :
                self.mainwindow.ui.lineEditScan.setText("Not found")
                self.mainwindow.scan_folder = ""
        else :
            self.mainwindow.ui.lineEditScan.setText("Not found")
            self.mainwindow.scan_folder = ""

    def auto_get_SPR(self):
        """  Finds any SPR files.

        NOTE: This might be a bit redundant as the SPR files are not essential and are copied over with
        any other file regardless
        """
        input = str(self.mainwindow.ui.lineEditInput.text())
        # Get the SPR file. Sometimes fiels are saved with upper or lower case file extensions
        # The following is bit of a stupid way of dealing with this problem but I think it works....
        SPR_file_bmp = os.path.join(input,self.mainwindow.full_name+"_spr.bmp")
        SPR_file_BMP = os.path.join(input,self.mainwindow.full_name+"_spr.BMP")
        SPR_file_tif = os.path.join(input,self.mainwindow.full_name+"_spr.tif")
        SPR_file_TIF = os.path.join(input,self.mainwindow.full_name+"_spr.TIF")
        SPR_file_jpg = os.path.join(input,self.mainwindow.full_name+"_spr.jpg")
        SPR_file_JPG = os.path.join(input,self.mainwindow.full_name+"_spr.JPG")

        if os.path.isfile(SPR_file_bmp):
            self.mainwindow.ui.lineEditCTSPR.setText(SPR_file_bmp)
        elif os.path.isfile(SPR_file_BMP):
            self.mainwindow.ui.lineEditCTSPR.setText(SPR_file_BMP)
        elif os.path.isfile(SPR_file_tif):
            self.mainwindow.ui.lineEditCTSPR.setText(SPR_file_tif)
        elif os.path.isfile(SPR_file_TIF):
            self.mainwindow.ui.lineEditCTSPR.setText(SPR_file_TIF)
        elif os.path.isfile(SPR_file_jpg):
            self.mainwindow.ui.lineEditCTSPR.setText(SPR_file_jpg)
        elif os.path.isfile(SPR_file_JPG):
            self.mainwindow.ui.lineEditCTSPR.setText(SPR_file_JPG)
        else:
            self.mainwindow.ui.lineEditCTSPR.setText("Not found")


    def folder_size_approx(self):
        """ Gets the approx folder size of the original recon folder and updates the paramters tab with the info.

        Calculating the folder size by going through each file would take too long. This
        function just checks the first recon file and then multiples this by the number of recon files.

        Output for display for the GUI will be in gb or mb depending on the size of the folder. This is done in
        size_cleanup()

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :ivar str self.mainwindow.f_size_out_gb: The file size in gb. Modified here.

        .. seealso::
            :func:`size_cleanup()`
        """

        # Get the input folder information
        input = str(self.mainwindow.ui.lineEditInput.text())

        # create a regex get example recon file
        prog = re.compile("(.*)_rec\d+\.(bmp|tif|jpg|jpeg)",re.IGNORECASE)

        try:
            filename = ""
            # for loop to go through the directory
            for line in os.listdir(input) :
                line =str(line)
                #print line+"\n"
                # if the line matches the regex break
                if prog.match(line) :
                    filename = line
                    break

            filename = os.path.join(input,filename)
            file1_size = os.stat(filename).st_size

            # Need to distinguish between the file types. The calculation only includes recon files, as we known they will all be the same size.
            # This means the figure given in HARP will not be the exact folder size but the size of the recon "stack"
            num_files = len([f for f in os.listdir(input) if ((f[-4:] == ".bmp") or (f[-4:] == ".tif") or (f[-4:] == ".jpg") or (f[-4:] == ".jpeg") or
                              (f[-4:] == ".BMP") or (f[-4:] == ".TIF") or (f[-4:] == ".JPG") or (f[-4:] == ".JPEG") or
                              (f[-7:] != "spr.bmp") or (f[-7:] != "spr.tif") or (f[-7:] != "spr.jpg") or (f[-7:] != "spr.jpeg") or
                              (f[-7:] != "spr.BMP") or (f[-7:] != "spr.TIF") or (f[-7:] != "spr.JPG") or (f[-7:] != "spr.JPEG"))])

            approx_size = num_files*file1_size

            # convert to gb
            size_mb =  (approx_size/(1024*1024))
            size_gb =  (approx_size/(1024*1024*1024.0))

            # Save file size as an object to be used later
            self.mainwindow.f_size_out_gb = "%0.4f" % (size_gb)

            #Clean up the formatting of gb mb
            self.size_cleanup(size_gb, size_mb)

        except Exception as e:
            # Should potentially add some other error catching
            message = QtWidgets.QMessageBox.warning(self.mainwindow, "Message", "Unexpected error in folder size calc: {0}".format(e))

    # def contiguous_naming(self):
    #
    #     indir = str(self.mainwindow.ui.lineEditInput.text())
    #     filelist = sorted(processing.gefilelist(indir))
    #
    #     numb_re = re.compile("\D+\..+$",re.IGNORECASE)
    #     for file_ in filelist:
    #         if numb_re.match(file_):
    #             print numb_re.groups
    #



    def size_cleanup(self, size_gb, size_mb):
        """ Used in folderSizeApprox() to format the output.

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :param float f_size_out:
        :param approx_size:
        """
        # Check if size should be shown as gb or mb
        # Need to change file size to 2 decimal places
        if size_gb < 0.05 :
            # make to 2 decimal places
            size_mb =  "%0.2f" % (size_mb)
            # change label to show mb
            self.mainwindow.ui.labelFile.setText("Folder size (Mb)")
            # update lcd display
            self.mainwindow.ui.lcdNumberFile.display(size_mb)
        else :
            # display as gb
            # make to 2 decimal places
            size_gb =  "%0.2f" % (size_gb)
            # change label to show mb
            self.mainwindow.ui.labelFile.setText("Folder size (Gb)")
            # update lcd display
            self.mainwindow.ui.lcdNumberFile.display(size_gb)

    #==========================================================================
    # All the uCT channel shenanigans
    #==========================================================================
    def opt_uCT_check(self, suppress=False):
        """ Checks whether or not folder name contains reference to either opt or microCT

        Updates the GUI options based on modality

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :param boolean suppress: If True warning messages will spit out. If suppressed they won't
        :ivar str self.mainwindow.modality: Changes based on the modality chosen. Value should be either 'MicroCT' or 'OPT'. Modified.
        """
        # Get in file
        file_in = str(self.mainwindow.ui.lineEditInput.text())
        log_OPT = False
        log_uCT = False

        # Scan log file for evidence of OPT or uCT
        try:
            opt_terms = ['OPT', 'Skyscan3001', 'UV']
            uCT_terms = ['MicroCT', 'Skyscan1172']
            log_file = str(self.mainwindow.recon_log_path)
            with open(log_file, "r") as f:
                search_lines = f.readlines()
                for k, line in enumerate(search_lines):
                    if any(term in line for term in opt_terms):
                        log_OPT = True
                        break
                    if any(term in line for term in uCT_terms):
                        log_uCT = True
                        break
        except IOError:
            print("Failed to read log file for OPT/uCT check")

        # Create compiled regex
        p_opt = re.compile("OPT",re.IGNORECASE)
        p_uCT = re.compile("MicroCT",re.IGNORECASE)

        # Check if OPT and enable relevant options
        if log_OPT or p_opt.search(file_in):
            self.mainwindow.modality = "OPT"
            self.mainwindow.ui.radioButtonOPT.setChecked(True)
            self.mainwindow.ui.lineEditChannel.setEnabled(True)
            self.mainwindow.ui.labelChannel.setEnabled(True)
            self.mainwindow.ui.tableWidgetOPT.setEnabled(True)
            self.mainwindow.ui.radioButtonDerived.setEnabled(True)
            if self.mainwindow.ui.radioButtonDerived.isChecked():
                self.mainwindow.ui.lineEditDerivedChnName.setEnabled(True)
            self.mainwindow.ui.checkBoxInd.setEnabled(True)

        # Check if uCT and enable relevant options
        elif log_uCT or p_uCT.search(file_in):
            self.mainwindow.modality = "MicroCT"
            self.mainwindow.ui.radioButtonuCT.setChecked(True)
            self.mainwindow.ui.lineEditChannel.setEnabled(False)
            self.mainwindow.ui.labelChannel.setEnabled(False)
            self.mainwindow.ui.tableWidgetOPT.setEnabled(False)
            self.mainwindow.ui.radioButtonDerived.setEnabled(False)
            self.mainwindow.ui.lineEditDerivedChnName.setEnabled(False)
            self.mainwindow.ui.checkBoxInd.setEnabled(False)
        else:
            if not suppress:
                QtWidgets.QMessageBox.warning(self.mainwindow, 'uCT or OPT?', 'Unable to determine imaging modality. '
                                                               'Please select uCT or OPT.')

    def get_channels(self):
        """ Updates the OPT list on the GUI

        This method does the following:
        * Check if OPT is selected
        * look up recon parent folder and search for other available OPT channels
        * Make a list of these channels
        * Loop through this list and each channel to the OPT channel table (the parameters tab)

        .. seealso::
            :func:`error_check_chn()`,
            :func:`get_crop_box()`
            :func:`check_if_on_list()`
        """

        # reset the table
        self.mainwindow.ui.tableWidgetOPT.clearContents()

        # Make sure OPT is selected
        if not self.mainwindow.modality == "OPT":
            return

        # Are there matching folders in the parent directory of the input directory
        in_dir = str(self.mainwindow.ui.lineEditInput.text())

        # Get the folder name and path name
        path, folder_name = os.path.split(in_dir)

        # get a list of the names in the folder name
        l_init = folder_name.split("_")

        # get the name without the channel (only works if name is in the correct format)
        base_name = '_'.join(l_init[0:6])

        # set the name up for the current channel. Blank if name not set up properly
        try:
            chn_init = str(l_init[6])
        except IndexError:
            chn_init = "NA"

        # Initialised tuples
        chan_full = []
        chan_short = []

        # add original current channel to the channel lists.
        # Full has the path, short does not
        chan_full.append(folder_name)
        chan_short.append(chn_init)

        #===========================================================================================
        # look up recon parent folder and search for other available OPT channels
        #===========================================================================================
        # Check parent input folder actually exists
        if not os.path.exists(path):
            return

        # for loop to go through the parent input directory
        for line in os.listdir(path):

            # convert to string (had problems in the past with numbers)
            line =str(line)

            # Check if the line matches the base_name but is not the same as the input file. The folder is probably another
            # channel
            # Check line matches base name
            m = re.search(base_name,line)

            # Check if is not the same as the input file
            if m and (not line == folder_name):

                # Check if it is a folder with recons etc for the other channels
                if not self.error_check_chn(os.path.join(path, line)):

                    # if it is then add to the channel lists
                    chan_full.append(line)
                    chan_short.append(m.group(0))

        #===========================================================================================
        # Add channels to OPT table on parameters tab
        #===========================================================================================
        # initialise count
        count = 0

        # Create instance variable for other methods to use
        self.mainwindow.chan_full = chan_full

        # for loop through the channel names
        for name in chan_full:

            # split the name into IMPC components
            l = name.split("_")

            # If cant split into IMPC components then can't set the channel type
            try:
                chn = l[6]
            except IndexError:
                chn = "NA"

            # Make the current channel highlighted
            chn_item = QtWidgets.QTableWidgetItem()
            self.mainwindow.ui.tableWidgetOPT.setItem(count, 0, chn_item)
            chn_item = self.mainwindow.ui.tableWidgetOPT.item(count, 0)
            chn_item.setText(chn)
            if name == folder_name:
                chn_item.setBackground(QtGui.QColor(220, 0, 0))

            # Set up the name of the recon
            item = QtWidgets.QTableWidgetItem()
            self.mainwindow.ui.tableWidgetOPT.setItem(count, 1, item)
            item = self.mainwindow.ui.tableWidgetOPT.item(count, 1)
            item.setText(name)

            # Set up whether or not there is a crop box available
            # The get_crop_box checks if the parent processed folder to see if the channel has previously been analysed
            # and a cropbox file has been saved
            if self.get_crop_box(name):
                crop_status = "Yes"
            # check_if_on_list method checks if channel is on the processing list
            elif self.check_if_on_list(name):
                crop_status = "On list"
            else:
                crop_status = "No"

            # add to the GUI table
            item = QtWidgets.QTableWidgetItem()
            self.mainwindow.ui.tableWidgetOPT.setItem(count, 2, item)
            item = self.mainwindow.ui.tableWidgetOPT.item(count, 2)
            item.setText(crop_status)

            # count_in is the counter for the row to add data
            count += 1

            # Reszie and sort the columns to fit the data
            self.mainwindow.ui.tableWidgetOPT.resizeColumnsToContents()
            self.mainwindow.ui.tableWidgetOPT.setSortingEnabled(True)
            self.mainwindow.ui.tableWidgetOPT.sortByColumn(0)

    def get_crop_box(self, name):
        """ Checks if cropbox file exists for a given recon name

        Used by get_channels

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :param str name: Recon name for which the cropbox path is to be checked
        :return boolean: True if cropbox path exists
        """
        if not self.mainwindow.modality == "OPT":
            return
        out_dir = str(self.mainwindow.ui.lineEditOutput.text())
        path_out,folder_name = os.path.split(out_dir)

        # See if the cropbox file exists
        cropbox_path = os.path.join(path_out, name, "Metadata","cropbox.txt")
        if os.path.exists(cropbox_path):
            return True


    def check_if_on_list(self, name):
        """  A while loop is used to go through the processing table see if the channel is on the list

        Used by get_channels

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :param name:
        :return boolean: True if channel is on list
        """
        count = 0
        while True:
            # This gets the status text
            name_on_list = self.mainwindow.ui.tableWidget.item(count, 0)
            if not name_on_list:
                # if not defined it means there are no recons left to process
                return False
            if re.search(name, name_on_list.text()):
                # this row has the OPT channel ID meaning a cropbox will be ready when this is ran
                return True
            count += 1


    def error_check_chn(self, chn_dir):
        """ Checks the channel recon directory to see if it is a valid file

        Used in get_channels

        :param str chn_dir: The channel directory to be checked
        :return int: 1 if error 0 or nothing if OK
        """
        # Check if input folder exists
        if not os.path.exists(chn_dir):
            return 1

        # Check if a directory
        if not os.path.isdir(chn_dir):
            return 1

        #Check if folder is empty
        if os.listdir(chn_dir) == []:
                return 1

        #Check if input folder contains any image files
        prog = re.compile("(.*).(bmp|tif|jpg|jpeg)",re.IGNORECASE)

        # init file check variable
        file_check = None

        # for loop to go through the directory
        for line in os.listdir(chn_dir) :
            line =str(line)
            #print line+"\n"
            # if the line matches the regex break
            if prog.match(line) :
                file_check = True
                break

        # No valid files return with error
        if not file_check:
            return 1


    def auto_get_derived(self):
        """ Updates the derived crop box line edit box on the GUI

        NOTE: Only works for IMPC setup folder structure

        * While loop through OPT list.
        * See if one of them is either processed or on list.
            * Previously checked if processed or on list in get_channels()
        * If one of them is - Set as the derived crop box on the GUI
        """
        # Get row count
        n = self.mainwindow.ui.tableWidgetOPT.rowCount()

        # Get parent output folder
        out_dir = str(self.mainwindow.ui.lineEditOutput.text())
        path_out, folder_name = os.path.split(out_dir)

        # For loop through the OPT list
        for i in range(n):
            # Get info from table
            processed = self.mainwindow.ui.tableWidgetOPT.item(i, 2)
            name = self.mainwindow.ui.tableWidgetOPT.item(i, 1)

            if processed:
                # check if on processing list
                if processed.text() == "On list":
                        # If it is the current recon don't use as the derived
                        if name.text() == folder_name:
                            continue

                # Now we can use the channel if it matches the following criteria
                if processed.text() == "Yes" or processed.text() == "On list":
                    self.mainwindow.crop_box_use = True
                    self.mainwindow.ui.radioButtonDerived.setEnabled(True)
                    self.mainwindow.ui.radioButtonDerived.setChecked(True)
                    self.mainwindow.ui.lineEditDerivedChnName.setEnabled(True)

                    # show name for user
                    self.mainwindow.ui.lineEditDerivedChnName.setText(name.text())
                    break
