#include "clean_view.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
int main(){try{
 CleanViewAdmissionFacts admission{true,true,true,true,true,true,true,true,true,true,true,true};
 CHECK(evaluate_clean_view_admission(admission).admitted);
 auto user_off=admission;user_off.requested=false;const auto context_only=evaluate_clean_view_admission(user_off);
 CHECK(!context_only.admitted&&context_only.context_valid);
 bool CleanViewAdmissionFacts::* gates[]={&CleanViewAdmissionFacts::pilot,&CleanViewAdmissionFacts::requested,&CleanViewAdmissionFacts::exact_build,
  &CleanViewAdmissionFacts::render_thread,&CleanViewAdmissionFacts::race_certificate,&CleanViewAdmissionFacts::freecam_active,
  &CleanViewAdmissionFacts::pause_known,&CleanViewAdmissionFacts::paused,&CleanViewAdmissionFacts::window_valid,
  &CleanViewAdmissionFacts::device_scope_valid,&CleanViewAdmissionFacts::ui_hook_owned,&CleanViewAdmissionFacts::frame_context_current};
 for(auto gate:gates){auto test=admission;test.*gate=false;CHECK(!evaluate_clean_view_admission(test).admitted);}
 bool CleanViewAdmissionFacts::* lifecycle_gates[]={&CleanViewAdmissionFacts::pilot,&CleanViewAdmissionFacts::exact_build,
  &CleanViewAdmissionFacts::render_thread,&CleanViewAdmissionFacts::race_certificate,&CleanViewAdmissionFacts::freecam_active,
  &CleanViewAdmissionFacts::pause_known,&CleanViewAdmissionFacts::paused,&CleanViewAdmissionFacts::window_valid,&CleanViewAdmissionFacts::ui_hook_owned};
 for(auto gate:lifecycle_gates){auto test=admission;test.*gate=false;CHECK(clean_view_lifecycle_invalid(test,true));}
 CHECK(clean_view_lifecycle_invalid(admission,false));
 auto draw_scope_absent=admission;draw_scope_absent.device_scope_valid=false;draw_scope_absent.frame_context_current=false;
 CHECK(!clean_view_lifecycle_invalid(draw_scope_absent,true));
 CHECK(!std::strcmp(evaluate_clean_view_admission(CleanViewAdmissionFacts{}).reason,"pilot_disabled"));
 CleanViewDrawFacts draw{};draw.exact_build=draw.hook_owned=draw.render_thread=draw.consumer_scope=draw.identity_complete=draw.identity_current=draw.callsite_exact=draw.fvf_known=true;
 draw.fvf=0x142;draw.primitive=D3DPT_TRIANGLELIST;draw.primitive_count=2;
 CHECK(clean_view_draw_eligible(draw));CHECK(clean_view_should_suppress(true,true,true));
 CHECK(!clean_view_should_suppress(false,true,true));CHECK(!clean_view_should_suppress(true,false,true));CHECK(!clean_view_should_suppress(true,true,false));
 auto rejects=[&](auto mutate){auto candidate=draw;mutate(candidate);CHECK(!clean_view_draw_eligible(candidate));};
 rejects([](auto& d){d.exact_build=false;});rejects([](auto& d){d.hook_owned=false;});rejects([](auto& d){d.render_thread=false;});
 rejects([](auto& d){d.consumer_scope=false;});rejects([](auto& d){d.identity_complete=false;});rejects([](auto& d){d.identity_current=false;});
 rejects([](auto& d){d.callsite_exact=false;});rejects([](auto& d){d.fvf_known=false;});rejects([](auto& d){d.fvf=0x152;});
 rejects([](auto& d){d.primitive=D3DPT_LINELIST;});rejects([](auto& d){d.primitive_count=0;});
 CleanViewFrameContext context{};context.valid=true;context.completed=true;context.scheduler_generation=7;context.race_generation=3;
 context.owner_lifetime=4;context.camera=0x1234;context.device_id=9;context.sampled_tick_ms=1000;context.trace_frame=50;context.render_thread=22;
 CleanViewFrameCheck frame_check{};
 CHECK(clean_view_frame_context_fresh(context,7,50,22,9,1010,250,0,true,&frame_check));
 CHECK(!std::strcmp(frame_check.phase,"current_completed")&&frame_check.snapshot_completed);
 CHECK(!clean_view_frame_context_fresh(context,8,50,22,9,1010,250,0,true,&frame_check)&&!std::strcmp(frame_check.reason,"scheduler_generation_mismatch"));
 CHECK(!clean_view_frame_context_fresh(context,7,51,22,9,1010,250,0,true,&frame_check)&&!std::strcmp(frame_check.reason,"trace_frame_mismatch"));
 CHECK(!clean_view_frame_context_fresh(context,7,50,23,9,1010,250,0,true,&frame_check)&&!std::strcmp(frame_check.reason,"render_thread_mismatch"));
 CHECK(!clean_view_frame_context_fresh(context,7,50,22,10,1010,250,0,true,&frame_check)&&!std::strcmp(frame_check.reason,"device_mismatch"));
 CHECK(!clean_view_frame_context_fresh(context,7,50,22,9,1251,250,0,true,&frame_check)&&!std::strcmp(frame_check.reason,"snapshot_timestamp_stale"));
 CHECK(!clean_view_frame_context_fresh(context,7,50,22,9,1010,250,0,false,&frame_check)&&!std::strcmp(frame_check.reason,"native_ui_scope_missing"));
 context.completed=false;
 CHECK(clean_view_frame_context_fresh(context,7,50,22,9,1010,250,1,true,&frame_check));
 CHECK(!std::strcmp(frame_check.phase,"current_inflight")&&!frame_check.snapshot_completed);
 context.completed=true;CHECK(!clean_view_frame_context_fresh(context,7,50,22,9,1010,250,1,true,&frame_check));
 CHECK(!std::strcmp(frame_check.reason,"inflight_snapshot_already_completed"));context.completed=false;
 CHECK(!clean_view_frame_context_fresh(context,7,50,22,9,1010,250,0,true,&frame_check)&&!std::strcmp(frame_check.reason,"scheduler_inactive_snapshot_uncompleted"));
 CHECK(!clean_view_frame_context_fresh(context,7,50,22,9,1010,250,1,false,&frame_check));
 CHECK(!clean_view_context_loss_disarms(true,false,true));
 CHECK(!clean_view_context_loss_disarms(true,true,false));
 CHECK(clean_view_context_loss_disarms(true,false,false));
 CHECK(clean_view_draw_rejected(true,true,false));CHECK(!clean_view_draw_rejected(false,true,false));
 CHECK(!clean_view_draw_rejected(true,false,false));CHECK(!clean_view_draw_rejected(true,true,true));
 // Scheduler completes and restores CameraFrame before UI. Neither that
 // restoration nor unrelated/unknown draws should clear the user's request.
 bool requested=true;context.completed=false;context.sampled_tick_ms=2000;context.trace_frame=51;
 CHECK(!clean_view_context_loss_disarms(requested,false,true));
 CHECK(!clean_view_should_suppress(true,requested,false));CHECK(requested);
 const bool in_flight_context=clean_view_frame_context_fresh(context,7,51,22,9,2010,250,1,true,&frame_check);
 CHECK(in_flight_context);auto in_flight_admission=admission;in_flight_admission.frame_context_current=in_flight_context;
 CHECK(evaluate_clean_view_admission(in_flight_admission).admitted);
 CHECK(clean_view_should_suppress(true,requested,true));CHECK(clean_view_should_suppress(true,requested,true));
 // Scheduler completion is still observed normally; it does not extend CameraFrame ownership.
 context.completed=true;CHECK(clean_view_frame_context_fresh(context,7,51,22,9,2010,250,0,true,&frame_check));
 CHECK(!std::strcmp(frame_check.phase,"current_completed"));
 requested=false;CHECK(!clean_view_should_suppress(true,requested,true));
 std::cout<<"CleanView persistent request, bounded scheduler/frame snapshot, pause/freecam/device/native-scope and exact draw-signature contracts: PASS\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
