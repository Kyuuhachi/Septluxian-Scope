from __future__ import annotations
assert __name__ == "__main__"

import read
from pathlib import Path

from common import insn_table, InsnTable
import parse_bin
import print_text
import parse_text
import print_bin

def parse_and_print(file: Path, insns: InsnTable):
	import sys
	print(file, file=sys.stderr, end="", flush=True)
	data = file.read_bytes()
	scp = parse_bin.parse_ys7_scp(read.Reader(data), insns)
	print('.', file=sys.stderr)
	redata = print_bin.write_ys7_scp(scp, insns)
	if data != redata:
		print(len(data), len(redata))
		rescp = parse_bin.parse_ys7_scp(read.Reader(redata), insns)
		assert scp == rescp
		import common
		for i, (a, b) in enumerate(zip(data, redata)):
			if a != b:
				print(i)
				break
		print(data[:256])
		print(redata[:256])

insns_ys8 = insn_table("insn/ys8.txt")
for file in sorted(Path("/home/large/kiseki/ys8/script/").glob("*.bin")):
	parse_and_print(file, insns_ys8)

insns_nayuta = insn_table("insn/nayuta.txt")
for file in sorted(Path("/home/large/kiseki/nayuta/US/script/").glob("*.bin")):
	parse_and_print(file, insns_nayuta)
