"""Read-only private asset audit and conservative nine-bin view-window bound."""
import hashlib
import json
from pathlib import Path
import time
from collections import defaultdict
import prepare_all as source

def main():
    path=Path(__file__).parent
    registry=json.loads((path/'coverage-registry.json').read_text())
    source.grass.MAX_POINTS=registry['artifact_point_budget']
    rows=[];start=time.monotonic()
    for row in registry['courses']:
        for category,item in row['categories'].items():
            data=(source.PORT/'.assets/grass'/item['filename']).read_bytes()
            actual=source.grass.validate_artifact(data,item['artifact']['sha256'],
                    (row['psm_sha256'],item['gxi_sha256'],row['pc_dx_sha256']))
            if actual!=item['artifact']:raise ValueError('Artifact metadata changed')
            bins={}
            for i in range(actual['bin_count']):
                x,z,first,count=source.grass.BIN.unpack_from(data,source.grass.HEADER.size+i*source.grass.BIN.size)
                bins[x,z]=count
            # Any60-unit X/Z window intersects at most9 bins of width8.
            # Count entire intersected bins: conservative, not live visiblecount.
            windows=defaultdict(int)
            for (x,z),count in bins.items():
                for dx in range(9):
                    for dz in range(9):windows[x-dx,z-dz]+=count
            maximum=max(windows.values())
            rows.append({'course':row['course'],'category':category,'filename':item['filename'],
                         'private_sha256':hashlib.sha256(data).hexdigest(),
                         'conservative_9x9_bin_point_bound':maximum,'existing_visible_guard':16384,
                         'all_windows_proven_below_guard':maximum<=16384})
    summary={'schema_version':1,'course_count':len(registry['courses']),'asset_count':len(rows),
             'total_source_points':sum(i['point_count'] for r in registry['courses'] for i in r['categories'].values()),
             'total_artifact_bytes':sum(i['artifact']['size'] for r in registry['courses'] for i in r['categories'].values()),
             'max_category_points':max(i['point_count'] for r in registry['courses'] for i in r['categories'].values()),
             'total_eligible_triangles':sum(i['eligible_triangles'] for r in registry['courses'] for i in r['categories'].values()),
             'total_exact_pc_matched_triangles':sum(i['strict_matched_triangles'] for r in registry['courses'] for i in r['categories'].values()),
             'rows':rows,'runtime_validation':'NOT_PERFORMED'}
    (path/'asset-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print('Validated',len(rows),'assets; seconds',round(time.monotonic()-start,3),flush=True)
    print('max conservative viewwindow',max(r['conservative_9x9_bin_point_bound'] for r in rows),flush=True)

if __name__=='__main__':main()
