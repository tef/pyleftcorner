class LE(object):
    def __init__(self, c):
        self.c = c

    def accepts(self, o):
        return o <= self.c

    def __str__(self):
        return "<=%s"%self.c

class LT(object):
    def __init__(self, c):
        self.c = c

    def accepts(self, o):
        return o < self.c

    def __str__(self):
        return "<%s"%self.c

