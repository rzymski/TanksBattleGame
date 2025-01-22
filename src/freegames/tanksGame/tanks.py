from turtle import *
from freegames import floor, vector
from enum import Enum
import configparser
import os
from pygame import mixer
import heapq 


def loadFileAsArray(filename, errorMessage="There was a problem loading file content"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.readlines()
    except FileNotFoundError:
        print(f"{errorMessage} File {filename} not found")
        return [errorMessage]


def loadSettingsAndMapFromFile(filePath):
    if not os.path.exists(filePath):
        raise ValueError(f"The file '{filePath}' does not exist.")
    config = configparser.ConfigParser()
    config.read(filePath)
    requiredSections = ['map', 'settings', 'positions']
    if not all(section in config for section in requiredSections):
        raise ValueError(f"The configuration file must have {requiredSections} sections.")
    tilesUnprocessed = config['map']['tiles']
    if not tilesUnprocessed:
        raise ValueError("No tiles found in the 'map' section of the configuration file.")
    try:
        tilesProcessed = tilesUnprocessed.replace(" ", "1")
        tileRows = [list(map(int, row.split(','))) for row in tilesProcessed.strip().splitlines()]
        flatTiles = [tile for row in tileRows for tile in row]
    except ValueError as e:
        raise ValueError(f"Error processing tile data: {e}")
    try:
        rowsCount = int(config['settings'].get('rows', "20"))
        columnsCount = int(config['settings'].get('columns', "20"))
        tileSize = int(config['settings'].get('tileSize', "20"))
        startGameX = int(config['settings'].get('startGameX', "500"))
        startGameY = int(config['settings'].get('startGameY', "100"))
        firstTankIndex = int(config['positions'].get('firstTankSpawnPosition', '187'))
        secondTankIndex = int(config['positions'].get('secondTankSpawnPosition', '64'))
        enemies = list(map(int, config['enemies']['enemyTanksPositions'].split(','))) if 'enemies' in config and 'enemyTanksPositions' in config['enemies'] else []
    except ValueError as e:
        raise ValueError(f"Error reading settings: {e}")
    if rowsCount * columnsCount != len(flatTiles):
        raise ValueError(f"Invalid map size compare to settings. Map have {len(flatTiles)} tiles, but settings have {rowsCount}x{columnsCount}={rowsCount * columnsCount}.")
    if firstTankIndex > len(flatTiles):
        raise ValueError(f"Invalid first tank spawn position. Tank index {firstTankIndex} out of range. Max possible {len(flatTiles) - 1} index.")
    if secondTankIndex > len(flatTiles):
        raise ValueError(f"Invalid second tank spawn position. Tank index {secondTankIndex} out of range. Max possible {len(flatTiles) - 1} index.")
    return flatTiles, rowsCount, columnsCount, tileSize, startGameX, startGameY, firstTankIndex, secondTankIndex, enemies


def conditionalExecution(condition, function, *args, **kwargs):
    conditionResult = condition() if callable(condition) else condition
    if conditionResult:
        return function(*args, **kwargs)


class Tile(Enum):
    NO_TILE = 0
    ROAD = 1
    RIVER = 2
    FOREST = 3
    INDESTRUCTIBLE_BLOCK = 4
    DESTRUCTIBLE_BLOCK = 5
    DESTROYED_DESTRUCTIBLE_BLOCK = 6
    MINE = 7


tiles = [
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 7, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 7, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 1, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 7, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 7, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 4,
    4, 1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 4,
    4, 1, 3, 3, 3, 3, 3, 3, 1, 1, 5, 5, 5, 5, 5, 5, 5, 5, 1, 4,
    4, 1, 3, 3, 3, 3, 3, 3, 1, 1, 5, 1, 1, 1, 1, 1, 1, 5, 1, 4,
    4, 1, 3, 3, 3, 3, 3, 3, 1, 1, 5, 1, 1, 1, 1, 1, 1, 5, 1, 4,
    4, 1, 3, 3, 3, 3, 3, 3, 1, 1, 5, 1, 1, 1, 1, 1, 1, 5, 1, 4,
    4, 1, 3, 3, 3, 3, 3, 3, 1, 1, 5, 1, 1, 1, 1, 1, 1, 5, 1, 4,
    4, 1, 3, 3, 3, 3, 3, 3, 1, 1, 5, 5, 5, 5, 5, 5, 5, 5, 1, 4,
    4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
]
tileColors = {
    Tile.ROAD.value: "light goldenrod",
    Tile.RIVER.value: "navy",
    Tile.FOREST.value: "forest green",
    Tile.INDESTRUCTIBLE_BLOCK.value: "snow2",
    Tile.DESTRUCTIBLE_BLOCK.value: "dark orange",
    Tile.DESTROYED_DESTRUCTIBLE_BLOCK.value: "tan1",
    Tile.MINE.value: "light goldenrod",
}

class Node:
    def __init__(self, position, parent=None, g=0, h=0):
        self.position = position  
        self.parent = parent
        self.g = g  
        self.h = h  
        self.f = g + h 

    def __lt__(self, other):
        return self.f < other.f


class Game:
    def __init__(self, initialTiles, initialTileColors, settingsFile=None, helpFile=None):
        self.initialTiles = initialTiles
        self.rows = 20
        self.columns = 20
        self.tileSize = 20
        self.startGameX = 500
        self.startGameY = 100
        self.firstTankSpawnIndex = 187
        self.secondTankSpawnIndex = 64
        self.enemyTanksSpawnIndexes = []
        self.assignSettingsFromFile(settingsFile)
        self.gameWidth = self.columns * self.tileSize
        self.gameHeight = self.rows * self.tileSize

        self.helpContent = loadFileAsArray(helpFile, "There was a problem loading help content.") if helpFile else None

        self.tiles = list(self.initialTiles)
        self.tileColors = initialTileColors

        self.mapTurtle = Turtle(visible=False)
        self.messageTurtle = Turtle(visible=False)
        self.minesTurtle = Turtle(visible=False)

        self.bullets = []

        self.gameRunning = False
        self.gamePaused = False
        self.showingHelpFromGame = False

        self.firstTank = None
        self.secondTank = None
        self.enemyTanks = []
        self.allTanks = []

        tankSpeed = self.tileSize // 4
        self.controls1 = {
            "Up": (vector(0, tankSpeed), 0),
            "Down": (vector(0, -tankSpeed), 180),
            "Left": (vector(-tankSpeed, 0), 270),
            "Right": (vector(tankSpeed, 0), 90)
        }
        self.controls2 = {
            "w": (vector(0, tankSpeed), 0),
            "s": (vector(0, -tankSpeed), 180),
            "a": (vector(-tankSpeed, 0), 270),
            "d": (vector(tankSpeed, 0), 90)
        }

        self.tankCentralization = self.tileSize // 10  # minimal shift of tanks to make tanks stay in the center of the title

        self.laserShootSound = mixer.Sound("files/sounds/laserShoot.wav")
        self.explosionSound = mixer.Sound("files/sounds/explosion.wav")
        self.damageSound = mixer.Sound("files/sounds/damage.wav")
        self.gameOverSound = mixer.Sound("files/sounds/game-over.mp3")

        setup(420, 420, 750, 330)  # would center in resolution 1920x1080 and tiles 20x20 tileSize 40
        hideturtle()
        tracer(False)

        for key in ["r", "R"]:
            onkey(self.startGame, key)
        for key in ["p", "P"]:
            onkey(self.togglePause, key)
        for key in ["h", "H"]:
            onkey(self.toggleHelpMenu, key)

        listen()
        self.startScreen()
        done()

    def getTileCoordinates(self, point):
        x = int((point.x + (self.columns // 2) * self.tileSize) / self.tileSize)
        y = int(((self.rows // 2 - 1) * self.tileSize - point.y) / self.tileSize)
        return x, y

    def getPointFromTileCoordinates(self, x, y):
        x = x * self.tileSize - (self.columns // 2) * self.tileSize
        y = (self.rows // 2 - 1) * self.tileSize - y * self.tileSize
        return vector(x, y)  

    def assignSettingsFromFile(self, settingsFile):
        if not settingsFile:
            return
        try:
            loadedTiles, rows, columns, tileSize, startGameX, startGameY, firstTankSpawnIndex, secondTankSpawnIndex, enemyTanksSpawnIndexes = loadSettingsAndMapFromFile(settingsFile)
            self.initialTiles = loadedTiles or self.initialTiles
            self.rows = rows or self.rows
            self.columns = columns or self.columns
            self.tileSize = tileSize or self.tileSize
            self.startGameX = startGameX or self.startGameX
            self.startGameY = startGameY or self.startGameY
            self.firstTankSpawnIndex = firstTankSpawnIndex or self.firstTankSpawnIndex
            self.secondTankSpawnIndex = secondTankSpawnIndex or self.secondTankSpawnIndex
            self.enemyTanksSpawnIndexes = enemyTanksSpawnIndexes or self.enemyTanksSpawnIndexes
            print(f"Map and settings successfully loaded from '{settingsFile}'!")
        except ValueError as e:
            print(f"Error loading configuration: {e}")
            exit()

    def getTilePosition(self, index):
        x = (index % self.columns) * self.tileSize - (self.columns // 2) * self.tileSize
        y = (self.rows // 2 - 1) * self.tileSize - (index // self.columns) * self.tileSize
        return x, y

    def offset(self, point):
        x = (floor(point.x, self.tileSize, self.tileSize * (self.columns // 2)) + (self.columns // 2) * self.tileSize) / self.tileSize
        y = ((self.rows // 2 - 1) * self.tileSize - floor(point.y, self.tileSize, self.tileSize * (self.rows // 2))) / self.tileSize
        index = int(x + y * self.columns)
        return index

    def valid(self, point):
        blockingTiles = [Tile.NO_TILE.value, Tile.RIVER.value, Tile.INDESTRUCTIBLE_BLOCK.value, Tile.DESTRUCTIBLE_BLOCK.value]
        index = self.offset(point)
        if self.tiles[index] in blockingTiles:
            return False
        index = self.offset(point + int(self.tileSize * 0.95) - self.tankCentralization)
        if self.tiles[index] in blockingTiles:
            return False
        return True  # Remove alignment check



    def startScreen(self):
        self.gameRunning = False
        self.drawStartMenu()
        self.awaitStart()

    def awaitStart(self):
        onkey(self.startGame, "s")
        onkey(self.startGame, "S")
        onkey(self.toggleHelpMenu, "h")
        onkey(self.toggleHelpMenu, "H")
        onkey(exit, "Escape")

    def startGame(self):
        if self.gameRunning:  # don't start game if it's already started
            return
        setup(max((self.columns + 1) * self.tileSize, 420), max((self.rows + 1) * self.tileSize, 420), self.startGameX, self.startGameY)
        self.gameRunning = True
        self.gamePaused = False
        self.tiles = list(self.initialTiles)  # restarting map to state before changes in game

        self.drawSquare(Turtle(visible=False), -self.gameWidth, -self.gameHeight, 2*(self.gameWidth+self.gameHeight), "black")

        self.bullets = []
        self.enemyTanks = []
        self.allTanks = []

        firstTankSpawnPosition = self.getTilePosition(self.firstTankSpawnIndex)
        self.firstTank = Tank(self, firstTankSpawnPosition[0] + self.tankCentralization, firstTankSpawnPosition[1] + self.tankCentralization, "dark green", 0, self.controls1, "Control_R", "Return")
        secondTankSpawnPosition = self.getTilePosition(self.secondTankSpawnIndex)
        self.secondTank = Tank(self, secondTankSpawnPosition[0] + self.tankCentralization, secondTankSpawnPosition[1] + self.tankCentralization, "slate gray", 1, self.controls2, "Control_L", "Shift_L")
        # self.secondTank = AITank(self, secondTankSpawnPosition[0] + self.tankCentralization, secondTankSpawnPosition[1] + self.tankCentralization, "slate gray", 2, self.firstTank)
        for enemyId, enemyTankSpawnIndex in enumerate(self.enemyTanksSpawnIndexes, 2):
            enemyTankPosition = self.getTilePosition(enemyTankSpawnIndex)
            enemyTank = AITank(self, enemyTankPosition[0] + self.tankCentralization, enemyTankPosition[1] + self.tankCentralization, "gold", enemyId, self.firstTank)
            self.enemyTanks.append(enemyTank)
        self.allTanks = [self.firstTank, self.secondTank] + self.enemyTanks

        self.drawBoard()
        ontimer(self.minesTurtle.clear, 10000)  # hiding mines after 10 seconds
        self.roundOfMovement()

    def roundOfMovement(self):
        if not self.gameRunning or self.gamePaused:
            return
        self.firstTank.tankMovement()
        self.secondTank.tankMovement()
        self.firstTank.moveTank()
        self.secondTank.moveTank()
        for enemyTank in self.enemyTanks:
            enemyTank.moveTank()
        self.processBulletsMovementsAndCollisions()
        self.checkIfGameOver()
        update()
        if self.gameRunning:
            ontimer(self.roundOfMovement, 100)

    def checkIfGameOver(self):
        if self.firstTank and self.firstTank.hp == 0:
            self.endGame(self.firstTank.deathReason)
        if self.secondTank and self.secondTank.hp == 0:
            self.endGame(self.secondTank.deathReason)

    def endGame(self, reason):
        if not self.gameRunning:
            return
        self.gameRunning = False

        for tank in self.allTanks:  # draw destroyed tanks
            tank.drawTank()

        ontimer(lambda: conditionalExecution(not self.gameRunning, self.drawModalMessage, f"Game Over!\n{reason}", "Press 'R' to restart"), 2000)
        ontimer(lambda: conditionalExecution(not self.gameRunning, self.gameOverSound.play), 1000)

    def tanksCollision(self, tankChecking, tankCheckingPosition=None, collisionThreshold=20):
        tankCheckingPosition = tankCheckingPosition or tankChecking.position
        for otherTank in self.allTanks:
            distanceBetweenTanks = abs(tankCheckingPosition - otherTank.position)
            if otherTank != tankChecking and distanceBetweenTanks < collisionThreshold and tankChecking.speed != vector(0, 0):
                tankChecking.takeDamage(f"tank {tankChecking.tankId} collide with tank {otherTank.tankId}")
                otherTank.takeDamage(f"tank {otherTank.tankId} collide with tank {tankChecking.tankId}")
                tankChecking.speed = vector(0, 0)
                return True
        return False

    def processBulletsMovementsAndCollisions(self):
        for bullet in self.bullets[:]:
            bullet.moveBullet()
            hit = False
            tankSize = 0.8 * self.tileSize
            for tank in self.allTanks:
                if tank != bullet.shooter and tank.position.x <= bullet.position.x <= tank.position.x + tankSize and tank.position.y <= bullet.position.y <= tank.position.y + tankSize:
                    self.drawExplosion(Turtle(visible=False), bullet.position.x, bullet.position.y)
                    tank.takeDamage(f"tank {tank.tankId} was shot down by tank {bullet.shooter.tankId}")
                    hit = True
            bulletTileValue = self.tiles[self.offset(bullet.position)]
            if bulletTileValue in [Tile.INDESTRUCTIBLE_BLOCK.value, Tile.DESTRUCTIBLE_BLOCK.value]:
                if bulletTileValue == Tile.DESTRUCTIBLE_BLOCK.value:
                    self.tiles[self.offset(bullet.position)] = Tile.DESTROYED_DESTRUCTIBLE_BLOCK.value
                    x, y = self.getTilePosition(self.offset(bullet.position))
                    self.drawSquare(self.mapTurtle, x, y, squareColor=self.tileColors[Tile.DESTROYED_DESTRUCTIBLE_BLOCK.value])
                hit = True
            if hit:
                self.bullets.remove(bullet)
                bullet.bulletTurtle.clear()
                self.explosionSound.play()
                
    def togglePause(self):
        self.gamePaused = not self.gamePaused

        if not self.gamePaused:
            print("Game resumes!")
            self.messageTurtle.clear()
            self.roundOfMovement()
        else:
            print("Game paused!")
            self.drawModalMessage("Game Paused!", "Press 'P' to play")

    def toggleHelpMenu(self):
        if not self.helpContent:
            print("Help menu was not loaded correctly, so you can't open menu.")
            return
        if not self.gamePaused:
            self.showingHelpFromGame = self.gameRunning
            self.gamePaused = True
            self.drawHelpMenu()
        else:
            self.gamePaused = False
            self.messageTurtle.clear()
            if self.showingHelpFromGame:
                self.showingHelpFromGame = False
                self.roundOfMovement()
            else:
                self.drawStartMenu()
                self.awaitStart()

    def drawSquare(self, turtleObject, x, y, size=None, squareColor=None, circuitColor="black"):
        if not size:
            size = self.tileSize
        if circuitColor:
            turtleObject.color(circuitColor)
        else:
            turtleObject.color("")
        turtleObject.fillcolor(squareColor)
        turtleObject.up()
        turtleObject.goto(x, y)
        turtleObject.down()
        turtleObject.begin_fill()
        for count in range(4):
            turtleObject.forward(size)
            turtleObject.left(90)
        turtleObject.end_fill()

    def drawBoard(self):
        bgcolor('black')
        for index in range(len(self.tiles)):
            tile = self.tiles[index]
            if tile > 0:
                x, y = self.getTilePosition(index)
                tileColor = self.tileColors[tile]
                self.drawSquare(self.mapTurtle, x, y, squareColor=tileColor)
                if tile == Tile.MINE.value:  # drawing mines
                    self.minesTurtle.up()
                    self.minesTurtle.goto(x + self.tileSize // 2, y + self.tileSize // 2)
                    self.minesTurtle.dot(self.tileSize // 2, "black")

    def drawExplosion(self, drawingTurtle, x, y, explosionIteration=0, maxIterations=3):
        explosionColors = ["red", "yellow", "orange"]
        explosionColor = explosionColors[explosionIteration % len(explosionColors)]
        t = self.tileSize // 20
        offsets = [(0, 0), (2 * t, 2 * t), (-2 * t, -2 * t), (-2 * t, 2 * t), (2 * t, -2 * t), (4 * t, 0), (0, 4 * t), (-4 * t, 0), (0, -4 * t)]
        for dx, dy in offsets:
            self.drawSquare(drawingTurtle, x + dx * (explosionIteration + t), y + dy * (explosionIteration + t), 2 * t + explosionIteration, explosionColor)
        if explosionIteration < maxIterations:
            ontimer(lambda: self.drawExplosion(drawingTurtle, x, y, explosionIteration + 1, maxIterations), 150)
        else:
            ontimer(drawingTurtle.clear, 200)

    def drawModalBackground(self, x, y, modalWidth, modalHeight, backgroundColor="white", borderColor="black"):
        self.messageTurtle.color(borderColor)
        self.messageTurtle.fillcolor(backgroundColor)
        self.messageTurtle.penup()
        self.messageTurtle.goto(x - modalWidth / 2, y - modalHeight / 2)
        self.messageTurtle.pendown()
        self.messageTurtle.begin_fill()
        for _ in range(2):
            self.messageTurtle.forward(modalWidth)
            self.messageTurtle.left(90)
            self.messageTurtle.forward(modalHeight)
            self.messageTurtle.left(90)
        self.messageTurtle.end_fill()
        self.messageTurtle.penup()

    def drawModalMessage(self, message, subMessage, x=0, y=0, modalWidth=350, modalHeight=120):
        self.messageTurtle.clear()
        self.drawModalBackground(x, y, modalWidth, modalHeight)
        self.messageTurtle.goto(0, 0)
        self.messageTurtle.write(message, align="center", font=("Arial", 16, "bold"))
        self.messageTurtle.goto(0, -40)
        self.messageTurtle.write(subMessage, align="center", font=("Arial", 12, "normal"))

    def drawHelpMenu(self, modalWidth=420, modalHeight=420):
        self.messageTurtle.clear()
        self.drawModalBackground(0, 0, modalWidth, modalHeight, backgroundColor="white", borderColor="black")

        yOffset = (modalHeight / 2) - 40
        longestTextLineWidth = 312  # I checked how much pixels take to write the longest line

        for line in self.helpContent:
            strippedLine = line.lstrip()
            leadingSpaces = len(line) - len(strippedLine)

            x_offset = -modalWidth / 2 + (modalWidth - longestTextLineWidth) / 2
            x_offset += leadingSpaces * 10

            self.messageTurtle.goto(x_offset, yOffset)
            self.messageTurtle.write(line, align="left", font=("Arial", 10, "normal"))
            yOffset -= 20

        self.messageTurtle.goto(0, yOffset - 10)
        if self.showingHelpFromGame:
            self.messageTurtle.write("Press 'H' to return to the game", align="center", font=("Arial", 8, "italic"))
        else:
            self.messageTurtle.write("Press 'H' to return to the start screen", align="center", font=("Arial", 8, "italic"))

    def drawStartMenu(self):
        self.messageTurtle.clear()
        self.drawModalBackground(0, 0, 350, 250, backgroundColor="white", borderColor="black")

        self.messageTurtle.goto(0, 70)
        self.messageTurtle.write("Tank Battle Game", align="center", font=("Arial", 20, "bold"))

        self.messageTurtle.goto(0, -20)
        self.messageTurtle.write("Press 'S' to Start", align="center", font=("Arial", 12, "normal"))
        self.messageTurtle.goto(0, -60)
        self.messageTurtle.write("Press 'H' for Help", align="center", font=("Arial", 12, "normal"))
        self.messageTurtle.goto(0, -100)
        self.messageTurtle.write("Press Escape for Exit", align="center", font=("Arial", 12, "normal"))

    def getTileCoordinates(self, point):
        x = int((point.x + (self.columns // 2) * self.tileSize) / self.tileSize)
        y = int(((self.rows // 2 - 1) * self.tileSize - point.y) / self.tileSize)
        return x, y

    def getPointFromTileCoordinates(self, x, y):
        x = x * self.tileSize - (self.columns // 2) * self.tileSize
        y = (self.rows // 2 - 1) * self.tileSize - y * self.tileSize
        return vector(x, y)



class Bullet:
    def __init__(self, shooter, bulletSpeed=None):
        self.position = vector(shooter.position.x + int(0.35 * shooter.game.tileSize), shooter.position.y + int(0.35 * shooter.game.tileSize))
        self.direction = shooter.direction
        self.bulletSpeed = bulletSpeed if bulletSpeed else shooter.game.tileSize // 2
        self.shooter = shooter
        self.bulletTurtle = Turtle(visible=False)

    def moveBullet(self):
        self.bulletTurtle.clear()
        bulletOffsets = {
            90: vector(self.bulletSpeed, 0),
            180: vector(0, -self.bulletSpeed),
            270: vector(-self.bulletSpeed, 0),
            0: vector(0, self.bulletSpeed)
        }
        self.position.move(bulletOffsets[self.direction])
        self.shooter.game.drawSquare(self.bulletTurtle, self.position.x, self.position.y, int(0.15 * self.shooter.game.tileSize), "red")


class Tank:
    def __init__(self, game, x, y, tankColor, tankId, moveControls, stoppingControl, shootingControl, hp=3):
        self.game = game
        self.position = vector(x, y)
        self.speed = vector(0, 0)
        self.direction = 0  # 0 - forward, 90 - right, 180 - backward, 270 - left
        self.tankColor = tankColor
        self.tankId = tankId
        self.moveControls = moveControls
        self.stoppingControl = stoppingControl
        self.shootingControl = shootingControl
        self.setControls()
        self.keysPressed = {key: False for key in moveControls}
        self.hp = hp
        self.tankTurtle = Turtle(visible=False)
        self.hpTurtle = Turtle(visible=False)
        self.reloadingTime = 2000  # value in milliseconds
        self.loaded = True
        self.destroyed = False
        self.deathReason = ""

    def takeDamage(self, reason):
        if self.hp > 0:
            self.hp -= 1
            print(f"Tank {self.tankId} HP: {self.hp}")
            if self.hp == 0:
                self.destroyed = True
                self.deathReason = reason
                self.drawTank()
        self.game.damageSound.play()

    def change(self, tankSpeedDirection, angle=None):
        if self.destroyed:
            return
        tankSpeed = self.game.tileSize // 4
        offsets = {
            90: vector(tankSpeed, 0),  # right
            180: vector(0, -tankSpeed),  # down
            270: vector(-tankSpeed, 0),  # left
            0: vector(0, tankSpeed)  # up
        }
        if angle in offsets and self.game.valid(self.position + offsets[angle]):
            self.speed = tankSpeedDirection
            self.direction = angle
            return 0
        # stop tank
        if tankSpeedDirection.x == 0 and tankSpeedDirection.y == 0:
            self.speed = tankSpeedDirection
            return 1
        # if tank was stopped before then he can turn in any direction
        if self.speed.x == 0 and self.speed.y == 0 and angle is not None:
            self.direction = angle
            return 2
        # if tank move in wrong direction, where he can't go
        return -1

    def moveTank(self, wantMove=True):
        newPosition = self.position + self.speed  # wrapping map
        if newPosition.y > self.game.gameHeight / 2:
            newPosition.y -= self.game.gameHeight
        elif newPosition.y < -self.game.gameHeight / 2:
            newPosition.y += self.game.gameHeight
        if newPosition.x > self.game.gameWidth / 2:
            newPosition.x -= self.game.gameWidth
        elif newPosition.x < -self.game.gameWidth / 2:
            newPosition.x += self.game.gameWidth

        if not self.destroyed and self.game.valid(newPosition) and not self.game.tanksCollision(self, newPosition, int(self.game.tileSize * 0.8)) and wantMove:
            self.position = newPosition

        if self.game.tiles[self.game.offset(self.position)] == Tile.MINE.value:
            x, y = self.game.getTilePosition(self.game.offset(self.position))
            self.game.tiles[self.game.offset(self.position)] = Tile.ROAD.value
            self.game.drawSquare(self.game.mapTurtle, x, y, squareColor=self.game.tileColors[Tile.ROAD.value])
            self.game.drawExplosion(Turtle(visible=False), x + self.game.tileSize // 2, y + self.game.tileSize // 2)
            self.takeDamage(f"tank {self.tankId} ran over a mine")
        elif self.game.tiles[self.game.offset(self.position)] == Tile.FOREST.value:
            self.tankTurtle.clear()
            self.hpTurtle.clear()  # tank hide in forest
        else:
            self.drawTank()

    def drawHP(self, hpColor="red"):
        self.hpTurtle.clear()
        if self.hp > 0:
            x, y = self.position
            self.hpTurtle.up()
            self.hpTurtle.goto(x + self.game.tileSize // 2, y + int(self.game.tileSize * 1.25))
            self.hpTurtle.color(hpColor)
            self.hpTurtle.write(f"HP: {self.hp}", align="center", font=("Arial", self.game.tileSize // 2, "bold"))

    def drawTank(self):
        self.tankTurtle.clear()
        x, y = self.position
        angle = self.direction
        t = self.game.tileSize // 20
        """Draw tracks."""
        trackOffsets = {
            0: [(0, 0), (0, 4 * t), (0, 8 * t), (0, 12 * t), (12 * t, 0), (12 * t, 4 * t), (12 * t, 8 * t), (12 * t, 12 * t)],
            90: [(0, 0), (4 * t, 0), (8 * t, 0), (12 * t, 0), (0, 12 * t), (4 * t, 12 * t), (8 * t, 12 * t), (12 * t, 12 * t)],
            180: [(0, 0), (0, 4 * t), (0, 8 * t), (0, 12 * t), (12 * t, 0), (12 * t, 4 * t), (12 * t, 8 * t), (12 * t, 12 * t)],
            270: [(0, 0), (4 * t, 0), (8 * t, 0), (12 * t, 0), (0, 12 * t), (4 * t, 12 * t), (8 * t, 12 * t), (12 * t, 12 * t)]
        }
        for index, (dx, dy) in enumerate(trackOffsets[angle]):
            self.game.drawSquare(self.tankTurtle, x + dx, y + dy, 4 * t, self.tankColor)
            if self.destroyed and index in [0, t, 5, t]:
                self.game.drawSquare(self.tankTurtle, x + dx, y + dy, 4 * t, "black")
        """Draw hull."""
        hullOffsets = {0: (4 * t, t), 90: (t, 4 * t), 180: (4 * t, 7 * t), 270: (7 * t, 4 * t)}
        self.game.drawSquare(self.tankTurtle, x + hullOffsets[angle][0], y + hullOffsets[angle][1], 8 * t, self.tankColor)
        if self.destroyed:
            self.game.drawSquare(self.tankTurtle, x + hullOffsets[angle][0], y + hullOffsets[angle][1], 2 * t, "black", "")
            self.game.drawSquare(self.tankTurtle, x + hullOffsets[angle][0] + 4 * t, y + hullOffsets[angle][1], 2 * t, "black", "")
            self.game.drawSquare(self.tankTurtle, x + hullOffsets[angle][0], y + hullOffsets[angle][1] + 4 * t, 2 * t, "black", "")
            self.game.drawSquare(self.tankTurtle, x + hullOffsets[angle][0] + 2 * t, y + hullOffsets[angle][1] + 2 * t, 2 * t, "black", "")
            self.game.drawSquare(self.tankTurtle, x + hullOffsets[angle][0] + 6 * t, y + hullOffsets[angle][1] + 4 * t, 2 * t, "black", "")
        """Draw cannon."""
        cannonOffsets = {
            0: [(7 * t, 9 * t), (7 * t, 11 * t), (7 * t, 13 * t)],
            90: [(9 * t, 7 * t), (11 * t, 7 * t), (13 * t, 7 * t)],
            180: [(7 * t, 5 * t), (7 * t, 3 * t), (7 * t, t)],
            270: [(5 * t, 7 * t), (3 * t, 7 * t), (t, 7 * t)]
        }
        for dx, dy in cannonOffsets[angle]:
            self.game.drawSquare(self.tankTurtle, x + dx, y + dy, 2 * t, self.tankColor)
        if self.destroyed:
            self.game.drawSquare(self.tankTurtle, x + cannonOffsets[angle][1][0], y + cannonOffsets[angle][1][1], 2 * t, "black")
        self.drawHP()

    def setControls(self):
        onkey(lambda: self.shoot(), self.shootingControl)
        onkey(lambda: self.change(vector(0, 0)), self.stoppingControl)
        for key, (tankSpeed, angle) in self.moveControls.items():
            onkey(lambda k=key: self.keyPressHandler(k), key)
            if len(key) == 1 and key.isalpha():
                onkey(lambda k=key: self.keyPressHandler(k), key.upper())

    def keyPressHandler(self, key):
        self.keysPressed[key] = True

    def tankMovement(self):
        for key, (tankSpeed, angle) in self.moveControls.items():
            if self.keysPressed[key]:
                if self.change(tankSpeed, angle) != -1:
                    for k in self.keysPressed:
                        self.keysPressed[k] = False

    def shoot(self):
        if not self.loaded or self.destroyed:
            return
        bullet = Bullet(self)
        self.game.bullets.append(bullet)
        self.loaded = False
        ontimer(self.reload, self.reloadingTime)
        self.game.laserShootSound.play()

    def reload(self):
        self.loaded = True


class AITank(Tank):
    def __init__(self, game, x, y, tankColor, tankId, target, hp=3):
        super().__init__(game, x, y, tankColor, tankId, {}, "", "", hp)
        self.target = target
        self.path = []
        self.movementTimer = 0
        self.shootTimer = 0

    def moveTank(self, wantMove=True):
        if self.destroyed:
            return
        super().moveTank(wantMove)
        self.makeDecision()

    def makeDecision(self):
        if not self.target:
            return

        dx = self.target.position.x - self.position.x
        dy = self.target.position.y - self.position.y

        tankSpeed = self.game.tileSize // 20
        if abs(dx) > abs(dy):
            if dx > 0 and self.game.valid(self.position + vector(tankSpeed, 0)):
                self.change(vector(tankSpeed, 0), 90)
            elif dx < 0 and self.game.valid(self.position + vector(-tankSpeed, 0)):
                self.change(vector(-tankSpeed, 0), 270)
            else:
                if dy > 0:
                    self.change(vector(0, tankSpeed), 0)
                elif dy < 0:
                    self.change(vector(0, -tankSpeed), 180)
        else:
            if dy > 0 and self.game.valid(self.position + vector(0, tankSpeed)):
                self.change(vector(0, tankSpeed), 0)
            elif dy < 0 and self.game.valid(self.position + vector(0, -tankSpeed)):
                self.change(vector(0, -tankSpeed), 180)
            else:
                if dx > 0:
                    self.change(vector(tankSpeed, 0), 90)
                elif dx < 0:
                    self.change(vector(-tankSpeed, 0), 270)

        # Sprawdź, czy AI ma linię widzenia do gracza i strzelaj
        if self.hasLineOfSight(self.target.position):
            self.adjustDirectionTowards(self.target.position)
            self.shoot()

        # targetTileIndex = self.game.offset(self.target.position)
        # myTileIndex = self.game.offset(self.position)
        #
        # targetRow, targetColumn = divmod(targetTileIndex, self.game.columns)
        # myRow, myColumn = divmod(myTileIndex, self.game.columns)
        # print(f"Tank {self.tankId}:\nM {myRow}x{myColumn}\nT {targetRow}x{targetColumn}")

    def checkIfWantMoveInThatDirection(self):
        checkPosition = vector.copy(self.position)
        checkPosition.move(self.speed)
        checkTileIndex = self.game.offset(checkPosition)
        print(f"Speed={self.speed} Kierunek={self.direction}  moje pole= {self.game.offset(self.position)} sprawdzam={checkTileIndex} wS={self.game.tiles[checkTileIndex]}")
        if self.game.tiles[checkTileIndex] == Tile.MINE.value:
            return False
        for allyTank in self.game.enemyTanks:
            if allyTank != self and checkTileIndex == self.game.offset(allyTank.position):
                return False
        return True

    def checkIfAnyAllyTankBetweenSelfAndTarget(self):
        selfX, selfY = self.position
        targetX, targetY = self.target.position
        for allyTank in self.game.enemyTanks:
            if allyTank == self:
                continue
            allyX, allyY = allyTank.position
            dx = self.position.x - allyX
            dy = self.position.y - allyY
            if ((self.direction == 90 and abs(dy) < self.game.tileSize and selfX < allyX < targetX) or
                    (self.direction == 270 and abs(dy) < self.game.tileSize and targetX < allyX < selfX) or
                    (self.direction == 0 and abs(dx) < self.game.tileSize and selfY < allyY < targetY) or
                    (self.direction == 180 and abs(dx) < self.game.tileSize and targetY < allyY < selfY)):
                # print(f"Index={self.game.offset(self.position)} S{self.tankId}=({selfX};{selfY}) T=({targetX};{targetY}) A=({allyX};{allyY})")
                return True
        return False


mixer.init()  # for playing sounds
Game(tiles, tileColors, "files/tanksConfig.ini", "files/help.txt")
