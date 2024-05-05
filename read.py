from __future__ import annotations
import typing as T

import dataclasses as dc
import struct

__all__ = ["Reader", "dump"]

A = T.TypeVar("A")
R = T.TypeVar("R", bound="Reader")

@dc.dataclass(repr=False)
class Reader:
	data: bytes
	pos: int = 0

	def __repr__(self) -> str:
		return f"{type(self).__name__}({len(self)})"
	__str__ = __repr__

	def __len__(self) -> int:
		return len(self.data)

	def __getitem__(self, n: int) -> bytes:
		v = self.data[self.pos:self.pos+n]
		if len(v) != n:
			raise ValueError(f"At 0x{self.pos:04x}: tried to read {n} bytes, but only {len(v)} were available")
		self.pos += n
		return v

	def __iter__(self) -> T.Iterator[int]:
		end = len(self.data)
		while self.pos < end:
			yield self.byte()

	def byte(self) -> int:
		v = self.data[self.pos]
		self.pos += 1
		return v

	def zstr(self) -> bytes:
		l = self.data[self.pos:].find(0)
		s = self.data[self.pos:self.pos+l]
		self.pos += l + 1
		return s

	@property
	def remaining(self) -> int:
		return len(self.data) - self.pos

	def at(self: R, pos: int|None = None) -> R:
		return dc.replace(self, pos = pos if pos is not None else self.pos)

	def sub(self: R, n: int) -> R:
		data = self.data[self.pos:self.pos+n]
		self.pos += n
		return dc.replace(self, pos = 0, data = data)

	def unpack(self, spec: str) -> tuple[T.Any, ...]:
		return struct.unpack(spec, self[struct.calcsize(spec)])

	def u8 (self) -> int: return self.unpack("B")[0]
	def u16(self) -> int: return self.unpack("H")[0]
	def u32(self) -> int: return self.unpack("I")[0]
	def u64(self) -> int: return self.unpack("Q")[0]

	def i8 (self) -> int: return self.unpack("b")[0]
	def i16(self) -> int: return self.unpack("h")[0]
	def i32(self) -> int: return self.unpack("i")[0]
	def i64(self) -> int: return self.unpack("q")[0]

	def f32(self) -> float:
		f = self.unpack("f")[0]
		return float(f"{f:f}")
	def f64(self) -> float: return self.unpack("d")[0]

	def check(self, data: bytes): _check(self, lambda: self[len(data)], data)

	def check_u8 (self, v: int): _check(self, self.u8,  v)
	def check_u16(self, v: int): _check(self, self.u16, v)
	def check_u32(self, v: int): _check(self, self.u32, v)
	def check_u64(self, v: int): _check(self, self.u64, v)

	def check_i8 (self, v: int): _check(self, self.i8,  v)
	def check_i16(self, v: int): _check(self, self.i16, v)
	def check_i32(self, v: int): _check(self, self.i32, v)
	def check_i64(self, v: int): _check(self, self.i64, v)

def _check(f: Reader, func: T.Callable[[], A], v: A):
	pos = f.pos
	w = func()
	if w != v:
		f.pos = pos
		raise ValueError(f"at {pos:X}: got {w}, expected {v}")

def dump(data: bytes, width: int = 48) -> str:
	import re
	escape = re.compile("[\x00-\x1F\x7F\x80-\x9F�]+")
	s = ""
	for a in range(0, len(data), width):
		pfmt = ""
		for b in range(a, a+width):
			if b >= len(data): s += "   "; continue
			b = data[b]

			if   0x00 == b       : fmt = "\x1B[2m"
			elif 0x20 <= b < 0x7F: fmt = "\x1B[38;5;10m"
			elif 0xFF == b       : fmt = "\x1B[38;5;9m"
			else:                  fmt = ""
			if fmt != pfmt:
				pfmt = fmt
				s += "\x1B[m" + fmt

			s += f"{b:02X} "

		s += "\x1B[m"
		text = data[a:a+width].decode("cp932", errors="replace")
		text = escape.sub(lambda a: "\x1B[2m" + "·"*len(a.group()) + "\x1B[m", text)
		s += "▏" + text + "\n"
	return s

class Label: pass

@dc.dataclass(repr=False)
class Writer:
	data: bytearray
	thunks: dict[int, tuple[int, T.Callable[[Writer], bytes]]]
	labels: dict[Label, int]

	def __init__(self, data: bytes = b""):
		self.data = bytearray(data)
		self.thunks = {}
		self.labels = {}

	def __repr__(self) -> str:
		return f"{type(self).__name__}({len(self)})"
	__str__ = __repr__

	def __len__(self) -> int:
		return len(self.data)

	def __bytes__(self) -> bytes:
		for pos, (n, thunk) in self.thunks.items():
			b = thunk(self)
			assert len(b) == n, (b, n)
			self.data[pos:pos+n] = b
		self.thunks.clear()
		return bytes(self.data)

	def write(self, v: bytes) -> None:
		self.data += v

	def __iadd__(self, v: Writer) -> Writer:
		self.thunks.update((k + len(self.data), v) for k, v in v.thunks.items())
		self.labels.update((k, v + len(self.data)) for k, v in v.labels.items())
		self.data += v.data
		return self

	def __add__(self, v: Writer) -> Writer:
		w = Writer()
		w += self
		w += v
		return w

	def __getitem__(self, label: Label) -> int:
		return self.labels[label]

	def place(self, label: Label) -> Label:
		self.labels[label] = len(self)
		return label

	def pack(self, spec: str, *args: T.Any) -> None:
		self.write(struct.pack(spec, *args))

	def delay(self, n: int, thunk: T.Callable[[Writer], bytes]) -> None:
		self.thunks[len(self.data)] = (n, thunk)
		self.write(bytes(n))

	def diff(self, width: int, a: Label, b: Label) -> None:
		self.delay(width, lambda r: int.to_bytes(r[b] - r[a], width, "little", signed = True))

	def u8 (self, v: int) -> None: self.pack("B", v)
	def u16(self, v: int) -> None: self.pack("H", v)
	def u32(self, v: int) -> None: self.pack("I", v)
	def u64(self, v: int) -> None: self.pack("Q", v)

	def i8 (self, v: int) -> None: self.pack("b", v)
	def i16(self, v: int) -> None: self.pack("h", v)
	def i32(self, v: int) -> None: self.pack("i", v)
	def i64(self, v: int) -> None: self.pack("q", v)

	def f32(self, v: float) -> None: self.pack("f", v)
	def f64(self, v: float) -> None: self.pack("d", v)
