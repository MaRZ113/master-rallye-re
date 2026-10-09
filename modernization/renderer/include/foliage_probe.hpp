#pragma once
#include "state_tracker.hpp"
#include <string>
#include <vector>
namespace gfx2 {
// F10-only evidence producer. Never authorizes or applies a material override.
inline constexpr unsigned FOLIAGE_PROBE_LIMIT=128, FOLIAGE_FACE_LIMIT=256;
inline constexpr uint64_t FOLIAGE_BYTE_LIMIT=1024*1024;
struct FoliageBudget {
 uint64_t frame=0,bytes=0;unsigned draws=0;bool disabled=false;
 bool take(uint64_t at,uint64_t count) noexcept;
};
struct FoliageEvidence {
 bool attempted=false;std::string reason="not_requested",geometry_sha;
 std::vector<std::string> face_hashes;
 uint64_t vertex_generation=0,index_generation=0,texture_generation=0;
 uintptr_t vertex_buffer=0,index_buffer=0,texture=0;
 DWORD fvf=0,vertex_usage=0,index_usage=0;UINT stride=0,base=0;
 D3DPOOL vertex_pool=D3DPOOL_DEFAULT,index_pool=D3DPOOL_DEFAULT;
 D3DFORMAT index_format=D3DFMT_UNKNOWN;
 std::array<Known<DWORD>,12> native_rs;
 std::array<std::array<Known<DWORD>,8>,2> native_tss;
 Known<D3DMATRIX> native_world;
 Known<D3DMATERIAL8> native_material;
 Known<DWORD> diffuse_alpha_min,diffuse_alpha_max;
 Known<uint32_t> vertex_lock,index_lock;
 HRESULT vertex_unlock=S_OK,index_unlock=S_OK;
};
inline constexpr D3DRENDERSTATETYPE FOLIAGE_RS[]={D3DRS_ALPHATESTENABLE,D3DRS_ALPHAREF,D3DRS_ALPHAFUNC,D3DRS_ALPHABLENDENABLE,D3DRS_SRCBLEND,D3DRS_DESTBLEND,D3DRS_ZENABLE,D3DRS_ZWRITEENABLE,D3DRS_ZFUNC,D3DRS_CULLMODE,D3DRS_COLORVERTEX,D3DRS_DIFFUSEMATERIALSOURCE};
inline constexpr D3DTEXTURESTAGESTATETYPE FOLIAGE_TSS[]={D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_ALPHAARG2,D3DTSS_TEXCOORDINDEX,D3DTSS_TEXTURETRANSFORMFLAGS};
std::string foliage_face_hash(const float* xyz9);
bool foliage_layout(DWORD fvf,UINT stride,UINT& diffuse_offset) noexcept;
FoliageEvidence probe_foliage(IDirect3DDevice8& native,const ResourceRegistry& resources,
 const Args& draw,uint64_t frame,FoliageBudget& budget) noexcept;
std::string foliage_json(const FoliageEvidence& e);
}
