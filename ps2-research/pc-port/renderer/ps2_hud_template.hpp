#pragma once
// PS2HudTemplate=1: the PS2 HUD-TEMPLATE art on the PC race HUD images.
//
// PC Hud0.xml and PS2 HUD0.XML draw the speed dial, needle and race progress bar from the same image bank
// hud\hud-template with the same authored geometry. The PC re-authored the art (thinner needle, smaller dial
// numerals, light progress bar); the PS2 art is rebuilt offline for each PC texture (tools/
// prepare_hud_template_asset.py, ps2-research/hud-dump1 HUD-PORT4). A PC UI draw whose stage0 texture is one of
// these exact PC images (level-0 SHA-256) is drawn with the PS2 texture instead; geometry, placement, needle
// rotation, colours and blending stay the PC draw's own.
// Image 3 (progress car) uses the PS2 arrow: its PC quad is remapped onto the PS2 box through a temporary WORLD.
// Not substituted: image 1 (GPS radar, PS2HudMap), 7 (GPS pointer). GXI alpha is 8-bit and kept as is.
#include "ps2_hud_damage.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace gfx2::ps2port {

// pc_*: the exact PC texture; width/height: the PS2 texture; remap: x' = sx*x + tx, y' = sy*y + ty applied to the PC
// quad in authored units (identity unless the PS2 image box differs).
struct HudTemplateRemap { float sx,tx,sy,ty; };
struct HudTemplateImage { int image; UINT pc_width,pc_height; const char* pc_sha; UINT width,height; const char* ps2_sha; HudTemplateRemap remap; };
inline constexpr HudTemplateImage kHudTemplateImages[]={
    { 0,128,128,"fefa1f352be2ac5bb7bde14dbcd1b1863f0b4e670c3d2491b52e824428da004c",
        128,128,"8ef002e8c34f2afda8921532de683a278dcae6b345f110f61eedc7447a063e87",{1.f,0.f,1.f,0.f}},
    { 2, 16, 64,"4084f2e3f7fc1318771ed36288dacaeb182dca64fa299a36223c5c3d7c4e0e17",
         16, 64,"ba125b04c163c02c7d877200ef8d7e0ffb46edb77afc31e48c9c17175b7df348",{1.f,0.f,1.f,0.f}},
    { 3, 16,  8,"83f2d1fe5d3c6a821eee6353e56647b053283078c9af6a6ee790ee54ff195312",
         16, 16,"2621aa8fc8ffdb0fa3d59c91ec7be6a536b22b232541d30f93ce3f8e337ad295",{.8125f,-.9375f,2.f,0.f}},
    { 4,  8, 16,"d5cacfb02d18956fde4c6aa6cf31c061cab102473799e0b9f2e3caf680ed36cb",
          8, 16,"f1626f21839c9bcb7528d1e699f21951271e641bccfed41426888eddc51e6f96",{1.f,0.f,1.f,0.f}},
    { 5,  4, 16,"471908a49f3d3be50fb183b29b23d03e6143d1e43f35bd9361a9fc4cfed43d2e",
          4, 16,"7319f5c42a803687a4251dcf1c12e9fedfae833d7647776a32d31ddc480ba8dc",{1.f,0.f,1.f,0.f}},
    { 6,  8, 16,"96ead40e7ab3b5a72b7eff1a0ba4a87f6a64edbabb7ba57a08cfd9ccbf215474",
          8, 16,"68b2688f2995dd35d67e2a8a864be3badecc37a3671f767f1b43771461099b10",{1.f,0.f,1.f,0.f}},
    { 8, 32, 32,"9d6e59042dfd11c64037bb523aecf9681bc07da51ab13b556a8b4bf18b8e6996",
         32, 32,"52f34e97eecbafbdf6cb660335229d49bcce05af3423bc6caffe0f7a433b505c",{1.f,0.f,1.f,0.f}},
    { 9,  8, 32,"361eec5fbc58c189bada3a561cc76fed52b7c181e591b6208f2ea5191f63f96f",
          8, 32,"b85bc102fa0903471256dca5f27476a6622ced30f4a6a46aedbd125953f72bf2",{1.f,0.f,1.f,0.f}},
    {10, 32, 32,"114dd3956e4574849e2f3f93c52568e7cd16a04b3993199e3349ec10205b754f",
         32, 32,"e4012239e10334210134c2c45a6e308183589265630672c34ca5920205101dd3",{1.f,0.f,1.f,0.f}},
};
inline constexpr size_t kHudTemplateCount=sizeof(kHudTemplateImages)/sizeof(kHudTemplateImages[0]);

inline std::string hud_hex(const uint8_t* p,size_t n){static const char* d="0123456789abcdef";std::string s;s.reserve(n*2);for(size_t i=0;i<n;++i){s+=d[p[i]>>4];s+=d[p[i]&15];}return s;}

// 'MRHT' v2 pack -> per-table-entry BGRA rows; every entry must match the table exactly (image, sizes, both SHAs, remap).
inline bool decode_hud_template_pack(const std::vector<uint8_t>& b,std::array<std::vector<DWORD>,kHudTemplateCount>& out) noexcept {
    try{
        auto u32=[&](size_t o){uint32_t v=0;std::memcpy(&v,b.data()+o,4);return v;};
        auto f32=[&](size_t o){float v=0;std::memcpy(&v,b.data()+o,4);return v;};
        if(b.size()<12||std::memcmp(b.data(),"MRHT",4)||u32(4)!=2||u32(8)!=kHudTemplateCount)return false;
        size_t o=12;
        for(size_t i=0;i<kHudTemplateCount;++i){
            const auto& e=kHudTemplateImages[i];
            if(b.size()<o+68)return false;
            if(u32(o)!=uint32_t(e.image)||u32(o+4)!=e.pc_width||u32(o+8)!=e.pc_height)return false;
            if(hud_hex(b.data()+o+12,32)!=e.pc_sha)return false;
            if(u32(o+44)!=e.width||u32(o+48)!=e.height)return false;
            if(f32(o+52)!=e.remap.sx||f32(o+56)!=e.remap.tx||f32(o+60)!=e.remap.sy||f32(o+64)!=e.remap.ty)return false;
            o+=68;const size_t bytes=size_t(e.width)*e.height*4;
            if(b.size()<o+bytes||sha256_bytes(b.data()+o,bytes)!=e.ps2_sha)return false;
            out[i].resize(size_t(e.width)*e.height);std::memcpy(out[i].data(),b.data()+o,bytes);o+=bytes;
        }
        return o==b.size();
    }catch(...){return false;}
}

// Level-0 SHA of any small A8R8G8B8/X8R8G8B8 texture (rows in D3D order), as pc_hud_level0_sha for 32x32.
inline std::string hud_level0_sha(const BYTE* bits,INT pitch,UINT width,UINT height,D3DFORMAT format) noexcept {
    try{
        if(!bits||pitch<INT(width*4)||(format!=D3DFMT_A8R8G8B8&&format!=D3DFMT_X8R8G8B8))return {};
        std::vector<BYTE> rows(size_t(width)*height*4);
        for(UINT y=0;y<height;++y)std::memcpy(rows.data()+size_t(y)*width*4,bits+size_t(y)*pitch,width*4);
        if(format==D3DFMT_X8R8G8B8)for(size_t i=3;i<rows.size();i+=4)rows[i]=0xff;
        return sha256_bytes(rows.data(),rows.size());
    }catch(...){return {};}
}
inline int hud_template_index(const std::string& sha,UINT width,UINT height) noexcept {
    for(size_t i=0;i<kHudTemplateCount;++i)
        if(kHudTemplateImages[i].pc_width==width&&kHudTemplateImages[i].pc_height==height&&sha==kHudTemplateImages[i].pc_sha)return int(i);
    return -1;
}

// PC hud-template draw order puts the split marker / ticks / finish flag (images 4, 5, 6) before the progress bar,
// which the PS2 bar's dark translucent fill then covers (F10: finish 347, ticks 349-354, bar 359-442). The PS2 draws
// the bar first (GS dump 195341: bar 1817-1829, ticks/finish 1831-1837). These three are drawn at Present instead,
// over the bar, from the PC draw's own placement (PC box, PC UV; the substitute texture is in PC UV space).
struct HudTemplateDeferredImage { int image; float x0,y0,x1,y1,u1; };
inline constexpr HudTemplateDeferredImage kHudTemplateDeferred[]={{4,-3,-7,5,9,1.f},{5,0,-7,2,9,.5f},{6,-3,-7,5,9,1.f}};
inline const HudTemplateDeferredImage* hud_template_deferred(int image) noexcept {
    for(const auto& d:kHudTemplateDeferred)if(d.image==image)return &d;return nullptr;
}

class PS2HudTemplate {
    bool requested_=false,disabled_=false,context_ok_=false;
    struct Deferred { size_t table=0; HudPlacement placement; };
    std::array<Deferred,24> deferred_{};size_t deferred_count_=0;
    std::array<std::vector<DWORD>,kHudTemplateCount> pixels_;
    std::array<IDirect3DTexture8*,kHudTemplateCount> textures_{};
    std::array<HudPcIdentity,48> identities_{};size_t next_identity_=0;
    const char* startup_reason_=nullptr;
    uint64_t substituted_=0;
public:
    PS2HudTemplate(bool supported,const std::wstring& ini) noexcept {
        if(!supported)return;
        try{
            if(config::read_int(L"PS2HudTemplate",0,ini.c_str())!=1)return;
            wchar_t folder[32768]{};
            config::read_string(L"PS2HudAssetDir",L"PS2Hud",folder,32768,ini.c_str());
            auto dir=std::filesystem::path(folder);if(dir.is_relative())dir=std::filesystem::path(ini).parent_path()/dir;
            std::ifstream file(dir/L"PS2HudTemplate.bin",std::ios::binary);
            std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
            requested_=decode_hud_template_pack(bytes,pixels_);
            if(!requested_){startup_reason_="hud_template_asset_missing_or_mismatch";pixels_={};}
        }catch(...){requested_=false;pixels_={};}
    }
    ~PS2HudTemplate(){release();}
    PS2HudTemplate(const PS2HudTemplate&)=delete;
    PS2HudTemplate& operator=(const PS2HudTemplate&)=delete;
    bool requested() const noexcept {return requested_&&!disabled_;}
    void disable() noexcept {disabled_=true;}
    const char* take_startup_reason() noexcept {const char* r=startup_reason_;startup_reason_=nullptr;return r;}
    // Set at Present from the certified race HUD context; draws of the next frame use it.
    void set_context(bool ok) noexcept {context_ok_=ok;}
    bool context_ok() const noexcept {return context_ok_;}
    bool ready() const noexcept {for(auto* t:textures_)if(!t)return false;return true;}
    uint64_t substituted() const noexcept {return substituted_;}
    PS2HudLayer layer;
    // A PC split marker / tick / finish draw: drawn at Present over the bar (see kHudTemplateDeferred).
    bool defer(const HudTemplateImage& image,const HudPlacement& p) noexcept {
        if(!p.valid||deferred_count_>=deferred_.size()||!hud_template_deferred(image.image))return false;
        deferred_[deferred_count_++]={size_t(&image-kHudTemplateImages),p};++substituted_;return true;
    }
    // Present: this frame's deferred quads (white, as the PS2 GS dump draws them); clears the list.
    std::vector<HudTexQuad> take_deferred() {
        std::vector<HudTexQuad> quads;
        for(size_t i=0;i<deferred_count_;++i){
            const auto& d=deferred_[i];const auto* box=hud_template_deferred(kHudTemplateImages[d.table].image);if(!box)continue;
            // PC vertex = (x-0.5, 0.5-y) in the draw's WORLD space (hud_slot_rect convention).
            float xs[2],ys[2];
            if(!hud_project(d.placement,box->x0-.5f,.5f-box->y0,xs[0],ys[0])||!hud_project(d.placement,box->x1-.5f,.5f-box->y1,xs[1],ys[1]))continue;
            HudTexQuad q;q.rect={std::fmin(xs[0],xs[1]),std::fmin(ys[0],ys[1]),std::fmax(xs[0],xs[1]),std::fmax(ys[0],ys[1])};
            q.page=d.table;q.u0=0.f;q.u1=box->u1;q.v0=1.f;q.v1=0.f;q.color=0xffffffffu;   // top = PC v 1
            if(q.rect.r>q.rect.l&&q.rect.b>q.rect.t)quads.push_back(q);
        }
        deferred_count_=0;return quads;
    }
    std::vector<IDirect3DTexture8*> pages() const {return std::vector<IDirect3DTexture8*>(textures_.begin(),textures_.end());}
    void note_substituted() noexcept {++substituted_;}
    void release() noexcept {for(auto& t:textures_){if(t)t->Release();t=nullptr;}}
    bool initialize(IDirect3DDevice8& n) noexcept {
        if(ready())return true;
        if(!requested())return false;
        release();
        for(size_t i=0;i<kHudTemplateCount;++i){
            const auto& e=kHudTemplateImages[i];
            if(FAILED(n.CreateTexture(e.width,e.height,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&textures_[i]))||!textures_[i]){textures_[i]=nullptr;release();disable();return false;}
            D3DLOCKED_RECT lock{};if(FAILED(textures_[i]->LockRect(0,&lock,nullptr,0))){release();disable();return false;}
            const bool good=lock.pBits&&lock.Pitch>=INT(e.width*4);
            if(good)for(UINT y=0;y<e.height;++y)std::memcpy(static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,pixels_[i].data()+size_t(y)*e.width,e.width*4);
            if(FAILED(textures_[i]->UnlockRect(0))||!good){release();disable();return false;}
        }
        return true;
    }
    // The PS2 texture for an exact PC hud-template image, or null. Identity cached per resource generation.
    IDirect3DTexture8* substitute(IDirect3DBaseTexture8* base,uint64_t generation,const HudTemplateImage** image=nullptr) noexcept {
        const auto id=reinterpret_cast<uintptr_t>(base);
        if(image)*image=nullptr;
        if(!base||!generation||!ready())return nullptr;
        for(const auto& c:identities_)if(c.texture==id&&c.generation==generation){
            if(c.index<0)return nullptr;if(image)*image=&kHudTemplateImages[size_t(c.index)];return textures_[size_t(c.index)];}
        HudPcIdentity result{id,generation,-1,"not_pc_hud_template"};
        if(base->GetType()==D3DRTYPE_TEXTURE){
            auto* t=static_cast<IDirect3DTexture8*>(base);D3DSURFACE_DESC desc{};
            if(SUCCEEDED(t->GetLevelDesc(0,&desc))&&desc.Width<=128&&desc.Height<=128&&
               (desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8)&&desc.Pool!=D3DPOOL_DEFAULT){
                bool sized=false;for(const auto& e:kHudTemplateImages)sized=sized||(e.pc_width==desc.Width&&e.pc_height==desc.Height);
                D3DLOCKED_RECT lock{};
                if(sized&&SUCCEEDED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY))){
                    const auto sha=hud_level0_sha(static_cast<const BYTE*>(lock.pBits),lock.Pitch,desc.Width,desc.Height,desc.Format);
                    t->UnlockRect(0);
                    result.index=hud_template_index(sha,desc.Width,desc.Height);
                    if(result.index>=0)result.reason="exact_pc_hud_template";
                }
            }
        }
        identities_[next_identity_]=result;next_identity_=(next_identity_+1)%identities_.size();
        if(result.index<0)return nullptr;
        if(image)*image=&kHudTemplateImages[size_t(result.index)];return textures_[size_t(result.index)];
    }
};

}  // namespace gfx2::ps2port
