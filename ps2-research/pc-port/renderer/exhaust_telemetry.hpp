#pragma once
// FX-EXHAUST1 step 2: engine telemetry of the cars that have SDK supplemental audio (roster payload, v-cap
// tools/native_audio/layers.c). The audio helper owns a RW page that starts with the magic "MRSFXTL1" (version 1,
// 64 records of 48 bytes, one per audio slot): owner, tick, world position of the car entity, omega / rev limit, load
// proxy, gear, lift-off count (the same events that fire the pop / anti-lag sound), limiter flag, sequence.
// The renderer finds the page by its magic in the roster extension (0x10000000.., read/write pages only), and matches
// each fresh record to the nearest car pose. Read only: nothing is written to game memory.
#include <windows.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace gfx2::exhaust {
struct Record {uint32_t owner,tick;float pos[3],ratio,load;uint32_t gear,lifts,limiter,seq,reserved;};
static_assert(sizeof(Record)==48,"telemetry record layout");
constexpr char kMagic[8]={'M','R','S','F','X','T','L','1'};
constexpr uintptr_t kScanBegin=0x10000000,kScanEnd=0x10800000;
constexpr unsigned kRecords=64,kHeader=32;

// Per car instance: latest engine state and the lift-off events not yet consumed by an effect.
struct CarEngine {uintptr_t instance=0;uint64_t frame=UINT64_MAX;float ratio=0,load=0;uint32_t gear=0,limiter=0,pending_lifts=0;};

struct Reader {
    uintptr_t page=0;uint64_t next_scan=0,last_frame=UINT64_MAX,log_frame=0;
    std::array<uint32_t,kRecords> seq{},owner{},lifts{};
    std::array<CarEngine,24> cars{};
    uint64_t scans=0,fresh=0,matched=0,unmatched=0,events=0;float worst_match=0;
    float sample_pos[3]{},sample_pose[3]{};float sample_distance=-1;
};
inline Reader& reader() noexcept {static Reader r;return r;}

inline bool writable_page(const void* at) noexcept {
    MEMORY_BASIC_INFORMATION mi{};
    if(!VirtualQuery(at,&mi,sizeof mi)||mi.State!=MEM_COMMIT||(mi.Protect&(PAGE_GUARD|PAGE_NOACCESS)))return false;
    return (mi.Protect&0xff)==PAGE_READWRITE&&reinterpret_cast<uintptr_t>(at)+4096<=reinterpret_cast<uintptr_t>(mi.BaseAddress)+mi.RegionSize;
}
inline bool page_valid(uintptr_t q) noexcept {
    if(!writable_page(reinterpret_cast<const void*>(q)))return false;
    uint32_t version=0,count=0;std::memcpy(&version,reinterpret_cast<const void*>(q+8),4);std::memcpy(&count,reinterpret_cast<const void*>(q+12),4);
    return !std::memcmp(reinterpret_cast<const void*>(q),kMagic,8)&&version==1&&count==kRecords;
}
inline uintptr_t scan() noexcept {
    for(uintptr_t a=kScanBegin;a<kScanEnd;){
        MEMORY_BASIC_INFORMATION mi{};if(!VirtualQuery(reinterpret_cast<const void*>(a),&mi,sizeof mi))break;
        const uintptr_t base=reinterpret_cast<uintptr_t>(mi.BaseAddress),end=base+mi.RegionSize;
        if(mi.State==MEM_COMMIT&&!(mi.Protect&(PAGE_GUARD|PAGE_NOACCESS))&&(mi.Protect&0xff)==PAGE_READWRITE)
            for(uintptr_t q=base;q+4096<=end;q+=4096)if(page_valid(q))return q;
        a=end>a?end:a+4096;
    }
    return 0;
}
inline CarEngine* car(uintptr_t instance) noexcept {for(auto& c:reader().cars)if(c.instance==instance)return &c;return nullptr;}

// poses: callable(visit) that calls visit(instance, x, y, z) for every car pose current in this frame.
template<class Poses> inline void update(uint64_t frame,Poses&& poses) noexcept {
    auto& r=reader();if(r.last_frame==frame)return;r.last_frame=frame;
    if(r.page&&!page_valid(r.page))r.page=0;
    if(!r.page){if(frame<r.next_scan)return;r.next_scan=frame+300;++r.scans;r.page=scan();if(!r.page)return;r.seq.fill(0);r.owner.fill(0);r.lifts.fill(0);}
    for(unsigned i=0;i<kRecords;++i){
        Record rec{};std::memcpy(&rec,reinterpret_cast<const void*>(r.page+kHeader+i*sizeof(Record)),sizeof rec);
        if(!rec.owner||rec.seq==r.seq[i])continue;
        const bool same=r.owner[i]==rec.owner;const uint32_t before=r.lifts[i];
        r.seq[i]=rec.seq;r.owner[i]=rec.owner;r.lifts[i]=rec.lifts;++r.fresh;
        uintptr_t best=0;float best_d=1e30f,bx=0,by=0,bz=0;
        poses([&](uintptr_t instance,float x,float y,float z){const float dx=x-rec.pos[0],dy=y-rec.pos[1],dz=z-rec.pos[2],d=dx*dx+dy*dy+dz*dz;
            if(d<best_d){best_d=d;best=instance;bx=x;by=y;bz=z;}});
        std::memcpy(r.sample_pos,rec.pos,12);r.sample_pose[0]=bx;r.sample_pose[1]=by;r.sample_pose[2]=bz;r.sample_distance=best?std::sqrt(best_d):-1;
        if(!best||best_d>9.f){++r.unmatched;continue;}
        ++r.matched;r.worst_match=std::max(r.worst_match,std::sqrt(best_d));
        CarEngine* c=car(best);
        if(!c){for(auto& s:r.cars)if(!s.instance||s.frame==UINT64_MAX||s.frame+600<frame){s=CarEngine{};s.instance=best;c=&s;break;}}
        if(!c)continue;
        c->frame=frame;c->ratio=rec.ratio;c->load=rec.load;c->gear=rec.gear;c->limiter=rec.limiter;
        if(same&&rec.lifts>before){c->pending_lifts+=rec.lifts-before;r.events+=rec.lifts-before;}
    }
}

// ---- step 3: pipe outlets (Atmosphere/vehicles/exhaust_points.txt, model frame +X left, +Y up, +Z front) ----------
struct Pipe {float pos[3],dir[3],radius;};
struct Pipes {std::wstring path;bool tried=false;std::unordered_map<std::string,std::vector<Pipe>> cars;};
inline Pipes& pipes() noexcept {static Pipes p;return p;}
inline void load_pipes(const std::wstring& lamp_rigs_path) noexcept {
    auto& p=pipes();if(p.tried&&p.path==lamp_rigs_path)return;p=Pipes{};p.path=lamp_rigs_path;p.tried=true;
    try{const auto slash=lamp_rigs_path.find_last_of(L"\\/");if(slash==std::wstring::npos)return;
        std::ifstream in(lamp_rigs_path.substr(0,slash+1)+L"exhaust_points.txt");std::string line,car;
        while(std::getline(in,line)){std::istringstream q(line);std::string tag;q>>tag;
            if(tag=="car")q>>car;
            else if(tag=="exhaust"&&!car.empty()){Pipe e{};q>>e.pos[0]>>e.pos[1]>>e.pos[2]>>e.dir[0]>>e.dir[1]>>e.dir[2]>>e.radius;
                const float l=std::sqrt(e.dir[0]*e.dir[0]+e.dir[1]*e.dir[1]+e.dir[2]*e.dir[2]);
                if(q&&std::isfinite(e.pos[0]+e.pos[1]+e.pos[2])&&l>1e-3f){for(auto& d:e.dir)d/=l;p.cars[car].push_back(e);}}}
    }catch(...){}
}

// ---- step 3: flame bursts. One lift-off event = 1..3 pops 70..110 ms apart, each visible 55 ms ---------------------
struct Burst {uintptr_t instance=0;uint64_t start=0;uint32_t pops=0,seed=0;};
struct Flames {std::array<Burst,32> bursts{};uint64_t test_next=0,started=0,drawn=0;};
inline Flames& flames() noexcept {static Flames f;return f;}
inline uint32_t mix(uint32_t x) noexcept {x^=x>>16;x*=0x7feb352dU;x^=x>>15;x*=0x846ca68bU;x^=x>>16;return x;}
inline void start_burst(uintptr_t instance,uint64_t now) noexcept {
    auto& f=flames();Burst* slot=nullptr;for(auto& b:f.bursts)if(!b.instance){slot=&b;break;}
    if(!slot)return;const uint32_t seed=mix(uint32_t(now)^uint32_t(instance)^uint32_t(++f.started*2654435761u));
    *slot=Burst{instance,now,1+seed%3,seed};
}
// intensity (0 = dark) and a per-pop size jitter of the burst at time now; retires finished bursts
inline float pop_at(Burst& b,uint64_t now,float& size) noexcept {
    if(!b.instance||now<b.start)return 0;
    uint64_t t=b.start;for(uint32_t k=0;k<b.pops;++k){const uint32_t r=mix(b.seed+k*977);
        if(now>=t&&now<t+55){const float a=float(now-t)/55.f;size=.8f+.5f*float(r&255)/255.f;return a<.25f?a/.25f:1.f-(a-.25f)/.75f*.85f;}
        t+=70+r%41;}
    if(now>=t)b.instance=0;
    return 0;
}
// strongest pop of the car's bursts now (0 = no flame): drives the flame light of the rear lamp projector
inline float flame_level(uintptr_t instance,uint64_t now) noexcept {
    float best=0;for(const auto& b:flames().bursts)if(b.instance==instance){Burst c=b;float size=1;best=std::max(best,pop_at(c,now,size));}return best;
}

// ---- step 4: smoke puffs ------------------------------------------------------------------------------------------------
struct Puff {float pos[3]{},vel[3]{},age=0,life=0,size0=0,size1=0,alpha=0;bool live=false;};
struct Smoke {std::array<Puff,384> puffs{};unsigned next=0;uint64_t tick=0;std::array<std::pair<uintptr_t,float>,24> acc{};uint64_t spawned=0;};
inline Smoke& smoke() noexcept {static Smoke s;return s;}
inline float& accumulator(uintptr_t instance) noexcept {
    auto& s=smoke();for(auto& a:s.acc)if(a.first==instance)return a.second;
    for(auto& a:s.acc)if(!a.first){a={instance,0.f};return a.second;}
    s.acc[0]={instance,0.f};return s.acc[0].second;
}
inline void spawn(const std::array<float,3>& at,const std::array<float,3>& dir,const std::array<float,3>& carvel,float strength,float size) noexcept {
    auto& s=smoke();Puff& p=s.puffs[s.next++%s.puffs.size()];const uint32_t r=mix(uint32_t(++s.spawned*2654435761u));
    auto jit=[&](unsigned k){return (float((mix(r+k)>>8)&1023)/1023.f-.5f);};
    for(unsigned i=0;i<3;++i){p.pos[i]=at[i];p.vel[i]=dir[i]*(1.1f+.6f*jit(1))+carvel[i]*.25f+.35f*jit(2+i);}
    p.age=0;p.life=1.4f+1.2f*(jit(7)+.5f);p.size0=.10f*size;p.size1=(.75f+.4f*(jit(8)+.5f))*size;p.alpha=std::clamp(strength,0.f,1.f);p.live=true;
}
inline void step(float dt) noexcept {
    const float drag=std::exp(-2.2f*dt);
    for(auto& p:smoke().puffs){if(!p.live)continue;p.age+=dt;if(p.age>=p.life){p.live=false;continue;}
        for(unsigned i=0;i<3;++i){p.vel[i]*=drag;p.pos[i]+=p.vel[i]*dt;}p.vel[1]+=.45f*dt;}
}
}  // namespace gfx2::exhaust
