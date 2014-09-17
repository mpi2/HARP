from PyQt4 import QtCore, QtGui
import sys
import os
import re
import datetime

def opt_uCT_check(self,suppress=False):
    '''
    Checks whether or not folder name contains reference to either opt or microCT
    '''
    print "doing opt_uct check"
    file_in = str(self.ui.lineEditInput.text())
    print file_in
    p_opt = re.compile("OPT",re.IGNORECASE)
    p_uCT = re.compile("MicroCT",re.IGNORECASE)
    if p_opt.search(file_in):
        self.modality = "OPT"
        self.ui.radioButtonOPT.setChecked(True)
        self.ui.lineEditChannel.setEnabled(True)
        self.ui.labelChannel.setEnabled(True)
        self.ui.tableWidgetOPT.setEnabled(True)
        self.ui.radioButtonDerived.setEnabled(True)
        if self.ui.radioButtonDerived.isChecked():
            self.ui.lineEditDerivedChnName.setEnabled(True)
        self.ui.checkBoxInd.setEnabled(True)
    elif p_uCT.search(file_in):
        self.modality = "MicroCT"
        self.ui.radioButtonuCT.setChecked(True)
        self.ui.lineEditChannel.setEnabled(False)
        self.ui.labelChannel.setEnabled(False)
        self.ui.tableWidgetOPT.setEnabled(False)
        self.ui.radioButtonDerived.setEnabled(False)
        self.ui.lineEditDerivedChnName.setEnabled(False)
        self.ui.checkBoxInd.setEnabled(False)
    else:
        if not suppress:
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: Cannot automatically determine if uCT or OPT please check')

def get_crop_box(self,alt_name):
    """

    """
    if not self.modality == "OPT":
        return
    out_dir = str(self.ui.lineEditOutput.text())
    path_out,folder_name = os.path.split(out_dir)

    # go through all the folders indentified to see if one has a cropbox pickle file. If it does save the
    cropbox_path = os.path.join(path_out, alt_name, "Metadata","cropbox.txt")
    if os.path.exists(cropbox_path):
        return True

def check_if_on_list(self,alt_name):
    # A while loop is used to go through the processing table see if the alternative channel is on the list already
    count = 0
    while True:
        # This gets the status text
        name_on_list = self.ui.tableWidget.item(count, 0)
        if not name_on_list:
            # if not defined it means there are no recons left to process
            return False
        if re.search(alt_name, name_on_list.text()):
            # this row has the OPT channel ID meaning a cropbox will be ready when this is ran
            return True
        count += 1

def get_channels(self):
    """
    Check if OPT is selected
    look up recon parent folder and search for other available
    Then checks if are there similar named folders in the input directory
    Go through the folders identified and put in table
    :return:
    """
    # reset the table
    self.ui.tableWidgetOPT.clearContents()

    if not self.modality == "OPT":
        return

    # Are there matching folders in the parent directory of the input directory
    in_dir = str(self.ui.lineEditInput.text())
    # Get the folder name and path name
    path,folder_name = os.path.split(in_dir)
    # get a list of the names in the folder name
    l_init = folder_name.split("_")
    # get the name without the channel (only works if name is in the correct format)
    base_name = '_'.join(l_init[0:6])

    # set the name up for the current channel. Blank if name not set up properly
    try:
        chn_init = str(l_init[6])
    except IndexError:
        chn_init = "NA"

    chan_full = []
    chan_short = []

    # add current to channel list
    chan_full.append(folder_name)
    chan_short.append(chn_init)


    if not os.path.exists(path):
        return

    # for loop to go through the parent input directory
    for line in os.listdir(path) :
        line =str(line)
        # if the line matches the base_name but is not the same as the input file. The folder is probably another
        # channel
        m = re.search(base_name,line)
        if m and (not line == folder_name):
            # Check if it is a folder with recons etc for the other channels
            if error_check_chn(os.path.join(path,line)) != 1:
                chan_full.append(line)
                chan_short.append(m.group(0))

    count = 0
    self.chan_full = chan_full

    # Save the the opt channels to the opt channel table
    for alt_name in chan_full:
        # Set the data for an individual row
        # Set up the channel type
        l = alt_name.split("_")
        try:
            chn = l[6]
        except IndexError:
            chn = "NA"
        # Make the current channel highlighted
        chn_item = QtGui.QTableWidgetItem()
        self.ui.tableWidgetOPT.setItem(count, 0, chn_item)
        chn_item = self.ui.tableWidgetOPT.item(count, 0)
        chn_item.setText(chn)
        if alt_name == folder_name:#
            chn_item.setBackground(QtGui.QColor(220, 0, 0))

        # Set up the name of the recon
        item = QtGui.QTableWidgetItem()
        self.ui.tableWidgetOPT.setItem(count, 1, item)
        item = self.ui.tableWidgetOPT.item(count, 1)
        item.setText(alt_name)

        # Set up whether or not there is a crop box available
        if get_crop_box(self,alt_name):
            crop_status = "Yes"
        elif check_if_on_list(self,alt_name):
            crop_status = "On list"
        else:
            crop_status = "No"

        item = QtGui.QTableWidgetItem()
        self.ui.tableWidgetOPT.setItem(count, 2, item)
        item = self.ui.tableWidgetOPT.item(count, 2)
        # Status is pending untill processing has started
        item.setText(crop_status)

        # count_in is the counter for the row to add data
        count += 1

        # Reszie the columns to fit the data
        self.ui.tableWidgetOPT.resizeColumnsToContents()

        self.ui.tableWidgetOPT.setSortingEnabled(True)
        self.ui.tableWidgetOPT.sortByColumn(0)

def error_check_chn(inputFolder):
    # Check if input folder exists
    if not os.path.exists(inputFolder):
        return 1

    # Check if a directory
    if not os.path.isdir(inputFolder):
        return 1

    #Check if folder is empty
    if os.listdir(inputFolder) == []:
            return 1

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
            break

    if not file_check:
        return 1


def auto_get_derived(self):
    """
    While loop through OPT list. See if one of them is either processed or on list. if they are set the derived crop box
    settings
    :return:
    """
    n = self.ui.tableWidgetOPT.rowCount()
    out_dir = str(self.ui.lineEditOutput.text())
    path_out,folder_name = os.path.split(out_dir)

    for i in range(n):
        print i
        processed = self.ui.tableWidgetOPT.item(i, 2)
        name = self.ui.tableWidgetOPT.item(i,1)
        if processed:
            print processed.text()
            if processed.text() == "On list":
                    if name.text() == folder_name:
                        continue
            if processed.text() == "Yes" or processed.text() == "On list":
                print "use dirived crop box"
                self.crop_box_use = True
                self.ui.radioButtonDerived.setEnabled(True)
                self.ui.radioButtonDerived.setChecked(True)
                self.ui.lineEditDerivedChnName.setEnabled(True)

                # show name for user

                self.ui.lineEditDerivedChnName.setText(name.text())
                break


def get_recon_log(self):
    '''
    Gets the recon log from the original recon folder and gets the pixel size information
    '''
    input = str(self.ui.lineEditInput.text())

    # Get the folder name and path name
    path,folder_name = os.path.split(input)

    try:
        # I think some times the log file is .txt and sometimes .log, a check for both types and other
        # old formats of log files is checked as follows:
        if os.path.exists(os.path.join(path,folder_name,folder_name+".txt")):
            recon_log_path = os.path.join(path,folder_name,folder_name+".txt")
        elif os.path.exists(os.path.join(path,folder_name,folder_name+"_rec.txt")):
            recon_log_path = os.path.join(path,folder_name,folder_name+"_rec.txt")
        elif os.path.exists(os.path.join(path,folder_name,folder_name+".log")):
            recon_log_path = os.path.join(path,folder_name,folder_name+".log")
        elif os.path.exists(os.path.join(path,folder_name,folder_name+"_rec.log")):
            recon_log_path = os.path.join(path,folder_name,folder_name+"_rec.log")
        else :
            raise Exception('No log file')
        # To make sure the path is in the correct format (prob not necessary..)
        self.recon_log_path = os.path.abspath(recon_log_path)

        # Open the log file as read only
        recon_log_file = open(self.recon_log_path, 'r')

        self.pixel_size = get_pixel(self.modality, recon_log_file)

        # Display the number on the lcd display
        self.ui.lcdNumberPixel.display(self.pixel_size)

        # Set recon log text
        self.ui.lineEditCTRecon.setText(str(self.recon_log_path))

    except IOError as e:
        # Python standard exception identifies recon file not found
        print "exception re"
        self.ui.lineEditCTRecon.setText("Not found")
        self.pixel_size = ""
        self.ui.lcdNumberPixel.display(self.pixel_size)
    except Exception as inst:
        # Custom exception identifies recon file not found
        self.pixel_size = ""
        self.ui.lcdNumberPixel.display(self.pixel_size)
        self.ui.lineEditCTRecon.setText("Not found")
    except:
        self.pixel_size = ""
        self.ui.lcdNumberPixel.display(self.pixel_size)
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error getting recon log file',sys.exc_info()[0])
        self.ui.lineEditCTRecon.setText("Not found")

def get_pixel(modality,recon_log_file):
    # create a regex to pixel size
    # We want the pixel size where it starts with Pixel. This is the pixel size with the most amount of decimal
    # places for uCT. For OPT this is the "image pixel size"
    if modality == "OPT":
        prog = re.compile("^Image Pixel Size \(um\)=(\w+.\w+)")
    else:
        prog = re.compile("^Pixel Size \(um\)\=(\w+.\w+)")

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

def get_name(self,name,suppress=False):
    '''
    Gets the id from the folder name. Then fills out the text boxes on the main window with the relevant information
    '''
    # Get the folder name and path
    path,folder_name = os.path.split(name)

    # first split the folder into list of identifiers
    name_list = folder_name.split("_")
    # the full name will at first just be the folder name
    self.ui.lineEditName.setText(folder_name)
    self.full_name = folder_name

    # Need to have exception to catch if the name is not in correct format.
    # If the name is not in the correct format it should flag to the user that this needs to be sorted
    # Added additional regex which the user has to check

    error_list = []

    # Checking Date
    try:
        self.ui.lineEditDate.setText(name_list[0])
        datetime.datetime.strptime(name_list[0], '%Y%m%d')
    except IndexError:
        error_list.append("- Date not available")
    except ValueError:
        error_list.append("- Incorrect date format should be = [YYYYMMDD]")

    # Checking gene name/group
    try:
        self.ui.lineEditGroup.setText(name_list[1])
    except IndexError:
        error_list.append("- Gene name info not available")

    # Checking age/stage
    try:
        self.ui.lineEditAge.setText(name_list[2])
    except IndexError:
        error_list.append("- Stage/age info not available")

    # Litter
    try:
        self.ui.lineEditLitter.setText(name_list[3])
    except IndexError:
        error_list.append("- Litter info not available")

    # Zygosity
    try:
        self.ui.lineEditZygosity.setText(name_list[4])
        prog = re.compile("HOM|HET|WT|ND|NA",re.IGNORECASE)
        if not prog.search(name_list[4]):
            error_list.append("- Zygosity should be either HOM,HET,WT,ND or NA")

    except IndexError:
        error_list.append("- Zygosity info not available")

    # Sex
    try:
        self.ui.lineEditSex.setText(name_list[5])

        prog = re.compile("XX|XY|ND",re.IGNORECASE)
        if not prog.search(name_list[5]):
            error_list.append("- Sex should be either XX,XY or ND")

    except IndexError:
        error_list.append("- Sex info not available")

    # Channel (OPT only)
    try:
        if self.modality == "OPT":
            self.ui.lineEditChannel.setText(name_list[6])
            if name_list[6].lower() == "rec" :
                error_list.append("- IMPORTANT: OPT needs to include channel information. e.g. UV")


    except IndexError as e:
        error_list.append("- IMPORTANT: OPT needs to include channel information. e.g. UV")

    if error_list:
        error_string = os.linesep.join(error_list)
        if not suppress:
            QtGui.QMessageBox.warning(self, 'Message', 'Warning (Naming not canonical):'+os.linesep+error_string)



def auto_file_out(self):
    '''
    Auto fill to make output folder name. Just replaces 'recons' to 'processed recons' if possible
    '''
    # Not sure whether to include try and except catch here...
    try :
        input = str(self.ui.lineEditInput.text())
        path,folder_name = os.path.split(input)
        pattern = re.compile("recons", re.IGNORECASE)
        if re.search(pattern, input):
            output_path = pattern.sub("processed recons", path)
            output_full = os.path.join(output_path,self.full_name)
            self.ui.lineEditOutput.setText(os.path.abspath(output_full))
        else:
            output_full = os.path.join(path,"processed recons",folder_name)

            self.ui.lineEditOutput.setText(os.path.abspath(output_full))
    except:
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected getting and auto file out',sys.exc_info()[0])


def auto_get_scan(self):
    '''
    Auto find scan folder. Just replaces 'recons' to 'processed recons' if possible
    '''
    input = str(self.ui.lineEditInput.text())
    pattern = re.compile("recons", re.IGNORECASE)
    if re.search(pattern, input):
        self.scan_folder = pattern.sub("scan", input)
        if os.path.exists(self.scan_folder):
            self.ui.lineEditScan.setText(self.scan_folder)
        else :
            self.ui.lineEditScan.setText("Not found")
            self.scan_folder = ""
    else :
        self.ui.lineEditScan.setText("Not found")
        self.scan_folder = ""

def auto_get_SPR(self):
    '''
    Finds any SPR files. This might be a bit redundant as the SPR files are not essential and are copied over with any other
    file regardless
    '''
    input = str(self.ui.lineEditInput.text())
    # Get the SPR file. Sometimes fiels are saved with upper or lower case file extensions
    # The following is bit of a stupid way of dealing with this problem but I think it works....
    SPR_file_bmp = os.path.join(input,self.full_name+"_spr.bmp")
    SPR_file_BMP = os.path.join(input,self.full_name+"_spr.BMP")
    SPR_file_tif = os.path.join(input,self.full_name+"_spr.tif")
    SPR_file_TIF = os.path.join(input,self.full_name+"_spr.TIF")
    SPR_file_jpg = os.path.join(input,self.full_name+"_spr.jpg")
    SPR_file_JPG = os.path.join(input,self.full_name+"_spr.JPG")

    if os.path.isfile(SPR_file_bmp):
        self.ui.lineEditCTSPR.setText(SPR_file_bmp)
    elif os.path.isfile(SPR_file_BMP):
        self.ui.lineEditCTSPR.setText(SPR_file_BMP)
    elif os.path.isfile(SPR_file_tif):
        self.ui.lineEditCTSPR.setText(SPR_file_tif)
    elif os.path.isfile(SPR_file_TIF):
        self.ui.lineEditCTSPR.setText(SPR_file_TIF)
    elif os.path.isfile(SPR_file_jpg):
        self.ui.lineEditCTSPR.setText(SPR_file_jpg)
    elif os.path.isfile(SPR_file_JPG):
        self.ui.lineEditCTSPR.setText(SPR_file_JPG)
    else:
        self.ui.lineEditCTSPR.setText("Not found")

def folder_size_approx(self):
    '''
    Gets the approx folder size of the original recon folder and updates the main window with
    this information. Calculating the folder size by going through each file takes a while on janus. This
    function just checks the first recon file and then multiples this by the number of recon files.

    Creates self.f_size_out_gb: The file size in gb
    '''

    # Get the input folder information
    input = str(self.ui.lineEditInput.text())

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
        f_size_out =  (approx_size/(1024*1024*1024.0))

        # Save file size as an object to be used later
        self.f_size_out_gb = "%0.4f" % (f_size_out)

        #Clean up the formatting of gb mb
        size_cleanup(self,f_size_out,approx_size)
    except Exception as e:
        # Should pontially add some other error catching
        message = QtGui.QMessageBox.warning(self, "Message", "Unexpected error in folder size calc: {0}".format(e))



def size_cleanup(self,f_size_out,approx_size):
    '''
    Used in folderSizeApprox() to format the output. In a separate method Potentially to be used again for more accurate folder size calc.
    '''
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