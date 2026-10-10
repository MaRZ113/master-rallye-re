#pragma once
#include "game_fov.hpp"
#include "flight_clock.hpp"
#include <atomic>
namespace gfx2 {
struct FreeCameraConfig {
 bool enabled=false;unsigned preset=0;unsigned toggle=VK_F8;
 float speed=40,fast=6,slow=.2f,sensitivity=.12f;
 float min_speed=.25f,max_speed=300.f,wheel_speed_factor=1.25f,movement_smooth_seconds=.12f;
 unsigned speed_increase=VK_PRIOR,speed_decrease=VK_NEXT;
 bool auto_level_horizon=true;float horizon_level_seconds=.30f;
 std::array<unsigned,8> keys{'W','S','A','D',VK_SPACE,VK_LCONTROL,VK_LSHIFT,VK_LMENU};
 const char* reason="disabled";
};
// 0x100+scan denotes a physical, non-extended keypad key, independent of NumLock.
unsigned free_camera_key(const std::string&) noexcept;
FreeCameraConfig parse_free_camera_config(const std::map<std::string,std::string>&);
bool pose_from_native_view(const D3DMATRIX&,std::array<float,16>&) noexcept;
struct FlightInput {bool focused=false,toggle=false,speed_increase=false,speed_decrease=false;std::array<bool,8> keys{};float mouse_x=0,mouse_y=0;double seconds=0;int wheel_delta=0;};
class FlightController {
 bool toggle_down_=false,focused_=false;
 double horizon_elapsed_=0,previous_horizon_progress_=0;
 std::array<float,3> horizon_right_{};
 std::array<double,3> velocity_{};
 bool speed_up_down_=false,speed_down_down_=false,speed_initialized_=false;
 double runtime_speed_=40;
 int wheel_remainder_=0;
 uint64_t speed_adjustment_count_=0;
 const char* speed_input_source_="configured_initial";
public:
 bool active=false,last_toggle_edge=false;std::array<float,16> pose{};
 bool orientation_valid=true,horizon_leveling_active=false;
 float current_roll_degrees=0,target_roll_degrees=0,horizon_level_progress=0;
 bool update(const FreeCameraConfig&,const FlightInput&,bool certified,const std::array<float,16>* visible) noexcept;
 void cancel() noexcept {active=false;toggle_down_=false;focused_=false;horizon_elapsed_=previous_horizon_progress_=0;horizon_level_progress=0;current_roll_degrees=target_roll_degrees=0;horizon_leveling_active=false;orientation_valid=true;velocity_={};speed_up_down_=speed_down_down_=false;wheel_remainder_=0;}
 void reset_for_race(const FreeCameraConfig&) noexcept;
 double current_speed() const noexcept {return runtime_speed_;}
 double velocity_magnitude() const noexcept;
 uint64_t speed_adjustment_count() const noexcept {return speed_adjustment_count_;}
 const char* speed_input_source() const noexcept {return speed_input_source_;}
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
 bool wheel_input_available() const noexcept {return window_!=nullptr;}
 bool cursor_capture_active() const noexcept {return cursor_capture_active_.load(std::memory_order_relaxed);}
 const FlightClock& clock() const noexcept {return clock_;}
 bool physical_down(unsigned scan) const noexcept {return scan<keypad_.size()&&keypad_[scan];}
 FlightInput sample(const FreeCameraConfig&,bool capture_mouse) noexcept;
 bool intact() const noexcept;
};
}
