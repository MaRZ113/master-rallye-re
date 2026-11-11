"""Compile and run native registry/geometry checks on an authored candidate."""
import argparse,sys,struct,subprocess
from pathlib import Path
from vehicle_presentation_fix import Resources
from build_r_mod1_candidate import locate_toolchain,compiler_environment


def run(candidate,sdk,out):
    sys.path.insert(0,str(sdk.resolve()/'src'))
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    root=Path(__file__).resolve().parents[1];out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    candidate=candidate.resolve();r=Resources(candidate);registry=candidate/'MRMods/Vehicles/active/addon-brake-lamps.tsv'
    rows=registry.read_text().splitlines()[1:];data=bytearray(struct.pack('<I',len(rows)))
    for row in rows:
        family,layer,*_=row.split();m=parse_dx_bytes(r.read(f'DataGx/Vehicles/{family}/car.dx'));cases,_=logical_cases(m)
        d=next(d for d in m.physical_draws if cases.get(d.draw_index)==(1,2)and not d.flags_0x20[2]and bool(d.flags_0x20[0])==bool(int(layer)))
        vb=b''.join(struct.pack('<3f3f2f',*m.vertices.positions[i],*m.vertices.normals[i],*m.uv_sets[0].values[i])for i in range(d.vertex_base,d.vertex_base+d.local_vertex_max+1))
        ib=struct.pack('<'+'H'*d.index_count,*m.local_indices[d.index_start:d.index_start+d.index_count])
        data+=struct.pack('<I',len(vb))+vb+struct.pack('<I',len(ib))+ib
    fixture=out/'native-lamps.bin';fixture.write_bytes(data)
    body=parse_dx_bytes(r.read('DataGx/Vehicles/ForesterSTI/car.dx'))
    sources=[d for d in body.physical_draws if d.tag==2 and d.group_label is None and '.' not in d.record_path and not d.texture_tuple[0].startswith('breaklightson')]
    payload=bytearray(struct.pack('<I',len(sources)))
    for d in sources:
        vb=b''.join(struct.pack('<3f3f2f',*body.vertices.positions[i],*body.vertices.normals[i],*body.uv_sets[0].values[i])for i in range(d.vertex_base,d.vertex_base+d.local_vertex_max+1))
        ib=struct.pack('<'+'H'*d.index_count,*body.local_indices[d.index_start:d.index_start+d.index_count])
        payload+=struct.pack('<III',d.local_vertex_max+1,d.triangle_count,len(vb))+vb+struct.pack('<I',len(ib))+ib
    body_fixture=out/'forester-private-body.bin';body_fixture.write_bytes(payload)

    vc,tool=locate_toolchain();env=compiler_environment(vc,'x86');cl=tool/'bin/Hostx64/x86/cl.exe'
    build=root/'ps2-research/pc-port/.build/ps2-enabled/Release'
    for test in ('addon_lamp_registry_tests','addon_lamp_native_tests','forester_private_bootstrap_tests'):
        exe=out/(test+'.exe')
        renderer=root/'ps2-research/pc-port/.staging/ps2-enabled/modernization/renderer'
        args=[str(cl),'/nologo','/std:c++17','/EHsc','/O2','/MT','/Gy',
              '/I'+str(renderer/'include'),'/I'+str(renderer/'vendor/d3d8'),
              '/I'+str(root/'ps2-research/pc-port/renderer'),str(root/'tests'/(test+'.cpp')),
              '/Fe:'+str(exe),'/Fo:'+str(out/(test+'.obj'))]
        if test!='addon_lamp_registry_tests':args+=['/link',str(build/'proxy_core.lib'),'bcrypt.lib','user32.lib','gdi32.lib','advapi32.lib','/OPT:REF']
        result=subprocess.run(args,env=env,text=True,capture_output=True)
        (out/(test+'-build.log')).write_text(result.stdout+result.stderr)
        if result.returncode:print(result.stdout,result.stderr);result.check_returncode()
        command=[str(exe),str(registry)]+([str(fixture),str(candidate)]if test=='addon_lamp_native_tests'else[])
        if test=='forester_private_bootstrap_tests':command=[str(exe),str(body_fixture)]
        result=subprocess.run(command,text=True,capture_output=True)
        (out/(test+'.log')).write_text(result.stdout+result.stderr);print(result.stdout,result.stderr);result.check_returncode()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--sdk',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.candidate,a.sdk,a.output)
