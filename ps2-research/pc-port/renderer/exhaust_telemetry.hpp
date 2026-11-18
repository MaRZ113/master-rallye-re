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
}  // namespace gfx2::exhaust
