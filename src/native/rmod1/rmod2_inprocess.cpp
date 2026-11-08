#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _WIN32_WINNT 0x0601
#include <windows.h>
#include <tlhelp32.h>
#include <bcrypt.h>

#include "core.hpp"
#include "extra_options.hpp"
#if defined(RMOD_EXTRA_OPTIONS)
#include "sdk_roster_abi.hpp"
#include "extra_options_package.hpp"
#endif
#include "image_mapping.hpp"
#include "native_plan.hpp"
#include "rmod2_inprocess.hpp"
#include "runtime_image_diff.hpp"
#include "rmod2_startup_preflight.hpp"
#if defined(RMOD_EXTRA_SDK_BINDING)
#include "extra_sdk_profile.hpp"
#endif

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <cwctype>
#include <filesystem>
#include <fstream>
#include <limits>
#include <map>
#include <string>
#include <string_view>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace fs = std::filesystem;
namespace {
using namespace rmod1;
using namespace rmod2_boot;

struct Patch {
    const rmod1_plan::ImageOperation* source{};
    std::vector<std::uint8_t> expected;
    std::vector<std::uint8_t> replacement;
    std::uintptr_t address{};
};

struct HandlePin {
    HANDLE value = INVALID_HANDLE_VALUE;
    explicit HandlePin(HANDLE h) : value(h) {}
    ~HandlePin() { if (value != INVALID_HANDLE_VALUE) CloseHandle(value); }
    HandlePin(const HandlePin&) = delete;
    HandlePin& operator=(const HandlePin&) = delete;
};

volatile LONG g_log_lock = 0;
HANDLE g_log = INVALID_HANDLE_VALUE;

void set_error(char* output, unsigned capacity, const char* value) {
    if (!output || !capacity) return;
    const auto length = std::min<std::size_t>(std::strlen(value), capacity - 1);
    std::memcpy(output, value, length);
    output[length] = '\0';
}

std::wstring module_path(HMODULE module) {
    std::vector<wchar_t> path(32768);
    const DWORD length = GetModuleFileNameW(module, path.data(), static_cast<DWORD>(path.size()));
    if (!length || length >= path.size()) return {};
    return std::wstring(path.data(), length);
}

std::wstring normalize_path(std::wstring path) {
    std::vector<wchar_t> full(32768);
    const DWORD length = GetFullPathNameW(path.c_str(), static_cast<DWORD>(full.size()), full.data(), nullptr);
    if (!length || length >= full.size()) return {};
    std::wstring result(full.data(), length);
    std::replace(result.begin(), result.end(), L'/', L'\\');
    std::transform(result.begin(), result.end(), result.begin(), [](wchar_t c) {
        return static_cast<wchar_t>(towlower(c));
    });
    return result;
}

bool same_path(const std::wstring& a, const std::wstring& b) {
    const auto left = normalize_path(a), right = normalize_path(b);
    return !left.empty() && left == right;
}

void append_log(const std::wstring& game_dir, const char* event, const char* details = "") {
    while (InterlockedCompareExchange(&g_log_lock, 1, 0) != 0) SwitchToThread();
    if (g_log == INVALID_HANDLE_VALUE) {
        const std::wstring path = game_dir + L"\\MRallyeRandomizer-boot.log";
        g_log = CreateFileW(path.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                            nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    }
    if (g_log != INVALID_HANDLE_VALUE) {
        SYSTEMTIME time{};
        GetLocalTime(&time);
        char line[768]{};
        const int count = wsprintfA(line, "%04u-%02u-%02uT%02u:%02u:%02u.%03u %s %s\r\n",
            time.wYear, time.wMonth, time.wDay, time.wHour, time.wMinute, time.wSecond,
            time.wMilliseconds, event, details);
        if (count > 0 && count < static_cast<int>(sizeof(line))) {
            DWORD written = 0;
            WriteFile(g_log, line, static_cast<DWORD>(count), &written, nullptr);
            FlushFileBuffers(g_log);
        }
    }
    InterlockedExchange(&g_log_lock, 0);
}

bool hash_bytes(const std::uint8_t* data, std::size_t size, char output[65]) {
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    DWORD object_size{}, digest_size{}, received{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) return false;
    bool ok = BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
        reinterpret_cast<PUCHAR>(&object_size), sizeof(object_size), &received, 0) >= 0 &&
        BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
        reinterpret_cast<PUCHAR>(&digest_size), sizeof(digest_size), &received, 0) >= 0 && digest_size == 32;
    std::vector<UCHAR> object(ok ? object_size : 0), digest(ok ? digest_size : 0);
    if (ok) ok = BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr, 0, 0) >= 0;
    if (ok && size) ok = BCryptHashData(hash, const_cast<PUCHAR>(data), static_cast<ULONG>(size), 0) >= 0;
    if (ok) ok = BCryptFinishHash(hash, digest.data(), digest_size, 0) >= 0;
    if (hash) BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (!ok) return false;
    static constexpr char digits[] = "0123456789abcdef";
    for (unsigned i = 0; i < 32; ++i) { output[i * 2] = digits[digest[i] >> 4]; output[i * 2 + 1] = digits[digest[i] & 15]; }
    output[64] = 0;
    return true;
}

bool read_file(const std::wstring& path, std::size_t maximum, std::vector<std::uint8_t>& bytes) {
    HANDLE file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                              FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER size{};
    bool ok = GetFileSizeEx(file, &size) && size.QuadPart >= 0 &&
              static_cast<std::uint64_t>(size.QuadPart) <= maximum;
    if (ok) {
        bytes.resize(static_cast<std::size_t>(size.QuadPart));
        std::size_t offset = 0;
        while (offset < bytes.size()) {
            DWORD got = 0;
            const DWORD request = static_cast<DWORD>(std::min<std::size_t>(bytes.size() - offset, 1u << 20));
            if (!ReadFile(file, bytes.data() + offset, request, &got, nullptr) || got != request) { ok = false; break; }
            offset += got;
        }
    }
    CloseHandle(file);
    return ok;
}

std::uint16_t u16(const std::vector<std::uint8_t>& b, std::size_t at) {
    if (at > b.size() || b.size() - at < 2) throw std::runtime_error("truncated PE header");
    return static_cast<std::uint16_t>(b[at] | (static_cast<unsigned>(b[at + 1]) << 8));
}
std::uint32_t u32(const std::vector<std::uint8_t>& b, std::size_t at) {
    if (at > b.size() || b.size() - at < 4) throw std::runtime_error("truncated PE header");
    return static_cast<std::uint32_t>(b[at]) | (static_cast<std::uint32_t>(b[at+1]) << 8) |
        (static_cast<std::uint32_t>(b[at+2]) << 16) | (static_cast<std::uint32_t>(b[at+3]) << 24);
}
std::vector<std::uint8_t> from_hex(const char* text) {
    if (!text) throw std::runtime_error("missing native operation bytes");
    const std::string_view s(text);
    if (s.size() & 1) throw std::runtime_error("odd native operation hex");
    auto nibble = [](char c) -> int { if(c>='0'&&c<='9') return c-'0'; if(c>='a'&&c<='f') return c-'a'+10; if(c>='A'&&c<='F') return c-'A'+10; return -1; };
    std::vector<std::uint8_t> out; out.reserve(s.size()/2);
    for (std::size_t i=0;i<s.size();i+=2) { int a=nibble(s[i]), b=nibble(s[i+1]); if(a<0||b<0) throw std::runtime_error("invalid native operation hex"); out.push_back(static_cast<std::uint8_t>((a<<4)|b)); }
    return out;
}

bool verify_mapped_image(const std::vector<std::uint8_t>& disk, std::string& error) {
#if defined(RMOD_EXTRA_OPTIONS)
    if (disk.size() < 0x40 || disk[0] != 'M' || disk[1] != 'Z') { error="invalid host image header"; return false; }
#else
    if (disk.size() != rmod1_plan::kRetailSize || disk.size() < 0x40 || disk[0] != 'M' || disk[1] != 'Z') { error="retail image size/header mismatch"; return false; }
#endif
    const auto pe = u32(disk, 0x3c);
    if (pe > disk.size() || disk.size() - pe < 24) { error="retail PE header is outside the pinned image"; return false; }
    if (std::memcmp(disk.data()+pe, "PE\0\0", 4) || u16(disk, pe+4) != IMAGE_FILE_MACHINE_I386) { error="retail image is not pinned PE32/I386"; return false; }
    const std::size_t opt = pe + 24;
    if (opt > disk.size() || disk.size() - opt < 64 || u16(disk,opt) != 0x10b || u32(disk,opt+28) != rmod1_plan::kImageBase ||
        u32(disk,opt+56) != rmod1_plan::kImageSize || (u16(disk,pe+22)&1)==0) { error="retail PE layout differs from pinned fixed-base image"; return false; }
    auto* base = reinterpret_cast<std::uint8_t*>(static_cast<std::uintptr_t>(rmod1_plan::kImageBase));
    MEMORY_BASIC_INFORMATION header_region{};
    if (reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) != rmod1_plan::kImageBase ||
        VirtualQuery(base, &header_region, sizeof(header_region)) != sizeof(header_region) ||
        header_region.Type != MEM_IMAGE || header_region.State != MEM_COMMIT ||
        reinterpret_cast<std::uintptr_t>(header_region.AllocationBase) != rmod1_plan::kImageBase ||
        u32(disk,opt+60) > disk.size() || u32(disk,opt+60) > rmod1_plan::kImageSize ||
        std::memcmp(base, disk.data(), u32(disk,opt+60)) != 0) { error="mapped retail headers/base do not match exact image"; return false; }
    const std::uint16_t sections = u16(disk,pe+6), opt_size = u16(disk,pe+20);
    const std::size_t table = opt + opt_size;
    if (table > disk.size() || sections > (disk.size() - table) / 40) { error="retail section table is outside the pinned image"; return false; }
    for (unsigned i=0;i<sections;++i) {
        const std::size_t s = table + i*40;
        const auto virtual_size=u32(disk,s+8), rva=u32(disk,s+12), raw_size=u32(disk,s+16), raw=u32(disk,s+20), flags=u32(disk,s+36);
        if (!(flags & IMAGE_SCN_MEM_EXECUTE)) continue;
        if (raw > disk.size() || raw_size > disk.size()-raw || rva > rmod1_plan::kImageSize || virtual_size > rmod1_plan::kImageSize-rva) { error="invalid executable section bounds"; return false; }
        // Validate the actual mapped virtual extent. SizeOfRawData can include
        // file-alignment padding that is not part of the section's live code.
        const auto begin = reinterpret_cast<std::uintptr_t>(base+rva);
        const auto end = begin + virtual_size;
        for (auto cursor = begin; cursor < end;) {
            MEMORY_BASIC_INFORMATION region{};
            if (VirtualQuery(reinterpret_cast<void*>(cursor),&region,sizeof(region))!=sizeof(region) ||
                region.Type!=MEM_IMAGE || region.State!=MEM_COMMIT ||
                reinterpret_cast<std::uintptr_t>(region.AllocationBase)!=rmod1_plan::kImageBase) {
                error="executable virtual section extent is not committed from the pinned MEM_IMAGE"; return false;
            }
            const DWORD page_protection=region.Protect&0xff;
            if ((region.Protect&PAGE_GUARD) ||
                (page_protection!=PAGE_EXECUTE_READ && page_protection!=PAGE_EXECUTE_READWRITE &&
                 page_protection!=PAGE_EXECUTE_WRITECOPY)) {
                error="executable virtual section extent is not readable and executable"; return false;
            }
            const auto region_end = reinterpret_cast<std::uintptr_t>(region.BaseAddress) + region.RegionSize;
            if (region_end <= cursor) { error="invalid mapped executable region extent"; return false; }
            cursor = std::min<std::uintptr_t>(end, region_end);
        }
    }
    return true;
}

std::string byte_window(const std::uint8_t* disk, std::size_t raw_size,
                        const std::uint8_t* mapped, std::size_t virtual_size,
                        std::size_t offset) {
    char text[64]{}; std::size_t used=0;
    const auto first = offset > 3 ? offset - 3 : 0;
    const auto last = std::min<std::size_t>(virtual_size, offset + 5);
    for (auto i=first;i<last;++i) {
        const auto expected=i<raw_size?disk[i]:std::uint8_t{0};
        used += static_cast<std::size_t>(wsprintfA(text+used,"%s%02X/%02X",i==first?"":" ",expected,mapped[i]));
    }
    return text;
}

bool diagnose_mapped_code_differences(const std::vector<std::uint8_t>& disk,
                                      const std::vector<Patch>& patches,
                                      const std::wstring& game_dir,
                                      bool sdk_bound,
                                      std::string& error) {
    const auto pe=u32(disk,0x3c);
    const auto opt=static_cast<std::size_t>(pe)+24;
    const auto table=opt+u16(disk,pe+20);
    const auto sections=u16(disk,pe+6);
    auto* base=reinterpret_cast<const std::uint8_t*>(static_cast<std::uintptr_t>(rmod1_plan::kImageBase));
    std::vector<NativeRange> planned; planned.reserve(patches.size());
    for (const auto& patch:patches) {
        // These exact two composed preimages are separately checked, including
        // after thread suspension. Other differences remain normal conflicts.
        if (sdk_bound && (std::string_view(patch.source->id)=="challenge-preview-identity" ||
                          std::string_view(patch.source->id)=="challenge-race-consume")) continue;
        planned.push_back({patch.source->id, static_cast<std::uint32_t>(patch.address-rmod1_plan::kImageBase), static_cast<std::uint32_t>(patch.expected.size())});
    }
    bool have_first=false, have_conflict=false;
    auto emit=[&](const char* event,const char* section,std::uint32_t rva,std::uint32_t raw,std::uint32_t raw_size,
                  std::uint32_t virtual_size,const ImageDifference& diff,bool conflict) {
        const auto va=rmod1_plan::kImageBase+rva+diff.offset;
        MEMORY_BASIC_INFORMATION page{}; DWORD protection=0;
        if(VirtualQuery(reinterpret_cast<const void*>(va),&page,sizeof(page))==sizeof(page)) protection=page.Protect;
        const auto detail=byte_window(disk.data()+raw,raw_size,base+rva,virtual_size,diff.offset);
        const std::string operation=diff.operation.empty()?"-":std::string(diff.operation);
        char line[768]{};
        wsprintfA(line,"section=%s RVA=0x%08X VA=0x%08X bytes(expected/actual)=%s page_protect=0x%08X overlaps_selected_operation=%s operation=%s",
            section,rva+diff.offset,static_cast<unsigned>(va),detail.c_str(),protection,
            conflict?"YES":"NO",operation.c_str());
        append_log(game_dir,event,line);
    };
    for(unsigned i=0;i<sections;++i) {
        const auto s=table+i*40;
        const auto virtual_size=u32(disk,s+8),rva=u32(disk,s+12),raw_size=u32(disk,s+16),raw=u32(disk,s+20),flags=u32(disk,s+36);
        if(!(flags&IMAGE_SCN_MEM_EXECUTE)||!virtual_size) continue;
        char name[9]{}; std::memcpy(name,disk.data()+s,8);
        const auto scan=scan_mapped_section(disk.data()+raw,raw_size,base+rva,virtual_size,rva,planned);
        if(scan.first.found&&!have_first){emit("IMAGE_DIFFERENCE_OUTSIDE_OR_AT_HOOK",name,rva,raw,raw_size,virtual_size,scan.first,!scan.first.operation.empty());have_first=true;}
        if(scan.first_planned_overlap.found&&!have_conflict){emit("IMAGE_SELECTED_HOOK_CONFLICT",name,rva,raw,raw_size,virtual_size,scan.first_planned_overlap,true);have_conflict=true;}
    }
    if(have_conflict){error="mapped executable bytes differ inside a selected native operation; see IMAGE_SELECTED_HOOK_CONFLICT";return false;}
    if(have_first) append_log(game_dir,"IMAGE_DIFFERENCES_NONCONFLICTING","live executable differs from disk outside selected native operation ranges; exact selected preimages remain mandatory");
    else append_log(game_dir,"IMAGE_MATCH","mapped executable code matches disk within audited virtual extents");
    return true;
}

bool region_free(std::uintptr_t address, std::size_t size) {
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(reinterpret_cast<void*>(address), &info, sizeof(info)) == sizeof(info) &&
        info.State == MEM_FREE && reinterpret_cast<std::uintptr_t>(info.BaseAddress) <= address &&
        address + size <= reinterpret_cast<std::uintptr_t>(info.BaseAddress) + info.RegionSize;
}

bool read_exact(std::uintptr_t address, void* out, std::size_t length) {
    __try { std::memcpy(out, reinterpret_cast<const void*>(address), length); return true; }
    __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}

#if defined(RMOD_EXTRA_SDK_BINDING)
struct SdkSnapshot {
    std::vector<std::vector<std::uint8_t>> checks;
    std::vector<std::uint8_t> code;
};

bool sdk_extension_present() {
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(reinterpret_cast<const void*>(sdk_binding_profile::extension_va), &info, sizeof(info)) == sizeof(info) &&
        info.State == MEM_COMMIT && info.Type == MEM_PRIVATE &&
        reinterpret_cast<std::uintptr_t>(info.AllocationBase) == sdk_binding_profile::extension_va;
}

bool sdk_profile_matches(SdkSnapshot* snapshot = nullptr) {
    if (sdk_binding_profile::check_count == 0 || sdk_binding_profile::check_count > 4096 ||
        sdk_binding_profile::hook_count != 2) return false;
    SdkSnapshot candidate;
    candidate.checks.reserve(sdk_binding_profile::check_count);
    for (const auto& item : sdk_binding_profile::checks) {
        const auto expected = from_hex(item.expected_hex);
        if (expected.empty() || expected.size() > 256 || item.rva > rmod1_plan::kImageSize ||
            expected.size() > rmod1_plan::kImageSize - item.rva) return false;
        std::vector<std::uint8_t> observed(expected.size());
        if (!read_exact(rmod1_plan::kImageBase + item.rva, observed.data(), observed.size()) || observed != expected) return false;
        candidate.checks.push_back(expected);
    }
    if (!sdk_extension_present() || !sdk_binding_profile::extension_size ||
        sdk_binding_profile::rw_offset > sdk_binding_profile::extension_size ||
        sdk_binding_profile::rw_size > sdk_binding_profile::extension_size - sdk_binding_profile::rw_offset) return false;
    const auto head = sdk_binding_profile::rw_offset;
    const auto tail = head + sdk_binding_profile::rw_size;
    std::vector<std::uint8_t> code(head + sdk_binding_profile::extension_size - tail);
    if ((!code.empty() && head && !read_exact(sdk_binding_profile::extension_va, code.data(), head)) ||
        (tail < sdk_binding_profile::extension_size &&
         !read_exact(sdk_binding_profile::extension_va + tail, code.data() + head,
                     sdk_binding_profile::extension_size - tail))) return false;
    if (snapshot) {candidate.code=std::move(code);*snapshot=std::move(candidate);}
    return true;
}

// No allocation, locks, BCrypt calls or mutable SDK state reads while other
// threads are suspended. Detect changes during installation, without requiring
// the entire extension to have one particular hash.
bool sdk_snapshot_matches(const SdkSnapshot& snapshot) noexcept {
    if (snapshot.checks.size()!=sdk_binding_profile::check_count || !sdk_extension_present()) return false;
    std::array<std::uint8_t,256> bytes{};
    for (std::size_t i=0;i<sdk_binding_profile::check_count;++i) {
        const auto& item=sdk_binding_profile::checks[i]; const auto& expected=snapshot.checks[i];
        if (expected.empty() || expected.size()>bytes.size() ||
            !read_exact(rmod1_plan::kImageBase+item.rva,bytes.data(),expected.size()) ||
            std::memcmp(bytes.data(),expected.data(),expected.size())) return false;
    }
    const auto head=sdk_binding_profile::rw_offset;
    const auto tail=head+sdk_binding_profile::rw_size;
    if (snapshot.code.size()!=head+sdk_binding_profile::extension_size-tail) return false;
    for (std::size_t index=0;index<snapshot.code.size();) {
        const auto source=index<head ? index : index+sdk_binding_profile::rw_size;
        const auto region_end=index<head ? head : snapshot.code.size();
        const auto n=std::min<std::size_t>(bytes.size(),region_end-index);
        if (!read_exact(sdk_binding_profile::extension_va+source,bytes.data(),n) ||
            std::memcmp(bytes.data(),snapshot.code.data()+index,n)) return false;
        index+=n;
    }
    return true;
}

bool any_sdk_hook_present() {
    for (const auto& item : sdk_binding_profile::hooks) {
        const auto expected = from_hex(item.mapped_hex);
        if (expected.size() != 7 || item.rva > rmod1_plan::kImageSize - expected.size())
            throw std::runtime_error("invalid generated SDK hook profile");
        std::vector<std::uint8_t> observed(expected.size());
        if (read_exact(rmod1_plan::kImageBase + item.rva, observed.data(), observed.size()) && observed == expected) return true;
    }
    return false;
}

void compose_sdk_challenge(std::vector<Patch>& patches) {
    unsigned found = 0;
    for (auto& p : patches) for (const auto& hook : sdk_binding_profile::hooks) {
        if (std::string_view(p.source->id) != hook.id) continue;
        if (p.address != rmod1_plan::kImageBase + hook.rva || p.expected != from_hex("8bbc3874050000"))
            throw std::runtime_error("F3 challenge operation does not match SDK composition profile");
        p.expected = from_hex(hook.mapped_hex); ++found;
    }
    if (found != sdk_binding_profile::hook_count)
        throw std::runtime_error("SDK composition requires both selected F3 challenge hooks");
}

void compose_sdk_stubs(std::vector<std::uint8_t>& code) {
    for (const auto& hook : sdk_binding_profile::hooks) {
        if (hook.stub_va < rmod1_plan::kCodeBase) throw std::runtime_error("SDK stub below F3 code allocation");
        const auto offset = static_cast<std::size_t>(hook.stub_va - rmod1_plan::kCodeBase);
        const auto original = from_hex("8bbc38740500009c60");
        const auto replacement = from_hex(hook.mapped_hex);
        if (offset > code.size() || original.size() > code.size() - offset || replacement.size()!=7 ||
            !std::equal(original.begin(), original.end(), code.begin()+offset))
            throw std::runtime_error("F3 challenge replay does not match SDK composition");
        std::copy(replacement.begin(), replacement.end(), code.begin()+offset);
    }
}
#endif

void store32(std::vector<std::uint8_t>& data, std::uint32_t address, std::uint32_t value) {
    if (!write_u32_address(data, rmod1_plan::kDataBase, address, value))
        throw std::runtime_error("callback slot outside runtime data allocation");
}

struct FrozenThreads {
    std::vector<HANDLE> handles;
    bool active = false;
    ~FrozenThreads() { resume(); }
    void resume() { for (auto it=handles.rbegin();it!=handles.rend();++it) { ResumeThread(*it); CloseHandle(*it); } handles.clear(); active=false; }
    bool freeze(std::string& error, const std::vector<Patch>& patches) {
        const DWORD self=GetCurrentThreadId(), pid=GetCurrentProcessId();
        handles.reserve(128);
        std::vector<DWORD> seen; seen.reserve(128);
        for (unsigned pass=0;pass<8;++pass) {
            HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
            if(snapshot==INVALID_HANDLE_VALUE){error="cannot snapshot process threads for patch transaction";return false;}
            THREADENTRY32 entry{}; entry.dwSize=sizeof(entry); bool ok=Thread32First(snapshot,&entry)!=FALSE; bool added=false;
            while(ok) {
                if(entry.th32OwnerProcessID==pid && entry.th32ThreadID!=self && std::find(seen.begin(),seen.end(),entry.th32ThreadID)==seen.end()) {
                    HANDLE thread=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,entry.th32ThreadID);
                    if(!thread){DWORD e=GetLastError(); if(e==ERROR_INVALID_PARAMETER){ok=Thread32Next(snapshot,&entry)!=FALSE;continue;} CloseHandle(snapshot);error="cannot open a game thread before native patch transaction";return false;}
                    if(SuspendThread(thread)==static_cast<DWORD>(-1)){DWORD e=GetLastError();CloseHandle(thread);if(e==ERROR_INVALID_PARAMETER){ok=Thread32Next(snapshot,&entry)!=FALSE;continue;}CloseHandle(snapshot);error="cannot suspend every other game thread";return false;}
                    CONTEXT context{}; context.ContextFlags=CONTEXT_CONTROL;
                    if(!GetThreadContext(thread,&context)){ResumeThread(thread);CloseHandle(thread);CloseHandle(snapshot);error="cannot inspect suspended game thread EIP";return false;}
                    const std::uintptr_t ip=context.Eip;
                    for(const auto& patch:patches) if(ip>=patch.address&&ip<patch.address+patch.replacement.size()) {
                        ResumeThread(thread);CloseHandle(thread);CloseHandle(snapshot);error="a suspended thread EIP is inside a native patch range";return false;
                    }
                    if(handles.size()==handles.capacity()||seen.size()==seen.capacity()) { ResumeThread(thread);CloseHandle(thread);CloseHandle(snapshot);error="startup thread count exceeds bounded quiescence capacity";return false; }
                    handles.push_back(thread);seen.push_back(entry.th32ThreadID);added=true;
                }
                ok=Thread32Next(snapshot,&entry)!=FALSE;
            }
            CloseHandle(snapshot);
            if(!added){active=true;return true;}
        }
        error="game thread set did not quiesce within bounded enumeration";return false;
    }
};

bool initialize_impl(char* error, unsigned capacity) {
    const std::wstring exe=module_path(nullptr);
    if(exe.empty()){set_error(error,capacity,"cannot resolve process executable path");return false;}
    const fs::path exe_path(exe), game_dir=exe_path.parent_path();
        append_log(game_dir.wstring(),"BOOT_B_PROXY_LOADED","genuine System32/SysWOW64 DirectInput resolved before bootstrap");
    try {
        std::vector<std::uint8_t> disk; char digest[65]{};
#if defined(RMOD_EXTRA_OPTIONS)
        if(!read_file(exe,32u*1024u*1024u,disk)) throw std::runtime_error("cannot read host executable");
#else
        if(!read_file(exe,rmod1_plan::kRetailSize,disk)||disk.size()!=rmod1_plan::kRetailSize||!hash_bytes(disk.data(),disk.size(),digest)||_stricmp(digest,rmod1_plan::kRetailSha256)) throw std::runtime_error("host executable SHA256/size is not the pinned retail build");
#endif
        std::string map_error; if(!verify_mapped_image(disk,map_error)) throw std::runtime_error(map_error);
        append_log(game_dir.wstring(),"HOST_VERIFIED","fixed PE identity, mapped headers and executable virtual extents verified");

        std::wstring runtime_path=(game_dir/L"MRallyeRandomizerRuntime.dll").wstring();
        HandlePin runtime_pin(CreateFileW(runtime_path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr));
        if(runtime_pin.value==INVALID_HANDLE_VALUE) throw std::runtime_error("cannot pin runtime DLL against replacement before loading");
        std::vector<std::uint8_t> runtime_bytes;
#if defined(RMOD_EXTRA_OPTIONS)
        if(!read_file(runtime_path,32u*1024u*1024u,runtime_bytes)) throw std::runtime_error("runtime DLL unavailable");
#else
        if(!read_file(runtime_path,32u*1024u*1024u,runtime_bytes)||!hash_bytes(runtime_bytes.data(),runtime_bytes.size(),digest)||_stricmp(digest,rmod1_plan::kRuntimeCoreSha256)) throw std::runtime_error("runtime DLL missing or SHA256 differs from F3-pinned core");
#endif
        const auto dll_pe=u32(runtime_bytes,0x3c);
        if(u16(runtime_bytes,dll_pe+4)!=IMAGE_FILE_MACHINE_I386||u16(runtime_bytes,dll_pe+24)!=0x10b) throw std::runtime_error("runtime core is not x86 PE32");
        HMODULE runtime=LoadLibraryW(runtime_path.c_str());
        if(!runtime) throw std::runtime_error("LoadLibraryW failed for the verified runtime core");
        if(!same_path(module_path(runtime),runtime_path)) throw std::runtime_error("loaded runtime core path differs from the verified adjacent file");
        append_log(game_dir.wstring(),"RUNTIME_LOADED","required runtime exports checked; module loaded from game directory");

        using ConfigureFn=DWORD (WINAPI*)(const void*);
        auto configure=reinterpret_cast<ConfigureFn>(GetProcAddress(runtime,"MRConfigureBlobV1"));
        auto choose=GetProcAddress(runtime,"MRChooseClassV1"); auto limit=GetProcAddress(runtime,"MROpponentLimitV1");
        auto can_start=GetProcAddress(runtime,"MRCanStartQuickRaceV1"); auto set_phase=GetProcAddress(runtime,"MRSetStartPhaseV1");
        auto challenge=GetProcAddress(runtime,"MRChallengeV1");
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        auto player_car=GetProcAddress(runtime,"MRQuickRacePlayerCarV1");
#endif
        if(!configure||!choose||!limit||!can_start||!set_phase||!challenge) throw std::runtime_error("runtime DLL is missing one or more required F3 exports");
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        if(!player_car) throw std::runtime_error("runtime DLL is missing the G2 player-vehicle callback");
#endif

        // Keep ConfigVersion 2 strictly interpreted by the existing parser.
        // Extra Options has an independent optional file, so existing user
        // settings and their live-reload contract are never rewritten.
        const auto extra_path = (game_dir/L"MRallyeExtraOptions.ini").wstring();
        const DWORD extra_attr = GetFileAttributesW(extra_path.c_str());
        if (extra_attr == INVALID_FILE_ATTRIBUTES) {
            append_log(game_dir.wstring(),"EXTRA_OPTIONS_DISABLED","separate optional configuration absent");
        } else {
            std::vector<std::uint8_t> extra_bytes;
            if ((extra_attr & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)) ||
                !read_file(extra_path,4096,extra_bytes)) {
                append_log(game_dir.wstring(),"EXTRA_OPTIONS_CONFIG_REJECTED","unreadable, linked, or oversized; customization disabled");
            } else {
                const auto extra = extra_options::parse_config(std::string_view(
                    reinterpret_cast<const char*>(extra_bytes.data()), extra_bytes.size()));
                if (!extra.accepted) append_log(game_dir.wstring(),"EXTRA_OPTIONS_CONFIG_REJECTED",extra.error);
                else if ((extra.config.enabled && (extra.config.liveries || extra.config.tires)) || extra.config.ghost || extra.config.five_difficulties)
#if defined(RMOD_EXTRA_OPTIONS)
                    append_log(game_dir.wstring(),"EXTRA_OPTIONS_REQUESTED","native customization initialized by the owning dinput8 bootstrap");
#else
                    append_log(game_dir.wstring(),"EXTRA_OPTIONS_UNAVAILABLE","requested customization has not been installed or qualified");
#endif
                else append_log(game_dir.wstring(),"EXTRA_OPTIONS_DISABLED","customization or both child features disabled");
            }
        }
        std::vector<std::uint8_t> ini; const std::wstring ini_path=(game_dir/L"MRallyeRandomizer.ini").wstring();
        Config config{}; bool ini_ok=false;
        const DWORD attr=GetFileAttributesW(ini_path.c_str());
        if(attr!=INVALID_FILE_ATTRIBUTES && !(attr&FILE_ATTRIBUTE_DIRECTORY) && read_file(ini_path,kMaxConfigBytes,ini)) {
            auto parsed=parse_ini(std::string_view(reinterpret_cast<const char*>(ini.data()),ini.size()));
            if(parsed.accepted){config=parsed.config;ini_ok=true;} else append_log(game_dir.wstring(),"CONFIG_REJECTED_SAFE_DEFAULT","INI parse failed; all features use safe Stock defaults");
        } else if(attr==INVALID_FILE_ATTRIBUTES) append_log(game_dir.wstring(),"CONFIG_DEFAULT","INI missing; safe Stock defaults");
        else append_log(game_dir.wstring(),"CONFIG_REJECTED_SAFE_DEFAULT","INI unreadable or exceeds 4096 bytes; safe Stock defaults");
        std::vector<std::uint8_t> blob(4+(ini_ok?ini.size():0),0);
        const std::uint32_t ini_length=ini_ok?static_cast<std::uint32_t>(ini.size()):0;
        std::memcpy(blob.data(),&ini_length,4); if(ini_length) std::memcpy(blob.data()+4,ini.data(),ini_length);
        if(!configure(blob.data())) throw std::runtime_error("runtime core rejected initial configuration or could not initialize diagnostics");
        append_log(game_dir.wstring(),ini_ok?"CONFIG_ACCEPTED":"CONFIG_SAFE_DEFAULT","complete ConfigVersion=2 snapshot applied by F3 runtime core");

        const std::uint32_t requested=(config_needs_randomizer_hooks(config)?rmod1_plan::kFeatureRandomizer:0u)|
            (config_requests_opponent_extension(config)?rmod1_plan::kFeatureOpponents:0u);
        std::vector<Patch> patches;
        for(std::size_t i=0;i<rmod1_plan::kOperationCount;++i){const auto& op=rmod1_plan::kOperations[i];
            if(std::string_view(op.id)=="oep-bootstrap") continue; // OEP has already executed in the proxy path.
            if((op.feature&requested)==0) continue;
            Patch p; p.source=&op; p.expected=from_hex(op.expected_hex); p.replacement=from_hex(op.replacement_hex); p.address=rmod1_plan::kImageBase+op.rva;
            if(std::string_view(op.id)=="opponent-arrow-bound"&&config_requests_opponent_extension(config)){
                if(p.replacement.size()!=3||config.max_opponents<1||config.max_opponents>7) throw std::runtime_error("opponent arrow bound is invalid");
                p.replacement[2]=static_cast<std::uint8_t>(config.max_opponents-1);
            }
            if(p.expected.empty()||p.expected.size()!=p.replacement.size()||p.address<rmod1_plan::kImageBase||p.address+p.expected.size()>rmod1_plan::kImageBase+rmod1_plan::kImageSize) throw std::runtime_error("native operation is outside the audited retail image");
            patches.push_back(std::move(p));
        }
        if(patches.empty()){append_log(game_dir.wstring(),"BOOT_B_NO_FEATURES","F3 core configured safely; no gameplay features requested");return true;}
        bool sdk_bound = false;
#if defined(RMOD_EXTRA_SDK_BINDING)
        SdkSnapshot sdk_snapshot;
        sdk_bound = sdk_profile_matches(&sdk_snapshot);
        if (!sdk_bound && (any_sdk_hook_present() || sdk_extension_present()))
            throw std::runtime_error("partial or mismatched SDK profile; no composed hooks installed");
        if (sdk_bound) {
#if defined(RMOD_EXTRA_OPTIONS)
            auto register_sdk=reinterpret_cast<DWORD (WINAPI*)(const rmod1::SdkRosterV1*)>(GetProcAddress(runtime,"MRRegisterSdkRosterV1"));
            const rmod1::SdkRosterV1 descriptor{sizeof(rmod1::SdkRosterV1),1,
                static_cast<unsigned>(std::size(extra_package::sdk_vehicles)),extra_package::challenge_human_offset,extra_package::sdk_vehicles};
            if(!register_sdk||!register_sdk(&descriptor))throw std::runtime_error("SDK roster provider rejected qualified registration");
            append_log(game_dir.wstring(),"SDK_ROSTER_REGISTERED","existing physical IDs and per-mode eligibility supplied by SDK; G1 participant limits unchanged");
#endif
            compose_sdk_challenge(patches);
            append_log(game_dir.wstring(),"SDK_BINDING_PROFILE_MATCH","all SDK operation bytes match; validating combined transaction");
        }
#endif
        std::sort(patches.begin(),patches.end(),[](const Patch&a,const Patch&b){return a.address<b.address;});
        std::vector<OperationSpan> spans; spans.reserve(patches.size());
        for(const auto& p:patches) spans.push_back({static_cast<std::uint32_t>(p.address-rmod1_plan::kImageBase),p.expected.size(),p.replacement.size(),p.source->id});
        std::string operation_error;
        if(!validate_operation_spans(spans.data(),spans.size(),rmod1_plan::kImageSize,operation_error)) throw std::runtime_error(operation_error);
        std::string image_difference_error;
        if(!diagnose_mapped_code_differences(disk,patches,game_dir.wstring(),sdk_bound,image_difference_error)) throw std::runtime_error(image_difference_error.c_str());
        std::vector<NativePreimage> preimages; preimages.reserve(patches.size());
        for(const auto& p:patches){MEMORY_BASIC_INFORMATION info{};if(VirtualQuery(reinterpret_cast<void*>(p.address),&info,sizeof(info))!=sizeof(info)||info.Type!=MEM_IMAGE||info.State!=MEM_COMMIT||info.Protect!=PAGE_EXECUTE_READ||p.address+p.expected.size()>reinterpret_cast<std::uintptr_t>(info.BaseAddress)+info.RegionSize) throw std::runtime_error("native operation mapping/protection is not pristine executable image");preimages.push_back({p.address,p.expected.data(),p.expected.size(),p.source->id});}
        if(!verify_native_preimages(preimages.data(),preimages.size(),[](std::uintptr_t address,void* out,std::size_t length){return read_exact(address,out,length);},operation_error)) throw std::runtime_error(operation_error);
        if(!region_free(rmod1_plan::kCodeBase,rmod1_plan::kCodeSize)||!region_free(rmod1_plan::kDataBase,rmod1_plan::kDataSize)) throw std::runtime_error("fixed F3 code/data allocation is not free");

        std::vector<std::uint8_t> code(rmod1_plan::kCodeSize,0),data(rmod1_plan::kDataSize,0);
        if(!copy_generated_template(code,rmod1_plan::kCodeTemplate,rmod1_plan::kCodeTemplateSize,rmod1_plan::kCodeUsed)||
           !copy_generated_template(data,rmod1_plan::kDataTemplate,rmod1_plan::kDataTemplateSize,rmod1_plan::kDataUsed)) throw std::runtime_error("generated F3 template bounds are inconsistent");
        if(!hash_bytes(rmod1_plan::kCodeTemplate,rmod1_plan::kCodeTemplateSize,digest)||_stricmp(digest,rmod1_plan::kCodeTemplateSha256)||
           !hash_bytes(rmod1_plan::kDataTemplate,rmod1_plan::kDataTemplateSize,digest)||_stricmp(digest,rmod1_plan::kDataTemplateSha256)) throw std::runtime_error("generated F3 template SHA256 mismatch");
#if defined(RMOD_EXTRA_SDK_BINDING)
        if (sdk_bound) compose_sdk_stubs(code);
#endif
        const auto slot=[&](std::uint32_t at, FARPROC fn){const auto value=reinterpret_cast<std::uintptr_t>(fn);if(value>UINT32_MAX) throw std::runtime_error("runtime callback is outside x86 address space");store32(data,at,static_cast<std::uint32_t>(value));};
        store32(data,rmod1_plan::kSlotModule,static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(runtime)));
        slot(rmod1_plan::kSlotConfigure,reinterpret_cast<FARPROC>(configure));slot(rmod1_plan::kSlotChooseClass,choose);slot(rmod1_plan::kSlotOpponentLimit,limit);slot(rmod1_plan::kSlotCanStart,can_start);store32(data,rmod1_plan::kSlotLoadLibraryW,0);slot(rmod1_plan::kSlotStartPhase,set_phase);slot(rmod1_plan::kSlotChallenge,challenge);
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        slot(rmod1_plan::kSlotPlayerCar,player_car);
#endif
        // BOOT-B omits the OEP bootstrap, the only generated code that reads
        // CONFIG_BLOB/DLL_PATH. MRConfigureBlobV1 consumed this local bounded
        // blob above, so it must not be copied into the unrelated F3 data area.

        void* code_mem=VirtualAlloc(reinterpret_cast<void*>(rmod1_plan::kCodeBase),rmod1_plan::kCodeSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
        if(code_mem!=reinterpret_cast<void*>(rmod1_plan::kCodeBase)) throw std::runtime_error("cannot reserve fixed F3 code region");
        void* data_mem=VirtualAlloc(reinterpret_cast<void*>(rmod1_plan::kDataBase),rmod1_plan::kDataSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
        if(data_mem!=reinterpret_cast<void*>(rmod1_plan::kDataBase)){VirtualFree(code_mem,0,MEM_RELEASE);throw std::runtime_error("cannot reserve fixed F3 data region");}
        bool committed=false;
        auto release_allocations=[&](){if(!committed){VirtualFree(code_mem,0,MEM_RELEASE);VirtualFree(data_mem,0,MEM_RELEASE);}};
        std::memcpy(code_mem,code.data(),code.size());std::memcpy(data_mem,data.data(),data.size());
        if(std::memcmp(code_mem,code.data(),code.size())||std::memcmp(data_mem,data.data(),data.size())){release_allocations();throw std::runtime_error("F3 code/data template readback mismatch");}
        DWORD old_code=0;if(!VirtualProtect(code_mem,rmod1_plan::kCodeSize,PAGE_EXECUTE_READ,&old_code)||old_code!=PAGE_READWRITE){release_allocations();throw std::runtime_error("cannot set F3 code region PAGE_EXECUTE_READ");}
        if(!FlushInstructionCache(GetCurrentProcess(),code_mem,code.size())){release_allocations();throw std::runtime_error("cannot flush F3 generated code");}

        FrozenThreads frozen; std::string freeze_error;
        if(!frozen.freeze(freeze_error,patches)){release_allocations();throw std::runtime_error(freeze_error);}
#if defined(RMOD_EXTRA_SDK_BINDING)
        if (sdk_bound && !sdk_snapshot_matches(sdk_snapshot)) { release_allocations(); throw std::runtime_error("SDK profile changed during startup quiescence"); }
#endif
        for(const auto& p:patches){std::array<std::uint8_t,256> actual{};if(p.expected.size()>actual.size()||!read_exact(p.address,actual.data(),p.expected.size())||std::memcmp(actual.data(),p.expected.data(),p.expected.size())){release_allocations();throw std::runtime_error("native preimage changed during startup quiescence");}}
        SYSTEM_INFO system{};GetSystemInfo(&system);const std::uintptr_t page_size=system.dwPageSize;
        std::map<std::uintptr_t,DWORD> protections;
        const auto restore_open_pages = [&]() {
            bool ok = true;
            for (auto it = protections.rbegin(); it != protections.rend(); ++it) {
                DWORD ignored = 0;
                if (!VirtualProtect(reinterpret_cast<void*>(it->first), page_size, it->second, &ignored)) ok = false;
            }
            return ok;
        };
        for (const auto& p : patches) {
            const auto page = p.address & ~(page_size - 1);
            if (protections.count(page)) continue;
            DWORD old = 0;
            if (!VirtualProtect(reinterpret_cast<void*>(page), page_size, PAGE_EXECUTE_READWRITE, &old)) {
                if (!restore_open_pages()) TerminateProcess(GetCurrentProcess(), 0xE02Bu);
                release_allocations();
                throw std::runtime_error("cannot open native image page for atomic startup patch");
            }
            if (old != PAGE_EXECUTE_READ) {
                DWORD ignored = 0;
                const bool current_restored = VirtualProtect(reinterpret_cast<void*>(page), page_size, old, &ignored) != FALSE;
                if (!current_restored || !restore_open_pages()) TerminateProcess(GetCurrentProcess(), 0xE02Bu);
                release_allocations();
                throw std::runtime_error("native patch page was not PAGE_EXECUTE_READ");
            }
            protections.emplace(page, old);
        }
        std::size_t written_count=0;bool write_ok=true;
        for(const auto& p:patches){std::memcpy(reinterpret_cast<void*>(p.address),p.replacement.data(),p.replacement.size());++written_count;std::vector<std::uint8_t> check(p.replacement.size());if(!read_exact(p.address,check.data(),check.size())||check!=p.replacement){write_ok=false;break;}}
        if(write_ok) write_ok=FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(rmod1_plan::kImageBase),rmod1_plan::kImageSize)!=FALSE;
        bool protection_ok=true;for(auto it=protections.rbegin();it!=protections.rend();++it){DWORD ignored=0;if(!VirtualProtect(reinterpret_cast<void*>(it->first),page_size,it->second,&ignored))protection_ok=false;}
        if(!write_ok||!protection_ok){bool rollback_ok=true;
            // Re-open every page and restore all attempted preimages while other game threads remain suspended.
            for(const auto& page:protections){DWORD ignored=0;if(!VirtualProtect(reinterpret_cast<void*>(page.first),page_size,PAGE_EXECUTE_READWRITE,&ignored))rollback_ok=false;}
            if(!rollback_ok) TerminateProcess(GetCurrentProcess(),0xE02Bu);
            for(std::size_t i=0;i<written_count;++i) std::memcpy(reinterpret_cast<void*>(patches[i].address),patches[i].expected.data(),patches[i].expected.size());
            FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(rmod1_plan::kImageBase),rmod1_plan::kImageSize);
            for(std::size_t i=0;i<written_count;++i){std::vector<std::uint8_t> check(patches[i].expected.size());if(!read_exact(patches[i].address,check.data(),check.size())||check!=patches[i].expected)rollback_ok=false;}
            for(const auto& page:protections){DWORD ignored=0;if(!VirtualProtect(reinterpret_cast<void*>(page.first),page_size,page.second,&ignored))rollback_ok=false;}
            if(!rollback_ok) TerminateProcess(GetCurrentProcess(),0xE02Bu);
            release_allocations();throw std::runtime_error("native patch transaction failed; original bytes restored while startup threads were suspended");
        }
        committed=true; frozen.resume();
        char detail[256]{};wsprintfA(detail,"operations=%u plan=%s",static_cast<unsigned>(patches.size()),rmod1_plan::kPlanSha256);
        append_log(game_dir.wstring(),"NATIVE_INSTALL_COMPLETE",detail);
        append_log(game_dir.wstring(),"BOOT_B_READY","F3 Randomizer initialized before frontend loop");
        return true;
    } catch(const std::exception& ex) {
        set_error(error,capacity,ex.what());
        append_log(game_dir.wstring(),"BOOT_B_FAILED",ex.what());
        return false;
    } catch(...) {
        set_error(error,capacity,"unknown in-process initialization failure");
        append_log(game_dir.wstring(),"BOOT_B_FAILED","unknown in-process initialization failure");
        return false;
    }
}
}

bool rmod2_boot::initialize(char* error, unsigned error_capacity) { return initialize_impl(error,error_capacity); }

bool rmod2_boot::apply_native_writes(const NativeWrite* writes, std::size_t count, char* error, unsigned capacity) {
    try {
        if (!writes || !count) { set_error(error, capacity, "no native writes"); return false; }
        std::vector<Patch> patches;
        for (std::size_t i = 0; i < count; ++i) {
            const auto& w = writes[i];
            if (!w.expected || !w.replacement || !w.size || w.size > 256) throw std::runtime_error("native write is malformed");
            Patch p; p.address = w.address;
            p.expected.assign(w.expected, w.expected + w.size); p.replacement.assign(w.replacement, w.replacement + w.size);
            for (const auto& q : patches)
                if (p.address < q.address + q.expected.size() && q.address < p.address + p.expected.size()) throw std::runtime_error("native writes overlap");
            MEMORY_BASIC_INFORMATION info{};
            if (VirtualQuery(reinterpret_cast<void*>(p.address), &info, sizeof(info)) != sizeof(info) || info.Type != MEM_IMAGE ||
                info.State != MEM_COMMIT || info.Protect != PAGE_EXECUTE_READ ||
                p.address + p.expected.size() > reinterpret_cast<std::uintptr_t>(info.BaseAddress) + info.RegionSize)
                throw std::runtime_error("native write target is not pristine executable image");
            std::array<std::uint8_t, 256> actual{};
            if (!read_exact(p.address, actual.data(), w.size) || std::memcmp(actual.data(), w.expected, w.size)) throw std::runtime_error(w.id ? w.id : "native preimage differs");
            patches.push_back(std::move(p));
        }
        FrozenThreads frozen; std::string freeze_error;
        if (!frozen.freeze(freeze_error, patches)) throw std::runtime_error(freeze_error);
        for (const auto& p : patches) {
            std::array<std::uint8_t, 256> actual{};
            if (!read_exact(p.address, actual.data(), p.expected.size()) || std::memcmp(actual.data(), p.expected.data(), p.expected.size()))
                throw std::runtime_error("native preimage changed during startup quiescence");
        }
        SYSTEM_INFO system{}; GetSystemInfo(&system); const std::uintptr_t page_size = system.dwPageSize;
        std::map<std::uintptr_t, DWORD> protections;
        for (const auto& p : patches)
            for (std::uintptr_t page = p.address & ~(page_size - 1); page < p.address + p.replacement.size(); page += page_size) {
                if (protections.count(page)) continue;
                DWORD old = 0;
                if (!VirtualProtect(reinterpret_cast<void*>(page), page_size, PAGE_EXECUTE_READWRITE, &old) || old != PAGE_EXECUTE_READ) {
                    bool ok = true; DWORD ignored = 0;
                    if (old && !VirtualProtect(reinterpret_cast<void*>(page), page_size, old, &ignored)) ok = false;
                    for (auto it = protections.rbegin(); it != protections.rend(); ++it)
                        if (!VirtualProtect(reinterpret_cast<void*>(it->first), page_size, it->second, &ignored)) ok = false;
                    if (!ok) TerminateProcess(GetCurrentProcess(), 0xE02Bu);
                    throw std::runtime_error("cannot open native image page for atomic patch");
                }
                protections.emplace(page, old);
            }
        std::size_t written = 0; bool ok = true;
        for (const auto& p : patches) {
            std::memcpy(reinterpret_cast<void*>(p.address), p.replacement.data(), p.replacement.size()); ++written;
            std::vector<std::uint8_t> check(p.replacement.size());
            if (!read_exact(p.address, check.data(), check.size()) || check != p.replacement) { ok = false; break; }
        }
        if (!ok) {
            for (std::size_t i = 0; i < written; ++i) std::memcpy(reinterpret_cast<void*>(patches[i].address), patches[i].expected.data(), patches[i].expected.size());
            for (std::size_t i = 0; i < written; ++i) {
                std::vector<std::uint8_t> check(patches[i].expected.size());
                if (!read_exact(patches[i].address, check.data(), check.size()) || check != patches[i].expected) TerminateProcess(GetCurrentProcess(), 0xE02Bu);
            }
        }
        for (const auto& p : patches) FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void*>(p.address), p.replacement.size());
        bool restored = true;
        for (auto it = protections.rbegin(); it != protections.rend(); ++it) { DWORD ignored = 0; if (!VirtualProtect(reinterpret_cast<void*>(it->first), page_size, it->second, &ignored)) restored = false; }
        if (!restored) TerminateProcess(GetCurrentProcess(), 0xE02Bu);
        if (!ok) throw std::runtime_error("native write readback failed; original bytes restored");
        frozen.resume();
        return true;
    } catch (const std::exception& ex) {
        set_error(error, capacity, ex.what()); return false;
    }
}
