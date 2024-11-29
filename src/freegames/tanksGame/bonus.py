from turtle import Turtle
from enum import Enum


class BonusType(Enum):
    HEALTH = 1
    SHOOTING_SPEED = 2


class Bonus:
    def __init__(self, game, bonus_type, position):
        self.game = game
        self.bonus_type = bonus_type
        self.position = position
        self.turtle = Turtle(visible=False)
        self.drawBonus()

    def drawBonus(self):
        x, y = self.position.x + self.game.tileSize // 2, self.position.y + self.game.tileSize // 2
        if self.bonus_type == BonusType.HEALTH:
            color = "red"
            shape = "circle"
        elif self.bonus_type == BonusType.SHOOTING_SPEED:
            color = "blue"
            shape = "square"
        else:
            color = "white"
            shape = "circle"
        self.turtle.up()
        self.turtle.goto(x, y)
        self.turtle.shape(shape)
        self.turtle.color(color)
        self.turtle.shapesize(self.game.tileSize / 20)
        self.turtle.showturtle()
