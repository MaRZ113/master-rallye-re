#pragma once
#include "game_fov.hpp"
namespace gfx2 {
struct FreeCameraConfig {
 bool enabled=false;unsigned preset=0;unsigned toggle=VK_F8;
 float speed=40,fast=6,slow=.2f,sensitivity=.12f;
 std::array<unsigned,8> keys{'W','S','A','D',VK_SPACE,VK_LCONTROL,VK_LSHIFT,VK_LMENU};
 const char* reason="disabled";
};
// 0x100+scan denotes a physical, non-extended keypad key, independent of NumLock.
unsigned free_camera_key(const std::string&) noexcept;
FreeCameraConfig parse_free_camera_config(const std::map<std::string,std::string>&);
bool pose_from_native_view(const D3DMATRIX&,std::array<float,16>&) noexcept;
struct FlightInput {bool focused=false,toggle=false;std::array<bool,8> keys{};float mouse_x=0,mouse_y=0;double seconds=0;};
class FlightController {
 bool toggle_down_=false,focused_=false;
public:
 bool active=false;std::array<float,16> pose{};
 bool update(const FreeCameraConfig&,const FlightInput&,bool certified,const std::array<float,16>* visible) noexcept;
 void cancel() noexcept {active=false;toggle_down_=false;focused_=false;}
};
// Optional game-HWND subclass only; never a global/thread message hook.
class FlightWindowInput {
 HWND window_=nullptr;WNDPROC original_=nullptr;DWORD thread_=0;
 std::array<bool,128> keypad_{};uint64_t tick_=0;POINT center_{};bool mouse_ready_=false;
 static FlightWindowInput* current_;
 static LRESULT CALLBACK procedure(HWND,UINT,WPARAM,LPARAM);
public:
 bool attach(HWND) noexcept;void release() noexcept;~FlightWindowInput(){release();}
 void key_event(unsigned scan,bool extended,bool down) noexcept;
 void focus_lost() noexcept;
 bool physical_down(unsigned scan) const noexcept {return scan<keypad_.size()&&keypad_[scan];}
 FlightInput sample(const FreeCameraConfig&,bool capture_mouse) noexcept;
 bool intact() const noexcept;
};
}
