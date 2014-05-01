from PyQt4 import QtCore, QtGui
import sys
import subprocess
import os, signal
import re
import pickle
import pprint
import time
import shutil
import logging
import logging.handlers
import tarfile
import autocrop
import cPickle as pickle
from config import ConfigClass

def get_recon_log(self):
    '''
    Gets the recon log from the original recon folder and gets the pixel size information
    '''
    input = str(self.ui.lineEditInput.text())

    # Get the folder name and path name
    path,folder_name = os.path.split(input)

    try:
        # I think some times the log file is .txt and sometimes .log, a check for both types follows:
        recon_log_path = os.path.join(path,folder_name,folder_name+".txt")
        if os.path.exists(os.path.join(path,folder_name,folder_name+".txt")):
            recon_log_path = os.path.join(path,folder_name,folder_name+".txt")
        elif os.path.exists(os.path.join(path,folder_name,folder_name+".log")):
            recon_log_path = os.path.join(path,folder_name,folder_name+".log")
        else :
            raise Exception('No log file')

        # To make sure the path is in the correct format (probab not necessary..)
        self.recon_log_path = os.path.abspath(recon_log_path)

        # Open the log file as read only
        recon_log_file = open(self.recon_log_path, 'r')

        # create a regex to pixel size
        # We want the pixel size where it starts with Pixel. This is the pixel size with the most amount of decimal places
        prog = re.compile("^Pixel Size \(um\)\=(\w+.\w+)")

        # for loop to go through the recon log file
        for line in recon_log_file:
            # "chomp" the line endings off
            line = line.rstrip()
            # if the line matches the regex print the (\w+.\w+) part of regex
            if prog.match(line) :
                # Grab the pixel size with with .group(1)
                self.pixel_size = prog.match(line).group(1)
                break

        # Display the number on the lcd display
        self.ui.lcdNumberPixel.display(self.pixel_size)

        # Set recon log text
        self.ui.lineEditCTRecon.setText(str(self.recon_log_path))

    except IOError as e:
        # Python standard exception identifies recon file not found
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
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error getting recon log file',sys.exc_info()[0])
        self.ui.lineEditCTRecon.setText("Not found")



def get_name(self):
    '''
    Gets the id from the folder name. Then fills out the text boxes on the main window with the relevant information
    '''
    # Get input folder
    input = str(self.ui.lineEditInput.text())

    # Get the folder name and path
    path,folder_name = os.path.split(input)

    # first split the folder into list of identifiers
    name_list = folder_name.split("_")
    # the full name will at first just be the folder name
    self.ui.lineEditName.setText(folder_name)
    self.full_name = folder_name

    # Need to have exception to catch if the name is not in correct format.
    # If the name is not in the correct format it should flag to the user that this needs to be sorted
    # Could put additional regexes to check format is correct but could be a little bit annoying for the user
    try:
        self.ui.lineEditDate.setText(name_list[0])
        self.ui.lineEditGroup.setText(name_list[1])
        self.ui.lineEditAge.setText(name_list[2])
        self.ui.lineEditLitter.setText(name_list[3])
        self.ui.lineEditZygosity.setText(name_list[4])
        self.ui.lineEditSex.setText(name_list[5])
    except IndexError as e:
        pass
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Name ID is not in the correct format\n')
        self.full_name = folder_name
    except:
        message = QtGui.QMessageBox.warning(self, 'Message', 'Auto-populate not possible. Unexpected error:',sys.exc_info()[0])



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
            self.ui.lineEditOutput.setText(output_full)
    except:
        message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected getting and auto file out',sys.exc_info()[0])


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

        filename = input+"/"+filename
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