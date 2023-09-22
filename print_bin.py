from __future__ import annotations
from copy import deepcopy
import typing as T
import dataclasses as dc
import struct

from common import insn_tables, InsnTable, Insn, Expr, Binop, Unop, Call, Index, AExpr, Ys7Scp
import parse_bin

RevInsnTable: T.TypeAlias = dict[str, int]

def write_ys7_scp(scp: Ys7Scp, insns: InsnTable | None = None) -> bytes:
	f = Writer()
	f.write(b"YS7_SCP")
	f.u32(0)
	f.u8(scp.version)
	assert len(scp.hash) == 8
	f.write(scp.hash)
	f.u32(len(scp.functions))

	if insns is None:
		insns = insn_tables.get(scp.version, {})

	_insns = { v: k for k, v in insns.items() }

	datastart = len(f) + 40 * len(scp.functions)

	data = bytearray()
	for name, code in scp.functions:
		name = name.encode("cp932").ljust(32, b"\0")
		assert len(name) == 32
		funcdata = write_func(code, _insns, scp.version)
		f.write(name)
		f.u32(len(funcdata))
		f.u32(datastart + len(data))
		data.extend(funcdata)

	return bytes(f.data + data)

def write_func(code: list[Insn], insns: RevInsnTable, version: int) -> bytes:
	code = deepcopy(code)
	insert_tail(code, "return")
	if version == 6:
		mangle_return(code)
	data, refs = write_block(code, insns)
	assert not refs
	return data

def write_block(code: list[Insn], insns: RevInsnTable) -> tuple[bytes, list[int]]:
	data, refs = bytearray(), []
	for stmt in code:
		pos = len(data)
		dat, ref = write_stmt(stmt, insns)
		data += dat
		refs += [pos + ref for ref in ref]
	return data, refs

def write_stmt(stmt: Insn, insns: RevInsnTable) -> tuple[bytes, list[int]]:
	match stmt.name:
		case "Message": stmt.args[-1] = "\\n".join(stmt.args[-1])
		case "OpenMessage": stmt.args[-1] = "\\n".join(stmt.args[-1])
		case "Message2": stmt.args[3:] = stmt.args[3]
		case "YesNoMenu": stmt.args[1] = "\\n".join(stmt.args[1])
		case "GetItemMessageExPlus": stmt.args[3] = "\\n".join(stmt.args[3])
		case "NoiSystemMessage": stmt.args[-1] = "\r\n".join(stmt.args[-1])

	if stmt.name == "break" and not stmt.args:
		stmt.args.append(0)
		d = write_insn(stmt, insns)
		return d, [len(d)]

	if stmt.name == "while":
		stmt.args.append(0)
		body, refs = write_block(stmt.body, insns)
		head_len = len(write_insn(stmt, insns))
		body += write_insn(Insn("goto", [0]), insns)
		struct.pack_into("i", body, len(body)-4, -(head_len + len(body)))
		stmt.args[-1] = len(body)
	elif stmt.body is not None:
		body, refs = write_block(stmt.body, insns)
		if stmt.name != "switch":
			stmt.args.append(len(body))
	else:
		body, refs = b"", []

	if stmt.name in { "while", "switch" }:
		body = update_break(body, refs)

	head = write_insn(stmt, insns)
	return head + body, [len(head) + ref for ref in refs]

def write_insn(insn: Insn, insns: RevInsnTable) -> bytes:
	if insn.name.startswith("op_"):
		op = int(insn.name[3:], 16)
	elif insn.name == "while":
		op = insns["if"]
	else:
		op = insns[insn.name]
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
				f.write(g.data)
				f.write(bs)

			case _: raise ValueError(arg)

	return f.data

binop = { v: k for k, v in parse_bin.binop.items() }
unop  = { v: k for k, v in parse_bin.unop.items() }
index = { v: k for k, v in parse_bin.index.items() }
func  = { v: k for k, v in parse_bin.func.items() }

def write_expr(expr: Expr) -> bytes:
	f = Writer()
	def w(expr: Expr):
		match expr:
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
				f.u16(binop[op])

			case Unop(op, a):
				w(a)
				f.u16(unop[op])

			case Index(name, e):
				w(e)
				f.u16(index[name])

			case Call(target, name, args):
				if target is not None:
					w(target)
				for arg in args:
					w(arg)

				if name != "expr_missing":
					f.u16(func[name])

			case _:
				raise ValueError(expr)
	w(expr)
	f.u16(0x1D)
	return f.data

def update_break(data: bytes, refs: list[int]) -> bytes:
	data = bytearray(data)
	for ref in refs:
		struct.pack_into("I", data, ref-4, len(data)-ref)
	refs.clear()
	return data

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

@dc.dataclass(repr=False)
class Writer:
	data: bytearray = dc.field(default_factory=bytearray)

	def __repr__(self) -> str:
		return f"{type(self).__name__}({len(self)})"
	__str__ = __repr__

	def __len__(self) -> int:
		return len(self.data)

	def write(self, data: bytes):
		self.data.extend(data)

	def pack(self, spec: str, *args: T.Any):
		self.write(struct.pack(spec, *args))

	def u8 (self, v: int): return self.pack("B", v)
	def u16(self, v: int): return self.pack("H", v)
	def u32(self, v: int): return self.pack("I", v)
	def u64(self, v: int): return self.pack("Q", v)

	def i8 (self, v: int): return self.pack("b", v)
	def i16(self, v: int): return self.pack("h", v)
	def i32(self, v: int): return self.pack("i", v)
	def i64(self, v: int): return self.pack("q", v)

	def f32(self, v: float): return self.pack("f", v)
	def f64(self, v: float): return self.pack("d", v)
