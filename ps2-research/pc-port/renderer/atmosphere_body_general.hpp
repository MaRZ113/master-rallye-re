#pragma once
#include "atmosphere_body_common.hpp"
#include "atmosphere_body_binding.hpp"
namespace gfx2::atmospherebody {
inline HRESULT general(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,bool& applied) {
    auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||!p->body_materials||!p->lighting.active()||!vertices||vertices>8192||!count||count>8192||type!=D3DPT_TRIANGLELIST||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    Timing timer(*p);auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
    auto reject=[&](const char* why){if(!p->pending.any())p->pending.release();if(p->body_debug&&d.trace.control.active&&p->first_reason(why))atmosphereintegration::log(d,why);return S_OK;};
    DWORD fvf=0,pixel=1;
    if(FAILED(n.GetVertexShader(&fvf))||(fvf!=0x152&&fvf!=0x142&&fvf!=0x112)||FAILED(n.GetPixelShader(&pixel))||pixel||
       !groundintegration::render(d,n,D3DRS_LIGHTING,FALSE)||!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,FALSE)||!groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,FALSE)||
       !groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||!groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)||
       !groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||
       !groundintegration::stage(d,n,0,D3DTSS_RESULTARG,D3DTA_CURRENT)||!groundintegration::stage(d,n,2,D3DTSS_COLOROP,D3DTOP_DISABLE)||
       !groundintegration::render(d,n,D3DRS_VERTEXBLEND,D3DVBF_DISABLE)||!groundintegration::render(d,n,D3DRS_INDEXEDVERTEXBLENDENABLE,FALSE))return S_OK;
    DWORD stage_op=0;if(FAILED(n.GetTextureStageState(1,D3DTSS_COLOROP,&stage_op)))return S_OK;
    const bool flat=stage_op==D3DTOP_DISABLE;
    if(!flat&&((fvf!=0x152&&fvf!=0x112)||(stage_op!=D3DTOP_ADD&&stage_op!=D3DTOP_MODULATEALPHA_ADDCOLOR)||
        !groundintegration::stage(d,n,1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACENORMAL)||!groundintegration::stage(d,n,1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2)))return S_OK;
    courseintegration::Ref<IDirect3DSurface8> target,back;
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return S_OK;
    frontendmodelintegration::Context owner;
    if(!frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner))return S_OK;
    D3DMATRIX world{};if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||!frontendmodelintegration::fleet_owner_world(owner,world))return reject("body_material_owner_world_mismatch");
    const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));atmosphere::NativeMaterialBinding binding;
    if(!atmosphere::native_material_binding(exe,owner.mesh,frontendmodelintegration::word,binding))return reject("body_material_native_binding_missing");
    uint32_t name_id=0;std::string resource;
    if(!frontendmodelintegration::word(owner.owner.packet+0xc,name_id)||!atmosphere::native_name(exe,name_id,frontendmodelintegration::word,resource))return reject("body_material_resource_missing");
    for(auto& c:resource){c=char(std::tolower(static_cast<unsigned char>(c)));if(c=='\\')c='/';}
    const auto slash=resource.find('/',9);if(resource.rfind("vehicles/",0)!=0||slash==std::string::npos)return reject("body_material_not_vehicle_resource");
    const auto part=resource.substr(slash+1);if(part!="car"&&part!="wheel")return reject("body_material_not_race_car_or_wheel_resource");
    const auto family=resource.substr(9,slash-9);p->body_capabilities.load(p->body_path);
    const auto* capability=p->body_capabilities.native_capability(family,binding.names[0],binding.names[1],part);
    if(!capability)return reject("body_material_not_authorized_surface");
    const bool implicit=fvf==0x112;
    if(implicit&&(!p->native_wheel_lighting||part!="wheel"||(capability->role!=atmosphere::WheelRubber&&capability->role!=atmosphere::WheelMetal)||flat||!groundintegration::stage(d,n,3,D3DTSS_COLOROP,D3DTOP_DISABLE)))return reject("body_implicit_diffuse_not_certified_wheel");
    if(!p->body_capabilities.extended&&flat!=(capability->role==atmosphere::OpaqueFlat))return reject("body_material_flat_role_pass_mismatch");
    courseintegration::Ref<IDirect3DBaseTexture8> texture;
    if(FAILED(n.GetTexture(0,&texture.p))||reinterpret_cast<uintptr_t>(texture.p)!=binding.textures[0]||!d.trace.resources.generation(binding.textures[0]))return reject("body_material_live_texture_mismatch");
    if(p->pending.any())return D3DERR_DEVICELOST;
    const bool normals=fvf==0x152;const unsigned stride=implicit?32u:normals?36u:24u;atmosphereintegration::Geometry g;if(!atmosphereintegration::geometry(d,*p,min,vertices,start,count,g)||p->pending.stride!=stride)return reject("body_material_current_mirror_missing");
    ps2port::RaceDescriptors desc;uintptr_t vb=0,ib=0;
    if(!ps2port::race_descriptors(exe,owner.mesh,frontendmodelintegration::word,desc)||!frontendmodelintegration::pointer_word(desc.vd[0],vb)||!frontendmodelintegration::pointer_word(desc.id[0],ib)||
       d.unwrap_vertex_buffer(reinterpret_cast<IDirect3DVertexBuffer8*>(vb))!=p->pending.stream||d.unwrap_index_buffer(reinterpret_cast<IDirect3DIndexBuffer8*>(ib))!=p->pending.indices||
       desc.vd[2]!=min||desc.vd[3]!=vertices||desc.vd[4]!=fvf||desc.vd[5]!=stride||desc.id[2]!=start||desc.id[3]!=count*3)return reject("body_material_current_descriptor_mismatch");
    std::vector<uint8_t> debug_original;if(normals&&p->body_debug&&d.trace.control.active)debug_original=g.bytes;
    uint64_t changed=0;
    D3DMATRIX view{};const bool have_view=p->lighting.rim&&SUCCEEDED(n.GetTransform(D3DTS_VIEW,&view));
    if(implicit){const auto hr=atmosphere::native_wheel_energy(*p,n,[&](uint32_t slot,const Args& a,HRESULT h){atmosphereintegration::notify(d,slot,a,h);});
        if(hr!=S_OK)return FAILED(hr)?hr:reject("body_wheel_energy_unsupported");changed=vertices;}
    else if(!normals){for(size_t at=0;at<g.bytes.size();at+=24){uint32_t before=0;std::memcpy(&before,g.bytes.data()+at+12,4);const auto after=atmosphere::flat_body_color(before,p->lighting);std::memcpy(g.bytes.data()+at+12,&after,4);changed+=before!=after;}}
    else if(!shade(g.bytes,36,24,12,world,p->lighting,false,changed,capability->role,have_view?&view:nullptr))return reject("body_material_invalid_normal_transform");
    const auto hr=implicit?S_OK:atmosphereintegration::upload(d,*p,min,vertices,g.bytes);if(FAILED(hr)){if(p->pending.any())return atmosphereintegration::repair(d);return reject("body_material_private_upload_failed");}
    if(FAILED(environment_exposure(d,*p)))return atmosphereintegration::repair(d);
    applied=true;p->body_vertices+=changed;
    if(!debug_original.empty())debug_sample(d,*p,"native_owner_material",family,debug_original.data(),g.bytes.data(),vertices,world);
    if(p->first_reason(("body_native_"+family+part+binding.names[0]).c_str()))session().write("{\"type\":\"atmosphere_body_material\",\"route\":\"native_owner_material\",\"family\":"+quote(family)+",\"primary\":"+quote(binding.names[0])+",\"secondary\":"+quote(binding.names[1])+",\"resource\":"+quote(part)+",\"metadata_payload_sha256\":"+quote(p->body_capabilities.payload_sha)+",\"surface_role\":"+quote(std::string(atmosphere::body_role_name(capability->role)))+",\"private_damage_tree\":"+(owner.owner.private_tree?"true":"false")+",\"geometry_hash_required\":false,\"changed_vertices\":"+std::to_string(changed)+",\"shared_buffer_mutated\":false,\"reflection_uv_changed\":false,\"environment_exposure_requested\":false,\"frame\":"+std::to_string(d.trace.frame_number())+"}");
    return S_OK;
}
}
