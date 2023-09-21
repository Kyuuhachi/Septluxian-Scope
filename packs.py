import kaiseki

def unpack_bz(data: bytes) -> bytes:
	if data[0] != 0:
		raise ValueError("bzip mode 1 is not supported")
	f = kaiseki.Reader(data)

	the_bits = f.u16()
	next_bit = 8
	def bit() -> bool:
		nonlocal the_bits, next_bit
		if next_bit == 16:
			the_bits, next_bit = f.u16(), 0
		v = bool(the_bits & (1<<next_bit))
		next_bit += 1
		return v

	def bits(n: int) -> int:
		v = 0
		for _ in range(n % 8):  v = (v << 1) | bit()
		for _ in range(n // 8): v = (v << 8) | f.u8()
		return v

	def repeat(o: int):
		if bit(): count = 2
		elif bit(): count = 3
		elif bit(): count = 4
		elif bit(): count = 5
		elif bit(): count = 6 + bits(3)
		else: count = 14 + bits(8)
		for _ in range(count):
			out.append(out[-o])

	out = bytearray()
	while True:
		if not bit():
			out.append(f.u8())
		elif not bit():
			repeat(bits(8))
		else:
			match bits(13):
				case 0:
					break
				case 1:
					n = bits(12) if bit() else bits(4)
					out.extend([f.u8()] * (n + 14))
				case o:
					repeat(o)

	assert not f.remaining
	return out

def unpack_c77(f: kaiseki.Reader) -> bytes:
	csize = f.u32()
	usize = f.u32()
	f = f.sub(csize)

	data = bytearray()
	mode = f.u32()
	if mode == 0:
		data.extend(f.remaining)
	else:
		while f.remaining:
			x = f.u16()
			op = x & ~(~0 << mode)
			num = x >> mode
			if op == 0:
				data.extend(f[num])
			else:
				for _ in range(op):
					data.append(data[~num])
				data.append(f.u8())
	assert len(data) == usize
	return bytes(data)
