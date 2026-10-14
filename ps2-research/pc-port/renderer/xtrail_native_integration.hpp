#pragma once
#include "reflection_native_integration.hpp"
#include "xtrail_fidelity.hpp"
#include "xtrail_decal_registry.hpp"
#include "xtrail_glass.hpp"
#include "brake_glow.hpp"
#include "course_objects_native_integration.hpp"
namespace gfx2::xtrailintegration {
inline void notify(Device8& d,uint32_t slot,const Args& a,HRESULT hr) noexcept {
    d.trace.after(slot,a,static_cast<uint32_t>(hr),0,&a,256,false,true);
}
inline HRESULT repair(Device8& d) noexcept {
    auto* p=d.ps2_port()?d.ps2_port()->xtrail():nullptr;if(!p)return S_OK;
    if(p->blocked())return D3DERR_DEVICELOST;
    if(auto* brake=p->brake()){if(brake->blocked())return D3DERR_DEVICELOST;if(brake->transaction.pending()){auto hr=brake->transaction.restore(*d.native(),[&](uint32_t slot,const Args& a,HRESULT h)noexcept{notify(d,slot,a,h);});if(FAILED(hr))return hr;}}
    if(auto* glass=p->glass()){
        if(glass->blocked())return D3DERR_DEVICELOST;
        if(glass->transaction.pending()){const auto hr=glass->transaction.restore(*d.native(),[&](uint32_t slot,const Args& a,HRESULT h)noexcept{notify(d,slot,a,h);});if(FAILED(hr))return hr;}
    }
    if(!p->transaction.pending())return S_OK;
    return p->transaction.restore(*d.native(),[&](uint32_t slot,const Args& a,HRESULT hr) noexcept {notify(d,slot,a,hr);});
}
struct Result{bool handled=false;HRESULT hr=S_OK;};
inline Result draw(Device8& d,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc) noexcept {
    auto* e=d.ps2_port();auto* p=e?e->xtrail():nullptr;auto* reflection=e?e->reflection():nullptr;
    if(!p||!p->requested()||!reflection||!reflection->active()||reflection->mode_value()!=4||
       d.visuals.effective.reflection_mode!="Stock"||
       type!=D3DPT_TRIANGLELIST||vertices!=20||count!=14||!d.trace.scene_active||
       d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return {};
    const auto image=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if(image!=0x400000||pc<image||pc-image!=SHARED_WORLD_RETURN_RVA)return {};
    bool committed=false;HRESULT target_result=E_PENDING;
    try {
        auto& n=*d.native();ps2integration::Ref<IDirect3DVertexBuffer8> vb;ps2integration::Ref<IDirect3DIndexBuffer8> ib;
        DWORD fvf=0,pixel=0;UINT stride=0,base=0;
        if(FAILED(n.GetVertexShader(&fvf))||fvf!=0x142||FAILED(n.GetPixelShader(&pixel))||pixel||
           FAILED(n.GetStreamSource(0,&vb.value,&stride))||!vb.value||stride!=24||
           FAILED(n.GetIndices(&ib.value,&base))||!ib.value)return {};
        const auto& bindings=d.trace.effective_shadow.bindings;
        if(!bindings.vertex_shader.known||bindings.vertex_shader.value!=fvf||
           !bindings.pixel_shader.known||bindings.pixel_shader.value!=pixel||
           !bindings.streams[0].known||bindings.streams[0].value.pointer!=reinterpret_cast<uintptr_t>(vb.value)||
           bindings.streams[0].value.stride!=stride||!bindings.indices.known||
           bindings.indices.value.pointer!=reinterpret_cast<uintptr_t>(ib.value)||bindings.indices.value.base!=base)return {};
        D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC id{};
        if(FAILED(vb.value->GetDesc(&vd))||FAILED(ib.value->GetDesc(&id)))return {};
        const UINT size=id.Format==D3DFMT_INDEX16?2u:id.Format==D3DFMT_INDEX32?4u:0;
        const uint64_t vo=(uint64_t(base)+min_index)*24,vs=uint64_t(vertices)*24,io=uint64_t(start)*size,is=uint64_t(count)*3*size;
        if(!size||vo>vd.Size||vs>vd.Size-vo||io>id.Size||is>id.Size-io)return {};
        ps2port::DrawSnapshot g;g.supported_build=session().target;g.device_id=d.trace.device_id();g.reset_generation=e->reset_generation();
        g.primitive_type=type;g.primitive_count=count;g.min_index=min_index;g.vertex_count=vertices;g.start_index=start;
        g.base_vertex=base;g.fvf=fvf;g.stride=stride;g.index_format=id.Format;g.vertex_byte_offset=vo;
        g.vertex_resource=reinterpret_cast<uintptr_t>(vb.value);g.index_resource=reinterpret_cast<uintptr_t>(ib.value);
        g.vertex_generation=d.trace.resources.generation(g.vertex_resource);g.index_generation=d.trace.resources.generation(g.index_resource);
        if(!g.vertex_generation||!g.index_generation||
           !d.copy_buffer_shadow(vb.value,BufferKind::Vertex,g.vertex_generation,vo,static_cast<size_t>(vs),g.vertex_bytes,g.vertex_revision)||
           !d.copy_buffer_shadow(ib.value,BufferKind::Index,g.index_generation,io,static_cast<size_t>(is),g.index_bytes,g.index_revision))return {};
        g.complete_mirror_coverage=true;
        const auto* data=p->prepare(g);
        auto log=[&](bool success,const char* reason,HRESULT apply,HRESULT draw,HRESULT restore) noexcept {
            if(!p->claim(success))return;
            try{session().write("{\"type\":\"ps2_xtrail_decal\",\"frame\":"+std::to_string(d.trace.frame_number())+
                ",\"expected_geometry_sha256\":"+quote(ps2port::kXtrailDecalGeometrySha)+
                ",\"source_upload_verified\":"+(data?"true":"false")+",\"reason\":"+quote(reason)+
                ",\"override_applied\":"+(success?"true":"false")+",\"native_target_draws\":"+(draw==E_PENDING?"0":"1")+
                ",\"native_method\":\"DrawPrimitiveUP\",\"triangles\":14,\"normal_augmentation_applied\":"+(success?"true":"false")+",\"vertex_generation\":"+
                std::to_string(g.vertex_generation)+",\"index_generation\":"+std::to_string(g.index_generation)+
                ",\"vertex_revision\":"+std::to_string(g.vertex_revision)+",\"index_revision\":"+std::to_string(g.index_revision)+
                ",\"reset_generation\":"+std::to_string(g.reset_generation)+",\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(apply))+
                ",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(draw))+
                ",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restore))+
                ",\"restore_pending\":"+(p->transaction.pending()?"true":"false")+"}");}catch(...){}
        };
        if(!data){log(false,"current_geometry_uv_or_diffuse_not_source_compatible",E_PENDING,E_PENDING,E_PENDING);return {};}
        // Race ownership and every native material dependency remain current.
        uintptr_t manager=0,camera=0;uint32_t cameras=0;
        if(!safe_copy(&manager,reinterpret_cast<void*>(image+CAMERA_MANAGER_RVA),4)||!manager||
           !safe_copy(&cameras,reinterpret_cast<void*>(manager+16),4)||cameras!=1||
           !safe_copy(&camera,reinterpret_cast<void*>(manager),4)||!camera)return {};
        const auto certificate=live_race_certificate(camera);
        if(!certificate.valid||!certificate.race_generation||!certificate.owner_lifetime)return {};
        D3DMATRIX world{},texture_matrix{};
        for(auto key:{D3DTS_WORLD,D3DTS_TEXTURE1}){
            auto& matrix=key==D3DTS_WORLD?world:texture_matrix;const auto& tracked=d.trace.effective_shadow.matrices[key];
            if(!tracked.known||FAILED(n.GetTransform(key,&matrix))||!courseintegration::finite_matrix(matrix)||std::memcmp(&matrix,&tracked.value,64))return {};
        }
        constexpr D3DRENDERSTATETYPE rs[]={D3DRS_ALPHATESTENABLE,D3DRS_ALPHABLENDENABLE,D3DRS_ZWRITEENABLE,D3DRS_LIGHTING};
        constexpr DWORD expected[]={FALSE,FALSE,TRUE,FALSE};
        for(unsigned i=0;i<4;++i){DWORD value=0;auto& tracked=d.trace.effective_shadow.rs[rs[i]];
            if(!tracked.known||FAILED(n.GetRenderState(rs[i],&value))||value!=expected[i]||value!=tracked.value)return {};}
        constexpr std::array<DWORD,8> base_stage={D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,0};
        for(unsigned stage=0;stage<2;++stage)for(unsigned i=0;i<8;++i){
            DWORD value=0;const auto key=ps2port::kReflectionStageStates[i];const auto& tracked=d.trace.effective_shadow.tss[stage][key];
            if(!tracked.known||FAILED(n.GetTextureStageState(stage,key,&value))||value!=tracked.value)return {};
            if(stage==0&&value!=base_stage[i])return {};
            if(stage==1&&i==0&&value!=D3DTOP_DISABLE)return {};
        }
        DWORD next=0,result_arg=0;
        if(FAILED(n.GetTextureStageState(2,D3DTSS_COLOROP,&next))||next!=D3DTOP_DISABLE||
           FAILED(n.GetTextureStageState(1,D3DTSS_RESULTARG,&result_arg))||result_arg!=D3DTA_CURRENT||!courseintegration::native_dependencies(n))return {};
        ps2integration::Ref<IDirect3DBaseTexture8> primary;
        if(FAILED(n.GetTexture(0,&primary.value))||!primary.value||primary.value->GetType()!=D3DRTYPE_TEXTURE||
           !d.trace.resources.generation(reinterpret_cast<uintptr_t>(primary.value)))return {};
        if(!bindings.textures[0].known||bindings.textures[0].value!=reinterpret_cast<uintptr_t>(primary.value))return {};
        ps2integration::Ref<IDirect3DBaseTexture8> old_secondary;
        if(FAILED(n.GetTexture(1,&old_secondary.value))||!bindings.textures[1].known||
           bindings.textures[1].value!=reinterpret_cast<uintptr_t>(old_secondary.value)||
           (old_secondary.value&&!d.trace.resources.generation(reinterpret_cast<uintptr_t>(old_secondary.value))))return {};
        D3DCAPS8 caps{};if(FAILED(n.GetDeviceCaps(&caps))||caps.MaxSimultaneousTextures<2||caps.MaxTextureBlendStages<2||
           !(caps.TextureOpCaps&D3DTEXOPCAPS_ADD)||!(caps.VertexProcessingCaps&D3DVTXPCAPS_TEXGEN)||caps.MaxPrimitiveCount<14)return {};
        auto& capture=reflection->mixed_capture();capture.set_writer(&d,[](void* owner,uint32_t slot,const Args& a,HRESULT hr) noexcept {notify(*static_cast<Device8*>(owner),slot,a,hr);});
        const auto captured=capture.capture(n,reflection->static_texture(),d.trace.frame_number(),false);
        if(capture.pending()){const auto hr=ps2integration::repair(d);if(FAILED(hr))return {true,hr};}
        auto* mixed=capture.ready_texture(d.trace.frame_number());if(FAILED(captured)||!mixed)return {};
        auto& transaction=p->transaction;
        auto hr=transaction.capture(n);if(FAILED(hr))return {};
        auto writer=[&](uint32_t slot,const Args& a,HRESULT h) noexcept {notify(d,slot,a,h);};
        committed=true; // Any attempted native write closes the unguarded exception fallback.
        const auto apply=transaction.apply(n,mixed,writer);
        if(FAILED(apply)){
            const auto restore=transaction.restore(n,writer);log(false,"apply_failed",apply,E_PENDING,restore);
            if(FAILED(restore)){p->disable();return {true,restore};}return {};
        }
        transaction.mark_up();
        const auto result=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,14,data->data(),sizeof(ps2port::XtrailDecalVertex));
        target_result=result;
        notify(d,72,pack(D3DPT_TRIANGLELIST,14,data->data(),sizeof(ps2port::XtrailDecalVertex)),result);
        const auto restore=transaction.restore(n,writer);
        if(FAILED(restore))p->disable();log(true,"exact_xtrail_plate_current_upload_and_source_normals",apply,result,restore);
        return {true,result}; // never retry original geometry after this submission
    }catch(...){
        if(!committed)return {};
        const auto restored=repair(d);if(FAILED(restored))p->disable();
        return {true,target_result==E_PENDING?E_FAIL:target_result};
    }
}
} // namespace gfx2::xtrailintegration
