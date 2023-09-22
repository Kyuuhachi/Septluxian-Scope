from __future__ import annotations
assert __name__ == "__main__"

from pathlib import Path

from common import insn_table, InsnTable
import parse_bin
import print_text
import parse_text
import print_bin

def parse_and_print(file: Path):
	import sys
	print(file, file=sys.stderr, end="", flush=True)
	data = file.read_bytes()
	scp = parse_bin.parse_ys7_scp(data)
	print('.', file=sys.stderr)
	redata = print_bin.write_ys7_scp(scp)
	if data != redata:
		print(len(data), len(redata))
		rescp = parse_bin.parse_ys7_scp(redata)
		assert scp == rescp
		for i, (a, b) in enumerate(zip(data, redata)):
			if a != b:
				print(i)
				break
		print(data[:256])
		print(redata[:256])

for file in sorted(Path("/home/large/kiseki/ys8/script/").glob("*.bin")):
	parse_and_print(file)

for file in sorted(Path("/home/large/kiseki/nayuta/US/script/").glob("*.bin")):
	parse_and_print(file)
