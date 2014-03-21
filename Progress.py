# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Progress.ui'
#
# Created: Fri Mar 21 09:29:39 2014
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
        Progress.resize(842, 245)
        self.pushButtonAddMore = QtGui.QPushButton(Progress)
        self.pushButtonAddMore.setGeometry(QtCore.QRect(30, 10, 761, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButtonAddMore.setFont(font)
        self.pushButtonAddMore.setObjectName(_fromUtf8("pushButtonAddMore"))
        self.gridLayoutWidget = QtGui.QWidget(Progress)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(40, 90, 751, 80))
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.progressBar_1 = QtGui.QProgressBar(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.progressBar_1.setFont(font)
        self.progressBar_1.setProperty("value", 0)
        self.progressBar_1.setFormat(_fromUtf8(""))
        self.progressBar_1.setObjectName(_fromUtf8("progressBar_1"))
        self.gridLayout.addWidget(self.progressBar_1, 0, 1, 1, 1)
        self.label_1 = QtGui.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_1.setFont(font)
        self.label_1.setObjectName(_fromUtf8("label_1"))
        self.gridLayout.addWidget(self.label_1, 0, 0, 1, 1)
        self.pushButtonCancel_1 = QtGui.QPushButton(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButtonCancel_1.setFont(font)
        self.pushButtonCancel_1.setObjectName(_fromUtf8("pushButtonCancel_1"))
        self.gridLayout.addWidget(self.pushButtonCancel_1, 0, 2, 1, 1)
        self.label1_tracking = QtGui.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Sans Serif"))
        font.setPointSize(12)
        self.label1_tracking.setFont(font)
        self.label1_tracking.setAlignment(QtCore.Qt.AlignCenter)
        self.label1_tracking.setObjectName(_fromUtf8("label1_tracking"))
        self.gridLayout.addWidget(self.label1_tracking, 1, 1, 1, 1)

        self.retranslateUi(Progress)
        QtCore.QMetaObject.connectSlotsByName(Progress)

    def retranslateUi(self, Progress):
        Progress.setWindowTitle(_translate("Progress", "Track progress", None))
        self.pushButtonAddMore.setText(_translate("Progress", "Add another recon to process", None))
        self.label_1.setText(_translate("Progress", "...", None))
        self.pushButtonCancel_1.setText(_translate("Progress", "Cancel", None))
        self.label1_tracking.setText(_translate("Progress", "...", None))

