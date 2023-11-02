#!/bin/env python3
import typing as T
from sys import stderr, exit
import argparse
import csv
from pathlib import Path
from common import InsnTable, insn_table
import parse_bin, print_text, parse_text, print_bin

argp = argparse.ArgumentParser()
argp.add_argument("-q", "--quiet", help="don't write status messages", action = "store_true")
argp.add_argument("-i", "--insn", help="path to instruction table", type = Path)
argp.add_argument("-o", "--output", help="file or directory to place files in", type = Path)
argp.add_argument("files", metavar="file", nargs="+", help="files to convert", type = Path)

def __main__(quiet: bool, insn: Path | None, output: Path | None, files: list[Path]) -> int:
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
		try:
			outfile = process_file(make_output, insns, file)
		except Exception as e:
			if not quiet:
				import traceback
				traceback.print_exc()
				print(e, file=stderr)
			failed = True
		else:
			if not quiet: print(f"{outfile}", file=stderr)
	return 0 if not failed else 2

def process_file(make_output: T.Callable[[Path, str], Path], insns: InsnTable | None, file: Path) -> Path:
	if file.suffix == ".bin":
		data = file.read_bytes()
		scp = parse_bin.parse_ys7_scp(data, insns)
		src = print_text.print_ys7_scp(scp)
		outfile = make_output(file, ".7l")
		outfile.write_bytes(src.encode())
	elif file.suffix == ".7l":
		src = file.read_bytes().decode()
		scp = parse_text.parse_ys7_scp(src)
		outdata = print_bin.write_ys7_scp(scp, insns)
		outfile = make_output(file, ".bin")
		outfile.write_bytes(outdata)
	elif file.suffix == ".scp":
		try:
			lines = file.read_bytes().decode().split('\0')
			match lines.pop():
				case "\t": pass
				case "\t\r\n": lines.extend(["", ""])
				case _: raise Exception
			assert not len(lines) % 2
		except Exception:
			raise Exception("invalid .scp file — is it a script source?")
		outfile = make_output(file, ".csv")
		with outfile.open("w", newline="") as f:
			csv.writer(f).writerows(zip(lines[0::2], lines[1::2]))
	elif file.suffix == ".csv":
		strings = []
		with file.open() as f:
			for row in csv.reader(f):
				assert len(row) == 2, f"invalid row {row}"
				strings.extend(row)
		if strings[-2:] == ["", ""]:
			strings[-2:] = ["\t\r\n"]
		else:
			strings.append("\t")
		outfile = make_output(file, ".scp")
		outfile.write_bytes("\0".join(strings).encode())
	else:
		raise Exception(f"not sure how to handle")
	return outfile

if __name__ == "__main__":
	exit(__main__(**argp.parse_args().__dict__))
