#pragma once
// Shared helpers of the PS2 DrawIndexedPrimitive handler chain (patch 0001): every handler reports its native calls
// through notify() and returns a Result (handled = the draw was consumed, hr = what to return to the game).
#include "reflection_native_integration.hpp"
namespace gfx2::dipintegration {
inline void notify(Device8& d,uint32_t slot,const Args& a,HRESULT hr) noexcept {
    d.trace.after(slot,a,static_cast<uint32_t>(hr),0,&a,256,false,true);
}
struct Result{bool handled=false;HRESULT hr=S_OK;};
} // namespace gfx2::dipintegration
