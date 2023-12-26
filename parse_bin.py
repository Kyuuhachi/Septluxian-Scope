from __future__ import annotations
import read

from common import insn_tables, InsnTable, Insn, Expr, Binop, Unop, Call, Index, AExpr, Ys7Scp

def parse_ys7_scp(data: bytes, insns: InsnTable | None = None) -> Ys7Scp:
	f = read.Reader(data)
	f.check(b"YS7_SCP")
	f.check_u32(0)
	version = f.u8()
	hash = f[8]
	nfuncs = f.u32()

	if insns is None:
		insns = insn_tables.get(version, {})

	functbl = []
	for _ in range(nfuncs):
		name = f[32].rstrip(b"\0").decode("cp932")
		length = f.u32()
		start = f.u32()
		functbl.append((name, start, length))

	ends = [start for _, start, _ in functbl[1:]] + [len(data)]
	functions = []
	for (name, start, length), end in zip(functbl, ends):
		if start+length != end:
			print(f"{name}: incorrect length {length}, should be {end - start}")
		functions.append((name, parse_func(data[start:end], insns, version)))

	return Ys7Scp(version, hash, functions)

def parse_func(data: bytes, insns: InsnTable, version: int) -> list[Insn]:
	f = read.Reader(data)
	code = parse_block(f, len(data), insns)
	assert not f.remaining
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

expr = {
	# - 1
	0x01: ('binop', "!="),
	0x02: ('unop',  "!"),
	0x03: ('binop', "*"),
	0x04: ('binop', "/"),
	0x05: ('binop', "%"),
	0x06: ('binop', "+"),
	0x07: ('binop', "-"),
	0x08: ('binop', ">>"),
	0x09: ('binop', ">="),
	0x0A: ('binop', ">"),
	0x0B: ('binop', "<<"),
	0x0C: ('binop', "<="),
	0x0D: ('binop', "<"),
	0x0E: ('binop', "=="),
	# - 1
	0x10: ('binop', "&&"),
	0x11: ('binop', "&"),
	0x12: ('binop', "||"),
	0x13: ('binop', "|"),
	0x14: ('unop',  "~"),
	0x15: ('binop', "^"),
	# - 4
	0x1A: 'int',
	0x1B: 'float',
	0x1C: 'str',
	0x1D: 'break',
	# - 1
	0x1F: ('index', "FLAG"),
	0x20: ('index', "WORK"),
	0x21: ('index', "CHRWORK"),
	0x22: ('index', "ITEMWORK"),
	0x23: ('index', "ALLITEMWORK"),
	0x24: ('index', "TEMP"),
	0x25: ('func', "abs", 1),
	0x26: ('func', "INT", 1),
	0x27: ('func', "FLOAT", 1),
	0x28: ('index', "ACTIONFLAG"),
	0x29: ('func', "rand", 0),
	0x2A: ('func', "randf", 0),
	0x2B: ('func', "SETFLAG_TIME"),
	0x2C: 'chr',
	0x2D: ('binop', "."),
	0x2E: ('func', "GetPlayerType", 1),
	0x2F: ('func', "GetMoveSpd", 1),
	0x30: ('func', "GetNo", 1),
	0x31: ('func', "IsChange", 1),
	0x32: ('func', "IsKey", 1),
	0x33: ('func', "IsMoving", 1),
	0x34: ('func', "IsPlayer", 1),
	0x35: ('func', "IsPartyIn", 1),
	0x36: ('func', "IsGuestOk", 1),
	0x37: ('func', "NextAnimation", 1),
	0x38: ('func', "PrevAnimation", 1),
	0x39: ('func', "IsWalking", 1),
	0x3A: ('func', "IsEquip", 1),
	0x3B: ('func', "GetSpdRatio", 1),
	0x3C: ('func', "CheckStatus"),
	0x3D: ('func', "IsMagicItem", 1),
	0x3E: ('func', "IsJumpKey", 1),
	0x3F: ('func', "IsStepKey", 1),
	0x40: ('func', "IsAnimeEnd", 1),
	0x41: ('func', "GetProcess"),
	0x42: ('unop', "-"),
	0x43: ('func', "sin", 1),
	0x44: ('func', "cos", 1),
	0x45: ('func', "sqrt", 1),
	0x46: ('func', "IsDefeatEnemy"),
	0x47: ('func', "IsTurning", 1),
	0x48: ('index', "GOTITEMWORK"),
}

def parse_expr(f: read.Reader) -> Expr:
	ops = []
	def pop() -> Expr:
		return ops.pop() if ops else Call("expr_missing", [])
	while True:
		opcode = f.u16()
		match expr.get(opcode):
			case "break":
				break
			case "int":
				ops.append(f.i32())
			case "float":
				ops.append(f.f32())
			case "chr":
				ops.append(f[f.u32()].decode("cp932"))
			case "unop", op:
				a = pop()
				ops.append(Unop(op, a))
			case "binop", op:
				b = pop()
				a = pop()
				ops.append(Binop(a, op, b))
			case "index", name:
				a = pop()
				ops.append(Index(name, a))
			case "func", name, n:
				args = [pop() for _ in range(n)][::-1]
				ops.append(Call(name, args))
			case desc:
				raise ValueError(hex(opcode), desc)
	assert not f.remaining
	while len(ops) > 1:
		return Call("expr_missing", ops)
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
