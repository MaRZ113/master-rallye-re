"""One bounded byte audit: root17 absent shader/primary and GS mode0 entry.

Run with the existing tooling venv (Rabbitizer R5900); original ELF read-only.
No decompiler approximation or runtime invocation is asserted.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'ps2-research/revalidation2/tools'))
import verify_r5900_revalidation2 as verification
import rabbitizer

RANGES = ((0x3916d0, 0x391750), (0x391774, 0x391790),
          (0x3918fc, 0x391938), (0x391af0, 0x391bf8),
          (0x391bfc, 0x391d04), (0x3126e4, 0x3128f0),
          (0x3715b0, 0x371650), (0x2fd788, 0x2fd7a0),
          (0x2f7b20, 0x2f7b30), (0x2f8014, 0x2f8048),
          (0x2dc720, 0x2dc7ac), (0x2dd1d0, 0x2dd234))
ANCHORS = {0x3916dc: 0xac400028, 0x39177c: 0x1060005f,
           0x391b68: 0x1840001a, 0x391c58: 0xac430028,
           0x391cc4: 0xac430028}


def main():
    data = Path('D:/Game/Master Rallye PS2/SLES_509.06').read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != verification.EXPECTED_ELF_SHA256:
        raise ValueError('Canonical original ELF drift')
    header = verification.parse_elf32_le(data)
    def offset(va, size=4):
        return verification.va_to_offset(va, size, header['load_segments'])
    instructions = []
    for begin, end in RANGES:
        for va in range(begin, end, 4):
            word = struct.unpack_from('<I', data, offset(va))[0]
            ins = rabbitizer.Instruction(word, va, rabbitizer.InstrCategory.R5900)
            if not ins.isValid():
                raise ValueError('Invalid R5900 original word')
            if va in ANCHORS and word != ANCHORS[va]:
                raise ValueError('Original instruction anchor drift')
            instructions.append({'va': hex(va), 'original_word': hex(word),
                                 'r5900': str(ins), 'file_offset': offset(va)})
    target = struct.unpack_from('<I', data, offset(0x4850c0))[0]
    if target != 0x3126e4:
        raise ValueError('Mode0 original dispatch drift')
    strings = {}
    for va in (0x487928, 0x487950, 0x487958, 0x487970, 0x483f58):
        at = offset(va, 64)
        strings[hex(va)] = data[at:at + 64].split(b'\0')[0].decode('ascii')
    report = {'canonical_elf_sha256': digest, 'processor': 'R5900',
              'elf_mapping': header, 'instructions': instructions,
              'instruction_count': len(instructions), 'original_strings': strings,
              'mode0_dispatch': {'table_va': '0x4850c0', 'target': hex(target)},
              'root17_static_mode': 0, 'root17_primary_copy': False,
              'root17_secondary_copy': False,
              'missing_shader_branch': '0x391b68 -> 0x391bd4',
              'missing_primary_branch': '0x39177c -> 0x3918fc',
              'missing_primary_binding': '2fd788 -> manager texture-owner+0x58 default resident handle',
              'default_handle_constructor': '0x2f8044 stores 2f84f0-created handle from initializer-supplied default name',
              'default_texture_original_pixels': 'CANONICAL_DEFAULT_GXI_8x8_RGBA_0_0_0_255',
              'default_texture_sha256': 'ad2960c11407794294b6d188db3660478f21ecea1a9b0fef4e69fc0a4ccef6d5',
              'live_invocation': 'NOT_CAPTURED', 'strip_flag_culling': 'UNKNOWN'}
    (Path(__file__).parent / 'default-material-evidence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'words': len(instructions), 'mode': 0, 'dispatch': hex(target)}))


if __name__ == '__main__':
    main()
