"""Shared read-only native camera inputs and bounded static preview export."""
import copy,json,shutil
from pathlib import Path
from master_rallye.game_camera import follow_preset,static_pose,fixed_preset,fixed_pose,gameplay_mode,GAMEPLAY_MODES


class CameraLabAuthoring:
    def camera_lab_inspect(self,preset=0,split=False,*,mode=None):
        from master_rallye.addon_sdk.project import read_sma_member
        from .service import sha
        info=self.camera_inspect();settings=self.data['build_settings']
        # Reuse the existing original-retail authority check for addon inputs.
        if self.data['kind']=='addon':self._retail_members()
        raw=read_sma_member(Path(settings['retail_sma']),'DataGame/Cameras.xml')
        selected=gameplay_mode(preset if mode is None else mode);preset=selected['index']
        params=(follow_preset if selected['kind']=='follow'else fixed_preset)(raw,preset,split)
        donor=(self.vehicle_defaults()['camera']or{}).get('follow_extents',info['original'])
        key=selected['kind']+str(preset);state=self.vehicle_state()['camera']or{};defaults=self.vehicle_defaults()['camera']or{}
        parameters={view:{**params,**profile.get('mode_overrides',{}).get(key,{})}for view,profile in [('original',{}),('donor',defaults),('modified',state)]}
        if selected['kind']=='follow':poses={key:static_pose(extents,parameters[key])for key,extents in [('original',info['original']),('donor',donor),('modified',info['current'])]}
        else:
            from master_rallye.dx import parse_dx_bytes
            from master_rallye.bounds import parse_bounds1339
            bounds=parse_bounds1339(parse_dx_bytes(self.camera_source()).collision.unparsed_data)
            poses={view:fixed_pose({'minimum':bounds.minimum,'maximum':bounds.maximum},parameters[view])for view in parameters}
        return {'identity':info,'preset':preset,'mode':selected,'modes':GAMEPLAY_MODES,'split':split,'parameters_read_only':params,'parameters':parameters,'camera_xml_sha256':sha(raw),'poses':poses,'qualified':'Five source-mapped gameplay views. Per-CarID/per-mode FOV and Follow Front/Back/Up copy overrides; existing follow extents preserved. Mode overrides affect normal AND split source presets.','approximate':'Flat static pose. Fixed type0/1 use original model bounds, not XML offset placeholders. Pitch/acceleration/terrain/history/device presentation need gameplay comparison.','unknown':'Rear/replay/switch timing and live owner lifecycle require owner validation.'}

    def camera_mode_update(self,mode,fields):
        from master_rallye.addon_sdk.camera_profile import bind_camera_profile
        selected=gameplay_mode(mode);info=self.camera_inspect();state=self.vehicle_state()
        if not fields and not state['camera']:return
        profile=copy.deepcopy(state['camera'])if state['camera']else {'version':1,'car_id':self.data['car_id'],'policy':'native_follow_extents','runtime_family':info['family'],'source_model_sha256':info['source_model_sha256'],'follow_extents':info['current']}
        key=selected['kind']+str(selected['index']);modes=profile.setdefault('mode_overrides',{})
        if fields:modes[key]=copy.deepcopy(fields)
        else:modes.pop(key,None)
        bind_camera_profile(profile,self.camera_source());state['camera']=None if not modes and profile['follow_extents']==info['original']else profile;self._vehicle_commit(state)

    def camera_lab_export(self,*,view='modified',preset=0,split=False,guides=True,mode=None):
        from .service import write_json,write_resource
        from master_rallye.preview_scene import stage_vehicle
        if view not in ('original','donor','modified')or type(guides)is not bool:raise ValueError('Unknown gameplay preview mode')
        self.materialize();report=self.camera_lab_inspect(preset,split,mode=mode);folder=self.root/'preview/game-camera'/view;folder.mkdir(parents=True,exist_ok=True)
        for f in self.assets.iterdir():
            if f.is_file()and f.suffix.lower()in('.dx','.dxt'):shutil.copyfile(f,folder/f.name)
        write_resource(folder/'car.dx',self.camera_source());profile=copy.deepcopy(self.preview_profile()or{})
        if guides:profile['camera_debug']={key:{field:report['poses'][key][field]for field in ('eye','target','source_fov_degrees')}for key in ('original','modified')}
        write_json(folder/'profile.json',profile);scene=folder/'camera.mrpv';stage_vehicle(folder/'car.dx',scene,profile=folder/'profile.json');write_json(folder/'camera-report.json',report)
        import struct
        with scene.open('rb')as stream:header=stream.read(40)
        lohi=struct.unpack_from('<6f',header,16);report['preview_bounds']={'minimum':list(lohi[:3]),'maximum':list(lohi[3:])}
        write_json(folder/'camera-report.json',report)
        return {'scene':str(scene),'report':report,'pose':report['poses'][view],'source':str(folder/'car.dx')}
