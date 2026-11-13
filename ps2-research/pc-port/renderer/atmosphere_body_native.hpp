#pragma once
// Included after the existing native model/owner integrations. This optional
// single-material prototype runs AFTER reflection snapshots, never changes a
// texture/normal/UV/material state, and restores VB/IB before reflection cleanup.
#include "atmosphere_native.hpp"
#include "atmosphere_body_general.hpp"
namespace gfx2::atmospherebody {
inline HRESULT begin(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,bool& applied)noexcept {
    applied=false;
    collect_lamp_attachment(d,type,min,vertices,start,count,pc);
    try{const auto result=general(d,type,min,vertices,start,count,pc,applied);if(applied||FAILED(result))return result;}catch(...){return atmosphereintegration::repair(d);}
    grime_blended(d,type,min,vertices,start,count,pc);   // R-SURFACE1 G1.1: glass, lamps, grille, decals (candidate only)
    {const auto result=night_energy(d,min,vertices,start,count,pc,applied);if(applied||FAILED(result))return result;}
    auto* p=atmosphereintegration::pilot(d);
    if(!p||!p->enabled()||!p->body_tata||!p->lighting.active()||type!=D3DPT_TRIANGLELIST||vertices!=48||count!=55||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||
       d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    try{
        auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
        auto rejected=[&](const char* why){if(!p->pending.any())p->pending.release();if(p->first_reason(why))atmosphereintegration::log(d,why);return S_OK;};
        DWORD fvf=0,pixel=1;
        if(FAILED(n.GetVertexShader(&fvf))||fvf!=0x152||FAILED(n.GetPixelShader(&pixel))||pixel||
           !groundintegration::render(d,n,D3DRS_LIGHTING,FALSE)||!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,FALSE)||
           !groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,FALSE)||!groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||
           !groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)||!groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||
           !groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE))return rejected("body_prototype_material_state_excluded");
        courseintegration::Ref<IDirect3DSurface8> target,back;
        if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return S_OK;
        frontendmodelintegration::Context owner;
        if(!frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner)||owner.owner.private_tree)return rejected("body_prototype_healthy_native_owner_missing");
        D3DMATRIX world{};if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||!frontendmodelintegration::fleet_owner_world(owner,world))return rejected("body_prototype_owner_world_mismatch");
        courseintegration::Ref<IDirect3DBaseTexture8> texture;if(FAILED(n.GetTexture(0,&texture.p)))return S_OK;
        if(atmosphereintegration::material_sha(d,*p,texture.p)!="0587119628cdc1f4a5d0903756f9091290f61b697711d83ec49a2ae6a6ecb66c")return rejected("body_prototype_not_original_tatabon_texture");
        if(p->pending.any())return D3DERR_DEVICELOST;
        atmosphereintegration::Geometry g;
        if(!atmosphereintegration::geometry(d,*p,min,vertices,start,count,g)||p->pending.stride!=36)return rejected("body_prototype_source_mirror_missing");
        ps2port::RaceDescriptors descriptors;uintptr_t vb=0,ib=0;
        if(!ps2port::race_descriptors(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),owner.mesh,frontendmodelintegration::word,descriptors)||
           !frontendmodelintegration::pointer_word(descriptors.vd[0],vb)||!frontendmodelintegration::pointer_word(descriptors.id[0],ib)||
           d.unwrap_vertex_buffer(reinterpret_cast<IDirect3DVertexBuffer8*>(vb))!=p->pending.stream||d.unwrap_index_buffer(reinterpret_cast<IDirect3DIndexBuffer8*>(ib))!=p->pending.indices||
           descriptors.vd[2]!=min||descriptors.vd[3]!=vertices||descriptors.vd[4]!=0x152||descriptors.vd[5]!=36||descriptors.id[2]!=start||descriptors.id[3]!=count*3)return rejected("body_prototype_current_descriptor_mismatch");
        ps2port::DrawSnapshot snapshot;snapshot.supported_build=session().target;snapshot.device_id=d.trace.device_id();snapshot.reset_generation=d.ps2_port()->reset_generation();
        snapshot.primitive_type=type;snapshot.min_index=min;snapshot.vertex_count=vertices;snapshot.start_index=start;snapshot.primitive_count=count;snapshot.fvf=0x152;snapshot.stride=36;
        snapshot.base_vertex=p->pending.base;snapshot.vertex_byte_offset=(uint64_t(snapshot.base_vertex)+min)*36;snapshot.vertex_bytes=g.bytes;
        snapshot.vertex_resource=reinterpret_cast<uintptr_t>(p->pending.stream);snapshot.index_resource=reinterpret_cast<uintptr_t>(p->pending.indices);
        snapshot.vertex_generation=g.vertex_generation;snapshot.index_generation=g.index_generation;snapshot.vertex_revision=g.vertex_revision;snapshot.index_revision=g.index_revision;
        snapshot.index_format=D3DFMT_INDEX32;snapshot.index_bytes.resize(g.indices.size()*4);
        for(size_t i=0;i<g.indices.size();++i){const uint32_t ix=g.indices[i]+min;std::memcpy(snapshot.index_bytes.data()+i*4,&ix,4);}snapshot.complete_mirror_coverage=true;
        // Existing source witness is exactly record19, tatabon/whitepaint, 55
        // triangles. Off-lamp additions in Reflection4 are NOT consulted here.
        if(ps2port::reflection_geometry_sha(snapshot)!=ps2port::kTataBonnetGeometrySha)return rejected("body_prototype_not_single_source_bonnet");
        std::array<float,16> transform{};std::memcpy(transform.data(),&world,64);uint64_t changed=0;
        for(unsigned i=0;i<vertices;++i){auto* v=g.bytes.data()+i*36;std::array<float,3> normal{},world_normal{};std::memcpy(normal.data(),v+12,12);
            if(!atmosphere::transformed_normal(normal,transform,world_normal))return rejected("body_prototype_invalid_normal_transform");
            uint32_t original=0;std::memcpy(&original,v+24,4);const auto color=atmosphere::scene_color(original,world_normal,p->lighting);changed+=color!=original;std::memcpy(v+24,&color,4);}
        const auto hr=atmosphereintegration::upload(d,*p,min,vertices,g.bytes);if(FAILED(hr)){if(p->pending.any())return atmosphereintegration::repair(d);return rejected("body_prototype_private_upload_failed");}
        applied=true;
        if(p->first_reason("body_prototype_tata_admitted"))session().write("{\"type\":\"atmosphere_body_prototype\",\"material\":\"Tata/record19/tatabon\",\"changed_vertices\":"+std::to_string(changed)+
            ",\"current_native_owner\":true,\"source_geometry_verified\":true,\"healthy_only\":true,\"normal_transform\":\"inverse_transpose\",\"reflection_states_changed\":false,\"shared_buffer_mutated\":false,\"frame\":"+std::to_string(d.trace.frame_number())+
            ",\"race_generation\":"+std::to_string(cert.race_generation)+",\"owner_lifetime\":"+std::to_string(cert.owner_lifetime)+"}");return S_OK;
    }catch(...){if(!p->pending.any())p->pending.release();return atmosphereintegration::repair(d);}
}
} // namespace gfx2::atmospherebody
