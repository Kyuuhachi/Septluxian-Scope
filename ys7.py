from __future__ import annotations
import typing as T
import read
import dataclasses as dc
from pathlib import Path

insns = {}
n = 0
for line in open("ys7_scp.txt"):
	match line.split("#")[0].split():
		case []: pass
		case ["-", skip]: n += int(skip)
		case [v]: insns[n] = v; n += 1
		case _: raise ValueError(line)

@dc.dataclass
class Insn:
	name: str
	args: list[int | float | str | AExpr | list[str]] = dc.field(default_factory=list)
	body: list[Insn] | None = None

@dc.dataclass
class Binop:
	a: Expr
	op: str
	b: Expr

@dc.dataclass
class Unop:
	pre: str
	a: Expr
	suf: str

@dc.dataclass
class Nilop:
	op: str

Expr: T.TypeAlias = int | str | float | Binop | Unop | Nilop

def term(t: int | float | str) -> str:
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
			import json
			return json.dumps(t, ensure_ascii=False)

def format_expr(e: Expr, prio: int = 1000) -> str:
	prio2 = 100
	match e:
		case int(e): s = term(e)
		case float(e): s = term(e)
		case str(e): s = e
		case Binop(a, op, b):
			prio2 = binops[op]
			if op != ".": op = f" {op} "
			s = format_expr(a, prio2) + op + format_expr(b, prio2+1)
		case Unop(pre, a, suf): s = pre + format_expr(a, 0 if suf else 100) + suf
		case Nilop(op): s = op
		case _: raise ValueError(e)
	return f"({s})" if prio2 < prio else s

@dc.dataclass
class AExpr:
	expr: Expr

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

def parse_expr(f: read.Reader) -> Expr:
	ops = []
	def pop() -> Expr:
		return ops.pop() if ops else Nilop("expr_missing")
	def unop(pre: str, suf: str):
		a = pop()
		ops.append(Unop(pre, a, suf))
	def binop(op: str):
		b = pop()
		a = pop()
		ops.append(Binop(a, op, b))
	while True:
		match f.u16():
			case 0x01: binop("!=")
			case 0x02: unop("!", "")
			case 0x03: binop("*")
			case 0x04: binop("/")
			case 0x05: binop("%")
			case 0x06: binop("+")
			case 0x07: binop("-")
			case 0x09: binop(">")
			case 0x0A: binop(">=")
			case 0x0C: binop("<=")
			case 0x0D: binop("<")
			case 0x0E: binop("==")
			case 0x10: binop("&&")
			case 0x11: binop("&")
			case 0x12: binop("||")
			case 0x13: binop("|")
			case 0x1A: ops.append(f.i32())
			case 0x1B: ops.append(f.f32())
			case 0x1D: break
			case 0x1F: unop("FLAG[", "]")
			case 0x20: unop("WORK[", "]")
			case 0x21: unop("CHRWORK[", "]")
			case 0x22: unop("ITEMWORK[", "]")
			case 0x23: unop("ALLITEMWORK[", "]")
			case 0x29: ops.append(Nilop("rand()"))
			case 0x2C: ops.append(f[f.u32()].decode("cp932"))
			case 0x2D: binop(".")
			case 0x35: unop("IsPartyIn(", ")")
			case 0x3D: unop("IsMagicItem(", ")")
			case 0x42: unop("-", "")
			case 0x47: unop("", ".IsTurning()")
			case 0x48: unop("GOTITEMWORK[", "]")
			case op: ops.append(Nilop(f"expr_{op:X}"))
	assert not f.remaining
	while len(ops) > 1:
		binop("expr_missing_op")
	return pop()

def parse_insn(f: read.Reader) -> Insn:
	op = f.u16()
	name = insns.get(op, f"op_{op:04X}")
	args = []
	while f.remaining:
		match f.u16():
			case 0x82DD:
				args.append(f.i32())
			case 0x82DE:
				args.append(f.f32())
			case 0x82DF:
				args.append(f[f.u32()].decode("cp932"))
			case 0x82E0:
				args.append(AExpr(parse_expr(f.sub(f.u32()))))
			case 0x2020:
				nlines, nbytes = f.u32(), f.u32()
				starts = [f.u32() for _ in range(nlines)]
				text = f[nbytes]
				val = []
				for a, b in zip(starts, starts[1:] + [nbytes]):
					s = text[a:b].decode("cp932")
					assert s.endswith("\x01")
					val.append(s[:-1])
				args.append(val)

			case op:
				f.pos -= 2
				break
	return Insn(name, args)

def parse_stmt(f: read.Reader) -> Insn:
	pos = f.pos
	stmt = parse_insn(f)

	if stmt.name in { "if", "elif", "else", "case", "ExecuteCmd" }:
		stmt.body = parse_block(f.sub(stmt.args.pop()))

	if stmt.name == "if" and stmt.body[-1].name == "goto":
		assert stmt.body[-1] == Insn("goto", [pos - f.pos])
		stmt.name = "while"
		stmt.body.pop()

	if stmt.name == "switch":
		body = []
		end = set()
		while True:
			pos = f.pos
			insn = parse_stmt(f)
			body.append(insn)
			if insn.name != "case":
				break
			if insn.body[-1].name == "break":
				end.add(f.pos + insn.body[-1].args.pop())
			else:
				raise ValueError(insn)
		end.add(f.pos)
		assert len(end) == 1, end

		stmt.body = body

	return stmt

def parse_block(f: read.Reader) -> list[Insn]:
	out = []
	while f.remaining:
		out.append(parse_stmt(f))
	return out

tails = {
	"if": "endif",
	"elif": "endif",
	"else": "endif",
	"while": "endif",
	"switch": "endif",
	"ExecuteCmd": "return",
}

def print_code(code: list[Insn], indent: str = ""):
	print(" {")
	for insn in code:
		args = []
		for a in insn.args:
			match a:
				case int(a): args.append(term(a))
				case float(a): args.append(term(a))
				case str(a): args.append(term(a))
				case list(a): args.append(repr(a))
				case AExpr(a): args.append(format_expr(a))
		print(indent + f"\t{insn.name}({', '.join(args)})", end = "")
		if insn.body is not None:
			print_code(insn.body, indent + "\t")
		print()
	print(indent + "}", end = "")

def restore_return(code: list[Insn]):
	if code[-1].body is not None:
		if code[-1].name != "while":
			assert code[-1].body[-1] == Insn("return")
			code[-1].body.pop()
		code[-1].body.append(Insn("endif"))
		code.append(Insn("return"))

def strip_tail(code: list[Insn], tail: str | None):
	if tail is not None:
		assert code[-1] == Insn(tail)
		code.pop()
	for insn in code:
		if insn.body is not None:
			strip_tail(insn.body, tails.get(insn.name))

def parse_ys7_scp(f: read.Reader):
	f.check(b"YS7_SCP")
	f.check_u32(0)
	unk = f[9]

	for _ in range(f.u32()):
		name = f[32].rstrip(b"\0").decode("cp932")
		length = f.u32()
		start = f.u32()
		print(f"{file}:{name}", end="")
		code = parse_block(f.at(start).sub(length))
		restore_return(code)
		strip_tail(code, "return")
		print_code(code)
		print()
		print()

file = Path("/home/large/kiseki/ys8/script/test.bin")
parse_ys7_scp(read.Reader(file.read_bytes()))
# for file in sorted(Path("/home/large/kiseki/ys8/script/").glob("*.bin")):
# 	parse_ys7_scp(read.Reader(file.read_bytes()))
# for file in sorted(Path("/home/large/kiseki/nayuta/US/script/").glob("*.bin")):
# 	parse_ys7_scp(read.Reader(file.read_bytes()))
