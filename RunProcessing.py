#!/usr/bin/python
import sys
import subprocess
import argparse
import os
import cPickle as pickle
# Have to load the custom ConfigClass see http://stefaanlippens.net/pickleproblem for reasons
from Main import ConfigClass

class RunProcessing:
    '''
    Class to run the back end processing
    '''

    # Create a constructor
    def __init__(self,args):

        filehandler = open(args.param, 'r')

        param = pickle.load(filehandler)

        cropped_path = os.path.join(param.output_folder,"cropped")

        # Get the directory of the script
        dir = os.path.dirname(os.path.abspath(__file__))

        # Store tracking information in the session tmp folder
        # Create path for session log file
        session_log = os.path.join("/tmp","siah",param.unique_ID,param.full_name+"_session.log")

        # Create session log file
        session = open(session_log, 'w')

        if not os.path.exists(cropped_path):
            os.makedirs(cropped_path)

        session.write("Autocrop started\n");
        subprocess.call(["python", dir+"/autocrop.py","-i",param.input_folder,"-o",
                         cropped_path, "-t", "tif"])
        session.write("Autocrop finished\n");

        if param.SF2 == "yes" :
            session.write("Scaling SF2 started\n");
            pro = subprocess.Popen(["imagej", "-b", dir+"/siah_scale.txt", param.imageJ+":2"])

        if param.SF3 == "yes" :
            session.write("Scaling SF3 started\n");
            subprocess.Popen(["imagej", "-b", dir+"/siah_scale.txt", param.imageJ+":3"])

        if param.SF4 == "yes" :
            session.write("Scaling SF4 started\n");
            subprocess.Popen(["imagej", "-b", dir+"/siah_scale.txt", param.imageJ+":4"])




def main():

    parser = argparse.ArgumentParser(description='Run processing (autocrop and scaling)')
    parser.add_argument('-i', dest='param', help='location of parameters', required=True)

    args = parser.parse_args()

    runProcessing = RunProcessing(args)


if __name__ == '__main__':
    main()