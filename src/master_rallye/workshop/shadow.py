"""Project/history adapter for the qualified shadow-only bounds compiler."""
import copy
import json
from pathlib import Path
from master_rallye.addon_sdk.vehicle_shadow import generate_profile, bind_profile

CONTROLS = dict(alpha_threshold=32, scale_x=1., scale_z=1., offset_x_m=0., offset_z_m=0., margin_x_m=.05, margin_z_m=.10)


class ShadowAuthoring:
    def shadow_state(self):
        from .service import write_json,sha
        if self.data['kind'] != 'addon':
            raise ValueError('Shadow runtime editing requires a qualified addon; stock resources remain read-only')
        if 'shadow_baseline' not in self.data:
            path = self.root / 'original-shadow.json'
            source = path if path.exists() else self.working / 'shadow-profile.json'
            self.data['shadow_baseline'] = json.loads(source.read_text()) if source.exists() else None
            self.save()
        pin=self.root/'shadow-author-baseline.json'
        if 'shadow_baseline_pin' not in self.data:
            write_json(pin,self.data['shadow_baseline']);self.data['shadow_baseline_pin']=sha(pin.read_bytes());self.save()
        if sha(pin.read_bytes())!=self.data['shadow_baseline_pin'] or json.loads(pin.read_text())!=self.data['shadow_baseline']:
            raise ValueError('Immutable shadow author baseline changed')
        return copy.deepcopy(self.data.get('shadow') or {'mode':'donor', 'controls':{}})

    def shadow_sources(self):
        from master_rallye.addon_sdk.project import read_sma_member
        from .service import write_resource
        self.verify_inputs()
        # Reuse exact retail identity admission before accessing its shared image.
        self._retail_members()
        texture = read_sma_member(Path(self.data['build_settings']['retail_sma']), 'DataGx/Misc/Shadow/shadow.dxt')
        pin = self.root / 'shadow-source.dxt'
        if pin.exists() and pin.read_bytes() != texture:
            raise ValueError('Shadow texture source changed')
        write_resource(pin, texture)
        return self.camera_source(), texture

    def shadow_calculate(self, state=None):
        original=self.shadow_state()
        state = original if state is None else copy.deepcopy(state)
        if set(state) != {'mode','controls'} or state['mode'] not in ('original','donor','auto','custom'):
            raise ValueError('Unknown shadow mode or state')
        if not isinstance(state['controls'],dict) or set(state['controls'])-set(CONTROLS):
            raise ValueError('Unknown shadow controls')
        model, texture = self.shadow_sources()
        family = json.loads((self.working/'addon.json').read_text())['identity']['runtime_family']
        controls = {**CONTROLS, **state['controls']} if state['mode']=='custom' else dict(CONTROLS)
        profile = generate_profile(model, texture, family, **controls)
        if state['mode']=='donor' and self.data.get('shadow_baseline'):
            # Explicit author baseline, never a profile left by a previous edit.
            baseline = self.data['shadow_baseline']
            if baseline['runtime_family'] != family:
                raise ValueError('Shadow donor family mismatch')
            if baseline['source_texture_sha256'] != profile['source_texture_sha256']:
                raise ValueError('Shadow donor texture changed')
            profile = generate_profile(model,texture,family,**{k:baseline[k] for k in CONTROLS})
        bound = bind_profile(profile,model,texture)
        bound.update(mode=state['mode'], enabled=state['mode'] not in ('original',) and (state['mode']!='donor' or self.data.get('shadow_baseline') is not None),
                     evidence='Existing 00588200 consumer only; 00553C80 native bounds layout. X/Z factors 1.75/1.5; alpha-cell support is a threshold diagnostic, not an opacity slider.',
                     preview='D3D9 ground/footprint guides; no terrain projection, light direction or exact D3D8 blob appearance')
        if not bound['enabled']:
            bound['generated_alpha_support_xz_m'] = bound['native_alpha_support_xz_m']
            bound['generated_quad_size_xz_m'] = bound['native_quad_size_xz_m']
            bound['generated_quad_center_xz_m'] = bound['native_quad_center_xz_m']
        return bound

    def shadow_update(self, mode, **controls):
        self.shadow_state()
        state = {'mode':mode,'controls':controls}
        report = self.shadow_calculate(state)
        self._record(); self.data['shadow']=state; self.materialize(); self.save()
        return report

    def shadow_materialize(self):
        if 'shadow_baseline' not in self.data:return
        from .service import write_json
        report = self.shadow_calculate()
        target = self.working/'shadow-profile.json'
        if report['enabled']:write_json(target,report['profile'])
        elif target.exists():target.unlink()

    def shadow_reset(self, mode='donor'):
        return self.shadow_update(mode)

    def shadow_debug_profile(self):
        """A sealed diagnostic payload for the shared scene exporter, not a game asset."""
        report = self.shadow_calculate()
        return {k:report[k] for k in ('body_bounds_xz_m','native_alpha_support_xz_m','generated_alpha_support_xz_m','mode','evidence','preview')}

    def shadow_preview_export(self):
        import shutil
        from master_rallye.preview_scene import stage_vehicle
        from .service import write_json,write_resource
        self.materialize()
        folder=self.root/'preview/shadow';folder.mkdir(parents=True,exist_ok=True)
        for path in self.assets.iterdir():
            if path.suffix.lower() in ('.dx','.dxt'):shutil.copyfile(path,folder/path.name)
        write_resource(folder/'car.dx',self.camera_source())
        profile=copy.deepcopy(self.preview_profile() or {})
        profile['shadow_debug']=self.shadow_debug_profile()
        write_json(folder/'profile.json',profile)
        report=stage_vehicle(folder/'car.dx',folder/'shadow.mrpv',profile=folder/'profile.json')
        return folder/'shadow.mrpv',report
