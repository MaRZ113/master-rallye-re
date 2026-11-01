"""Bounded SeatBuggy/Megane livery evidence; no original files are written."""
from pathlib import Path
import argparse
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.setup_sources import ps2_model, public_model, compare_native_atlas
from master_rallye.addon_sdk.vehicle_setup import digest
from master_rallye.dx import parse_dx_bytes
from build_vehicle_setup_pilot import uv_witness


def audit(upstream,ps2_root,ps2_assets,retail,output):
    output=Path(output).resolve()
    if output.exists() or not output.is_relative_to((ROOT/'.research-output/vehicles/v-set1').resolve()):
        raise ValueError('Select a fresh private V-SET1 report directory')
    tool=Path(upstream).parent/'tools/tngtool.py'
    spec=importlib.util.spec_from_file_location('qualified_packfs',tool);packfs=importlib.util.module_from_spec(spec);spec.loader.exec_module(packfs)
    directory,compressed=packfs.load_pak(Path(ps2_root)/'TNG.PAK')
    catalog=json.loads((ROOT/'.research-output/vehicles/demo-audit/final/catalog.json').read_text())
    result={'schema':'v-set1-source-audit/1','packfs_tool_sha256':digest(tool.read_bytes()),
            'pak_sha256':digest((Path(ps2_root)/'TNG.PAK').read_bytes()),'families':{},
            'historical_audit_sha256':digest((ROOT/'.research-output/vehicles/demo-audit/final/catalog.json').read_bytes())}
    for family in ('SeatBuggy','megane'):
        original_entries=[]
        for entry in directory['entries']:
            if entry.get('offset') is None or ('\\'+family.upper()+'\\') not in entry['path'].upper():
                continue
            raw,report=packfs.read_payload(entry,Path(ps2_root)/'TNG.000',max_output=32*1024*1024)
            original_entries.append({'path':entry['path'],'offset':entry['offset'],'stored_size':entry['stored_size'],
                                     'decoded_size':len(raw),'sha256':digest(raw)})
        source_raw=(Path(ps2_assets)/(family.upper()+'-CAR-FLEET.ps2model')).read_bytes();source=ps2_model(source_raw)
        raw_car=[r for r in original_entries if r['path'].upper().endswith('\\'+family.upper()+'\\CAR.PSM')]
        if len(raw_car)!=1 or raw_car[0]['sha256']!=source['original_source_sha256']:
            raise ValueError('Private source assembly differs from original selected PSM')
        native_folder=Path(retail)/'DataGx/Vehicles'/family
        native_raw=(native_folder/'car.dx').read_bytes();native=parse_dx_bytes(native_raw)
        atlas=compare_native_atlas(source,{p.name.lower():p.read_bytes() for p in native_folder.glob('*.dxt')})
        paint=[]
        for texture in source['textures']:
            name=(texture['source'] or {}).get('path','').replace('\\','/').split('/')[-1].lower()
            if name in ('seat07-tga.gxi','seat02-tga.gxi','seat06-tga.gxi','sblogo128-tga.gxi','sdoors128-tga.gxi','rplogo64-tga.gxi','logostrip64-tga.gxi'):
                paint.append(uv_witness(source_raw,source,native,texture['index']))
        historical=[]
        for row in catalog['families']:
            if row['family'].lower()==family.lower() and row['label'] in ('shipped841','shipped931','shipped910','pcg-rebaked','nov-local'):
                historical.append({'id':row['id'],'source_models':{k:{a:v for a,v in m.items() if a in ('sha256','vertices','triangles','surface_sha256','position_cloud_sha256','format')} for k,m in row['models'].items() if k in ('car.dx','car.gxm')},
                                   'evidence':'Previous complete audit, retained as historical evidence; selected native/PS2 inputs re-read in this report'})
        result['families'][family]={'original_ps2_members':original_entries,'selected_ps2_source':public_model(source),
                                   'retail_car_sha256':digest(native_raw),'atlas_candidates':atlas,'uv_witnesses':paint,
                                   'historical_models':historical,'demo931':'MISSING INPUT for Megane in inventoried 9.3.1 sources' if family=='megane' else 'See complete demo audit',
                                   'runtime_livery_selection':'NOT_TESTED','geometry_parity':'Not inferred from material names or UV point coverage'}
    output.mkdir(parents=True);(output/'source-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('upstream','ps2-root','ps2-assets','retail','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();audit(a.upstream,a.ps2_root,a.ps2_assets,a.retail,a.output)
