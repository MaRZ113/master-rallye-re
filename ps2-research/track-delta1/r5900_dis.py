"""Disassemble ranges of SLES_509.06 with Rabbitizer (read-only). Usage: r5900_dis.py 0xSTART 0xEND [...]"""
import struct
import sys

import rabbitizer
from rabbitizer import InstrCategory

ELF = 'D:/Game/Master Rallye PS2/SLES_509.06'
BASE = 0xff000


def main(args):
    d = open(ELF, 'rb').read()
    for i in range(0, len(args), 2):
        lo, hi = int(args[i], 0), int(args[i + 1], 0)
        print(f'--- {lo:#x}..{hi:#x}')
        for va in range(lo, hi, 4):
            w = struct.unpack_from('<I', d, va - BASE)[0]
            ins = rabbitizer.Instruction(w, vram=va, category=InstrCategory.R5900)
            print(f'{va:08x}  {w:08x}  {ins.disassemble()}')


if __name__ == '__main__':
    main(sys.argv[1:])
