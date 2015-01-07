#!/usr/bin/python
__author__ = 'james.brown'

from PyQt4 import QtGui, QtCore
from sys import platform as _platform
import zproject


class AutoMask(QtCore.QThread):

    def __init__(self, input_folder, tmp_dir):
        QtCore.QThread.__init__(self)
        self.input_folder = input_folder
        self.tmp_dir = tmp_dir

    def __del__(self):
        self.wait()