# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ErrorMessage.ui'
#
# Created: Tue Feb 25 16:48:09 2014
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

class Ui_DialogErrMessage(object):
    def setupUi(self, DialogErrMessage):
        DialogErrMessage.setObjectName(_fromUtf8("DialogErrMessage"))
        DialogErrMessage.resize(653, 332)
        self.frame = QtGui.QFrame(DialogErrMessage)
        self.frame.setGeometry(QtCore.QRect(50, 50, 561, 271))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.objectNameErrMessage = QtGui.QTextBrowser(self.frame)
        self.objectNameErrMessage.setGeometry(QtCore.QRect(100, 10, 371, 201))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.objectNameErrMessage.setFont(font)
        self.objectNameErrMessage.setObjectName(_fromUtf8("objectNameErrMessage"))

        self.retranslateUi(DialogErrMessage)
        QtCore.QMetaObject.connectSlotsByName(DialogErrMessage)

    def retranslateUi(self, DialogErrMessage):
        DialogErrMessage.setWindowTitle(_translate("DialogErrMessage", "Dialog", None))

