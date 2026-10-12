#include "road_teleport_model.hpp"
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>

namespace {
using namespace gfx2;
using namespace gfx2::road_teleport;
int failures = 0;
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#x); ++failures; } } while (0)

road_target::LiveSnapshot snapshot() {
    road_target::LiveSnapshot s{};
    s.count = road_target::FRANCE1_MARKER_COUNT;
    s.stride = road_target::NATIVE_MARKER_STRIDE;
    s.position_offset = road_target::NATIVE_POSITION_OFFSET;
    s.race_generation = 7;
    s.owner_lifetime = 3;
    s.sequence = 8;
    s.fingerprint = 0x1234;
    s.native_route_object = 0x02D41000;
    s.native_position_begin = 0x02D42000;
    s.native_position_end = s.native_position_begin + s.count * s.stride;
    s.recovery_manager = 0x02D43000;
    s.native_thread_id = 19;
    s.source_native_live = s.exact_supported_course = s.capture_owner_current = s.available = true;
    s.markers[12] = {100.f, 50.f, -25.f};
    return s;
}
road_target::Preview preview(const road_target::LiveSnapshot& s) {
    road_target::Preview p{};
    p.found = p.route_candidate_valid = p.within_radius = true;
    p.marker_ordinal = 12;
    p.marker = s.markers[p.marker_ordinal];
    p.horizontal_distance = 8.5;
    p.world_distance = 9.0;
    p.reason = "nearest_live_marker";
    return p;
}
ArmFacts facts() {
    ArmFacts f{};
    f.enabled = f.exact_build = f.freecam_active = f.pause_known = f.paused = true;
    f.race_certificate = f.single_human_car_race = f.unique_current_human_controller = true;
    f.owner_gate_reason = "accepted";
    f.no_active_recovery = true;
    f.native_selection_contract_verified = true;
    f.race_generation = 7;
    f.owner_lifetime = 3;
    f.now_tick_ms = 1000;
    f.human_actor = 0x02D44000;
    f.human_controller = 0x02D44100;
    f.human_backing = 0x02D45000;
    f.human_identity_generation = 4;
    auto& owner = f.owner_evidence;
    owner.race_certificate_current = owner.single_human_car = true;
    owner.race_generation = owner.expected_race_generation = f.race_generation;
    owner.owner_lifetime = owner.expected_owner_lifetime = f.owner_lifetime;
    owner.participant_count = 1;
    owner.participant_index = 0;
    owner.participant_identity_verified = true;
    owner.participant_player_type = 1;
    owner.tracked_controllers = owner.human_controllers = 1;
    owner.physical_player_type = 1;
    owner.race_owner_actor = 0x02D44000;
    owner.physical_actor = f.human_actor;
    owner.controller = f.human_controller;
    owner.backing = f.human_backing;
    owner.links_readable = owner.links_stable = true;
    owner.track_generation = owner.current_track_generation = f.human_identity_generation;
    owner.current_apply_flag_readable = true;
    owner.recovery = {0x02D43000, 0, 1, 0x119BC270, 0, true, true};
    return f;
}
std::array<uint32_t,16> native_matrix(float x,float y,float z) {
    std::array<uint32_t,16> m{};
    const float values[16]={1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1};
    std::memcpy(m.data(),values,sizeof(values));
    return m;
}
NativeCallFacts native_facts(const road_teleport::Request& r) {
    NativeCallFacts f{};
    f.exact_build = f.race_context_current = f.unique_current_human_controller = true;
    f.no_active_recovery = f.route_snapshot_current = true;
    f.native_selection_contract_verified = true;
    f.recovery = r.owner_evidence.recovery;
    f.race_generation = r.race_generation;
    f.owner_lifetime = r.owner_lifetime;
    f.human_actor = r.human_actor;
    f.human_controller = r.human_controller;
    f.human_backing = r.human_backing;
    f.human_identity_generation = r.human_identity_generation;
    f.reset_manager = r.reset_manager;
    f.route_object = r.route_object;
    f.route_fingerprint = r.route_fingerprint;
    f.route_count = road_target::FRANCE1_MARKER_COUNT;
    f.native_thread_id = r.native_thread_id;
    f.participant_index = 0;
    f.now_tick_ms = 1200;
    return f;
}
void test_arm_gates() {
    auto s=snapshot();auto p=preview(s);auto f=facts();road_teleport::Request r{};
    road_teleport::initialize(r,false);
    CHECK(!road_teleport::arm(r,1,f,s,p).accepted&&r.state==road_teleport::State::Rejected);
    road_teleport::initialize(r,true);f=facts();f.exact_build=false;
    CHECK(road_teleport::arm(r,2,f,s,p).reason==std::string("exact_retail_build_required"));
    road_teleport::initialize(r,true);f=facts();f.paused=false;
    CHECK(road_teleport::arm(r,3,f,s,p).reason==std::string("verified_pause_required"));
    road_teleport::initialize(r,true);f=facts();f.single_human_car_race=false;
    CHECK(road_teleport::arm(r,4,f,s,p).reason==std::string("single_human_car_race_required"));
    road_teleport::initialize(r,true);f=facts();f.unique_current_human_controller=false;
    f.owner_gate_reason = "controller_owner_mismatch";
    f.owner_evidence.human_controllers = 0;
    CHECK(road_teleport::arm(r,5,f,s,p).reason==std::string("unique_current_human_controller_required"));
    CHECK(std::strcmp(r.owner_gate_reason,"controller_owner_mismatch")==0);
    road_teleport::initialize(r,true);f=facts();f.no_active_recovery=false;
    CHECK(road_teleport::arm(r,6,f,s,p).reason==std::string("native_recovery_already_active"));
    road_teleport::initialize(r,true);f=facts();p.height_ambiguous=true;
    CHECK(!road_teleport::arm(r,7,f,s,p).accepted);
    p=preview(s);p.horizontal_distance=20.01;
    CHECK(road_teleport::arm(r,8,f,s,p).reason==std::string("selected_marker_exceeds_teleport_radius"));
    p=preview(s);p.marker_ordinal=road_target::FRANCE1_MARKER_COUNT;
    CHECK(!road_teleport::arm(r,9,f,s,p).accepted);
    p=preview(s);f.maximum_horizontal_distance=0;
    CHECK(road_teleport::arm(r,10,f,s,p).reason==std::string("road_target_radius_out_of_range"));
    f=facts();f.owner_evidence.tracked_controllers=4;
    f.owner_evidence.cached_apply_flag_known=f.owner_evidence.cached_apply_flag_set=true;
    f.owner_evidence.current_apply_flag_readable=true;f.owner_evidence.current_apply_flag=0;
    road_teleport::initialize(r,true);
    CHECK(road_teleport::arm(r,11,f,s,p).accepted);
    CHECK(r.owner_evidence.cached_apply_flag_set&&r.owner_evidence.current_apply_flag==0);
}
void test_selection_and_stock_fail_closed() {
    auto s=snapshot();auto p=preview(s);auto f=facts();road_teleport::Request r{};
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,1,f,s,p).accepted);
    CHECK(std::strcmp(r.owner_gate_reason,"accepted")==0);
    auto c=native_facts(r);uint32_t marker=4;
    c.participant_index=1;
    auto rejected=road_teleport::select_native_destination(r,c,marker);
    CHECK(!rejected.changed&&marker==4&&r.state==road_teleport::State::Cancelled);
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,2,f,s,p).accepted);
    c=native_facts(r);c.reset_manager++;
    marker=4;CHECK(!road_teleport::select_native_destination(r,c,marker).changed&&marker==4);
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,3,f,s,p).accepted);
    c=native_facts(r);c.route_fingerprint++;
    marker=4;CHECK(!road_teleport::select_native_destination(r,c,marker).changed&&marker==4);
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,4,f,s,p).accepted);
    c=native_facts(r);c.now_tick_ms=r.deadline_tick_ms;
    marker=4;CHECK(!road_teleport::select_native_destination(r,c,marker).changed&&marker==4&&r.state==road_teleport::State::Expired);
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,5,f,s,p).accepted);
    c=native_facts(r);marker=4;
    auto admitted=road_teleport::select_native_destination(r,c,marker);
    CHECK(admitted.changed&&admitted.original_ordinal==4&&admitted.selected_ordinal==12&&marker==12);
    CHECK(r.state==road_teleport::State::DestinationOverridden&&r.input_overridden);
    CHECK(!road_teleport::commit_matrix(r,r.reset_manager,0,native_matrix(100.f,50.f,-25.f)));
    uint32_t returned_ordinal=12;
    CHECK(road_teleport::observe_native_adjustment(r,returned_ordinal));
    auto once=road_teleport::select_native_destination(r,c,marker);
    CHECK(!once.changed&&marker==12);

    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,6,f,s,p).accepted);
    c=native_facts(r);marker=4;
    CHECK(road_teleport::select_native_destination(r,c,marker).changed);
    returned_ordinal=11;
    CHECK(!road_teleport::observe_native_adjustment(r,returned_ordinal));
    CHECK(returned_ordinal==11);
    CHECK(r.state==road_teleport::State::CommitMismatch&&marker==12);
    CHECK(!road_teleport::commit_matrix(r,r.reset_manager,0,native_matrix(100.f,50.f,-25.f)));

    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,7,f,s,p).accepted);
    c=native_facts(r);c.human_backing++;
    marker=4;
    CHECK(!road_teleport::select_native_destination(r,c,marker).changed&&marker==4);
    CHECK(r.state==road_teleport::State::Cancelled);
}
void test_stock_matrix_and_transaction_completion() {
    auto s=snapshot();auto p=preview(s);auto f=facts();road_teleport::Request r{};
    uint32_t returned_ordinal=12;
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,10,f,s,p).accepted);
    auto c=native_facts(r);uint32_t marker=0;
    CHECK(road_teleport::select_native_destination(r,c,marker).changed);
    returned_ordinal=12;
    CHECK(road_teleport::observe_native_adjustment(r,returned_ordinal));
    // Native road placement may adjust Y through its own surface query; no
    // inferred fixed vertical offset is used for the target check.
    auto m=native_matrix(100.f,51.004f,-25.f);
    CHECK(road_teleport::commit_matrix(r,r.reset_manager,0,m));
    CHECK(r.state==road_teleport::State::DestinationCommitted&&r.matrix_matches_target);
    auto wrong_position=r;
    CHECK(!road_teleport::observe_native_consumption(wrong_position,0x02D45000,m,{99,51,-25},true,1));
    auto inactive=r;
    CHECK(!road_teleport::observe_native_consumption(inactive,0x02D45000,m,{100,51,-25},false,1));
    CHECK(inactive.state==road_teleport::State::DestinationCommitted);
    CHECK(road_teleport::observe_native_consumption(r,0x02D45000,m,{100,51,-25},true,1));
    CHECK(r.state==road_teleport::State::NativeConsumed&&r.chassis_matches_destination);
    CHECK(!road_teleport::observe_clear(r,0x02D45000,0x00591345,0,0));
    CHECK(!road_teleport::observe_clear(r,0x02D45000,0x00591345,1,1));
    auto timer_clear = r;
    CHECK(road_teleport::observe_clear(timer_clear,0x02D45000,0x004CD1DE,1,0));
    CHECK(std::string(timer_clear.clear_writer)=="reset_timer_0x004CD1DE");
    CHECK(road_teleport::observe_clear(r,0x02D45000,0x00591345,1,0));
    CHECK(!road_teleport::observe_settled_zero(r,0x02D45000,1));
    CHECK(road_teleport::observe_settled_zero(r,0x02D45000,0));
    CHECK(r.state==road_teleport::State::Completed&&r.native_consumed&&r.native_clear_seen&&r.settled_zero_seen);

    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,12,f,s,p).accepted);
    c=native_facts(r);marker=0;CHECK(road_teleport::select_native_destination(r,c,marker).changed);
    returned_ordinal=12;
    CHECK(road_teleport::observe_native_adjustment(r,returned_ordinal));
    CHECK(road_teleport::commit_matrix(r,r.reset_manager,0,m));
    CHECK(!road_teleport::observe_native_consumption(r,0x02D45000,m,{100,51,-25},true,2));
    CHECK(r.active_consumer_calls==2&&std::string(r.reason)=="native_consumer_count_not_exclusive");
    CHECK(r.state==road_teleport::State::CommitMismatch);
    CHECK(!road_teleport::observe_clear(r,0x02D45000,0x00591345,1,0));
    CHECK(!road_teleport::observe_settled_zero(r,0x02D45000,0));

    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,11,f,s,p).accepted);
    c=native_facts(r);marker=0;CHECK(road_teleport::select_native_destination(r,c,marker).changed);
    returned_ordinal=12;
    CHECK(road_teleport::observe_native_adjustment(r,returned_ordinal));
    m=native_matrix(101.f,50.f,-25.f);
    CHECK(!road_teleport::commit_matrix(r,r.reset_manager,0,m));
    CHECK(r.state==road_teleport::State::CommitMismatch&&!r.matrix_matches_target);
}
void test_expiry_cancel_and_identity_lifetime() {
    auto s=snapshot();auto p=preview(s);auto f=facts();road_teleport::Request r{};
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,20,f,s,p).accepted);
    road_teleport::invalidate_generation(r,8,3);
    CHECK(r.state==road_teleport::State::Cancelled&&std::string(r.reason)=="race_or_owner_generation_changed");
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,21,f,s,p).accepted);
    CHECK(road_teleport::expire(r,r.deadline_tick_ms));
    CHECK(r.state==road_teleport::State::Expired);
    road_teleport::initialize(r,true);CHECK(road_teleport::arm(r,22,f,s,p).accepted);
    road_teleport::cancel(r,"device_release");
    CHECK(r.state==road_teleport::State::Cancelled);
    road_teleport::initialize(r,true);
    CHECK(r.state==road_teleport::State::Idle&&!r.input_overridden);
}
}

int main() {
    test_arm_gates();
    test_selection_and_stock_fail_closed();
    test_stock_matrix_and_transaction_completion();
    test_expiry_cancel_and_identity_lifetime();
    if (failures) return 1;
    std::puts("road teleport state-machine contracts PASS");
    return 0;
}
