from sys import argv

insns = {}
n = 0
with open("ys7_scp.txt", "rt") as f:
	for line in f:
		match line.split("#")[0].split():
			case []: pass
			case ["-", skip]: n += int(skip)
			case [v]: insns[n] = v; n += 1
			case _: raise ValueError(line)

assert len(argv) % 2 == 1
for k, v in zip(argv[1::2], argv[2::2]):
	if k.startswith("op_"):
		k = k[3:]
	k = int(k, 16)
	assert k not in insns
	insns[k] = v

with open("ys7_scp.txt", "wt") as f:
	prev = 0
	for a, b in sorted(insns.items()):
		if a != prev:
			print(f"- {a-prev}", file=f)
		print(b, file=f)
		prev = a+1
