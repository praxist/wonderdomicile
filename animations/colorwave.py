import datetime
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix

class Horizontal(Matrix):
    def __init__(self, *args, **kwds):
        #The base class MUST be initialized by calling super like this
        super().__init__(*args, **kwds)

    def step(self, amt=1):
        for i in range(self.layout.width):
            for j in range(self.layout.height):
                self.layout.set(i,j,self.palette(1*i + self._step))

        self._step += amt

class Vertical(Matrix):
    def __init__(self, *args, **kwds):
        #The base class MUST be initialized by calling super like this
        super().__init__(*args, **kwds)

    def step(self, amt=1):
        for i in range(self.layout.width):
            color = self.palette(1*i + self._step)
            for j in range(self.layout.height):
                self.layout.set(i,j,color)

        self._step += amt
