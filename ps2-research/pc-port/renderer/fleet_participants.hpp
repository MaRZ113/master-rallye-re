#pragma once
// FLEET-ALL-CARS1 (docs/fleet-all-cars/findings.md): exact per-draw race participant identity.
//
// gaBootAICar (MRallye.exe 0x4b6a00) boots egg "Car<N>" as participant N, gives its en3d (egg+0x50) the model
// "vehicles/<CarName>/car" and creates four wheel eggs "Car<N>/Wheel<i>" with model "vehicles/<CarName>/wheel".
// Each egg is the unique entry of its name pool id in the egg manager registry (base+0x2f96fc, +0x1c), the same
// registry the baseline uses to prove the RaceLimits owner. The renderer joins a draw to its egg through
// instance+0xb0 -> en3d, en3d+0x74 == instance. No position, distance or geometry heuristic is used.
//
// The table is rebuilt from live reads for every frame; pool ids are resolved once per race generation and
// re-verified by text on every use. A participant whose chain does not prove stays out of the table (Stock).
#include "race_epoch.hpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace gfx2::ps2port {

inline constexpr uint32_t kFleetEggManagerRva=0x2f96fc;
inline constexpr uint32_t kFleetBrokerRva=0x2f9410;
inline constexpr uint32_t kFleetMaxCars=8;

enum class FleetRole : uint8_t {None,Body,Wheel};

struct FleetParticipant {
    bool valid=false;const char* reason="not_resolved";
    uint32_t egg=0,en3d=0,instance=0;int32_t player_type=-1;
    std::array<uint32_t,4> wheel_egg{},wheel_en3d{},wheel_instance{};uint32_t wheel_mask=0;
    std::array<char,48> folder{};  // <CarName> of vehicles/<CarName>/car, as stored by the game
    std::array<char,64> model_text{};  // diagnostics only: a body model name that is not such a path
};

struct FleetParticipantTable {
    bool valid=false;const char* reason="not_resolved";
    uint64_t race_generation=0,owner_lifetime=0;uint32_t count=0,local=UINT32_MAX,proven=0;
    std::array<FleetParticipant,kFleetMaxCars> cars{};
    // Exactly one participant owns an instance; a wheel instance also names its wheel slot.
    bool find(uint32_t instance,uint32_t& index,FleetRole& role,unsigned& wheel) const noexcept {
        if(!valid||!instance)return false;
        for(uint32_t i=0;i<count&&i<cars.size();++i){const auto& c=cars[i];if(!c.valid)continue;
            if(c.instance==instance){index=i;role=FleetRole::Body;wheel=4;return true;}
            for(unsigned w=0;w<4;++w)if((c.wheel_mask&(1u<<w))&&c.wheel_instance[w]==instance){index=i;role=FleetRole::Wheel;wheel=w;return true;}}
        return false;
    }
};

// Case-insensitive equality of the game folder name and a fleet family ("megane", "Forester", ...).
inline bool fleet_folder_matches(const char* folder,const char* family) noexcept {
    if(!folder||!family||!*folder)return false;
    for(;*folder&&*family;++folder,++family){char a=*folder,b=*family;if(a>='A'&&a<='Z')a=char(a-'A'+'a');if(b>='A'&&b<='Z')b=char(b-'A'+'a');if(a!=b)return false;}
    return !*folder&&!*family;
}
// "vehicles<sep><name><sep><leaf>" -> name. 0x4b6f9f builds "vehicles/" + lower(<CarName>) + "/car"; the en3d
// setter stores the pool id of the 0x4d1010-normalised file name (lower case, '/' replaced by '\'), so the live
// text is "vehicles\<name>\car" (runtime PID 26308 rejected the '/'-only form for all four cars).
inline bool fleet_path_separator(char c) noexcept {return c=='/'||c=='\\';}
inline bool fleet_model_folder(const char* text,const char* leaf,std::array<char,48>& out) noexcept {
    out={};if(!text||!leaf)return false;constexpr char prefix[]="vehicles";const size_t n=std::strlen(text),p=sizeof(prefix)-1,l=std::strlen(leaf);
    if(n<=p+2+l)return false;
    for(size_t i=0;i<p;++i){char c=text[i];if(c>='A'&&c<='Z')c=char(c-'A'+'a');if(c!=prefix[i])return false;}
    // One separator style per path, as the game produces it.
    if(!fleet_path_separator(text[p])||text[n-l-1]!=text[p])return false;
    for(size_t i=0;i<l;++i){char c=text[n-l+i];if(c>='A'&&c<='Z')c=char(c-'A'+'a');if(c!=leaf[i])return false;}
    const size_t name=n-l-2-p;if(!name||name>=out.size())return false;
    for(size_t i=0;i<name;++i){const char c=text[p+1+i];if(fleet_path_separator(c)||c<0x20)return false;out[i]=c;}
    return true;
}

class FleetParticipantResolver {
public:
    struct Ids {uint32_t car=0,player_type=0;std::array<uint32_t,4> wheel{};bool car_ok=false,player_type_ok=false;std::array<bool,4> wheel_ok{};};

    // Names created after the first certified frame are looked up again, at most once per kRetryCalls.
    static constexpr uint64_t kRetryCalls=300;
    void reset() noexcept {generation_=0;owner_=0;count_=0;ids_={};incomplete_=false;}
    uint64_t id_resolutions() const noexcept {return resolutions_;}

    // max_locals: 1, or 2 for a certified split-screen race (two local drivers).
    FleetParticipantTable resolve(RaceReadMemory& m,uint32_t base,const RaceCertificate& race,unsigned max_locals=1) noexcept {
        FleetParticipantTable t;t.race_generation=race.race_generation;t.owner_lifetime=race.owner_lifetime;
        if(!race.valid||!race.race_generation||!race.owner_lifetime){t.reason="race_certificate_invalid";return t;}
        if(race.participant_count<1||race.participant_count>kFleetMaxCars){t.reason="participant_count_invalid";return t;}
        t.count=race.participant_count;
        ++calls_;
        if(generation_!=race.race_generation||owner_!=race.owner_lifetime||count_!=t.count||(incomplete_&&calls_>=retry_at_)){
            generation_=race.race_generation;owner_=race.owner_lifetime;count_=t.count;ids_={};++resolutions_;
            incomplete_=false;retry_at_=calls_+kRetryCalls;
            for(uint32_t i=0;i<t.count;++i){auto& k=ids_[i];char key[64]{};
                std::snprintf(key,sizeof(key),"Car%u",i);k.car_ok=race_pool_id(m,base,key,k.car);
                std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);k.player_type_ok=race_pool_id(m,base,key,k.player_type);
                for(unsigned w=0;w<4;++w){std::snprintf(key,sizeof(key),"Car%u/Wheel%u",i,w);k.wheel_ok[w]=race_pool_id(m,base,key,k.wheel[w]);incomplete_=incomplete_||!k.wheel_ok[w];}
                incomplete_=incomplete_||!k.car_ok||!k.player_type_ok;}
        }
        unsigned locals=0;
        for(uint32_t i=0;i<t.count;++i){auto& c=t.cars[i];resolve_car(m,base,i,c);if(!c.valid)continue;++t.proven;
            if(c.player_type==1){++locals;t.local=i;}}
        if(locals>max_locals){t.reason="multiple_local_participants";t.cars={};t.proven=0;t.local=UINT32_MAX;return t;}
        // Every proven egg, en3d and instance belongs to exactly one participant role.
        std::array<uint32_t,kFleetMaxCars*15> seen{};size_t used=0;
        auto unique=[&](uint32_t v){for(size_t k=0;k<used;++k)if(seen[k]==v)return false;seen[used++]=v;return true;};
        for(uint32_t i=0;i<t.count;++i){const auto& c=t.cars[i];if(!c.valid)continue;
            if(!unique(c.egg)||!unique(c.en3d)||!unique(c.instance)){t.reason="participant_identity_not_unique";t.cars={};t.proven=0;t.local=UINT32_MAX;return t;}
            for(unsigned w=0;w<4;++w)if(c.wheel_mask&(1u<<w))
                if(!unique(c.wheel_egg[w])||!unique(c.wheel_en3d[w])||!unique(c.wheel_instance[w])){t.reason="participant_identity_not_unique";t.cars={};t.proven=0;t.local=UINT32_MAX;return t;}}
        t.valid=t.proven>0;t.reason=t.valid?"participant_eggs_proven":"no_participant_proven";
        return t;
    }

private:
    uint64_t generation_=0,owner_=0,resolutions_=0,calls_=0,retry_at_=0;uint32_t count_=0;bool incomplete_=false;std::array<Ids,kFleetMaxCars> ids_{};

    static bool word(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return a&&!(a&3)&&m.read(a,&v,4);}
    static bool pointer(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return word(m,a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);}
    // Baseline vector shape (race_epoch.cpp): begin +4, end +8, capacity +12.
    static bool vector(RaceReadMemory& m,uint32_t p,uint32_t limit,uint32_t& begin,uint32_t& count) noexcept {
        uint32_t end=0,capacity=0;if(!word(m,p+4,begin)||!word(m,p+8,end)||!word(m,p+12,capacity)||!begin||end<begin||capacity<end||(end-begin)%4)return false;
        count=(end-begin)/4;return count<=limit;
    }
    static bool text_is(RaceReadMemory& m,uint32_t base,uint32_t id,const char* expected) noexcept {
        char text[96]{};return race_pool_text(m,base,id,text,sizeof(text))&&!std::strcmp(text,expected);
    }
    // Unique live egg registered under the pool id, with its en3d and current instance.
    static const char* egg_chain(RaceReadMemory& m,uint32_t base,uint32_t id,uint32_t& egg,uint32_t& en3d,uint32_t& instance) noexcept {
        uint32_t manager=0,registry=0,begin=0,count=0,bucket=0;
        if(!pointer(m,base+kFleetEggManagerRva,manager)||!pointer(m,manager+0x1c,registry)||!vector(m,registry,1u<<20,begin,count)||id>=count)return "egg_registry_unreadable";
        if(!pointer(m,begin+id*4,bucket)||!vector(m,bucket,64,begin,count))return "egg_registry_bucket_unreadable";
        if(count!=1)return "egg_name_not_unique";
        uint32_t name=0;uint8_t flags=0;
        if(!pointer(m,begin,egg)||!word(m,egg+0x5c,name)||name!=id)return "egg_name_mismatch";
        if(!m.read(egg,&flags,1)||(flags&2))return "egg_retired";
        uint32_t back=0;
        if(!pointer(m,egg+0x50,en3d))return "egg_en3d_missing";
        if(!pointer(m,en3d+0x74,instance))return "en3d_instance_not_created";
        if(!pointer(m,instance+0xb0,back)||back!=en3d)return "instance_en3d_link_mismatch";
        return nullptr;
    }
    static bool model_folder(RaceReadMemory& m,uint32_t base,uint32_t en3d,const char* leaf,std::array<char,48>& folder,std::array<char,64>* seen=nullptr) noexcept {
        uint32_t id=0;char text[128]{};
        if(!word(m,en3d+0xc,id)||!id||!race_pool_text(m,base,id,text,sizeof(text)))return false;
        if(fleet_model_folder(text,leaf,folder))return true;
        if(seen){*seen={};for(size_t i=0;i+1<seen->size()&&text[i];++i)(*seen)[i]=(text[i]>=0x20&&text[i]<0x7f)?text[i]:'?';}
        return false;
    }
    // Broker "Car<N>" is the gaVehicleOutputData of the same participant (HUD feed, PC 4a4540).
    static bool vehicle_output(RaceReadMemory& m,uint32_t base,uint32_t id) noexcept {
        uint32_t manager=0,begin=0,end=0,native=0,payload=0,tag=0,type=0;
        if(!pointer(m,base+kFleetBrokerRva,manager)||!pointer(m,manager+4,begin)||!word(m,manager+8,end)||end<begin||(end-begin)%0x1c||id>=(end-begin)/0x1c)return false;
        const uint32_t record=begin+id*0x1c;char name[32]{};
        return word(m,record,native)&&native==id&&word(m,record+8,tag)&&tag==10&&pointer(m,record+4,payload)&&
            word(m,payload+4,type)&&race_pool_text(m,base,type,name,sizeof(name))&&!std::strcmp(name,"gaVehicleOutputData");
    }
    void resolve_car(RaceReadMemory& m,uint32_t base,uint32_t i,FleetParticipant& c) const noexcept {
        const auto& k=ids_[i];char key[64]{};c={};
        std::snprintf(key,sizeof(key),"Car%u",i);
        if(!k.car_ok||!text_is(m,base,k.car,key)){c.reason="car_name_id_unresolved";return;}
        if(!k.player_type_ok){c.reason="player_type_key_missing";return;}
        std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);
        if(!text_is(m,base,k.player_type,key)){c.reason="player_type_key_changed";return;}
        const auto type=race_broker_scalar(m,base,k.player_type,2);if(!type.present){c.reason="player_type_unreadable";return;}
        c.player_type=type.value;
        if(!vehicle_output(m,base,k.car)){c.reason="vehicle_output_missing";return;}
        if(const char* r=egg_chain(m,base,k.car,c.egg,c.en3d,c.instance)){c.reason=r;return;}
        if(!model_folder(m,base,c.en3d,"car",c.folder,&c.model_text)){c.reason="body_model_name_not_vehicle_car";return;}
        for(unsigned w=0;w<4;++w){
            std::snprintf(key,sizeof(key),"Car%u/Wheel%u",i,w);
            if(!k.wheel_ok[w]||!text_is(m,base,k.wheel[w],key))continue;
            uint32_t egg=0,en3d=0,instance=0;std::array<char,48> folder{};
            if(egg_chain(m,base,k.wheel[w],egg,en3d,instance)||!model_folder(m,base,en3d,"wheel",folder)||folder!=c.folder)continue;
            c.wheel_egg[w]=egg;c.wheel_en3d[w]=en3d;c.wheel_instance[w]=instance;c.wheel_mask|=1u<<w;
        }
        c.valid=true;c.reason="participant_egg_chain_proven";
    }
};

// The participant that owns the draw being processed (set by FleetParticipantScope at each draw entry).
struct FleetActive {
    bool active=false,local=false;uint32_t index=UINT32_MAX;FleetRole role=FleetRole::None;unsigned wheel=4;
    uint64_t race_generation=0,owner_lifetime=0,frame=UINT64_MAX;std::array<char,48> folder{};
};
inline thread_local FleetActive fleet_active{};
struct FleetActiveScope {
    FleetActive previous;
    explicit FleetActiveScope(const FleetActive& a) noexcept:previous(fleet_active){fleet_active=a;}
    ~FleetActiveScope(){fleet_active=previous;}
    FleetActiveScope(const FleetActiveScope&)=delete;FleetActiveScope& operator=(const FleetActiveScope&)=delete;
};
// FRONTEND-CARS1: the frontend model slot that owns the current COMPLETE draw (0 = the original model).
inline thread_local unsigned frontend_slot_active=0;
struct FrontendSlotScope {
    unsigned previous;
    explicit FrontendSlotScope(unsigned slot) noexcept:previous(frontend_slot_active){frontend_slot_active=slot;}
    ~FrontendSlotScope(){frontend_slot_active=previous;}
    FrontendSlotScope(const FrontendSlotScope&)=delete;FrontendSlotScope& operator=(const FrontendSlotScope&)=delete;
};
inline constexpr unsigned kFrontendExtraSlots=3;
// Owner-to-slot table for frontend COMPLETE cars. A slot keeps its instance while it is drawn every frame;
// a slot not drawn in this or the previous frame may take a new instance. With one slot (PS2FrontendAllCars=0)
// a second instance drawn in the same frame is refused instead of re-binding the model (no per-draw thrash).
struct FrontendSlotTable {
    struct Slot {uintptr_t instance=0;uint64_t frame=UINT64_MAX;};
    std::array<Slot,1+kFrontendExtraSlots> slots{};
    // Returns the slot index, or UINT32_MAX when every usable slot already owns another car this frame.
    unsigned assign(uintptr_t instance,uint64_t frame,unsigned count) noexcept {
        if(!instance||!count||count>slots.size())return UINT32_MAX;
        for(unsigned i=0;i<count;++i)if(slots[i].instance==instance){slots[i].frame=frame;return i;}
        for(unsigned i=0;i<count;++i){auto& s=slots[i];
            const bool live=s.instance&&s.frame!=UINT64_MAX&&(s.frame==frame||s.frame+1==frame);
            if(!live){s.instance=instance;s.frame=frame;return i;}}
        return UINT32_MAX;
    }
};

// Extension slot for the active participant: 0 = the original single-car parents (local driver, or no
// participant scope), 1..8 = participant N+1 for every non-local car.
inline unsigned fleet_slot(const FleetActive& a) noexcept {return a.active&&!a.local&&a.index<kFleetMaxCars?a.index+1:0;}

}  // namespace gfx2::ps2port
