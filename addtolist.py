"""
**Summary:**

The following functions are used to add the recon folders to the processing list and save the config file.

When a recon folder is added to the processing list a config file is saved in the output folder location. This is
done in the **add_to_list_action()** method.

For microCT data this is straight forward but for OPT data it is more complicated as multiple channels are added
to the list. This method **start()** is used to handle the different way folders are added to the list.

NOTE:
The methods here are not technically part of the HARP class but can be used as if they are. They are seperated from
the harp.py file just for convenience. To run a method from this module in harp.py the following notation can be
used start(self) rather than self.start().

--------------
"""
from PyQt4 import QtGui
import os
import errorcheck
import getpickle


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
    used start(self) rather than self.start().

    :param obj self:
        Although not technically part of the class, can still use this method as if it was part of the HARP class.
    :ivar str self.modality: Either MicroCT or OPT. Used here but not modified.
    :ivar boolean self.stop_chn_for_loop: Stops the for group OPT channel for loop.
        Used and modified in both methods here
    :ivar list self.chan_full: List of all the OPT channels HARP can find, created in autofill. Not modified here.
    :ivar str self.derived_output_name: Derived output name when processing group OPT channels.
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
    self.derived_output_name = None

    # get folder names
    in_dir = str(self.ui.lineEditInput.text())
    path, folder_name = os.path.split(in_dir)

    # Check if microCT, individual OPT or Batch OPT
    if self.modality == "MicroCT":
        # Standard microCT run
        add_to_list_action(self)

    elif self.ui.checkBoxInd.isChecked():
        # Individual OPT run
        add_to_list_action(self)

    #======================================================================
    # Batch OPT run
    #======================================================================
    else:
        ######## Save parameter settings ###########
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

        ######## Channel loop ###########
        # Make sure stop switch is turned off
        self.stop_chn_for_loop = False
        # go through list and get the channel names
        for name in self.chan_full:
            # if off switch is True then stop loop
            if self.stop_chn_for_loop:
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
                self.derived_output_name = self.ui.lineEditOutput.text()
                # add to the list
                add_to_list_action(self)
                # go to next iteration
                continue
            else:
                # Not the original channel so autofill the paramters tab
                self.ui.lineEditInput.setText(chan_path)
                # reset inputs
                self.reset_inputs()
                self.autofill_pipe(suppress=True)

            #need to setup the output folder based on original folder.
            #multiple channels (onl)
            if len(self.chan_full)>1:
                path_out, old_folder_name = os.path.split(str(out_dir_original))
                output_folder = os.path.join(path_out,name)
                self.ui.lineEditOutput.setText(os.path.abspath(output_folder))

            # Add to list!
            add_to_list_action(self)

        ######## Reset parameter settings ###########
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


def add_to_list_action(self):
    """ Adds recon to processing list, creates pickle file and does error checks

    1. First perform error checks using the errorcheck module
    2. Then creates a pickle file of the parameters using the getpickle module and saves in the output folder
    3. the currently selected recon (based on the parameters tab) onto the processing list

    :param obj self:
        Although not technically part of the class, can still use this method as if it was part of the HARP class.
    :ivar str self.modality: Either MicroCT or OPT. Used here but not modified.
    :ivar str self.stop: Modified with errorcheck module. If True
    :return: Returns early if processing group OPT channels and an invalid channel chosen to derive dimensions from

    .. seealso::
        :func:`errorcheck.errorCheck()`,
        :func:`getpickle.get_pickle()`
    """

    # get the input name for table
    input_name = str(self.ui.lineEditInput.text())

    # Error check for multiple channel for loop
    if self.modality == "OPT" and self.ui.radioButtonDerived.isChecked() \
            and not self.ui.lineEditDerivedChnName.text():
        self.stop = True
        self.stop_chn_for_loop = True
        QtGui.QMessageBox.warning(self,'Message','Warning: Derived dimensions for autocrop option selected.'
                                                    ' This requires a valid channel to be used to get the crop '
                                                    'dimensions from')
        return

    # Perform some checks before any processing is carried out
    print str(self.ui.lineEditOutput.text())
    errorcheck.errorCheck(self)

    # If an error has occured self.stop will be defined. if None then no error.
    if not self.stop:
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