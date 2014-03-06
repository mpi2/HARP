#!/usr/bin/env python
import sys

from PyQt4 import QtCore, QtGui


class MainWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.scene = QtGui.QGraphicsScene()
        self.view = QtGui.QGraphicsView(self.scene)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        print sys.argv[1]
        self.pixmap_item = QtGui.QGraphicsPixmapItem(QtGui.QPixmap(sys.argv[1]), None, self.scene)
        self.pixmap_item.mousePressEvent = self.pixelSelect
        self.click_positions = []
        self.x = None
        self.y = None

    def pixelSelect(self, event):
        self.click_positions.append(event.pos())

        if len(self.click_positions) == 1:
            self.x = event.pos.x()
        if len(self.click_positions) == 3:
            self.y = event.pos.x()
        pen = QtGui.QPen(QtCore.Qt.red)

        self.scene.addRect(QtCore.QRectF(self.click_positions), pen)
        for point in self.click_positions:
            self.scene.addEllipse(point.x(), point.y(), 2, 2, pen)
        self.click_positions = []


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(640, 480)
    widget.show()
    sys.exit(app.exec_())