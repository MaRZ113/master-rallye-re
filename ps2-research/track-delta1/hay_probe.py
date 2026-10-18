"""Turkey3 probe T7 step 1: add native gaAiHayBale Eggs to the PC RaceTest XML (loose file, channel B) at the first PS2 tumbleweed poses.

The PC executable's gaAiHayBale initializer renames the Egg, selects Misc/Haybale/haybaletest and creates the physical body itself
(mass 350, see pc-port/docs/rigid-port1.3), so only the Egg shell, position and the AI class name are authored. This is a channel test for
physics props, not a reproduction of the tumbleweed. Placed in the IContManager list like the PS2 tumbleweeds.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import gcoll_columns as gc  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402

EGG = '''      <Egg Name="{name}">
        <Value Name="Use en2d" Type="Bool" Value="False"/>
        <Value Name="Freezable" Type="Bool" Value="True"/>
        <Value Name="Hitable" Type="Bool" Value="True"/>
        <Value Name="Draw Priority" Type="Int" Value="3"/>
        <Value Name="Tick Priority" Type="Int" Value="3"/>
        <Value Name="Egg Group" Type="Int" Value="0"/>
        <Value Name="en3d Model Name" Type="String" Value="misc\haybale\haybaletest"/>
        <Value Name="en3d Matrix" Type="Matrix" Row0="1.00 0.00 0.00 0.00" Row1="0.00 1.00 0.00 0.00" Row2="0.00 0.00 1.00 0.00" Row3="{x:.2f} {y:.2f} {z:.2f} 1.00"/>
        <Value Name="en3d Draw 2D" Type="Bool" Value="False"/>
        <Value Name="en3d Interpolated" Type="Bool" Value="True"/>
        <Value Name="en3d Visible" Type="Bool" Value="True"/>
        <Value Name="en3d ZBuffered" Type="Bool" Value="True"/>
        <Value Name="en2d Model Name" Type="String" Value="Null"/>
        <Value Name="en2d Matrix" Type="Matrix" Row0="1.00 0.00 0.00 0.00" Row1="0.00 1.00 0.00 0.00" Row2="0.00 0.00 1.00 0.00" Row3="0.00 0.00 0.00 1.00"/>
        <Value Name="en2d FileType" Type="Int" Value="0"/>
        <Value Name="en2d Image Bank Index" Type="Int" Value="0"/>
        <Value Name="en2d Draw 2D" Type="Bool" Value="False"/>
        <Value Name="en2d Interpolated" Type="Bool" Value="True"/>
        <Value Name="en2d Visible" Type="Bool" Value="True"/>
        <Value Name="en2d ZBuffered" Type="Bool" Value="True"/>
        <Value Name="en2d 2dGlobal" Type="Bool" Value="False"/>
        <AI_List>
          <AI No="0">
            <Value Name="AI Name" Type="String" Value="gaAiHayBale"/>
            <gaAiHayBale/>
          </AI>
          <AI No="1">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
          <AI No="2">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
          <AI No="3">
            <Value Name="AI Name" Type="String" Value="Null"/>
          </AI>
        </AI_List>
      </Egg>
'''.replace('\n', '\r\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pc-root', type=Path, required=True)
    ap.add_argument('--ps2-scene', type=Path, required=True)
    ap.add_argument('--count', type=int, default=3)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    pc = (a.pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    ps2 = a.ps2_scene.read_bytes().decode('latin1')
    pcn = gc.pc_nodes(a.pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    poses = []
    for m in re.finditer(r'<Value Name="AI Name" Type="String" Value="gaAiRigidBody"/>', ps2):
        egg = ps2[ps2.rfind('<Egg ', 0, m.start()):m.start()]
        row3 = re.findall(r'Row3="([^"]+)"', egg)[0].split()
        poses.append((float(row3[0]), float(row3[1]), float(row3[2])))
    out = pc
    list_start = out.index(b'    <List Name="IContManager">\r\n')
    list_end = out.index(b'    </List>\r\n', list_start)
    eggs = b''
    report = []
    for k, (x, y, z) in enumerate(poses[:a.count], 1):
        g = gw.ground_at(pcn, x, z)
        yy = (g + 1.5) if g is not None else y
        report.append({'name': f'hay{k}', 'ps2_pose': [x, y, z], 'pc_ground': g, 'used_y': round(yy, 2)})
        eggs += EGG.format(name=f'hay{k}', x=x, y=yy, z=z).encode('latin1')
    out = out[:list_end] + eggs + out[list_end:]
    a.output.write_bytes(out)
    print(report)
    print('source', hashlib.sha256(pc).hexdigest()[:12], 'candidate', hashlib.sha256(out).hexdigest()[:12], len(out) - len(pc), 'bytes added')


if __name__ == '__main__':
    main()
