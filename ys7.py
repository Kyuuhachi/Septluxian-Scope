from __future__ import annotations
import read
from pathlib import Path

from common import insn_table, InsnTable
import parse_bin
import print_text

def parse_and_print(file: Path, insns: InsnTable):
	import sys
	print(file, file=sys.stderr, end="", flush=True)
	f = read.Reader(file.read_bytes())
	scp = parse_bin.parse_ys7_scp(f, insns)
	print('.', file=sys.stderr)
	print(f"==== {file.name} ====\n")
	print(print_text.print_ys7_scp(scp))

insns_ys8 = insn_table("insn/ys8.txt")
for file in sorted(Path("/home/large/kiseki/ys8/script/").glob("*.bin")):
	parse_and_print(file, insns_ys8)

# insns_nayuta = insn_table("insn/nayuta.txt")
# for file in sorted(Path("/home/large/kiseki/nayuta/US/script/").glob("*.bin")):
# 	parse_and_print(file, insns_nayuta)
