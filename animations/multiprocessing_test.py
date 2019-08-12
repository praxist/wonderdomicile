import datetime
from bibliopixel import animation
from bibliopixel.colors import COLORS
from bibliopixel.animation.matrix import Matrix
from bibliopixel.colors import hue2rgb
from multiprocessing import pool

class MultiProcessingTest(Matrix):
    def __init__(self, *args, **kwds):
        #The base class MUST be initialized by calling super like this
        self.p = pool.Pool(4)
        self.mp = True
        super().__init__(*args, **kwds)

    def step(self, amt=1):
        #Fill the strip, with each sucessive color
        if self.mp:
            results = [self.p.apply(mptest, args=(i,self._step)) for i in range(self.layout.width)]
            for i,r in enumerate(results):
                for j in range(self.layout.height):
                    self.layout.set(i,j,r)
        else:
            for i in range(self.layout.width):
                for j in range(self.layout.height):

                    self.layout.set(i,j,self.palette(i*1 + self._step))

        self._step += amt

def mptest(i,step):
    return hue2rgb((i + step) % 255)
