# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created: Mon Feb 03 15:37:30 2014
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(384, 353)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName(_fromUtf8("centralWidget"))
        self.formLayoutWidget = QtGui.QWidget(self.centralWidget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(30, 30, 281, 251))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setMargin(0)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(self.formLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.toolButtonInput = QtGui.QToolButton(self.formLayoutWidget)
        self.toolButtonInput.setObjectName(_fromUtf8("toolButtonInput"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.toolButtonInput)
        self.label_2 = QtGui.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.toolButtonOutput = QtGui.QToolButton(self.formLayoutWidget)
        self.toolButtonOutput.setObjectName(_fromUtf8("toolButtonOutput"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.toolButtonOutput)
        self.label_8 = QtGui.QLabel(self.formLayoutWidget)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_8)
        self.lineEditName = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEditName.setText(_fromUtf8(""))
        self.lineEditName.setObjectName(_fromUtf8("lineEditName"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.lineEditName)
        self.label_3 = QtGui.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_3)
        self.comboBoxCrop = QtGui.QComboBox(self.formLayoutWidget)
        self.comboBoxCrop.setObjectName(_fromUtf8("comboBoxCrop"))
        self.comboBoxCrop.addItem(_fromUtf8(""))
        self.comboBoxCrop.addItem(_fromUtf8(""))
        self.comboBoxCrop.addItem(_fromUtf8(""))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.comboBoxCrop)
        self.label_6 = QtGui.QLabel(self.formLayoutWidget)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_6)
        self.label_4 = QtGui.QLabel(self.formLayoutWidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_4)
        self.comboBoxScale = QtGui.QComboBox(self.formLayoutWidget)
        self.comboBoxScale.setObjectName(_fromUtf8("comboBoxScale"))
        self.comboBoxScale.addItem(_fromUtf8(""))
        self.comboBoxScale.addItem(_fromUtf8(""))
        self.comboBoxScale.addItem(_fromUtf8(""))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.comboBoxScale)
        self.label_5 = QtGui.QLabel(self.formLayoutWidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.label_5)
        self.label_7 = QtGui.QLabel(self.formLayoutWidget)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.LabelRole, self.label_7)
        self.checkBoxMovie = QtGui.QCheckBox(self.formLayoutWidget)
        self.checkBoxMovie.setObjectName(_fromUtf8("checkBoxMovie"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.FieldRole, self.checkBoxMovie)
        self.pushButtonGo = QtGui.QPushButton(self.formLayoutWidget)
        self.pushButtonGo.setObjectName(_fromUtf8("pushButtonGo"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.FieldRole, self.pushButtonGo)
        self.lineEditCropValue = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEditCropValue.setText(_fromUtf8(""))
        self.lineEditCropValue.setObjectName(_fromUtf8("lineEditCropValue"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.lineEditCropValue)
        self.lineEditScaleValue = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEditScaleValue.setText(_fromUtf8(""))
        self.lineEditScaleValue.setObjectName(_fromUtf8("lineEditScaleValue"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.lineEditScaleValue)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 384, 21))
        self.menuBar.setObjectName(_fromUtf8("menuBar"))
        self.menuFile = QtGui.QMenu(self.menuBar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtGui.QToolBar(MainWindow)
        self.mainToolBar.setObjectName(_fromUtf8("mainToolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        MainWindow.setStatusBar(self.statusBar)
        self.actionLoad_settings = QtGui.QAction(MainWindow)
        self.actionLoad_settings.setObjectName(_fromUtf8("actionLoad_settings"))
        self.actionSave_settings = QtGui.QAction(MainWindow)
        self.actionSave_settings.setObjectName(_fromUtf8("actionSave_settings"))
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionLoad_settings)
        self.menuFile.addAction(self.actionSave_settings)
        self.menuBar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.label.setText(_translate("MainWindow", "Input folder", None))
        self.toolButtonInput.setText(_translate("MainWindow", "...", None))
        self.label_2.setText(_translate("MainWindow", "Output folder", None))
        self.toolButtonOutput.setText(_translate("MainWindow", "...", None))
        self.label_8.setText(_translate("MainWindow", "Output Name", None))
        self.label_3.setText(_translate("MainWindow", "Cropping", None))
        self.comboBoxCrop.setItemText(0, _translate("MainWindow", "Automatic", None))
        self.comboBoxCrop.setItemText(1, _translate("MainWindow", "Manual", None))
        self.comboBoxCrop.setItemText(2, _translate("MainWindow", "No crop", None))
        self.label_6.setText(_translate("MainWindow", "Cropping Value (if manual)", None))
        self.label_4.setText(_translate("MainWindow", "Downsize", None))
        self.comboBoxScale.setItemText(0, _translate("MainWindow", "Automatic", None))
        self.comboBoxScale.setItemText(1, _translate("MainWindow", "Manual", None))
        self.comboBoxScale.setItemText(2, _translate("MainWindow", "No Downsize", None))
        self.label_5.setText(_translate("MainWindow", "Downsize Value (if manual)", None))
        self.label_7.setText(_translate("MainWindow", "Create Movie", None))
        self.checkBoxMovie.setText(_translate("MainWindow", "Yes", None))
        self.pushButtonGo.setText(_translate("MainWindow", "Go!", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.actionLoad_settings.setText(_translate("MainWindow", "Load settings", None))
        self.actionSave_settings.setText(_translate("MainWindow", "Save settings", None))

