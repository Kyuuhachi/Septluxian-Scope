from __future__ import annotations
from textwrap import indent

from common import Insn, Binop, Unop, Call, Index, AExpr, Ys7Scp

try:
	from lark import Lark, Transformer as _Transformer, v_args
	parser = Lark(open("grammar.g").read(), parser="lalr")
except ImportError:
	from grammar import Lark_StandAlone, Transformer as _Transformer, v_args
	parser = Lark_StandAlone(parser="lalr")
	assert parser.options.maybe_placeholders, "grammar not compliled correctly"

@v_args(inline=True)
class Transformer(_Transformer):
	def str(self, v):
		return v[1:-1].replace('""', '"')

	def number(self, v):
		if '.' in v:
			return float(v)
		else:
			return int(v)

	def start(self, header, *functions):
		(version, hash) = header
		return Ys7Scp(version, hash, dict(functions))

	header = lambda _, version, hash: (int(version), bytes.fromhex(hash))
	function = lambda _, name, block: (name, block)

	block = args = text = lambda self, *args: list(args)

	stmt = Insn

	expr = AExpr
	binop = lambda _, a, op, b: Binop(a, op.value, b)
	unop = lambda _, op, a: Unop(op.value, a)

	index = lambda _, name, expr: Index(name.value, expr)
	index_on = lambda _, target, name, expr: Binop(target, ".", Index(name.value, expr))

	call = lambda _, name, args: Call(None, name.value, args)
	call_on = lambda _, target, name, args: Call(target, name.value, args)

	def __default__(self, name, tokens, meta):
		if name.startswith("__"):
			return super().__default__(name, tokens, meta)
		raise AttributeError(name, tokens)

def parse_ys7_scp(src: str) -> Ys7Scp:
	return Transformer().transform(parser.parse(src))
