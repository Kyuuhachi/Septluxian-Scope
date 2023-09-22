from __future__ import annotations
from textwrap import indent

from common import binops, Insn, Expr, Binop, Unop, Nilop, AExpr, Ys7Scp

def print_str(s: str) -> str:
	assert '\n' not in s
	assert '\r' not in s
	assert '\t' not in s
	return '"' + s.replace('"', '""') + '"'

def print_expr(e: Expr, prio: int = 1000) -> str:
	prio2 = 100
	match e:
		case int(e): r = str(e)
		case float(e): r = f"{e:f}"
		case str(e): r = print_str(e)
		case Binop(a, op, b):
			prio2 = binops[op]
			if op != ".": op = f" {op} "
			r = print_expr(a, prio2) + op + print_expr(b, prio2+1)
		case Unop(pre, a, suf): r = pre + print_expr(a, 0 if suf else 100) + suf
		case Nilop(op): r = op
		case _: raise ValueError(e)
	return f"({r})" if prio2 < prio else r

def print_code(code: list[Insn]) -> str:
	s = ""
	for i, insn in enumerate(code):
		args = []
		for a in insn.args:
			match a:
				case int(e): r = str(e)
				case float(e): r = f"{e:f}"
				case str(e): r = print_str(e)
				case list(v):
					a = "".join([print_str(line) + "\n" for line in v])
					r = "{\n%s}" % indent(a, "\t")
				case AExpr(v): r = print_expr(v)
			args.append(r)
		s += f"{insn.name}({', '.join(args)})"
		if insn.body is not None:
			s += " " + print_code(insn.body)
		if insn.name in ["if", "elif"] and i+1 < len(code) and code[i+1].name in ["elif", "else"]:
			s += " "
		else:
			s += "\n"
	return "{\n%s}" % indent(s, "\t")

def print_ys7_scp(scp: Ys7Scp) -> str:
	s = ""
	s += f"version {scp.version}\n"
	s += f"hash {print_str(scp.hash.hex().upper())}\n"

	for name, code in scp.functions.items():
		s += f"\nfunction {print_str(name)} {print_code(code)}\n"
	return s
