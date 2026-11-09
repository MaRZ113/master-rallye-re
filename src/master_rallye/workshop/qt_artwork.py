"""CarSheet / SIDE HUD controls within the existing Qt Texture Studio."""
from pathlib import Path
import copy
import math
import struct
import time
from PySide6 import QtCore as Q,QtGui as G,QtWidgets as W
from .texture_images import IMPORT_FILTER
from .livery_artwork import compose_live,import_manual,export_resource


class ArtworkPanel(W.QGroupBox):
    def __init__(self,studio):
        super().__init__('CarSheet / SIDE HUD');self.studio=studio;self.candidate=None;self.candidates={};self.session_id=None;self.loading=False
        layout=W.QVBoxLayout(self);self.role=W.QComboBox();self.role.addItem('CarSheet · 128 × 128','vehicle_select_art');self.role.addItem('SIDE HUD · 32 × 16','smallcarsheet');layout.addWidget(self.role)
        self.preview=W.QLabel('Historical artwork stays preferred.\nGenerate explicitly as a reconstruction.');self.preview.setAlignment(Q.Qt.AlignmentFlag.AlignCenter);self.preview.setMinimumHeight(135);layout.addWidget(self.preview)
        self.active_state=W.QLabel();self.active_state.setWordWrap(True);layout.addWidget(self.active_state)
        self.view_mode=W.QComboBox();self.view_mode.addItems(['Active artwork','Generated candidate']);layout.addWidget(self.view_mode);self.view_mode.currentIndexChanged.connect(self.refresh_preview)
        camera=W.QGroupBox('3D camera / lighting — auto-fit before capture');layout.addWidget(camera);camera_form=W.QFormLayout(camera)
        frame=W.QGroupBox('Final native icon framing — never changes the camera');layout.addWidget(frame);form=W.QFormLayout(frame);self.fields={}
        for key,label,low,high,step in [('azimuth','Azimuth',-360,360,1),('elevation','Elevation',-85,85,1),('fov','Vertical FOV (perspective)',15,80,1),('frame_scale','Frame scale',.2,4,.05),('pan_x','Position X',-2,2,.02),('pan_y','Position Y',-2,2,.02),('key','Key light',0,2,.05),('ambient','Ambient',0,1,.05)]:
            spin=W.QDoubleSpinBox();spin.setRange(low,high);spin.setSingleStep(step);spin.setDecimals(3);self.fields[key]=spin;(form if key in ('frame_scale','pan_x','pan_y') else camera_form).addRow(label,spin);spin.valueChanged.connect(self.save_preset)
        self.ortho=W.QCheckBox('Orthographic side / silhouette');layout.addWidget(self.ortho);self.ortho.toggled.connect(self.save_preset)
        self.background=W.QComboBox();self.background.addItems(['transparent','#ffffff','#20252c']);form.addRow('Background',self.background);self.background.currentTextChanged.connect(self.save_preset)
        row=W.QHBoxLayout();layout.addLayout(row);studio.button(row,'Generate reconstruction',self.generate);studio.button(row,'Import historical / manual',self.manual)
        row=W.QHBoxLayout();layout.addLayout(row);studio.button(row,'Export PNG',self.export_png);studio.button(row,'Export native frame…',self.export_native)
        self.info=W.QLabel('Native resource export requires an existing same-size FEED template. No bank or CarID is allocated.');self.info.setWordWrap(True);layout.addWidget(self.info)
        self.role.currentIndexChanged.connect(self.load_preset)
        studio.button(layout,'Reset to stock presentation',self.reset_stock)
        studio.button(layout,'Use reconstruction as active',self.accept_candidate)

    def reset_stock(self):
        self.studio.require()
        from .livery_artwork import default_presets
        self.studio.session.art_presets[self.key()]=default_presets()[self.key()];self.load_preset();self.studio.refresh_dirty()

    def key(self):return self.role.currentData()
    def load_preset(self,*unused):
        session=self.studio.session
        if not session:return
        token=(id(session),session.metadata['livery_id'])
        if self.session_id!=token:
            self.candidates={};self.session_id=token
        self.loading=True;p=session.art_presets[self.key()]
        for key,spin in self.fields.items():spin.setValue(p[key])
        self.ortho.setChecked(p['orthographic']);self.background.setCurrentText(p['background']);self.loading=False
        self.view_mode.setCurrentIndex(0);self.refresh_preview()
    def save_preset(self,*unused):
        if self.loading or not self.studio.session:return
        self.studio.session.art_presets[self.key()]={**{k:s.value() for k,s in self.fields.items()},'preset_version':3,'orthographic':self.ortho.isChecked(),'background':self.background.currentText()};self.studio.refresh_dirty()
        self.info.setText('Preset changed — Generate reconstruction to refresh artwork; historical/manual selection stays intact')
    def show_entry(self,entry):
        self.candidate=entry
        pix=G.QPixmap(entry['png']);self.preview.setPixmap(pix.scaled(256,160,Q.Qt.AspectRatioMode.KeepAspectRatio,Q.Qt.TransformationMode.FastTransformation))
        self.info.setText(f"{entry['origin']} · {entry['dimensions'][0]} × {entry['dimensions'][1]} native pixels · {entry['method']} "+' | '.join(entry.get('warnings',[])))
    def refresh_preview(self,*unused):
        session=self.studio.session
        if not session:return
        active=session.artwork.get(self.key());candidate=self.candidates.get(self.key())
        self.active_state.setText('Active: '+(active['origin']+' · '+active['sha256'][:12] if active else 'none')+'\nGenerated candidate: '+(candidate['origin']+' · '+candidate['sha256'][:12] if candidate else 'none'))
        entry=candidate if self.view_mode.currentIndex()==1 else active
        if entry:self.show_entry(entry)
        else:self.candidate=None;self.preview.clear();self.preview.setText('No image in this slot')
    def accept_candidate(self):
        self.studio.require();entry=self.candidates.get(self.key())
        if not entry:raise ValueError('Generate a reconstruction candidate first')
        self.studio.session.accept_artwork(entry);self.candidates.pop(self.key(),None);self.view_mode.setCurrentIndex(0);self.refresh_preview();self.studio.refresh_dirty()
    def generate(self):
        studio=self.studio;studio.require()
        if studio.original.isChecked():raise ValueError('Select Modified before generating artwork for this livery')
        if studio.model.currentText()=='wheel.dx':raise ValueError('Select complete.dx or car.dx for vehicle artwork')
        model_role=studio.model.currentText()
        role=self.key();session=studio.session;p=copy.deepcopy(session.art_presets[role]);start=time.perf_counter()
        # 4x (CarSheet) / 16x (SIDE) target size, independently of UI DPI/window.
        width,height=(512,320) if role=='vehicle_select_art' else (512,256)
        payload=struct.pack('<4I8f',2,width,height,int(p['orthographic']),math.radians(p['azimuth']),math.radians(p['elevation']),1.,0.,0.,p['key'],p['ambient'],p['fov'])
        studio.viewport.send_data(0x33415856,payload)
        state=str(studio.viewport.state);output=session.project.root/'artwork-generations'/str(time.time_ns())
        def work(task):
            task.stage('Recover transparent coverage and compose native artwork with SDK presentation')
            return compose_live(session,role,state+'.art-black.bmp',state+'.art-white.bmp',p,output,model_role=model_role)
        def done(entry):
            self.candidates[role]=entry;self.view_mode.setCurrentIndex(1);self.refresh_preview()
            self.info.setText('Candidate only. Active artwork is unchanged; use Use reconstruction as active to accept it. The previous active image will be archived.')
            studio.refresh_dirty();studio.metrics['artwork_'+role+'_seconds']=time.perf_counter()-start;studio.editor.status.setText(f'Artwork generated · {time.perf_counter()-start:.3f}s · live camera retained')
        studio.editor.run('CarSheet / SIDE generation',work,done)
    def manual(self,path=None,origin=None,scale_to_native=False):
        studio=self.studio;studio.require()
        path=path or W.QFileDialog.getOpenFileName(self,'Import exact native-size historical/manual artwork','',IMPORT_FILTER)[0]
        if not path:return
        if origin is None:
            origin,ok=W.QInputDialog.getItem(self,'Artwork provenance','Classify this image',['Historical','Original','Custom'],0,False)
            if not ok:return
        from .texture_images import load_image
        from master_rallye.addon_sdk.ui_preview import PROFILES
        w,h,_,_=load_image(path);target=PROFILES[self.key()]['size']
        if (w,h)!=target and not scale_to_native:
            answer=W.QMessageBox.question(self,'Scale a copy to native resolution',f'Source is {w} × {h}; target is {target[0]} × {target[1]}. Scale the full canvas and retain the source image separately? No historical pixels will be cropped or recoloured.')
            if answer!=W.QMessageBox.StandardButton.Yes:return
            scale_to_native=True
        output=studio.session.project.root/'artwork-manual'/str(time.time_ns())
        entry=import_manual(studio.session,self.key(),path,origin,output,scale_to_native=scale_to_native);studio.session.artwork[self.key()]=entry;self.view_mode.setCurrentIndex(0);self.refresh_preview();studio.refresh_dirty()
    def entry(self):
        self.studio.require()
        entry=self.candidates.get(self.key()) if self.view_mode.currentIndex()==1 else self.studio.session.artwork.get(self.key())
        if not entry:raise ValueError('Generate or import artwork first')
        if entry.get('input_signature') and entry['input_signature']!=self.studio.session.signature():raise ValueError('Artwork is stale after texture/metadata edits; regenerate')
        if entry.get('preset') and entry['preset']!=self.studio.session.art_presets[self.key()]:raise ValueError('Artwork preset changed; regenerate')
        return entry
    def export_png(self,path=None):
        entry=self.entry();path=path or W.QFileDialog.getSaveFileName(self,'Export native-resolution artwork',self.key()+'.png','PNG (*.png)')[0]
        if path:self.studio.session.output_path(Path(path));Path(path).write_bytes(Path(entry['png']).read_bytes())
    def export_native(self,template=None,path=None):
        entry=self.entry();template=template or W.QFileDialog.getOpenFileName(self,'Qualified native same-size FEED frame template','','MR texture (*.dxt)')[0]
        if not template:return
        path=path or W.QFileDialog.getSaveFileName(self,'New standalone native artwork frame',self.key()+'.dxt','MR texture (*.dxt)')[0]
        if not path:return
        self.studio.session.output_path(Path(path))
        if Path(path).resolve()==Path(template).resolve():raise ValueError('Do not overwrite the native template')
        report=export_resource(entry,template,path)
        from .service import write_json
        write_json(Path(str(path)+'.json'),{'artwork':{k:v for k,v in entry.items() if k not in ('png','source_png')},**report})
