"""Read-only, hash-locked verification of the R-GFX4-3 camera/culling seams.

Print a compact JSON map. Never executes, patches or copies the game image.
Optional Ghidra exports contribute assembly digests, not authoritative C types.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from verify_proxy import PE

TARGET_SHA = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
ROOT = Path(__file__).resolve().parents[1]
SITES = (
    (0x004F2350, 'SourceVerticalAngle', '83ec088b81840000008b9180000000', None),
    (0x004F2380, 'SphereVisibility', 'd9442410d81d3cf5680083ec0c56', None),
    (0x004F2620, 'BuildSidePlanes', '83ec785355568bf1578b8684000000', None),
    (0x00561537, 'ProjectionAngleCall', 'e8140ef9ff', 0x004F2350),
    (0x0054CA9B, 'ModelBoundsVisibilityCall', 'e8e058faff', 0x004F2380),
    (0x004B7027, 'BodyModelBind', 'e844eb0300', 0x004F5B70),
    (0x004B71E1, 'WheelModelBind', 'e88ae90300', 0x004F5B70),
    (0x006532D1, 'SubmitScheduleContext', '8b40203bfb0f94c151578bc8e89e63ebff', None),
    (0x006532DD, 'PreSubmitCallHook', 'e89e63ebff', 0x00509680),
)
FUNCTIONS = (0x004F2350, 0x004F2380, 0x004F2620, 0x004E3DA0,
             0x00522600, 0x00653080, 0x00509680, 0x0054C9D0,
             0x0056BBC0, 0x004B6A00, 0x00431FB0, 0x004C4E90,
             0x00509810, 0x00509970)

def hx(n):
    return f'0x{n:08X}'

def verify_sites(blob, pe):
    rows = []
    if pe.image_base != 0x400000:
        raise ValueError('Unsupported image base')
    for va, role, signature, target in SITES:
        expected = bytes.fromhex(signature)
        actual = blob[pe.offset(va-pe.image_base, len(expected)):][:len(expected)]
        if actual != expected:
            raise ValueError(f'Signature mismatch at {hx(va)}')
        if target is not None:
            decoded = va+5+struct.unpack('<i', actual[1:5])[0]
            if actual[0] != 0xE8 or decoded != target:
                raise ValueError('Relative CALL target mismatch')
        rows.append(dict(va=hx(va), rva=hx(va-pe.image_base), role=role,
                         expected_bytes=signature, call_target=hx(target) if target else None,
                         evidence_grade='CONFIRMED_BY_EXE', source='hash-locked pristine bytes'))
    return rows

def angle_model(width, height, vfov=80):
    if not (0 < width <= 16384 and 0 < height <= 16384 and math.isfinite(vfov) and 30 <= vfov <= 110):
        raise ValueError('Unsupported dimensions or VFOV')
    aspect = width/height
    stock_v = 90/max(1, aspect)
    effective_h = math.degrees(2*math.atan(math.tan(math.radians(vfov/2))*aspect))
    implied_source = vfov*max(1, aspect)
    return dict(width=width, height=height, aspect=aspect, stock_vfov=stock_v,
                stock_cpu_hfov=90*min(1, aspect),
                target_vfov=vfov, target_hfov=effective_h,
                linear_source_if_used=implied_source,
                linear_source_safe=implied_source < 180,
                policy='side planes use actual perspective HFOV; source angle remains90',
                evidence_grade='STATIC_MODEL_NOT_RUNTIME')

def inspect(blob, exports=None):
    digest = hashlib.sha256(blob).hexdigest()
    if digest != TARGET_SHA:
        raise ValueError('Not pristine retail: '+digest)
    pe = PE(blob)
    rows = verify_sites(blob, pe)
    evidence = []
    if exports:
        exports = Path(exports)
        provenance = json.loads((exports/'provenance.json').read_text(encoding='utf-8'))
        if provenance.get('sha256') != TARGET_SHA or provenance.get('project_writable') or provenance.get('program_saved') or provenance.get('transaction') != 'ROLLED_BACK':
            raise ValueError('Ghidra provenance is not exact/read-only')
        for va in FUNCTIONS:
            value = json.loads((exports/f'{va:08x}.json').read_text(encoding='utf-8'))
            assembly = '\n'.join(value['assembly'])+'\n'
            evidence.append(dict(va=hx(va), rva=hx(va-0x400000), instructions=len(value['assembly']),
                                 assembly_sha256=hashlib.sha256(assembly.encode('utf-8')).hexdigest(),
                                 source=provenance['exporter'], project_writable=False,
                                 decompiler_types_authoritative=False, evidence_grade='CONFIRMED_BY_EXE'))
    return dict(schema_version=1, build=dict(sha256=digest, size=len(blob), image_base=hx(pe.image_base)),
                sites=rows, ghidra_evidence=evidence,
                camera=dict(owner='CameraManager+4*index', manager_pointer_va='0x006F94DC',
                            source_angle_offset='0x00', plane_offsets=['0x08','0x14','0x20','0x2C'],
                            viewport_offsets=['0x78','0x7C','0x80','0x84'],
                            old_pose_offset='0x38', current_pose_offset='0x88',
                            position_offset='0xB8', forward='negative current_pose row2',
                            evidence_grade='CONFIRMED_BY_EXE'),
                models=[angle_model(640,480), angle_model(1920,1027), angle_model(1920,1027,110)],
                runtime_status='PENDING_HUMAN_EDGE_AND_CAMERA_RETEST')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('binary', type=Path)
    ap.add_argument('--exports', type=Path)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    if a.output:
        output = a.output.resolve()
        if output.suffix != '.json' or not any(output.is_relative_to(ROOT/p) for p in ('data','.analysis','research')):
            raise ValueError('JSON output must stay inside this renderer phase')
    result = inspect(a.binary.read_bytes(), a.exports)
    text = json.dumps(result, indent=2)+'\n'
    if a.output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding='utf-8', newline='\n')
    else:
        print(text, end='')

if __name__ == '__main__':
    main()
