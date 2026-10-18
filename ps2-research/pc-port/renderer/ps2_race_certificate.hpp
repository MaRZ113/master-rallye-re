#pragma once
// RACE-CERT2: overlay-owned race certificate for every PS2 path (docs/race-cert2/README.md).
//
// The frozen baseline certificate (race_epoch.cpp check_live_race_certificate) runs, in order: owner registry,
// lifecycle ancestry, supported course job, offline context, single camera, course copy. The overlay never
// touches the baseline RaceEpoch. It takes the baseline result and, only when the baseline got past the owner,
// lifecycle and course steps THIS call (its reason is a context or camera reason), redoes the remaining steps
// itself from read-only proofs:
//   * owner: the baseline read_race_owner() for the same actor/AI/owner lifetime/race generation;
//   * context: the nine typed Race/* fields through the baseline broker reader;
//   * camera: manager count 1, selected == expected == renderer-holder current (baseline rule);
//   * course id: the valid baseline certificate, or the root job text of one exported baseline snapshot
//     (race_epoch_capture_json) per race generation/owner, checked against the same identities.
// It admits exactly three modes:
//   race     - a valid baseline certificate, returned unchanged;
//   finished - baseline context with only the participant-state bit normalised: the unique local
//              (PlayerType 1) participant is in RaceState 3, every other one in 0, 2 or 3;
//   attract  - the baseline Attract context (Type 14, no players, AttractMode 1) plus the baseline Attract HUD
//              scene proof for the same race generation and owner.
// RACE-MODES1 (opt-in PS2RaceAllModes=1, docs/race-modes1): before the baseline context rules run, two context
// fields may be normalised; every other proof (owner, lifecycle, course, participants, single camera) is unchanged:
//   competition - Race/Type 5 Master Rallye, 6 Rallye Cup, 7 Challenge, 8 Invitation (R-AI1.2 mode map, one
//                 human driver) are checked as Type 2 Quick Race; Challenge may use FinishingType 1;
//   replay      - Race/PlaybackReplay 1 is checked as 0, as the baseline replay HUD context already does.
// SPLIT-SCREEN1 (opt-in PS2SplitScreen=1, docs/split-screen1): Race/NumPlayers 2 with Type 1 or 2 (the 0x4aa040
// selector's Hud/Hud1 race, accepted by the patched baseline lifecycle) is checked as one player of Type 2; it then
// needs exactly two local (PlayerType 1) participants and, instead of the single-camera rule, exactly two active
// manager cameras with the renderer's current camera being the requested one of them.
// Everything else returns the baseline result.
#include "race_epoch.hpp"
#include "game_fov.hpp"
#include "ps2_hud_damage_feed.hpp"
#include "ps2_perf_timing.hpp"
#include <array>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>

namespace gfx2::ps2port {

enum class Ps2RaceMode : uint8_t {None,Race,Finished,Attract,Competition,Replay,SplitScreen};
struct Ps2RaceCertificate : RaceCertificate {Ps2RaceMode mode=Ps2RaceMode::None;};

inline constexpr char kPs2FinishedReason[]="ps2_finished_phase_certificate";
inline constexpr char kPs2AttractReason[]="ps2_attract_demo_certificate";
inline constexpr char kPs2FinishedHudReason[]="ps2_finished_phase_hud_context";
inline constexpr char kParticipantStateReason[]="participant_race_state_not_active_or_starting";
inline constexpr char kPs2CompetitionReason[]="ps2_competition_mode_certificate";
inline constexpr char kPs2ReplayReason[]="ps2_replay_playback_certificate";
inline constexpr char kPs2CompetitionHudReason[]="ps2_competition_mode_hud_context";
inline constexpr char kUnsupportedTypeReason[]="unsupported_race_or_player_configuration";
inline constexpr char kPs2SplitReason[]="ps2_split_screen_certificate";
inline constexpr char kPs2SplitHudReason[]="ps2_split_screen_hud_context";

// RACE-MODES1 field normalisation; returns which rule applied. Fields keep their presence/tag.
struct Ps2ModeNormalisation {bool competition=false,replay=false,split=false;};
inline Ps2ModeNormalisation normalise_race_mode(std::array<RaceScalar,9>& f,bool enabled,bool split=false) noexcept {
    Ps2ModeNormalisation n;
    if(split&&f[0].present&&f[0].tag==RACE_CONTEXT_TAGS[0]&&(f[0].value==1||f[0].value==2)&&f[1].present&&f[1].tag==RACE_CONTEXT_TAGS[1]&&f[1].value==2){
        f[0].value=2;f[1].value=1;n.split=true;}
    if(!enabled)return n;
    if(f[0].present&&f[0].tag==RACE_CONTEXT_TAGS[0]&&f[0].value>=5&&f[0].value<=8&&f[7].present&&f[7].tag==RACE_CONTEXT_TAGS[7]&&
       (f[7].value==0||(f[0].value==7&&f[7].value==1))){f[0].value=2;f[7].value=0;n.competition=true;}
    if(f[6].present&&f[6].tag==RACE_CONTEXT_TAGS[6]&&f[6].value==1){f[6].value=0;n.replay=true;}
    return n;
}

// Baseline reasons that are only produced after owner registry, lifecycle and course job passed in that call.
inline bool baseline_context_stage(const char* reason) noexcept {
    static constexpr const char* stages[]={"missing_or_wrong_type_broker_entry","unsupported_race_or_player_configuration",
        "network_attract_ghost_or_replay","mode1_without_verified_single_car","participants_not_currently_ready",
        kParticipantStateReason,"single_camera_identity_not_verified"};
    if(!reason)return false;
    for(const char* stage:stages)if(!std::strcmp(reason,stage))return true;
    return false;
}
inline bool race_single_camera(RaceReadMemory& m,uint32_t base,uint32_t expected) noexcept {
    uint32_t manager=0,count=0,selected=0,holder=0,current=0;
    return expected&&m.read(base+CAMERA_MANAGER_RVA,&manager,4)&&manager&&m.read(manager+16,&count,4)&&count==1&&
        m.read(manager,&selected,4)&&selected==expected&&m.read(base+RENDERER_HOLDER_RVA,&holder,4)&&holder&&
        m.read(holder+0x38,&holder,4)&&holder&&m.read(holder+4,&current,4)&&current==selected;
}
// SPLIT-SCREEN1: manager slots +0x00..+0x0C, active count +0x10 (docs r-cam1-a); the frame scheduler 0x653080 binds
// each active camera through the renderer holder before its traversal, so the current camera names the pass.
inline bool race_split_camera(RaceReadMemory& m,uint32_t base,uint32_t expected) noexcept {
    uint32_t manager=0,count=0,first=0,second=0,holder=0,current=0;
    return expected&&m.read(base+CAMERA_MANAGER_RVA,&manager,4)&&manager&&m.read(manager+16,&count,4)&&count==2&&
        m.read(manager,&first,4)&&m.read(manager+4,&second,4)&&first&&second&&first!=second&&(expected==first||expected==second)&&
        m.read(base+RENDERER_HOLDER_RVA,&holder,4)&&holder&&m.read(holder+0x38,&holder,4)&&holder&&m.read(holder+4,&current,4)&&current==expected;
}
// Same shape as the baseline valid_race_root: "RaceTest/" (case folded) + 1..96 of [A-Za-z0-9_-].
inline bool valid_course_text(std::string_view text) noexcept {
    constexpr std::string_view prefix="racetest/";
    if(text.size()<=prefix.size()||text.size()-prefix.size()>96)return false;
    for(size_t i=0;i<prefix.size();++i){char c=text[i];if(c>='A'&&c<='Z')c=static_cast<char>(c-'A'+'a');if(c!=prefix[i])return false;}
    for(size_t i=prefix.size();i<text.size();++i){const char c=text[i];
        if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return false;}
    return true;
}

// The parts of race_epoch_capture_json() that identify the course root of the current owner.
struct RaceCourseSnapshot {
    uint64_t race_generation=0,root_lifetime=0,owner_race_generation=0,owner_lifetime=0,owner_execution_job=0;
    uint32_t actor=0,ai=0;std::array<char,128> course{};
};
inline bool snapshot_number(std::string_view json,std::string_view key,size_t from,size_t limit,uint64_t& value) noexcept {
    const size_t at=json.find(key,from);if(at==std::string_view::npos||at>=limit)return false;
    size_t p=at+key.size();if(p>=json.size()||json[p]<'0'||json[p]>'9')return false;
    value=0;for(;p<json.size()&&json[p]>='0'&&json[p]<='9';++p){const uint64_t digit=static_cast<uint64_t>(json[p]-'0');
        if(value>(UINT64_MAX-digit)/10)return false;value=value*10+digit;}
    return true;
}
inline bool parse_race_course_snapshot(std::string_view json,RaceCourseSnapshot& out) noexcept {
    out={};constexpr auto npos=std::string_view::npos;
    if(json.rfind("{\"type\":\"race_epoch_snapshot\"",0)!=0||json.find(",\"poisoned\":false,")==npos||
       json.find(",\"course_identity_verified\":true,")==npos)return false;
    constexpr std::string_view root_key=",\"correlated_owner_candidate\":true,\"root_job_success\":{\"lifetime\":";
    const size_t root=json.find(root_key);if(root==npos)return false;
    const size_t root_end=json.find('}',root+root_key.size());if(root_end==npos)return false;
    if(!snapshot_number(json,root_key,root,root+1,out.root_lifetime))return false;
    constexpr std::string_view scene_key=",\"scene\":\"";
    const size_t scene=json.find(scene_key,root);if(scene==npos||scene>=root_end)return false;
    const size_t scene_begin=scene+scene_key.size(),scene_end=json.find('"',scene_begin);
    if(scene_end==npos||scene_end>root_end||scene_end-scene_begin>=out.course.size())return false;
    const auto course=json.substr(scene_begin,scene_end-scene_begin);if(!valid_course_text(course))return false;
    std::memcpy(out.course.data(),course.data(),course.size());out.course[course.size()]=0;
    // The epoch's race generation directly follows its request generation.
    constexpr std::string_view generation_key=",\"race_lifecycle_generation\":";
    const size_t request=json.find(",\"request_generation\":");if(request==npos)return false;
    const size_t request_end=json.find(',',request+1);if(request_end==npos)return false;
    if(!snapshot_number(json,generation_key,request_end,request_end+1,out.race_generation))return false;
    constexpr std::string_view owner_key=",\"owner\":{\"actor\":";
    const size_t owner=json.find(owner_key);if(owner==npos)return false;
    const size_t owner_end=json.find('}',owner);if(owner_end==npos)return false;
    uint64_t actor=0,ai=0;
    if(!snapshot_number(json,owner_key,owner,owner+1,actor)||!snapshot_number(json,",\"ai\":",owner,owner_end,ai)||
       actor>UINT32_MAX||ai>UINT32_MAX||
       !snapshot_number(json,generation_key,owner,owner_end,out.owner_race_generation)||
       !snapshot_number(json,",\"lifetime\":",owner,owner_end,out.owner_lifetime)||
       !snapshot_number(json,",\"execution_job_lifetime\":",owner,owner_end,out.owner_execution_job))return false;
    out.actor=static_cast<uint32_t>(actor);out.ai=static_cast<uint32_t>(ai);
    return true;
}

class Ps2RaceCertifier {
public:
    struct Context {
        Ps2RaceMode mode=Ps2RaceMode::None;const char* reason="not_classified";
        RaceOwnerRead owner{};std::array<RaceScalar,9> fields{};uint32_t local=UINT32_MAX;Ps2ModeNormalisation normalised{};
    };
    void configure(bool all_modes,bool split=false) noexcept {all_modes_=all_modes;split_=split;}
    bool all_modes() const noexcept {return all_modes_;}
    bool split_screen() const noexcept {return split_;}
    bool normalising() const noexcept {return all_modes_||split_;}
    static constexpr uint64_t kCourseRetryCalls=600;

    // Context and participant classification after the baseline passed owner/lifecycle/course (pure on reads).
    static Context classify(const RaceCertificate& base,RaceReadMemory& m,uint32_t image,bool all_modes=false,bool split=false) noexcept {
        Context c;
        if(!baseline_context_stage(base.reason)){c.reason=base.reason;return c;}
        if(!base.race_generation||!base.owner_lifetime||!base.actor||!base.ai){c.reason="ps2_owner_identity_missing";return c;}
        RaceOwner identity{};identity.actor=base.actor;identity.ai=base.ai;identity.lifetime=base.owner_lifetime;
        identity.race_generation=base.race_generation;identity.initialized=identity.live=true;
        c.owner=read_race_owner(m,image,identity,base.race_generation);
        if(!c.owner.valid||!c.owner.storage_readable||!c.owner.native_live_unique||!c.owner.temporal_match||!c.owner.arrays_ready){
            c.reason=c.owner.reason;return c;}
        for(size_t i=0;i<c.fields.size();++i){uint32_t id=0;
            if(m.resolve_id(image,RACE_CONTEXT_KEYS[i],id))c.fields[i]=race_broker_scalar(m,image,id,RACE_CONTEXT_TAGS[i]);
            if(!c.fields[i].present||c.fields[i].tag!=RACE_CONTEXT_TAGS[i]){c.reason="missing_or_wrong_type_broker_entry";return c;}}
        if(c.fields[8].value<1||c.fields[8].value>8||static_cast<uint32_t>(c.fields[8].value)!=c.owner.count){
            c.reason="participants_not_currently_ready";return c;}
        const auto raw=c.fields;c.normalised=normalise_race_mode(c.fields,all_modes,split);
        const unsigned expected_locals=c.normalised.split?2u:1u;
        const auto race=check_race_context(c.fields,c.owner);
        if(race.supported){
            if(c.normalised.split){unsigned locals=0;
                for(uint32_t i=0;i<c.owner.count;++i){char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);uint32_t id=0;
                    if(!m.resolve_id(image,key,id)){c.reason="ps2_player_type_unreadable";return c;}
                    const auto type=race_broker_scalar(m,image,id,2);if(!type.present){c.reason="ps2_player_type_unreadable";return c;}
                    if(type.value==1)++locals;}
                if(locals!=2){c.reason="ps2_split_local_players_unproven";return c;}
                c.mode=Ps2RaceMode::SplitScreen;c.reason=kPs2SplitReason;return c;}
            if(c.normalised.replay){c.mode=Ps2RaceMode::Replay;c.reason=kPs2ReplayReason;}
            else if(c.normalised.competition){c.mode=Ps2RaceMode::Competition;c.reason=kPs2CompetitionReason;}
            else {c.mode=Ps2RaceMode::Race;c.reason=race.reason;}
            return c;}
        if(!std::strcmp(race.reason,kParticipantStateReason)){c.reason=race.reason;
            const char* states=c.owner.participant_states_reason;
            if(!states||!std::strcmp(states,"race_state_key_missing")||!std::strcmp(states,"race_state_value_unreadable_or_wrong_type"))return c;
            unsigned locals=0;
            for(uint32_t i=0;i<c.owner.count;++i){char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);uint32_t id=0;
                if(!m.resolve_id(image,key,id)){c.reason="ps2_player_type_unreadable";return c;}
                const auto type=race_broker_scalar(m,image,id,2);if(!type.present){c.reason="ps2_player_type_unreadable";return c;}
                const auto state=c.owner.participant_states[i];
                // Split screen: either driver may finish first; both keep the other-participant phases 0/2/3.
                if(type.value==1&&!c.normalised.split){++locals;c.local=i;if(state!=3){c.reason="ps2_local_participant_not_finished";return c;}}
                else {if(type.value==1){++locals;c.local=i;}if(state!=0&&state!=2&&state!=3){c.reason="ps2_participant_state_not_finished_phase";return c;}}
            }
            if(locals!=expected_locals){c.reason=c.normalised.split?"ps2_split_local_players_unproven":"ps2_single_local_participant_unproven";return c;}
            auto finished=c.owner;finished.participant_states_ready=true;
            const auto normalised=check_race_context(c.fields,finished);
            if(!normalised.supported){c.reason=normalised.reason;return c;}
            c.mode=Ps2RaceMode::Finished;c.reason=kPs2FinishedReason;return c;
        }
        if(check_race_attract_hud_context(raw,c.owner)){c.fields=raw;c.normalised={};c.mode=Ps2RaceMode::Attract;c.reason=kPs2AttractReason;return c;}
        c.reason=race.reason;return c;
    }

    // HudProof: () -> RaceHudContext (baseline live HUD context). Snapshot: () -> std::string (baseline capture json).
    template<class HudProof,class Snapshot>
    Ps2RaceCertificate certificate(const RaceCertificate& base,RaceReadMemory& m,uint32_t image,uint32_t camera,
                                   HudProof&& hud_proof,Snapshot&& snapshot) noexcept {
        ++calls_;Ps2RaceCertificate out;static_cast<RaceCertificate&>(out)=base;
        if(base.valid){out.mode=Ps2RaceMode::Race;remember_course(base);return out;}
        out.valid=false;
        const auto c=classify(base,m,image,all_modes_,split_);
        // A baseline-invalid certificate in the ordinary race context keeps the baseline rejection (camera).
        if(c.mode==Ps2RaceMode::None||c.mode==Ps2RaceMode::Race){if(c.mode==Ps2RaceMode::None&&baseline_context_stage(base.reason))out.reason=c.reason;return out;}
        // A competition/replay context only stands in for the baseline's own context rejection, never a camera one.
        if((c.mode==Ps2RaceMode::Competition||c.mode==Ps2RaceMode::Replay||c.mode==Ps2RaceMode::SplitScreen||(c.mode==Ps2RaceMode::Finished&&(c.normalised.competition||c.normalised.replay||c.normalised.split)))&&
           std::strcmp(base.reason,kUnsupportedTypeReason)&&std::strcmp(base.reason,"network_attract_ghost_or_replay")&&std::strcmp(base.reason,kParticipantStateReason)){
            out.reason=base.reason;return out;}
        if(c.mode==Ps2RaceMode::Attract){const RaceHudContext hud=hud_proof();
            if(!hud.valid||!hud.attract||hud.race_generation!=base.race_generation||hud.owner_lifetime!=base.owner_lifetime){
                out.reason="ps2_attract_hud_scene_not_proven";return out;}}
        if(c.normalised.split?!race_split_camera(m,image,camera):!race_single_camera(m,image,camera)){
            out.reason=c.normalised.split?"ps2_split_camera_identity_not_verified":"single_camera_identity_not_verified";return out;}
        if(!course_for(base,snapshot,out.course_id)){out.reason="ps2_course_identity_unproven";return out;}
        out.valid=true;out.camera=camera;out.mode=c.mode;out.reason=c.reason;
        out.participant_count=c.owner.count;
        if(c.mode==Ps2RaceMode::Finished&&out.single_human_car_race&&out.participant_count==1&&c.local==0){
            out.human_participant_index=0;out.human_participant_player_type=1;out.human_participant_identity_verified=true;}
        return out;
    }
    // HUD context: the baseline one, or the finished phase of a baseline-proven Hud/Hud0 race scene.
    // base_any_camera is live_race_certificate(0), read only after the baseline HUD path passed its thread check.
    // countdown_active: scene manager (base+0x2f9aa0)+12 > 0, read the way the baseline HUD path reads it.
    RaceHudContext hud(const RaceHudContext& base_hud,const RaceCertificate& base_any_camera,RaceReadMemory& m,uint32_t image,
                       const RaceScalar& pause,bool countdown_active=false) noexcept {
        if(base_hud.valid||!base_hud.reason)return base_hud;
        const bool participant_stage=!std::strcmp(base_hud.reason,kParticipantStateReason);
        // The baseline HUD path reports the race type only after the Hud/Hud0 scene, its lifecycle and the owner read passed.
        const bool type_stage=normalising()&&!std::strcmp(base_hud.reason,kUnsupportedTypeReason);
        if(!participant_stage&&!type_stage)return base_hud;
        if(!base_hud.race_generation||base_any_camera.race_generation!=base_hud.race_generation||
           base_any_camera.owner_lifetime!=base_hud.owner_lifetime)return base_hud;
        const auto c=classify(base_any_camera,m,image,all_modes_,split_);
        // Type stage: the baseline HUD rules already passed the participant phases, so only the race type differed.
        if(type_stage)return (c.normalised.competition||c.normalised.split)?competition_hud(base_hud,c,m,image,pause,countdown_active):base_hud;
        if(c.mode!=Ps2RaceMode::Finished)return base_hud;
        auto out=base_hud;out.valid=true;out.attract=false;out.replay=false;out.startup_countdown=false;
        out.pause_known=pause.present&&pause.tag==0;out.paused=out.pause_known&&pause.value!=0;out.reason=kPs2FinishedHudReason;
        return out;
    }
    uint64_t snapshot_reads() const noexcept {return snapshot_reads_;}
private:
    bool all_modes_=false,split_=false;
    // The baseline race HUD rules (race_observer.cpp live_race_hud_context) on the normalised competition fields.
    static RaceHudContext competition_hud(const RaceHudContext& base_hud,const Context& c,RaceReadMemory& m,uint32_t image,
                                          const RaceScalar& pause,bool countdown_active) noexcept {
        auto out=base_hud;
        if(!c.owner.valid||!c.owner.arrays_ready){return out;}
        const auto context=check_race_hud_context(c.fields,c.owner,countdown_active);
        if(!context.supported){out.reason=context.reason;return out;}
        unsigned locals=0;const unsigned expected=c.normalised.split?2u:1u;std::array<uint32_t,2> local{UINT32_MAX,UINT32_MAX};
        for(uint32_t i=0;i<c.owner.count;++i){char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);uint32_t id=0;
            if(!m.resolve_id(image,key,id)){out.reason="single_local_player_identity_unproven";return out;}
            const auto value=race_broker_scalar(m,image,id,2);if(!value.present){out.reason="single_local_player_identity_unproven";return out;}
            if(value.value==1){if(locals<local.size())local[locals]=i;++locals;}}
        if(locals!=expected){out.reason="single_local_player_identity_unproven";return out;}
        for(unsigned k=0;k<expected;++k)if(!race_hud_player_drawable(c.owner,local[k])){out.reason="local_player_not_in_hud_phase";return out;}
        if(!pause.present||pause.tag!=0){out.reason="pause_state_unknown";return out;}
        out.valid=true;out.attract=false;out.replay=context.replay;out.pause_known=true;out.paused=pause.value!=0;
        out.startup_countdown=race_hud_startup_phase(c.owner)&&countdown_active;out.reason=c.normalised.split?kPs2SplitHudReason:kPs2CompetitionHudReason;
        return out;
    }
    struct Course {uint64_t generation=0,owner=0;uint32_t actor=0,ai=0;bool known=false,ok=false;uint64_t retry_at=0;std::array<char,128> id{};};
    Course course_{};uint64_t calls_=0,snapshot_reads_=0;
    bool same_key(const RaceCertificate& c) const noexcept {
        return course_.known&&course_.generation==c.race_generation&&course_.owner==c.owner_lifetime&&course_.actor==c.actor&&course_.ai==c.ai;}
    void remember_course(const RaceCertificate& c) noexcept {
        if(!valid_course_text(c.course_id.data()))return;
        course_={};course_.generation=c.race_generation;course_.owner=c.owner_lifetime;course_.actor=c.actor;course_.ai=c.ai;
        course_.known=course_.ok=true;course_.id=c.course_id;
    }
    template<class Snapshot>bool course_for(const RaceCertificate& c,Snapshot& snapshot,std::array<char,128>& out) noexcept {
        if(same_key(c)&&(course_.ok||calls_<course_.retry_at)){if(course_.ok)out=course_.id;return course_.ok;}
        course_={};course_.generation=c.race_generation;course_.owner=c.owner_lifetime;course_.actor=c.actor;course_.ai=c.ai;
        course_.known=true;course_.retry_at=calls_+kCourseRetryCalls;++snapshot_reads_;
        const std::string json=snapshot();RaceCourseSnapshot s;
        if(!parse_race_course_snapshot(json,s)||s.race_generation!=c.race_generation||s.owner_race_generation!=c.race_generation||
           s.owner_lifetime!=c.owner_lifetime||s.actor!=c.actor||s.ai!=c.ai||!s.root_lifetime||s.root_lifetime!=s.owner_execution_job)return false;
        course_.ok=true;course_.id=s.course;out=s.course;return true;
    }
};

// Live reader: SEH-guarded reads plus the baseline's validated key-id cache (race_pool_text re-check per use).
class Ps2LiveRaceMemory final : public RaceReadMemory {
    struct Key {std::array<char,64> name{};uint32_t id=0;};std::array<Key,40> keys_{};size_t used_=0;
public:
    bool read(uint32_t address,void* output,size_t bytes) noexcept override {return hud_live_read(address,output,bytes);}
    bool resolve_id(uint32_t base,const char* key,uint32_t& id) noexcept override {
        if(!key||std::strlen(key)>63)return false;
        for(size_t i=0;i<used_;++i)if(!std::strcmp(keys_[i].name.data(),key)){
            char text[192]{};if(race_pool_text(*this,base,keys_[i].id,text,sizeof(text))&&!std::strcmp(text,key)){id=keys_[i].id;return true;}
            if(!race_pool_id(*this,base,key,id))return false;keys_[i].id=id;return true;
        }
        if(!race_pool_id(*this,base,key,id))return false;
        if(used_<keys_.size()){auto& k=keys_[used_++];std::memcpy(k.name.data(),key,std::strlen(key)+1);k.id=id;}
        return true;
    }
};

// Render-thread singletons used by every PS2 path in place of the baseline calls.
inline Ps2RaceCertifier& ps2_race_certifier() noexcept {static Ps2RaceCertifier state;return state;}
inline Ps2LiveRaceMemory& ps2_live_race_memory() noexcept {static Ps2LiveRaceMemory memory;return memory;}
inline Ps2RaceCertificate ps2_race_certificate(uintptr_t camera) noexcept {
    perf::Timer timer(perf::RaceCertificate);
    const auto base=live_race_certificate(camera);
    if(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=0x400000||camera>UINT32_MAX){
        Ps2RaceCertificate out;static_cast<RaceCertificate&>(out)=base;out.mode=base.valid?Ps2RaceMode::Race:Ps2RaceMode::None;return out;}
    // live_race_certificate passed its thread check whenever classify() proceeds, so the snapshot call is safe.
    return ps2_race_certifier().certificate(base,ps2_live_race_memory(),0x400000,static_cast<uint32_t>(camera),
        []() noexcept {return live_race_hud_context();},
        []() noexcept {try{return race_epoch_capture_json(0,0);}catch(...){return std::string();}});
}
inline RaceHudContext ps2_race_hud_context() noexcept {
    perf::Timer timer(perf::HudContext);
    const auto base=live_race_hud_context();
    const bool participant_stage=base.reason&&!std::strcmp(base.reason,kParticipantStateReason);
    const bool type_stage=base.reason&&ps2_race_certifier().normalising()&&!std::strcmp(base.reason,kUnsupportedTypeReason);
    if(base.valid||(!participant_stage&&!type_stage)||reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=0x400000)return base;
    // Only reached after the baseline HUD path passed its render-thread check.
    const auto any_camera=live_race_certificate(0);
    uint32_t scene_manager=0,countdown=0;
    const bool countdown_active=hud_live_read(0x400000+0x2f9aa0,&scene_manager,4)&&scene_manager&&hud_live_read(scene_manager+12,&countdown,4)&&countdown>0;
    return ps2_race_certifier().hud(base,any_camera,ps2_live_race_memory(),0x400000,read_pause_menu_state_readonly(),countdown_active);
}

}  // namespace gfx2::ps2port
