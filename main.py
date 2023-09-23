#!/bin/env python3
from sys import stderr
import argparse
from pathlib import Path
from common import insn_table
import parse_bin, print_text, parse_text, print_bin

argp = argparse.ArgumentParser()
argp.add_argument("-i", "--insn", help="path to instruction table", type = Path)
argp.add_argument("-o", "--output", help="file or directory to place files in", type = Path)
argp.add_argument("files", metavar="file", nargs="+", help="files to convert", type = Path)

def __main__(insn: Path | None, output: Path | None, files: list[Path]):
	if len(files) != 1 and output and not output.is_dir():
		output.mkdir(parents=True)
	insns = insn_table(insn) if insn is not None else None

	for file in files:
		if file.suffix == ".bin":
			print(f"{file} → ", file=stderr, end="", flush=True)
			outfile = (output or file.parent)/file.with_suffix(".scp").name
			data = file.read_bytes()
			scp = parse_bin.parse_ys7_scp(data, insns)
			src = print_text.print_ys7_scp(scp)
			outfile.write_text(src)
			print(f"{outfile}", file=stderr)
		elif file.suffix == ".scp":
			print(f"{file} → ", file=stderr, end="", flush=True)
			outfile = (output or file.parent)/file.with_suffix(".bin").name
			src = file.read_text()
			scp = parse_text.parse_ys7_scp(src)
			data = print_bin.write_ys7_scp(scp, insns)
			outfile.write_bytes(data)
			print(f"{outfile}", file=stderr)
		else:
			print(f"Not sure how to handle {file}", file=stderr)

if __name__ == "__main__":
	__main__(**argp.parse_args().__dict__)
