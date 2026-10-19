"""TRACK-GROUND1 texture parity audit for a course.

For every texture used by the PS2 PSM meshes of the course:
  * GXI size / alpha, PC DXT of the same name (size, CRC32 header check),
  * difference to the same-name PC texture in the expected orientation and in the three alternative orientations (the expected one must be the best),
  * the best other PC texture of the course (a same-name match must be clearly better than any other texture),
  * decision at the converter tolerance: use the PC file, keep the PS2 file, or no PC file.
Writes JSON; prints a table. Read-only.
"""
import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TD1 = HERE.parent / 'track-delta1'
sys.path.insert(0, str(TD1))
sys.path.insert(0, str(TD1.parent / 'tools'))
sys.path.insert(0, str(TD1.parent.parent / 'src'))
import ps2_obj_to_dx as o  # noqa: E402
import ps2_terrain as terrain  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402

BS = chr(92)


def ps2_textures(scene):
    names = {}
    for mesh in scene.meshes:
        for slot in mesh['textures']:
            if slot['name'] and slot['name'].lower() != 'null':
                names.setdefault(slot['name'].split(BS)[-1], set()).add(mesh['material'].split('$')[0].strip() or '(ground family)')
    return names


def load_gxi(manifest, ps2_root, course, base):
    path = BS + 'TNG' + BS + 'DATAPSM' + BS + 'COURSE' + BS + course + BS + base.upper() + '.GXI'
    gxi = o.extract(manifest, ps2_root, path)
    tex = o.p.parse_gxi(gxi)
    w_, h_ = tex['width'], tex['height']
    return gxi[8:8 + w_ * h_ * 4], w_, h_


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-dir', type=Path, required=True, help='retail DataGx/Course/<Course>')
    ap.add_argument('--course', default='TURKEY3')
    ap.add_argument('--tolerance', type=float, default=8.0)
    ap.add_argument('--rename-tolerance', type=float, default=2.0)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    manifest, _ = o.t.load_pak(a.ps2_root / 'TNG.PAK')
    psm = BS + 'TNG' + BS + 'DATAPSM' + BS + 'COURSE' + BS + a.course + BS + a.course + '.PSM'
    scene = o.w.decode_scene(o.extract(manifest, a.ps2_root, psm))
    pc_files = {f.stem: f for f in a.pc_dir.glob('*.dxt')}
    pc_cache = {}

    def pc_tex(name):
        if name not in pc_cache:
            pc_cache[name] = parse_dxt_bytes(pc_files[name].read_bytes())
        return pc_cache[name]
    rows = []
    for base, materials in sorted(ps2_textures(scene).items()):
        row = {'texture': base, 'materials': sorted(materials)}
        try:
            rgba, w_, h_ = load_gxi(manifest, a.ps2_root, a.course, base)
        except Exception as e:  # noqa: BLE001
            row.update(ps2='unreadable', error=str(e)[:80], decision='no PS2 file')
            rows.append(row)
            continue
        row['ps2'] = [w_, h_]
        row['ps2_alpha_min_max'] = [min(rgba[3::4]), max(rgba[3::4])]
        if base not in pc_files:
            row.update(pc=None, decision='ps2_only')
            rows.append(row)
            continue
        pc = pc_tex(base)
        crc = zlib.crc32(pc.bgra) & 0xFFFFFFFF
        row['pc'] = [pc.width, pc.height]
        row['pc_header_crc_ok'] = struct.unpack_from('<I', pc_files[base].read_bytes(), 8)[0] == crc
        scores = {}
        for label, kw in (('expected_rows_flipped', dict(flip_rows=True)), ('rows_not_flipped', dict(flip_rows=False)),
                          ('cols_flipped', dict(flip_rows=True, flip_cols=True)), ('both_flipped', dict(flip_rows=False, flip_cols=True))):
            d = terrain.texture_difference(pc, rgba, w_, h_, **kw)
            scores[label] = None if d is None else round(d, 2)
        row['difference_by_orientation'] = scores
        row['expected_is_best'] = scores['expected_rows_flipped'] is not None and all(
            v is None or scores['expected_rows_flipped'] <= v for v in scores.values())
        # best other PC texture of the same size class (a same-name match must stand out)
        best = None
        for other in pc_files:
            if other == base:
                continue
            ot = pc_tex(other)
            d = terrain.texture_difference(ot, rgba, w_, h_)
            if d is not None and (best is None or d < best[1]):
                best = (other, d)
        row['best_other_pc_texture'] = None if best is None else [best[0], round(best[1], 2)]
        d = scores['expected_rows_flipped']
        if d is not None and d <= a.tolerance:
            row['decision'] = 'pc'
        elif best is not None and best[1] <= a.rename_tolerance:
            row['decision'] = 'pc_renamed:' + best[0]
        else:
            row['decision'] = 'ps2_kept_different_artwork' if d is not None else 'ps2_kept_size_ratio'
        rows.append(row)
    print(f"{'texture':34} {'ps2':>9} {'pc':>9} {'diff':>6} {'best other':>26} decision")
    for r in rows:
        print(f"{r['texture'][:34]:34} {str(r.get('ps2')):>9} {str(r.get('pc')):>9} {str((r.get('difference_by_orientation') or {}).get('expected_rows_flipped')):>6} "
              f"{str(r.get('best_other_pc_texture')):>26} {r['decision']}")
    summary = {'textures': len(rows), 'decisions': {}}
    for r in rows:
        summary['decisions'][r['decision']] = summary['decisions'].get(r['decision'], 0) + 1
    summary['expected_orientation_best'] = sum(1 for r in rows if r.get('expected_is_best'))
    summary['pc_headers_crc_ok'] = sum(1 for r in rows if r.get('pc_header_crc_ok'))
    summary['decisions'] = {('pc_renamed' if k.startswith('pc_renamed') else k): sum(1 for r in rows if (('pc_renamed' if r['decision'].startswith('pc_renamed') else r['decision']) == ('pc_renamed' if k.startswith('pc_renamed') else k))) for k in summary['decisions']}
    print(summary)
    if a.out:
        a.out.write_text(json.dumps({'summary': summary, 'tolerance': a.tolerance, 'rename_tolerance': a.rename_tolerance, 'textures': rows}, indent=1))


if __name__ == '__main__':
    main()
