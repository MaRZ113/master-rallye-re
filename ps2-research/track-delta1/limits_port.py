"""Turkey3 probe: replace the PC Left/RightOuterLimit marker lists by the PS2 Left/RightOuterLimit2 positions.

Byte-preserving edit of the PC RaceTest XML: only the two <List> bodies change (marker count and positions). Marker Type and Marker Dir keep the
PC values, so no PS2-only marker model is referenced. `--check` prints ordering diagnostics (progress of each list along the RaceLine).
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import course_delta as cd  # noqa: E402
import gcoll_map as gm  # noqa: E402

PAIRS = {'LeftOuterLimit': 'LeftOuterLimit2', 'RightOuterLimit': 'RightOuterLimit2'}


def list_span(data, name):
    m = re.search(rb'    <List Name="' + name.encode() + rb'">\r\n', data)
    if not m:
        raise SystemExit(f'list {name} not found')
    end = data.index(b'    </List>\r\n', m.end()) + len(b'    </List>\r\n')
    return m.end(), end - len(b'    </List>\r\n')


def marker_block(no, x, y, z):
    # Y is forced to 0.00 like every PC Turkey3 limit marker: the PS2 lists carry -4.5 to 5.0 and the game's nearest-marker search is 3D.
    y = 0.0
    return (f'      <Marker No="{no}">\r\n'
            '        <Value Name="Marker Type" Type="String" Value="markers\\purple_marker"/>\r\n'
            f'        <Value Name="Marker Pos" Type="Vector3" Value="{x:.2f} {y:.2f} {z:.2f}"/>\r\n'
            f'        <Value Name="Marker Dir" Type="Vector3" Value="1.00 0.00 0.00"/>\r\n'
            f'      </Marker>\r\n').encode()


def progress(route, pts):
    return [min(range(len(route)), key=lambda j: math.dist(route[j], p)) for p in pts]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pc-scene', type=Path, required=True)
    ap.add_argument('--ps2-scene', type=Path, required=True)
    ap.add_argument('--sdk', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    sdk, _ = cd.sdk_modules(a.sdk)
    pc = a.pc_scene.read_bytes()
    ps2 = a.ps2_scene.read_bytes()
    route = gm.markers(sdk, pc, 'RaceLine')
    # XYZ with Y as stored (markers() returns x,z; read full positions from the XML text)
    def full(data, name):
        s, e = list_span(data, name)
        return [tuple(float(v) for v in m.split()) for m in re.findall(rb'Marker Pos" Type="Vector3" Value="([^"]+)"', data[s:e])]
    report = {}
    new = pc
    for pc_name, ps2_name in PAIRS.items():
        pts = full(ps2, ps2_name)
        old = full(pc, pc_name)
        pr_new, pr_old = progress(route, [(p[0], p[2]) for p in pts]), progress(route, [(p[0], p[2]) for p in old])
        back = lambda seq: sum(1 for i in range(1, len(seq)) if seq[i] < seq[i - 1] - 5)
        report[pc_name] = {'pc_count': len(old), 'ps2_count': len(pts), 'pc_progress_first_last': [pr_old[0], pr_old[-1]], 'ps2_progress_first_last': [pr_new[0], pr_new[-1]],
                           'pc_backward_jumps': back(pr_old), 'ps2_backward_jumps': back(pr_new), 'ps2_y_values': sorted({p[1] for p in pts})}
        s, e = list_span(new, pc_name)
        body = b''.join(marker_block(i, *p) for i, p in enumerate(pts))
        new = new[:s] + body + new[e:]
    report['source_sha256'] = hashlib.sha256(pc).hexdigest()
    report['candidate_sha256'] = hashlib.sha256(new).hexdigest()
    print(json.dumps(report, indent=1))
    if a.output and not a.check:
        a.output.write_bytes(new)
        print('wrote', a.output)


if __name__ == '__main__':
    main()
