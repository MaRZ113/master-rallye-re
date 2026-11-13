from pathlib import Path
import hashlib,json,re,struct
root=Path(r'E:\RallyWorkshop_Sources\sources\Rally Championship Xtreme')
out=Path(r'E:\RallyWorkshop_Sources\exclusive_research')
cars=root/'Data'/'Cars'
rows=[]
for p in sorted(cars.glob('*.rcx'),key=lambda p:p.name.lower()):
 b=p.read_bytes(); matches=list(re.finditer(rb'[\x20-\x7e]{3,}\.(?:tex|qto|edg)\x00',b,re.I)); names=[m.group()[:-1].decode('ascii') for m in matches]
 rows.append({'file':p.name,'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'header_hex':b[:12].hex(),'name_occurrences':{ext:sum(n.lower().endswith('.'+ext) for n in names) for ext in ('tex','qto','edg')},'sample_names':names[:12]})
result={'source':str(root),'exe_sha256':hashlib.sha256((root/'Rally.exe').read_bytes()).hexdigest(),'method':'ASCII NUL terminated name scan; occurrences are not parsed container members','files':rows}
(out/'rcx_inventory.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('files',len(rows),'arcade',sum('_arcade.rcx' in x['file'].lower() for x in rows),'regular',sum('_arcade.rcx' not in x['file'].lower() for x in rows))
print('headers',sorted(set(x['header_hex'][:16] for x in rows)))
print('astra',next(x for x in rows if x['file']=='Astra.rcx'))
