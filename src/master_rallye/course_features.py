"""Inspect-only course dressing, trigger and surface inventories.

Proxy layouts follow existing pc-port prepare_* tools. No runtime hooks.
"""
from __future__ import annotations
import math
from pathlib import Path
import re
import struct

from .sidecar import parse_sidecar


class Reader:
    def __init__(self,raw):self.raw=raw;self.at=0
    def read(self,fmt):
        codec=struct.Struct(fmt)
        if self.at+codec.size>len(self.raw):raise ValueError('Truncated proxy feature asset')
        value=codec.unpack_from(self.raw,self.at);self.at+=codec.size
        if any(isinstance(x,float) and not math.isfinite(x) for x in value):raise ValueError('Non-finite feature data')
        return value
    def skip(self,count):
        if count<0 or self.at+count>len(self.raw):raise ValueError('Invalid feature span')
        self.at+=count
    def done(self):
        if self.at!=len(self.raw):raise ValueError('Unconsumed feature bytes')


def _text(raw):return raw.split(b'\0',1)[0].decode('ascii')


def read_proxy_features(path, course_dx):
    raw=Path(path).read_bytes()
    if len(raw)>64*1024*1024:raise ValueError('Feature asset exceeds inspect budget')
    r=Reader(raw);records=[];course_dx=course_dx.replace('\\','/').casefold()
    if raw[:8]==b'PS2GRS01':
        magic,version,count,bins,width,height,image_bytes,psm,gxi,pc=r.read('<8s6I32s32s32s')
        if version!=1 or not 0<count<=300000 or not 0<bins<=min(65536,count) or (width,height,image_bytes)!=(32,32,4096):
            raise ValueError('Unsupported grass/shrub asset')
        cells=[r.read('<2i2I') for _ in range(bins)]
        points=[r.read('<3f') for _ in range(count)];r.skip(image_bytes);r.done()
        next_index=0;last=None
        for x,z,first,size in cells:
            if first!=next_index or not size or first+size>count or (last is not None and (z,x)<=last):raise ValueError('Invalid ground-detail bins')
            for point in points[first:first+size]:
                if math.floor(point[0]/8)!=x or math.floor(point[2]/8)!=z:raise ValueError('Ground detail point outside source bin')
            next_index+=size;last=(z,x)
        if next_index!=count:raise ValueError('Unbound ground-detail points')
        records.append(dict(kind='shrubs' if 'shrub' in Path(path).stem.casefold() else 'mini_grass',name=Path(path).stem,
                            points=points,source_pc_sha256=pc.hex(),source_psm_sha256=psm.hex(),source_texture_sha256=gxi.hex(),
                            bins=len(cells),representation='original placement point cloud; no billboard geometry inferred'))
    elif raw[:8]==b'PS2SPL01':
        magic,version,nt,nm,nv,nc,no=r.read('<8s6I')
        if version!=1 or not 0<nt<=32 or not 0<nm<=32 or not 0<nv<=65536 or not 0<nc<=64 or not 0<no<=128:raise ValueError('Unsupported spline asset header')
        for _ in range(nt):
            w,h=r.read('<2I')
            if not 0<w<=2048 or not 0<h<=2048:raise ValueError('Invalid spline texture')
            r.skip(w*h*4)
        models=[r.read('<16sI6If') for _ in range(nm)]
        vertices=[r.read('<3fI2f') for _ in range(nv)]
        courses=[r.read('<48s64s32s2I') for _ in range(nc)]
        objects=[r.read('<32s3I4B4f2i') for _ in range(no)]
        total=sum(o[3] for o in objects)
        if any(not 4<=o[3]<=64 for o in objects):raise ValueError('Invalid spline control count')
        points=[r.read('<3f') for _ in range(total)];r.done()
        for course in courses:
            if _text(course[1]).replace('\\','/').casefold()!=course_dx:continue
            first,count=course[3:5]
            if first+count>no:raise ValueError('Invalid spline course span')
            for obj in objects[first:first+count]:
                name,model,start,size,*config=obj
                if model>=nm or start+size>total:raise ValueError('Invalid spline object span')
                records.append(dict(kind='spline_object',name=_text(name),points=points[start:start+size],model=_text(models[model][0]),
                                    config=dict(zip(('const_speed','loop','trigger','rest','speed','on_distance','off_distance','banking','rest_ticks','samples'),config)),
                                    source_pc_sha256=course[2].hex(),representation='native control polygon; Catmull-Rom runtime interpolation not baked'))
    elif raw[:8]==b'PS2BRD01':
        magic,version,nf,nc,np=r.read('<8s4I')
        if version!=1 or not 0<nf<=16 or not 0<nc<=64 or np>65536:raise ValueError('Unsupported bird asset')
        r.skip(4*16*16*4);r.skip(nf*2*struct.calcsize('<I6f6f'))
        courses=[r.read('<48s64s32s4f2i2B2x2I') for _ in range(nc)]
        points=[r.read('<3f') for _ in range(np)];r.done()
        for course in courses:
            if _text(course[1]).replace('\\','/').casefold()!=course_dx:continue
            first,count=course[-2:]
            if first+count>np:raise ValueError('Invalid bird point span')
            records.append(dict(kind='bird_triggers',name=_text(course[0]),points=points[first:first+count],
                min_fly=course[3],max_fly=course[4],min_milling=course[5],max_milling=course[6],
                random_fly=course[7],random_milling=course[8],flight_present=bool(course[9]),milling_present=bool(course[10]),
                source_pc_sha256=course[2].hex(),representation='flight spawn/trigger anchors; manager list gates retained; no fabricated active birds'))
    else:raise ValueError('Unsupported proxy feature format')
    for record in records:record.update(source=str(Path(path).resolve()),support='INSPECT_ONLY')
    if not records:raise ValueError('Feature asset has no exact matching course DX binding')
    return records


def scene_features(project):
    records=[]
    if project.race_logic:
        for egg in project.race_logic.source_document.eggs:
            tags=[c.tag for c in egg.components()]
            names=[a.ai_name or '' for a in egg.ai_objects]
            if egg.list_name=='Sound' or any('sound' in x.casefold() for x in tags+names):
                kind='sound_trigger'
            elif any('bird' in x.casefold() for x in tags+names):kind='bird_manager'
            elif any('spline' in x.casefold() for x in tags+names):kind='spline_controller'
            else:continue
            matrix=egg.matrix()
            records.append(dict(kind=kind,name=egg.name,path=egg.xml_path,center=matrix.position if matrix else None,
                components=tags,ai_names=names,values=[dict(name=v.name,type=v.type_name,value=v.value) for c in egg.components() for v in c.values],
                support='INSPECT_ONLY',source=str(project.resources.race_test_xml)))
    source=project.resources.source_txt
    if source:
        for material in parse_sidecar(source).materials:
            surface=re.findall(r'\$surfacetype\(([^)]+)\)',material.name,re.I)
            ground=re.findall(r'\$grnd\(([^)]+)\)',material.name,re.I)
            if surface or ground:
                records.append(dict(kind='surface_type',name=material.name,material_number=material.number,
                                    surface=surface,ground=ground,source=str(source),support='INSPECT_ONLY',
                                    semantics='literal source tokens; physics binding/rebuild not inferred from shading'))
    return records
