#include "grass_pilot.hpp"
#include "ps2_config.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <cwchar>
#include <filesystem>
#include <fstream>
#include <limits>

namespace gfx2::ps2port {
namespace {
// Force each recovered arithmetic step through float32 storage; this remains
// FLOAT32_RECONSTRUCTION rather than a claim of R5900 FPU bit parity.
float add(float a,float b)noexcept{volatile float v=a+b;return v;}
float sub(float a,float b)noexcept{volatile float v=a-b;return v;}
float mul(float a,float b)noexcept{volatile float v=a*b;return v;}
float div(float a,float b)noexcept{volatile float v=a/b;return v;}
float pitch()noexcept{const uint32_t bits=0x3faa3d71u;float p;std::memcpy(&p,&bits,4);return p;}
std::string hex(const uint8_t* p,size_t n){std::string s;for(size_t i=0;i<n;++i){s+="0123456789abcdef"[p[i]>>4];s+="0123456789abcdef"[p[i]&15];}return s;}
bool bin_index(float value,int32_t& result)noexcept{
    if(!std::isfinite(value))return false;
    const double bin=std::floor(double(value)/double(kGrassBinWidth));
    if(bin<std::numeric_limits<int32_t>::min()||bin>std::numeric_limits<int32_t>::max())return false;
    result=static_cast<int32_t>(bin);return true;
}
bool ordered(const GrassBin& a,const GrassBin& b)noexcept{return a.z<b.z||(a.z==b.z&&a.x<b.x);}
const std::array<float,1024>& fade_table()noexcept{
    static const std::array<float,1024> table=[](){
        std::array<float,1024> values{};
        for(size_t i=0;i<values.size();++i){
            const float root=static_cast<float>(std::sqrt(mul(static_cast<float>(i),1.f/1024.f)));
            values[i]=std::max(0.f,std::min(128.f,mul(sub(1.f,std::min(1.f,root)),128.f)));
        }
        return values;
    }();
    return table;
}
}
bool decode_grass_asset_layout(const uint8_t* p,size_t n,GrassAsset& out,GroundDetailKind kind,const GrassSourceContract* source)noexcept{
    out={};
    if(kind!=GroundDetailKind::Grass&&kind!=GroundDetailKind::Shrubs)return false;
    if(!p||n<128||n>kGrassMaximumAssetBytes||std::memcmp(p,"PS2GRS01",8))return false;
    uint32_t f[6]{};std::memcpy(f,p+8,sizeof(f));
    if(f[0]!=1||!f[1]||f[1]>300000||!f[2]||f[2]>65536||f[3]!=32||f[4]!=32||f[5]!=4096)return false;
    const uint64_t expected=128ull+uint64_t(f[2])*16+uint64_t(f[1])*12+4096;
    if(expected!=n)return false;
    try{
        const auto& contract=source?*source:kGrassSources[0];
        if(hex(p+32,32)!=contract.psm||hex(p+64,32)!=(kind==GroundDetailKind::Shrubs?kTurkey3BushGxiSha:kTurkey3GrassGxiSha)||
           hex(p+96,32)!=contract.pc)return false;
        GrassAsset decoded;decoded.bins.resize(f[2]);decoded.points.resize(f[1]);
        std::memcpy(decoded.bins.data(),p+128,size_t(f[2])*16);
        const size_t point_start=128+size_t(f[2])*16;
        std::memcpy(decoded.points.data(),p+point_start,size_t(f[1])*12);
        uint32_t next=0;
        for(size_t i=0;i<decoded.bins.size();++i){
            const auto& b=decoded.bins[i];
            if(!b.count||b.first!=next||b.count>f[1]-next||(i&&!ordered(decoded.bins[i-1],b)))return false;
            for(size_t j=b.first;j<size_t(b.first)+b.count;++j){
                const auto& v=decoded.points[j];int32_t x=0,z=0;
                if(!std::isfinite(v.y)||std::abs(v.x)>1000000.f||std::abs(v.y)>1000000.f||std::abs(v.z)>1000000.f||
                   !bin_index(v.x,x)||!bin_index(v.z,z)||x!=b.x||z!=b.z)return false;
            }
            next+=b.count;
        }
        if(next!=f[1])return false;
        decoded.texture_bgra.resize(1024);const auto* rgba=p+point_start+size_t(f[1])*12;
        for(size_t i=0;i<1024;++i){const auto* c=rgba+i*4;
            decoded.texture_bgra[i]=(DWORD(c[3])<<24)|(DWORD(c[0])<<16)|(DWORD(c[1])<<8)|c[2];}
        out=std::move(decoded);return true;
    }catch(...){return false;}
}
bool decode_grass_asset(const uint8_t* p,size_t n,std::string_view digest,GrassAsset& out,GroundDetailKind kind)noexcept{
    out={};
    const char* expected=kind==GroundDetailKind::Shrubs?kTurkey3ShrubsArtifactSha:kTurkey3GrassArtifactSha;
    return std::string_view(expected).size()==64&&digest==expected&&decode_grass_asset_layout(p,n,out,kind);
}
bool decode_course_grass_asset(const uint8_t* p,size_t n,std::string_view digest,GrassAsset& out,GroundDetailKind kind,const GrassSourceContract& source)noexcept{
    out={};
    const char* expected=kind==GroundDetailKind::Shrubs?source.shrubs_artifact:source.grass_artifact;
    return digest==expected&&decode_grass_asset_layout(p,n,out,kind,&source);
}
bool grass_ee_floor(float x,int32_t& result)noexcept{
    if(!std::isfinite(x)||std::abs(double(x))>=2147483648.)return false;
    uint32_t bits=0;std::memcpy(&bits,&x,4);
    const int exponent=int((bits&0x7fffffffu)>>23)-127;
    const int32_t sign=bits>>31?-1:0;
    const uint32_t mantissa=bits&0x7fffffu;
    const uint32_t magnitude=((mantissa|0x800000u)<<8)>>((31-exponent)&31);
    int32_t value=static_cast<int32_t>(exponent>=0?magnitude:0)^sign;
    const uint32_t fraction_mask=(uint32_t(1)<<((31-std::max(exponent,0))&31))-1;
    if(((mantissa<<8)&fraction_mask)==0)value-=sign;
    result=value;return true;
}
bool grass_camera_center(const D3DMATRIX& view,std::array<float,3>& camera,
                         std::array<float,2>& snapped)noexcept{
    camera={};snapped={};
    for(const auto& row:view.m)for(float v:row)if(!std::isfinite(v))return false;
    constexpr double tolerance=.0002;
    if(std::abs(view._14)>tolerance||std::abs(view._24)>tolerance||std::abs(view._34)>tolerance||
       std::abs(double(view._44)-1)>tolerance)return false;
    for(size_t i=0;i<3;++i)for(size_t j=0;j<3;++j){double dot=0;
        for(size_t k=0;k<3;++k)dot+=double(view.m[i][k])*view.m[j][k];
        if(std::abs(dot-(i==j?1.:0.))>tolerance)return false;
    }
    // Native PC gameplay views include an orthogonal axis reflection (det=-1)
    // in the measured F10 frames. R^-1=R^T for both signs; no handedness
    // conversion or guessed sign flip is needed to recover the camera.
    const double determinant=double(view._11)*(double(view._22)*view._33-double(view._23)*view._32)
       -double(view._12)*(double(view._21)*view._33-double(view._23)*view._31)
       +double(view._13)*(double(view._21)*view._32-double(view._22)*view._31);
    if(std::abs(std::abs(determinant)-1)>tolerance)return false;
    for(size_t i=0;i<3;++i)camera[i]=-add(add(mul(view._41,view.m[i][0]),mul(view._42,view.m[i][1])),mul(view._43,view.m[i][2]));
    const float step=add(pitch(),pitch());
    for(size_t i=0;i<2;++i){int32_t integer=0;
        if(!grass_ee_floor(div(camera[i?2:0],step),integer))return false;
        snapped[i]=mul(static_cast<float>(integer),step);
    }
    return true;
}
bool grass_distance_alpha(const GrassPoint& point,const std::array<float,2>& center,
                          uint32_t& index,float& alpha)noexcept{
    index=0;alpha=0;
    if(!std::isfinite(point.x)||!std::isfinite(point.y)||!std::isfinite(point.z)||
       !std::isfinite(center[0])||!std::isfinite(center[1]))return false;
    const float reciprocal=div(1.f,sub(35.f,add(pitch(),pitch())));
    const float dx=mul(sub(point.x,center[0]),reciprocal),dz=mul(sub(point.z,center[1]),reciprocal);
    int32_t q=0;if(!grass_ee_floor(mul(add(mul(dx,dx),mul(dz,dz)),1024.f),q)||q<0||q>=1023)return false;
    index=static_cast<uint32_t>(q);
    alpha=fade_table()[index];
    return true;
}
bool grass_preview_vertices(const GrassAsset& asset,const D3DMATRIX& view,float half,
                            std::vector<ObjectVertex>& out,const char*& reason)noexcept{
    out.clear();reason="invalid_grass_camera_or_size";
    std::array<float,3> camera{};std::array<float,2> center{};
    if(!std::isfinite(half)||half<.05f||half>2.f||!grass_camera_center(view,camera,center))return false;
    const float xmin=sub(center[0],30.f),xmax=add(center[0],30.f),zmin=sub(center[1],30.f),zmax=add(center[1],30.f);
    int32_t bx0=0,bx1=0,bz0=0,bz1=0;
    if(!bin_index(xmin,bx0)||!bin_index(xmax,bx1)||!bin_index(zmin,bz0)||!bin_index(zmax,bz1))return false;
    try{
        out.reserve(std::min(asset.points.size(),kGrassMaximumVisiblePoints)*6);
        for(int64_t z=bz0;z<=bz1;++z){
            GrassBin key{bx0,static_cast<int32_t>(z),0,0};
            auto bin=std::lower_bound(asset.bins.begin(),asset.bins.end(),key,ordered);
            for(;bin!=asset.bins.end()&&bin->z==z&&bin->x<=bx1;++bin){
                if(bin->first>asset.points.size()||bin->count>asset.points.size()-bin->first){out.clear();reason="invalid_grass_point_range";return false;}
                for(size_t j=bin->first;j<size_t(bin->first)+bin->count;++j){
                    const auto& p=asset.points[j];
                    if(p.x<xmin||p.x>=xmax||p.z<zmin||p.z>=zmax)continue;
                    uint32_t q=0;float alpha=0;if(!grass_distance_alpha(p,center,q,alpha))continue;
                    const float x=add(add(add(mul(p.x,view._11),mul(p.y,view._21)),mul(p.z,view._31)),view._41);
                    const float y=add(add(add(mul(p.x,view._12),mul(p.y,view._22)),mul(p.z,view._32)),view._42);
                    const float depth=add(add(add(mul(p.x,view._13),mul(p.y,view._23)),mul(p.z,view._33)),view._43);
                    if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(depth)){out.clear();reason="nonfinite_grass_view_position";return false;}
                    if(depth<=0)continue; // Native D3D positive view-Z preview convention, independently admitted.
                    if(out.size()/6>=kGrassMaximumVisiblePoints){out.clear();reason="grass_visible_point_limit_no_thinning";return false;}
                    const DWORD a=static_cast<DWORD>(std::floor(double(mul(div(alpha,128.f),255.f))+.5));
                    const DWORD color=(std::min<DWORD>(255,a)<<24)|0x00ffffffu;
                    const float left=sub(x,half),right=add(x,half),bottom=sub(y,half),top=add(y,half);
                    // Screen-aligned view-space rectangle; no time, rotation,
                    // height bias or invented wind. Native projection is reused.
                    out.push_back({left,bottom,depth,color,0,1});out.push_back({left,top,depth,color,0,0});out.push_back({right,top,depth,color,1,0});
                    out.push_back({left,bottom,depth,color,0,1});out.push_back({right,top,depth,color,1,0});out.push_back({right,bottom,depth,color,1,1});
                }
            }
        }
        reason="source_point_preview_pc_billboard_mapping";return true;
    }catch(...){out.clear();reason="grass_preview_allocation_failed";return false;}
}
GrassPilot::GrassPilot(bool supported,const std::wstring& ini,GroundDetailKind kind)noexcept:kind_(kind){
    if(kind!=GroundDetailKind::Grass&&kind!=GroundDetailKind::Shrubs){reason_="unsupported_ground_detail_category";return;}
    if(!supported){reason_="unsupported_build_stock";return;}
    wchar_t mode[32]{},version[32]{},size[64]{};
    const bool shrubs=kind_==GroundDetailKind::Shrubs;
    ::gfx2::ps2port::config::read_string(shrubs?L"ShrubsMode":L"GrassMode",L"0",mode,32,ini.c_str());
    ::gfx2::ps2port::config::read_string(shrubs?L"ShrubsConfigVersion":L"GrassConfigVersion",L"1",version,32,ini.c_str());
    if((std::wstring_view(mode)!=L"1"&&std::wstring_view(mode)!=L"2")||std::wstring_view(version)!=L"1")return;
    // v2 Grass/Shrubs=1 means every verified course (the historical mode 2); the single-file Turkey3
    // pilot (historical mode 1) stays reachable only through the legacy GrassMode/ShrubsMode keys.
    multi_course_=std::wstring_view(mode)==L"2"||::gfx2::ps2port::config::present(shrubs?L"Shrubs":L"Grass",ini.c_str());
    const DWORD size_length=::gfx2::ps2port::config::read_string(shrubs?L"ShrubsSpriteHalfSize":L"GrassSpriteHalfSize",shrubs?L"0.4":L"0.33",size,64,ini.c_str());
    if(!size_length||size_length>=63){reason_="invalid_grass_preview_size_stock";return;}
    wchar_t* end=nullptr;sprite_half_size_=std::wcstof(size,&end);
    if(!end||end==size||*end||!std::isfinite(sprite_half_size_)||sprite_half_size_<.05f||sprite_half_size_>2.f){reason_="invalid_grass_preview_size_stock";return;}
    requested_=true;diagnostics_=::gfx2::ps2port::config::read_int(shrubs?L"ShrubsDiagnostics":L"GrassDiagnostics",0,ini.c_str())==1;
    try{
        wchar_t path[32768]{};const auto count=::gfx2::ps2port::config::read_string(shrubs?L"ShrubsAsset":L"GrassAsset",shrubs?L"Turkey3Shrubs.ps2grass":L"Turkey3Grass.ps2grass",path,32768,ini.c_str());
        if(!count||count>=32767){reason_="invalid_grass_asset_path";return;}
        std::filesystem::path input(path);if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
        std::ifstream file(input,std::ios::binary|std::ios::ate);if(!file){reason_="missing_grass_source_asset";return;}
        const auto length=file.tellg();if(length<128||length>kGrassMaximumAssetBytes){reason_="invalid_grass_source_asset_size";return;}
        std::vector<uint8_t> bytes(static_cast<size_t>(length));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),bytes.size());
        verified_=file&&decode_grass_asset(bytes.data(),bytes.size(),sha256_bytes(bytes.data(),bytes.size()),asset_,kind_);
        course_ready_[0]=verified_;
        if(verified_&&multi_course_){
            wchar_t directory[32768]{};
            const auto dir_length=::gfx2::ps2port::config::read_string(L"GrassAssetDirectory",L".",directory,32768,ini.c_str());
            if(!dir_length||dir_length>=32767)return;
            std::filesystem::path base(directory);if(base.is_relative())base=std::filesystem::path(ini).parent_path()/base;
            for(size_t i=1;i<kGrassSources.size();++i){
                const std::wstring name=std::wstring(kGrassSources[i].stem)+(shrubs?L"Shrubs.ps2grass":L"Grass.ps2grass");
                std::ifstream extra(base/name,std::ios::binary|std::ios::ate);if(!extra)continue;
                const auto size=extra.tellg();if(size<128||size>kGrassMaximumAssetBytes)continue;
                std::vector<uint8_t> data(static_cast<size_t>(size));extra.seekg(0);extra.read(reinterpret_cast<char*>(data.data()),data.size());
                course_ready_[i]=extra&&decode_course_grass_asset(data.data(),data.size(),sha256_bytes(data.data(),data.size()),extra_assets_[i-1],kind_,kGrassSources[i]);
            }
        }
        reason_=verified_?"verified_grass_points_waiting_for_device":"grass_source_asset_hash_or_layout_mismatch";
    }catch(...){verified_=false;reason_="grass_asset_load_failed_stock";}
}
bool GrassPilot::initialize(IDirect3DDevice8& device)noexcept{
    if(!identity_requested()||suspended_||blocked_)return false;
    if(texture_)return true;
    D3DCAPS8 caps{};HRESULT hr=device.GetDeviceCaps(&caps);
    if(FAILED(hr)||caps.MaxTextureWidth<32||caps.MaxTextureHeight<32||caps.MaxPrimitiveCount<kGrassMaximumVisiblePoints*2){disable("unsupported_grass_device_caps");return false;}
    hr=device.CreateTexture(32,32,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture_);
    if(FAILED(hr)||!texture_){if(texture_)texture_->Release();texture_=nullptr;disable("grass_texture_creation_failed");return false;}
    D3DLOCKED_RECT lock{};hr=texture_->LockRect(0,&lock,nullptr,0);
    if(SUCCEEDED(hr)){
        const bool valid=lock.pBits&&lock.Pitch>=128;
        if(valid)for(size_t row=0;row<32;++row)std::memcpy(static_cast<uint8_t*>(lock.pBits)+row*lock.Pitch,asset().texture_bgra.data()+row*32,128);
        const auto unlocked=texture_->UnlockRect(0);if(!valid||FAILED(unlocked))hr=E_FAIL;
    }
    if(FAILED(hr)){texture_->Release();texture_=nullptr;disable("grass_texture_upload_failed");return false;}
    reason_="source_point_preview_pc_billboard_mapping_ready";return true;
}
bool GrassPilot::build_vertices(const D3DMATRIX& view,std::vector<ObjectVertex>& vertices)noexcept{
    if(!active()){vertices.clear();return false;}
    return grass_preview_vertices(asset(),view,sprite_half_size_,vertices,reason_);
}
bool GrassPilot::select_course(std::string_view course_id,IDirect3DDevice8& device)noexcept{
    for(size_t i=0;i<(multi_course_?kGrassSources.size():1);++i){
        if(!course_id_matches(course_id,kGrassSources[i].course)||!course_ready_[i])continue;
        if(i==selected_course_)return active();
        if(transaction.has_pending()||blocked_||suspended_){proof.clear();return false;}
        proof.clear();if(texture_)texture_->Release();texture_=nullptr;
        selected_course_=i;consumed_frame_=UINT64_MAX;logged_build_=logged_draw_=logged_rejection_=false;
        return initialize(device);
    }
    proof.clear();return false;
}
bool GrassPilot::consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept{
    if(consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset)return false;
    consumed_frame_=frame;consumed_race_=race;consumed_reset_=reset;return true;
}
bool GrassPilot::claim_log(bool draw)noexcept{auto& done=draw?logged_draw_:logged_rejection_;if(!diagnostics_||done)return false;done=true;return true;}
void GrassPilot::before_reset()noexcept{
    proof.clear();if(transaction.has_pending())blocked_=true;transaction.release();
    if(texture_)texture_->Release();texture_=nullptr;consumed_frame_=UINT64_MAX;
}
void GrassPilot::after_reset(IDirect3DDevice8& device,bool called,bool success)noexcept{
    if(!called)return;if(!success){suspended_=true;return;}
    blocked_=suspended_=false;initialize(device);
}
void GrassPilot::shutdown()noexcept{proof.clear();transaction.release();if(texture_)texture_->Release();texture_=nullptr;disabled_=true;}
} // namespace gfx2::ps2port
