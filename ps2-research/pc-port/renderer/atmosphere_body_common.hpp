#pragma once
#include "atmosphere_native.hpp"
namespace gfx2::atmospherebody {
struct Timing {atmosphere::Pilot& p;LARGE_INTEGER start{};Timing(atmosphere::Pilot& x):p(x){QueryPerformanceCounter(&start);}~Timing(){LARGE_INTEGER end{};QueryPerformanceCounter(&end);p.body_cpu_ticks+=end.QuadPart-start.QuadPart;++p.body_calls;}};
// Diffuse exposure is already applied in body_color. Never multiply the final
// reflection combine again: doing so crushes diffuse AND environment highlights.
// Keep this hook shared by native and PS2 fleet paths without touching stages.
inline HRESULT environment_exposure(Device8& d,atmosphere::Pilot& p) {
    if(p.first_reason("body_environment_unscaled"))session().write("{\"type\":\"atmosphere_body_exposure\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"gain\":1,\"policy\":\"diffuse_only_native_highlights\",\"reflection_uv_changed\":false,\"alpha_preserved\":true,\"pending_restore_slots\":0}");
    return S_OK;
}
inline bool shade(std::vector<uint8_t>& bytes,unsigned stride,unsigned color_offset,unsigned normal_offset,const D3DMATRIX& world,const atmosphere::Lighting& lighting,bool replace_ps2_prepared,uint64_t& changed,uint32_t role=atmosphere::Paint,const D3DMATRIX* view=nullptr) {
    std::array<float,16> transform{};std::memcpy(transform.data(),&world,64);changed=0;
    if(!stride||bytes.size()%stride||color_offset+4>stride||normal_offset+12>stride)return false;
    std::array<float,3> camera{};std::array<float,16> vm{};if(view)std::memcpy(vm.data(),view,64);
    const bool rim=lighting.rim&&view&&(role==atmosphere::Paint||role==atmosphere::OpaquePanel)&&atmosphere::rigid_camera_position(vm,camera);
    for(size_t i=0;i<bytes.size();i+=stride){auto* v=bytes.data()+i;std::array<float,3> n{},world_normal{};std::memcpy(n.data(),v+normal_offset,12);
        if(role!=atmosphere::OpaqueFlat&&role!=atmosphere::OpaqueInterior&&!atmosphere::transformed_normal(n,transform,world_normal))return false;uint32_t original=0;std::memcpy(&original,v+color_offset,4);
        // VL1's model-space normal-Y directional term must not be multiplied by
        // another directional term. Replace it in the transient copy with its
        // neutral .4 base; alpha and immutable prepared source remain intact.
        auto color=atmosphere::vehicle_surface_color(original,world_normal,lighting,replace_ps2_prepared,role);
        if(rim){std::array<float,3> position{},eye{};std::memcpy(position.data(),v,12);bool finite=true;for(float x:position)finite=finite&&std::isfinite(x);
            if(finite){for(unsigned j=0;j<3;++j)eye[j]=camera[j]-(position[0]*transform[j]+position[1]*transform[4+j]+position[2]*transform[8+j]+transform[12+j]);
                const float amount=atmosphere::rim_amount(world_normal,eye,lighting.direction,lighting.rim_power)*lighting.rim_strength;const float peak=std::max({lighting.sun[0],lighting.sun[1],lighting.sun[2],.01f});
                uint32_t result=color&0xff000000;for(unsigned j=0;j<3;++j){const unsigned shift=(2-j)*8;const float old=float((color>>shift)&255);result|=uint32_t(std::clamp(std::lround(old+(255-old)*amount*lighting.sun[j]/peak),0l,255l))<<shift;}color=result;}}
        changed+=color!=original;std::memcpy(v+color_offset,&color,4);
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
