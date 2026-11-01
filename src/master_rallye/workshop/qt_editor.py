"""Optional Qt Widgets vertical slice. Legacy Tk remains supported.

The existing D3D9 viewer is a coordinated external window, not an embedded Qt
renderer. Capture previews are cached. No game or runtime installer is started.
"""
from pathlib import Path
import copy
import json
import queue
import subprocess
import threading
import time
import math
from PySide6 import QtCore,QtGui,QtWidgets as W
from master_rallye import universal_vehicle_scene as u
from master_rallye.editable_vehicle import EditableVehicle,MODES,ROLES,build_fixture
from .preview_cache import PreviewCache,Task,Cancelled,stage,render
from master_rallye.source_scene_preview import VIEWS,viewer_command,preview_cull

STYLE='''
QWidget { background:#20252c; color:#e2e8ef; font:10pt "Segoe UI"; }
QMainWindow,QDialog { background:#161b21; }
QGroupBox { border:1px solid #3b4653; border-radius:5px; margin-top:10px; padding-top:14px; }
QGroupBox::title { color:#e5b66a; subcontrol-origin:margin; left:10px; }
QPushButton { background:#303943; border:1px solid #52606c; border-radius:4px; padding:7px 10px; }
QPushButton:hover { background:#46505b; } QPushButton:pressed { background:#615033; }
QPushButton:disabled { color:#7e8892; border-color:#353c45; }
QLineEdit,QDoubleSpinBox,QSpinBox,QComboBox,QListWidget,QPlainTextEdit { background:#11171e; border:1px solid #44505d; padding:4px; selection-background-color:#765a30; }
QWidget:focus { border-color:#e5b66a; }
QListWidget::item { padding:3px; } QListWidget::item:selected { background:#655030; color:white; }
QSlider::groove:horizontal { height:6px; background:#10161d; border-radius:3px; }
QSlider::handle:horizontal { background:#dfac5c; width:14px; margin:-5px 0; border-radius:6px; }
QProgressBar { border:1px solid #46505b; background:#11171e; text-align:center; }
QProgressBar::chunk { background:#bf8f45; } QTabBar::tab { background:#28313b; padding:9px 15px; }
QTabBar::tab:selected { background:#5d4b30; color:#ffdfa5; }
'''


class Editor(W.QMainWindow):
    def __init__(self,workspace,viewer):
        super().__init__();self.workspace=Path(workspace).absolute();u.unlinked(self.workspace);self.workspace.mkdir(parents=True,exist_ok=True)
        self.viewer=Path(viewer).absolute();self.cache=PreviewCache(self.workspace/'preview-cache-v1')
        self.project=None;self.path=None;self.selected_mesh=None;self.references={};self.process=None;self.native_preview_root=None
        self.results=queue.Queue();self.task=None;self.generation=0;self.started=0;self.photo=None;self.preview_path=None;self.last_error=None
        self.setWindowTitle('Rally Workshop 2.0 — Editable Garage · prototype');self.resize(1480,940)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating,True);self.setStyleSheet(STYLE)
        main=W.QWidget();self.setCentralWidget(main);layout=W.QVBoxLayout(main)
        header=W.QLabel('RALLY WORKSHOP 2.0   /   EDITABLE GARAGE');header.setStyleSheet('font: bold 19pt "Segoe UI"; color:#e7b76b; padding:8px;');layout.addWidget(header)
        toolbar=W.QHBoxLayout();layout.addLayout(toolbar);self.buttons={}
        for label,fn in [('Open source',self.open_source),('Reopen edit',self.open_edit),('Save',self.save),('Undo',self.undo),('Redo',self.redo),('Restore Original',self.restore),('Preview',self.preview),('Open 3D',self.interactive),('Build fixture',self.build),('Force Refresh',lambda:self.preview(refresh=True))]:
            b=W.QPushButton(label);b.clicked.connect(lambda checked=False,action=fn:self.guard(action));toolbar.addWidget(b);self.buttons[label]=b
        self.mode=W.QComboBox();self.mode.addItems(MODES);self.mode.setCurrentText('User Customized');toolbar.addWidget(self.mode)
        self.mode.currentTextChanged.connect(self.change_mode)
        migration=self.menuBar().addMenu('Compatibility');migration.addAction('Snapshot existing native family…',self.open_native)
        split=W.QSplitter();layout.addWidget(split,1)
        left=W.QWidget();ll=W.QVBoxLayout(left);self.library=W.QListWidget();self.library.setMaximumHeight(110);ll.addWidget(W.QLabel('OPEN SOURCE / PROJECT LIBRARY'));ll.addWidget(self.library)
        self.library.itemDoubleClicked.connect(lambda item:self.load_path(Path(item.data(QtCore.Qt.ItemDataRole.UserRole))))
        self.meshes=W.QListWidget();ll.addWidget(W.QLabel('MESHES — exact derived groups'));ll.addWidget(self.meshes,1);self.meshes.currentRowChanged.connect(self.select_mesh)
        self.faces=W.QListWidget();self.faces.setSelectionMode(W.QAbstractItemView.SelectionMode.ExtendedSelection);ll.addWidget(W.QLabel('FACES — select one or more stable IDs'));ll.addWidget(self.faces,1)
        split.addWidget(left)
        center=W.QWidget();cl=W.QVBoxLayout(center);self.image=W.QLabel('Open an immutable Universal Vehicle Scene, then edit its derived copy.');self.image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter);self.image.setMinimumSize(450,360);cl.addWidget(self.image,1)
        views=W.QHBoxLayout();self.view=W.QComboBox();self.view.addItems(VIEWS);self.view.setCurrentText('isometric');views.addWidget(self.view)
        self.view.currentTextChanged.connect(self.view_changed)
        self.brake=W.QCheckBox('Brake ON (native fixture preview)');views.addWidget(self.brake);cl.addLayout(views)
        native_button=W.QPushButton('Preview built native materials');native_button.clicked.connect(self.native_preview);views.addWidget(native_button)
        self.info=W.QPlainTextEdit();self.info.setReadOnly(True);self.info.setMaximumHeight(150);cl.addWidget(self.info);split.addWidget(center)
        tabs=W.QTabWidget();tabs.setMinimumWidth(340);split.addWidget(tabs);split.setSizes([320,800,360])
        geometry=W.QWidget();gl=W.QVBoxLayout(geometry);geometry_scroll=W.QScrollArea();geometry_scroll.setWidgetResizable(True);geometry_scroll.setWidget(geometry);tabs.addTab(geometry_scroll,'Geometry')
        self.vertex=W.QSpinBox();self.vertex.setRange(0,199999);gl.addWidget(W.QLabel('Vertex index'));gl.addWidget(self.vertex);self.vertex.valueChanged.connect(self.show_vertex)
        self.xyz=[]
        for axis in('X','Y','Z'):
            row=W.QHBoxLayout();row.addWidget(W.QLabel(axis));spin=W.QDoubleSpinBox();spin.setRange(-100000,100000);spin.setDecimals(6);row.addWidget(spin);gl.addLayout(row);self.xyz.append(spin)
        self.button(gl,'Move vertex',self.move_vertex);self.button(gl,'Add vertex at XYZ',self.add_vertex)
        self.button(gl,'Set vertex normal from XYZ',lambda:self.edit({'op':'normal','mesh':self.mid(),'index':self.vertex.value(),'value':[s.value()for s in self.xyz]}))
        self.button(gl,'Delete unused vertex',lambda:self.edit({'op':'delete_vertex','mesh':self.mid(),'index':self.vertex.value()}))
        uvrow=W.QHBoxLayout();self.uv=[]
        for label in('U','V'):
            uvrow.addWidget(W.QLabel(label));spin=W.QDoubleSpinBox();spin.setRange(-1000,1000);spin.setDecimals(6);uvrow.addWidget(spin);self.uv.append(spin)
        gl.addLayout(uvrow);self.button(gl,'Set vertex UV',lambda:self.edit({'op':'uv','mesh':self.mid(),'index':self.vertex.value(),'value':[s.value()for s in self.uv]}))
        self.triangle=W.QLineEdit('0,1,2');gl.addWidget(W.QLabel('New triangle indices'));gl.addWidget(self.triangle)
        self.button(gl,'Add face',lambda:self.edit({'op':'add_face','mesh':self.mid(),'vertices':[int(x.strip())for x in self.triangle.text().split(',')]}))
        self.button(gl,'Delete selected faces',lambda:self.edit({'op':'delete_faces','mesh':self.mid(),'faces':self.face_ids()}))
        self.button(gl,'Duplicate as independent equipment',self.duplicate)
        self.button(gl,'Add wheel backing quad',self.backing)
        self.button(gl,'Split selected faces',lambda:self.edit({'op':'split','mesh':self.mid(),'faces':self.face_ids()}))
        self.button(gl,'Merge compatible section…',self.merge)
        self.button(gl,'Flip selected faces',lambda:self.edit({'op':'flip_faces','mesh':self.mid(),'faces':self.face_ids()}))
        self.button(gl,'Translate component by XYZ',self.translate)
        self.button(gl,'Rotate / scale component…',self.transform)
        self.button(gl,'Hide component',lambda:self.set_visibility(False))
        self.button(gl,'Show all components',self.show_all)
        self.button(gl,'Orient winding to vertex normals (selected mesh)',lambda:self.edit({'op':'orient_winding','mesh':self.mid()}))
        self.button(gl,'Orient all derived groups to normals',self.orient_all)
        gl.addStretch()
        material=W.QWidget();ml=W.QVBoxLayout(material);material_scroll=W.QScrollArea();material_scroll.setWidgetResizable(True);material_scroll.setWidget(material);tabs.addTab(material_scroll,'Material / Glow')
        self.role=W.QComboBox();self.role.addItems(ROLES);ml.addWidget(W.QLabel('Native role'));ml.addWidget(self.role)
        self.coverage=W.QComboBox();self.coverage.addItems(('opaque','alpha_test','alpha_blend'));ml.addWidget(self.coverage)
        self.color=W.QLineEdit('255,255,255,255');ml.addWidget(W.QLabel('Vertex / Glow RGBA (0–255)'));ml.addWidget(self.color)
        self.opacity=W.QSlider(QtCore.Qt.Orientation.Horizontal);self.opacity.setRange(0,255);self.opacity.setValue(255);ml.addWidget(W.QLabel('Opacity'));ml.addWidget(self.opacity)
        self.button(ml,'Assign material to selected faces',self.assign)
        self.button(ml,'Assign current material to all groups',self.assign_all)
        self.button(ml,'Copy stock MR material onto selected faces',self.copy_stock)
        self.button(ml,'Select environment reference DXT',self.environment)
        self.button(ml,'Restore source material',self.reset_material)
        self.trigger=W.QComboBox();self.trigger.addItems(('always','brake'));ml.addWidget(W.QLabel('Glow trigger (separate from glass)'));ml.addWidget(self.trigger)
        self.button(ml,'Author Glow on selected faces',self.glow)
        self.button(ml,'Remove selected Glow',lambda:self.edit({'op':'remove_glow','faces':self.face_ids()}))
        ml.addWidget(W.QLabel('MR authoring replaces donor effects intentionally.\nSource Fidelity remains separate.\nGlass role does not invent damage zones.'));ml.addStretch()
        footer=W.QHBoxLayout();self.progress=W.QProgressBar();self.progress.setRange(0,1);footer.addWidget(self.progress)
        self.status=W.QLabel('Ready — original files stay immutable');footer.addWidget(self.status,1)
        cancel=W.QPushButton('Cancel');cancel.clicked.connect(self.cancel);footer.addWidget(cancel);layout.addLayout(footer)
        self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(40)
        for key,callback in [('Ctrl+S',self.save),('Ctrl+Z',self.undo),('Ctrl+Y',self.redo),('F5',self.preview)]:
            action=QtGui.QAction(self);action.setShortcut(QtGui.QKeySequence(key));action.triggered.connect(callback);self.addAction(action)

    def button(self,layout,label,fn):
        def action():
            if self.task:raise ValueError('Wait or cancel before editing')
            return fn()
        b=W.QPushButton(label);b.clicked.connect(lambda:self.guard(action));layout.addWidget(b);return b
    def guard(self,fn):
        try:return fn()
        except Exception as e:self.last_error=str(e);self.status.setText(str(e))
    def run(self,title,work,done):
        if self.task:self.status.setText('Cancel or wait for the current operation');return
        self.generation+=1;generation=self.generation;self.started=time.perf_counter();self.label=title;self.last_error=None
        task=Task(lambda label:self.results.put(('stage',generation,label,None)));self.task=task;self.progress.setRange(0,0)
        def worker():
            try:value=work(task);task.check();self.results.put(('done',generation,value,done))
            except Cancelled:self.results.put(('cancelled',generation,None,None))
            except Exception as e:self.results.put(('error',generation,str(e),None))
        threading.Thread(target=worker,daemon=True).start()
    def poll(self):
        try:
            while True:
                kind,generation,value,done=self.results.get_nowait()
                if generation!=self.generation:continue
                if kind=='stage':self.label=value;continue
                cancelled=self.task is not None and self.task.cancelled.is_set();self.task=None;self.progress.setRange(0,1)
                if cancelled or kind=='cancelled':self.status.setText('Cancelled safely');continue
                if kind=='error':self.last_error=value;self.status.setText(value+' — retry is available');continue
                self.guard(lambda:done(value))
        except queue.Empty:pass
        if self.task:self.status.setText(self.label+f' · {time.perf_counter()-self.started:.1f}s')
    def cancel(self):
        if self.task:self.task.cancelled.set()
    def open_source(self):
        path,_=W.QFileDialog.getOpenFileName(self,'Immutable UVS scene','','Source scene (scene.json)')
        if path:self.load_path(Path(path))
    def open_edit(self):
        path,_=W.QFileDialog.getOpenFileName(self,'Editable vehicle project',str(self.workspace),'Editable project (*.json)')
        if path:self.load_path(Path(path),editable=True)
    def open_native(self):
        folder=W.QFileDialog.getExistingDirectory(self,'Native family containing car.dx, complete.dx and wheel.dx')
        if not folder:return
        from master_rallye.native_family_scene import snapshot
        output=self.workspace/'native-snapshots'/str(time.time_ns())
        def work(task):
            task.stage('Verify native family and recover exact existing wheel instances')
            snapshot(Path(folder),output);task.check();return output/'scene.json'
        self.run('Compatibility migration',work,lambda path:self.load_path(path,editable=False))
    def load_path(self,path,editable=None):
        if editable is None:editable=path.name!='scene.json'
        mode=self.mode.currentText()
        def load(task):
            task.stage('Verify immutable parent and reopen derived journal')
            return EditableVehicle.open(path)if editable else EditableVehicle.create(path,mode,preview_cache=True)
        def done(project):
            self.project=project;self.path=path if editable else None;self.mode.blockSignals(True);self.mode.setCurrentText(project.document['mode']);self.mode.blockSignals(False)
            if not any(self.library.item(i).data(QtCore.Qt.ItemDataRole.UserRole)==str(path)for i in range(self.library.count())):
                item=W.QListWidgetItem(path.parent.name+' / '+path.name);item.setData(QtCore.Qt.ItemDataRole.UserRole,str(path));self.library.addItem(item)
            self.refresh();self.status.setText('Opened; edits stay in a separate journal')
        self.run('Opening project',load,done)
    def refresh(self):
        if not self.project:return
        self.preview_path=None
        old=self.selected_mesh;scene=self.project.evaluate();self.meshes.blockSignals(True);self.meshes.clear()
        for mesh in scene['meshes']:
            item=W.QListWidgetItem(mesh.get('name',mesh['id'])+' · '+str(len(mesh['triangles']))+' faces');item.setData(QtCore.Qt.ItemDataRole.UserRole,mesh['id']);self.meshes.addItem(item)
        ids=[m['id']for m in scene['meshes']];self.meshes.blockSignals(False);self.meshes.setCurrentRow(ids.index(old)if old in ids else 0)
        self.info.setPlainText(json.dumps(self.project.diagnostics(),indent=2));self.photo=None;self.image.setPixmap(QtGui.QPixmap());self.image.setText('Edits changed — Preview updates only affected cache layers.')
    def mid(self):
        if not self.project or not self.selected_mesh:raise ValueError('Select a derived mesh')
        return self.selected_mesh
    def mesh(self):return next(m for m in self.project.evaluate()['meshes']if m['id']==self.mid())
    def face_ids(self):
        ids=[x.text()for x in self.faces.selectedItems()]
        if not ids:raise ValueError('Select exact receiving faces; no implicit whole-body Glow')
        return ids
    def select_mesh(self,row):
        if row<0:return
        self.selected_mesh=self.meshes.item(row).data(QtCore.Qt.ItemDataRole.UserRole);mesh=self.mesh();self.faces.clear();self.faces.addItems(mesh.get('face_ids',[mesh['id']+':face:'+str(i)for i in range(len(mesh['triangles']))]));self.vertex.setMaximum(len(mesh['positions'])-1);self.show_vertex()
    def show_vertex(self,*unused):
        if not self.project or not self.selected_mesh:return
        ps=self.mesh()['positions'];index=min(self.vertex.value(),len(ps)-1)
        for spin,value in zip(self.xyz,ps[index]):spin.setValue(value)
        for spin,value in zip(self.uv,self.mesh()['uvs'][index]):spin.setValue(value)
    def edit(self,op):
        if self.task:raise ValueError('Wait or cancel before editing')
        if not self.project:raise ValueError('Open a source vehicle first')
        self.project.edit(op);self.refresh();self.status.setText('Derived edit applied; Undo available')
    def move_vertex(self):self.edit({'op':'vertex','mesh':self.mid(),'index':self.vertex.value(),'value':[s.value()for s in self.xyz]})
    def add_vertex(self):self.edit({'op':'add_vertex','mesh':self.mid(),'positions':[s.value()for s in self.xyz],'normals':[0,1,0],'uvs':[0,0]})
    def duplicate(self):
        owners=[n for n in self.project.evaluate()['nodes']if self.mid()in n['mesh_ids']]
        op={'op':'duplicate','mesh':self.mid(),'name':'User spare / equipment'}
        if len(owners)>1:
            selected,ok=W.QInputDialog.getItem(self,'Source instance','Duplicate which component instance?',[n['id']for n in owners],0,False)
            if not ok:return
            op['source_node']=selected
        self.edit(op)
    def translate(self):
        scene=self.project.evaluate();owners=[n for n in scene['nodes']if self.mid()in n['mesh_ids']]
        if len(owners)!=1:raise ValueError('Select a mesh with one instance')
        matrix=owners[0]['local_transform'][:]
        for i,spin in zip((3,7,11),self.xyz):matrix[i]+=spin.value()
        self.edit({'op':'transform','node':owners[0]['id'],'matrix':matrix})
    def merge(self):
        scene=self.project.evaluate();choices=[m['id']for m in scene['meshes']if m['id']!=self.mid()and m['material_id']==self.mesh()['material_id']]
        if not choices:raise ValueError('No same-material sections to merge')
        other,ok=W.QInputDialog.getItem(self,'Merge sections','Same-instance/material section',choices,0,False)
        if ok:self.edit({'op':'merge','mesh':self.mid(),'other':other})
    def transform(self):
        owners=[n for n in self.project.evaluate()['nodes']if self.mid()in n['mesh_ids']]
        if len(owners)!=1:raise ValueError('Select an explicit independent instance first')
        dialog=W.QDialog(self);dialog.setWindowTitle('Relative component rotation / scale');layout=W.QFormLayout(dialog);fields=[]
        for label,default in [('Rotate X degrees',0),('Rotate Y degrees',0),('Rotate Z degrees',0),('Scale X',1),('Scale Y',1),('Scale Z',1)]:
            spin=W.QDoubleSpinBox();spin.setRange(-360 if 'Rotate'in label else .001,360 if 'Rotate'in label else 100);spin.setDecimals(4);spin.setValue(default);layout.addRow(label,spin);fields.append(spin)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Ok|W.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addRow(buttons)
        if dialog.exec()!=W.QDialog.DialogCode.Accepted:return
        x,y,z=[math.radians(s.value())for s in fields[:3]];sx,sy,sz=[s.value()for s in fields[3:]]
        rx=[1,0,0,0,0,math.cos(x),-math.sin(x),0,0,math.sin(x),math.cos(x),0,0,0,0,1]
        ry=[math.cos(y),0,math.sin(y),0,0,1,0,0,-math.sin(y),0,math.cos(y),0,0,0,0,1]
        rz=[math.cos(z),-math.sin(z),0,0,math.sin(z),math.cos(z),0,0,0,0,1,0,0,0,0,1]
        scale=u.IDENTITY[:];scale[0]=sx;scale[5]=sy;scale[10]=sz
        delta=u.multiply(u.multiply(u.multiply(rz,ry),rx),scale)
        self.edit({'op':'transform','node':owners[0]['id'],'matrix':u.multiply(owners[0]['local_transform'],delta)})
    def backing(self):
        mesh=self.mesh();ps=mesh['positions'];lo=[min(p[i]for p in ps)for i in range(3)];hi=[max(p[i]for p in ps)for i in range(3)]
        x=(lo[0]+hi[0])/2
        geometry={'positions':[[x,lo[1],lo[2]],[x,hi[1],lo[2]],[x,hi[1],hi[2]],[x,lo[1],hi[2]]],
                  'normals':[[1,0,0]]*4,'uvs':[[0,0],[1,0],[1,1],[0,1]],'triangles':[[0,1,2],[0,2,3]],'material_id':mesh['material_id']}
        owners=[n for n in self.project.evaluate()['nodes']if self.mid()in n['mesh_ids']]
        if len(owners)!=1:raise ValueError('Select an explicitly instanced wheel mesh')
        self.edit({'op':'add_mesh','name':'User wheel backing — fit manually','geometry':geometry,'matrix':owners[0]['local_transform'],'parent_id':owners[0]['parent_id']})
    def set_visibility(self,value):
        owners=[n for n in self.project.evaluate()['nodes']if self.mid()in n['mesh_ids']]
        self.project.edit_many([{'op':'visibility','node':n['id'],'visible':value}for n in owners]);self.refresh()
    def show_all(self):
        if self.project:self.project.edit_many([{'op':'visibility','node':n['id'],'visible':True}for n in self.project.evaluate()['nodes']]);self.refresh()
    def orient_all(self):
        if not self.project:raise ValueError('Open an editable scene')
        if self.task:raise ValueError('Wait or cancel before editing')
        self.project.edit_many([{'op':'orient_winding','mesh':m['id']}for m in self.project.evaluate()['meshes']]);self.refresh()
    def rule(self):
        rgba=[int(x)for x in self.color.text().split(',')]
        if len(rgba)!=4 or any(not 0<=x<=255 for x in rgba):raise ValueError('RGBA must contain four bytes')
        rule={'mode':self.coverage.currentText(),'role':self.role.currentText(),'evidence':'Explicit user-selected MR adaptation in Qt Material Studio','vertex_rgba':rgba,'opacity':self.opacity.value()/255}
        if rule['mode']=='alpha_test':rule['alpha_ref']=128
        if rule['mode']=='alpha_blend':rule['alpha_override']=self.opacity.value()
        if rule['role']=='reflective_paint':
            if not self.references:raise ValueError('Select a native environment DXT reference first')
            key=next(iter(self.references));rule['environment_reference']={'key':key,'sha256':u.sha(self.references[key])}
        return rule
    def assign(self):self.edit({'op':'material','mesh':self.mid(),'faces':self.face_ids(),'rule':self.rule()})
    def assign_all(self):
        if not self.project:raise ValueError('Open source first')
        # Explicit bulk action, same authoring intent recorded per group.
        rule=self.rule();ids=[m['id']for m in self.project.evaluate()['meshes']]
        self.project.edit_many([{'op':'material','mesh':mid,'rule':rule}for mid in ids])
        self.refresh()
    def environment(self):
        name,_=W.QFileDialog.getOpenFileName(self,'Native MR environment DXT','','MR texture (*.dxt)')
        if name:
            from master_rallye.dxt import parse_dxt_bytes
            blob=u.read_bounded(Path(name),64*1024*1024);parse_dxt_bytes(blob);self.references={str(Path(name).absolute()):blob};self.status.setText('Environment pinned: '+u.sha(blob)[:16])
    def copy_stock(self):
        from master_rallye.editable_vehicle import copy_native_material
        name,_=W.QFileDialog.getOpenFileName(self,'Copy qualified native material settings','','MR model (*.dx)')
        if not name:return
        index,ok=W.QInputDialog.getInt(self,'Native reference draw','Draw index (inspect stock reference first)',0,0,8191)
        if not ok:return
        rule,references=copy_native_material(Path(name),index,self.role.currentText());self.references.update(references)
        self.edit({'op':'material','mesh':self.mid(),'faces':self.face_ids(),'rule':rule})
    def reset_material(self):
        mesh=self.mesh();origin=mesh['source'].get('derived_from_mesh')
        original=next((m for m in self.project.source['meshes']if m['id']==origin),None)
        if original is None:raise ValueError('User-created component has no original donor material; use Undo or assign a material')
        self.edit({'op':'reset_material','mesh':self.mid(),'faces':self.face_ids(),'original_material':original['material_id']})
    def glow(self):self.edit({'op':'glow','mesh':self.mid(),'faces':self.face_ids(),'trigger':self.trigger.currentText(),'rgba':[int(x)for x in self.color.text().split(',')]})
    def change_mode(self,mode):
        if not self.project:return
        if self.task:
            self.mode.blockSignals(True);self.mode.setCurrentText(self.project.document['mode']);self.mode.blockSignals(False);self.status.setText('Wait or cancel before changing workflow');return
        if mode=='Source Fidelity'and self.project.document['cursor']:
            self.status.setText('Restore Original first, or reopen source separately; edits are retained')
            self.mode.blockSignals(True);self.mode.setCurrentText(self.project.document['mode']);self.mode.blockSignals(False);return
        self.project.document['mode']=mode;self.refresh()
    def view_changed(self,*unused):
        self.cancel();self.photo=None;self.image.setPixmap(QtGui.QPixmap());self.image.setText('Camera changed — Preview reuses geometry and renders the selected view.')
    def undo(self):
        if self.project and not self.task:self.project.undo();self.refresh()
    def redo(self):
        if self.project and not self.task:self.project.redo();self.refresh()
    def restore(self):
        if self.project and not self.task:self.project.restore();self.refresh()
    def save(self):
        if not self.project:return
        if self.task:self.status.setText('Wait or cancel before saving');return
        name=str(self.path)if self.path else W.QFileDialog.getSaveFileName(self,'Save derived project',str(self.workspace/'vehicle.edit.json'),'Editable project (*.json)')[0]
        if name:
            try:self.project.save(Path(name));self.path=Path(name);self.status.setText('Derived journal saved atomically')
            except Exception as error:self.status.setText(str(error))
    def preview(self,*,refresh=False):
        if not self.project:return
        scene=self.project.evaluate();root=Path(self.project.document['source_path']).parent;view=self.view.currentText()
        def work(task):
            path,report,geometry_hit=stage(self.cache,scene,{'scene_root':root,'material_mode':'interpreted'},task=task,refresh=refresh)
            capture,image_hit=render(self.cache,self.viewer,path,report,view=view,cull=preview_cull(scene),task=task,refresh=refresh)
            return path,capture,geometry_hit,image_hit
        def done(value):
            self.preview_path,capture,g,i=value;self.photo=QtGui.QPixmap(str(capture));self.fit_image();self.status.setText(f'Geometry cache {g} · image cache {i} · {time.perf_counter()-self.started:.2f}s · neutral D3D9 approximation')
        self.run('Preview',work,done)
    def fit_image(self):
        if self.photo:self.image.setPixmap(self.photo.scaled(self.image.size(),QtCore.Qt.AspectRatioMode.KeepAspectRatio,QtCore.Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self,event):super().resizeEvent(event);self.fit_image()
    def interactive(self):
        if self.preview_path is None:self.status.setText('Generate Preview first');return
        if self.process and self.process.poll()is None:
            if getattr(self,'interactive_path',None)==self.preview_path:self.status.setText('Existing D3D9 viewport reused; orbit and selection remain intact');return
            self.process.terminate();self.process.wait(timeout=5)
        self.process=subprocess.Popen(viewer_command(self.viewer,self.preview_path,cull=preview_cull(self.project.evaluate()),view=self.view.currentText(),provenance='Editable derived project — no source-runtime equivalence'))
        self.interactive_path=self.preview_path
    def build(self):
        if not self.project:return
        if self.task:self.status.setText('Wait or cancel before building');return
        name,_=W.QFileDialog.getOpenFileName(self,'Qualified stock native DX template','','MR model (*.dx)')
        if not name:return
        scale,ok=W.QInputDialog.getDouble(self,'Explicit MR scale','Uniform source-to-MR authoring scale (not inferred metres)',1,.000001,100,6)
        if not ok:return
        basis_choice,ok=W.QInputDialog.getItem(self,'Explicit native authoring frame','Normalized scene → native fixture frame',
            ['Keep normalized axes','Turn 180 degrees around Y','Mirror Z (change handedness)'],0,False)
        if not ok:return
        basis=u.IDENTITY[:]
        if basis_choice=='Turn 180 degrees around Y':basis[0]=basis[10]=-1
        elif basis_choice=='Mirror Z (change handedness)':basis[10]=-1
        project=EditableVehicle(copy.deepcopy(self.project.document),copy.deepcopy(self.project.source));template=u.read_bounded(Path(name),128*1024*1024)
        output=self.workspace/'builds'/str(time.time_ns());refs=copy.deepcopy(self.references)
        def work(task):
            task.stage('Compile derived geometry and native material groups')
            # Persisted environment assignments remain pinned after reopening.
            for material in project.evaluate()['materials']:
                ref=material.get('authored_rule',{}).get('environment_reference')
                if ref and ref['key']not in refs:
                    blob=u.read_bounded(Path(ref['key']),64*1024*1024)
                    if u.sha(blob)!=ref['sha256']:raise ValueError('Native reference changed since assignment')
                    refs[ref['key']]=blob
            return build_fixture(project,output,template,scale=scale,normalized_to_mr=basis,references=refs)
        def done(report):
            self.native_preview_root=output/'native';self.info.setPlainText(json.dumps({'output':str(output),**report},indent=2));self.status.setText('Native fixture built; preview OFF/ON separately. No vehicle installed.')
        self.run('Native geometry/material fixture',work,done)

    def native_preview(self):
        if self.native_preview_root is None:self.status.setText('Build a native fixture first');return
        manifest=self.native_preview_root.parent/'manifest.json'
        if u.load_json(u.read_bounded(manifest,u.MAX_JSON_BYTES)).get('project_sha256')!=u.sha(u.canonical(self.project.document)):
            self.status.setText('Native fixture is from an older edit revision — rebuild before previewing');return
        from .preview_cache import identity
        from master_rallye.preview_scene import stage_vehicle
        root=self.native_preview_root;view=self.view.currentText();brake=self.brake.isChecked()
        def work(task):
            # Custom filename stages the already assembled complete geometry as
            # one model0; it does not invent wheel controllers/physics.
            files={p.name:p.read_bytes()for p in root.iterdir()if p.suffix=='.dxt' or p.name=='complete.dx'}
            key=identity({'kind':'native-material-fixture','files':{n:u.sha(b)for n,b in files.items()}})
            def build(folder,job):
                job.stage('Stage native material OFF/ON geometry')
                for name,blob in files.items():(folder/('fixture.dx'if name=='complete.dx'else name)).write_bytes(blob)
                stage_vehicle(folder/'fixture.dx',folder/'preview.mrpv')
                return {'basis':'normalized','display_name':'Derived native fixture'}
            folder,report,_=self.cache.get(key,build,task=task)
            return render(self.cache,self.viewer,folder/'preview.mrpv',report,view=view,cull='cw',native=True,brake=brake,task=task)
        def done(value):
            capture,hit=value;self.photo=QtGui.QPixmap(str(capture));self.fit_image();self.status.setText(f'Native MR material preview · brake {brake} · cache {hit} · D3D8 NOT TESTED')
        self.run('Native material preview',work,done)
    def closeEvent(self,event):
        self.cancel();self.generation+=1
        if self.process and self.process.poll()is None:self.process.terminate()
        event.accept()


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True);p.add_argument('--source',type=Path)
    args=p.parse_args(argv);app=W.QApplication.instance()or W.QApplication([]);app.setStyle('Fusion')
    window=Editor(args.workspace,args.viewer);window.show()
    if args.source:window.load_path(args.source)
    return app.exec()
