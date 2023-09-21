import read
import dataclasses as dc
from pathlib import Path

insns = {}
for line in open("ys7_scp.txt"):
	match line.split("#")[0].split():
		case []: pass
		case [k, v]: insns[int(k, 16)] = v
		case _: raise ValueError(line)

def parse_expr(f: read.Reader):
	ops = []
	while True:
		op = f.u16()
		match op:
			case 1: ops.append("!=")
			case 5: ops.append("%")
			case 6: ops.append("+")
			case 9: ops.append(">")
			case 10: ops.append(">=")
			case 12: ops.append("<=")
			case 13: ops.append("<")
			case 14: ops.append("==")
			case 16: ops.append("&&")
			case 17: ops.append("&")
			case 18: ops.append("||")
			case 26: ops.append(f.u32())
			case 27: ops.append(f.f32())
			case 29: break
			case 31: ops.append("FLAG")
			case 32: ops.append("WORK")
			case 35: ops.append("ALLITEMWORK")
			case 41: ops.append("rand()")
			case 53: ops.append("IsPartyIn")
			case 66: ops.append("0-")
			case _:
				print(op)
				read.dump(f.data)
				ops.append("-error-")
				return ops
	assert not f.remaining
	return ops

def parse_function(f: read.Reader, length: int):
	end = f.pos + length
	out = []
	has_error = False
	while f.pos < end:
		op = f.u16()
		a = None
		match op:
			case op if op in insns:
				name = insns[op]

			case 0x82DD:
				name = "int"
				a = f.i32()
			case 0x82DE:
				name = "float"
				a = f.f32()
			case 0x82DF:
				name = "string"
				a = f[f.u32()].decode("cp932")
			case 0x82E0:
				name = "expr"
				a = parse_expr(f.sub(f.u32()))
			case 0x2020:
				name = "text";
				nlines, nbytes = f.u32(), f.u32()
				starts = [f.u32() for _ in range(nlines)]
				text = f[nbytes]
				a = [
					text[a:b].decode("cp932")
					for a, b in zip(starts, starts[1:] + [nbytes])
				]

			case v:
				has_error = True
				name = f"\x1B[31m{v:04X}\x1B[m"
				print("\n" + " "*21 + f"-error 0x{op:X}", end=" ")
				read.dump(f[min(end - f.pos, 48)])
				raise ValueError

		if a is not None:
			print(" "+repr(a), end="")
		else:
			print("\n" + " "*21, end="")
			print(f"{name}", end="")
		out.append((name, a))
	print()
	# if has_error: raise ValueError
	# read.dump(f[min(length, 48)])

def parse_ys7_scp(f: read.Reader):
	f.check(b"YS7_SCP")
	f.check_u32(0)
	unk = f[9]

	for _ in range(f.u32()):
		name = f[32].rstrip(b"\0").decode("cp932")
		length = f.u32()
		start = f.u32()
		print(name)
		parse_function(f.at(start), length)

f = read.Reader(open("/home/large/kiseki/ys8/script/test.bin", "rb").read())
parse_ys7_scp(f)
# for f in sorted(Path("/home/large/kiseki/nayuta/script/").glob("*.bin")):
# 	# print(f)
# 	parse_ys7_scp(read.Reader(f.read_bytes()))
