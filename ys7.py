from __future__ import annotations
import read
from pathlib import Path

from common import insn_table, InsnTable, Insn, Expr, Binop, Unop, Nilop, AExpr, Ys7Scp
import parse_bin

binops = {
	"!=": 4,
	"==": 4,
	"<": 4,
	">": 4,
	"<=": 4,
	">=": 4,
	"&": 3,
	"&&": 3,
	"|": 1,
	"||": 1,
	"+": 5,
	"-": 5,
	"*": 6,
	"/": 6,
	"%": 6,
	".": 10,
	"expr_missing_op": 100,
}


def print_term(t: int | float | str) -> str:
	match t:
		case int(t):
			return str(t)
		case float(t):
			try:
				from numpy import float32
				return str(float32(t))
			except ImportError:
				return str(t)
		case str(t):
			assert '\n' not in t
			assert '\r' not in t
			assert '\t' not in t
			return '"' + t.replace('"', '""') + '"'

def print_expr(e: Expr, prio: int = 1000) -> str:
	prio2 = 100
	match e:
		case int(e): s = print_term(e)
		case float(e): s = print_term(e)
		case str(e): s = e
		case Binop(a, op, b):
			prio2 = binops[op]
			if op != ".": op = f" {op} "
			s = print_expr(a, prio2) + op + print_expr(b, prio2+1)
		case Unop(pre, a, suf): s = pre + print_expr(a, 0 if suf else 100) + suf
		case Nilop(op): s = op
		case _: raise ValueError(e)
	return f"({s})" if prio2 < prio else s

def print_code(code: list[Insn]) -> str:
	from textwrap import indent
	s = ""
	for i, insn in enumerate(code):
		args = []
		for a in insn.args:
			match a:
				case int(v):
					args.append(print_term(v))
				case float(v):
					args.append(print_term(v))
				case str(v):
					args.append(print_term(v))
				case list(v):
					a = "".join([print_term(line) + "\n" for line in v])
					args.append("{\n%s}" % indent(a, "\t"))
				case AExpr(v): args.append(print_expr(v))
		s += f"{insn.name}({', '.join(args)})"
		if insn.body is not None:
			s += " " + print_code(insn.body)
		if insn.name in ["if", "elif"] and i+1 < len(code) and code[i+1].name in ["elif", "else"]:
			s += " "
		else:
			s += "\n"
	return "{\n%s}" % indent(s, "\t")

def parse_and_print(file: Path, insns: InsnTable):
	import sys
	print(file, file=sys.stderr, end="", flush=True)
	f = read.Reader(file.read_bytes())
	scp = parse_bin.parse_ys7_scp(f, insns)
	print('.', file=sys.stderr)
	for name, code in scp.functions.items():
		print(f"{file}:{name} {print_code(code)}")
		print()

insns_ys8 = insn_table("insn/ys8.txt")
for file in sorted(Path("/home/large/kiseki/ys8/script/").glob("*.bin")):
	parse_and_print(file, insns_ys8)

# insns_nayuta = insn_table("insn/nayuta.txt")
# for file in sorted(Path("/home/large/kiseki/nayuta/US/script/").glob("*.bin")):
# 	parse_and_print(file, insns_nayuta)
