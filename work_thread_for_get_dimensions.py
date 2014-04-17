from PyQt4 import QtGui, QtCore
# Import MainWindow class from QT Designer
from MainWindow import Ui_MainWindow
import zproject
import crop
import tempfile
#from RunProcessing import *
import sys
import subprocess
import os, signal
import re
# cPickle is faster than pickle and is pretty much the same
import pickle
import pprint
import logging
import psutil
import datetime
from multiprocessing import freeze_support
from sys import platform as _platform


class WorkThreadGetDimensions(QtCore.QThread):
    def __init__(self,input,tmp_dir):
        QtCore.QThread.__init__(self)
        self.input_folder = input
        self.tmp_dir = tmp_dir

    def __del__(self):
        self.wait()

    def run(self):

        # Get the directory of the script
        if getattr(sys, 'frozen', False):
            self.dir = os.path.dirname(sys.executable)
        elif __file__:
            self.dir = os.path.dirname(__file__)

        # Set up a zproject object
        zp = zproject.Zproject(self.input_folder,self.tmp_dir, self.z_callback)
        # run the object
        zp_result = zp.run()

        # An error has happened. The error message will be shown on the status section
        if zp_result != 0:
            self.emit( QtCore.SIGNAL('update(QString)'), "Z projection failed. Error message: {0}. Give Tom or Neil a Call if it happens again".format(zp_result))
            return
        # let the user know what's happened
        self.emit( QtCore.SIGNAL('update(QString)'), "Z-projection finished" )

    def z_callback(self, msg):
        self.emit( QtCore.SIGNAL('update(QString)'), msg )


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()
