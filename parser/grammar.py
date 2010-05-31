import re

def main():
    g = Grammar('g')

    g.item[0,ItemParseTree] = re.compile("\d+")

    constructor = OpParseTree
    g.add[20,constructor] = (g.expr < 20) + "+" + (g.expr <= 20) 
    g.sub[20,constructor] = (g.expr < 20) + "-" + (g.expr <= 20) 
    g.mul[10,constructor] = (g.expr <= 10) + "*" + (g.expr < 10) 
    g.div[10,constructor] = (g.expr <= 10) + "/" + (g.expr < 10)


    def sub(name, p, args):
        return args[1] # return the middle expression

    g.subexpr[0, sub] = "(" + (g.expr <= 100) + ")"

    g.expr[0, ExprParseTree] = g.subexpr | g.item | g.add | g.sub | g.mul | g.div

    g.block = g.expr +"$"


    def do(input):
        t = Tokenizer(input)
        print 'input', input
        print 'tree', g.block.parse(t)
        if t.items:
            print 'leftovers', t
        print

    do(["1","*","2","+","1"])
    do(["1","+","2","*","8"])
    do(["1","*","2","+","1"])
    do(["1","*","2","*","8"])
    do("(1+2)*3")
    do("(2)")
    do("1+2-3/5")
    do("1+2/3/5")



# precedence functions
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


default_precedence=LE(100)

# helper functions
def lift(item):
    "transform an object into a grammar object. i.e lift(2)"
    if isinstance(item, GrammarObject):
        return item
    else:
        return GrammarTerminal(item)


#parse tree
class ParseTree(object):
    def __init__(self, name, precedence, args):
        self.name = name
        self.precedence = precedence
        if isinstance(args, (ParseTree,Terminal)):
            args = (args,)
        self.args = args

    def __str__(self):
        return "%s(%s)"%(self.name," ".join(str(x) for x in self.args))

class OpParseTree(ParseTree):
    def __init__(self, name, precedence, args):
        self.name = name
        self.precedence = precedence
        self.args =  args;

    def __str__(self):
        return "[%s %s %s]"%(self.args[0], self.args[1].arg, self.args[2])

class ItemParseTree(ParseTree):
    def __init__(self, name, precedence, args):
        self.name = name
        self.precedence = precedence
        self.args =  args;

    def __str__(self):
        return str(self.args)

class ExprParseTree(ParseTree):
    def __init__(self, name, precedence, args):
        self.name = name
        self.precedence = precedence
        self.args =  args;

    def __str__(self):
        return "%s"%self.args

class Terminal(object):
    def __init__(self, arg):
        self.arg = arg
        self.precedence = 0

    def __str__(self):
        return '<'+self.arg+'>'


#Grammar Objects
class GrammarObject(object):
    def __add__(self, item):
        return GrammarAnd(self, item)

    def __radd__(self,item):
        return GrammarAnd(item, self)

    def __or__(self, item):
        return GrammarOr(self, item)

    def __ror__(self,item):
        return GrammarOr(item, self)
    
    def all_rules(self):
        return (self,)

    def corner_names(self):
        return ()

class GrammarTerminal(GrammarObject):
    "A terminal within a grammar rule"
    def __init__(self, terminal):
        self.terminal = terminal

    def __str__(self):
        return "'%s'"%self.terminal


    def parse_left_corner(self, input, precedence):
        return input.next(self.terminal)

    def parse(self, input, p):
        token = self.parse_left_corner(input, p)
        if token:
            return Terminal(token)
        else:
            return None

    def parse_right_hand(self, left, input,p):
        return Terminal(left)

class GrammarNonTerminal(GrammarObject):
    "Any non terminal"
    def parse_left_corner(self, input,p):
        return None

    def parse_right_hand(self, left, input,p):
        return None

class GrammarRule(GrammarNonTerminal):
    "A non terminal appearing on the right hand side"
    def __init__(self, grammar, name):
        self.grammar = grammar
        self.name = name

    def corner_names(self):
        return (self.name,)

    def parse_left_corner(self, input, p):
        left = input.next()
        if isinstance(left, ParseTree) and left.name == self.name:
            return left
        else:
            input.pushback(left)
            return None

    def parse_right_hand(self, left, input,p):
        return left

    def parse(self, input, precedence=None):
        if precedence is None:
            precedence = default_precedence
        return self.grammar.parse(self.name, input, precedence)

    def __str__(self):
        return "%s:%s" % (self.grammar._name, self.name)

    def __lt__(self, other):
        return GrammarConstraint(self,LT(other))

    def __le__(self, other):
        return GrammarConstraint(self,LE(other))

    def __gt__(self, other):
        return GrammarConstraint(self,GT(other))

    def __ge__(self, other):
        return GrammarConstraint(self,GE(other))

    def __eq__(self, other):
        return GrammarConstraint(self,EQ(other))

    def __ne__(self, other):
        return GrammarConstraint(self,NE(other))

    def __setitem__(self, p, val):
        try:
            self.grammar._add(self.name,p[0],val,p[1])
        except:
            self.grammar._add(self.name,p,val)

    def __getitem__(self, p, val):
        class Temp(object):
            def __setitem__(s, c, val):
                print 'iset',self,p,val
                self.grammar._add(self.name,p,val,c)
        return Temp()

class GrammarOr(GrammarObject):
    "A | B | C. Represents directed choice of A or then B or then C"
    def __init__(self, a,b):
        self.rules = [lift(a),lift(b)]

    def corner_names(self):
        s = set()
        for r in self.rules:
            s.update(r.corner_names())
        return s

    def __or__(self, item):
        self.rules.append(lift(item))
        return self

    def __ror__(self, item):
        self.rules.insert(0,lift(item))
        return self

    def __str__(self):
        return " | ".join(str(r) for r in self.rules)

    def parse_left_corner(self,input,p):
        return None

    def parse_right_hand(self, left, input):
        return None

    def all_rules(self):
        x = []
        for rule in self.rules:
            x.extend(rule.all_rules())
        return x

    def parse(self, input, precedence):
        return None

    

class GrammarAnd(GrammarNonTerminal):
    "A sequence of grammar clauses in succession"
    def __init__(self, a,b):
        self.rules = [lift(a),lift(b)]

    def __add__(self, item):
        self.rules.append(lift(item))
        return self

    def corner_names(self):
        return self.rules[0].corner_names();

    def __radd__(self, item):
        self.rules.insert(0,lift(item))
        return self

    def __str__(self):
        return " + ".join(str(r) for r in self.rules)

    def parse_left_corner(self, input,p):
        return self.rules[0].parse_left_corner(input,p)

    def parse_right_hand(self, left, input,p):
        right0 = self.rules[0].parse_right_hand(left, input,p)
        #print 'and',  self.rules, right0
        if not right0:
            input.pushback(left)
            return None
        rights = [right0]
        for r in self.rules[1:]:
            #print '  > ', r , right0
            for rule in r.all_rules():
                next = r.parse(input,p)
                #print '    |', rule, input ,next
                if next:
                    rights.append(next)
                    break
            else:
                for rt in reversed(rights):
                    input.pushback_token(rt)
                return None
        return rights

class GrammarConstraint(GrammarNonTerminal):
    "Normally a non terminal which must have a specific precedence"
    def __init__(self, rule, precedence):
        self.rule = rule
        self.precedence = precedence

    def __str__(self):
        return str(self.rule)

    def parse_left_corner(self, input,p):
        return self.rule.parse_left_corner(input, self.precedence)

    def parse_right_hand(self, left, input, p):
        return self.rule.parse_right_hand(left, input, self.precedence)

    def all_rules(self):
        x = []
        for r in self.rule.all_rules():
            x.append(GrammarConstraint(r, self.precedence))
        return x

    def parse(self, input, p):
        return self.rule.parse(input, self.precedence)

class Grammar():
    def __init__(self, name):
        self._rules = {}
        self._name = name
        self._corners = {}
        self._corners_idx = {}


    def _add(self,name, p, val, c = ParseTree):
        "internal method for adding a rule"
        v = lift(val)
        self._add_corner(name, v)
        if name not in self._rules:
            self._rules[name] = []
        self._rules[name].append((p,c,v))

    def _add_corner(self, name, val):
        "index the left corners of each rule added. this is used to guide bottom up parsing"
        if name not in self._corners:
            self._corners[name] = set()
            self._corners[name].add(name)

        corners = val.corner_names()
        if corners:
            self._corners[name].update(corners)
            for c in corners:
                if c in self._corners:
                    self._corners[name].update(self._corners[c])
                if c not in self._corners_idx:
                    self._corners_idx[c] = set()
                self._corners_idx[c].add(name)
                if name in self._corners_idx:
                    for n in self._corners_idx[name]:
                      self._corners[n].add(c)
                      self._corners_idx[c].add(n)

    def __setattr__(self,name,val):
        if name.startswith('_'):
            self.__dict__[name] = val
        else:
            self._add(name,0, val)

    def __getattr__(self, name):
        return GrammarRule(self, name)

    def __str__(self):
        return self._name+":\n\t"+"".join("%s%s --> %s\n\t"%((n[0],"[%s]"%n[1]) for n,r in self._rules.items()))

    def parse(self, name, input, precedence):
        print '>parse', name , input
        while input.has_next() and self.parse_up(name, input,precedence):
            pass # repeately grow the input until it cannot apply any more rules
        peek = input.peek()
        if peek and isinstance(peek, ParseTree) and name == peek.name and precedence.accepts(peek.precedence):
            #print 'parse< yes', name , input
            return input.next()
        #print 'parse<', name , input
        return None

    def parse_up(self,topname,  input, precedence):
        print '>parse_up', input
        peek = input.peek()
        # for each of the non-terminals that can appear in the left corner of a top-name rule
        for name in self._corners[topname]:
            for p,c,r in self._rules[name]:
                if precedence.accepts(p):
                    for rule in r.all_rules():
                        left = rule.parse_left_corner(input, precedence)
                    #    print r,'      left ', rule, input, left
                        if left:
                            right = rule.parse_right_hand(left, input, precedence)
                    #        print r,'     right', rule, input, right
                            if right:
                                input.pushback_token(c(name,p,right))
                    #            print 'parse_up<', inputa
                                return True
                    
        #print 'parse_up<', input
        return False

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




if __name__ == '__main__': main()
