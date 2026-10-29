"""Owner-source validation of isolation, UV/pixel conservation and rollback."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.pajero_livery_forensics import OverlayHistory,badge_experiment,file_hash
from master_rallye.source_scene_preview import stage_source_scene


def validate(source,experiment,family,output):
    from PIL import Image,ImageDraw
    source,experiment,family=map(lambda p:Path(p).absolute(),(source,experiment,family))
    output=u.output_directory(Path(output).absolute(),[source.parent,experiment,family])
    if output.exists():raise ValueError('Fresh validation output required')
    original=u.load_scene(source);c=u.load_scene(experiment/'C/scene/scene.json')
    assert original['meshes']==c['meshes'];assert original['nodes']==c['nodes'];assert original['textures']==c['textures'][:-1]
    changes=[]
    for old,new in zip(original['materials'],c['materials']):
        if old!=new:
            assert old['id']=='node-000-sub-01';copy=dict(new);copy['diffuse_texture_id']=old['diffuse_texture_id'];assert copy==old;changes.append(old['id'])
    assert changes==['node-000-sub-01']
    for name in json.loads((source.parent/'manifest.json').read_text())['files']:
        if name=='scene.json':continue
        assert (source.parent/name).read_bytes()==(experiment/'C/scene'/name).read_bytes()
    original_tex=next(t for t in original['textures']if t['id']=='xtx-046');derived=c['textures'][-1]
    a=(source.parent/original_tex['rgba_path']).read_bytes();b=(experiment/'C/scene'/derived['rgba_path']).read_bytes();assert a[3::4]==b[3::4]
    changed={i for i in range(256*256)if a[i*4:i*4+4]!=b[i*4:i*4+4]}
    allowed={y*256+x for left,top,right,bottom in c['metadata']['livery_experiment']['atlas_rectangles']for y in range(top,bottom)for x in range(left,right)}
    assert changed and changed<=allowed
    output.mkdir(parents=True);history=OverlayHistory();history.apply(True)
    repeated=badge_experiment(source,output/'repeat-C',family,history)
    assert file_hash(experiment/'C/scene/scene.json')==repeated['scene_sha256']
    history.undo();assert not history.enabled
    restored=badge_experiment(source,output/'undo-A',family,history);s=u.load_scene(output/'undo-A/scene.json')
    stage_source_scene(s,output/'restored.mrpv',scene_root=output/'undo-A')
    assert (output/'restored.mrpv').read_bytes()==(experiment/'A/preview.mrpv').read_bytes()
    history.redo();assert history.enabled;redo=badge_experiment(source,output/'redo-C',family,history);assert redo['scene_sha256']==repeated['scene_sha256']
    history.restore();assert not history.enabled;history.save(output/'history.json');assert not OverlayHistory.load(output/'history.json').enabled
    mesh=next(m for m in c['meshes']if m['id']=='node-000-sub-01');coverage=[]
    for ordinal,tri in enumerate(mesh['triangles']):
        mask=Image.new('1',(256,256));draw=ImageDraw.Draw(mask);draw.polygon([(mesh['uvs'][i][0]*256,mesh['uvs'][i][1]*256)for i in tri],fill=1)
        count=sum(bool(mask.getpixel((i%256,i//256)))for i in changed)
        if count:coverage.append({'triangle':ordinal,'raster_patch_samples':count})
    report={'schema':'lost-pajero-validation/1','status':'PASS','original_geometry_uv_normals_nodes_exact':True,
        'original_texture_sidecars_exact':True,'original_alpha_exact':True,'material_changes':changes,'changed_rgb_pixels':len(changed),
        'allowed_pixels':len(allowed),'selected_mesh_raster_coverage':coverage,'original_triangles':sum(len(m['triangles'])for m in c['meshes']),
        'restore_mrpv_matches_A_exactly':True,'deterministic_C':True,'undo_redo_restore_reopen':True,
        'direct_B':'UNSUPPORTED','C':'PARTIAL_BADGE_ONLY_NOT_FULL_RED_LIVERY','native_candidate':'NOT CREATED','l2':'WARN'}
    (output/'validation.json').write_bytes(u.canonical(report));print({k:v for k,v in report.items()if k!='selected_mesh_raster_coverage'});return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','experiment','family','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();validate(a.source,a.experiment,a.family,a.output)
