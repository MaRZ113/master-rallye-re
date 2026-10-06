"""Read-only stock course actor-template/start-grid coverage; no terrain proof."""
import argparse,json,math,re,xml.etree.ElementTree as ET
from pathlib import Path
from r_ai1_mixed_class import REPOSITORY,sha256

def inspect_xml(data):
    root=ET.fromstring(data);slots=[]
    for egg in root.iter('Egg'):
        m=re.fullmatch(r'Car([0-9]+)',egg.get('Name',''))
        if m and any(v.get('Value')=='gaBootAICar' for v in egg.iter('Value')):slots.append(int(m[1]))
    lists=[l for l in root.iter('List') if l.get('Name')=='StartArea'];positions=[]
    if len(lists)==1:
        for marker in lists[0].findall('Marker'):
            values=[v for v in marker.findall('Value') if v.get('Name')=='Marker Pos']
            if len(values)!=1:raise ValueError('Ambiguous start marker')
            p=tuple(map(float,values[0].get('Value','').split()))
            if len(p)!=3 or not all(math.isfinite(x) for x in p):raise ValueError('Invalid marker')
            positions.append(p)
    width=math.dist(positions[0],positions[1]) if len(positions)>=2 else 0
    contiguous=next((n for n in range(9) if n not in slots),8)
    viable=slots==list(range(8)) and len(positions)>=2 and width>0
    return dict(authored_actor_indices=slots,contiguous_actor_capacity=min(contiguous,8),start_marker_count=len(positions),start_edge_length=width,
        grid='DYNAMIC_N / 0x48EB40',static_viable_total=8 if viable else None,structurally_ready_for_eight=viable,
        terrain_clearance_runtime='UNKNOWN',evidence='CONFIRMED_BY_CORPUS + CONFIRMED_BY_EXE')

def audit(data_root):
    sdk=json.loads((REPOSITORY/'research/r5t_sdk1/retail-corpus-validation.json').read_text(encoding='utf-8'))
    projects=sdk['course_projects']
    if len(projects)!=36:raise ValueError('Expected canonical 36 retail courses')
    rows=[]
    for p in projects:
        rel=p['race_test_xml'];data=(data_root/rel).read_bytes()
        rows.append(dict(course=p['identity'],path=rel,sha256=sha256(data),**inspect_xml(data)))
    return dict(phase='R-AI2.1',stock_course_count=len(rows),all_stock_courses_audited=True,
        all_structurally_ready_for_eight=all(r['structurally_ready_for_eight'] for r in rows),courses=rows,
        limit='Templates and a nondegenerate StartArea permit the native count-based grid; geometry clearance and eight actual spawns are not runtime-proven.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data_root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=audit(a.data_root);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='courses'},indent=2))
if __name__=='__main__':main()
