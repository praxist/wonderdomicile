import math
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix

from bibliopixel.util import log

"""
Cool little running pixel pattern with a surprise at the end.
"""

BLACK = (0,0,0)


class Streaker(Matrix):
    def __init__(self, *args, fade=0.99, **kwds):

        # Fades previously lit pixels by a percentage
        self.fade = fade

        super().__init__(*args, **kwds)
        self.layout.set_brightness(255)


    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )

    def step(self, amt=1):
        self._step += amt
        color = self.palette(self._step)

        for i in range(self.layout.width):
            for j in range(self.layout.height):
                if self.fade < 1:
                    self.fade_pixel(i, j)
                else:
                    self.layout.set(i, j, BLACK)

        pos = self._step % (self.layout.height * self.layout.width)
        height, width = divmod(pos, self.layout.height)
        if width == 0:
            self.layout.fill(color)
        log.error((height, width, color))
        self.layout.set(height, width, color)


class MicroSeizure(Matrix):
    def __init__(self, *args, wait=100, **kwargs):
        self.wait = wait
        super().__init__(*args, **kwds)

    def step(self, amt=1):
        self._step += amt

        if self._step % self.wait == 0:
            self.layout.fill((255, 255, 0))
        elif self._step % self.wait == 1:
            self.layout.fill((0, 255, 255))
        elif self._step % self.wait == 2:
            self.layout.fill((255, 0, 255))
        elif self._step % self.wait == 3:
            self.layout.fill((0, 0, 0))
