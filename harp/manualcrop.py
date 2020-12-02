#!/usr/bin/env python

"""
Copyright 2015 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

E-mail the developers: sig@har.mrc.ac.uk




Crop.py open an image (probably a max intensity z-projection)
User draws a cropping box. returns the coordinates
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import math
import operator
import sys
import os
try:
    import Image
except ImportError:
    import PIL


class Crop(QtWidgets.QMainWindow):

    def __init__(self, callback, image, parent=None):
        """
        :param callback:
        :param image: str, path to max intensity z projection
        :param parent:
        :return:
        """

        super(Crop, self).__init__(parent)
        self.setWindowTitle("Manual cropping")
        self.callback = callback
        self.widget = MainWidget(self, callback, image)
        self.widget.resize(950, 950)
        self.setCentralWidget(self.widget)
        self.widget.setContentsMargins(0,0,0,0)
        self.widget.show()
        self.cropbox = None

        #Do not allow resizing for now as the rubber band does not move in proportion with the image
        self.widget.setFixedSize(QtCore.QSize(1000, 1000))

        #Menu bar
        self.menubar = self.menuBar()
        self.closeAction = QtWidgets.QAction(self.tr("&close"), self)
        self.closeAction.triggered.connect(self.closeMenuAction)
        fileMenu = self.menubar.addMenu('&file')
        fileMenu.addAction(self.closeAction)

        self.action = QtWidgets.QAction(self.tr("&crop (right click)"), self)
        self.action.triggered.connect(self.cropMenuAction)
        cropMenu = self.menubar.addMenu('&crop')
        cropMenu.addAction(self.action)

    def cropMenuAction(self):
        self.widget.doTheCrop()

    def closeMenuAction(self):
        self.callback(self.cropbox)
        self.close()

    def closeEvent(self, event):
        self.callback(self.cropbox)
        event.accept()


class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent, callback, image_path):
        """
        :param parent:
        :param callback:
        :param image_path: str, path to the zprojection image
        :return:
        """
        self.parent = parent
        super(MainWidget, self).__init__()
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.setSceneRect(0, 0, 950, 950)

        self.callback = callback
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setSceneRect(0, 0, 950, 950)
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.view)
        self.setLayout(layout)


        img = QtGui.QImage(image_path)
        #print '============', img.height()
        self.image = QtGui.QPixmap(img)
        #Try with PIL
        # img = Image.open(image_path)
        # print 'PIL size', img.size
        if not os.path.isfile:
            print('wheres the file')
        else:
            print('found the file {}'.format(image_path))
        #Scale the largest dimension to 950 pixs. Use same scaling for the other dimensions
        self.orig_width = self.image.width()
        if self.image.isNull():
            raise ValueError('the pixmap is null!!!!')
        self.orig_height = self.image.height()
        max_dimen = max([float(self.orig_width), float(self.orig_height)])
        print(float(self.orig_width), float(self.orig_height))
        print("crop: dim", max_dimen)
        self.scaleFact = 950.00 / max_dimen
        #print "jhg ", self.scaleFact
        x = self.orig_width * self.scaleFact
        y = self.orig_height * self.scaleFact

        self.pixmap_item = QtWidgets.QGraphicsPixmapItem(self.image.scaled(x, y), None)
        self.scene.addItem(self.pixmap_item)
        self.pixmap_item.mousePressEvent = self.mousePress
        self.pixmap_item.mouseMoveEvent = self.mouseMove
        self.pixmap_item.mouseReleaseEvent = self.mouseRelease

        self.click_positions = []
        self.x = 2
        self.y = 2
        self.width = 1
        self.height = 1
        self.drawing = True
        self.cornerSet = False

        #Hack. Mouse events give me position of mouse relative to image
        #TODO: set this dynamically
        self.img_dist_top = 15
        self.img_dist_left = 15
        self.pixmap_item.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self.view)
        self.pixmap_item.rubberBand.setGeometry(QtCore.QRect(1, 1, 1, 1))
        self.pixmap_item.rubberBand.updatesEnabled()
        self.pixmap_item.rubberBand.show()


    def doTheCrop(self):
        #Get the coords of the rubber band
        small_box = self.pixmap_item.rubberBand.geometry().getCoords()
        #Convert this to the dimensions of the unscaled image
        large_box = [(1/self.scaleFact)* x for x in small_box]

        #To get the ruuber band to fit on the pixmap I added self.distance from x + y
        # So need to remove that * the scaling factor of the image (yscale = xscale)
        x1 = int(large_box[0] - (self.img_dist_left / self.scaleFact ))
        y1 = int(large_box[1] - (self.img_dist_top / self.scaleFact))
        width = int(large_box[2] - large_box[0])
        height = int(large_box[3] - large_box[1])
        #x2 = self.orig_width - (int(large_box[2] - (self.img_dist_left / self.scaleFact )))
        #y2 = self.orig_height - (int(large_box[3] - (self.img_dist_top / self.scaleFact)))

        ijCropBox = (x1, y1, width, height)
        #print "ImageJ friendly cropbox: makeRectangle({0})".format(str(ijCropBox))
        self.parent.cropbox = (x1, y1, width, height)
        self.parent.close()


    def mouseMove(self, event):
        """
        Called when mouse is moved with button pressed
        """
        #print "frame ", self.parent.geometry().width()
        #print "widget ", self.geometry().width()
        pos = (event.pos().x() + self.img_dist_left, event.pos().y() + self.img_dist_top)
        #print(pos)
        if not self.cornerSet:
            self.x = pos[0]
            self.y = pos[1]
            self.cornerSet = True

            #bodge
            self.height = pos[1] - self.y
            self.width = pos[0] - self.x
            if self.width < 20:
                self.width = 20
            if self.height < 20:
                self.height = 20
            self.pixmap_item.rubberBand.setGeometry(self.x, self.y, self.width, self.height)
            return

        #print "event: ", pos
        #print pos
        if self.drawing:
            #print self.x, ":", self.y
            self.height = pos[1] - self.y
            self.width = pos[0] - self.x
            if self.width < 20:
                self.width = 20
            if self.height < 20:
                self.height = 20
            self.pixmap_item.rubberBand.setGeometry(self.x, self.y, self.width, self.height)
        else:#Band has been drawn, bow resize it
            self.resizeRect(event)


    def mousePress(self, event):
        button = event.button()
        if button == 1:
            #self.pixmap_item.rubberBand.setGeometry(1, 1, 200, 200)
            #self.setCorner(event) #
            pass
        if button == 2:
            self.doTheCrop() #self.drawing = True #maybe clear the box and start over


#     def setCorner(self, event):
#         #if self.drawing:
#         pass


    def resizeRect(self, event):
        '''
        Find the nearest side of the rubber band and drag it
        @param event Qt mouse event
        '''

        #Fet the current mouse pos
        pos = (event.pos().x() + self.img_dist_left, event.pos().y() + self.img_dist_top)

        #Get ccords of current rubber band
        rect = self.pixmap_item.rubberBand.geometry().getCoords()

        topLx = rect[0]
        topLy = rect[1]
        botRx = rect[2]
        botRy = rect[3]

        # Compute distances to all four corners
        dists = {1: math.sqrt((pos[0] - topLx)**2 + (pos[1] - topLy)**2),
                 2: math.sqrt((pos[0] - botRx)**2 + (pos[1] - topLy)**2),
                 3: math.sqrt((pos[0] - botRx)**2 + (pos[1] - botRy)**2),
                 4: math.sqrt((pos[0] - topLx)**2 + (pos[1] - botRy)**2)}

        # Find minimum distance
        corner = min(iter(dists.items()), key=operator.itemgetter(1))[0]
        r = self.pixmap_item.rubberBand.geometry()

        # Modify rectangle according to selected corner and mouse position
        if corner == 1:
            r.setLeft(pos[0])
            r.setTop(pos[1])
            # k = {1: abs(pos[1] - topLy),
            #      4: abs(pos[0] - topLx)}
            # side = min(k.iteritems(), key=operator.itemgetter(1))[0]
        if corner == 2:
            r.setRight(pos[0])
            r.setTop(pos[1])
            # k = {2: abs(pos[0] - botRx),
            #      1: abs(pos[1] - topLy)}
            # side = min(k.iteritems(), key=operator.itemgetter(1))[0]
        if corner == 3:
            r.setRight(pos[0])
            r.setBottom(pos[1])
            # k = {2: abs(pos[0] - botRx),
            #      3: abs(pos[1] - botRy)}
            # side = min(k.iteritems(), key=operator.itemgetter(1))[0]
        if corner == 4:
            r.setLeft(pos[0])
            r.setBottom(pos[1])
            # k = {4: abs(pos[0] - topLx),
            #      3: abs(pos[1] - botRy)}
            # side = min(k.iteritems(), key=operator.itemgetter(1))[0]

        self.pixmap_item.rubberBand.setGeometry(r)

        #Get the nearest side. Sides numbered 1-4 clockwise from top
        # print "corner: ", corner, " side: ", side
        # if side == 1:
        #     r.setTop(pos[1])
        #     self.pixmap_item.rubberBand.setGeometry(r)
        # if side == 2:
        #     r.setRight(pos[0])
        #     self.pixmap_item.rubberBand.setGeometry(r)
        # if side == 3:
        #     r.setBottom(pos[1])
        #     self.pixmap_item.rubberBand.setGeometry(r)
        # if side == 4:
        #     r.setLeft(pos[0])
        #     self.pixmap_item.rubberBand.setGeometry(r)

        print(r)

    def mouseRelease(self, event):
        '''
        On first mouse release, prevent further drawing of rubberbands
        So that box can be resized
        '''
        if self.drawing:
            self.drawing = False


def run_from_cli(callback, image):
    #Need access to app to be able to exit gracefully from cli
    app = QtWidgets.QApplication(sys.argv)
    window = Crop(callback, image)
    window.show()
    sys.exit(app.exec_())

def run(callback, image):
    window = Crop(callback, image)
    window.show()

def dummyCallback(output):
    print(output)

if __name__ == "__main__":
    image = sys.argv[1]
    run_from_cli(dummyCallback, image) #create def for printing box
