#include "broker_null_guard.hpp"
#include "provenance.hpp"
#include "state_tracker.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <mutex>
#include <tlhelp32.h>

namespace gfx2 {
namespace {
constexpr uintptr_t RETAIL_BASE = 0x00400000;
constexpr uintptr_t FACTORY_RETURN_VA = 0x00559060;
constexpr size_t CODE_PAGE_SIZE = 4096;

constexpr unsigned char STRINGLIST_CONTEXT[] = {0x8b,0x7b,0x04,0x3b,0x7b,0x08,0x74,0x1a};
constexpr unsigned char STRINGLIST_EMPTY_CONTEXT[] = {0x8b,0x15,0x84,0x7b,0x6f,0x00};
constexpr unsigned char XMLDATA_CONTEXT[] = {0x8b,0x10,0x8b,0xc8,0xff,0x52,0x0c,0x8b,0xf8,0x85,0xff,0x74,0x2e};
constexpr unsigned char XMLDATA_NULL_CONTEXT[] = {0x8b,0x4c,0x24,0x0c,0x51};

bool rel32(uintptr_t instruction_end, uintptr_t target, int32_t& value) noexcept {
    const int64_t delta = static_cast<int64_t>(target) - static_cast<int64_t>(instruction_end);
    if (delta < INT32_MIN || delta > INT32_MAX) return false;
    value = static_cast<int32_t>(delta);
    return true;
}

void store32(unsigned char* out, uint32_t value) noexcept {
    std::memcpy(out, &value, sizeof(value));
}

uintptr_t va(uintptr_t base, uintptr_t retail_va) noexcept {
    return base + (retail_va - RETAIL_BASE);
}

bool context_matches(PatchMemory& memory, BrokerNullSite site, uintptr_t base) noexcept {
    if (base != RETAIL_BASE) return false;
    if (site == BrokerNullSite::StringList) {
        std::array<unsigned char, sizeof(STRINGLIST_CONTEXT)> current{};
        std::array<unsigned char, sizeof(STRINGLIST_EMPTY_CONTEXT)> empty{};
        return memory.read(current.data(), reinterpret_cast<void*>(va(base,BROKER_STRINGLIST_SITE_VA)), current.size()) &&
               std::memcmp(current.data(), STRINGLIST_CONTEXT, current.size()) == 0 &&
               memory.read(empty.data(), reinterpret_cast<void*>(va(base,BROKER_STRINGLIST_EMPTY_VA)), empty.size()) &&
               std::memcmp(empty.data(), STRINGLIST_EMPTY_CONTEXT, empty.size()) == 0 &&
               BROKER_STRINGLIST_SITE_VA + 8 + STRINGLIST_CONTEXT[7] == BROKER_STRINGLIST_EMPTY_VA;
    }
    std::array<unsigned char, sizeof(XMLDATA_CONTEXT)> current{};
    std::array<unsigned char, sizeof(XMLDATA_NULL_CONTEXT)> null_path{};
    const uintptr_t branch_va = BROKER_XMLDATA_SITE_VA + 11;
    return memory.read(current.data(), reinterpret_cast<void*>(va(base,BROKER_XMLDATA_SITE_VA)), current.size()) &&
           std::memcmp(current.data(), XMLDATA_CONTEXT, current.size()) == 0 &&
           memory.read(null_path.data(), reinterpret_cast<void*>(va(base,BROKER_XMLDATA_NULL_VA)), null_path.size()) &&
           std::memcmp(null_path.data(), XMLDATA_NULL_CONTEXT, null_path.size()) == 0 &&
           branch_va + 2 + XMLDATA_CONTEXT[12] == BROKER_XMLDATA_NULL_VA;
}

bool make_detour(uintptr_t site, uintptr_t destination, size_t patch_size,
                 std::array<unsigned char,8>& out) noexcept {
    int32_t displacement = 0;
    if (patch_size < 5 || patch_size > out.size() ||
        !rel32(site + 5, destination, displacement)) return false;
    out.fill(0x90);
    out[0] = 0xe9;
    std::memcpy(out.data()+1, &displacement, sizeof(displacement));
    return true;
}

bool rollback_site(PatchMemory& memory, void* site, const unsigned char* original,
                   size_t size, DWORD old_protection) noexcept {
    DWORD writable_old = 0, ignored = 0;
    if (!memory.protect(site,size,PAGE_EXECUTE_READWRITE,writable_old)) return false;
    bool okay = memory.write(site,original,size);
    std::array<unsigned char,8> readback{};
    okay = okay && memory.read(readback.data(),site,size) && !std::memcmp(readback.data(),original,size);
    okay = memory.flush(site,size) && okay;
    const bool protection = memory.protect(site,size,old_protection,ignored);
    return okay && protection;
}

class NativeMemory final : public PatchMemory {
public:
    bool read(void* destination,const void* source,size_t size) noexcept override {
        return safe_copy(destination,source,size);
    }
    bool write(void* destination,const void* source,size_t size) noexcept override {
        return safe_copy(destination,source,size);
    }
    bool protect(void* address,size_t size,DWORD value,DWORD& old) noexcept override {
        return VirtualProtect(address,size,value,&old)!=FALSE;
    }
    bool flush(void* address,size_t size) noexcept override {
        return FlushInstructionCache(GetCurrentProcess(),address,size)!=FALSE;
    }
};

bool pin_proxy_module() noexcept {
    HMODULE pinned = nullptr;
    return GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&install_broker_null_guards), &pinned) != FALSE;
}

class NativeCodeMemory final : public BrokerCodeMemory {
public:
    uintptr_t allocate(size_t) noexcept override {
        if (!pin_proxy_module()) return 0;
        return reinterpret_cast<uintptr_t>(VirtualAlloc(nullptr,CODE_PAGE_SIZE,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    }
    bool seal(uintptr_t address,size_t size) noexcept override {
        DWORD old=0;
        return VirtualProtect(reinterpret_cast<void*>(address),CODE_PAGE_SIZE,PAGE_EXECUTE_READ,&old)!=FALSE &&
               FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(address),size)!=FALSE;
    }
    void discard(uintptr_t address) noexcept override {
        if (address) VirtualFree(reinterpret_cast<void*>(address),0,MEM_RELEASE);
    }
};

class NativeThreads final : public AttractThreadGate {
    std::array<HANDLE,64> handles_{};
    std::array<DWORD,64> ids_{};
    size_t count_=0;
public:
    ~NativeThreads() override { leave(); }
    void leave() noexcept override {
        while(count_){HANDLE h=handles_[--count_];ResumeThread(h);CloseHandle(h);}
    }
    bool enter(uintptr_t begin,size_t size) noexcept override {
        HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
        if(snapshot==INVALID_HANDLE_VALUE)return false;
        THREADENTRY32 entry{};entry.dwSize=sizeof(entry);bool okay=Thread32First(snapshot,&entry)!=FALSE;
        if(okay)do{
            if(entry.th32OwnerProcessID!=GetCurrentProcessId()||entry.th32ThreadID==GetCurrentThreadId())continue;
            if(count_==handles_.size()){okay=false;break;}
            HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,entry.th32ThreadID);
            if(!h){okay=false;break;}
            if(SuspendThread(h)==DWORD(-1)){CloseHandle(h);okay=false;break;}
            handles_[count_]=h;ids_[count_++]=entry.th32ThreadID;
            CONTEXT context{};context.ContextFlags=CONTEXT_CONTROL;
            if(!GetThreadContext(h,&context)||(context.Eip>=begin&&context.Eip<begin+size)){okay=false;break;}
        }while(Thread32Next(snapshot,&entry));
        CloseHandle(snapshot);
        if(!okay)return false;
        snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
        if(snapshot==INVALID_HANDLE_VALUE)return false;
        entry={};entry.dwSize=sizeof(entry);okay=Thread32First(snapshot,&entry)!=FALSE;
        if(okay)do{
            if(entry.th32OwnerProcessID!=GetCurrentProcessId()||entry.th32ThreadID==GetCurrentThreadId())continue;
            bool found=false;for(size_t i=0;i<count_;++i)found|=ids_[i]==entry.th32ThreadID;
            if(!found){okay=false;break;}
        }while(Thread32Next(snapshot,&entry));
        CloseHandle(snapshot);return okay;
    }
};

struct Registry {
    std::mutex mutex;
    bool attempted=false;
    BrokerNullSiteState stringlist{},xmldata{};
    volatile LONG stringlist_count=0,xmldata_count=0;
    const char* refusal="not_attempted";
};
Registry& registry(){static Registry* value=new Registry();return *value;}

uint32_t read_counter(volatile LONG* value) noexcept {
    return static_cast<uint32_t>(InterlockedCompareExchange(value,0,0));
}

BrokerNullGuardStatus status_locked(Registry& r) noexcept {
    BrokerNullGuardStatus s;
    s.retail_build_verified=session().target&&session().exe_sha==TARGET_SHA;
    s.stringlist_site_verified=r.stringlist.context_verified;
    s.stringlist_guard_installed=r.stringlist.installed;
    s.xmldata_site_verified=r.xmldata.context_verified;
    s.xmldata_guard_installed=r.xmldata.installed;
    s.rollback_performed=r.stringlist.rollback_performed||r.xmldata.rollback_performed;
    s.rollback_verified=r.stringlist.rollback_verified&&r.xmldata.rollback_verified;
    s.original_bytes_restored=(!r.stringlist.installed&&(!r.stringlist.context_verified||r.stringlist.original_bytes_restored))&&
        (!r.xmldata.installed&&(!r.xmldata.context_verified||r.xmldata.original_bytes_restored));
    s.safe_to_continue=s.rollback_verified;
    s.stringlist_null_branches=read_counter(&r.stringlist_count);
    s.xmldata_null_branches=read_counter(&r.xmldata_count);
    s.install_failure_reason=r.refusal;
    if(r.stringlist.context_verified&&!r.stringlist.installed&&std::strcmp(r.stringlist.reason,"installed")&&
       std::strcmp(r.stringlist.reason,"restored"))s.install_failure_reason=r.stringlist.reason;
    else if(r.xmldata.context_verified&&!r.xmldata.installed&&std::strcmp(r.xmldata.reason,"installed")&&
            std::strcmp(r.xmldata.reason,"restored"))s.install_failure_reason=r.xmldata.reason;
    return s;
}

void write_status(const char* phase,const BrokerNullGuardStatus& s,
                  const BrokerNullSiteState& a,const BrokerNullSiteState& b) noexcept {
    try {
        session().write("{\"type\":\"broker_null_guard\",\"phase\":"+quote(phase)+
            ",\"retail_build_verified\":"+(s.retail_build_verified?"true":"false")+
            ",\"stringlist_site_verified\":"+(s.stringlist_site_verified?"true":"false")+
            ",\"stringlist_guard_installed\":"+(s.stringlist_guard_installed?"true":"false")+
            ",\"stringlist_reason\":"+quote(a.reason)+
            ",\"stringlist_null_branches\":"+std::to_string(s.stringlist_null_branches)+
            ",\"xmldata_site_verified\":"+(s.xmldata_site_verified?"true":"false")+
            ",\"xmldata_guard_installed\":"+(s.xmldata_guard_installed?"true":"false")+
            ",\"xmldata_reason\":"+quote(b.reason)+
            ",\"xmldata_null_branches\":"+std::to_string(s.xmldata_null_branches)+
            ",\"install_failure_reason\":"+quote(s.install_failure_reason)+
            ",\"rollback_performed\":"+(s.rollback_performed?"true":"false")+
            ",\"rollback_verified\":"+(s.rollback_verified?"true":"false")+
            ",\"stringlist_original_bytes_restored\":"+(a.original_bytes_restored?"true":"false")+
            ",\"xmldata_original_bytes_restored\":"+(b.original_bytes_restored?"true":"false")+
            ",\"original_bytes_restored\":"+(s.original_bytes_restored?"true":"false")+
            ",\"safe_to_continue\":"+(s.safe_to_continue?"true":"false")+"}");
    } catch (...) {}
}
} // namespace

bool build_broker_null_stub(BrokerNullSite site,uintptr_t stub_address,
                            uintptr_t null_counter,BrokerNullStub& out) noexcept {
    out={};
    if(!stub_address||!null_counter||stub_address>UINT32_MAX||null_counter>UINT32_MAX)return false;
    if(site==BrokerNullSite::StringList){
        // TEST preserves all registers; the null path increments a bounded counter
        // while restoring TEST's flags before jumping to the native empty-list path.
        auto* b=out.bytes.data();
        b[0]=0x85;b[1]=0xdb;                         // test ebx, ebx
        b[2]=0x0f;b[3]=0x85;                         // jnz nonnull
        int32_t branch=0;if(!rel32(stub_address+8,stub_address+22,branch))return false;
        std::memcpy(b+4,&branch,4);
        b[8]=0x9c;b[9]=0xf0;b[10]=0xff;b[11]=0x05; // pushfd; lock inc dword ptr [counter]
        store32(b+12,static_cast<uint32_t>(null_counter));
        b[16]=0x9d;b[17]=0xe9;                      // popfd; jmp empty-list completion
        int32_t to_empty=0;if(!rel32(stub_address+22,BROKER_STRINGLIST_EMPTY_VA,to_empty))return false;
        std::memcpy(b+18,&to_empty,4);
        const unsigned char original_ops[]={0x8b,0x7b,0x04,0x3b,0x7b,0x08};
        std::memcpy(b+22,original_ops,sizeof(original_ops));
        b[28]=0xe9;int32_t to_branch=0;
        if(!rel32(stub_address+33,BROKER_STRINGLIST_SITE_VA+6,to_branch))return false;
        std::memcpy(b+29,&to_branch,4);out.size=33;return true;
    }
    auto* b=out.bytes.data();
    b[0]=0x9c;b[1]=0x85;b[2]=0xc0;                // pushfd; test eax, eax
    b[3]=0x0f;b[4]=0x84;                          // jz null path
    int32_t to_null=0;if(!rel32(stub_address+9,stub_address+22,to_null))return false;
    std::memcpy(b+5,&to_null,4);
    b[9]=0x9d;b[10]=0x8b;b[11]=0x10;             // popfd; mov edx, [eax]
    b[12]=0x8b;b[13]=0xc8;                       // mov ecx, eax
    b[14]=0x68;store32(b+15,static_cast<uint32_t>(BROKER_XMLDATA_CONTINUE_VA));
    b[19]=0xff;b[20]=0x62;b[21]=0x0c;            // jmp dword ptr [edx+0c]
    b[22]=0x9d;b[23]=0x9c;b[24]=0xf0;b[25]=0xff;b[26]=0x05;
    store32(b+27,static_cast<uint32_t>(null_counter));
    b[31]=0x9d;b[32]=0xe9;                       // restore flags, continue at native next-entry path
    int32_t to_next=0;if(!rel32(stub_address+37,BROKER_XMLDATA_NULL_VA,to_next))return false;
    std::memcpy(b+33,&to_next,4);out.size=37;return true;
}

bool apply_broker_null_guard(PatchMemory& memory,BrokerCodeMemory& code,
                             AttractThreadGate& threads,BrokerNullSite site,
                             uintptr_t image_base,bool exact_retail,
                             uintptr_t null_counter,BrokerNullSiteState& state) noexcept {
    if(!exact_retail){state.reason="unsupported_build";return true;}
    if(image_base!=RETAIL_BASE){state.reason="unexpected_image_base";return true;}
    if(state.installed){
        std::array<unsigned char,8> current{};
        if(memory.read(current.data(),reinterpret_cast<void*>(state.address),state.patch_size)&&
           !std::memcmp(current.data(),state.replacement.data(),state.patch_size)){
            state.reason="already_owned";return true;
        }
        state.installed=false;state.reason="patch_ownership_lost";return true;
    }
    const size_t patch_size=site==BrokerNullSite::StringList?6:7;
    const uintptr_t site_va=site==BrokerNullSite::StringList?BROKER_STRINGLIST_SITE_VA:BROKER_XMLDATA_SITE_VA;
    const uintptr_t address=va(image_base,site_va);
    if(!context_matches(memory,site,image_base)){state.context_verified=false;state.reason="exact_context_or_continuation_mismatch";return true;}
    state.context_verified=true;state.address=address;state.patch_size=patch_size;
    if(!memory.read(state.original.data(),reinterpret_cast<void*>(address),patch_size)){state.reason="site_read_failed";return true;}
    uintptr_t stub=state.stub;
    BrokerNullStub built{};
    if(!stub){
        stub=code.allocate(site==BrokerNullSite::StringList?33:37);
        if(!stub){state.reason="stub_allocation_or_module_pin_failed";return true;}
        if(!build_broker_null_stub(site,stub,null_counter,built)||
           !memory.write(reinterpret_cast<void*>(stub),built.bytes.data(),built.size)||
           !code.seal(stub,built.size)||!memory.flush(reinterpret_cast<void*>(stub),built.size)){
            code.discard(stub);state.reason="stub_build_or_seal_failed";return true;
        }
        state.stub=stub;state.stub_size=built.size;
    }else{
        if(!build_broker_null_stub(site,stub,null_counter,built)||built.size!=state.stub_size){state.reason="stub_reuse_shape_mismatch";return true;}
        std::array<unsigned char,40> current{};
        if(!memory.read(current.data(),reinterpret_cast<void*>(stub),built.size)||
           std::memcmp(current.data(),built.bytes.data(),built.size)){state.reason="stub_reuse_bytes_mismatch";return true;}
    }
    std::array<unsigned char,8> replacement{};
    if(!make_detour(address,stub,patch_size,replacement)){state.reason="detour_out_of_range";if(!state.installed){code.discard(stub);state.stub=0;state.stub_size=0;}return true;}
    if(!threads.enter(address,patch_size)){threads.leave();state.reason="thread_quiescence_unavailable_or_site_active";if(!state.installed){code.discard(stub);state.stub=0;state.stub_size=0;}return true;}
    std::array<unsigned char,8> current{};
    if(!context_matches(memory,site,image_base)||!memory.read(current.data(),reinterpret_cast<void*>(address),patch_size)||
       std::memcmp(current.data(),state.original.data(),patch_size)){
        threads.leave();state.reason="context_changed_after_quiescence";if(!state.installed){code.discard(stub);state.stub=0;state.stub_size=0;}return true;
    }
    DWORD old=0,ignored=0;
    if(!memory.protect(reinterpret_cast<void*>(address),patch_size,PAGE_EXECUTE_READWRITE,old)){
        threads.leave();state.reason="site_protect_failed_no_write";if(!state.installed){code.discard(stub);state.stub=0;state.stub_size=0;}return true;
    }
    state.replacement=replacement;
    std::array<unsigned char,8> readback{};
    bool written=memory.write(reinterpret_cast<void*>(address),replacement.data(),patch_size);
    bool verified=written&&memory.read(readback.data(),reinterpret_cast<void*>(address),patch_size)&&
                  !std::memcmp(readback.data(),replacement.data(),patch_size)&&memory.flush(reinterpret_cast<void*>(address),patch_size);
    bool protection=memory.protect(reinterpret_cast<void*>(address),patch_size,old,ignored);
    if(verified&&protection){state.installed=true;state.original_bytes_restored=false;state.reason="installed";threads.leave();return true;}
    state.rollback_performed=true;
    const bool rollback=rollback_site(memory,reinterpret_cast<void*>(address),state.original.data(),patch_size,old);
    state.rollback_verified=rollback;
    state.reason=rollback?"install_failed_rollback_verified":"install_failed_rollback_unverified_restart_required";
    if(rollback&&!state.stub_size){code.discard(stub);state.stub=0;}
    threads.leave();return rollback;
}

bool restore_broker_null_guard(PatchMemory& memory,AttractThreadGate& threads,
                               BrokerNullSiteState& state) noexcept {
    if(!state.installed){state.reason=state.context_verified?state.reason:"not_installed";return true;}
    if(!threads.enter(state.address,state.patch_size)){threads.leave();state.reason="restore_thread_quiescence_failed";return false;}
    std::array<unsigned char,8> current{};
    if(!memory.read(current.data(),reinterpret_cast<void*>(state.address),state.patch_size)||
       std::memcmp(current.data(),state.replacement.data(),state.patch_size)){
        threads.leave();state.reason="restore_refused_patch_ownership_lost";return false;
    }
    DWORD old=0,ignored=0;
    if(!memory.protect(reinterpret_cast<void*>(state.address),state.patch_size,PAGE_EXECUTE_READWRITE,old)){
        threads.leave();state.reason="restore_protect_failed";return false;
    }
    bool written=memory.write(reinterpret_cast<void*>(state.address),state.original.data(),state.patch_size);
    bool verified=written&&memory.read(current.data(),reinterpret_cast<void*>(state.address),state.patch_size)&&
                  !std::memcmp(current.data(),state.original.data(),state.patch_size)&&memory.flush(reinterpret_cast<void*>(state.address),state.patch_size);
    bool protection=memory.protect(reinterpret_cast<void*>(state.address),state.patch_size,old,ignored);
    if(verified&&protection){state.installed=false;state.original_bytes_restored=true;state.reason="restored";threads.leave();return true;}
    state.rollback_performed=true;
    const bool rollback=rollback_site(memory,reinterpret_cast<void*>(state.address),state.replacement.data(),state.patch_size,old);
    state.rollback_verified=rollback;state.installed=rollback;
    state.original_bytes_restored=false;
    state.reason=rollback?"restore_failed_patch_rollback_verified":"restore_failed_patch_rollback_unverified_restart_required";
    threads.leave();return rollback;
}

bool install_broker_null_guards(uintptr_t factory_caller) noexcept {
    Registry& r=registry();std::lock_guard<std::mutex> guard(r.mutex);
    if(r.attempted)return r.stringlist.rollback_verified&&r.xmldata.rollback_verified;
    r.attempted=true;
    Session& s=session();
    if(!s.target||s.exe_sha!=TARGET_SHA){r.refusal="unsupported_build";write_status("startup",status_locked(r),r.stringlist,r.xmldata);return true;}
    if(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=RETAIL_BASE){r.refusal="unexpected_image_base";write_status("startup",status_locked(r),r.stringlist,r.xmldata);return true;}
    if(factory_caller!=FACTORY_RETURN_VA){r.refusal="unexpected_factory_callsite";write_status("startup",status_locked(r),r.stringlist,r.xmldata);return true;}
    NativeMemory memory;NativeCodeMemory code;NativeThreads threads;
    const bool a=apply_broker_null_guard(memory,code,threads,BrokerNullSite::StringList,RETAIL_BASE,true,
        reinterpret_cast<uintptr_t>(&r.stringlist_count),r.stringlist);
    const bool b=a?apply_broker_null_guard(memory,code,threads,BrokerNullSite::XmlData,RETAIL_BASE,true,
        reinterpret_cast<uintptr_t>(&r.xmldata_count),r.xmldata):false;
    if(!a)r.xmldata.reason="skipped_after_stringlist_rollback_failure";
    if(std::strcmp(r.stringlist.reason,"installed")&&std::strcmp(r.stringlist.reason,"already_owned"))r.refusal=r.stringlist.reason;
    else if(std::strcmp(r.xmldata.reason,"installed")&&std::strcmp(r.xmldata.reason,"already_owned"))r.refusal=r.xmldata.reason;
    else r.refusal="none";
    auto status=status_locked(r);write_status("startup",status,r.stringlist,r.xmldata);
    return a&&b&&status.safe_to_continue;
}

void restore_broker_null_guards() noexcept {
    Registry& r=registry();std::lock_guard<std::mutex> guard(r.mutex);
    if(!r.attempted)return;
    NativeMemory memory;NativeThreads threads;
    bool a=restore_broker_null_guard(memory,threads,r.stringlist);
    bool b=restore_broker_null_guard(memory,threads,r.xmldata);
    if(!a||!b)r.refusal=!a?r.stringlist.reason:r.xmldata.reason;
    auto status=status_locked(r);write_status("teardown",status,r.stringlist,r.xmldata);
}

BrokerNullGuardStatus broker_null_guard_status() noexcept {
    Registry& r=registry();std::lock_guard<std::mutex> guard(r.mutex);return status_locked(r);
}
} // namespace gfx2
