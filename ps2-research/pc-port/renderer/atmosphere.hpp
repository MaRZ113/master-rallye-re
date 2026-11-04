#pragma once
// ATMOSPHERE1: bounded PC sky/terrain experiment. No dinput8 dependency.
#include "sdk.hpp"
#include "game_fov.hpp"
#include "provenance.hpp"
#include "ps2_hud_damage_feed.hpp"
#include "atmosphere_sky_registry.hpp"
#include "atmosphere_lifecycle.hpp"
#include "ground_detail.hpp"
#include "atmosphere_scene.hpp"
#include "scene_resolver.hpp"
#include "atmosphere_sun.hpp"
#include "atmosphere_water.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cwchar>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <tlhelp32.h>
#include <vector>

namespace gfx2::atmosphere {
inline constexpr uintptr_t kSkyReadSite=0x4b123c;
inline constexpr std::array<unsigned char,5> kSkyReadBytes={0xe8,0x1f,0x55,0x02,0x00};
inline int parse_preset(const wchar_t* text) noexcept {
    return text&&text[0]>=L'0'&&text[0]<=L'5'&&text[1]==0 ? text[0]-L'0' : -1;
}
inline DWORD tint(DWORD color,float r,float g,float b,float light=0) noexcept {
    auto channel=[&](unsigned shift,float scale){return DWORD(std::clamp(std::lround(float((color>>shift)&255)*scale+light*255),0l,255l))<<shift;};
    return (color&0xff000000u)|channel(16,r)|channel(8,g)|channel(0,b);
}
inline float point_light(float x,float y,float z,float sx,float sy,float sz,float radius) noexcept {
    if(!std::isfinite(radius)||radius<=0)return 0;
    const float d2=(x-sx)*(x-sx)+(y-sy)*(y-sy)+(z-sz)*(z-sz);
    if(!std::isfinite(d2)||d2>=radius*radius)return 0;
    const float a=1-std::sqrt(d2)/radius;return .4f*a*a;
}
// B3 math prototype only. Visibility is unknown without a current-frame depth
// observation; callers must suppress disk/halo/flare in that case.
struct SunProjection {bool inside=false;float x=0,y=0,z=0;};
inline SunProjection project_sun(const D3DMATRIX& view,const D3DMATRIX& projection,float x,float y,float z) noexcept {
    const float vx=x*view._11+y*view._21+z*view._31;
    const float vy=x*view._12+y*view._22+z*view._32;
    const float vz=x*view._13+y*view._23+z*view._33;
    const float w=vx*projection._14+vy*projection._24+vz*projection._34;
    if(!std::isfinite(w)||w<=0)return {};
    SunProjection p{false,(vx*projection._11+vy*projection._21+vz*projection._31)/w,
        (vx*projection._12+vy*projection._22+vz*projection._32)/w,1};
    p.inside=std::isfinite(p.x)&&std::isfinite(p.y)&&std::abs(p.x)<=1&&std::abs(p.y)<=1;return p;
}
inline bool sun_visible(bool projected,bool depth_observed,float clear_fraction) noexcept {
    return projected&&depth_observed&&std::isfinite(clear_fraction)&&clear_fraction>=.99f;
}
struct Pixels {unsigned width=0,height=0;std::vector<DWORD> bgra;};
inline bool decode_sky(const std::vector<uint8_t>& bytes,Pixels& p) {
    p={};if(bytes.size()<20)return false;uint32_t h[5]{};std::memcpy(h,bytes.data(),20);
    if(h[0]!=0xfeed||h[3]!=256||h[4]!=256||bytes.size()!=20+256*256*4)return false;
    p.width=h[3];p.height=h[4];p.bgra.resize(256*256);std::memcpy(p.bgra.data(),bytes.data()+20,p.bgra.size()*4);return true;
}
struct Selection {
    bool configured=false,enabled=false,installed=false;
    std::wstring ini;CallPatch patch,used_patch;
    const char* reason="off";
};
inline Selection& selection() {static Selection s;return s;}
class Memory final:public PatchMemory {
public:
    bool read(void* d,const void* s,size_t n)noexcept override{return safe_copy(d,s,n);}
    bool write(void* d,const void* s,size_t n)noexcept override{return safe_copy(d,s,n);}
    bool protect(void* p,size_t n,DWORD v,DWORD& old)noexcept override{return VirtualProtect(p,n,v,&old)!=0;}
    bool flush(void* p,size_t n)noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=0;}
};
struct BrokerField {
    bool id_found=false,unpublished=false,native_null=false;uint32_t id=0;RaceScalar scalar;
};
inline BrokerField field(RaceReadMemory& memory,const char* key,uint32_t tag)noexcept {
    BrokerField f;f.id_found=memory.resolve_id(0x400000,key,f.id);
    if(f.id_found){
        f.scalar=race_broker_scalar(memory,0x400000,f.id,tag);
        // A sparse Broker slot has the exact native 4DD980 constructor state:
        // id=0, payload=null, tag=12. Unreadable/malformed/wrong-type data is
        // different from this positively observed, not-yet-published slot.
        uint32_t manager=0,begin=0,end=0,capacity=0,slot[3]{};
        if(!f.scalar.present&&f.id>0&&memory.read(0x6f9410,&manager,4)&&manager>=0x10000&&manager<=0x7fffffe0&&
            memory.read(manager+4,&begin,4)&&memory.read(manager+8,&end,4)&&memory.read(manager+12,&capacity,4)&&
            begin>=0x10000&&end>=begin&&capacity>=end&&capacity<=0x7fffffff&&(end-begin)%28==0&&
            (end-begin)/28<=32768&&f.id<(end-begin)/28&&memory.read(begin+f.id*28,slot,sizeof(slot))){
            f.unpublished=slot[0]==0&&slot[1]==0&&slot[2]==12;
            f.native_null=slot[0]==f.id&&slot[1]==0&&slot[2]==12;
        }
    }return f;
}
struct Readiness {BrokerField players,sync,browse,locals,type,replay;const char* reason="unread";bool accepted=false;};
inline Readiness readiness(RaceReadMemory& memory,bool native_local_sky_init=false)noexcept {
    Readiness r;r.players=field(memory,"Race/NumNetworkPlayers",2);r.sync=field(memory,"Race/NetworkSyncActive",0);
    r.browse=field(memory,"FrontEnd/Network/Browse",0);r.locals=field(memory,"Race/NumPlayers",2);
    r.type=field(memory,"Race/Type",2);r.replay=field(memory,"Race/PlaybackReplay",0);
    if(!r.players.id_found)r.reason="network_players_key_absent";
    else if(!r.players.scalar.present)r.reason="network_players_record_unready_or_wrong_type";
    else if(r.players.scalar.value!=0)r.reason="network_players_nonzero";
    else if(!r.sync.id_found)r.reason="network_sync_key_absent";
    else if(!r.sync.scalar.present){
        // 48E3AA calls 4AD930 (typed FrontEnd/Network/Browse), then publishes
        // SyncActive with that boolean at 48E3D6 / 48E473. During the first sky
        // init that publisher has not run. Use its actual source, NEVER an
        // absent-field default or a native getter that would create a record.
        if(!r.sync.unpublished)r.reason="network_sync_record_unready_or_wrong_type";
        else if(!native_local_sky_init)r.reason="early_sky_lifecycle_unproven";
        // Native bool getter 4D6610..4D6627 returns false for tag12. On a
        // pristine cold local run Browse is an assigned native null, not a bool
        // (confirmed PID39180, including after Sync=false publication). Accept
        // ONLY that exact readable id/payload/tag state, not missing storage or
        // other types, and still require every typed local/lifecycle proof.
        else if(!r.browse.scalar.present&&!r.browse.native_null)r.reason="early_network_source_unready_or_wrong_type";
        else if(r.browse.scalar.present&&r.browse.scalar.value!=0)r.reason="early_network_source_active";
        else if(!r.locals.scalar.present||r.locals.scalar.value!=1)r.reason="early_single_local_player_unproven";
        else if(!r.type.scalar.present||(r.type.scalar.value!=1&&r.type.scalar.value!=2))r.reason="early_local_race_type_unproven";
        else if(!r.replay.scalar.present||r.replay.scalar.value!=0)r.reason="early_non_replay_unproven";
        else {r.reason=r.browse.native_null?"native_null_false_source_with_typed_local_context":"typed_native_network_source_offline_before_publication";r.accepted=true;}
    }
    else if(r.sync.scalar.value!=0)r.reason="network_sync_active";
    else {r.reason="typed_offline_network_fields_ready";r.accepted=true;}return r;
}
inline std::string field_json(const BrokerField& f) {
    return std::string("{\"id_found\":")+(f.id_found?"true":"false")+",\"id\":"+std::to_string(f.id)+
        ",\"present\":"+(f.scalar.present?"true":"false")+",\"unpublished\":"+(f.unpublished?"true":"false")+",\"native_null\":"+(f.native_null?"true":"false")+",\"tag\":"+std::to_string(f.scalar.tag)+
        ",\"value\":"+(f.scalar.present?std::to_string(f.scalar.value):"null")+"}";
}
inline int choose(int original,int requested,bool enabled,bool offline,bool first_layer)noexcept {
    return enabled&&offline&&first_layer&&requested>=0&&requested<=5?requested:original;
}
inline int __cdecl sky_read(uint32_t caller,void* manager,uint32_t ai,uint32_t egg,const uint32_t* key) noexcept {
    // ALWAYS preserve the native getter, including its record-creation effects
    // and RET-4 ABI. Unknown contexts still use the original value.
    const int original=reinterpret_cast<int(__thiscall*)(void*,const uint32_t*)>(0x4d6760)(manager,key);
    try {
        auto& s=selection();wchar_t text[32]{};
        const bool enabled=s.enabled&&GetPrivateProfileIntW(L"Atmosphere",L"Enabled",0,s.ini.c_str())==1;
        GetPrivateProfileStringW(L"Atmosphere",L"SkyPreset",L"Auto",text,32,s.ini.c_str());
        const int requested=parse_preset(text);ps2port::HudLiveMemory memory;
        const auto life=lifecycle();uint32_t key_id=0,layer=UINT32_MAX,ai_vtable=0;char key_name[192]{};
        safe_copy(&key_id,key,4);race_pool_text(memory,0x400000,key_id,key_name,sizeof(key_name));
        safe_copy(&layer,reinterpret_cast<void*>(ai+12),4);safe_copy(&ai_vtable,reinterpret_cast<void*>(ai),4);
        const bool first=caller==kSkyReadSite+5;
        const bool early=first&&layer==0&&ai_vtable==0x691090&&egg&&life.installed&&life.same_thread&&
            life.initializing&&life.race&&life.job&&life.request&&life.scene&&!std::strncmp(life.scene_name.data(),"RaceTest/",9)&&
            !std::strcmp(key_name,"CloudNumber");
        const auto ready=readiness(memory,early);const int effective=choose(original,requested,enabled,ready.accepted,first);
        const char* reason=!enabled?"disabled":!first?"native_layer_used_read":requested<0?"auto_or_invalid_preset":ready.reason;
        session().write("{\"type\":\"atmosphere_sky_selection\",\"requested\":"+std::to_string(requested)+
            ",\"original\":"+std::to_string(original)+",\"effective\":"+std::to_string(effective)+",\"selected\":"+std::to_string(effective)+
            ",\"override\":"+(effective!=original?"true":"false")+",\"branch\":"+quote(std::string(first?"first_layer":"layer_used"))+
            ",\"reason\":"+quote(std::string(reason))+",\"caller_va\":"+std::to_string(caller)+",\"key\":"+quote(std::string(key_name))+
            ",\"network_players\":"+field_json(ready.players)+",\"network_sync\":"+field_json(ready.sync)+
            ",\"network_source\":"+field_json(ready.browse)+",\"local_players\":"+field_json(ready.locals)+
            ",\"race_type\":"+field_json(ready.type)+",\"playback_replay\":"+field_json(ready.replay)+
            ",\"race_generation\":"+std::to_string(life.race)+",\"request_generation\":"+std::to_string(life.request)+
            ",\"scene_job\":"+std::to_string(life.job)+",\"scene_id\":"+std::to_string(life.scene)+",\"scene\":"+quote(std::string(life.scene_name.data()))+
            ",\"native_ai\":"+std::to_string(ai)+",\"native_ai_vtable\":"+std::to_string(ai_vtable)+",\"native_egg\":"+std::to_string(egg)+
            ",\"layer\":"+std::to_string(layer)+",\"owner\":"+std::to_string(life.actor)+",\"owner_lifetime\":"+std::to_string(life.owner_lifetime)+
            ",\"observer_same_thread\":"+(life.same_thread?"true":"false")+",\"initializing_current_scene\":"+(life.initializing?"true":"false")+",\"thread\":"+std::to_string(GetCurrentThreadId())+"}");
        return effective;
    }catch(...){return original;}
}
__declspec(naked) inline void sky_read_bridge() {
    __asm {push dword ptr [esp+4]} // native key argument
    __asm {push ebp}              // native egg initializer argument
    __asm {push esi}              // gaAiCloudSetUp
    __asm {push ecx}              // broker manager
    __asm {push dword ptr [esp+16]} // native return PC
    __asm {call sky_read}
    __asm {add esp,20}
    __asm {ret 4}
}
// Same fail-closed thread protocol as the existing broker-null guard. All
// threads are resumed on every exit, before logging or C++ allocation.
class Threads {
    std::array<HANDLE,128> handles_{};std::array<DWORD,128> ids_{};size_t count_=0;
public:
    ~Threads(){leave();}
    void leave()noexcept{while(count_){auto h=handles_[--count_];ResumeThread(h);CloseHandle(h);}}
    bool enter()noexcept{
        HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(snap==INVALID_HANDLE_VALUE)return false;
        THREADENTRY32 e{};e.dwSize=sizeof(e);bool ok=Thread32First(snap,&e)!=0;
        if(ok)do{
            if(e.th32OwnerProcessID!=GetCurrentProcessId()||e.th32ThreadID==GetCurrentThreadId())continue;
            if(count_==handles_.size()){ok=false;break;}
            HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,e.th32ThreadID);
            if(!h){ok=false;break;}if(SuspendThread(h)==DWORD(-1)){CloseHandle(h);ok=false;break;}
            handles_[count_]=h;ids_[count_++]=e.th32ThreadID;CONTEXT c{};c.ContextFlags=CONTEXT_CONTROL;
            if(!GetThreadContext(h,&c)||(c.Eip>=0x4b1180&&c.Eip<0x4b1530)){ok=false;break;}
        }while(Thread32Next(snap,&e));CloseHandle(snap);if(!ok)return false;
        snap=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(snap==INVALID_HANDLE_VALUE)return false;
        e={};e.dwSize=sizeof(e);ok=Thread32First(snap,&e)!=0;
        if(ok)do{
            if(e.th32OwnerProcessID!=GetCurrentProcessId()||e.th32ThreadID==GetCurrentThreadId())continue;
            bool found=false;for(size_t i=0;i<count_;++i)found|=ids_[i]==e.th32ThreadID;
            if(!found){ok=false;break;}
        }while(Thread32Next(snap,&e));CloseHandle(snap);return ok;
    }
};
inline void configure_selection(bool supported,const std::wstring& ini) {
    auto& s=selection();if(s.configured)return;s.configured=true;s.ini=ini;
    if(!supported||GetPrivateProfileIntW(L"Atmosphere",L"Enabled",0,ini.c_str())!=1)return;
    if(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=0x400000){s.reason="image_base_mismatch";return;}
    // Called during initial D3D device construction, before the native scene
    // initializers on this render thread. The hook owns exactly one CALL.
    HMODULE pinned=nullptr;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&sky_read_bridge),&pinned)){s.reason="module_pin_failed";return;}
    Memory m;s.enabled=true;
    {
        Threads threads;
        if(threads.enter()){
            s.installed=s.patch.install(m,reinterpret_cast<void*>(kSkyReadSite),reinterpret_cast<uintptr_t>(&sky_read_bridge),kSkyReadBytes);
            if(s.installed&&!s.used_patch.install(m,reinterpret_cast<void*>(0x4b1374),reinterpret_cast<uintptr_t>(&sky_read_bridge),{0xe8,0xe7,0x53,0x02,0x00})){s.patch.remove(m);s.installed=false;}
            s.reason=s.installed?"installed_initial_device_before_scenes":"callsite_conflict_or_write_failed";
        }else s.reason="thread_quiescence_unproven";
    }
    if(!s.installed)s.enabled=false;
    session().write("{\"type\":\"atmosphere_sky_hook\",\"reason\":"+quote(std::string(s.reason))+"}");
}

class Pilot {
    bool enabled_=false;std::wstring ini_;std::filesystem::path set_;
    std::array<IDirect3DTexture8*,2> textures_{};
    std::array<Pixels,2> pixels_;
    bool custom_ready_=false,custom_failed_=false;
public:
    // Read-only original-PC identity helper; no PS2 noise asset/effect requested.
    ps2port::GroundDetail pc_noise_identity{false,L""};
    bool world=false,light_probe=false,scene_diagnostics=false;unsigned custom_base=3;
    unsigned scene_diagnostic_count=0;
    Lighting lighting;SceneAtlas atlas;std::filesystem::path atlas_path;
    bool universal=true,auto_ground=true;LightingMetadata metadata;SceneResolver resolver;std::filesystem::path metadata_path;
    bool body_tata=false;bool body_materials=false,seam_debug=false,body_debug=false;
    BodyMaterials body_capabilities;std::map<std::pair<std::string,unsigned>,std::string> body_texture_cache;
    uint64_t body_cpu_ticks=0,body_calls=0,body_vertices=0;
    NormalHints normal_hints;std::filesystem::path normals_path,body_path;
    bool seam_key_down=false;uint64_t seam_poll_frame=UINT64_MAX;
    uint64_t seam_frame=UINT64_MAX;unsigned seam_count=0;uint64_t body_debug_frame=UINT64_MAX;unsigned body_debug_count=0;
    bool world_route()const noexcept{return lighting.active()&&(world||lighting.fog_enabled);}
    uint64_t resolved_draws=0,resolver_skipped_draws=0;
    float sky_u_scale=1;std::array<uint64_t,5> category_draws{};uint64_t copied_bytes=0,scene_restore_count=0;
    uint64_t cpu_ticks=0,cpu_calls=0,perf_frame=0,perf_previous_ticks=0,perf_previous_calls=0;std::array<uint64_t,5> category_vertices{};
    bool sun_disk=false,sun_halo=false,sun_flare=false,pc_water=false,pc_water_caps=false;SunFx sun;uint64_t pc_water_draws=0;
    struct MaterialCache {uintptr_t pointer=0;uint64_t generation=0;std::string sha;bool opaque=false;};
    std::array<MaterialCache,1024> material_cache{};size_t material_cache_next=0;
    float source_x=0,source_y=0,source_z=0,radius=12;
    uint64_t sky_draws=0,world_draws=0,light_vertices=0;
    uint64_t observed_race=UINT64_MAX,observed_reset=UINT64_MAX,last_fog_frame=UINT64_MAX;
    uint64_t sky_candidates=0,sky_matched=0,sky_rejected=0,world_rejected=0;
    DWORD last_fog=0;bool fog_seen=false;
    struct SkyCache {uintptr_t pointer=0;uint64_t generation=0;std::string sha;int preset=-1,layer=-1;const char* reason="uninspected";};
    std::array<SkyCache,24> sky_cache{};size_t sky_cache_next=0;
    std::array<std::string,128> reasons{};size_t reason_count=0;
    void diagnostic_epoch(uint64_t race,uint64_t reset)noexcept {
        if(race==observed_race&&reset==observed_reset)return;
        // Resource serials are never re-used; reset still revokes hash evidence.
        if(reset!=observed_reset){for(auto& c:sky_cache)c={};sky_cache_next=0;for(auto& c:material_cache)c={};material_cache_next=0;}
        observed_race=race;observed_reset=reset;reason_count=0;scene_diagnostic_count=0;fog_seen=false;last_fog_frame=UINT64_MAX;
        resolver.clear();body_texture_cache.clear();
    }
    bool first_reason(const char* reason) {
        for(size_t i=0;i<reason_count;++i)if(reasons[i]==reason)return false;
        if(reason_count==reasons.size())return false;reasons[reason_count++]=reason;return true;
    }
    // A failed restoration is retained until repair succeeds. No subsequent
    // native draw/Reset may run with these outstanding changes.
    struct Pending {
        IDirect3DBaseTexture8* texture=nullptr;IDirect3DVertexBuffer8* stream=nullptr;
        IDirect3DIndexBuffer8* indices=nullptr;UINT stride=0,base=0;DWORD fog=0;
        DWORD body_factor=0;std::array<DWORD,7> body_stage{};uint32_t body_pending=0;
        bool texture_changed=false,stream_changed=false,indices_changed=false,fog_changed=false;
        bool any()const noexcept{return texture_changed||stream_changed||indices_changed||fog_changed||body_pending;}
        void release()noexcept{if(texture)texture->Release();if(stream)stream->Release();if(indices)indices->Release();texture=nullptr;stream=nullptr;indices=nullptr;}
    } pending;
    IDirect3DVertexBuffer8* scratch=nullptr;UINT scratch_size=0;
    Pilot(bool supported,const std::wstring& renderer_ini) {
        ini_=(std::filesystem::path(renderer_ini).parent_path()/L"Atmosphere.ini").wstring();
        enabled_=supported&&GetPrivateProfileIntW(L"Atmosphere",L"Enabled",0,ini_.c_str())==1;
        configure_selection(supported,ini_);enabled_=enabled_&&selection().installed;if(!enabled_)return;
        world=GetPrivateProfileIntW(L"Atmosphere",L"WorldLighting",0,ini_.c_str())==1;
        light_probe=GetPrivateProfileIntW(L"Atmosphere",L"LightProbe",0,ini_.c_str())==1;
        scene_diagnostics=GetPrivateProfileIntW(L"Atmosphere",L"SceneDiagnostics",0,ini_.c_str())==1;
        auto number=[&](const wchar_t* key,float fallback){return read_number(key,fallback);};
        auto setting=[&](const wchar_t* key,const wchar_t* fallback){wchar_t b[512]{};GetPrivateProfileStringW(L"Atmosphere",key,fallback,b,512,ini_.c_str());return std::wstring(b);};
        read_tunables();
        live_tuning=GetPrivateProfileIntW(L"Atmosphere",L"LiveTuning",0,ini_.c_str())==1;
        if(live_tuning){std::error_code ec;ini_time_=std::filesystem::last_write_time(ini_,ec);}
        atlas_path=setting(L"SceneAtlas",L"Atmosphere/scene.atlas");if(atlas_path.is_relative())atlas_path=std::filesystem::path(ini_).parent_path()/atlas_path;
        universal=setting(L"SceneResolver",L"Universal")!=L"LegacyAtlas";
        auto_ground=GetPrivateProfileIntW(L"Atmosphere",L"AutoGround",1,ini_.c_str())==1;
        seam_debug=GetPrivateProfileIntW(L"Atmosphere",L"SeamDebug",0,ini_.c_str())==1;
        body_debug=GetPrivateProfileIntW(L"Atmosphere",L"BodyDebug",0,ini_.c_str())==1;
        body_materials=setting(L"BodyPrototype",L"Off")==L"Materials";
        normals_path=setting(L"NormalHints",L"Atmosphere22/normals.lnh");if(normals_path.is_relative())normals_path=std::filesystem::path(ini_).parent_path()/normals_path;
        body_path=setting(L"BodyMaterials",L"Atmosphere22/body.blm");if(body_path.is_relative())body_path=std::filesystem::path(ini_).parent_path()/body_path;
        body_tata=setting(L"BodyPrototype",L"Off")==L"TataBonnet";
        metadata_path=setting(L"LightingMetadata",L"Atmosphere21/materials.lsm");if(metadata_path.is_relative())metadata_path=std::filesystem::path(ini_).parent_path()/metadata_path;
        pc_water=GetPrivateProfileIntW(L"Atmosphere",L"PCWaterAtmosphere",0,ini_.c_str())==1;
        source_x=number(L"LightX",0);source_y=number(L"LightY",0);source_z=number(L"LightZ",0);radius=std::clamp(number(L"LightRadius",12),.1f,100.f);
        wchar_t name[32768]{};GetPrivateProfileStringW(L"Atmosphere",L"CustomSet",L"",name,32768,ini_.c_str());
        custom_base=GetPrivateProfileIntW(L"Atmosphere",L"CustomBase",3,ini_.c_str());
        if(name[0]&&custom_base<=5){set_=std::filesystem::path(name);if(set_.is_relative())set_=std::filesystem::path(ini_).parent_path()/set_;}
        session().write(std::string("{\"type\":\"atmosphere_config\",\"enabled\":true,\"world_lighting\":")+(world?"true":"false")+
            ",\"light_probe\":"+(light_probe?"true":"false")+",\"custom_set_requested\":"+(!set_.empty()?"true":"false")+
            ",\"lighting_preset\":"+quote(std::string(lighting.mode==Lighting::Mode::GoldenHour?"GoldenHour":lighting.mode==Lighting::Mode::Day?"Day":"Original"))+
            ",\"lighting_strength\":"+std::to_string(lighting.strength)+",\"exposure\":"+std::to_string(lighting.exposure)+
            ",\"world_brightness\":"+std::to_string(lighting.world_brightness)+",\"scene_resolver\":"+quote(std::string(universal?"Universal":"LegacyAtlas"))+",\"auto_ground\":"+(auto_ground?"true":"false")+
            ",\"fog_enabled\":"+(lighting.fog_enabled?"true":"false")+",\"fog_color\":"+std::to_string(lighting.fog)+
            ",\"scene_atlas_sha256\":"+quote(std::string(kSceneAtlasSha))+",\"custom_sky_u_scale\":"+std::to_string(sky_u_scale)+
            ",\"vehicle_direct_lighting\":"+quote(std::string(body_materials?"native_and_PS2_material_capabilities":body_tata?"opt_in_Tata_bonnet_only":"off"))+",\"sun_fx\":\"current_frame_gpu_depth_mask_or_suppressed\""+
            ",\"live_tuning\":"+(live_tuning?"true":"false")+"}");
    }
    // LiveTuning=1: values that only change colours/sun visuals are re-read when
    // Atmosphere.ini is saved. Routes, paths, metadata and Enabled stay as loaded
    // at process start, so a live edit can never widen admission.
    bool live_tuning=false;uint64_t live_poll_frame=0,live_reloads=0;
    bool poll_live(uint64_t frame)noexcept {
        if(!enabled_||!live_tuning||frame<live_poll_frame+30)return false;live_poll_frame=frame;
        try{std::error_code ec;const auto now=std::filesystem::last_write_time(ini_,ec);if(ec||now==ini_time_)return false;ini_time_=now;
            read_tunables();resolver.clear();++live_reloads;
            session().write("{\"type\":\"atmosphere_live_reload\",\"frame\":"+std::to_string(frame)+",\"reloads\":"+std::to_string(live_reloads)+
                ",\"world_brightness\":"+std::to_string(lighting.world_brightness)+",\"sun_strength\":"+std::to_string(lighting.sun_strength)+
                ",\"sun_dir\":["+std::to_string(lighting.direction[0])+","+std::to_string(lighting.direction[1])+","+std::to_string(lighting.direction[2])+"]}");
            return true;
        }catch(...){return false;}
    }
private:
    std::filesystem::file_time_type ini_time_{};
    float read_number(const wchar_t* key,float fallback)const{wchar_t b[64]{};GetPrivateProfileStringW(L"Atmosphere",key,L"",b,64,ini_.c_str());wchar_t* end=nullptr;float v=std::wcstof(b,&end);return end!=b&&*end==0&&std::isfinite(v)?v:fallback;}
    void read_tunables(){
        auto number=[&](const wchar_t* key,float fallback){return read_number(key,fallback);};
        auto setting=[&](const wchar_t* key,const wchar_t* fallback){wchar_t b[512]{};GetPrivateProfileStringW(L"Atmosphere",key,fallback,b,512,ini_.c_str());return std::wstring(b);};
        Lighting fresh;const auto mode=setting(L"LightingPreset",L"GoldenHour");
        fresh.mode=mode==L"GoldenHour"?Lighting::Mode::GoldenHour:mode==L"Day"?Lighting::Mode::Day:Lighting::Mode::Original;
        if(fresh.mode==Lighting::Mode::Day){fresh.ambient={.9f,.94f,1.f};fresh.sun={.3f,.28f,.24f};fresh.ambient_strength=1;fresh.sun_strength=.35f;}
        fresh.strength=std::clamp(number(L"LightingStrength",1),0.f,1.f);fresh.exposure=std::clamp(number(L"Exposure",1.05f),.25f,2.f);
        fresh.world_brightness=std::clamp(number(L"WorldBrightness",1),.1f,1.5f);
        fresh.prelight_contrast=std::clamp(number(L"PrelightContrast",1),0.f,1.f);
        fresh.prelight_visibility=std::clamp(number(L"PrelightVisibility",0),0.f,1.f);
        fresh.ambient_strength=std::clamp(number(L"AmbientStrength",fresh.ambient_strength),0.f,2.f);fresh.sun_strength=std::clamp(number(L"SunlightStrength",fresh.sun_strength),0.f,2.f);
        const wchar_t* ambient_keys[]={L"AmbientR",L"AmbientG",L"AmbientB"};const wchar_t* sun_keys[]={L"SunlightR",L"SunlightG",L"SunlightB"};const wchar_t* dir_keys[]={L"SunDirX",L"SunDirY",L"SunDirZ"};
        for(unsigned i=0;i<3;++i){fresh.ambient[i]=std::clamp(number(ambient_keys[i],fresh.ambient[i]),0.f,2.f);fresh.sun[i]=std::clamp(number(sun_keys[i],fresh.sun[i]),0.f,2.f);fresh.direction[i]=std::clamp(number(dir_keys[i],fresh.direction[i]),-1.f,1.f);}
        fresh.fog_enabled=GetPrivateProfileIntW(L"Atmosphere",L"FogEnabled",0,ini_.c_str())==1;fresh.fog_strength=std::clamp(number(L"FogStrength",1),0.f,1.f);
        const auto fog=setting(L"FogColor",L"0x98765d");wchar_t* fog_end=nullptr;const auto fog_value=std::wcstoul(fog.c_str(),&fog_end,0);if(fog_end!=fog.c_str()&&!*fog_end&&fog_value<=0xffffff)fresh.fog=0xff000000u|static_cast<DWORD>(fog_value);else fresh.fog_enabled=false;
        lighting=fresh;
        sky_u_scale=std::clamp(number(L"CustomSkyUScale",1),.1f,2.f);
        sun_disk=GetPrivateProfileIntW(L"Atmosphere",L"SunDisk",0,ini_.c_str())==1;sun_halo=GetPrivateProfileIntW(L"Atmosphere",L"SunHalo",0,ini_.c_str())==1;sun_flare=GetPrivateProfileIntW(L"Atmosphere",L"SunFlare",0,ini_.c_str())==1;
    }
public:
    ~Pilot(){pending.release();reset();}
    bool enabled()const noexcept{return enabled_;}
    bool custom()const noexcept{return enabled_&&!set_.empty()&&!custom_failed_;}
    void disable()noexcept{enabled_=false;}
    void reset()noexcept{sun.reset();resolver.clear();body_texture_cache.clear();for(auto*& t:textures_){if(t)t->Release();t=nullptr;}if(scratch)scratch->Release();scratch=nullptr;scratch_size=0;custom_ready_=false;}
    const Pixels& pixels(unsigned layer)const noexcept{return pixels_[layer];}
    bool load(IDirect3DDevice8& n) {
        if(custom_ready_)return true;if(!custom())return false;
        try {
        for(unsigned i=0;i<2;++i){
            std::ifstream f(set_/(i?L"layer.dxt":L"clouds.dxt"),std::ios::binary|std::ios::ate);
            if(!f||f.tellg()!=std::streamoff(20+256*256*4)){custom_failed_=true;reset();return false;}
            f.seekg(0);std::vector<uint8_t> bytes(20+256*256*4);f.read(reinterpret_cast<char*>(bytes.data()),bytes.size());
            if(!f||!decode_sky(bytes,pixels_[i])){custom_failed_=true;reset();return false;}
            std::vector<BYTE> alpha(256*256);for(size_t j=0;j<alpha.size();++j)alpha[j]=BYTE(pixels_[i].bgra[j]>>24);
            bool matched=false;const auto alpha_sha=sha256_bytes(alpha.data(),alpha.size());
            for(const auto& id:kSkyIdentities)if(id.preset==custom_base&&id.layer==i&&alpha_sha==id.alpha_sha)matched=true;
            if(!matched||FAILED(n.CreateTexture(256,256,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&textures_[i]))||!textures_[i]){custom_failed_=true;reset();return false;}
            D3DLOCKED_RECT l{};if(FAILED(textures_[i]->LockRect(0,&l,nullptr,0))){custom_failed_=true;reset();return false;}
            const bool valid=l.pBits&&l.Pitch>=1024;
            if(valid)for(unsigned y=0;y<256;++y)std::memcpy(static_cast<BYTE*>(l.pBits)+y*l.Pitch,pixels_[i].bgra.data()+y*256,1024);
            const HRESULT hr=textures_[i]->UnlockRect(0);if(!valid||FAILED(hr)){custom_failed_=true;reset();return false;}
        }
        custom_ready_=true;return true;
        }catch(...){custom_failed_=true;reset();return false;}
    }
    IDirect3DTexture8* texture(unsigned layer)noexcept{return textures_[layer];}
};

template<class Writer> inline HRESULT restore_pending(Pilot& p,IDirect3DDevice8& n,Writer&& notify) noexcept {
    auto& s=p.pending;HRESULT result=S_OK;
    constexpr D3DTEXTURESTAGESTATETYPE body_keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_RESULTARG,D3DTSS_ALPHAARG2};
    for(unsigned i=0;i<8;++i)if(s.body_pending&(1u<<i)){const auto hr=i==7?n.SetRenderState(D3DRS_TEXTUREFACTOR,s.body_factor):n.SetTextureStageState(2,body_keys[i],s.body_stage[i]);
        if(i==7)notify(50,pack(D3DRS_TEXTUREFACTOR,s.body_factor),hr);else notify(63,pack(2,body_keys[i],s.body_stage[i]),hr);
        if(SUCCEEDED(hr))s.body_pending&=~(1u<<i);else if(SUCCEEDED(result))result=hr;}
    auto check=[&](bool& pending,HRESULT hr){if(SUCCEEDED(hr))pending=false;else if(SUCCEEDED(result))result=hr;};
    if(s.fog_changed){auto a=pack(D3DRS_FOGCOLOR,s.fog);auto hr=n.SetRenderState(D3DRS_FOGCOLOR,s.fog);notify(50,a,hr);check(s.fog_changed,hr);}
    if(s.indices_changed){auto a=pack(s.indices,s.base);auto hr=n.SetIndices(s.indices,s.base);notify(85,a,hr);check(s.indices_changed,hr);}
    if(s.stream_changed){auto a=pack(0,s.stream,s.stride);auto hr=n.SetStreamSource(0,s.stream,s.stride);notify(83,a,hr);check(s.stream_changed,hr);}
    if(s.texture_changed){auto a=pack(0,s.texture);auto hr=n.SetTexture(0,s.texture);notify(61,a,hr);check(s.texture_changed,hr);}
    if(!s.any())s.release();else p.disable();return result;
}
} // namespace gfx2::atmosphere
