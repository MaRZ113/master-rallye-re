"""T4a: convert one PS2 course mesh into a loose PC model (DX rev135 + DXT) and a RaceTest Egg.

Slice for the Turkey3 'House 1' mesh (texture brickhouse-tga). The PC engine already draws a plain Egg with a DX model and no AI
(HAY-PROBE bisect B), so the object is delivered as data:
  DataGx/Misc/PS2Port/house1/house1.dx      template haybaletest.dx with its single render draw replaced (topology_writer)
  DataGx/Misc/PS2Port/house1/brk-tga.dxt    GXI pixels, RGBA -> BGRA (64x64, same header words as hay-tga.dxt)
  DataScene/RaceTest/Turkey3.xml            retail PC XML plus one Egg in the IContManager list
Vertices are stored relative to the mesh centroid, the Egg translation is the centroid (identity rotation).
Winding of the PS2 strips is unresolved, so every triangle is written twice (both windings, flat normals); this is an explicit
placeholder policy, not a PS2 claim. Vertex colour is the PS2 baked tint copied as is (same value as the PC course DX for shared vertices). No collision is generated.
"""
import argparse
import hashlib
import json
import math
import re
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT.parent / 'src'))
import psbtool as p  # noqa: E402
import tngtool as t  # noqa: E402
import water_runtime as w  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402
import tag100_patch as tp  # noqa: E402
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology  # noqa: E402

PSM_PATH = r'\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM'
GXI_PATH = r'\TNG\DATAPSM\COURSE\TURKEY3\BRICKHOUSE-TGA.GXI'
MESH_PATH = 'root.0.65.1'
MODEL_DIR = 'DataGx/Misc/PS2Port/house1'
MODEL_NAME = r'misc\ps2port\house1\house1'
EGG_NAME = 'ps2_house1'
TEXTURE_FROM, TEXTURE_TO = b'hay-tga', b'brk-tga'


def extract(manifest, root, path):
    entries = [e for e in manifest['entries'] if e['kind'] == 'file' and t.logical_path(e['path']) == t.logical_path(path)]
    if len(entries) != 1:
        raise SystemExit('missing or ambiguous resource ' + path)
    return t.read_payload(entries[0], root / 'TNG.000')[0]


def source_triangles_ext(scene, mesh):
    """Same strip/ADC rule as prepare_course_objects.collect_preview_vertices; returns (positions, uv) triples."""
    out = []
    for strip in mesh['strips']:
        for newest in range(strip['start'] + 2, strip['start'] + strip['count']):
            if scene.control(newest) & 1:
                continue
            idx = (newest - 2, newest - 1, newest)
            pos = tuple(scene.position(i) for i in idx)
            if w.area_normal(pos)[0] <= 1e-7:
                continue
            uv = tuple(struct.unpack_from('<2f', scene.payload, 32 + i * 52 + 20) for i in idx)
            # PS2 vertex word at +16 holds bytes (A, c1, c2, c3); the PC course DX colour is (c1, c2, c3, 255) for the same vertex
            # (48,406 exact-position pairs in Turkey3: same value within 1, no x2 scaling), so the tint is copied as is.
            col = tuple(bytes(scene.payload[32 + i * 52 + 17:32 + i * 52 + 20]) + bytes([255]) for i in idx)
            aux = tuple(struct.unpack_from('<2f', scene.payload, 32 + i * 52 + 28) for i in idx)  # unexplained pair at +28/+32 (HYPOTHESIS: PS2 noise UV)
            out.append((pos, uv, col, aux))
    return out


def source_triangles(scene, mesh):
    """(positions, uv, colours) per triangle; see source_triangles_ext for the extra +28/+32 pair."""
    return [(p, u, c) for p, u, c, _ in source_triangles_ext(scene, mesh)]


def normal_of(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    length = math.sqrt(sum(x * x for x in n)) or 1.0
    return tuple(x / length for x in n)


def build_geometry(triangles, centroid, flip_v):
    vertices, faces = [], []
    for pos, uv, col in triangles:
        local = [(x - centroid[0], y - centroid[1], z - centroid[2]) for x, y, z in pos]
        n = normal_of(*local)
        for winding, normal in ((0, n), (1, tuple(-x for x in n))):
            order = (0, 1, 2) if winding == 0 else (0, 2, 1)
            base = len(vertices)
            for i in order:
                u, v = uv[i]
                vertices.append(CompiledVertex(tuple(local[i]), normal, col[i], ((u, 1.0 - v if flip_v else v),)))
            faces.append((base, base + 1, base + 2))
    return DrawGeometry(tuple(vertices), tuple(faces))


def egg_xml(name, model, row3, rows=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))):
    lines = f'''      <Egg Name="{name}">
        <Value Name="Use en2d" Type="Bool" Value="False"/>
        <Value Name="Freezable" Type="Bool" Value="True"/>
        <Value Name="Hitable" Type="Bool" Value="True"/>
        <Value Name="Draw Priority" Type="Int" Value="3"/>
        <Value Name="Tick Priority" Type="Int" Value="3"/>
        <Value Name="Egg Group" Type="Int" Value="0"/>
        <Value Name="en3d Model Name" Type="String" Value="{model}"/>
        <Value Name="en3d Matrix" Type="Matrix" Row0="{rows[0][0]:.6f} {rows[0][1]:.6f} {rows[0][2]:.6f} 0.00" Row1="{rows[1][0]:.6f} {rows[1][1]:.6f} {rows[1][2]:.6f} 0.00" Row2="{rows[2][0]:.6f} {rows[2][1]:.6f} {rows[2][2]:.6f} 0.00" Row3="{row3[0]:.2f} {row3[1]:.2f} {row3[2]:.2f} 1.00"/>
        <Value Name="en3d Draw 2D" Type="Bool" Value="False"/>
        <Value Name="en3d Interpolated" Type="Bool" Value="True"/>
        <Value Name="en3d Visible" Type="Bool" Value="True"/>
        <Value Name="en3d ZBuffered" Type="Bool" Value="True"/>
        <Value Name="en2d Model Name" Type="String" Value="Null"/>
        <Value Name="en2d Matrix" Type="Matrix" Row0="1.00 0.00 0.00 0.00" Row1="0.00 1.00 0.00 0.00" Row2="0.00 0.00 1.00 0.00" Row3="0.00 0.00 0.00 1.00"/>
        <Value Name="en2d FileType" Type="Int" Value="0"/>
        <Value Name="en2d Image Bank Index" Type="Int" Value="0"/>
        <Value Name="en2d Draw 2D" Type="Bool" Value="False"/>
        <Value Name="en2d Interpolated" Type="Bool" Value="True"/>
        <Value Name="en2d Visible" Type="Bool" Value="True"/>
        <Value Name="en2d ZBuffered" Type="Bool" Value="True"/>
        <Value Name="en2d 2dGlobal" Type="Bool" Value="False"/>
        <AI_List>
          <AI No="0">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
          <AI No="1">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
          <AI No="2">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
          <AI No="3">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
        </AI_List>
      </Egg>
'''
    return lines.replace('\n', '\r\n').encode('latin1')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--collision', action='store_true', help='also write a loose turkey3.dx whose tag100 has the convex hull of the mesh as a solid brush')
    ap.add_argument('--flip-v', action='store_true', help='mirror V (PS2 and PC row order are not proven equal)')
    a = ap.parse_args()
    manifest, _ = t.load_pak(a.ps2_root / 'TNG.PAK')
    scene = w.decode_scene(extract(manifest, a.ps2_root, PSM_PATH))
    mesh = next(m for m in scene.meshes if m['path'] == MESH_PATH)
    if t.logical_path(mesh['textures'][0]['name']) != t.logical_path(r'Course\turkey3\brickhouse-tga'):
        raise SystemExit('mesh texture changed: ' + str(mesh['textures']))
    triangles = source_triangles(scene, mesh)
    allpos = [pt for pos, _, _ in triangles for pt in pos]
    centroid = tuple(sum(c[i] for c in allpos) / len(allpos) for i in range(3))
    geometry = build_geometry(triangles, centroid, a.flip_v)
    template = (a.pc_root / 'DataGx/Misc/Haybale/haybaletest.dx').read_bytes()
    rebuilt = rebuild_topology(template, {0: geometry}, bounds_mode='recompute')
    dx = bytearray(rebuilt.data)
    slot = next(s for s in rebuilt.output_model.physical_draws[0].texture_slots if s.slot == 0)
    if bytes(dx[slot.data_offset:slot.data_offset + len(TEXTURE_FROM)]) != TEXTURE_FROM:
        raise SystemExit('template texture slot not found')
    dx[slot.data_offset:slot.data_offset + len(TEXTURE_TO)] = TEXTURE_TO
    parse_dx_bytes(bytes(dx))  # must still parse
    gxi = extract(manifest, a.ps2_root, GXI_PATH)
    tex = p.parse_gxi(gxi)
    if (tex['width'], tex['height']) != (64, 64):
        raise SystemExit('unexpected GXI size')
    hay = parse_dxt_bytes((a.pc_root / 'DataGx/Misc/Haybale/hay-tga.dxt').read_bytes())
    rgba = gxi[8:]
    bgra = bytearray(len(rgba))
    for i in range(0, len(rgba), 4):
        bgra[i], bgra[i + 1], bgra[i + 2], bgra[i + 3] = rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]
    dxt = hay.header[:8] + struct.pack('<3I', zlib.crc32(bytes(bgra)) & 0xFFFFFFFF, 64, 64) + bytes(bgra)  # word_0x08 = CRC32 of the pixel payload
    parse_dxt_bytes(dxt)
    pc_xml = (a.pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    start = pc_xml.index(b'    <List Name="IContManager">\r\n')
    end = pc_xml.index(b'    </List>\r\n', start)
    new_xml = pc_xml[:end] + egg_xml(EGG_NAME, MODEL_NAME, centroid) + pc_xml[end:]
    collision = {}
    if a.collision:
        course = (a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx').read_bytes()
        sl = extract_tag100_from_dx_bytes(course, 'turkey3.dx')
        verts = sorted(set(allpos))
        nodes_old, _ = tp.to_nodes(sl.raw)
        # the plane code must be a valid non-negative surface code (0xFFFFFFFF planes never generate contacts, see tag100_patch.reference_code)
        below = (centroid[0], min(v[1] for v in verts) - 0.5, centroid[2])
        code = tp.reference_code(nodes_old, below)
        if code is None:
            raise SystemExit('no ground plane code found below the object')
        patched, rep = tp.insert_brush(sl.raw, verts, code=code)
        nodes_new, _ = tp.to_nodes(patched)
        import random
        rnd = random.Random(7)
        lo = [min(v[i] for v in verts) for i in range(3)]
        hi = [max(v[i] for v in verts) for i in range(3)]
        planes = tp.hull_planes(verts)

        def inside(pt):
            return all(n[0] * pt[0] + n[1] * pt[1] + n[2] * pt[2] + n[3] < -1e-3 for n in planes)

        checks = {'inside_solid': 0, 'inside_total': 0, 'outside_changed': 0, 'outside_total': 0}
        for _ in range(30000):
            pt = tuple(rnd.uniform(lo[i] - 25, hi[i] + 25) for i in range(3))
            old, new = tp.classify(nodes_old, pt).field_0, tp.classify(nodes_new, pt).field_0
            if inside(pt):
                checks['inside_total'] += 1
                checks['inside_solid'] += new == tp.SOLID
            else:
                checks['outside_total'] += 1
                checks['outside_changed'] += old != new and not any(
                    n[0] * pt[0] + n[1] * pt[1] + n[2] * pt[2] + n[3] > -1e-3 and n[0] * pt[0] + n[1] * pt[1] + n[2] * pt[2] + n[3] < 1e-3 for n in planes)
        collision = {'DataGx/Course/Turkey3/turkey3.dx': course[:sl.tag_offset] + patched}
        coll_report = {'plane_code_used': code, 'brush_planes': rep, 'sampled_checks': checks}
    files = {MODEL_DIR + '/house1.dx': bytes(dx), MODEL_DIR + '/brk-tga.dxt': dxt, 'DataScene/RaceTest/Turkey3.xml': new_xml, **collision}
    for rel, data in files.items():
        path = a.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    report = {'mesh': MESH_PATH, 'source_triangles': len(triangles), 'dx_triangles': len(geometry.triangles), 'centroid': centroid,
              'flip_v': a.flip_v, 'collision': coll_report if a.collision else None, 'files': {rel: {'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()} for rel, d in files.items()}}
    (a.out / 'report.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
