#include "frontend_model.hpp"
#include <filesystem>
#include <fstream>
#include <cstring>
#include <cmath>
namespace gfx2::ps2port {
bool decode_frontend_asset(const std::vector<uint8_t>& bytes,FrontendAsset& out,bool race)noexcept{try{
 out={};if(bytes.size()!=(race?495343u:741114u)||sha256_bytes(bytes.data(),bytes.size())!=(race?"a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac":"ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b"))return false;
 size_t at=0;auto word=[&](){if(at+4>bytes.size())throw 1;uint32_t v;std::memcpy(&v,bytes.data()+at,4);at+=4;return v;};
 if(std::memcmp(bytes.data(),"PS2MDL02",8))return false;at=8;if(word()!=2)return false;const auto metadata=word(),meshes=word(),vertices=word(),indices=word(),textures=word();
 if(meshes!=(race?20u:24u)||vertices!=(race?3292u:6606u)||indices!=(race?5940u:13908u)||textures!=(race?24u:28u))return false;at=64;if(metadata>bytes.size()-at)return false;at+=metadata;
 out.meshes.resize(meshes);for(auto& m:out.meshes){m.node=word();m.mode=word();for(auto& t:m.texture){t=word();if(t!=UINT32_MAX&&t>=textures)return false;}m.first=word();m.count=word();if(m.first>indices||m.count>indices-m.first||m.count%3||!m.count||(m.mode!=0&&m.mode!=1&&m.mode!=3&&m.mode!=20))return false;if(m.texture[0]==UINT32_MAX)return false;}
 if(uint64_t(at)+uint64_t(vertices)*36+uint64_t(indices)*4>bytes.size())return false;out.vertices.resize(vertices);std::memcpy(out.vertices.data(),bytes.data()+at,vertices*36);at+=vertices*36;
 for(const auto& v:out.vertices){for(float x:v.xyz)if(!std::isfinite(x))return false;for(float x:v.normal)if(!std::isfinite(x))return false;for(float x:v.uv)if(!std::isfinite(x))return false;}
 out.indices.resize(indices);for(auto& i:out.indices){i=word();if(i>=vertices)return false;}
 out.textures.resize(textures);for(auto& t:out.textures){t.width=word();t.height=word();const auto size=word();if(!t.width||!t.height||t.width>1024||t.height>1024||uint64_t(t.width)*t.height*4!=size||size>bytes.size()-at)return false;t.pixels.resize(size/4);std::memcpy(t.pixels.data(),bytes.data()+at,size);at+=size;}
 return at==bytes.size();}catch(...){out={};return false;}}
FrontendModel::FrontendModel(bool supported,const std::wstring& ini,bool race)noexcept{try{
 wchar_t mode[16]{},version[16]{};GetPrivateProfileStringW(L"PS2Port",race?L"RacePS2ModelMode":L"FrontendModelMode",L"0",mode,16,ini.c_str());GetPrivateProfileStringW(L"PS2Port",race?L"RacePS2ModelVersion":L"FrontendModelVersion",L"1",version,16,ini.c_str());if(!supported||std::wcscmp(mode,L"1")||std::wcscmp(version,L"1"))return;
 parts_=race&&GetPrivateProfileIntW(L"PS2Port",L"RacePS2ModelParts",0,ini.c_str())==1;diagnostics_=GetPrivateProfileIntW(L"PS2Port",race?L"RacePS2ModelDiagnostics":L"FrontendModelDiagnostics",0,ini.c_str())==1;wchar_t filename[32768]{};GetPrivateProfileStringW(L"PS2Port",race?L"RacePS2ModelAsset":L"FrontendModelAsset",race?L"XTRAIL-CAR.ps2model":L"XTRAIL-COMPLETE.ps2model",filename,32768,ini.c_str());auto p=std::filesystem::path(filename);if(p.is_relative())p=std::filesystem::path(ini).parent_path()/p;std::ifstream file(p,std::ios::binary|std::ios::ate);if(!file||file.tellg()!=(race?495343:741114))return;std::vector<uint8_t> b(race?495343:741114);file.seekg(0);file.read(reinterpret_cast<char*>(b.data()),b.size());if(!file||!decode_frontend_asset(b,asset_,race))return;
 expanded_.resize(asset_.meshes.size());for(size_t i=0;i<expanded_.size();++i){const auto& m=asset_.meshes[i];auto& v=expanded_[i];v.reserve(m.count);for(unsigned k=0;k<m.count;++k)v.push_back(frontend_primary_sample_vertex(asset_.vertices[asset_.indices[m.first+k]]));}requested_=true;
 }catch(...){requested_=false;}}
bool FrontendModel::initialize(IDirect3DDevice8& n)noexcept{if(!requested())return false;if(textures_.size()==asset_.textures.size())return true;try{
 reset();textures_.resize(asset_.textures.size(),nullptr);for(size_t i=0;i<textures_.size();++i){const auto& t=asset_.textures[i];if(FAILED(n.CreateTexture(t.width,t.height,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&textures_[i]))||!textures_[i]){reset();disable();return false;}D3DLOCKED_RECT l{};if(FAILED(textures_[i]->LockRect(0,&l,nullptr,0))){reset();disable();return false;}bool good=l.pBits&&l.Pitch>=int(t.width*4);if(good)for(UINT y=0;y<t.height;++y)std::memcpy(static_cast<uint8_t*>(l.pBits)+y*l.Pitch,t.pixels.data()+y*t.width,t.width*4);auto hr=textures_[i]->UnlockRect(0);if(!good||FAILED(hr)){reset();disable();return false;}}
 return true;}catch(...){reset();disable();return false;}}
void FrontendModel::reset()noexcept{if(transaction.pending())return;transaction.release();environment_known=false;for(auto* t:textures_)if(t)t->Release();textures_.clear();invalidate();logs_=0;}
}
