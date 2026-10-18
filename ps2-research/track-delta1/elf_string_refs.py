"""List code locations that build a given address with lui + addiu/ori (read-only, SLES_509.06)."""
import struct
import sys
from pathlib import Path

ELF = Path('D:/Game/Master Rallye PS2/SLES_509.06')
BASE = 0xff000  # file offset = VA - BASE
CODE_END = 0x450000


def refs(binary, targets, window=12):
    found = {t: [] for t in targets}
    n = (CODE_END - 0x100000) // 4
    for i in range(n):
        va = 0x100000 + 4 * i
        w = struct.unpack_from('<I', binary, va - BASE)[0]
        if w >> 26 != 0x0f:
            continue
        rt = (w >> 16) & 31
        hi = (w & 0xffff) << 16
        for j in range(1, window):
            w2 = struct.unpack_from('<I', binary, va + 4 * j - BASE)[0]
            op, rs, rt2, imm = w2 >> 26, (w2 >> 21) & 31, (w2 >> 16) & 31, w2 & 0xffff
            if rs != rt:
                continue
            if op == 0x09:
                addr = (hi + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xffffffff
            elif op == 0x0d:
                addr = hi | imm
            else:
                continue
            if addr in found:
                found[addr].append((va, va + 4 * j))
    return found


if __name__ == '__main__':
    targets = [int(a, 0) for a in sys.argv[1:]]
    out = refs(ELF.read_bytes(), targets)
    for t, lst in out.items():
        print(hex(t), [(hex(a), hex(b)) for a, b in lst])
