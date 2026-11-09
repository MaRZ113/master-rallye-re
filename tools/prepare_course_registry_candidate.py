"""Reproduce the two-route COURSE-CAP2 candidate from accepted private inputs."""
import argparse
import json
from pathlib import Path
from build_course_registry import ROOT,build,encoded
from course_capacity_audit import extract,catalog_from_resources


def prepare(vehicle_source,vehicle_runtime,retail_exe,output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'.research-output/course-cap2').resolve()) or output.exists():
        raise ValueError('Fresh private COURSE-CAP2 output required')
    output.mkdir(parents=True)
    base=Path(vehicle_runtime).resolve();exe=Path(retail_exe).resolve()
    rows,_=extract(exe.read_bytes())
    catalog,missing=catalog_from_resources(rows,base/'resource-root')
    if missing:raise ValueError('Accepted parent lacks original Course dependencies')
    catalog['vehicle_count']=json.loads((base/'runtime-profile.json').read_text())['capacity_profile']['record_count']
    catalog['runtime_budget']={'max_shared_bytes':65536}
    for ident,name,spacing in [(39,'CapFranceTour',20.0),(40,'CapFranceTourFine',15.0)]:
        row=json.loads(json.dumps(catalog['races'][0]));row['id']=ident;row['native_fields'][0]=ident
        row.update(scene='DataScene/RaceTest/'+name+'.xml',icont='DataScene/ICont/'+name.lower()+'.sfl',
                   title='France - '+('Registry Tour' if ident==39 else 'Tour Fine'),modes=['QuickRace'],
                   progress_key=name.lower(),menu={'group':0,'position':ident-36,'flag_frame':0,'screenshot_pair':0},
                   prepare_variant={'source_scene':rows[0]['scene'],'source_icont':catalog['races'][0]['icont'],'marker_spacing':spacing})
        catalog['races'].append(row)
    # Demonstrates an independent explicit schedule contract, currently not
    # surfaced in the native competition UI or admitted as a playable Cup.
    catalog['competitions']=[{'key':'course-cap2-tour','progress_key':'course-cap2-tour-v1',
                              'races':[40,39],'runtime_enabled':False}]
    manifest=output/'courses.json';manifest.write_bytes(encoded(catalog))
    config={'vehicle_source':str(Path(vehicle_source).resolve()),'vehicle_runtime':str(base),
            'vehicle_manifest':str(base.parent/'registry-build.json'),'retail_exe':str(exe),'course_manifest':str(manifest)}
    (output/'compose.json').write_bytes(encoded(config))
    return build(config,output/'candidate')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['vehicle-source','vehicle-runtime','retail-exe','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.vehicle_source,a.vehicle_runtime,a.retail_exe,a.output),indent=2))
