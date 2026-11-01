"""Disposable preview-only cache. Native builds still perform full validation.

Source reopen checks only its manifest-listed dependencies, never a game tree.
Memory hits trust unchanged filesystem identities/times, not just path names.
Persistent generated artifacts are content verified before use. No pickle/code
or private cache is admitted as original source or native approval evidence.
"""
from __future__ import annotations
from collections import OrderedDict
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading
import time
import uuid
from master_rallye import universal_vehicle_scene as u

VERSION='workshop-preview-cache/1'
MAX_ARTIFACTS=512  # UVS permits256 textures plus staged geometry/metadata.


class Cancelled(Exception):pass


class Task:
    def __init__(self, progress=None):
        self.cancelled=threading.Event();self.progress=progress or (lambda stage:None)
    def check(self):
        if self.cancelled.is_set():raise Cancelled('Cancelled safely; source/project unchanged')
    def stage(self,label):self.check();self.progress(label)


def fingerprint(path):
    path=Path(path).absolute();u.unlinked(path);s=path.stat()
    if not path.is_file():raise ValueError('Regular dependency file required')
    return [str(path),s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def source_dependencies(path):
    path=Path(path).absolute();manifest=path.parent/'manifest.json'
    doc=u.load_json(u.read_bounded(manifest,2*1024*1024));files=doc.get('files')
    if not isinstance(files,dict)or not 1<=len(files)<=1024:raise ValueError('Preview manifest dependency budget')
    checked=set();rows=[]
    # Check each shared directory once per request rather than walking the same
    # long Windows ancestry for every stream. All children still get fresh stat.
    for file in [manifest,*[path.parent/u.relative_name(n)for n in sorted(files)]]:
        for parent in reversed([file,*file.parents]):
            if parent in checked:continue
            if parent.is_symlink()or(parent.exists()and getattr(parent.stat(),'st_file_attributes',0)&0x400):
                raise ValueError('Linked preview dependency')
            checked.add(parent)
        s=file.stat()
        if not file.is_file():raise ValueError('Regular source dependency required')
        rows.append([str(file),s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns])
    return rows


def identity(value):return u.sha(u.canonical({'version':VERSION,'value':value}))


class SceneMemory:
    def __init__(self, limit=4):self.limit=limit;self.entries=OrderedDict();self.lock=threading.RLock()
    def load(self,path,*,refresh=False,task=None):
        path=Path(path).absolute();task=task or Task();task.stage('Checking source scene dependencies')
        before=source_dependencies(path);key=str(path)
        with self.lock:
            cached=self.entries.get(key)
            if not refresh and cached and cached[0]==before:
                self.entries.move_to_end(key);task.check();return copy.deepcopy(cached[1]),True
        task.stage('Verifying source scene and private resource hashes')
        scene=u.load_scene(path);task.check()
        if source_dependencies(path)!=before:raise ValueError('Source dependencies changed while opening')
        with self.lock:
            self.entries[key]=(before,copy.deepcopy(scene));self.entries.move_to_end(key)
            while len(self.entries)>self.limit:self.entries.popitem(last=False)
        return scene,False


class PreviewCache:
    def __init__(self,root,*,max_bytes=512*1024*1024):
        self.root=Path(root).absolute();u.unlinked(self.root)
        if type(max_bytes)is not int or not 1024<=max_bytes<=16*1024**3:raise ValueError('Bounded cache quota required')
        self.max_bytes=max_bytes;self.lock=threading.RLock()
        self.stats={'hits':0,'misses':0,'recovered':0}

    def _entry(self,key):
        u._hash(key);path=self.root/key;u.unlinked(path);return path

    def _read(self,path):
        doc=u.load_json(u.read_bounded(path/'entry.json',1024*1024))
        if doc.get('version')!=VERSION or doc.get('key')!=path.name:raise ValueError('Stale cache version/key')
        files=doc.get('files',{})
        if not isinstance(files,dict)or not 1<=len(files)<=MAX_ARTIFACTS:raise ValueError('Cache file budget')
        total=0
        for name,row in files.items():
            u.relative_name(name);size=row['bytes'];u._size(size,256*1024*1024);total+=size
            if total>self.max_bytes:raise ValueError('Cache entry exceeds quota')
            raw=u.read_bounded(path/name,size)
            if len(raw)!=size or u.sha(raw)!=row['sha256']:raise ValueError('Corrupt preview cache artifact')
        os.utime(path/'entry.json',None)
        return doc

    def _remove(self,path):
        # Delete cache-owned directories only; never follow reparse points.
        if path.parent!=self.root:raise ValueError('Cache containment')
        u.unlinked(path)
        for p in path.rglob('*'):u.unlinked(p)
        shutil.rmtree(path)

    def get(self,key,build,*,refresh=False,task=None):
        task=task or Task();path=self._entry(key)
        task.check();self.root.mkdir(parents=True,exist_ok=True)
        with self.lock,self._process_lock(task):
            task.check()
            if path.exists():
                if not refresh:
                    try:
                        doc=self._read(path);self.stats['hits']+=1;return path,doc['report'],True
                    except (ValueError,OSError,KeyError,TypeError):self.stats['recovered']+=1
                self._remove(path)
            self.stats['misses']+=1
            temporary=self.root/('.pending-'+uuid.uuid4().hex);temporary.mkdir()
            try:
                report=build(temporary,task);task.check();files={};total=0
                for p in sorted(temporary.rglob('*')):
                    u.unlinked(p)
                    if not p.is_file():continue
                    size=p.stat().st_size;total+=size
                    if total>self.max_bytes or len(files)>=MAX_ARTIFACTS:raise ValueError('Preview cache output budget')
                    files[p.relative_to(temporary).as_posix()]={'bytes':size,'sha256':u.sha(u.read_bounded(p,256*1024*1024))}
                if not files:raise ValueError('Empty preview cache output')
                doc={'version':VERSION,'key':key,'files':files,'report':report}
                (temporary/'entry.json').write_bytes(u.canonical(doc));task.check()
                # Another process may have won. Its artifacts must verify first.
                if path.exists():self._read(path);self._remove(temporary)
                else:temporary.rename(path)
                self.cleanup(keep=key);return path,report,False
            except BaseException:
                if temporary.exists():self._remove(temporary)
                raise

    @contextmanager
    def _process_lock(self,task):
        """Serialize commits/eviction between Workshop processes, cancellably."""
        path=self.root/'.lock';u.unlinked(path)
        with path.open('a+b')as stream:
            stream.seek(0,2)
            if not stream.tell():stream.write(b'0');stream.flush()
            deadline=time.monotonic()+60;locked=False
            try:
                while not locked:
                    task.check();stream.seek(0)
                    try:
                        if os.name=='nt':
                            import msvcrt
                            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                        else:
                            import fcntl
                            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                        locked=True
                    except OSError:
                        if time.monotonic()>deadline:raise TimeoutError('Preview cache is busy; retry')
                        task.cancelled.wait(.05)
                yield
            finally:
                if locked:
                    stream.seek(0)
                    if os.name=='nt':
                        import msvcrt
                        msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

    def cleanup(self,*,keep=None):
        entries=[];total=0
        if not self.root.exists():return
        for path in self.root.iterdir():
            if path.is_dir()and path.name.startswith('.pending-'):
                u.unlinked(path)
                if time.time()-path.stat().st_mtime>24*3600:self._remove(path)
                continue
            if not path.is_dir()or len(path.name)!=64:continue
            u.unlinked(path)
            try:
                size=sum(p.stat().st_size for p in path.rglob('*')if p.is_file())
                stamp=(path/'entry.json').stat().st_mtime_ns
            except OSError:continue
            total+=size;entries.append((stamp,path,size))
        for _,path,size in sorted(entries,key=lambda row:row[0]):
            if total<=self.max_bytes:break
            if path.name==keep:continue
            self._remove(path);total-=size


def renderer_revision(viewer):
    # Stat identity is not a renderer provenance claim. Hash only on replacement.
    key=tuple(fingerprint(viewer))
    with _renderer_lock:
        if key not in _renderers:
            _renderers.clear();_renderers[key]=u.sha(u.read_bounded(Path(viewer),64*1024*1024))
        return _renderers[key]


def stage(cache,scene,options,*,task=None,refresh=False):
    from master_rallye.source_scene_preview import stage_source_scene
    from master_rallye import source_scene_preview
    options=dict(options);root=Path(options.pop('scene_root'))
    for protected in(root,Path(scene['source']['root']),*map(Path,scene['source'].get('protected_roots',[]))):
        a=cache.root.resolve();b=protected.resolve()
        if a==b or a.is_relative_to(b)or b.is_relative_to(a):raise ValueError('Preview cache overlaps protected source')
    # Covers edited geometry/materials/visibility, typed preview options and all
    # manifest-listed sidecars. Camera is deliberately absent from this layer.
    key=identity({'kind':'stage','scene':scene,'dependencies':source_dependencies(root/'scene.json'),
                  'options':options,'stager':u.sha(Path(source_scene_preview.__file__).read_bytes())})
    def build(folder,job):
        job.stage('Preparing D3D9 geometry and textures')
        return stage_source_scene(scene,folder/'preview.mrpv',scene_root=root,**options)
    path,report,hit=cache.get(key,build,refresh=refresh,task=task)
    return path/'preview.mrpv',report,hit


def render(cache,viewer,preview,report,*,view,cull,task=None,refresh=False,native=False,brake=False):
    import subprocess
    from master_rallye.source_scene_preview import viewer_command,capture_startup_info
    task=task or Task();key=identity({'kind':'capture','preview':u.sha(Path(preview).read_bytes()),
                                   'renderer':renderer_revision(viewer),'orchestrator':u.sha(Path(__file__).read_bytes()),
                                   'view':view,'cull':cull,'basis':report['basis'],'native':native,'brake':brake,'provenance':report['display_name']})
    def build(folder,job):
        job.stage('Rendering D3D9 '+view);capture=folder/'capture.bmp'
        if native:
            camera={'front':1,'rear':2,'left':6,'right':3,'top':5,'isometric':4}
            if view not in camera:raise ValueError('Unsupported native view')
            command=[str(viewer),'--scene',str(preview),'--model','race','--preset',str(camera[view]),'--capture',str(capture),'--cull',cull,'--provenance','Authored native fixture; D3D8 owner qualification pending']
            if brake:command.append('--brake')
        else:command=viewer_command(viewer,preview,view=view,capture=capture,provenance=report['display_name'],basis=report['basis'],cull=cull)
        process=subprocess.Popen(command,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),startupinfo=capture_startup_info())
        start=time.monotonic()
        try:
            while process.poll()is None:
                job.check()
                if time.monotonic()-start>45:raise TimeoutError('D3D9 capture timeout')
                job.cancelled.wait(.02)
            if process.returncode:raise ValueError('D3D9 capture failed: '+str(process.returncode))
            from PIL import Image
            with Image.open(capture)as image:image.verify()
            return {'view':view,'seconds':time.monotonic()-start,'renderer_sha256':renderer_revision(viewer)}
        finally:
            if process.poll()is None:process.terminate();process.wait(timeout=5)
    folder,_,hit=cache.get(key,build,refresh=refresh,task=task)
    return folder/'capture.bmp',hit


_renderer_lock=threading.Lock();_renderers={}
SCENES=SceneMemory()
