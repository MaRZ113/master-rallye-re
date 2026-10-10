#include "game_fov.hpp"
#include "free_camera.hpp"
#include "race_epoch.hpp"
#include <sstream>
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <intrin.h>
#include <cfenv>
namespace gfx2 {
struct FlightState {
 FreeCameraConfig config;FlightWindowInput input;FlightController controller;RaceCertificate certificate,visible_certificate,scope_certificate;
 std::array<float,16> visible_pose{};bool visible=false,pose_scope=false;
 bool speed_identity_valid=false;uint64_t speed_race_generation=0,speed_owner_lifetime=0;
 const char* reason="disabled";uint64_t scopes=0,restores=0,failures=0;
 bool reported_valid=false,reported_active=false,reported_horizon_leveling=false;uint64_t reported_race=0,reported_owner=0;const char* reported_reason="disabled";
 bool input_focused=false,toggle_pressed_focused=false,toggle_edge=false;
 bool reported_input_focused=false,reported_toggle_pressed=false,reported_toggle_edge=false;
 bool reported_cursor_capture=false;uint64_t reported_speed_adjustments=0;
 float effective_vfov=0,effective_hfov=0,projection_vfov=0;bool projection_frustum_synchronized=false;
 const char* projection_reason="awaiting_projection_call";
};
namespace {FlightState flight_state;}

namespace detail {uintptr_t original_submit=0;}
namespace {
struct SavedFP {fenv_t value;SavedFP(){fegetenv(&value);}~SavedFP(){fesetenv(&value);}};
class NativeMemory final:public PatchMemory {
public:
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
 bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
} memory;
GameFov* active=nullptr;
bool ambiguous_devices=false;
void __stdcall synchronize_camera(unsigned index) noexcept {if(active)active->before_submit(index);}
void __stdcall scheduler_notify(uint32_t kind,const camera_bridge::Saved*) noexcept {if(active){if(kind==0)active->scheduler_begin();else active->scheduler_end();}}
}
namespace detail {
// Original ECX, both stack arguments, return PC, flags and x87/SSE state survive.
__declspec(naked) void submit_bridge(){
 __asm {
  pushfd
  pushad
  mov ebp,esp
  and esp,-16
  sub esp,528
  fxsave [esp]
  fninit
  mov dword ptr [esp+512],01f80h
  ldmxcsr [esp+512]
  cld
  push dword ptr [ebp+40]
  call synchronize_camera
  fxrstor [esp]
  mov esp,ebp
  popad
  popfd
  jmp dword ptr [original_submit]
 }
}
}
namespace {
bool snapshot_equal(const CameraFrame& a,const CameraFrame& b) noexcept {
 return a.width==b.width&&a.height==b.height&&a.source_angle==b.source_angle&&
  std::memcmp(a.pose.data(),b.pose.data(),sizeof(a.pose))==0;
}
CameraFrame* current_camera(uintptr_t base) noexcept {
 uintptr_t holder=0,state=0,camera=0;
 if(!safe_copy(&holder,reinterpret_cast<void*>(base+RENDERER_HOLDER_RVA),4)||!holder||
    !safe_copy(&state,reinterpret_cast<void*>(holder+0x38),4)||!state||
    !safe_copy(&camera,reinterpret_cast<void*>(state+4),4))return nullptr;
 return reinterpret_cast<CameraFrame*>(camera);
}
void report(const FovCullStatus& s) noexcept {
 try{session().write("{\"type\":\"fov_culling_hook\",\"call_rva\":2437853,\"installed\":"+std::string(s.installed?"true":"false")+",\"reason\":"+quote(s.reason)+"}");}catch(...){}
}
}
bool CallPatch::exchange(PatchMemory& m,const std::array<unsigned char,5>& from,const std::array<unsigned char,5>& to) noexcept {
 std::array<unsigned char,5> seen{};DWORD old=0,ignored=0;
 if(!m.read(seen.data(),site_,5)||seen!=from||!m.protect(site_,5,PAGE_EXECUTE_READWRITE,old))return false;
 bool okay=m.write(site_,to.data(),5)&&m.flush(site_,5)&&m.read(seen.data(),site_,5)&&seen==to;
 bool protected_ok=m.protect(site_,5,old,ignored);
 if(!okay||!protected_ok){
  // Recover partial writes while the page is writable, then restore its original protection.
  DWORD rollback_old=0;
  if(m.protect(site_,5,PAGE_EXECUTE_READWRITE,rollback_old)){m.write(site_,from.data(),5);m.flush(site_,5);m.protect(site_,5,old,ignored);}
  okay=false;
 }
 if(m.read(seen.data(),site_,5))installed_=seen==after_;
 return okay;
}
bool CallPatch::install(PatchMemory& m,void* site,uintptr_t destination,const std::array<unsigned char,5>& expected) noexcept {
 if(installed_||expected[0]!=0xe8||!site||!destination)return false;
 site_=site;before_=expected;after_[0]=0xe8;
 uint32_t relative=static_cast<uint32_t>(destination)-static_cast<uint32_t>(reinterpret_cast<uintptr_t>(site)+5);
 std::memcpy(after_.data()+1,&relative,4);
 return exchange(m,before_,after_);
}
bool CallPatch::remove(PatchMemory& m) noexcept {return !installed_||exchange(m,after_,before_);}
bool effective_side_planes(const CameraFrame& c,float vfov,std::array<float,12>& out,float& hfov) noexcept {
 SavedFP fp;
 if(c.width<=0||c.height<=0||c.width>16384||c.height>16384||!std::isfinite(c.source_angle)||
    std::abs(c.source_angle-90.f)>SOURCE_CAMERA_TOLERANCE_DEGREES||!std::isfinite(vfov)||vfov<30.f||vfov>110.f)return false;
 // Match the stock rigid camera basis. A scaled/sheared/degenerate camera stays stock.
 for(int row=0;row<4;++row)for(int j=0;j<4;++j)if(!std::isfinite(c.pose[row*4+j]))return false;
 for(int row=0;row<3;++row){double length=0;for(int j=0;j<3;++j)length+=double(c.pose[row*4+j])*c.pose[row*4+j];if(std::abs(length-1.)>.02)return false;
  for(int other=0;other<row;++other){double dot=0;for(int j=0;j<3;++j)dot+=double(c.pose[row*4+j])*c.pose[other*4+j];if(std::abs(dot)>.02)return false;}}
 if(c.pose[3]!=0||c.pose[7]!=0||c.pose[11]!=0||c.pose[15]!=1)return false;
 constexpr double pi=3.14159265358979323846;
 double v=vfov*pi/360.,h=std::atan(std::tan(v)*double(c.width)/c.height);
 if(!std::isfinite(h)||h<=0||h>=pi/2)return false;
 hfov=static_cast<float>(h*360./pi);
 const double local[4][3]={{0,std::cos(v),std::sin(v)},{0,-std::cos(v),std::sin(v)},
  {std::cos(h),0,std::sin(h)},{-std::cos(h),0,std::sin(h)}};
 for(int n=0;n<4;++n)for(int j=0;j<3;++j){out[n*3+j]=static_cast<float>(local[n][0]*c.pose[j]+local[n][1]*c.pose[4+j]+local[n][2]*c.pose[8+j]);if(!std::isfinite(out[n*3+j]))return false;}
 return true;
}
bool FrustumFrame::begin(CameraFrame* camera,float vfov,const std::array<float,16>* pose) noexcept {
 if(!restore())return false;
 CameraFrame c{};float hfov=0;std::array<float,12> planes{};
 if(!camera||!safe_copy(&c,camera,sizeof(c))){status.reason="ineligible_camera";return false;}
 CameraFrame effective=c;if(pose){effective.pose=*pose;effective.previous_pose=*pose;}
 if(!effective_side_planes(effective,vfov,planes,hfov)){status.reason="ineligible_camera";return false;}
 if(!safe_copy(camera->planes.data(),planes.data(),sizeof(planes))){
  // A guarded memcpy can have written a prefix before faulting across a page boundary.
  safe_copy(camera->planes.data(),c.planes.data(),sizeof(c.planes));CameraFrame check{};
  status.restored=safe_copy(&check,camera,sizeof(check))&&std::memcmp(check.planes.data(),c.planes.data(),sizeof(c.planes))==0;
  status.reason="camera_write_failed";++status.failures;return false;
 }
 if(pose&&(!safe_copy(camera->previous_pose.data(),pose->data(),64)||!safe_copy(camera->pose.data(),pose->data(),64))){
  bool restored=safe_copy(camera->planes.data(),c.planes.data(),48)&&safe_copy(camera->previous_pose.data(),c.previous_pose.data(),64)&&safe_copy(camera->pose.data(),c.pose.data(),64);
  CameraFrame check{};restored=restored&&safe_copy(&check,camera,sizeof(check))&&check.planes==c.planes&&check.previous_pose==c.previous_pose&&check.pose==c.pose;
  status.restored=restored;status.reason="camera_pose_write_failed";++status.failures;return false;
 }
 camera_=camera;snapshot_=c;effective_=planes;owns_pose_=pose!=nullptr;effective_pose_=effective.pose;status.synchronized=true;status.restored=false;
 status.width=c.width;status.height=c.height;status.source=c.source_angle;status.vfov=vfov;status.hfov=hfov;++status.synchronized_frames;status.reason="matched_side_planes";return true;
}
bool FrustumFrame::matches(const CameraFrame* camera,const D3DMATRIX& p) const noexcept {
 SavedFP fp;
 CameraFrame c{};
 return status.synchronized&&camera==camera_&&safe_copy(&c,camera,sizeof(c))&&(owns_pose_?(c.width==snapshot_.width&&c.height==snapshot_.height&&c.source_angle==snapshot_.source_angle&&c.pose==effective_pose_&&c.previous_pose==effective_pose_):snapshot_equal(c,snapshot_))&&
  std::memcmp(c.planes.data(),effective_.data(),sizeof(effective_))==0&&symmetric_lh(p)&&
  std::abs(double(p._22)/p._11-double(c.width)/c.height)<=.00001*double(c.width)/c.height&&
  std::abs(source_camera_angle(p)-90.)<=SOURCE_CAMERA_TOLERANCE_DEGREES;
}
bool FrustumFrame::restore() noexcept {
 SavedFP fp;
 status.synchronized=false;status.width=status.height=0;status.source=status.vfov=status.hfov=0;
 if(!camera_)return status.restored;
 CameraFrame c{};bool okay=safe_copy(&c,camera_,sizeof(c));
 if(owns_pose_){
  okay=okay&&c.planes==effective_&&c.pose==effective_pose_&&c.previous_pose==effective_pose_;
  if(okay)okay=safe_copy(camera_->planes.data(),snapshot_.planes.data(),48)&&safe_copy(camera_->previous_pose.data(),snapshot_.previous_pose.data(),64)&&safe_copy(camera_->pose.data(),snapshot_.pose.data(),64);
  CameraFrame check{};okay=okay&&safe_copy(&check,camera_,sizeof(check))&&check.planes==snapshot_.planes&&check.previous_pose==snapshot_.previous_pose&&check.pose==snapshot_.pose;
 }else if(okay&&c.planes==effective_)
  okay=c.pose==snapshot_.pose&&c.source_angle==snapshot_.source_angle&&safe_copy(camera_->planes.data(),snapshot_.planes.data(),sizeof(snapshot_.planes));
 // Viewport, flags, source and snap fields are never restored.
 camera_=nullptr;status.synchronized=false;status.restored=okay;
 if(!okay){++status.failures;status.reason="camera_restore_failed";}return okay;
}
bool GameFov::install(bool exact,const VisualConfig& c,HWND window,bool exact_retail) noexcept {
 submission_=CameraSubmissionSnapshot{};
 auto flight_config=parse_free_camera_config(c.raw_fields);flight_config.enabled&=exact_retail&&c.version_ok;
 if(!exact||(!c.fov&&!flight_config.enabled)){frame_.status.reason=exact?"disabled":"unsupported_build";return false;}
 if(active||ambiguous_devices){ambiguous_devices=true;if(active)active->disable("multiple_devices");frame_.status.reason="multiple_devices";report(frame_.status);return false;}
 base_=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));thread_=GetCurrentThreadId();vfov_=c.vfov;fov_enabled_=c.fov;
 // The pristine PE uses absolute constants; unsupported placement stays stock.
 if(base_!=0x400000||!IsProcessorFeaturePresent(PF_XMMI64_INSTRUCTIONS_AVAILABLE)){frame_.status.reason="unsupported_image_or_cpu";report(frame_.status);return false;}
 constexpr unsigned char context[]={0x8b,0x40,0x20,0x3b,0xfb,0x0f,0x94,0xc1,0x51,0x57,0x8b,0xc8,0xe8,0x9e,0x63,0xeb,0xff};
 unsigned char observed[sizeof(context)]{};
 if(!safe_copy(observed,reinterpret_cast<void*>(base_+SUBMIT_CALL_RVA-12),sizeof(observed))||std::memcmp(context,observed,sizeof(context))){frame_.status.reason="call_signature_mismatch";report(frame_.status);return false;}
 HMODULE pinned=nullptr;
 if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&detail::submit_bridge),&pinned)){frame_.status.reason="module_pin_failed";report(frame_.status);return false;}
 constexpr std::array<unsigned char,5> completion_bytes={0xe8,0x15,0x2f,0x0a,0};
 unsigned char scheduler_call[5]{};if(!safe_copy(scheduler_call,reinterpret_cast<void*>(base_+0x1b0166),5)||std::memcmp(scheduler_call,completion_bytes.data(),5)){frame_.status.reason="scheduler_signature_mismatch";return false;}
 camera_bridge::scheduler_original=base_+0x253080;camera_bridge::callback=&scheduler_notify;
 if(!completion_.install(memory,reinterpret_cast<void*>(base_+0x1b0166),reinterpret_cast<uintptr_t>(&camera_bridge::scheduler),completion_bytes)){frame_.status.reason="scheduler_patch_failed";return false;}
 detail::original_submit=base_+SUBMIT_OWNER_RVA;active=this;
 enabled_=patch_.install(memory,reinterpret_cast<void*>(base_+SUBMIT_CALL_RVA),reinterpret_cast<uintptr_t>(&detail::submit_bridge),SUBMIT_CALL_BYTES);
 frame_.status.installed=patch_.installed();frame_.status.reason=enabled_?"installed_before_device_return":"call_patch_failed";
 if(!enabled_){active=nullptr;patch_.remove(memory);completion_.remove(memory);frame_.status.installed=patch_.installed()||completion_.installed();}
 if(enabled_&&flight_config.enabled){flight_=&flight_state;flight_->config=flight_config;flight_->controller.cancel();flight_->speed_identity_valid=false;flight_->visible=false;flight_->reason=flight_->input.attach(window)?"awaiting_live_race_certificate":"game_window_input_unavailable";if(!flight_->input.intact())flight_->config.enabled=false;}
 report(frame_.status);return enabled_;
}
void GameFov::before_submit(unsigned index) noexcept {
 submission_=CameraSubmissionSnapshot{};submission_.index=index;submission_.status="unmapped_camera_schedule";
 if(!enabled_){frame_.status.reason="inactive";submission_.status="hook_inactive";return;}
 if(scheduler_depth_!=1){cancel_frame();frame_.status.reason="outside_single_scheduler_scope";return;}
 if(!patch_.intact(memory)||!completion_.intact(memory)){disable("camera_hook_ownership_lost");return;}
 if(GetCurrentThreadId()!=thread_){disable("wrong_render_thread");submission_.status="wrong_render_thread";return;}
 uintptr_t manager=0,camera=0;int count=0;
 if(!safe_copy(&manager,reinterpret_cast<void*>(base_+CAMERA_MANAGER_RVA),4)||!manager||
    !safe_copy(&count,reinterpret_cast<void*>(manager+0x10),4)||count!=1||index!=0||
    !safe_copy(&camera,reinterpret_cast<void*>(manager+index*4),4)||!camera||
    current_camera(base_)!=reinterpret_cast<CameraFrame*>(camera)){
  cancel_frame();if(flight_){flight_->controller.cancel();flight_->input.set_cursor_capture(false);flight_->visible=false;}frame_.status.reason="unmapped_camera_schedule";return;
 }
 if(!frame_.restore()){
  submission_.status="previous_camera_restore_failed";disable("camera_restore_failed");return;
 }
 submission_.camera_pointer=camera;
 if(!safe_copy(&submission_.camera,reinterpret_cast<const void*>(camera),sizeof(submission_.camera))){
  submission_.status="camera_snapshot_read_failed";return;
 }
 submission_.available=true;submission_.status="captured_before_fov_plane_write";

 const std::array<float,16>* effective_pose=nullptr;
 if(flight_&&flight_->config.enabled){
  auto& f=*flight_;f.certificate=live_race_certificate(camera);
  // The native builder skips only argument == this sentinel (normally -1).
  // Reviewed gameplay/finalize/debug calls pass zero. Never force its cache flag.
  uint32_t sentinel=0;
  if(!safe_copy(&sentinel,reinterpret_cast<void*>(base_+0x2e9a74),4)||sentinel!=UINT32_MAX){f.certificate.valid=false;f.certificate.reason="camera_builder_cache_sentinel_changed";}
  if(f.certificate.valid&&(!f.speed_identity_valid||f.speed_race_generation!=f.certificate.race_generation||f.speed_owner_lifetime!=f.certificate.owner_lifetime)){
   f.controller.reset_for_race(f.config);f.speed_identity_valid=true;f.speed_race_generation=f.certificate.race_generation;f.speed_owner_lifetime=f.certificate.owner_lifetime;
  }
  if(!f.certificate.valid)f.visible=false;
  auto input=f.input.sample(f.config,f.controller.active);
  input.inherited_vfov=fov_enabled_?vfov_:submission_.camera.source_angle/std::max(1.f,float(submission_.camera.width)/submission_.camera.height);
  bool visible=f.visible&&f.visible_certificate.camera==camera&&f.visible_certificate.owner_lifetime==f.certificate.owner_lifetime&&f.visible_certificate.race_generation==f.certificate.race_generation;
  bool flying=f.controller.update(f.config,input,f.certificate.valid,visible?&f.visible_pose:nullptr);
  f.input.set_cursor_capture(flying&&input.focused);
  f.input_focused=input.focused;f.toggle_pressed_focused=input.focused&&input.toggle;f.toggle_edge=f.controller.last_toggle_edge;
  f.reason=flying?"freecam_active":!input.focused?"focus_lost":!f.certificate.valid?f.certificate.reason:visible?"ready_toggle_off":"awaiting_displayed_stock_view";
  if(flying){effective_pose=&f.controller.pose;f.scope_certificate=f.certificate;f.pose_scope=true;}
 }
 if(fov_enabled_||effective_pose){float fov=fov_enabled_?vfov_:submission_.camera.source_angle/std::max(1.f,float(submission_.camera.width)/submission_.camera.height);
  if(effective_pose&&flight_&&flight_->config.cinematic_fov_enabled&&flight_->controller.current_vertical_fov()>0)fov=static_cast<float>(flight_->controller.current_vertical_fov());
  if(flight_){flight_->projection_frustum_synchronized=false;flight_->projection_reason=effective_pose&&flight_->config.cinematic_fov_enabled?"awaiting_cinematic_projection":"awaiting_projection_call";}
  if(!frame_.begin(reinterpret_cast<CameraFrame*>(camera),fov,effective_pose)){if(flight_){flight_->controller.cancel();flight_->input.set_cursor_capture(false);flight_->pose_scope=false;++flight_->failures;flight_->reason="effective_camera_ineligible_or_write_failed";flight_->projection_reason="frustum_scope_failed";}if(!frame_.status.restored)disable("camera_restore_failed");}
  else {if(flight_){flight_->effective_vfov=frame_.status.vfov;flight_->effective_hfov=frame_.status.hfov;flight_->projection_reason=effective_pose&&flight_->config.cinematic_fov_enabled?"awaiting_cinematic_projection":"awaiting_projection_call";}
   if(effective_pose&&flight_){++flight_->scopes;if(flight_->scopes==1)try{session().write("{\"type\":\"free_camera_scope\",\"phase\":\"R-CAM1-A3d\",\"event\":\"first_effective_scope\",\"owned_bytes\":176,\"pre_call_va\":6632157}");}catch(...){}}}
 }
 if(flight_){auto& f=*flight_;if(f.reported_valid!=f.certificate.valid||f.reported_active!=f.controller.active||f.reported_horizon_leveling!=f.controller.horizon_leveling_active||f.reported_race!=f.certificate.race_generation||f.reported_owner!=f.certificate.owner_lifetime||f.reported_input_focused!=f.input_focused||f.reported_toggle_pressed!=f.toggle_pressed_focused||f.reported_toggle_edge!=f.toggle_edge||f.reported_cursor_capture!=f.input.cursor_capture_active()||f.reported_speed_adjustments!=f.controller.speed_adjustment_count()||std::strcmp(f.reported_reason,f.reason)){
  f.reported_valid=f.certificate.valid;f.reported_active=f.controller.active;f.reported_horizon_leveling=f.controller.horizon_leveling_active;f.reported_race=f.certificate.race_generation;f.reported_owner=f.certificate.owner_lifetime;f.reported_input_focused=f.input_focused;f.reported_toggle_pressed=f.toggle_pressed_focused;f.reported_toggle_edge=f.toggle_edge;f.reported_cursor_capture=f.input.cursor_capture_active();f.reported_speed_adjustments=f.controller.speed_adjustment_count();f.reported_reason=f.reason;
  try{session().write("{\"type\":\"free_camera_state\",\"phase\":\"R-CAM1-A3g\",\"state\":"+camera_json()+"}");
   // Emit the full, bounded lifecycle certificate alongside each meaningful
   // freecam state/input transition. This keeps F10 reserved and records the
   // root/HUD jobs, their copied flags and commit results, RaceState admission,
   // final certificate reason, and whether the configured toggle produced an edge.
   session().write(race_epoch_capture_json(0,0,true,f.input_focused,f.toggle_pressed_focused,f.toggle_edge,f.config.toggle));
  }catch(...){}
 }}
}
void GameFov::submission_snapshot(uintptr_t expected_camera,CameraSubmissionSnapshot& out) const noexcept {
 out=submission_;
 if(out.available&&!camera_submission_matches(out,expected_camera)){out.available=false;out.status="camera_owner_changed";}
}
bool GameFov::allows(const D3DMATRIX& p) const noexcept {
 return enabled_&&fov_enabled_&&GetCurrentThreadId()==thread_&&frame_.matches(current_camera(base_),p);
}
bool GameFov::cinematic_projection_vfov(const D3DMATRIX& p,bool exe,uint32_t rva,float& vfov) const noexcept {
 if(!enabled_||!flight_||!flight_->controller.active||!flight_->config.cinematic_fov_enabled||!exe||rva!=GAMEPLAY_PROJECTION_RETURN_RVA||GetCurrentThreadId()!=thread_||
    !frame_.status.synchronized||!frame_.matches(current_camera(base_),p))return false;
 const double selected=flight_->controller.current_vertical_fov();if(!std::isfinite(selected)||selected<30||selected>110)return false;
 vfov=static_cast<float>(selected);return true;
}
void GameFov::projection_applied(float vfov,bool success) noexcept {
 if(!flight_)return;auto& f=*flight_;f.projection_vfov=vfov;
 f.projection_frustum_synchronized=success&&frame_.status.synchronized&&std::isfinite(vfov)&&std::abs(double(vfov)-frame_.status.vfov)<.001;
 f.projection_reason=f.projection_frustum_synchronized?"projection_matches_cpu_frustum":success?"projection_frustum_mismatch":"projection_rewrite_rejected";
 if(!f.projection_frustum_synchronized&&frame_.status.synchronized){cancel_frame();f.projection_reason=frame_.status.restored?"projection_rejected_scope_restored":"projection_rejected_scope_not_restored";}
}
void GameFov::finish_frame() noexcept {
 // Present occurs inside EndFrame: late readers must still see the same scope.
 if(scheduler_depth_)return;cancel_frame();
}
void GameFov::cancel_frame() noexcept {
 if(thread_&&GetCurrentThreadId()!=thread_){frame_.abandon();if(flight_){flight_->pose_scope=false;flight_->controller.cancel();flight_->input.set_cursor_capture(false);flight_->visible=false;flight_->reason="wrong_thread_no_stale_restore";++flight_->failures;}submission_=CameraSubmissionSnapshot{};return;}
 if(flight_&&flight_->pose_scope){auto& f=*flight_;auto c=live_race_certificate(f.scope_certificate.camera);
  if(current_camera(base_)!=reinterpret_cast<CameraFrame*>(f.scope_certificate.camera)||!c.valid||c.owner_lifetime!=f.scope_certificate.owner_lifetime||c.race_generation!=f.scope_certificate.race_generation){frame_.abandon();f.controller.cancel();f.input.set_cursor_capture(false);++f.failures;f.reason="scope_identity_changed_no_stale_restore";}
  else if(frame_.restore()){++f.restores;if(f.restores==1)try{session().write("{\"type\":\"free_camera_scope\",\"phase\":\"R-CAM1-A3d\",\"event\":\"first_verified_restore_after_scheduler\",\"owned_bytes\":176}");}catch(...){}}else {f.controller.cancel();f.input.set_cursor_capture(false);++f.failures;f.reason="camera_restore_failed";}
  f.pose_scope=false;
 }else if(!frame_.restore()){enabled_=false;frame_.status.reason="camera_restore_failed";}
 submission_=CameraSubmissionSnapshot{};
}
void GameFov::cancel_lifecycle(const char* reason) noexcept {cancel_frame();if(flight_){flight_->controller.cancel();flight_->input.focus_lost();flight_->visible=false;flight_->certificate.valid=false;flight_->certificate.reason=reason;flight_->reason=reason;}}
void GameFov::scheduler_begin() noexcept {if(thread_&&GetCurrentThreadId()!=thread_){disable("wrong_scheduler_thread");return;}if(++scheduler_depth_!=1){cancel_frame();if(flight_){flight_->controller.cancel();flight_->input.set_cursor_capture(false);}frame_.status.reason="scheduler_reentry";}}
void GameFov::scheduler_end() noexcept {if(thread_&&GetCurrentThreadId()!=thread_){disable("wrong_scheduler_thread");return;}if(!scheduler_depth_){disable("scheduler_depth_underflow");return;}--scheduler_depth_;if(!scheduler_depth_)cancel_frame();}
void GameFov::stock_view(const D3DMATRIX& v) noexcept {
 if(!flight_||!flight_->config.enabled||flight_->controller.active||!submission_.available)return;
 auto& f=*flight_;f.visible=pose_from_native_view(v,f.visible_pose)&&f.certificate.valid;f.visible_certificate=f.certificate;
}
bool GameFov::free_camera_configured() const noexcept {return flight_&&flight_->config.enabled;}
bool GameFov::free_camera_active() const noexcept {return flight_&&flight_->controller.active;}
std::string GameFov::camera_json() const {
 std::ostringstream o;o<<"{\"configured\":"<<(free_camera_configured()?"true":"false")<<",\"active\":"<<(free_camera_active()?"true":"false")<<",\"scheduler_depth\":"<<scheduler_depth_<<",\"scope_restored\":"<<(frame_.status.restored?"true":"false");
 if(flight_){auto& f=*flight_;auto& c=f.controller;const auto& clock=f.input.clock();const auto& timing=clock.stats();const char* clock_source=clock.source()==FlightClockSource::qpc?"qpc":clock.source()==FlightClockSource::tick_count64?"get_tick_count64":"unavailable";const char* fov_source=c.active&&f.config.cinematic_fov_enabled?"cinematic_freecam":fov_enabled_?"gameplay_fov":"stock";o<<",\"reason\":"<<quote(f.reason)<<",\"certificate_valid\":"<<(f.certificate.valid?"true":"false")<<",\"certificate_reason\":"<<quote(f.certificate.reason)<<",\"race_generation\":"<<f.certificate.race_generation<<",\"owner_lifetime\":"<<f.certificate.owner_lifetime<<",\"camera\":"<<f.certificate.camera<<",\"toggle_key_vk\":"<<f.config.toggle<<",\"toggle_pressed_while_focused\":"<<((f.input_focused&&f.toggle_pressed_focused)?"true":"false")<<",\"controller_toggle_edge\":"<<(f.toggle_edge?"true":"false")<<",\"cinematic_fov_enabled\":"<<(f.config.cinematic_fov_enabled?"true":"false")<<",\"fov_source\":"<<quote(fov_source)<<",\"effective_vertical_fov\":"<<f.effective_vfov<<",\"target_vertical_fov\":"<<c.target_vertical_fov()<<",\"effective_horizontal_fov\":"<<f.effective_hfov<<",\"fov_transition_active\":"<<(c.fov_transition_active()?"true":"false")<<",\"projection_frustum_synchronized\":"<<(f.projection_frustum_synchronized?"true":"false")<<",\"projection_vfov\":"<<f.projection_vfov<<",\"fov_validation_reason\":"<<quote(f.projection_reason)<<",\"manual_roll_enabled\":"<<(f.config.manual_roll_enabled?"true":"false")<<",\"manual_roll_degrees\":"<<c.manual_roll_degrees<<",\"manual_roll_target_degrees\":"<<c.manual_roll_target_degrees<<",\"manual_roll_transition_active\":"<<(c.manual_roll_transition_active?"true":"false")<<",\"roll_speed_degrees_per_second\":"<<f.config.roll_speed<<",\"roll_smooth_seconds\":"<<f.config.roll_smooth_seconds<<",\"configured_base_speed\":"<<f.config.speed<<",\"current_base_speed\":"<<c.current_speed()<<",\"minimum_base_speed\":"<<f.config.min_speed<<",\"maximum_base_speed\":"<<f.config.max_speed<<",\"wheel_speed_factor\":"<<f.config.wheel_speed_factor<<",\"movement_smoothing_seconds\":"<<f.config.movement_smooth_seconds<<",\"current_velocity_magnitude\":"<<c.velocity_magnitude()<<",\"speed_input_source\":"<<quote(c.speed_input_source())<<",\"speed_adjustment_count\":"<<c.speed_adjustment_count()<<",\"flight_clock_source\":"<<quote(clock_source)<<",\"flight_clock_frequency_hz\":"<<clock.frequency()<<",\"flight_dt_last_ms\":"<<timing.last_seconds*1000<<",\"flight_dt_min_ms\":"<<timing.min_seconds*1000<<",\"flight_dt_max_ms\":"<<timing.max_seconds*1000<<",\"flight_dt_mean_ms\":"<<timing.mean_seconds*1000<<",\"flight_dt_zero_samples\":"<<timing.zero_samples<<",\"flight_dt_clamped_samples\":"<<timing.clamped_samples<<",\"flight_clock_invalid_samples\":"<<timing.invalid_samples<<",\"wheel_input_available\":"<<(f.input.wheel_input_available()?"true":"false")<<",\"wheel_input_status\":"<<quote(f.input.wheel_input_available()?"game_hwnd_subclass_delta_forwarded":"unavailable_without_game_hwnd")<<",\"cursor_capture_active\":"<<(f.input.cursor_capture_active()?"true":"false")<<",\"cursor_policy\":"<<quote(f.input.cursor_capture_active()?"focused_freecam_suppress_client_setcursor":"native_window_policy")<<",\"look_smoothing_seconds\":0,\"look_smoothing_status\":\"deferred_to_preserve_mouse_precision\",\"horizon_mode\":"<<quote(f.config.auto_level_horizon?"auto_level":"native_roll")<<",\"horizon_leveling_active\":"<<(c.horizon_leveling_active?"true":"false")<<",\"current_roll_degrees\":"<<c.current_roll_degrees<<",\"target_roll_degrees\":"<<c.target_roll_degrees<<",\"horizon_level_progress\":"<<c.horizon_level_progress<<",\"orientation_valid\":"<<(c.orientation_valid?"true":"false")<<",\"scopes\":"<<f.scopes<<",\"restores\":"<<f.restores<<",\"failures\":"<<f.failures;}
 o<<'}';return o.str();
}
std::string free_camera_snapshot_json(){return active?active->camera_json():"{\"configured\":false,\"active\":false,\"reason\":\"shared_camera_hook_inactive\"}";}
void GameFov::disable(const char* reason) noexcept {
 cancel_lifecycle(reason);enabled_=false;if(flight_){flight_->input.release();flight_->config.enabled=false;}submission_=CameraSubmissionSnapshot{};if(active==this)active=nullptr;
 // Startup/teardown are on the renderer thread; never hot-patch from an unreviewed thread.
 if(GetCurrentThreadId()==thread_){patch_.remove(memory);completion_.remove(memory);}
 frame_.status.installed=patch_.installed();frame_.status.reason=reason;report(frame_.status);
}
GameFov::~GameFov(){if(patch_.installed()||completion_.installed())disable("device_release");}
}
