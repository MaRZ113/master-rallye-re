"""Read-only MR follow-camera model-extents diagnostics; no camera patch.

The arithmetic is qualified by exact retail instructions 0052C630..0052C6C2.
Optional x86 replay executes that original initializer, stubbing the model
bounds lookup and subsequent update callback. No gameplay pose is simulated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]
from master_rallye.bounds import parse_bounds1339
from master_rallye.dx import parse_dx_bytes
from master_rallye.addon_sdk.vehicle_shadow import runtime_bounds
from master_rallye.vehicle_physics_binding import parse_pe32_layout

SHA = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
ANCHORS = {
    0x52c630: '83ec0c33c0568bf1578b7c24188a4e3c',
    0x52c67c: 'd94024d94028d864241083c02057',
    0x52c68e: 'd9e1d80d58f96800d95e40d8642410d9e1d95e44',
    0x68f958: '0000003f',
}


def verify(exe):
    if hashlib.sha256(exe).hexdigest() != SHA:
        raise ValueError('unqualified camera diagnostic executable')
    layout = parse_pe32_layout(exe)
    for address, hx in ANCHORS.items():
        offset = layout.va_to_file_offset(address)
        if exe[offset:offset + len(bytes.fromhex(hx))].hex() != hx:
            raise ValueError('camera instruction anchor mismatch')


def extent_terms(minimum, maximum):
    if len(minimum) != 3 or len(maximum) != 3 or not all(math.isfinite(x) for x in (*minimum, *maximum)) or any(a > b for a, b in zip(minimum, maximum)):
        raise ValueError('finite ordered model bounds required')
    return {'half_length_m': abs(maximum[2] - minimum[2]) * .5,
            'height_m': abs(maximum[1] - minimum[1])}


def camera_settings(raw):
    if len(raw) > 1024 * 1024 or b'<!' in raw:
        raise ValueError('bounded plain Cameras XML required')
    root = ET.fromstring(raw)
    records = {}
    for value in root.findall('./Broker/Value'):
        name = value.get('Name')
        if name not in ('Camera/Setup', 'Camera/SplitSetup'):
            continue
        if name in records:
            raise ValueError('duplicate camera setup')
        entries = value.findall('./gaCameraManagerParams/Value')
        if len({v.get('Name') for v in entries}) != len(entries):
            raise ValueError('duplicate camera setting')
        records[name] = {v.get('Name'): {'type': v.get('Type'), 'value': v.get('Value')} for v in entries}
    if not records:
        raise ValueError('native camera setups absent')
    return records


def inspect_model(path):
    raw = Path(path).read_bytes()
    model = parse_dx_bytes(raw)
    if not model.diagnostics.validated:
        raise ValueError('unvalidated source DX')
    bounds = parse_bounds1339(model.collision.unparsed_data)
    if bounds is None:
        raise ValueError('qualified model bounds absent')
    positions = model.vertices.positions
    render_min = tuple(min(v[i] for v in positions) for i in range(3))
    render_max = tuple(max(v[i] for v in positions) for i in range(3))
    source = extent_terms(bounds.minimum, bounds.maximum)
    render = extent_terms(render_min, render_max)
    ordered_y = sorted(v[1] for v in positions)
    return {'path': str(Path(path).resolve()), 'sha256': hashlib.sha256(raw).hexdigest(),
            'stored_bounds': bounds.to_dict(), 'native_extents_terms': source,
            'render_vertex_bounds': {'minimum': render_min, 'maximum': render_max},
            'render_only_terms': render,
            'render_y_percentile_99_diagnostic_only': ordered_y[int((len(ordered_y) - 1) * .99)],
            'highest_unique_vertices_diagnostic_only': sorted(set(positions), key=lambda v: v[1])[-6:],
            'bounds_minus_render': {k: source[k] - render[k] for k in source},
            'boundary': 'Native source bounds include collision geometry where authored. Render-only terms are diagnostic; no footer or collision is rewritten.'}


def replay_initializer(exe, minimum, maximum, enabled=True):
    verify(exe)
    from validate_vehicle_physics_forces import machine, ptr, get
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX, UC_X86_REG_ECX as CX, UC_X86_REG_EDX as DX, UC_X86_REG_ESP as SP, UC_X86_REG_EIP as IP
    u = machine(exe)
    camera, frame, box, vtable, update, stop = (0x2000000 + o for o in (0, 0x1000, 0x2000, 0x3000, 0x4000, 0x5000))
    serialized = struct.pack('<I3ff3f3f', 1339, 0, 0, 0, 3, *minimum, *maximum)
    u.mem_write(box, runtime_bounds(serialized))
    ptr(u, camera, vtable); ptr(u, vtable + 0x10, update)
    u.mem_write(update, bytes.fromhex('c20400'))
    u.mem_write(camera + 0x3c, bytes((int(enabled),)))
    ptr(u, frame + 0x50, 0x2006000)
    stack = 0x100f000
    ptr(u, stack, stop); ptr(u, stack + 4, frame)
    calls = []
    def hook(uc, address, size, data):
        if address == 0x4f5bc0:
            calls.append(uc.reg_read(CX))
            sp = uc.reg_read(SP)
            uc.reg_write(IP, struct.unpack('<I', uc.mem_read(sp, 4))[0])
            uc.reg_write(SP, sp + 4); uc.reg_write(AX, box)
            uc.reg_write(CX, 0xdeadbeef); uc.reg_write(DX, 0xdeadbeef)
    u.hook_add(UC_HOOK_CODE, hook)
    u.reg_write(SP, stack); u.reg_write(CX, camera)
    u.emu_start(0x52c630, stop, count=500)
    result = {'half_length_m': get(u, camera + 0x40), 'height_m': get(u, camera + 0x44)}
    expected = extent_terms(minimum, maximum) if enabled else {'half_length_m': 0., 'height_m': 0.}
    if u.reg_read(IP) != stop or any(abs(result[k] - expected[k]) > 1e-5 for k in result):
        raise ValueError('original camera initializer arithmetic mismatch')
    return {'status': 'PASS_ORIGINAL_X86_INITIALIZER', 'terms': result, 'use_model_extents': enabled,
            'bounds_getter_calls': len(calls), 'runtime_qualified': False,
            'boundary': 'Original x87 instructions and stack shifts execute; model lookup and following camera update are stubbed. Not a live camera or complete follow simulation.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, action='append', required=True)
    p.add_argument('--cameras', type=Path)
    p.add_argument('--exe', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = {'status': 'READ_ONLY_CAMERA_DIAGNOSTIC', 'models': [inspect_model(x) for x in a.model],
              'runtime_camera_modified': False}
    if a.cameras:
        raw = a.cameras.read_bytes()
        result['global_setups'] = camera_settings(raw)
        result['camera_xml_sha256'] = hashlib.sha256(raw).hexdigest()
    if a.exe:
        exe = a.exe.read_bytes()
        result['native_replay'] = [replay_initializer(exe, row['stored_bounds']['minimum'], row['stored_bounds']['maximum'], flag)
                                   for row in result['models'] for flag in (True, False)]
    if a.output.exists():
        raise ValueError('new diagnostic report required')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], len(result['models']))


if __name__ == '__main__': main()
