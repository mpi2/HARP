__author__ = 'james'

import sys
import os
import unittest
from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt, QTimer
import harp


class BasicTest(unittest.TestCase):

    def setUp(self):

        # Specify uCT test data paths
        self.lowres_uCT = os.path.join("HARP_testing", "lowres_uCT", "20130430_oxford_lowres_rec_WT_XX")
        self.highres_15_5_uCT = os.path.join("HARP_testing", "highres_uCT", "20140121_RIC8B_15.5_h_wt_rec")
        self.highres_18_5_uCT = os.path.join("MicroCT", "project-IMPC_MCT", "recons",
                                             "20141202_GFOD2_E18.5_15.1E_WT_XY_rec")
        self.default_uCT = self.lowres_uCT

        # Specify OPT test data paths
        self.single_channel_OPT = os.path.join("HARP_testing", "OPT", "single_channel", "20140514_TULP3_16.5a_WT_")
        self.matching_W = os.path.join("HARP_testing", "OPT", "matching", "20141202_MPO_E12.5_15.3g_HOM_W_Rec")
        self.matching_UV = os.path.join("HARP_testing", "OPT", "matching", "20141202_MPO_E12.5_15.3g_HOM_UV_Rec")
        self.mismatching_W = os.path.join("HARP_testing", "OPT", "mismatching", "20141202_COL4A5_E12.5_16.1a_HOM_W_Rec")
        self.mismatching_UV = os.path.join("HARP_testing", "OPT", "mismatching", "20141202_COL4A5_E12.5_HOM_UV_Rec")
        self.default_OPT = self.single_channel_OPT

        # Create HARP instance
        print '### Initialising test ###'
        self.app = QApplication(sys.argv)
        self.ex = harp.MainWindow(self.app)

    def set_example_data(self, example_data):

        # Set example data as input field, as would occur after using the QFileDialog
        self.ex.ui.lineEditInput.setText(example_data)
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
            QTest.qWait(1)

    def close_msg_boxes(self):

        message_boxes = QApplication.topLevelWidgets()
        for msg in message_boxes:
            if msg.inherits("QMessageBox"):
                QTest.keyClick(msg, Qt.Key_Enter)


class DataProcessingTest(BasicTest):

    def setUp(self):

        # Call superclass method
        BasicTest.setUp(self)

    def test_output_exists(self):

        # Process data
        self.process_example_data()

        sep = os.path.sep
        fileparts = self.example_data.split(sep)
        outdir = os.path.join(sep.join(fileparts[:-1]), "processed_recons", fileparts[-1])
        self.assertTrue(os.path.isdir(outdir))

    def test_autocrop(self):

        # Set autocrop to true
        self.ex.ui.radioButtonAuto.setChecked(True)

        # Process the data


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
    suite = unittest.TestLoader().loadTestsFromTestCase(DataProcessingTest)
    unittest.TextTestRunner(verbosity=2).run(suite)