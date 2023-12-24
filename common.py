from __future__ import annotations
import typing as T
import dataclasses as dc
from pathlib import Path

@dc.dataclass
class Binop:
	a: Expr
	op: str
	b: Expr

@dc.dataclass
class Unop:
	op: str
	a: Expr

@dc.dataclass
class Call:
	name: str
	args: list[Expr]

@dc.dataclass
class Index:
	name: str
	body: Expr

Expr: T.TypeAlias = int | str | float | Binop | Unop | Call | Index

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
	functions: list[tuple[str, list[Insn]]]

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

NAYUTA = insn_table(Path(__file__).parent / "insn/nayuta.txt")
YS7 = insn_table(Path(__file__).parent / "insn/ys7.txt")
YS8 = insn_table(Path(__file__).parent / "insn/ys8.txt")

named_tables = {
	"nayuta": NAYUTA,
	"ys7": YS7,
	"ys8": YS8,
}

insn_tables = {
	2: NAYUTA,
	6: YS8,
}

A = T.TypeVar("A")
def diff(a: A, b: A):
	if a != b:
		import pprint, difflib
		text1 = pprint.pformat(a).splitlines(keepends=True)
		text2 = pprint.pformat(b).splitlines(keepends=True)
		for line in difflib.Differ().compare(text1, text2):
			match line[0]:
				case " ": pass
				case "-": print("\x1B[31m" + line + "\x1B[m", end="")
				case "+": print("\x1B[32m" + line + "\x1B[m", end="")
				case "?": print(line, end="")
				case _: raise ValueError(line)
		raise AssertionError
