"""GEOM1 read-only source geometry comparison. No asset writer or registration fit.

PSM/PackFS decoding and validated DX reading are delegated to existing readers.
Polygon subtraction measures union coverage without counting duplicate triangles
twice. Original coordinates and full relation tables belong in ignored data/geom1.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
import struct
import time

import tngtool as t
import water_runtime as w
import course_delta as c

ROOT = Path(__file__).resolve().parents[1]
COURSES = ('TURKEY3', 'FRANCE1', 'ITALY_S1')
PROFILES = {
    'strict': dict(vertex=.0001, plane=.0001, normal=.99999, coverage=.99999, near=.1),
    'baseline': dict(vertex=.001, plane=.001, normal=.99999, coverage=.99999, near=1.),
    'relaxed': dict(vertex=.01, plane=.01, normal=.9999, coverage=.9999, near=1.),
}
AREA_EPSILON = 1e-7


@dataclass(frozen=True)
class Face:
    identifier: str
    group: str
    points: tuple
    indices: tuple = ()
    reference: tuple = ()

    def __post_init__(self):
        if len(self.points) != 3 or any(len(p) != 3 or not all(math.isfinite(x) for x in p)
                                        for p in self.points):
            raise t.FormatError('Expected three finite source-space positions')


@dataclass
class Geometry:
    source: dict
    groups: dict
    faces: list[Face]
    positions: tuple


def normal(points):
    a, b, c0 = points
    u, v = [b[i]-a[i] for i in range(3)], [c0[i]-a[i] for i in range(3)]
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(sum(x*x for x in n))
    return tuple(x/length for x in n) if length else (0., 0., 0.)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def bounds(points):
    points = list(points)
    return {'min': [min(p[i] for p in points) for i in range(3)],
            'max': [max(p[i] for p in points) for i in range(3)]} if points else None


def signed_area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1]))/2


def halfplane(poly, a, b, inside):
    """Convex polygon half-plane clipping in the dominant-axis projection."""
    if not poly:
        return []
    def side(p):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    out = []
    prev, sp = poly[-1], side(poly[-1])
    for cur in poly:
        sc = side(cur)
        ip, ic = (sp >= 0, sc >= 0) if inside else (sp <= 0, sc <= 0)
        if ip != ic:
            f = sp/(sp-sc)
            out.append((prev[0]+f*(cur[0]-prev[0]), prev[1]+f*(cur[1]-prev[1])))
        if ic:
            out.append(cur)
        prev, sp = cur, sc
    return out if len(out) >= 3 and abs(signed_area(out)) > 1e-14 else []


def subtract_convex(poly, cutter):
    """Return disjoint convex pieces of poly outside the CCW convex cutter."""
    if signed_area(cutter) < 0:
        cutter = list(reversed(cutter))
    pieces, remainder = [], poly
    for a, b in zip(cutter, cutter[1:]+cutter[:1]):
        outside = halfplane(remainder, a, b, False)
        if outside:
            pieces.append(outside)
        remainder = halfplane(remainder, a, b, True)
        if not remainder:
            break
    return pieces


def union_coverage(points, other_points, fragment_budget=4096):
    n = normal(points)
    axis = max(range(3), key=lambda i: abs(n[i]))
    axes = [i for i in range(3) if i != axis]
    origin = points[0]
    project = lambda tri: [(p[axes[0]]-origin[axes[0]], p[axes[1]]-origin[axes[1]]) for p in tri]
    poly = project(points)
    area = abs(signed_area(poly))
    if not area:
        return 0.
    pieces = [poly]
    for tri in other_points:
        cutter = project(tri)
        if abs(signed_area(cutter)) < 1e-14:
            continue
        pieces = [part for piece in pieces for part in subtract_convex(piece, cutter)]
        if len(pieces) > fragment_budget:
            raise t.FormatError('Surface subtraction exceeded explicit fragment budget')
        if not pieces:
            return 1.
    return max(0., min(1., 1-sum(abs(signed_area(p)) for p in pieces)/area))


class SpatialIndex:
    """3D AABB hash; sorted identifiers make candidate ordering deterministic."""
    def __init__(self, faces, cell=32., max_cells=2000000):
        if not math.isfinite(cell) or cell <= 0:
            raise t.FormatError('Invalid spatial cell size')
        self.faces, self.cell = faces, cell
        self.cells = defaultdict(list)
        self.boxes, self.normals = [], []
        total = 0
        for i, face in enumerate(faces):
            box = bounds(face.points)
            self.boxes.append(box)
            self.normals.append(normal(face.points))
            ranges = [range(math.floor(box['min'][j]/cell), math.floor(box['max'][j]/cell)+1)
                      for j in range(3)]
            count = math.prod(len(r) for r in ranges)
            total += count
            if total > max_cells:
                raise t.FormatError('AABB index exceeded explicit cell budget; no groups skipped')
            for key in itertools.product(*ranges):
                self.cells[key].append(i)

    def candidates(self, box, margin):
        ranges = [range(math.floor((box['min'][j]-margin)/self.cell),
                        math.floor((box['max'][j]+margin)/self.cell)+1) for j in range(3)]
        ids = {i for key in itertools.product(*ranges) for i in self.cells.get(key, ())}
        return [i for i in sorted(ids) if all(self.boxes[i]['min'][j] <= box['max'][j]+margin
                   and self.boxes[i]['max'][j] >= box['min'][j]-margin for j in range(3))]


def vertex_agreement(source, target, epsilon):
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise t.FormatError('Invalid vertex tolerance')
    source = list(source)
    target = list(target)
    source_bits = {struct.pack('<3f', *p) for p in source}
    bits = {struct.pack('<3f', *p) for p in target}
    target = sorted(set(target))
    numeric = set(target)
    grid = defaultdict(list)
    for p in target:
        grid[w._cell(p, 10*epsilon)].append(p)
    source = sorted(set(source))
    hits = sum(any(max(abs(a-b) for a, b in zip(p, q)) <= epsilon
               for key in w._neighbors(w._cell(p, 10*epsilon)) for q in grid.get(key, ()))
               for p in source)
    return {'source_unique_numeric_positions': len(source),
            'target_unique_numeric_positions': len(target),
            'source_unique_bitwise_positions': len(source_bits),
            'target_unique_bitwise_positions': len(bits),
            'bitwise_float32_matches': len(source_bits & bits),
            'numeric_matches': sum(p in numeric for p in source), 'tolerance_matches': hits,
            'signed_zero_note': 'Numeric equality coalesces signed zero; bitwise positions retain both encodings'}


def direction_match(source, target, profile, extra_label):
    eps = profile['vertex']
    exact_grid = defaultdict(list)
    for i, f in enumerate(target):
        if w.area_normal(f.points)[0] > AREA_EPSILON:
            exact_grid[w._cell(w.centroid(f.points), 100*eps)].append(i)
    spatial = SpatialIndex(target)
    rows, exact_pairs, surface_pairs, clip_pairs = [], 0, 0, 0
    for face in source:
        area = w.area_normal(face.points)[0]
        row = {'source': face.identifier, 'group': face.group, 'source_reference': face.reference,
               'source_indices': face.indices, 'area': area, 'coverage': 0., 'other_groups': [],
               'targets': [], 'maximum_corner_error': None, 'plane_gap': None,
               'raw_order_parity': None, 'runtime_visibility': 'UNKNOWN'}
        if area <= AREA_EPSILON:
            row['geometry_relation'] = 'DIAGNOSTIC_DEGENERATE'
            rows.append(row)
            continue
        candidates = sorted({i for key in w._neighbors(w._cell(w.centroid(face.points), 100*eps))
                             for i in exact_grid.get(key, ())})
        exact_pairs += len(candidates)
        hits = []
        for i in candidates:
            error = w.corner_error(face.points, target[i].points)
            if error <= eps:
                hits.append((error, target[i].identifier, i))
        if hits:
            error, _, i = min(hits)
            permutation = min(itertools.permutations(range(3)), key=lambda order:
                max(abs(x-y) for p, k in zip(face.points, order) for x, y in zip(p, target[i].points[k])))
            row.update(geometry_relation='EXACT_TRIANGLE_MATCH', coverage=1.,
                       maximum_corner_error=error, targets=[target[j].identifier for _, _, j in sorted(hits)],
                       other_groups=sorted({target[j].group for _, _, j in hits}),
                       raw_order_parity=sum(permutation[a] > permutation[b] for a in range(3) for b in range(a+1, 3))%2,
                       correspondence_multiplicity=len(hits))
        else:
            n, box = normal(face.points), bounds(face.points)
            near = spatial.candidates(box, profile['near'])
            surface_pairs += len(near)
            planar, parallel, gaps = [], [], []
            for i in near:
                if abs(dot(n, spatial.normals[i])) < profile['normal']:
                    continue
                gap = max(abs(dot(n, tuple(p[j]-face.points[0][j] for j in range(3))))
                          for p in target[i].points)
                if gap <= profile['plane']:
                    planar.append(i)
                elif gap <= profile['near']:
                    parallel.append(i)
                    gaps.append(gap)
            # Only actual projected overlaps enter ownership. Nearby planes alone
            # do not associate an unrelated group with this source surface.
            planar = [i for i in planar if union_coverage(face.points, [target[i].points]) > 1e-8]
            parallel = [i for i in parallel if union_coverage(face.points, [target[i].points]) > 1e-8]
            clip_pairs += len(planar)+len(parallel)
            coverage = union_coverage(face.points, (target[i].points for i in planar))
            near_coverage = union_coverage(face.points, (target[i].points for i in parallel))
            if coverage >= profile['coverage']:
                relation, used = 'SAME_SURFACE_DIFFERENT_TRIANGULATION', planar
            elif coverage > 1e-8:
                relation, used = 'PARTIAL_SURFACE_OVERLAP', planar
            elif near_coverage > 1e-8:
                relation, used = 'GEOMETRY_MODIFIED', parallel
            else:
                relation, used = extra_label, []
            row.update(geometry_relation=relation, coverage=coverage, near_coverage=near_coverage,
                       targets=[target[i].identifier for i in used], other_groups=sorted({target[i].group for i in used}),
                       plane_gap=min((max(abs(dot(n, tuple(p[j]-face.points[0][j] for j in range(3))))
                                          for p in target[i].points) for i in used), default=None))
        row['evidence_grade'] = ('CONFIRMED_BY_BYTES' if row['geometry_relation']=='EXACT_TRIANGLE_MATCH'
                                 else 'STATIC_INFERENCE')
        rows.append(row)
    return rows, {'exact_candidate_pairs': exact_pairs, 'surface_aabb_candidate_pairs': surface_pairs,
                  'projected_overlap_pairs': clip_pairs, 'spatial_cell': spatial.cell,
                  'index_cells': len(spatial.cells)}


def texture_key(value):
    return value.replace('\\', '/').split('/')[-1].lower()


def edge_components(faces):
    """Source components using complete coordinate-welded edges, never instances."""
    parent=list(range(len(faces)));edges={}
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,f in enumerate(faces):
        keys=[tuple(round(v,4) for v in p) for p in f.points]
        for a,b in ((0,1),(1,2),(2,0)):
            key=tuple(sorted((keys[a],keys[b])))
            if key in edges:parent[find(i)]=find(edges[key])
            else:edges[key]=i
    components=defaultdict(list)
    for i in range(len(faces)):components[find(i)].append(i)
    return sorted(components.values(),key=lambda ids:faces[ids[0]].identifier)


def shape_summary(faces):
    points=sorted({p for f in faces for p in f.points})
    bb=bounds(points)
    edges=sorted({round(math.dist(a,b),6) for f in faces for a,b in itertools.combinations(f.points,2)})
    return {'triangles':len(faces),'unique_positions':len(points),'bounds':bb,
        'source_axis_extents':[bb['max'][i]-bb['min'][i] for i in range(3)] if bb else None,
        'maximum_pair_distance':max((math.dist(a,b) for a,b in itertools.combinations(points,2)),default=0.),
        'area':sum(w.area_normal(f.points)[0] for f in faces),'unique_edge_length_samples':edges[:20]}


def dinghy_study(ps2root,pcroot,sdk):
    manifest,_=t.load_pak(ps2root/'TNG.PAK')
    models=[]
    for name in ('BLUEDINGHY','REDDINGHY'):
        path='\\TNG\\DATAPSM\\MISC\\OBJECTS\\DINGHYS\\'+name+'.PSM'
        entries=[e for e in manifest['entries'] if e['path']==path]
        if len(entries)!=1:raise t.FormatError('Missing/ambiguous standalone dinghy')
        payload,prov=t.read_payload(entries[0],ps2root/'TNG.000')
        geom=ps2_adapter(payload,path,standalone=True)
        models.append({'source':geom.source,'packfs':prov,'shape':shape_summary(geom.faces),
            'components':[shape_summary([geom.faces[i] for i in ids]) for ids in edge_components(geom.faces)],
            'position_sha256':t.sha(b''.join(struct.pack('<3f',*p) for p in geom.positions)),
            'labels':['PS2_STANDALONE_DYNAMIC_MODEL'],'runtime_pose':'AMBIENT1 spline publication; not authored Row3'})
    pc=pc_adapter(pcroot,sdk,'FRANCE1')
    candidates=[f for f in pc.faces if any('dinghy' in texture_key(x) for x in pc.groups[f.group]['textures'])]
    parts=[{'first_source_face':candidates[ids[0]].identifier,
            'draws':sorted({pc.groups[candidates[i].group]['draw_index'] for i in ids}),
            **shape_summary([candidates[i] for i in ids])} for ids in edge_components(candidates)]
    xml,_=c.sdk_modules(sdk)
    e=next(e for e in manifest['entries'] if e['path']=='\\TNG\\DATASCENE\\RACETEST\\FRANCE1.XML')
    content,prov=t.read_payload(e,ps2root/'TNG.000')
    _,eggs=c.parse_scene(content,e['path'],xml)
    authored=[x for x in eggs if x['model'] and 'dinghy' in x['model']]
    return {'schema':1,'course':'FRANCE1','ps2_models':models,'ps2_authored_references':authored,
        'pc_source':pc.source,'pc_candidate_triangles':len(candidates),
        'pc_compiled_draws':sorted({pc.groups[f.group]['draw_index'] for f in candidates}),
        'pc_edge_components':parts,'component_method':'Complete edges, decimal coordinate rounding 1e-4; NOT boat instance count',
        'labels':['PS2_STANDALONE_DYNAMIC_MODEL','PC_BAKED_STATIC_GEOMETRY','PLACEMENT_CORRESPONDENCE_UNKNOWN'],
        'geometry_shape_relation':'UNKNOWN until independent local/world orientation and partition correspondence',
        'duplication_risk':'Existing compiled dinghy geometry is a replace/hide candidate only after instance correspondence',
        'txt_link':'Literal hull/mast names are source metadata; no direct TXT Index to DX face mapping assumed',
        'runtime_validation':'NOT_PERFORMED'}


def material_relation(ps2, pc):
    a = [texture_key(x) for x in ps2['textures']]
    b = [texture_key(x) for x in pc['textures']]
    while a and a[-1] in ('null', ''): a.pop()
    while b and b[-1] in ('null', ''): b.pop()
    names = sorted(set(pc['materials']))
    if a != b:
        return 'DIFFERENT_TEXTURE_BINDING'
    if len(names) != 1:
        return 'UNRESOLVED_MATERIAL_MAPPING'
    left, right = w.shader_contract(ps2['material']), w.shader_contract(names[0])
    if left['interned_shader'] != right['interned_shader']:
        return 'DIFFERENT_SHADER_SEMANTICS'
    if ps2['material'].strip().lower() == names[0].strip().lower():
        return 'SAME_OR_EQUIVALENT_MATERIAL'
    return 'UNRESOLVED_MATERIAL_MAPPING'


def ps2_adapter(payload, resource, standalone=False):
    scene = w.decode_scene(payload, terminator=0xffffffff if standalone else 100)
    h = t.sha(payload)
    groups, faces, exclusions = {}, [], Counter()
    for mesh in scene.meshes:
        gid = 'PS2:'+h+':node:%x' % mesh['node_offset']
        groups[gid] = {k: mesh[k] for k in ('path', 'node_offset', 'material_offset', 'material',
                                           'flags', 'word70_unknown', 'strips')}
        groups[gid].update(textures=[next((x['name'] for x in mesh['textures'] if x['slot']==slot),'Null') for slot in range(3)],
                           texture_slots=mesh['textures'], representation='PS2_VISUAL_SOURCE_MESH',
                           ancestors=[n for n in scene.nodes if mesh['path'].startswith(n['path']+'.')],
                           hierarchy='SOURCE_PATH_PRESERVED; branch selection UNKNOWN', materials=[mesh['material']])
        for si, strip in enumerate(mesh['strips']):
            for vi in range(strip['start']+2, strip['start']+strip['count']):
                if scene.control(vi)&1:
                    exclusions['adc_suppressed'] += 1
                    continue
                ids=(vi-2,vi-1,vi)
                points=tuple(scene.position(i) for i in ids)
                if w.area_normal(points)[0] <= AREA_EPSILON:
                    exclusions['area_at_or_below_diagnostic_cutoff'] += 1
                faces.append(Face(gid+':strip:%d:newest:%d'%(si,vi),gid,points,ids,
                                  (si,vi,strip['offset'],strip['flag'],strip['scale'])))
    return Geometry({'path':resource,'decoded_sha256':h,'decoded_size':len(payload),
        'vertex_count':scene.vertex_count,'visual_tree_start':scene.start,'visual_tree_end':scene.end,
        'terminator':0xffffffff if standalone else 100,'node_counts':scene.node_counts,
        'mesh_count':len(groups),'triangle_records':len(faces),'exclusions':dict(exclusions),
        'coordinates':'MODEL_LOCAL' if standalone else 'GAME_SOURCE',
        'strip_winding':'Ordered consecutive triples retained; rendered parity/culling UNKNOWN'},
        groups,faces,tuple(scene.position(i) for i in range(scene.vertex_count)))


def pc_adapter(pc_root, sdk, course):
    xmlmod, sidecar = c.sdk_modules(sdk)
    from master_rallye.dx_course import parse_course_dx
    from master_rallye.course_source import parse_course_txt
    folder=pc_root/'DataGx'/'Course'/w.CASES[course]
    dxs=sorted(folder.glob('*.dx'));txts=sorted(folder.glob('*.txt'))
    if len(dxs)!=1 or len(txts)!=1:
        raise t.FormatError('Expected one canonical DX and TXT in paired course folder')
    model=parse_course_dx(dxs[0]);meta=sidecar.parse_sidecar(txts[0]);txt=parse_course_txt(txts[0])
    sidecar.apply_material_candidates(model.physical_draws,meta)
    if not model.course_render_validated:
        raise t.FormatError('SDK complete-disjoint draw coverage not validated')
    h=t.file_hash(dxs[0]);txt_hash=t.file_hash(txts[0])
    frozen=json.loads((ROOT/'water1'/'case-evidence.json').read_text())
    known=next(x['pc'] for x in frozen['cases'] if x['course']==course)
    if h!=known['dx_sha256'] or txt_hash!=known['sidecar_sha256']:
        raise t.FormatError('Selected PC retail DX/TXT identity differs from verified WATER1 corpus')
    faces=[];groups={}
    for draw in model.physical_draws:
        gid='PC:'+h+':draw:%d'%draw.draw_index
        groups[gid]={'draw_index':draw.draw_index,'record_path':draw.record_path,'record_offset':draw.offset,
            'group_label':draw.group_label,'tag':draw.tag,'control_words':draw.control_words,
            'index_start':draw.index_start,'index_count':draw.index_count,'vertex_base':draw.vertex_base,
            'textures':list(draw.texture_tuple),'materials':[m.name for m in draw.material_candidates],
            'material_numbers':[m.number for m in draw.material_candidates],
            'material_mapping':'ORDERED_TEXTURE_TUPLE_CANDIDATES; uniqueness retained',
            'representation':'PC_COMPILED_RENDER_DRAW','hierarchy':'Compiled record path; live subset UNKNOWN'}
        ids=model.draw_global_indices(draw)
        for i in range(0,len(ids),3):
            refs=tuple(ids[i:i+3]);pts=tuple(model.vertices.positions[j] for j in refs)
            faces.append(Face(gid+':triangle:%d'%(i//3),gid,pts,refs,(i//3,draw.index_start+i)))
    return Geometry({'path':str(dxs[0].relative_to(pc_root)),'sha256':h,'size':dxs[0].stat().st_size,
        'txt_path':str(txts[0].relative_to(pc_root)),'txt_sha256':txt_hash,
        'position_array_offset':model.vertices.position_offset,
        'retail_identity':'Fresh SHA matches independent frozen WATER1 source identities',
        'draws':len(groups),'vertices':model.vertex_count,'triangles':model.triangle_count,
        'coverage':'VALIDATED_COMPLETE_DISJOINT','txt_mesh_records':len(meta.meshes),
        'txt_named_nodes':len(txt.nodes),'txt_to_compiled_face_mapping':'UNKNOWN: source spans are not DX face IDs',
        'txt_dinghy_leads':[{'node_id':n.node_id,'name':n.name,'parent_id':n.parent_id,
            'source_index':n.mesh_index,'source_size':n.mesh_size} for n in txt.nodes
            if 'dinghy' in n.name.lower()], 'coordinates':'GAME_SOURCE'},groups,faces,model.vertices.positions)


def alignment(ps2root,pcroot,sdk,course,manifest):
    pairs=json.loads((ROOT/'cdelta1'/'course-pairs.json').read_text())
    expected=c.normalize('course/'+course+'/'+course)
    selected=[p for p in pairs if p['landscape']==expected]
    if len(selected)!=1:
        raise t.FormatError('Missing/ambiguous internal landscape identity in course pairs')
    pair=selected[0]
    if pair['confidence'] not in ('STRONG','EXACT'):
        raise t.FormatError('Course identity is not confidently paired')
    xml,_=c.sdk_modules(sdk)
    entry=next(e for e in manifest['entries'] if e['path']==pair['ps2'])
    data,prov=t.read_payload(entry,ps2root/'TNG.000')
    pcdata=(pcroot/pair['pc']).read_bytes()
    a,_=c.parse_scene(data,pair['ps2'],xml);b,_=c.parse_scene(pcdata,pair['pc'],xml)
    align=c.route_alignment(a['_route_points'],b['_route_points'])
    if align is None or align['within_one_world_unit']<.95 or a['landscape']!=pair['landscape'] or b['landscape']!=pair['pc_landscape']:
        raise t.FormatError('Fresh independent route identity/alignment failed')
    matrices=[]
    for content in (data,pcdata):
        doc=xml.parse_course_xml_bytes(content)
        eggs=[e for e in doc.eggs if e.list_name=='landscape' and e.model_name]
        if len(eggs)!=1 or eggs[0].matrix() is None:
            raise t.FormatError('Missing/ambiguous authored landscape matrix')
        matrices.append(eggs[0].matrix().rows)
    if matrices[0]!=matrices[1]:
        raise t.FormatError('Different landscape transforms require separate RE; no arbitrary fit')
    for matrix in matrices:
        require_identity_transform(matrix)
    return {'transform':'IDENTITY_IN_SOURCE_FRAME; NO_FIT','independent_anchor':'ORDERED_RACELINE',
        'route_residual':align,'ps2_route_sha256':t.sha(data),'pc_route_sha256':t.sha(pcdata),
        'authored_landscape_matrices':matrices,'runtime_transform':'UNKNOWN',
        'evidence_grade':'CONFIRMED_BY_BYTES'}


def require_identity_transform(matrix):
    expected=[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
    if [list(row) for row in matrix]!=expected:
        raise t.FormatError('Non-identity source transform unsupported; explicit independent RE required')


def aggregate(rows,geometry,other,ps2_direction):
    result=[]
    buckets=defaultdict(list)
    for row in rows:
        rels=[]
        for gid in row['other_groups']:
            a,b=(geometry.groups[row['group']],other.groups[gid]) if ps2_direction else (other.groups[gid],geometry.groups[row['group']])
            rels.append(material_relation(a,b))
        mat=rels[0] if len(set(rels))==1 else 'UNRESOLVED_MATERIAL_MAPPING' if rels else 'UNKNOWN'
        buckets[row['group'],row['geometry_relation'],mat].append(row)
    face_lookup={f.identifier:f for f in geometry.faces}
    for (gid,relation,mat),rs in sorted(buckets.items()):
        ids={r['source'] for r in rs}
        fs=[face_lookup[i] for i in sorted(ids)]
        peers=sorted({g for r in rs for g in r['other_groups']})
        result.append({'delta_id':t.sha((gid+'|'+relation+'|'+mat).encode())[:24],
            'source_id':gid,'source':geometry.groups[gid],'other_group_ids':peers,
            'geometry_relation':relation,'material_relation':mat,'source_triangles':len(rs),
            'area':sum(r['area'] for r in rs),'bounds':bounds(p for f in fs for p in f.points),
            'coverage':{'min':min(r['coverage'] for r in rs),'max':max(r['coverage'] for r in rs)},
            'maximum_corner_error':max((r['maximum_corner_error'] for r in rs if r['maximum_corner_error'] is not None),default=None),
            'plane_gap_range':([min(v),max(v)] if (v:=[r['plane_gap'] for r in rs if r['plane_gap'] is not None]) else None),
            'face_reference_samples':[{'id':f.identifier,'indices':f.indices,'reference':f.reference} for f in fs[:2]],
            'visibility':'ALL_DECODED_AUTHORED_SOURCE; LIVE_LOD/ACTIVE_SUBSET_UNKNOWN',
            'evidence_grade':'CONFIRMED_BY_BYTES' if relation=='EXACT_TRIANGLE_MATCH' else 'STATIC_INFERENCE',
            'exclusivity_scope':'Examined compiled landscape only; unmatched labels are bounded candidates'})
    return result


def compare(a,b,profile='baseline'):
    if profile not in PROFILES: raise t.FormatError('Unknown tolerance profile')
    p=PROFILES[profile]
    forward,perf1=direction_match(a.faces,b.faces,p,'PS2_EXTRA_VISUAL_SOURCE')
    reverse,perf2=direction_match(b.faces,a.faces,p,'PC_EXTRA_COMPILED_DRAW')
    groups=aggregate(forward,a,b,True)+aggregate(reverse,b,a,False)
    return {'schema':1,'coordinate_system':'GAME_SOURCE','ps2_source':a.source,'pc_source':b.source,
        'matching_profile':profile,'thresholds':p,'diagnostic_area_cutoff':AREA_EPSILON,
        'ps2_relations':dict(sorted(Counter(r['geometry_relation'] for r in forward).items())),
        'pc_relations':dict(sorted(Counter(r['geometry_relation'] for r in reverse).items())),
        'material_relations':dict(sorted(Counter(r['material_relation'] for r in groups).items())),
        'vertices':vertex_agreement(a.positions,b.positions,p['vertex']),
        'candidate_counts':{'ps2_to_pc':perf1,'pc_to_ps2':perf2},'groups':groups,
        'runtime_validation':'NOT_PERFORMED','limitations':[
            'Independent directional coverage; not a one-to-one instance or group bijection',
            'Unsigned geometric equivalence retains raw winding separately',
            'Near parallel overlap is a changed-surface candidate, not proved common author identity',
            'All decoded alternatives included; no live LOD or polygon budget claim',
            'PC TXT source spans are not assumed to index compiled DX faces']},forward,reverse


def load_pair(ps2root,pcroot,sdk,course):
    if course not in COURSES: raise t.FormatError('Unsupported selected course')
    manifest,_=t.load_pak(ps2root/'TNG.PAK')
    path=('\\TNG\\DATAPSM\\COURSE\\'+course+'\\'+course+'.PSM')
    entries=[e for e in manifest['entries'] if e['path']==path and e['kind']=='file']
    if len(entries)!=1: raise t.FormatError('Missing/ambiguous canonical landscape')
    payload,prov=t.read_payload(entries[0],ps2root/'TNG.000')
    a=ps2_adapter(payload,path);a.source['packfs']=prov
    b=pc_adapter(pcroot,sdk,course)
    align=alignment(ps2root,pcroot,sdk,course,manifest)
    return a,b,align


def local_output(path):
    p=path.resolve()
    if not p.is_relative_to((ROOT/'data'/'geom1').resolve()):
        raise t.FormatError('Full diagnostics must remain under ignored data/geom1')
    if p.exists() and p.stat().st_nlink>1:
        raise t.FormatError('Refusing multiply linked output')
    return p


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--course',choices=COURSES,required=True)
    ap.add_argument('--ps2-root',type=Path,required=True)
    ap.add_argument('--pc-root',type=Path,required=True)
    ap.add_argument('--sdk',type=Path,required=True)
    ap.add_argument('--profile',choices=tuple(PROFILES),default='baseline')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--svg',type=Path)
    args=ap.parse_args();out=local_output(args.output)
    w.verify_inputs(args.ps2_root)
    start=time.perf_counter();a,b,align=load_pair(args.ps2_root,args.pc_root,args.sdk,args.course)
    report,forward,reverse=compare(a,b,args.profile)
    report.update(course_pair=args.course,alignment=align)
    t.write_json(out,report)
    if args.svg:
        from geometry_delta_visualize import write_svg
        write_svg(local_output(args.svg),a,b,forward,reverse,args.course)
    print(json.dumps({'course':args.course,'seconds':time.perf_counter()-start,
        'ps2':report['ps2_relations'],'pc':report['pc_relations'],'output':str(out)}))


if __name__=='__main__': main()
