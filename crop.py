#!/usr/bin/env python
import sys

from PyQt4 import QtCore, QtGui

class MainWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.scene = QtGui.QGraphicsScene()
        self.scene.setSceneRect(self.scecone.itemsBoundingRect())
        self.view = QtGui.QGraphicsView(self.scene)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.pixmap_item = QtGui.QGraphicsPixmapItem(QtGui.QPixmap(sys.argv[1]).scaled(1000, 1000), None, self.scene)

        self.pixmap_item.mousePressEvent = self.mousePress
        self.pixmap_item.mouseMoveEvent = self.mouseMove
        self.click_positions = []
        self.x = None
        self.y = None
        self.width = 40
        self.height = 40
        self.mousePresses = 0
        self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self);
        #setGeometry ( int x, int y, int width, int height )
        self.rubberBand.setGeometry(QtCore.QRect(10, 100, 200, 300))
        self.rubberBand.updatesEnabled()
        self.rubberBand.show()

    def mouseMove(self, event):
        print "moved"
        if self.mousePresses == 1:
            #We are dragging the band
            self.height = event.pos().y() - self.y
            self.width = event.pos().x() - self.x
            self.rubberBand.setGeometry(self.x, self.y, self.width, self.height)
    def mousePress(self, event):
        print "clicked"
        print event.pos().x(),", ", event.pos().y()
        self.mousePresses += 1
        if self.mousePresses == 3:
            self.mousePresses = 0
        if self.mousePresses == 0:
            #remove rubber band
            self.rubberBand.hide()
        if self.mousePresses == 1:
            self.x = event.pos().x()
            self.y = event.pos().y()
            self.rubberBand.setGeometry(self.x, self.y, self.width, self.height)
            self.rubberBand.show()



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(1000, 1000)
    app.installEventFilter(widget)
    widget.show()
    sys.exit(app.exec_())