"""SDK-native Blazer lamp transfer and Mercedes glass authoring for Roster V4.

The PC assets are ordinary native DX/DXT resources. The optional renderer
registry only binds authored lamp draws to its existing PS2 Glow transaction.
"""
from __future__ import annotations
import argparse, json, struct, sys, shutil, os, hashlib
from dataclasses import replace
from pathlib import Path
from collections import Counter
from vehicle_presentation_fix import Resources, sha
from verify_vehicle_presentation_fix import native
from vehicle_roster_build import fnv64


def merge(parts):
    from master_rallye.topology_writer import DrawGeometry
    vs=[];ts=[]
    for g in parts:
        at=len(vs);vs.extend(g.vertices);ts.extend(tuple(i+at for i in t)for t in g.triangles)
    return DrawGeometry(tuple(vs),tuple(ts))


def transfer(targets,donor):
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import DrawGeometry,source_geometry
    from master_rallye.scene_dx_writer import ScenePart
    from master_rallye.preview_scene import logical_cases
    from master_rallye.addon_sdk.native_effect_reference import _components,_bounds
    m=parse_dx_bytes(donor);geom=source_geometry(m);cases,_=logical_cases(m)
    cores=[d for d in m.physical_draws if cases.get(d.draw_index)==(1,2)and not d.flags_0x20[0]]
    halos=[d for d in m.physical_draws if cases.get(d.draw_index)==(1,2)and d.flags_0x20[0]]
    assert len(cores)==len(halos)==1
    coreparts=sorted(_components(geom[cores[0].draw_index]),key=lambda g:sum(v.position[0]for v in g.vertices))
    haloparts=sorted(_components(geom[halos[0].draw_index]),key=lambda g:sum(v.position[0]for v in g.vertices))
    assert len(coreparts)==len(haloparts)==2
    clusters={}
    for part in _components(merge(targets)):
        box=_bounds(part);key='centre'if box[0][0]<0<box[1][0]else'left'if box[1][0]<=0 else'right'
        clusters.setdefault(key,[]).append(part)
    if not {'left','right'}<=clusters.keys():raise ValueError('two independently identified source lamps required')
    output=[[],[]];fits=[]
    for side,parts in sorted(clusters.items()):
        target=_bounds(merge(parts));index=1 if side=='right'else 0;original=_bounds(coreparts[index])
        ratios=[(target[1][k]-target[0][k])/(original[1][k]-original[0][k])for k in (0,1)]
        scale=min(ratios)
        # Existing high centre strip keeps its horizontal footprint. This is
        # explicit authoring, independent of the two main side-lamp fits.
        scales=[ratios[0],ratios[1],scale]if side=='centre'else[scale]*3
        if any(not .05<=s<=4 for s in scales):raise ValueError('lamp fit exceeds authoring budget')
        anchor=lambda b:[(b[0][k]+b[1][k])/2 if k<2 else b[0][k]for k in range(3)]
        a,b=anchor(target),anchor(original)
        for layer,part in enumerate((coreparts[index],haloparts[index])):
            output[layer].append(DrawGeometry(tuple(replace(v,position=tuple(a[k]+scales[k]*(v.position[k]-b[k])for k in range(3)))for v in part.vertices),part.triangles))
        fits.append({'side':side,'target_bounds':target,'donor_bounds':original,'scales':scales})
    return [ScenePart(merge(output[i]),tuple((cores if i==0 else halos)[0].texture_tuple),alpha=i==1,diffuse=False)for i in range(2)],fits


def parts_with_states(raw,new_lamps):
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.scene_dx_writer import ScenePart
    from master_rallye.preview_scene import logical_cases
    m=parse_dx_bytes(raw);geometry=source_geometry(m);cases,_=logical_cases(m)
    part=lambda d:ScenePart(geometry[d.draw_index],d.texture_tuple,bool(d.flags_0x20[0]),bool(d.flags_0x20[1]),bool(d.unknown_0x24&4),bool(d.flags_0x20[2]))
    items=[];i=0
    while i<len(m.physical_draws):
        d=m.physical_draws[i]
        if d.tag!=7:items.append(part(d));i+=1;continue
        label=d.group_label;n=d.control_words[4];j=i+n;second=m.physical_draws[j]
        count=second.control_words[1];off=[part(x)for x in m.physical_draws[i:j]]
        on=[part(x)for x in m.physical_draws[j:j+count]]
        # Some imported models serialize case2 first. The SDK writer emits
        # case1 first: preserve selector meaning, not physical record order.
        if d.control_words[3]==2:off,on=on,off
        if label=='blight':on=off+new_lamps
        items.append((label,off,on));i=j+count
    return items


def draw_identity(m,d):
    # Match the actual renderer algorithms, including native float bit order.
    faces=[];corners=[];indices=m.draw_global_indices(d)
    for at in range(0,len(indices),3):
        points=[]
        for i in indices[at:at+3]:
            pos=m.vertices.positions[i]
            bits=tuple(struct.unpack('<I',struct.pack('<f',0.0 if v==0 else v))[0]for v in pos)
            points.append(bits);corners.append(struct.pack('<3f2f',*pos,*m.uv_sets[0].values[i]))
        faces.append(sha(b''.join(struct.pack('<3I',*p)for p in sorted(points))))
    return sha(''.join(sorted(faces)).encode()),sha(b''.join(sorted(corners)))


def unlock_description(raw,img):
    # Keep all prior owners; prepend a Forklift-only branch before their chain.
    site=0x481acf;op,off=img.rvp.op_at(site)
    if not op or op['after'][off]!=0xe9:raise ValueError('expected active locked-description bridge')
    previous=site+5+struct.unpack_from('<i',op['after'],off+1)[0]
    text=img.append(b'UNLOCK WITH UNLOCK CARS CHEAT\0')
    # Non-Forklift -> previous bridge. Forklift -> native ModelName broker,
    # then the native string setter with a truthful, narrowly scoped message.
    start=(len(img.payload)+15)&~15;base=0x10000000+start
    code=bytearray(b'\x83\xf8\x16\x0f\x85'+struct.pack('<i',previous-(base+9)))
    code+=b'\x68'+struct.pack('<I',0x6b76f8)+b'\x8d\x4c\x24\x10'
    code+=b'\xe8'+struct.pack('<i',0x4d0580-(base+len(code)+5))
    code+=b'\xb8'+struct.pack('<I',text)
    code+=b'\xe9'+struct.pack('<i',0x481b64-(base+len(code)+5))
    assert img.append(code)==base
    img.write(site,b'\xe9'+struct.pack('<i',base-site-5))
    return {'entry':base,'previous':previous,'resume':0x481b64,'text':'UNLOCK WITH UNLOCK CARS CHEAT','stock_text':'UNLOCK BY WINNING 1 T1 CUP','unlock_flag':'Bonus2','normal_award_found':False}


def build(source,out,sdk):
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.preview_scene import logical_cases
    from master_rallye.addon_sdk.native_states import wrap_states,author_states
    from master_rallye.addon_sdk.auto_features import derive
    from master_rallye.glass_authoring import subset
    source=source.resolve();out=out.resolve()
    if out.exists() or out==source or source in out.parents:raise ValueError('choose a fresh sibling output host')
    resources=Resources(source);old,img=native(source);report={'schema':'mr-addon-lamp-authoring/1','source':str(source),'source_roster_sha256':sha(old),'gameplay_tested':False,'families':[]}
    donor=resources.read('DataGx/Vehicles/Chevyblazer/car.dx')
    # A known stock signature cross-check catches a Python/native hashing mismatch.
    dm=parse_dx_bytes(donor)
    assert draw_identity(dm,dm.physical_draws[34])==('335831c600040fd15759a169c8ddcf9ff910118bfe701964d7c4d2aa8001c1ca','0262dd49ea66080f91266f31ff89763c944d111d7222219726cf7c4db3e11b80')
    changes={};bindings=[]
    # Demo restorations only. Independent addons retain their authored lamps.
    families=['Mercedes','Trooper','ForesterSTI','Rav4','Tomcat','HeritageNewRav']
    report['preserve_native_families']=['ImprezaProto','LancerEvo4','Evo2FourRunner']
    for family in families:
        rel=f'DataGx/Vehicles/{family}/car.dx';raw=resources.read(rel);m=parse_dx_bytes(raw);g=source_geometry(m)
        detail={'family':family,'source_sha256':sha(raw)}
        if family=='Mercedes':
            textures={}
            for d in m.physical_draws:
                for t in d.texture_tuple:
                    if t!='Null':textures[(t+'.dxt').lower()]=resources.read(f'DataGx/Vehicles/{family}/{t}.dxt')
            states,_,glass=derive(raw,textures,glass=True,brake=False)
            # Explicit rear lens material/triangle selection; generic redness
            # also selects Mercedes' red body paint and is not used for lamps.
            ids=[i for i,t in enumerate(g[5].triangles)if max(g[5].vertices[v].position[2]for v in t)<-1.5]
            if m.physical_draws[5].texture_tuple[0]!='mblight64-tga' or len(ids)!=22:raise ValueError('Mercedes lamp selection needs review')
            targets=[subset(g[5],ids)];lamps,fits=transfer(targets,donor)
            states['brake']={'source_draw':5,'triangles':ids,'lit_texture':lamps[0].textures[0],'glow_texture':lamps[1].textures[0],'evidence':'Explicit Mercedes rear mblight64 lens triangles; original Blazer core/halo fitted independently to each side'}
            if len(states.get('panes',[]))!=3:raise ValueError('Mercedes glass selection needs review')
            extra_name='mr-auto-cracked-tga.dxt';changes[f'DataGx/Vehicles/{family}/{extra_name}']=resources.read('DataGx/Vehicles/Navara/windscreenc32-tga.dxt')
            fixed,validation=author_states(raw,states,brake_lit=lamps[0],brake_glow=lamps[1],brake_material={'alpha':False,'alpha_test':False,'environment':False,'diffuse':False,'secondary_texture':'Null'})
            detail.update(glass=glass,native_states=states,sdk_validation=validation)
        else:
            cases,_=logical_cases(m)
            target_draws=[d for d in m.physical_draws if cases.get(d.draw_index)==(1,2)and not d.flags_0x20[2]and(not d.flags_0x20[0]or d.flags_0x20[1])]
            if not target_draws:raise ValueError(f'{family}: no authored ON core')
            lamps,fits=transfer([g[d.draw_index]for d in target_draws],donor)
            fixed=wrap_states(raw,parts_with_states(raw,lamps))
        changed=parse_dx_bytes(fixed);cases,_=logical_cases(changed)
        for d in changed.physical_draws:
            if cases.get(d.draw_index)==(1,2)and not d.flags_0x20[2]:
                geom,uv=draw_identity(changed,d);bindings.append(f'{family} {int(bool(d.flags_0x20[0]))} {d.local_vertex_max+1} {d.triangle_count} {geom} {uv}')
        # Original collision remains source-authoritative; bounds may expand
        # for the copied halo and are recomputed by the SDK writer.
        assert raw[m.collision.offset:m.collision.unparsed_offset]==fixed[changed.collision.offset:changed.collision.unparsed_offset]
        changes[rel]=fixed
        for name in ('breaklightson-tga.dxt','breaklightsonglow-tga.dxt'):
            changes[f'DataGx/Vehicles/{family}/{name}']=resources.read('DataGx/Vehicles/Chevyblazer/'+name)
        detail.update(output_sha256=sha(fixed),fits=fits,collision_preserved=True)
        report['families'].append(detail)
    report['forklift']={'status':'NO_OPTICAL_SURFACES','both_modes':'no effect','owner_instruction':'preserve model without lamps'}
    report['unlock_description']=unlock_description(old,img)
    ro,rl,po,pl=struct.unpack_from('<4I',old,144);rvp=img.rvp.build();header=bytearray(old[:256]);payload=bytes(img.payload)
    if len(payload)>struct.unpack_from('<I',header,20)[0]:raise ValueError('native payload exceeds existing allocation')
    struct.pack_into('<I',header,24,len(payload));struct.pack_into('<4I',header,144,256,len(rvp),256+len(rvp),len(payload));struct.pack_into('<Q',header,160,fnv64(rvp+payload))
    header[176:256]=b'Roster V4 lamps fix 02'.ljust(80,b'\0');roster=bytes(header)+rvp+payload
    out.mkdir(parents=True)
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if 'active.prev'in rel.parts or 'logs'in rel.parts:continue
        dst=out/rel
        if p.is_dir():dst.mkdir(parents=True,exist_ok=True)
        else:
            dst.parent.mkdir(parents=True,exist_ok=True)
            if rel==Path('Data.sma'):os.link(p,dst)
            else:shutil.copy2(p,dst)
    historical=out/'provenance/presentation-fix-01';historical.mkdir(parents=True,exist_ok=True)
    for name in ('source-build-manifest.json','vehicle-presentation-report.json','vehicle-presentation-validation.json','READ_ME.md'):
        if (out/name).is_file():shutil.move(str(out/name),str(historical/name))
    active=out/'MRMods/Vehicles/active'
    for rel,data in changes.items():
        p=active/'resources'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    (active/'roster.mrvr').write_bytes(roster)
    registry='MR-ADDON-LAMPS 1\n'+'\n'.join(bindings)+'\n';(active/'addon-brake-lamps.tsv').write_text(registry,encoding='ascii')
    report.update(registry_rows=len(bindings),donor_sha256=sha(donor),roster_sha256=sha(roster),source_sdk=str(sdk.resolve()))
    catalog=json.loads((active/'catalog.json').read_text());catalog.update(label='Roster V4 lamps fix 02',roster_mrvr_sha256=sha(roster),native_patch_operations_sha256=sha(rvp),native_extension_sha256=sha(payload),source_runtime_role='historical_ancestor_only',source_active_roster_sha256=sha(old))
    catalog['active_derivation']={'tool':'tools/vehicle_lamp_authoring.py','source_host':str(source),'source_roster_sha256':sha(old)}
    catalog['resources']=[{'path':p.relative_to(active/'resources').as_posix(),'size':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in sorted((active/'resources').rglob('*'))if p.is_file()]
    (active/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');(out/'vehicle-lamp-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-host',type=Path,required=True);p.add_argument('--output-host',type=Path,required=True);p.add_argument('--sdk',type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.sdk.resolve()/'src'));report=build(a.source_host,a.output_host,a.sdk)
    print(json.dumps({k:report[k]for k in ('roster_sha256','registry_rows','forklift','unlock_description')},indent=2))
