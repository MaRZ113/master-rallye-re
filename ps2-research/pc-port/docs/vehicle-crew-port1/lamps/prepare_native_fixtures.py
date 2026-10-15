"""Create ignored original-PC upload fixtures; never package these proprietary bytes."""
from pathlib import Path
import hashlib, importlib.util, json, struct

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]

def main():
    spec = importlib.util.spec_from_file_location('lamp_original_pc', PORT / 'docs/full-coverage/vehicles/audit.py')
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    registry = json.loads((HERE / 'source-registry.json').read_text())
    fleet = {r['pc_family']: r for r in json.loads((HERE.parent / 'fleet/coverage.json').read_text())['fleet'] if r['pc_family']}
    cases = []
    for family in registry['families']:
        pc_family = family['pc_family']
        selected = [m for m in family['meshes'] if m['mode'] == 14 and len(m['pc_candidates']) == 1]
        if pc_family == 'Xtrail':
            selected += [m for m in family['meshes'] if m['path'] in ('root.20.0.0', 'root.20.1.0')]
        if not selected:
            continue
        path = a.PC / pc_family / 'car.dx'
        if a.sha(path.read_bytes()) != fleet[pc_family]['models']['CAR']['pc_compiled_source']['sha256']:
            raise ValueError('Original PC source drift: ' + pc_family)
        pc = a.parse_dx(path)
        for mesh in selected:
            candidate = mesh['pc_candidates'][0]
            draw = list(pc.physical_draws)[candidate['record']]
            ids = pc.draw_global_indices(draw)
            first = min(ids)
            count = max(ids) - first + 1
            kind = 2 if mesh['mode'] == 14 else 0 if mesh['mode'] == 3 else 1
            stride = 32 if kind == 2 else 36
            vertices = b''.join(
                struct.pack('<3f3f', *pc.vertices.positions[i], *pc.vertices.normals[i])
                + (b'' if kind == 2 else struct.pack('<I', 0xffffffff))
                + struct.pack('<2f', *pc.uv_sets[0].values[i])
                for i in range(first, first + count))
            indices = struct.pack('<%dI' % len(ids), *(i - first for i in ids))
            cases.append(struct.pack('<4I', kind, count, len(ids)//3, stride) + vertices + indices)
    if len(cases) != 22:
        raise ValueError('Expected 20 glow + Xtrail OFF/ON fixtures')
    binary = b'PS2LMP01' + struct.pack('<I', len(cases)) + b''.join(cases)
    out = PORT / '.assets/vehicles/crew-port1-native-lamps.bin'
    out.write_bytes(binary)
    print(json.dumps({'path': str(out), 'cases': len(cases), 'sha256': hashlib.sha256(binary).hexdigest()}))

if __name__ == '__main__':
    main()
