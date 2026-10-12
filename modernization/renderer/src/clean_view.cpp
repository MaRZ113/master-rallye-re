#include "clean_view.hpp"

namespace gfx2 {
CleanViewAdmission evaluate_clean_view_admission(const CleanViewAdmissionFacts& f) noexcept {
 const bool context=f.exact_build&&f.render_thread&&f.race_certificate&&f.freecam_active&&f.pause_known&&f.paused&&
  f.window_valid&&f.device_scope_valid&&f.frame_context_current&&f.ui_hook_owned;
 if(!f.pilot)return {false,"pilot_disabled",context};
 if(!f.requested)return {false,"user_off",context};
 if(!f.exact_build)return {false,"unsupported_build",false};
 if(!f.render_thread)return {false,"wrong_render_thread",false};
 if(!f.race_certificate)return {false,"invalid_race_certificate",false};
 if(!f.freecam_active)return {false,"freecam_inactive",false};
 if(!f.pause_known)return {false,"pause_state_unknown",false};
 if(!f.paused)return {false,"race_not_paused",false};
 if(!f.window_valid)return {false,"window_or_focus_unavailable",false};
 if(!f.device_scope_valid)return {false,"device_frame_scope_unavailable",false};
 if(!f.frame_context_current)return {false,"scheduler_context_stale_or_uncompleted",false};
 if(!f.ui_hook_owned)return {false,"native_ui_consumer_unowned",false};
 return {true,"admitted_paused_freecam",true};
}
bool clean_view_frame_context_fresh(const CleanViewFrameContext& c,uint64_t generation,uint64_t frame,DWORD thread,
 uint64_t device,uint64_t now,uint64_t max_age,unsigned depth,bool ui_scope,CleanViewFrameCheck* out) noexcept {
 CleanViewFrameCheck d{};d.snapshot_valid=c.valid;d.snapshot_completed=c.completed;d.scheduler_depth=depth;d.ui_scope_valid=ui_scope;
 d.phase=depth?"inflight_no_snapshot":"inactive_no_snapshot";
 d.current_scheduler_generation=generation;d.snapshot_scheduler_generation=c.scheduler_generation;
 d.current_trace_frame=frame;d.snapshot_trace_frame=c.trace_frame;
 d.scheduler_generation_match=c.scheduler_generation&&c.scheduler_generation==generation;
 d.trace_frame_match=c.trace_frame&&c.trace_frame==frame;
 d.render_thread_match=thread&&c.render_thread==thread;
 d.device_match=c.device_id&&c.device_id==device;
 d.snapshot_age_ms=now>=c.sampled_tick_ms?now-c.sampled_tick_ms:UINT64_MAX;
 d.age_valid=now>=c.sampled_tick_ms&&d.snapshot_age_ms<=max_age;
 if(!c.valid)d.reason="snapshot_invalid";
 else if(!d.scheduler_generation_match)d.reason="scheduler_generation_mismatch";
 else if(!d.trace_frame_match)d.reason="trace_frame_mismatch";
 else if(!d.render_thread_match)d.reason="render_thread_mismatch";
 else if(!d.device_match)d.reason="device_mismatch";
 else if(!d.age_valid)d.reason="snapshot_timestamp_stale";
 else if(!c.race_generation||!c.owner_lifetime||!c.camera)d.reason="snapshot_identity_incomplete";
 else if(!ui_scope)d.reason="native_ui_scope_missing";
 else if(depth&&!c.completed){d.phase="current_inflight";d.valid=true;d.reason="current_inflight_snapshot";}
 else if(!depth&&c.completed){d.phase="current_completed";d.valid=true;d.reason="current_completed_snapshot";}
 else if(depth&&c.completed){d.phase="inflight_completed_inconsistent";d.reason="inflight_snapshot_already_completed";}
 else {d.phase="inactive_uncompleted";d.reason="scheduler_inactive_snapshot_uncompleted";}
 if(out)*out=d;
 return d.valid;
}
bool clean_view_context_loss_disarms(bool requested,bool initial_pending,bool context_valid) noexcept {
 return requested&&!initial_pending&&!context_valid;
}
bool clean_view_draw_rejected(bool requested,bool ui_callsite,bool eligible) noexcept {
 return requested&&ui_callsite&&!eligible;
}
bool clean_view_lifecycle_invalid(const CleanViewAdmissionFacts& f,bool device_identity_valid) noexcept {
 return !f.pilot||!f.exact_build||!f.render_thread||!f.race_certificate||!f.freecam_active||
  !f.pause_known||!f.paused||!f.window_valid||!device_identity_valid||!f.ui_hook_owned;
}
bool clean_view_draw_eligible(const CleanViewDrawFacts& f) noexcept {
 return f.exact_build&&f.hook_owned&&f.render_thread&&f.consumer_scope&&
  f.identity_complete&&f.identity_current&&f.callsite_exact&&f.fvf_known&&f.fvf==0x142&&
  f.primitive==D3DPT_TRIANGLELIST&&f.primitive_count>0;
}
bool clean_view_should_suppress(bool admission_valid,bool requested,bool draw_eligible) noexcept {
 return admission_valid&&requested&&draw_eligible;
}
}
