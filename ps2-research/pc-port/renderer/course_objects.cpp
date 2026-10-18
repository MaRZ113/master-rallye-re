#include "course_objects.hpp"
#include "ps2_config.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>

namespace gfx2::ps2port {
namespace {
std::string hex(const uint8_t* p,size_t n){std::string s;for(size_t i=0;i<n;++i){s+="0123456789abcdef"[p[i]>>4];s+="0123456789abcdef"[p[i]&15];}return s;}
}
bool decode_course_object_asset(const uint8_t* p,size_t n,std::string_view digest,CourseObjectAsset& out)noexcept {
    out={};
    if(!p||n!=70384||digest!=kTurkey3ObjectArtifactSha||std::memcmp(p,"PS2OBJ01",8))return false;
    uint32_t fields[4]{};std::memcpy(fields,p+8,16);
    if(fields[0]!=1||fields[1]!=17||fields[2]!=2235||fields[3]!=16384)return false;
    try {
        if(hex(p+24,32)!=kTurkey3PsmSha||hex(p+56,32)!=kTurkey3WaterSha)return false;
        out.meshes.resize(17);std::memcpy(out.meshes.data(),p+88,17*16);
        uint32_t next=0,previous=0;
        for(const auto& mesh:out.meshes){
            if(mesh.node_offset<=previous||mesh.material_offset<=mesh.node_offset||mesh.first_vertex!=next||
                !mesh.vertex_count||mesh.vertex_count%3||mesh.vertex_count>2235-next)return false;
            next+=mesh.vertex_count;previous=mesh.node_offset;
        }
        if(next!=2235)return false;
        out.vertices.resize(2235);std::memcpy(out.vertices.data(),p+360,2235*24);
        for(const auto& v:out.vertices)if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)||
            !std::isfinite(v.u)||!std::isfinite(v.v)||v.color!=0xffffffffu)return false;
        out.texture_bgra.resize(4096);const auto* rgba=p+54000;
        for(size_t i=0;i<4096;++i){const auto* c=rgba+i*4;if(c[3]!=255)return false;
            out.texture_bgra[i]=0xff000000u|(DWORD(c[0])<<16)|(DWORD(c[1])<<8)|c[2];}
        return true;
    }catch(...){out={};return false;}
}
bool turkey3_course(std::string_view id)noexcept {
    return course_id_matches(id,"RaceTest/Turkey3");
}
bool course_id_matches(std::string_view id,std::string_view expected)noexcept {
    if(id.size()!=expected.size())return false;
    for(size_t i=0;i<id.size();++i){auto a=id[i],b=expected[i];
        if(a>='A'&&a<='Z')a+=32;if(b>='A'&&b<='Z')b+=32;if(a!=b)return false;}
    return true;
}
const char* course_object_admission(const CourseAdmission& a,std::string_view source_course)noexcept {
    if(!a.supported_build||!a.asset_ready)return "unsupported_build_or_missing_verified_asset";
    if(!a.render_thread||!a.scene_active)return "outside_verified_render_scene";
    if(a.state_block_recording)return "native_state_block_recording";
    if(!a.race_valid||!a.camera_single||!course_id_matches(a.course,source_course)||!a.race||!a.owner||!a.camera)return "turkey3_owner_or_camera_unverified";
    if(!a.ui_callsite||!a.ui_consumer)return "typed_pre_ui_boundary_unverified";
    if(a.frame!=a.proof_frame||!a.device||a.device!=a.proof_device||a.reset!=a.proof_reset||
       a.race!=a.proof_race||a.owner!=a.proof_owner||a.camera!=a.proof_camera)return "stale_world_frame_or_owner";
    if(!a.view_site||!a.projection_site||!a.world_draw)return "gameplay_camera_or_world_draw_missing";
    if(!a.target_matches||!a.depth_matches||!a.viewport_matches)return "main_target_depth_or_viewport_changed";
    if(!a.pc_depth_convention||!a.native_dependency_states)return "unsupported_native_depth_or_vertex_blend";
    return "eligible";
}
const char* course_split_admission(const CourseSplitAdmission& a,const CourseSplitProof& p,std::string_view source_course)noexcept {
    if(!a.supported_build||!a.asset_ready)return "unsupported_build_or_missing_verified_asset";
    if(!a.render_thread||!a.scene_active)return "outside_verified_render_scene";
    if(a.state_block_recording)return "native_state_block_recording";
    if(!a.race_valid||!a.split_certificate||!course_id_matches(a.course,source_course)||!a.race||!a.owner||!a.camera)return "split_owner_or_camera_unverified";
    if(!a.ui_callsite||!a.ui_consumer)return "typed_pre_ui_boundary_unverified";
    if(!a.device||!p.same_frame(a.frame,a.device,a.reset,a.race,a.owner))return "split_stale_world_frame_or_owner";
    if(p.count!=kCourseSplitPasses||!p.passes[0].camera||!p.passes[1].camera||p.passes[0].camera==p.passes[1].camera)return "split_two_camera_passes_missing";
    if(a.camera!=p.passes[0].camera&&a.camera!=p.passes[1].camera)return "split_ui_camera_not_a_pass";
    for(size_t i=0;i<kCourseSplitPasses;++i){const auto& pass=p.passes[i];
        if(!pass.view_site||!pass.projection_site||!pass.world_draw)return i?"split_pass2_camera_or_world_draw_missing":"split_pass1_camera_or_world_draw_missing";
        if(!a.target_matches[i]||!a.depth_matches[i]||!course_split_viewport(pass.viewport,a.target_width,a.target_height))return "split_target_depth_or_viewport_changed";
        if(!a.pc_depth_convention[i])return "unsupported_native_depth_or_vertex_blend";
    }
    if(!course_viewports_disjoint(p.passes[0].viewport,p.passes[1].viewport))return "split_viewports_overlap";
    if(!a.native_dependency_states)return "unsupported_native_depth_or_vertex_blend";
    return "eligible";
}
CourseObjectsPilot::CourseObjectsPilot(bool supported,const std::wstring& ini)noexcept {
    if(!supported){reason_="unsupported_build_stock";return;}
    wchar_t mode[32]{},version[32]{};
    ::gfx2::ps2port::config::read_string(L"CourseObjectsMode",L"0",mode,32,ini.c_str());
    ::gfx2::ps2port::config::read_string(L"CourseObjectsVersion",L"1",version,32,ini.c_str());
    if(std::wstring_view(mode)!=L"1"||std::wstring_view(version)!=L"1")return;
    requested_=true;diagnostics_=::gfx2::ps2port::config::read_int(L"CourseObjectsDiagnostics",0,ini.c_str())==1;
    try {
        wchar_t path[32768]{};wchar_t course_dir[32768]{};::gfx2::ps2port::config::read_string(L"GrassAssetDirectory",L".",course_dir,32768,ini.c_str());const std::wstring course_default=std::wstring(course_dir)+L"\\Turkey3Puddles.ps2obj";const auto count=::gfx2::ps2port::config::read_string(L"CourseObjectsAsset",course_default.c_str(),path,32768,ini.c_str());
        if(!count||count>=32767){reason_="invalid_asset_path";return;}
        std::filesystem::path input(path);if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
        std::ifstream file(input,std::ios::binary|std::ios::ate);
        if(!file||file.tellg()!=70384){reason_="missing_or_wrong_size_object_asset";return;}
        std::vector<uint8_t> bytes(70384);file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),bytes.size());
        verified_=file&&decode_course_object_asset(bytes.data(),bytes.size(),sha256_bytes(bytes.data(),bytes.size()),asset_);
        reason_=verified_?"verified_source_geometry_waiting_for_device":"object_asset_hash_or_layout_mismatch";
    }catch(...){reason_="object_asset_load_failed_stock";verified_=false;}
}
bool CourseObjectsPilot::initialize(IDirect3DDevice8& device)noexcept {
    if(!identity_requested()||suspended_||blocked_)return false;
    if(texture_)texture_->Release();texture_=nullptr;
    D3DCAPS8 caps{};HRESULT hr=device.GetDeviceCaps(&caps);
    if(FAILED(hr)||caps.MaxTextureWidth<64||caps.MaxTextureHeight<64||caps.MaxPrimitiveCount<745){disable("unsupported_object_device_caps");return false;}
    hr=device.CreateTexture(64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture_);
    if(FAILED(hr)||!texture_){if(texture_)texture_->Release();texture_=nullptr;disable("object_texture_creation_failed");return false;}
    D3DLOCKED_RECT lock{};hr=texture_->LockRect(0,&lock,nullptr,0);
    if(SUCCEEDED(hr)){
        bool valid=lock.pBits&&lock.Pitch>=256;
        if(valid)for(size_t row=0;row<64;++row)std::memcpy(static_cast<uint8_t*>(lock.pBits)+row*lock.Pitch,asset_.texture_bgra.data()+row*64,256);
        const auto unlocked=texture_->UnlockRect(0);if(!valid||FAILED(unlocked))hr=E_FAIL;
    }
    if(FAILED(hr)){texture_->Release();texture_=nullptr;disable("object_texture_upload_failed");return false;}
    reason_="source_geometry_static_material_preview_ready";return true;
}
bool CourseObjectsPilot::consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept {
    if(consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset)return false;
    consumed_frame_=frame;consumed_race_=race;consumed_reset_=reset;return true;
}
bool CourseObjectsPilot::claim_log(bool draw)noexcept {auto& done=draw?logged_draw_:logged_rejection_;if(!diagnostics_||done)return false;done=true;return true;}
void CourseObjectsPilot::before_reset()noexcept {
    proof.clear();if(transaction.has_pending())blocked_=true;transaction.release();
    if(texture_)texture_->Release();texture_=nullptr;consumed_frame_=UINT64_MAX;
}
void CourseObjectsPilot::after_reset(IDirect3DDevice8& device,bool called,bool success)noexcept {
    if(!called)return;if(!success){suspended_=true;return;}
    blocked_=suspended_=false;initialize(device);
}
void CourseObjectsPilot::shutdown()noexcept {proof.clear();transaction.release();if(texture_)texture_->Release();texture_=nullptr;disabled_=true;}
} // namespace gfx2::ps2port
