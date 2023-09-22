from __future__ import annotations
import read

from common import InsnTable, Insn, Expr, Binop, Unop, Call, Index, AExpr, Ys7Scp

def parse_ys7_scp(f: read.Reader, insns: InsnTable) -> Ys7Scp:
	f.check(b"YS7_SCP")
	f.check_u32(0)
	version = f.u8()
	hash = f[8]
	nfuncs = f.u32()

	datastart0 = f.pos + 40 * nfuncs
	datastart = datastart0

	functions = {}
	for _ in range(nfuncs):
		name = f[32].rstrip(b"\0").decode("cp932")
		length = f.u32()
		start = f.u32()
		assert start == datastart
		assert name not in functions, name
		functions[name] = parse_func(f.at(start), length, insns, version)
		datastart += length

	assert f.pos == datastart0

	return Ys7Scp(version, hash, functions)

def parse_func(f: read.Reader, length: int, insns: InsnTable, version: int) -> list[Insn]:
	code = parse_block(f, length, insns)
	if version == 6:
		restore_return(code)
	strip_tail(code, "return")
	return code

def parse_block(f: read.Reader, length: int, insns: InsnTable) -> list[Insn]:
	out = []
	end = f.pos + length
	while f.pos < end:
		out.append(parse_stmt(f, insns))
	assert f.pos == end
	return out

def parse_stmt(f: read.Reader, insns: InsnTable) -> Insn:
	pos = f.pos
	stmt = parse_insn(f, insns)
	stmt.pos = f.pos

	if stmt.name in { "break", "goto" }:
		stmt.args[-1] += stmt.pos

	if stmt.name in { "if", "elif", "else", "case", "default", "ExecuteCmd" }:
		stmt.body = parse_block(f, stmt.args.pop(), insns)

	if stmt.name == "if" and stmt.body[-1].name == "goto":
		assert stmt.body[-1] == Insn("goto", [pos])
		stmt.name = "while"
		stmt.body.pop()
		fix_break(stmt.body, f.pos)

	if stmt.name == "switch":
		stmt.body = []
		while True:
			pos = f.pos
			insn = parse_stmt(f, insns)
			stmt.body.append(insn)
			if insn.name in {"return", "endif"}:
				break
			assert insn.name in {"case", "default"}, insn
		fix_break(stmt.body, f.pos)

	match stmt.name:
		case "Message": stmt.args[-1] = stmt.args[-1].split("\\n")
		case "OpenMessage": stmt.args[-1] = stmt.args[-1].split("\\n")
		case "Message2": stmt.args[3:] = [stmt.args[3:]]
		case "YesNoMenu": stmt.args[1] = stmt.args[1].split("\\n")
		case "GetItemMessageExPlus": stmt.args[3] = stmt.args[3].split("\\n")
		case "NoiSystemMessage": stmt.args[-1] = stmt.args[-1].split("\r\n")

	return stmt

def parse_insn(f: read.Reader, insns: InsnTable) -> Insn:
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

binop = {
	0x01: "!=",
	0x03: "*",
	0x04: "/",
	0x05: "%",
	0x06: "+",
	0x07: "-",
	0x09: ">",
	0x0A: ">=",
	0x0C: "<=",
	0x0D: "<",
	0x0E: "==",
	0x10: "&&",
	0x11: "&",
	0x12: "||",
	0x13: "|",
	0x2D: ".",
}

unop = {
	0x02: "!",
	0x42: "-",
}

index = {
	0x1F: "FLAG",
	0x20: "WORK",
	0x21: "CHRWORK",
	0x22: "ITEMWORK",
	0x23: "ALLITEMWORK",
	0x48: "GOTITEMWORK",
}

func = {
	0x29: "rand",
	0x35: "IsPartyIn",
	0x3D: "IsMagicItem",
	0x47: "IsTurning",
}

def parse_expr(f: read.Reader) -> Expr:
	ops = []
	def pop() -> Expr:
		return ops.pop() if ops else Call(None, "expr_missing", [])
	def binop(op: str) -> Binop:
		b = pop()
		a = pop()
		return Binop(a, op, b)
	while True:
		match f.u16():
			case 0x01: ops.append(binop("!="))
			case 0x02: ops.append(Unop("!", pop()))
			case 0x03: ops.append(binop("*"))
			case 0x04: ops.append(binop("/"))
			case 0x05: ops.append(binop("%"))
			case 0x06: ops.append(binop("+"))
			case 0x07: ops.append(binop("-"))
			case 0x09: ops.append(binop(">"))
			case 0x0A: ops.append(binop(">="))
			case 0x0C: ops.append(binop("<="))
			case 0x0D: ops.append(binop("<"))
			case 0x0E: ops.append(binop("=="))
			case 0x10: ops.append(binop("&&"))
			case 0x11: ops.append(binop("&"))
			case 0x12: ops.append(binop("||"))
			case 0x13: ops.append(binop("|"))
			case 0x1A: ops.append(f.i32())
			case 0x1B: ops.append(f.f32())
			case 0x1D: break
			case 0x1F: ops.append(Index("FLAG", pop()))
			case 0x20: ops.append(Index("WORK", pop()))
			case 0x21: ops.append(Index("CHRWORK", pop()))
			case 0x22: ops.append(Index("ITEMWORK", pop()))
			case 0x23: ops.append(Index("ALLITEMWORK", pop()))
			case 0x29: ops.append(Call(None, "rand", []))
			case 0x2C: ops.append(f[f.u32()].decode("cp932"))
			case 0x2D: ops.append(binop("."))
			case 0x35: ops.append(Call(None, "IsPartyIn", [pop()]))
			case 0x3D: ops.append(Call(None, "IsMagicItem", [pop()]))
			case 0x42: ops.append(Unop("-", pop()))
			case 0x47: ops.append(Call(pop(), "IsTurning", []))
			case 0x48: ops.append(Index("GOTITEMWORK", pop()))
			case op: raise ValueError(hex(op))
	assert not f.remaining
	while len(ops) > 1:
		return Call(None, "expr_missing", ops)
	return pop()


def fix_break(code: list[Insn], end: int):
	for i in code:
		if i.name == "break":
			if i.args == [end]:
				i.args = []
			else:
				# I don't know what these mean. Breaking from a non-loop?
				i.args[0] -= i.pos
		if i.body is not None and i.name not in { "switch", "while" }:
			fix_break(i.body, end)

def restore_return(code: list[Insn]):
	if code[-1].body is not None:
		if code[-1].name != "while":
			assert code[-1].body[-1] == Insn("return")
			code[-1].body.pop()
		code[-1].body.append(Insn("endif"))
		code.append(Insn("return"))

tails = {
	"if": "endif",
	"elif": "endif",
	"else": "endif",
	"while": "endif",
	"switch": "endif",
	"ExecuteCmd": "return",
}

def strip_tail(code: list[Insn], tail: str | None):
	if tail is not None:
		assert code[-1] == Insn(tail)
		code.pop()
	for insn in code:
		if insn.body is not None:
			strip_tail(insn.body, tails.get(insn.name))
