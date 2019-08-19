import math
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix

class BasicTest(Matrix):
    def __init__(self, *args,
                 **kwds):

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        color = self.palette(self._step)

        for i in range(self.layout.width):
            for j in range(self.layout.height):
                pos = j + self.layout.height * i + self._step

                if pos % (self.layout.width * self.layout.height) == 0:
                    self.layout.set(i, j, color)
                else:
                    self.layout.set(i, j, (0,0,0))

        self._step += amt
