#pragma once
#include "state_tracker.hpp"
#include <string>
#include <unordered_map>
#include <map>
namespace gfx2 {
inline constexpr uint32_t GAMEPLAY_PROJECTION_RETURN_RVA=0x0013FA75;
inline constexpr double SOURCE_CAMERA_TOLERANCE_DEGREES=0.01;
inline constexpr uint32_t STOCK_SHADOW_RETURN_RVA=0x001881EB;
struct VisualConfig {
 bool found=false,version_ok=false,anisotropy=false,fov=false,shadow_off=false;
 unsigned max_anisotropy=16;float vfov=75.f;
 std::map<std::string,std::string> raw_fields;
 std::string reason,af_reason,fov_reason,shadow_reason;
 std::string reflection_mode="Stock",reflection_reason;
 std::string display_mode="Stock",display_reason,interface_mode="Stock",interface_reason;
 unsigned width=0,height=0,refresh=0,samples=4;
 std::string aa_mode="Stock",aa_reason,freeze_reason;
 bool menu_freeze=false,auto_hide_cursor=true;unsigned cursor_delay_ms=1500;std::string cursor_reason;
};
VisualConfig parse_visual_config(const std::unordered_map<std::string,std::string>& fields,bool found);
VisualConfig read_visual_config(const std::wstring& path);
bool parse_config_boolean(std::string value,bool& output);
std::string config_json(const VisualConfig& c);
struct VisualPolicy {
 VisualConfig requested,effective;
 bool min_supported=false,mag_supported=false;DWORD caps_max=0;HRESULT caps_result=D3DERR_NOTAVAILABLE;
 void configure(const VisualConfig& config,bool known,const D3DCAPS8* caps,HRESULT hr);
 DWORD filter(DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD value) const noexcept;
 bool projection(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* input,D3DMATRIX& output,bool exe_caller,uint32_t rva) const noexcept;
 bool suppress(uint32_t slot,bool exe_caller,uint32_t rva,const Shadow& state,D3DPRIMITIVETYPE primitive) const noexcept;
 bool active() const noexcept {return effective.anisotropy||effective.fov||effective.shadow_off||effective.reflection_mode=="ViewDependent2D";}
};
bool symmetric_lh(const D3DMATRIX& p) noexcept;
double source_camera_angle(const D3DMATRIX& p) noexcept;
float vertical_fov(const D3DMATRIX& p) noexcept;
}
