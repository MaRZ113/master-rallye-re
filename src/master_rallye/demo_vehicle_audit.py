"""Read-only decoded surface comparison, independent of file and vertex order.

Surface equality does not establish original asset authorship or game behavior.
Legacy stored-global tables and opaque GXM semantics retain separate boundaries.
"""
from collections import Counter
import hashlib
import math
from pathlib import Path
import struct

from .addon_sdk import heritage_source as heritage
from .demo_dx import inspect_demo_dx
from .dx import parse_dx_bytes
from .gxm import parse_gxm_prefix_bytes, parse_gxm_geometry_prefix_bytes, parse_gxm_triangle_prefix_bytes


def sha(raw): return hashlib.sha256(raw).hexdigest()


def number(v):
    if not math.isfinite(v) or abs(v)>1e6: raise ValueError('nonfinite or excessive geometry coordinate')
    return 0.0 if v==0 else v


def digest_rows(rows):
    h=hashlib.sha256()
    for row in sorted(rows): h.update(struct.pack('<I',len(row)));h.update(row)
    return h.hexdigest()


def cycle(corners):
    return min(b''.join(corners[i:]+corners[:i])for i in range(3))


def surfaces(positions, normals, colors, uv_sets, triangles, materials=None):
    """Exact float32 corner fingerprints plus explicitly approximate shape keys."""
    if len(positions)>100000 or len(triangles)>200000:raise ValueError('Audit geometry allocation budget exceeded')
    if normals and len(normals)!=len(positions):raise ValueError('Normal buffer length mismatch')
    if any(len(layer)!=len(positions)for layer in uv_sets):raise ValueError('UV buffer length mismatch')
    if normals and len(colors)!=len(positions)*4:raise ValueError('Color buffer length mismatch')
    if materials is not None and len(materials)!=len(triangles):raise ValueError('Material ownership length mismatch')
    points=[struct.pack('<3f',*(number(v)for v in p))for p in positions]
    norms=[struct.pack('<3f',*(number(v)for v in p))for p in normals]if normals else []
    uvs=[b''.join(struct.pack('<2f',*(number(v)for v in uv[i]))for uv in uv_sets)for i in range(len(points))]
    geometry=[];unoriented=[];attributes=[];normal_rows=[];material_rows=[];tokens=[]
    for n,tri in enumerate(triangles):
        if len(tri)!=3 or any(type(i)is not int or not 0<=i<len(points)for i in tri):raise ValueError('triangle index outside vertex buffer')
        ps=[points[i]for i in tri];geometry.append(cycle(ps));unoriented.append(b''.join(sorted(ps)))
        attributes.append(cycle([points[i]+uvs[i]for i in tri]))
        if norms:normal_rows.append(cycle([points[i]+norms[i]+colors[i*4:i*4+4]for i in tri]))
        if materials is not None:material_rows.append(cycle(ps)+materials[n])
        q=sorted(tuple(round(number(v)/1e-5)for v in positions[i])for i in tri)
        tokens.append(struct.pack('<9q',*(v for p in q for v in p)))
    bounds=[[min(p[k]for p in positions)for k in range(3)],[max(p[k]for p in positions)for k in range(3)]]if positions else None
    return {'vertices':len(points),'triangles':len(triangles),'bounds':bounds,
            'position_cloud_sha256':digest_rows(set(points)),
            'surface_sha256':digest_rows(geometry),'unoriented_surface_sha256':digest_rows(unoriented),
            'uv_surface_sha256':digest_rows(attributes)if uv_sets else None,
            'normal_color_surface_sha256':digest_rows(normal_rows)if norms else None,
            'material_surface_sha256':digest_rows(material_rows)if materials is not None else None,
            'approximate_surface_sha256':digest_rows(tokens),'quantization':1e-5,
            '_tokens':Counter(tokens),'_positions':positions,'_triangles':triangles}


def dx_evidence(raw, name):
    rev=struct.unpack_from('<I',raw,4)[0]
    if rev in (131,135):
        if rev==135:
            converted=raw;conversion={'status':'READ_ONLY_REV135_RENDER_CORE','boundary':'No writer/export permission inferred from parsed draw surfaces'}
        else:converted,conversion=heritage.compatible_model(raw,name)
        m=parse_dx_bytes(converted)
        triangles=[];materials=[]
        for draw in m.physical_draws:
            if (draw.index_start<0 or draw.index_count<0 or draw.index_count%3 or
                    draw.index_start+draw.index_count>len(m.local_indices)or draw.vertex_base<0 or
                    draw.vertex_base+draw.local_vertex_max>=m.vertex_count):raise ValueError('unsafe render draw range')
            indices=m.draw_global_indices(draw)
            state=repr((draw.tag,draw.group_label,draw.control_words,draw.flags_0x20,draw.unknown_0x24,
                        tuple(s.casefold()for s in draw.texture_tuple))).encode()
            for i in range(0,len(indices),3):triangles.append(tuple(indices[i:i+3]));materials.append(state)
        result=surfaces(m.vertices.positions,m.vertices.normals,m.vertices.colors,[u.values for u in m.uv_sets],triangles,materials)
        result.update(status='PASS_DRAW_SURFACES',revision=rev,conversion=conversion,
                      texture_references=sorted({s for d in m.physical_draws for s in d.texture_tuple if s.casefold()!='null'}),
                      parser_errors=m.diagnostics.errors,parser_warnings=m.diagnostics.warnings,
                      collision_errors=m.collision.errors,collision_warnings=m.collision.warnings,
                      global_table_agrees=m.global_index_table.reconstructed_match if m.global_index_table else None,
                      collision_tags=m.collision.tag_ids,collision_sha256=sha(converted[m.global_index_table.data_offset+m.global_index_table.count*4:])if m.global_index_table else None,
                      native_draws=[{'index':d.draw_index,'tag':d.tag,'group':d.group_label,'control_words':list(d.control_words),
                                     'flags':list(d.flags_0x20),'state_0x24':d.unknown_0x24,'textures':list(d.texture_tuple),
                                     'triangles':d.triangle_count}for d in m.physical_draws],
                      draw_state_sha256=sha(repr([(d.tag,d.group_label,d.flags_0x20,d.unknown_0x24,d.control_words,d.texture_tuple)for d in m.physical_draws]).encode()))
        return result
    # Existing conservative parser, no new legacy draw grammar or conversion.
    m=inspect_demo_dx(raw,name)
    triangles=[tuple(m.global_indices[i:i+3])for i in range(0,len(m.global_indices),3)]
    uv_sets=[list(struct.iter_unpack('<2f',uv))for uv in m.uv_sets]
    result=surfaces(m.positions,m.normals,m.colors,uv_sets,triangles)
    result.update(status='WARN_LEGACY_STORED_GLOBAL_ONLY',revision=rev,draw_state_sha256=None,
                  boundary='Legacy draw grammar not decoded; stored global surface is diagnostic, not renderer-equivalence proof.',
                  collision_tags=m.collision.tag_ids)
    return result


def gxm_evidence(raw,name):
    p=parse_gxm_prefix_bytes(raw,name)
    if p.header_words[6]>200000 or p.header_words[7]>100000:raise ValueError('Audit GXM geometry allocation budget exceeded')
    g=parse_gxm_geometry_prefix_bytes(raw,p);t=parse_gxm_triangle_prefix_bytes(raw,p,g)
    positions=list(struct.iter_unpack('<3f',raw[t.vector_c_offset:t.vector_c_offset+t.vector_c_count*12]))
    triangles=[];materials=[];descriptors=[]
    for i in range(t.record_count):
        row=struct.unpack_from('<10I',raw,t.record_offset+i*52)
        triangles.append(tuple(row[4:7]))
        material=p.materials[row[0]]if row[0]!=0xffffffff else None
        materials.append(repr((material.name,[(s.flags3.hex(),s.reference.replace('\\','/').split('/')[-1].casefold())for s in material.slots])if material else None).encode())
        descriptors.append(struct.pack('<6I',*row[1:4],*row[7:10]))
    result=surfaces(positions,[],b'',[],triangles,materials)
    result.update(status='WARN_GXM_PREFIX_RECORDS',boundary='Source C position and triangle arrays decoded using existing GXM/auto_features readers; hierarchy, render visibility and UV meaning are not newly qualified.',
                  source_materials=[{'name':m.name,'textures':[{'flags':s.flags3.hex(),'reference':s.reference}for s in m.slots]}for m in p.materials],
                  raw_index_descriptor_sha256=digest_rows(descriptors),hierarchy_tail_sha256=sha(raw[t.hierarchy_offset:]))
    return result


def public(model): return {k:v for k,v in model.items()if not k.startswith('_')}


def comparison(a,b):
    if a['surface_sha256']==b['surface_sha256']:
        equal=['surface']
        for field in ('uv_surface_sha256','normal_color_surface_sha256','material_surface_sha256','draw_state_sha256'):
            if a.get(field)is not None and a.get(field)==b.get(field):equal.append(field)
        return {'kind':'EXACT_DECODED_SURFACE','equal':equal,'overlap':1.0,
                'boundary':'Identical rendered positional triangle multiset with winding, not proof of shared historical asset origin.'}
    if a['unoriented_surface_sha256']==b['unoriented_surface_sha256']:
        return {'kind':'SAME_SURFACE_WINDING_DIFFERS','overlap':1.0}
    count=sum((a['_tokens']&b['_tokens']).values())
    total=max(a['triangles'],b['triangles'],1)
    try:
        import numpy as np
        for m in (a,b):
            if '_cloud'in m:continue
            unique=sorted(set(m['_positions']));step=max(1,len(unique)//2048)
            m['_cloud']=np.asarray(unique[::step][:2048],dtype=np.float64)
            m['_sample']=m['_cloud'][::max(1,len(m['_cloud'])//64)][:64]
        def nearest(left,right):
            return np.square(left[:,None,:]-right[None,:,:]).sum(axis=2).min(axis=1)
        squared=np.concatenate((nearest(a['_sample'],b['_cloud']),nearest(b['_sample'],a['_cloud'])))
        distance={'sampled_unscaled_rms':round(float(np.sqrt(squared.mean())),6),
                  'sampled_unscaled_max':round(float(np.sqrt(squared.max())),6),
                  'distance_boundary':'Nearest sampled vertices in unchanged coordinate frame; max64 samples/2048 target vertices each way, no scaling or translation.'}
    except ImportError:distance={'distance_boundary':'NumPy missing; no nearest-position estimate'}
    return {'kind':'PARTIAL_POSITIONAL_OVERLAP'if count else'DIFFERENT_DECODED_SURFACE','overlap':round(count/total,6),**distance,
            'shared_quantized_triangles':count,'quantization':1e-5,
            'boundary':'Approximate positional triangle overlap only; not a compatibility or provenance score.'}


def signed_axis_alignment(source,target):
    """Measured position-only axis match; never a source renderer transform."""
    import itertools
    points=source['_positions'];triangles=source['_triangles']
    if not triangles:return None
    sample=triangles[::max(1,len(triangles)//48)][:48];votes=[]
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((-1,1),repeat=3):
            hits=0
            for t in sample:
                q=sorted(tuple(round(points[i][perm[k]]*signs[k]/1e-5)for k in range(3))for i in t)
                token=struct.pack('<9q',*(v for p in q for v in p))
                hits+=token in target['_tokens']
            votes.append((hits,perm,signs))
    votes.sort(reverse=True)
    best=votes[0]
    if best[0]<max(3,len(sample)*.7)or best[0]==votes[1][0]:return None
    return {'permutation':list(best[1]),'signs':list(best[2]),'sample_hits':best[0],'sample_size':len(sample),
            'boundary':'Unique signed-axis match of sampled positions; hierarchy/UV/materials not inferred.'}


def transform_surface(source,alignment):
    p=alignment['permutation'];s=alignment['signs']
    points=[tuple(row[p[k]]*s[k]for k in range(3))for row in source['_positions']]
    return surfaces(points,[],b'',[],source['_triangles'])
