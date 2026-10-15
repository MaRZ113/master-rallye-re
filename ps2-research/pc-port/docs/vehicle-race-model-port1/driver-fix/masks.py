# Topology-labelled SVG evidence; source face ordinals, never runtime bbox classification.
from pathlib import Path
import json,runpy
H=Path(__file__).resolve().parent
g=runpy.run_path(str(H/'components.py'));v=g['v'];ix=g['ix'];meshes=g['meshes'];out=g['out']
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><rect width="1200" height="760" fill="white"/>']
for col,(a,b,title) in enumerate([(0,1,'FRONT / X,Y'),(2,1,'SIDE / Z,Y')]):
 parts.append(f'<text x="{col*600+20}" y="25">{title}: red static body; orange face; purple head insert; gray interior</text>')
 for root in (0,7):
  m=meshes[root];fs=[ix[m[5]+i:m[5]+i+3]for i in range(0,m[6],3)]
  for c in out[str(root)]['components']:
   seed=c['seed_face'];color='red' if root==0 and seed in(71,73) else 'orange' if root==0 and seed in(123,222) else 'purple' if root==7 and seed in(6,10) else '#aaaaaa'
   for fi in c['faces']:
    points=' '.join(f'{col*600+300+v[j][a]*155:.2f},{570-v[j][b]*300:.2f}'for j in fs[fi]);parts.append(f'<polygon points="{points}" fill="none" stroke="{color}" stroke-width=".6"/>')
parts.append('</svg>');(H.parents[2]/'.analysis/driver-source-topology.svg').write_text(''.join(parts))
mask={'schema_version':1,'private_asset_sha256':g['hashlib'].sha256(g['b']).hexdigest(),'ps2_source_sha256':g['sha'].hex(),'rule':'EXACT_SOURCE_TOPOLOGY_COMPONENT_MEMBERSHIP_NO_RUNTIME_SPATIAL_HEURISTICS','roots':{}}
for root,seeds in ((0,(71,73,123,222)),(7,(6,10))):
 cs=out[str(root)]['components'];drop=sorted(i for c in cs if c['seed_face']in seeds for i in c['faces']);total=sum(c['face_count']for c in cs)
 mask['roots'][str(root)]={'source_face_count':total,'excluded_faces':drop,'kept_faces':[i for i in range(total)if i not in drop],'exclude_count':len(drop),'keep_count':total-len(drop),'component_seeds':seeds,'component_hashes':[c['index_sha256']for c in cs if c['seed_face']in seeds]}
H.joinpath('driver-masks.json').write_text(json.dumps(mask,indent=2)+'\n')
