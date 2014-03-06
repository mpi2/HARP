import sys
from PyQt4.QtGui import QApplication, QDialog
from MainWindow import *

app = QApplication(sys.argv)
window = QDialog()
ui = Ui_MainWindow()
ui.setupUi(window)

window.show()
sys.exit(app.exec_())