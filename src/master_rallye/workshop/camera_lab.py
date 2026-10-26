"""Shared read-only native camera inputs and bounded static preview export."""
import copy,json,shutil
from pathlib import Path
from master_rallye.game_camera import follow_preset,static_pose


class CameraLabAuthoring:
    def camera_lab_inspect(self,preset=0,split=False):
        from master_rallye.addon_sdk.project import read_sma_member
        from .service import sha
        info=self.camera_inspect();settings=self.data['build_settings']
        # Reuse the existing original-retail authority check for addon inputs.
        if self.data['kind']=='addon':self._retail_members()
        raw=read_sma_member(Path(settings['retail_sma']),'DataGame/Cameras.xml')
        params=follow_preset(raw,preset,split)
        donor=(self.vehicle_defaults()['camera']or{}).get('follow_extents',info['original'])
        poses={key:static_pose(extents,params)for key,extents in [('original',info['original']),('donor',donor),('modified',info['current'])]}
        return {'identity':info,'preset':preset,'split':split,'parameters_read_only':params,'camera_xml_sha256':sha(raw),'poses':poses,'qualified':'Source follow parameters and original bounds; only per-CarID half-length/height extents editable through the existing guarded adapter.','approximate':'Static upright first-update pose is CPU-replayed; acceleration, pitch response, terrain, history/smoothing and final D3D8 projection/device presentation are not simulated.','unknown':'Live world target, velocity, helper correction, replay/switch timing and renderer overrides need owner/runtime evidence.'}

    def camera_lab_export(self,*,view='modified',preset=0,split=False,guides=True):
        from .service import write_json,write_resource
        from master_rallye.preview_scene import stage_vehicle
        if view not in ('original','donor','modified')or type(guides)is not bool:raise ValueError('Unknown gameplay preview mode')
        self.materialize();report=self.camera_lab_inspect(preset,split);folder=self.root/'preview/game-camera'/view;folder.mkdir(parents=True,exist_ok=True)
        for f in self.assets.iterdir():
            if f.is_file()and f.suffix.lower()in('.dx','.dxt'):shutil.copyfile(f,folder/f.name)
        write_resource(folder/'car.dx',self.camera_source());profile=copy.deepcopy(self.preview_profile()or{})
        if guides:profile['camera_debug']={key:{field:report['poses'][key][field]for field in ('eye','target','source_fov_degrees')}for key in ('original','modified')}
        write_json(folder/'profile.json',profile);scene=folder/'camera.mrpv';stage_vehicle(folder/'car.dx',scene,profile=folder/'profile.json');write_json(folder/'camera-report.json',report)
        return {'scene':str(scene),'report':report,'pose':report['poses'][view],'source':str(folder/'car.dx')}
