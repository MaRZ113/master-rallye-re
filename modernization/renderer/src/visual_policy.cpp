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
bool boolean(std::string v,bool& out){v=trim(v);for(char& c:v)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));if(v=="true"){out=true;return true;}if(v=="false"){out=false;return true;}return false;}
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
 auto mode=trim(get("Shadows.Mode","Stock"));if(mode=="Off")c.shadow_off=true;else if(mode!="Stock")c.shadow_reason="invalid_shadow_mode";
 return c;
}
VisualConfig read_visual_config(const std::wstring& path){
 auto attributes=GetFileAttributesW(path.c_str());bool found=attributes!=INVALID_FILE_ATTRIBUTES&&!(attributes&FILE_ATTRIBUTE_DIRECTORY);
 std::unordered_map<std::string,std::string> fields;
 if(found){
  struct Key{const wchar_t* section;const wchar_t* key;const char* name;};
  const Key keys[]={{L"Renderer",L"ConfigVersion","Renderer.ConfigVersion"},{L"Filtering",L"AnisotropicFiltering","Filtering.AnisotropicFiltering"},{L"Filtering",L"MaxAnisotropy","Filtering.MaxAnisotropy"},{L"Camera",L"GameplayFOV","Camera.GameplayFOV"},{L"Camera",L"VerticalFOVDegrees","Camera.VerticalFOVDegrees"},{L"Shadows",L"Mode","Shadows.Mode"}};
  for(const auto& k:keys){wchar_t b[256];DWORD n=GetPrivateProfileStringW(k.section,k.key,L"__ABSENT__",b,256,path.c_str());if(n>=255)fields[k.name]="__TRUNCATED_INVALID__";else if(wcscmp(b,L"__ABSENT__"))fields[k.name]=utf8(b);}
 }
 return parse_visual_config(fields,found);
}
std::string config_json(const VisualConfig& c){std::ostringstream o;o<<"{\"config_found\":"<<(c.found?"true":"false")<<",\"ConfigVersion\":"<<(c.version_ok?"1":"null")<<",\"anisotropy\":"<<(c.anisotropy?"true":"false")<<",\"max_anisotropy\":"<<c.max_anisotropy<<",\"gameplay_fov\":"<<(c.fov?"true":"false")<<",\"vfov\":"<<c.vfov<<",\"shadow\":"<<quote(c.shadow_off?"Off":"Stock")<<",\"reason\":"<<quote(c.reason)<<",\"af_reason\":"<<quote(c.af_reason)<<",\"fov_reason\":"<<quote(c.fov_reason)<<",\"shadow_reason\":"<<quote(c.shadow_reason)<<",\"raw_fields\":{";bool first=true;for(const auto& entry:c.raw_fields){if(!first)o<<',';first=false;o<<quote(entry.first)<<':'<<quote(entry.second);}o<<"}}";return o.str();}
void VisualPolicy::configure(const VisualConfig& c,bool known,const D3DCAPS8* caps,HRESULT hr){
 requested=c;effective=c;caps_result=hr;
 if(!known){effective.anisotropy=effective.fov=effective.shadow_off=false;effective.reason="unsupported_build";return;}
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
 if(type==D3DTSS_MAGFILTER&&mag_supported)return D3DTEXF_ANISOTROPIC;
 return value;
}
bool symmetric_lh(const D3DMATRIX& p) noexcept {
 const float* f=&p.m[0][0];for(int i=0;i<16;++i){if(!std::isfinite(f[i]))return false;if(i!=0&&i!=5&&i!=10&&i!=11&&i!=14&&f[i]!=0.f)return false;}
 return p._11>0.f&&p._22>0.f&&p._33>1.f&&p._34==1.f&&p._43<0.f;
}
float vertical_fov(const D3DMATRIX& p) noexcept {PolicyFP fp;return static_cast<float>(2.*std::atan(1./p._22)*180./3.14159265358979323846);}
bool VisualPolicy::projection(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* input,D3DMATRIX& out,bool exe_caller,uint32_t rva) const noexcept {
 PolicyFP fp;
 if(!effective.fov||type!=D3DTS_PROJECTION||!exe_caller||rva!=GAMEPLAY_PROJECTION_RETURN_RVA||!input||!safe_copy(&out,input,sizeof(out))||!symmetric_lh(out))return false;
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
