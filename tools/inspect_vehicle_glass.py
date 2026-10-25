"""Audit native glass switch ownership without guessing a damage controller.

Reads user-supplied DX only; JSON contains numerical diagnostics, not assets.
"""
import argparse,json,hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry


def components(geometry):
    """Exact source position connectivity; no tolerance weld or pane inference."""
    owners={};parent=list(range(len(geometry.triangles)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,tri in enumerate(geometry.triangles):
        for v in tri:
            position=geometry.vertices[v].position
            if position in owners:parent[find(i)]=find(owners[position])
            else:owners[position]=i
    groups={}
    for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
    result=[]
    for indices in groups.values():
        points={geometry.vertices[v].position for t in indices for v in geometry.triangles[t]}
        result.append({'triangles':indices,'minimum':[min(p[k] for p in points) for k in range(3)],'maximum':[max(p[k] for p in points) for k in range(3)]})
    return result


def audit(raw):
    m=parse_dx_bytes(raw);g=source_geometry(m);rows=[]
    for group in m.draw_groups:
        root=group.root
        if root.tag!=7 or not (root.group_label or '').startswith('screen'):continue
        members=[d for d in m.physical_draws if d.draw_index in group.draw_indices]
        rows.append({'label':root.group_label,'controls':root.control_words,'members':[{'draw':d.draw_index,'tag':d.tag,'case':d.control_words,'textures':d.texture_tuple,'flags':list(d.flags_0x20),'triangles':len(g[d.draw_index].triangles),'components':components(g[d.draw_index])} for d in members]})
    return {'sha256':hashlib.sha256(raw).hexdigest(),'validated':m.diagnostics.validated,'glass_switches':rows,'boundary':'source structure and exact position connectivity; not native damage trigger emulation'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(audit(a.model.read_bytes()),indent=2)+'\n')
