"""Run the PS2 BSP reader over every course .BSP in the canonical PackFS and check count invariants (read-only)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE))
import ps2_bsp as b  # noqa: E402
import tngtool as t  # noqa: E402


def main(root, output):
    root = Path(root)
    man, _ = t.load_pak(root / 'TNG.PAK')
    rows = []
    for e in man['entries']:
        if e['kind'] != 'file' or not e['path'].upper().endswith('.BSP'):
            continue
        payload, _ = t.read_payload(e, root / 'TNG.000')
        bsp = b.parse(payload)
        s = b.summary(bsp)
        planes = s['nodes_with_plane']
        w0 = [n.payload[0] for n in bsp.nodes if n.payload]
        w1 = [n.payload[1] for n in bsp.nodes if n.payload]
        s.update(course=e['path'].replace(chr(92), '/').split('/')[-1][:-4],
                 invariants={'consumed_eq_size': s['trailing'] == 0,
                             'nodes_eq_2P_plus_1': s['nodes'] == 2 * planes + 1,
                             'planes_eq_w3': planes == bsp.header[3],
                             'payload_nodes_eq_w0': s['nodes_with_payload'] == bsp.header[0],
                             'w3_eq_w4': bsp.header[3] == bsp.header[4]},
                 payload_word0_max_low24=max(w0) & 0xffffff if w0 else None,
                 payload_word0_max_high8=max(w0) >> 24 if w0 else None,
                 payload_word1_range=[min(w1), max(w1)] if w1 else None)
        rows.append(s)
    Path(output).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
    ok = sum(all(r['invariants'].values()) for r in rows)
    print(f'{len(rows)} files, {ok} satisfy every invariant')
    for r in rows:
        print(r['course'], r['nodes'], r['plane_table'], r['payload_word0_max_low24'], r['payload_word0_max_high8'], r['payload_word1_range'])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
