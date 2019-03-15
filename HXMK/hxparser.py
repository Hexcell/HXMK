from lark import Lark
from lark.indenter import Indenter

try:
	from . import hxtree
except Exception:
	import hxtree

grammar = r"""
start		: pattern _ARROW pattern

pattern		: part+

part		: STRING	-> part
			| STAR		-> star

_ARROW		: "->"
STRING		: /((?!->)[^\*](?<!->))+/
STAR		: "*"

%import common.WS
%ignore WS
"""

parser = Lark(grammar, parser="lalr")

def parse(s):
	return hxtree.Patterns(parser.parse(s))

if __name__ == "__main__":
	p = parse("src/*/*.c -> bin/obj/*/*.o")
	print(p.evaluate())