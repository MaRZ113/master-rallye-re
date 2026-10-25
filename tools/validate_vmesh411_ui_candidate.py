"""Independent UI-only scope and reference checks on the finished runtime bundle."""
from __future__ import annotations
import argparse,json,sys,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank,archive_member
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from master_rallye.addon_sdk.manifest import AddonValidationError
from build_vmesh_impreza_experimental import dump,sha_file
import prepare_vehicle_unlock_overlay as scene

def audit(stage,before):
    current=stage/'runtime/resource-root';old=before/'runtime/resource-root'
    a={p.relative_to(current).as_posix():p for p in current.rglob('*') if p.is_file()}
    b={p.relative_to(old).as_posix():p for p in old.rglob('*') if p.is_file()}
    expected={prefix+suffix for prefix,count,template,size in BANKS.values() for suffix in ('.dxb',f'_{count:03d}_000.dxt')}
    if set(a)-set(b)!=expected or set(b)-set(a):raise ValueError('unexpected resource file-set change')
    changes=[n for n in b if a[n].read_bytes()!=b[n].read_bytes()]
    if changes!=['DataScene/FrontendScreens/VehicleSelect.xml']:raise ValueError('unexpected existing resource change: '+str(changes))
    path='DataScene/FrontendScreens/VehicleSelect.xml';oldtext=b[path].read_text(encoding='utf-8-sig');text=a[path].read_text(encoding='utf-8-sig')
    lo,hi=scene._egg_span(oldtext,'T2_Car8');low,high=scene._egg_span(text,'T2_Car8')
    if oldtext[:lo]!=text[:low] or oldtext[hi:]!=text[high:]:raise ValueError('unrelated Vehicle Select controls changed')
    expected_widget=scene._replace_value(oldtext[lo:hi],'en2d Image Bank Index','32')
    expected_widget=scene._replace_value(expected_widget,'True Value','32')
    if expected_widget!=text[low:high]:raise ValueError('unexpected Subaru widget change')
    plan=json.loads((stage/'runtime/addon-plan.json').read_text());row=next(r for r in plan['addons'] if r['physical_id']==27)
    previous=json.loads((before/'runtime/addon-plan.json').read_text());prior=next(r for r in previous['addons'] if r['physical_id']==27)
    modified=json.loads(json.dumps(row))
    for role in BANKS:modified['frontend'][role]=prior['frontend'][role]
    if modified!=prior:raise ValueError('unrelated ID27 manifest property changed')
    if [r for r in plan['addons'] if r['physical_id']!=27]!=[r for r in previous['addons'] if r['physical_id']!=27]:raise ValueError('unrelated addon changed')
    reports={}
    with zipfile.ZipFile(current/'Data.sma') as stock:
        for role,(prefix,count,template,size) in BANKS.items():
            beforebank=parse_bank(archive_member(stock,prefix+'.dxb'));bank=parse_bank(a[prefix+'.dxb'].read_bytes())
            if bank['count']!=count+1 or bank['records'][:-1]!=beforebank['records'] or row['frontend'][role]!={'policy':'project_frame','frame':count}:
                raise ValueError('stock bank records/reference changed')
            frame=prefix+f'_{count:03d}_000.dxt';t=parse_dxt_bytes(a[frame].read_bytes())
            if bank['names'][count]!=Path(frame).stem or (t.width,t.height)!=size or t.word_0x04!=1 or t.word_0x08!=zlib.crc32(t.bgra)&0xffffffff:raise ValueError('invalid UI DXT format/checksum')
            px=decode_rgba_pixels(t)
            if not any(px[3::4]) or not any(v==0 for v in px[3::4]):raise ValueError('UI alpha missing')
            # No stock texture override: every old frame resolves to its original archive member.
            for name in beforebank['names']:
                oldpath=prefix.rsplit('/',1)[0]+'/'+name+'.dxt';archive_member(stock,oldpath)
                if oldpath in a:raise ValueError('stock frame unexpectedly overridden')
            reports[role]={'frame':count,'dimensions':list(size),'stock_records_retained':count,'crc32_valid':True,'sha256':sha_file(a[frame])}
    ops=json.loads((stage/'runtime/native-patch-manifest.json').read_text())['operations']
    oldops=json.loads((before/'runtime/native-patch-manifest.json').read_text())['operations'];diffs=[]
    if len(ops)!=len(oldops):raise ValueError('native operation count changed')
    for x,y in zip(oldops,ops):
        if (x['file_offset'],x['expected_original_bytes'],x.get('installation'))!=(y['file_offset'],y['expected_original_bytes'],y.get('installation')):raise ValueError('native patch scope changed')
        one,two=bytes.fromhex(x['replacement_bytes']),bytes.fromhex(y['replacement_bytes'])
        if len(one)!=len(two):raise ValueError('native patch span changed')
        for i,(aa,bb) in enumerate(zip(one,two)):
            if aa!=bb:
                if i==0 or one[i-1]!=0x6a or (aa,bb)!=(prior['frontend']['smallcarsheet']['frame'],row['frontend']['smallcarsheet']['frame']):raise ValueError('unexpected native byte change')
                diffs.append({'file_offset':x['file_offset']+i,'old':aa,'new':bb,'instruction':'PUSH imm8 SmallCarSheet frame'})
    if len(diffs)!=1:raise ValueError('native ID27 selector change absent/ambiguous')
    candidate=stage/'review'/(stage.name+'-candidate.zip')
    with zipfile.ZipFile(candidate) as z:
        if z.testzip():raise ValueError('candidate ZIP CRC failed')
        for name in expected|set(changes):
            if z.read(stage.name+'/runtime/resource-root/'+name)!=a[name].read_bytes():raise ValueError('candidate asset differs')
    result={'status':'PASS_OFFLINE_RUNTIME_TEST_PENDING','resource_count':len(a),'retained_resource_count':len(b)-len(changes),
        'added_resources':sorted(expected),'changed_resources':changes,'all_stock_frames_preserved':True,'all_vehicle_resources_byte_identical':True,
        'native_selector_byte_delta':diffs,'roles':reports,'candidate_sha256':sha_file(candidate)}
    dump(stage/'reports/final-ui-audit.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--before',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.stage,a.before),indent=2))
