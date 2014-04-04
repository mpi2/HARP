# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Progress.ui'
#
# Created: Fri Apr  4 16:00:22 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Progress(object):
    def setupUi(self, Progress):
        Progress.setObjectName(_fromUtf8("Progress"))
        Progress.resize(842, 192)
        self.gridLayout_2 = QtGui.QGridLayout(Progress)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.pushButtonAddMore = QtGui.QPushButton(Progress)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButtonAddMore.setFont(font)
        self.pushButtonAddMore.setObjectName(_fromUtf8("pushButtonAddMore"))
        self.gridLayout_2.addWidget(self.pushButtonAddMore, 0, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.progressBar_1 = QtGui.QProgressBar(Progress)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.progressBar_1.setFont(font)
        self.progressBar_1.setProperty("value", 0)
        self.progressBar_1.setFormat(_fromUtf8(""))
        self.progressBar_1.setObjectName(_fromUtf8("progressBar_1"))
        self.gridLayout.addWidget(self.progressBar_1, 0, 1, 1, 1)
        self.label_1 = QtGui.QLabel(Progress)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_1.setFont(font)
        self.label_1.setObjectName(_fromUtf8("label_1"))
        self.gridLayout.addWidget(self.label_1, 0, 0, 1, 1)
        self.pushButtonCancel_1 = QtGui.QPushButton(Progress)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButtonCancel_1.setFont(font)
        self.pushButtonCancel_1.setObjectName(_fromUtf8("pushButtonCancel_1"))
        self.gridLayout.addWidget(self.pushButtonCancel_1, 0, 2, 1, 1)
        self.label1_tracking = QtGui.QLabel(Progress)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Sans Serif"))
        font.setPointSize(12)
        self.label1_tracking.setFont(font)
        self.label1_tracking.setAlignment(QtCore.Qt.AlignCenter)
        self.label1_tracking.setObjectName(_fromUtf8("label1_tracking"))
        self.gridLayout.addWidget(self.label1_tracking, 1, 1, 1, 1)
        self.pushButtonQuit = QtGui.QPushButton(Progress)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButtonQuit.setFont(font)
        self.pushButtonQuit.setObjectName(_fromUtf8("pushButtonQuit"))
        self.gridLayout.addWidget(self.pushButtonQuit, 1, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Progress)
        QtCore.QMetaObject.connectSlotsByName(Progress)

    def retranslateUi(self, Progress):
        Progress.setWindowTitle(_translate("Progress", "Track progress", None))
        self.pushButtonAddMore.setText(_translate("Progress", "Add another recon to process", None))
        self.label_1.setText(_translate("Progress", "...", None))
        self.pushButtonCancel_1.setText(_translate("Progress", "Cancel", None))
        self.label1_tracking.setText(_translate("Progress", "...", None))
        self.pushButtonQuit.setText(_translate("Progress", "Quit", None))

