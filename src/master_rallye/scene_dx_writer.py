"""Write an explicit variable draw list using the qualified MR render grammar.

Material records are independent of donor draw IDs. Existing native collision
and suffix are copied from a caller-selected baseline and bounds recomputed.
No asset routing, physics or runtime installation is performed here.
"""
from __future__ import annotations
from dataclasses import dataclass
import math,struct
from .dx import parse_dx_bytes
from .bounds import compute_bounds1339,replace_bounds1339,parse_bounds1339
from .topology_writer import DrawGeometry

@dataclass(frozen=True)
class ScenePart:
    geometry:DrawGeometry
    textures:tuple[str,str,str]
    alpha:bool=False
    alpha_test:bool=False
    environment:bool=False
    diffuse:bool=True

def write_scene_dx(template:bytes,parts:list[ScenePart],*,allow_unlit=False):
    donor=parse_dx_bytes(template)
    if not donor.diagnostics.validated or (donor.word_0x04,donor.word_0x08)!=(135,1337):raise ValueError('unqualified DX template')
    if not 0<len(parts)<=8192:raise ValueError('draw list budget')
    if parse_bounds1339(donor.collision.unparsed_data,donor.collision.unparsed_offset) is None:raise ValueError('requires qualified marker1339 suffix')
    prototype=next(d for d in donor.physical_draws if d.tag==2 and len(d.texture_slots)==3)
    vertices=[];locals_=[];globals_=[];records=[]
    for part in parts:
        if not part.diffuse and not allow_unlit:raise ValueError('unlit scene parts require qualified native-state packaging')
        g=part.geometry
        if not 0<len(g.vertices)<=65536 or not g.triangles:raise ValueError('empty or oversized draw geometry')
        base,start=len(vertices),len(locals_);used=set()
        for v in g.vertices:
            if len(v.color)!=4 or len(v.uvs)!=1 or not all(math.isfinite(n) for n in (*v.position,*v.normal,*v.uvs[0])):raise ValueError('invalid compiled scene vertex')
        for tri in g.triangles:
            if len(tri)!=3 or any(type(k)is not int or not 0<=k<len(g.vertices) for k in tri):raise ValueError('scene triangle out of bounds')
            used.update(tri);a,b,c=tri;locals_.extend((b,a,c));globals_.extend(base+k for k in tri)
        if used!=set(range(len(g.vertices))):raise ValueError('scene draw has unused vertices')
        vertices.extend(g.vertices)
        record=bytearray(struct.pack('<7If4BI',2,base,len(g.vertices)-1,start,len(g.triangles)*3,
            prototype.unknown_0x14,prototype.unknown_0x18,prototype.unknown_0x1c_float,
            int(part.alpha),int(part.alpha_test),int(part.diffuse),1,(3 if part.diffuse else 1)|(4 if part.environment else 0)))
        record.extend(struct.pack('<I',3))
        for value in part.textures:
            raw=value.encode('ascii')
            if not 0<len(raw)<=255 or '/' in value or '\\' in value:raise ValueError('invalid local texture binding')
            record.extend(struct.pack('<I',len(raw))+raw)
        record.extend(struct.pack('<I',0));records.append(record)
    if len(vertices)>1000000 or len(locals_)>6000000:raise ValueError('scene resource budget')
    data=bytearray(template[:12]+struct.pack('<I',len(vertices)))
    for v in vertices:data.extend(struct.pack('<3f',*v.position))
    for v in vertices:data.extend(struct.pack('<3f',*v.normal))
    data.extend(b''.join(v.color for v in vertices)+struct.pack('<I',1))
    for v in vertices:data.extend(struct.pack('<2f',*v.uvs[0]))
    data.extend(struct.pack('<I',len(locals_))+struct.pack(f'<{len(locals_)}H',*locals_))
    data.extend(struct.pack('<II',1,len(parts))+b''.join(records))
    data.extend(struct.pack('<II',1,len(globals_))+struct.pack(f'<{len(globals_)}I',*globals_)+template[donor.trailing.offset:])
    model=parse_dx_bytes(bytes(data));bounds=compute_bounds1339(model.vertices.positions,model.collision.convex_hull,offset=model.collision.unparsed_offset)
    result=replace_bounds1339(bytes(data),bounds,footer_offset=model.collision.unparsed_offset);after=parse_dx_bytes(result)
    if not after.diagnostics.validated or after.declared_top_level_record_count!=len(parts) or len(after.physical_draws)!=len(parts):raise ValueError('scene DX post-write validation failed')
    before_collision=template[donor.trailing.offset:donor.collision.unparsed_offset]
    after_collision=result[after.trailing.offset:after.collision.unparsed_offset]
    if before_collision!=after_collision:raise ValueError('baseline collision bytes changed')
    validate_scene_dx(template,result,allow_unlit=allow_unlit)
    return result


def validate_scene_dx(template:bytes,candidate:bytes,*,allow_unlit=False):
    """Admit explicit imported scenes without weakening same-draw authoring.

    Only this writer's tag2/three-slot grammar is admitted. Collision and all
    unqualified material words must still come from the pinned donor. Bounds
    are the only permitted suffix change. Texture dependencies are checked by
    the enclosing VehicleProject against its user-owned source asset family.
    """
    old=parse_dx_bytes(template);new=parse_dx_bytes(candidate)
    if not old.diagnostics.validated or not new.diagnostics.validated or template[:12]!=candidate[:12]:
        raise ValueError('invalid imported-scene header/structure')
    if (old.word_0x04,old.word_0x08)!=(135,1337):raise ValueError('unsupported imported-scene grammar')
    if not 0<len(new.physical_draws)<=8192 or new.vertex_count>1000000 or len(new.local_indices)>6000000:
        raise ValueError('imported-scene budget exceeded')
    if new.declared_top_level_record_count!=len(new.physical_draws):raise ValueError('imported scene has nested controls')
    if len(new.uv_sets)!=1:raise ValueError('imported scene requires one UV channel')
    prototype=next(d for d in old.physical_draws if d.tag==2 and len(d.texture_slots)==3)
    vertex_cursor=index_cursor=0
    for d in new.physical_draws:
        if (d.tag,d.group_label,d.control_words)!=(2,None,()):raise ValueError('unsupported imported-scene draw control')
        if (d.unknown_0x14,d.unknown_0x18,d.unknown_0x1c_float)!=(prototype.unknown_0x14,prototype.unknown_0x18,prototype.unknown_0x1c_float):
            raise ValueError('unqualified imported-scene material words')
        admitted=((0,0,1,1),(1,0,1,1),(1,1,1,1))+(((0,0,0,1),(1,0,0,1),(1,1,0,1)) if allow_unlit else ())
        if tuple(d.flags_0x20) not in admitted or d.unknown_0x24 not in ((1,3,5,7) if allow_unlit else (3,7)):
            raise ValueError('unqualified imported-scene material flags')
        if len(d.texture_slots)!=3 or d.texture_tuple[2]!='Null' or not d.unknown_0x24&4 and d.texture_tuple[1]!='Null':
            raise ValueError('unsupported imported-scene texture layers')
        for name in d.texture_tuple:
            if not name.isascii() or not 0<len(name)<=255 or not name.isprintable() or any(c in name for c in '/\\:'):
                raise ValueError('imported-scene texture must be a local basename')
        if candidate[d.offset+d.own_size-4:d.offset+d.own_size]!=bytes(4):raise ValueError('unqualified imported-scene record tail')
        if d.vertex_base!=vertex_cursor or d.index_start!=index_cursor:raise ValueError('noncontiguous imported-scene draw spans')
        if set(new.local_indices[d.index_start:d.index_start+d.index_count])!=set(range(d.local_vertex_max+1)):
            raise ValueError('imported-scene draw has unused vertices')
        vertex_cursor+=d.local_vertex_max+1;index_cursor+=d.index_count
    if vertex_cursor!=new.vertex_count or index_cursor!=len(new.local_indices):raise ValueError('imported-scene unaccounted geometry')
    if template[old.trailing.offset:old.collision.unparsed_offset]!=candidate[new.trailing.offset:new.collision.unparsed_offset]:
        raise ValueError('imported scene changed donor collision')
    footer=new.collision.unparsed_offset
    bounds=parse_bounds1339(new.collision.unparsed_data,footer)
    expected=compute_bounds1339(new.vertices.positions,new.collision.convex_hull,offset=footer)
    if bounds is None or footer+44!=len(candidate):raise ValueError('unqualified imported-scene suffix')
    if max(abs(a-b) for a,b in zip((*bounds.minimum,*bounds.maximum,*bounds.center,bounds.radius),
                                  (*expected.minimum,*expected.maximum,*expected.center,expected.radius)))>1e-5:
        raise ValueError('imported-scene bounds stale')
    if any(not math.isfinite(x) for p in (*new.vertices.positions,*new.vertices.normals) for x in p):
        raise ValueError('imported-scene nonfinite geometry')
    return {'status':'PASS','source_draws':len(old.physical_draws),'output_draws':len(new.physical_draws),
            'output_vertices':new.vertex_count,'output_triangles':new.triangle_count,'collision_preserved':True,
            'grammar':'135/1337 tag2 three-slot imported scene; no runtime qualification implied'}
