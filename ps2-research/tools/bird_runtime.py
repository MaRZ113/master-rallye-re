"""AMBIENT2 read-only BirdManager inventory and explicit-state flight diagnostics.

PackFS/XML/PSB/GXI primitives are reused. No game asset writer or bird port.
One step means one owner invocation; the actual scheduler cadence is not captured.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import spline_runtime as s
import psbtool as p
import tngtool as t

ROOT = s.ROOT
SCHEMA = 'ps2-bird-contract-v1'
f32, add, sub, mul, div = s.f32, s.add, s.sub, s.mul, s.div
Error = s.ContractError


def local_output(path):
    path = Path(path).resolve()
    if not path.is_relative_to((ROOT/'data/ambient2').resolve()) or path == ROOT/'data/ambient2':
        raise Error('Original-data diagnostics must stay under ignored data/ambient2')
    if path.exists():raise Error('Existing diagnostic output preserved; select a new filename')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def parse_authored(data, source):
    if not 0 < len(data) <= 16*1024*1024 or any(x in data.upper() for x in (b'<!DOCTYPE', b'<!ENTITY')):
        raise Error('Unsupported XML size/declarations')
    try: tree = ET.fromstring(data)
    except ET.ParseError as exc: raise Error('Malformed scene XML') from exc
    if tree.tag != 'Scene' or tree.find('EggLists_Version4') is None:
        raise Error('Expected Scene/EggLists_Version4')
    lists = {}
    for node in tree.findall('MarkerLists/List'):
        name = node.get('Name')
        if not name or name in lists: raise Error('Missing/duplicate marker-list name')
        markers = []
        for marker in node.findall('Marker'):
            props = s.properties(marker)
            pos = s.vector(s.value(props, 'Marker Pos', 'Vector3'))
            direction = s.vector(s.value(props, 'Marker Dir', 'Vector3'))
            if s.value(props, 'Marker Type', 'String') is None: raise Error('Missing Marker Type')
            markers.append(dict(attributes=dict(marker.attrib), properties=props,
                                position=pos, direction=direction))
        lists[name] = markers
    managers = []
    for group in tree.findall('EggLists_Version4/List'):
        for egg in group.findall('Egg'):
            for ai in egg.findall('AI_List/AI'):
                if s.value(s.properties(ai), 'AI Name', 'String') != 'gaAnimals_BirdManager': continue
                node = ai.find('gaAnimals_BirdManager')
                if node is None: raise Error('Missing BirdManager configuration')
                props = s.properties(node)
                refs = {key: s.value(props, label, 'String', default) for key, label, default in
                        [('milling', 'Milling MarkerList', 'MillList'),
                         ('flight', 'Flight MarkerList', 'FlightList')]}
                config = {}
                for label, typ, default in [('Min Fly Dist','Float','100'),('Max Fly Dist','Float','600'),
                                            ('Min Mil Dist','Float','200'),('Max Mil Dist','Float','1500'),
                                            ('Rnd Fly','Int','10'),('Rnd Mil','Int','10')]:
                    try: v = s.value(props,label,typ,default);config[label] = f32(float(v)) if typ == 'Float' else min(int(v),10)
                    except (ValueError, TypeError) as exc: raise Error('Invalid property: '+label) from exc
                managers.append(dict(egg_list=group.get('Name'), egg=egg.get('Name'),
                                     ai_attributes=dict(ai.attrib), parameters=props, references=refs,
                                     resolved_config=config, lists={k: lists.get(v) for k,v in refs.items()},
                                     bird_brown_authored=[r.get('Value') for r in props if r.get('Name')=='Bird Brown'],
                                     bird_brown_loaded=True,
                                     bird_brown_note='1af150 calls Boolean writer 1e2b98; fresh owner +94 remains 1'))
    return dict(source=source, decoded_sha256=t.sha(data), managers=managers)


def compact_authored(case):
    result = {k:v for k,v in case.items() if k != 'managers'}
    result['managers'] = []
    for m in case['managers']:
        r = {k:v for k,v in m.items() if k != 'lists'}
        r['lists'] = {}
        for name, markers in m['lists'].items():
            points = [x['position'] for x in markers] if markers is not None else []
            r['lists'][name] = dict(present=markers is not None, authored_point_count=len(points),
                                   ordered_xyz_f32_sha256=t.sha(b''.join(struct.pack('<3f',*x) for x in points)),
                                   bounds_xyz=[list(v) for v in zip(*[(min(x[i] for x in points),max(x[i] for x in points)) for i in range(3)])] if points else None,
                                   marker_no_order_sha256=t.sha(json.dumps([x['attributes'] for x in markers or []],sort_keys=True).encode()),
                                   runtime_record_stride=80, position_offset=64, direction_basis_offset=16,
                                   homogeneous_w_offset=76)
        r['update_pointer_gate'] = 'BOTH_LOCAL_LISTS_PRESENT' if all(v is not None for v in m['lists'].values()) else 'MISSING_LOCAL_LIST; EXTERNAL_REGISTRY_CONTENT_UNKNOWN'
        result['managers'].append(r)
    return result


def corpus_inventory(directory):
    corpus = s.Corpus(directory)
    pairs = json.loads((ROOT/'cdelta1/course-pairs.json').read_text())
    cases=[]
    for pair in pairs:
        entries=[e for e in corpus.manifest['entries'] if e['path']==pair['ps2']]
        if len(entries)!=1: raise Error('Missing/ambiguous paired resource')
        data, report=t.read_payload(entries[0],corpus.directory/'TNG.000')
        case=compact_authored(parse_authored(data,pair['ps2']))
        case.update(course=Path(pair['ps2']).stem, pc_source=pair['pc'], packfs=report)
        cases.append(case)
    counts=lambda name: sum(m['lists'][name]['authored_point_count'] for c in cases for m in c['managers'])
    return dict(schema=SCHEMA, canonical_inputs=corpus.provenance, courses=cases,
                totals=dict(course_pairs=len(cases),managers=sum(len(c['managers']) for c in cases),
                            flight_points=counts('flight'),milling_points=counts('milling'),
                            local_milling_lists=sum(m['lists']['milling']['present'] for c in cases for m in c['managers'])),
                evidence_grade='CONFIRMED_BY_BYTES',runtime_validation='NOT_PERFORMED')


def signed32(n): return ((n+2**31)%2**32)-2**31


@dataclass
class RandomStream:
    """001d5df0 Schrage update; exact integer state and low24/2^24 output.

    A supplied state is synthetic/captured input, never a recovered per-course seed.
    The real accessor 1d5f70 shares a process-global four-byte state.
    """
    state: int
    calls: int = 0

    def __post_init__(self):
        if isinstance(self.state,bool) or not isinstance(self.state,int) or not 0<=self.state<2**32:
            raise Error('RNG state must be an explicit uint32')

    def unit(self):
        seed=signed32(self.state)
        q=(abs(seed)//44488)*(1 if seed>=0 else -1)
        v=signed32((seed-q*44488)*48271-q*3399)
        if v<=0: v=signed32(v+2147483647)
        self.state=v&0xffffffff;self.calls+=1
        return mul(float(self.state&0xffffff),2**-24)

    def real(self,lo,hi): return add(f32(lo),mul(self.unit(),sub(f32(hi),f32(lo))))
    def integer(self,lo,hi):
        if not isinstance(lo,int) or not isinstance(hi,int) or hi<lo:raise Error('Invalid integer range')
        v=lo+math.floor(mul(self.unit(),f32(hi-lo)))
        return lo if v==hi else v


def normalized(v):
    n2=add(add(mul(v[0],v[0]),mul(v[1],v[1])),mul(v[2],v[2]))
    if n2<=2**-23:return (0.,0.,0.)
    inverse=div(1.,f32(math.sqrt(n2)))
    return tuple(mul(x,inverse) for x in v)


def xyz(v):
    try: result=tuple(f32(float(x)) for x in v)
    except (TypeError,ValueError) as exc: raise Error('Finite XYZ input required') from exc
    if len(result)!=3: raise Error('XYZ input requires three components')
    return result


@dataclass
class FlyBird:
    origin: tuple
    direction: tuple = (0.,0.,1.)
    unused_parameter_24: float = 100.
    speed: float = 15.
    travel: float = 0.

    def __post_init__(self):
        self.origin=xyz(self.origin);self.direction=xyz(self.direction)
        self.unused_parameter_24=f32(self.unused_parameter_24)
        self.speed=f32(self.speed);self.travel=f32(self.travel)

    def initialize(self,observer,rng):
        observer=xyz(observer)
        self.speed=add(self.speed,rng.real(0.,15.))
        unused=rng.real(0.,60.)
        self.unused_parameter_24=add(self.unused_parameter_24,unused) if rng.unit()>.5 else sub(self.unused_parameter_24,unused)
        toward=normalized((sub(observer[0],self.origin[0]),0.,sub(observer[2],self.origin[2])))
        mix=rng.real(0.,f32(.12)); lateral=mix if rng.unit()>.5 else -mix
        away=-sub(1.,mix)
        x=add(mul(toward[0],away),mul(toward[2],lateral))
        z=add(mul(toward[2],away),mul(-toward[0],lateral))
        self.direction=normalized((x,rng.real(.001,.2),z));self.travel=0.
        return self.origin

    def step(self,rng):
        dx,dy,dz=self.direction
        if dy<f32(.35):dy=add(dy,div(rng.real(.001,.05),30.))
        self.direction=(dx,dy,dz)
        self.speed=add(self.speed,div(rng.real(.1,2.5),30.))
        self.travel=add(self.travel,div(self.speed,30.))
        return tuple(add(x,mul(y,self.travel)) for x,y in zip(self.origin,self.direction))


def nearest_marker(points,observer,previous=-1):
    if not points: raise Error('Empty list has no valid marker destination')
    points=[xyz(point) for point in points];observer=xyz(observer)
    if isinstance(previous,bool) or not isinstance(previous,int):raise Error('Invalid cached index')
    if previous != -1 and not 0<=previous<len(points):raise Error('Unknown cached index')
    lo,hi=(0,len(points)) if previous==-1 else (max(0,previous-5),min(len(points),previous+5))
    best=previous if previous!=-1 else 0;distance=f32(struct.unpack('<f',bytes.fromhex('ffff7f7f'))[0])
    for i in range(lo,hi):
        dx=sub(points[i][0],observer[0]);dz=sub(points[i][2],observer[2]);d=add(add(mul(dx,dx),0.),mul(dz,dz))
        if d<distance:best,distance=i,d
    return best


def spawn_marker(points,observer,previous,rng):
    base=nearest_marker(points,observer,previous)
    return base,min(len(points)-1,max(0,base+rng.integer(0,3)))


def flight_gate(distance2,min_distance,max_distance):
    return mul(min_distance,min_distance)<distance2<mul(max_distance,max_distance)


@dataclass
class BankSwitcher:
    frame: int=0
    counter: int=0
    def step(self,visual_present=True):
        if not visual_present:return self.frame
        if 3<self.counter:
            self.counter=0;self.frame+=1
            if self.frame>2:self.frame=0
        else:self.counter+=1
        return self.frame


def billboard_rows(camera_rows,scale=.1):
    """330530 Y-locked basis +337a98 scale; render-only camera input.

    No normalization is invented. The bounded producer retains camera-row X/Z.
    """
    if len(camera_rows)!=3 or any(len(row)!=3 for row in camera_rows):raise Error('Three camera XYZ rows required')
    rows=[xyz(row) for row in camera_rows];scale=f32(scale)
    x,z=rows[2][0],rows[2][2]
    if abs(x)<=f32(1.1920929e-6) and abs(z)<=f32(1.1920929e-6):x=1.
    return [[mul(z,scale),0.,mul(-x,scale),0.], [0.,f32(scale),0.,0.],
            [mul(x,scale),0.,mul(z,scale),0.]]


def gs_state():
    """Mode8 integer template writes, not a captured final GS register dump."""
    import foliage_runtime as f
    ops={'GIF_TAG':(0xffc07fffffffffff,0x003e000000000000),
         'TEST':(0xfffffffffff9c000,0x41000),
         'ALPHA':(0xffffff00ffffff00,0x44),
         'ZBUF':(f.MASK64^(1<<32),1<<32),
         'TEX0':(0xffffffe3ffffffff,0x400000000),
         'TEX1':(0xfffff000ffe7fe1e,0x61),
         'FBA':(f.MASK64^1,0)}
    result={}
    for name,(mask,bits) in ops.items():
        r=dict(and_mask=f'{mask:016x}',or_bits=f'{bits:016x}',known_mask=f'{f.MASK64^mask:016x}')
        if name in f.FIELDS:r['fields']=f.decoded_fields(name,bits,f.MASK64^mask)
        result[name]=r
    result['PRIM']=dict(PRIM=4,IIP=1,TME=1,FGE=1,ABE=1,FST='INHERITED',CTXT='INHERITED')
    result['blend_equation']='(Cs-Cd)*As/128+Cd; selectors A0 B1 C0 D1'
    result['CLAMP']='Per atlas rect: WMS=2 WMT=2; min/max from cache+44/+48/+4c/+50; high bits inherited'
    result['boundary']='Mode8 templates; texture bind can overwrite TEX0/TEX1; FRAME/TEXA not resolved'
    return result


def probe_scalar(words,start,fpu,memory):
    """Independent interpreter for compact original straight-line EE/FPU probes.

    Only the explicitly used subset is supported; no full R5900 emulator.
    memory uses synthetic s0-relative byte offsets. Original operation order is
    preserved, while IEEE arithmetic remains FLOAT32_RECONSTRUCTION.
    """
    g={0:0,16:0};f=dict(fpu);mem=dict(memory)
    for i,word in enumerate(words):
        op,rs,rt=word>>26,(word>>21)&31,(word>>16)&31
        imm=word&65535;imm=imm if imm<32768 else imm-65536
        fs,fd,fn=(word>>11)&31,(word>>6)&31,word&63
        if op==15:g[rt]=(word&65535)<<16
        elif op==13:g[rt]=g[rs]|(word&65535)
        elif op==49:f[rt]=f32(mem[g[rs]+imm])
        elif op==57:mem[g[rs]+imm]=f[rt]
        elif op==17 and rs==4:f[fs]=struct.unpack('<f',struct.pack('<I',g[rt]&0xffffffff))[0]
        elif op==17 and rs==16:
            if fn==0:f[fd]=add(f[fs],f[rt])
            elif fn==3:f[fd]=div(f[fs],f[rt])
            elif fn==6:f[fd]=f[fs]
            else:raise Error(f'Unsupported scalar probe FPU at {start+i*4:x}')
        elif word==0:pass
        elif op==0 and fn==45:g[fs]=g.get(rs,0)+g.get(rt,0)
        else:raise Error(f'Unsupported scalar probe instruction at {start+i*4:x}')
    return f,mem


def trace(origin,observer,seed,steps):
    if not isinstance(steps,int) or not 0<=steps<=100000:raise Error('Invalid diagnostic step count')
    rng=RandomStream(seed);bird=FlyBird(tuple(origin));bird.initialize(observer,rng);switch=BankSwitcher()
    initial=dict(bird=asdict(bird),rng=asdict(rng));timeline=[]
    for i in range(steps):
        position=bird.step(rng);frame=switch.step()
        timeline.append(dict(invocation=i,position=position,direction=bird.direction,speed=bird.speed,
                             travel=bird.travel,image_key=frame,rng=asdict(rng)))
    return dict(schema=SCHEMA,inputs='EXPLICIT_SYNTHETIC_DIAGNOSTIC',
                initial=initial,observer=observer,seed=seed,steps=steps,updates=timeline,
                source_point_data=dict(kind='SYNTHETIC',original_resource=None),
                timing=dict(source='OWNER_INVOCATION_COUNT',wall_clock_cadence='UNKNOWN'),
                precision='FLOAT32_RECONSTRUCTION',runtime_validation='NOT_PERFORMED',
                limitations=['One invocation per step; no proven wall-clock cadence',
                             'Motion and animation are separate owner slots; trace uses explicit motion-then-animation order',
                             'Global RNG consumers outside this one bird are excluded',
                             'Host IEEE sqrt/div are not bit-exact PS2 FPU'])


def resource_inventory(directory):
    corpus=s.Corpus(directory);out=[]
    for entry in corpus.manifest['entries']:
        if 'BURDY' not in entry['path']:continue
        data,provenance=t.read_payload(entry,corpus.directory/'TNG.000')
        row=dict(path=entry['path'],decoded_size=len(data),decoded_sha256=t.sha(data),packfs=provenance)
        if entry['path'].endswith('.PSB'):
            bank=p.parse_psb(data)
            if bank['unknown_ranges']:raise Error('Unsupported bird bank trailing bytes')
            row.update(type='SPRITE_BANK',mapping=bank['mappings'],images=[dict(key=x['image_index'],
                source_triangle_count=x['triangle_count'],local_bounds=x['local_bounds_xyxy']) for x in bank['images']],
                texture_references=bank['texture_references'],loader='0x00380a08 -> 0x00386d28',consumer='0x00337a98')
        elif entry['path'].endswith('.GXI'):row.update(type='TEXTURE',gxi=p.parse_gxi(data),loader='0x002fd7d0',consumer='0x003376c0 -> 0x00311c50')
        else:raise Error('Unexpected Burdy resource kind')
        out.append(row)
    return dict(schema=SCHEMA,resources=out,evidence_grade='CONFIRMED_BY_BOTH',runtime_validation='NOT_PERFORMED')


def point_map(path,points):
    if not points:raise Error('No points to visualize')
    lo=[min(p[i] for p in points) for i in (0,2)];hi=[max(p[i] for p in points) for i in (0,2)]
    scale=660/max(hi[0]-lo[0],hi[1]-lo[1],1)
    circles=''.join(f'<circle cx="{30+(x-lo[0])*scale:.3f}" cy="{30+(z-lo[1])*scale:.3f}" r="3" fill="#2187a4"/>' for x,y,z in points)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="740" height="740"><rect width="740" height="740" fill="white"/>'+circles+'<text x="20" y="720">Authored origins, X/Z; no connected flight route; NOT runtime</text></svg>\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['inventory','resources','trace','contract'])
    ap.add_argument('--input',type=Path);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--state',type=Path);ap.add_argument('--steps',type=int,default=30)
    a=ap.parse_args();out=local_output(a.output)
    if a.mode in ('inventory','resources'):
        if a.input is None:ap.error('--input required')
        result=corpus_inventory(a.input) if a.mode=='inventory' else resource_inventory(a.input)
    elif a.mode=='trace':
        if a.state is None:ap.error('--state JSON with origin/observer/seed required')
        state=json.loads(a.state.read_text());result=trace(state['origin'],state['observer'],state['seed'],a.steps)
    else:result=json.loads((ROOT/'ambient2/bird-render-contract.json').read_text())
    t.write_json(out,result);print(json.dumps(dict(output=str(out),runtime_validation='NOT_PERFORMED')))


if __name__=='__main__':main()
