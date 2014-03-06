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

        if not os.path.exists(cropped_path):
            os.makedirs(cropped_path)

        subprocess.call(["python", "/mnt/MyShare/autocrop.py","-i",param.input_folder,"-o",
                         cropped_path, "-t", "tif"])

        if param.SF2 == "yes" :
            subprocess.Popen(["java", "-jar", "/usr/share/java/ij.jar", "-batch", "/mnt/MyShare/siah_scale.ijm",
                         param.imageJ+":2"])

        #if param.SF3 == "yes" :
         #   subprocess.Popen(["java", "-jar", "/usr/share/java/ij.jar", "-batch", "/mnt/MyShare/siah_scale.ijm",
          #               param.imageJ+":3"])

        #if param.SF4 == "yes" :
         #   subprocess.Popen(["java", "-jar", "/usr/share/java/ij.jar", "-batch", "/mnt/MyShare/siah_scale.ijm",
          #               param.imageJ+":4"])




def main():

    parser = argparse.ArgumentParser(description='Run processing (autocrop and scaling)')
    parser.add_argument('-i', dest='param', help='location of parameters', required=True)

    args = parser.parse_args()

    runProcessing = RunProcessing(args)


if __name__ == '__main__':
    main()