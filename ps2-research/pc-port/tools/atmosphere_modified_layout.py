"""Build a bounded Course SDK render-layout variant for resolver regression.

Positions, normals, bounds, collision/route suffix and triangle geometry stay
unchanged. Road UV0, prelight and triangle submission order change. This is an
edited render configuration, not a claim of a new playable route.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('fresh output required')
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
    from master_rallye.course_render_writer import CourseRender
    from master_rallye.dx_course import parse_course_dx_bytes
    source=args.source.read_bytes();render=CourseRender.from_bytes(source)
    if render.serialize()!=source:raise ValueError('SDK round-trip is not exact for source')
    uses=Counter()
    draws=list(render.draws())
    for draw in draws:
        uses.update({draw.vertex_base+i for i in render.indices[draw.index_start:draw.index_start+draw.index_count]})
    targets=[d for d in draws if d.texture_tuple[0]=='road-tga' and d.texture_tuple[2]=='noise-tga' and d.index_count>=6]
    if not targets:raise ValueError('no bounded original road candidate')
    changed=set();ranges=[]
    for draw in targets:
        vertices={draw.vertex_base+i for i in render.indices[draw.index_start:draw.index_start+draw.index_count]}
        exclusive={i for i in vertices if uses[i]==1}
        for i in exclusive:
            u,v=render.uv_sets[0][i];render.uv_sets[0][i]=(u+.125,v)
            for channel in range(3):render.colors[4*i+channel]=round(render.colors[4*i+channel]*.9)
        changed.update(exclusive)
        triangles=[render.indices[i:i+3] for i in range(draw.index_start,draw.index_start+draw.index_count,3)]
        render.indices[draw.index_start:draw.index_start+draw.index_count]=[i for triangle in reversed(triangles) for i in triangle]
        ranges.append({'material':draw.texture_tuple[0],'start':draw.index_start,'triangles':draw.index_count//3,'edited_vertices':len(exclusive)})
    if not changed:raise ValueError('no exclusive source vertices')
    data=render.serialize();parsed=parse_course_dx_bytes(data,'lighting-render-variant')
    assert parsed.course_render_validated
    check=CourseRender.from_bytes(data)
    assert check.positions==render.positions and check.normals==render.normals and check.suffix==render.suffix
    assert len(data)==len(source) and data!=source
    args.output.mkdir(parents=True)
    dest=args.output/'DataGx/Course/France1/france1.dx';dest.parent.mkdir(parents=True);dest.write_bytes(data)
    report={'status':'OFFLINE_SDK_VALIDATED_RUNTIME_PENDING','source':str(args.source),'source_sha256':hashlib.sha256(source).hexdigest(),
            'variant_sha256':hashlib.sha256(data).hexdigest(),'changed_vertices':len(changed),'ranges':ranges,
            'changes':['UV0 u+0.125','Road RGB prelight x0.9; alpha preserved','Triangle order reversed inside original draw ranges'],
            'preserved':['Vertex positions','Normals','Triangle multiset / physical geometry','Original draw counts and buffer ranges','Collision/BSP/route suffix bytes','Native material labels and textures'],
            'metadata_regeneration_required':False,'proxy_rebuild_required':False,
            'scope':'Render configuration variation; not a new route or collision reconstruction'}
    (args.output/'provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"{len(changed)} road vertices edited; no position/collision changes; {report['variant_sha256']}")

if __name__=='__main__':main()
