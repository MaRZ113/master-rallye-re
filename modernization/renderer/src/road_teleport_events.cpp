#include "road_teleport_events.hpp"
namespace gfx2::road_teleport {
namespace {
bool current(const Request& r,const physics_probe::TransactionSample& s) noexcept {
    return s.readable && s.race_valid && s.owner_current && s.human &&
        s.thread==r.native_thread_id && s.race==r.race_generation &&
        s.lifetime==r.owner_lifetime && s.controller==r.human_controller &&
        s.backing==r.human_backing && s.identity_generation==r.human_identity_generation;
}
bool current(const Request& r,const ConsumerEvent& s) noexcept {
    return s.race_current && s.owner_current && s.human &&
        s.thread==r.native_thread_id && s.race_generation==r.race_generation &&
        s.owner_lifetime==r.owner_lifetime && s.controller==r.human_controller &&
        s.backing==r.human_backing && s.actor==r.human_actor &&
        s.identity_generation==r.human_identity_generation;
}
}
void handle_transaction_event(Request& r,const physics_probe::TransactionRecord& e) noexcept {
    if(e.kind!=0 || !current(r,e.before) || !current(r,e.after))return;
    if(e.before.site==physics_probe::PUBLISH_PATCH_VA && e.after.flag==1 &&
       e.after.manager==r.reset_manager && e.after.participant==static_cast<int32_t>(r.participant_index)) {
        if(r.state==State::DestinationOverridden && r.stock_adjustment_returned &&
           !r.native_publication_seen && e.before.flag==0 && e.after.candidate) {
            r.native_publication_seen=true;r.native_transaction_candidate=e.after.candidate;
        } else if(r.state==State::DestinationCommitted || r.state==State::NativeConsumed ||
                  (r.state==State::DestinationOverridden && r.native_publication_seen)) {
            r.state=State::CommitMismatch;r.reason="native_republication_before_settlement";
        }
        return;
    }
    if(e.before.site==physics_probe::MATRIX_COMPLETE_PATCH_VA && r.native_publication_seen &&
       e.after.candidate==r.native_transaction_candidate && e.before.flag==1 && e.after.flag==1 &&
       e.before.matrix==e.after.matrix) {
        commit_matrix(r,e.after.manager,static_cast<uint32_t>(e.after.participant),e.after.matrix);
        return;
    }
    if(e.before.flag==1 && e.after.flag==0 && e.before.candidate==r.native_transaction_candidate) {
        if(r.state==State::DestinationCommitted) {
            r.state=State::CommitMismatch;r.reason="native_clear_before_physical_consumption";
        } else observe_clear(r,e.after.backing,e.before.site,e.before.flag,e.after.flag);
    }
}
void handle_consumer_event(Request& r,const ConsumerEvent& e) noexcept {
    if(!current(r,e)||!e.flag_readable||!e.matrix_readable||!e.chassis_readable||e.flag!=1||
       !r.native_publication_seen||e.transaction_candidate!=r.native_transaction_candidate)return;
    if(r.state==State::NativeConsumed && e.active_consumer_calls!=1) {
        r.active_consumer_calls=e.active_consumer_calls;r.state=State::CommitMismatch;
        r.reason="native_consumer_count_not_exclusive";return;
    }
    observe_native_consumption(r,e.backing,e.matrix,e.chassis_after,true,e.active_consumer_calls);
}
void handle_settled_event(Request& r,const ConsumerEvent& e) noexcept {
    if(current(r,e)&&e.flag_readable)observe_settled_zero(r,e.backing,e.flag);
}
}
