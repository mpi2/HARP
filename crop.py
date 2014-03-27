#!/usr/bin/env python
import sys
import logging
from PyQt4 import QtCore, QtGui
import math
import operator
import sys

'''
Crop.py open an image (probably a max intensity z-projection)
User draws a cropping box. returns the coordinates
'''

class Crop(QtGui.QMainWindow):

    def __init__(self, callback, image, parent=None):
	'''
	@param: image, str, image file
	'''
        super(Crop, self).__init__(parent)
        self.setWindowTitle("Manual cropping")
        self.widget = MainWidget(self, callback, image)
        self.widget.resize(950, 950)
        self.setCentralWidget(self.widget)
        self.widget.show()

        #Do not allow resizing for now as the rubber band does not move in proportion with the image
        self.setFixedSize(QtCore.QSize(1050, 1050))

        #Menu bar
        self.menubar = self.menuBar()
        self.closeAction = QtGui.QAction(self.tr("&close"), self)
        self.closeAction.triggered.connect(self.closeMenuAction)
        fileMenu = self.menubar.addMenu('&file')
        fileMenu.addAction(self.closeAction)


        self.action = QtGui.QAction(self.tr("&crop (right click)"), self)
        self.action.triggered.connect(self.cropMenuAction)
        cropMenu = self.menubar.addMenu('&crop')
        cropMenu.addAction(self.action)




    def cropMenuAction(self):
        self.widget.doTheCrop()

    def closeMenuAction(self):
    #sys.exit(app.exec_())
    #self.widget.close()
        self.close()




class MainWidget(QtGui.QWidget):
    def __init__(self, parent, callback, image):
        self.parent = parent
        super(MainWidget, self).__init__()
        self.scene = QtGui.QGraphicsScene()
        self.scene.setSceneRect(0, 0, 950, 950)
        self.callback = callback
        self.view = QtGui.QGraphicsView(self.scene)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)


        self.image = QtGui.QPixmap(image)
        #Scale the largest dimension to 950 pixs. Use same scaling for the other dimensions
        self.orig_width = self.image.width()
        self.orig_height = self.image.height()
        max_dimen = max([float(self.orig_width), float(self.orig_height)])
        print float(self.orig_width), float(self.orig_height)
        print "crop: dim", max_dimen
        self.scaleFact = 950.00 / max_dimen
        #print "jhg ", self.scaleFact
        x = self.orig_width * self.scaleFact
        y = self.orig_height * self.scaleFact

        self.pixmap_item = QtGui.QGraphicsPixmapItem(self.image.scaled(x, y), None, self.scene)
        self.pixmap_item.mousePressEvent = self.mousePress
        self.pixmap_item.mouseMoveEvent = self.mouseMove
        self.pixmap_item.mouseReleaseEvent = self.mouseRelease

        self.click_positions = []
        self.x = 2
        self.y = 2
        self.width = 1
        self.height = 1
        self.drawing = True
        self.cropBox = None
        self.cornerSet = False

        #Hack. Mouse events give me position of mouse relative to image
        #TODO: set this dynamically
        self.img_dist_top = 35 #
        self.img_dist_left = 50
        self.pixmap_item.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self);
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

        ijCropBox = (x1, y1, width, height )
        print "ImageJ friendly cropbox: makeRectangle({0})".format(str(ijCropBox))
        logging.info("ImageJ friendly cropbox: makeRectangle({0})".format(str(ijCropBox)))
        cropBox = (x1, y1, width, height)
        self.callback(cropBox)
        print self.cropBox
        self.parent.close()


    def mouseMove(self, event):
        '''
        Called when mouse is moved with button pressed
        '''
        #print "frame ", self.parent.geometry().width()
        #print "widget ", self.geometry().width()
        pos = (event.pos().x() + self.img_dist_left, event.pos().y() + self.img_dist_top)
        if not self.cornerSet:
            self.x = pos[0]
            self.y = pos[1]
            self.cornerSet = True
            #print "corner: ",self.x, " ", self.y
            return

        #print "event: ", pos
        #print pos
        if self.drawing:
            #print self.x, ":", self.y
            self.height = pos[1] - self.y
            self.width = pos[0] - self.x
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
        #print pos
        #Get ccords of current rubber band
        rect = self.pixmap_item.rubberBand.geometry().getCoords()

        topLx = rect[0]
        topLy = rect[1]
        botRx= rect[2]
        botRy = rect[3]

        #find closest corder to mouse with Pythagoras
        dists = {1:math.sqrt((pos[0] - topLx)**2  + ( pos[1] - topLy)**2 ),
                 2:math.sqrt((pos[0] - botRx)**2  + ( pos[1] - topLy)**2 ),
                 3:math.sqrt((pos[0] - botRx)**2  + ( pos[1] - botRy)**2 ),
                 4:math.sqrt((pos[0] - topLx)**2  + ( pos[1] - botRy)**2 )}

        corner = min(dists.iteritems(), key=operator.itemgetter(1))[0]

        #get the corner. Corner numbered 1-4 clockwise from top-left
        side = 1
        if corner == 1:
            k = {1: abs(pos[1] - topLy),
               4: abs(pos[0] - topLx)}
            side = min(k.iteritems(), key=operator.itemgetter(1))[0]

        if corner == 2:
            k = {2: abs(pos[0] - botRx),
               1: abs(pos[1] - topLy)}
            side = min(k.iteritems(), key=operator.itemgetter(1))[0]

        if corner == 3:
            k = {2: abs(pos[0] - botRx),
               3: abs(pos[1] - botRy)}
            side = min(k.iteritems(), key=operator.itemgetter(1))[0]

        if corner == 4:
            k = {4: abs(pos[0] - topLx),
               3: abs(pos[1] - botRy)}
            side = min(k.iteritems(), key=operator.itemgetter(1))[0]

        r = self.pixmap_item.rubberBand.geometry()

        #Get the nearest side. Sides numbered 1-4 clockwise from top
        #print "corner:" , corner, " side:", side
        if side == 1:
            r.setTop(pos[1])
            self.pixmap_item.rubberBand.setGeometry(r)
            #print r.getRect()
        if side == 2:
            r.setRight(pos[0])
            self.pixmap_item.rubberBand.setGeometry(r)
        if side == 3:
            r.setBottom(pos[1])
            self.pixmap_item.rubberBand.setGeometry(r)
            #print r.getRect()
        if side == 4:
            r.setLeft(pos[0])
            self.pixmap_item.rubberBand.setGeometry(r)





    def mouseRelease(self, event):
        '''
        On first mouse release, prevent further drawing of rubberbands
        So that box can be resized
        '''
        if self.drawing:
            self.drawing = False




def run_from_cli(callback, image):
    #Need access to app to be able to exit gracefully from cli
    app = QtGui.QApplication(sys.argv)
    window = Crop(callback, image)
    window.show()
    sys.exit(app.exec_())

def run(callback, image):
    window = Crop(callback, image)
    window.show()

def dummyCallback(output):
    print output

if __name__ == "__main__":
    image = sys.argv[1]
    run_from_cli(dummyCallback, image) #create def for printing box
