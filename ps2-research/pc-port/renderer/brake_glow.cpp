#include "brake_glow.hpp"
#include "brake_glow_identity.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
#include <fstream>
#include <filesystem>
namespace gfx2::ps2port {
BrakeGlow::BrakeGlow(bool supported,const std::wstring& ini)noexcept{
 wchar_t mode[16]{},version[16]{};GetPrivateProfileStringW(L"PS2Port",L"BrakeGlowMode",L"0",mode,16,ini.c_str());GetPrivateProfileStringW(L"PS2Port",L"BrakeGlowVersion",L"1",version,16,ini.c_str());if(!xtrail_fidelity_opt_in(mode,version,supported))return;
 diagnostics_=GetPrivateProfileIntW(L"PS2Port",L"BrakeGlowDiagnostics",0,ini.c_str())==1;
 try{wchar_t filename[32768]{};GetPrivateProfileStringW(L"PS2Port",L"BrakeGlowAsset",L"PS2BrakeGlow.gxi",filename,32768,ini.c_str());auto path=std::filesystem::path(filename);if(path.is_relative())path=std::filesystem::path(ini).parent_path()/path;std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file||file.tellg()!=1032)return;std::vector<uint8_t> bytes(1032);file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),1032);if(!file||sha256_bytes(bytes.data(),bytes.size())!="b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09")return;pixels_.resize(256);for(unsigned i=0;i<256;++i){const auto* c=bytes.data()+8+4*i;pixels_[i]=(DWORD(c[3])<<24)|(DWORD(c[0])<<16)|(DWORD(c[1])<<8)|c[2];}requested_=true;}catch(...){requested_=false;pixels_.clear();}
}
bool BrakeGlow::initialize(IDirect3DDevice8& n)noexcept{
 if(!requested()||blocked_)return false;if(texture_)return true;
 auto hr=n.CreateTexture(16,16,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture_);if(FAILED(hr)||!texture_){before_reset();disabled_=true;return false;}D3DLOCKED_RECT lock{};hr=texture_->LockRect(0,&lock,nullptr,0);if(FAILED(hr)){before_reset();disabled_=true;return false;}bool valid=lock.pBits&&lock.Pitch>=64;if(valid)for(unsigned y=0;y<16;++y)std::memcpy(static_cast<uint8_t*>(lock.pBits)+y*lock.Pitch,pixels_.data()+y*16,64);const auto unlocked=texture_->UnlockRect(0);if(!valid||FAILED(unlocked)){before_reset();disabled_=true;return false;}return true;
}
bool terrano_glow_identity(const DrawSnapshot& g,std::string_view geometry,std::string_view expected_attributes)noexcept{try{
 if(!g.supported_build||!g.device_id||g.fvf!=0x112||g.stride!=32||g.vertex_count!=20||g.primitive_count!=20||g.vertex_byte_offset!=(uint64_t(g.base_vertex)+g.min_index)*32||g.vertex_bytes.size()!=640)return false;
 std::vector<std::string> attributes;DrawSnapshot normalized=g;normalized.fvf=0x152;normalized.stride=36;normalized.base_vertex=0;normalized.vertex_byte_offset=uint64_t(g.min_index)*36;normalized.vertex_bytes.resize(720);
 for(unsigned i=0;i<20;++i){const auto* v=g.vertex_bytes.data()+i*32;attributes.emplace_back(reinterpret_cast<const char*>(v),32);auto* out=normalized.vertex_bytes.data()+i*36;std::memcpy(out,v,24);uint32_t white=0xffffffff;std::memcpy(out+24,&white,4);std::memcpy(out+28,v+24,8);}
 auto fs=vehicle_face_hashes(normalized);if(fs.size()!=20)return false;std::sort(fs.begin(),fs.end());std::string joined;for(auto& h:fs)joined+=h;if(sha256_bytes(joined.data(),joined.size())!=geometry)return false;
 std::sort(attributes.begin(),attributes.end());joined.clear();for(auto& v:attributes)joined+=v;return sha256_bytes(joined.data(),joined.size())==expected_attributes;
 }catch(...){return false;}}
}
