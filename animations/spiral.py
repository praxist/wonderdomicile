import math
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix

# Like chase, but horizontal
class Spiral(Matrix):
    def __init__(self, *args,
                 fade=0.5,
                 length=16,
                 spacing=64,
                 **kwds):

        # Length of the chase
        self.length = length

        # Fades previously lit pixels by a percentage
        self.fade = fade

        # Length of empty space between each chase. Likely to look best as a multiple of 8
        self.spacing = spacing

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        color = self.palette(self._step)

        for i in range(self.layout.width):
            for j in range(self.layout.height):
                pos = i + 16 * j - self._step

                if pos % self.spacing in range(self.length):
                    self.layout.set(i, j, color)
                else:
                    if self.fade < 1:
                        old = self.layout.get(i, j)
                        if old != (0,0,0):
                            self.layout.set(
                                i, j,
                                fade_by(old, self.fade))
                    else:
                        self.layout.set(i, j, (0,0,0))

        self._step += amt

def fade_by(color, level):
    """
    Fades RGB tuple by percentage, 0 - 100
    """
    return map(lambda x: math.floor(x * level), color)


