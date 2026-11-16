"""Dump the PS2 Rally Championship CAR_DEFINITION table (840-byte records, STABS layout).

The table is not stored as data: CarDefs.cpp builds it in code (function 0x1596F8, 0x5D50-byte
frame, one memset per car). This script runs that function under Unicorn (MIPS64 LE, the whole
ELF image loaded, gp = 0x629A70) and then finds the records in memory by their name pointers.

Usage: python car_definitions.py <SLES_507.63> <out.json>
"""
import json
import struct
import sys
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import (UC_MIPS_REG_GP, UC_MIPS_REG_SP, UC_MIPS_REG_RA, UC_MIPS_REG_A0, UC_MIPS_REG_A1,
                                UC_MIPS_REG_A2, UC_MIPS_REG_V0, UC_MIPS_REG_PC)

GP, STOP, VA = 0x629A70, 0x0FFFF0, 0xFF000
FIELDS = [  # name, byte offset, kind, count  (bit offsets / 8 from the STABS record)
    ('Id', 0, 'i', 1), ('Group', 4, 'i', 1), ('pName', 8, 's', 1), ('pRealName', 12, 's', 1), ('pCode', 16, 's', 1),
    ('pFileName', 20, 's', 1), ('p3PlFileName', 24, 's', 1), ('pMeckName', 28, 's', 1), ('pTransName', 32, 's', 1),
    ('driving', 40, 'i', 1), ('icon', 44, 'i', 1), ('prize', 48, 'i', 1), ('engine_sound_revs', 52, 'f', 5),
    ('steering_sensitivity_critical_speed', 72, 'f', 1), ('EngineSound', 76, 'i', 1), ('Flags', 80, 'i', 1), ('revs', 84, 'i', 1),
    ('TorqueSplit', 88, 'f', 1), ('TorqueBoost', 92, 'f', 1), ('TurboBoost', 96, 'f', 1), ('EngineSample', 100, 'i', 1),
    ('AccelerationSample', 104, 'i', 1), ('EngineVol', 108, 'f', 1), ('AccelVolMin', 112, 'f', 1), ('AccelVolMax', 116, 'f', 1),
    ('TurboVol', 120, 'f', 1), ('PopVol', 124, 'f', 1), ('Dimensions', 128, 'f', 3), ('WheelOffset', 140, 'f', 3),
    ('WheelOffsetRear', 152, 'f', 3), ('Mass', 164, 'f', 1), ('power_curve', 288, 'f', 8), ('friction_curve', 320, 'f', 8),
    ('num_gears', 352, 'i', 1), ('gear_ratio', 356, 'f', 8), ('ride_height', 388, 'f', 3), ('final_drive', 400, 'f', 5),
    ('brake_bias', 420, 'f', 9), ('brake_power', 456, 'f', 9), ('hand_brake_power', 492, 'f', 9), ('steering_sensitivity', 528, 'f', 9),
    ('suspension', 564, 'f', 36), ('max_turn', 708, 'f', 1), ('cg_offset', 732, 'f', 3), ('friction_fudge', 744, 'f', 1),
    ('lateral_friction', 748, 'f', 1), ('slip_angle', 752, 'f', 1), ('redline', 756, 'f', 1), ('engine_pitch', 760, 'f', 1),
    ('idle', 764, 'f', 1), ('wheel_radius', 768, 'f', 1), ('wheel_render_top', 772, 'f', 1), ('wheel_arch_top', 776, 'f', 1),
    ('num_engine_sounds', 780, 'i', 1), ('center_of_gravity', 816, 'f', 3), ('gear_up_revs', 828, 'f', 1), ('gear_dn_revs', 832, 'f', 1),
]


def main():
    elf, out = sys.argv[1], sys.argv[2]
    e = open(elf, 'rb').read()
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 + UC_MODE_LITTLE_ENDIAN)
    mu.mem_map(0, 0x4000000)
    mu.mem_write(0x100000, e[0x1000:0x1000 + 0x52558C])
    mu.mem_map(0x10000000, 0x1000)
    mu.reg_write(UC_MIPS_REG_GP, GP); mu.reg_write(UC_MIPS_REG_SP, 0x3F00000); mu.reg_write(UC_MIPS_REG_RA, STOP)

    # func_1E0D8C = memset(a0, a1, a2) written with R5900 128-bit MMI ops Unicorn cannot run: do it here.
    def memset(uc, addr, size, user):
        a0, a1, a2 = (uc.reg_read(r) & 0xFFFFFFFF for r in (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2))
        uc.mem_write(a0, bytes([a1 & 0xFF]) * a2)
        uc.reg_write(UC_MIPS_REG_V0, a0); uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))
    mu.hook_add(UC_HOOK_CODE, memset, begin=0x1E0D8C, end=0x1E0D8C)
    mu.emu_start(0x1596F8, STOP, count=50_000_000)
    mem = bytes(mu.mem_read(0x100000, 0x600000))

    def cstr(va):
        if not 0x100000 <= va < 0x700000: return None
        o = va - 0x100000; end = mem.find(b'\0', o)
        t = mem[o:end]
        return t.decode('latin1') if 0 < len(t) < 64 and all(32 <= c < 127 for c in t) else None

    rows = []
    for o in range(0, len(mem) - 840, 4):
        i, g, pn, prn = struct.unpack_from('<4I', mem, o)
        if i < 64 and g < 16 and cstr(pn) and cstr(prn) and (cstr(struct.unpack_from('<I', mem, o + 20)[0]) or '').upper().startswith('CARS'):
            rec = {}
            for name, off, kind, n in FIELDS:
                if kind == 's': rec[name] = cstr(struct.unpack_from('<I', mem, o + off)[0])
                else:
                    v = struct.unpack_from('<%d%s' % (n, 'i' if kind == 'i' else 'f'), mem, o + off)
                    rec[name] = [round(x, 5) for x in v] if kind == 'f' and n > 1 else (round(v[0], 5) if kind == 'f' else v[0] if n == 1 else list(v))
            rec['va'] = hex(o + 0x100000)
            rows.append(rec)
    json.dump(rows, open(out, 'w'), indent=1)
    for r in rows:
        print(r['Id'], r['Group'], r['pName'], '|', r['pRealName'], '| mass', r['Mass'], 'gears', r['num_gears'], 'redline', r['redline'],
              'torque split', r['TorqueSplit'], 'wheel r', r['wheel_radius'])


if __name__ == '__main__':
    main()
