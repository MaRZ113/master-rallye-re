#pragma once
// RACE-CERT2 contracts (docs/race-cert2/README.md). Included by ps2_hud_damage_tests.cpp after FakeMemory/CHECK.
#include "ps2_race_certificate.hpp"
#include <iostream>

// A complete read-only native world for the baseline read_race_owner(), the typed broker and the camera.
struct CertWorld {
    FakeMemory m;const uint32_t base=0x400000;
    static constexpr uint32_t broker=0x90000,records=0x100000,payloads=0x200000,manager=0x300000,actor=0x310000,ai=0x320000,arrays=0x330000;
    static constexpr uint32_t camera=0x5000,cars=4;
    static uint32_t player_type_id(uint32_t i){return 9+2*i;}
    static uint32_t race_state_id(uint32_t i){return 10+2*i;}
    CertWorld(){
        const uint32_t n=9+2*cars;
        for(uint32_t i=0;i<9;++i)m.ids[RACE_CONTEXT_KEYS[i]]=i;
        for(uint32_t i=0;i<cars;++i){m.ids["Race/Car"+std::to_string(i)+"/PlayerType"]=player_type_id(i);m.ids["Race/Car"+std::to_string(i)+"/RaceState"]=race_state_id(i);}
        m.ids["RaceLimits"]=0;
        m.u32(base+0x2f9410,broker);m.u32(broker+4,records);m.u32(broker+8,records+n*0x1c);m.u32(broker+12,records+n*0x1c);
        for(uint32_t i=0;i<n;++i){m.u32(records+i*0x1c,i);m.u32(records+i*0x1c+4,payloads+i*0x10);m.u32(records+i*0x1c+8,i<9?RACE_CONTEXT_TAGS[i]:2);m.u32(payloads+i*0x10,0);}
        // RaceLimits registry: one registration of the actor, actor/AI identity, pending list empty, one live list membership.
        const uint32_t registry=0x301000,bucket=0x303000;
        m.u32(base+0x2f96fc,manager);m.u32(manager+0x1c,registry);m.u32(registry+4,0x302000);m.u32(registry+8,0x302004);m.u32(registry+12,0x302004);
        m.u32(0x302000,bucket);m.u32(bucket+4,0x304000);m.u32(bucket+8,0x304004);m.u32(bucket+12,0x304004);m.u32(0x304000,actor);
        m.u32(actor,0);m.u32(actor+4,ai);m.u32(actor+0x5c,0);m.u32(ai,base+0x29152c);
        m.u32(manager+0x14,manager+0x10);m.u32(manager+0x18,manager+0x10);
        for(uint32_t p=0;p<7;++p){const uint32_t head=manager+0x24+p*12;m.u32(head+4,head);m.u32(head+8,head);}
        const uint32_t live=manager+0x24,node=actor+0x60;m.u32(live+4,node);m.u32(live+8,node);m.u32(node,actor);m.u32(node+4,live);m.u32(node+8,live);
        for(uint32_t o:{0x20u,0x24u,0x30u,0x34u,0x38u,0x3cu,0x40u})m.u32(ai+o,arrays);
        for(uint32_t i=0;i<8;++i)m.u32(arrays+i*4,0);
        for(uint32_t o:{0x10u,0x14u,0x18u,0x1cu})m.u32(ai+o,0x340000);
        const uint32_t cm=0x91000,holder=0x92000,inner=0x93000;
        m.u32(base+CAMERA_MANAGER_RVA,cm);m.u32(cm+16,1);m.u32(cm,camera);
        m.u32(base+RENDERER_HOLDER_RVA,holder);m.u32(holder+0x38,inner);m.u32(inner+4,camera);
        race(2,4);
    }
    void field(uint32_t i,int32_t v){m.u32(payloads+i*0x10,static_cast<uint32_t>(v));}
    void count(uint32_t c){field(8,static_cast<int32_t>(c));m.u32(ai+0x2c,c);}
    // Type 2 race with one local player (car 0) and AI cars.
    void race(int32_t type,uint32_t c){for(uint32_t i=0;i<9;++i)field(i,0);field(0,type);field(1,1);count(c);
        for(uint32_t i=0;i<cars;++i){field(player_type_id(i),i?2:1);field(race_state_id(i),2);}}
    void attract(){for(uint32_t i=0;i<9;++i)field(i,0);field(0,14);field(4,1);count(4);
        for(uint32_t i=0;i<cars;++i){field(player_type_id(i),2);field(race_state_id(i),0);}}
    void state(uint32_t car,int32_t v){field(race_state_id(car),v);}
};
inline RaceCertificate cert_base(const char* reason,bool valid=false){
    RaceCertificate c;c.valid=valid;c.reason=reason;c.race_generation=22;c.owner_lifetime=4;c.actor=CertWorld::actor;c.ai=CertWorld::ai;
    if(valid){c.camera=CertWorld::camera;std::snprintf(c.course_id.data(),c.course_id.size(),"RaceTest/France1");}
    return c;
}
inline std::string cert_snapshot(uint64_t generation=22,uint64_t owner=4,uint64_t root=25,uint64_t execution=25,const char* scene="Racetest/france2",
                                 bool poisoned=false,bool course=true,uint32_t actor=CertWorld::actor){
    return "{\"type\":\"race_epoch_snapshot\",\"phase\":\"R-CAM1-A3e\",\"device\":0,\"frame\":0,\"capture_id\":null,\"read_only\":true,"
        "\"live_certificate_reason\":\"unsupported_race_or_player_configuration\",\"course_identity_verified\":"+std::string(course?"true":"false")+
        ",\"state\":\"AWAITING_RACE_OWNER\",\"poisoned\":"+(poisoned?"true":"false")+",\"request_generation\":31,\"race_lifecycle_generation\":"+
        std::to_string(generation)+",\"successful_race_generation\":"+std::to_string(generation)+",\"execution_depth\":0,\"correlated_owner_candidate\":true,"
        "\"root_job_success\":{\"lifetime\":"+std::to_string(root)+",\"parent_job_lifetime\":0,\"request_origin\":4496527,\"scene\":\""+scene+
        "\",\"source\":\"DataScene/Racetest/france2.xml\",\"flag21\":1,\"flag22\":1,\"commit_seen\":true,\"commit_success\":true,\"terminal\":true,\"failed\":false},"
        "\"hud_job_success\":{\"lifetime\":26,\"parent_job_lifetime\":25,\"scene\":\"Hud/AttractMode\"},\"scene\":{\"read_complete\":true},"
        "\"owner\":{\"actor\":"+std::to_string(actor)+",\"ai\":"+std::to_string(CertWorld::ai)+",\"generation\":25,\"race_lifecycle_generation\":"+std::to_string(generation)+
        ",\"storage_readable\":true,\"native_live_unique\":true,\"temporal_match\":true,\"lifetime\":"+std::to_string(owner)+",\"execution_job_lifetime\":"+
        std::to_string(execution)+",\"initialized\":true,\"participant_states\":[0,0,0,0]},\"jobs\":[]}";
}
inline RaceHudContext attract_hud(uint64_t generation=22,uint64_t owner=4){
    RaceHudContext h;h.valid=true;h.attract=true;h.race_generation=generation;h.owner_lifetime=owner;h.reason="certified_attract_demo_hud";return h;
}

void race_certificate_parse_tests(){
    RaceCourseSnapshot s;
    CHECK(parse_race_course_snapshot(cert_snapshot(),s)&&!std::strcmp(s.course.data(),"Racetest/france2")&&s.race_generation==22&&
          s.owner_race_generation==22&&s.owner_lifetime==4&&s.root_lifetime==25&&s.owner_execution_job==25&&s.actor==CertWorld::actor&&s.ai==CertWorld::ai);
    CHECK(!parse_race_course_snapshot(cert_snapshot(22,4,25,25,"Racetest/france2",true),s));          // poisoned epoch
    CHECK(!parse_race_course_snapshot(cert_snapshot(22,4,25,25,"Racetest/france2",false,false),s));   // course job unverified
    CHECK(!parse_race_course_snapshot(cert_snapshot(22,4,25,25,"Hud/AttractMode"),s));                // not a RaceTest root
    CHECK(!parse_race_course_snapshot(cert_snapshot(22,4,25,25,"RaceTest/fr ance"),s));
    CHECK(!parse_race_course_snapshot("",s)&&!parse_race_course_snapshot("{\"type\":\"other\"}",s));
    CHECK(valid_course_text("RACETEST/Turkey3")&&!valid_course_text("RaceTest/")&&!valid_course_text("RaceTes/x"));
    CHECK(baseline_context_stage("network_attract_ghost_or_replay")&&!baseline_context_stage("lifecycle_ancestry_or_completion_unproven")&&
          !baseline_context_stage("supported_course_job_not_verified")&&!baseline_context_stage("registry_read_or_name_failed")&&!baseline_context_stage(nullptr));
}
void race_certificate_finished_tests(){
    CertWorld w;Ps2RaceCertifier c;unsigned snapshots=0,huds=0;
    auto hud=[&]{++huds;return RaceHudContext{};};auto snap=[&]{++snapshots;return std::string();};
    // Race: a valid baseline certificate is returned unchanged.
    auto r=c.certificate(cert_base("live_supported_course_offline_race_certificate",true),w.m,w.base,CertWorld::camera,hud,snap);
    CHECK(r.valid&&r.mode==Ps2RaceMode::Race&&!std::strcmp(r.reason,"live_supported_course_offline_race_certificate")&&!std::strcmp(r.course_id.data(),"RaceTest/France1"));
    // Still racing: the participant rejection is kept.
    const auto finished=cert_base(kParticipantStateReason);
    w.state(0,2);w.state(1,1);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(1,2);
    CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);                       // states 0/2: race context, baseline said no
    w.state(0,3);w.state(2,3);
    r=c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap);
    CHECK(r.valid&&r.mode==Ps2RaceMode::Finished&&!std::strcmp(r.reason,kPs2FinishedReason)&&r.race_generation==22&&r.owner_lifetime==4&&
          r.actor==CertWorld::actor&&r.ai==CertWorld::ai&&r.camera==CertWorld::camera&&!std::strcmp(r.course_id.data(),"RaceTest/France1")&&r.participant_count==4);
    CHECK(snapshots==0&&huds==0);                                                                        // course from the valid certificate
    CHECK(!c.certificate(finished,w.m,w.base,0x6000,hud,snap).valid);                                   // camera identity
    w.m.u32(0x91000+16,2);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(0x91000+16,1);
    w.state(3,7);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(3,2);  // unknown other state
    w.state(1,1);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(1,2);  // countdown state
    w.field(CertWorld::player_type_id(1),1);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);  // two locals
    w.field(CertWorld::player_type_id(1),2);
    w.field(6,1);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(6,0);  // replay stays rejected
    w.field(2,1);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(2,0);  // network
    // Owner and lifecycle proofs: never bypassed.
    CHECK(!c.certificate(cert_base("lifecycle_ancestry_or_completion_unproven"),w.m,w.base,CertWorld::camera,hud,snap).valid);
    CHECK(!c.certificate(cert_base("supported_course_job_not_verified"),w.m,w.base,CertWorld::camera,hud,snap).valid);
    auto other=finished;other.actor=0x311000;CHECK(!c.certificate(other,w.m,w.base,CertWorld::camera,hud,snap).valid);
    other=finished;other.ai=0x321000;CHECK(!c.certificate(other,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.m.u32(CertWorld::actor,2);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(CertWorld::actor,0);  // retired
    w.m.u32(0x304000,0x311000);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(0x304000,CertWorld::actor);
    w.count(3);w.field(8,4);CHECK(!c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);w.count(4);
    CHECK(c.certificate(finished,w.m,w.base,CertWorld::camera,hud,snap).valid);
    // A new owner lifetime (restart) needs its own course proof: the snapshot is empty, so it fails closed.
    other=finished;other.owner_lifetime=5;r=c.certificate(other,w.m,w.base,CertWorld::camera,hud,snap);
    CHECK(!r.valid&&!std::strcmp(r.reason,"ps2_course_identity_unproven")&&snapshots==1);
    // Single-car race: the finished certificate keeps the verified human participant.
    CertWorld s;s.race(1,1);s.state(0,3);Ps2RaceCertifier d;
    d.certificate(cert_base("live",true),s.m,s.base,CertWorld::camera,hud,snap);
    auto one=cert_base(kParticipantStateReason);one.single_human_car_race=true;one.participant_count=1;one.human_participant_index=0;
    r=d.certificate(one,s.m,s.base,CertWorld::camera,hud,snap);
    CHECK(r.valid&&r.single_human_car_race&&r.participant_count==1&&r.human_participant_index==0&&r.human_participant_identity_verified&&r.human_participant_player_type==1);
}
void race_certificate_attract_tests(){
    CertWorld w;w.attract();Ps2RaceCertifier c;unsigned snapshots=0;std::string json=cert_snapshot();RaceHudContext proof=attract_hud();
    auto hud=[&]{return proof;};auto snap=[&]{++snapshots;return json;};
    const auto base=cert_base("unsupported_race_or_player_configuration");
    auto r=c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap);
    CHECK(r.valid&&r.mode==Ps2RaceMode::Attract&&!std::strcmp(r.reason,kPs2AttractReason)&&!std::strcmp(r.course_id.data(),"Racetest/france2")&&
          r.camera==CertWorld::camera&&r.participant_count==4&&!r.single_human_car_race&&!r.human_participant_identity_verified);
    CHECK(c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid&&snapshots==1);                // one snapshot per owner
    CHECK(!c.certificate(base,w.m,w.base,0x6000,hud,snap).valid);                                        // camera identity
    proof.race_generation=21;CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);
    proof=attract_hud(22,5);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);
    proof=attract_hud();proof.attract=false;CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);
    proof=attract_hud();
    w.field(5,1);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(5,0);   // ghost
    w.field(6,1);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(6,0);   // replay
    w.field(3,1);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(3,0);   // network sync
    w.field(1,1);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(1,0);   // a player
    w.state(2,3);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(2,0);   // demo states 0/2 only
    w.m.u32(CertWorld::ai,0);CHECK(!c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(CertWorld::ai,w.base+0x29152c);
    CHECK(c.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);
    // Course snapshot must match generation, owner, actor and the root job of the owner.
    for(const auto& bad:{cert_snapshot(21),cert_snapshot(22,5),cert_snapshot(22,4,25,24),cert_snapshot(22,4,25,25,"Racetest/france2",false,true,0x311000)}){
        Ps2RaceCertifier e;json=bad;r=e.certificate(base,w.m,w.base,CertWorld::camera,hud,snap);
        CHECK(!r.valid&&!std::strcmp(r.reason,"ps2_course_identity_unproven"));
        json=cert_snapshot();CHECK(!e.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid);   // no retry before kCourseRetryCalls
    }
    Ps2RaceCertifier e;json="";e.certificate(base,w.m,w.base,CertWorld::camera,hud,snap);json=cert_snapshot();
    for(uint64_t i=0;i+1<Ps2RaceCertifier::kCourseRetryCalls;++i)e.certificate(base,w.m,w.base,CertWorld::camera,hud,snap);
    CHECK(e.certificate(base,w.m,w.base,CertWorld::camera,hud,snap).valid&&e.snapshot_reads()==2);
}
// RACE-MODES1: opt-in competition (Types 5..8) and replay normalisation; every other proof unchanged.
void race_certificate_modes_tests(){
    CertWorld w;Ps2RaceCertifier off,on;on.configure(true);CHECK(on.all_modes()&&!off.all_modes());
    std::string json=cert_snapshot();unsigned snapshots=0;auto hud=[]{return RaceHudContext{};};auto snap=[&]{++snapshots;return json;};
    const auto type=cert_base(kUnsupportedTypeReason),replay=cert_base("network_attract_ghost_or_replay");
    for(int32_t t:{5,6,7,8}){w.race(t,4);
        CHECK(!off.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
        const auto r=on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap);
        CHECK(r.valid&&r.mode==Ps2RaceMode::Competition&&!std::strcmp(r.reason,kPs2CompetitionReason)&&r.participant_count==4&&
              r.camera==CertWorld::camera&&!std::strcmp(r.course_id.data(),"Racetest/france2")&&!r.single_human_car_race);}
    CHECK(snapshots==1);                                                                                  // one course proof per owner
    for(int32_t t:{0,1,3,4,9,14}){w.race(t,4);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);}
    // FinishingType: 0 for every competition, 1 only for Challenge.
    w.race(7,4);w.field(7,1);CHECK(on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.field(7,2);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.race(6,4);w.field(7,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    // Baseline rules still apply on the normalised context: players, network, ghost, attract, participant count, camera, owner.
    w.race(5,4);w.field(1,2);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(1,1);
    w.field(2,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(2,0);
    w.field(5,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(5,0);
    w.field(8,3);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(8,4);
    CHECK(!on.certificate(type,w.m,w.base,0x6000,hud,snap).valid);
    CHECK(!on.certificate(cert_base("lifecycle_ancestry_or_completion_unproven"),w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.m.u32(CertWorld::actor,2);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(CertWorld::actor,0);
    w.state(1,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(1,2);  // countdown: no camera certificate
    CHECK(on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    // Finished phase of a competition.
    w.state(0,3);auto r=on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap);CHECK(r.valid&&r.mode==Ps2RaceMode::Finished);
    CHECK(!off.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(0,2);
    // Replay playback of a Quick Race and of a competition.
    w.race(2,4);w.field(6,1);CHECK(!off.certificate(replay,w.m,w.base,CertWorld::camera,hud,snap).valid);
    r=on.certificate(replay,w.m,w.base,CertWorld::camera,hud,snap);CHECK(r.valid&&r.mode==Ps2RaceMode::Replay&&!std::strcmp(r.reason,kPs2ReplayReason));
    w.race(6,4);w.field(6,1);r=on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap);CHECK(r.valid&&r.mode==Ps2RaceMode::Replay);
    w.field(6,2);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    // A context normalisation never stands in for a camera rejection of an otherwise supported race.
    w.race(2,4);w.field(6,1);CHECK(!on.certificate(cert_base("single_camera_identity_not_verified"),w.m,w.base,CertWorld::camera,hud,snap).valid);
    // Attract keeps its own rule.
    w.attract();r=on.certificate(type,w.m,w.base,CertWorld::camera,[]{return attract_hud();},snap);CHECK(r.valid&&r.mode==Ps2RaceMode::Attract);
    // HUD context for a competition race: baseline HUD rules on the normalised fields.
    RaceScalar pause;pause.present=true;pause.tag=0;pause.value=0;
    RaceHudContext base_hud;base_hud.reason=kUnsupportedTypeReason;base_hud.race_generation=22;base_hud.owner_lifetime=4;
    w.race(8,4);auto h=on.hud(base_hud,type,w.m,w.base,pause);
    CHECK(h.valid&&!h.paused&&h.pause_known&&!h.attract&&!h.replay&&!h.startup_countdown&&!std::strcmp(h.reason,kPs2CompetitionHudReason));
    CHECK(!off.hud(base_hud,type,w.m,w.base,pause).valid);
    pause.present=false;CHECK(!on.hud(base_hud,type,w.m,w.base,pause).valid);pause.present=true;
    w.field(CertWorld::player_type_id(2),1);CHECK(!on.hud(base_hud,type,w.m,w.base,pause).valid);w.field(CertWorld::player_type_id(2),2);
    for(uint32_t i=0;i<4;++i)w.state(i,1);
    CHECK(!on.hud(base_hud,type,w.m,w.base,pause,false).valid);
    h=on.hud(base_hud,type,w.m,w.base,pause,true);CHECK(h.valid&&h.startup_countdown);
    for(uint32_t i=0;i<4;++i)w.state(i,2);
    auto stale=type;stale.owner_lifetime=5;CHECK(!on.hud(base_hud,stale,w.m,w.base,pause).valid);
    w.race(3,4);CHECK(!on.hud(base_hud,type,w.m,w.base,pause).valid);
    auto other=base_hud;other.reason="race_hud_lifecycle_not_proven";w.race(8,4);CHECK(!on.hud(other,type,w.m,w.base,pause).valid);
    // Normalisation helper.
    std::array<RaceScalar,9> f{};for(size_t i=0;i<f.size();++i){f[i].present=true;f[i].tag=RACE_CONTEXT_TAGS[i];}
    f[0].value=7;f[7].value=1;f[6].value=1;auto n=normalise_race_mode(f,true);CHECK(n.competition&&n.replay&&f[0].value==2&&f[7].value==0&&f[6].value==0);
    f[0].value=7;f[7].value=1;f[6].value=1;n=normalise_race_mode(f,false);CHECK(!n.competition&&!n.replay&&f[0].value==7);
    f[0].tag=0;n=normalise_race_mode(f,true);CHECK(!n.competition&&f[0].value==7);
    std::cout<<"RACE-MODES1 competition/replay certificates: PASS\n";
}
// SPLIT-SCREEN1: patched baseline lifecycle (Hud/Hud1 from selector 0x4aa0c1) and the opt-in split-screen certificate.
void race_certificate_split_tests(){
    for(const char* hud:{"Hud/Hud0","Hud/Hud1"})for(uint32_t origin:{0x4aa0c1u,0u}){
        RaceEpoch e;e.generation=6;e.request(9269,"RaceTest/Turkey2");e.queue(100,9269,12,true,1,1,"DataScene/RaceTest/Turkey2.xml");e.begin(100,true);
        e.attach(200,208,true);e.initialized(200,208,true);const auto race=e.race_generation;
        const std::string source=std::string("DataScene/")+hud+".xml";
        e.request(11413,hud,origin);e.queue(101,11413,13,true,1,0,source.c_str());CHECK((e.race_generation==race)==(origin!=0));
        e.commit(11413,true);e.end(100);e.admitted(200,true);e.begin(101,true);e.commit(11413,true);e.end(101);
        CHECK(e.correlated_owner_candidate()==(origin!=0)&&race_hud_scene_proven(e)==(origin!=0));
    }
    {RaceEpoch e;e.generation=6;e.request(9269,"RaceTest/Turkey2");e.queue(100,9269,12,true,1,1,"DataScene/RaceTest/Turkey2.xml");e.begin(100,true);
     e.attach(200,208,true);e.initialized(200,208,true);e.request(11413,"Hud/Hud2",0x4aa0c1);CHECK(!e.request_supported_hud);}
    CertWorld w;Ps2RaceCertifier off,on;on.configure(false,true);CHECK(on.split_screen()&&on.normalising()&&!on.all_modes()&&!off.split_screen());
    std::string json=cert_snapshot();auto hud=[]{return RaceHudContext{};};auto snap=[&]{return json;};
    const auto type=cert_base(kUnsupportedTypeReason);
    const uint32_t cm=0x91000,inner=0x93000,second=0x5100;
    auto split=[&](int32_t race_type,uint32_t cars){w.race(race_type,cars);w.field(1,2);w.field(CertWorld::player_type_id(1),1);
        w.m.u32(cm+16,2);w.m.u32(cm+4,second);w.m.u32(inner+4,CertWorld::camera);};
    for(int32_t t:{1,2}){split(t,t==1?2u:4u);
        CHECK(!off.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
        const auto r=on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap);
        CHECK(r.valid&&r.mode==Ps2RaceMode::SplitScreen&&!std::strcmp(r.reason,kPs2SplitReason)&&r.camera==CertWorld::camera&&!r.single_human_car_race);}
    // The second pass: its camera is current; a camera that is not current, not a slot, or a third camera fails.
    w.m.u32(inner+4,second);CHECK(on.certificate(type,w.m,w.base,second,hud,snap).valid);
    CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    CHECK(!on.certificate(type,w.m,w.base,0x6000,hud,snap).valid);w.m.u32(inner+4,CertWorld::camera);
    w.m.u32(cm+16,3);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.m.u32(cm+16,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(cm+16,2);
    w.m.u32(cm+4,CertWorld::camera);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.m.u32(cm+4,second);
    // Exactly two local drivers; three players, network, ghost and replay stay rejected.
    w.field(CertWorld::player_type_id(1),2);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.field(CertWorld::player_type_id(2),1);w.field(CertWorld::player_type_id(1),1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.field(CertWorld::player_type_id(2),2);CHECK(on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);
    w.field(1,3);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(1,2);
    w.field(2,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(2,0);
    w.field(5,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(5,0);
    w.field(6,1);CHECK(!on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.field(6,0);
    CHECK(!on.certificate(cert_base("lifecycle_ancestry_or_completion_unproven"),w.m,w.base,CertWorld::camera,hud,snap).valid);
    // Finished: either driver first.
    w.state(1,3);auto r=on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap);CHECK(r.valid&&r.mode==Ps2RaceMode::Finished);
    w.state(0,3);CHECK(on.certificate(type,w.m,w.base,CertWorld::camera,hud,snap).valid);w.state(0,2);w.state(1,2);
    // HUD context for the Hud/Hud1 race.
    RaceScalar pause;pause.present=true;pause.tag=0;pause.value=0;
    RaceHudContext base_hud;base_hud.reason=kUnsupportedTypeReason;base_hud.race_generation=22;base_hud.owner_lifetime=4;
    auto h=on.hud(base_hud,type,w.m,w.base,pause);CHECK(h.valid&&!std::strcmp(h.reason,kPs2SplitHudReason)&&!h.attract&&!h.replay);
    CHECK(!off.hud(base_hud,type,w.m,w.base,pause).valid);
    w.field(CertWorld::player_type_id(1),2);CHECK(!on.hud(base_hud,type,w.m,w.base,pause).valid);w.field(CertWorld::player_type_id(1),1);
    w.state(1,7);CHECK(!on.hud(base_hud,type,w.m,w.base,pause).valid);w.state(1,2);
    // Split normalisation needs the key; a one-player race is never touched by it.
    std::array<RaceScalar,9> f{};for(size_t i=0;i<f.size();++i){f[i].present=true;f[i].tag=RACE_CONTEXT_TAGS[i];}
    f[0].value=1;f[1].value=2;auto n=normalise_race_mode(f,false,true);CHECK(n.split&&f[0].value==2&&f[1].value==1);
    f[0].value=1;f[1].value=2;n=normalise_race_mode(f,true,false);CHECK(!n.split&&f[1].value==2);
    f[0].value=1;f[1].value=1;n=normalise_race_mode(f,false,true);CHECK(!n.split&&f[0].value==1);
    f[0].value=6;f[1].value=2;n=normalise_race_mode(f,false,true);CHECK(!n.split);
    std::cout<<"SPLIT-SCREEN1 lifecycle and split-screen certificates: PASS\n";
}
void race_certificate_hud_tests(){
    CertWorld w;Ps2RaceCertifier c;w.state(0,3);
    RaceScalar pause;pause.present=true;pause.tag=0;pause.value=1;
    RaceHudContext finished;finished.reason=kParticipantStateReason;finished.race_generation=22;finished.owner_lifetime=4;
    const auto any=cert_base(kParticipantStateReason);
    auto h=c.hud(finished,any,w.m,w.base,pause);
    CHECK(h.valid&&h.paused&&h.pause_known&&!h.attract&&!h.startup_countdown&&h.race_generation==22&&!std::strcmp(h.reason,kPs2FinishedHudReason));
    pause.present=false;h=c.hud(finished,any,w.m,w.base,pause);CHECK(h.valid&&!h.pause_known&&!h.paused);
    w.state(0,2);CHECK(!c.hud(finished,any,w.m,w.base,pause).valid);w.state(0,3);                        // local still racing
    auto stale=any;stale.owner_lifetime=5;CHECK(!c.hud(finished,stale,w.m,w.base,pause).valid);
    CHECK(!c.hud(finished,cert_base("lifecycle_ancestry_or_completion_unproven"),w.m,w.base,pause).valid);
    auto unrelated=finished;unrelated.reason="race_hud_lifecycle_not_proven";CHECK(!c.hud(unrelated,any,w.m,w.base,pause).valid);
    const auto attract=attract_hud();h=c.hud(attract,any,w.m,w.base,pause);CHECK(h.valid&&h.attract&&!std::strcmp(h.reason,"certified_attract_demo_hud"));
    race_certificate_modes_tests();
    race_certificate_split_tests();
}
