import random

class Shape:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.color = random.choice(["#f1c40f", "#9b59b6", "#1abc9c"])
        self.alive = True