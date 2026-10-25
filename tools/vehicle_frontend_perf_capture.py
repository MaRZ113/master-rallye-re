"""Read-only Windows sampler for the opt-in native frontend QPC counters."""
import argparse,ctypes,hashlib,json,struct,time
from pathlib import Path
from vehicle_frontend_perf_native import RETAIL_SHA256,COUNTER_STRIDE,STATE_BYTES,STAGES
DECODER_CALL=0x558cba
ORIGINAL_DECODER=0x581120


def find_binding(value):
    hits=[];bulk=[]
    def visit(item):
        if isinstance(item,dict):
            if {'stages','state_va','state_bytes','counter_stride'}<=set(item):hits.append(item)
            else:
                for key,nested in item.items():
                    if key=='frontend_bulk_read':bulk.append(nested)
                    visit(nested)
        elif isinstance(item,list):
            for nested in item:visit(nested)
    visit(value)
    if len(hits)!=1:raise ValueError('expected exactly one native frontend profiler binding')
    binding=hits[0]
    if binding['counter_stride']!=COUNTER_STRIDE or binding['state_bytes']!=STATE_BYTES or not 0x10000000<=binding['state_va']<=0x10040000-STATE_BYTES:raise ValueError('unsupported native profiler layout')
    if [row['name'] for row in binding['stages']]!=[row[0] for row in STAGES]:raise ValueError('unsupported native profiler stages')
    if len(bulk)>1:raise ValueError('ambiguous native bulk decoder binding')
    target=ORIGINAL_DECODER
    if bulk:
        if not isinstance(bulk[0],dict) or type(bulk[0].get('entry_va')) is not int or not 0x10000000<=bulk[0]['entry_va']<0x10040000:raise ValueError('unsupported native bulk decoder entry')
        target=bulk[0]['entry_va']
    return {**binding,'decoder_path':{'mode':'canonical_loose_bulk' if bulk else 'original_scalar','call_va':DECODER_CALL,'target_va':target}}


def verify_decoder(memory,binding):
    selected=binding.get('decoder_path')
    if not selected:raise ValueError('capture binding lacks decoder identity; use find_binding on the full native manifest')
    expected=b'\xe8'+struct.pack('<i',selected['target_va']-DECODER_CALL-5);observed=memory(DECODER_CALL,5)
    if observed!=expected:raise ValueError('running DXT decoder does not match selected baseline/bulk candidate')
    return {**selected,'observed_bytes':observed.hex(),'verified':True}


def decode(raw,binding,frequency):
    if len(raw)!=STATE_BYTES or frequency<=0:raise ValueError('invalid telemetry snapshot')
    rows=[]
    for i,stage in enumerate(binding['stages']):
        lock,calls,total,maximum,last=struct.unpack_from('<IIQQQ',raw,i*COUNTER_STRIDE)
        if lock:raise ValueError('counter row is busy; retry')
        rows.append({'stage':stage['name'],'calls':calls,'total_ms':total*1000/frequency,'maximum_since_launch_ms':maximum*1000/frequency,'last_ms':last*1000/frequency})
    return rows


def difference(first,last):
    rows=[]
    for a,b in zip(first,last):
        if a['stage']!=b['stage'] or b['calls']<a['calls'] or b['total_ms']<a['total_ms']:raise ValueError('counter reset or incompatible stages')
        count=b['calls']-a['calls'];duration=b['total_ms']-a['total_ms']
        rows.append({'stage':a['stage'],'calls':count,'total_ms':duration,'average_ms':duration/count if count else None,'maximum_since_launch_ms':b['maximum_since_launch_ms']})
    return rows


def capture(pid,binding,seconds,interval):
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    kernel.ReadProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[w.HANDLE]
    handle=kernel.OpenProcess(0x1010,False,pid) # QUERY_LIMITED_INFORMATION|VM_READ only
    if not handle:raise OSError(ctypes.get_last_error(),'cannot open target for read-only diagnostics')
    try:
        path=ctypes.create_unicode_buffer(32768);length=w.DWORD(len(path))
        if not kernel.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(length)):raise OSError(ctypes.get_last_error(),'cannot query target identity')
        digest=hashlib.sha256(Path(path.value).read_bytes()).hexdigest()
        if digest!=RETAIL_SHA256:raise ValueError('target executable is not qualified retail')
        def memory(at,size):
            raw=ctypes.create_string_buffer(size);read=ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle,at,raw,size,ctypes.byref(read)) or read.value!=size:raise OSError(ctypes.get_last_error(),'cannot read qualified profiler data')
            return raw.raw
        for stage in binding['stages']:
            expected=b'\xe8'+struct.pack('<i',stage['entry_va']-stage['call_va']-5)
            if memory(stage['call_va'],5)!=expected:raise ValueError('target does not contain the selected profiler hook: '+stage['name'])
        decoder=verify_decoder(memory,binding)
        frequency=ctypes.c_longlong()
        if not kernel.QueryPerformanceFrequency(ctypes.byref(frequency)):raise OSError('QPC frequency unavailable')
        start=time.perf_counter();samples=[];skips=0
        while True:
            raw=memory(binding['state_va'],STATE_BYTES);confirm=memory(binding['state_va'],STATE_BYTES)
            try:
                if raw!=confirm:raise ValueError('telemetry changed during read')
                rows=decode(raw,binding,frequency.value)
            except ValueError:skips+=1
            else:samples.append({'elapsed_ms':(time.perf_counter()-start)*1000,'stages':rows})
            if time.perf_counter()-start>=seconds:break
            time.sleep(interval)
        if len(samples)<2:raise ValueError('not enough stable telemetry snapshots')
        if verify_decoder(memory,binding)!=decoder:raise ValueError('DXT decoder changed while capturing')
        return {'status':'CAPTURED_NATIVE_FRONTEND_COUNTERS','pid':pid,'exe_sha256':digest,'decoder_path':decoder,'qpc_frequency':frequency.value,'samples':samples,'busy_skips':skips,'interval_summary':difference(samples[0]['stages'],samples[-1]['stages']),
            'boundary':'read-only native inclusive call timings; measurement label supplied manually; no independent fileIO/DXdecode split, GPU completion or FPS claim'}
    finally:kernel.CloseHandle(handle)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--binding',type=Path,required=True);p.add_argument('--seconds',type=float,default=30);p.add_argument('--interval',type=float,default=.1);p.add_argument('--label',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not 1<=a.seconds<=600 or not .02<=a.interval<=5:p.error('duration/interval outside bounded range')
    r=capture(a.pid,find_binding(json.loads(a.binding.read_text())),a.seconds,a.interval);r['label']=a.label;r['binding_sha256']=hashlib.sha256(a.binding.read_bytes()).hexdigest();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['interval_summary'],indent=2))
