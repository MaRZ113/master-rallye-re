"""AUDIO-RALLY1 engine tone layer (Vehicle Manager): de-clipped native engine synthesis + pitched stock engine loops.

Findings (v-cap tools/engine_brightness_audition.py, original DSP in Unicorn, 2026-11-18):
* the native generator 005A7C30 mixes dry / low-pass / band-pass by the second synthesis table rows 3 / 4 / 5
  (005A7950; 205 = unity); with the stock weights ~20 % of the output samples clip (flat tops = the muddy sound);
* the native RPM -> pitch curve is compressive: a loop plays at x1.0 only near the limiter (x0.38 at 4000 of 7500 rpm).

This layer (owner choice "3-clean-pitched", 2026-11-18):
* copies the four curve groups' second arrays (A..D) into the roster payload with rows 3..5 scaled by `mix`, and points
  the five code immediates that load them (0x409B51 / 0x409C06 A, 0x409B7F B, 0x409BAD C, 0x409BDB D) at the copies;
* writes the stock engine loops (DataAudio/vehicles/engine*.wav, rev9.wav) into the overlay pitched up by `pitch`
  (cyclic linear resampling: still a seamless loop). SDK engines (DataAudio/vehicles/sdk/...) are untouched.
"""
from __future__ import annotations

import struct
import wave
from pathlib import Path

from roster_v4 import Image, Rvp
from frontend_classes import IMAGE_BASE, PAYLOAD_VA

GROUPS = {'A': (0x68FA14, (0x409B51, 0x409C06)), 'B': (0x68FBF4, (0x409B7F,)), 'C': (0x68FB04, (0x409BAD,)),
          'D': (0x68FCE4, (0x409BDB,))}
MIX_ROWS = (3, 4, 5)
STOCK_LOOPS = ('engine2', 'engine3', 'engine4', 'engine5', 'engine9', 'rev9')


def scaled_table(exe: bytes, va: int, mix: float) -> bytes:
    fo = va - IMAGE_BASE                                  # .rdata: file offset == RVA
    vals = list(struct.unpack_from('<60H', exe, fo))
    for r in MIX_ROWS:
        for i in range(9):                                # entry 9 = 65535 sentinel
            vals[r * 10 + i] = max(0, min(1200, round(vals[r * 10 + i] * mix)))
    return struct.pack('<60H', *vals)


def apply_native(v1: bytes, exe: bytes, writable, mix: float) -> tuple[bytes, dict]:
    if not (.1 <= mix <= 2.):
        raise ValueError('engine mix scale outside 0.1..2')
    rvp_off, rvp_size, ext_off, ext_size = struct.unpack_from('<4I', v1, 144)
    if rvp_off != 256 or ext_off != rvp_off + rvp_size or ext_off + ext_size != len(v1):
        raise ValueError('unexpected MRVR v1 layout')
    img = Image(v1[ext_off:], Rvp(v1[rvp_off:ext_off]), writable, exe)
    while len(img.payload) % 16: img.payload.append(0)
    tables, ops = {}, []
    for g, (va, sites) in GROUPS.items():
        tables[g] = PAYLOAD_VA + len(img.payload); img.payload += scaled_table(exe, va, mix)
        for site in sites:
            fo = site - IMAGE_BASE
            if struct.unpack_from('<I', exe, fo)[0] != va:
                raise ValueError(f'engine table immediate at {site:#x} is not {va:#x}')
            if img.rvp.op_at(site)[0] or img.rvp.op_at(site + 3)[0]:
                raise ValueError(f'engine table immediate at {site:#x} is already owned')
            img.rvp.ops.append({'fo': fo, 'rva': fo, 'len': 4, 'flags': 0, 'page': 1, 'before': exe[fo:fo + 4],
                                'after': bytearray(struct.pack('<I', tables[g]))})
            ops.append({'va': hex(site), 'table': g, 'to': hex(tables[g])})
    rvp = img.rvp.build(); payload = bytes(img.payload)
    header = bytearray(v1[:256])
    if len(payload) > struct.unpack_from('<I', header, 20)[0]:
        raise ValueError(f'native payload {len(payload)} exceeds the roster allocation {struct.unpack_from("<I", header, 20)[0]}')
    struct.pack_into('<I', header, 24, len(payload))
    struct.pack_into('<4I', header, 144, 256, len(rvp), 256 + len(rvp), len(payload))
    from vehicle_roster_build import fnv64
    struct.pack_into('<Q', header, 160, fnv64(rvp + payload))
    return bytes(header) + rvp + payload, {'mix': mix, 'operations': ops, 'tables': {g: hex(v) for g, v in tables.items()}}


def pitched_loop(src: Path, pitch: float) -> bytes:
    import io
    with wave.open(str(src)) as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f'{src.name}: mono PCM16 expected')
        rate, raw = w.getframerate(), w.readframes(w.getnframes())
    x = struct.unpack('<%dh' % (len(raw) // 2), raw)
    n = max(16, round(len(x) / pitch)); out = []
    for i in range(n):
        t = i * len(x) / n; k = int(t); f = t - k
        out.append(max(-32768, min(32767, round(x[k] * (1 - f) + x[(k + 1) % len(x)] * f))))
    bio = io.BytesIO()
    with wave.open(bio, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(struct.pack('<%dh' % n, *out))
    return bio.getvalue()


def install_loops(res: Path, game: Path, pitch: float) -> list[str]:
    if not (.5 <= pitch <= 3.):
        raise ValueError('engine pitch outside 0.5..3')
    done = []
    for name in STOCK_LOOPS:
        src = game / 'DataAudio' / 'vehicles' / (name + '.wav')
        if not src.is_file():
            continue
        out = res / 'DataAudio' / 'vehicles' / (name + '.wav'); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pitched_loop(src, pitch)); done.append(out.relative_to(res).as_posix())
    return done
