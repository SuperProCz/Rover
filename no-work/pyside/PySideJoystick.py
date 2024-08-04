from PySide6.QtGui import QPainter
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt
from PySide6.QtWidgets import QWidget, QApplication, QStyleFactory, QMainWindow, QGridLayout
from PySide6 import QtCore
import sys
from enum import Enum
import math

class Direction(Enum):
    Left = 0
    Right = 1
    Up = 2
    Down = 3

def remap(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

class Joystick(QWidget):
    def __init__(self, parent=None):
        super(Joystick, self).__init__(parent)
        self.setMinimumSize(200, 200)
        self.movingOffset = QPointF(0, 0)
        self.grabCenter = False
        self.__maxDistance = 50

    def paintEvent(self, event):
        painter = QPainter(self)
        bounds = QRectF(-self.__maxDistance, -self.__maxDistance, self.__maxDistance * 2, self.__maxDistance * 2).translated(self._center())
        painter.drawEllipse(bounds)
        painter.setBrush(Qt.black)
        painter.drawEllipse(self._centerEllipse())

    def _centerEllipse(self):
        if self.grabCenter:
            return QRectF(-20, -20, 40, 40).translated(self.movingOffset)
        return QRectF(-20, -20, 40, 40).translated(self._center())

    def _center(self):
        return QPointF(self.width()/2, self.height()/2)


    def _boundJoystick(self, point):
        limitLine = QLineF(self._center(), point)
        if (limitLine.length() > self.__maxDistance):
            limitLine.setLength(self.__maxDistance)
        return limitLine.p2()

    def joystickDirection(self):
        if not self.grabCenter:
            return 0
        normVector = QLineF(self._center(), self.movingOffset)
        currentDistance = normVector.length()
        angle = normVector.angle()

        #print(angle)
        distance = min(currentDistance / self.__maxDistance, 1.0)
        # if 45 <= angle < 135:
        #     return (Direction.Up, distance)
        # elif 135 <= angle < 225:
        #     return (Direction.Left, distance)
        # elif 225 <= angle < 315:
        #     return (Direction.Down, distance)
        # return (Direction.Right, distance)
        return (angle, distance)

    def joystickValue(self):
        angle, distance = self.joystickDirection()
        # Converting polar coordinates to cartesian
        x = distance * math.cos(math.radians(angle))
        y = distance * math.sin(math.radians(angle))

        remappedX = remap(x, -1, 1, -1000, 1000)
        remappedY = remap(y, -1, 1, -1000, 1000)
        return (remappedX,remappedY)
        #convertedX = remap(x, )
    def mousePressEvent(self, ev):
        self.grabCenter = self._centerEllipse().contains(ev.pos())
        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, event):
        self.grabCenter = False
        self.movingOffset = QPointF(0, 0)
        self.update()

    def mouseMoveEvent(self, event):
        try:
            if self.grabCenter:
                #print("Moving")
                self.movingOffset = self._boundJoystick(event.pos())
                self.update()
            steer, speed = self.joystickValue()
            print(f"Steer: {steer}, Speed: {speed}")
        except:
            pass

if __name__ == '__main__':
    # Create main application window
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Cleanlooks"))
    mw = QMainWindow()
    mw.setWindowTitle('Joystick example')

    # Create and set widget layout
    # Main widget container
    cw = QWidget()
    ml = QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    # Create joystick 
    joystick = Joystick()

    # ml.addLayout(joystick.get_joystick_layout(),0,0)
    ml.addWidget(joystick,0,0)

    mw.show()

    ## Start Qt event loop unless running in interactive mode or using pyside.
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QApplication.instance().exec()