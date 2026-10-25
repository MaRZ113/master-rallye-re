"""Launch or stage a real MR vehicle for the standalone fixed-function viewer."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import os
import json
import math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye.preview_scene import stage_vehicle

def audio_rev_limit(fields=None,override=None):
    value=override if override is not None else float(fields['Engine/RevLimit']['value']) if fields else 7000
    if not math.isfinite(value) or not 500<=value<=20000:raise ValueError('audio preview rev limit outside 500..20000 guard')
    return round(value)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path,help='car.dx, complete.dx, wheel.dx or another converted DX')
    p.add_argument('--output',type=Path,default=ROOT/f'.research-output/vehicles/previewer/cache/{os.getpid()}.mrpv')
    p.add_argument('--profile',type=Path)
    p.add_argument('--mechanics-profile',type=Path,help='source-pinned selected mechanical draws; red source / green target hub diagnostic overlay')
    p.add_argument('--attachment-build',type=Path,help='SDK author-build with sealed unsprung auxiliary models; requires wheel instance profile or physics XML')
    p.add_argument('--physics-xml',type=Path,help='optional actual generated vehicles.xml; inspect native attachment datum, not settled suspension')
    p.add_argument('--physics-family',help='independent named family in --physics-xml')
    p.add_argument('--physics-profile',type=Path,help='optional SDK reference datum sidecar used with physics XML')
    p.add_argument('--modifications-xml',type=Path,help='initial player setup deltas')
    p.add_argument('--player-state',type=Path,help='read-only saved setup overlay for this diagnostic')
    p.add_argument('--player',type=int,choices=[1,2],default=1)
    p.add_argument('--audio-profile',type=Path,help='optional independent SDK audio profile; opens a separate lightweight native-DSP panel')
    p.add_argument('--audio-source-root',type=Path,help='source project folder for the optional audio panel')
    p.add_argument('--audio-exe',type=Path,default=ROOT.parent/'MRallye.exe',help='exact local original executable for read-only DSP audition')
    p.add_argument('--audio-rev-limit',type=float,help='audition limit override; otherwise use physics XML or editable standalone default7000')
    p.add_argument('--export-only',action='store_true')
    p.add_argument('--resource-diagnostics',type=Path,help='write static DX complexity, native texture dimensions/usage and image-detail risks; not gameplay timings')
    p.add_argument('--viewer',type=Path,default=ROOT/'.research-output/vehicles/previewer/build/Release/mr-vehicle-previewer.exe')
    p.add_argument('--capture',type=Path)
    p.add_argument('--model',choices=['race','frontend','wheel'],default='frontend')
    p.add_argument('--preset',type=int,default=4)
    p.add_argument('--zoom',type=float,default=1.,help='distance multiplier, 0.1 to 5')
    p.add_argument('--azimuth',type=float,help='camera azimuth in degrees')
    p.add_argument('--elevation',type=float,help='camera elevation in degrees')
    p.add_argument('--target',type=float,nargs=3,help='explicit camera look-at XYZ in model units')
    p.add_argument('--cull',choices=['none','cw','ccw'],default='cw',help='CW calibrated for stored-global indices/RH camera; none is an explicit diagnostic')
    p.add_argument('--depth-write',choices=['instance-on','shader'],default='instance-on',help='native instance constructor enables ZWrite; shader-only is a separate diagnostic')
    p.add_argument('--raw-race',action='store_true',help='show car.dx only; keep qualified staged wheels hidden')
    p.add_argument('--brake',action='store_true');p.add_argument('--no-reflections',action='store_true')
    a=p.parse_args()
    if bool(a.audio_profile)!=bool(a.audio_source_root):p.error('--audio-profile and --audio-source-root must be supplied together')
    if bool(a.physics_xml)!=bool(a.physics_family):p.error('--physics-xml and --physics-family must be supplied together')
    if not a.physics_xml and (a.physics_profile or a.modifications_xml or a.player_state):p.error('physics setup inputs require --physics-xml and --physics-family')
    if a.physics_xml:
        if a.profile:p.error('choose explicit wheel profile or physics XML, not both')
        from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes
        from master_rallye.addon_sdk.physics_model import wheel_attachments,effective_setup,suspension_summary
        fields=parse_vehicle_config_bytes(a.physics_xml.read_bytes(),build='retail-2001-verified').families.get(a.physics_family)
        if fields is None:p.error('named physics family is absent')
        definition=json.loads(a.physics_profile.read_text()) if a.physics_profile else {}
        modifications=parse_vehicle_config_bytes(a.modifications_xml.read_bytes(),build='retail-2001-verified').families[a.physics_family] if a.modifications_xml else {}
        from vehicle_physics_native import runtime_reference
        fields,setup=effective_setup(fields,modifications,family=a.physics_family,player=a.player,saved_state=a.player_state.read_bytes() if a.player_state else None,reference=runtime_reference(definition))
        setup['reference_binding']=definition.get('ride_height_reference_binding','legacy_inactive_or_absent')
        a.output.parent.mkdir(parents=True,exist_ok=True);a.profile=a.output.with_suffix('.physics.json')
        a.profile.write_text(json.dumps(wheel_attachments(fields),indent=2)+'\n')
        a.output.with_suffix('.setup.json').write_text(json.dumps({'effective_setup':setup,'suspension_force_diagnostic':suspension_summary(fields)},indent=2)+'\n')
    if a.attachment_build:
        if not a.profile:p.error('--attachment-build requires explicit wheel profile or physics XML')
        import hashlib
        built=json.loads((a.attachment_build/'build-manifest.json').read_text())['authoring_project']['mechanical_attachments']
        config=json.loads(a.profile.read_text());groups=built['resources']['groups']
        car=a.source.parent/'car.dx'
        if hashlib.sha256(car.read_bytes()).hexdigest()!=built['resources']['body_sha256']:p.error('attachment body source differs from build provenance')
        config['attached_models']=[]
        for index,group in enumerate(groups):
            if hashlib.sha256((a.source.parent/group['resource']).read_bytes()).hexdigest()!=group['output_sha256']:p.error('attachment source differs from build provenance')
            config['attached_models'].append({'resource':group['resource'],'wheel_index':index})
        a.profile=a.output.with_suffix('.attachments.json');a.profile.parent.mkdir(parents=True,exist_ok=True)
        a.profile.write_text(json.dumps(config,indent=2)+'\n')
    if a.mechanics_profile:
        config=json.loads(a.profile.read_text()) if a.profile else {}
        config['mechanical_debug']=json.loads(a.mechanics_profile.read_text())
        a.profile=a.output.with_suffix('.mechanics.json');a.profile.parent.mkdir(parents=True,exist_ok=True)
        a.profile.write_text(json.dumps(config,indent=2)+'\n')
    report=stage_vehicle(a.source,a.output,profile=a.profile)
    if a.resource_diagnostics:
        from diagnose_vehicle_resources import diagnose
        diagnostic=diagnose(a.source.parent)
        a.resource_diagnostics.parent.mkdir(parents=True,exist_ok=True)
        a.resource_diagnostics.write_text(json.dumps(diagnostic,indent=2)+'\n')
    if a.audio_profile and not a.export_only:
        limit=audio_rev_limit(fields if a.physics_xml else None,a.audio_rev_limit)
        subprocess.Popen([sys.executable,str(ROOT/'tools/vehicle_audio_preview.py'),'--profile',str(a.audio_profile.resolve()),'--source-root',str(a.audio_source_root.resolve()),'--exe',str(a.audio_exe.resolve()),'--rev-limit',str(limit)],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    residency=report['native_texture_residency']
    if residency['warning']:
        print(f"WARNING: vehicle textures charge {residency['family_cache_bytes']} bytes against the retail 32 MiB cache; "
              'exceeds the SDK 16 MiB authoring budget. A fast preview does not prove native MR performance.',flush=True)
    if not a.export_only:
        command=[str(a.viewer),'--scene',str(a.output.resolve()),'--source',str(a.source.resolve()),'--python',sys.executable,
                 '--exporter',str(Path(__file__).resolve()),'--model',a.model,'--preset',str(a.preset),'--cull',a.cull,'--depth-write',a.depth_write]
        command+=['--zoom',str(a.zoom)]
        if a.azimuth is not None:command+=['--azimuth',str(a.azimuth)]
        if a.elevation is not None:command+=['--elevation',str(a.elevation)]
        if a.target is not None:command+=['--target',*(str(x) for x in a.target)]
        if a.profile:command+=['--profile',str(a.profile.resolve())]
        if a.capture:command+=['--capture',str(a.capture.resolve())]
        if a.brake:command+=['--brake']
        if a.raw_race:command+=['--raw-race']
        if a.no_reflections:command+=['--no-reflections']
        subprocess.run(command,check=True)
    print(f'{report["draws"]} draws / {report["textures"]} textures: {a.output}')

if __name__=='__main__':main()
