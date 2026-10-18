#pragma once
// PS2HudSplitFlash=1: the PS2 gaHudAiSplitTime flash of the SPLIT TIME value after a checkpoint.
//
// EE 0x14c000 (per 50 Hz frame), owner +0x14 = Race/Car<local>/SplitPoint (int), +0x18 last value (init -1),
// +0x1c active, +0x20 angle (init 90):
//   if active: if angle < 450: c = clamp(|sinf(angle)|, 0, 1) (fdlibm sinf 0x3f3140, radians), angle += 6,
//              text colour (c,c,c,1); else active = 0, angle = 90, colour (1,1,1,1)
//   if SplitPoint != last: last = SplitPoint, new text, active = 1, angle = 90.
// GS dumps 20261018 161115 / 161201 show the value at (10,10,10) and (119,119,119) while the labels stay white.
// The PC gaHudAiSplitTime (0x4a9050) only rewrites the text. Its draws (egg GameSplitTimeNumber, white vertices)
// are modulated by TEXTUREFACTOR in stage1 while the flash runs.
#include "ps2_hud_damage_feed.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>

namespace gfx2::ps2port {

class SplitFlashModel {
    bool active_=false;float angle_=90.f,colour_=1.f,pending_=0.f;int last_=-1;
public:
    void reset() noexcept {*this=SplitFlashModel{};}
    float colour() const noexcept {return colour_;}
    bool active() const noexcept {return active_;}
    // split: current SplitPoint; dt seconds (PS2 steps at 50 Hz).
    void update(int split,float dt) noexcept {
        pending_+=std::clamp(dt,0.f,.25f);
        int steps=0;
        while(pending_>=.02f&&steps<12){
            pending_-=.02f;++steps;
            if(active_){
                if(angle_<450.f){colour_=std::clamp(std::fabs(std::sin(angle_)),0.f,1.f);angle_+=6.f;}
                else{active_=false;angle_=90.f;colour_=1.f;}
            }
            if(split!=last_){last_=split;active_=true;angle_=90.f;}
        }
    }
};

class PS2HudSplitFlash {
    bool requested_=false,context_=false;uint64_t generation_=0;uint32_t split_id_=0;bool id_ok_=false;
    SplitFlashModel model_;long long last_qpc_=0;const char* reason_="not_read";uint64_t modulated_=0;
public:
    explicit PS2HudSplitFlash(bool supported,const std::wstring& ini) noexcept {
        if(!supported)return;
        try{requested_=config::read_int(L"PS2HudSplitFlash",0,ini.c_str())==1;}catch(...){requested_=false;}
    }
    bool requested() const noexcept {return requested_;}
    const char* reason() const noexcept {return reason_;}
    uint64_t modulated() const noexcept {return modulated_;}
    void note_modulated() noexcept {++modulated_;}
    // Colour factor for this frame's GameSplitTimeNumber draws, or 1 when nothing to do.
    float factor() const noexcept {return requested_&&context_?model_.colour():1.f;}
    void present(RaceReadMemory& m,uint32_t base,bool hud_valid,uint64_t generation,long long now,long long frequency) noexcept {
        const float dt=last_qpc_&&frequency>0?float(double(now-last_qpc_)/double(frequency)):.02f;last_qpc_=now;
        context_=false;
        if(!hud_valid||!generation){reason_="no_race_hud";return;}
        if(generation!=generation_){
            generation_=generation;id_ok_=false;model_.reset();
            int locals=0,local=0;
            for(int i=0;i<8;++i){char key[64]{};uint32_t id=0;std::snprintf(key,sizeof(key),"Race/Car%d/PlayerType",i);
                if(!m.resolve_id(base,key,id))break;const auto t=race_broker_scalar(m,base,id,2);if(t.present&&t.value==1){++locals;local=i;}}
            char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%d/SplitPoint",local);
            id_ok_=locals==1&&m.resolve_id(base,key,split_id_);
        }
        if(!id_ok_){reason_="split_point_key_unresolved";return;}
        const auto split=race_broker_scalar(m,base,split_id_,2);
        if(!split.present){reason_="split_point_unreadable";return;}
        model_.update(split.value,dt);context_=true;reason_=model_.active()?"split_flash_active":"split_flash_idle";
    }
};

}  // namespace gfx2::ps2port
