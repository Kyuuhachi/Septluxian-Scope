from __future__ import annotations
import typing as T
import read
import json

def parse_dbin(data: bytes) -> str:
	f = read.Reader(data, pos = len(data)-64)
	kind = f[4].decode("ascii")
	f.check_u16(1)
	f.check_u16(1)
	f.check_u16(4)
	f.check_u16(16)
	f.check_u64(4)
	p = [f.u32() for _ in range(6)]
	f.check_u32(1)
	f.check(bytes(16))
	assert not f.remaining

	assert p[4] == p[2] + p[1] * 4

	fields = []
	f = f.at(p[2])
	for i in range(p[3]):
		k = f.u8()
		f.check_u8(4)
		v = f.u16()
		f.check_u32(i*4)
		f.check_u32(0xFFFFFFFF)
		f.check_u16(v)
		f.check_u16(v)
		fields.append({
			"type": {0: "int", 5: "str"}[k],
			"unk": {0: False, 1: True}[v],
		})
	f.check(bytes(p[4]-f.pos))

	f = f.at(p[4])
	strings = {}
	for _ in range(p[5]):
		v = f.pos - p[4]
		s = f.zstr()
		try:
			strings[v] = s.decode("utf8")
		except UnicodeError:
			strings[v] = "SJIS:"+s.decode("cp932")
	assert len(strings) == len(set(strings))
	f.check(bytes(len(f)-64-f.pos))

	f = f.at(0)
	assert p[1] == p[3] * 4
	rows = []
	for _ in range(p[0]):
		row = []
		for field in fields:
			v = f.u32()
			match field["type"]:
				case "int": row.append(v)
				case "str": row.append(strings[v])
		rows.append(row)
	f.check(bytes(p[2]-f.pos))
	
	v = json.dumps(
		{
			"kind": kind,
			"fields": ["#" for _ in fields],
			"rows": ["#" for _ in rows],
		},
		ensure_ascii=False,
		indent="\t"
	).split('"#"')
	a = [json.dumps(a, ensure_ascii=False) for a in fields + rows]
	w = [None] * (len(v) + len(a))
	w[0::2] = v
	w[1::2] = a
	return "".join(w)

def parse_json(data: str) -> bytes:
	data: T.Any = json.loads(data)
	kind = data["kind"].encode("ascii")
	assert len(kind) == 4

	fields = read.Writer()
	for i, field in enumerate(data["fields"]):
		fields.u8({"int": 0, "str": 5}[field["type"]])
		fields.u8(4)
		fields.u16(field["unk"])
		fields.u32(i*4)
		fields.u32(0xFFFFFFFF)
		fields.u16(field["unk"])
		fields.u16(field["unk"])
	fields.pad(16)

	rows = read.Writer()
	string_pos = {}
	strings = read.Writer()
	for row in data["rows"]:
		for v in row:
			if isinstance(v, str):
				if v not in string_pos:
					string_pos[v] = len(strings)
					if v.startswith("SJIS:"):
						strings.write(v[5:].encode("cp932"))
					else:
						strings.write(v.encode("utf8"))
					strings.u8(0)
				rows.u32(string_pos[v])
			else:
				rows.u32(v)

	rows.pad(16)
	strings.pad(16)

	p = [
		len(data["rows"]),
		len(data["fields"]) * 4,
		len(rows.data),
		len(data["fields"]),
		len(rows.data) + len(fields.data),
		len(string_pos),
	]

	tail = read.Writer()
	tail.write(kind)
	tail.u16(1)
	tail.u16(1)
	tail.u16(4)
	tail.u16(16)
	tail.u64(4)
	[tail.u32(p) for p in p]
	tail.u32(1)
	tail.write(bytes(16))

	return rows.data + fields.data + strings.data + tail.data
