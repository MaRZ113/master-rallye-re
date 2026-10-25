"""Qualified MR blight serialization over shared scene parts.

Stock tag7 switch -> two tag8 cases -> counted material children. Source lens
geometry is caller supplied; no donor hub, lamp coordinates or vehicle names.
The general DX parser's flattened physical parentage is not a logical case
decoder, so the native byte envelopes are validated independently here.
"""
import struct
from master_rallye.dx import parse_dx_bytes
from master_rallye.scene_dx_writer import write_scene_dx,validate_scene_dx


def stock_evidence(template):
    m=parse_dx_bytes(template);roots=[d for d in m.physical_draws if d.group_label=='blight']
    if len(roots)!=1:raise ValueError('requires a qualified stock blight reference')
    root=roots[0];i=root.draw_index
    if root.control_words!=(2,2,8,1,1) or m.physical_draws[i+1].control_words!=(2,2):raise ValueError('unknown stock blight grammar')
    lit,glow=m.physical_draws[i+1:i+3]
    if lit.tag!=8 or glow.tag!=2 or tuple(lit.flags_0x20)!=(0,0,0,1) or tuple(glow.flags_0x20)!=(1,0,0,1):raise ValueError('unknown native lamp families')
    return {'controller':'gaSFXBrakeLights / blight: case2 above brake0.1, case1 otherwise',
            'stock_cases':[1,2],'stock_material_counts':[1,2],'depth_and_blend':'original native shader/instance semantics; no controller or DLL patch'}


def write_brake_scene(template,body,unlit,lit,glow):
    stock_evidence(template)
    if not 1<=len(unlit)<=16 or not 1<=len(lit)<=16 or len(glow)!=1:raise ValueError('unqualified brake state material count')
    if any(p.diffuse for p in lit+glow):raise ValueError('native lit/glow must bypass damaged diffuse RGB, as stock')
    if any(p.environment for p in lit+glow) or not glow[0].alpha or glow[0].alpha_test:raise ValueError('unqualified native light/glow state')
    parts=body+unlit+lit+glow;flat=write_scene_dx(template,parts,allow_unlit=True);m=parse_dx_bytes(flat)
    records=[];first=len(body);second=first+len(unlit)
    for i,d in enumerate(m.physical_draws):
        core=flat[d.core_offset:d.offset+d.own_size]
        if i==first:
            label=b'blight';core=struct.pack('<II',7,len(label))+label+struct.pack('<5I',2,2,8,1,len(unlit))+core
        elif i==second:core=struct.pack('<3I',8,2,len(lit)+1)+core
        records.append(core)
    result=flat[:m.draw_table_offset]+struct.pack('<2I',1,len(body)+1)+b''.join(records)+flat[m.global_index_table.preamble_offset:]
    validate_brake_scene(template,result)
    return result


def validate_brake_scene(template,data):
    stock_evidence(template);m=parse_dx_bytes(data);roots=[d for d in m.physical_draws if d.group_label=='blight']
    if not m.diagnostics.validated or len(roots)!=1:raise ValueError('invalid native brake scene')
    root=roots[0];i=root.draw_index
    if root.control_words[:4]!=(2,2,8,1):raise ValueError('unqualified blight case1 envelope')
    off=root.control_words[4];on_index=i+off
    if not 1<=off<=16 or on_index>=len(m.physical_draws):raise ValueError('invalid unlit state extent')
    on=m.physical_draws[on_index]
    if on.tag!=8 or len(on.control_words)!=2 or on.control_words[0]!=2:raise ValueError('unqualified blight case2 envelope')
    count=on.control_words[1]
    if not 2<=count<=17 or on_index+count!=len(m.physical_draws):raise ValueError('invalid lit state extent')
    if m.declared_top_level_record_count!=i+1:raise ValueError('native top-level count must count the switch once')
    records=[]
    for n,d in enumerate(m.physical_draws):
        if d.tag!=(7 if n==i else 8 if n==on_index else 2):raise ValueError('unexpected native scene control')
        if n<on_index and not d.flags_0x20[2]:raise ValueError('unlit/body lost native damage diffuse ownership')
        if n>=on_index and (d.flags_0x20[2] or d.unknown_0x24!=1):raise ValueError('lit/glow material must use stock unlit family')
        records.append(data[d.core_offset:d.offset+d.own_size])
    flat=data[:m.draw_table_offset]+struct.pack('<2I',1,len(records))+b''.join(records)+data[m.global_index_table.preamble_offset:]
    result=validate_scene_dx(template,flat,allow_unlit=True)
    return {**result,'grammar':'qualified native blight two-case scene','case1_draws':list(range(i,on_index)),
            'case2_draws':list(range(on_index,on_index+count)),'glow_draw':on_index+count-1,
            'native_controller_preserved':True,'runtime_qualified':False}
