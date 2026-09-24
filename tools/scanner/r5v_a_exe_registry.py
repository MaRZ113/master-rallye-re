"""Extract one verified vehicle constructor from a local PE with objdump.

Constructor ranges and record constructor targets are explicit research anchors.
The extractor refuses duplicate indices, bad strides and non-string pointers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

BUILD = {
    "september": (0x447870, 0x447CAF, 0x447F10, 0x24, 26),
    "november": (0x44D360, 0x44D7C9, 0x44DF00, 0x24, 27),
    "final": (0x458E70, 0x4598CC, 0x45A0B0, 0x34, 26),
}
EXPECTED_SHA256 = {
    "september": "bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be",
    "november": "931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680",
    "final": "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
}

LINE = re.compile(r"^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\s+([^\r\n]+)$")
PUSH = re.compile(r"^push\s+0x([0-9a-f]+)$")
LEA = re.compile(r"^lea\s+ecx,\[esi\+0x([0-9a-f]+)\]$")
CALL = re.compile(r"^call\s+0x([0-9a-f]+)$")


def read_cstring(data: bytes, va: int) -> str | None:
    # All three inspected PE files have section VA = ImageBase + file offset.
    offset = va - 0x400000
    if not (0 <= offset < len(data)):
        return None
    end = data.find(b"\0", offset, min(len(data), offset + 96))
    if end < 0:
        return None
    raw = data[offset:end]
    if any(c < 32 or c > 126 for c in raw):
        return None
    return raw.decode("ascii")


def records(exe: Path, build: str, objdump: Path) -> dict:
    start, stop, ctor, stride, capacity = BUILD[build]
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256[build]:
        raise ValueError("EXE hash does not match the verified build")
    run = subprocess.run(
        [str(objdump), "-D", "-Mintel", f"--start-address=0x{start:x}",
         f"--stop-address=0x{stop:x}", str(exe)],
        capture_output=True, text=True, check=True,
    )
    entries = []
    pointer = None
    name = None
    offset = None
    args = []
    for line in run.stdout.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        address = int(match.group(1), 16)
        instruction = match.group(2).strip()
        push = PUSH.match(instruction)
        lea = LEA.match(instruction)
        call = CALL.match(instruction)
        if push:
            value = int(push.group(1), 16)
            possible = read_cstring(data, value) if value >= 0x400000 else None
            if (possible is not None and value != 0x400000) or value in (0x5F9114, 0x67F6F8):
                pointer, name, args = value, possible or None, []
            elif value < 0x100 and pointer is not None:
                args.append(value)
        elif lea:
            offset = int(lea.group(1), 16)
        elif call and int(call.group(1), 16) == ctor:
            if pointer is None or offset is None:
                raise ValueError(f"Missing name/offset at 0x{address:X}")
            if (offset - 4) % stride:
                raise ValueError(f"Bad record offset 0x{offset:X}")
            index = (offset - 4) // stride
            entries.append({
                "index": index, "name": name or None,
                "name_string_va": f"0x{pointer:08X}",
                "name_status": "literal" if name else "unresolved_global",
                "record_offset": f"0x{offset:X}",
                "constructor_call_va": f"0x{address:08X}",
                "raw_numeric_arguments_push_order": args[-7:],
            })
            pointer = name = offset = None
            args = []
    indices = [item["index"] for item in entries]
    if len(indices) != len(set(indices)) or sorted(indices) != list(range(len(indices))):
        raise ValueError(f"Noncontiguous or duplicate indices: {indices}")
    if len(entries) > capacity:
        raise ValueError("More initialized entries than allocated capacity")
    return {
        "build": build, "constructor_va": f"0x{start:08X}",
        "record_constructor_va": f"0x{ctor:08X}",
        "record_stride": stride, "array_capacity": capacity,
        "initialized_records": len(entries),
        "named_records": sum(bool(x["name"]) for x in entries),
        "unresolved_name_indices": [x["index"] for x in entries if not x["name"]],
        "trailing_default_records": capacity - len(entries),
        "records": entries,
        "interpretation_limit": "Constructor/static evidence only; selectable runtime count and sentinel semantics require caller analysis.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", choices=BUILD)
    parser.add_argument("exe", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--objdump", type=Path, required=True)
    args = parser.parse_args()
    result = records(args.exe, args.build, args.objdump)
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    inventory["executable_registry"] = result
    args.inventory.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.build, result["initialized_records"], result["named_records"],
          result["unresolved_name_indices"], result["trailing_default_records"])


if __name__ == "__main__":
    main()