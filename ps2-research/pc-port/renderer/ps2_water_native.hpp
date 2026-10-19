#pragma once
// COURSE-WATER1 native side (PS2Water=1): in draw_indexed_at, a native course draw that is exactly one PS2 water asset
// key is replaced by the PS2 passes of its matched water triangles (ps2_water_pilot.hpp). Compiled only into the staged
// baseline. Anything unproved (no certificate, not a key, world matrix not identity, mirrors missing) stays the original
// draw.
#include "xtrail_native_integration.hpp"
#include "course_objects_native_integration.hpp"
#include "ps2_water_pilot.hpp"
#include <cstdio>

namespace gfx2::waterintegration {
using Result=xtrailintegration::Result;
inline ps2port::PS2WaterPilot* pilot(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->water():nullptr;}

inline void writer(void* o,uint32_t slot,const Args& a,HRESULT hr) noexcept {xtrailintegration::notify(*static_cast<Device8*>(o),slot,a,hr);}
inline HRESULT repair(Device8& d) noexcept {
    auto* p=pilot(d);if(!p)return S_OK;if(p->blocked())return D3DERR_DEVICELOST;
    if(!p->transaction.pending())return S_OK;
    p->transaction.set_writer(&d,writer);
    return p->transaction.restore(*d.native());
}
inline void log(Device8& d,ps2port::PS2WaterPilot& p,const char* reason,const std::string& extra=std::string()) noexcept {
    if(!p.note_reason(reason))return;
    try{session().write("{\"type\":\"ps2_water\",\"reason\":\""+std::string(reason)+"\",\"frame\":"+std::to_string(d.trace.frame_number())+extra+"}");}catch(...){}
}

// The buffer/range identity of a draw (TRIANGLELIST, FVF with D3DFVF_XYZ at offset 0) with the current mirror revisions;
// a zero-size mirror copy proves availability and generation without copying.
struct DrawSource { courseintegration::Ref<IDirect3DVertexBuffer8> vb; courseintegration::Ref<IDirect3DIndexBuffer8> ib;
    uint64_t vertex_offset=0,vertex_bytes=0,index_offset=0,index_bytes=0; unsigned index_size=0; };
inline bool draw_identity(Device8& d,UINT min_index,UINT vertices,UINT start,UINT count,ps2port::WaterDrawIdentity& id,
                          DrawSource& s,const char*& reason) noexcept {
    auto& n=*d.native();DWORD fvf=0;UINT stride=0,base=0;
    if(FAILED(n.GetVertexShader(&fvf))||FAILED(n.GetStreamSource(0,&s.vb.p,&stride))||!s.vb.p||FAILED(n.GetIndices(&s.ib.p,&base))||!s.ib.p){reason="buffers_unbound";return false;}
    if((fvf&D3DFVF_POSITION_MASK)!=D3DFVF_XYZ||stride<12||stride>256){reason="fvf_not_xyz";return false;}
    D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC idd{};
    if(FAILED(s.vb.p->GetDesc(&vd))||FAILED(s.ib.p->GetDesc(&idd))){reason="buffer_desc_failed";return false;}
    // Course geometry lives in static buffers; dynamic ones (particles, sprites) are never course water.
    if((vd.Usage&D3DUSAGE_DYNAMIC)||(idd.Usage&D3DUSAGE_DYNAMIC)){reason="dynamic_buffer";return false;}
    s.index_size=idd.Format==D3DFMT_INDEX16?2u:idd.Format==D3DFMT_INDEX32?4u:0u;
    if(!s.index_size||!vertices){reason="index_format";return false;}
    s.vertex_offset=(uint64_t(base)+min_index)*stride;s.vertex_bytes=uint64_t(vertices)*stride;
    s.index_offset=uint64_t(start)*s.index_size;s.index_bytes=uint64_t(count)*3u*s.index_size;
    if(s.vertex_offset>vd.Size||s.vertex_bytes>vd.Size-s.vertex_offset||s.index_offset>idd.Size||s.index_bytes>idd.Size-s.index_offset||
       s.vertex_bytes>4u*1024u*1024u||s.index_bytes>1024u*1024u){reason="draw_range_outside_buffers";return false;}
    id.vb=reinterpret_cast<uintptr_t>(s.vb.p);id.ib=reinterpret_cast<uintptr_t>(s.ib.p);
    id.vb_generation=d.trace.resources.generation(id.vb);id.ib_generation=d.trace.resources.generation(id.ib);
    id.base=base;id.min_index=min_index;id.vertices=vertices;id.start=start;id.count=count;id.fvf=fvf;id.stride=stride;
    std::vector<BYTE> none;
    if(!id.vb_generation||!id.ib_generation||
       !d.copy_buffer_shadow(s.vb.p,BufferKind::Vertex,id.vb_generation,s.vertex_offset,0,none,id.vb_revision)||
       !d.copy_buffer_shadow(s.ib.p,BufferKind::Index,id.ib_generation,s.index_offset,0,none,id.ib_revision)){reason="mirror_unavailable";return false;}
    return true;
}
// Positions in index order from the mirrors; the revisions must still be the identity's.
inline bool draw_positions(Device8& d,const ps2port::WaterDrawIdentity& id,const DrawSource& s,std::vector<float>& out,const char*& reason) noexcept {
    std::vector<BYTE> vbytes,ibytes;uint64_t vr=0,ir=0;
    if(!d.copy_buffer_shadow(s.vb.p,BufferKind::Vertex,id.vb_generation,s.vertex_offset,static_cast<size_t>(s.vertex_bytes),vbytes,vr)||
       !d.copy_buffer_shadow(s.ib.p,BufferKind::Index,id.ib_generation,s.index_offset,static_cast<size_t>(s.index_bytes),ibytes,ir)||
       vr!=id.vb_revision||ir!=id.ib_revision){reason="mirror_unavailable";return false;}
    try{
        out.resize(size_t(id.count)*9);
        for(size_t k=0;k<size_t(id.count)*3;++k){
            uint32_t index=0;std::memcpy(&index,ibytes.data()+k*s.index_size,s.index_size);
            if(index<id.min_index||index-id.min_index>=id.vertices){reason="index_outside_vertex_range";return false;}
            std::memcpy(out.data()+k*3,vbytes.data()+size_t(index-id.min_index)*id.stride,12);
        }
    }catch(...){reason="position_copy_failed";return false;}
    return true;
}

inline bool identity_world(Device8& d) noexcept {
    D3DMATRIX world{};const auto& tracked=d.trace.effective_shadow.matrices[D3DTS_WORLD];
    if(tracked.known)world=tracked.value;else if(FAILED(d.native()->GetTransform(D3DTS_WORLD,&world)))return false;
    D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1.f;
    return !std::memcmp(&world,&identity,sizeof(identity));
}

// Pass states (ps2water::pass_material). Fog stays native for fogged passes (course linear vertex fog, PS2 FGE 1).
inline HRESULT apply_pass(ps2port::PS2WaterPilot& p,IDirect3DDevice8& n,const ps2water::Part& part,int pass) noexcept {
    using K=ps2port::WaterStateKind;auto& t=p.transaction;
    const auto m=ps2water::pass_material(part.mode,pass);
    auto op=[&](K kind,DWORD stage,DWORD key){return ps2port::water_op(kind,stage,key);};
    auto* texture=p.texture(pass?part.secondary:part.primary);if(!texture)return E_FAIL;
    const DWORD fog=m.fog?t.saved(op(K::Render,0,D3DRS_FOGENABLE)):FALSE;
    const std::array<std::pair<size_t,DWORD>,25> values{{
        {op(K::Render,0,D3DRS_ALPHABLENDENABLE),TRUE},
        {op(K::Render,0,D3DRS_SRCBLEND),D3DBLEND_SRCALPHA},
        {op(K::Render,0,D3DRS_DESTBLEND),m.blend==ps2water::Blend::AddFix56?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA},
        {op(K::Render,0,D3DRS_BLENDOP),D3DBLENDOP_ADD},
        {op(K::Render,0,D3DRS_ZWRITEENABLE),m.z_write?TRUE:FALSE},
        {op(K::Render,0,D3DRS_ZFUNC),D3DCMP_LESSEQUAL},
        {op(K::Render,0,D3DRS_ALPHATESTENABLE),FALSE},
        {op(K::Render,0,D3DRS_CULLMODE),D3DCULL_NONE},
        {op(K::Render,0,D3DRS_LIGHTING),FALSE},
        {op(K::Render,0,D3DRS_FOGENABLE),fog},
        {op(K::Render,0,D3DRS_SPECULARENABLE),FALSE},
        {op(K::Render,0,D3DRS_TEXTUREFACTOR),ps2water::kPuddleFixFactor},
        {op(K::Stage,0,D3DTSS_COLOROP),D3DTOP_MODULATE},
        {op(K::Stage,0,D3DTSS_COLORARG1),D3DTA_TEXTURE},
        {op(K::Stage,0,D3DTSS_COLORARG2),D3DTA_DIFFUSE},
        {op(K::Stage,0,D3DTSS_ALPHAOP),m.texture_alpha?D3DTOP_MODULATE:D3DTOP_SELECTARG1},
        {op(K::Stage,0,D3DTSS_ALPHAARG1),m.texture_alpha?D3DTA_TEXTURE:D3DTA_TFACTOR},
        {op(K::Stage,0,D3DTSS_ALPHAARG2),D3DTA_DIFFUSE},
        {op(K::Stage,0,D3DTSS_TEXCOORDINDEX),0},
        {op(K::Stage,0,D3DTSS_TEXTURETRANSFORMFLAGS),D3DTTFF_DISABLE},
        {op(K::Stage,0,D3DTSS_ADDRESSU),(part.clamp&1)?D3DTADDRESS_CLAMP:D3DTADDRESS_WRAP},
        {op(K::Stage,0,D3DTSS_ADDRESSV),(part.clamp&2)?D3DTADDRESS_CLAMP:D3DTADDRESS_WRAP},
        {op(K::Stage,0,D3DTSS_MAGFILTER),D3DTEXF_LINEAR},
        {op(K::Stage,0,D3DTSS_MINFILTER),D3DTEXF_LINEAR},
        {op(K::Stage,0,D3DTSS_MIPFILTER),D3DTEXF_LINEAR},
    }};
    for(const auto& [i,v]:values){const HRESULT hr=t.set(n,i,v);if(FAILED(hr))return hr;}
    HRESULT hr=t.set(n,op(K::Stage,1,D3DTSS_COLOROP),D3DTOP_DISABLE);
    if(SUCCEEDED(hr))hr=t.set(n,op(K::Stage,1,D3DTSS_ALPHAOP),D3DTOP_DISABLE);
    if(SUCCEEDED(hr))hr=t.set(n,op(K::VertexShader,0,0),D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);
    if(SUCCEEDED(hr))hr=t.set(n,op(K::Texture,0,0),0,texture);
    return hr;
}

inline Result draw(Device8& d,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc) noexcept {
    auto* p=pilot(d);if(!p||!p->active())return {};
    if(type!=D3DPT_TRIANGLELIST||!count||!p->candidate(count)||!d.trace.scene_active||d.trace.shadow.recording||
       d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return {};
    bool single=false,split=false;const auto cert=courseintegration::certificate(d,single,split);
    if(!cert.valid)return {};
    const size_t course=p->course(cert.course_id.data());if(course==SIZE_MAX||!p->course_candidate(course,count))return {};
    // Exact geometry: the cached key of this buffer/range identity, else the order-free SHA-256 of its triangles.
    ps2port::WaterDrawIdentity id{};DrawSource source;const char* reason="";
    if(!draw_identity(d,min_index,vertices,start,count,id,source,reason)){if(std::strcmp(reason,"dynamic_buffer"))log(d,*p,reason);return {};}
    id.course=course;
    bool cached=false;size_t key=p->cached(id,cached);
    if(!cached){
        key=SIZE_MAX;
        if(!draw_positions(d,id,source,p->positions,reason)){log(d,*p,reason);return {};}
        if(ps2water::canonical_triangles(p->positions.data(),count,p->canonical))
            key=p->match(course,count,sha256_bytes(p->canonical.data(),p->canonical.size()));
        p->remember(id,key);
    }
    if(key==SIZE_MAX){
        // A PC base_water draw (stage 1 ADD of watersurface3, 5854d0) of a water course that is not in the asset.
        const auto& op1=d.trace.effective_shadow.tss[1][D3DTSS_COLOROP];
        if(op1.known&&op1.value==D3DTOP_ADD)log(d,*p,"base_water_draw_without_key",",\"triangles\":"+std::to_string(count)+
            ",\"course\":"+quote(p->asset().courses[course].id));
        return {};
    }
    auto& n=*d.native();
    if(!identity_world(d)){log(d,*p,"world_not_identity");return {};}
    DWORD z=0;if(FAILED(n.GetRenderState(D3DRS_ZENABLE,&z))||z!=D3DZB_TRUE){log(d,*p,"native_depth_off");return {};}
    D3DMATRIX view{};const auto& tracked_view=d.trace.effective_shadow.matrices[D3DTS_VIEW];
    if(tracked_view.known)view=tracked_view.value;else if(FAILED(n.GetTransform(D3DTS_VIEW,&view))){log(d,*p,"view_unreadable");return {};}
    if(!courseintegration::finite_matrix(view)){log(d,*p,"view_not_finite");return {};}
    const auto pause=read_pause_menu_state_readonly();
    p->advance(d.trace.frame_number(),pause.present&&pause.tag==0&&pause.value!=0);
    const float t=p->phase();
    const auto basis=ps2water::basis_from_view(view.m);
    auto& tr=p->transaction;tr.set_writer(&d,writer);
    HRESULT hr=tr.capture(n,&d.trace.effective_shadow);
    if(FAILED(hr)){log(d,*p,"transaction_capture_failed");return {};}
    const auto& k=p->asset().keys[key];
    HRESULT drawn=S_OK;uint64_t passes=0;
    for(uint32_t i=0;i<k.parts&&SUCCEEDED(drawn);++i){
        const auto& part=p->asset().parts[k.first_part+i];
        if(!ps2water::build_part(p->asset(),part,t,basis,p->first,p->second)){drawn=E_FAIL;break;}
        for(int pass=0;pass<2&&SUCCEEDED(drawn);++pass){
            drawn=apply_pass(*p,n,part,pass);
            if(FAILED(drawn))break;
            tr.mark_up_stream_changed();
            const auto& v=pass?p->second:p->first;
            // Private draw; never fed into the application's draw tracker or classifier.
            drawn=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,static_cast<UINT>(v.size()/3),v.data(),sizeof(ps2water::PassVertex));
            if(SUCCEEDED(drawn))++passes;
        }
    }
    const HRESULT restored=tr.restore(n);
    if(FAILED(restored)){p->disable("water_state_restore_failed");log(d,*p,"water_state_restore_failed");return {true,restored};}
    if(FAILED(drawn)){
        // Nothing or part of the PS2 water reached the target: the native draw keeps the surface, the feature stops.
        p->disable("water_draw_failed");log(d,*p,"water_draw_failed");
        if(passes)return {true,S_OK};
        return {};
    }
    p->count(passes);p->note_owned(course,cert.race_generation);
    if(p->claim_course_log(course))try{
        char buf[160];std::snprintf(buf,sizeof(buf),",\"triangles\":%u,\"parts\":%u,\"source\":%u,\"phase\":%.4f,\"counter\":%u,\"caller_rva\":%u",
            k.triangles,k.parts,k.source,double(t),p->counter(),static_cast<unsigned>(pc-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))));
        session().write("{\"type\":\"ps2_water_course\",\"course\":"+quote(p->asset().courses[course].id)+",\"race_generation\":"+
            std::to_string(cert.race_generation)+",\"split\":"+(split?"true":"false")+buf+",\"artifact_sha256\":"+quote(ps2port::kPS2WaterArtifactSha)+
            ",\"runtime_visibility\":\"PENDING_USER\"}");
    }catch(...){}
    return {true,S_OK};
}
}  // namespace gfx2::waterintegration
