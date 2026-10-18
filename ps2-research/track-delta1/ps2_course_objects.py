"""T4b: convert the Turkey3 MISSING_ON_PC objects (House 1, caravans) into loose PC models, Eggs and collision.

Reuses the T4a pieces (ps2_obj_to_dx.py, tag100_patch.py). Instances of one model (same vertex count and order, rigid fit with residual
< 0.01) share one DX; every instance gets its own Egg (rotation from the rigid fit, translation = centroid) and its own collision brush in the loose turkey3.dx.
Not converted here: CARAVAN_ALPHA (alpha-test material, 16 vertices each), huts, shrubs, boats, fences (PLACEMENT_DIFFERS: the PC course has
these models at other positions, adding the PS2 placements would duplicate them), puddles (own overlay channel).
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ps2_obj_to_dx as o  # noqa: E402
import gcoll_columns as gc  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402
import tag100_patch as tp  # noqa: E402
import tag100_tree as tt  # noqa: E402
import ps2_terrain as terrain  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402
from master_rallye.topology_writer import rebuild_topology  # noqa: E402

BS = chr(92)
# model name (7 chars after the template texture slot rule: texture slot text must keep the template length), GXI base name, mesh paths
MODELS = [
    {'name': 'house1', 'slot': b'brk-tga', 'gxi': 'BRICKHOUSE-TGA.GXI', 'texture': 'brickhouse-tga', 'meshes': ['root.0.65.1']},
    {'name': 'caravan', 'slot': b'cvn-tga', 'gxi': 'CARAVAN-TGA.GXI', 'texture': 'caravan-tga', 'meshes': ['root.0.9.7', 'root.0.56.1']},
    {'name': 'redcaravan', 'slot': b'rcv-tga', 'gxi': 'NEWTEX-TGA.GXI', 'texture': 'newtex-tga',
     'meshes': ['root.0.0.1', 'root.0.8.15', 'root.0.56.2', 'root.0.65.9']},
]
DIR = 'DataGx/Misc/PS2Port/'


def strip_vertices(scene, mesh):
    """Source vertex positions in strip order (used to pair instances)."""
    out = []
    for strip in mesh['strips']:
        out += [scene.position(i) for i in range(strip['start'], strip['start'] + strip['count'])]
    return out


def _jacobi_eigen(m, sweeps=60):
    """Largest eigenvector of a symmetric 4x4 matrix (cyclic Jacobi)."""
    n = 4
    a = [row[:] for row in m]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(sweeps):
        off = sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < 1e-24:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-30:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s_ = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s_ * akq, s_ * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s_ * aqk, s_ * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - s_ * vkq, s_ * vkp + c * vkq
    best = max(range(n), key=lambda i: a[i][i])
    return [v[k][best] for k in range(n)]


def rigid_fit(a, b):
    """Proper rotation R (world = R . local, column convention) mapping centered points a onto b (Horn quaternion method); returns (R, residual)."""
    s = [[sum(p[i] * q[j] for p, q in zip(a, b)) for j in range(3)] for i in range(3)]
    sxx, sxy, sxz = s[0]
    syx, syy, syz = s[1]
    szx, szy, szz = s[2]
    nmat = [[sxx + syy + szz, syz - szy, szx - sxz, sxy - syx],
            [syz - szy, sxx - syy - szz, sxy + syx, szx + sxz],
            [szx - sxz, sxy + syx, -sxx + syy - szz, syz + szy],
            [sxy - syx, szx + sxz, syz + szy, -sxx - syy + szz]]
    w_, x, y, z = _jacobi_eigen(nmat)
    n = math.sqrt(w_ * w_ + x * x + y * y + z * z)
    w_, x, y, z = w_ / n, x / n, y / n, z / n
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w_), 2 * (x * z + y * w_)],
         [2 * (x * y + z * w_), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w_)],
         [2 * (x * z - y * w_), 2 * (y * z + x * w_), 1 - 2 * (x * x + y * y)]]
    res = max(math.dist(tuple(sum(r[i][j] * p[j] for j in range(3)) for i in range(3)), q) for p, q in zip(a, b))
    return r, res


def _apply(r, p):
    return tuple(sum(r[i][j] * p[j] for j in range(3)) for i in range(3))


def fit_unordered(a, b, iterations=30):
    """Rigid fit of point set a onto b when the vertex order of the two instances may differ.

    Start: pair by distance from the centroid (rigid copies share the radii), then iterate nearest-neighbour pairing and Horn fits.
    Returns (R, residual) with residual = largest nearest-neighbour distance in both directions (set equality, not order).
    """
    ra = sorted(range(len(a)), key=lambda i: math.dist(a[i], (0, 0, 0)))
    rb = sorted(range(len(b)), key=lambda i: math.dist(b[i], (0, 0, 0)))
    rot, _ = rigid_fit([a[i] for i in ra], [b[i] for i in rb])
    for _ in range(iterations):
        moved = [_apply(rot, p) for p in a]
        pairs = [min(b, key=lambda q: math.dist(m, q)) for m in moved]
        rot, _ = rigid_fit(a, pairs)
    moved = [_apply(rot, p) for p in a]
    forward = max(min(math.dist(m, q) for q in b) for m in moved)
    backward = max(min(math.dist(m, q) for m in moved) for q in b)
    return rot, max(forward, backward)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--no-flip-v', action='store_true', help='keep the PS2 V as is (default flips V: the GXI rows are top-down, the PC texture V runs bottom-up; confirmed by the user on Turkey3)')
    ap.add_argument('--terrain', action='store_true', help='also carry the PS2 ground that differs from the PC ground (ps2_terrain.py)')
    ap.add_argument('--snap-threshold', type=float, default=1e9, help='shift an instance vertically when its lowest vertices are this far above or below the PC ground (the PS2 ground differs there)')
    a = ap.parse_args()
    manifest, _ = o.t.load_pak(a.ps2_root / 'TNG.PAK')
    scene = o.w.decode_scene(o.extract(manifest, a.ps2_root, o.PSM_PATH))
    by_path = {m['path']: m for m in scene.meshes}
    template = (a.pc_root / 'DataGx/Misc/Haybale/haybaletest.dx').read_bytes()
    hay = parse_dxt_bytes((a.pc_root / 'DataGx/Misc/Haybale/hay-tga.dxt').read_bytes())
    pc_xml = (a.pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    course = (a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx').read_bytes()
    slice_ = extract_tag100_from_dx_bytes(course, 'turkey3.dx')
    tree = tt.Tree(slice_.raw)
    terrain_report, terrain_eggs = None, []
    if a.terrain:
        _, pc_model, ps2_non, pc_non, pc_all = terrain.load_delta(a.ps2_root, a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
        pc_neutral, pc_kept = terrain.with_replacement(pc_non, ps2_non)
        course = terrain.neutralise(course, pc_model, pc_neutral)
        pcn0 = gc.pc_nodes(a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
        import ground_delta_probe as gdp
        gscene = scene
        ps2_grid = gdp.build_index(gdp.ground_triangles(gscene))
        coll = terrain.collision(tree, ps2_non, pc_all, pcn0, ps2_top=lambda x, z: gdp.height_at(ps2_grid, x, z))
        tfiles, terrain_eggs, vis = terrain.visual_models(a.ps2_root, manifest, ps2_non, template, hay)
        files_terrain = tfiles
        terrain_report = {'ps2_non_exact_ground': len(ps2_non), 'pc_non_exact_ground_neutralised': len(pc_neutral), 'pc_non_exact_ground_kept_no_replacement': len(pc_kept), 'collision': coll, 'visual': vis}
    else:
        files_terrain = {}
    pcn = gc.pc_nodes(a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    files, eggs, report = dict(files_terrain), b'', {'models': []}
    for ename, mname, ec in terrain_eggs:
        eggs += o.egg_xml(ename, mname, ec)
    for model in MODELS:
        first = by_path[model['meshes'][0]]
        tex_name = first['textures'][0]['name']
        if o.t.logical_path(tex_name) != o.t.logical_path(BS.join(['Course', 'turkey3', model['texture']])):
            raise SystemExit('texture mismatch for ' + model['name'] + ': ' + tex_name)
        tris0 = o.source_triangles(scene, first)
        verts0 = strip_vertices(scene, first)
        c0 = tuple(sum(v[i] for v in verts0) / len(verts0) for i in range(3))
        geometry = o.build_geometry(tris0, c0, (not a.no_flip_v))
        rebuilt = rebuild_topology(template, {0: geometry}, bounds_mode='recompute')
        dx = bytearray(rebuilt.data)
        slot = next(s for s in rebuilt.output_model.physical_draws[0].texture_slots if s.slot == 0)
        dx[slot.data_offset:slot.data_offset + len(model['slot'])] = model['slot']
        parse_dx_bytes(bytes(dx))
        gxi = o.extract(manifest, a.ps2_root, BS + 'TNG' + BS + 'DATAPSM' + BS + 'COURSE' + BS + 'TURKEY3' + BS + model['gxi'])
        tex = o.p.parse_gxi(gxi)
        w_, h_ = tex['width'], tex['height']
        rgba = gxi[8:8 + w_ * h_ * 4]
        bgra = bytearray(len(rgba))
        for i in range(0, len(rgba), 4):
            bgra[i], bgra[i + 1], bgra[i + 2], bgra[i + 3] = rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]
        dxt = hay.header[:12] + struct.pack('<2I', w_, h_) + bytes(bgra)
        parse_dxt_bytes(dxt)
        mdir = DIR + model['name'] + '/'
        files[mdir + model['name'] + '.dx'] = bytes(dx)
        files[mdir + model['slot'].decode() + '.dxt'] = dxt
        entry = {'name': model['name'], 'texture': [w_, h_], 'dx_triangles': len(geometry.triangles), 'instances': []}
        for k, path in enumerate(model['meshes']):
            mesh = by_path[path]
            verts = strip_vertices(scene, mesh)
            if len(verts) != len(verts0):
                raise SystemExit('instance vertex count differs: ' + path)
            c = tuple(sum(v[i] for v in verts) / len(verts) for i in range(3))
            low = sorted(verts, key=lambda p: p[1])[:20]
            offsets = [p[1] - g for p in low for g in [gw.ground_at(pcn, p[0], p[2])] if g is not None]
            lift = (sum(offsets[:8]) / len(offsets[:8])) if offsets else 0.0
            dy = -lift if abs(lift) > a.snap_threshold else 0.0
            rot, residual = fit_unordered([tuple(p[i] - c0[i] for i in range(3)) for p in verts0], [tuple(p[i] - c[i] for i in range(3)) for p in verts])
            if residual > 0.01:
                raise SystemExit(f'{path}: instance is not a rigid copy of the first one (residual {residual:.4f})')
            # row-vector convention of the Egg matrix: world = local . M with M = R^T, so Row i is column i of R
            rows = tuple(tuple(rot[j][i] for j in range(3)) for i in range(3))
            name = f'ps2_{model["name"]}{k + 1}'
            c_world = (c[0], c[1] + dy, c[2])
            eggs += o.egg_xml(name, 'misc' + BS + 'ps2port' + BS + model['name'] + BS + model['name'], c_world, rows)
            allpos = [(pt[0], pt[1] + dy, pt[2]) for pos, _, _ in o.source_triangles(scene, mesh) for pt in pos]
            code = tree.reference_code((c_world[0], min(p[1] for p in allpos) - 0.5, c_world[2]))
            if code is None:
                raise SystemExit(path + ': no ground code below the object')
            hull_verts = sorted(set(allpos))
            hull = tp.hull_planes(hull_verts)
            leaves = tree.apply_prepared(hull_verts, [((q[0], q[1], q[2]), q[3]) for q in hull], code, 'fill')
            rep = {'planes': len(hull), 'leaves_replaced': leaves}
            entry['instances'].append({'egg': name, 'mesh': path, 'translation': [round(x, 2) for x in c_world], 'ground_offset_before': round(lift, 2), 'applied_dy': round(dy, 2), 'rotation_rows': [[round(x, 6) for x in r] for r in rows],
                                       'fit_residual': round(residual, 5), 'plane_code': code, 'brush_planes': rep['planes'],
                                       'leaves_replaced': rep['leaves_replaced']})
        report['models'].append(entry)
    start = pc_xml.index(b'    <List Name="IContManager">\r\n')
    end = pc_xml.index(b'    </List>\r\n', start)
    files['DataScene/RaceTest/Turkey3.xml'] = pc_xml[:end] + eggs + pc_xml[end:]
    tree_bytes = tree.serialize()
    files['DataGx/Course/Turkey3/turkey3.dx'] = course[:slice_.tag_offset] + tree_bytes
    nodes, parsed = tp.to_nodes(tree_bytes)
    report['tag100'] = {'header': list(parsed.header_words), 'invariants_ok': all(parsed.count_invariants().values()), 'bytes': len(tree_bytes)}
    report['terrain'] = terrain_report
    for rel, data in files.items():
        path = a.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    report['files'] = {rel: {'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()} for rel, d in files.items()}
    (a.out / 'report.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
