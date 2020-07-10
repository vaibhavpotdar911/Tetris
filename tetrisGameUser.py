#!/usr/bin/python3

import sys, random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor

from tetrisModel import GAME_BOARD, Shape
from tetrisAI import TETRIS_AI

TETRIS_AI = None

class Tetris(QMainWindow):
    def __init__(self):
        super().__init__()
        self.isStarted = False
        self.isPaused = False
        self.nextMove = None
        self.lastShape = Shape.shapeNone

        self.initUI()

    def initUI(self):
        self.gridSize = 22
        self.speed = 400

        self.timer = QBasicTimer()
        self.setFocusPolicy(Qt.StrongFocus)

        hLayout = QHBoxLayout()
        self.tboard = Board(self, self.gridSize)
        hLayout.addWidget(self.tboard)

        self.sidePanel = SidePanel(self, self.gridSize)
        hLayout.addWidget(self.sidePanel)

        self.statusbar = self.statusBar()
        self.tboard.msg2Statusbar[str].connect(self.statusbar.showMessage)

        self.start()

        self.center()
        self.setWindowTitle('Tetris Game')
        self.show()

        self.setFixedSize(self.tboard.width() + self.sidePanel.width(),
                          self.sidePanel.height() + self.statusbar.height())

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def start(self):
        if self.isPaused:
            return

        self.isStarted = True
        self.tboard.score = 0
        GAME_BOARD.clear()

        self.tboard.msg2Statusbar.emit(str(self.tboard.score))

        GAME_BOARD.createNewPiece()
        self.timer.start(self.speed, self)

    def pause(self):
        if not self.isStarted:
            return

        self.isPaused = not self.isPaused

        if self.isPaused:
            self.timer.stop()
            self.tboard.msg2Statusbar.emit("Paused")
        else:
            self.timer.start(self.speed, self)

        self.updateWindow()

    def updateWindow(self):
        self.tboard.updateData()
        self.sidePanel.updateData()
        self.update()

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if TETRIS_AI and not self.nextMove:
                self.nextMove = TETRIS_AI.nextMove()
            if self.nextMove:
                k = 0
                while GAME_BOARD.currentDirection != self.nextMove[0] and k < 4:
                    GAME_BOARD.rotateRight()
                    k += 1
                k = 0
                while GAME_BOARD.currentX != self.nextMove[1] and k < 5:
                    if GAME_BOARD.currentX > self.nextMove[1]:
                        GAME_BOARD.moveLeft()
                    elif GAME_BOARD.currentX < self.nextMove[1]:
                        GAME_BOARD.moveRight()
                    k += 1
            lines = GAME_BOARD.moveDown()
            self.tboard.score += lines
            if self.lastShape != GAME_BOARD.currentShape:
                self.nextMove = None
                self.lastShape = GAME_BOARD.currentShape
            self.updateWindow()
        else:
            super(Tetris, self).timerEvent(event)

    def keyPressEvent(self, event):
        if not self.isStarted or GAME_BOARD.currentShape == Shape.shapeNone:
            super(Tetris, self).keyPressEvent(event)
            return

        key = event.key()
        
        if key == Qt.Key_P:
            self.pause()
            return
            
        if self.isPaused:
            return
        elif key == Qt.Key_Left:
            GAME_BOARD.moveLeft()
        elif key == Qt.Key_Right:
            GAME_BOARD.moveRight()
        elif key == Qt.Key_Up:
            GAME_BOARD.rotateLeft()
        elif key == Qt.Key_Down:
            self.tboard.score += GAME_BOARD.dropDown()
        else:
            super(Tetris, self).keyPressEvent(event)

        self.updateWindow()


def drawSquare(painter, x, y, val, s):
    colorTable = [0x000000, 0xEE6666, 0x66EE66, 0x6666EE,
                  0xEEEE66, 0xEE66EE, 0x66EEEE, 0xDAAA00]

    if val == 0:
        return

    color = QColor(colorTable[val])
    painter.fillRect(x + 1, y + 1, s - 2, s - 2, color)

    painter.setPen(color.lighter())
    painter.drawLine(x, y + s - 1, x, y)
    painter.drawLine(x, y, x + s - 1, y)

    painter.setPen(color.darker())
    painter.drawLine(x + 1, y + s - 1, x + s - 1, y + s - 1)
    painter.drawLine(x + s - 1, y + s - 1, x + s - 1, y + 1)


class SidePanel(QFrame):
    def __init__(self, parent, gridSize):
        super().__init__(parent)
        self.setFixedSize(gridSize * 5, gridSize * GAME_BOARD.height)
        self.move(gridSize * GAME_BOARD.width, 0)
        self.gridSize = gridSize

    def updateData(self):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        minX, maxX, minY, maxY = GAME_BOARD.nextShape.getBoundingOffsets(0)

        dy = 3 * self.gridSize
        dx = (self.width() - (maxX - minX) * self.gridSize) / 2

        val = GAME_BOARD.nextShape.shape
        for x, y in GAME_BOARD.nextShape.getCoords(0, 0, -minY):
            drawSquare(painter, x * self.gridSize + dx, y * self.gridSize + dy, val, self.gridSize)


class Board(QFrame):
    msg2Statusbar = pyqtSignal(str)
    speed = 10

    def __init__(self, parent, gridSize):
        super().__init__(parent)
        self.setFixedSize(gridSize * GAME_BOARD.width, gridSize * GAME_BOARD.height)
        self.gridSize = gridSize
        self.initBoard()

    def initBoard(self):
        self.score = 0
        GAME_BOARD.clear()

    def paintEvent(self, event):
        painter = QPainter(self)

        for x in range(GAME_BOARD.width):
            for y in range(GAME_BOARD.height):
                val = GAME_BOARD.getValue(x, y)
                drawSquare(painter, x * self.gridSize, y * self.gridSize, val, self.gridSize)

        for x, y in GAME_BOARD.getCurrentShapeCoord():
            val = GAME_BOARD.currentShape.shape
            drawSquare(painter, x * self.gridSize, y * self.gridSize, val, self.gridSize)

        painter.setPen(QColor(0x777777))
        painter.drawLine(self.width()-1, 0, self.width()-1, self.height())
        painter.setPen(QColor(0xEEEEEE))
        painter.drawLine(self.width(), 0, self.width(), self.height())

    def updateData(self):
        self.msg2Statusbar.emit(str(self.score))
        self.update()


if __name__ == '__main__':
    app = QApplication([])
    tetris = Tetris()
    sys.exit(app.exec_())
