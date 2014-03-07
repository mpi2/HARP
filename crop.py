#!/usr/bin/env python
import sys

from PyQt4 import QtCore, QtGui
import math
import operator

'''
Crop.py open an image (probably a max intensity z-projection)
User draws a cropping box. returns the coordinates
'''

class MainWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        #QtGui.QWidget.__init__(self, parent)
        super(MainWidget, self).__init__()
        self.scene = QtGui.QGraphicsScene()
        #self.scene.setSceneRect(self.scecone.itemsBoundingRect())
        self.view = QtGui.QGraphicsView(self.scene)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.image = QtGui.QPixmap(sys.argv[1])
        #Scale y to 1000 pixs. Use same scaling for x in case of differring dimensions
        self.orig_width = self.image.width()
        self.orig_height = self.image.height()
        self.y_scale = 950.00 / self.orig_height
        x_width = self.orig_width * self.y_scale

        self.pixmap_item = QtGui.QGraphicsPixmapItem(self.image.scaled(x_width, 950), None, self.scene)

        self.pixmap_item.mousePressEvent = self.mousePress
        self.pixmap_item.mouseMoveEvent = self.mouseMove
        self.pixmap_item.mouseReleaseEvent = self.mouseRelease

        self.click_positions = []
        self.x = None
        self.y = None
        self.width = 40
        self.height = 40
        self.drawing = True
        self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self);
        #setGeometry ( int x, int y, int width, int height )
        self.rubberBand.setGeometry(QtCore.QRect(10, 100, 20, 20))
        self.rubberBand.updatesEnabled()
        self.rubberBand.show()




    def mouseMove(self, event):
        #We are dragging the band

        if self.drawing:
            self.height = event.pos().y() - self.y
            self.width = event.pos().x() - self.x
            self.rubberBand.setGeometry(self.x, self.y, self.width, self.height)
        else:
            self.resizeRect(event)



    def mousePress(self, event):
        button = event.button()
        if button == 1:
            self.setCorner(event)
        if button == 2:
            pass


    def setCorner(self, event):
        self.x = event.pos().x()
        self.y = event.pos().y()


    def resizeRect(self, event):
        '''
        Find the nearest side of the rubber band and drag it
        @param event Qt mouse event
        '''

        #Fet the current mouse pos
        pos = (event.pos().x(), event.pos().y())

        #Get ccords of current rubber band
        rect = self.rubberBand.geometry().getCoords()


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

        #get the nearest side. Sides numbered 1-4 clockwise from top
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


        r = self.rubberBand.geometry()

        if side == 1:
          r.setTop(pos[1])
          self.rubberBand.setGeometry(r)
          #print r.getRect()
        if side == 2:
          r.setRight(pos[0])
          self.rubberBand.setGeometry(r)
        if side == 3:
          r.setBottom(pos[1])
          self.rubberBand.setGeometry(r)
          #print r.getRect()
        if side == 4:
          r.setLeft(pos[0])
          self.rubberBand.setGeometry(r)

        #Get the coords of the original image
        small_box = r.getCoords()
        large_box = [(1/self.y_scale)* x for x in small_box]
        print small_box, large_box
        width = str(int(large_box[2] - large_box[0]))
        height = str(int(large_box[3] - large_box[1]))
        print "ij", "makeRectangle("+str(int(large_box[0])) + "," + str(int(large_box[1])) + "," + width + "," + height + ");"








    def mouseRelease(self, event):
        if self.drawing:
            self.drawing = False


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(1000, 1000)
    app.installEventFilter(widget)
    widget.show()
    sys.exit(app.exec_())