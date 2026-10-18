#pragma once
// Opt-in PS2HudDamage (default 0): the PS2 damage row (gaHudAiCarDamage) and the damage notification
// (gaHudAiCarDamage1) drawn by the PS2 port before Present, in place of the PC damage row.
//
// Evidence: ps2-research/hud-dump1/findings.md (GS dumps + R5900 1414e8/1412f8/142ab0/142b90, HUD0.XML).
// * Colour of a channel from its damage d (PS2 1412f8, h=1-clamp(d)): white <0.2, green <0.4, yellow <0.6,
//   orange (1,.75,.3) <0.8, red. Applied only when d rises by more than 0.001 over the last applied value.
// * Notification on every colour change: icon x1.5, birth 25 frames (fade in, in place), life 30 frames,
//   death 25 frames (slides 50*1.5 authored units down, fades out); the newest two are drawn. PS2 is 50 Hz.
// * Each slot: icon image (tinted) then the white frame image 5 (HUD-DAMAGE.PSB, pages HUD-DAMAGE_000/001
//   whose rows the PS2 holds reversed in VRAM).
// PC side: the PC row (4a4540, own 0.25-band table with black) is replaced only for UI draws whose stage0
// texture is one of the six exact PC hud-damage dxt images; their final WORLD/VIEW/PROJ/viewport give the
// screen place, so PreserveMargins and any resolution follow the PC layout.
#include "sdk.hpp"
#include "provenance.hpp"
#include "ps2_config.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace gfx2::ps2port {

// ---------------------------------------------------------------- PS2 data
inline constexpr char kHudDamagePageSha[2][65]={
    "1b11baddf6e0d414cad52f485ac79a9be1841ea012d964267381d6228c2820c6",  // HUD-DAMAGE_000.GXI
    "cb58cda5f89fdeb98958b6b6e5375489ebc81a32048dd586a13cf930e965ca45"}; // HUD-DAMAGE_001.GXI
inline constexpr size_t kHudDamageGxiSize=8+64*64*4;
inline constexpr UINT kHudDamagePage=64;
// HUD-DAMAGE.PSB images 0..5 (0 steering, 1 engine, 2 suspension, 3 gear, 4 tyres, 5 frame): page, u0,v0,u1,v1.
struct HudImage { unsigned page; float u0,v0,u1,v1; };
inline constexpr std::array<HudImage,6> kHudDamageImages={{
    {1,.5f,.5f,1.f,.96875f},{1,0.f,.5f,.5f,.96875f},{0,.5f,0.f,1.f,.46875f},
    {0,0.f,0.f,.5f,.46875f},{0,.5f,.5f,1.f,.96875f},{0,0.f,.5f,.5f,.96875f}}};
inline constexpr unsigned kHudDamageFrameImage=5;
inline constexpr float kPS2HudFrameRate=50.f;
inline constexpr float kNotifyBirth=25.f/kPS2HudFrameRate,kNotifyLife=30.f/kPS2HudFrameRate,kNotifyDeath=25.f/kPS2HudFrameRate;
inline constexpr float kNotifyScale=1.5f,kNotifyEndY=-50.f;
// PS2 HUD0.XML: notification egg (565,340), damage row y 380 -> anchor relative to the tyres slot (580,380).
inline constexpr float kNotifyOffsetX=565.f-580.f,kNotifyOffsetY=340.f-380.f;

// PC DataGx/Hud/hud-damage_000..005_000.dxt level 0 as stored BGRA rows (= D3D level 0).
inline constexpr char kPcHudDamageSha[6][65]={
    "ddd54425832502abc5fa3816a844f8b1ff5728edda66e40e3643d86e51026bc4",
    "a64687326d7829e28ce3d24f7835dd7c4202ef956e3d5192d4cda62b8da79381",
    "2bbecfa5e2e5f9d8393261cc3fe08bf051635936c1b4ea12d8f3b8d402069862",
    "60329a0d925eeda4989aaed9ef6bb9c971d3342a226b0be0f19b5b3133dc7122",
    "a13dbd9ee2e62d3ea677188ba0b59496f66b20272034f989ad9b399d8da905f0",
    "502462b8776c34c948dd778a8d3042f29df0dd2cfd39ea2ec18c408bcc21fbb4"};
inline constexpr UINT kPcHudDamageSize=32;

// ---------------------------------------------------------------- PS2 colour logic
// Band 0 white, 1 green, 2 yellow, 3 orange, 4 red (PS2 1412f8 / 142068).
inline unsigned ps2_damage_band(float d) noexcept {
    float c=d;if(!(c<=1.f))c=1.f;if(c<0.f)c=0.f;
    const float h=1.f-c;
    if(h>.8f)return 0;
    if(h>.6f)return 1;
    if(h>.4f)return 2;
    if(h>.2f)return 3;
    return 4;
}
inline constexpr std::array<std::array<float,3>,5> kPS2DamageColours={{{1,1,1},{0,1,0},{1,1,0},{1,.75f,.3f},{1,0,0}}};

struct HudNotice { unsigned image=0,band=0; int phase=-1; float t=0.f; };  // phase -1 queued, 0 birth, 1 life, 2 death

class HudDamageState {
    std::array<float,5> applied_{};
    std::array<unsigned,5> band_{};
    std::vector<HudNotice> notices_;
public:
    void reset() noexcept {applied_={};band_={};notices_.clear();}
    unsigned band(unsigned i) const noexcept {return i<5?band_[i]:0;}
    const std::vector<HudNotice>& notices() const noexcept {return notices_;}
    // values: steering, engine, suspension, gear, tyres (HUD-DAMAGE image order).
    void update(const std::array<float,5>& values) {
        for(unsigned i=0;i<5;++i){
            const float d=values[i];
            if(!std::isfinite(d)||!(d-applied_[i]>.001f))continue;
            applied_[i]=d;const unsigned b=ps2_damage_band(d);
            if(b!=band_[i]){band_[i]=b;if(notices_.size()<16)notices_.push_back({i,b,-1,0.f});}
        }
    }
    // Front notice runs birth -> life -> death; the next one is born when the front starts dying.
    void advance(float dt) {
        if(!(dt>0.f))return;
        if(dt>.25f)dt=.25f;
        if(notices_.empty())return;
        if(notices_[0].phase<0)notices_[0].phase=0;
        for(size_t i=0;i<notices_.size()&&i<2;++i){
            auto& n=notices_[i];if(n.phase<0)continue;
            n.t+=dt;
            if(n.phase==0&&n.t>=kNotifyBirth){n.t-=kNotifyBirth;n.phase=1;}
            if(n.phase==1&&i==0&&n.t>=kNotifyLife){n.t-=kNotifyLife;n.phase=2;if(notices_.size()>1&&notices_[1].phase<0){notices_[1].phase=0;notices_[1].t=0.f;}}
            if(n.phase==1&&i!=0&&n.t>kNotifyLife)n.t=kNotifyLife;
        }
        if(notices_[0].phase==2&&notices_[0].t>=kNotifyDeath){
            notices_.erase(notices_.begin());
            if(!notices_.empty()&&notices_[0].phase<0){notices_[0].phase=0;notices_[0].t=0.f;}
        }
    }
};
// Alpha (0..1) and authored y offset of a visible notice.
inline bool notice_pose(const HudNotice& n,float& alpha,float& dy) noexcept {
    switch(n.phase){
    case 0:alpha=n.t/kNotifyBirth;dy=0.f;break;
    case 1:alpha=1.f;dy=0.f;break;
    case 2:{const float t=n.t/kNotifyDeath;alpha=1.f-t;dy=kNotifyEndY*kNotifyScale*t;break;}
    default:return false;
    }
    if(alpha<0.f)alpha=0.f;if(alpha>1.f)alpha=1.f;return true;
}

// ---------------------------------------------------------------- assets
// GXI 0x13039 RGBA rows -> D3D A8R8G8B8, rows reversed (the PS2 VRAM order the PSB UVs address).
inline bool decode_hud_damage_page(const std::vector<uint8_t>& gxi,unsigned page,std::vector<DWORD>& out) noexcept {
    try {
        out.clear();
        if(page>1||gxi.size()!=kHudDamageGxiSize||sha256_bytes(gxi.data(),gxi.size())!=kHudDamagePageSha[page])return false;
        uint32_t magic=0;uint16_t w=0,h=0;std::memcpy(&magic,gxi.data(),4);std::memcpy(&w,gxi.data()+4,2);std::memcpy(&h,gxi.data()+6,2);
        if(magic!=0x13039||w!=kHudDamagePage||h!=kHudDamagePage)return false;
        out.resize(size_t(w)*h);
        for(UINT y=0;y<h;++y)for(UINT x=0;x<w;++x){
            const auto* c=gxi.data()+8+4*(size_t(h-1-y)*w+x);
            out[size_t(y)*w+x]=(DWORD(c[3])<<24)|(DWORD(c[0])<<16)|(DWORD(c[1])<<8)|c[2];
        }
        return true;
    } catch(...) { out.clear(); return false; }
}
inline std::string pc_hud_level0_sha(const BYTE* bits,INT pitch,D3DFORMAT format) noexcept {
    try {
        if(!bits||pitch<INT(kPcHudDamageSize*4)||(format!=D3DFMT_A8R8G8B8&&format!=D3DFMT_X8R8G8B8))return {};
        std::vector<BYTE> rows(size_t(kPcHudDamageSize)*kPcHudDamageSize*4);
        for(UINT y=0;y<kPcHudDamageSize;++y)std::memcpy(rows.data()+size_t(y)*kPcHudDamageSize*4,bits+size_t(y)*pitch,kPcHudDamageSize*4);
        if(format==D3DFMT_X8R8G8B8)for(size_t i=3;i<rows.size();i+=4)rows[i]=0xff;
        return sha256_bytes(rows.data(),rows.size());
    } catch(...) { return {}; }
}
inline int pc_hud_damage_index(const std::string& sha) noexcept {
    for(int i=0;i<6;++i)if(sha==kPcHudDamageSha[i])return i;
    return -1;
}

// ---------------------------------------------------------------- screen placement
struct HudMatrix { float m[4][4]{}; };
inline HudMatrix hud_multiply(const HudMatrix& a,const HudMatrix& b) noexcept {
    HudMatrix r;for(int i=0;i<4;++i)for(int j=0;j<4;++j){float s=0;for(int k=0;k<4;++k)s+=a.m[i][k]*b.m[k][j];r.m[i][j]=s;}return r;
}
// Captured from one PC damage draw: WORLD*VIEW*PROJ and the viewport.
struct HudPlacement { bool valid=false; HudMatrix wvp; float vx=0,vy=0,vw=0,vh=0; };
inline bool hud_project(const HudPlacement& p,float x,float y,float& sx,float& sy) noexcept {
    const auto& m=p.wvp.m;
    const float cx=x*m[0][0]+y*m[1][0]+m[3][0],cy=x*m[0][1]+y*m[1][1]+m[3][1],cw=x*m[0][3]+y*m[1][3]+m[3][3];
    if(!(std::fabs(cw)>1e-6f))return false;
    sx=p.vx+(cx/cw*.5f+.5f)*p.vw;sy=p.vy+(.5f-cy/cw*.5f)*p.vh;
    return std::isfinite(sx)&&std::isfinite(sy);
}
// Screen rect of a PC damage image quad (PC vertex = (intX-0.5, 0.5-intY), intX 0..32, intY -14..16),
// optionally scaled about the local origin and moved by an authored offset.
struct HudRect { float l=0,t=0,r=0,b=0; };
inline bool hud_slot_rect(const HudPlacement& p,float scale,float ox,float oy,HudRect& out) noexcept {
    if(!p.valid)return false;
    float xs[2],ys[2];
    if(!hud_project(p,ox+(-.5f)*scale,oy+(.5f-16.f)*scale,xs[0],ys[0])||!hud_project(p,ox+(31.5f)*scale,oy+(.5f+14.f)*scale,xs[1],ys[1]))return false;
    out={std::fmin(xs[0],xs[1]),std::fmin(ys[0],ys[1]),std::fmax(xs[0],xs[1]),std::fmax(ys[0],ys[1])};
    return out.r>out.l&&out.b>out.t;
}

// ---------------------------------------------------------------- native pass
enum class HudStateKind : uint8_t { Render, Stage, VertexShader, PixelShader, Texture };
struct HudStateOp { HudStateKind kind; DWORD key, stage, value; };
inline constexpr std::array<HudStateOp,38> kHudOps={{
    {HudStateKind::Render,D3DRS_ZENABLE,0,D3DZB_FALSE},{HudStateKind::Render,D3DRS_ZWRITEENABLE,0,FALSE},
    {HudStateKind::Render,D3DRS_ALPHATESTENABLE,0,FALSE},{HudStateKind::Render,D3DRS_ALPHABLENDENABLE,0,TRUE},
    {HudStateKind::Render,D3DRS_SRCBLEND,0,D3DBLEND_SRCALPHA},{HudStateKind::Render,D3DRS_DESTBLEND,0,D3DBLEND_INVSRCALPHA},
    {HudStateKind::Render,D3DRS_BLENDOP,0,D3DBLENDOP_ADD},{HudStateKind::Render,D3DRS_CULLMODE,0,D3DCULL_NONE},
    {HudStateKind::Render,D3DRS_LIGHTING,0,FALSE},{HudStateKind::Render,D3DRS_FOGENABLE,0,FALSE},
    {HudStateKind::Render,D3DRS_STENCILENABLE,0,FALSE},{HudStateKind::Render,D3DRS_CLIPPLANEENABLE,0,0},
    {HudStateKind::Render,D3DRS_COLORWRITEENABLE,0,15},{HudStateKind::Render,D3DRS_FILLMODE,0,D3DFILL_SOLID},
    {HudStateKind::Render,D3DRS_CLIPPING,0,TRUE},{HudStateKind::Render,D3DRS_SPECULARENABLE,0,FALSE},
    {HudStateKind::Render,D3DRS_VERTEXBLEND,0,D3DVBF_DISABLE},{HudStateKind::Render,D3DRS_WRAP0,0,0},
    {HudStateKind::Render,D3DRS_SHADEMODE,0,D3DSHADE_GOURAUD},
    {HudStateKind::Stage,D3DTSS_COLOROP,0,D3DTOP_MODULATE},{HudStateKind::Stage,D3DTSS_COLORARG1,0,D3DTA_TEXTURE},
    {HudStateKind::Stage,D3DTSS_COLORARG2,0,D3DTA_DIFFUSE},{HudStateKind::Stage,D3DTSS_ALPHAOP,0,D3DTOP_MODULATE},
    {HudStateKind::Stage,D3DTSS_ALPHAARG1,0,D3DTA_TEXTURE},{HudStateKind::Stage,D3DTSS_ALPHAARG2,0,D3DTA_DIFFUSE},
    {HudStateKind::Stage,D3DTSS_TEXCOORDINDEX,0,0},{HudStateKind::Stage,D3DTSS_TEXTURETRANSFORMFLAGS,0,D3DTTFF_DISABLE},
    {HudStateKind::Stage,D3DTSS_ADDRESSU,0,D3DTADDRESS_CLAMP},{HudStateKind::Stage,D3DTSS_ADDRESSV,0,D3DTADDRESS_CLAMP},
    {HudStateKind::Stage,D3DTSS_MAGFILTER,0,D3DTEXF_LINEAR},{HudStateKind::Stage,D3DTSS_MINFILTER,0,D3DTEXF_LINEAR},
    {HudStateKind::Stage,D3DTSS_MIPFILTER,0,D3DTEXF_NONE},{HudStateKind::Stage,D3DTSS_RESULTARG,0,D3DTA_CURRENT},
    {HudStateKind::Stage,D3DTSS_COLOROP,1,D3DTOP_DISABLE},{HudStateKind::Stage,D3DTSS_ALPHAOP,1,D3DTOP_DISABLE},
    {HudStateKind::VertexShader,0,0,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1},{HudStateKind::PixelShader,0,0,0},
    {HudStateKind::Texture,0,0,0},
}};
inline constexpr size_t kHudTextureOp=37,kHudColorOp=19,kHudAlphaOp=22;
static_assert(kHudOps[kHudColorOp].key==D3DTSS_COLOROP&&kHudOps[kHudAlphaOp].key==D3DTSS_ALPHAOP&&kHudOps[kHudTextureOp].kind==HudStateKind::Texture);

struct HudVertex { float x,y,z,rhw; DWORD color; float u,v; };
struct HudQuad { HudRect rect; unsigned image=0; DWORD color=0xffffffffu; };
inline DWORD hud_colour(const std::array<float,3>& rgb,float alpha) noexcept {
    const auto c=[](float v){v=v<0.f?0.f:v>1.f?1.f:v;return DWORD(v*255.f+.5f);};
    return (c(alpha)<<24)|(c(rgb[0])<<16)|(c(rgb[1])<<8)|c(rgb[2]);
}
inline std::array<HudVertex,4> hud_quad_vertices(const HudQuad& q) noexcept {
    const auto& im=kHudDamageImages[q.image];const float inset=.5f/kHudDamagePage;
    const float u0=im.u0+inset,u1=im.u1-inset,v0=im.v0+inset,v1=im.v1-inset;
    const float l=q.rect.l-.5f,t=q.rect.t-.5f,r=q.rect.r-.5f,b=q.rect.b-.5f;
    // PSB local y=-14 (v1) is the top of the image on screen (runtime: v0 at the top drew the icons upside down).
    return {{{l,t,0.f,1.f,q.color,u0,v1},{r,t,0.f,1.f,q.color,u1,v1},{l,b,0.f,1.f,q.color,u0,v0},{r,b,0.f,1.f,q.color,u1,v0}}};
}

// A sprite quad: screen rect, atlas page, UV at the rect's top-left (u0,v0) and bottom-right (u1,v1) corners.
struct HudTexQuad { HudRect rect; size_t page=0; float u0=0,v0=0,u1=0,v1=0; DWORD color=0xffffffffu; };
inline std::array<HudVertex,4> hud_tex_quad_vertices(const HudTexQuad& q) noexcept {
    const float l=q.rect.l-.5f,t=q.rect.t-.5f,r=q.rect.r-.5f,b=q.rect.b-.5f;
    return {{{l,t,0.f,1.f,q.color,q.u0,q.v0},{r,t,0.f,1.f,q.color,q.u1,q.v0},{l,b,0.f,1.f,q.color,q.u0,q.v1},{r,b,0.f,1.f,q.color,q.u1,q.v1}}};
}

struct HudLayerStatus { const char* reason="not_attempted"; HRESULT hr=S_FALSE,restore_hr=S_FALSE; uint64_t frames=0; unsigned quads=0; };

class PS2HudLayer {
    struct Saved { DWORD scalar=0; IDirect3DBaseTexture8* texture=nullptr; };
    std::array<Saved,kHudOps.size()> saved_{};
    uint64_t pending_=0;
    D3DVIEWPORT8 viewport_{};
    IDirect3DVertexBuffer8* stream_=nullptr;UINT stride_=0;
    bool viewport_pending_=false,stream_pending_=false;
    HudLayerStatus status_{};
    template<class T> static void drop(T*& p) noexcept {if(p)p->Release();p=nullptr;}
    void release_saved() noexcept {for(auto& s:saved_){drop(s.texture);s={};}drop(stream_);}
    HRESULT write(IDirect3DDevice8& d,size_t i,DWORD scalar,IDirect3DBaseTexture8* texture) noexcept {
        const auto& op=kHudOps[i];pending_|=uint64_t(1)<<i;
        switch(op.kind){
        case HudStateKind::Render:return d.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),scalar);
        case HudStateKind::Stage:return d.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),scalar);
        case HudStateKind::VertexShader:return d.SetVertexShader(scalar);
        case HudStateKind::PixelShader:return d.SetPixelShader(scalar);
        case HudStateKind::Texture:return d.SetTexture(op.stage,texture);
        }
        return E_INVALIDARG;
    }
    HRESULT capture(IDirect3DDevice8& d) noexcept {
        release_saved();HRESULT hr=S_OK;
        for(size_t i=0;i<kHudOps.size()&&SUCCEEDED(hr);++i){
            const auto& op=kHudOps[i];auto& v=saved_[i];
            switch(op.kind){
            case HudStateKind::Render:hr=d.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&v.scalar);break;
            case HudStateKind::Stage:hr=d.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&v.scalar);break;
            case HudStateKind::VertexShader:hr=d.GetVertexShader(&v.scalar);break;
            case HudStateKind::PixelShader:hr=d.GetPixelShader(&v.scalar);break;
            case HudStateKind::Texture:hr=d.GetTexture(op.stage,&v.texture);break;
            }
        }
        if(SUCCEEDED(hr))hr=d.GetViewport(&viewport_);
        if(SUCCEEDED(hr))hr=d.GetStreamSource(0,&stream_,&stride_);
        if(FAILED(hr))release_saved();
        return hr;
    }
    HRESULT fail(const char* reason,HRESULT hr) noexcept {status_.reason=reason;status_.hr=hr;return hr;}
public:
    PS2HudLayer()=default;
    ~PS2HudLayer(){release_saved();}
    PS2HudLayer(const PS2HudLayer&)=delete;
    PS2HudLayer& operator=(const PS2HudLayer&)=delete;
    bool pending() const noexcept {return pending_||viewport_pending_||stream_pending_;}
    const HudLayerStatus& status() const noexcept {return status_;}
    HRESULT restore(IDirect3DDevice8& d) noexcept {
        HRESULT result=S_OK;const auto keep=[&](HRESULT hr){if(FAILED(hr)&&SUCCEEDED(result))result=hr;};
        if(viewport_pending_){const HRESULT hr=d.SetViewport(&viewport_);if(SUCCEEDED(hr))viewport_pending_=false;else keep(hr);}
        if(stream_pending_){const HRESULT hr=d.SetStreamSource(0,stream_,stride_);if(SUCCEEDED(hr))stream_pending_=false;else keep(hr);}
        for(size_t i=kHudOps.size();i-- >0;){
            const uint64_t bit=uint64_t(1)<<i;if(!(pending_&bit))continue;
            const HRESULT hr=write(d,i,saved_[i].scalar,saved_[i].texture);
            if(SUCCEEDED(hr))pending_&=~bit;else keep(hr);
        }
        if(!pending())release_saved();
        status_.restore_hr=result;return result;
    }
    // Draws the quads over the finished frame (outside any scene) on the full render target.
    HRESULT draw(IDirect3DDevice8& d,const std::array<IDirect3DTexture8*,2>& pages,const std::vector<HudQuad>& quads,
                 UINT width,UINT height,bool scene_active,bool recording) noexcept {
        status_.quads=0;
        if(quads.empty())return fail("nothing_to_draw",S_FALSE);
        if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
        if(scene_active||recording)return fail(scene_active?"scene_still_active":"stateblock_recording",S_FALSE);
        if(!pages[0]||!pages[1]||!width||!height)return fail("pages_missing",E_FAIL);
        HRESULT hr=capture(d);if(FAILED(hr))return fail("native_state_capture_failed",hr);
        hr=d.BeginScene();if(FAILED(hr)){restore(d);return fail("begin_scene_failed",hr);}
        viewport_pending_=true;const D3DVIEWPORT8 full{0,0,width,height,0.f,1.f};hr=d.SetViewport(&full);
        for(size_t i=0;i<kHudOps.size()&&SUCCEEDED(hr);++i)if(i!=kHudTextureOp)hr=write(d,i,kHudOps[i].value,nullptr);
        unsigned page=2;
        for(const auto& q:quads){
            if(FAILED(hr))break;
            const unsigned want=kHudDamageImages[q.image].page;
            if(want!=page){hr=write(d,kHudTextureOp,0,pages[want]);page=want;if(FAILED(hr))break;}
            const auto v=hud_quad_vertices(q);stream_pending_=true;
            hr=d.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,v.data(),sizeof(HudVertex));
            if(SUCCEEDED(hr))++status_.quads;
        }
        const HRESULT ended=d.EndScene();const HRESULT restored=restore(d);
        if(FAILED(restored))return fail("native_state_restore_failed",restored);
        if(FAILED(hr)||FAILED(ended))return fail(FAILED(hr)?"draw_failed":"end_scene_failed",FAILED(hr)?hr:ended);
        ++status_.frames;status_.reason="ps2_hud_damage_drawn";status_.hr=S_OK;return S_OK;
    }
    // Textured quads from several 64x64 atlas pages (PS2 font / image banks): explicit screen rect, page and UVs.
    HRESULT draw_textured(IDirect3DDevice8& d,const std::vector<IDirect3DTexture8*>& pages,const std::vector<HudTexQuad>& quads,
                          UINT width,UINT height,bool scene_active,bool recording) noexcept {
        status_.quads=0;
        if(quads.empty())return fail("nothing_to_draw",S_FALSE);
        if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
        if(scene_active||recording)return fail(scene_active?"scene_still_active":"stateblock_recording",S_FALSE);
        if(!width||!height)return fail("target_size_missing",E_FAIL);
        for(const auto& q:quads)if(q.page>=pages.size()||!pages[q.page])return fail("pages_missing",E_FAIL);
        HRESULT hr=capture(d);if(FAILED(hr))return fail("native_state_capture_failed",hr);
        hr=d.BeginScene();if(FAILED(hr)){restore(d);return fail("begin_scene_failed",hr);}
        viewport_pending_=true;const D3DVIEWPORT8 full{0,0,width,height,0.f,1.f};hr=d.SetViewport(&full);
        for(size_t i=0;i<kHudOps.size()&&SUCCEEDED(hr);++i)if(i!=kHudTextureOp)hr=write(d,i,kHudOps[i].value,nullptr);
        size_t page=SIZE_MAX;
        for(const auto& q:quads){
            if(FAILED(hr))break;
            if(q.page!=page){hr=write(d,kHudTextureOp,0,pages[q.page]);page=q.page;if(FAILED(hr))break;}
            const auto v=hud_tex_quad_vertices(q);stream_pending_=true;
            hr=d.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,v.data(),sizeof(HudVertex));
            if(SUCCEEDED(hr))++status_.quads;
        }
        const HRESULT ended=d.EndScene();const HRESULT restored=restore(d);
        if(FAILED(restored))return fail("native_state_restore_failed",restored);
        if(FAILED(hr)||FAILED(ended))return fail(FAILED(hr)?"draw_failed":"end_scene_failed",FAILED(hr)?hr:ended);
        ++status_.frames;status_.reason="ps2_hud_sprites_drawn";status_.hr=S_OK;return S_OK;
    }
    // Untextured triangle strips (PS2 stroked HUD primitives, PRIM 0x14c): colour and alpha from the vertices.
    HRESULT draw_strips(IDirect3DDevice8& d,const std::vector<std::vector<HudVertex>>& strips,UINT width,UINT height,
                        bool scene_active,bool recording) noexcept {
        status_.quads=0;
        if(strips.empty())return fail("nothing_to_draw",S_FALSE);
        if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
        if(scene_active||recording)return fail(scene_active?"scene_still_active":"stateblock_recording",S_FALSE);
        if(!width||!height)return fail("target_size_missing",E_FAIL);
        HRESULT hr=capture(d);if(FAILED(hr))return fail("native_state_capture_failed",hr);
        hr=d.BeginScene();if(FAILED(hr)){restore(d);return fail("begin_scene_failed",hr);}
        viewport_pending_=true;const D3DVIEWPORT8 full{0,0,width,height,0.f,1.f};hr=d.SetViewport(&full);
        for(size_t i=0;i<kHudOps.size()&&SUCCEEDED(hr);++i){
            DWORD value=kHudOps[i].value;
            if(i==kHudColorOp||i==kHudAlphaOp)value=D3DTOP_SELECTARG2;
            hr=write(d,i,value,nullptr);
        }
        for(const auto& s:strips){
            if(FAILED(hr))break;
            if(s.size()<3)continue;
            stream_pending_=true;
            hr=d.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,UINT(s.size()-2),s.data(),sizeof(HudVertex));
            if(SUCCEEDED(hr))++status_.quads;
        }
        const HRESULT ended=d.EndScene();const HRESULT restored=restore(d);
        if(FAILED(restored))return fail("native_state_restore_failed",restored);
        if(FAILED(hr)||FAILED(ended))return fail(FAILED(hr)?"draw_failed":"end_scene_failed",FAILED(hr)?hr:ended);
        ++status_.frames;status_.reason="ps2_hud_strips_drawn";status_.hr=S_OK;return S_OK;
    }
};

// ---------------------------------------------------------------- feature object
struct HudPcIdentity { uintptr_t texture=0; uint64_t generation=0; int index=-1; const char* reason=""; };

class PS2HudDamage {
    bool requested_=false,disabled_=false;
    std::array<std::vector<DWORD>,2> pixels_;
    std::array<IDirect3DTexture8*,2> pages_{};
    std::array<HudPcIdentity,16> identities_{};
    size_t next_identity_=0;
    std::array<HudPlacement,5> slots_{};       // this frame's PC damage icon draws
    bool frame_seen_=false;
    bool feed_ok_=false;                       // last Present had a live semantic feed
    uint64_t race_generation_=0;
    HudDamageState state_;
    long long last_qpc_=0;
    const char* startup_reason_=nullptr;
    uint64_t suppressed_=0;
public:
    PS2HudLayer layer;
    PS2HudDamage(bool supported,const std::wstring& ini) noexcept {
        if(!supported)return;
        try{
            if(config::read_int(L"PS2HudDamage",0,ini.c_str())!=1)return;
            wchar_t folder[32768]{};
            config::read_string(L"PS2HudAssetDir",L"PS2Hud",folder,32768,ini.c_str());
            auto dir=std::filesystem::path(folder);if(dir.is_relative())dir=std::filesystem::path(ini).parent_path()/dir;
            bool ok=true;
            for(unsigned p=0;p<2&&ok;++p){
                std::ifstream file(dir/(p?L"PS2HudDamage001.gxi":L"PS2HudDamage000.gxi"),std::ios::binary);
                std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
                ok=decode_hud_damage_page(bytes,p,pixels_[p]);
            }
            requested_=ok;
            if(!ok){startup_reason_="hud_damage_asset_missing_or_mismatch";pixels_={};}
        }catch(...){requested_=false;pixels_={};}
    }
    ~PS2HudDamage(){release_pages();}
    PS2HudDamage(const PS2HudDamage&)=delete;
    PS2HudDamage& operator=(const PS2HudDamage&)=delete;
    bool requested() const noexcept {return requested_&&!disabled_;}
    void disable() noexcept {disabled_=true;}
    const char* take_startup_reason() noexcept {const char* r=startup_reason_;startup_reason_=nullptr;return r;}
    bool feed_ok() const noexcept {return feed_ok_;}
    uint64_t suppressed() const noexcept {return suppressed_;}
    HudDamageState& state() noexcept {return state_;}
    void release_pages() noexcept {for(auto& p:pages_){if(p)p->Release();p=nullptr;}}
    bool initialize(IDirect3DDevice8& n) noexcept {
        if(pages_[0]&&pages_[1])return true;
        if(!requested())return false;
        release_pages();
        for(unsigned p=0;p<2;++p){
            if(FAILED(n.CreateTexture(kHudDamagePage,kHudDamagePage,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&pages_[p]))||!pages_[p]){pages_[p]=nullptr;release_pages();disable();return false;}
            D3DLOCKED_RECT lock{};if(FAILED(pages_[p]->LockRect(0,&lock,nullptr,0))){release_pages();disable();return false;}
            const bool good=lock.pBits&&lock.Pitch>=INT(kHudDamagePage*4);
            if(good)for(UINT y=0;y<kHudDamagePage;++y)std::memcpy(static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,pixels_[p].data()+size_t(y)*kHudDamagePage,kHudDamagePage*4);
            if(FAILED(pages_[p]->UnlockRect(0))||!good){release_pages();disable();return false;}
        }
        return true;
    }
    const std::array<IDirect3DTexture8*,2>& pages() const noexcept {return pages_;}
    // Exact PC hud-damage identity of a bound texture, cached per resource generation.
    HudPcIdentity identify(IDirect3DBaseTexture8* base,uint64_t generation) noexcept {
        const auto id=reinterpret_cast<uintptr_t>(base);
        if(!base||!generation)return {id,generation,-1,"stage0_texture_untracked"};
        for(const auto& c:identities_)if(c.texture==id&&c.generation==generation)return c;
        HudPcIdentity result{id,generation,-1,"not_pc_hud_damage"};
        if(base->GetType()==D3DRTYPE_TEXTURE){
            auto* t=static_cast<IDirect3DTexture8*>(base);D3DSURFACE_DESC desc{};
            if(SUCCEEDED(t->GetLevelDesc(0,&desc))&&desc.Width==kPcHudDamageSize&&desc.Height==kPcHudDamageSize&&
               (desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8)&&desc.Pool!=D3DPOOL_DEFAULT){
                D3DLOCKED_RECT lock{};
                if(SUCCEEDED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY))){
                    const auto sha=pc_hud_level0_sha(static_cast<const BYTE*>(lock.pBits),lock.Pitch,desc.Format);
                    t->UnlockRect(0);
                    result.index=pc_hud_damage_index(sha);
                    if(result.index>=0)result.reason="exact_pc_hud_damage";
                }else result.reason="pc_hud_lock_failed";
            }
        }
        identities_[next_identity_]=result;next_identity_=(next_identity_+1)%identities_.size();
        return result;
    }
    // A PC damage draw was replaced: keep its placement (slot icons 0..4; the frame image 5 only marks the frame).
    void note_pc_draw(int index,const HudPlacement& placement) noexcept {
        ++suppressed_;frame_seen_=true;
        if(index>=0&&index<5)slots_[index]=placement;
    }
    // Present: advance the PS2 logic and build the quads for this frame's PC row places.
    // values: steering, engine, suspension, gear, tyres; feed false keeps the last state.
    std::vector<HudQuad> frame(bool feed,const std::array<float,5>& values,uint64_t race_generation,bool paused,float dt) {
        std::vector<HudQuad> quads;
        feed_ok_=feed;
        if(feed&&race_generation!=race_generation_){state_.reset();race_generation_=race_generation;}
        if(feed){state_.update(values);if(!paused)state_.advance(dt);}
        const bool seen=frame_seen_;frame_seen_=false;
        auto slots=slots_;slots_={};
        if(!seen)return quads;
        for(unsigned i=0;i<5;++i){HudRect r;if(!hud_slot_rect(slots[i],1.f,0.f,0.f,r))continue;
            quads.push_back({r,i,hud_colour(kPS2DamageColours[state_.band(i)],1.f)});}
        for(unsigned i=0;i<5;++i){HudRect r;if(!hud_slot_rect(slots[i],1.f,0.f,0.f,r))continue;
            quads.push_back({r,kHudDamageFrameImage,0xffffffffu});}
        const auto& notices=state_.notices();
        for(size_t k=std::min<size_t>(notices.size(),2);k-- >0;){
            float alpha=0,dy=0;if(!notice_pose(notices[k],alpha,dy))continue;
            HudRect r;if(!hud_slot_rect(slots[4],kNotifyScale,kNotifyOffsetX,kNotifyOffsetY+dy,r))continue;
            quads.push_back({r,notices[k].image,hud_colour(kPS2DamageColours[notices[k].band],alpha)});
            quads.push_back({r,kHudDamageFrameImage,hud_colour({1,1,1},alpha)});
        }
        return quads;
    }
    float tick(long long now,long long frequency) noexcept {
        const float dt=last_qpc_&&frequency?float(double(now-last_qpc_)/double(frequency)):0.f;last_qpc_=now;return dt;
    }
};

}  // namespace gfx2::ps2port
