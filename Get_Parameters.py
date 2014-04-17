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
from ConfigClass import ConfigClass


def getParamaters(self):
    '''
    Creates the config file for future processing
    '''
    # Get input and output folders (As the text is always from the text box it will hopefully keep track of
    #any changes the user might have made
    inputFolder = str(self.ui.lineEditInput.text())
    outputFolder = str(self.ui.lineEditOutput.text())

    #### Write to config file ####
    self.configOb = ConfigClass()

    # Create a folder for the metadata
    self.meta_path = os.path.join(outputFolder,"Metadata")
    if not os.path.exists(self.meta_path):
        os.makedirs(self.meta_path)

    # OS path used for compatibility issues between Linux and windows directory spacing
    self.config_path = os.path.join(self.meta_path,"configobject.txt")
    self.log_path = os.path.join(self.meta_path,"config4user.log")

    # Create config file and log file
    config = open(self.config_path, 'w')
    log = open(self.log_path, 'w')

    #######################################
    # Create config object                #
    #######################################
    # Get cropping options
    if self.ui.radioButtonMan.isChecked() :
        self.configOb.xcrop = str(self.ui.lineEditX.text())
        self.configOb.ycrop = str(self.ui.lineEditY.text())
        self.configOb.wcrop = str(self.ui.lineEditW.text())
        self.configOb.hcrop = str(self.ui.lineEditH.text())
        self.configOb.crop_option = "Manual"
        self.configOb.crop_manual = self.configOb.xcrop+" "+self.configOb.ycrop+" "+self.configOb.wcrop+" "+self.configOb.hcrop
    elif self.ui.radioButtonAuto.isChecked() :
        self.configOb.crop_manual = "Not_applicable"
        self.configOb.crop_option = "Automatic"
    elif self.ui.radioButtonNo.isChecked() :
        self.configOb.crop_manual = "Not_applicable"
        self.configOb.crop_option = "No_crop"

    ##### Get Scaling factors ####
    if self.ui.checkBoxSF2.isChecked() :
        self.configOb.SF2 = "yes"
    else :
        self.configOb.SF2 = "no"

    if self.ui.checkBoxSF3.isChecked() :
        self.configOb.SF3 = "yes"
    else :
        self.configOb.SF3 = "no"

    if self.ui.checkBoxSF4.isChecked() :
        self.configOb.SF4 = "yes"
    else :
        self.configOb.SF4 = "no"

    if self.ui.checkBoxSF5.isChecked() :
        self.configOb.SF5 = "yes"
    else :
        self.configOb.SF5 = "no"

    if self.ui.checkBoxSF6.isChecked() :
        self.configOb.SF6 = "yes"
    else :
        self.configOb.SF6 = "no"

    if self.ui.checkBoxPixel.isChecked() :
        self.configOb.pixel_option = "yes"
        self.configOb.user_specified_pixel = str(self.ui.lineEditPixel.text())
        self.configOb.SF_pixel = float(self.pixel_size) / float(self.ui.lineEditPixel.text())
        self.configOb.SF_pixel = round(self.configOb.SF_pixel,4)
        self.configOb.SFX_pixel = float(self.ui.lineEditPixel.text())/float(self.pixel_size)
        self.configOb.SFX_pixel = round(self.configOb.SFX_pixel,4)
    else :
        self.configOb.user_specified_pixel = "Not applicable"
        self.configOb.pixel_option = "no"
        self.configOb.SF_pixel = "Not applicable"
        self.configOb.SFX_pixel = "Not applicable"

    if self.ui.checkBoxScansReconComp.isChecked():
        self.configOb.scans_recon_comp = "yes"
    else :
        self.configOb.scans_recon_comp = "No"

    if self.ui.checkBoxCropComp.isChecked():
        self.configOb.crop_comp = "yes"
    else :
        self.configOb.crop_comp  = "No"

    # ID for session
    self.configOb.unique_ID = str(self.unique_ID)
    self.configOb.config_path = self.config_path
    self.configOb.tmp_dir = self.tmp_dir
    self.configOb.full_name = self.full_name
    self.configOb.input_folder = inputFolder
    self.configOb.output_folder = outputFolder
    self.configOb.scan_folder = self.scan_folder
    self.configOb.meta_path = self.meta_path
    self.configOb.recon_log_file = self.recon_log_path
    self.configOb.recon_folder_size = self.f_size_out_gb
    self.configOb.recon_pixel_size = self.pixel_size

    # If using windows it is important to put \ at the end of folder name
    # Combining scaling and SF into input for imageJ macro
    self.configOb.cropped_path = os.path.join(self.configOb.output_folder,"cropped")
    self.configOb.scale_path = os.path.join(self.configOb.output_folder,"scaled_stacks")
    if self.configOb.crop_option == "No_crop":
        self.configOb.imageJ = self.configOb.input_folder+os.sep+'^'+self.configOb.scale_path+os.sep+'^'+self.configOb.full_name
    else :
        self.configOb.imageJ = self.configOb.cropped_path+os.sep+'^'+self.configOb.scale_path+os.sep+'^'+self.configOb.full_name

    # write the config information into an easily readable log file
    log.write("Session_ID    "+self.configOb.unique_ID+"\n");
    log.write("full_name    "+self.configOb.full_name+"\n");
    log.write("Input_folder    "+self.configOb.input_folder+"\n");
    log.write("Output_folder    "+self.configOb.output_folder+"\n");
    log.write("Scan_folder    "+self.configOb.scan_folder+"\n");
    log.write("Crop_option    "+self.configOb.crop_option+"\n");
    log.write("Crop_manual    "+self.configOb.crop_manual+"\n");
    log.write("Crop_folder    "+self.configOb.cropped_path+"\n");
    log.write("Downsize_by_factor_2?    "+self.configOb.SF2+"\n");
    log.write("Downsize_by_factor_3?    "+self.configOb.SF3+"\n");
    log.write("Downsize_by_factor_4?    "+self.configOb.SF4+"\n");
    log.write("Downsize_by_factor_5?    "+self.configOb.SF5+"\n");
    log.write("Downsize_by_factor_6?    "+self.configOb.SF6+"\n");
    log.write("Downsize_by_pixel?    "+self.configOb.pixel_option+"\n");
    log.write("User_specified_pixel_size?    "+self.configOb.user_specified_pixel+"\n");
    log.write("Downsize_value_for_pixel    "+str(self.configOb.SF_pixel)+"\n");
    log.write("Compression_of_scans_and_original_recon?    "+self.configOb.scans_recon_comp+"\n");
    log.write("Compression_of_cropped_recon?    "+self.configOb.crop_comp+"\n");
    log.write("ImageJconfig    "+self.configOb.imageJ+"\n");
    log.write("Recon_log_file    "+self.configOb.recon_log_file+"\n");
    log.write("Recon_folder_size   "+self.configOb.recon_folder_size+"\n");
    log.write("Recon_pixel_size  "+self.configOb.recon_pixel_size+"\n");

    # Pickle the class to a file
    pickle.dump(self.configOb, config)

    # Copy temp files
    if self.configOb.crop_option == "Manual" :
        if os.path.exists(os.path.join(self.configOb.tmp_dir,"max_intensity_z.tif")):
            shutil.copyfile(os.path.join(self.configOb.tmp_dir,"max_intensity_z.tif"), os.path.join(self.configOb.meta_path,"max_intensity_z.tif"))

    config.close()
    log.close()
