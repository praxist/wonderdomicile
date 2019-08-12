import math
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix

# BUG: spacing at 0 should just look completely solid, but there is a gap.

# "Triangles" that move up and down the columns
class Triangles(Matrix):
    def __init__(self, *args,
                 share_edge=True,
                 size=3,
                 spacing=4,
                 group_spacing=0,
                 blink=False,
                 blink_steps=6,
                 fade=0.5,
                 **kwds):

        # Gap between each triangle
        self.spacing = spacing

        # Gap between each pair of triangles
        self.group_spacing = group_spacing

        # Pixel length of the long edge of triangle. Likely best with 3 or 5
        self.size = size

        # True to have triangles share long edges with adjacent column
        self.share_edge = share_edge

        # Triangles blink and crawl up as opposed to scrolling
        self.blink = blink

        # Number of steps before blinking
        self.blink_steps = blink_steps

        # Fades previously lit pixels by a percentage
        self.fade = fade

        # Internal variables
        self.block = None
        self.long_edge = None
        self.short_edge = None
        self.long_edge2 = None
        self.short_edge2 = None
        self.blink_incr = 0
        self.blink_switch = True
        self.calculate_internal_vars()
        super().__init__(*args, **kwds)

    def calculate_internal_vars(self):
        self.long_edge = list(range(self.size))
        self.short_edge = [x + len(self.long_edge) + self.spacing for x in list(range(self.size - 2))]
        self.short_edge2 = list(range(self.size - 2))
        self.long_edge2 = [x + len(self.short_edge2) + self.spacing for x in list(range(self.size))]

        self.block = len(self.long_edge) + len(self.short_edge) + 2 * self.spacing + self.group_spacing


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
        black = (0,0,0)

        if self.blink:
            blink_side = math.floor(self._step / self.blink_steps) % 2 == 0
            if blink_side != self.blink_switch:
                self.blink_switch = blink_side
                if blink_side:
                    self.blink_incr += (self.size - 1) * 2

            for i in range(self.layout.width):
                if self.share_edge:
                    left = (math.floor(i/2) + i) % 2 == 0
                else:
                    left = i % 2 == 0

                for j in range(self.layout.height):
                    pos = j + self.blink_incr
                    if left:
                        # left side of column
                        if blink_side and pos % self.block in self.short_edge:
                            self.layout.set(i, j, color)
                        elif not blink_side and pos % self.block in self.long_edge:
                            self.layout.set(i, j, color)
                        else:
                            if self.fade < 1:
                                self.fade_pixel(i, j)
                            else:
                                self.layout.set(i, j, (0,0,0))
                    else:
                        # right side of column
                        if blink_side and (pos - 1) % self.block in self.long_edge2:
                            self.layout.set(i, j, color)
                        elif not blink_side and (pos - 1) % self.block in self.short_edge2:
                            self.layout.set(i, j, color)
                        else:
                            if self.fade < 1:
                                self.fade_pixel(i, j)
                            else:
                                self.layout.set(i, j, (0,0,0))

        # No blinking. Just scrolling
        else:
            for i in range(self.layout.width):
                if self.share_edge:
                    left = (math.floor(i/2) + i) % 2 == 0
                else:
                    left = i % 2 == 0

                for j in range(self.layout.height):
                    pos = j + self._step
                    if left:
                        # left side of column
                        if pos % self.block in self.short_edge:
                            self.layout.set(i, j, color)
                        elif pos % self.block in self.long_edge:
                            self.layout.set(i, j, color)
                        else:
                            if self.fade < 1:
                                self.fade_pixel(i, j)
                            else:
                                self.layout.set(i, j, (0,0,0))
                    else:
                        # right side of column
                        if (pos - 1) % self.block in self.long_edge2:
                            self.layout.set(i, j, color)
                        elif (pos - 1) % self.block in self.short_edge2:
                            self.layout.set(i, j, color)
                        else:
                            if self.fade < 1:
                                self.fade_pixel(i, j)
                            else:
                                self.layout.set(i, j, (0,0,0))
