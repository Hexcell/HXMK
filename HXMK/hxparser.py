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

class Debug(Indenter):
	NL_type = '_NL'
	OPEN_PAREN_types = []
	CLOSE_PAREN_types = []
	def process(self, stream):
		for t in stream:
			# print(t.type, t)
			yield t

parser = Lark(grammar, parser="lalr", postlex=Debug())

def parse(s):
	return hxtree.Patterns(parser.parse(s))

if __name__ == "__main__":
	p = parse("src/*/*.c -> bin/obj/*/*.o")
	print(p.evaluate())