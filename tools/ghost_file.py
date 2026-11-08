#!/usr/bin/env python3
"""Decode and audit Master Rallye `.ghost` files (retail SplineManager format v3).

Layout reconstructed from retail MRallye.exe (SHA256 bf8aef32...):
reader 0x4BBA00, record parser 0x4BCEB0 / writer 0x4BCBD0, sample codec
0x4BADC0 (decode) / 0x4BAA10 (encode), extra channels 0x4BA8B0/0x4BA8F0/0x4BA9B0.
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

MAGIC = 0xAB59D02E
VERSION = 3
POS_DELTA_RANGE = 10.0          # 0x6911B0
INV_32767 = 3.0518509447574615e-05  # 0x691124
INV_16383 = 6.103888154029846e-05   # 0x6911CC
INV_127 = 0.007874015718698502      # 0x6911C4
PI = 3.141592502593994              # 0x6911DC
KEY_INTERVAL = 10                   # DAT_006F6980 reload value


class Reader:
    def __init__(self, data: bytes):
        self.d, self.o = data, 0

    def take(self, n: int) -> bytes:
        if self.o + n > len(self.d):
            raise ValueError(f"read past end at {self.o:#x} (+{n})")
        b = self.d[self.o:self.o + n]
        self.o += n
        return b

    def u8(self): return self.take(1)[0]
    def i8(self): return struct.unpack("<b", self.take(1))[0]
    def i16(self): return struct.unpack("<h", self.take(2))[0]
    def i32(self): return struct.unpack("<i", self.take(4))[0]
    def f32(self): return struct.unpack("<f", self.take(4))[0]
    def string(self): return self.take(self.i32()).decode("latin-1")


@dataclass
class Sample:
    pos: tuple[float, float, float]
    fwd: tuple[float, float, float]
    roll: float
    key: bool
    steer: float = 0.0
    susp: tuple[float, ...] = ()
    spin: float = 0.0


@dataclass
class Ghost:
    time: float
    splits: list[float]
    car: str
    race: str
    params: list[bytes]
    samples: list[Sample] = field(default_factory=list)
    times: list[float] = field(default_factory=list)
    tail: bytes = b""
    payload_end: int = 0
    payload_size: int = 0


def decode_samples(r: Reader, count: int) -> list[Sample]:
    out, counter, prev = [], 0, (0.0, 0.0, 0.0)
    for _ in range(count):
        counter -= 1
        key = True
        if counter < 0:
            pos = struct.unpack("<3f", r.take(12))
            counter = KEY_INTERVAL
        else:
            sy = r.i16()
            if sy < 0:
                pos = struct.unpack("<3f", r.take(12))
                counter = KEY_INTERVAL
            else:
                key = False
                sx, sz = r.i16(), r.i16()
                pos = (sx * POS_DELTA_RANGE * INV_32767 + prev[0],
                       (sy - 0x4000) * POS_DELTA_RANGE * INV_16383 + prev[1],
                       sz * POS_DELTA_RANGE * INV_32767 + prev[2])
        prev = pos
        fx_raw, fz_raw = r.i16(), r.i16()
        fx = fx_raw * INV_32767
        fz = ((fz_raw + 0x4000) if fz_raw < 1 else (fz_raw - 0x4000)) * INV_16383
        rad = 1.0 - fx * fx - fz * fz
        fy = math.sqrt(rad) if rad >= 0 else float("nan")
        if fz_raw < 1:
            fy = -fy
        rb = r.i8() * INV_127
        roll = (rb * rb if rb >= 0 else -(rb * rb)) * PI
        s = Sample(pos, (fx, fy, fz), roll, key)
        s.steer = r.i8() * 1.0 * INV_127
        s.susp = tuple((0.25 + 0.8) * r.u8() * 0.00390625 - 0.8 for _ in range(4))
        sb = r.i8() * 24.0 * INV_127
        s.spin = sb * sb if sb >= 0 else -(sb * sb)
        out.append(s)
    return out


def parse(path: Path) -> Ghost:
    data = path.read_bytes()
    r = Reader(data)
    magic, ver, size = struct.unpack("<IiI", r.take(12))
    if magic != MAGIC or ver != VERSION:
        raise ValueError(f"{path}: bad header {magic:#x} v{ver}")
    t = r.f32()
    splits = [r.f32() for _ in range(r.u8())]
    car, race = r.string(), r.string()
    params = [r.take(4) for _ in range(8)]
    n = r.i32()
    g = Ghost(t, splits, car, race, params, payload_size=size)
    g.samples = decode_samples(r, n)
    g.times = [r.f32() for _ in range(r.i32())]
    g.tail = r.take(1 + 4 + 16 + 4 + 1 + 1)
    g.payload_end = r.o
    return g


def audit(g: Ghost, jump: float) -> list[str]:
    issues = []
    if len(g.times) != len(g.samples):
        issues.append(f"times {len(g.times)} != samples {len(g.samples)}")
    for i in range(1, len(g.times)):
        if g.times[i] < g.times[i - 1]:
            issues.append(f"time goes backwards at {i}: {g.times[i-1]:.3f} -> {g.times[i]:.3f}")
        elif g.times[i] == g.times[i - 1]:
            issues.append(f"duplicate time at {i}: {g.times[i]:.3f}")
    for i, s in enumerate(g.samples):
        if any(math.isnan(v) for v in s.fwd):
            issues.append(f"NaN forward at {i} t={g.times[i] if i < len(g.times) else '?'}")
        if i:
            d = math.dist(s.pos, g.samples[i - 1].pos)
            dt = (g.times[i] - g.times[i - 1]) if i < len(g.times) else 0.0
            if d > jump:
                issues.append(f"jump {d:.1f} m at {i} (dt {dt:.3f} s, key={s.key})")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", type=Path, nargs="+")
    ap.add_argument("--jump", type=float, default=15.0, help="report position steps above this (m)")
    ap.add_argument("--dump", action="store_true", help="print every sample")
    a = ap.parse_args()
    for p in a.files:
        g = parse(p)
        print(f"== {p.name}: car={g.car} race={g.race} time={g.time:.2f} splits={[round(x, 2) for x in g.splits]}"
              f" samples={len(g.samples)} times={len(g.times)} params={[x.hex() for x in g.params]}"
              f" end={g.payload_end}/{g.payload_size + 12}")
        if a.dump:
            for i, s in enumerate(g.samples):
                t = g.times[i] if i < len(g.times) else float("nan")
                print(f"{i:5d} t={t:8.3f} key={int(s.key)} pos=({s.pos[0]:9.2f},{s.pos[1]:8.2f},{s.pos[2]:9.2f})"
                      f" fwd=({s.fwd[0]:6.3f},{s.fwd[1]:6.3f},{s.fwd[2]:6.3f}) roll={s.roll:6.3f}")
        issues = audit(g, a.jump)
        print(f"   issues: {len(issues)}")
        for line in issues[:40]:
            print("   ", line)


if __name__ == "__main__":
    sys.exit(main())
