"""One-shot exact overlay revision; frozen renderer is only read from Git."""
from pathlib import Path
import difflib
import hashlib
import importlib.util
import json
import subprocess

PORT=Path(__file__).resolve().parents[2]
ROOT=PORT.parents[1]


def main():
    lockpath=PORT/'overlay/baseline-lock.json'
    lock=json.loads(lockpath.read_text())
    patch=PORT/'overlay/patches/0001-renderer-integration.patch'
    expected='faeafdc2c78611adbc65438a97aae7d6e753007008dd62be57274ecfac0a996a'
    if hashlib.sha256(patch.read_bytes()).hexdigest()!=expected:
        raise ValueError('Expected exact prior overlay, refusing reapply or fuzzy revision')
    stage=PORT/'.staging/ps2-enabled'
    source=stage/'modernization/renderer/src/wrappers.cpp'
    text=source.read_text()
    needle='void Device8::invalidate_all_buffer_shadows(const char* reason) noexcept {'
    lines=text.splitlines(keepends=True)
    found=[i for i,line in enumerate(lines) if line.startswith(needle)]
    if len(found)!=1:raise ValueError('Original staged function not unique')
    i=found[0]
    if not lines[i].rstrip().endswith('}}'):raise ValueError('Unexpected staged original reset function')
    replacement='''void Device8::invalidate_all_buffer_shadows(const char* reason) noexcept {
 std::lock_guard<std::recursive_mutex> l(buffer_mutex_);
 size_t retained=0,revoked=0;
#ifdef MRR_ENABLE_PS2_PORT
 const bool preserve=ps2_port_&&ps2_port_->buffer_mirroring_required();
 const bool reset_reason=reason&&!std::strcmp(reason,"device_reset");
#endif
 for(auto& entry:buffer_mirrors_){
  if(!entry.second)continue;auto& mirror=*entry.second;std::lock_guard<std::mutex> m(mirror.mutex);
#ifdef MRR_ENABLE_PS2_PORT
  const auto proxy=buffer_proxies_.find(entry.first);
  const uint64_t proxy_generation=proxy!=buffer_proxies_.end()&&proxy->second?proxy->second->generation():0;
  if(ps2port::retain_managed_mirror_on_reset(preserve,reset_reason,mirror,
      trace.resources.generation(reinterpret_cast<uintptr_t>(entry.first)),proxy_generation)){++retained;continue;}
#endif
  ++revoked;mirror.poisoned=true;mirror.initialized.clear();if(mirror.revision!=UINT64_MAX)++mirror.revision;
  try{mirror.poison_reason=reason?reason:"device_reset";}catch(...){mirror.poison_reason.clear();}
 }
 stream_buffers_.fill(nullptr);index_buffer_=nullptr;
 for(auto it=buffer_mirrors_.begin();it!=buffer_mirrors_.end();){if(!buffer_proxies_.count(it->first)){auto raw=it->first;++it;discard_unbound_buffer_mirror_locked(raw);}else ++it;}
#ifdef MRR_ENABLE_PS2_PORT
 if(reset_reason&&ps2_port_&&ps2_port_->reflection()&&ps2_port_->reflection()->diagnostics()){
  try{session().write("{\\"type\\":\\"ps2_buffer_mirror_reset\\",\\"retained_managed\\":"+std::to_string(retained)+
    ",\\"revoked\\":"+std::to_string(revoked)+",\\"policy\\":\\"retain_only_current_owned_cpu_uploads\\"}");}catch(...){}
 }
#endif
}
'''
    lines[i]=replacement
    updated=''.join(lines).replace('#include "ps2_port_extension.hpp"\n','#include "ps2_port_extension.hpp"\n#include "buffer_reset_policy.hpp"\n',1)
    source.write_text(updated,newline='\n')
    spec=importlib.util.spec_from_file_location('overlay_builder',PORT/'overlay/build_overlay.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    paths=builder.PATCH_PATHS['0001-renderer-integration.patch']
    pieces=[]
    for relative in sorted(paths):
        original=subprocess.check_output(['git','show',f"{lock['baseline_head']}:{relative}"],cwd=ROOT).decode()
        current=(stage/relative).read_text()
        pieces.extend(difflib.unified_diff(original.splitlines(keepends=True),current.splitlines(keepends=True),
            fromfile='a/'+relative,tofile='b/'+relative))
    patch.write_text(''.join(pieces),newline='\n')
    lock['patches']['0001-renderer-integration.patch']['sha256']=hashlib.sha256(patch.read_bytes()).hexdigest()
    lockpath.write_text(json.dumps(lock,indent=2)+'\n',newline='\n')
    print('Exact overlay patch',lock['patches']['0001-renderer-integration.patch']['sha256'])


if __name__=='__main__':main()
