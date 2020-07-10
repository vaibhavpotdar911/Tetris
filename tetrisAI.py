#!/usr/bin/python3

from tetrisModel import GAME_BOARD, Shape
import math
from datetime import datetime
import numpy as np

class TetrisAI(object):

    def nextMove(self):
        t1 = datetime.now()
        if GAME_BOARD.currentShape == Shape.shapeNone:
            return None

        currentDirection = GAME_BOARD.currentDirection
        currentY = GAME_BOARD.currentY
        _, _, minY, _ = GAME_BOARD.nextShape.getBoundingOffsets(0)
        nextY = -minY

        method = None
        if GAME_BOARD.currentShape.shape in (Shape.shapeI, Shape.shapeZ, Shape.shapeS):
            d0Range = (0, 1)
        elif GAME_BOARD.currentShape.shape == Shape.shapeO:
            d0Range = (0,)
        else:
            d0Range = (0, 1, 2, 3)

        if GAME_BOARD.nextShape.shape in (Shape.shapeI, Shape.shapeZ, Shape.shapeS):
            d1Range = (0, 1)
        elif GAME_BOARD.nextShape.shape == Shape.shapeO:
            d1Range = (0,)
        else:
            d1Range = (0, 1, 2, 3)

        for d0 in d0Range:
            minX, maxX, _, _ = GAME_BOARD.currentShape.getBoundingOffsets(d0)
            for x0 in range(-minX, GAME_BOARD.width - maxX):
                board = self.calcStep1Board(d0, x0)
                for d1 in d1Range:
                    minX, maxX, _, _ = GAME_BOARD.nextShape.getBoundingOffsets(d1)
                    dropDist = self.calcNextDropDist(board, d1, range(-minX, GAME_BOARD.width - maxX))
                    for x1 in range(-minX, GAME_BOARD.width - maxX):
                        score = self.calculateScore(np.copy(board), d1, x1, dropDist)
                        if not method or method[2] < score:
                            method = (d0, x0, score)
        print("===", datetime.now() - t1)
        return method

    def calcNextDropDist(self, data, d0, xRange):
        res = {}
        for x0 in xRange:
            if x0 not in res:
                res[x0] = GAME_BOARD.height - 1
            for x, y in GAME_BOARD.nextShape.getCoords(d0, x0, 0):
                yy = 0
                while yy + y < GAME_BOARD.height and (yy + y < 0 or data[(y + yy), x] == Shape.shapeNone):
                    yy += 1
                yy -= 1
                if yy < res[x0]:
                    res[x0] = yy
        return res

    def calcStep1Board(self, d0, x0):
        board = np.array(GAME_BOARD.getData()).reshape((GAME_BOARD.height, GAME_BOARD.width))
        self.dropDown(board, GAME_BOARD.currentShape, d0, x0)
        return board

    def dropDown(self, data, shape, direction, x0):
        dy = GAME_BOARD.height - 1
        for x, y in shape.getCoords(direction, x0, 0):
            yy = 0
            while yy + y < GAME_BOARD.height and (yy + y < 0 or data[(y + yy), x] == Shape.shapeNone):
                yy += 1
            yy -= 1
            if yy < dy:
                dy = yy
        self.dropDownByDist(data, shape, direction, x0, dy)

    def dropDownByDist(self, data, shape, direction, x0, dist):
        for x, y in shape.getCoords(direction, x0, 0):
            data[y + dist, x] = shape.shape

    def calculateScore(self, step1Board, d1, x1, dropDist):
        t1 = datetime.now()
        width = GAME_BOARD.width
        height = GAME_BOARD.height

        self.dropDownByDist(step1Board, GAME_BOARD.nextShape, d1, x1, dropDist[x1])

        fullLines, nearFullLines = 0, 0
        roofY = [0] * width
        holeCandidates = [0] * width
        holeConfirm = [0] * width
        vHoles, vBlocks = 0, 0
        for y in range(height - 1, -1, -1):
            hasHole = False
            hasBlock = False
            for x in range(width):
                if step1Board[y, x] == Shape.shapeNone:
                    hasHole = True
                    holeCandidates[x] += 1
                else:
                    hasBlock = True
                    roofY[x] = height - y
                    if holeCandidates[x] > 0:
                        holeConfirm[x] += holeCandidates[x]
                        holeCandidates[x] = 0
                    if holeConfirm[x] > 0:
                        vBlocks += 1
            if not hasBlock:
                break
            if not hasHole and hasBlock:
                fullLines += 1
        vHoles = sum([x ** .7 for x in holeConfirm])
        maxHeight = max(roofY) - fullLines

        roofDy = [roofY[i] - roofY[i+1] for i in range(len(roofY) - 1)]

        if len(roofY) <= 0:
            stdY = 0
        else:
            stdY = math.sqrt(sum([y ** 2 for y in roofY]) / len(roofY) - (sum(roofY) / len(roofY)) ** 2)
        if len(roofDy) <= 0:
            stdDY = 0
        else:
            stdDY = math.sqrt(sum([y ** 2 for y in roofDy]) / len(roofDy) - (sum(roofDy) / len(roofDy)) ** 2)

        absDy = sum([abs(x) for x in roofDy])
        maxDy = max(roofY) - min(roofY)

        score = fullLines * 1.8 - vHoles * 1.0 - vBlocks * 0.5 - maxHeight ** 1.5 * 0.02 \
            - stdY * 0.0 - stdDY * 0.01 - absDy * 0.2 - maxDy * 0.3
        return score

TETRIS_AI = TetrisAI()