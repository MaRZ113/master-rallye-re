#pragma once
#include "dip_integration.hpp"
#include "brake_glow.hpp"
namespace gfx2::lampintegration {
// Restores a brake-lamp transaction left pending by an interrupted draw (device repair / reset).
inline HRESULT repair(Device8& d) noexcept {
    auto* p=d.ps2_port()?d.ps2_port()->brake_glow():nullptr;if(!p)return S_OK;
    if(p->blocked())return D3DERR_DEVICELOST;if(!p->transaction.pending())return S_OK;
    return p->transaction.restore(*d.native(),[&](uint32_t slot,const Args& a,HRESULT h)noexcept{dipintegration::notify(d,slot,a,h);});
}
} // namespace gfx2::lampintegration
