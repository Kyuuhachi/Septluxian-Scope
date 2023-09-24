#!/bin/env python3
import typing as T
from sys import stderr
import argparse
from pathlib import Path
from common import insn_table
import parse_bin, print_text, parse_text, print_bin

argp = argparse.ArgumentParser()
argp.add_argument("-q", "--quiet", help="don't write status messages", action = "store_true")
argp.add_argument("-i", "--insn", help="path to instruction table", type = Path)
argp.add_argument("-o", "--output", help="file or directory to place files in", type = Path)
argp.add_argument("files", metavar="file", nargs="+", help="files to convert", type = Path)

def __main__(quiet: bool, insn: Path | None, output: Path | None, files: list[Path]):
	make_output: T.Callable[[Path, str], Path]
	if output is None:
		make_output = lambda path, suffix: path.with_suffix(suffix)
	elif len(files) == 1 and not output.is_dir():
		make_output = lambda path, suffix: output
	else:
		output.mkdir(parents=True, exist_ok=True)
		make_output = lambda path, suffix: output / path.with_suffix(suffix).name

	insns = insn_table(insn) if insn is not None else None

	for file in files:
		if not quiet: print(f"{file} → ", file=stderr, end="", flush=True)
		if file.suffix == ".bin":
			outfile = make_output(file, ".scp")
			data = file.read_bytes()
			scp = parse_bin.parse_ys7_scp(data, insns)
			src = print_text.print_ys7_scp(scp)
			outfile.write_text(src)
		elif file.suffix == ".scp":
			outfile = make_output(file, ".bin")
			src = file.read_text()
			scp = parse_text.parse_ys7_scp(src)
			data = print_bin.write_ys7_scp(scp, insns)
			outfile.write_bytes(data)
		else:
			if not quiet: print(f"not sure how to handle", file=stderr)
			continue
		if not quiet: print(f"{outfile}", file=stderr)

if __name__ == "__main__":
	__main__(**argp.parse_args().__dict__)
