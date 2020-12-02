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


import os
import shutil
try:
    import pickle as pickle
except ImportError:
    import pickle
from .config import Config


def get_pickle(mainwindow, center):
    """ Creates the python pickle config file for future processing. Also creates a more readable text file of the
    same information.
    """

    # Get input and output folders (As the text is always from the text box it will hopefully keep track of
    #any changes the user might have made
    inputFolder = str(mainwindow.ui.lineEditInput.text())
    outputFolder = str(mainwindow.ui.lineEditOutput.text())
    path_out, folder_name = os.path.split(outputFolder)

    #### Write to config file ####
    config = Config()

    config.center = center

    # Create a folder for the metadata
    mainwindow.meta_path = os.path.join(outputFolder, "Metadata")
    if not os.path.exists(mainwindow.meta_path):
        os.makedirs(mainwindow.meta_path)

    mainwindow.config_path = os.path.join(mainwindow.meta_path, "configobject.txt")
    mainwindow.log_path = os.path.join(mainwindow.meta_path, "config4user.log")

    # Create config file and log file
    log = open(mainwindow.log_path, 'w+')

    #========================================================================================
    # Create config object
    #========================================================================================
    # Get cropping options
    if not mainwindow.ui.checkBoxCropYes.isChecked():
        config.cropbox_path = "Not_applicable"
        config.crop_manual = "Not_applicable"
        config.crop_option = "No_crop"
        config.single_volume = "Not applicable"
    elif mainwindow.ui.radioButtonMan.isChecked():
        config.xcrop = str(mainwindow.ui.lineEditX.text())
        config.ycrop = str(mainwindow.ui.lineEditY.text())
        config.wcrop = str(mainwindow.ui.lineEditW.text())
        config.hcrop = str(mainwindow.ui.lineEditH.text())
        config.crop_option = "Manual"
        config.crop_manual = config.xcrop+" "+config.ycrop+" "+config.wcrop+" "+config.hcrop
        config.cropbox_path = "Not_applicable"
    elif mainwindow.ui.radioButtonAuto.isChecked():
        config.cropbox_path = "Not_applicable"
        config.crop_manual = "Not_applicable"
        config.crop_option = "Automatic"
    elif mainwindow.ui.radioButtonUseOldCrop.isChecked():
        config.crop_manual = "Not_applicable"
        config.crop_option = "Old_crop"
        config.cropbox_path = "Not_applicable"
    elif mainwindow.ui.radioButtonDerived.isChecked() and mainwindow.ui.radioButtonOPT.isChecked:
        config.crop_manual = "Not_applicable"
        config.crop_option = "Derived"

        if mainwindow.derived_output_name:
            d_path = os.path.join(path_out, str(mainwindow.derived_output_name), "Metadata", "cropbox.txt")
        else:
            d_path =os.path.join(path_out, str(mainwindow.ui.lineEditDerivedChnName.text()), "Metadata", "cropbox.txt")
        mainwindow.crop_pickle_path = d_path
        config.cropbox_path = mainwindow.crop_pickle_path

    # Native resolution stack
    # if mainwindow.ui.checkBoxCreateStack.isChecked() and config.crop_option != 'No_crop':
    if mainwindow.ui.checkBoxCreateStack.isChecked():  # Neil: fix to get OPT images to work
        config.single_volume = mainwindow.ui.comboBoxStackType.currentText()
    else:
        config.single_volume = "Not_applicable"

    ##### Get scaling factors ####
    config.SF2 = "yes" if mainwindow.ui.checkBoxSF2.isChecked() else "no"
    config.SF3 = "yes" if mainwindow.ui.checkBoxSF3.isChecked() else "no"
    config.SF4 = "yes" if mainwindow.ui.checkBoxSF4.isChecked() else "no"
    config.SF5 = "yes" if mainwindow.ui.checkBoxSF5.isChecked() else "no"
    config.SF6 = "yes" if mainwindow.ui.checkBoxSF6.isChecked() else "no"

    # Arbitrary rescaling
    # if mainwindow.ui.checkBoxPixel.isChecked():
    #     config.pixel_option = "yes"
    #     config.user_specified_pixel = str(mainwindow.ui.lineEditPixel.text())
    #     config.SF_pixel = float(mainwindow.pixel_size) / float(mainwindow.ui.lineEditPixel.text())
    #     config.SF_pixel = round(config.SF_pixel,4)
    #     config.SFX_pixel = float(mainwindow.ui.lineEditPixel.text())/float(mainwindow.pixel_size)
    #     config.SFX_pixel = round(config.SFX_pixel,4)

    num_rows = mainwindow.ui.tableWidgetPixelScales.rowCount()
    if num_rows > 0:
        config.pixel_option = "yes"
        config.user_specified_pixel = [mainwindow.ui.tableWidgetPixelScales.item(i, 0).text() for i in range(0, num_rows)]
        config.SF_pixel = [round(float(mainwindow.pixel_size) / float(pixel_size), 4) for pixel_size in config.user_specified_pixel]
        config.SFX_pixel = [round(float(pixel_size)/float(mainwindow.pixel_size), 4) for pixel_size in config.user_specified_pixel]
    else:
        config.user_specified_pixel = "Not applicable"
        config.pixel_option = "no"
        config.SF_pixel = "Not applicable"
        config.SFX_pixel = "Not applicable"

    if mainwindow.ui.checkBoxScansReconComp.isChecked():
        config.scans_recon_comp = "yes"
    else :
        config.scans_recon_comp = "No"

    if mainwindow.ui.checkBoxCropComp.isChecked():
        config.crop_comp = "yes"
    else :
        config.crop_comp = "No"

    config.config_path = mainwindow.config_path
    config.tmp_dir = mainwindow.tmp_dir
    config.full_name = mainwindow.full_name
    config.input_folder = inputFolder
    config.output_folder = outputFolder
    config.scan_folder = mainwindow.scan_folder
    config.scan_folder = str(mainwindow.ui.lineEditScan.text())
    config.meta_path = mainwindow.meta_path
    config.recon_log_file = mainwindow.recon_log_path
    config.recon_folder_size = mainwindow.f_size_out_gb
    config.recon_pixel_size = mainwindow.pixel_size

    # If using windows it is important to put \ at the end of folder name
    # Combining scaling and SF into input for imageJ macro
    config.cropped_path = os.path.join(config.output_folder, "cropped")
    config.scale_path = os.path.join(config.output_folder, "scaled_stacks")
    if config.crop_option == "No_crop":
        config.imageJ = config.input_folder+os.sep+'^'+config.scale_path+os.sep+'^'+config.full_name
    else:
        config.imageJ = config.cropped_path+os.sep+'^'+config.scale_path+os.sep+'^'+config.full_name

    #========================================================================================
    # Write the config more readable version
    #========================================================================================
    log.write("full_name    "+config.full_name+"\n")
    log.write("Input_folder    "+config.input_folder+"\n")
    log.write("Output_folder    "+config.output_folder+"\n")
    log.write("Scan_folder    "+config.scan_folder+"\n")
    log.write("Crop_option    "+config.crop_option+"\n")
    log.write("Crop_manual    "+config.crop_manual+"\n")
    log.write("Crop_folder    "+config.cropped_path+"\n")
    log.write("Cropped_volume_type    "+config.single_volume+"\n")
    log.write("Cropbox_location    "+config.cropbox_path+"\n")
    log.write("Downsize_by_factor_2?    "+config.SF2+"\n")
    log.write("Downsize_by_factor_3?    "+config.SF3+"\n")
    log.write("Downsize_by_factor_4?    "+config.SF4+"\n")
    log.write("Downsize_by_factor_5?    "+config.SF5+"\n")
    log.write("Downsize_by_factor_6?    "+config.SF6+"\n")
    log.write("Downsize_by_pixel?    "+config.pixel_option+"\n")

    pixel_size_log = ", ".join(map(str, config.user_specified_pixel)) if type(config.user_specified_pixel) == list else config.user_specified_pixel
    downsize_log = ", ".join(map(str, config.SF_pixel)) if type(config.SF_pixel) == list else config.SF_pixel
    log.write("User_specified_pixel_size?    " + str(pixel_size_log) + "\n")
    log.write("Downsize_value_for_pixel    " + downsize_log + "\n")

    log.write("Compression_of_scans_and_original_recon?    "+config.scans_recon_comp+"\n")
    log.write("Compression_of_cropped_recon?    "+config.crop_comp+"\n")
    log.write("ImageJconfig    "+config.imageJ+"\n")
    log.write("Recon_log_file    "+config.recon_log_file+"\n")
    log.write("Recon_folder_size   "+config.recon_folder_size+"\n")
    log.write("Recon_pixel_size  "+config.recon_pixel_size+"\n")
    mainwindow.configOb = config
    # Pickle the class to a file
    with open(mainwindow.config_path, 'wb') as fh:
        pickle.dump(config, fh)

    # Copy temp files
    if config.crop_option == "Manual":
        if os.path.exists(os.path.join(config.tmp_dir, "max_intensity_z.tif")):
            shutil.copyfile(os.path.join(config.tmp_dir, "max_intensity_z.tif"), os.path.join(config.meta_path,"max_intensity_z.tif"))

    log.close()

