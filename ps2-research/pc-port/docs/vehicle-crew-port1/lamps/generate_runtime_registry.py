"""Reproduce the admitted native glow registry from verified source metadata."""
from pathlib import Path
import json, sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]

def generate():
    registry = json.loads((HERE / 'source-registry.json').read_text())
    fleet = {f['pc_family']: f for f in json.loads((HERE.parent / 'fleet/coverage.json').read_text())['fleet'] if f['pc_family']}
    rows = []
    for family in registry['families']:
        for mesh in family['meshes']:
            if mesh['mode'] != 14 or len(mesh['pc_candidates']) != 1:
                continue
            candidate = mesh['pc_candidates'][0]
            draw = fleet[family['pc_family']]['models']['CAR']['pc_compiled_source']['draws'][candidate['record']]
            rows.append((family['pc_family'], draw['vertices'], draw['faces'], draw['geometry_sha256'], candidate['position_uv_corner_sha256']))
    if len(rows) != 20 or len({r[3:] for r in rows}) != 20:
        raise ValueError('Ambiguous native glow registry')
    return ('#pragma once\nnamespace gfx2::ps2port {\n'
            'struct BrakeGlowProfile {const char* family;unsigned vertices,triangles;const char* geometry;const char* positionUv;};\n'
            'inline constexpr BrakeGlowProfile kBrakeGlowProfiles[]={\n'
            + ''.join(' {"%s",%du,%du,"%s","%s"},\n' % row for row in rows)
            + '};\n}\n')

if __name__ == '__main__':
    path = PORT / 'renderer/brake_glow_registry.hpp'
    expected = generate()
    if '--check' in sys.argv:
        if path.read_text() != expected:
            raise ValueError('Native glow registry drift')
    else:
        path.write_text(expected)
    print('Native glow registry: 20 exact source profiles PASS')
