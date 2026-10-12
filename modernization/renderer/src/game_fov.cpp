#include "game_fov.hpp"
#include "free_camera.hpp"
#include "camera_bookmarks.hpp"
#include "race_epoch.hpp"
#include "physics_probe.hpp"
#include "trace.hpp"
#include <sstream>
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <iomanip>
#include <intrin.h>
#include <cfenv>
namespace gfx2 {
struct FlightState {
 FreeCameraConfig config;FlightWindowInput input;FlightController controller;RaceCertificate certificate,visible_certificate,scope_certificate;
 std::string display_mode="unknown";uintptr_t game_hwnd=0,d3d_focus_hwnd=0;
 std::array<float,16> visible_pose{};bool visible=false,pose_scope=false;
 bool road_preview_context_published=false,road_preview_context_valid=false;
 uint64_t road_preview_race_generation=0,road_preview_owner_lifetime=0;
 bool speed_identity_valid=false;uint64_t speed_race_generation=0,speed_owner_lifetime=0;
 const char* reason="disabled";uint64_t scopes=0,restores=0,failures=0;
 bool reported_valid=false,reported_active=false,reported_horizon_leveling=false;uint64_t reported_race=0,reported_owner=0;const char* reported_reason="disabled";
 bool input_focused=false,toggle_pressed_focused=false,toggle_edge=false;
 bool road_teleport_arm_down=false;uint64_t reported_road_teleport_sequence=UINT64_MAX;
 const char* reported_road_teleport_state="",*reported_road_teleport_reason="";
 bool clean_view_requested=false,clean_view_toggle_down=false,clean_view_initial_pending=false,pause_known=false,pause_enabled=false;
 CleanViewFrameContext clean_view_frame{};uint64_t clean_view_disarm_count=0;
 const char* clean_view_last_disarm_reason="none";bool clean_view_toggle_edge=false,clean_view_initial_armed=false;
 const char* clean_view_reason="pilot_disabled";
 bool reported_input_focused=false,reported_toggle_pressed=false,reported_toggle_edge=false;
 bool reported_clean_view_requested=false,reported_pause_known=false,reported_pause_enabled=false;
 bool reported_cursor_capture=false;uint64_t reported_speed_adjustments=0;
 uintptr_t reported_foreground_hwnd=0,reported_keyboard_focus_hwnd=0;bool reported_wndproc_owned=false,reported_window_valid=false,reported_minimized=false;
 CameraBookmarkSet bookmarks{};std::wstring bookmark_path;CameraBookmarkIo bookmark_storage=CameraBookmarkIo::path_unavailable;
 unsigned bookmark_current_slot=1;bool bookmark_save_down=false,bookmark_load_down=false,bookmark_next_down=false;
 const char* bookmark_last_action="none";const char* bookmark_last_result="not_requested";uint64_t bookmark_action_count=0,bookmark_save_count=0,bookmark_load_count=0,bookmark_reject_count=0;
 FlightBookmarkPose bookmark_last_pose{};bool bookmark_last_pose_valid=false;
 unsigned reported_bookmark_slot=0;uint64_t reported_bookmark_action_count=0;
 float effective_vfov=0,effective_hfov=0,projection_vfov=0;bool projection_frustum_synchronized=false;
 const char* projection_reason="awaiting_projection_call";
 void disarm_clean_view(const char* why) noexcept {
  if(clean_view_requested){++clean_view_disarm_count;clean_view_last_disarm_reason=why?why:"disarmed";}
  clean_view_requested=false;clean_view_frame={};clean_view_reason=why?why:"disarmed";
 }
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
bool pressed_edge(bool focused,bool down,bool& previous) noexcept {bool edge=focused&&down&&!previous;previous=focused&&down;return edge;}
void bookmark_result(FlightState& f,const char* action,const char* result) noexcept {
 f.bookmark_last_action=action?action:"unknown";f.bookmark_last_result=result?result:"unknown";
 if(f.bookmark_action_count!=UINT64_MAX)++f.bookmark_action_count;
 const char* event="bookmark_invalid";
 if(action&&std::strcmp(action,"select")==0&&result&&std::strcmp(result,"slot_selected")==0)event="bookmark_slot_changed";
 else if(action&&std::strcmp(action,"save")==0&&result&&std::strcmp(result,"saved_atomically")==0)event="bookmark_saved";
 else if(action&&std::strcmp(action,"load")==0&&result&&std::strcmp(result,"loaded_exact_pose")==0)event="bookmark_loaded";
 else if(result&&std::strcmp(result,"empty_slot")==0)event="bookmark_empty";
 else if(result&&std::strcmp(result,"supported_course_job_not_verified")==0)event="bookmark_course_mismatch";
 else if(action&&std::strcmp(action,"save")==0&&(result&&(
          std::strcmp(result,"io_error")==0||std::strcmp(result,"local_appdata_unavailable")==0)))event="bookmark_write_failed";
 else if(action&&std::strcmp(action,"load")==0&&result&&(
          std::strcmp(result,"io_error")==0||std::strcmp(result,"local_appdata_unavailable")==0))event="bookmark_read_failed";
 try{session().write("{\"type\":\"camera_bookmark_event\",\"event\":"+quote(std::string(event))+
  ",\"action\":"+quote(std::string(f.bookmark_last_action))+
  ",\"slot\":"+std::to_string(f.bookmark_current_slot)+
  ",\"course_id\":"+(f.certificate.valid?quote(std::string(CAMERA_BOOKMARK_COURSE_ID)):"null")+
  ",\"course_reason\":"+quote(std::string(f.certificate.reason?f.certificate.reason:"unknown"))+
  ",\"reason\":"+quote(std::string(f.bookmark_last_result))+"}");}catch(...){}
}
void process_bookmark_inputs(FlightState& f,const FlightInput& input,bool flying) noexcept {
 if(!input.focused){f.bookmark_save_down=f.bookmark_load_down=f.bookmark_next_down=true;return;}
 const bool save=pressed_edge(true,input.save_camera_bookmark,f.bookmark_save_down);
 const bool load=pressed_edge(true,input.load_camera_bookmark,f.bookmark_load_down);
 const bool next=pressed_edge(true,input.next_camera_bookmark_slot,f.bookmark_next_down);
 if(!save&&!load&&!next)return;
 const char* gate=!f.config.camera_bookmarks_enabled?"bookmarks_disabled":!flying?"freecam_inactive":
  !f.certificate.valid?(f.certificate.reason&&std::strcmp(f.certificate.reason,"supported_course_job_not_verified")==0?"supported_course_job_not_verified":"live_france1_certificate_required"):
  !f.input.intact()?"game_window_input_unavailable":nullptr;
 if(gate){bookmark_result(f,next?"select":save?"save":"load",gate);if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;return;}
 if(next){f.bookmark_current_slot=f.bookmark_current_slot%static_cast<unsigned>(CAMERA_BOOKMARK_SLOT_COUNT)+1;bookmark_result(f,"select","slot_selected");}
 try{
  if(save){FlightBookmarkPose pose{};if(!f.controller.capture_bookmark(pose,f.config)){bookmark_result(f,"save","controller_pose_unavailable");if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;return;}
   CameraBookmark bookmark;bookmark.present=true;bookmark.slot=f.bookmark_current_slot;bookmark.label="Bookmark "+std::to_string(f.bookmark_current_slot);bookmark.camera=pose;
   if(!current_utc_timestamp(bookmark.saved_at_utc)){bookmark_result(f,"save","timestamp_unavailable");if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;return;}
   if(f.bookmark_path.empty()||!ensure_camera_bookmark_directory()){f.bookmark_storage=CameraBookmarkIo::path_unavailable;bookmark_result(f,"save",camera_bookmark_io_name(f.bookmark_storage));if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;return;}
   CameraBookmarkSet updated;f.bookmark_storage=save_camera_bookmark(f.bookmark_path,f.bookmark_current_slot,bookmark,updated);
   if(f.bookmark_storage==CameraBookmarkIo::ok){f.bookmarks=std::move(updated);f.bookmark_last_pose=pose;f.bookmark_last_pose_valid=true;if(f.bookmark_save_count!=UINT64_MAX)++f.bookmark_save_count;bookmark_result(f,"save","saved_atomically");}
   else {bookmark_result(f,"save",camera_bookmark_io_name(f.bookmark_storage));if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;}
  }
  if(load){const auto& bookmark=f.bookmarks.slots[f.bookmark_current_slot-1];
   if(!bookmark.present){const char* why=f.bookmark_storage==CameraBookmarkIo::io_error||f.bookmark_storage==CameraBookmarkIo::path_unavailable?"io_error":
      f.bookmark_storage==CameraBookmarkIo::invalid||f.bookmark_storage==CameraBookmarkIo::identity_mismatch?"invalid_file_or_bookmark":"empty_slot";
    bookmark_result(f,"load",why);if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;return;}
   if(f.bookmark_storage==CameraBookmarkIo::missing)f.bookmark_storage=CameraBookmarkIo::ok;
   if(!f.controller.restore_bookmark(bookmark.camera,f.config)){bookmark_result(f,"load","bookmark_pose_rejected");if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;return;}
   f.input.discard_after_bookmark_load();f.bookmark_last_pose=bookmark.camera;f.bookmark_last_pose_valid=true;if(f.bookmark_load_count!=UINT64_MAX)++f.bookmark_load_count;bookmark_result(f,"load","loaded_exact_pose");
  }
 }catch(...){bookmark_result(f,save?"save":"load","bounded_operation_exception");if(f.bookmark_reject_count!=UINT64_MAX)++f.bookmark_reject_count;}
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
bool GameFov::install(bool exact,const VisualConfig& c,HWND window,bool exact_retail,uint64_t device_id,const Trace* trace,const char* display_mode,HWND d3d_focus_window) noexcept {
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
 detail::original_submit=base_+SUBMIT_OWNER_RVA;active=this;device_id_=device_id;trace_=trace;scheduler_generation_=0;
 enabled_=patch_.install(memory,reinterpret_cast<void*>(base_+SUBMIT_CALL_RVA),reinterpret_cast<uintptr_t>(&detail::submit_bridge),SUBMIT_CALL_BYTES);
 frame_.status.installed=patch_.installed();frame_.status.reason=enabled_?"installed_before_device_return":"call_patch_failed";
 if(!enabled_){active=nullptr;patch_.remove(memory);completion_.remove(memory);frame_.status.installed=patch_.installed()||completion_.installed();}
 if(enabled_&&flight_config.enabled){flight_=&flight_state;flight_->config=flight_config;flight_->display_mode=display_mode?display_mode:"unknown";flight_->game_hwnd=reinterpret_cast<uintptr_t>(window);flight_->d3d_focus_hwnd=reinterpret_cast<uintptr_t>(d3d_focus_window?d3d_focus_window:window);flight_->controller.cancel();flight_->speed_identity_valid=false;flight_->visible=false;flight_->clean_view_requested=global_hud_request_;flight_->clean_view_toggle_down=false;flight_->clean_view_initial_pending=false;flight_->clean_view_frame={};flight_->clean_view_disarm_count=0;flight_->clean_view_last_disarm_reason="none";flight_->clean_view_toggle_edge=false;flight_->clean_view_initial_armed=false;
  flight_->bookmarks=CameraBookmarkSet{};flight_->bookmark_current_slot=flight_config.camera_bookmark_default_slot;flight_->bookmark_save_down=flight_->bookmark_load_down=flight_->bookmark_next_down=false;
  flight_->bookmark_last_action="none";flight_->bookmark_last_result="not_requested";flight_->bookmark_action_count=flight_->bookmark_save_count=flight_->bookmark_load_count=flight_->bookmark_reject_count=0;flight_->bookmark_last_pose={};flight_->bookmark_last_pose_valid=false;
  flight_->bookmark_path=flight_config.camera_bookmarks_enabled?default_camera_bookmark_path():std::wstring{};
  flight_->bookmark_storage=flight_->bookmark_path.empty()?CameraBookmarkIo::path_unavailable:read_camera_bookmarks(flight_->bookmark_path,flight_->bookmarks);
  flight_->reported_bookmark_slot=0;flight_->reported_bookmark_action_count=UINT64_MAX;
  flight_->reason=flight_->input.attach(window)?"awaiting_live_race_certificate":"game_window_input_unavailable";flight_->road_teleport_arm_down=false;flight_->reported_road_teleport_sequence=UINT64_MAX;flight_->reported_road_teleport_state="";if(!flight_->input.intact())flight_->config.enabled=false;}
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
  cancel_frame();if(flight_){flight_->controller.cancel();flight_->input.set_cursor_capture(false);flight_->visible=false;flight_->disarm_clean_view("camera_schedule_unmapped");}frame_.status.reason="unmapped_camera_schedule";return;
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
  if(!f.road_preview_context_published||f.road_preview_context_valid!=f.certificate.valid||
     f.road_preview_race_generation!=f.certificate.race_generation||
     f.road_preview_owner_lifetime!=f.certificate.owner_lifetime){
   publish_physics_probe_race_context(f.certificate.valid,f.certificate.race_generation,
                                      f.certificate.owner_lifetime);
   f.road_preview_context_published=true;f.road_preview_context_valid=f.certificate.valid;
   f.road_preview_race_generation=f.certificate.race_generation;
   f.road_preview_owner_lifetime=f.certificate.owner_lifetime;
  }
  if(f.certificate.valid&&(!f.speed_identity_valid||f.speed_race_generation!=f.certificate.race_generation||f.speed_owner_lifetime!=f.certificate.owner_lifetime)){
   f.controller.reset_for_race(f.config);f.speed_identity_valid=true;f.speed_race_generation=f.certificate.race_generation;f.speed_owner_lifetime=f.certificate.owner_lifetime;
  }
  if(!f.certificate.valid)f.visible=false;
  const RaceScalar pause=read_pause_menu_state_readonly();f.pause_known=pause.present&&pause.tag==0;f.pause_enabled=f.pause_known&&pause.value!=0;
  publish_physics_probe_pause_state(f.pause_known,f.pause_enabled,GetTickCount64());
  auto input=f.input.sample(f.config,f.controller.active);
  input.inherited_vfov=fov_enabled_?vfov_:submission_.camera.source_angle/std::max(1.f,float(submission_.camera.width)/submission_.camera.height);
  bool visible=f.visible&&f.visible_certificate.camera==camera&&f.visible_certificate.owner_lifetime==f.certificate.owner_lifetime&&f.visible_certificate.race_generation==f.certificate.race_generation;
  const bool camera_admission=free_camera_admitted(f.certificate.valid,f.pause_known,f.pause_enabled);
  bool flying=f.controller.update(f.config,input,camera_admission,visible?&f.visible_pose:nullptr);
   process_bookmark_inputs(f,input,flying);
  const bool road_teleport_arm_edge=input.focused&&input.arm_road_teleport&&!f.road_teleport_arm_down;
  if(!input.focused)f.road_teleport_arm_down=true;else if(!input.arm_road_teleport)f.road_teleport_arm_down=false;else f.road_teleport_arm_down=true;
  if(road_teleport_arm_edge&&f.config.vehicle_teleport_enabled){
   arm_physics_probe_road_teleport(f.controller.pose[12],f.controller.pose[13],f.controller.pose[14],
    flying,f.pause_known,f.pause_enabled,f.certificate,
    f.config.vehicle_teleport_arm_timeout_seconds,f.config.vehicle_teleport_max_road_distance);
  }
  f.input.set_cursor_capture(flying&&input.focused);
  f.input_focused=input.focused;f.toggle_pressed_focused=input.focused&&input.toggle;f.toggle_edge=f.controller.last_toggle_edge;
  const bool clean_context=f.config.clean_view_pilot&&f.certificate.valid&&f.controller.active&&f.pause_known&&f.pause_enabled&&input.focused&&f.input.intact();
  // The session HUD preference owns H. Clean View consumes that same request
  // under its existing paused-Freecam admission; it no longer polls its own key.
  f.clean_view_requested=global_hud_request_;f.clean_view_toggle_edge=false;f.clean_view_initial_pending=false;
  if(clean_context&&global_hud_request_)f.clean_view_initial_armed=true;
  f.clean_view_reason=!f.config.clean_view_pilot?f.config.clean_view_config_reason:!f.clean_view_requested?"user_off":!clean_context?"freecam_pause_or_focus_gate":"pending_draw_scope";
  if(clean_context){f.clean_view_frame={};f.clean_view_frame.valid=true;f.clean_view_frame.scheduler_generation=scheduler_generation_;
   f.clean_view_frame.race_generation=f.certificate.race_generation;f.clean_view_frame.owner_lifetime=f.certificate.owner_lifetime;
   f.clean_view_frame.camera=f.certificate.camera;f.clean_view_frame.device_id=device_id_;f.clean_view_frame.trace_frame=trace_?trace_->frame_number():0;
   f.clean_view_frame.sampled_tick_ms=GetTickCount64();f.clean_view_frame.render_thread=thread_;}
  f.reason=flying?"freecam_active":!input.focused?"focus_lost":!f.certificate.valid?f.certificate.reason:!f.pause_known?"pause_state_unavailable":!f.pause_enabled?"race_not_paused":visible?"ready_toggle_off":"awaiting_displayed_stock_view";
  if(flying){effective_pose=&f.controller.pose;f.scope_certificate=f.certificate;f.pose_scope=true;}
 }
 if(fov_enabled_||effective_pose){float fov=fov_enabled_?vfov_:submission_.camera.source_angle/std::max(1.f,float(submission_.camera.width)/submission_.camera.height);
  if(effective_pose&&flight_&&flight_->config.cinematic_fov_enabled&&flight_->controller.current_vertical_fov()>0)fov=static_cast<float>(flight_->controller.current_vertical_fov());
  if(flight_){flight_->projection_frustum_synchronized=false;flight_->projection_reason=effective_pose&&flight_->config.cinematic_fov_enabled?"awaiting_cinematic_projection":"awaiting_projection_call";}
  if(!frame_.begin(reinterpret_cast<CameraFrame*>(camera),fov,effective_pose)){if(flight_){flight_->controller.cancel();flight_->input.set_cursor_capture(false);flight_->pose_scope=false;++flight_->failures;flight_->reason="effective_camera_ineligible_or_write_failed";flight_->projection_reason="frustum_scope_failed";}if(!frame_.status.restored)disable("camera_restore_failed");}
  else {if(flight_){flight_->effective_vfov=frame_.status.vfov;flight_->effective_hfov=frame_.status.hfov;flight_->projection_reason=effective_pose&&flight_->config.cinematic_fov_enabled?"awaiting_cinematic_projection":"awaiting_projection_call";}
   if(effective_pose&&flight_){++flight_->scopes;if(flight_->scopes==1)try{session().write("{\"type\":\"free_camera_scope\",\"phase\":\"R-CAM1-A3d\",\"event\":\"first_effective_scope\",\"owned_bytes\":176,\"pre_call_va\":6632157}");}catch(...){}}}
 }
  if(flight_){auto& f=*flight_;const auto road_status=physics_probe_road_teleport_status();const bool road_status_changed=f.reported_road_teleport_sequence!=road_status.sequence||std::strcmp(f.reported_road_teleport_state,road_status.state)!=0||std::strcmp(f.reported_road_teleport_reason,road_status.reason)!=0;if(road_status_changed){
   f.reported_road_teleport_sequence=road_status.sequence;f.reported_road_teleport_state=road_status.state;f.reported_road_teleport_reason=road_status.reason;
  }
  const auto window_state=f.input.snapshot();const bool window_state_changed=window_state.foreground_hwnd!=f.reported_foreground_hwnd||window_state.keyboard_focus_hwnd!=f.reported_keyboard_focus_hwnd||window_state.wndproc_owned!=f.reported_wndproc_owned||window_state.window_valid!=f.reported_window_valid||window_state.minimized!=f.reported_minimized;
  if(f.reported_valid!=f.certificate.valid||f.reported_active!=f.controller.active||f.reported_horizon_leveling!=f.controller.horizon_leveling_active||f.reported_race!=f.certificate.race_generation||f.reported_owner!=f.certificate.owner_lifetime||f.reported_input_focused!=f.input_focused||f.reported_toggle_pressed!=f.toggle_pressed_focused||f.reported_toggle_edge!=f.toggle_edge||f.reported_cursor_capture!=f.input.cursor_capture_active()||f.reported_speed_adjustments!=f.controller.speed_adjustment_count()||f.reported_clean_view_requested!=f.clean_view_requested||f.reported_pause_known!=f.pause_known||f.reported_pause_enabled!=f.pause_enabled||f.reported_bookmark_slot!=f.bookmark_current_slot||f.reported_bookmark_action_count!=f.bookmark_action_count||std::strcmp(f.reported_reason,f.reason)||road_status_changed||window_state_changed){
   f.reported_valid=f.certificate.valid;f.reported_active=f.controller.active;f.reported_horizon_leveling=f.controller.horizon_leveling_active;f.reported_race=f.certificate.race_generation;f.reported_owner=f.certificate.owner_lifetime;f.reported_input_focused=f.input_focused;f.reported_toggle_pressed=f.toggle_pressed_focused;f.reported_toggle_edge=f.toggle_edge;f.reported_cursor_capture=f.input.cursor_capture_active();f.reported_speed_adjustments=f.controller.speed_adjustment_count();f.reported_clean_view_requested=f.clean_view_requested;f.reported_pause_known=f.pause_known;f.reported_pause_enabled=f.pause_enabled;f.reported_bookmark_slot=f.bookmark_current_slot;f.reported_bookmark_action_count=f.bookmark_action_count;f.reported_reason=f.reason;f.reported_foreground_hwnd=window_state.foreground_hwnd;f.reported_keyboard_focus_hwnd=window_state.keyboard_focus_hwnd;f.reported_wndproc_owned=window_state.wndproc_owned;f.reported_window_valid=window_state.window_valid;f.reported_minimized=window_state.minimized;
  try{session().write("{\"type\":\"free_camera_state\",\"phase\":\"R-CAM1-A3g\",\"state\":"+camera_json()+"}");
   session().write("{\"type\":\"freecam_window_input\",\"display_mode\":"+quote(f.display_mode)+",\"game_hwnd\":"+std::to_string(f.game_hwnd)+",\"attached_hwnd\":"+std::to_string(window_state.attached_hwnd)+",\"d3d_focus_hwnd\":"+std::to_string(f.d3d_focus_hwnd)+",\"foreground_hwnd\":"+std::to_string(window_state.foreground_hwnd)+",\"keyboard_focus_hwnd\":"+std::to_string(window_state.keyboard_focus_hwnd)+",\"hwnd_thread\":"+std::to_string(window_state.hwnd_thread)+",\"current_thread\":"+std::to_string(window_state.current_thread)+",\"process_id\":"+std::to_string(window_state.process_id)+",\"wndproc_owned\":"+(window_state.wndproc_owned?"true":"false")+",\"window_valid\":"+(window_state.window_valid?"true":"false")+",\"window_minimized\":"+(window_state.minimized?"true":"false")+",\"client_size_valid\":"+(window_state.client_size_valid?"true":"false")+",\"client_width\":"+std::to_string(window_state.client_width)+",\"client_height\":"+std::to_string(window_state.client_height)+",\"input_focus_accepted\":"+(window_state.input_focus_accepted?"true":"false")+",\"toggle_key_observed\":"+(f.toggle_pressed_focused?"true":"false")+",\"toggle_edge_generated\":"+(f.toggle_edge?"true":"false")+",\"race_certified\":"+(f.certificate.valid?"true":"false")+",\"race_certificate_reason\":"+quote(f.certificate.reason)+",\"pause_verified\":"+(f.pause_known&&f.pause_enabled?"true":"false")+",\"camera_owner_accepted\":"+(f.certificate.valid&&f.certificate.camera?"true":"false")+",\"camera_admission_accepted\":"+(free_camera_admitted(f.certificate.valid,f.pause_known,f.pause_enabled)?"true":"false")+",\"activation_result\":"+(f.controller.active?"active":"inactive")+",\"rejection_reason\":"+quote(f.reason)+"}");
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
void GameFov::cancel_lifecycle(const char* reason) noexcept {cancel_frame();if(flight_){publish_physics_probe_race_context(false,0,0);flight_->road_preview_context_published=true;flight_->road_preview_context_valid=false;flight_->road_preview_race_generation=0;flight_->road_preview_owner_lifetime=0;flight_->controller.cancel();flight_->input.focus_lost();flight_->visible=false;flight_->certificate.valid=false;flight_->certificate.reason=reason;flight_->reason=reason;flight_->disarm_clean_view(reason?reason:"lifecycle_cancelled");flight_->clean_view_toggle_down=false;}}
void GameFov::scheduler_begin() noexcept {if(thread_&&GetCurrentThreadId()!=thread_){disable("wrong_scheduler_thread");return;}if(++scheduler_depth_!=1){cancel_frame();if(flight_){flight_->controller.cancel();flight_->input.set_cursor_capture(false);flight_->clean_view_frame={};}frame_.status.reason="scheduler_reentry";return;}++scheduler_generation_;if(flight_)flight_->clean_view_frame={};}
void GameFov::scheduler_end() noexcept {if(thread_&&GetCurrentThreadId()!=thread_){disable("wrong_scheduler_thread");return;}if(!scheduler_depth_){disable("scheduler_depth_underflow");return;}--scheduler_depth_;if(!scheduler_depth_){cancel_frame();if(flight_&&flight_->clean_view_frame.valid&&flight_->clean_view_frame.scheduler_generation==scheduler_generation_)flight_->clean_view_frame.completed=true;}}
void GameFov::stock_view(const D3DMATRIX& v) noexcept {
 if(!flight_||!flight_->config.enabled||flight_->controller.active||!submission_.available)return;
 auto& f=*flight_;f.visible=pose_from_native_view(v,f.visible_pose)&&f.certificate.valid;f.visible_certificate=f.certificate;
}
bool GameFov::free_camera_configured() const noexcept {return flight_&&flight_->config.enabled;}
bool GameFov::free_camera_active() const noexcept {return flight_&&flight_->controller.active;}
bool GameFov::race_lifecycle_generation(uint64_t& generation) const noexcept {
 if(!flight_||!flight_->certificate.valid||!flight_->certificate.race_generation)return false;
 generation=flight_->certificate.race_generation;return true;
}
bool GameFov::clean_view_requested() const noexcept {return global_hud_request_;}
void GameFov::set_global_hud_request(bool requested) noexcept {global_hud_request_=requested;if(flight_)flight_->clean_view_requested=requested;}
bool GameFov::clean_view_toggle_edge_seen() const noexcept {return flight_&&flight_->clean_view_toggle_edge;}
bool GameFov::clean_view_initial_armed() const noexcept {return flight_&&flight_->clean_view_initial_armed;}
uint64_t GameFov::clean_view_disarm_count() const noexcept {return flight_?flight_->clean_view_disarm_count:0;}
const char* GameFov::clean_view_last_disarm_reason() const noexcept {return flight_?flight_->clean_view_last_disarm_reason:"none";}
uint64_t GameFov::clean_view_context_trace_frame() const noexcept {return flight_?flight_->clean_view_frame.trace_frame:0;}
uint64_t GameFov::clean_view_context_scheduler_generation() const noexcept {return flight_?flight_->clean_view_frame.scheduler_generation:0;}
CleanViewAdmission GameFov::clean_view_admission(bool device_scope_valid,bool ui_hook_owned,bool native_ui_scope_valid,uint64_t device_id) noexcept {
 CleanViewAdmissionFacts facts{};
 if(!flight_)return evaluate_clean_view_admission(facts);
 auto& f=*flight_;facts.pilot=f.config.clean_view_pilot;facts.requested=global_hud_request_;
 facts.exact_build=base_==0x400000;facts.render_thread=thread_&&GetCurrentThreadId()==thread_;
 const auto& context=f.clean_view_frame;const auto live=context.valid?live_race_certificate(context.camera):RaceCertificate{};
 facts.race_certificate=context.valid&&live.valid&&live.race_generation==context.race_generation&&live.owner_lifetime==context.owner_lifetime&&
  f.certificate.valid&&f.certificate.race_generation==context.race_generation&&f.certificate.owner_lifetime==context.owner_lifetime;
 facts.freecam_active=f.config.enabled&&f.controller.active;
 const RaceScalar pause=read_pause_menu_state_readonly();facts.pause_known=pause.present&&pause.tag==0;facts.paused=facts.pause_known&&pause.value!=0;
 facts.window_valid=f.input.intact()&&f.input.focused_now();const bool device_identity_valid=device_id&&device_id==device_id_;
 facts.device_scope_valid=device_scope_valid&&device_identity_valid;
 CleanViewFrameCheck frame_check{};
 facts.frame_context_current=clean_view_frame_context_fresh(context,scheduler_generation_,trace_?trace_->frame_number():0,thread_,device_id,GetTickCount64(),250,scheduler_depth_,native_ui_scope_valid,&frame_check);
 facts.ui_hook_owned=ui_hook_owned;const auto result=evaluate_clean_view_admission(facts);
 auto diagnosed=result;diagnosed.frame=frame_check;
 if(!facts.frame_context_current)diagnosed.reason=frame_check.reason;
 // The preference survives lifecycle and context loss; the existing Clean
 // View admission still fails closed until every paused-Freecam fact is fresh.
 f.clean_view_requested=global_hud_request_;
 f.pause_known=facts.pause_known;f.pause_enabled=facts.paused;
 f.clean_view_reason=result.admitted?"admitted_paused_freecam":diagnosed.reason;
 return diagnosed;
}
void GameFov::disarm_clean_view(const char* reason) noexcept {
  if(!flight_)return;flight_->disarm_clean_view(reason);
}
std::string GameFov::camera_json() const {
 std::ostringstream o;o<<"{\"configured\":"<<(free_camera_configured()?"true":"false")<<",\"active\":"<<(free_camera_active()?"true":"false")<<",\"scheduler_depth\":"<<scheduler_depth_<<",\"scope_restored\":"<<(frame_.status.restored?"true":"false");
 if(flight_){const auto& f=*flight_;const auto& cv=f.clean_view_frame;o<<",\"clean_view\":{\"pilot\":"<<(f.config.clean_view_pilot?"true":"false")<<",\"user_requested\":"<<(f.clean_view_requested?"true":"false")<<",\"toggle_key_vk\":"<<f.config.clean_view_toggle<<",\"toggle_edge_detected\":"<<(f.clean_view_toggle_edge?"true":"false")<<",\"initial_armed\":"<<(f.clean_view_initial_armed?"true":"false")<<",\"pause_known\":"<<(f.pause_known?"true":"false")<<",\"pause_enabled\":"<<(f.pause_enabled?"true":"false")<<",\"context_snapshot_valid\":"<<(cv.valid?"true":"false")<<",\"context_snapshot_completed\":"<<(cv.completed?"true":"false")<<",\"trace_frame\":"<<cv.trace_frame<<",\"scheduler_generation\":"<<cv.scheduler_generation<<",\"request_disarm_count\":"<<f.clean_view_disarm_count<<",\"last_disarm_reason\":"<<quote(f.clean_view_last_disarm_reason)<<",\"reason\":"<<quote(f.clean_view_reason)<<"}";}
  if(flight_){auto& f=*flight_;auto& c=f.controller;const auto& clock=f.input.clock();const auto& timing=clock.stats();const char* clock_source=clock.source()==FlightClockSource::qpc?"qpc":clock.source()==FlightClockSource::tick_count64?"get_tick_count64":"unavailable";const char* fov_source=c.active&&f.config.cinematic_fov_enabled?"cinematic_freecam":fov_enabled_?"gameplay_fov":"stock";o<<",\"reason\":"<<quote(f.reason)<<",\"certificate_valid\":"<<(f.certificate.valid?"true":"false")<<",\"single_human_car_race\":"<<(f.certificate.single_human_car_race?"true":"false")<<",\"certificate_reason\":"<<quote(f.certificate.reason)<<",\"race_generation\":"<<f.certificate.race_generation<<",\"owner_lifetime\":"<<f.certificate.owner_lifetime<<",\"camera\":"<<f.certificate.camera<<",\"road_target_preview\":"<<physics_probe_road_target_preview_json(c.pose[12],c.pose[13],c.pose[14],c.active,f.certificate.race_generation,f.certificate.owner_lifetime)<<",\"road_teleport\":"<<physics_probe_road_teleport_status_json()<<",\"vehicle_teleport_enabled\":"<<(f.config.vehicle_teleport_enabled?"true":"false")<<",\"arm_road_teleport_key_vk\":"<<f.config.arm_road_teleport<<",\"toggle_key_vk\":"<<f.config.toggle<<",\"toggle_pressed_while_focused\":"<<((f.input_focused&&f.toggle_pressed_focused)?"true":"false")<<",\"controller_toggle_edge\":"<<(f.toggle_edge?"true":"false")<<",\"clean_view_pilot\":"<<(f.config.clean_view_pilot?"true":"false")<<",\"clean_view_requested\":"<<(f.clean_view_requested?"true":"false")<<",\"clean_view_toggle_key_vk\":"<<f.config.clean_view_toggle<<",\"clean_view_reason\":"<<quote(f.clean_view_reason)<<",\"pause_menu_known\":"<<(f.pause_known?"true":"false")<<",\"pause_menu_enabled\":"<<(f.pause_enabled?"true":"false")<<",\"cinematic_fov_enabled\":"<<(f.config.cinematic_fov_enabled?"true":"false")<<",\"fov_source\":"<<quote(fov_source)<<",\"effective_vertical_fov\":"<<f.effective_vfov<<",\"target_vertical_fov\":"<<c.target_vertical_fov()<<",\"effective_horizontal_fov\":"<<f.effective_hfov<<",\"fov_transition_active\":"<<(c.fov_transition_active()?"true":"false")<<",\"projection_frustum_synchronized\":"<<(f.projection_frustum_synchronized?"true":"false")<<",\"projection_vfov\":"<<f.projection_vfov<<",\"fov_validation_reason\":"<<quote(f.projection_reason)<<",\"manual_roll_enabled\":"<<(f.config.manual_roll_enabled?"true":"false")<<",\"manual_roll_degrees\":"<<c.manual_roll_degrees<<",\"manual_roll_target_degrees\":"<<c.manual_roll_target_degrees<<",\"manual_roll_transition_active\":"<<(c.manual_roll_transition_active?"true":"false")<<",\"roll_speed_degrees_per_second\":"<<f.config.roll_speed<<",\"roll_smooth_seconds\":"<<f.config.roll_smooth_seconds<<",\"configured_base_speed\":"<<f.config.speed<<",\"current_base_speed\":"<<c.current_speed()<<",\"minimum_base_speed\":"<<f.config.min_speed<<",\"maximum_base_speed\":"<<f.config.max_speed<<",\"wheel_speed_factor\":"<<f.config.wheel_speed_factor<<",\"movement_smoothing_seconds\":"<<f.config.movement_smooth_seconds<<",\"current_velocity_magnitude\":"<<c.velocity_magnitude()<<",\"speed_input_source\":"<<quote(c.speed_input_source())<<",\"speed_adjustment_count\":"<<c.speed_adjustment_count()<<",\"flight_clock_source\":"<<quote(clock_source)<<",\"flight_clock_frequency_hz\":"<<clock.frequency()<<",\"flight_dt_last_ms\":"<<timing.last_seconds*1000<<",\"flight_dt_min_ms\":"<<timing.min_seconds*1000<<",\"flight_dt_max_ms\":"<<timing.max_seconds*1000<<",\"flight_dt_mean_ms\":"<<timing.mean_seconds*1000<<",\"flight_dt_zero_samples\":"<<timing.zero_samples<<",\"flight_dt_clamped_samples\":"<<timing.clamped_samples<<",\"flight_clock_invalid_samples\":"<<timing.invalid_samples<<",\"wheel_input_available\":"<<(f.input.wheel_input_available()?"true":"false")<<",\"wheel_input_status\":"<<quote(f.input.wheel_input_available()?"game_hwnd_subclass_delta_forwarded":"unavailable_without_game_hwnd")<<",\"cursor_capture_active\":"<<(f.input.cursor_capture_active()?"true":"false")<<",\"cursor_policy\":"<<quote(f.input.cursor_capture_active()?"focused_freecam_suppress_client_setcursor":"native_window_policy")<<",\"look_smoothing_seconds\":0,\"look_smoothing_status\":\"deferred_to_preserve_mouse_precision\",\"horizon_mode\":"<<quote(f.config.auto_level_horizon?"auto_level":"native_roll")<<",\"horizon_leveling_active\":"<<(c.horizon_leveling_active?"true":"false")<<",\"current_roll_degrees\":"<<c.current_roll_degrees<<",\"target_roll_degrees\":"<<c.target_roll_degrees<<",\"horizon_level_progress\":"<<c.horizon_level_progress<<",\"orientation_valid\":"<<(c.orientation_valid?"true":"false")<<",\"scopes\":"<<f.scopes<<",\"restores\":"<<f.restores<<",\"failures\":"<<f.failures;}
 if(flight_){const auto& f=*flight_;o<<",\"camera_bookmarks\":{\"enabled\":"<<(f.config.camera_bookmarks_enabled?"true":"false")<<",\"slot_count\":"<<CAMERA_BOOKMARK_SLOT_COUNT<<",\"current_slot\":"<<f.bookmark_current_slot<<",\"slot_present\":[";
  for(size_t i=0;i<CAMERA_BOOKMARK_SLOT_COUNT;++i){if(i)o<<',';o<<(f.bookmarks.slots[i].present?"true":"false");}
  o<<"],\"course_id\":"<<(f.certificate.valid?quote(std::string(CAMERA_BOOKMARK_COURSE_ID)):"null")<<",\"storage_status\":"<<quote(camera_bookmark_io_name(f.bookmark_storage))<<",\"last_action\":"<<quote(f.bookmark_last_action)<<",\"last_result\":"<<quote(f.bookmark_last_result)<<",\"action_count\":"<<f.bookmark_action_count<<",\"save_count\":"<<f.bookmark_save_count<<",\"load_count\":"<<f.bookmark_load_count<<",\"rejected_count\":"<<f.bookmark_reject_count<<",\"last_pose\":";
  if(!f.bookmark_last_pose_valid)o<<"null";else {const auto& p=f.bookmark_last_pose;o<<"{\"world_position\":["<<p.visible_pose[12]<<','<<p.visible_pose[13]<<','<<p.visible_pose[14]<<"],\"visible_pose\":[";for(size_t i=0;i<16;++i){if(i)o<<',';o<<std::setprecision(9)<<p.visible_pose[i];}o<<"],\"orientation\":[";for(size_t i=0;i<16;++i){if(i)o<<',';o<<std::setprecision(9)<<p.orientation[i];}o<<"],\"manual_roll_degrees\":"<<p.manual_roll<<",\"manual_roll_target_degrees\":"<<p.manual_roll_target<<",\"current_vfov\":"<<p.current_vfov<<",\"target_vfov\":"<<p.target_vfov<<",\"horizon_level_progress\":"<<p.horizon_level_progress<<"}";}
  o<<'}';}
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
