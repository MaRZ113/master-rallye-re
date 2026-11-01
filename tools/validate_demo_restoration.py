"""Reproduce a manifest restoration; independently protect the prior roster."""
from pathlib import Path
import argparse,json,hashlib,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.demo_restoration import verify_inputs,off_geometry
from master_rallye.addon_sdk.heritage_source import compatible_model,verify_author
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank
from master_rallye.preview_scene import presentation_wheels
from master_rallye.dx import parse_dx_bytes
from master_rallye.workshop.service import WorkshopProject
from validate_sdk_roster import validate
from build_sdk_roster import derive
import prepare_sdk_capacity_probe as probe
sha=lambda b:hashlib.sha256(b).hexdigest()


def run(restoration,roots,previous,output,*,repeat=False,emulate=False):
    if output.exists():raise ValueError('Choose a fresh validation report')
    m=json.loads((restoration/'restoration-manifest.json').read_text());source,inputs,pins,evidence=verify_inputs(m,roots);verify_author(restoration/'author')
    candidate=restoration/'workshop/builds/first/candidate';config=json.loads((candidate/'roster-config.json').read_text());result=validate(config,candidate)
    old=derive(json.loads(previous.read_text()));new=candidate/'runtime/resource-root';shared={'DataGame/vehicles.xml','DataGame/Modifications.xml','DataScene/FrontendScreens/VehicleSelect.xml',*(p+'.dxb'for p,_,_,_ in BANKS.values())}
    kept=[]
    for path,value in old['resources'].items():
        if path in shared:continue
        if probe.value(value)!=(new/path).read_bytes():raise ValueError('Previously accepted resource changed: '+path)
        kept.append(path)
    old_values={}
    for name in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        rows=lambda raw:{v.get('Name'):dict(v.attrib)for v in ET.fromstring(raw).iter('Value')}
        a,b=rows(probe.value(old['resources'][name])),rows((new/name).read_bytes())
        if any(b.get(k)!=v for k,v in a.items()):raise ValueError('Prior physics row changed')
        old_values[name]=len(a)
    for prefix,_,_,_ in BANKS.values():
        a=parse_bank(probe.value(old['resources'][prefix+'.dxb']));b=parse_bank((new/(prefix+'.dxb')).read_bytes())
        if a['records']!=b['records'][:a['count']]:raise ValueError('Existing UI bank records changed')
    target=new/('DataGx/Vehicles/'+m['runtime_family']);original=compatible_model((restoration/'author/native-import/car.dx').read_bytes(),'original source')[0]
    a,b=off_geometry(original),off_geometry((target/'car.dx').read_bytes())
    for key in ('surface_sha256','uv_surface_sha256','normal_color_surface_sha256','material_surface_sha256'):
        if a[key]!=b[key]:raise ValueError('Original intact source surface changed: '+key)
    models=[parse_dx_bytes((target/n).read_bytes())for n in ('car.dx','complete.dx','wheel.dx')]
    wheels=presentation_wheels(*models,diagnostics=True)
    result.update(manifest_id=m['id'],original_source_pins=len(pins),accepted_resource_count=len(kept),accepted_physics_rows=old_values,original_off_geometry=a,derived_off_geometry=b,wheels=wheels,
                  source_physics=json.loads((restoration/'physics-preservation.json').read_text()),identity=json.loads((restoration/'identity-evidence.json').read_text()),owner_gameplay='PENDING')
    if emulate:
        sys.path.insert(0,str(ROOT/'.research-output/vehicles/v-def1/python-deps'))
        from validate_sdk_capacity_emulation import validate as emulation
        context=derive(config);result['native_emulation']=emulation(Path(config.get('retail_exe',ROOT.parent/'MRallye.exe')).read_bytes(),context['image'],context['capacity'],context['rows'],shared_payload=(0x10000000,(candidate/'runtime/native-extension.bin').read_bytes()))
    if repeat:
        project=WorkshopProject(restoration/'workshop');project.build(restoration/'workshop/builds/repeat',sdk_root=ROOT,log=print)
        second=restoration/'workshop/builds/repeat/candidate/runtime/resource-root';manifest=json.loads((candidate/'runtime/resource-manifest.json').read_text());files=[r['path']for r in manifest['resources']if r['path'].lower().endswith(('.dx','.dxt'))]
        if any((new/p).read_bytes()!=(second/p).read_bytes()for p in files):raise ValueError('Native resources are nondeterministic')
        result['determinism']={'identical_dx_dxt':len(files),'different':[],'builds':2}
    output.write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('restoration','roots','previous','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--repeat',action='store_true');p.add_argument('--emulate',action='store_true');a=p.parse_args()
    print(run(a.restoration,json.loads(a.roots.read_text()),a.previous,a.output,repeat=a.repeat,emulate=a.emulate)['status'])
