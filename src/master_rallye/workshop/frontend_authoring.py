"""Frontend-only authoring service shared by Studio and CLI."""
import copy,hashlib,json
from pathlib import Path
from master_rallye.frontend_presentation import bind_profile,measure,pose,auto_frame,XML_SHA256

class FrontendAuthoring:
    def frontend_source(self):
        self.materialize()
        return self.native_model_resources()['complete.dx']

    def frontend_inspect(self,offset=None,aspect=4/3):
        from master_rallye.addon_sdk.project import read_sma_member
        raw=read_sma_member(Path(self.data['build_settings']['retail_sma']),'DataScene/FrontendScreens/VehicleSelect.xml')
        if hashlib.sha256(raw).hexdigest()!=XML_SHA256:raise ValueError('Frontend scene source changed')
        source=self.frontend_source();state=self.vehicle_state().get('frontend');value=offset if offset is not None else(state['vertical_offset_m']if state else 0.)
        if state:bind_profile(state,source)
        from master_rallye.frontend_presentation import validate_profile
        info=self.camera_inspect();profile={'version':1,'car_id':self.data['car_id'],'runtime_family':info['family'],'source_model_sha256':hashlib.sha256(source).hexdigest(),'vertical_offset_m':value};validate_profile(profile)
        from master_rallye.frontend_presentation import wheel_baseline
        try:wheel=wheel_baseline(self.native_model_resources())
        except ValueError as exc:wheel={'status':'UNQUALIFIED','reason':str(exc)}
        return {'profile':profile,'original':measure(source,0.,aspect),'modified':measure(source,value,aspect),'wheel_baseline':wheel,'pose':pose(value),'source_scene_sha256':XML_SHA256,'scope':'Large VehicleSelect complete model only; unique resource identity, no gameplay camera or model edits','boundary':'Original source pose/projection arithmetic; D3D9 material approximation. Full viewport clipping checked; panel guide illustrative. D3D8 owner comparison pending.'}

    def frontend_update(self,value):
        if self.data['kind']!='addon':raise ValueError('Frontend native authoring currently requires a unique addon resource; stock reference is read-only')
        from master_rallye.frontend_presentation import validate_offset
        validate_offset(value)
        if value==0:
            state=self.vehicle_state();state['frontend']=None;self._vehicle_commit(state);return
        report=self.frontend_inspect(value);bind_profile(report['profile'],self.frontend_source());state=self.vehicle_state();state['frontend']=None if value==0 else report['profile'];self._vehicle_commit(state)

    def frontend_auto_frame(self):
        from master_rallye.addon_sdk.project import read_sma_member
        reference=read_sma_member(Path(self.data['build_settings']['retail_sma']),'DataGx/Vehicles/NewRav/complete.dx')
        return auto_frame(self.frontend_source(),reference)

    def frontend_export(self,*,view='modified',offset=None):
        from master_rallye.preview_scene import stage_vehicle
        from .service import write_json
        if view=='stock NewRav':return self.frontend_reference_export()
        if view not in('original','modified'):raise ValueError('Invalid frontend comparison view')
        report=self.frontend_inspect(0. if view=='original'else offset);folder=self.root/'preview/frontend';folder.mkdir(parents=True,exist_ok=True)
        import shutil
        for file in self.assets.iterdir():
            if file.is_file()and file.suffix.lower()in('.dx','.dxt'):shutil.copyfile(file,folder/file.name)
        (folder/'complete.dx').write_bytes(self.frontend_source())
        write_json(folder/'profile.json',{'native_frontend_presentation':1})
        scene=folder/'frontend.mrpv';stage_vehicle(folder/'complete.dx',scene,profile=folder/'profile.json')
        write_json(folder/'report.json',report)
        return {'scene':str(scene),'source':str(folder/'complete.dx'),'preview_profile':str(folder/'profile.json'),'report':report,'pose':report['pose']}

    def frontend_reference_export(self):
        """Read-only stock comparison, never a new stock editing qualification."""
        from master_rallye.addon_sdk.project import read_sma_member
        from master_rallye.preview_scene import stage_vehicle
        from .service import write_json
        self.frontend_inspect() # scene source authority
        settings=self.data['build_settings'];source=Path(settings['retail_root'])/'DataGx/Vehicles/NewRav';folder=self.root/'preview/frontend-reference';folder.mkdir(parents=True,exist_ok=True)
        for p in source.iterdir():
            if p.is_file()and p.suffix.lower()in('.dx','.dxt'):
                raw=read_sma_member(Path(settings['retail_sma']),'DataGx/Vehicles/NewRav/'+p.name)
                if p.read_bytes()!=raw:raise ValueError('Retail NewRav unpacked source differs from archive')
                (folder/p.name).write_bytes(raw)
        write_json(folder/'profile.json',{'native_frontend_presentation':1});scene=folder/'frontend.mrpv';stage_vehicle(folder/'complete.dx',scene,profile=folder/'profile.json')
        return {'scene':str(scene),'source':str(folder/'complete.dx'),'preview_profile':str(folder/'profile.json'),'pose':pose(),'report':measure((folder/'complete.dx').read_bytes())}

    def frontend_build_roster(self,roster,snapshot):
        from .service import write_json
        current=self.vehicle_state().get('frontend');paths=[]
        for path in roster.get('frontend_profiles',[]):
            if json.loads(Path(path).read_text())['car_id']!=self.data['car_id']:paths.append(path)
        if current:
            bind_profile(current,self.frontend_source());p=Path(snapshot)/'frontend-profile.json';write_json(p,current);paths.append(str(p))
        if paths:roster['frontend_profiles']=paths
        else:roster.pop('frontend_profiles',None)
