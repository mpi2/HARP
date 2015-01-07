__author__ = 'james'

import sys
import os
import time
import unittest
from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt, QTimer
import harp


class BasicTest(unittest.TestCase):

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
            #self.example_data = "/home/neil/siah/Example_Data/test_4_harp/20130430_oxford_lowres_rec_WT_XX"
            self.example_data = "/home/james/Desktop/20130430_oxford_lowres_rec_WT_XX"
            self.data_name = self.example_data.split("/")[-1]

    def set_example_data(self):

        # Set example data as input field, as would occur after using the QFileDialog
        self.ex.ui.lineEditInput.setText(self.example_data)
        QTimer.singleShot(1000, self.close_msg_boxes)
        QTimer.singleShot(1000, self.close_msg_boxes)
        self.ex.autofill_pipe()

    def process_example_data(self):

        # Add the job to the list
        self.ex.ui.pushButtonGo.click()

        # Click the start button to run the job
        self.ex.ui.pushButtonStart.click()

        # Wait for process to finish
        while self.ex.p_thread_pool is not None:
            QTest.qWait(0.5)

    def close_msg_boxes(self):

        message_boxes = QApplication.topLevelWidgets()
        for msg in message_boxes:
            if msg.inherits("QMessageBox"):
                QTest.keyClick(msg, Qt.Key_Enter)


class SingleProcessingTest(BasicTest):

    def setUp(self):

        # Call superclass method
        BasicTest.setUp(self)

        # Set up example data
        self.set_example_data()

    def test_output_exists(self):

        # Process data
        self.process_example_data()

        fileparts = self.example_data.split('/')
        outdir = os.path.join('/'.join(fileparts[:-1]), "processed recons", fileparts[-1])
        self.assertTrue(os.path.isdir(outdir))

    def test_scaling(self):

        # Set all scaling factors to checked
        self.ex.ui.checkBoxSF2.setChecked(True)
        self.ex.ui.checkBoxSF3.setChecked(True)
        self.ex.ui.checkBoxSF4.setChecked(True)
        self.ex.ui.checkBoxSF5.setChecked(True)
        self.ex.ui.checkBoxSF6.setChecked(True)
        self.ex.ui.checkBoxPixel.setChecked(True)
        self.ex.ui.lineEditPixel.setText("28")  # 28 micron resolution

        # Process the data
        self.process_example_data()

        # Get output dir and check it exists
        scaled_dir = os.path.join(self.ex.output_folder, 'scaled_stacks')
        self.assertTrue(os.path.isdir(scaled_dir))

        # Check the files actually exist
        scaled_stacks = os.listdir(scaled_dir)
        self.assertEqual(len(scaled_stacks, 6))


class GUIFeaturesTest(BasicTest):

    def setUp(self):

        # Call superclass method
        BasicTest.setUp(self)

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



class MiscellaneousTests(BasicTest):

    def setUp(self):

        # Call superclass method
        BasicTest.setUp(self)

    '''Resize the main window and reset it'''
    def test_resize_and_reset_screen(self):

        print "Testing window resizing..."

        # Get the current window and scrollarea size
        window_size = self.ex.size()
        scroll_size = self.ex.ui.scrollArea.size()

        # Trigger menu click event
        self.ex.ui.actionResize.trigger()
        self.ex.ui.actionReset_screen_size.trigger()

        # Get the new window size after reset
        new_window_size = self.ex.size()
        new_scroll_size = self.ex.ui.scrollArea.size()

        # Are the sizes back as they were?
        self.assertEqual(window_size, new_window_size)
        self.assertEqual(scroll_size, new_scroll_size)

if __name__ == "__main__":
    unittest.main()

