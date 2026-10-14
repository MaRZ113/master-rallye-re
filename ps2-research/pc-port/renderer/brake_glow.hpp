#pragma once
#include "xtrail_glass.hpp"
#include "brake_glow_identity.hpp"
namespace gfx2::ps2port {
bool terrano_glow_identity(const DrawSnapshot&,std::string_view geometry=kTerranoGlowGeometry,std::string_view attributes=kTerranoGlowAttributes)noexcept;
class BrakeGlow {
 bool requested_=false,diagnostics_=false,disabled_=false,blocked_=false;unsigned logs_=0;
public:
 GlassTransaction transaction;
 BrakeGlow(bool supported,const std::wstring& ini)noexcept{
  wchar_t mode[16]{},version[16]{};GetPrivateProfileStringW(L"PS2Port",L"BrakeGlowMode",L"0",mode,16,ini.c_str());GetPrivateProfileStringW(L"PS2Port",L"BrakeGlowVersion",L"1",version,16,ini.c_str());requested_=xtrail_fidelity_opt_in(mode,version,supported);diagnostics_=GetPrivateProfileIntW(L"PS2Port",L"BrakeGlowDiagnostics",0,ini.c_str())==1;
 }
 bool requested()const noexcept{return requested_&&!disabled_;}
 bool blocked()const noexcept{return blocked_;}
 void disable()noexcept{disabled_=true;}
 bool claim(bool success)noexcept{unsigned bit=success?2:1;if(!diagnostics_||(logs_&bit))return false;logs_|=bit;return true;}
 void before_reset()noexcept{if(transaction.pending())blocked_=true;transaction.release();}
 void after_reset(bool called,bool success)noexcept{if(called&&success){blocked_=false;logs_=0;}}
};
}
