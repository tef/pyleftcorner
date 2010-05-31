#parse tree

class ParseObject(object):
    pass

class ParseTree(ParseObject):
    def __init__(self, name, precedence, args):
        self.name = name
        self.precedence = precedence
        if isinstance(args, ParseObject):
            args = (args,)
        self.args = args

    def __str__(self):
        return "%s(%s)"%(self.name," ".join(str(x) for x in self.args))

 
class ParseTerminal(ParseObject): 
    def __init__(self, arg): 
        self.arg = arg 
        self.precedence = 0 
 
    def __str__(self): 
        return '<'+self.arg+'>' 

