import math
import random

from bibliopixel.animation.matrix import Matrix


class Sparkles(Matrix):
    def __init__(self, *args,
                 fade=0.8,
                 sparkle_prob=0.0005,
                 **kwds):

        self.fade = fade
        self.sparkle_prob = sparkle_prob

        # The base class MUST be initialized by calling super like this
        super().__init__(*args, **kwds)

    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )

    def step(self, amt=1):
        for i in range(self.layout.width):
            # color = self.palette(self._step + 50 * math.floor(i / 2))
            for j in range(self.layout.height):
                # color = self.palette(random.randint(0, 255))
                color = (255,255,255)
                self.fade_pixel(i, j)

                if random.random() < self.sparkle_prob:
                    self.layout.set(i, j, color)

        self._step += amt
