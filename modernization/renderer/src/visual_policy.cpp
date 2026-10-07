#include "visual_policy.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cerrno>
#include <cstdlib>
#include <cctype>
#include <sstream>
#include <cfenv>
namespace gfx2 {
namespace {
struct PolicyFP {fenv_t env;PolicyFP(){fegetenv(&env);}~PolicyFP(){fesetenv(&env);}};
std::string trim(std::string v){auto a=v.find_first_not_of(" \t\r\n");return a==std::string::npos?"":v.substr(a,v.find_last_not_of(" \t\r\n")-a+1);}
bool boolean(std::string v,bool& out){v=trim(v);for(char& c:v)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));if(v=="true"||v=="1"){out=true;return true;}if(v=="false"||v=="0"){out=false;return true;}return false;}
bool number(const std::string& text,double& out){auto v=trim(text);char* end=nullptr;errno=0;out=std::strtod(v.c_str(),&end);return !v.empty()&&end==v.c_str()+v.size()&&!errno&&std::isfinite(out);}
}
VisualConfig parse_visual_config(const std::unordered_map<std::string,std::string>& fields,bool found){
 PolicyFP fp;VisualConfig c;c.found=found;c.raw_fields.insert(fields.begin(),fields.end());if(!found){c.reason="missing_config_stock";return c;}
 auto get=[&](const char* key,const char* fallback){auto i=fields.find(key);return i==fields.end()?std::string(fallback):i->second;};
 c.version_ok=trim(get("Renderer.ConfigVersion",""))=="1";
 if(!c.version_ok){c.reason="unknown_or_missing_config_version_stock";return c;}
 c.reason="version_1";
 if(!boolean(get("Filtering.AnisotropicFiltering","false"),c.anisotropy)){c.anisotropy=false;c.af_reason="invalid_boolean";}
 double n=0;if(!number(get("Filtering.MaxAnisotropy","16"),n)||n<1||n>65535||n!=std::floor(n)){c.anisotropy=false;c.af_reason="invalid_max_anisotropy";}else c.max_anisotropy=static_cast<unsigned>(n);
 if(!boolean(get("Camera.GameplayFOV","false"),c.fov)){c.fov=false;c.fov_reason="invalid_boolean";}
 if(!number(get("Camera.VerticalFOVDegrees","75"),n)||n<30||n>110){c.fov=false;c.fov_reason="invalid_vertical_fov";}else c.vfov=static_cast<float>(n);
 auto selector=[&](const char* key,std::initializer_list<const char*> names){auto v=trim(get(key,"Stock"));unsigned i=0;for(auto name:names){if(v==std::to_string(i++))return std::string(name);}return v;};
 auto mode=selector("Shadows.Mode",{"Stock","Off"});if(mode=="Off")c.shadow_off=true;else if(mode!="Stock")c.shadow_reason="invalid_shadow_mode";
 auto reflection=selector("VehicleReflections.Mode",{"Stock","ViewDependent2D"});
 if(reflection=="Stock"||reflection=="ViewDependent2D")c.reflection_mode=reflection;else c.reflection_reason="invalid_reflection_mode_stock";
 auto display=selector("Display.Mode",{"Stock","Windowed","Borderless","ExclusiveFullscreen"});
 if(display=="Stock"||display=="Windowed"||display=="Borderless"||display=="ExclusiveFullscreen")c.display_mode=display;else c.display_reason="invalid_display_mode_stock";
 auto integer=[&](const char* key,const char* fallback,unsigned limit,unsigned& value){double v=0;if(!number(get(key,fallback),v)||v<0||v>limit||v!=std::floor(v))return false;value=static_cast<unsigned>(v);return true;};
 if(!integer("Display.Width","0",16384,c.width)||!integer("Display.Height","0",16384,c.height)||
    ((c.width==0)!=(c.height==0))||(c.width&& (c.width<320||c.height<200))||!integer("Display.RefreshRate","0",1000,c.refresh)){
  c.display_mode="Stock";c.width=c.height=c.refresh=0;c.display_reason="invalid_display_dimensions_or_refresh_stock";
 }
 auto ui=selector("Widescreen.InterfaceMode",{"Stock","Centered4x3","PreserveMargins"});
 if(ui=="Stock"||ui=="Centered4x3"||ui=="PreserveMargins")c.interface_mode=ui;else c.interface_reason="invalid_interface_mode_stock";
 auto aa=selector("AntiAliasing.Mode",{"Stock","MSAA"});if(aa=="Stock"||aa=="MSAA")c.aa_mode=aa;else c.aa_reason="invalid_aa_mode_stock";
 if(!integer("AntiAliasing.Samples","4",8,c.samples)||(c.samples!=2&&c.samples!=4&&c.samples!=8)){c.aa_mode="Stock";c.samples=4;c.aa_reason="invalid_samples_stock";}
 if(!boolean(get("Compatibility.MenuFreezeFix","false"),c.menu_freeze)){c.menu_freeze=false;c.freeze_reason="invalid_freeze_boolean_disabled";}
 if(!boolean(get("Display.AutoHideCursor","1"),c.auto_hide_cursor)){c.auto_hide_cursor=false;c.cursor_reason="invalid_cursor_boolean_disabled";}
 if(!integer("Display.CursorHideDelayMs","1500",60000,c.cursor_delay_ms)){c.auto_hide_cursor=false;c.cursor_reason="invalid_cursor_delay_disabled";}
 return c;
}
VisualConfig read_visual_config(const std::wstring& path){
 auto attributes=GetFileAttributesW(path.c_str());bool found=attributes!=INVALID_FILE_ATTRIBUTES&&!(attributes&FILE_ATTRIBUTE_DIRECTORY);
 std::unordered_map<std::string,std::string> fields;
 if(found){
  struct Key{const wchar_t* section;const wchar_t* key;const char* name;};
  const Key keys[]={{L"Renderer",L"ConfigVersion","Renderer.ConfigVersion"},{L"Filtering",L"AnisotropicFiltering","Filtering.AnisotropicFiltering"},{L"Filtering",L"MaxAnisotropy","Filtering.MaxAnisotropy"},{L"Camera",L"GameplayFOV","Camera.GameplayFOV"},{L"Camera",L"VerticalFOVDegrees","Camera.VerticalFOVDegrees"},{L"Shadows",L"Mode","Shadows.Mode"},{L"VehicleReflections",L"Mode","VehicleReflections.Mode"}};
  const Key quality_keys[]={{L"Display",L"AutoHideCursor","Display.AutoHideCursor"},{L"Display",L"CursorHideDelayMs","Display.CursorHideDelayMs"},{L"Display",L"Mode","Display.Mode"},{L"Display",L"Width","Display.Width"},{L"Display",L"Height","Display.Height"},{L"Display",L"RefreshRate","Display.RefreshRate"},{L"Widescreen",L"InterfaceMode","Widescreen.InterfaceMode"},{L"AntiAliasing",L"Mode","AntiAliasing.Mode"},{L"AntiAliasing",L"Samples","AntiAliasing.Samples"},{L"Compatibility",L"MenuFreezeFix","Compatibility.MenuFreezeFix"}};
  auto read=[&](const Key& k){wchar_t b[256];DWORD n=GetPrivateProfileStringW(k.section,k.key,L"__ABSENT__",b,256,path.c_str());if(n>=255)fields[k.name]="__TRUNCATED_INVALID__";else if(wcscmp(b,L"__ABSENT__"))fields[k.name]=utf8(b);};
  for(const auto& k:keys)read(k);for(const auto& k:quality_keys)read(k);
 }
 return parse_visual_config(fields,found);
}
std::string config_json(const VisualConfig& c){std::ostringstream o;o<<"{\"config_found\":"<<(c.found?"true":"false")<<",\"ConfigVersion\":"<<(c.version_ok?"1":"null")<<",\"anisotropy\":"<<(c.anisotropy?"true":"false")<<",\"max_anisotropy\":"<<c.max_anisotropy<<",\"gameplay_fov\":"<<(c.fov?"true":"false")<<",\"vfov\":"<<c.vfov<<",\"shadow\":"<<quote(c.shadow_off?"Off":"Stock")<<",\"reason\":"<<quote(c.reason)<<",\"af_reason\":"<<quote(c.af_reason)<<",\"fov_reason\":"<<quote(c.fov_reason)<<",\"shadow_reason\":"<<quote(c.shadow_reason)<<",\"vehicle_reflections\":"<<quote(c.reflection_mode)<<",\"reflection_reason\":"<<quote(c.reflection_reason)<<",\"display_mode\":"<<quote(c.display_mode)<<",\"auto_hide_cursor\":"<<(c.auto_hide_cursor?"true":"false")<<",\"cursor_hide_delay_ms\":"<<c.cursor_delay_ms<<",\"cursor_reason\":"<<quote(c.cursor_reason)<<",\"display_width\":"<<c.width<<",\"display_height\":"<<c.height<<",\"refresh_rate\":"<<c.refresh<<",\"display_reason\":"<<quote(c.display_reason)<<",\"interface_mode\":"<<quote(c.interface_mode)<<",\"interface_reason\":"<<quote(c.interface_reason)<<",\"aa_mode\":"<<quote(c.aa_mode)<<",\"aa_samples\":"<<c.samples<<",\"aa_reason\":"<<quote(c.aa_reason)<<",\"menu_freeze_fix\":"<<(c.menu_freeze?"true":"false")<<",\"freeze_reason\":"<<quote(c.freeze_reason)<<",\"raw_fields\":{";bool first=true;for(const auto& entry:c.raw_fields){if(!first)o<<',';first=false;o<<quote(entry.first)<<':'<<quote(entry.second);}o<<"}}";return o.str();}
void VisualPolicy::configure(const VisualConfig& c,bool known,const D3DCAPS8* caps,HRESULT hr){
 requested=c;effective=c;caps_result=hr;
 if(c.reflection_mode=="ViewDependent2D")effective.reflection_reason="requires_live_or_learned_body_proof_current_material";
 if(!known){effective.fov=effective.shadow_off=false;effective.reason="feature_local_compatibility";effective.reflection_mode="Stock";effective.reflection_reason="unsupported_build";}
 // Game-specific quality capabilities are applied by the device/root owners.
 // AF is purely D3D-generic and still goes through actual device capability checks.
 if(effective.anisotropy){
  if(caps&&SUCCEEDED(hr)){caps_max=caps->MaxAnisotropy;min_supported=(caps->TextureFilterCaps&D3DPTFILTERCAPS_MINFANISOTROPIC)!=0;mag_supported=(caps->TextureFilterCaps&D3DPTFILTERCAPS_MAGFANISOTROPIC)!=0;}
  if(!caps||FAILED(hr)||caps_max<2||!min_supported){effective.anisotropy=false;effective.af_reason="unsupported_min_anisotropy_or_caps_query_failed";}
  else effective.max_anisotropy=std::min(c.max_anisotropy,static_cast<unsigned>(caps_max));
 }
}
DWORD VisualPolicy::filter(DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD value) const noexcept {
 if(!effective.anisotropy||stage!=0)return value;
 if(type==D3DTSS_MAXANISOTROPY&&value>0)return effective.max_anisotropy;
 if(value!=D3DTEXF_LINEAR)return value;
 if(type==D3DTSS_MINFILTER&&min_supported)return D3DTEXF_ANISOTROPIC;
 return value;
}
bool symmetric_lh(const D3DMATRIX& p) noexcept {
 const float* f=&p.m[0][0];for(int i=0;i<16;++i){if(!std::isfinite(f[i]))return false;if(i!=0&&i!=5&&i!=10&&i!=11&&i!=14&&f[i]!=0.f)return false;}
 return p._11>0.f&&p._22>0.f&&p._33>1.f&&p._34==1.f&&p._43<0.f;
}
float vertical_fov(const D3DMATRIX& p) noexcept {PolicyFP fp;return static_cast<float>(2.*std::atan(1./p._22)*180./3.14159265358979323846);}
double source_camera_angle(const D3DMATRIX& p) noexcept {
 PolicyFP fp;if(!symmetric_lh(p))return 0.;
 const double aspect=static_cast<double>(p._22)/p._11;
 // Original helper 004F2350 scales authored angle by H/W only for landscape.
 return 2.*std::atan(1./p._22)*180./3.14159265358979323846*std::max(1.,aspect);
}
bool VisualPolicy::projection(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* input,D3DMATRIX& out,bool exe_caller,uint32_t rva) const noexcept {
 PolicyFP fp;
 if(!effective.fov||type!=D3DTS_PROJECTION||!exe_caller||rva!=GAMEPLAY_PROJECTION_RETURN_RVA||!input||!safe_copy(&out,input,sizeof(out))||!symmetric_lh(out))return false;
 if(std::abs(source_camera_angle(out)-90.)>SOURCE_CAMERA_TOLERANCE_DEGREES)return false;
 double aspect=static_cast<double>(out._22)/out._11;double y=1./std::tan(effective.vfov*3.14159265358979323846/360.);
 if(!std::isfinite(aspect)||aspect<=0||!std::isfinite(y))return false;
 out._11=static_cast<float>(y/aspect);out._22=static_cast<float>(y);return std::isfinite(out._11)&&out._11>0&&std::isfinite(out._22)&&out._22>0;
}
bool VisualPolicy::suppress(uint32_t slot,bool exe_caller,uint32_t rva,const Shadow& s,D3DPRIMITIVETYPE primitive) const noexcept {
 return effective.shadow_off&&slot==70&&exe_caller&&rva==STOCK_SHADOW_RETURN_RVA&&primitive==D3DPT_TRIANGLELIST&&
 s.rs[27].known&&s.rs[27].value==1&&s.rs[28].known&&s.rs[28].value==0&&s.rs[14].known&&s.rs[14].value==0&&
 s.bindings.vertex_shader.known&&s.bindings.vertex_shader.value==0x142;
}
}
