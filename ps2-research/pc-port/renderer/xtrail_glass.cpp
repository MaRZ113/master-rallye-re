#include "xtrail_glass.hpp"
#include "xtrail_glass_identity.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
namespace gfx2::ps2port {
bool decode_xtrail_glass(const std::vector<uint8_t>& b,std::vector<GlassSourceVertex>& vertices,std::vector<DWORD>& primary,std::vector<DWORD>& highlight)noexcept{
    vertices.clear();primary.clear();highlight.clear();
    if(b.size()!=6920||std::memcmp(b.data(),"XGLASS01",8)||sha256_bytes(b.data(),b.size())!=kXtrailGlassAssetSha)return false;
    uint32_t h[4]{};std::memcpy(h,b.data()+8,16);if(h[0]!=1||h[1]!=22||h[2]!=1032||h[3]!=4104)return false;
    try{
        vertices.resize(22);std::memcpy(vertices.data(),b.data()+24,1760);
        const auto* tex=b.data()+1784;
        auto decode=[&](const uint8_t* gx,uint32_t side,std::vector<DWORD>& out,bool weight){
            uint32_t magic;uint16_t wh[2];std::memcpy(&magic,gx,4);std::memcpy(wh,gx+4,4);
            if(magic!=0x13039||wh[0]!=side||wh[1]!=side)return false;
            out.resize(side*side);
            for(size_t i=0;i<out.size();++i){const uint8_t* c=gx+8+i*4;
                const auto r=weight?DWORD(c[0])*96/128:DWORD(c[0]);const auto g=weight?DWORD(c[1])*96/128:DWORD(c[1]);
                const auto bl=weight?DWORD(c[2])*96/128:DWORD(c[2]);
                out[i]=(DWORD(weight?255:c[3])<<24)|(r<<16)|(g<<8)|bl;}
            return true;
        };
        return decode(tex,16,primary,false)&&decode(tex+1032,32,highlight,true);
    }catch(...){vertices.clear();primary.clear();highlight.clear();return false;}
}
std::vector<XtrailDecalVertex> glass_vertices(const DrawSnapshot& g,const std::vector<GlassSourceVertex>& source,std::string_view expected){
    if(!g.supported_build||!g.device_id||g.fvf!=0x152||g.stride!=36||g.vertex_count!=22||g.primitive_count!=18||source.size()!=22)return {};
    auto faces=vehicle_face_hashes(g);if(faces.size()!=18)return {};
    std::sort(faces.begin(),faces.end());std::string joined;for(const auto& f:faces)joined+=f;
    if(sha256_bytes(joined.data(),joined.size())!=expected)return {};
    const auto relative=static_cast<size_t>((uint64_t(g.base_vertex)+g.min_index)*36-g.vertex_byte_offset);
    std::array<XtrailDecalVertex,22> vertices;
    for(unsigned i=0;i<22;++i){const uint8_t* raw=g.vertex_bytes.data()+relative+i*36;
        float xyz[3];std::memcpy(xyz,raw,12);for(float& v:xyz)if(v==0)v=0;
        const auto key=sha256_bytes(xyz,12);const GlassSourceVertex* found=nullptr;
        for(const auto& s:source){std::string h;h.reserve(64);for(uint8_t v:s.position_hash){h+="0123456789abcdef"[v>>4];h+="0123456789abcdef"[v&15];}if(h==key){if(found)return {};found=&s;}}
        if(!found||std::memcmp(raw+12,found->expected_normal,12)||std::memcmp(raw+28,found->expected_uv,8)||std::memcmp(raw+24,&found->expected_color,4))return {};
        auto& v=vertices[i];std::memcpy(v.xyz,raw,12);std::memcpy(v.normal,found->normal,12);std::memcpy(v.uv,found->uv,8);v.diffuse=found->color;
    }
    std::vector<XtrailDecalVertex> out;out.reserve(54);const auto size=g.index_format==D3DFMT_INDEX16?2u:4u;
    for(unsigned i=0;i<54;++i){uint32_t at=0;std::memcpy(&at,g.index_bytes.data()+i*size,size);out.push_back(vertices[at-g.min_index]);}return out;
}
void GlassTransaction::release()noexcept{
    if(texture_)texture_->Release();if(stream_)stream_->Release();if(indices_)indices_->Release();
    texture_=nullptr;stream_=nullptr;indices_=nullptr;pending_=0;captured_=false;
}
HRESULT GlassTransaction::capture(IDirect3DDevice8& n)noexcept{
    if(pending_)return D3DERR_INVALIDCALL;release();
    for(size_t i=0;i<std::size(kGlassOps);++i){const auto& op=kGlassOps[i];const auto hr=op.render?n.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&scalar_[i]):n.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&scalar_[i]);if(FAILED(hr))return hr;}
    auto hr=n.GetTexture(0,&texture_);if(SUCCEEDED(hr))hr=n.GetTransform(D3DTS_TEXTURE0,&tex0_);
    if(SUCCEEDED(hr))hr=n.GetStreamSource(0,&stream_,&stride_);if(SUCCEEDED(hr))hr=n.GetIndices(&indices_,&base_);
    if(FAILED(hr)||!stream_||!indices_){release();return FAILED(hr)?hr:E_POINTER;}captured_=true;return S_OK;
}
XtrailGlass::XtrailGlass(bool supported,const std::wstring& ini)noexcept{
    wchar_t mode[16]{},version[16]{};GetPrivateProfileStringW(L"PS2Port",L"XtrailGlassMode",L"0",mode,16,ini.c_str());
    GetPrivateProfileStringW(L"PS2Port",L"XtrailGlassVersion",L"1",version,16,ini.c_str());
    if(!xtrail_fidelity_opt_in(mode,version,supported))return;
    diagnostics_=GetPrivateProfileIntW(L"PS2Port",L"XtrailGlassDiagnostics",0,ini.c_str())==1;
    try{
        wchar_t filename[32768]{};GetPrivateProfileStringW(L"PS2Port",L"XtrailGlassAsset",L"XtrailHeadlight.ps2glass",filename,32768,ini.c_str());
        auto path=std::filesystem::path(filename);if(path.is_relative())path=std::filesystem::path(ini).parent_path()/path;
        std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file||file.tellg()!=6920)return;
        std::vector<uint8_t> bytes(6920);file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),6920);
        requested_=file&&decode_xtrail_glass(bytes,vertices_,primary_,highlight_);
    }catch(...){requested_=false;}
}
bool XtrailGlass::initialize(IDirect3DDevice8& n)noexcept{
    if(!requested()||blocked_)return false;if(ready_)return true;
    auto upload=[&](uint32_t side,const std::vector<DWORD>& pixels,IDirect3DTexture8*& texture){
        auto hr=n.CreateTexture(side,side,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture);if(FAILED(hr)||!texture)return false;
        D3DLOCKED_RECT locked{};hr=texture->LockRect(0,&locked,nullptr,0);if(FAILED(hr))return false;
        bool valid=locked.pBits&&locked.Pitch>=int(side*4);if(valid)for(unsigned y=0;y<side;++y)std::memcpy(static_cast<uint8_t*>(locked.pBits)+y*locked.Pitch,pixels.data()+y*side,side*4);
        const auto unlocked=texture->UnlockRect(0);return valid&&SUCCEEDED(unlocked);
    };
    if(!upload(16,primary_,primary_texture_)||!upload(32,highlight_,highlight_texture_)){before_reset();disabled_=true;return false;}
    ready_=true;return true;
}
const std::vector<XtrailDecalVertex>* XtrailGlass::prepare(const DrawSnapshot& g)noexcept{
    try{
        if(!g.supported_build||!g.complete_mirror_coverage||!g.device_id||!g.vertex_generation||!g.index_generation||!g.vertex_revision||!g.index_revision)return nullptr;
        const std::array<uint64_t,15> key={g.device_id,g.reset_generation,g.vertex_resource,g.index_resource,g.vertex_generation,g.index_generation,g.vertex_revision,g.index_revision,g.start_index,g.base_vertex,g.min_index,g.vertex_count,g.index_format,g.vertex_byte_offset,g.primitive_count};
        for(auto& c:cache_)if(c.valid&&c.key==key)return c.vertices.empty()?nullptr:&c.vertices;
        auto& c=cache_[next_++%cache_.size()];c={key,glass_vertices(g,vertices_,kXtrailGlassGeometrySha),true};return c.vertices.empty()?nullptr:&c.vertices;
    }catch(...){return nullptr;}
}
void XtrailGlass::before_reset()noexcept{
    for(auto& c:cache_)c={};next_=0;
    if(transaction.pending())blocked_=true;transaction.release();if(primary_texture_)primary_texture_->Release();if(highlight_texture_)highlight_texture_->Release();primary_texture_=nullptr;highlight_texture_=nullptr;ready_=false;
}
} // namespace gfx2::ps2port
