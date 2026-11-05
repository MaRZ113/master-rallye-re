#pragma once
#include "ps2_diag.hpp"
namespace gfx2::atmosphereintegration {
inline std::string material_sha(Device8&,atmosphere::Pilot&,IDirect3DBaseTexture8*);
inline bool capture_png(Device8& d,const std::filesystem::path& path){
    auto& n=*d.native();courseintegration::Ref<IDirect3DSurface8> back,image;D3DSURFACE_DESC desc{};
    if(FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!back.p||FAILED(back.p->GetDesc(&desc))||!desc.Width||!desc.Height||uint64_t(desc.Width)*desc.Height>4194304)return false;
    if(auto* p=pilot(d);p&&p->capture.stage&&(desc.Width!=p->capture.reference_viewport.Width||desc.Height!=p->capture.reference_viewport.Height))return false;
    ps2diag::PixelFormat format;
    switch(desc.Format){case D3DFMT_X8R8G8B8:format=ps2diag::PixelFormat::X8R8G8B8;break;case D3DFMT_A8R8G8B8:format=ps2diag::PixelFormat::A8R8G8B8;break;
    case D3DFMT_R5G6B5:format=ps2diag::PixelFormat::R5G6B5;break;case D3DFMT_A1R5G5B5:format=ps2diag::PixelFormat::A1R5G5B5;break;default:return false;}
    if(FAILED(n.CreateImageSurface(desc.Width,desc.Height,desc.Format,&image.p))||!image.p)return false;
    const RECT rect{0,0,LONG(desc.Width),LONG(desc.Height)};const POINT origin{0,0};
    if(FAILED(n.CopyRects(back.p,&rect,1,image.p,&origin)))return false;
    D3DLOCKED_RECT locked{};if(FAILED(image.p->LockRect(&locked,nullptr,D3DLOCK_READONLY)))return false;
    std::vector<uint8_t> rgb;
    try{if(locked.pBits&&locked.Pitch>=INT(desc.Width*((desc.Format==D3DFMT_X8R8G8B8||desc.Format==D3DFMT_A8R8G8B8)?4:2)))rgb=ps2diag::to_rgb(static_cast<const uint8_t*>(locked.pBits),UINT(locked.Pitch),desc.Width,desc.Height,format);}catch(...){image.p->UnlockRect();throw;}
    const auto unlocked=image.p->UnlockRect();if(FAILED(unlocked)||rgb.empty())return false;
    const auto png=ps2diag::encode_png(desc.Width,desc.Height,rgb);std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(png.data()),png.size());return bool(f);
}
inline void capture_observe(Device8& d,atmosphere::Pilot& p){
    if(!p.capture.enabled)return;D3DMATRIX view{},projection{};D3DVIEWPORT8 viewport{};
    if(SUCCEEDED(d.native()->GetTransform(D3DTS_VIEW,&view))&&SUCCEEDED(d.native()->GetTransform(D3DTS_PROJECTION,&projection))&&SUCCEEDED(d.native()->GetViewport(&viewport))){
        const bool changed=p.capture.seen&&p.capture.seen_frame==d.trace.frame_number()&&std::memcmp(&viewport,&p.capture.viewport,sizeof(viewport));
        p.capture.observe(d.trace.frame_number(),view,projection);p.capture.viewport=viewport;
        if(changed||!viewport.Width||!viewport.Height||viewport.X||viewport.Y||viewport.MinZ!=0||viewport.MaxZ!=1)p.capture.ambiguous=true;}

}
inline void capture_boundary(Device8& d,bool ui)noexcept{
    auto* p=pilot(d);if(!ui||!p||!p->enabled()||!p->capture.enabled)return;auto& c=p->capture;const auto frame=d.trace.frame_number();
    if(c.last_boundary==frame)return;c.last_boundary=frame;
    try{
        DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
        const bool down=pid==GetCurrentProcessId()&&(GetAsyncKeyState(VK_CONTROL)&0x8000)&&(GetAsyncKeyState(VK_MENU)&0x8000)&&(GetAsyncKeyState('B')&0x8000);
        const bool trigger=down&&!c.key_down;c.key_down=down;if(!trigger&&!c.stage)return;
        auto abort=[&](const char* reason){session().write("{\"type\":\"atmosphere_aborted_pair\",\"reason\":"+quote(std::string(reason))+",\"frame\":"+std::to_string(frame)+"}");
            if(c.stage&&!c.directory.empty()){std::ofstream f(c.directory/L"pair.json");f<<"{\"status\":\"ABORTED\",\"reason\":"<<quote(std::string(reason))<<"}\n";}c.cancel(p->world);};
        bool single=false;const auto cert=courseintegration::certificate(d,single);const auto pause=read_pause_menu_state_readonly();
        if(pid!=GetCurrentProcessId()||!d.game_fov.free_camera_active()||!pause.present||pause.tag!=0||!pause.value||!d.trace.enabled||!single||!cert.valid||!c.seen||c.seen_frame!=frame||c.ambiguous){abort("paused_focused_freecam_single_camera_trace_and_world_required");return;}
        if(!c.stage){
            c.original_world=p->world;c.reference_view=c.view;c.reference_projection=c.projection;c.reference_lighting=p->lighting;c.reference_viewport=c.viewport;c.reference_sky_scale=p->sky_u_scale;c.metadata_sha=p->metadata.sha;c.metadata_reload=p->package_reloads;
            c.race=cert.race_generation;c.owner=cert.owner_lifetime;c.course=cert.course_id.data();c.start=frame;c.ledger.clear();c.overflow=false;
            c.directory=std::filesystem::path(session().directory)/(L"atmosphere27-"+std::to_wstring(GetCurrentProcessId())+L"-d"+std::to_wstring(d.trace.device_id())+L"-f"+std::to_wstring(frame));
            if(!std::filesystem::create_directory(c.directory)){abort("fresh_capture_directory_unavailable");return;}
            c.stage=1;p->world=true;d.trace.control.pending=true;return;
        }
        if(frame!=c.start+c.stage||!c.same_camera(frame)||c.race!=cert.race_generation||c.owner!=cert.owner_lifetime||c.course!=cert.course_id.data()||
           !atmosphere::CourseCapture::same_lighting(c.reference_lighting,p->lighting)||c.reference_sky_scale!=p->sky_u_scale||c.metadata_sha!=p->metadata.sha||c.metadata_reload!=p->package_reloads||p->world!=(c.stage==1)||c.overflow){abort("camera_lifecycle_lighting_changed_or_capture_overflow");return;}
        if(!capture_png(d,c.directory/(c.stage==1?L"lit.png":L"native.png"))){abort("native_readback_or_png_write_failed");return;}
        {std::ofstream f(c.directory/L"admissions.jsonl",std::ios::app);for(const auto& line:c.ledger)f<<line<<'\n';if(!f){abort("ledger_write_failed");return;}}
        c.ledger.clear();
        if(c.stage==1){c.stage=2;p->world=false;d.trace.control.pending=true;return;}
        std::ofstream f(c.directory/L"pair.json");f<<"{\"status\":\"CAPTURED_MATCHED_CAMERA_RUNTIME_TRACE_JOIN_REQUIRED\",\"course\":"<<quote(c.course)
            <<",\"proxy_sha256\":"<<quote(session().proxy_sha)<<",\"metadata_payload_sha256\":"<<quote(p->metadata.sha)
            <<",\"lit_frame\":"<<c.start+1<<",\"native_frame\":"<<c.start+2<<",\"pid\":"<<GetCurrentProcessId()<<",\"device\":"<<d.trace.device_id()
            <<",\"camera_equal_by_bits\":true,\"boundary\":\"world_before_sun_and_hud\",\"dynamic_layers_may_differ\":true,\"pixel_diff_is_secondary\":true,\"freecam\":"<<d.game_fov.camera_json()<<"}\n";
        f.close();if(!f){abort("pair_manifest_write_failed");return;}
        session().write("{\"type\":\"atmosphere_ab_pair_written\",\"start_frame\":"+std::to_string(c.start)+",\"camera_equal_by_bits\":true}");c.cancel(p->world);
    }catch(...){c.cancel(p->world);}
}
// Admission ledger; importer joins the real F10 HRESULT before declaring Lit.
struct CaptureDraw {
    Device8& d;atmosphere::Pilot& p;bool active=false;UINT min,vertices,start,triangles;DWORD fvf=0;uint64_t vg=0,ig=0,tg=0;
    CaptureDraw(Device8& device,atmosphere::Pilot& pilot,UINT mi,UINT ve,UINT st,UINT tr):d(device),p(pilot),min(mi),vertices(ve),start(st),triangles(tr){
        auto& c=p.capture;if(!c.stage||d.trace.frame_number()!=c.start+c.stage)return;active=true;p.draw_reason.clear();p.draw_material.clear();p.draw_texture.clear();p.draw_category=0;p.draw_lit=p.draw_resolved=false;
        auto& n=*d.native();courseintegration::Ref<IDirect3DBaseTexture8> texture;courseintegration::Ref<IDirect3DVertexBuffer8> vb;courseintegration::Ref<IDirect3DIndexBuffer8> ib;UINT stride=0,base=0;
        n.GetVertexShader(&fvf);if(fvf==0x102)p.draw_reason="sky_excluded";
        if(SUCCEEDED(n.GetTexture(0,&texture.p))&&texture.p){tg=d.trace.resources.generation(reinterpret_cast<uintptr_t>(texture.p));p.draw_texture=material_sha(d,p,texture.p);}
        if(SUCCEEDED(n.GetStreamSource(0,&vb.p,&stride))&&vb.p)vg=d.trace.resources.generation(reinterpret_cast<uintptr_t>(vb.p));
        if(SUCCEEDED(n.GetIndices(&ib.p,&base))&&ib.p)ig=d.trace.resources.generation(reinterpret_cast<uintptr_t>(ib.p));
    }
    ~CaptureDraw(){if(!active||!p.capture.stage)return;try{
        const auto& r=p.draw_reason;const char* verdict=p.capture.stage==2?"Native control":p.draw_resolved?(p.draw_lit?"Lit candidate":"Native control"):
            r.find("excluded")!=std::string::npos||r.find("vehicle")!=std::string::npos?"Excluded":
            r.find("unknown")!=std::string::npos||r.find("ambiguous")!=std::string::npos?"Unclassified":
            r.find("shader")!=std::string::npos||r.find("stage")!=std::string::npos||r.find("contract")!=std::string::npos?"Shader mismatch":"Unsupported";
        p.capture.append("{\"type\":\"course_admission\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"course\":"+quote(p.capture.course)+",\"material\":"+quote(p.draw_material)+
            ",\"texture_sha256\":"+quote(p.draw_texture)+",\"admission\":"+quote(std::string(verdict))+",\"reason\":"+quote(r)+",\"category\":"+std::to_string(p.draw_category)+
            ",\"fvf\":"+std::to_string(fvf)+",\"vertex_generation\":"+std::to_string(vg)+",\"index_generation\":"+std::to_string(ig)+",\"texture_generation\":"+std::to_string(tg)+
            ",\"min_index\":"+std::to_string(min)+",\"vertices\":"+std::to_string(vertices)+",\"start_index\":"+std::to_string(start)+",\"triangles\":"+std::to_string(triangles)+"}");
    }catch(...){p.capture.overflow=true;}}
};
} // namespace gfx2::atmosphereintegration
