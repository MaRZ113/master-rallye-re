"""DRESSING1 read-only ownership diagnostics; components are never object counts.

PackFS, PSM visual strips and compiled DX are decoded by the established tools.
No asset writer, runtime simulation, PSM grammar extension or visibility guess.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import geometry_delta as g

ROOT = g.ROOT
CANDIDATES = (
    ('TURKEY3', 3620664, 'turkey3-shrub'),
    ('TURKEY3', 3429766, 'turkey3-hut'),
    ('TURKEY3', 3583641, 'turkey3-boat'),
    ('ITALY_S1', 3706566, 'italys1-pinus'),
)
METHODS = ('source_index', 'coordinate_vertex', 'coordinate_edge')


def stable_id(*parts):
    return hashlib.sha256(json.dumps(parts, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()[:24]


def local_output(path):
    path = Path(path).resolve()
    root = (ROOT/'data/dressing1').resolve()
    if not path.is_relative_to(root) or path == root:
        raise g.t.FormatError('Original-data diagnostics must remain under ignored data/dressing1')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def validate_hierarchy(nodes):
    """Validate decoder paths/counts, without inventing serialized transforms."""
    table = {}
    for node in nodes:
        path = node['path']
        if path in table or not isinstance(path, str) or not path:
            raise g.t.FormatError('Duplicate/invalid node path')
        if node['tag'] not in (0, 1, 2, 5, 6):
            raise g.t.FormatError('Unsupported selected landscape node tag')
        if not isinstance(node['offset'], int) or node['offset'] < 0:
            raise g.t.FormatError('Invalid node source offset')
        table[path] = node
    if set(p for p in table if '.' not in p) != {'root'}:
        raise g.t.FormatError('Expected one source root')
    children = Counter()
    for path in table:
        if path == 'root':
            continue
        parent = path.rsplit('.', 1)[0]
        if parent not in table:
            raise g.t.FormatError('Missing parent or cyclic/malformed hierarchy reference')
        children[parent] += 1
    for path, node in table.items():
        if children[path] != node['children']:
            raise g.t.FormatError('Source child count mismatch')
    return table


def components(faces, method='coordinate_edge', decimals=4):
    """Deterministic diagnostics: source indices, welded vertices or whole edges."""
    if method not in METHODS or not isinstance(decimals, int) or not 0 <= decimals <= 8:
        raise g.t.FormatError('Unsupported component method/precision')
    parent = list(range(len(faces)))
    owners = {}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(a, b):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)
    for i, face in enumerate(faces):
        if method == 'source_index':
            if len(face.indices) != 3:
                raise g.t.FormatError('Source-index grouping needs three original indices')
            keys = set(face.indices)
        else:
            points = [tuple(round(x, decimals) for x in p) for p in face.points]
            if method == 'coordinate_vertex':
                keys = set(points)
            else:
                # Zero-length edges do not connect unrelated degenerate records.
                keys = {tuple(sorted((points[a], points[b]))) for a, b in ((0, 1), (1, 2), (2, 0))
                        if points[a] != points[b]}
        for key in sorted(keys):
            if key in owners:
                join(i, owners[key])
            else:
                owners[key] = i
    groups = defaultdict(list)
    for i in range(len(faces)):
        groups[find(i)].append(i)
    return sorted(groups.values(), key=lambda ids: min(faces[i].identifier for i in ids))


def component_summary(faces, method, decimals=4):
    rows = []
    for ids in components(faces, method, decimals):
        selected = [faces[i] for i in ids]
        first = min(f.identifier for f in selected)
        rows.append({'component_id': stable_id(first, method, decimals),
                     'first_source_face': first, 'source_faces': len(ids),
                     'groups': sorted({f.group for f in selected}),
                     'bounds': g.bounds(p for f in selected for p in f.points),
                     'unique_xyz': len({p for f in selected for p in f.points}),
                     'area': sum(g.w.area_normal(f.points)[0] for f in selected),
                     'identity': 'GEOMETRIC_COMPONENT', 'instance_count': 'UNKNOWN'})
    return {'method': method, 'decimals': decimals if method != 'source_index' else None,
            'count': len(rows), 'face_count_histogram': dict(sorted(Counter(r['source_faces'] for r in rows).items())),
            'components': rows}


def transform_status(matrix):
    if matrix is None:
        return 'UNKNOWN'
    if len(matrix) != 4 or any(len(row) != 4 or any(not math.isfinite(x) for x in row) for row in matrix):
        raise g.t.FormatError('Expected finite 4x4 transform')
    a, b, c = matrix[:3]
    determinant = (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0])
                   + a[2]*(b[0]*c[1]-b[1]*c[0]))
    if abs(determinant) < 1e-12:
        raise g.t.FormatError('Singular transform')
    return 'MIRRORED_AUTHORED_TRANSFORM' if determinant < 0 else 'AUTHORED_TRANSFORM'


def sphere_eligibility(radius, center, view_position, view_direction, side_planes, range_value=None):
    """Float32 reconstruction of 0x00200550, explicit synthetic/captured inputs.

    Inputs are the four triples at view+8..+34, direction+0xb0, position+0xc0
    and optional graphics-config+0x28. This is not a complete scene selector.
    """
    values = [radius, *center, *view_position, *view_direction, *(v for p in side_planes for v in p)]
    if len(center) != 3 or len(view_position) != 3 or len(view_direction) != 3 or len(side_planes) != 4 or any(len(p)!=3 for p in side_planes):
        raise g.t.FormatError('Invalid sphere/view input layout')
    if range_value is not None: values.append(range_value)
    if not all(math.isfinite(x) for x in values): raise g.t.FormatError('Non-finite sphere/view inputs')
    def f(x):
        try: value=struct.unpack('<f',struct.pack('<f',x))[0]
        except OverflowError as exc: raise g.t.FormatError('Float32 sphere arithmetic overflow') from exc
        if not math.isfinite(value): raise g.t.FormatError('Float32 sphere arithmetic overflow')
        return value
    def mul(a,b):return f(f(a)*f(b))
    def dot(a,b):return f(f(mul(a[0],b[0])+mul(a[1],b[1]))+mul(a[2],b[2]))
    r=f(radius);delta=tuple(f(f(a)-f(b)) for a,b in zip(center,view_position))
    reason='ELIGIBLE'
    if r<=0:reason='NONPOSITIVE_RADIUS'
    elif range_value is not None and dot(delta,delta)>mul(f(f(range_value)+r),f(f(range_value)+r)):
        reason='OUTSIDE_RANGE_PLUS_RADIUS'
    elif range_value is not None and f(-dot(view_direction,delta))<f(-r):
        reason='BEHIND_DIRECTION_BOUNDARY'
    elif any(dot(delta,plane)>=r for plane in side_planes):reason='OUTSIDE_SIDE_PLANE'
    return {'eligible':reason=='ELIGIBLE','reason':reason,'precision':'FLOAT32_RECONSTRUCTION',
            'function':'0x00200550','runtime_visibility':'UNKNOWN'}


def authored_instances(rows):
    """Retain duplicate references; only explicit carriers establish instances.

    This is an evidence presentation API, not a claim about PSM component owners.
    Authored matrices are not promoted to current gaEntitySpline runtime poses.
    """
    result = []
    for ordinal, row in enumerate(rows):
        carrier = row.get('carrier_id')
        status = transform_status(row.get('matrix'))
        result.append({**row, 'reference_id': stable_id(row.get('source'), ordinal, row.get('name')),
                       'transform_status': status,
                       'identity': 'INDEPENDENT_TRANSFORM_INSTANCE' if carrier else 'AUTHORED_SCENE_REFERENCE',
                       'live_visible': 'UNKNOWN', 'runtime_pose': 'UNKNOWN'})
    return result


def rigid_shape_search(source_faces, target_faces, tolerance=.01, scale_range=(1., 1.), budget=10000):
    """Fitted proper-rigid/uniform-scale shape diagnostic, never authored placement.

    An anchor triangle supplies a hypothesis. Every source position AND triangle
    must then have a target counterpart. No shear, reflection or partial fit.
    """
    if not 0 < tolerance <= .01 or not 0 < scale_range[0] <= scale_range[1] <= 4 or budget < 1:
        raise g.t.FormatError('Unsupported shape diagnostic bounds')
    if not source_faces or not target_faces:
        return {'hypotheses': 0, 'matches': [], 'placement': 'UNKNOWN'}
    def sub(a, b): return tuple(x-y for x, y in zip(a, b))
    def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    def basis(points):
        u = sub(points[1], points[0]); length = math.sqrt(g.dot(u, u))
        if length <= 1e-9: return None
        u = tuple(x/length for x in u)
        n = cross(u, sub(points[2], points[0])); size = math.sqrt(g.dot(n, n))
        if size <= 1e-9: return None
        n = tuple(x/size for x in n)
        return (u, cross(n, u), n)
    anchor = max(source_faces, key=lambda f: (g.w.area_normal(f.points)[0], f.identifier)).points
    bs = basis(anchor)
    if bs is None: return {'hypotheses': 0, 'matches': [], 'placement': 'UNKNOWN', 'degenerate': True}
    lengths = [math.dist(anchor[i], anchor[j]) for i, j in ((0, 1), (0, 2), (1, 2))]
    source_points = sorted({p for f in source_faces for p in f.points})
    point_grid = defaultdict(list)
    for p in sorted({p for f in target_faces for p in f.points}):
        point_grid[g.w._cell(p, tolerance)].append(p)
    def nearest(p):
        return min((max(abs(x-y) for x, y in zip(p, q)) for key in g.w._neighbors(g.w._cell(p, tolerance))
                    for q in point_grid[key]), default=math.inf)
    matches, seen, hypotheses = [], set(), 0
    for target in sorted(target_faces, key=lambda f: f.identifier):
        for tri in itertools.permutations(target.points):
            scale = math.dist(tri[0], tri[1])/lengths[0]
            if scale_range == (1., 1.):
                scale = 1.
            elif not scale_range[0]-1e-6 <= scale <= scale_range[1]+1e-6:
                continue
            if any(abs(math.dist(tri[i], tri[j])-scale*length) > tolerance
                   for (i, j), length in zip(((0, 1), (0, 2), (1, 2)), lengths)): continue
            bt = basis(tri)
            if bt is None: continue
            rotation = tuple(tuple(sum(bt[k][i]*bs[k][j] for k in range(3)) for j in range(3)) for i in range(3))
            translation = tuple(tri[0][i]-scale*g.dot(rotation[i], anchor[0]) for i in range(3))
            key = (round(scale, 5), tuple(round(x, 5) for row in rotation for x in row),
                   tuple(round(x, 3) for x in translation))
            if key in seen: continue
            seen.add(key); hypotheses += 1
            if hypotheses > budget: raise g.t.FormatError('Shape hypothesis budget exceeded; split the search explicitly')
            def transform(p): return tuple(scale*g.dot(row, p)+translation[i] for i, row in enumerate(rotation))
            residual = max(nearest(transform(p)) for p in source_points)
            if residual > tolerance: continue
            evidence = g.w.match_geometry([tuple(transform(p) for p in f.points) for f in source_faces],
                                          [(f.points, f.group) for f in target_faces],
                                          [p for f in target_faces for p in f.points], tolerance=tolerance)
            if evidence['triangle_matches'] != len(source_faces): continue
            matches.append({'scale': scale, 'rotation_rows': rotation, 'translation': translation,
                            'maximum_vertex_residual': residual,
                            'maximum_corner_residual': evidence['maximum_corner_error'],
                            'source_faces': len(source_faces), 'target_groups': sorted(evidence['matched_pc_draws']),
                            'transform_provenance': 'FITTED_DIAGNOSTIC; not an authored or runtime transform',
                            'geometry_relation': 'CONGRUENT_SOURCE_SUBPART', 'evidence_grade': 'STATIC_INFERENCE'})
    return {'hypotheses': hypotheses, 'matches': matches, 'tolerance': tolerance,
            'scale_range': scale_range, 'placement': 'UNKNOWN',
            'method': 'Largest-area anchor / 6 permutations / all source positions and exact source triangles verified',
            'limitations': 'No changed-topology shape search; failure is not proof of family absence'}


def payload_for(manifest, ps2root, path):
    entries = [e for e in manifest['entries'] if e['path'] == path]
    if len(entries) != 1:
        raise g.t.FormatError('Missing/ambiguous canonical PackFS resource: ' + path)
    return g.t.read_payload(entries[0], ps2root/'TNG.000')


def pc_search_inventory(pcroot):
    """Bounded name/reference search, explicitly separate from geometry matching."""
    files = sorted((p for p in pcroot.rglob('*') if p.is_file()), key=lambda p: p.relative_to(pcroot).as_posix())
    families = {'shrub': ('shrub', 'bush', 'tree', 'vegetation'),
                'hut': ('hut', 'house', 'building', 'rustic', 'architecture'), 'boat': ('boat', 'dinghy'),
                'pinus': ('pinus', 'pine', 'plant'), 'haybale': ('haybal',)}
    dx = [p for p in files if p.suffix.lower() == '.dx']
    standalone = [p for p in dx if not any(x.lower() in ('course', 'vehicles', 'autoshow')
                                          for x in p.relative_to(pcroot).parts)]
    references = []
    texts = [p for p in files if p.suffix.lower() in ('.txt', '.xml')]
    for path in texts:
        data = path.read_bytes()
        if len(data) > g.c.MAX_XML:
            raise g.t.FormatError('Bounded reference search input too large')
        content = data.decode('latin1').lower()
        hits = [name for name, terms in families.items() if any(term in content for term in terms)]
        if hits:
            row = {'path': path.relative_to(pcroot).as_posix(), 'size': len(data), 'sha256': g.t.sha(data),
                   'families': hits, 'representation': 'TEXT_REFERENCE_LEAD'}
            if path.suffix.lower() == '.xml':
                if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                    raise g.t.FormatError('Unsupported XML declarations')
                try:
                    xml = ET.fromstring(data)
                except ET.ParseError as exc:
                    raise g.t.FormatError('Malformed searched XML: ' + str(path)) from exc
                # Name hits never imply instantiated visibility.
                row['model_references'] = [v.attrib.get('Value', '') for v in xml.iter()
                                           if v.attrib.get('Name', '').lower() in ('model', 'model name', 'en3d model name')]
            references.append(row)
    return {'pc_root': str(pcroot), 'file_count': len(files), 'compiled_dx_count': len(dx),
            'text_files_scanned': len(texts),
            'path_inventory_sha256': g.t.sha('\n'.join(p.relative_to(pcroot).as_posix() for p in files).encode()),
            'standalone_noncourse_nonvehicle_dx': [
                {'path': p.relative_to(pcroot).as_posix(), 'size': p.stat().st_size, 'sha256': g.t.file_hash(p)}
                for p in standalone],
            'text_reference_hits': references,
            'scope': 'All retail paths; all TXT/XML text; noncourse/nonvehicle DX identity inventory. '
                     'Geometry decoded only for selected paired courses, not every standalone model.',
            'negative_result': 'NOT_FOUND_IN_SCANNED_PC_CORPUS never means universal absence'}


def inspect_candidate(a, b, scene, course, offset, name):
    nodes = validate_hierarchy(scene.nodes)
    groups = [k for k, v in a.groups.items() if v['node_offset'] == offset]
    if len(groups) != 1:
        raise g.t.FormatError('Missing/ambiguous frozen candidate node')
    gid = groups[0]; owner = a.groups[gid]
    faces = [f for f in a.faces if f.group == gid]
    parent = owner['path'].rsplit('.', 1)[0]
    ancestors = [nodes[p] for p in sorted(nodes, key=lambda p: (p.count('.'), p))
                 if owner['path'].startswith(p+'.')]
    siblings = [{'source_id': k, 'node_offset': v['node_offset'], 'material': v['material'],
                 'textures': v['textures'], 'source_faces': sum(f.group == k for f in a.faces)}
                for k, v in sorted(a.groups.items()) if v['path'].rsplit('.', 1)[0] == parent]
    family = {g.texture_key(x) for x in owner['textures'] if x.lower() != 'null'}
    pc_groups = [k for k, v in b.groups.items() if family & {g.texture_key(x) for x in v['textures']}]
    pc_rows = [{'source_id': k, 'draw_index': b.groups[k]['draw_index'], 'textures': b.groups[k]['textures'],
                'materials': b.groups[k]['materials'],
                'shape': g.shape_summary([f for f in b.faces if f.group == k])} for k in sorted(pc_groups)]
    # Independent WATER1 exact-corner routine; no full-course rematch.
    match = g.w.match_geometry([f.points for f in faces],
                              [(f.points, b.groups[f.group]['draw_index']) for f in b.faces],
                              b.positions, tolerance=.001)
    shape_search = []
    whole_shape_search = None
    if name in ('turkey3-hut', 'turkey3-boat'):
        target = [f for f in b.faces if f.group in pc_groups]
        whole_shape_search = rigid_shape_search(faces, target, tolerance=.001)
        for ids in components(faces):
            selected = [faces[i] for i in ids]
            if len(selected) < 4:
                continue
            result = rigid_shape_search(selected, target, tolerance=.001)
            shape_search.append({'component_id': stable_id(min(f.identifier for f in selected), 'coordinate_edge', 4),
                                 'source_faces': len(selected), 'search': result})
    return {'schema': 1, 'candidate_id': name, 'course': course, 'source_id': gid,
            'ps2_source': a.source, 'pc_source': b.source, 'source_owner': owner,
            'hierarchy': ancestors + [nodes[owner['path']]], 'sibling_material_groups': siblings,
            'shape': g.shape_summary(faces),
            'decomposition': [component_summary(faces, m) for m in METHODS],
            'weld_sensitivity': [{'decimals': d, 'edge_components': len(components(faces, 'coordinate_edge', d))}
                                 for d in (3, 4, 5)],
            'exact_world_comparison': match, 'pc_family_draws': pc_rows,
            'fitted_subpart_shape_search': shape_search,
            'whole_group_shape_search': whole_shape_search,
            'identity': 'SOURCE_MESH_GROUP', 'instance_count': 'UNKNOWN',
            'serialized_local_transform': 'NONE in selected tags 1/6/5/2 grammar',
            'runtime_transform': 'Landscape carrier; current runtime matrix NOT_CAPTURED',
            'runtime_eligibility': 'Tag6 selection -> runtime bounding wrapper -> group/mesh draw; live selected subset UNKNOWN',
            'evidence_grade': 'CONFIRMED_BY_BOTH',
            'pc_geometry_relationship': 'Same texture family elsewhere is a search lead; exact candidate placement is independent',
            'implementation_ready': False,
            'portability': ['REQUIRES_DEEPER_PS2_RE', 'UNKNOWN'],
            'open_questions': ['Source subparts versus actual object population', 'Live culling selection',
                               'PC same-family shape and placement correspondence']}


def scene_study(ps2root, pcroot, sdk, manifest, course):
    xmlmod, _ = g.c.sdk_modules(sdk)
    path = '\\TNG\\DATASCENE\\RACETEST\\'+course.replace('_', '')+'.XML'
    content, provenance = payload_for(manifest, ps2root, path)
    summary, rows = g.c.parse_scene(content, path, xmlmod)
    doc = xmlmod.parse_course_xml_bytes(content, path)
    selected = []
    for ordinal, (egg, row) in enumerate(zip(doc.eggs, rows)):
        if not row['model']:
            continue
        matrix = egg.matrix()
        selected.append({**row, 'ordinal': ordinal,
                         'authored_matrix': matrix.rows if matrix else None,
                         'reference_id': stable_id(summary['sha256'], ordinal),
                         'identity': 'AUTHORED_SCENE_REFERENCE',
                         'independent_carrier': 'AMBIENT1 entity allocation; per Egg' if row['owners'] else 'NOT_RECOVERED_HERE',
                         'live_pose': 'UNKNOWN', 'live_visible': 'UNKNOWN'})
    filename = course.replace('_', '')+'.xml'
    pcpath = pcroot/'DataScene/RaceTest'/filename
    pcdata = pcpath.read_bytes()
    pcsummary, pcrows = g.c.parse_scene(pcdata, pcpath.relative_to(pcroot).as_posix(), xmlmod)
    return {'course': course, 'ps2_source': summary, 'packfs': provenance,
            'ps2_references': selected, 'pc_source': pcsummary,
            'pc_references': [dict(row, ordinal=i, identity='AUTHORED_SCENE_REFERENCE')
                              for i, row in enumerate(pcrows) if row['model']],
            'count_contract': 'Authored references retain duplicate transforms and are not live populations'}


def dinghy_study(ps2root, pcroot, sdk, manifest):
    result = g.dinghy_study(ps2root, pcroot, sdk)
    pc = g.pc_adapter(pcroot, sdk, 'FRANCE1')
    target = [f for f in pc.faces if any('dinghy' in g.texture_key(x) for x in pc.groups[f.group]['textures'])]
    model = result['ps2_models'][0]
    payload, _ = payload_for(manifest, ps2root, model['source']['path'])
    a = g.ps2_adapter(payload, model['source']['path'], standalone=True)
    result['local_shape_search'] = {'whole_model': rigid_shape_search(a.faces, target),
        'edge_components': [rigid_shape_search([a.faces[i] for i in ids], target)
                            for ids in components(a.faces)]}
    result['authored_scene'] = scene_study(ps2root, pcroot, sdk, manifest, 'FRANCE1')
    result['replacement_status'] = 'NOT_READY'
    result['safe_hide_unit'] = 'UNKNOWN: whole draws 897/904 aggregate unrelated subparts/placements'
    result['runtime_pose_provenance'] = 'AMBIENT1 0x001aa308 -> (*(entity+0x50))+0x20..0x5c; original route state not captured'
    return result


def haybale_study(ps2root, pcroot, sdk, manifest, italy_study):
    """The single optional family: references/resources only; no physics reverse."""
    path='\\TNG\\DATAPSM\\MISC\\HAYBALE\\HAYBALE.PSM'
    payload, provenance=payload_for(manifest,ps2root,path)
    result={'ps2_source':provenance,'geometry_status':'UNKNOWN','live_instances':'UNKNOWN','readiness':'NOT_READY'}
    try:
        model=g.ps2_adapter(payload,path,standalone=True)
        result['ps2_geometry']=model.source
    except g.t.FormatError as exc:
        # A declared failed optional probe; never a skipped/faked parse success.
        result['geometry_blocker']=str(exc)
        result['geometry_status']='NOT_DECODED: strict standalone EOF grammar refused; no speculative extension'
    g.c.sdk_modules(sdk)
    from master_rallye.course_source import parse_course_txt
    txt=pcroot/'DataGx/Course/Italy_S1/Italy_S1.txt';doc=parse_course_txt(txt)
    named=[n for n in doc.nodes if 'haybal' in n.name.lower()]
    result['pc_txt_source']={'path':txt.relative_to(pcroot).as_posix(),'sha256':g.t.file_hash(txt)}
    result['pc_txt_name_lead_count']=len(named)
    result['pc_txt_name_lead_classes']=dict(sorted(Counter(n.class_name for n in named).items()))
    result['pc_txt_name_lead_samples']=[{'node_id':n.node_id,'name':n.name,'parent_id':n.parent_id,
        'source_index':n.mesh_index,'source_size':n.mesh_size,'class':n.class_name} for n in named[:12]]
    model=pcroot/'DataGx/Misc/Haybale/haybaletest.dx'
    result['pc_standalone']={'path':model.relative_to(pcroot).as_posix(),'sha256':g.t.file_hash(model),
                            'presence':'RESOURCE_EXISTS; current course instance UNKNOWN'}
    refs=[r for r in italy_study['ps2_references'] if 'haybal' in r['model']]
    result.update(authored_references=len(refs),unique_matrix_hashes=len({r['matrix_sha256'] for r in refs}),
                  references=[{k:r[k] for k in ('reference_id','ordinal','egg','model','matrix_sha256','owners')} for r in refs])
    return result


def build(ps2root, pcroot, sdk):
    manifest, _ = g.t.load_pak(ps2root/'TNG.PAK')
    cards, alignment = [], {}
    cache = {}
    for course, offset, name in CANDIDATES:
        if course not in cache:
            a, b, proof = g.load_pair(ps2root, pcroot, sdk, course)
            payload, _ = payload_for(manifest, ps2root, a.source['path'])
            scene = g.w.decode_scene(payload)
            cache[course] = (a, b, scene)
            alignment[course] = proof
        a, b, scene = cache[course]
        cards.append(inspect_candidate(a, b, scene, course, offset, name))
    studies=[scene_study(ps2root,pcroot,sdk,manifest,course) for course in ('TURKEY3','ITALY_S1')]
    return {'schema': 1, 'phase': 'PS2-DRESSING1', 'coordinate_frame': 'GAME_SOURCE',
            'alignment': alignment, 'candidates': cards, 'pc_search': pc_search_inventory(pcroot),
            'scene_studies': studies,
            'dinghy_study': dinghy_study(ps2root, pcroot, sdk, manifest),
            'haybale_study':haybale_study(ps2root,pcroot,sdk,manifest,studies[1]),
            'ps2_noncourse_family_paths': [dict(path=e['path'], offset=e['offset'], stored_size=e['stored_size'])
                for e in manifest['entries'] if e['path'].endswith('.PSM') and '\\COURSE\\' not in e['path']
                and any(x in e['path'].lower() for x in ('boat','dinghy','hut','house','shrub','bush','pinus','pine','haybal'))],
            'runtime_validation': 'NOT_PERFORMED',
            'count_contract': 'Mesh groups, components, authored references and independent transform carriers stay separate'}


def compact_inventory(data):
    """Reviewable counts/bounds/provenance, no mesh arrays or scene-position dump."""
    cards=[]
    for original in data['candidates']:
        card=dict(original)
        card['decomposition']=[dict(x,components=x['components'] if x['method']=='coordinate_edge' else x['components'][:2],
                                    retained_samples='All coordinate-edge components; two examples for other methods, complete counts preserved')
                               for x in original['decomposition']]
        card['fitted_subpart_shape_search']=[]
        for row in original['fitted_subpart_shape_search']:
            search=dict(row['search']);matches=search['matches']
            search['verified_transform_hypotheses']=len(matches)
            search['matches']=matches[:2]
            search['retained_samples']='At most two fitted transforms per source component; all hypotheses in ignored full diagnostic'
            card['fitted_subpart_shape_search'].append({**row,'search':search})
        card['comparable_instance_count']='UNKNOWN'
        positives=sum(bool(r['search']['matches']) for r in original['fitted_subpart_shape_search'])
        card['pc_verified_subpart_components']=positives
        if positives:
            card['pc_geometry_relationship']='CONGRUENT_SOURCE_SUBPARTS_AT_DIFFERENT_PLACEMENTS; whole-object/instance mapping UNKNOWN'
            card['portability']=['REUSE_EXISTING_PC_MESH','REQUIRES_DEEPER_PS2_RE']
        else:
            card['pc_geometry_relationship']='NO_EXACT_WORLD_MATCH; family geometry correspondence UNKNOWN'
        if original.get('whole_group_shape_search') and original['whole_group_shape_search']['matches']:
            card['pc_geometry_relationship']='CONGRUENT_WHOLE_SOURCE_GROUP_AT_DIFFERENT_PLACEMENT; authored instance map UNKNOWN'
        card['evidence_grades']={'source_material_and_geometry':'CONFIRMED_BY_BYTES',
            'source_runtime_hierarchy':'CONFIRMED_BY_BOTH','fitted_shape_relation':'STATIC_INFERENCE',
            'live_selected_group':'UNKNOWN','runtime_validation':'NOT_PERFORMED'}
        card['readiness']='NOT_READY'
        cards.append(card)
    pc=dict(data['pc_search'])
    pc['text_reference_hits']=[{k:v for k,v in row.items() if k!='model_references'}
                                for row in pc['text_reference_hits']]
    scenes=[]
    for study in [*data['scene_studies'],data['dinghy_study']['authored_scene']]:
        scenes.append({'course':study['course'],
            'ps2_source':{k:v for k,v in study['ps2_source'].items() if not k.startswith('_')},
            'pc_source':{k:v for k,v in study['pc_source'].items() if not k.startswith('_')},
            'selected_references':[{k:r.get(k) for k in ('reference_id','ordinal','list','egg','model','owners','matrix_sha256','identity','authored_visible')}
                                  for r in study['ps2_references'] if 'dinghy' in r['model'] or 'haybal' in r['model']],
            'count_contract':study['count_contract']})
    dinghy={k:v for k,v in data['dinghy_study'].items() if k!='authored_scene'}
    return {'schema':1,'phase':data['phase'],'coordinate_frame':data['coordinate_frame'],
            'candidates':cards,'pc_search':pc,'scene_studies':scenes,'dinghy_study':dinghy,
            'haybale_study':data.get('haybale_study'),
            'ps2_noncourse_family_paths':data['ps2_noncourse_family_paths'],
            'runtime_validation':data['runtime_validation'],'count_contract':data['count_contract']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, required=True)
    ap.add_argument('--pc-root', type=Path, required=True)
    ap.add_argument('--sdk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--compact-output', type=Path,
                    help='Optional reviewable summary, also restricted to ignored dressing1 data')
    args = ap.parse_args()
    out = local_output(args.output)
    data=build(args.ps2_root, args.pc_root, args.sdk)
    g.t.write_json(out,data)
    if args.compact_output:g.t.write_json(local_output(args.compact_output),compact_inventory(data))
    print(json.dumps({'output': str(out), 'candidates': 4, 'runtime': 'NOT_PERFORMED'}))


if __name__ == '__main__':
    main()
