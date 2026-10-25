"""Independent UI-only delta, reference, pixel recomposition and ZIP audit."""
import argparse,json,sys,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank,alpha_bounds
from master_rallye.addon_sdk.ui_preview import compose_preview,PROFILES
from master_rallye.texture_authoring import decode_rgba_png
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from build_vmesh_impreza_experimental import dump,sha_file

def audit(stage,before,accepted_side_from=None):
    with zipfile.ZipFile(before/'review'/(before.name+'-candidate.zip')) as z:
        prefix=before.name+'/runtime/resource-root/';base={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
        manifest=json.loads(z.read(before.name+'/runtime/resource-manifest.json'))
        old_native=z.read(before.name+'/runtime/native-patch-manifest.json')
    current=stage/'runtime/resource-root';actual={p.relative_to(current).as_posix():p for p in current.rglob('*') if p.is_file()}
    if 'Data.sma' not in base:
        pinned=next(r['sha256'] for r in manifest['resources'] if r['path']=='Data.sma')
        if sha_file(actual['Data.sma'])!=pinned:raise ValueError('stock runtime archive changed')
        base['Data.sma']=actual['Data.sma'].read_bytes()
    if set(base)!=set(actual):raise ValueError('resource file set changed')
    changes=sorted(n for n in base if base[n]!=actual[n].read_bytes())
    expected=sorted(prefix+f'_{count:03d}_000.dxt' for prefix,count,template,size in BANKS.values())
    if changes!=expected:raise ValueError('unexpected non-UI delta '+str(changes))
    if (stage/'runtime/native-patch-manifest.json').read_bytes()!=old_native:raise ValueError('native operations changed')
    cfg=json.loads((stage/'project/ui-assets.json').read_text());checks={}
    for role,(prefix,count,template,size) in BANKS.items():
        name=prefix+f'_{count:03d}_000.dxt';new=parse_dxt_bytes(actual[name].read_bytes());old=parse_dxt_bytes(base[name]);bank=parse_bank(actual[prefix+'.dxb'].read_bytes())
        if (new.width,new.height)!=size or new.word_0x08!=zlib.crc32(new.bgra)&0xffffffff:raise ValueError('invalid texture dimensions/CRC')
        if new.header[:8]+new.header[12:]!=old.header[:8]+old.header[12:]:raise ValueError('non-CRC format header changed')
        if bank['names'][count]!=Path(name).stem:raise ValueError('UI bank reference mismatch')
        source=stage/'project'/cfg['icons'][role]['png'];image=decode_rgba_png(source.read_bytes());source_bounds=alpha_bounds(image)
        if min(source_bounds[0],source_bounds[1],image[0]-source_bounds[2],image[1]-source_bounds[3])<8:raise ValueError('source preview touches viewport edge before normalization')
        rgba,detail=compose_preview(image,role)
        if rgba!=decode_rgba_pixels(new):raise ValueError('final pixels differ from SDK normalization')
        bounds=alpha_bounds((*size,rgba))
        if bounds[3]!=PROFILES[role]['baseline']:raise ValueError('ground baseline mismatch')
        if bounds[0]<0 or bounds[1]<0 or bounds[2]>size[0] or bounds[3]>size[1]:raise ValueError('icon clipping')
        checks[role]={'bounds':bounds,'source_alpha_bounds':source_bounds,'source_viewport_guard_valid':True,'dimensions':size,'crc32_valid':True,'sdk_recomposition_exact':True,'presentation':detail}
    candidate=stage/'review'/(stage.name+'-candidate.zip')
    with zipfile.ZipFile(candidate) as z:
        if z.testzip():raise ValueError('ZIP CRC failed')
        for name,path in actual.items():
            if z.read(stage.name+'/runtime/resource-root/'+name)!=path.read_bytes():raise ValueError('ZIP/runtime mismatch')
    result={'status':'PASS_OFFLINE_RUNTIME_TEST_PENDING','resource_count':len(actual),'changed_resources':changes,'all_vehicle_geometry_wheels_physics_byte_identical':True,'native_operations_banks_scenes_byte_identical':True,'roles':checks,'candidate_sha256':sha_file(candidate)}
    if accepted_side_from:
        path='DataGx/Frontend/RaceResults/smallcarsheet_030_000.dxt'
        if (accepted_side_from/'runtime/resource-root'/path).read_bytes()!=actual[path].read_bytes():raise ValueError('accepted side preview changed during camera refinement')
        result['accepted_side_preview_byte_identical_during_camera_refinement']=True
    dump(stage/'reports/final-ui-audit.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--before',type=Path,required=True);p.add_argument('--accepted-side-from',type=Path);a=p.parse_args();print(json.dumps(audit(a.stage,a.before,a.accepted_side_from),indent=2))
