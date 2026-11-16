"""Dump the PS2 Rally Championship (SLES-50763) stage table and string-resolved
stage info. The table is TRACK_DEFINITIONS[] (140-byte records, layout from the
STABS debug types in SLES_507.63) at VA 0x5FEAF0.

Usage: python -I ps2_tables.py <disc dir> <out.json>
"""
import json
import re
import struct
import sys
from pathlib import Path

TABLE_VA = 0x5FEAF0
VA_TO_OFF = 0xFF000
# STR_ enum values from the STABS type "strings" (first entries of each group)
STR_DESC0, STR_WEATHER0, STR_SURFACE0 = 682, 722, 758
RALLIES = {0: 'Kenya', 1: 'Scotland', 2: 'Wales', 3: 'Manx', 4: 'Arctic', 5: 'USA', 6: 'Special/Multiplayer'}
TYRES = {0: 'tarmac', 1: 'gravel', 2: 'ice', 3: 'snow'}


def strings(path):
    """STRINGS.ENG: ';<KEY>' comment then value lines; returns key -> text."""
    vals, cur = {}, None
    for line in path.read_bytes().decode('latin1').splitlines():
        s = line.strip()
        if s.startswith(';'):
            t = s.lstrip(';').strip().rstrip(',').split()
            if t and t[0].startswith('STR_'):
                cur = t[0].rstrip(',')
            continue
        if cur and s:
            vals.setdefault(cur, []).append(s)
    return {k: ' / '.join(v).replace('\\n', ' / ') for k, v in vals.items()}


def text_for(sid, st):
    for base, key in ((STR_SURFACE0, 'SURFACE'), (STR_WEATHER0, 'WEATHER'), (STR_DESC0, 'DESC')):
        if base <= sid < base + 36:
            return st.get(f'STR_FRONTEND_STAGE_{key}_{sid - base}', '')
    extra = {969: 'DESC_50', 970: 'SURFACE_50', 971: 'WEATHER_50', 972: 'DESC_57', 973: 'SURFACE_57',
             974: 'WEATHER_57', 975: 'DESC_58', 976: 'SURFACE_58', 977: 'WEATHER_58', 978: 'DESC_59',
             979: 'SURFACE_59', 980: 'WEATHER_59'}
    return st.get('STR_FRONTEND_STAGE_' + extra[sid], '') if sid in extra else ''


def main():
    disc, out = Path(sys.argv[1]), Path(sys.argv[2])
    b = (disc / 'SLES_507.63').read_bytes()
    st = strings(disc / 'STRINGS' / 'STRINGS.ENG')

    def cstr(va):
        if not va:
            return ''
        o = va - VA_TO_OFF
        return b[o:b.index(b'\0', o)].decode('latin1')

    rows = []
    for i in range(64):
        o = TABLE_VA - VA_TO_OFF + i * 140
        f = struct.unpack_from('<35I', b, o)
        if not (0 <= f[0] < 100 and f[2] > 0x100000):
            break
        fl = struct.unpack_from('<35f', b, o)
        track = cstr(f[18])
        # test/placeholder rows (TestBana, Surface Test, Farmland Dash, ...) are not real stages
        used = (track.startswith('TRACKS\\') and cstr(f[1]).isdigit()
                and not re.search(r'test|farmland|somename', cstr(f[2]), re.I))
        r = {
            'index': i, 'track_id': f[0], 'map_file': f'MAP{cstr(f[1])}' if used else None,
            'name': cstr(f[2]), 'flag_sprite': cstr(f[4]), 'tyre': TYRES.get(f[7], f[7]),
            'flags': hex(f[8]), 'length_km': round(fl[9], 2), 'rally': RALLIES.get(f[11], f[11]), 'rain_flag': bool(f[8] & 0x10), 'snowfall_flag': bool(f[8] & 0x2),
            'stage_in_rally': f[12], 'source_track': track,
            'fog_rgb': f'{f[19] & 0xFFFFFF:06x}', 'fog_sat_far': fl[20], 'fog_sat_near': fl[21],
            'fog_sat_sky': fl[22], 'fog_far_m': fl[23], 'object_sun_base': fl[24],
            'object_sun_amp': fl[25], 'car_reflection': fl[26],
            'surface': text_for(f[14], st), 'weather': text_for(f[15], st), 'used': used,
        }
        rows.append(r)
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + '\n', encoding='utf8')
    for r in rows:
        if r['used']:
            print(r['map_file'], r['rally'], r['stage_in_rally'], r['name'], r['tyre'], r['flags'],
                  r['length_km'], '|', r['weather'], '|', r['surface'], '| fog', r['fog_rgb'], r['fog_far_m'])


if __name__ == '__main__':
    main()
