import datetime
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix
import math

class HydroPump(Matrix):
    def __init__(self, *args,
                 fade=0.8,
                 pump_speed=12,
                 gravity=1,
                 pipe_rate=12,
                 **kwds):

        # Fades previously lit pixels by a percentage
        self.fade = fade

        self.pump_speed = pump_speed

        self.gravity = gravity

        # number of pipes active
        self.pipe_rate = pipe_rate

        self.active_columns = []
        #The base class MUST be initialized by calling super like this
        super().__init__(*args, **kwds)

        for i in range(self.layout.width):
            # Tuple of (active, water_level)
            self.active_columns.append([False, 0])


    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )

    def update_water_levels(self):
        # how long to stay at peak water level
        modifier = 0
        for c in self.active_columns:
            if c[0]:
                c[1] += self.pump_speed
                if c[1] > self.layout.height + modifier:
                    c[0] = False
            else:
                if c[1] > 1:
                    c[1] -= int(self.pump_speed * self.gravity)


    def step(self, amt=1):
        newly_active = 2 * int(math.floor(self._step / self.layout.height * self.pump_speed * self.pipe_rate) % (self.layout.width / 2))
        self.active_columns[newly_active][0] = True
        self.active_columns[newly_active + 1][0] = True

        self.update_water_levels()
        for i in range(self.layout.width):
            color = self.palette(self._step + 50 * math.floor(i/2))
            for j in range(self.layout.height):
                if j > self.layout.height - self.active_columns[i][1]:
                    self.layout.set(i, j, color)
                else:
                    if self.fade < 1:
                        self.fade_pixel(i, j)
                    else:
                        self.layout.set(i, j, (0,0,0))

        self._step += amt
