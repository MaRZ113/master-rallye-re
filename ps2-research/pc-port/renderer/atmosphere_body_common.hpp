#pragma once
#include "atmosphere_native.hpp"
namespace gfx2::atmospherebody {
struct Timing {atmosphere::Pilot& p;LARGE_INTEGER start{};Timing(atmosphere::Pilot& x):p(x){QueryPerformanceCounter(&start);}~Timing(){LARGE_INTEGER end{};QueryPerformanceCounter(&end);p.body_cpu_ticks+=end.QuadPart-start.QuadPart;++p.body_calls;}};
// Apply an achromatic exposure AFTER the original reflection combine. Original
// reflection texture, UV transform, alpha and capture remain unchanged. Every
// modified state is retained in Pending until a successful restoration.
inline HRESULT environment_exposure(Device8& d,atmosphere::Pilot& p) {
    auto& n=*d.native();auto& saved=p.pending;if(saved.body_pending)return D3DERR_DEVICELOST;
    const float gain=1+p.lighting.strength*(std::min(p.lighting.world_brightness,1.f)-1);
    if(gain>=.999f)return S_OK;
    constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_RESULTARG,D3DTSS_ALPHAARG2};
    for(unsigned i=0;i<7;++i)if(FAILED(n.GetTextureStageState(2,keys[i],&saved.body_stage[i])))return D3DERR_INVALIDCALL;
    DWORD next=0;if(saved.body_stage[0]!=D3DTOP_DISABLE||FAILED(n.GetTextureStageState(3,D3DTSS_COLOROP,&next))||next!=D3DTOP_DISABLE||FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&saved.body_factor)))return D3DERR_INVALIDCALL;
    const DWORD v=DWORD(std::clamp(std::lround(gain*255),0l,255l));const DWORD factor=0xff000000u|(v<<16)|(v<<8)|v;
    const DWORD values[]{D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TFACTOR,D3DTOP_SELECTARG1,D3DTA_CURRENT,D3DTA_CURRENT,D3DTA_CURRENT};
    // Enable COLOROP last so partially installed state is never submitted.
    for(unsigned i: {7u,1u,2u,3u,4u,5u,6u,0u}){saved.body_pending|=1u<<i;
        const auto hr=i==7?n.SetRenderState(D3DRS_TEXTUREFACTOR,factor):n.SetTextureStageState(2,keys[i],values[i]);
        if(i==7)atmosphereintegration::notify(d,50,pack(D3DRS_TEXTUREFACTOR,factor),hr);else atmosphereintegration::notify(d,63,pack(2,keys[i],values[i]),hr);
        if(FAILED(hr))return hr;
    }
    if(p.first_reason("body_environment_exposure_installed"))session().write("{\"type\":\"atmosphere_body_exposure\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"gain\":"+std::to_string(gain)+",\"reflection_uv_changed\":false,\"alpha_preserved\":true,\"pending_restore_slots\":8}");
    return S_OK;
}
inline bool shade(std::vector<uint8_t>& bytes,unsigned stride,unsigned color_offset,unsigned normal_offset,const D3DMATRIX& world,const atmosphere::Lighting& lighting,bool replace_ps2_prepared,uint64_t& changed) {
    std::array<float,16> transform{};std::memcpy(transform.data(),&world,64);changed=0;
    if(!stride||bytes.size()%stride||color_offset+4>stride||normal_offset+12>stride)return false;
    for(size_t i=0;i<bytes.size();i+=stride){auto* v=bytes.data()+i;std::array<float,3> n{},world_normal{};std::memcpy(n.data(),v+normal_offset,12);
        if(!atmosphere::transformed_normal(n,transform,world_normal))return false;uint32_t original=0;std::memcpy(&original,v+color_offset,4);
        // VL1's model-space normal-Y directional term must not be multiplied by
        // another directional term. Replace it in the transient copy with its
        // neutral .4 base; alpha and immutable prepared source remain intact.
        const auto color=atmosphere::body_color(original,world_normal,lighting,replace_ps2_prepared);changed+=color!=original;std::memcpy(v+color_offset,&color,4);
    }return true;
}
inline void debug_sample(Device8& d,atmosphere::Pilot& p,const char* route,const std::string& family,const void* original,const void* effective,size_t vertices,const D3DMATRIX& world) {
    if(!p.body_debug||!d.trace.control.active)return;const auto frame=d.trace.frame_number();
    if(p.body_debug_frame!=frame){p.body_debug_frame=frame;p.body_debug_count=0;}if(p.body_debug_count>=32)return;++p.body_debug_count;
    std::array<float,16> transform{};std::memcpy(transform.data(),&world,64);std::string samples="[";
    for(size_t i=0;i<std::min(vertices,size_t(8));++i){const auto* a=static_cast<const uint8_t*>(original)+i*36;const auto* b=static_cast<const uint8_t*>(effective)+i*36;
        uint32_t before=0,after=0;std::memcpy(&before,a+24,4);std::memcpy(&after,b+24,4);std::array<float,3> n{},wn{};std::memcpy(n.data(),a+12,12);atmosphere::transformed_normal(n,transform,wn);
        if(i)samples+=",";samples+="{\"source_prelight\":"+std::to_string(before)+",\"effective_color\":"+std::to_string(after)+",\"world_normal\":["+std::to_string(wn[0])+","+std::to_string(wn[1])+","+std::to_string(wn[2])+"]}";
    }
    atmosphereintegration::debug_record(d,"{\"type\":\"atmosphere_body_samples\",\"frame\":"+std::to_string(frame)+",\"route\":"+quote(std::string(route))+",\"family\":"+quote(family)+",\"vertices\":"+std::to_string(vertices)+",\"samples\":"+samples+"]}");
}

}
