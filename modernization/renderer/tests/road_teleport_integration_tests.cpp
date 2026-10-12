#include <windows.h>
#include "road_teleport_events.hpp"
#include "road_teleport_bridge.hpp"
#include <cstdio>
#include <cstring>
#include <array>
using namespace gfx2;
using namespace gfx2::road_teleport;
using namespace gfx2::physics_probe;
namespace {
Request request;
TransactionCapture capture;
TransactionSample pending;
alignas(4) std::array<uint8_t,128> manager{},backing{},input_owner{};
alignas(4) std::array<uint32_t,2> countdown{};
std::array<uint32_t,16> destination{};
uint32_t native_input=0,native_result=0;
bool force_adjustment_mismatch=false,unreadable_zero=false,duplicate_consumer=false;
int failures=0;
#define CHECK(c) do{if(!(c)){std::fprintf(stderr,"FAIL %d: %s\n",__LINE__,#c);++failures;}}while(0)
uint32_t ptr(const void* p){return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(p));}
void word(std::array<uint8_t,128>& bytes,size_t offset,uint32_t value){std::memcpy(bytes.data()+offset,&value,4);}
bool read_word(uint32_t address,uint32_t& value) noexcept {
    const auto valid=[&](const void* p,size_t n){return uint64_t(address)>=ptr(p)&&uint64_t(address)+4<=uint64_t(ptr(p))+n;};
    if(!valid(manager.data(),manager.size())&&!valid(countdown.data(),sizeof(countdown)))return false;
    std::memcpy(&value,reinterpret_cast<void*>(address),4);return true;
}
ConsumerEvent consumer() {
    ConsumerEvent e{};e.race_generation=7;e.owner_lifetime=3;e.identity_generation=4;
    e.thread=GetCurrentThreadId();e.controller=0x30000;e.backing=ptr(backing.data());e.actor=0x40000;
    e.race_current=e.owner_current=e.human=true;e.flag=backing[0x33];
    e.flag_readable=!(unreadable_zero&&e.flag==0);
    e.matrix_readable=e.chassis_readable=true;
    std::memcpy(e.matrix.data(),backing.data()+0x34,64);
    std::memcpy(&e.chassis_after.x,&e.matrix[12],12);e.active_consumer_calls=duplicate_consumer?2:1;
    return e;
}
ArmFacts arm_facts() {
    ArmFacts f{};f.enabled=f.exact_build=f.freecam_active=f.pause_known=f.paused=true;
    f.race_certificate=f.single_human_car_race=f.unique_current_human_controller=true;
    f.native_selection_contract_verified=true;f.race_generation=7;f.owner_lifetime=3;f.now_tick_ms=1000;
    f.human_actor=0x40000;f.human_controller=0x30000;f.human_backing=ptr(backing.data());f.human_identity_generation=4;
    auto& o=f.owner_evidence;o.race_certificate_current=o.single_human_car=true;
    o.race_generation=o.expected_race_generation=7;o.owner_lifetime=o.expected_owner_lifetime=3;
    o.participant_count=1;o.participant_index=0;o.participant_identity_verified=true;o.participant_player_type=1;
    o.tracked_controllers=4;o.human_controllers=1;o.physical_player_type=1;
    o.race_owner_actor=0x20000;o.physical_actor=f.human_actor;o.controller=f.human_controller;o.backing=f.human_backing;
    o.links_readable=o.links_stable=true;o.track_generation=o.current_track_generation=4;
    o.current_apply_flag_readable=true;o.current_apply_flag=backing[0x33];
    o.recovery=read_recovery_manager(ptr(manager.data()),0,&read_word);
    f.no_active_recovery=evaluate_recovery_manager(o.recovery,RecoveryPhase::ArmIdle).accepted;
    return f;
}
road_target::LiveSnapshot route() {
    road_target::LiveSnapshot s{};s.count=road_target::FRANCE1_MARKER_COUNT;s.stride=0x48;s.position_offset=0x38;
    s.race_generation=7;s.owner_lifetime=3;s.sequence=8;s.native_route_object=0x50000;
    s.native_position_begin=0x60000;s.native_position_end=s.native_position_begin+s.count*s.stride;
    s.recovery_manager=ptr(manager.data());s.native_thread_id=GetCurrentThreadId();
    s.source_native_live=s.exact_supported_course=s.capture_owner_current=s.available=true;
    for(unsigned i=0;i<s.count;++i)s.markers[i]={float(i*20),50.f,-25.f};
    s.fingerprint=road_target::position_fingerprint(s.markers.data(),s.count);return s;
}
bool arm_current() {
    auto s=route();auto p=road_target::nearest_marker(s,{240,55,-25},20,7,3,true);
    return arm(request,1,arm_facts(),s,p).accepted;
}
void reset_fixture(bool enabled=true) {
    initialize(request,enabled);capture={};pending={};manager.fill(0);backing.fill(0);input_owner.fill(0);countdown.fill(0);
    word(manager,0x14,1);word(manager,0x50,ptr(countdown.data()));word(input_owner,0x2c,ptr(backing.data()));
    const float m[16]={1,0,0,0,0,1,0,0,0,0,1,0,240,51.004f,-25,1};std::memcpy(destination.data(),m,64);
    force_adjustment_mismatch=unreadable_zero=duplicate_consumer=false;native_input=native_result=0;
}
}
extern "C" {
uintptr_t road_teleport_adjust_original=0,physics_probe_restore_target=0;
uint32_t integration_manager=0,integration_backing=0,integration_input=0;
uint32_t integration_returned_result=0;
void road_teleport_adjust_bridge_observe(const RoadAdjustSaved* saved) noexcept {
    NativeCallFacts f{};f.exact_build=f.race_context_current=f.unique_current_human_controller=f.route_snapshot_current=true;
    f.native_selection_contract_verified=true;f.race_generation=7;f.owner_lifetime=3;f.now_tick_ms=1200;
    f.human_actor=0x40000;f.human_controller=0x30000;f.human_backing=ptr(backing.data());f.human_identity_generation=4;
    f.reset_manager=saved->esi;f.route_object=saved->route_object;f.participant_index=saved->participant_index;
    auto s=route();f.route_count=s.count;f.route_fingerprint=s.fingerprint;f.native_thread_id=GetCurrentThreadId();
    f.recovery=read_recovery_manager(saved->esi,saved->participant_index,&read_word);
    f.no_active_recovery=evaluate_recovery_manager(f.recovery,RecoveryPhase::NativeSelection).accepted;
    auto* argument=reinterpret_cast<uint32_t*>(saved->saved_esp+12);
    select_native_destination(request,f,*argument);
}
uint32_t __stdcall integration_native_adjust(uint32_t participant,uint32_t marker,uint32_t) {
    CHECK(participant==0);native_input=marker;
    return force_adjustment_mismatch?11:marker;
}
void road_teleport_adjust_bridge_after(RoadAdjustSaved* saved) noexcept {
    native_result=saved->eax;observe_native_adjustment(request,saved->eax);
}
void __cdecl physics_probe_clear_writer_observe(uint32_t,uint32_t,uint32_t) {}
void __cdecl physics_probe_transaction_observe(const uint32_t* saved,uint32_t site,uint32_t after) {
    if(!after) {
        pending={};pending.site=site;pending.thread=GetCurrentThreadId();pending.backing=ptr(backing.data());
        pending.controller=0x30000;pending.identity_generation=4;pending.race=7;pending.lifetime=3;
        pending.readable=pending.owner_current=pending.human=pending.race_valid=true;
        pending.flag=backing[0x33];std::memcpy(pending.matrix.data(),backing.data()+0x34,64);
        if(site==PUBLISH_PATCH_VA||site==MATRIX_COMPLETE_PATCH_VA){pending.manager=saved[1];pending.participant=static_cast<int32_t>(saved[4]/4);}
    } else {
        TransactionRecord e{};e.before=pending;e.after=pending;e.after.flag=backing[0x33];
        std::memcpy(e.after.matrix.data(),backing.data()+0x34,64);
        e=transaction_retain(capture,e);handle_transaction_event(request,e);
    }
}
void __cdecl integration_copy() {std::memcpy(backing.data()+0x34,destination.data(),64);}
void __cdecl integration_consume() {
    // The same capture correlation used by the production controller callback.
    TransactionRecord record{};record.kind=1;record.before=pending;record.after=pending;
    record.before.site=record.after.site=CONTROLLER_CALL_VA;
    record.before.flag=record.after.flag=backing[0x33];
    std::memcpy(record.before.matrix.data(),backing.data()+0x34,64);record.after.matrix=record.before.matrix;
    record=transaction_retain(capture,record);auto e=consumer();e.transaction_candidate=record.before.candidate;
    handle_consumer_event(request,e);
}
void __cdecl integration_settle() {handle_settled_event(request,consumer());}
}
#include "../src/road_teleport_bridge.inc"
#include "../src/physics_transaction_bridges.inc"
extern "C" __declspec(naked) void integration_stock_reset() {
    __asm {
        push ebp
        push ebx
        push esi
        push edi
        mov esi,dword ptr [integration_manager]
        mov edi,50000h
        push edi
        push 4
        push 0
        mov ecx,esi
        call road_teleport_adjust_bridge
        mov dword ptr [integration_returned_result],eax
        mov ebp,dword ptr [integration_backing]
        xor ebx,ebx
        call physics_probe_publish_bridge
        call integration_copy
        mov esi,dword ptr [integration_manager]
        mov ebp,dword ptr [integration_backing]
        xor ebx,ebx
        call physics_probe_matrix_complete_bridge
        call integration_consume
        mov eax,dword ptr [integration_backing]
        mov ecx,dword ptr [integration_input]
        xor edx,edx
        call physics_probe_input_flag_bridge
        call integration_settle
        pop edi
        pop esi
        pop ebx
        pop ebp
        ret
    }
}
int main() {
    road_teleport_adjust_original=reinterpret_cast<uintptr_t>(&integration_native_adjust);
    integration_manager=ptr(manager.data());integration_backing=ptr(backing.data());integration_input=ptr(input_owner.data());
    reset_fixture();CHECK(arm_current());integration_stock_reset();
    CHECK(native_input==12&&native_result==12&&integration_returned_result==12&&request.state==State::Completed);
    CHECK(request.native_publication_seen&&request.native_transaction_candidate==1&&request.native_consumed&&request.native_clear_seen);
    reset_fixture(false);integration_stock_reset();CHECK(native_input==4&&native_result==4&&request.state==State::Disabled);
    reset_fixture();countdown[0]=4;CHECK(!arm_current());CHECK(!request.input_overridden);
    reset_fixture();CHECK(arm_current());countdown[0]=4;integration_stock_reset();CHECK(native_input==4&&request.state==State::Cancelled);
    reset_fixture();CHECK(arm_current());force_adjustment_mismatch=true;integration_stock_reset();
    CHECK(native_input==12&&native_result==11&&integration_returned_result==11&&request.state==State::CommitMismatch);
    reset_fixture();CHECK(arm_current());duplicate_consumer=true;integration_stock_reset();
    CHECK(request.state==State::CommitMismatch&&!request.settled_zero_seen);
    reset_fixture();CHECK(arm_current());unreadable_zero=true;integration_stock_reset();
    CHECK(request.state!=State::Completed);
    if(failures)return 1;
    std::puts("production x86 teleport admission/selection/publication/copy/consumption/clear/settlement integration PASS");return 0;
}
