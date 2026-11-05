#pragma once
// FreeCam bookmark label: when a bookmark slot is selected, saved or loaded, a
// short "CAMERA 2/3 LOADED" line is shown top-left for two seconds, then fades.
// Drawn at Present over the finished frame (same PS2HudLayer state transaction
// as the collision legend), so it never touches the scene or the game HUD.
// PS2Port.ini: FreeCamBookmarkLabel=1 (default) / 0.
#include "free_camera.hpp"
#include "collision_debug.hpp"
#include "ps2_hud_damage.hpp"
#include <algorithm>
#include <string>
#include <vector>

namespace gfx2::ps2port {

inline std::string bookmark_label_text(const CameraBookmarkNotice& n) {
    const std::string slot="CAMERA "+std::to_string(n.slot)+"/"+std::to_string(n.slots);
    const std::string action=n.action?n.action:"",result=n.result?n.result:"";
    if(result=="freecam_inactive")return "CAMERA: FREECAM OFF";
    if(result=="bookmarks_disabled")return "CAMERA: BOOKMARKS OFF";
    if(action=="select"&&result=="slot_selected")return slot+(n.present?"":" - EMPTY");
    if(action=="save"&&result=="saved_atomically")return slot+" SAVED";
    if(action=="load"&&result=="loaded_exact_pose")return slot+" LOADED";
    if(action=="load"&&result=="empty_slot")return slot+" EMPTY";
    std::string upper=action;for(char& c:upper)if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');
    return slot+" "+upper+" FAILED";
}

class BookmarkOsd {
    static constexpr ULONGLONG kShowMs=2000,kFadeMs=400;
    bool enabled_=true;uint64_t seen_=0;ULONGLONG start_=0;std::string text_;PS2HudLayer layer_;
public:
    void configure(bool enabled) noexcept {enabled_=enabled;seen_=camera_bookmark_notice().serial;}
    bool requested() const noexcept {
        if(!enabled_)return false;
        return camera_bookmark_notice().serial!=seen_||(start_&&GetTickCount64()-start_<kShowMs)||layer_.pending();
    }
    bool pending() const noexcept {return layer_.pending();}
    HRESULT present(IDirect3DDevice8& device,bool scene_active,bool recording) noexcept {
        if(!enabled_)return S_FALSE;
        try{
            const auto notice=camera_bookmark_notice();
            if(notice.serial!=seen_){seen_=notice.serial;text_=bookmark_label_text(notice);start_=GetTickCount64();if(!start_)start_=1;}
            if(!start_)return S_FALSE;
            const ULONGLONG age=GetTickCount64()-start_;
            if(age>=kShowMs){start_=0;return S_FALSE;}
            const float fade=age+kFadeMs>kShowMs?float(kShowMs-age)/float(kFadeMs):1.f;
            IDirect3DSurface8* back=nullptr;D3DSURFACE_DESC desc{};
            if(FAILED(device.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back))||!back)return S_FALSE;
            const HRESULT described=back->GetDesc(&desc);back->Release();if(FAILED(described))return described;
            colldebug::Legend legend;legend.scale=float(std::max<UINT>(3,desc.Height/270));
            const float pad=legend.scale*2,x=legend.scale*8,y=legend.scale*8;
            const DWORD a=DWORD(std::clamp(fade,0.f,1.f)*255.f);
            legend.rect(x-pad,y-pad,legend.text_width(text_)-legend.scale+pad*2,legend.scale*5+pad*2,((a*0x90/255)<<24));
            legend.text(x,y,text_,(a<<24)|0xffffffu);
            std::vector<std::vector<HudVertex>> strips;strips.reserve(legend.quads.size()/6);
            for(size_t i=0;i+5<legend.quads.size();i+=6){
                const auto& p=legend.quads[i];const auto& q=legend.quads[i+1];const auto& r=legend.quads[i+2];const auto& s=legend.quads[i+4];
                strips.push_back({{p.x,p.y,0.f,1.f,p.color,0,0},{q.x,q.y,0.f,1.f,q.color,0,0},{r.x,r.y,0.f,1.f,r.color,0,0},{s.x,s.y,0.f,1.f,s.color,0,0}});
            }
            return layer_.draw_strips(device,strips,desc.Width,desc.Height,scene_active,recording);
        }catch(...){return E_OUTOFMEMORY;}
    }
};

} // namespace gfx2::ps2port
