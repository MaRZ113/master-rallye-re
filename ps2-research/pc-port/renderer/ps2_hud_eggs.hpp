#pragma once
// HUD element (egg) names for native UI draws.
//
// The baseline UI consumer hook (UiMargins::enter_consume, MRallye.exe 0x56d110) runs every UI packet under the
// egg that owns it (egg+0x4c is its en2d packet). An egg's name is the pool text id at egg+0x5c, and the egg
// registry (base+0x2f96fc, +0x1c: vector of buckets indexed by name id) lists the egg under that id
// (renderer/fleet_participants.hpp egg_chain). A name is accepted only when both agree and the egg is not retired.
//
// PS2HudHidePcOnly=1 suppresses the draws of the eggs that exist only in the PC Hud0.xml (PS2 HUD0.XML has none):
//   SpeedVelocityText ("MPH"/"KPH" under the speed), TimeDiffs (gaHudTimeDiffsAi opponent list; PS2 uses
//   gaHudTimeDiffs2Ai) and TimeDiffArrow (its hud-template image 7 arrow).
#include "ps2_hud_damage_feed.hpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

namespace gfx2::ps2port {

inline constexpr uint32_t kHudEggManagerRva=0x2f96fc;
inline constexpr const char* kHudPcOnlyEggs[]={"SpeedVelocityText","TimeDiffs","TimeDiffArrow"};

enum class HudEggRole : uint8_t { Unknown, Named, PcOnly };

inline HudEggRole hud_egg_role_for_name(const char* name) noexcept {
    if(!name||!*name)return HudEggRole::Unknown;
    for(const char* n:kHudPcOnlyEggs)if(!std::strcmp(name,n))return HudEggRole::PcOnly;
    return HudEggRole::Named;
}

class HudEggNames {
public:
    struct Entry { uint32_t egg=0,id=0; HudEggRole role=HudEggRole::Unknown; char name[40]{}; };
private:
    std::array<Entry,192> cache_{};size_t next_=0;   // two HUDs (split screen) stay cached
    std::array<Entry,64> seen_{};size_t seen_count_=0;bool seen_changed_=false;
    static bool word(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return a&&!(a&3)&&m.read(a,&v,4);}
    static bool pointer(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return word(m,a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);}
    static bool registered(RaceReadMemory& m,uint32_t base,uint32_t egg,uint32_t id) noexcept {
        uint32_t manager=0,registry=0,begin=0,end=0,bucket=0,b=0,e=0;
        if(!pointer(m,base+kHudEggManagerRva,manager)||!pointer(m,manager+0x1c,registry)||!word(m,registry+4,begin)||!word(m,registry+8,end)||
           !begin||end<begin||(end-begin)%4||id>=(end-begin)/4)return false;
        if(!pointer(m,begin+id*4,bucket)||!word(m,bucket+4,b)||!word(m,bucket+8,e)||!b||e<b||(e-b)%4||(e-b)/4>64)return false;
        for(uint32_t p=b;p<e;p+=4){uint32_t v=0;if(!word(m,p,v))return false;if(v==egg)return true;}
        return false;
    }
    void note_seen(const Entry& e) noexcept {
        for(size_t i=0;i<seen_count_;++i)if(seen_[i].id==e.id)return;
        if(seen_count_<seen_.size()){seen_[seen_count_++]=e;seen_changed_=true;}
    }
    std::array<uint32_t,96> probed_{};size_t probed_count_=0;
    static void hex(std::string& out,uint32_t v){char b[12];std::snprintf(b,sizeof(b),"\"%08x\"",v);out+=b;}
public:
    void reset() noexcept {cache_={};next_=0;seen_={};seen_count_=0;seen_changed_=false;probed_={};probed_count_=0;}
    // Diagnostics=1 only: one record per new UI-draw entity per race (bounded), for the child-entity link research
    // (PC enUIText / gaHudTimeDiffsAi draw through unnamed child entities). Read-only.
    bool probe_json(RaceReadMemory& m,uint32_t base,uintptr_t entity,float x,float y,std::string& out) {
        if(!entity||entity>0x7ffffffc||(entity&3)||probed_count_>=probed_.size())return false;
        const auto e=static_cast<uint32_t>(entity);
        for(size_t i=0;i<probed_count_;++i)if(probed_[i]==e)return false;
        probed_[probed_count_++]=e;
        const auto r=resolve(m,base,entity);
        uint32_t id=0;word(m,e+0x5c,id);
        char head[160];std::snprintf(head,sizeof(head),"{\"type\":\"ps2_hud_entity\",\"entity\":\"%08x\",\"id\":%u,\"name\":\"%s\",\"x\":%.1f,\"y\":%.1f,\"bytes\":\"",e,id,r.name,x,y);
        out=head;
        for(uint32_t o=0;o<0x80;o+=4){uint32_t v=0;char b[10];std::snprintf(b,sizeof(b),"%08x",word(m,e+o,v)?v:0xdeadbeefu);out+=b;if(o+4<0x80)out+=' ';}
        out+="\",\"lists\":[";
        for(uint32_t k=0;k<4;++k){
            if(k)out+=',';out+='[';
            const uint32_t h=e+0x18+12*k;uint32_t node=0;bool first=true;
            if(word(m,h+4,node))for(int n=0;n<4&&node&&node!=h;++n){
                uint32_t owner=0,vt=0,next=0;word(m,node,owner);if(owner)word(m,owner,vt);
                if(!first)out+=',';first=false;out+='[';hex(out,node);out+=',';hex(out,owner);out+=',';hex(out,vt);out+=']';
                if(!word(m,node+4,next))break;node=next;
            }
            out+=']';
        }
        out+="]}";return true;
    }
    // Name of the egg that owns the current UI draw; Unknown unless id, registry and liveness all agree.
    Entry resolve(RaceReadMemory& m,uint32_t base,uintptr_t entity) noexcept {
        Entry none{};
        if(!entity||entity>0x7ffffffc||(entity&3))return none;
        const auto egg=static_cast<uint32_t>(entity);uint32_t id=0;uint8_t flags=0;
        if(!word(m,egg+0x5c,id)||!id||!m.read(egg,&flags,1)||(flags&2))return none;
        for(const auto& c:cache_)if(c.egg==egg&&c.id==id)return c;
        Entry e{};e.egg=egg;e.id=id;
        if(!registered(m,base,egg,id)||!race_pool_text(m,base,id,e.name,sizeof(e.name)))return none;
        for(char c:e.name){if(!c)break;if(c<0x20||c>=0x7f)return none;}
        e.role=hud_egg_role_for_name(e.name);
        cache_[next_]=e;next_=(next_+1)%cache_.size();note_seen(e);
        return e;
    }
    // Diagnostics: the distinct names seen since the last reset, once after the set grows.
    bool take_seen_json(std::string& out) {
        if(!seen_changed_)return false;seen_changed_=false;
        out="{\"type\":\"ps2_hud_eggs\",\"names\":[";
        for(size_t i=0;i<seen_count_;++i){if(i)out+=',';out+='"';out+=seen_[i].name;out+='"';}
        out+="]}";return true;
    }
};

}  // namespace gfx2::ps2port
