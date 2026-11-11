"""Use original PS2 FORESTER ON geometry with PC art and model-gated PS2 art.

Operate only on an explicitly selected private candidate. Uses the accepted PS2
decoder/strip conversion and Vehicle SDK state writer, preserving body/collision.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
from vehicle_lamp_authoring import parts_with_states, draw_identity
from ps2_fleet_new_families import PORT, DOCS, load


def author(raw):
    from master_rallye.topology_writer import CompiledVertex, DrawGeometry
    from master_rallye.scene_dx_writer import ScenePart
    from master_rallye.addon_sdk.native_states import wrap_states
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    from verify_vehicle_lamps import triangles
    rt=load('forester_source_converter', DOCS/'convert_runtime.py')
    blob=(PORT/'.assets/vehicles/FORESTER-CAR-SOURCE.ps2vehicle').read_bytes()
    rt.source.validate(blob)
    _,_,size,count,_,_=rt.source.HEADER.unpack_from(blob)
    meta=json.loads(blob[rt.source.HEADER.size:rt.source.HEADER.size+size])
    source=blob[rt.source.HEADER.size+size:][:count*52]
    lamps=[];evidence=[]
    for name in ('breaklightson-tga','breaklightsonglow-tga'):
        mesh=next(m for m in meta['meshes'] if any(t['slot']==0 and t['name'].lower().endswith('\\'+name) for t in m['textures']))
        ids,diag=rt.c.indices_for_mesh(source,mesh)
        used=sorted(set(ids));local={v:i for i,v in enumerate(used)}
        vertices=[]
        for i in used:
            pos=struct.unpack_from('<3f',source,i*52+36)
            normal=struct.unpack_from('<3f',source,i*52)
            uv=struct.unpack_from('<2f',source,i*52+20)
            # Runtime uses 1-v for PS2 source coordinates. FEED PNG orientation
            # remains handled by the existing codec, not an extra atlas flip.
            color=rt.c.vertex(source,i)[24:28]
            vertices.append(CompiledVertex(pos,normal,color,((uv[0],1-uv[1]),)))
        # SDK display winding -> native writer swaps the first two corners.
        ts=tuple((local[ids[k+1]],local[ids[k]],local[ids[k+2]])for k in range(0,len(ids),3))
        lamps.append(ScenePart(DrawGeometry(tuple(vertices),ts),(name,'Null','Null'),alpha=len(lamps)==1,diffuse=False))
        evidence.append({'source_path':mesh['path'],'vertices':len(used),'triangles':len(ts),'strip_diagnostics':diag})
    output=wrap_states(raw,parts_with_states(raw,lamps))
    assert triangles(raw)==triangles(output), 'body/off states changed'
    old,new=parse_dx_bytes(raw),parse_dx_bytes(output)
    assert raw[old.collision.offset:old.collision.unparsed_offset]==output[new.collision.offset:new.collision.unparsed_offset]
    cases,_=logical_cases(new);rows=[]
    for d in new.physical_draws:
        if cases.get(d.draw_index)==(1,2) and d.texture_tuple[0] in ('breaklightson-tga','breaklightsonglow-tga'):
            geom,uv=draw_identity(new,d)
            rows.append(f'ForesterSTI {int(bool(d.flags_0x20[0]))} {d.local_vertex_max+1} {d.triangle_count} {geom} {uv} PS2_MODEL_ONLY')
    assert len(rows)==2
    return output,rows,evidence


def apply(host):
    from vehicle_presentation_fix import sha
    changes=[]
    for root in (host/'MRMods/Vehicles/active',host/'MRMods/Vehicles/manager/base'):
        p=root/'resources/DataGx/Vehicles/ForesterSTI/car.dx'
        if not p.exists():continue
        original=p.read_bytes();updated,rows,evidence=author(original);p.write_bytes(updated)
        registry=root/'addon-brake-lamps.tsv'
        lines=registry.read_text().splitlines()
        version=lines[0];assert version in ('MR-ADDON-LAMPS 1','MR-ADDON-LAMPS 2')
        keep=[l+(' ANY_MODEL' if version.endswith(' 1') else '')for l in lines[1:] if l.strip() and not l.startswith('ForesterSTI ')]
        registry.write_text('MR-ADDON-LAMPS 2\n'+'\n'.join(keep+rows)+'\n')
        cat=root/'catalog.json'
        if cat.exists():
            c=json.loads(cat.read_text());c['resources']=[{'path':f.relative_to(root/'resources').as_posix(),'size':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted((root/'resources').rglob('*'))if f.is_file()]
            cat.write_text(json.dumps(c,indent=1)+'\n')
        changes.append({'root':str(root),'before':sha(original),'after':sha(updated),'layers':evidence})
    return changes


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sdk',type=Path,required=True)
    a=ap.parse_args();sys.path.insert(0,str(a.sdk.resolve()/'src'))
    result=apply(a.candidate.resolve());print(json.dumps(result,indent=2));(a.candidate/'forester-lamp-authoring.json').write_text(json.dumps(result,indent=2)+'\n')
