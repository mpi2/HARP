__author__ = 'james'

import sys
import time
import unittest
from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt, QTimer
import harp



class HARPTestCase(unittest.TestCase):

    def setUp(self):

        # Create HARP instance
        print '### Initialising test ###'
        self.app = QApplication(sys.argv)
        self.ex = harp.MainWindow(self.app)

        # Specify test data paths
        if sys.platform == "win32" or sys.platform == "win64":
            self.example_data = "\\\\janus\\groups\\siah\\Example_Data\\test_4_harp\\20130430_oxford_lowres_rec_WT_XX"
            self.data_name = self.example_data.split("\\")[-1]
        else:
            self.example_data = "/home/neil/siah/Example_Data/test_4_harp/20130430_oxford_lowres_rec_WT_XX"
            self.data_name = self.example_data.split("/")[-1]

        self.ex.update1.connect(self.wait_for_job)




    def temp(self):

        print "Testing single run of example data..."
        self.set_example_data()

        # Add it to processing list and run
        self.ex.ui.pushButtonGo.click()
        #self.assertTrue(self.ex.ui.tableWidget.rowCount() > 0)

        # Click the start button
        self.ex.ui.pushButtonStart.click()
    '''Test autofill'''


    def test_autofill(self):

        print "Testing autofill..."

        # Load the example data - this should autofill
        self.set_example_data()

        # Split name by underscore
        name_parts = self.data_name.split('_')

        # Check that the fields have been set appropriately
        self.assertEqual(self.ex.ui.lineEditDate.text(), name_parts[0])
        self.assertEqual(self.ex.ui.lineEditGroup.text(), name_parts[1])
        self.assertEqual(self.ex.ui.lineEditAge.text(), name_parts[2])
        self.assertEqual(self.ex.ui.lineEditLitter.text(), name_parts[3])
        self.assertEqual(self.ex.ui.lineEditZygosity.text(), name_parts[4])
        self.assertEqual(self.ex.ui.lineEditSex.text(), name_parts[5])
        self.assertEqual(self.ex.ui.lineEditName.text(), self.data_name)

    def wait_for_job(self, msg):
        print msg

    def test_run_single_job(self):

        print "Testing single run of example data..."

        # self.set_example_data()
        self.temp()
        # Add it to processing list and run
        self.ex.ui.pushButtonGo.click()
        self.assertTrue(self.ex.ui.tableWidget.rowCount() > 0)

        # Click the start button
        self.ex.ui.pushButtonStart.click()


        #self.ex.p_thread_pool[0].update1.connect(self.wait_for_job)


    # '''Resize the main window and reset it'''
    # def test_resize_and_reset_screen(self):
    #
    #     print "Testing window resizing..."
    #
    #     # Get the current window and scrollarea size
    #     window_size = self.ex.size()
    #     scroll_size = self.ex.ui.scrollArea.size()
    #
    #     # Trigger menu click event
    #     self.ex.ui.actionResize.trigger()
    #     self.ex.ui.actionReset_screen_size.trigger()
    #
    #     # Get the new window size after reset
    #     new_window_size = self.ex.size()
    #     new_scroll_size = self.ex.ui.scrollArea.size()
    #
    #     # Are the sizes back as they were?
    #     self.assertEqual(window_size, new_window_size)
    #     self.assertEqual(scroll_size, new_scroll_size)



    def set_example_data(self):

        # Set example data as input field, as would occur after using the QFileDialog
        self.ex.ui.lineEditInput.setText(self.example_data)

        QTimer.singleShot(500, self.close_msg_boxes)
        QTimer.singleShot(500, self.close_msg_boxes)
        self.ex.autofill_pipe()

    def close_msg_boxes(self):

        message_boxes = QApplication.topLevelWidgets()
        for msg in message_boxes:
            if msg.inherits("QMessageBox"):
                QTest.keyClick(msg, Qt.Key_Enter)

if __name__ == "__main__":
    unittest.main()

