from __future__ import annotations
from textwrap import indent

from common import binops, Insn, Expr, Binop, Unop, Nilop, AExpr, Ys7Scp

try:
	from lark import Lark, Transformer as _Transformer, v_args
	parser = Lark(open("grammar.g").read(), parser="lalr")
except ImportError:
	from grammar import Lark_StandAlone, Transformer as _Transformer, v_args
	parser = Lark_StandAlone(parser="lalr")
	assert parser.options.maybe_placeholders, "grammar not compliled correctly"

@v_args(inline=True)
class Transformer(_Transformer):
	WORD = str
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

	def header(self, version, hash):
		return (int(version), bytes.fromhex(hash))

	def function(self, name, block):
		return (str(name), block)

	block = args = text = v_args(inline = False)(list)

	stmt = Insn

	expr = AExpr

	def binop(self, a, op, b):
		return Binop(a, str(op), b)
	def prefixop(self, pre, a):
		if pre == "-":
			return Unop("-(", a, ")")
		else:
			return Unop(str(pre), a, "")
	def index(self, name, expr):
		return Unop(name + "[", expr, "]")
	def index_on(self, target, name, expr):
		return Binop(target, ".", Unop(name + "[", expr, "]"))

	def call(self, name, args):
		match name, args:
			case "rand", []: return Nilop("rand()")
			case "IsPartyIn", [a]: return Unop("IsPartyIn(", a, ")")
			case "IsMagicItem", [a]: return Unop("IsMagicItem(", a, ")")
			case _: raise ValueError(name, args)
	def call_on(self, target, name, args):
		match name, args:
			case "IsTurning", []: return Unop("", target, ".IsTurning()")
			case _: raise ValueError(target, name, args)

	def expr_missing(self):
		return Nilop("expr_missing")

	def __default__(self, name, tokens, meta):
		if name.startswith("__"):
			return super().__default__(name, tokens, meta)
		raise AttributeError(name, tokens)

def parse_ys7_scp(src: str) -> Ys7Scp:
	return Transformer().transform(parser.parse(src))
