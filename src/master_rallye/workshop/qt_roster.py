"""Vehicle Manager panel inside the existing Qt Workshop application."""
from pathlib import Path
import threading
from PySide6 import QtCore, QtWidgets as W
from .roster import Manager


class RosterDialog(W.QDialog):
    completed=QtCore.Signal(object,object)

    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle('Vehicle Manager / native roster');self.resize(1000,660)
        self.manager=None;self.busy=False;self.lists={}
        layout=W.QVBoxLayout(self);row=W.QHBoxLayout();layout.addLayout(row)
        self.folder=W.QLineEdit();row.addWidget(self.folder)
        choose=W.QPushButton('Choose game folder…');choose.clicked.connect(self.choose);row.addWidget(choose)
        self.load=W.QPushButton('Open roster');self.load.clicked.connect(self.open);row.addWidget(self.load)
        layout.addWidget(W.QLabel('Edit class order, addon availability and DEMO packages. Apply writes only MRMods/Vehicles. Close the game before Apply.'))
        self.controls=W.QWidget();v=W.QVBoxLayout(self.controls);layout.addWidget(self.controls,1)
        classes=W.QHBoxLayout();v.addLayout(classes,1)
        for cls in ('T1','T2','T3'):
            box=W.QGroupBox(cls);col=W.QVBoxLayout(box);lst=W.QListWidget();self.lists[cls]=lst;col.addWidget(lst);classes.addWidget(box)
            for label,fn in [('Move up',lambda c=cls:self.move(c,-1)),('Move down',lambda c=cls:self.move(c,1)),('Remove / Restore addon',lambda c=cls:self.toggle(c))]:
                b=W.QPushButton(label);b.clicked.connect(lambda checked=False,action=fn:action());col.addWidget(b)
        self.packages=W.QListWidget();self.packages.setMaximumHeight(105);v.addWidget(self.packages)
        actions=W.QHBoxLayout();v.addLayout(actions)
        for label,fn in [('Import active roster as base',self.import_base),('Install .mrcar…',self.install),('Enable / Disable package',self.toggle_package),('Apply roster',self.apply),('Disable roster (Stock)',self.stock)]:
            b=W.QPushButton(label);b.clicked.connect(fn);actions.addWidget(b)
        self.status=W.QLabel('Choose a game/candidate folder. No files are changed when opening it.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.completed.connect(self.operation_finished);self.controls.setEnabled(False)
        saved=QtCore.QSettings('MasterRallye','Workshop').value('roster/game','')
        if saved:self.folder.setText(str(saved))

    def choose(self):
        path=W.QFileDialog.getExistingDirectory(self,'Game or private candidate folder',self.folder.text())
        if path:self.folder.setText(path);self.open()

    def open(self):
        if self.busy:return
        path=Path(self.folder.text())
        if not (path/'MRallye.exe').is_file():return self.error('Select the folder containing MRallye.exe.')
        self.manager=Manager(path);self.controls.setEnabled(True)
        QtCore.QSettings('MasterRallye','Workshop').setValue('roster/game',str(path.resolve()));self.refresh()

    def error(self,text):W.QMessageBox.warning(self,'Vehicle Manager',str(text))

    def refresh(self):
        try:
            m=self.manager;n=m.native();plan=m.plan();removed=set(m.selection().get('removed',[]))
            for cls,lst in self.lists.items():
                lst.clear()
                for vid in plan[cls]+[i for i in n['classes'][cls] if i in removed]:
                    item=W.QListWidgetItem(f"{vid:2d}  {n['names'].get(vid,'')}"+(' (removed)'if vid in removed else''));item.setData(QtCore.Qt.ItemDataRole.UserRole,vid);lst.addItem(item)
            self.packages.clear()
            for p in m.list_packages():
                item=W.QListWidgetItem(('Enabled: 'if p['enabled'] else'Disabled: ')+p['file']);item.setData(QtCore.Qt.ItemDataRole.UserRole,p['file']);self.packages.addItem(item)
            self.status.setText('Selection saved. Apply roster activates it; original game resources and DLLs stay unchanged.')
        except Exception as e:self.status.setText(f'No usable base roster: {e}. Import the active roster first.')

    def edit(self,fn):
        if self.busy or not self.manager:return
        try:fn();self.refresh()
        except Exception as e:self.error(e)

    def move(self,cls,delta):
        item=self.lists[cls].currentItem()
        if item:self.edit(lambda:self.manager.move(item.data(QtCore.Qt.ItemDataRole.UserRole),delta))

    def toggle(self,cls):
        item=self.lists[cls].currentItem()
        if not item:return
        vid=item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.edit(lambda:(self.manager.restore if vid in self.manager.selection().get('removed',[])else self.manager.remove)(vid))

    def import_base(self):
        if not self.manager:return
        force=self.manager.base.exists()
        if force and W.QMessageBox.question(self,'Replace base snapshot?','Replace the manager base with the active roster? Existing selection is retained.')!=W.QMessageBox.StandardButton.Yes:return
        self.work(lambda:self.manager.import_base(force=force))

    def install(self):
        path,_=W.QFileDialog.getOpenFileName(self,'Install vehicle variant package','','Vehicle package (*.mrcar)')
        if path:self.edit(lambda:self.manager.install(Path(path)))

    def toggle_package(self):
        item=self.packages.currentItem()
        if not item:return
        name=item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.edit(lambda:self.manager.uninstall(name) if name in self.manager.selection().get('packages',[]) else self.manager.install(self.manager.packages/name))

    def apply(self):self.work(self.manager.apply)

    def stock(self):
        if W.QMessageBox.question(self,'Disable active roster?','Move the active roster aside and use Stock on the next launch?')==W.QMessageBox.StandardButton.Yes:self.work(self.manager.stock)

    def work(self,fn):
        if self.busy:return
        self.busy=True;self.controls.setEnabled(False);self.load.setEnabled(False);self.status.setText('Building and validating roster…')
        def run():
            try:self.completed.emit(fn(),None)
            except Exception as e:self.completed.emit(None,str(e))
        threading.Thread(target=run,daemon=True).start()

    def operation_finished(self,result,error):
        self.busy=False;self.controls.setEnabled(True);self.load.setEnabled(True);self.refresh()
        if error:self.error(error);self.status.setText('Operation failed: '+error)
        else:self.status.setText('Completed. '+str(result))

    def closeEvent(self,event):
        if self.busy:event.ignore()
        else:super().closeEvent(event)
