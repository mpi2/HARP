from PyQt4 import QtCore, QtGui
import os

from imgprocessing.zproject import ZProjectThread
import manualcrop


#======================================================================
#  Functions for get Dimensions (z projection)
#======================================================================
def get_dimensions(self):
    """ Allow a user to choose crop dimensions by choosing a region based on the z-projection of the image.

    This z projection is calculated on a seperate thread. Process is as follows:

    1. **start_z_thread** starts a thread using the module zproject
    2. z projection is performed in background giving updates to the "status" section of the GUI
    3. The **zproject_slot** catches any signals
    4. "Z-projection finished" is called and **run_crop** loads a new window.
    5. The user can then select the crop dimensions
    6. When the crop dimensions are selected the crop window is closed and the cropbox parameter is saved on the GUI

    Two important modules used: manualcrop.py and zproject.py

    * zproject performs the zprojection and displays the image.
    * manualcrop.py then gets the dimensions to perform the crop

    IMPORTANT NOTE: The cropping is not actually done here. This is just to get the dimensions.

    :ivar boolean self.stop: If True HARP stops pre-processing steps. Set to None before z projection performed

    .. seealso::
        :func:`start_z_thread()`,
    """
    # get the input folder
    input_folder = str(self.ui.lineEditInput.text())

    # Check input folder is defined
    if not input_folder:
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input directory not defined')
        return
    # Check input folder exists
    if not os.path.exists(input_folder):
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not exist')
        return
    #Check if folder is empty
    elif os.listdir(input_folder) == []:
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty')
        return

    # Set to None so z_projection doesn't stop unless cancelled
    self.stop = None
    # Let the user know what is going on
    self.ui.textEditStatusMessages.setText("Z-projection in process, please wait")
    #Run the zprojection
    self.start_z_thread()


def start_z_thread(self):
    """ Starts a thread to perform z projection processing in the background.

    .. seealso::
        :func:`zproject.ZProjectThread()`
    """
    # Get input folder
    input_folder = str(self.ui.lineEditInput.text())

    # Set thread off
    z_thread_pool = []
    z_thread_pool.append(ZProjectThread(input_folder, self.tmp_dir))
    self.connect(self.z_thread_pool[len(z_thread_pool) - 1], QtCore.SIGNAL("update(QString)"),
                    self.zproject_slot)
    z_thread_pool[len(z_thread_pool) - 1].start()


def zproject_slot(self, message):
    """ Listens to the z projection child process.

    Displays all messages to the status section of the parameters tab. Once zprojection is finished opens window
    to display zproject for user to get crop dimensions, using *run_crop*

    .. seealso::
        :func:`run_crop()`
    """
    # Update HARP GUI to status of the zprojection
    self.ui.textEditStatusMessages.setText(message)

    # Check if z projection finished
    if message == "Z-projection finished":
        # Get the crop dimensions and save the file
        self.get_manual_bbox(os.path.join(self.tmp_dir, "max_intensity_z.tif"))

def run_crop(self, img_path):
    """ Creates the a window to display the z projection used to get crop dimensions

    Creates an object from the crop module. Uses a call back method to get the crop dimensions after the user
    has selected them.

    .. seealso::
        :func:`crop.Crop()`
        :func:`crop_call_back()`
    """
    cropper = manualcrop.Crop(self.crop_call_back, img_path, self)
    cropper.show()


def crop_call_back(self, box):
    """ Method to get crop dimension (crop box) from z projecion image.

    Saves the crop dimensions to the line edit boxes on the GUI.

    :param list box: Crop dimensions (crop box) the user selected
    """
    self.ui.lineEditX.setText(str(box[0]))
    self.ui.lineEditY.setText(str(box[1]))
    self.ui.lineEditW.setText(str(box[2]))
    self.ui.lineEditH.setText(str(box[3]))
    self.ui.textEditStatusMessages.setText("Dimensions selected")
    self.ui.pushButtonGetDimensions.setText("Get Dimensions")
