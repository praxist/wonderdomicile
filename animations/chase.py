import math
import random

from bibliopixel import animation
from bibliopixel.animation.matrix import Matrix
from bibliopixel.colors import COLORS

class Chase(Matrix):
    def __init__(self, *args,
                 alternating=2,
                 spacing=40,
                 length=2,
                 alternating_colors=True,
                 fade=0.5,
                 direction=-1,
                 **kwds):

        # Specified columns to chase in reverse.
        # Every $alternating will be reversed.
        self.alternating = alternating

        # If alternating, also alternate colors
        self.alternating_colors = alternating_colors

        # Length of empty space between each chase
        self.spacing = spacing

        # Length of the chase
        self.length = length

        # Chase goes up or down (up, down)
        self.direction = direction

        # Fades previously lit pixels by a percentage
        self.fade = fade

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        colors = [self.palette(self._step), self.palette(self._step * -1)]
        color = colors[0]

        for i in range(self.layout.width):

            if self.alternating > 0 and (math.floor(i / self.alternating)) % 2 == 0:
                alter_reverse = 1
                color = colors[0]
            else:
                alter_reverse = -1
                if self.alternating_colors:
                    color = colors[1]

            for j in range(self.layout.height):
                pos = j * alter_reverse * self.direction + self._step

                if pos % (self.spacing + self.length) in range(self.length):
                    self.layout.set(i, j, color)
                else:
                    if self.fade < 1:
                        self.fade_pixel(i, j)
                    else:
                        self.layout.set(i, j, (0,0,0))

        self._step += amt

    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )

class Wat(Matrix):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def step(self, amt=1):
        self.layout.set(0, 0, (0,235,0))
        self.layout.set(0, 1, (0,185,0))
        self.layout.set(0, 2, (0,135,0))
        self.layout.set(0, 3, (0,85,0))
        self.layout.set(0, 4, (0,35,0))
        self.layout.set(0, 5, (0,5,0))
        self.layout.set(0, 6, (0,3,0))
        # self.layout.set(1, 0, (0,0,255))
        # self.layout.set(1, 1, (0,255,255))


class Basic(Matrix):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.color = self.palette(random.randint(0, 255))
        from pprint import pformat as pf
        print(pf(self.layout.__dict__))

    def step(self, amt=1):
        lnum = self._step % 10
        if lnum == 0:
            self.color = self.palette(random.randint(0, 255))
        print("{}\t{}".format(self._step, lnum))
        self.layout.set(lnum, 0, self.color)
        self.layout.set(lnum, 1, self.color)
        self._step += amt

import time
import redis

class Bump(Matrix):
    """Bump to the music"""
    def __init__(self, *args,
                 bpm=100,
                 multiple=1,
                 hue=128,
                 **kwds):
        super().__init__(*args, **kwds)
        self.set_bpm_attrs(bpm, multiple)
        self.hue = hue
        # _msbpm is "milliseconds per beat multiple", set from bpm and
        # multiple. It's the interval between events.
        #
        # _reltime is the current time in ms mod _msbpm, tells us which frame
        # of the animation we should display now.
        #
        # _last_zero_time is the (interpolated) timestamp of the last
        # beat-multiple, we use it to calculate _reltime. Note that we can't
        # just use `now % _msbpm` because we want to move smoothly between
        # nearby bpms.
        self._reltime = self._last_zero_time = int(time.time() * 1000)
        self.rc = redis.Redis()
        self._last_fetch = 0
        self.fetch()

    def set_bpm_attrs(self, bpm, multiple):
        self._bpm = bpm
        self._multiple = multiple
        self._msbpm = 60000 // (self._bpm * self._multiple)

    def fetch(self):
        ts, bpm, multiple, hue = map(int, self.rc.mget("ts", "bpm", "multiple", "hue"))
        if ts > self._last_fetch:
            self.set_bpm_attrs(bpm, multiple)
            self.hue = hue
            self._last_fetch = ts
            print("{}\t{}".format(self._msbpm, self._last_fetch))

    def step(self, amt=1):
        # poll redis for new arg values
        self.fetch()

        # timing stuff
        self._last_reltime = self._reltime
        now = int(time.time() * 1000)
        self._reltime = (now - self._last_zero_time) % self._msbpm
        if self._reltime < self._last_reltime:
            self._last_zero_time = now - self._reltime

        # regular interpolation: however far we are into the interval, light up
        # the strip that much
        if self._msbpm > 150:
            bright = 255 - int(self._reltime / self._msbpm * 255)
        # the animation gets blurry at high frame rates, use quartiles instead,
        # spend half the time either off or at full brightness
        elif self._msbpm > 45:
            perc = self._reltime / self._msbpm
            if perc > 3/4:
                bright = 255
            elif perc > 1/2:
                bright = 159  # = 255 * 5/8
            elif perc > 1/4:
                bright = 96  # = 255 * 3/8
            else:
                bright = 0
        # full strobe mode baby
        elif self._msbpm > 22:
            bright = 255 if 2 * self._reltime > self._msbpm else 0
        # too fast, give up
        else:
            bright = 255

        # print("{}\t{}".format(bright, self.hue))
        self.layout.fillHSV((self.hue, 255, bright))

def blend(a, b, perc=.5):
    return [int(a[i] * perc + b[i] * (1 - perc)) for i in range(len(a))]


class Embers(Matrix):
    def __init__(self, *args,
                 fade=0.9,
                 sparkle_prob=0.00125,
                 **kwds):

        self.fade = fade
        self.sparkle_prob = sparkle_prob

        # The base class MUST be initialized by calling super like this
        super().__init__(*args, **kwds)

    # fades pixel at [i,j] by self.fade
    def fade_pixel_random(self, i, j):
        hi, lo = 1.5, .45
        old = self.layout.get(i, j)
        if old != (0,0,0):
            fade = lo + (hi - lo) * random.random()
            self.layout.set(
                i, j,
                [math.floor(x * fade) for x in old]
            )

    def step(self, amt=1):
        leader_size = 8
        # how white (1 full white)
        hw = .4

        stepscale = 7 / 8
        eff_step = int(self._step * stepscale)
        for i in range(self.layout.width):
            # do_sparkle = random.random() < self.sparkle_prob:
            # print(self._step, self.layout.width, self._step % self.layout.width)
            do_light = eff_step % self.layout.width == i
            for j in range(self.layout.height):
                # color = (255,255,255)
                color = self.palette(int(255 * i / self.layout.width))
                # color = self.palette(random.randint(0, 255))
                if do_light:
                    # leading white lights
                    for k in range(leader_size, 0, -1):
                        if i + k < self.layout.width:
                            self.layout.set(i + k, j,
                                blend((255, 255, 255), color,
                                      hw * k / leader_size))
                    self.layout.set(i, j, color)
                self.fade_pixel_random(i, j)

        if self._step > int(1 / stepscale) + 1 and eff_step == 0:
            self._step = 0
        self._step += amt


class ChaseChris(Matrix):
    def __init__(self, *args,
                 spacing=40,
                 lllength=2,
                 fade=0.5,
                 dirrrection=-1,
                 **kwds):

        # Length of empty space between each chase
        self.spacing = spacing

        # Length of the chase
        self.length = lllength

        # Chase goes up or down (up, down)
        self.direction = dirrrection

        # Fades previously lit pixels by a percentage
        self.fade = fade

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        for j in range(self.layout.width):
            color = self.palette((j + .2 * self._step) % 255)
            pos = j * self.direction - self._step

            if pos % (self.spacing + self.height) in range(self.height):
                self.layout.set(j, 0, color)
                self.layout.set(j, 1, color)
            else:
                if self.fade < 1:
                    self.fade_pixel(j, 0)
                    self.fade_pixel(j, 1)
                else:
                    self.layout.set(j, 0, (0,0,0))
                    self.layout.set(j, 1, (0,0,0))

        self._step += amt

    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )

class ChaseUp(Matrix):
    def __init__(self, *args,
                 spacing=40,
                 length=2,
                 fade=0.5,
                 direction=-1,
                 **kwds):

        # Length of empty space between each chase
        self.spacing = spacing

        # Length of the chase
        self.length = length

        # Chase goes up or down (up, down)
        self.direction = direction

        # Fades previously lit pixels by a percentage
        self.fade = fade

        super().__init__(*args, **kwds)

    def step(self, amt=1):
        for j in range(self.layout.height):
            color = self.palette(j)
            pos = j * self.direction - self._step

            if pos % (self.spacing + self.length) in range(self.length):
                self.layout.set(0, j, color)
                self.layout.set(1, j, color)
            else:
                if self.fade < 1:
                    self.fade_pixel(0, j)
                    self.fade_pixel(1, j)
                else:
                    self.layout.set(0, j, (0,0,0))
                    self.layout.set(1, j, (0,0,0))

        self._step += amt

    # fades pixel at [i,j] by self.fade
    def fade_pixel(self, i, j):
        old = self.layout.get(i, j)
        if old != (0,0,0):
            self.layout.set(
                i, j,
                [math.floor(x * self.fade) for x in old]
            )
