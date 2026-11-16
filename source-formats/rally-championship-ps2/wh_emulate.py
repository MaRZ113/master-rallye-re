"""Decode a Rally Championship (PS2, SLES-50763) "WH" compressed HOG member by
emulating the game's own streaming decompressor from SLES_507.63 (research only).

The decompressor lives at 0x19CA30 (output pointer set by 0x19C918); its state
is initialised by 0x19B894..0x19B8E4 (bit buffer 0x80000000, input after the
6-byte "WH"+u32 header). The whole compressed stream is placed in memory so the
CD refill path is never taken. The hardware timer read at 0x10000000 is mapped
as zero so the routine never yields.

Usage: python -I wh_emulate.py SLES_507.63 <file.HOG> <out.bin>
"""
import struct
import sys
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import (UC_MIPS_REG_GP, UC_MIPS_REG_SP, UC_MIPS_REG_RA, UC_MIPS_REG_A0,
                                UC_MIPS_REG_V0, UC_MIPS_REG_PC)

GP = 0x629A70
RAM = 0x8000000            # 128 MiB scratch address space
IN_BASE = 0x2000000
OUT_BASE = 0x4000000
STOP = 0x0FFFF0
TIMER = 0x10000000


def g(off):
    return (GP + off) & 0xFFFFFFFF


def hog_member(b):
    if b[:8] != b'WART1.10':
        raise ValueError('not a WART1.10 HOG')
    count, first, data_off = struct.unpack_from('<3I', b, 8)
    return count, b


def main():
    elf, hog, out = sys.argv[1:4]
    e = open(elf, 'rb').read()
    b = open(hog, 'rb').read()
    pos = b.find(b'WH', 0x20)
    if pos < 0:
        raise ValueError('no WH stream')
    expanded = struct.unpack_from('<I', b, pos + 2)[0]
    stream = b[pos:]
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 + UC_MODE_LITTLE_ENDIAN)
    mu.mem_map(0, RAM)
    mu.mem_map(TIMER, 0x1000)
    seg_off, seg_va, filesz = 0x1000, 0x100000, 0x52558C
    mu.mem_write(seg_va, e[seg_off:seg_off + filesz])
    mu.mem_write(IN_BASE, stream)
    w32 = lambda a, v: mu.mem_write(a, struct.pack('<I', v & 0xFFFFFFFF))
    # state as set up by 0x19B894..0x19B8E4
    w32(g(-0x4D44), 0)
    w32(g(-0x4CD8), 0x80000000)
    w32(g(-0x4CC4), 8)
    w32(g(-0x4CB8), 1)
    w32(g(-0x4CD4), IN_BASE + 6)
    w32(g(-0x4CAC), IN_BASE + len(stream) + 0x10000)
    for off in (-0x4CC0, -0x4CBC, -0x4CDC, -0x4C98, -0x4CA8, -0x4D34, -0x4C94):
        w32(g(off), 0)

    def call(fn, a0):
        mu.reg_write(UC_MIPS_REG_GP, GP)
        mu.reg_write(UC_MIPS_REG_SP, 0x1F00000)
        mu.reg_write(UC_MIPS_REG_RA, STOP)
        mu.reg_write(UC_MIPS_REG_A0, a0)
        mu.emu_start(fn, STOP, count=2_000_000_000)
        return mu.reg_read(UC_MIPS_REG_V0) & 0xFFFFFFFF

    call(0x19C918, OUT_BASE)
    rounds = 0
    while True:
        rounds += 1
        rv = call(0x19CA30, expanded)
        done = struct.unpack('<I', mu.mem_read(g(-0x4CB4), 4))[0] - OUT_BASE
        if rv == 2 or done >= expanded or rounds > 64:
            break
    data = bytes(mu.mem_read(OUT_BASE, expanded))
    open(out, 'wb').write(data)
    print(f'{hog}: expanded {expanded}, produced {done}, rv {rv}, rounds {rounds}')


if __name__ == '__main__':
    main()
