#!/usr/bin/env python
import sys

from PyQt4 import QtCore, QtGui
import math
import operator

'''
Crop.py open an image (probably a max intensity z-projection)
User draws a cropping box. returns the coordinates
'''

class MyMainWindow(QtGui.QMainWindow):

    def __init__(self, callback, image, parent=None):

        super(MyMainWindow, self).__init__(parent)
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
        self.close()



class MainWidget(QtGui.QWidget):
    def __init__(self, parent, callback, image):
        self.parent = parent
        super(MainWidget, self).__init__()
        self.scene = QtGui.QGraphicsScene()
        self.callback = callback
        self.view = QtGui.QGraphicsView(self.scene)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)


        self.image = QtGui.QPixmap(image)
        #Scale y to 1000 pixs. Use same scaling for x in case of differring dimensions
        self.orig_width = self.image.width()
        self.orig_height = self.image.height()
        self.y_scale = 950.00 / self.orig_height
        x_width = self.orig_width * self.y_scale

        #self.dist_from_x_to_window - parent.
        #self.dist_from_y_to_window - None


        self.pixmap_item = QtGui.QGraphicsPixmapItem(self.image.scaled(x_width, 950), None, self.scene)
        self.pixmap_item.mousePressEvent = self.mousePress
        self.pixmap_item.mouseMoveEvent = self.mouseMove
        self.pixmap_item.mouseReleaseEvent = self.mouseRelease

        self.click_positions = []
        self.x = None
        self.y = None
        self.width = 1
        self.height = 1
        self.drawing = True
        self.cropBox = None

        #Hack. Mouse events give me position of mouse relative to image
        #But setiing geometry on rubberband does it relative to mani window
        self.img_dist_top = 73/2
        self.img_dist_left = 105/2
        self.pixmap_item.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self);
        self.pixmap_item.rubberBand.setGeometry(QtCore.QRect(1, 1, 1, 1))
        self.pixmap_item.rubberBand.updatesEnabled()
        self.pixmap_item.rubberBand.show()


    def doTheCrop(self):
        small_box = self.pixmap_item.rubberBand.geometry().getCoords()
        large_box = [(1/self.y_scale)* x for x in small_box]

        width = str(int(large_box[2] - large_box[0]) )
        height = str(int(large_box[3] - large_box[1]))
        cropBox =  "makeRectangle("+str(int(large_box[0] -100)) + "," + str(int(large_box[1] -70)) + "," + width + "," + height + ");"
        self.callback(cropBox)


    def mouseMove(self, event):
        '''
        Called when mouse is moved with button pressed
        '''
        #print "frame ", self.parent.geometry().width()
        #print "widget ", self.geometry().width()
        pos = (event.pos().x(), event.pos().y())
        print pos
        if self.drawing:
            print self.x, ":", self.y
            self.height = event.pos().y() - self.y
            self.width = event.pos().x() - self.x
            self.pixmap_item.rubberBand.setGeometry(self.x, self.y, self.width, self.height)
        else:#Band has been drawn, bow resize it
            self.resizeRect(event)


    def mousePress(self, event):
        print ""
        button = event.button()
        if button == 1:
            #self.pixmap_item.rubberBand.setGeometry(1, 1, 200, 200)
            self.setCorner(event) #
        if button == 2:
            self.doTheCrop() #self.drawing = True #maybe clear the box and start over


    def setCorner(self, event):
        self.x = event.pos().x()
        self.y = event.pos().y()


    def resizeRect(self, event):
        '''
        Find the nearest side of the rubber band and drag it
        @param event Qt mouse event
        '''

        #Fet the current mouse pos
        pos = (event.pos().x() - 50, event.pos().y() -35)
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
    app = QtGui.QApplication(sys.argv)
    window = MyMainWindow(callback, image)
    window.show()
    sys.exit(app.exec_())

def run(callback, image):
    window = MyMainWindow(callback, image)
    window.show()


if __name__ == "__main__":
    run_from_cli() #create def for printing box