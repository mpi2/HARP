from PyQt4 import QtGui
import os
import errorcheck
import getpickle

#======================================================================
# Functions for adding the recon to the list
#======================================================================
def start(self):
    in_dir = str(self.ui.lineEditInput.text())
    path,folder_name = os.path.split(in_dir)
    # Check if multiple channels will be added to the list at the same time
    # Standard microCT run
    if self.modality == "MicroCT":
        add_to_list_action(self)
    # Individual OPT run
    elif self.ui.checkBoxInd.isChecked():
        add_to_list_action(self)
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

        self.stop_chn_for_loop = False
        print "start channel loop"
        # go through list and get the channel names
        for name in self.chan_full:
            if self.stop_chn_for_loop == True:
                break

            chan_path = os.path.join(path,name)
            # Check if the input director is already set the channel in the loop
            # if the current channel is not the same as the loop then perform autofill before adding to the list
            chan_short = chan_path.replace("\\", "")
            chan_short = chan_short.replace("/", "")
            in_dir_short = in_dir.replace("\\", "")
            in_dir_short = in_dir_short.replace("/", "")

            print in_dir_short
            print chan_short
            if chan_short != in_dir_short:
                print "does not match"
                self.ui.lineEditInput.setText(chan_path)
                self.reset_inputs()
                self.autofill_pipe(suppress=True)

            if len(self.chan_full)>1:
                #need to setup the output folder based on original folder used for output. Only required for
                #multiple channels
                path_out,old_folder_name = os.path.split(str(out_dir_original))
                output_folder = os.path.join(path_out,name)
                self.ui.lineEditOutput.setText(os.path.abspath(output_folder))


            add_to_list_action(self)

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
    # This adds a recon folder to be processed.
    # Get the directory of the script
    dir = os.path.dirname(os.path.abspath(__file__))

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