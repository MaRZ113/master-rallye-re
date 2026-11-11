"""Targeted asset, native-description and registry checks for lamps fix02."""
import argparse,json,struct,sys
from pathlib import Path
from collections import Counter
from vehicle_presentation_fix import Resources,sha
from verify_vehicle_presentation_fix import native,machine,capture_initializers,check_bonus2
from vehicle_lamp_authoring import draw_identity


def triangles(raw,exclude_lit=True,flatten=False):
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    m=parse_dx_bytes(raw);cases,_=logical_cases(m);result=Counter()
    for d in m.physical_draws:
        state=cases.get(d.draw_index)
        if exclude_lit and state==(1,2):continue
        if flatten and state and state[1]==2:continue
        state=None if flatten else state
        ids=m.draw_global_indices(d)
        for at in range(0,len(ids),3):
            # Corners, including winding, retain actual UV/normal/colour bytes.
            attrs=tuple((m.vertices.positions[i],m.vertices.normals[i],m.vertices.colors[i*4:i*4+4],m.uv_sets[0].values[i])for i in ids[at:at+3])
            result[(state,attrs,d.texture_tuple,d.flags_0x20,d.unknown_0x24)]+=1
    return result


def description(host,img,cid,new):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_EIP
    u=machine(host,img);u.reg_write(UC_X86_REG_EAX,(cid-3)&0xffffffff);u.reg_write(UC_X86_REG_EBX,8)
    def hook(u,at,size,user):
        if at!=0x4d0580:return
        esp=u.reg_read(UC_X86_REG_ESP);ret,key=struct.unpack('<2I',u.mem_read(esp,8))
        assert bytes(u.mem_read(key,64)).split(b'\0')[0]==b'Frontend/VehicleSelect/ModelName'
        u.mem_write(u.reg_read(UC_X86_REG_ECX),struct.pack('<I',key));u.reg_write(UC_X86_REG_ESP,esp+8);u.reg_write(UC_X86_REG_EIP,ret)
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x481acf,0x481b64 if new and cid==25 else 0x481b49,count=10000)
    if new and cid==25:
        return bytes(u.mem_read(u.reg_read(UC_X86_REG_EAX),100)).split(b'\0')[0].decode()
    return u.reg_read(UC_X86_REG_EBX)


def verify(source,candidate,state_host=None):
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    a,ai=native(source);b,bi=native(candidate)
    before=capture_initializers(source,ai);after=capture_initializers(candidate,bi)
    assert before==after
    assert a[100:144]==b[100:144] and a[20:24]==b[20:24] and a[28:96]==b[28:96]
    assert bytes(bi.payload[:len(ai.payload)])==bytes(ai.payload)
    report={'status':'OFFLINE_VALIDATED','gameplay_tested':False,'initializers_identical':35,
            'forklift_unlock':check_bonus2(candidate,bi),'forklift_description':description(candidate,bi,25,True)}
    assert report['forklift_description']=='UNLOCK WITH UNLOCK CARS CHEAT'
    assert description(source,ai,25,False)==26
    for cid in range(35):
        if cid!=25:assert description(source,ai,cid,False)==description(candidate,bi,cid,True)
    report['other_locked_descriptions_preserved']=34
    # English localization row6/26 in the original executable points to the
    # misleading T1 Cup text. Its bytes are not changed globally by this fix.
    ar,br=Resources(source),Resources(candidate)
    report['families']=[];binding_lines=(candidate/'MRMods/Vehicles/active/addon-brake-lamps.tsv').read_text().splitlines()
    assert binding_lines[0]=='MR-ADDON-LAMPS 1'
    data=json.loads((candidate/'vehicle-lamp-report.json').read_text())
    for item in data['families']:
        family=item['family'];rel=f'DataGx/Vehicles/{family}/car.dx';old,new=ar.read(rel),br.read(rel)
        x,y=parse_dx_bytes(old),parse_dx_bytes(new);cases,_=logical_cases(y)
        if family=='Mercedes':
            assert triangles(old,flatten=True)==triangles(new,flatten=True)
            labels={g.root.group_label for g in y.draw_groups if g.root.tag==7}
            assert labels=={'blight','screenfront','screenleft','screenright'}
            assert item['sdk_validation']['intact_off_geometry_normals_uv_materials_identical']
        else:assert triangles(old)==triangles(new),family
        assert old[x.collision.offset:x.collision.unparsed_offset]==new[y.collision.offset:y.collision.unparsed_offset]
        lit=[d for d in y.physical_draws if cases.get(d.draw_index)==(1,2) and not d.flags_0x20[2]]
        assert len(lit)==2
        for layer,d in enumerate(lit):
            assert d.flags_0x20==bytes([layer,0,0,1]) and d.unknown_0x24==1
            assert d.texture_tuple==('breaklightson-tga'if layer==0 else'breaklightsonglow-tga','Null','Null')
            g,uv=draw_identity(y,d);assert f'{family} {layer} {d.local_vertex_max+1} {d.triangle_count} {g} {uv}'in binding_lines
        report['families'].append({'family':family,'collision_preserved':True,'body_uv_materials_preserved':True,'PC_Glow':True,'PS2_Glow_binding':True})
    assert ar.read('DataGx/Vehicles/Forklift/car.dx')==br.read('DataGx/Vehicles/Forklift/car.dx')
    assert len(binding_lines)==1+2*len(data['families'])
    for family in data.get('preserve_native_families',[]):
        assert ar.read(f'DataGx/Vehicles/{family}/car.dx')==br.read(f'DataGx/Vehicles/{family}/car.dx')
        assert not any(line.startswith(family+' ') for line in binding_lines[1:])
    # Existing base/skin textures and untouched models must not drift.
    active=source/'MRMods/Vehicles/active/resources';replaced={f'DataGx/Vehicles/{r["family"]}/car.dx'for r in data['families']}
    replaced|={f'DataGx/Vehicles/{r["family"]}/{n}.dxt'for r in data['families']for n in ('breaklightson-tga','breaklightsonglow-tga')}
    preserved=0
    for p in active.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(active).as_posix()
        if rel not in replaced:assert p.read_bytes()==br.read(rel);preserved+=1
    report['existing_overlay_files_preserved']=preserved
    state_host=state_host or source
    for name in ('MRallye.exe','dinput8.dll','MRallyeExtraOptions.ini','MRallyeRandomizerRuntime.dll','DataGame/PlayerState.xml','DataGame/options.xml'):
        if (state_host/name).is_file():assert (state_host/name).read_bytes()==(candidate/name).read_bytes(),name
    report['mutable_state_reference']=str(state_host)
    report['roster_sha256']=sha(b)
    (candidate/'vehicle-lamp-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-host',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--sdk',type=Path,required=True)
    p.add_argument('--state-host',type=Path,help='Actual accepted parent if its saves/config changed since asset baseline')
    a=p.parse_args();sys.path.insert(0,str(a.sdk.resolve()/'src'));print(json.dumps(verify(a.source_host,a.candidate,a.state_host),indent=2))
