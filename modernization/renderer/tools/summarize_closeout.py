"""Read-only closeout digest; retain input hashes, never copy captures into Git."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

EXE = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
PRE_FIX = '307a5fe4c83d95bd14d460cf767aa751e94b7f0a8e962c8c29c67681f2c17313'

def session_counts(rows):
    summaries = [r for r in rows if r['type'] == 'frame_summary']
    resets = [r for r in rows if r['type'] == 'reset']
    return {'summaries': len(summaries),
            'present_failures': sum(r['present_hresult'] != 0 for r in summaries),
            'bypass_suspected': sum(bool(r['bypass_suspected']) for r in summaries),
            'reset_success': sum(r['hresult'] == 0 for r in resets),
            'reset_failures': sum(r['hresult'] != 0 for r in resets),
            'reset_dimensions': sorted({(r['parameters_after']['width'], r['parameters_after']['height']) for r in resets})}

def source_angle(bits):
    if len(bits) != 16:
        return None
    f = struct.unpack('<16f', struct.pack('<16I', *bits))
    if not all(map(math.isfinite, f)) or f[0] <= 0 or f[5] <= 0:
        return None
    if f[11] != 1 or f[10] <= 1 or f[14] >= 0 or any(f[i] != 0 for i in range(16) if i not in (0,5,10,11,14)):
        return None
    aspect = f[5]/f[0]
    vfov = math.degrees(2*math.atan(1/f[5]))
    return {'vfov': vfov, 'aspect': aspect, 'source_angle': vfov*max(1,aspect)}

def digest(logs, brokers):
    result = {'exe_sha256': EXE, 'pre_fix_dll_sha256': PRE_FIX, 'sessions': [], 'projections': [], 'broker_camera_setup': []}
    for p in sorted(logs.glob('*.jsonl')):
        raw = p.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        if not rows or rows[0].get('exe_sha256') != EXE or rows[0].get('proxy_sha256') != PRE_FIX:
            continue
        identity = {'file': p.name, 'sha256': hashlib.sha256(raw).hexdigest()}
        if rows[0]['type'] == 'session':
            result['sessions'].append(dict(identity, **session_counts(rows)))
        elif rows[0]['type'] == 'frame_begin':
            values = []
            for r in rows:
                if r.get('method') == 'SetTransform' and r.get('arguments', [0])[0] == 3 and r.get('caller', {}).get('return_rva') == 0x13fa75:
                    value = source_angle(r.get('payload_bits', []))
                    if value is not None and value not in values:
                        values.append(value)
            result['projections'].append(dict(identity, values=values))
    for p in sorted(brokers.glob('*gfx3*.json')):
        raw = p.read_bytes()
        for entry in json.loads(raw)['entries']:
            if entry['path'] == 'Camera/Setup':
                xml = '\n'.join(entry.get('continuation_lines', []))
                values = {v.attrib['Name']: v.attrib['Value'] for v in ET.fromstring(xml)}
                result['broker_camera_setup'].append({'file': p.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'values': values})
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('logs', type=Path)
    ap.add_argument('brokers', type=Path)
    args = ap.parse_args()
    print(json.dumps(digest(args.logs, args.brokers), indent=2))

if __name__ == '__main__':
    main()
