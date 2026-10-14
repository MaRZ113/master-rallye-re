#pragma once
#include "xtrail_native_integration.hpp"
#include "xtrail_glass_identity.hpp"
namespace gfx2::xtrailintegration {
inline Result glass_draw(Device8& d,const DrawClassification& c,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc)noexcept{
    auto* e=d.ps2_port();auto* p=e&&e->xtrail()?e->xtrail()->glass():nullptr;auto* reflection=e?e->reflection():nullptr;
    if(!p||!p->requested()||!reflection||!reflection->active()||reflection->mode_value()!=4||
       type!=D3DPT_TRIANGLELIST||count!=18||vertices!=22||!d.trace.scene_active||
       GetCurrentThreadId()!=d.trace.render_thread_id()||d.trace.shadow.recording||d.trace.effective_shadow.recording)return {};
    bool committed=false;HRESULT result=E_PENDING;
    try{
        ps2port::DrawSnapshot g;ps2port::ReflectionSnapshot s;
        if(!ps2integration::snapshot(d,c,type,min_index,vertices,start,count,g,s,false,true)||
           !ps2port::partition_context_valid(s,e->reset_generation()))return {};
        const auto* data=p->prepare(g);
        auto log=[&](bool success,const char* reason,HRESULT primary,HRESULT highlight,HRESULT restored)noexcept{
            if(!p->claim(success))return;
            try{session().write("{\"type\":\"ps2_xtrail_headlight_glass\",\"frame\":"+std::to_string(d.trace.frame_number())+
                ",\"expected_geometry_sha256\":"+quote(ps2port::kXtrailGlassGeometrySha)+
                ",\"source_upload_verified\":"+(data!=nullptr?"true":"false")+",\"reason\":"+quote(reason)+
                ",\"override_applied\":"+(success?"true":"false")+",\"source\":\"STATIC_GLASS_PRIMARY_AND_STATIC_HIGHLIGHT\""+
                ",\"primary_hresult\":"+std::to_string(static_cast<uint32_t>(primary))+
                ",\"highlight_hresult\":"+std::to_string(static_cast<uint32_t>(highlight))+
                ",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+
                ",\"restore_pending\":"+(p->transaction.pending()?"true":"false")+
                ",\"vertex_generation\":"+std::to_string(g.vertex_generation)+",\"index_generation\":"+std::to_string(g.index_generation)+
                ",\"vertex_revision\":"+std::to_string(g.vertex_revision)+",\"index_revision\":"+std::to_string(g.index_revision)+
                ",\"reset_generation\":"+std::to_string(g.reset_generation)+",\"triangles_per_pass\":18}");}catch(...){}
        };
        if(!data){log(false,"native_source_attributes_do_not_match",E_PENDING,E_PENDING,E_PENDING);return {};}
        auto& n=*d.native();DWORD value=0;
        if(!courseintegration::native_dependencies(n)||FAILED(n.GetTextureStageState(2,D3DTSS_COLOROP,&value))||value!=D3DTOP_DISABLE)return {};
        for(DWORD stage:{0u,1u})if(FAILED(n.GetTextureStageState(stage,D3DTSS_RESULTARG,&value))||value!=D3DTA_CURRENT)return {};
        D3DMATRIX normal_matrix{};const auto& tracked=d.trace.effective_shadow.matrices[D3DTS_TEXTURE1];
        if(!tracked.known||FAILED(n.GetTransform(D3DTS_TEXTURE1,&normal_matrix))||!courseintegration::finite_matrix(normal_matrix)||std::memcmp(&normal_matrix,&tracked.value,64))return {};
        D3DCAPS8 caps{};if(FAILED(n.GetDeviceCaps(&caps))||!(caps.TextureOpCaps&D3DTEXOPCAPS_SELECTARG1)||
           !(caps.VertexProcessingCaps&D3DVTXPCAPS_TEXGEN)||caps.MaxPrimitiveCount<18||!(caps.SrcBlendCaps&D3DPBLENDCAPS_SRCALPHA)||!(caps.DestBlendCaps&D3DPBLENDCAPS_INVSRCALPHA)||!(caps.SrcBlendCaps&D3DPBLENDCAPS_ONE)||!(caps.DestBlendCaps&D3DPBLENDCAPS_ONE))return {};
        if(!p->initialize(n)){log(false,"private_texture_upload_failed",E_PENDING,E_PENDING,E_PENDING);return {};}
        auto& transaction=p->transaction;
        auto writer=[&](uint32_t slot,const Args& a,HRESULT h)noexcept{notify(d,slot,a,h);};
        auto hr=transaction.capture(n);if(FAILED(hr))return {};
        committed=true;hr=transaction.pass(n,p->primary(),false,normal_matrix,writer);
        if(FAILED(hr)){const auto restore=transaction.restore(n,writer);if(FAILED(restore)){p->disable();return {true,restore};}return {};}
        transaction.mark_up();result=n.DrawPrimitiveUP(type,18,data->data(),sizeof(ps2port::XtrailDecalVertex));notify(d,72,pack(type,18,data->data(),36),result);
        const HRESULT primary=result;HRESULT highlight=E_PENDING;
        if(SUCCEEDED(result)){
            hr=transaction.pass(n,p->highlight(),true,normal_matrix,writer);
            if(SUCCEEDED(hr)){transaction.mark_up();highlight=n.DrawPrimitiveUP(type,18,data->data(),36);notify(d,72,pack(type,18,data->data(),36),highlight);result=highlight;}
            else result=hr;
        }
        const auto restored=transaction.restore(n,writer);if(FAILED(restored))p->disable();
        log(SUCCEEDED(primary)&&SUCCEEDED(highlight)&&SUCCEEDED(restored),"exact_headlight_source_primary_uv_and_static_mode20_highlight",primary,highlight,restored);
        return {true,result}; // Original opaque cover never replays after a primary pass.
    }catch(...){if(!committed)return {};const auto restored=repair(d);if(FAILED(restored))p->disable();return {true,result==E_PENDING?E_FAIL:result};}
}
} // namespace gfx2::xtrailintegration
