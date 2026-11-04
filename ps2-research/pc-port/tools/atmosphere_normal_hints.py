"""Optional spatial authored normals, independent of material admission/mesh hashes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

def export(sources,courses,materials,output,base=None):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
    from master_rallye.dx_course import parse_course_dx
    from master_rallye.dxt import parse_dxt
    from master_rallye.course_lighting import decode_metadata,fixed
    capabilities={(r['course'],r['texture_sha256']):r for r in decode_metadata(materials.read_bytes()) if r['category'] in (1,2,4) and not r['flags']&16}
    rows=set();evidence=[]
    if base:
        data=base.read_bytes()
        if len(data)<76:raise ValueError('base normal metadata size')
        magic,version,count=struct.unpack_from('<4sII',data)
        if magic!=b'LNH1' or version!=1 or count>400000 or len(data)!=76+153*count or data[12:76]!=hashlib.sha256(data[76:]).hexdigest().encode():raise ValueError('base normal metadata integrity')
        for i in range(count):
            row=data[76+153*i:76+153*(i+1)]
            values=struct.unpack_from('<6f',row,129)
            rows.add((row[:64].split(b'\0')[0].decode('ascii'),row[64:129].split(b'\0')[0].decode('ascii'),*(round(x,3) for x in values[:3]),*(round(x,5) for x in values[3:])))
    for root in sources:
        for course in courses:
            path=root/course/(course.lower()+'.dx')
            if not path.exists():continue
            model=parse_course_dx(path)
            if not model.course_render_validated:raise ValueError('unvalidated source')
            textures={}
            for draw in model.physical_draws:
                name=draw.texture_tuple[0]
                if name not in textures:
                    texture=next((r/course/(name+'.dxt') for r in sources if (r/course/(name+'.dxt')).exists()),None)
                    if not texture:textures[name]=[];continue
                    t=parse_dxt(texture);opaque=bytearray(t.bgra);opaque[3::4]=bytes([255])*(len(opaque)//4)
                    textures[name]=[s for s in sorted({hashlib.sha256(t.bgra).hexdigest(),hashlib.sha256(opaque).hexdigest()}) if (course,s) in capabilities]
                if not textures[name]:continue
                indices=model.local_indices[draw.index_start:draw.index_start+draw.index_count]
                for index in set(indices):
                    at=draw.vertex_base+index;p=model.vertices.positions[at];n=model.vertices.normals[at]
                    length=math.sqrt(sum(x*x for x in n))
                    if not .001<length<100 or not all(math.isfinite(x) and abs(x)<1e6 for x in p):continue
                    # Deduplicate near-identical normals from PC/PS2 variants;
                    # retain distinct authored hard-edge clusters at one point.
                    p=tuple(round(x*1000)/1000 for x in p);n=tuple(round(x/length,5) for x in n)
                    for digest in textures[name]:rows.add((course,digest,*p,*n))
            evidence.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    # Material/UV boundaries must not split one authored smooth normal. Gather
    # stock variants once at export, preserving separate clusters beyond 14 deg.
    from collections import defaultdict
    clusters=defaultdict(set)
    for r in rows:clusters[(r[0],*r[2:5])].add(r[5:8])
    smoothed=set()
    for r in rows:
        n=r[5:8];near=[v for v in sorted(clusters[(r[0],*r[2:5])]) if sum(a*b for a,b in zip(n,v))>.97]
        # Complete-link criterion prevents a chain from rounding a hard edge.
        if any(sum(a*b for a,b in zip(v,w))<.97 for v in near for w in near):near=[n]
        average=[sum(v[k] for v in near) for k in range(3)];length=math.sqrt(sum(x*x for x in average))
        smoothed.add((*r[:5],*(round(x/length,5) for x in average)))
    rows=smoothed
    payload=b''.join(fixed(r[0],64)+fixed(r[1],65)+struct.pack('<6f',*r[2:]) for r in sorted(rows))
    data=struct.pack('<4sII',b'LNH1',1,len(rows))+hashlib.sha256(payload).hexdigest().encode()+payload
    if len(rows)>400000:raise ValueError('runtime hint capacity')
    output.mkdir(parents=True,exist_ok=False);(output/'normals.lnh').write_bytes(data)
    report={'format':'LNH1','records':len(rows),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'sources':evidence,
            'admission_authority':False,'geometry_hashes':False,'missing_or_ambiguous':'current geometric normal fallback','position_quantization_m':.001,'cross_material_smoothing_cosine':.97,'facing_cosine_min':.5}
    (output/'provenance.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,action='append',required=True);p.add_argument('--course',action='append',required=True)
    p.add_argument('--base',type=Path);p.add_argument('--materials',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.source,a.course,a.materials,a.output,a.base),indent=2))
