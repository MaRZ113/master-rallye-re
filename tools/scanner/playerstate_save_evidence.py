"""Read-only revalidation of the bounded pristine-retail save-call evidence.

Does not launch the game, write saves, or change a Ghidra program. The call
census is direct E8 only; this verifier does not infer native event semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2] / 'research/general-re/persistence/playerstate-save-trigger.json'


def image_layout(data: bytes) -> tuple[int, list[tuple[int, int, int, bool]]]:
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('not a bounded PE image')
    pe = struct.unpack_from('<I', data, 60)[0]
    if pe + 24 > len(data) or data[pe:pe+4] != b'PE\0\0':
        raise ValueError('invalid PE signature/header bounds')
    machine, count = struct.unpack_from('<HH', data, pe+4)
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    opt = pe+24
    if machine != 0x14c or optional_size < 32 or opt+optional_size+count*40 > len(data):
        raise ValueError('unsupported or truncated PE32 layout')
    if struct.unpack_from('<H', data, opt)[0] != 0x10b:
        raise ValueError('not PE32')
    base = struct.unpack_from('<I', data, opt+28)[0]
    sections = []
    for index in range(count):
        section = opt+optional_size+index*40
        rva, size, offset = struct.unpack_from('<III', data, section+12)
        flags = struct.unpack_from('<I', data, section+36)[0]
        if offset+size > len(data):
            raise ValueError('section exceeds file bounds')
        sections.append((base+rva, offset, size, bool(flags & 0x20000000)))
    return base, sections


def va_offset(va: int, sections: list[tuple[int, int, int, bool]], size: int = 1) -> int:
    for start, offset, length, _ in sections:
        if size > 0 and start <= va and va+size <= start+length:
            return offset+va-start
    raise ValueError(f'VA {va:08X} is not backed by the requested file bytes')


def direct_calls(data: bytes, sections: list[tuple[int, int, int, bool]], target: int) -> set[int]:
    calls = set()
    for start, offset, length, executable in sections:
        if not executable:
            continue
        payload = data[offset:offset+length]
        for pos in range(max(0, len(payload)-4)):
            if payload[pos] == 0xe8:
                displacement = struct.unpack_from('<i', payload, pos+1)[0]
                if (start+pos+5+displacement) & 0xffffffff == target:
                    calls.add(start+pos)
    return calls


def verify(binary: Path) -> dict:
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    data = binary.read_bytes()
    if len(data) != evidence['file_size'] or hashlib.sha256(data).hexdigest() != evidence['sha256']:
        raise ValueError('input is not the exact authoritative pristine retail corpus')
    base, sections = image_layout(data)
    if base != int(evidence['image_base'], 16):
        raise ValueError('image base disagrees with evidence')
    expected = {int(row['call_va'], 16) for row in evidence['calls']}
    actual = direct_calls(data, sections, int(evidence['save_entry_va'], 16))
    if actual != expected:
        raise ValueError('direct save-call census differs from recorded evidence')
    for row in evidence['calls']:
        if isinstance(row['mode'], int):
            pos = va_offset(int(row['mode_push_va'], 16), sections, 2)
            if data[pos:pos+2] != bytes((0x6a, row['mode'])):
                raise ValueError(f"mode PUSH disagrees at {row['mode_push_va']}")
    return {'sha256': evidence['sha256'], 'direct_calls_verified': len(actual),
            'literal_mode_pushes_verified': sum(isinstance(row['mode'], int) for row in evidence['calls']),
            'scope': 'byte identity and bounded direct-call evidence, not runtime behavior'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.binary), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
