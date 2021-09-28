import math
import random
import redis
import time

from bibliopixel.animation.matrix import Matrix


class Bumper:
    def __init__(self, bpm, multiple):
        self.set_bpm_attrs(bpm, multiple)
        self._reltime = self._last_zero_time = int(time.time() * 1000)
        self._frac = 0

    def set_bpm_attrs(self, bpm, multiple):
        """Update timing args, call to change bpm or multiple.

        The important var is _usbpm, or "microseconds per beat multiple". It's
        the interval in microseconds ("us") between beat-multiple events. E.g.
        at 100 BPM, multiple 4, there's 150000 us between events.
        """
        self._bpm = bpm
        self._multiple = multiple
        self._usbpm = 60000000 // (self._bpm * self._multiple)

    @property
    def bpm(self):
        return self._bpm

    @bpm.setter
    def bpm(self, val):
        self.set_bpm_attrs(val, self.multiple)

    @property
    def multiple(self):
        return self._multiple

    @multiple.setter
    def multiple(self, val):
        self.set_multiple_attrs(self.bpm, val)

    @property
    def usbpm(self):
        return self._usbpm

    @property
    def frac(self):
        return self._frac

    def update(self):
        """Updates internal timestamps, call from step.

        Call this before using frac in animations.

        This updates:
            _frac: how far we are into the current beat-multiple
            _reltime: the current time in ms mod _usbpm, used to calculate
                      _frac
            _last_reltime: _reltime as of the last update
            _last_zero_time: _ the (interpolated) timestamp of the last
                             beat-multiple, we use it to calculate _reltime.
                             Note that we can't just use `now % _usbpm` because
                             we want to move smoothly between nearby bpms.
        """
        self._last_reltime = self._reltime
        now = int(time.time() * 1000000)
        self._reltime = (now - self._last_zero_time) % self._usbpm
        if self._reltime < self._last_reltime:
            self._last_zero_time = now - self._reltime
        self._frac = self._reltime / self._usbpm


class Looperball:
    def __init__(self, length, clock, hue=0):
        self._length = length
        self._clock = clock
        self._hue = hue

        self.width = 200
        self.height = 2
        self._hsvs = [[(0, 0, 0) for i in range(self.width)] for j in
                      range(self.height)]
        self._embers = {}
        self._ef_hi = 1.1
        self._ef_lo = .65
        self._ember_update_rate = .5

        self._last_head = 0
        self._last_blank = 0

    def step(self):
        # draw the fireball, overwriting still-flickering embers if necessary
        head = int(self._clock.frac * self.width)
        # print("head: {}\t #embers: {}".format(head, len(self._embers)))
        for ll in range(self._length):
            w = head - ll
            # don't let negative width indexes leak through
            if w < 0:
                w = self.width + w
            b = 255 - 10 * ll
            for strip in range(self.height):
                self._hsvs[strip][w] = (self._hue, 255, b)  # TODO: palette

        # clear the last pixel behind the tail
        blank = head - self._length
        if blank < 0:
            blank = self.width + blank
        # print("head: {}\tblank: {}\tfrac:{}".format(head, blank, self._clock.frac))
        for strip in range(self.height):
            self._hsvs[strip][blank] = (self._hue, 255, 0)  # TODO: palette
        if self._last_blank < blank - 1:
            for ob in range(self._last_blank, blank):
                for strip in range(self.height):
                    self._hsvs[strip][ob] = (self._hue, 255, 0)  # TODO: palette
        # might have looped, blank the end and beginning of both strips
        elif self._last_blank > blank:
            for ob in range(self._last_blank, self.width):
                for strip in range(self.height):
                    self._hsvs[strip][ob] = (self._hue, 255, 0)  # TODO: palette
            for ob in range(0, blank):
                for strip in range(self.height):
                    self._hsvs[strip][ob] = (self._hue, 255, 0)  # TODO: palette
        self._last_blank = blank

        # start a new ember at the head and any pixels we skipped over since
        # the last update
        for strip in range(self.height):
            self._embers[(strip, head)] = [self._hue, 255, 255]  # TODO
        if self._last_head < head - 1:
            for ob in range(self._last_head, head):
                for strip in range(self.height):
                    self._embers[(strip, ob)] = [self._hue, 255, 255]  # TODO
        # might have looped, ignite the end and beginning of both strips
        elif self._last_head > head:
            for ob in range(self._last_head, self.width):
                for strip in range(self.height):
                    self._embers[(strip, head)] = [self._hue, 255, 255]  # TODO
            for strip in range(0, head):
                for strip in range(self.height):
                    self._embers[(strip, head)] = [self._hue, 255, 255]  # TODO
        self._last_head = head

        # clear the dead embers....
        self._embers = {k: v for k, v in self._embers.items()
                        if v[2] > 0}
        # ...and flicker the live ones
        for k in self._embers:
            if (self._ember_update_rate != 1 and random.random() <
                    self._ember_update_rate):
                self._embers[k][2] = \
                    min(255,
                        int(
                            (self._embers[k][2] *
                             (self._ef_lo + (self._ef_hi - self._ef_lo) *
                              random.random()))))
                self._hsvs[k[0]][k[1]] = self._embers[k]
        return self._hsvs

    # some bug, all pixels stay lit w/ 1 fireball...
    # @classmethod
    # def combine_hsvs(cls, balls):
    #     # for i, ball in enumerate(balls):
    #     #     print(i, len(ball._hsvs), len(ball._hsvs[0]))
    #     sums = [[[0, 0, 0] for j in range(len(balls[0]._hsvs[0]))]
    #             for i in range(len(balls[0]._hsvs))]
    #     for strip in range(len(balls[0]._hsvs)):
    #         for w in range(len(balls[0]._hsvs[strip])):
    #             # print("strip, w:", strip, w)
    #             # for i, ball in enumerate(balls):
    #                 # print("ball i:", i)
    #                 # print("hue sum:", ball._hsvs[strip][w][0])
    #                 # print("sat maz1:", ball._hsvs[strip][w][1])
    #                 # print("val maz2:", ball._hsvs[strip][w][2])

    #             sums[strip][w] = (
    #                 sum(ball._hsvs[strip][w][0] for ball in balls) % 255,
    #                 max(255, sum(ball._hsvs[strip][w][1] for ball in balls)),
    #                 max(255, sum(ball._hsvs[strip][w][2] for ball in balls))
    #             )
    #     return sums


def ccombine_hsvs(hsvs):
    num_strips = len(hsvs[0])
    num_leds = len(hsvs[0][0])
    res = [[[0, 0, 0] for ll in range(num_leds)]
           for ss in range(num_strips)]
    for strip in range(num_strips):
        for led in range(num_leds):
            h, s, v = 0, 0, 0
            for hsv in hsvs:
                h += hsv[strip][led][0]
                s += hsv[strip][led][1]
                v += hsv[strip][led][2]
            h = h % 256
            s = min(255, s)
            v = min(255, v)
            res[strip][led] = [h, s, v]
    return res


from functools import reduce
import bibliopixel as bp
bp.colors.conversions.hsv2rgb


# something is going wrong here, pixels are not going to zero!
def many_hsvs_to_rgb(hsvs):
    num_strips = len(hsvs[0])
    num_leds = len(hsvs[0][0])
    res = [[[0, 0, 0] for ll in range(num_leds)]
           for ss in range(num_strips)]
    for strip in range(num_strips):
        for led in range(num_leds):
            # for some reason the conversion screws this up?
            #
            # import bibliopixel as bp
            # c1 = bp.colors.conversions.hsv2rgb((0, 0, 0))
            # c2 = bp.colors.conversions.hsv2rgb((0, 0, 0))
            # c3 = bp.colors.conversions.hsv2rgb((0, 0, 0))
            # bp.colors.arithmetic.color_blend(
            #     bp.colors.arithmetic.color_blend(c1, c2),
            #     c3)
            #
            # = (2, 2, 2)
            if all(hsv[strip][led][2] == 0 for hsv in hsvs):
                rgb = (0, 0, 0)
            else:
                rgbs = [bp.colors.conversions.hsv2rgb(hsv[strip][led]) for hsv in hsvs]
                rgb = reduce(bp.colors.arithmetic.color_blend, rgbs)
            res[strip][led] = rgb
    return res


class Mega(Matrix):
    def __init__(self, *args,
                 bpm=30,
                 multiple=1,
                 **kwds):
        super().__init__(*args, **kwds)
        self.clock = Bumper(bpm, multiple)
        self.clock2 = Bumper(int(3 / 2 * bpm), 2)
        # self.clock3 = Bumper(4 * bpm, 1)
        self.fireballs = [
            Looperball(5, self.clock, hue=40), 
            # Looperball(5, self.clock2, hue=100),
            Flash(self.clock2),
            # Looperball(30, self.clock, hue=200),
        ]

    def step(self, amt=1):
        self.clock.update()
        self.clock2.update()
        # self.clock3.update()

        hsv_sets = [ball.step() for ball in self.fireballs]
        hsv_sets = [x for x in hsv_sets if x is not None]
        # for ball in self.fireballs:
        #     ball.step()
        # hsvs = Looperball.combine_hsvs(self.fireballs)

        # rgbs = many_hsvs_to_rgb([fb._hsvs for fb in self.fireballs])
        rgbs = many_hsvs_to_rgb(hsv_sets)
        # hsvs = self.fireballs[0]._hsvs

        # for h, strip in enumerate(self.fireballs[0]._hsvs):
        for h, strip in enumerate(rgbs):
            for w in range(len(strip)):
                rgb = strip[w]
                self.layout.set(w, h, rgb)


class Fill(Matrix):
    """Basic redis-controlled HSV fill."""
    def __init__(self, *args,
                 hue=128,
                 sat=128,
                 val=128,
                 **kwds):
        super().__init__(*args, **kwds)
        self._last_fetch = 0
        self.hue = hue
        self.sat = sat
        self.val = val
        self.rc = redis.Redis()

    def fetch(self):
        """Poll redis for new arg values."""
        got = self.rc.mget("ts", "hue", "sat", "val")
        ts = int(got['ts'])
        if ts > self._last_fetch:
            if got['hue']:
                self.hue = got['hue']
            if got['sat']:
                self.sat = got['sat']
            if got['val']:
                self.val = got['val']
            self._last_fetch = ts

    def step(self, amt=1):
        self.fetch()
        self.layout.fillHSV((self.hue, self.sat, self.val))


class RedisGetter:
    pass


class Flash:
    """Quick flash every beat"""
    def __init__(self, clock):
        self.clock = clock
        # frames per color
        self.fpc = 2
        self.colors = [(0, 255, 255),
                       (85, 255, 255),
                       (170, 255, 255)]
        self._blink = None
        self._last_frac = 0

    def step(self, amt=1):
        if self.clock.frac < self._last_frac:
            self._blink = 0
        self._last_frac = self.clock.frac

        # blank most of the time
        if self._blink is None:
            return None

        # avoid an IndexError if either attr changes in the next couple
        # lines
        fpc = self.fpc
        colors = self.colors

        if self._blink // fpc >= len(colors):
            self._blink = None
            return None
        hsv = colors[self._blink // fpc]
        self._blink += 1
        return [[hsv for i in range(200)] for j in range(2)]
        # print(self._blink)



class BumpMix:
    """Bump to the music"""
    def __init__(self, clock, hue=128):
        self.hue = hue
        self.clock = clock

    def step(self, amt=1):
        # regular interpolation: however far we are into the interval, light up
        # the strip that much
        if self.clock.usbpm > 150000:
            bright = 255 - int(self.clock.frac * 255)
        # the animation gets blurry at high frame rates, use quartiles instead,
        # spend half the time either off or at full brightness
        elif self.clock.usbpm > 45000:
            if self.clock.frac > 3/4:
                bright = 255
            elif self.clock.frac > 1/2:
                bright = 159  # = 255 * 5/8
            elif self.clock.frac > 1/4:
                bright = 96  # = 255 * 3/8
            else:
                bright = 0
        # full strobe mode baby
        elif self.clock.usbpm > 22000:
            bright = 255 if self.clock.frac > .5 else 0
        # too fast, give up
        else:
            bright = 255

        # print("{}\t{}".format(bright, self.hue))
        # self.layout.fillHSV((self.hue, 255, bright))
        return [[[self.hue, 255 // 2, bright // 2] for i in range(200)]
                for j in range(2)]


class Bump(Matrix):
    """Bump to the music"""
    def __init__(self, *args,
                 bpm=100,
                 multiple=1,
                 hue=128,
                 **kwds):
        super().__init__(*args, **kwds)
        self.hue = hue
        self.clock = Bumper(bpm, multiple)
        self.rc = redis.Redis()
        self._last_fetch = 0
        self.fetch()

    def fetch(self):
        ts, bpm, multiple, hue = map(int, self.rc.mget("ts", "bpm", "multiple",
                                                       "hue"))
        if ts > self._last_fetch:
            self.clock.set_bpm_attrs(bpm, multiple)
            self.hue = hue
            self._last_fetch = ts

    def step(self, amt=1):
        # poll redis for new arg values
        self.fetch()
        # update BPM clock
        self.clock.update()

        # regular interpolation: however far we are into the interval, light up
        # the strip that much
        if self.clock._msbpm > 150:
            bright = 255 - int(self.clock.frac * 255)
        # the animation gets blurry at high frame rates, use quartiles instead,
        # spend half the time either off or at full brightness
        elif self.clock._msbpm > 45:
            if self.clock.frac > 3/4:
                bright = 255
            elif self.clock.frac > 1/2:
                bright = 159  # = 255 * 5/8
            elif self.clock.frac > 1/4:
                bright = 96  # = 255 * 3/8
            else:
                bright = 0
        # full strobe mode baby
        elif self.clock._msbpm > 22:
            bright = 255 if self.clock.frac > .5 else 0
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
