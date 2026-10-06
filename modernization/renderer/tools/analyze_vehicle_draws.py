"""Summarize D3D-boundary material families; no single frame proves a vehicle."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
import math
import ntpath
from pathlib import Path
from trace_common import read_jsonl,TARGET_SHA

# Values and coordinate-size encoding verified against pinned vendor/d3d8/d3d8types.h.
def decode_fvf(fvf):
    if not isinstance(fvf,int) or fvf not in (0x102,0x112,0x142,0x152,0x242,0x252):return {'fvf':fvf,'known_layout':False}
    normals=bool(fvf&0x10);diffuse=bool(fvf&0x40);uv=(fvf&0xf00)>>8
    return {'fvf':f'0x{fvf:03X}','known_layout':True,'position':'XYZ','normal':normals,'diffuse':diffuse,'uv_count':uv,'stride':12+12*normals+4*diffuse+8*uv,'uv_dimensions':[2]*uv}

def family(draw):
    s=draw.get('state',{});st=s.get('texture_stage_states') or [{},{}];rs=s.get('render_states',{})
    return {'layout':decode_fvf(s.get('vertex_shader')),'stage0':{k:st[0].get(k) for k in ('1','2','3','4','5','6','11','24')},
            'stage1':{k:st[1].get(k) for k in ('1','2','3','4','5','6','11','24')},
            'alpha_test':rs.get('15'),'alpha_blend':rs.get('27'),'z_write':rs.get('14'),'lighting':rs.get('137')}

def rectangle(points):
    """Mirror the documented native conservative geometry bounds; not temporal proof."""
    q={}
    for x,y,z in points:
        if not all(math.isfinite(v) for v in (x,y,z)) or not (.35<=abs(x)<=2.5 and .5<=abs(z)<=4 and -2<=y<=1.5):return None
        k=(x>0,z>0)
        if k in q:return None
        q[k]=(x,y,z)
    if len(q)!=4:return None
    a,b,c,d=[q[k] for k in ((False,False),(True,False),(False,True),(True,True))]
    width=sum(abs(p[0]) for p in points)/4;base=sum(abs(p[2]) for p in points)/4
    bilateral=max(abs(a[0]+b[0]),abs(c[0]+d[0]));axle=max(abs(a[2]-b[2]),abs(c[2]-d[2]))
    widths=max(abs(a[0]-c[0]),abs(b[0]-d[0]));center=abs(sum(p[2] for p in points)/4)
    height=max(p[1] for p in points)-min(p[1] for p in points)
    if bilateral>.15+.15*width or axle>.15+.15*base or widths>.15+.15*width or center>.2+.2*base or height>.5:return None
    return bilateral/width+axle/base+widths/width+center/base+height

def constellations(groups):
    wheels=[g for g in groups if g['wheel_draws']>=2 and g['wheel_draws']==g['draws'] and g['tracks'] and not g['ambiguous']]
    proposals=[]
    for b in groups:
        if not b['dynamic'] or b['ambiguous'] or b['body_draws']<2 or b['body_draws']!=b['draws'] or not b['body_env_draws']:continue
        w=b['world'];near=[]
        for wheel in wheels:
            delta=[wheel['world'][12+k]-w[12+k] for k in range(3)]
            local=[sum(delta[k]*w[a*4+k] for k in range(3)) for a in range(3)]
            if .35<=abs(local[0])<=2.5 and .5<=abs(local[2])<=4 and -2<=local[1]<=1.5:near.append((wheel,local))
        matches=[]
        if len(near)<=8:
            for quad in combinations(near,4):
                error=rectangle([p for _,p in quad])
                if error is not None:matches.append((quad,error))
        proposal={'chassis_tracks':b['tracks'],'body_draws':b['draws'],'body_triangles':b['triangles'],
                  'near_wheel_candidates':len(near),'valid_rectangles':len(matches),'accepted':len(matches)==1,
                  'reason':'unique_four_wheel' if len(matches)==1 else 'ambiguous_or_capacity' if len(matches)>1 or len(near)>8 else 'no_four_wheel_rectangle',
                  'wheel_tracks':[],'local_wheels':[],'symmetry_error':None}
        if len(matches)==1:
            quad,error=matches[0];proposal.update(wheel_tracks=[g['tracks'][0] for g,_ in quad],local_wheels=[p for _,p in quad],
                                                 symmetry_error=error,wheel_triangles=[g['triangles'] for g,_ in quad],
                                                 wheels_independently_dynamic=[g['dynamic'] for g,_ in quad])
        proposals.append(proposal)
    uses=Counter(t for p in proposals if p['accepted'] for t in p['wheel_tracks'])
    for p in proposals:
        if p['accepted'] and any(uses[t]!=1 for t in p['wheel_tracks']):p.update(accepted=False,reason='shared_wheel_conflict')
    return proposals

def reflection_audit(records,known):
    errors=[];modified=0
    for i,d in enumerate(records):
        if d.get('type')!='draw' or not d.get('native_override_applied',False):continue
        modified+=1;state=d.get('state',{});rs=state.get('render_states',{});stage=state.get('texture_stage_states',[{},{}])[1]
        if not known:errors.append('modified draw without exact complete canonical capture')
        if d.get('method')!='DrawIndexedPrimitive' or d.get('object_class_at_draw')!='VEHICLE_BODY' or state.get('vertex_shader')!=0x152 or not d.get('constellation_id_at_draw'):errors.append('unqualified draw/object/layout')
        if rs.get('27')!=0 or rs.get('14')!=1 or stage.get('1')!=18 or stage.get('2')!=1 or stage.get('3')!=2 or stage.get('4')!=4 or stage.get('5')!=1 or stage.get('6')!=2 or stage.get('24')!=2:errors.append('unqualified material combine')
        reasons={'dynamic_chassis','body_draw_cluster','wheel_signature','four_wheel_match','bilateral_symmetry','axle_pairing','unambiguous_assignment'}
        wheels=d.get('associated_wheel_track_ids',[])
        if d.get('classifier_confidence')!='STRONG_FOUR_WHEEL' or not reasons.issubset(d.get('classifier_reasons',[])) or len(wheels)!=4 or len(set(wheels))!=4 or not all(wheels):errors.append('missing strong four-wheel evidence')
        requested=d.get('requested_stage1_tci');effective=d.get('effective_stage1_tci_for_draw')
        if not isinstance(requested,int) or not isinstance(effective,int) or requested&0xffff0000!=0x10000 or effective!=(requested&0xffff)|0x30000:errors.append('TCI or low-index mismatch')
        if not d.get('native_restore_success'):errors.append('native restore failed or unavailable')
        prev=records[i-1] if i else {};nxt=records[i+1] if i+1<len(records) else {}
        for event,value in ((prev,effective),(nxt,requested)):
            if event.get('type')!='native_override' or event.get('method')!='SetTextureStageState' or event.get('arguments',[])[:3]!=[1,11,value] or not isinstance(event.get('result'),int) or event['result']&0x80000000:errors.append('missing successful draw-local setter/restore')
    return {'modified_draws':modified,'errors':errors,'status':'FAIL' if errors else 'AUTOMATED_TRACE_PASS' if modified else 'NO_MODIFICATIONS'}

def analyze(records):
    header=records[0] if records else {};end=records[-1] if records else {}
    complete=header.get('type')=='frame_begin' and end.get('type')=='frame_end' and end.get('complete') is True and end.get('truncated') is False
    known=header.get('exe_sha256')==TARGET_SHA and complete
    families={};groups=defaultdict(lambda:{'draws':0,'triangles':0,'tracks':set(),'dynamic':False,'ambiguous':False,'body_draws':0,'body_env_draws':0,'wheel_draws':0,'world':[]});classifications=Counter();reflections=0
    for d in records:
        if d.get('type')!='draw':continue
        classifications[d.get('object_classification','UNAVAILABLE_LEGACY')]+=1
        reflections+=d.get('native_override_applied',d.get('reflection_feature','Stock')!='Stock')
        caller=d.get('caller',{})
        if not known or d.get('result')!=0 or d.get('method')!='DrawIndexedPrimitive' or caller.get('return_rva')!=0x17707e or ntpath.normcase(caller.get('module') or '')!=ntpath.normcase(header.get('exe_path') or ''):continue
        f=family(d);key=json.dumps(f,sort_keys=True);item=families.setdefault(key,dict(f,draws=0,triangles=0,texture_generations=set()))
        item['draws']+=1;item['triangles']+=d['primitive_count'] if d.get('primitive_type') in (4,5,6) else 0
        item['texture_generations'].add(tuple(t.get('last_creation_serial',0) for t in d['state'].get('textures',[])[:2]))
        world=d['state'].get('matrices',{}).get('256')
        if world:
            key=tuple(world.get('bits') or world.get('values',[]));g=groups[key];g['draws']+=1;g['triangles']+=d['primitive_count'] if d.get('primitive_type') in (4,5,6) else 0;g['tracks'].add(d.get('transform_track_id',0));g['dynamic']|=d.get('transform_dynamic',False)
            g['ambiguous']|=d.get('transform_ambiguous',False);g['world']=world.get('values',[])
            fvf=d['state'].get('vertex_shader');env=f['stage1']=={'1':18,'2':1,'3':2,'4':4,'5':1,'6':2,'11':f['stage1']['11'],'24':2} and isinstance(f['stage1']['11'],int) and f['stage1']['11']&0xffff0000==0x10000
            opaque=f['alpha_blend']==0 and f['z_write']==1
            g['body_draws']+=fvf in (0x142,0x152,0x242,0x252)
            g['body_env_draws']+=fvf==0x152 and env and opaque
            g['wheel_draws']+=fvf==0x112 and env and opaque
    for v in families.values():v['texture_generations']=sorted(v['texture_generations'])
    for v in groups.values():v['tracks']=sorted(t for t in v['tracks'] if t)
    return {'exact_build_and_complete':known,'header':{k:header.get(k) for k in ('exe_sha256','proxy_sha256','device','frame')},'families':list(families.values()),'transform_groups':list(groups.values()),'constellation_analysis':constellations([g for g in groups.values() if len(g['world'])==16]) if known else [],'classification_counts':dict(classifications),'reflection_modified_draws':reflections,'reflection_validation':reflection_audit(records,known),'vehicle_semantics':'UNPROVEN_UNLESS_SEPARATELY_CORRELATED','legacy_temporal_status':'UNAVAILABLE' if not any('transform_dynamic' in d for d in records) else 'RECORDED_RUNTIME_TRACKER'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('captures',type=Path,nargs='+');a=ap.parse_args()
    results=[]
    for p in a.captures:
        result=analyze(read_jsonl(p));result['file']=p.name;result['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();results.append(result)
    # No identities are joined across sessions or independently sampled F10 frames.
    print(json.dumps({'captures':results,'cross_capture_temporal_inference':False},indent=2,allow_nan=False))
if __name__=='__main__':main()
