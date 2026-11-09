"""Integrated native texture authoring and the existing embedded D3D9 viewer."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as T
import json
import struct
import subprocess
import time
from PySide6 import QtCore as Q, QtGui as G, QtWidgets as W
from master_rallye.dxt import encode_png, parse_dxt_bytes
from master_rallye.preview_scene import stage_vehicle
from .livery import LiverySession
from .texture_images import IMPORT_FILTER,EXPORT_FILTER


class CopyData(C.Structure):
    _fields_ = [('kind', C.c_size_t), ('size', T.DWORD), ('data', C.c_void_p)]


class NativeViewport(W.QWidget):
    """Own a child HWND; no second renderer, game DLL or texture watcher."""
    def __init__(self, viewer, parent=None):
        super().__init__(parent)
        self.viewer=Path(viewer);self.process=None;self.hwnd=None;self.state=None;self.sent={};self.active=set()
        self.setMinimumSize(480,340)
        self.setAttribute(Q.Qt.WidgetAttribute.WA_NativeWindow)
        self.user=C.WinDLL('user32',use_last_error=True)
        self.user.SendMessageTimeoutW.argtypes=[T.HWND,T.UINT,C.c_size_t,C.c_ssize_t,T.UINT,T.UINT,C.POINTER(C.c_size_t)]
        self.user.SendMessageTimeoutW.restype=C.c_ssize_t
        self.user.SetWindowPos.argtypes=[T.HWND,T.HWND,C.c_int,C.c_int,C.c_int,C.c_int,T.UINT]
        self.user.GetParent.argtypes=[T.HWND];self.user.GetParent.restype=T.HWND

    def start(self, scene, state):
        self.stop();self.state=Path(state);self.state.unlink(missing_ok=True);self.sent={}
        self.active=set()
        with Path(scene).open('rb') as stream:
            header=stream.read(40);count=struct.unpack_from('<I',header,8)[0]
            for _ in range(count):
                n=struct.unpack('<I',stream.read(4))[0];self.active.add(stream.read(n).decode('utf-8'))
                w,h=struct.unpack('<II',stream.read(8));stream.seek(w*h*4,1)
        self.process=subprocess.Popen([str(self.viewer),'--scene',str(scene),'--parent-hwnd',str(int(self.winId())),
            '--session-state',str(state),'--selection-file',str(state)+'.selection','--model','frontend','--provenance','Vehicle SDK texture workspace'])

    def attach(self):
        if self.hwnd:return True
        if self.process and self.process.poll() is not None:
            error=Path(str(self.state)+'.error')
            raise ValueError(error.read_text(encoding='utf-8') if error.exists() else 'Embedded viewer exited; rebuild the V-TEX2 viewer')
        if not self.state or not self.state.exists():return False
        try:hwnd=json.loads(self.state.read_text())['hwnd']
        except (ValueError,KeyError):return False
        if self.user.GetParent(hwnd)!=int(self.winId()):raise ValueError('Viewer parent HWND mismatch')
        self.hwnd=hwnd;self.resize_child();return True

    def message(self, message, w=0, l=0):
        if not self.hwnd:raise ValueError('3D viewport is still opening')
        result=C.c_size_t()
        if not self.user.SendMessageTimeoutW(self.hwnd,message,w,l,2,3000,C.byref(result)):
            raise ValueError('3D viewport did not acknowledge the operation')
        return result.value

    def packet(self, command, name, texture=None):
        if not self.hwnd:return False
        encoded=name.encode('utf-8')
        payload=struct.pack('<5I',1,command,texture.width if texture else 0,texture.height if texture else 0,len(encoded))+encoded
        if texture:payload+=texture.bgra
        return self.send_data(0x32545856,payload)

    def send_data(self,kind,payload):
        buffer=C.create_string_buffer(payload);data=CopyData(kind,len(payload),C.cast(buffer,C.c_void_p))
        if not self.message(0x4a,int(self.winId()),C.addressof(data)):raise ValueError('3D bridge rejected target/dimensions or unsupported command')
        return True

    def update_textures(self, session, original=False):
        from .service import sha
        # Compare content identities: untouched textures never cross IPC.
        for name,usages in session.index().items():
            if name not in self.active:continue
            raw=((session.project.baseline if original else session.project.assets)/name).read_bytes()
            digest=sha(raw)
            if self.sent.get(name)!=digest:
                self.packet(1,name,parse_dxt_bytes(raw));self.sent[name]=digest

    def resize_child(self):
        if self.hwnd:
            ratio=self.devicePixelRatioF()
            self.user.SetWindowPos(self.hwnd,None,0,0,max(1,int(self.width()*ratio)),max(1,int(self.height()*ratio)),0x14)

    def resizeEvent(self,event):super().resizeEvent(event);self.resize_child()
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate();self.process.wait(timeout=5)
        self.process=None;self.hwnd=None


class UVView(W.QGraphicsView):
    def __init__(self):
        super().__init__();self.canvas=W.QGraphicsScene(self);self.setScene(self.canvas)
        self.setMinimumHeight(210);self.setDragMode(W.QGraphicsView.DragMode.ScrollHandDrag)
        self.paths=[];self.opacity=.65;self.width_px=1;self.height_px=1
        self.setRenderHint(G.QPainter.RenderHint.Antialiasing)

    def show_texture(self, png, usages, overlay=True):
        self.canvas.clear();self.paths=[]
        image=G.QImage.fromData(png,'PNG');self.width_px=image.width();self.height_px=image.height()
        self.canvas.addPixmap(G.QPixmap.fromImage(image));triangles=[t for u in usages for t in u['uv_triangles']]
        from .uv_islands import island_groups
        vertex_ids=[[(u['model'],vertex) for vertex in tri] for u in usages for tri in u.get('uv_vertex_ids',[])]
        groups=island_groups(triangles,vertex_ids if len(vertex_ids)==len(triangles) else None)
        membership={i:group[0] for group in groups for i in group}
        signed=[];seen=set();shared=0
        for tri in triangles:
            key=tuple(sorted(tuple(uv) for uv in tri));shared+=key in seen;seen.add(key)
            a,b,c=tri;signed.append((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        islands={}
        for i,tri in enumerate(triangles):
            path=islands.setdefault(membership[i],G.QPainterPath())
            points=[Q.QPointF(u*self.width_px,(1-v)*self.height_px) for u,v in tri]
            path.moveTo(points[0]);path.lineTo(points[1]);path.lineTo(points[2]);path.closeSubpath()
        for path in islands.values():
            item=self.canvas.addPath(path,G.QPen(G.QColor('#ffbf50'),.65))
            item.setFlag(W.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable);item.setOpacity(self.opacity);item.setVisible(overlay);self.paths.append(item)
        self.canvas.setSceneRect(0,0,self.width_px,self.height_px)
        self.fitInView(self.canvas.sceneRect(),Q.Qt.AspectRatioMode.KeepAspectRatio)
        outside=sum(any(u<0 or u>1 or v<0 or v>1 for u,v in t) for t in triangles)
        return f'{len(triangles)} UV triangles / {len(islands)} selectable islands; {shared} identical/shared triangles; winding +{sum(s>0 for s in signed)}/−{sum(s<0 for s in signed)} (mirror indicator, not proof); {outside} outside atlas'

    def set_overlay(self, visible, opacity):
        self.opacity=opacity
        for p in self.paths:p.setVisible(visible);p.setOpacity(opacity)

    def export_uv(self, path):
        image=G.QImage(self.width_px,self.height_px,G.QImage.Format.Format_ARGB32);image.fill(Q.Qt.GlobalColor.transparent)
        painter=G.QPainter(image);painter.setRenderHint(G.QPainter.RenderHint.Antialiasing);painter.setPen(G.QPen(G.QColor('#ffbf50'),1))
        for item in self.paths:painter.drawPath(item.path())
        painter.end()
        if not image.save(str(path),'PNG'):raise ValueError('UV PNG could not be written')
    def resizeEvent(self,event):super().resizeEvent(event);self.fitInView(self.canvas.sceneRect(),Q.Qt.AspectRatioMode.KeepAspectRatio)


class TextureStudio(W.QWidget):
    def __init__(self, editor):
        super().__init__();self.editor=editor;self.session=None;self.selected=None;self.selected_usage=None;self.loading=False;self.metrics={};self.selection_text=''
        layout=W.QVBoxLayout(self);bar=W.QHBoxLayout();layout.addLayout(bar)
        for label,fn in [('Open Vehicle',self.open_vehicle),('Open Livery',self.open_livery),('New from Stock',self.new_livery),('Duplicate Current Livery',self.duplicate_livery),('Save Livery',self.save_livery)]:self.button(bar,label,fn)
        self.dirty=W.QLabel('Open a native family or existing Workshop project');bar.addWidget(self.dirty,1)
        split=W.QSplitter();layout.addWidget(split,1)
        self.tree=W.QTreeWidget();self.tree.setHeaderLabels(['MODEL / MATERIAL / TEXTURE']);split.addWidget(self.tree)
        center=W.QWidget();cl=W.QVBoxLayout(center);self.viewport=NativeViewport(editor.viewer);cl.addWidget(self.viewport,1)
        cl.addWidget(W.QLabel('LMB: orbit / pick · MMB: pan · Wheel: zoom · F: focus · Home: reset · F1: help'))
        controls=W.QHBoxLayout();cl.addLayout(controls)
        self.model=W.QComboBox();self.model.addItems(['complete.dx','car.dx','wheel.dx']);controls.addWidget(self.model)
        self.model.currentIndexChanged.connect(lambda i:self.guard(lambda:self.viewport.message(0x800c,[2,1,3][i])))
        self.view=W.QComboBox();self.view.addItems(['Perspective','Front','Rear','Left','Right','Top']);controls.addWidget(self.view)
        self.view.currentIndexChanged.connect(lambda i:self.guard(lambda:self.viewport.message(0x8014,[4,1,2,3,6,5][i])))
        self.button(controls,'Reset',lambda:self.viewport.message(0x8017))
        self.wire=W.QCheckBox('Wireframe');controls.addWidget(self.wire);self.wire.toggled.connect(lambda v:self.guard(lambda:self.viewport.message(0x8015,int(v))))
        self.original=W.QCheckBox('Original');controls.addWidget(self.original);self.original.toggled.connect(lambda _:self.guard(self.sync))
        split.addWidget(center)
        right=W.QTabWidget();texture_page=W.QWidget();rl=W.QVBoxLayout(texture_page);self.uv=UVView();rl.addWidget(self.uv,1)
        overlay=W.QHBoxLayout();self.overlay=W.QCheckBox('UV overlay');self.overlay.setChecked(True);overlay.addWidget(self.overlay)
        self.alpha=W.QSlider(Q.Qt.Orientation.Horizontal);self.alpha.setRange(0,100);self.alpha.setValue(65);overlay.addWidget(self.alpha);rl.addLayout(overlay)
        for signal in (self.overlay.toggled,self.alpha.valueChanged):signal.connect(lambda _:self.uv.set_overlay(self.overlay.isChecked(),self.alpha.value()/100))
        self.all_uv=W.QCheckBox('Show UVs from all TEX0 owners in this model');rl.addWidget(self.all_uv);self.all_uv.toggled.connect(lambda _:self.guard(self.show_selected))
        self.uv_info=W.QLabel();self.uv_info.setWordWrap(True);rl.addWidget(self.uv_info)
        self.details=W.QPlainTextEdit();self.details.setReadOnly(True);self.details.setMaximumHeight(170);rl.addWidget(self.details)
        row=W.QHBoxLayout();rl.addLayout(row)
        self.button(row,'Export PNG / Image',self.export_png);self.button(row,'Import PNG / Image',self.import_png);self.button(row,'Reload from File',self.reload_png)
        row=W.QHBoxLayout();rl.addLayout(row);self.button(row,'Export All',self.export_all);self.button(row,'Import Manifest',self.import_manifest);self.button(row,'Export UV',self.export_uv)
        row=W.QHBoxLayout();rl.addLayout(row);self.button(row,'Restore Original',self.restore);self.button(row,'Undo',self.undo);self.button(row,'Redo',self.redo)
        self.preserve=W.QCheckBox('Preserve Original Alpha (disable to edit alpha explicitly)');self.preserve.setChecked(True);rl.addWidget(self.preserve)
        self.import_alpha=W.QCheckBox('Use Imported Alpha');rl.addWidget(self.import_alpha)
        self.import_alpha.toggled.connect(lambda value:self.preserve.setChecked(not value))
        self.preserve.toggled.connect(lambda value:self.import_alpha.setChecked(not value))
        self.channel=W.QComboBox();self.channel.addItems(['RGBA','RGB','Alpha']);rl.addWidget(self.channel);self.channel.currentTextChanged.connect(lambda _:self.guard(self.show_selected))
        form=W.QFormLayout();rl.addLayout(form);self.fields={}
        for key,label in [('name','Livery'),('number','Start number'),('crew','Pilot / crew'),('source','Source')]:
            edit=W.QLineEdit();self.fields[key]=edit;form.addRow(label,edit);edit.textEdited.connect(self.metadata_changed)
        self.origin=W.QComboBox();self.origin.addItems(['Original','Historical','Custom','Reconstructed']);form.addRow('Origin',self.origin);self.origin.currentTextChanged.connect(self.metadata_changed)
        self.variant=W.QLineEdit();self.variant.setReadOnly(True);self.variant.setToolTip('Variant is bound to the pinned source model; a PC asset cannot become PS2 by editing this label.');form.addRow('Verified model identity',self.variant)
        from .qt_artwork import ArtworkPanel
        self.artwork=ArtworkPanel(self)
        scroll=W.QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(texture_page);right.addTab(scroll,'Texture / UV')
        art_scroll=W.QScrollArea();art_scroll.setWidgetResizable(True);art_scroll.setWidget(self.artwork);right.addTab(art_scroll,'CarSheet / SIDE')
        split.addWidget(right);split.setSizes([280,740,460])
        summary=W.QHBoxLayout();layout.addLayout(summary)
        self.warning=W.QLabel('Offline 3D preview');summary.addWidget(self.warning,1)
        self.details_toggle=W.QToolButton();self.details_toggle.setText('Preview details');self.details_toggle.setCheckable(True);summary.addWidget(self.details_toggle)
        self.diagnostics=W.QPlainTextEdit();self.diagnostics.setReadOnly(True);self.diagnostics.setMaximumHeight(150);self.diagnostics.hide();layout.addWidget(self.diagnostics)
        self.details_toggle.toggled.connect(self.diagnostics.setVisible)
        self.tree.currentItemChanged.connect(self.choose)
        self.timer=Q.QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(100)

    def button(self,layout,label,fn):
        button=W.QPushButton(label);button.clicked.connect(lambda:self.guard(fn));layout.addWidget(button);return button
    def guard(self,fn):return self.editor.guard(fn)
    def require(self):
        if not self.session:raise ValueError('Open a native vehicle first')
        if self.loading:raise ValueError('Wait for the 3D viewport')
        if self.editor.task:raise ValueError('Wait or cancel the current operation')
    def target(self):
        self.require()
        if not self.selected:raise ValueError('Select a texture')
        return self.selected
    def folder(self,title):return W.QFileDialog.getExistingDirectory(self,title,str(self.editor.workspace))
    def open_vehicle(self):
        folder=self.folder('Native family or existing Workshop project (copied into a private texture workspace)')
        if folder:self.load_vehicle(Path(folder))
    def open_livery(self):
        path,_=W.QFileDialog.getOpenFileName(self,'Open portable livery','','Livery (livery.json)')
        if path:self.load_vehicle(Path(path),True)
    def load_vehicle(self,path,package=False):
        if self.loading:raise ValueError('Wait for the current vehicle to open')
        if self.editor.task:raise ValueError('Wait or cancel the current editor operation')
        self.viewport.stop();self.session=None
        self.loading=True;start=time.perf_counter();workspace=self.editor.workspace/'texture-sessions'/str(time.time_ns())
        self.open_started=start
        def work(task):
            task.stage('Open pinned texture session and stage real DX geometry once')
            session=LiverySession.open_package(path,workspace) if package else LiverySession.create(path,workspace)
            task.check();session.index();scene=workspace/'vehicle.mrpv'
            report=stage_vehicle(session.project.assets/'complete.dx',scene,profile=session.project.preview_profile_path())
            return session,scene,report
        def done(value):
            session,scene,report=value;self.session=session;self.selected=None
            self.model.blockSignals(True);self.model.setCurrentIndex(0);self.model.blockSignals(False)
            self.original.blockSignals(True);self.original.setChecked(False);self.original.blockSignals(False)
            self.viewport.start(scene,workspace/'viewport.json');self.metrics['open_stage_seconds']=time.perf_counter()-start
            self.populate();self.fill_metadata();self.artwork.load_preset();self.selection_text=''
            diagnostics=[w for s in report['sources'] for w in s.get('warnings',[])]+report.get('approximations',[])
            messages=list(dict.fromkeys(str(w) for w in diagnostics+session.warnings))
            self.warning.setText('Offline 3D preview · game lighting may differ')
            self.details_toggle.setText(f'Preview details ({len(messages)})')
            self.diagnostics.setPlainText('\n\n'.join(f'• {message}' for message in messages))
        def safe_work(task):
            try:return work(task)
            except Exception:self.loading=False;raise
        self.editor.run('Opening Texture Studio',safe_work,done)
    def populate(self):
        self.tree.clear();models={};first=None
        for name,usages in self.session.index().items():
            for usage in usages or [None]:
                key=usage['model'] if usage else 'Unbound textures'
                if key not in models:models[key]=W.QTreeWidgetItem(self.tree,[key])
                parent=models[key]
                if usage:parent=W.QTreeWidgetItem(parent,[f"draw {usage['draw']} / {usage['group']} / TEX{usage['stage']}"])
                item=W.QTreeWidgetItem(parent,[name]);item.setData(0,Q.Qt.ItemDataRole.UserRole,(name,usage));first=first or item
        self.tree.expandToDepth(0)
        if first:self.tree.setCurrentItem(first)
    def fill_metadata(self):
        self.loading_metadata=True
        for k,field in self.fields.items():field.setText(str(self.session.metadata.get(k,'')))
        self.origin.setCurrentText(self.session.metadata['origin']);self.variant.setText(self.session.metadata['model_variant']);self.loading_metadata=False;self.refresh_dirty()
    def metadata_changed(self,*unused):
        if not self.session or getattr(self,'loading_metadata',False):return
        self.session.metadata.update({k:v.text() for k,v in self.fields.items()});self.session.metadata.update(origin=self.origin.currentText());self.refresh_dirty()
    def refresh_dirty(self):
        if self.session:self.dirty.setText(('● Unsaved livery' if self.session.dirty else 'Saved livery')+' · '+self.session.metadata['livery_id'])
    def choose(self,item,*unused):
        data=item.data(0,Q.Qt.ItemDataRole.UserRole) if item else None
        if not data:return
        self.selected,self.selected_usage=data
        if self.viewport.hwnd:self.guard(self.show_selected)
    def show_selected(self):
        if not self.selected:return
        name=self.selected;session=self.session;t=session.project.texture(name)
        if self.original.isChecked():t=parse_dxt_bytes((session.project.baseline/name).read_bytes())
        usages=session.index()[name];visible=[self.selected_usage] if self.selected_usage else usages
        if self.all_uv.isChecked():visible=[u for u in usages if u['stage']==0 and (not self.selected_usage or u['model']==self.selected_usage['model'])]
        png=encode_png(t)
        if self.channel.currentText()!='RGBA':
            from PIL import Image
            from io import BytesIO
            from .texture_images import rgba_png
            im=Image.open(BytesIO(png)).convert('RGBA')
            if self.channel.currentText()=='Alpha':im=im.getchannel('A').convert('RGBA')
            else:im.putalpha(255)
            png=rgba_png(im.width,im.height,im.tobytes())
        info=self.uv.show_texture(png,visible,self.overlay.isChecked());self.uv.set_overlay(self.overlay.isChecked(),self.alpha.value()/100)
        self.uv_info.setText(info)
        self.details.setPlainText(json.dumps({'resource':name,'resolution':[t.width,t.height],'format':'FEED / BGRA32','alpha_range':[min(t.bgra[3::4]),max(t.bgra[3::4])],
            'edited':name in session.project.data['edits'],'baseline_sha256':session.project.data['inputs'][name],
            'source':str(session.project.baseline/name),'shared_owners':[{k:v for k,v in u.items() if k not in ('uv_triangles','uv_vertex_ids')} for u in usages],
            'warning':'Replacement affects ALL listed owners of this resource. Other resource/stage bindings stay unchanged.'},indent=2))
        if name in self.viewport.active:self.viewport.packet(2,name)
        else:self.viewport.message(0x8016)
        if self.selected_usage and self.selected_usage['stage']!=0 and not self.all_uv.isChecked():
            self.uv_info.setText('No qualified atlas UV for this generated/secondary stage. '+self.selected_usage['uv_status'])
        if name not in self.viewport.active:self.uv_info.setText('This resource is unbound/disabled or its stage is unsupported by the existing viewport. PNG authoring is available; no substituted material is shown.')
        self.refresh_dirty()
    def poll(self):
        if self.loading and self.editor.task is None and self.session is None:self.loading=False
        if self.loading and self.session and self.viewport.process:
            try:
                if self.viewport.attach():
                    from .service import sha
                    self.viewport.sent={n:sha((self.session.project.assets/n).read_bytes()) for n,u in self.session.index().items() if u}
                    self.loading=False;self.show_selected();self.editor.status.setText('Live Texture Studio ready · mouse orbit / wheel zoom / MMB pan');self.metrics['open_ready_seconds']=time.perf_counter()-self.open_started
            except Exception as error:self.loading=False;self.editor.status.setText(str(error));self.editor.last_error=str(error)
        # Synchronize an actual geometry pick back to texture/material without restarting anything.
        if self.viewport.hwnd and self.viewport.state:
            path=Path(str(self.viewport.state)+'.selection')
            if path.exists():
                text=path.read_text(encoding='utf-8')
                if text!=self.selection_text:
                    self.selection_text=text;lines=text.splitlines()
                    if len(lines)>2 and lines[2] in self.session.index():
                        self.selected=lines[2];self.selected_usage=next((u for u in self.session.index()[lines[2]] if lines[1].startswith(u['model']+':'+str(u['draw'])+':')),None);self.guard(self.show_selected)
    def sync(self):
        self.require();self.viewport.update_textures(self.session,self.original.isChecked());self.show_selected()
    def edit(self,fn):
        self.require();start=time.perf_counter();fn()
        self.original.blockSignals(True);self.original.setChecked(False);self.original.blockSignals(False)
        self.sync();elapsed=time.perf_counter()-start;self.metrics['last_edit_seconds']=elapsed
        self.editor.status.setText(f'Texture updated on the live model · {elapsed:.3f}s · camera retained. '+ ' | '.join(self.session.warnings))
    def export_png(self,path=None):
        name=self.target()
        path=path or W.QFileDialog.getSaveFileName(self,'Export texture (PNG retains alpha)',str(self.editor.workspace/(name+'.png')),EXPORT_FILTER)[0]
        if path:
            self.session.export_png(name,path,self.original.isChecked());self.editor.status.setText('Exported. '+' | '.join(self.session.warnings))
    def import_png(self,path=None):
        name=self.target();path=path or W.QFileDialog.getOpenFileName(self,'Import same-size image','',''+IMPORT_FILTER)[0]
        if path:self.edit(lambda:self.session.import_png(name,path,self.preserve.isChecked()))
    def reload_png(self):
        name=self.target();path=self.session.last_files.get(name)
        if not path:raise ValueError('Export or import this texture first')
        self.import_png(path)
    def export_all(self,folder=None):
        self.require();folder=folder or self.folder('New / empty PNG export folder')
        if folder:self.session.export_all(folder)
    def import_manifest(self,path=None):
        self.require();path=path or W.QFileDialog.getOpenFileName(self,'Import texture roundtrip manifest','','Manifest (textures.json)')[0]
        if path:self.edit(lambda:self.session.import_manifest(path,self.preserve.isChecked()))
    def export_uv(self,path=None):
        name=self.target()
        if not self.uv.paths:raise ValueError('No qualified UV layout for the selected stage')
        path=path or W.QFileDialog.getSaveFileName(self,'Export exact UV layout',str(self.editor.workspace/(name+'.uv.png')),'PNG (*.png)')[0]
        if path:self.session.output_path(Path(path));self.uv.export_uv(path)
    def restore(self):self.edit(lambda:self.session.project.restore(self.target()))
    def undo(self):self.edit(self.session.project.undo) if self.session else None
    def redo(self):self.edit(self.session.project.redo) if self.session else None
    def new_livery(self,name=None):
        self.require()
        if name is None:
            name,ok=W.QInputDialog.getText(self,'New livery from Stock','Livery name')
            if not ok:return
        if not self.confirm_discard():return
        self.edit(lambda:self.session.new_livery(name));self.fill_metadata();self.artwork.load_preset()
    def confirm_discard(self):
        if not self.session.dirty:return True
        choice=W.QMessageBox.warning(self,'Unsaved livery changes','Save the current livery before resetting to Stock?',W.QMessageBox.StandardButton.Save|W.QMessageBox.StandardButton.Discard|W.QMessageBox.StandardButton.Cancel,W.QMessageBox.StandardButton.Cancel)
        if choice==W.QMessageBox.StandardButton.Save:
            self.save_livery();return not self.session.dirty
        return choice==W.QMessageBox.StandardButton.Discard
    def duplicate_livery(self,name=None):
        self.require()
        if name is None:
            name,ok=W.QInputDialog.getText(self,'Duplicate current livery','New livery name',text=self.session.metadata['name']+' Copy')
            if not ok:return
        self.session.duplicate_current(name);self.fill_metadata();self.artwork.load_preset()
    def save_livery(self,folder=None):
        self.require();folder=folder or W.QFileDialog.getSaveFileName(self,'New portable livery folder',str(self.editor.workspace/'liveries'/self.session.metadata['livery_id']))[0]
        if folder:
            self.session.save_package(folder);self.refresh_dirty();self.editor.status.setText('Portable livery saved; original geometry, physics and IDs retained')
    def stop(self):self.viewport.stop()
