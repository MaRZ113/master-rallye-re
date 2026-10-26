"""Build the asset-free native viewport and a runnable Rally Workshop launcher."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]

def build(output=None):
    output=Path(output or ROOT/'.research-output/rally-workshop').resolve();output.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(ROOT/'tools/build_vehicle_previewer.py'),'--output',str(output/'native-build')],check=True)
    executable=output/'bin/mr-vehicle-previewer.exe';executable.parent.mkdir(exist_ok=True)
    built=output/'native-build/Release/mr-vehicle-previewer.exe'
    try:shutil.copyfile(built,executable)
    except PermissionError:
        executable=executable.with_name('mr-vehicle-previewer-'+hashlib.sha256(built.read_bytes()).hexdigest()[:12]+'.exe')
        if not executable.exists():shutil.copyfile(built,executable)
    interpreter=Path(sys.executable).with_name('pythonw.exe')
    if not interpreter.is_file():interpreter=Path(sys.executable)
    art=output/'assets/workshop';art.mkdir(parents=True,exist_ok=True)
    for name in ('rally-workshop.ico','rally-workshop.svg','LICENSE.txt'):shutil.copyfile(ROOT/'assets/workshop'/name,art/name)
    shutil.copytree(ROOT/'docs/sdk/help',output/'docs/sdk/help',dirs_exist_ok=True)
    workspace=output.parent/(output.name+'-workspace')
    (output/'Launch-Rally-Workshop.cmd').write_text('@echo off\ncd /d "'+str(ROOT)+'"\n"'+str(interpreter)+'" "'+str(ROOT/'tools/rally_workshop.py')+'" --workspace "'+str(workspace)+'" --viewer "'+str(executable)+'"\n')
    report={'status':'BUILT_WINDOWS_APPLICATION','viewer_path':str(executable),'viewer_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),'launcher':str(output/'Launch-Rally-Workshop.cmd'),'assets_bundled':False,'requirements':'Windows, Python with Tk/Pillow; NumPy for Classic qualification and Unicorn2.1.4 for native Audio Studio audition (pip install -e .[workshop]); MSVC/CMake for native builds'}
    (output/'application-build.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
    print(json.dumps(build(a.output),indent=2))
