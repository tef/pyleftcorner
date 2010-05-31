#!/usr/bin/env python
import re

from parser  import Grammar, Tokenizer

def main():
    g = Grammar('grammar')

    g.number = re.compile("\d+")

    g.add[20] = (g.expr < 20) + "+" + (g.expr <= 20)
    g.sub[20] = (g.expr < 20) + "-" + (g.expr <= 20)
    g.mul[10] = (g.expr <= 10) + "*" + (g.expr < 10)
    g.div[10] = (g.expr <= 10) + "/" + (g.expr < 10)

    g.subexpr[0] = "(" + (g.expr <= 100) + ")"

    g.expr[0] = g.subexpr | g.number | g.add | g.sub | g.mul | g.div

    g.block = g.expr +"$"


    def do(input):
        t = Tokenizer(input)
        print 'input', input
        print 'tree', g.block.parse(t)
        if t.items:
            print 'leftovers', t
        print

    do(["1","*","2","+","1"])
#    do(["1","+","2","*","8"])
#    do(["1","*","2","+","1"])
#    do(["1","*","2","*","8"])
#    do("(1+2)*3")
#    do("(2)")
#    do("1+2-3/5")
#    do("1+2/3/5")


if __name__ == '__main__': main()

