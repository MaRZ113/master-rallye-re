#pragma once
// Read-only semantic feed for PS2HudDamage: the local player's damage channels, read the way the PC damage
// row (MRallye.exe 4a4540) reads them.
//   Broker (base+0x2f9410, 0x1c records [id, payload, tag]) key "Car<N>" (N = the unique Race/Car<N>/PlayerType==1)
//   -> tag 10 object whose type name (payload+4, pool text) is "gaVehicleOutputData"
//   -> vehicle = payload+8: steering +0x104, engine +0x100, gear +0x108
//   -> wheels  = payload+0xc: suspension max(+0x9c,+0x48,+0x144,+0xf0), tyres max(+0xa0,+0x4c,+0x148,+0xf4).
// Pool ids are resolved once per race generation; every pointer and record is re-validated each frame.
#include "race_epoch.hpp"
#include "ps2_hud_map.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace gfx2::ps2port {

inline constexpr uint32_t kHudBrokerRva=0x2f9410;
inline constexpr uint32_t kHudBrokerObjectTag=10;

struct HudDamageFeed { bool ok=false; std::array<float,5> values{}; const char* reason="not_read"; };

inline bool hud_live_read(uint32_t address,void* out,size_t bytes) noexcept {
    if(address<0x10000||address>0x7fffffff||bytes>256||bytes>0x7fffffffu-address)return false;
    __try{std::memcpy(out,reinterpret_cast<const void*>(static_cast<uintptr_t>(address)),bytes);return true;}
    __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
class HudLiveMemory final : public RaceReadMemory {
public:
    bool read(uint32_t address,void* output,size_t bytes) noexcept override {return hud_live_read(address,output,bytes);}
};

class HudDamageFeedReader {
    uint64_t generation_=0;
    bool ids_ok_=false;
    uint32_t car_id_=0;
    const char* id_reason_="not_resolved";
    static bool word(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return !(a&3)&&m.read(a,&v,4);}
    static bool pointer(RaceReadMemory& m,uint32_t a,uint32_t& v) noexcept {return word(m,a,v)&&v>=0x10000&&v<=0x7ffffffc&&!(v&3);}
    static bool real(RaceReadMemory& m,uint32_t a,float& v) noexcept {return m.read(a,&v,4)&&std::isfinite(v);}
    bool resolve(RaceReadMemory& m,uint32_t base) noexcept {
        ids_ok_=false;unsigned locals=0;uint32_t local=0;
        for(uint32_t i=0;i<8;++i){
            char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);uint32_t id=0;
            if(!m.resolve_id(base,key,id))break;
            const auto type=race_broker_scalar(m,base,id,2);
            if(!type.present){id_reason_="player_type_unreadable";return false;}
            if(type.value==1){++locals;local=i;}
        }
        if(locals!=1){id_reason_="single_local_player_unproven";return false;}
        char car[16]{};std::snprintf(car,sizeof(car),"Car%u",local);
        if(!m.resolve_id(base,car,car_id_)){id_reason_="car_key_missing";return false;}
        ids_ok_=true;id_reason_="ids_resolved";return true;
    }
public:
    void reset() noexcept {generation_=0;ids_ok_=false;id_reason_="not_resolved";}
    HudDamageFeed read(RaceReadMemory& m,uint32_t base,uint64_t race_generation) noexcept {
        HudDamageFeed f;
        if(!race_generation){f.reason="no_race_generation";return f;}
        if(race_generation!=generation_){generation_=race_generation;resolve(m,base);}
        if(!ids_ok_){f.reason=id_reason_;return f;}
        uint32_t manager=0,begin=0,end=0;
        if(!pointer(m,base+kHudBrokerRva,manager)||!pointer(m,manager+4,begin)||!word(m,manager+8,end)||end<begin||(end-begin)%0x1c){f.reason="broker_unreadable";return f;}
        if(car_id_>=(end-begin)/0x1c){f.reason="car_record_out_of_range";return f;}
        const uint32_t record=begin+car_id_*0x1c;uint32_t native_id=0,payload=0,tag=0,type=0;
        if(!word(m,record,native_id)||native_id!=car_id_||!word(m,record+8,tag)||tag!=kHudBrokerObjectTag||!pointer(m,record+4,payload)){f.reason="car_record_not_object";return f;}
        char name[32]{};
        if(!word(m,payload+4,type)||!race_pool_text(m,base,type,name,sizeof(name))||std::strcmp(name,"gaVehicleOutputData")){f.reason="car_object_type_mismatch";return f;}
        uint32_t vehicle=0,wheels=0;
        if(!pointer(m,payload+8,vehicle)||!pointer(m,payload+0xc,wheels)){f.reason="vehicle_output_pointers_missing";return f;}
        float steering=0,engine=0,gear=0;
        if(!real(m,vehicle+0x104,steering)||!real(m,vehicle+0x100,engine)||!real(m,vehicle+0x108,gear)){f.reason="vehicle_damage_unreadable";return f;}
        float suspension=0,tyres=0;
        for(uint32_t o:{0x9cu,0x48u,0x144u,0xf0u}){float v=0;if(!real(m,wheels+o,v)){f.reason="wheel_damage_unreadable";return f;}if(v>suspension)suspension=v;}
        for(uint32_t o:{0xa0u,0x4cu,0x148u,0xf4u}){float v=0;if(!real(m,wheels+o,v)){f.reason="wheel_damage_unreadable";return f;}if(v>tyres)tyres=v;}
        f.values={steering,engine,suspension,gear,tyres};f.ok=true;f.reason="live_vehicle_output";return f;
    }

    // ---- PS2HudMap feed (PC GPS 4a57a0 reads the same objects).
    // Marker manager base+0x2f94e4: lists [mgr+4,mgr+8) indexed by pool id; list [+4,+8) records 0x48, position +0x38.
    struct MapIds { bool ok=false; uint32_t last_marker=0,raceline=0,finish_area=0; bool finish_known=false; int finish=0;
        std::array<uint32_t,8> split{};int splits=0;                                   // Race/SplitTime%d/Percentage
        std::array<uint32_t,8> car{},colour{};int cars=0;                             // Car%d, Race/Car%d/Colour
    };
private:
    MapIds map_ids_{};uint64_t map_generation_=0;uint32_t map_local_=0;bool map_local_ok_=false;
    static bool marker_list(RaceReadMemory& m,uint32_t base,uint32_t id,uint32_t& begin,uint32_t& count) noexcept {
        uint32_t mgr=0,lb=0,le=0,list=0,end=0;
        if(!pointer(m,base+0x2f94e4,mgr)||!pointer(m,mgr+4,lb)||!word(m,mgr+8,le)||le<lb||(le-lb)%4||id>=(le-lb)/4)return false;
        if(!pointer(m,lb+id*4,list)||!pointer(m,list+4,begin)||!word(m,list+8,end)||end<begin||(end-begin)%0x48)return false;
        count=(end-begin)/0x48;return count>0&&count<100000;
    }
    static bool marker_xz(RaceReadMemory& m,uint32_t begin,uint32_t i,float& x,float& z) noexcept {
        return real(m,begin+i*0x48+0x38,x)&&real(m,begin+i*0x48+0x40,z);
    }
public:
    bool read_map(RaceReadMemory& m,uint32_t base,uint64_t race_generation,int window,MapInput& out,const char*& reason) noexcept {
        reason="not_read";
        if(!race_generation){reason="no_race_generation";return false;}
        if(race_generation!=generation_){generation_=race_generation;resolve(m,base);}
        if(!ids_ok_){reason=id_reason_;return false;}
        if(race_generation!=map_generation_){
            map_generation_=race_generation;map_ids_={};
            unsigned locals=0;
            for(uint32_t i=0;i<8;++i){char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);uint32_t id=0;
                if(!m.resolve_id(base,key,id))break;const auto t=race_broker_scalar(m,base,id,2);if(t.present&&t.value==1){++locals;map_local_=i;}}
            char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/LastMarker",map_local_);
            map_ids_.ok=locals==1&&m.resolve_id(base,key,map_ids_.last_marker)&&m.resolve_id(base,"RaceLine",map_ids_.raceline);
            if(map_ids_.ok&&m.resolve_id(base,"FinishArea",map_ids_.finish_area)){
                uint32_t fb=0,fc=0,rb=0,rc=0;float fx=0,fz=0;
                if(marker_list(m,base,map_ids_.finish_area,fb,fc)&&marker_xz(m,fb,0,fx,fz)&&marker_list(m,base,map_ids_.raceline,rb,rc)){
                    float best=0;int index=-1;
                    for(uint32_t i=0;i<rc;++i){float x=0,z=0;if(!marker_xz(m,rb,i,x,z)){index=-1;break;}
                        const float d=(x-fx)*(x-fx)+(z-fz)*(z-fz);if(index<0||d<best){best=d;index=int(i);}}
                    if(index>=0){map_ids_.finish_known=true;map_ids_.finish=index+1;}
                }
            }
        }
        if(!map_ids_.ok){reason="map_ids_unresolved";return false;}
        if(map_ids_.cars==0){       // once per race: split and opponent keys (missing keys simply mean none)
            for(int d=0;d<8;++d){char key[64]{};std::snprintf(key,sizeof(key),"Race/SplitTime%d/Percentage",d);
                if(!m.resolve_id(base,key,map_ids_.split[size_t(d)]))break;map_ids_.splits=d+1;}
            uint32_t n_id=0;
            if(m.resolve_id(base,"Race/NumCars",n_id)){const auto n=race_broker_scalar(m,base,n_id,2);
                if(n.present&&n.value>=1&&n.value<=8){
                    for(int i=0;i<n.value;++i){char key[64]{};std::snprintf(key,sizeof(key),"Car%d",i);
                        if(!m.resolve_id(base,key,map_ids_.car[size_t(i)])){map_ids_.cars=-1;break;}
                        std::snprintf(key,sizeof(key),"Race/Car%d/Colour",i);if(!m.resolve_id(base,key,map_ids_.colour[size_t(i)]))map_ids_.colour[size_t(i)]=0;
                        map_ids_.cars=i+1;}
                }else map_ids_.cars=-1;
            }else map_ids_.cars=-1;
        }
        // Vehicle pose through the same Car<N> record as the damage feed.
        uint32_t manager=0,begin=0,end=0;
        if(!pointer(m,base+kHudBrokerRva,manager)||!pointer(m,manager+4,begin)||!word(m,manager+8,end)||end<begin||(end-begin)%0x1c||car_id_>=(end-begin)/0x1c){reason="broker_unreadable";return false;}
        uint32_t native_id=0,payload=0,tag=0,vehicle=0;const uint32_t record=begin+car_id_*0x1c;
        if(!word(m,record,native_id)||native_id!=car_id_||!word(m,record+8,tag)||tag!=kHudBrokerObjectTag||!pointer(m,record+4,payload)||!pointer(m,payload+8,vehicle)){reason="car_record_not_object";return false;}
        float px=0,pz=0,fx=0,fz=0,vx=0,vz=0;
        if(!real(m,vehicle+0xec,px)||!real(m,vehicle+0xf4,pz)||!real(m,vehicle+0xdc,fx)||!real(m,vehicle+0xe4,fz)||!real(m,vehicle+0x18,vx)||!real(m,vehicle+0x20,vz)){reason="vehicle_pose_unreadable";return false;}
        const auto last=race_broker_scalar(m,base,map_ids_.last_marker,2);
        if(!last.present){reason="last_marker_unreadable";return false;}
        uint32_t rb=0,rc=0;
        if(!marker_list(m,base,map_ids_.raceline,rb,rc)){reason="raceline_unreadable";return false;}
        const int count=int(rc);const int l=(last.value<=0||last.value>=count)?0:last.value;
        const int finish=map_ids_.finish_known?std::min(map_ids_.finish,count):count;
        const int lo=std::max(l-window,0),hi=std::min(std::min(l+window,finish),count);
        out=MapInput{};out.px=px;out.pz=pz;out.fx=fx;out.fz=fz;out.vx=vx;out.vz=vz;out.last=l;out.finish=finish;out.first=lo;
        for(int i=lo;i<hi;++i){float x=0,z=0;if(!marker_xz(m,rb,uint32_t(i),x,z)){reason="raceline_point_unreadable";return false;}out.points.push_back({x,z});}
        // Splits: PS2 0x181dd0 stores Percentage = BestMarker / count, so BestMarker = round(Percentage * count).
        for(int d=0;d<map_ids_.splits;++d){
            uint32_t pmgr=0,pb=0,pe=0,payload=0,tag=0,nid=0;float pct=0;const uint32_t id=map_ids_.split[size_t(d)];
            if(!pointer(m,base+kHudBrokerRva,pmgr)||!pointer(m,pmgr+4,pb)||!word(m,pmgr+8,pe)||pe<pb||(pe-pb)%0x1c||id>=(pe-pb)/0x1c)break;
            const uint32_t r=pb+id*0x1c;
            if(!word(m,r,nid)||nid!=id||!word(m,r+8,tag)||tag!=1||!pointer(m,r+4,payload)||!real(m,payload,pct))continue;
            const int idx=int(std::lround(double(pct)*count));if(idx>0&&idx<count)out.splits.push_back(idx);
        }
        // Opponents: every other car's vehicle position (same fields as the player) and Race/Car%d/Colour (tag 5, RGBA).
        for(int i=0;i<map_ids_.cars;++i){
            if(uint32_t(i)==map_local_)continue;
            const uint32_t cid=map_ids_.car[size_t(i)];uint32_t cnative=0,cpayload=0,ctag=0,cveh=0;
            if(cid>=(end-begin)/0x1c)continue;const uint32_t cr=begin+cid*0x1c;
            if(!word(m,cr,cnative)||cnative!=cid||!word(m,cr+8,ctag)||ctag!=kHudBrokerObjectTag||!pointer(m,cr+4,cpayload)||!pointer(m,cpayload+8,cveh))continue;
            MapInput::Opponent o;
            if(!real(m,cveh+0xec,o.x)||!real(m,cveh+0xf4,o.z))continue;
            const uint32_t col=map_ids_.colour[size_t(i)];
            if(col&&col<(end-begin)/0x1c){const uint32_t rr=begin+col*0x1c;uint32_t nn=0,tt=0,pp=0;float c[4]{};
                if(word(m,rr,nn)&&nn==col&&word(m,rr+8,tt)&&tt==5&&pointer(m,rr+4,pp)&&real(m,pp,c[0])&&real(m,pp+4,c[1])&&real(m,pp+8,c[2])){o.r=c[0];o.g=c[1];o.b=c[2];}}
            out.opponents.push_back(o);
        }
        out.ok=true;reason=map_ids_.finish_known?"live_raceline":"live_raceline_no_finish_area";return true;
    }
};

}  // namespace gfx2::ps2port
