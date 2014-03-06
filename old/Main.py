#!/usr/bin/python
# Import PyQT module
from PyQt4 import QtGui
# Import MainWindow class from QT creator
from mainwindow import *
import sys

# Basically extend the Mainwindow
class mainwindow(QtGui.QMainWindow):
    # Create a constructor
    def __init__(self):
        super(mainwindow, self).__init__()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)

       # self.ui.pushButtonGo.clicked.connect(self.process())
        #self.show()

    #def process(self):
     #   print "TESTT!!!"

def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainwindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()