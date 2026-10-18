#pragma once
// PS2HudTimeDiffs=1: the PS2 gaHudTimeDiffs2Ai opponent list in place of the PC gaHudTimeDiffsAi rows.
//
// Evidence: ps2-research/hud-dump1/findings.md "TimeDiffs" (EE 0x1502a8 init, 0x151120 tick, 0x150d18 diff,
// 0x150b28 row; GS dumps 20261018 110543 practice / 111758 four-car race).
//   * fewer than two cars: no rows (practice shows nothing);
//   * every 50 Hz frame each car stamps the local race time into its per-RaceLine-marker table at its LastMarker;
//   * every 40 frames each car's gap to the local car is recomputed, put in Rank order, made monotonic, and drawn:
//     row r (y = egg y - 15r) = car icon (SmallCarSheet[car table[CarType]]) + "%.2f" at +35 in font 102
//     (ARIAL_16), green (0.5,1,0.5) when ahead, red (1,0.5,0.5) when behind, white "--.--" for the local car or 0.
// The PC rows (unnamed child entities of the TimeDiffs egg's gaHudTimeDiffsAi, AI +0xc/+0x10/+0x14) are hidden by
// exact identity: egg name "TimeDiffs" in the egg registry -> egg+4 = AI with vtable base+0x291058 -> children.
#include "ps2_hud_damage_feed.hpp"
#include "ps2_hud_template.hpp"
#include "ps2_hud_eggs.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace gfx2::ps2port {

inline constexpr char kHudTimeDiffsPackSha[]="9b175c15388f1cfaf4feb201e05c89eae1af4d79a59ba46b4600dd3c77cba332";
// PS2 car table (EE 0x116f88): car id -> SmallCarSheet image (+0x18).
inline constexpr std::array<int,29> kPs2CarSmallImage={9,17,22,15,1,16,20,13,18,7,4,24,19,14,26,3,25,0,5,11,10,2,27,6,8,28,29,21,23};
// The same table's car names (EE 0x116f88 string arguments), in car id order. The PC Broker stores
// Race/Car%d/CarType as one of these names (tag 4, pool string id; PC 0x4c0b38 -> 0x4d6c00 -> 0x4ddb30).
inline constexpr std::array<const char*,29> kPs2CarNames={"Landcruiser","Pajero","Tata","Terrano","Chevyblazer","Xtrail","Frontera","Navara",
    "Forester","Jump","Wooldand","Rmonster","Patrol","Newrav","Kiasportage","Wildcat","Simmbugghini","Astero","Kangoo","Megane","Mattserati",
    "Bruno","SeatBuggy","Kamaz","Icecream","Ufo","Forklift","Moonbuggy","Tank"};
inline int ps2_car_id(const char* name) noexcept {
    if(!name)return -1;
    for(size_t i=0;i<kPs2CarNames.size();++i){
        const char* a=kPs2CarNames[i];const char* b=name;
        while(*a&&*b&&((*a|0x20)==(*b|0x20))){++a;++b;}
        if(!*a&&!*b)return int(i);
    }
    return -1;
}
inline constexpr uint32_t kPcTimeDiffsAiVtableRva=0x291058;   // gaHudTimeDiffsAi (MRallye.exe 0x691058)
inline constexpr float kTimeDiffsRowPitch=15.f,kTimeDiffsTextX=35.f,kTimeDiffsIconY=-4.f;
inline constexpr float kPs2TimeDiffsX=22.f,kPs2TimeDiffsY=365.f;  // PS2 HUD0.XML TimeDiffs egg
inline constexpr float kPcTimeDiffsX=20.f,kPcTimeDiffsY=380.f;    // PC Hud0.xml TimeDiffs egg (rows at y-15k)

struct HudSprite { uint8_t key=0,page=0xff; float x0=0,y0=0,x1=0,y1=0,u0=0,v0=0,u1=0,v1=0; };
struct HudTimeDiffsArt {
    std::vector<std::vector<DWORD>> pages;
    std::vector<HudSprite> glyphs;
    std::array<HudSprite,30> icons{};
    std::array<std::string,30> pc_icon_sha;
    const HudSprite* glyph(char c) const noexcept {for(const auto& g:glyphs)if(g.key==uint8_t(c))return &g;return nullptr;}
};

inline bool decode_hud_timediffs_pack(const std::vector<uint8_t>& b,HudTimeDiffsArt& art) noexcept {
    try{
        art=HudTimeDiffsArt{};
        if(b.size()<16||sha256_bytes(b.data(),b.size())!=kHudTimeDiffsPackSha)return false;
        size_t o=0;auto need=[&](size_t n){return o+n<=b.size();};
        auto u32=[&](){uint32_t v=0;std::memcpy(&v,b.data()+o,4);o+=4;return v;};
        auto sprite=[&](HudSprite& s){s.key=b[o];s.page=b[o+1];o+=2;float f[8];std::memcpy(f,b.data()+o,32);o+=32;
            s.x0=f[0];s.y0=f[1];s.x1=f[2];s.y1=f[3];s.u0=f[4];s.v0=f[5];s.u1=f[6];s.v1=f[7];};
        if(std::memcmp(b.data(),"MRTD",4))return false;o=4;if(u32()!=1)return false;
        const uint32_t pages=u32();if(pages==0||pages>16||!need(size_t(pages)*64*64*4))return false;
        art.pages.resize(pages);
        for(auto& p:art.pages){p.resize(64*64);std::memcpy(p.data(),b.data()+o,64*64*4);o+=64*64*4;}
        if(!need(4))return false;const uint32_t glyphs=u32();if(glyphs>64||!need(size_t(glyphs)*34))return false;
        art.glyphs.resize(glyphs);for(auto& g:art.glyphs){sprite(g);if(g.page>=pages)return false;}
        if(!need(4)||u32()!=30||!need(30*34+30*32))return false;
        for(auto& i:art.icons){sprite(i);if(i.page!=0xff&&i.page>=pages)return false;}
        for(auto& s:art.pc_icon_sha){s=hud_hex(b.data()+o,32);o+=32;}
        return o==b.size();
    }catch(...){art=HudTimeDiffsArt{};return false;}
}

// ---------------------------------------------------------------- live feed (read only)
struct TimeDiffsCar { float progress=0; int rank=0,last_marker=0,car_type=-1; bool exists=false; };
struct TimeDiffsInput {
    bool ok=false; int count=0,local=-1,markers=0; float local_time=0;
    std::array<TimeDiffsCar,8> cars{};
    const char* reason="not_read";
};

class TimeDiffsFeedReader {
    uint64_t generation_=0;bool ids_ok_=false;int count_=0,local_=-1;
    std::array<uint32_t,8> car_{},progress_{},rank_{},marker_{},type_{};uint32_t time_=0,raceline_=0;
    const char* id_reason_="not_resolved";
    static bool word(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return a&&!(a&3)&&m.read(a,&v,4);}
    static bool pointer(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return word(m,a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);}
    // Broker record [id, payload, tag]: tag 1 = float, 2 = int, 10 = object (PC 0x4d6650 / PS2 0x1e3610/3650/4d70).
    static bool record(RaceReadMemory& m,uint32_t base,uint32_t id,uint32_t tag,uint32_t& payload) noexcept {
        uint32_t manager=0,begin=0,end=0,native=0,t=0;
        if(!pointer(m,base+kHudBrokerRva,manager)||!pointer(m,manager+4,begin)||!word(m,manager+8,end)||end<begin||(end-begin)%0x1c||id>=(end-begin)/0x1c)return false;
        const uint32_t r=begin+id*0x1c;
        return word(m,r,native)&&native==id&&word(m,r+8,t)&&t==tag&&pointer(m,r+4,payload);
    }
    static bool real(RaceReadMemory& m,uint32_t base,uint32_t id,float& v) noexcept {uint32_t p=0;return record(m,base,id,1,p)&&m.read(p,&v,4)&&std::isfinite(v);}
    static bool integer(RaceReadMemory& m,uint32_t base,uint32_t id,int& v) noexcept {uint32_t p=0;return record(m,base,id,2,p)&&m.read(p,&v,4);}
    // Tag 4 string: the payload holds a pool string id.
    static bool text(RaceReadMemory& m,uint32_t base,uint32_t id,char* out,size_t n) noexcept {
        uint32_t p=0,sid=0;return record(m,base,id,4,p)&&word(m,p,sid)&&sid&&race_pool_text(m,base,sid,out,n);
    }
    bool resolve(RaceReadMemory& m,uint32_t base) noexcept {
        ids_ok_=false;count_=0;local_=-1;
        uint32_t id=0;if(!m.resolve_id(base,"Race/NumCars",id)){id_reason_="num_cars_key_missing";return false;}
        const auto n=race_broker_scalar(m,base,id,2);if(!n.present||n.value<1||n.value>8){id_reason_="num_cars_unreadable";return false;}
        int locals=0;
        for(int i=0;i<n.value;++i){
            char key[64]{};uint32_t pt=0;std::snprintf(key,sizeof(key),"Race/Car%d/PlayerType",i);
            if(!m.resolve_id(base,key,pt)){id_reason_="player_type_key_missing";return false;}
            const auto t=race_broker_scalar(m,base,pt,2);if(!t.present){id_reason_="player_type_unreadable";return false;}
            if(t.value==1){++locals;local_=i;}
            const struct {const char* fmt;uint32_t* out;} keys[]={{"Car%d",&car_[i]},{"Race/Car%d/Progress",&progress_[i]},{"Race/Car%d/Rank",&rank_[i]},
                {"Race/Car%d/LastMarker",&marker_[i]},{"Race/Car%d/CarType",&type_[i]}};
            for(const auto& k:keys){std::snprintf(key,sizeof(key),k.fmt,i);if(!m.resolve_id(base,key,*k.out)){id_reason_="car_key_missing";return false;}}
        }
        if(locals!=1){id_reason_="single_local_player_unproven";return false;}
        char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%d/Time",local_);
        if(!m.resolve_id(base,key,time_)||!m.resolve_id(base,"RaceLine",raceline_)){id_reason_="time_or_raceline_key_missing";return false;}
        count_=n.value;ids_ok_=true;id_reason_="ids_resolved";return true;
    }
    // RaceLine marker count (marker manager base+0x2f94e4: lists by pool id, records 0x48).
    static bool marker_count(RaceReadMemory& m,uint32_t base,uint32_t id,int& count) noexcept {
        uint32_t mgr=0,lb=0,le=0,list=0,b=0,e=0;
        if(!pointer(m,base+0x2f94e4,mgr)||!pointer(m,mgr+4,lb)||!word(m,mgr+8,le)||le<lb||(le-lb)%4||id>=(le-lb)/4)return false;
        if(!pointer(m,lb+id*4,list)||!pointer(m,list+4,b)||!word(m,list+8,e)||e<b||(e-b)%0x48)return false;
        count=int((e-b)/0x48);return count>0&&count<100000;
    }
public:
    TimeDiffsInput read(RaceReadMemory& m,uint32_t base,uint64_t race_generation) noexcept {
        TimeDiffsInput in;
        if(!race_generation){in.reason="no_race_generation";return in;}
        if(race_generation!=generation_){generation_=race_generation;resolve(m,base);}
        if(!ids_ok_){in.reason=id_reason_;return in;}
        in.count=count_;in.local=local_;
        if(!marker_count(m,base,raceline_,in.markers)){in.reason="raceline_unreadable";return in;}
        if(!real(m,base,time_,in.local_time)){in.reason="local_time_unreadable";return in;}
        for(int i=0;i<count_;++i){
            auto& c=in.cars[i];uint32_t object=0;c.exists=record(m,base,car_[i],10,object);
            if(!real(m,base,progress_[i],c.progress)){in.reason="car_progress_unreadable";return in;}
            if(!integer(m,base,rank_[i],c.rank)){in.reason="car_rank_unreadable";return in;}
            if(!integer(m,base,marker_[i],c.last_marker)){in.reason="car_last_marker_unreadable";return in;}
            char name[40]{};c.car_type=text(m,base,type_[i],name,sizeof(name))?ps2_car_id(name):-1;   // no icon when unknown
            if(c.rank<1||c.rank>count_){in.reason="rank_out_of_range";return in;}
        }
        in.ok=true;in.reason="live_time_diffs";return in;
    }
};

// ---------------------------------------------------------------- PS2 model (pure)
struct TimeDiffsRow { int car=-1; float value=0; };
class TimeDiffsModel {
    uint64_t generation_=0;int count_=0,markers_=0;
    std::vector<float> stamps_;      // count x markers, PS2 +0xa4
    std::array<float,8> progress_{}; // PS2 +0x70
    std::array<int,8> order_{};      // Rank-1, PS2 +0x94
    std::array<float,8> by_row_{};
    int frames_=0;float pending_=0,dat_48dd30_=0;bool shown_=false;
    float& stamp(int car,int marker) noexcept {return stamps_[size_t(car)*markers_+marker];}
    // EE 0x150d18: gap of car i to the local car (positive: car i ahead).
    float diff(const TimeDiffsInput& in,int i,int local,int local_marker) noexcept {
        if(!in.cars[i].exists)return 0.f;
        if(progress_[i]<progress_[local]){
            const int m=std::clamp(in.cars[i].last_marker,0,markers_-1);const float own=stamp(i,m);
            for(int k=0;k<8;++k){
                const float ahead=m+k<markers_?stamp(local,m+k):0.f;if(ahead!=0.f)return ahead-own;
                const float back=m-k>=0?stamp(local,m-k):0.f;if(back!=0.f)return back-own;
            }
        }else{
            const int m=local_marker;
            for(int k=0;k<8;++k){
                const float ahead=m+k<markers_?stamp(i,m+k):0.f;if(ahead!=0.f)return in.local_time-ahead;
                const float back=m-k>=0?stamp(i,m-k):0.f;if(back!=0.f)return in.local_time-back;
            }
        }
        return 0.f;
    }
    void recompute(const TimeDiffsInput& in) noexcept {
        const int local=in.local,lm=std::clamp(in.cars[local].last_marker,0,markers_-1);
        std::array<float,8> d{};
        for(int i=0;i<count_;++i)progress_[i]=in.cars[i].progress;
        for(int i=0;i<count_;++i){const float v=diff(in,i,local,lm);d[i]=i==local?0.f:v;order_[i]=in.cars[i].rank-1;}
        if(local==0){                        // EE 0x151120 car-0 branch (shared with the second HUD)
            if(count_>1&&d[1]>0.f){dat_48dd30_=d[1];d[0]=0.f;}
            else if(count_>1){const int m1=std::clamp(in.cars[1].last_marker,0,markers_-1);d[1]=-diff(in,0,1,m1);d[0]=0.f;dat_48dd30_=d[1];}
        }else{d[0]=-dat_48dd30_;if(count_>1)d[1]=0.f;}
        std::array<float,32> a{};
        for(int i=0;i<count_;++i)a[size_t(order_[i])]=d[i];
        const int lr=order_[local];
        for(int r=0;r+1<count_;++r){
            if(a[r]<a[r+1])a[r+1]=a[r]-(a[r+1]-a[r])*.25f;
            if(r<lr&&a[r]<0.f)a[r]=0.f;else if(r>lr&&a[r]>0.f)a[r]=0.f;
        }
        for(int r=0;r<count_;++r)by_row_[r]=a[r];
        shown_=true;
    }
public:
    void reset() noexcept {*this=TimeDiffsModel{};}
    // dt in seconds; the PS2 runs this per 50 Hz frame.
    void update(const TimeDiffsInput& in,uint64_t generation,float dt) noexcept {
        if(!in.ok||in.count<2||in.local<0||in.local>=in.count||in.markers<1){shown_=false;return;}
        if(generation!=generation_||in.count!=count_||in.markers!=markers_){
            reset();generation_=generation;count_=in.count;markers_=in.markers;stamps_.assign(size_t(count_)*markers_,0.f);
        }
        pending_+=std::clamp(dt,0.f,.25f);
        int steps=0;
        while(pending_>=.02f&&steps<12){
            pending_-=.02f;++steps;
            for(int i=0;i<count_;++i){const int m=std::clamp(in.cars[i].last_marker,0,markers_-1);if(stamp(i,m)==0.f)stamp(i,m)=in.local_time;}
            if(++frames_%40==0)recompute(in);
        }
    }
    bool shown() const noexcept {return shown_;}
    int count() const noexcept {return count_;}
    // Row r shows the car whose Rank is r+1 with the rank-ordered value.
    std::vector<TimeDiffsRow> rows(const TimeDiffsInput& in) const {
        std::vector<TimeDiffsRow> out;if(!shown_)return out;
        for(int i=0;i<count_;++i){const int r=order_[i];if(r<0||r>=count_)return {};out.resize(std::max<size_t>(out.size(),size_t(r)+1));out[size_t(r)]={i,by_row_[r]};}
        (void)in;return out;
    }
};

// Text and colour of one row (EE 0x150b28).
inline std::string time_diff_text(int car,int local,float value){
    if(car==local||value==0.f)return "--.--";
    char b[32];std::snprintf(b,sizeof(b),"%.2f",value);return b;
}
inline DWORD time_diff_colour(int car,int local,float value) noexcept {
    if(car==local||value==0.f)return 0xffffffffu;
    return value>0.f?0xff7fff7fu:0xffff7f7fu;
}

// ---------------------------------------------------------------- PC rows (exact identity)
// Egg "TimeDiffs" (unique in the egg registry, not retired, +0x5c = its name id) -> egg+4 = gaHudTimeDiffsAi
// (vtable base+0x291058; the baseline reads egg+4 the same way for RaceLimits) -> rows at AI +0xc/+0x10/+0x14
// (PC 0x4ab040: row k at the egg's y - 15k, k = 0 car ahead, 1 local, 2 car behind).
class PcTimeDiffsRows {
    uint64_t generation_=0;uint32_t name_id_=0;bool name_ok_=false;
    std::array<uint32_t,3> rows_{};bool ok_=false;const char* reason_="not_resolved";
    static bool word(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return a&&!(a&3)&&m.read(a,&v,4);}
    static bool pointer(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return word(m,a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);}
public:
    bool ok() const noexcept {return ok_;}
    const char* reason() const noexcept {return reason_;}
    int row_of(uintptr_t entity) const noexcept {if(!ok_||!entity)return -1;for(int k=0;k<3;++k)if(rows_[size_t(k)]==entity)return k;return -1;}
    bool refresh(RaceReadMemory& m,uint32_t base,uint64_t generation) noexcept {
        ok_=false;rows_={};
        if(generation!=generation_){generation_=generation;name_ok_=m.resolve_id(base,"TimeDiffs",name_id_);}
        if(!name_ok_){reason_="time_diffs_name_unresolved";return false;}
        uint32_t manager=0,registry=0,begin=0,end=0,bucket=0,b=0,e=0,egg=0,id=0,ai=0,vtable=0;uint8_t flags=0;
        if(!pointer(m,base+kHudEggManagerRva,manager)||!pointer(m,manager+0x1c,registry)||!word(m,registry+4,begin)||!word(m,registry+8,end)||
           !begin||end<begin||(end-begin)%4||name_id_>=(end-begin)/4||!pointer(m,begin+name_id_*4,bucket)||!word(m,bucket+4,b)||!word(m,bucket+8,e)||
           e!=b+4){reason_="time_diffs_egg_not_unique";return false;}
        if(!pointer(m,b,egg)||!word(m,egg+0x5c,id)||id!=name_id_||!m.read(egg,&flags,1)||(flags&2)){reason_="time_diffs_egg_invalid";return false;}
        if(!pointer(m,egg+4,ai)||!word(m,ai,vtable)||vtable!=base+kPcTimeDiffsAiVtableRva){reason_="time_diffs_ai_type_mismatch";return false;}
        for(uint32_t k=0;k<3;++k){uint32_t row=0;if(!pointer(m,ai+0xc+4*k,row)){reason_="time_diffs_rows_missing";return false;}rows_[k]=row;}
        ok_=true;reason_="pc_time_diffs_rows";return true;
    }
};

// ---------------------------------------------------------------- feature
class PS2HudTimeDiffs {
    bool requested_=false,disabled_=false;
    HudTimeDiffsArt art_;
    std::vector<IDirect3DTexture8*> pages_;
    const char* startup_reason_=nullptr;
    TimeDiffsModel model_;
    PcTimeDiffsRows rows_;
    bool hide_rows_=false;            // last Present: PS2 list owns the slot (live feed)
    HudPlacement placement_{};int placement_row_=-1;bool placement_seen_=false;
    int pc_local_icon_=-1;            // PC SmallCarSheet image of the local row (self-check of the car table)
    std::array<HudPcIdentity,16> identities_{};size_t next_identity_=0;
    uint64_t hidden_=0;long long last_qpc_=0;
public:
    PS2HudLayer layer;
    PS2HudTimeDiffs(bool supported,const std::wstring& ini) noexcept {
        if(!supported)return;
        try{
            if(config::read_int(L"PS2HudTimeDiffs",0,ini.c_str())!=1)return;
            wchar_t folder[32768]{};
            config::read_string(L"PS2HudAssetDir",L"PS2Hud",folder,32768,ini.c_str());
            auto dir=std::filesystem::path(folder);if(dir.is_relative())dir=std::filesystem::path(ini).parent_path()/dir;
            std::ifstream file(dir/L"PS2HudTimeDiffs.bin",std::ios::binary);
            std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
            requested_=decode_hud_timediffs_pack(bytes,art_);
            if(!requested_)startup_reason_="hud_time_diffs_asset_missing_or_mismatch";
        }catch(...){requested_=false;}
    }
    ~PS2HudTimeDiffs(){release();}
    PS2HudTimeDiffs(const PS2HudTimeDiffs&)=delete;
    PS2HudTimeDiffs& operator=(const PS2HudTimeDiffs&)=delete;
    bool requested() const noexcept {return requested_&&!disabled_;}
    void disable() noexcept {disabled_=true;}
    const char* take_startup_reason() noexcept {const char* r=startup_reason_;startup_reason_=nullptr;return r;}
    bool hide_rows() const noexcept {return requested()&&hide_rows_;}
    const PcTimeDiffsRows& rows() const noexcept {return rows_;}
    uint64_t hidden() const noexcept {return hidden_;}
    int pc_local_icon() const noexcept {return pc_local_icon_;}
    void release() noexcept {for(auto*& p:pages_){if(p)p->Release();p=nullptr;}pages_.clear();}
    bool initialize(IDirect3DDevice8& n) noexcept {
        if(!pages_.empty())return true;
        if(!requested())return false;
        for(const auto& px:art_.pages){
            IDirect3DTexture8* t=nullptr;
            if(FAILED(n.CreateTexture(64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&t))||!t){release();disable();return false;}
            pages_.push_back(t);D3DLOCKED_RECT lock{};
            if(FAILED(t->LockRect(0,&lock,nullptr,0))){release();disable();return false;}
            const bool good=lock.pBits&&lock.Pitch>=64*4;
            if(good)for(UINT y=0;y<64;++y)std::memcpy(static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,px.data()+size_t(y)*64,64*4);
            if(FAILED(t->UnlockRect(0))||!good){release();disable();return false;}
        }
        return true;
    }
    float tick(long long now,long long frequency) noexcept {
        const float dt=last_qpc_&&frequency>0?float(double(now-last_qpc_)/double(frequency)):.02f;last_qpc_=now;return dt;
    }
    void refresh_rows(RaceReadMemory& m,uint32_t base,uint64_t generation) noexcept {rows_.refresh(m,base,generation);}
    // A PC row draw is taken over: keep the first placement of the frame and check the local row's car icon.
    void note_pc_row(int row,const HudPlacement& p,IDirect3DBaseTexture8* texture,uint64_t generation) noexcept {
        ++hidden_;
        if(!placement_seen_&&p.valid){placement_=p;placement_row_=row;placement_seen_=true;}
        if(row!=1||!texture||!generation)return;
        const auto id=reinterpret_cast<uintptr_t>(texture);
        for(const auto& c:identities_)if(c.texture==id&&c.generation==generation){if(c.index>=0)pc_local_icon_=c.index;return;}
        HudPcIdentity r{id,generation,-1,"not_pc_small_car"};
        if(texture->GetType()==D3DRTYPE_TEXTURE){
            auto* t=static_cast<IDirect3DTexture8*>(texture);D3DSURFACE_DESC desc{};
            if(SUCCEEDED(t->GetLevelDesc(0,&desc))&&desc.Width==32&&desc.Height==16&&desc.Pool!=D3DPOOL_DEFAULT&&
               (desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8)){
                D3DLOCKED_RECT lock{};
                if(SUCCEEDED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY))){
                    const auto sha=hud_level0_sha(static_cast<const BYTE*>(lock.pBits),lock.Pitch,32,16,desc.Format);t->UnlockRect(0);
                    for(int k=0;k<30;++k)if(sha==art_.pc_icon_sha[size_t(k)]){r.index=k;r.reason="exact_pc_small_car";break;}
                }
            }
        }
        identities_[next_identity_]=r;next_identity_=(next_identity_+1)%identities_.size();
        if(r.index>=0)pc_local_icon_=r.index;
    }
    // Present: model update and the PS2 rows for this frame. reason reports the outcome.
    std::vector<HudTexQuad> frame(const TimeDiffsInput& in,uint64_t generation,float dt,const char*& reason) {
        std::vector<HudTexQuad> quads;
        const HudPlacement p=placement_;const int pc_row=placement_row_;const bool seen=placement_seen_;
        placement_seen_=false;placement_row_=-1;
        hide_rows_=in.ok&&rows_.ok();
        if(!in.ok){model_.reset();reason=in.reason;return quads;}
        if(!rows_.ok()){reason=rows_.reason();return quads;}
        model_.update(in,generation,dt);
        if(in.count<2){reason="single_car_no_list";return quads;}
        if(!model_.shown()){reason="waiting_first_update";return quads;}
        if(!seen||!p.valid){reason="no_pc_row_this_frame";return quads;}
        const int local_type=in.cars[size_t(in.local)].car_type;
        const bool icons=local_type>=0&&local_type<int(kPs2CarSmallImage.size())&&(pc_local_icon_<0||pc_local_icon_==kPs2CarSmallImage[size_t(local_type)]);
        const float inset=.5f/64.f;
        auto put=[&](const HudSprite& s,float ox,float oy,DWORD colour){   // s: PSB local box (y down), o: authored y-up
            float xs[2],ys[2];
            if(!hud_project(p,ox+s.x0,oy-s.y0,xs[0],ys[0])||!hud_project(p,ox+s.x1,oy-s.y1,xs[1],ys[1]))return;
            HudTexQuad q;q.rect={std::fmin(xs[0],xs[1]),std::fmin(ys[0],ys[1]),std::fmax(xs[0],xs[1]),std::fmax(ys[0],ys[1])};
            q.page=s.page;q.color=colour;
            q.u0=s.u0+(s.u1>s.u0?inset:-inset);q.u1=s.u1-(s.u1>s.u0?inset:-inset);
            q.v0=s.v0+(s.v1>s.v0?inset:-inset);q.v1=s.v1-(s.v1>s.v0?inset:-inset);
            if(q.rect.r>q.rect.l&&q.rect.b>q.rect.t)quads.push_back(q);
        };
        const auto rows=model_.rows(in);
        for(size_t r=0;r<rows.size();++r){
            const int car=rows[r].car;if(car<0)continue;
            // Local frame of the captured PC row k: origin (20, 380-15k); PS2 row r origin (22, 365-15r).
            const float ox=kPs2TimeDiffsX-kPcTimeDiffsX,oy=(kPs2TimeDiffsY-kTimeDiffsRowPitch*float(r))-(kPcTimeDiffsY-kTimeDiffsRowPitch*float(pc_row));
            const int type=in.cars[size_t(car)].car_type;
            if(icons&&type>=0&&type<int(kPs2CarSmallImage.size())){
                const auto& icon=art_.icons[size_t(kPs2CarSmallImage[size_t(type)])];
                if(icon.page!=0xff)put(icon,ox,oy+kTimeDiffsIconY,0xffffffffu);
            }
            const std::string text=time_diff_text(car,in.local,rows[r].value);
            const DWORD colour=time_diff_colour(car,in.local,rows[r].value);
            float pen=ox+kTimeDiffsTextX;
            for(char c:text){const auto* g=art_.glyph(c);if(!g)continue;put(*g,pen-g->x0,oy,colour);pen+=g->x1-g->x0;}
        }
        reason=icons?"ps2_time_diffs":"ps2_time_diffs_icons_off_car_table_mismatch";
        return quads;
    }
    const std::vector<IDirect3DTexture8*>& pages() const noexcept {return pages_;}
};

}  // namespace gfx2::ps2port
