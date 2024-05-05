from __future__ import annotations
from copy import deepcopy
import typing as T

from common import insn_tables, InsnTable, Insn, Expr, Binop, Unop, Call, Index, AExpr, Ys7Scp, Arg
from read import Writer, Label
import parse_bin

RevInsnTable: T.TypeAlias = dict[str, int]

def write_ys7_scp(scp: Ys7Scp, insns: InsnTable | None = None) -> bytes:
	if insns is None:
		insns = insn_tables.get(scp.version, {})
	_insns = { v: k for k, v in insns.items() }

	f = Writer()
	start = f.place(Label())
	f.write(b"YS7_SCP")
	f.u32(0)
	f.u8(scp.version)
	assert len(scp.hash) == 8
	f.write(scp.hash)
	f.u32(len(scp.functions))

	data = Writer()
	for name, code in scp.functions:
		name = name.encode("cp932").ljust(32, b"\0")
		assert len(name) == 32
		funcdata = write_func(code, _insns, scp.version)
		f.write(name)
		f.u32(len(funcdata))
		f.diff(4, start, data.place(Label()))
		data.write(funcdata)

	return bytes(f + data)

def write_func(code: list[Insn], insns: RevInsnTable, version: int) -> bytes:
	code = deepcopy(code)
	insert_tail(code, "return")
	if version >= 6:
		mangle_return(code)
	return bytes(write_block(code, insns, None))

def write_block(code: list[Insn], insns: RevInsnTable, brk: Label | None) -> Writer:
	out = Writer()
	for stmt in code:
		out += write_stmt(stmt, insns, brk)
	return out

def write_stmt(stmt: Insn, insns: RevInsnTable, brk: Label | None) -> Writer:
	match stmt.name:
		case "Message": stmt.args[-1] = "\\n".join(stmt.args[-1])
		case "OpenMessage": stmt.args[-1] = "\\n".join(stmt.args[-1])
		case "Message2": stmt.args[3:] = stmt.args[3]
		case "YesNoMenu": stmt.args[1] = "\\n".join(stmt.args[1])
		case "GetItemMessageExPlus": stmt.args[3] = "\\n".join(stmt.args[3])
		case "NoiSystemMessage": stmt.args[-1] = "\r\n".join(stmt.args[-1])

	f = Writer()
	end = Label()

	if stmt.name == "break":
		assert not stmt.args
		assert brk is not None
		f += write_insn(stmt, insns)
		f += write_label(brk)

	elif not stmt.body:
		f += write_insn(stmt, insns)

	elif stmt.name in { "if", "elif", "else", "case", "default", "ExecuteCmd" }:
		f += write_insn(stmt, insns)
		f += write_label(end)
		f += write_block(stmt.body, insns, brk)

	elif stmt.name == "while":
		stmt.name = "if"
		start = f.place(Label())
		f += write_insn(stmt, insns)
		f += write_label(end)
		f += write_block(stmt.body, insns, end)
		f += write_insn(Insn("goto", []), insns)
		f += write_label(start)

	elif stmt.name == "switch":
		f += write_insn(stmt, insns)
		f += write_block(stmt.body, insns, end)

	else:
		raise ValueError(stmt)

	f.place(end)
	return f

def write_insn(insn: Insn, insns: RevInsnTable) -> Writer:
	op = int(insn.name[3:], 16) if insn.name.startswith("op_") else insns[insn.name]
	f = Writer()
	f.u16(op)
	for arg in insn.args:
		match arg:
			case int(v):
				f.u16(0x82DD)
				f.i32(v)

			case float(v):
				f.u16(0x82DE)
				f.f32(v)

			case str(v):
				v = v.encode("cp932")
				f.u16(0x82DF)
				f.u32(len(v))
				f.write(v)

			case AExpr(v):
				bs = write_expr(v)
				f.u16(0x82E0)
				f.u32(len(bs))
				f.write(bs)

			case list(v):
				g = Writer()
				bs = bytearray()
				for line in v:
					line = (line + "\x01").encode("cp932")
					g.u32(len(bs))
					bs.extend(line)

				f.u16(0x2020)
				f.u32(len(v))
				f.u32(len(bs))
				f.write(bytes(g))
				f.write(bs)

			case _: raise ValueError(arg)

	return f

def write_label(label: Label) -> Writer:
	f = Writer()
	pos = Label()
	f.u16(0x82DD)
	f.diff(4, pos, label)
	f.place(pos)
	return f

expr = { v: k for k, v in parse_bin.expr.items() }

def write_expr(e: Expr) -> bytes:
	f = Writer()
	def w(e: Expr):
		match e:
			case int(v):
				f.u16(0x1A)
				f.i32(v)

			case float(v):
				f.u16(0x1B)
				f.f32(v)

			case str(v):
				v = v.encode("cp932")
				f.u16(0x2C)
				f.u32(len(v))
				f.write(v)

			case Binop(a, op, b):
				w(a)
				w(b)
				f.u16(expr["binop", op])

			case Unop(op, a):
				w(a)
				f.u16(expr["unop", op])

			case Index(name, e):
				w(e)
				f.u16(expr["index", name])

			case Call(name, args):
				for arg in args:
					w(arg)

				if name != "expr_missing":
					f.u16(expr["func", name, len(args)])

			case _:
				raise ValueError(e)
	w(e)
	f.u16(0x1D)
	return f.data

def mangle_return(code: list[Insn]):
	if len(code) >= 2 and code[-2].body is not None and code[-2].body[-1] == Insn("endif"):
		code[-2].body.pop()
		if code[-2].name != "while":
			code[-2].body.append(Insn("return"))
		code.pop()

def insert_tail(code: list[Insn], tail: str | None):
	if tail is not None:
		code.append(Insn(tail))
	for insn in code:
		if insn.body is not None:
			insert_tail(insn.body, parse_bin.tails.get(insn.name))
