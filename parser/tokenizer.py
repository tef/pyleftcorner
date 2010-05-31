class Tokenizer(object):
    def __init__(self, items):
        self.items = list(items)+["$"]

    def peek(self):
        if not self.items: return None
        return self.items[0]

    def has_next(self):
        return len(self.items) > 0

    def next(self, *args):
        if not self.items: return None
        if args:
            arg, = args
            if isinstance(arg, basestring):
                if self.items[0] == arg:
                    return self.items.pop(0)
            elif hasattr(arg,'match') and isinstance(self.items[0], basestring):
                if arg.match(self.items[0]):
                    return self.items.pop(0)
            return None
        else:
            return self.items.pop(0)

    def pushback_token(self, item):
        self.pushback(item)

    def pushback(self, item):
        self.items.insert(0,item)

    def __str__(self):
        return '[['+" ".join(str(x) for x in self.items)+']]'


