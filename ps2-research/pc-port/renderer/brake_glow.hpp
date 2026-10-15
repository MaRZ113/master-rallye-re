#pragma once
#include "xtrail_glass.hpp"
#include "brake_glow_identity.hpp"
#include "brake_glow_registry.hpp"
namespace gfx2::ps2port {
bool terrano_glow_identity(const DrawSnapshot&,std::string_view geometry=kTerranoGlowGeometry,std::string_view attributes=kTerranoGlowAttributes)noexcept;
const BrakeGlowProfile* fleet_glow_identity(const DrawSnapshot&)noexcept;
class BrakeGlow {
 bool requested_=false,diagnostics_=false,disabled_=false,blocked_=false;uint64_t logs_=0;
 std::vector<DWORD> pixels_;IDirect3DTexture8* texture_=nullptr;
public:
 GlassTransaction transaction;
 BrakeGlow(bool supported,const std::wstring& ini)noexcept;
 ~BrakeGlow(){before_reset();}
 bool initialize(IDirect3DDevice8&)noexcept;
 IDirect3DTexture8* texture()const noexcept{return texture_;}
 bool requested()const noexcept{return requested_&&!disabled_;}
 bool blocked()const noexcept{return blocked_;}
 void disable()noexcept{disabled_=true;}
 bool claim(bool success,unsigned profile=0)noexcept{if(profile>20)return false;const uint64_t bit=uint64_t(1)<<(profile*2+(success?1:0));if(!diagnostics_||(logs_&bit))return false;logs_|=bit;return true;}
 void before_reset()noexcept{if(transaction.pending())blocked_=true;transaction.release();if(texture_)texture_->Release();texture_=nullptr;}
 void after_reset(bool called,bool success)noexcept{if(called&&success){blocked_=false;logs_=0;}}
};
}
