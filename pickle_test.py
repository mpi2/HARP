#!/usr/bin/python
import pickle
# Have to load the ConfigClass see http://stefaanlippens.net/pickleproblem for reasons
from Main import ConfigClass

filehandler = open('/home/tom/Desktop/processed recons/20140408_RCAS_17_18.4e_wt_rc/configObject.txt', 'r')
check = pickle.load(filehandler)

print check.input_folder, check.recon_folder_size