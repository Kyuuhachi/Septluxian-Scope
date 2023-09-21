import subprocess
from pathlib import Path
NAYUTA = Path("/home/large/kiseki/nayuta")

import kaiseki
import packs

def decompress_ed7(f: kaiseki.Reader) -> bytes:
	csize = f.u32()
	pos = f.pos
	usize = f.u32()

	nchunks = f.u32()
	data = bytearray()
	for n in range(nchunks):
		block = f[f.u16() - 2]
		data.extend(packs.unpack_bz(block))
		if f.u8() != (n < nchunks - 1): raise ValueError()

	if data[0] != data.pop():
		raise ValueError("incorrect dummy byte")
	assert f.pos == pos + csize
	assert len(data) == usize
	return bytes(data)

def decompress_unk(f: kaiseki.Reader) -> bytes:
	f.check_u32(0x80000001)
	f.check_u32(1)
	csize = f.u32()
	f.check_u32(csize)
	usize = f.u32()
	pos = f.pos
	data = packs.unpack_c77(f)
	assert f.pos == pos + csize
	assert len(data) == usize
	return data

f = kaiseki.Reader((NAYUTA / "text/bgmtbl.tbb").read_bytes())
n = f.u32()
data = decompress_ed7(f)
assert not f.remaining
print(n)
kaiseki.dump(data, 24)

f = kaiseki.Reader((NAYUTA / "text/helplib.tbb").read_bytes())
data1 = decompress_ed7(f)
data2 = decompress_ed7(f)
assert not f.remaining
kaiseki.dump(data1)
kaiseki.dump(data2, 40)

f = kaiseki.Reader((NAYUTA / "US/text/helplib.tbb").read_bytes())
data1 = decompress_unk(f)
data2 = decompress_unk(f)
assert not f.remaining
kaiseki.dump(data1)
kaiseki.dump(data2, 40)
