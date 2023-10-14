#!/bin/env python3
import typing as T
from sys import stderr, exit
import argparse
from pathlib import Path
from common import insn_table
import parse_bin, print_text, parse_text, print_bin

argp = argparse.ArgumentParser()
argp.add_argument("-q", "--quiet", help="don't write status messages", action = "store_true")
argp.add_argument("-i", "--insn", help="path to instruction table", type = Path)
argp.add_argument("-o", "--output", help="file or directory to place files in", type = Path)
argp.add_argument("files", metavar="file", nargs="+", help="files to convert", type = Path)

def __main__(quiet: bool, insn: Path | None, output: Path | None, files: list[Path]) -> int:
	make_output: T.Callable[[Path, str], Path]
	if output is None:
		make_output = lambda path, suffix: path.with_suffix(suffix)
	elif len(files) == 1 and not output.is_dir():
		make_output = lambda path, suffix: output
	else:
		output.mkdir(parents=True, exist_ok=True)
		make_output = lambda path, suffix: output / path.with_suffix(suffix).name

	insns = insn_table(insn) if insn is not None else None

	failed = False
	for file in files:
		if not quiet: print(f"{file} → ", file=stderr, end="", flush=True)
		if file.suffix == ".bin":
			outfile = make_output(file, ".7l")
			data = file.read_bytes()
			scp = parse_bin.parse_ys7_scp(data, insns)
			src = print_text.print_ys7_scp(scp)
			outfile.write_bytes(src.encode())
		elif file.suffix == ".7l":
			outfile = make_output(file, ".bin")
			src = file.read_bytes().decode()
			scp = parse_text.parse_ys7_scp(src)
			outdata = print_bin.write_ys7_scp(scp, insns)
			outfile.write_bytes(outdata)
		elif file.suffix == ".scp":
			if not quiet:
				print(f"cannot handle .scp source files", file=stderr)
			failed = True
			continue
		else:
			if not quiet:
				print(f"not sure how to handle", file=stderr)
			failed = True
			continue
		if not quiet: print(f"{outfile}", file=stderr)
	return 0 if not failed else 2

if __name__ == "__main__":
	exit(__main__(**argp.parse_args().__dict__))
