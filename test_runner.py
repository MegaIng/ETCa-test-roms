from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Literal

TEST_ROMS = Path(__file__).parent / "test_roms"
TEMP_FOLDER = Path(__file__).parent / "temp"
OUTPUT_FOLDER = Path(__file__).parent / "output"

ASSEMBLER = "etc-as"


def prepare(name: Path, options):
    assembly_file = TEST_ROMS / name.with_suffix(".s")
    mem_desc_in = TEST_ROMS / name.with_suffix(".mem.json")

    mem_desc_out = TEMP_FOLDER / name.with_suffix(".mem.json")
    bin_file = TEMP_FOLDER / name.with_suffix(".bin")

    out_file = OUTPUT_FOLDER / name.with_suffix(".out")
    if not assembly_file.is_file():
        raise FileNotFoundError(f"{assembly_file} is not a file.")
    if not mem_desc_in.is_file():
        raise FileNotFoundError(f"{mem_desc_in} is not a file.")

    command = [options.assembler, "-o", bin_file, "-mformat=binary", assembly_file]
    if options.assembler == "etc-as":
        command[:1] = [sys.executable, "-m", "etc_as"]
    r = subprocess.run(command)
    r.check_returncode()

    if not bin_file.is_file():
        raise FileNotFoundError(f"Assembler failed to create binary.")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.touch(exist_ok=True)

    text = mem_desc_in.read_text(encoding="utf-8")
    text = text.replace("%outputfile", str(out_file).replace('\\', '\\\\'))
    text = text.replace("%rombin", str(bin_file).replace('\\', '\\\\'))
    mem_desc_out.write_text(text, encoding="utf-8")


def run(name, options):
    mem_desc = TEMP_FOLDER / name.with_suffix(".mem.json")
    command = [options.executable, mem_desc]
    r = subprocess.run(command)
    r.check_returncode()


def compare(got: str, expected: str, output_width: Literal["h", "x", "d", "q"]) -> bool:
    if output_width == "h":
        return got == expected
    elif output_width == "x":
        if got[0] == "\x00":
            return got[1::2] == expected and set(got[0::2]) == {'\x00'}
        else:
            return got[0::2] == expected and set(got[1::2]) == {'\x00'}
    else:
        raise NotImplementedError(output_width)


def check(name, options):
    expected_file = TEST_ROMS / name.with_suffix(".expected")
    output_file = OUTPUT_FOLDER / name.with_suffix(".out")
    any_failed = False

    for expected_line, actual_line in zip(expected_file.read_text().splitlines(), output_file.read_text().splitlines()):
        (expected, output_width, label, desc) = expected_line.split('|')
        if not compare(actual_line, expected, output_width):
            print(f"Mismatch in output for test {name} in label {label}: {desc}"
                  f" (got {actual_line!r}, expected {expected!r})")
            any_failed = True
            if options.fail_fast:
                return
    if not any_failed:
        print(f"Test Rom {name} completed successfully.")

def parse_arguments(args):
    arg_parser = argparse.ArgumentParser()
    sp = arg_parser.add_subparsers(required=True)

    prepare_ = sp.add_parser("prepare", help="prepares the test roms for execution.")
    prepare_.add_argument("-a", "--assembler", required=False, action="store", default="etc-as",
                          help="The assembler executable. Needs to have the same interface as etc-as")
    prepare_.add_argument("names", nargs="*", type=Path,
                          help="The test_roms to prepare. If not given, prepares all.")
    prepare_.set_defaults(funcs=[prepare])

    run_ = sp.add_parser("run")
    run_.add_argument("-e", "--executable", required=True, action="store", help="The emulator executable.")
    run_.add_argument("names", nargs="*", type=Path,
                      help="Names of the test roms to execute. If not given, runs all prepared.")
    run_.set_defaults(funcs=[run])

    check_ = sp.add_parser("check")
    check_.add_argument("-f", "--fail-fast", action="store_true", help="Fail on the first mismatch for each file")
    check_.add_argument("names", nargs="*", help="The outputfiles to verify. If not given, checks all in output.")
    check_.set_defaults(funcs=[check])

    test = sp.add_parser("test", help="prepare, run and check")
    test.add_argument("-e", "--executable", required=True, action="store", help="The emulator executable.")
    test.add_argument("-a", "--assembler", required=False, action="store", default="etc-as",
                      help="The assembler executable. Needs to have the same interface as etc-as")
    test.add_argument("-f", "--fail-fast", action="store_true", help="Fail on the first mismatch for each file")
    test.add_argument("names", nargs="*", type=Path,
                      help="The test_roms to test. If not given, tests all.")
    test.set_defaults(funcs=[prepare, run, check])

    return arg_parser.parse_args(args)


def main(args):
    ns = parse_arguments(args)
    if not ns.names:
        ns.names = [p.with_suffix('').relative_to(TEST_ROMS) for p in TEST_ROMS.rglob("*.s")]
    for name in ns.names:
        for f in ns.funcs:
            f(name, ns)


if __name__ == '__main__':
    main(sys.argv[1:])
