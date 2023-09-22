from __future__ import annotations
import typing as T
import dataclasses as dc
from pathlib import Path

binops = {
	"|": 1,
	"||": 1,
	"&": 3,
	"&&": 3,

	"!=": 4,
	"==": 4,
	"<": 4,
	">": 4,
	"<=": 4,
	">=": 4,

	"+": 5,
	"-": 5,

	"*": 6,
	"/": 6,
	"%": 6,

	".": 10,

	"expr_missing_op": 100,
}

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

@dc.dataclass
class Insn:
	name: str
	args: list[Arg] = dc.field(default_factory=list)
	body: list[Insn] | None = None

@dc.dataclass
class AExpr:
	expr: Expr

Arg: T.TypeAlias = int | float | str | AExpr | list[str]

@dc.dataclass
class Ys7Scp:
	version: int
	hash: bytes # length 8
	functions: dict[str, list[Insn]]

InsnTable: T.TypeAlias = dict[int, str]

def insn_table(path: str|Path) -> InsnTable:
	insns = {}
	n = 0
	for line in Path(path).open():
		match line.split("#")[0].split():
			case []: pass
			case ["-", skip]: n += int(skip)
			case [v]: insns[n] = v; n += 1
			case _: raise ValueError(line)
	return insns
