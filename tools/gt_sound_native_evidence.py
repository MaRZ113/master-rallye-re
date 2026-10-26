"""Exact supplied-GT4-CORE byte qualification and R5900 export cross-checks."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from gt_sound_jam import CORE_SHA256

# Digests of original instruction ranges; original bytes remain private.
PREIMAGES = {
    0x5338f0: (20, '7a7a8b005ca0665c877eba43b56eceb8da151b3ff342af08baa4fedf46bf23c6'),
    0x533730: (36, '1946970d8247fee509e049617d272cd17cd557773e774239cf913ae69f566109'),
    0x2e2d24: (36, '25241a6adec082dc42a72886d59b68cb487fd77eed19b1f8a0b3b95912220b26'),
    0x533ff4: (28, 'f5e8606562af6741e27672cb5eb48d9f3d21ac6ee385f003f4194c9793a0b923'),
}


class Elf32Image:
    def __init__(self, raw):
        self.raw = raw
        if len(raw) < 52 or raw[:7] != b'\x7fELF\x01\x01\x01':
            raise ValueError('ELF32 little-endian required')
        if struct.unpack_from('<H', raw, 18)[0] != 8:
            raise ValueError('MIPS ELF required')
        phoff = struct.unpack_from('<I', raw, 28)[0]
        size, count = struct.unpack_from('<HH', raw, 42)
        if size != 32 or not 1 <= count <= 32 or phoff + count * size > len(raw):
            raise ValueError('bounded ELF32 program headers required')
        self.segments = []
        for i in range(count):
            typ, off, va, _, filesz, memsz, flags, _ = struct.unpack_from('<8I', raw, phoff + i * size)
            if typ == 1:
                if filesz > memsz or off + filesz > len(raw) or va + memsz > 0x100000000:
                    raise ValueError('invalid ELF segment bounds')
                self.segments.append({'file_offset': off, 'virtual_address': va, 'file_bytes': filesz,
                                      'memory_bytes': memsz, 'flags': flags})

    def offset(self, va, size):
        if not isinstance(size, int) or size <= 0 or va < 0:
            raise ValueError('positive mapped byte range required')
        found = [s['file_offset'] + va - s['virtual_address'] for s in self.segments
                 if s['virtual_address'] <= va and va + size <= s['virtual_address'] + s['file_bytes']]
        if len(found) != 1:
            raise ValueError('address is unmapped, zero-fill-only or ambiguous')
        return found[0]

    def read(self, va, size):
        off = self.offset(va, size)
        return self.raw[off:off + size]


def qualify_core(raw):
    if hashlib.sha256(raw).hexdigest() != CORE_SHA256:
        raise ValueError('unqualified supplied GT4 CORE SHA256')
    image = Elf32Image(raw)
    for va, (length, expected) in PREIMAGES.items():
        if hashlib.sha256(image.read(va, length)).hexdigest() != expected:
            raise ValueError('native evidence preimage mismatch at ' + hex(va))
    return image


def inspect_exports(core, exports):
    import rabbitizer
    raw = Path(core).read_bytes()
    image = qualify_core(raw)
    words = {}
    for path in exports:
        text = Path(path).read_text(encoding='utf-8')
        if 'LANGUAGE=r5900:LE:32:default' not in text or 'PROGRAM_SHA256=' + CORE_SHA256 not in text:
            raise ValueError('unqualified Ghidra export identity')
        for match in re.finditer(r'^([0-9a-f]{8}) ([0-9a-f]{8}) (.+)$', text, re.M):
            va = int(match[1], 16)
            original = bytes.fromhex(match[2])
            if image.read(va, 4) != original:
                raise ValueError('Ghidra bytes differ from ELF at ' + hex(va))
            word = int.from_bytes(original, 'little')
            decoded = rabbitizer.Instruction(word, va, category=rabbitizer.InstrCategory.R5900)
            words[va] = {'va': f'0x{va:08x}', 'file_offset': image.offset(va, 4),
                         'bytes_hex': original.hex(), 'ghidra': match[3], 'rabbitizer': decoded.disassemble()}
    if not words:
        raise ValueError('no instruction records in exports')
    return {'status': 'STATIC_R5900_BYTES_CROSS_CHECKED', 'core_sha256': CORE_SHA256,
            'architecture': 'R5900 little-endian', 'segments': image.segments,
            'instruction_count': len(words), 'instructions': [words[v] for v in sorted(words)],
            'boundary': 'Exact source bytes and independent decoding; no game execution or Beta-runtime pairing.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--exports', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('new private evidence output required')
    report = inspect_exports(args.core, args.exports)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['status'], report['instruction_count'])
