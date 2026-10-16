#pragma once
#include <array>
#include <cstring>
#include <utility>
#include "xtrail_glass.hpp"
#include "brake_glow_identity.hpp"
#include "brake_glow_registry.hpp"
#include "kia_lamp_continuity.hpp"
namespace gfx2::ps2port {
bool terrano_glow_identity(const DrawSnapshot&,std::string_view geometry=kTerranoGlowGeometry,std::string_view attributes=kTerranoGlowAttributes)noexcept;
const BrakeGlowProfile* fleet_glow_identity(const DrawSnapshot&)noexcept;
class BrakeGlow {
 bool requested_=false,diagnostics_=false,disabled_=false,blocked_=false;uint64_t logs_=0;std::array<std::pair<unsigned,const char*>,64> fleet_rejections_{};unsigned fleet_rejection_count_=0;
 std::vector<DWORD> pixels_,kia_on_pixels_;IDirect3DTexture8* texture_=nullptr;IDirect3DTexture8* kia_on_texture_=nullptr;
public:
 KiaLampContinuity kia_lamps;std::array<NativeLampContinuity,25> fleet_lamps;std::array<uint8_t,25> fleet_lamp_logs{};
 struct OffReference {KiaLampContext owner;std::vector<std::array<float,3>> positions;std::vector<unsigned> order;};std::array<OffReference,8> private_off_reference;
 bool claim_fleet(unsigned family,unsigned layer,bool damaged)noexcept{if(!diagnostics_||family>=25||layer>=3)return false;const unsigned bit=1u<<(layer*2+(damaged?1:0));if(fleet_lamp_logs[family]&bit)return false;fleet_lamp_logs[family]|=uint8_t(bit);return true;}
 // Rejections are logged once per family and literal reason, bounded.
 bool claim_fleet_rejection(unsigned family,const char* why)noexcept{if(!diagnostics_||family>=25||!why)return false;for(unsigned i=0;i<fleet_rejection_count_;++i)if(fleet_rejections_[i].first==family&&!std::strcmp(fleet_rejections_[i].second,why))return false;if(fleet_rejection_count_>=fleet_rejections_.size())return false;fleet_rejections_[fleet_rejection_count_++]={family,why};return true;}
 GlassTransaction transaction;
 BrakeGlow(bool supported,const std::wstring& ini)noexcept;
 ~BrakeGlow(){before_reset();}
 bool initialize(IDirect3DDevice8&)noexcept;
 bool initialize_kia_on(IDirect3DDevice8&)noexcept;
 IDirect3DTexture8* kia_on_texture()const noexcept{return kia_on_texture_;}
 IDirect3DTexture8* texture()const noexcept{return texture_;}
 bool requested()const noexcept{return requested_&&!disabled_;}
 bool blocked()const noexcept{return blocked_;}
 void disable()noexcept{disabled_=true;}
 bool claim(bool success,unsigned profile=0)noexcept{if(profile>std::size(kBrakeGlowProfiles))return false;const uint64_t bit=uint64_t(1)<<(profile*2+(success?1:0));if(!diagnostics_||(logs_&bit))return false;logs_|=bit;return true;}
 void before_reset()noexcept{if(transaction.pending())blocked_=true;transaction.release();if(texture_)texture_->Release();texture_=nullptr;if(kia_on_texture_)kia_on_texture_->Release();kia_on_texture_=nullptr;}
 void after_reset(bool called,bool success)noexcept{if(called&&success){blocked_=false;logs_=0;}}
};
}
