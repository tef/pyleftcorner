import re


def lift(item):
    if isinstance(item, GrammarObject):
        return item
    else:
        return GrammarTerminal(item)

class ParseTree(object):
    def __init__(self, name, args):
        self.name = name
        if isinstance(args, (ParseTree,Terminal)):
            args = (args,)
        self.args = args

    def __str__(self):
        return "(%s %s)"%(self.name," ".join(str(x) for x in self.args))

class Terminal(object):
    def __init__(self, arg):
        self.arg = arg

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


    def left_corner(self, input):
        return self.parse(input)

    def parse(self, input):
        token = input.next(self.terminal)
        if token:
            return token
        else:
            return None

    def right_hand(self, left, input):
        return Terminal(left)

class GrammarNonTerminal(GrammarObject):
    def left_corner(self, input):
        return None

    def right_hand(self, left, input):
        return None

class GrammarRule(GrammarNonTerminal):
    def __init__(self, grammar, name):
        self.grammar = grammar
        self.name = name

    def left_corner(self, input):
        left = input.next()
        if isinstance(left, ParseTree) and left.name == self.name:
            return left
        else:
            input.pushback(left)
            return None

    def right_hand(self, left, input):
        return left


    def parse(self, input):
        return self.grammar.parse_down(self.name, input)

    def __str__(self):
        return "%s:%s" % (self.grammar._name, self.name)

    def __lt__(self, other):
        return GrammarConstraint(self,'<',other)

    def __le__(self, other):
        return GrammarConstraint(self,'=<',other)

    def __gt__(self, other):
        return GrammarConstraint(self,'>',other)

    def __ge__(self, other):
        return GrammarConstraint(self,'=>',other)

    def __eq__(self, other):
        return GrammarConstraint(self,'=',other)

    def __ne__(self, other):
        return GrammarConstraint(self,'!',other)

    def __setitem__(self, index, val):
        self.grammar._rules[self.name,index] = val

class GrammarConstraint(GrammarNonTerminal):
    def __init__(self, rule, s, n):
        self.name = rule.name
        self.grammar = rule.grammar
        self.c = s
        self.n = n

    def __str__(self):
        return "%s:%s[%s%s]"%(self.grammar._name, self.name, self.c, self.n)

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

    def left_corner(self,input):
        return None

    def right_hand(self, left, input):
        return None

    def all_rules(self):
        x = []
        for rule in self.rules:
            x.extend(rule.all_rules())
        return x

    def parse(self, input):
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

    def left_corner(self, input):
        return self.rules[0].left_corner(input)

    def right_hand(self, left, input):
        right0 = self.rules[0].right_hand(left, input)
        #print 'and',  self.rules, right0
        if not right0:
            input.pushback(left)
            return None
        rights = [right0]
        for r in self.rules[1:]:
            #print '  > ', r , right0
            for rule in r.all_rules():
                next = r.parse(input)
                #print '    |', rule, input ,next
                if next:
                    rights.append(next)
                    break
            else:
                for rt in reversed(rights):
                    input.pushback(rt)
                return None
        return rights

class Grammar():
    def __init__(self, name):
        self._rules = {}
        self._name = name

    def __setattr__(self,name,val):
        if name.startswith('_'):
            self.__dict__[name] = val
        else:
            self._rules[(name,None)] = lift(val)

    def __getattr__(self, name):
        return GrammarRule(self, name)

    def __str__(self):
        return self._name+":\n\t"+"".join("%s%s --> %s\n\t"%(n[0], ("[%s]"%n[1]) if n[1] else "", r) for n,r in self._rules.items())

    def parse_down(self, name, input):
        #print '>parse_down', name , input
        while input.has_next() and self.parse_up(input):
            pass
        if name == input.peek_name():
            #print 'parse_down< yes', name , input
            return input.next()
        #print 'parse_down<', name , input
        return None

    def parse_up(self, input):
        #print '>parse_up', input
        for name,r in self._rules.items():
            for rule in r.all_rules():
                left = rule.left_corner(input)
            #    print r,'      left ', rule, input, left
                if left:
                    right = rule.right_hand(left, input)
            #        print r,'     right', rule, input, right
                    if right:
                        input.pushback(ParseTree(name[0],right))
            #            print 'parse_up<', input
                        return True
                    
        #print 'parse_up<', input
        return False

class Tokenizer(object):
    def __init__(self, items):
        self.items = items

    def peek_name(self):
        if not self.items: return None
        peek = self.items[0]
        if isinstance(peek, ParseTree):
            return peek.name
        return None

    def has_next(self):
        return len(self.items) > 0

    def next(self, *args):
        if not self.items: return None
        if args:
            arg, = args
            if isinstance(arg, basestring):
                if self.items[0] == arg:
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
g.expr =  "(" + g.expr + ")" | g.add | g.item
g.add = g.expr + "*" + g.expr

#g.add = (g.expr < 90) + t.add + (g.expr < 90) 
#g.expr[90] = g.add

t = Tokenizer(["1","*","2","*","4"])


print 'tree', g.expr.parse(t)
print 'leftovers', t.items




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


so expr + expr 

1 -> num -> expr

then add -> expr + expr , check + memoization



number -> +



def predict(name, input):
    do:
        e = consume(name, input):
        input.pushback(e)

        if e failed
            return input
        input = e
    while e is not input


expr = 'foo' expr 'bar'
expr = 'foo' expr 'baz'

consume(expr,1 + 2 + 3) -> 
find number -> 1 -->  number --> expr --> expr + expr find expr 3->num

rule a + b, left = 

def parse_down(name, input):
    tree = input.next()
    do:
        new_tree = parse_up(tree, input)
        if new_tree:
            tree = new_tree
        else:
            break
    if tree is name:
        return token
    else:
        input.pushback(token)
        return None

def parse_up(token, input)
    for rule in rules:
        new_left = rule.left_corner(token)
        if new_left:
            arguments = [newleft]
            for clause in rule right hand:
                    right= parse_down(clause, input)
                    if right:
                        arguments.append(right) 
                    else:
                        for right in reverse(arguments right hand)
                            input.pushback(right)
                        break 
            else: 
                return rule.construct(arguments)

    return None





"""
