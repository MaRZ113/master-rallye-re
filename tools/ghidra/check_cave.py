#!/usr/bin/env python3
"""Validate an AsmCave.java listing: no 0x66/0x67 prefixes, every rel8/rel32 branch hits its label/address."""
from __future__ import annotations

import re
import sys


def main(path: str) -> int:
    lines = open(path, encoding="utf-8").read().splitlines()[1:]
    labels, ins, pending = {}, [], None
    for line in lines:
        if line.endswith(":"):
            pending = line[:-1]
            continue
        m = re.match(r"([0-9a-f]{8})\s+([0-9a-f]+)\s+(.*)", line)
        if not m:
            continue
        at, code, text = int(m.group(1), 16), bytes.fromhex(m.group(2)), m.group(3)
        if pending:
            labels[pending], pending = at, None
        ins.append((at, code, text))
    bad = 0
    for at, code, text in ins:
        if code[0] in (0x66, 0x67):
            print(f"PREFIX {at:#x} {text}")
            bad += 1
        target = None
        if 0x70 <= code[0] <= 0x7F or code[0] == 0xEB:
            target = at + 2 + int.from_bytes(code[1:2], "little", signed=True)
        elif code[0] in (0xE8, 0xE9):
            target = at + 5 + int.from_bytes(code[1:5], "little", signed=True)
        if target is None:
            continue
        name = text.split()[-1]
        expected = labels.get(name, int(name, 16) if name.startswith("0x") else None)
        if expected != target:
            print(f"MISMATCH {at:#x} {text} -> {target:#x}")
            bad += 1
    end = ins[-1][0] + len(ins[-1][1])
    print(f"labels: { {k: hex(v) for k, v in labels.items()} }")
    print(f"errors: {bad}; end {end:#x}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
