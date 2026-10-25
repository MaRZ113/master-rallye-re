"""Source ownership, exact native switch replay and comparative GPU diagnostics.

All MR inputs are supplied locally. No game assets are bundled or changed.
"""
import argparse,collections,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.preview_scene import stage_vehicle,presentation_wheels
from inspect_vehicle_glass import audit
from replay_glass_switch import replay
from validate_vehicle_damage_native import execute


def fingerprints(geometry):
    return collections.Counter(tuple((geometry.vertices[v].position,geometry.vertices[v].normal,geometry.vertices[v].color,geometry.vertices[v].uvs) for v in tri) for tri in geometry.triangles)


def validate(before,after,profile,exe):
    a,b=map(parse_dx_bytes,(before,after));ga,gb=map(source_geometry,(a,b))
    expected=fingerprints(ga[profile['source_draw']]);actual=collections.Counter()
    for index in [profile['static']['draw']]+[p['intact_draw'] for p in profile['panes']]:actual.update(fingerprints(gb[index]))
    if actual!=expected:raise ValueError('Intact triangle/UV/color/normal/material geometry changed')
    if before[a.trailing.offset:]!=after[b.trailing.offset:]:raise ValueError('Collision/suffix changed')
    for index in [profile['static']['draw']]+[p['intact_draw'] for p in profile['panes']]:
        d=b.physical_draws[index];source=a.physical_draws[profile['source_draw']]
        if (d.texture_tuple,d.flags_0x20,d.unknown_0x24)!=(source.texture_tuple,source.flags_0x20,source.unknown_0x24):raise ValueError('Intact material semantics changed')
    # Native vertex deformer replay, without inventing a new bridge for Subaru.
    impacts=[{'point':[0.,1.,.9],'direction':[.2,-.1,-.5],'speed':8.,'scale':1.}]*3
    left=execute(exe,before,impacts,adapted=False);right=execute(exe,after,impacts,adapted=False)
    def positions_by_origin(model,state):
        result={}
        for old,new in zip(model.vertices.positions,struct.iter_unpack('<3f',state['positions'])):
            if old in result and result[old]!=new:raise ValueError('Native coincident vertices split')
            result[old]=new
        return result
    x,y=positions_by_origin(a,left),positions_by_origin(b,right)
    if any(x[p]!=y[p] for p in x.keys()&y.keys()):raise ValueError('Native deformation changed at a preserved position')
    return {'intact_attribute_triangle_multiset_identical':True,'intact_material_flags_and_bindings_identical':True,'collision_suffix_byte_identical':True,'original_native_deformation_matches_preserved_positions':True,'native_switch':replay(exe),'boundary':'synthetic impacts and controller arrays, actual original x86 instructions; not gameplay'}


def validate_uv_continuation(before,after,profile,exe):
    from master_rallye.glass_authoring import remap_broken_uv
    expected,audit=remap_broken_uv(before,profile)
    if expected!=after:raise ValueError('UV-only candidate does not reproduce')
    a,b=map(parse_dx_bytes,(before,after))
    if a.vertices!=b.vertices or a.local_indices!=b.local_indices or a.physical_draws!=b.physical_draws or before[a.trailing.offset:]!=after[b.trailing.offset:]:raise ValueError('UV-only continuation changed geometry/material/controls/collision')
    impacts=[{'point':[0.,1.,.9],'direction':[.2,-.1,-.5],'speed':8.,'scale':1.}]*3
    left=execute(exe,before,impacts,adapted=False);right=execute(exe,after,impacts,adapted=False)
    if left['positions']!=right['positions']:raise ValueError('Native deformation changed')
    return {'uv_only_audit':audit,'intact_materials_geometry_and_native_switches_identical':True,'native_deformation_byte_identical':True,'native_switch':replay(exe),'boundary':'original x86 CPU replay with synthetic input; actual collision trigger classification needs gameplay'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','stock','imported','profile','exe','viewer','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--imported-preview-profile',type=Path)
    p.add_argument('--uv-only',action='store_true',help='Continue from an already repaired source, changing broken UVs only')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);profile=json.loads(a.profile.read_text())
    report=(validate_uv_continuation if a.uv_only else validate)((a.before/'car.dx').read_bytes(),(a.after/'car.dx').read_bytes(),profile,a.exe.read_bytes());report['captures']=[];report['families']={}
    for label,family in [('Subaru-before',a.before),('Subaru-after',a.after),('Stock',a.stock),('Imported',a.imported)]:
        raw=(family/'car.dx').read_bytes();e=audit(raw);report['families'][label]=e
        try:config=presentation_wheels(*(parse_dx_bytes((family/n).read_bytes()) for n in ('car.dx','complete.dx','wheel.dx')))
        except ValueError:
            config=json.loads(a.imported_preview_profile.read_text()) if label=='Imported' and a.imported_preview_profile else {'provenance':'No qualified wheel assembly; raw body diagnosis only'}
        states=[{}]+([{pane['label']:2} for pane in profile['panes'] if any(g['label']==pane['label'] for g in e['glass_switches'])])
        for index,state in enumerate(states):
            selected={**config,'glass_states':state};pr=a.output/f'{label}-{index}.profile.json';pr.write_text(json.dumps(selected));scene=a.output/f'{label}-{index}.mrpv';stage_vehicle(family/'car.dx',scene,profile=pr)
            for preset in (1,4):
                for env in (True,False):
                    capture=a.output/f'{label}-{index}-{preset}-{"env" if env else "noenv"}.bmp'
                    command=[str(a.viewer.resolve()),'--scene',str(scene.resolve()),'--model','race','--preset',str(preset),'--capture',str(capture.resolve())]
                    if not env:command+=['--no-reflections']
                    subprocess.run(command,check=True,timeout=30);report['captures'].append(capture.name)
    report['status']='PASS_OFFLINE_GLASS_OWNERSHIP_NATIVE_CPU_AND_GPU';report['runtime_qualified']=False
    (a.output/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(report['captures']))

if __name__=='__main__':main()
