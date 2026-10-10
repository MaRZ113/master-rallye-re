#pragma once
#include "sdk.hpp"
#include "visual_policy.hpp"
#include "compatibility.hpp"
#include <atomic>
#include <string>
#include <cstdint>
namespace gfx2 {
inline constexpr const char* TARGET_SHA="bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4";
extern HMODULE proxy_module;
std::wstring module_path(HMODULE module);
std::string utf8(const std::wstring& value);
std::string sha256_file(const std::wstring& path,uint64_t* size=nullptr) noexcept;
inline std::string trace_capture_id(uint64_t device_id,uint64_t frame_id){return "d"+std::to_string(device_id)+"-f"+std::to_string(frame_id);}
struct Caller {uintptr_t address=0,base=0;std::string module;bool known=false;};
Caller caller_info(uintptr_t address);
std::string quote(const std::string& text);
struct TraceConfig {
 bool enabled=true,summaries=true,enabled_valid=true,summaries_valid=true;
 std::string enabled_raw="1",summaries_raw="1";
};
TraceConfig read_trace_config(const std::wstring& path);
class Session {
public:
 bool enabled=true,summaries=true;
 std::wstring directory;
 std::string exe_sha,exe_path,proxy_sha,proxy_path,real_path;
 bool target=false;
 Compatibility compatibility;
 std::atomic_bool foliage_provenance_available{true};
 VisualConfig visual_config;std::wstring config_path;
 bool write(const std::string& record) noexcept;
 uint64_t device_serial() noexcept;
private:
 friend Session& session();
 Session();
 HANDLE file_=INVALID_HANDLE_VALUE;
 CRITICAL_SECTION lock_{};
 uint64_t bytes_=0,serial_=0;
};
Session& session();
void note_real_runtime(HMODULE module,const std::wstring& requested) noexcept;
void note_create_device(UINT adapter,D3DDEVTYPE type,HWND hwnd,DWORD flags,
 const D3DPRESENT_PARAMETERS* before,const D3DPRESENT_PARAMETERS* after,HRESULT hr,
 uintptr_t real,uintptr_t wrapper) noexcept;
std::string pp_json(const D3DPRESENT_PARAMETERS& pp);
}
