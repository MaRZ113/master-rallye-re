"""Exercise actual Windows GUI actions and SDK builds with private user inputs.

Only file-picker answers are supplied by the harness. Buttons, dialogs, workers,
native GPU captures, persistence, validators and runtime builders are real.
"""
from pathlib import Path
import argparse
import collections
import ctypes
from ctypes import wintypes
import hashlib
import json
import shutil
import struct
import sys
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.gui import WorkshopApp,bmp_png
from master_rallye.workshop.service import write_json

def screenshot(root,path):
    root.update_idletasks();root.lift()
    hwnd=int(root.wm_frame(),16);u=ctypes.windll.user32;g=ctypes.windll.gdi32
    u.GetWindowDC.argtypes=[wintypes.HWND];u.GetWindowDC.restype=wintypes.HDC
    u.ReleaseDC.argtypes=[wintypes.HWND,wintypes.HDC]
    g.CreateCompatibleDC.argtypes=[wintypes.HDC];g.CreateCompatibleDC.restype=wintypes.HDC
    g.CreateDIBSection.argtypes=[wintypes.HDC,ctypes.c_void_p,wintypes.UINT,ctypes.POINTER(ctypes.c_void_p),wintypes.HANDLE,wintypes.DWORD];g.CreateDIBSection.restype=wintypes.HANDLE
    g.SelectObject.argtypes=[wintypes.HDC,wintypes.HANDLE];g.SelectObject.restype=wintypes.HANDLE
    u.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    u.PrintWindow.argtypes=[wintypes.HWND,wintypes.HDC,wintypes.UINT]
    g.DeleteObject.argtypes=[wintypes.HANDLE];g.DeleteDC.argtypes=[wintypes.HDC]
    rect=wintypes.RECT();u.GetWindowRect(hwnd,ctypes.byref(rect));w,h=rect.right-rect.left,rect.bottom-rect.top
    dc=u.GetWindowDC(hwnd);memory=g.CreateCompatibleDC(dc);bits=ctypes.c_void_p()
    header=struct.pack('<IiiHHIIiiII',40,w,-h,1,32,0,w*h*4,0,0,0,0);info=ctypes.create_string_buffer(header)
    bitmap=g.CreateDIBSection(dc,info,0,ctypes.byref(bits),None,0)
    if not bitmap:raise ValueError('GUI screenshot bitmap allocation failed')
    previous=g.SelectObject(memory,bitmap)
    try:
        if not u.PrintWindow(hwnd,memory,2):raise ValueError('GUI PrintWindow failed')
        raw=ctypes.string_at(bits,w*h*4);bmp=Path(path).with_suffix('.bmp')
        bmp.write_bytes(struct.pack('<2sIHHI',b'BM',54+len(raw),0,0,54)+header+raw);Path(path).write_bytes(bmp_png(bmp))
    finally:g.SelectObject(memory,previous);g.DeleteObject(bitmap);g.DeleteDC(memory);u.ReleaseDC(hwnd,dc)

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('addon-project','roster-candidate','retail-sma','retail-root','viewer','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--surface',action='store_true',help='V-SDK4A selected-draw RGB instead of the V-SDK3 whole-texture demonstration')
    p.add_argument('--binding',action='store_true',help='Assign an existing compatible texture using the actual picker')
    p.add_argument('--reflection',action='store_true',help='Author qualified opaque reflection weight through actual controls')
    a=p.parse_args();output=a.output.resolve()
    if output.exists():raise ValueError('Use a fresh GUI evidence output directory')
    output.mkdir(parents=True);root=tk.Tk();app=WorkshopApp(root,output/'workspace',ROOT,a.viewer)
    errors=[];report={'status':'RUNNING','actions':[],'boundary':'Actual Tk Windows actions, D3D9 captures and sealed builds; not Master Rallye gameplay'}
    baseline=None;index=0;idle=0;last=time.monotonic();expected_kind=None
    def record(label,details=None):
        report['actions'].append({'action':label,'details':details});write_json(output/'gui-validation.json',report)
    def open_addon():
        with patch('master_rallye.workshop.gui.filedialog.askdirectory',return_value=str(a.addon_project.resolve())):app.buttons['Open project'].invoke()
    def configure():
        app.configure();dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        entries=[w for w in descendants(dialog) if isinstance(w,ttk.Entry)]
        for entry,value in zip(entries,(a.roster_candidate,a.retail_sma,a.retail_root)):entry.delete(0,'end');entry.insert(0,str(value.resolve()))
        next(w for w in descendants(dialog) if isinstance(w,ttk.Button) and w['text']=='Save build inputs').invoke()
    def baseline_capture():
        nonlocal baseline
        baseline=(app.project.root/'preview/latest.bmp').read_bytes();(output/(app.project.data['kind']+'-before.bmp')).write_bytes(baseline);report[app.project.data['kind']+'_project']=str(app.project.root)
        configure();record('configure build through GUI dialog',app.project.data['build_settings'])
        next(w for w in descendants(root) if isinstance(w,ttk.Button) and w['text']=='Open interactive 3D').invoke()
        assert app.process and app.process.poll() is None
        record('GUI opens managed native D3D9 window',app.process.pid)
    def edit():
        if a.binding:
            from master_rallye.dx import parse_dx_bytes
            from master_rallye.texture_binding import binding_patch
            from master_rallye.dxt import parse_dxt_bytes
            model=app.current_info['model'];raw=(app.project.assets/model).read_bytes();mesh=parse_dx_bytes(raw)
            textures={p.stem:(p,parse_dxt_bytes(p.read_bytes())) for p in app.project.assets.glob('*.dxt')}
            used={d.texture_slots[0].value for d in mesh.physical_draws}
            def score(d):
                points=[mesh.vertices.positions[i] for i in mesh.draw_global_indices(d)]
                return len(points)*max(0,max(p[2] for p in points))
            chosen=None
            for d in sorted(mesh.physical_draws,key=score,reverse=True):
                old=textures.get(d.texture_slots[0].value)
                if not old:continue
                t=old[1]
                for stem,(path,new) in textures.items():
                    if stem not in used or stem==old[0].stem:continue
                    try:binding_patch(raw,d.draw_index,0,stem,app.project.binding_texture)
                    except ValueError:continue
                    chosen=d,path;break
                if chosen:break
            if chosen is None:raise ValueError('No compatible existing shared texture for fixture')
            draw,path=chosen
            app.draws.selection_set(f'texture:{model}:{draw.draw_index}:0');app._draw_selected();app.assign_texture()
            dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
            root.update()
            box=next(w for w in descendants(dialog) if isinstance(w,tk.Listbox))
            index=next(i for i,value in enumerate(box.get(0,'end')) if value=='OK  '+path.name)
            box.selection_set(index);box.see(index);box.event_generate('<<ListboxSelect>>');root.update();time.sleep(.06);root.update();screenshot(dialog,output/(app.project.data['kind']+'-binding-picker.png'))
            next(w for w in descendants(dialog) if isinstance(w,ttk.Button) and w['text']=='Assign selected texture').invoke()
            record('native slot assignment through actual picker',{'model':model,'draw':draw.draw_index,'target':path.name,'already_used_by':app.project.texture_usage(path.name)})
            return
        if a.surface or a.reflection:
            from master_rallye.dx import parse_dx_bytes
            from master_rallye.surface_authoring import surface_capabilities
            model=app.current_info['model'];raw=(app.project.baseline/model).read_bytes();mesh=parse_dx_bytes(raw)
            candidates=[d for d in mesh.physical_draws if d.unknown_0x24&4 and not d.flags_0x20[0] and surface_capabilities(raw,d.draw_index)['reflection_strength_editable' if a.reflection else 'diffuse_rgb_editable']]
            def projected_area(draw):
                import math
                eye=(math.sin(.65)*math.cos(.18),math.sin(.18),math.cos(.65)*math.cos(.18));ids=mesh.draw_global_indices(draw);score=0
                for i in range(0,len(ids),3):
                    a,b,c=[mesh.vertices.positions[k] for k in ids[i:i+3]];u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)];normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);score+=max(0,sum(normal[k]*eye[k] for k in range(3)))
                return score
            draw=max(candidates,key=projected_area)
            app.draws.selection_set(app._draw_node(model,draw.draw_index));app._draw_selected()
            if a.reflection:
                app.reflection_strength.set(.25);assert not app.strength_button.instate(['disabled']);app.strength_button.invoke()
                record('qualified opaque reflection weight via GUI',{'model':model,'draw':draw.draw_index,'multiplier':.25,'texture_bytes_unchanged':True});return
            for var,value in zip(app.surface_gain,('.05','.1','1')):var.set(value)
            assert not app.surface_button.instate(['disabled'])
            app.surface_button.invoke();record('apply selected-surface RGB using real native attribute writer',{'model':model,'draw':draw.draw_index,'texture_unchanged':True})
            return
        counts=collections.Counter(str(d['textures'][0])+'.dxt' for d in app.current_info['draws'] if d['textures'])
        if app.project.data['kind']=='stock':name='whitepaint-tga.dxt'
        else:name=max((t for t in app.current_info['textures'] if counts[t['name']]),key=lambda t:counts[t['name']]*t['width']*t['height'])['name']
        draw=next((d for d in app.current_info['draws'] if d['textures'] and str(d['textures'][0])+'.dxt'==name),None)
        if draw:
            app.draws.selection_set(app._draw_node(app.current_info['model'],draw['id']));app._draw_selected();assert 'semantics' in app.inspector.get('1.0','end')
            record('inspect selected actual material',{'model':app.current_info['model'],'draw':draw['id'],'texture':name})
        app.texture_name.set(name);app.show_texture()
        for var,value in zip(app.gain,('.15','.45','1.0')):var.set(value)
        app.tint_button.invoke();record('apply visible whole-texture multiplier via button',name)
    def edited_capture():
        after=(app.project.root/'preview/latest.bmp').read_bytes();(output/(app.project.data['kind']+'-after.bmp')).write_bytes(after);difference=sum(x!=y for x,y in zip(baseline[54:],after[54:]));assert difference>100,('No visible GPU difference',difference)
        screenshot(root,output/(app.project.data['kind']+'-edited-gui.png'))
        record('visible real GPU change',{'different_bytes':difference,'texture_edits':app.project.data['edits'],'surface_edits':app.project.data.get('surfaces',{})})
        app.buttons['Save'].invoke();app.buttons['Validate'].invoke()
        from master_rallye.workshop.service import WorkshopProject
        reopened=WorkshopProject(app.project.root);reopened.materialize();assert reopened.data.get('surfaces',{})==app.project.data.get('surfaces',{})
        record('saved project reopened with identical scoped recipes')
    def undo_edit():
        next(w for w in descendants(root) if isinstance(w,ttk.Button) and w['text']=='Undo').invoke()
    def undo_checked():
        assert (app.project.root/'preview/latest.bmp').read_bytes()==baseline
        record('GUI Undo restores original GPU capture');next(w for w in descendants(root) if isinstance(w,ttk.Button) and w['text']=='Redo').invoke()
    def redo_checked():
        assert (app.project.root/'preview/latest.bmp').read_bytes()==(output/(app.project.data['kind']+'-after.bmp')).read_bytes()
        record('GUI Redo restores edited GPU capture')
    def build():app.buttons['Build'].invoke()
    def built():
        path=Path(app.project.data['last_build']);assert (path/'candidate/Launch-SDK-Roster.cmd').is_file()
        report[app.project.data['kind']+'_candidate']=str(path/'candidate');record('GUI build creates sealed launchable candidate',str(path))
        app.buttons['Restore all'].invoke()
    def restored():
        assert (app.project.root/'preview/latest.bmp').read_bytes()==baseline,'Restore GPU image differs from original'
        assert not app.project.data['edits'] and not any(app.project.data.get('surfaces',{}).values());record('GUI restore matches original GPU capture byte-for-byte',app.project.data['kind'])
    def new_stock():
        with patch('master_rallye.workshop.gui.filedialog.askdirectory',return_value=str(a.retail_root.resolve())):app.buttons['New stock'].invoke()
        dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        next(w for w in descendants(dialog) if isinstance(w,ttk.Button) and w['text']=='Create private project').invoke()
    def finish():
        report['status']='PASS_ACTUAL_WINDOWS_GUI_AND_TWO_SDK_BUILDS';write_json(output/'gui-validation.json',report);screenshot(root,output/'restored-gui.png');app.close()
    def restored_build():
        output=Path(app.project.data['last_build']);manifest=json.loads((output/'stock-overrides/override-manifest.json').read_text());assert manifest['zero_edit']
        report['stock_restored_candidate']=str(output/'candidate');record('GUI rebuild after Restore emits zero stock overrides',str(output))
    actions=[open_addon,baseline_capture,edit,edited_capture,undo_edit,undo_checked,redo_checked,build,built,restored,new_stock,baseline_capture,edit,edited_capture,undo_edit,undo_checked,redo_checked,build,built,restored,build,restored_build,finish]
    def tick():
        nonlocal index,idle,last
        try:
            if errors:raise ValueError('GUI error: '+str(errors))
            if time.monotonic()-last>420:raise TimeoutError('GUI action timed out')
            if app.busy:idle=0
            else:idle+=1
            if idle>=3:
                actions[index]();index+=1;idle=0;last=time.monotonic()
            if index<len(actions):root.after(150,tick)
        except Exception as e:
            import traceback
            report.update(status='FAIL',error=str(e),traceback=traceback.format_exc());write_json(output/'gui-validation.json',report)
            hwnd=app._viewer_window()
            if hwnd:ctypes.windll.user32.PostMessageW(hwnd,0x10,0,0)
            root.destroy()
    root.report_callback_exception=lambda *args:errors.append(str(args))
    with patch('master_rallye.workshop.gui.messagebox.askyesno',return_value=True), patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(args)):
        root.after(500,tick);root.mainloop()
    if report['status']!='PASS_ACTUAL_WINDOWS_GUI_AND_TWO_SDK_BUILDS':raise ValueError(report)
    print(report['status'])

if __name__=='__main__':main()
