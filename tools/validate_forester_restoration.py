"""Private V-DEF1 regression, accepted-roster conservation and native evidence."""
from pathlib import Path
import argparse,json,hashlib,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from build_sdk_roster import derive
from validate_sdk_roster import validate
import prepare_sdk_capacity_probe as probe
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.preview_scene import logical_cases,presentation_wheels
from master_rallye.workshop.service import WorkshopProject
from master_rallye.addon_sdk.heritage_source import compatible_model


from master_rallye.addon_sdk.demo_restoration import off_geometry


def run(restoration,accepted_config,retail,output,*,repeat=False,emulate=False):
    if output.exists():raise ValueError('Fresh verification report required')
    first=restoration/'workshop/builds/first/candidate';config=json.loads((first/'roster-config.json').read_text())
    result=validate(config,first);old=derive(json.loads(accepted_config.read_text()));new=first/'runtime/resource-root'
    shared={'DataGame/vehicles.xml','DataGame/Modifications.xml','DataScene/FrontendScreens/VehicleSelect.xml',*(p+'.dxb'for p,_,_,_ in BANKS.values())}
    unchanged=[]
    for path,value in old['resources'].items():
        if path in shared:continue
        if probe.value(value)!=(new/path).read_bytes():raise ValueError('Accepted 30-entry resource changed: '+path)
        unchanged.append(path)
    for name in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        rows=lambda b:{n.get('Name'):dict(n.attrib)for n in ET.fromstring(b).iter('Value')}
        before,after=rows(probe.value(old['resources'][name])),rows((new/name).read_bytes())
        if any(after.get(n)!=v for n,v in before.items()):raise ValueError('Accepted physics field changed')
    for _,(prefix,_,_,_)in BANKS.items():
        before=parse_bank(probe.value(old['resources'][prefix+'.dxb']));after=parse_bank((new/(prefix+'.dxb')).read_bytes())
        if before['records']!=after['records'][:before['count']]:raise ValueError('Accepted UI frame changed')
    source=restoration/'author/assets/source/Forester';target=new/'DataGx/Vehicles/DefForester'
    resource_equal={n:(source/n).read_bytes()==(target/n).read_bytes()for n in ('car.dx','complete.dx','wheel.dx')}
    if not all(resource_equal.values()):raise ValueError('Native compiler changed the qualified resource assembly')
    raw=(retail/'DataGx/Vehicles/Forester/car.dx').read_bytes();m=parse_dx_bytes(raw);g=source_geometry(m);cases,_=logical_cases(m)
    states=[{'draw':d.draw_index,'label':d.group_label,'case':cases[d.draw_index],'textures':list(d.texture_tuple),'flags':list(d.flags_0x20),'state_word':d.unknown_0x24,'triangles':d.triangle_count}for d in m.physical_draws if d.draw_index in cases]
    glass=[]
    for group in m.draw_groups:
        if group.root.tag!=7 or not group.root.group_label.startswith('screen'):continue
        ids=group.draw_indices
        if len(ids)!=2:raise ValueError('Unsupported donor glass span')
        a,b=(g[i]for i in ids)
        glass.append({'label':group.root.group_label,'triangles':len(a.triangles),'positions_equal':tuple(v.position for v in a.vertices)==tuple(v.position for v in b.vertices),
                      'changed_normals':sum(v.normal!=w.normal for v,w in zip(a.vertices,b.vertices)),'changed_uvs':sum(v.uvs!=w.uvs for v,w in zip(a.vertices,b.vertices))})
    models=[parse_dx_bytes((source/n).read_bytes())for n in ('car.dx','complete.dx','wheel.dx')]
    original=compatible_model((restoration/'author/native-import/car.dx').read_bytes(),'canonical Forester')[0]
    before,after=off_geometry(original),off_geometry((target/'car.dx').read_bytes())
    for key in ('surface_sha256','uv_surface_sha256','normal_color_surface_sha256','material_surface_sha256'):
        if before[key]!=after[key]:raise ValueError('Original OFF geometry or material semantics changed: '+key)
    result.update(accepted_30_roster_resources_unchanged=len(unchanged),compiled_model_bytes_preserved=resource_equal,donor_states=states,donor_glass=glass,
                  source_wheel_measurements=presentation_wheels(*models),off_geometry={'source':before,'restored':after,'donor':off_geometry(raw)},owner_gameplay='NOT TESTED')
    restoration_report=json.loads((restoration/'restoration-result.json').read_text())
    if restoration_report.get('retail_corrections'):
        from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
        profile=json.loads((restoration/'author/physics-profile.json').read_text())
        if profile['overrides']or profile.get('owned_tyres')or profile['donor_family']!='Forester':raise ValueError('Corrected candidate must use exact retail physics')
        counts={}
        for name in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
            values={v.get('Name'):dict(v.attrib)for v in ET.fromstring((new/name).read_bytes()).iter('Value')}
            donor={k:v for k,v in values.items()if k.startswith('Vehicles/Forester/')}
            dedicated={k:v for k,v in values.items()if k.startswith('Vehicles/DefForester/')}
            for k,v in donor.items():
                nk=k.replace('Vehicles/Forester/','Vehicles/DefForester/',1);expected={**v,'Name':nk}
                if dedicated.get(nk)!=expected:raise ValueError('Retail clone field differs: '+k)
            if len(dedicated)!=len(donor)or any(k.startswith('Vehicles/Tyres/DefForesterTyre')for k in values):raise ValueError('Demo physics leaked into corrected package')
            counts[name]=len(dedicated)
        identity=restoration_report['identity'];mini=identity['original_mini_icon']
        source_icon=Path(mini['path']).read_bytes()
        if hashlib.sha256(source_icon).hexdigest()!=mini['sha256']:raise ValueError('Original mini icon changed')
        bank=parse_bank((new/'DataGx/Frontend/RaceResults/smallcarsheet.dxb').read_bytes());icon=new/('DataGx/Frontend/RaceResults/'+bank['names'][-1]+'.dxt')
        if decode_rgba_pixels(parse_dxt_bytes(icon.read_bytes()))!=decode_rgba_pixels(parse_dxt_bytes(source_icon)):raise ValueError('Original mini icon pixels changed')
        from master_rallye.frontend_presentation import align_complete_rest_frame,measure
        baseline=restoration/'author/native-import';original_resources={n:compatible_model((baseline/n).read_bytes(),n)[0]for n in ('car.dx','complete.dx','wheel.dx')}
        reference={n:(retail/('DataGx/Vehicles/Forester/'+n)).read_bytes()for n in original_resources}
        expected_complete,frame=align_complete_rest_frame(original_resources,reference)
        if expected_complete!=(target/'complete.dx').read_bytes():raise ValueError('Frontend-only rebase differs from measured reference')
        for path,digest in restoration_report['source_pins'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('Immutable canonical input changed')
        result['owner_corrections']={'retail_clone_fields':counts,'mini_source':mini,'mini_native_rgba_exact':True,'frontend_frame':frame,
            'frontend_before':measure(original_resources['complete.dx']),'frontend_after':measure(expected_complete),'frontend_reference':measure(reference['complete.dx']),
            'original_input_pins_verified':len(restoration_report['source_pins']),'driver_identity':'Owner confirmed Darren Sutherland in race; unchanged',
            'boundary':'Corrected lamp/tyre wear/mini/menu D3D8 retest pending; no race-completion claim'}
    if emulate:
        from validate_sdk_capacity_emulation import validate as validate_emission
        context=derive(config);original_exe=Path(config.get('retail_exe',ROOT.parent/'MRallye.exe')).read_bytes()
        result['emulation']=validate_emission(original_exe,context['image'],context['capacity'],context['rows'],shared_payload=(0x10000000,(first/'runtime/native-extension.bin').read_bytes()))
    if repeat:
        workshop=WorkshopProject(restoration/'workshop');workshop.build(restoration/'workshop/builds/repeat',sdk_root=ROOT,log=print)
        second=restoration/'workshop/builds/repeat/candidate/runtime/resource-root';manifest=json.loads((first/'runtime/resource-manifest.json').read_text());changed=[]
        for row in manifest['resources']:
            if row['path'].lower().endswith(('.dx','.dxt'))and(new/row['path']).read_bytes()!=(second/row['path']).read_bytes():changed.append(row['path'])
        if changed:raise ValueError('Nondeterministic native model/texture output')
        result['determinism']={'native_dx_dxt_files':sum(r['path'].lower().endswith(('.dx','.dxt'))for r in manifest['resources']),'different':changed,'scope':'Two actual Workshop builds; provenance paths may differ, native rendering resources must not.'}
    output.write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('restoration','accepted-config','retail','output'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--repeat',action='store_true');p.add_argument('--emulate',action='store_true');a=p.parse_args();r=run(a.restoration,a.accepted_config,a.retail,a.output,repeat=a.repeat,emulate=a.emulate);print(r['status'])
