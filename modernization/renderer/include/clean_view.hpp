#pragma once
#include "sdk.hpp"
#include <cstdint>

namespace gfx2 {
struct CleanViewAdmissionFacts {
 bool pilot=false,requested=false,exact_build=false,render_thread=false;
 bool race_certificate=false,freecam_active=false,pause_known=false,paused=false;
 bool window_valid=false,device_scope_valid=false,ui_hook_owned=false;
 bool frame_context_current=false;
};
struct CleanViewFrameCheck {
 const char* phase="no_snapshot";
 const char* reason="snapshot_invalid";
 bool snapshot_valid=false,snapshot_completed=false,scheduler_generation_match=false,trace_frame_match=false;
 bool render_thread_match=false,device_match=false,age_valid=false,ui_scope_valid=false,valid=false;
 uint64_t current_scheduler_generation=0,snapshot_scheduler_generation=0,current_trace_frame=0,snapshot_trace_frame=0,snapshot_age_ms=0;
 unsigned scheduler_depth=0;
};
struct CleanViewAdmission {
 bool admitted=false;
 const char* reason="pilot_disabled";
 bool context_valid=false;
 CleanViewFrameCheck frame{};
};
CleanViewAdmission evaluate_clean_view_admission(const CleanViewAdmissionFacts&) noexcept;

struct CleanViewFrameContext {
 bool valid=false,completed=false;
 uint64_t scheduler_generation=0,race_generation=0,owner_lifetime=0,device_id=0,sampled_tick_ms=0,trace_frame=0;
 uintptr_t camera=0;
 DWORD render_thread=0;
};
bool clean_view_frame_context_fresh(const CleanViewFrameContext&,uint64_t scheduler_generation,
 uint64_t trace_frame,DWORD render_thread,uint64_t device_id,uint64_t now_tick_ms,uint64_t max_age_ms,
 unsigned scheduler_depth,bool ui_scope_valid,CleanViewFrameCheck* diagnostic=nullptr) noexcept;
bool clean_view_context_loss_disarms(bool requested,bool initial_pending,bool context_valid) noexcept;
bool clean_view_draw_rejected(bool draw_requested,bool ui_callsite,bool draw_eligible) noexcept;
bool clean_view_lifecycle_invalid(const CleanViewAdmissionFacts&,bool device_identity_valid) noexcept;

struct CleanViewDrawFacts {
 bool exact_build=false,hook_owned=false,render_thread=false,consumer_scope=false;
 bool identity_complete=false,identity_current=false,callsite_exact=false;
 bool fvf_known=false;
 DWORD fvf=0;
 D3DPRIMITIVETYPE primitive=D3DPT_FORCE_DWORD;
 UINT primitive_count=0;
};
bool clean_view_draw_eligible(const CleanViewDrawFacts&) noexcept;
bool clean_view_should_suppress(bool admission_valid,bool requested,bool draw_eligible) noexcept;
}
