import re


def lift(item):
    if isinstance(item, GrammarObject):
        return item
    else:
        return GrammarTerminal(item)

class ParseTree(object):
    def __init__(self, name, precedence, args):
        self.name = name
        self.precedence = precedence
        if isinstance(args, (ParseTree,Terminal)):
            args = (args,)
        self.args = args

    def __str__(self):
        return "(%s%d %s)"%(self.name,self.precedence," ".join(str(x) for x in self.args))

class Terminal(object):
    def __init__(self, arg):
        self.arg = arg
        self.precedence = 0

    def __str__(self):
        return '<'+self.arg+'>'

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


class GrammarTerminal(GrammarObject):
    def __init__(self, terminal):
        self.terminal = terminal

    def __str__(self):
        return "'%s'"%self.terminal


    def left_corner(self, input,p):
        return self.parse(input,p)

    def parse(self, input, precedence):
        token = input.next(self.terminal)
        if token:
            return token
        else:
            return None

    def right_hand(self, left, input,p):
        return Terminal(left)

class GrammarNonTerminal(GrammarObject):
    def left_corner(self, input,p):
        return None

    def right_hand(self, left, input,p):
        return None

class GrammarRule(GrammarNonTerminal):
    def __init__(self, grammar, name):
        self.grammar = grammar
        self.name = name

    def left_corner(self, input, p):
        left = input.next()
        if isinstance(left, ParseTree) and left.name == self.name:
            return left
        else:
            input.pushback(left)
            return None

    def right_hand(self, left, input,p):
        return left

    def parse(self, input, precedence=None):
        if precedence is None:
            precedence = default_precedence
        return self.grammar.parse_down(self.name, input, precedence)

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

    def __setitem__(self, index, val):
        self.grammar._add(self.name,index,val)

class GrammarOr(GrammarObject):
    def __init__(self, a,b):
        self.rules = [lift(a),lift(b)]

    def __or__(self, item):
        self.rules.append(lift(item))
        return self

    def __ror__(self, item):
        self.rules.insert(0,lift(item))
        return self

    def __str__(self):
        return " | ".join(str(r) for r in self.rules)

    def left_corner(self,input,p):
        return None

    def right_hand(self, left, input):
        return None

    def all_rules(self):
        x = []
        for rule in self.rules:
            x.extend(rule.all_rules())
        return x

    def parse(self, input, precedence):
        return None

    

class GrammarAnd(GrammarNonTerminal):
    def __init__(self, a,b):
        self.rules = [lift(a),lift(b)]

    def __add__(self, item):
        self.rules.append(lift(item))
        return self

    def __radd__(self, item):
        self.rules.insert(0,lift(item))
        return self

    def __str__(self):
        return " + ".join(str(r) for r in self.rules)

    def left_corner(self, input,p):
        return self.rules[0].left_corner(input,p)

    def right_hand(self, left, input,p):
        right0 = self.rules[0].right_hand(left, input,p)
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
                    input.pushback(rt)
                return None
        return rights

class GrammarConstraint(GrammarNonTerminal):
    def __init__(self, rule, precedence):
        self.rule = rule
        self.precedence = precedence

    def __str__(self):
        return "%s:%s[%s%s]"%(self.grammar._name, self.name, self.c, self.n)

    def left_corner(self, input,p):
        return self.rule.left_corner(input, self.precedence)

    def right_hand(self, left, input, p):
        return self.rule.right_hand(left, input, self.precedence)

    def all_rules(self):
        x = []
        for r in self.rule.all_rules():
            x.append(GrammarConstraint(r, self.precedence))
        return x

    def parse(self, input, p):
        return self.rule.parse(input, self.precedence)

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

class Grammar():
    def __init__(self, name):
        self._rules = []
        self._name = name

    def _add(self,name, p, val):
        self._rules.append((name,p,lift(val)))

    def __setattr__(self,name,val):
        if name.startswith('_'):
            self.__dict__[name] = val
        else:
            self._add(name,0, val)

    def __getattr__(self, name):
        return GrammarRule(self, name)

    def __str__(self):
        return self._name+":\n\t"+"".join("%s%s --> %s\n\t"%((n[0],"[%s]"%n[1]) for n,r in self._rules.items()))

    def parse_down(self, name, input, precedence):
        #print '>parse_down', name , input
        while input.has_next() and self.parse_up(input, precedence):
            pass

        peek = input.peek()
        if peek and isinstance(peek, ParseTree) and name == peek.name and precedence.accepts(peek.precedence):
            #print 'parse_down< yes', name , input
            return input.next()
        #print 'parse_down<', name , input
        return None

    def parse_up(self, input, precedence):
        #print '>parse_up', input
        for (name,p,r) in self._rules:
            if precedence.accepts(p):
                for rule in r.all_rules():
                    left = rule.left_corner(input, precedence)
                #    print r,'      left ', rule, input, left
                    if left:
                        right = rule.right_hand(left, input, precedence)
                #        print r,'     right', rule, input, right
                        if right:
                            input.pushback(ParseTree(name,p,right))
                #            print 'parse_up<', input
                            return True
                    
        #print 'parse_up<', input
        return False

class Tokenizer(object):
    def __init__(self, items):
        self.items = items

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

    def pushback(self, item):
        self.items.insert(0,item)

    def __str__(self):
        return '[['+" ".join(str(x) for x in self.items)+']]'


g = Grammar('g')

g.item = lift("1")| "2" | "3" | "4" 
g.item = re.compile("\d+")
g.expr = "(" + g.expr + ")" | g.add | g.mul | g.item
g.add[20] = (g.expr < 20) + "+" + (g.expr <= 20) 
g.mul[10] = (g.expr < 10) + "*" + (g.expr <= 10) 

#g.expr[90] = g.add



def do(input):
    t = Tokenizer(input)
    print 'input', input
    print 'tree', g.expr.parse(t)
    print 'leftovers', t.items

do(["1","*","2","*","4","+", "1"])
do(["1","*","2","+","1"])
do(["1","+","2","*","888888888888"])




"""
precedence climbing 

top down parsing - rewrite from the top down --> expr 
bottom up parsing - replace 1 + 2 -> num + num --> expr
lr - left to right, right most. i.e (1 + 2) + 3
ll - left to right, left most i.e 1 + (2 + 3)
egan stack - top down precedence parser with explicit stack for operations/items
pratt parser - top down parser with precedence and climbing

left corner / early parsing.

given rule a ---> fooBARbaz , bottom up on foo, top down on baz. i.e

when BAR, can we get foo from the left hand side


thing is, this is just pegs with left recursion. i.e bottom up + dcg + memoization

"""
