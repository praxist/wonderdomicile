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
    def __init__(self, *args,
                 bloom=False,
                 color_speed=2,
                 color_distance=2,
                 **kwds):
        #The base class MUST be initialized by calling super like this

        # Causes the color to bloom from the center
        self.bloom = bloom

        # higher values make colors change faster
        self.color_speed = color_speed

        # higher values display more colors in a single frame
        self.color_distance = color_distance

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        for j in range(self.layout.height):
            if self.bloom:
                distance = abs(self.layout.height / 2 - j)
                color = self.palette(self._step * self.color_speed - distance * self.color_distance)
            else:
                color = self.palette(self.color_speed * j + self._step * self.color_distance)

            for i in range(self.layout.width):
                self.layout.set(i,j,color)

        self._step += amt
