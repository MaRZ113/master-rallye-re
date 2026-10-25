"""Read-only live SDK supplemental SFX state; no injection or control writes."""
import argparse,ctypes,json,struct
from pathlib import Path

def inspect(pid,policy):
    def find(x):
        if isinstance(x,dict):
            if isinstance(x.get('entries'),dict) and 'voices' in x['entries']:return x
            for v in x.values():
                r=find(v)
                if r:return r
        if isinstance(x,list):
            for v in x:
                r=find(v)
                if r:return r
    binding=find(policy)
    if not binding:raise ValueError('no supplemental SFX binding in policy')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
    k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=k.OpenProcess(0x10|0x1000,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    def read(address,size):
        b=ctypes.create_string_buffer(size);n=ctypes.c_size_t()
        if not k.ReadProcessMemory(handle,address,b,size,ctypes.byref(n)) or n.value!=size:raise ctypes.WinError(ctypes.get_last_error())
        return b.raw
    try:
        stride=binding.get('voice_slot_stride',40)
        if stride not in (40,44):raise ValueError('unsupported voice slot stride')
        data=read(binding['entries']['voices'],64*stride);rows=[]
        for i in range(64):
            owner,a,b,c,tick,pressure,load,cooldown,events,amplitude=struct.unpack_from('<5I3fIf',data,i*stride)
            if not owner:continue
            row={'slot':i,'owner_va':owner,'participant_slot':struct.unpack('<I',read(owner+0x54,4))[0],'tick_ms':tick,'estimated_spool':pressure,'signed_crank_load_proxy':load,'cooldown_seconds':cooldown,'release_events':events,'voices':[]}
            for layer,address in zip(('transmission_whine','turbo_spool','bov_release'),(a,b,c)):
                if not address:continue
                v=read(address,0x34)
                row['voices'].append({'layer':layer,'address':address,'resource_handle':struct.unpack_from('<I',v)[0],
                    'backend_creation_requested':bool(v[12]),'backend_load_failed':bool(v[13]),'play_requested':bool(v[14]),'loop':bool(v[15]),
                    'gain':struct.unpack_from('<f',v,16)[0],'pitch':struct.unpack_from('<f',v,20)[0],
                    'entity':struct.unpack_from('<I',v,36)[0],'position':struct.unpack_from('<3f',v,40)})
            rows.append(row)
        return {'pid':pid,'rows':rows,'boundary':'Read-only SFX state snapshot, not proof of DirectSound device playback or audible mixing; may race normal engine updates.'}
    finally:k.CloseHandle(handle)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--policy',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.pid,json.loads(a.policy.read_text())),indent=2))
