"""Rally Championship Xtreme (PC) car archive -> Universal Vehicle Scene.

Source frame (MSH/QTO, metres): +X vehicle left ("headlamp l" at +X), +Y down (wheels touch
Y = 0, roof at Y < 0), -Z front (headlamps at -Z). Normalized frame: +X right, +Y up, -Z front,
so source_to_normalized = diag(-1, -1, 1) (det +1, no mirroring).

Selection (full archive, not the *_arcade one):
* body node = exterior panels, lamps, glass, wipers and the cabin (interior, dashboard, steering
  wheel), each QTO baked with its MSH matrix; the skinned crew figures are left out;
* hidden: damage pivots (*_pivot), light halos (MR draws its own glow), exhaust flash, shadow /
  collision / damage meshes, the cockpit-view copies (int *, body_hr), engine bay, spare wheel,
  motion-blur wheels (*a) and the placeholder "fudge" triangle;
* wheels = the detailed front wheel ("wheelfront l_hr" / "r_hr", rim, disc, wall, tread) on all
  four hubs (the archive has no detailed rear wheel; rear hubs and radius come from the
  "wheelback l/r" MSH records). Falls back to the plain wheels if no _hr mesh exists.
"""
from __future__ import annotations
from pathlib import Path
from .. import universal_vehicle_scene as uvs
from .rcx_formats import read_rcx, parse_qto, parse_msh, decode_tex, apply, rotate

NORMALIZATION = [-1., 0., 0., 0., 0., -1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
BODY_PARTS = ('body', 'bonnet', 'bumper front', 'bumper back', 'wing', 'mirror l', 'mirror r', 'headlamp l', 'headlamp r',
              'brakelight l', 'brakelight r', 'windows', 'wiper l', 'wiper r', 'interior', 'dashboard', 'steering wheel')
# The driver / co-driver figures are skinned (bind pose: arms through the roof without the .anm
# skeleton), so they are left out; the MR crew is added separately.
SLOTS = {'FL_WHEEL': 'wheelfront l', 'FR_WHEEL': 'wheelfront r', 'BL_WHEEL': 'wheelback l', 'BR_WHEEL': 'wheelback r'}
GLASS_ALPHA = 140


def _hub(msh, qto_bytes, name):
    """Centre of the plain wheel after its MSH matrix (source frame) and its radius."""
    rec = msh[name]; d = parse_qto(qto_bytes)
    pts = [apply(rec['matrix'], v[0]) for v in d['vertices']]
    lo = [min(p[k] for p in pts) for k in range(3)]; hi = [max(p[k] for p in pts) for k in range(3)]
    return [(lo[k] + hi[k]) / 2 for k in range(3)], (hi[1] - lo[1]) / 2


def create_scene(rcx_path, output, *, protected=()):
    rcx_path = Path(rcx_path); data = rcx_path.read_bytes(); files = read_rcx(data)
    msh_name = next(k for k in files if k.endswith('.msh')); msh = parse_msh(files[msh_name])
    meshes, materials, textures, nodes, assets = [], [], [], [], {}
    tex_ids = {}

    def texture(name, glass=False):
        key = (name, glass)
        if key in tex_ids: return tex_ids[key]
        dec = decode_tex(files[name]); rgba = bytearray(dec['rgba'])
        tid = 'tex-%03d%s' % (len({k for k in tex_ids if not k[1]}), '-glass' if glass else '')
        if glass:
            # MR authoring: the glass shares the exterior atlas; the window copy gets a uniform glass alpha
            rgba[3::4] = bytes(min(a, GLASS_ALPHA) for a in rgba[3::4])
        path = 'textures/%s.rgba' % tid; assets[path] = bytes(rgba)
        textures.append({'id': tid, 'width': dec['width'], 'height': dec['height'], 'rgba_path': path, 'rgba_sha256': uvs.sha(bytes(rgba)),
                         'source_channels': {'format': dec['format'], 'member': name, 'member_sha256': uvs.sha(files[name]),
                                             'glass_alpha_policy': 'min(source alpha, %d)' % GLASS_ALPHA if glass else None}})
        tex_ids[key] = tid
        return tid

    def add_part(part, matrix, prefix, offset=(0., 0., 0.)):
        d = parse_qto(files[part + '.qto']); ids = []
        for gi, g in enumerate(d['groups']):
            if g['texture_index'] is None or g['triangles'] == 0: continue
            tname = d['textures'][g['texture_index']]
            mid = 'mat-%s-%s-%02d' % (prefix, part.replace(' ', '_'), gi)
            tid = texture(tname, glass=(part == 'windows'))
            tri = [list(d['indices'][k:k + 3]) for k in range(g['start'], g['end'], 3)]
            used = sorted({k for t in tri for k in t}); remap = {k: j for j, k in enumerate(used)}
            pos = [list(apply(matrix, d['vertices'][k][0])) for k in used]
            pos = [[p[0] - offset[0], p[1] - offset[1], p[2] - offset[2]] for p in pos]
            materials.append({'id': mid, 'diffuse_texture_id': tid, 'object': part, 'texture': tname,
                              'flags_raw': g['flags'], 'raw_fields': [{'qto_group_hex': g['raw_hex']}],
                              'unsupported': ['RCX lighting, environment and blend states'],
                              'preview': {'opacity': 1., 'policy': 'source texture'}})
            meshes.append({'id': mid, 'name': part, 'material_id': mid, 'positions': pos,
                           'normals': [list(rotate(matrix, d['vertices'][k][1])) for k in used],
                           'uvs': [list(d['vertices'][k][2]) for k in used],
                           'triangles': [[remap[k] for k in t] for t in tri],
                           'source': {'member': part + '.qto', 'member_sha256': uvs.sha(files[part + '.qto']), 'group': gi}})
            ids.append(mid)
        return ids

    body_ids = []; present = []
    for part in BODY_PARTS:
        if part + '.qto' in files and part in msh:
            body_ids += add_part(part, msh[part]['matrix'], 'body'); present.append(part)
    nodes.append({'id': 'body', 'name': 'BODY', 'parent_id': None, 'mesh_ids': body_ids, 'visible': True, 'source_visible': True,
                  'role': 'body', 'local_transform': uvs.IDENTITY[:], 'source_local_transform': None,
                  'transform_evidence': 'QTO parts baked with their MSH matrices into the car frame'})
    hubs = {}; radius = {}
    for slot, plain in SLOTS.items():
        hubs[slot], radius[slot] = _hub(msh, files[plain + '.qto'], plain)
    detailed = {}
    for side in ('l', 'r'):
        name = 'wheelfront %s_hr' % side
        detailed[side] = name if name + '.qto' in files and name in msh else None
    wheel_report = {}
    for slot, plain in SLOTS.items():
        side = plain[-1]; src = detailed[side] or plain
        fslot = 'FL_WHEEL' if side == 'l' else 'FR_WHEEL'
        # detailed wheel: bake its own matrix, centre on its own (front) hub, place at this slot's hub
        centre = hubs[fslot] if detailed[side] else hubs[slot]
        if detailed[side] and abs(radius[slot] - radius[fslot]) > .02:
            src, centre = plain, hubs[slot]      # rear wheel of another size: keep the plain mesh
        ids = add_part(src, msh[src]['matrix'], slot.lower(), offset=centre)
        m = uvs.IDENTITY[:]; m[3], m[7], m[11] = hubs[slot]
        nodes.append({'id': slot.lower(), 'name': slot, 'parent_id': None, 'mesh_ids': ids, 'visible': True, 'source_visible': True,
                      'role': 'wheel', 'local_transform': m, 'source_local_transform': None,
                      'transform_evidence': {'kind': 'msh_bbox_centre', 'hub_record': plain, 'mesh': src}})
        wheel_report[slot] = {'mesh': src, 'hub': [round(c, 4) for c in hubs[slot]], 'radius': round(radius[slot], 4)}
    fl, fr, bl, br = (hubs[s] for s in ('FL_WHEEL', 'FR_WHEEL', 'BL_WHEEL', 'BR_WHEEL'))
    scene = {'schema': uvs.SCHEMA,
             'metadata': {'adapter': 'rcx-pc/1', 'display_name': rcx_path.stem,
                          'implementation_sha256': {p.name: uvs.sha(p.read_bytes()) for p in (Path(__file__), Path(__file__).with_name('rcx_formats.py'))}},
             'source': {'game': 'Rally Championship Xtreme (PC, Rally.exe efc94948)', 'root': str(rcx_path.parent),
                        'archive': {'path': rcx_path.name, 'bytes': len(data), 'sha256': uvs.sha(data)},
                        'protected_roots': [str(p) for p in protected], 'msh': msh_name},
             'coordinate_system': {'source': {'right_axis': [-1, 0, 0], 'up_axis': [0, -1, 0], 'forward_axis': [0, 0, -1], 'units': 'm'},
                                   'normalized': {'right_axis': [1, 0, 0], 'up_axis': [0, 1, 0], 'forward_axis': [0, 0, -1], 'units': 'm'},
                                   'source_to_normalized': NORMALIZATION[:], 'interpretation_status': 'MSH part names (l = +X), headlamps at -Z, wheels on Y = 0',
                                   'evidence': ['MSH records']},
             'meshes': meshes, 'materials': materials, 'textures': textures, 'nodes': nodes,
             'measurements': {'wheelbase_m': abs(fl[2] - bl[2]), 'front_track_m': abs(fl[0] - fr[0]), 'rear_track_m': abs(bl[0] - br[0]),
                              'wheel_radius_m': radius['FL_WHEEL']},
             'selection': {'body_parts': present, 'wheels': wheel_report},
             'unknown_semantics': [{'id': 'native-rendering', 'status': 'UNSUPPORTED', 'meaning': 'RCX reflections, light halos and blend states are not reproduced'}]}
    result = uvs.save_scene(scene, output, assets, protected_roots=list(protected))
    return {**result, 'measurements': scene['measurements'], 'selection': scene['selection']}
