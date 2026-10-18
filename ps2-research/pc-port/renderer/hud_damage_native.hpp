#pragma once
// Native layer of the PS2 HUD widgets (renderer/ps2_hud_damage.hpp, ps2_hud_map.hpp, ps2_hud_template.hpp,
// ps2_hud_eggs.hpp). Compiled only into the staged baseline. A UI draw (MRallye.exe 0x56d7c4 caller) is taken over
// only when its stage0 texture is one exact PC image owned by an enabled PS2 widget whose last Present had a live
// feed / certified race HUD context:
//   PS2HudDamage: hud-damage_000..005; PS2HudMap: hud-template_001 (GPS radar) / _007 (GPS pointer):
//     the draw is not forwarded; its final WORLD (PreserveMargins already applied by UiWorldScope), VIEW,
//     PROJECTION and viewport place the PS2 widget where the PC widget would be.
//   PS2HudTemplate: hud-template images 0,2,4,5,6,8,9,10: the same draw is issued with the PS2 texture bound.
// PS2HudHidePcOnly: a draw under a PC-only egg (exact name via the egg registry) is not forwarded.
#include "xtrail_native_integration.hpp"
#include "ps2_hud_damage.hpp"
#include "ps2_hud_map.hpp"
#include "ps2_hud_template.hpp"
#include "ps2_hud_eggs.hpp"
#include "ps2_hud_timediffs.hpp"
#include "ps2_hud_splitflash.hpp"

namespace gfx2::hudintegration {

inline ps2port::PS2HudDamage* hud(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->hud_damage():nullptr;}
inline ps2port::PS2HudMap* map(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->hud_map():nullptr;}

inline ps2port::HudMatrix hud_matrix(const D3DMATRIX& m) noexcept {
    ps2port::HudMatrix r;for(int i=0;i<4;++i)for(int j=0;j<4;++j)r.m[i][j]=m.m[i][j];return r;
}
inline bool placement(IDirect3DDevice8& n,ps2port::HudPlacement& p) noexcept {
    D3DMATRIX world{},view{},projection{};D3DVIEWPORT8 viewport{};
    if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||FAILED(n.GetTransform(D3DTS_VIEW,&view))||
       FAILED(n.GetTransform(D3DTS_PROJECTION,&projection))||FAILED(n.GetViewport(&viewport)))return false;
    p.wvp=ps2port::hud_multiply(ps2port::hud_multiply(hud_matrix(world),hud_matrix(view)),hud_matrix(projection));
    p.vx=float(viewport.X);p.vy=float(viewport.Y);p.vw=float(viewport.Width);p.vh=float(viewport.Height);
    p.valid=viewport.Width&&viewport.Height;return p.valid;
}

// Returns true when the PC draw is replaced (the caller must not forward it).
inline bool capture_ui_draw(Device8& d,bool ui_callsite,D3DPRIMITIVETYPE type,UINT start,UINT count,uintptr_t entity) noexcept {
    auto* h=hud(d);auto* m=map(d);auto* port=d.ps2_port();
    auto* t=port?port->hud_template():nullptr;auto* td=port?port->hud_timediffs():nullptr;
    const bool damage=h&&h->requested()&&h->feed_ok(),gps=m&&m->requested()&&m->feed_ok();
    const bool templ=t&&t->requested()&&t->context_ok(),eggs=port&&port->hud_eggs_requested()&&port->hud_eggs_context();
    const bool rows=td&&td->hide_rows();
    if((!damage&&!gps&&!templ&&!eggs&&!rows)||!ui_callsite||type!=D3DPT_TRIANGLELIST||!count)return false;
    if(!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||
       GetCurrentThreadId()!=d.trace.render_thread_id())return false;
    if(!d.trace.shadow.bindings.vertex_shader.known||d.trace.shadow.bindings.vertex_shader.value!=0x142)return false;
    try{
        if(eggs&&entity){
            ps2port::HudLiveMemory memory;
            const auto egg=port->hud_eggs().resolve(memory,0x400000,entity);
            if(port->diagnostics()){
                const auto& w=d.trace.effective_shadow.matrices[D3DTS_WORLD];std::string line;
                if(port->hud_eggs().probe_json(memory,0x400000,entity,w.known?w.value._41:-1.f,w.known?w.value._42:-1.f,line)){try{session().write(line);}catch(...){}}
            }
            if(egg.role==ps2port::HudEggRole::PcOnly&&port->hud_hide_pc_only()){++port->hud_hidden_draws();return true;}
            // PS2HudSplitFlash: the SPLIT TIME value (white vertices) times the PS2 flash colour through stage1 TFACTOR.
            auto* flash=port->hud_split_flash();
            if(flash&&egg.role!=ps2port::HudEggRole::Unknown&&!std::strcmp(egg.name,"GameSplitTimeNumber")){
                const float c=flash->factor();
                const auto& op=d.trace.effective_shadow.tss[1][D3DTSS_COLOROP];
                if(c<1.f&&op.known&&op.value==D3DTOP_DISABLE){
                    auto& n=*d.native();
                    DWORD factor=0,colorop=0,arg1=0,arg2=0,alphaop=0,alphaarg1=0;
                    if(FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&factor))||FAILED(n.GetTextureStageState(1,D3DTSS_COLOROP,&colorop))||
                       FAILED(n.GetTextureStageState(1,D3DTSS_COLORARG1,&arg1))||FAILED(n.GetTextureStageState(1,D3DTSS_COLORARG2,&arg2))||
                       FAILED(n.GetTextureStageState(1,D3DTSS_ALPHAOP,&alphaop))||FAILED(n.GetTextureStageState(1,D3DTSS_ALPHAARG1,&alphaarg1)))return false;
                    const DWORD v=DWORD(c*255.f+.5f);const DWORD tf=0xff000000u|(v<<16)|(v<<8)|v;
                    HRESULT hr=n.SetRenderState(D3DRS_TEXTUREFACTOR,tf);
                    if(SUCCEEDED(hr))hr=n.SetTextureStageState(1,D3DTSS_COLORARG1,D3DTA_CURRENT);
                    if(SUCCEEDED(hr))hr=n.SetTextureStageState(1,D3DTSS_COLORARG2,D3DTA_TFACTOR);
                    if(SUCCEEDED(hr))hr=n.SetTextureStageState(1,D3DTSS_ALPHAARG1,D3DTA_CURRENT);
                    if(SUCCEEDED(hr))hr=n.SetTextureStageState(1,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);
                    if(SUCCEEDED(hr))hr=n.SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_MODULATE);
                    const HRESULT drawn=SUCCEEDED(hr)?n.DrawPrimitive(type,start,count):hr;
                    HRESULT restored=n.SetTextureStageState(1,D3DTSS_COLOROP,colorop);
                    if(SUCCEEDED(restored))restored=n.SetTextureStageState(1,D3DTSS_ALPHAOP,alphaop);
                    if(SUCCEEDED(restored))restored=n.SetTextureStageState(1,D3DTSS_COLORARG1,arg1);
                    if(SUCCEEDED(restored))restored=n.SetTextureStageState(1,D3DTSS_COLORARG2,arg2);
                    if(SUCCEEDED(restored))restored=n.SetTextureStageState(1,D3DTSS_ALPHAARG1,alphaarg1);
                    if(SUCCEEDED(restored))restored=n.SetRenderState(D3DRS_TEXTUREFACTOR,factor);
                    if(FAILED(restored))return true;          // never forward the PC draw over half-restored states
                    if(SUCCEEDED(drawn)){flash->note_modulated();return true;}
                    return false;
                }
            }
        }
        auto& n=*d.native();
        // PS2HudTimeDiffs: the PC gaHudTimeDiffsAi rows (exact child entities of the TimeDiffs egg's AI).
        if(rows&&entity){
            const int row=td->rows().row_of(entity);
            if(row>=0){
                ps2port::HudPlacement p;placement(n,p);
                ps2integration::Ref<IDirect3DBaseTexture8> bound;uint64_t generation=0;
                if(SUCCEEDED(n.GetTexture(0,&bound.value))&&bound.value){
                    const auto& tracked=d.trace.effective_shadow.bindings.textures[0];
                    const auto id=reinterpret_cast<uintptr_t>(bound.value);
                    if(tracked.known&&tracked.value==id)generation=d.trace.resources.generation(id);
                }
                td->note_pc_row(row,p,bound.value,generation);return true;
            }
        }
        ps2integration::Ref<IDirect3DBaseTexture8> texture;
        if(FAILED(n.GetTexture(0,&texture.value))||!texture.value)return false;
        const auto id=reinterpret_cast<uintptr_t>(texture.value);
        const auto& tracked=d.trace.effective_shadow.bindings.textures[0];
        if(!tracked.known||tracked.value!=id)return false;
        const uint64_t generation=d.trace.resources.generation(id);
        if(damage){
            const auto identity=h->identify(texture.value,generation);
            if(identity.index>=0){ps2port::HudPlacement p;if(!placement(n,p))return false;h->note_pc_draw(identity.index,p);return true;}
        }
        if(gps){
            const auto identity=m->identify(texture.value,generation);
            if(identity.index>=0){ps2port::HudPlacement p;if(!placement(n,p))return false;m->note_pc_draw(identity.index,p);return true;}
        }
        if(templ){
            const ps2port::HudTemplateImage* image=nullptr;
            auto* ps2=t->substitute(texture.value,generation,&image);
            if(!ps2||!image)return false;
            // Split marker / ticks / finish: drawn at Present over the PS2 bar (PC order puts them under it).
            if(ps2port::hud_template_deferred(image->image)){ps2port::HudPlacement p;if(placement(n,p)&&t->defer(*image,p))return true;}
            // A different PS2 image box: the PC quad (authored units, before WORLD) is remapped onto it.
            const auto& r=image->remap;const bool remap=r.sx!=1.f||r.tx!=0.f||r.sy!=1.f||r.ty!=0.f;
            D3DMATRIX world{};
            if(remap){
                if(FAILED(n.GetTransform(D3DTS_WORLD,&world)))return false;
                D3DMATRIX moved=world;   // M*WORLD with M = diag(sx,sy,1,1) + translation (tx,ty)
                for(int j=0;j<4;++j){moved.m[0][j]=r.sx*world.m[0][j];moved.m[1][j]=r.sy*world.m[1][j];
                    moved.m[3][j]=r.tx*world.m[0][j]+r.ty*world.m[1][j]+world.m[3][j];}
                if(FAILED(n.SetTransform(D3DTS_WORLD,&moved))){n.SetTransform(D3DTS_WORLD,&world);return false;}
            }
            HRESULT drawn=E_FAIL;
            if(SUCCEEDED(n.SetTexture(0,ps2))){
                drawn=n.DrawPrimitive(type,start,count);
                if(FAILED(n.SetTexture(0,texture.value))){if(remap)n.SetTransform(D3DTS_WORLD,&world);t->disable();return true;}  // never forward over a foreign binding
            }
            if(remap&&FAILED(n.SetTransform(D3DTS_WORLD,&world))){t->disable();return true;}
            if(FAILED(drawn))return false;                                         // PC draw goes ahead unchanged
            t->note_substituted();return true;
        }
        return false;
    }catch(...){return false;}
}

}  // namespace gfx2::hudintegration
