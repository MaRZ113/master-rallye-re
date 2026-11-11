"""Validate the private EXTRA-SET1 collection without installing anything."""
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from build_extra_options_candidate import ROOT,SDK,BASE,GAME,sha
from audit_dinput8_exports import audit


def validate(delivery,build):
    delivery,build=Path(delivery),Path(build)
    bundle=delivery/'runtime';host=delivery/'host'
    rows=json.loads((bundle/'resource-manifest.json').read_text())['resources']
    for row in rows:
        path=bundle/'resource-root'/row['path']
        if path.stat().st_size!=row['size'] or sha(path)!=row['sha256']:raise ValueError('resource changed: '+row['path'])
    for name in ['addon-plan.json','native-patch-manifest.json','native-patch-ops.rvp','native-extension.bin']:
        if (bundle/name).read_bytes()!=(BASE/'runtime'/name).read_bytes():raise ValueError('accepted registry/code changed: '+name)
    accepted=json.loads((BASE/'runtime/resource-manifest.json').read_text())['resources']
    unchanged=[]
    for row in accepted:
        if row['path'].casefold()=='datagame/options.xml':continue
        path=bundle/'resource-root'/row['path']
        if sha(path)!=row['sha256']:raise ValueError('accepted asset changed: '+row['path'])
        unchanged.append(row['path'])
    baseline=json.loads((ROOT/'.research-output/extra-set1/integrated-baseline/manifest.json').read_text())
    protected=[]
    for name,item in baseline.items():
        if Path(name).is_absolute():
            if sha(name)!=item['sha256']:raise ValueError('installed file changed: '+name)
            protected.append(name)
    if (host/'MRallyeRandomizer.ini').read_bytes()!=(GAME/'MRallyeRandomizer.ini').read_bytes():raise ValueError('legacy INI changed')
    for name,source in [('dinput8.dll',build/'proxy/dinput8.dll'),('d3d8.dll',build/'d3d8.dll'),('MRallyeRandomizerRuntime.dll',build/'core/MRallyeRandomizerRuntime.dll')]:
        if sha(host/name)!=sha(source):raise ValueError('staged binary differs: '+name)
    exports=audit(host/'dinput8.dll')
    if not exports['required_match'] or exports['observed'].get('MRExtraOptionsAbi')!=8:raise ValueError('native interface export mismatch')
    sys.path.insert(0,str(SDK/'tools'))
    from extra_options_resources import native_setup_page
    page=(bundle/'resource-root/DataScene/FrontendScreens/VehicleSetup4.xml').read_bytes()
    original=(GAME/'Data.sma_unpacked/DataScene/FrontendScreens/VehicleSetup4.xml').read_bytes()
    if page!=native_setup_page(original):raise ValueError('native page is stale')
    tree=ET.parse(bundle/'resource-root/DataGame/vehicles.xml')
    values={v.get('Name'):v for v in tree.findall('./Broker/Value')}
    tires={}
    fields=['PeakMu','SoftRating','IceRating','WetRating','ScaleFactor','CorneringCoeff','CorneringCoeffGradient','PneumaticTrailCoeff','CamberStiffness','LongitudinalStiffness','InflationStiffness','InflationStiffnessDamping']
    for family in ['tarmac','harddirt','gravel','grass','mud']:
        records=[]
        for surface in range(5):
            record={}
            for field in fields:
                entry=values['Vehicles/Tyres/%s%d/%s'%(family,surface,field)]
                if entry.get('Type')!='Float':raise ValueError('tire coefficient type changed')
                record[field]=entry.get('Value')
            records.append(record)
        tires[family]={'records':5,'fields_per_record':12,'sha256':hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()}
    from build_extra_options_candidate import package_header
    _,previous,_=package_header()
    prepared=json.loads((previous/'preparation.json').read_text())
    textures=[]
    for binding in prepared['livery_bindings']:
        a=(host/binding['base_path']).read_bytes();b=(host/binding['alternate_path']).read_bytes()
        if len(a)!=binding['width']*binding['height']*4 or len(b)!=len(a) or a[3::4]!=b[3::4]:raise ValueError('livery channel/size mismatch')
        textures.append({'index':binding['index'],'original_sha256':hashlib.sha256(a).hexdigest(),'derived_sha256':hashlib.sha256(b).hexdigest(),
                         'alpha_unchanged':True,'changed_pixels':sum(a[i:i+4]!=b[i:i+4] for i in range(0,len(a),4))})
    report={'schema':'extra-set1-validation/1','status':'PASS_OFFLINE_CANDIDATE','owner_gameplay':'PENDING',
            'resource_count':len(rows),'accepted_resources_unchanged':len(unchanged),'accepted_registry_and_extension':'EXACT',
            'installed_files_unchanged':protected,'legacy_ini':'BYTE_IDENTICAL','tires':tires,'texture_uploads':textures,
            'native_page_sha256':hashlib.sha256(page).hexdigest(),'files':{n:sha(host/n) for n in ['MRallye.exe','dinput8.dll','d3d8.dll','MRallyeRandomizerRuntime.dll']},
            'source_files':{n:sha(ROOT/n) for n in ['src/native/rmod1/core.hpp','src/native/rmod1/runtime_core.cpp','src/native/rmod1/rmod2_inprocess.cpp','src/native/rmod1/dinput8_proxy.cpp','src/native/rmod1/extra_options_runtime.cpp','src/native/rmod1/extra_options_graphics.hpp']}}
    (delivery/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--delivery',type=Path,required=True);p.add_argument('--build',type=Path,required=True)
    a=p.parse_args();r=validate(a.delivery,a.build);print(r['status'],r['resource_count'],'resources;',r['accepted_resources_unchanged'],'accepted resources preserved')
