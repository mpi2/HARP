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

The following functions are used to add the recon folders to the processing list and save the config file.

When a recon folder is added to the processing list a config file is saved in the output folder location. This is
done in the **add_to_list_action()** method.

For microCT data this is straight forward but for OPT data it is more complicated as multiple channels are added
to the list. This method **start()** is used to handle the different way folders are added to the list.


--------------
"""
from PyQt5 import QtGui, QtWidgets
import os
from . import errorcheck
from . import getpickle


class Queuejob(object):

    def __init__(self, mainwindow, center):
        self.mainwindow = mainwindow
        self.center = center

    def start(self):
        """ Function to start the process of adding recon folders onto the processing list

        Uses the **add_to_list_action()** method to add folders onto the processing list and save a config file in the
        output folder location.

        For microCT data this is straight forward but for OPT data it is more complicated as multiple channels are added
        to the list.

        **For multi-channel OPT data:**
        Multi-channel OPT data can either be handled individually or together. The default is to handle together.

        This is achieved by a for loop which goes through the OPT channels list. For each OPT channel the following occurs
        in the for loop:
        * Recon folder is added to the input folder line edit box
        * Autofill operations are carried out (automatically determining the parameters).
        * If the autofill operation completes successfully the channel is then added to the processing list
        * A config file is saved in the relevant output folder location
        * Then parameters tab is also reset to its original view

        NOTE:
        The methods here are not technically part of the HARP class but can be used as if they are. They are seperated from
        the harp.py file just for convenience. To run a method from this module in harp.py the following notation can be
        used start(self.mainwindow) rather than self.mainwindow.start().

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :ivar str self.mainwindow.modality: Either MicroCT or OPT. Used here but not modified.
        :ivar boolean self.mainwindow.stop_chn_for_loop: Stops the for group OPT channel for loop.
            Used and modified in both methods here
        :ivar list self.mainwindow.chan_full: List of all the OPT channels HARP can find, created in autofill. Not modified here.
        :ivar str self.mainwindow.derived_output_name: Derived output name when processing group OPT channels.
            Initialised in this method

        .. seealso::
                :func:`add_to_list_action()`,
                :func:`harp.MainWindow.reset_inputs()`,
                :func:`harp.MainWindow.autofill_pipe()`,
                :func:`harp.MainWindow.man_crop_off()`,
                :func:`harp.MainWindow.man_crop_off()`,
                :func:`harp.MainWindow.man_crop_on()`
        """

        # Modality check
        # If MicroCT or individual OPT run, just add to the processing list
        # If group OPT run, go through the for loop of OPT channels
        # First reset this instance variable (used later)
        self.mainwindow.derived_output_name = None

        self.mainwindow.scan_folder = str(self.mainwindow.ui.lineEditScan.text())

        # get folder names
        in_dir = str(self.mainwindow.ui.lineEditInput.text())
        path, folder_name = os.path.split(in_dir)

        # Check if microCT, individual OPT or Batch OPT
        if self.mainwindow.modality == "MicroCT":
            # Standard microCT run
            self.add_to_list_action()

        elif self.mainwindow.ui.checkBoxInd.isChecked():
            # Individual OPT run
            self.add_to_list_action()

        #======================================================================
        # Batch OPT run
        #======================================================================
        else:
            ######## Save parameter settings ###########
            # Save the initial settings to be displayed again after all processing has been added
            # Recon log
            recon_log = self.mainwindow.ui.lineEditCTRecon.text()
            # SPR (should prob get rid of this
            spr = self.mainwindow.ui.lineEditCTSPR.text()
            # Output folder
            out_dir_original = self.mainwindow.ui.lineEditOutput.text()
            # Input folder
            in_dir_orignal = self.mainwindow.ui.lineEditInput.text()
            # derived name
            derive = self.mainwindow.ui.lineEditDerivedChnName.text()
            # crop option
            if self.mainwindow.ui.radioButtonAuto.isChecked():
                crop_option = "auto"
            elif self.mainwindow.ui.radioButtonDerived.isChecked():
                crop_option = "derived"
            elif self.mainwindow.ui.radioButtonUseOldCrop.isChecked():
                crop_option = "old"
            elif self.mainwindow.ui.radioButtonMan.isChecked():
                crop_option = "man"

            ######## Channel loop ###########
            # Make sure stop switch is turned off
            self.mainwindow.stop_chn_for_loop = False
            # go through list and get the channel names
            for name in self.mainwindow.chan_full:
                # if off switch is True then stop loop
                if self.mainwindow.stop_chn_for_loop:
                    break

                # Get full path of the input folder for channel
                chan_path = os.path.join(path,name)

                # backslash and forward slash should not be a problem but just incase we remove them here
                chan_short = chan_path.replace("\\", "")
                chan_short = chan_short.replace("/", "")
                in_dir_short = in_dir.replace("\\", "")
                in_dir_short = in_dir_short.replace("/", "")

                # Check if the input directory is already set to the current channel in the loop
                # If the current channel is not the same as the loop then perform autofill before adding to the list
                # If it is the same
                if chan_short == in_dir_short:
                    # In case the output folder name is different to input folder name. Need to save what will be used
                    # as the derived folder
                    self.mainwindow.derived_output_name = self.mainwindow.ui.lineEditOutput.text()
                    # add to the list
                    self.add_to_list_action()
                    # go to next iteration
                    continue
                else:
                    # Not the original channel so autofill the paramters tab
                    self.mainwindow.ui.lineEditInput.setText(chan_path)
                    # reset inputs
                    self.mainwindow.reset_inputs()
                    self.mainwindow.autofill_pipe(suppress=True)

                #need to setup the output folder based on original folder.
                #multiple channels (onl)
                if len(self.mainwindow.chan_full) > 1:
                    path_out, old_folder_name = os.path.split(str(out_dir_original))
                    output_folder = os.path.join(path_out,name)
                    self.mainwindow.ui.lineEditOutput.setText(os.path.abspath(output_folder))

                # Add to list!
                self.add_to_list_action()

            ######## Reset parameter settings ###########
            # reset the parameters tab back to what originally was for the user.
            # Save the initial settings to be displayed again after all processing has been added
            # Input folder
            self.mainwindow.ui.lineEditInput.setText(in_dir_orignal)
            self.mainwindow.autofill_pipe(suppress=True)

            # The following may have been changed from the user so have to be changed after the autofill
            # Recon log
            self.mainwindow.ui.lineEditCTRecon.setText(recon_log)
            # SPR (should prob get rid of this
            self.mainwindow.ui.lineEditCTSPR.setText(spr)
            # Scan folder
            self.mainwindow.ui.lineEditScan.setText(self.mainwindow.scan_folder)
            # Output folder
            self.mainwindow.ui.lineEditOutput.setText(out_dir_original)
            # derived name
            self.mainwindow.ui.lineEditDerivedChnName.setText(derive)
            # crop option
            if crop_option == "auto":
                self.mainwindow.ui.radioButtonAuto.setChecked(True)
                self.mainwindow.man_crop_off()
            elif crop_option == "derived":
                self.mainwindow.ui.radioButtonDerived.setChecked(True)
                self.mainwindow.derive_on()
            elif crop_option == "old":
                self.mainwindow.ui.radioButtonUseOldCrop.setChecked(True)
                self.mainwindow.man_crop_on()
            elif crop_option == "man":
                self.mainwindow.ui.radioButtonMan.setChecked(True)
                self.mainwindow.man_crop_on()


    def add_to_list_action(self):
        """ Adds recon to processing list, creates pickle file and does error checks

        1. First perform error checks using the errorcheck module
        2. Then creates a pickle file of the parameters using the getpickle module and saves in the output folder
        3. the currently selected recon (based on the parameters tab) onto the processing list

        :param obj self.mainwindow:
            Although not technically part of the class, can still use this method as if it was part of the HARP class.
        :ivar str self.mainwindow.modality: Either MicroCT or OPT. Used here but not modified.
        :ivar str self.mainwindow.stop: Modified with errorcheck module. If True
        :return: Returns early if processing group OPT channels and an invalid channel chosen to derive dimensions from

        .. seealso::
            :func:`errorcheck.errorCheck()`,
            :func:`getpickle.get_pickle()`
        """

        # get the input name for table
        input_name = str(self.mainwindow.ui.lineEditInput.text())

        # Error check for multiple channel for loop
        if self.mainwindow.modality == "OPT" and self.mainwindow.ui.radioButtonDerived.isChecked() \
                and not self.mainwindow.ui.lineEditDerivedChnName.text():
            self.mainwindow.stop = True
            self.mainwindow.stop_chn_for_loop = True
            QtWidgets.QMessageBox.warning(self.mainwindow, 'Message', 'Warning: Derived dimensions for autocrop option selected.'
                                                       ' This requires a valid channel to be used to get the crop '
                                                       'dimensions from')
            return

        # Perform some checks before any processing is carried out
        print(str(self.mainwindow.ui.lineEditOutput.text()))
        errorcheck.errorCheck(self.mainwindow)

        # If an error has occured self.mainwindow.stop will be defined. if None then no error.
        if not self.mainwindow.stop:
            # Get the parameters needed for processing
            getpickle.get_pickle(self.mainwindow, self.center)

            # Set up the table. 300 rows should be enough!
            self.mainwindow.ui.tableWidget.setRowCount(300)

            # Set the data for an individual row
            # Set up the name data cell
            item = QtWidgets.QTableWidgetItem()
            self.mainwindow.ui.tableWidget.setItem(self.mainwindow.count_in, 0, item)
            item = self.mainwindow.ui.tableWidget.item(self.mainwindow.count_in, 0)
            item.setText(input_name)

            # Set up the output folder cell
            item = QtWidgets.QTableWidgetItem()
            self.mainwindow.ui.tableWidget.setItem(self.mainwindow.count_in, 1, item)
            item = self.mainwindow.ui.tableWidget.item(self.mainwindow.count_in, 1)
            item.setText(self.mainwindow.configOb.output_folder)

            # Set up the status cell
            item = QtWidgets.QTableWidgetItem()
            self.mainwindow.ui.tableWidget.setItem(self.mainwindow.count_in, 2, item)
            item = self.mainwindow.ui.tableWidget.item(self.mainwindow.count_in, 2)
            # Status is pending untill processing has started
            item.setText("Pending")

            # count_in is the counter for the row to add data
            self.mainwindow.count_in += 1

            # Reszie the columns to fit the data
            self.mainwindow.ui.tableWidget.resizeColumnsToContents()

            # Go to second tab
            self.mainwindow.ui.tabWidget.setCurrentIndex(1)
