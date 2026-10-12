#pragma once
#include "game_fov.hpp"
#include "flight_clock.hpp"
#include <atomic>
namespace gfx2 {
struct FreeCameraConfig {
 bool enabled=false,allow_unpaused=false;unsigned preset=0;unsigned toggle=VK_F8;
 float speed=40,fast=6,slow=.2f,sensitivity=.12f;
 float min_speed=.25f,max_speed=300.f,wheel_speed_factor=1.25f,movement_smooth_seconds=.12f;
 unsigned speed_increase=VK_PRIOR,speed_decrease=VK_NEXT;
 bool cinematic_fov_enabled=true,inherit_stock_fov_on_toggle=true;float cinematic_vfov=0,min_vfov=35,max_vfov=100,fov_step=5,fov_smooth_seconds=.25f;
 const char* cinematic_fov_reason="configured";
 unsigned fov_decrease='Z',fov_increase='X';
 bool auto_level_horizon=true;float horizon_level_seconds=.30f;
 bool manual_roll_enabled=true;float roll_speed=45.f,roll_smooth_seconds=.10f,max_roll_degrees=90.f;
 unsigned roll_left='C',roll_right='V',roll_reset='B';
 bool camera_bookmarks_enabled=true;unsigned camera_bookmark_default_slot=1;
 unsigned save_camera_bookmark='J',load_camera_bookmark='K',next_camera_bookmark_slot='L';
 bool vehicle_teleport_enabled=false,vehicle_teleport_road_only=true;
 uint32_t vehicle_teleport_arm_timeout_seconds=60;float vehicle_teleport_max_road_distance=20.f;
 unsigned arm_road_teleport='T';
 bool clean_view_pilot=false,clean_view_enabled=false;unsigned clean_view_toggle='H';
 const char* clean_view_config_reason="pilot_disabled";
 std::array<unsigned,8> keys{'W','S','A','D','E','Q',VK_LSHIFT,VK_LMENU};
 const char* reason="disabled";
};
// 0x100+scan denotes a physical, non-extended keypad key, independent of NumLock.
unsigned free_camera_key(const std::string&) noexcept;
FreeCameraConfig parse_free_camera_config(const std::map<std::string,std::string>&);
bool pose_from_native_view(const D3DMATRIX&,std::array<float,16>&) noexcept;
struct FlightBookmarkPose {
 std::array<float,16> visible_pose{},orientation{};
 std::array<float,3> horizon_right{};
 double horizon_elapsed=0,previous_horizon_progress=0;
 double manual_roll=0,manual_roll_target=0,current_vfov=0,target_vfov=0;
 float current_roll_degrees=0,target_roll_degrees=0,horizon_level_progress=0;
 bool horizon_leveling_active=false;
 bool auto_level_horizon=true,cinematic_fov_enabled=true;
};
struct FlightInput {bool focused=false,toggle=false,speed_increase=false,speed_decrease=false,fov_decrease=false,fov_increase=false,roll_left=false,roll_right=false,roll_reset=false,clean_view_toggle=false,arm_road_teleport=false;bool save_camera_bookmark=false,load_camera_bookmark=false,next_camera_bookmark_slot=false;std::array<bool,8> keys{};float mouse_x=0,mouse_y=0;double seconds=0,inherited_vfov=0;int wheel_delta=0;};
struct FreeCameraAdmission {bool admitted=false;const char* mode="none";const char* reason="disabled";};
inline FreeCameraAdmission evaluate_free_camera_admission(bool configured,bool allow_unpaused,
 bool live_race_certificate,bool camera_owner_valid,bool pause_known,bool paused,bool input_focus) noexcept {
 if(!configured)return {false,"none","disabled"};
 if(!input_focus)return {false,"none","window_focus_lost"};
 if(!camera_owner_valid)return {false,"none","camera_owner_invalid"};
 if(!live_race_certificate)return {false,"none","missing_race_certificate"};
 if(!pause_known)return {false,"none","native_pause_unknown"};
 if(!paused&&!allow_unpaused)return {false,"paused_only","paused_only_required"};
 return {true,allow_unpaused?"live_allowed":"paused_only",paused?"admitted_paused":"admitted_running"};
}
struct FlightWindowSnapshot {
 uintptr_t attached_hwnd=0,foreground_hwnd=0,keyboard_focus_hwnd=0;
 DWORD hwnd_thread=0,current_thread=0,process_id=0;
 int32_t client_width=0,client_height=0;
 bool wndproc_owned=false,window_valid=false,minimized=false,client_size_valid=false,input_focus_accepted=false;
};
class FlightController {
 bool toggle_down_=false,focused_=false;
 double horizon_elapsed_=0,previous_horizon_progress_=0;
 std::array<float,3> horizon_right_{};
 std::array<double,3> velocity_{};
 bool speed_up_down_=false,speed_down_down_=false,speed_initialized_=false;
 bool fov_down_down_=false,fov_up_down_=false,fov_initialized_=false,fov_transition_active_=false,roll_initialized_=false;
 bool suppress_next_motion_sample_=false,bookmark_horizon_settled_=false;
 double runtime_speed_=40;
 double current_vfov_=0,target_vfov_=0;
 std::array<float,16> orientation_{};double manual_roll_=0,manual_roll_target_=0;
 int wheel_remainder_=0;
 uint64_t speed_adjustment_count_=0;
 const char* speed_input_source_="configured_initial";
public:
 bool active=false,last_toggle_edge=false;std::array<float,16> pose{};
 bool orientation_valid=true,horizon_leveling_active=false,manual_roll_transition_active=false;
 float current_roll_degrees=0,target_roll_degrees=0,horizon_level_progress=0;
 float manual_roll_degrees=0,manual_roll_target_degrees=0;
 bool update(const FreeCameraConfig&,const FlightInput&,bool certified,const std::array<float,16>* visible) noexcept;
 bool capture_bookmark(FlightBookmarkPose&,const FreeCameraConfig&) const noexcept;
 bool restore_bookmark(const FlightBookmarkPose&,const FreeCameraConfig&) noexcept;
 void cancel() noexcept {active=false;toggle_down_=false;focused_=false;horizon_elapsed_=previous_horizon_progress_=0;horizon_level_progress=0;current_roll_degrees=target_roll_degrees=0;manual_roll_degrees=manual_roll_target_degrees=0;manual_roll_transition_active=false;manual_roll_=manual_roll_target_=0;roll_initialized_=false;orientation_={};horizon_leveling_active=false;orientation_valid=true;velocity_={};speed_up_down_=speed_down_down_=false;fov_down_down_=fov_up_down_=fov_initialized_=fov_transition_active_=false;current_vfov_=target_vfov_=0;wheel_remainder_=0;suppress_next_motion_sample_=false;bookmark_horizon_settled_=false;}
 void reset_for_race(const FreeCameraConfig&) noexcept;
 double current_speed() const noexcept {return runtime_speed_;}
 double velocity_magnitude() const noexcept;
 uint64_t speed_adjustment_count() const noexcept {return speed_adjustment_count_;}
 const char* speed_input_source() const noexcept {return speed_input_source_;}
 double current_vertical_fov() const noexcept {return current_vfov_;}
 double target_vertical_fov() const noexcept {return target_vfov_;}
 bool fov_transition_active() const noexcept {return fov_transition_active_;}
};
// Optional game-HWND subclass only; never a global/thread message hook.
class FlightWindowInput {
 HWND window_=nullptr;WNDPROC original_=nullptr;DWORD thread_=0;
 std::array<bool,128> keypad_{};FlightClock clock_{};POINT center_{};bool mouse_ready_=false;
 std::atomic<int> pending_wheel_delta_{0};std::atomic<bool> cursor_capture_active_{false};
 static FlightWindowInput* current_;
 static LRESULT CALLBACK procedure(HWND,UINT,WPARAM,LPARAM);
public:
 bool attach(HWND) noexcept;void release() noexcept;~FlightWindowInput(){release();}
 void key_event(unsigned scan,bool extended,bool down) noexcept;
 void focus_lost() noexcept;
 void set_cursor_capture(bool active) noexcept;
 int take_wheel_delta() noexcept {return pending_wheel_delta_.exchange(0,std::memory_order_acq_rel);}
 void discard_after_bookmark_load() noexcept {mouse_ready_=false;clock_.reset_baseline();pending_wheel_delta_.store(0,std::memory_order_release);}
 bool wheel_input_available() const noexcept {return window_!=nullptr;}
 bool cursor_capture_active() const noexcept {return cursor_capture_active_.load(std::memory_order_relaxed);}
 bool focused_now() const noexcept {return intact()&&GetForegroundWindow()==window_&&!IsIconic(window_);}
 FlightWindowSnapshot snapshot() const noexcept;
 const FlightClock& clock() const noexcept {return clock_;}
 bool physical_down(unsigned scan) const noexcept {return scan<keypad_.size()&&keypad_[scan];}
 FlightInput sample(const FreeCameraConfig&,bool capture_mouse) noexcept;
 bool intact() const noexcept;
};
}
