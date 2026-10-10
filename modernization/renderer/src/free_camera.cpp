#include "free_camera.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <cctype>
#include <cstdlib>
namespace gfx2 {
unsigned free_camera_key(const std::string& input) noexcept {
 std::string s=input;for(auto& c:s)c=static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
 if(s.size()==1&&((s[0]>='A'&&s[0]<='Z')||(s[0]>='0'&&s[0]<='9')))return s[0];
 if(s=="SPACE")return VK_SPACE;if(s=="LEFTCTRL")return VK_LCONTROL;if(s=="LEFTSHIFT")return VK_LSHIFT;if(s=="LEFTALT")return VK_LMENU;
 if(s=="F8")return VK_F8;if(s=="F9")return VK_F9; // F10 and native F1..F7 are excluded.
 if(s=="PAGEUP")return VK_PRIOR;if(s=="PAGEDOWN")return VK_NEXT;
 if(s=="NUMPAD8")return 0x148;if(s=="NUMPAD2")return 0x150;if(s=="NUMPAD4")return 0x14b;if(s=="NUMPAD6")return 0x14d;
 if(s=="NUMPAD9")return 0x149;if(s=="NUMPAD3")return 0x151;return 0;
}
FreeCameraConfig parse_free_camera_config(const std::map<std::string,std::string>& f){
 FreeCameraConfig c;auto get=[&](const char* k,const char* d){auto i=f.find(k);return i==f.end()?std::string(d):i->second;};
 auto number=[&](const char* k,float& out,float lo,float hi){auto v=get(k,"");if(v.empty())return true;char* end=nullptr;double n=std::strtod(v.c_str(),&end);if(end!=v.c_str()+v.size()||!std::isfinite(n)||n<lo||n>hi)return false;out=static_cast<float>(n);return true;};
 bool valid=parse_config_boolean(get("FreeCamera.Enabled","0"),c.enabled);
 auto preset=get("FreeCamera.ControlPreset","0");if(preset=="0")c.preset=0;else if(preset=="1")c.preset=1;else if(preset=="2")c.preset=2;else valid=false;
 c.toggle=free_camera_key(get("FreeCamera.ToggleKey","F8"));valid&=c.toggle!=0;
 valid&=number("FreeCamera.MoveSpeed",c.speed,.01f,1000)&&number("FreeCamera.FastMultiplier",c.fast,1,20)&&number("FreeCamera.SlowMultiplier",c.slow,.01f,1)&&number("FreeCamera.MouseSensitivity",c.sensitivity,.001f,5);
 valid&=number("FreeCamera.MinMoveSpeed",c.min_speed,.0001f,1000)&&number("FreeCamera.MaxMoveSpeed",c.max_speed,.0001f,1000)&&number("FreeCamera.WheelSpeedFactor",c.wheel_speed_factor,1.01f,4)&&number("FreeCamera.MovementSmoothSeconds",c.movement_smooth_seconds,0.f,1.f);
 valid&=c.min_speed<=c.max_speed;
 c.speed_increase=free_camera_key(get("FreeCameraKeys.SpeedIncrease","PageUp"));c.speed_decrease=free_camera_key(get("FreeCameraKeys.SpeedDecrease","PageDown"));
 valid&=c.speed_increase!=0&&c.speed_decrease!=0&&c.speed_increase!=c.speed_decrease&&c.speed_increase!=c.toggle&&c.speed_decrease!=c.toggle;
 valid&=parse_config_boolean(get("FreeCamera.AutoLevelHorizon","1"),c.auto_level_horizon);
 valid&=number("FreeCamera.HorizonLevelSeconds",c.horizon_level_seconds,0.f,5.f);
 if(c.preset==1)c.keys={0x148,0x150,0x14b,0x14d,0x149,0x151,VK_LSHIFT,VK_LMENU};
 if(c.preset==2){const char* names[]={"Forward","Backward","Left","Right","Up","Down","Fast","Slow"};for(size_t i=0;i<8;++i){auto key=f.find(std::string("FreeCameraKeys.")+names[i]);if(key==f.end()){valid=false;continue;}c.keys[i]=free_camera_key(key->second);valid&=c.keys[i]!=0;}}
 for(size_t i=0;i<8;++i){valid&=c.keys[i]!=c.toggle&&c.keys[i]!=c.speed_increase&&c.keys[i]!=c.speed_decrease;for(size_t j=0;j<i;++j)valid&=c.keys[i]!=c.keys[j];}
 if(!valid){c.enabled=false;c.reason="invalid_free_camera_configuration";}else c.reason=c.enabled?"configured_exact_retail_only":"disabled";return c;
}
namespace {
constexpr double PI=3.14159265358979323846;
bool rigid(const std::array<float,16>& p){for(float f:p)if(!std::isfinite(f))return false;if(p[3]||p[7]||p[11]||p[15]!=1)return false;
 for(unsigned i=0;i<3;++i){double length=0;for(unsigned j=0;j<3;++j)length+=double(p[i*4+j])*p[i*4+j];if(std::abs(length-1)>.002)return false;
  for(unsigned k=0;k<i;++k){double dot=0;for(unsigned j=0;j<3;++j)dot+=double(p[i*4+j])*p[k*4+j];if(std::abs(dot)>.002)return false;}}
 double det=p[0]*(p[5]*p[10]-p[6]*p[9])-p[1]*(p[4]*p[10]-p[6]*p[8])+p[2]*(p[4]*p[9]-p[5]*p[8]);return det>.998&&det<1.002;
}
void rotate(float* v,const float* axis,double angle){double c=std::cos(angle),s=std::sin(angle),dot=0;float old[3]={v[0],v[1],v[2]};for(unsigned j=0;j<3;++j)dot+=old[j]*axis[j];
 for(unsigned j=0;j<3;++j)v[j]=static_cast<float>(old[j]*c+(axis[(j+1)%3]*old[(j+2)%3]-axis[(j+2)%3]*old[(j+1)%3])*s+axis[j]*dot*(1-c));}
bool normalize3(float* v){double n=std::sqrt(double(v[0])*v[0]+double(v[1])*v[1]+double(v[2])*v[2]);if(!std::isfinite(n)||n<1e-8)return false;for(unsigned j=0;j<3;++j)v[j]=static_cast<float>(v[j]/n);return true;}
void cross3(const float* a,const float* b,float* out){out[0]=a[1]*b[2]-a[2]*b[1];out[1]=a[2]*b[0]-a[0]*b[2];out[2]=a[0]*b[1]-a[1]*b[0];}
double dot3(const float* a,const float* b){return double(a[0])*b[0]+double(a[1])*b[1]+double(a[2])*b[2];}
bool projected_heading(const float* candidate,const float* back,float* out){double along=dot3(candidate,back);for(unsigned j=0;j<3;++j)out[j]=static_cast<float>(candidate[j]-along*back[j]);return normalize3(out);}
bool horizon_target(const std::array<float,16>& p,const std::array<float,3>& previous,float* target){
 const float world_up[3]={0,1,0};cross3(world_up,p.data()+8,target);
 // Near vertical, retain heading by projecting the last valid horizontal right
 // into the plane perpendicular to Back. Fall back to this pose's Right.
 double horizontal=dot3(target,target);
 if((!std::isfinite(horizontal)||horizontal<.0025||!normalize3(target))&&!projected_heading(previous.data(),p.data()+8,target)&&
    !projected_heading(p.data(),p.data()+8,target))return false;
 return true;
}
double signed_roll(const float* right,const float* target,const float* back){float cross[3];cross3(right,target,cross);return std::atan2(dot3(cross,back),dot3(right,target));}
double clamp_speed(double value,const FreeCameraConfig& c){return std::clamp(value,double(c.min_speed),double(c.max_speed));}
void add_speed_steps(double& speed,int steps,double factor,const FreeCameraConfig& c){int bounded=std::clamp(steps,-12,12);for(int i=0;i<std::abs(bounded);++i)speed=clamp_speed(speed*(bounded>0?factor:1.0/factor),c);}
void add_speed_count(uint64_t& count,unsigned amount){count=amount>UINT64_MAX-count?UINT64_MAX:count+amount;}
void orthogonalize(std::array<float,16>& p){auto norm=[](float* v){double n=std::sqrt(double(v[0])*v[0]+double(v[1])*v[1]+double(v[2])*v[2]);for(unsigned j=0;j<3;++j)v[j]=static_cast<float>(v[j]/n);};norm(p.data()+8);
 double dot=0;for(unsigned j=0;j<3;++j)dot+=p[j]*p[8+j];for(unsigned j=0;j<3;++j)p[j]-=static_cast<float>(dot*p[8+j]);norm(p.data());
 for(unsigned j=0;j<3;++j)p[4+j]=p[8+(j+1)%3]*p[(j+2)%3]-p[8+(j+2)%3]*p[(j+1)%3];norm(p.data()+4);}
}
bool pose_from_native_view(const D3DMATRIX& v,std::array<float,16>& p) noexcept {
 // Native VIEW uses columns Right, Up, -Back; invert its rigid affine translation.
 p={v._11,v._21,v._31,0,v._12,v._22,v._32,0,-v._13,-v._23,-v._33,0,0,0,0,1};
 for(unsigned j=0;j<3;++j)p[12+j]=-v._41*p[j]-v._42*p[4+j]+v._43*p[8+j];return rigid(p);
}
void FlightController::reset_for_race(const FreeCameraConfig& c) noexcept {
 cancel();
 runtime_speed_=clamp_speed(c.speed,c);speed_initialized_=true;speed_adjustment_count_=0;speed_input_source_="configured_initial";
 velocity_={};speed_up_down_=speed_down_down_=false;wheel_remainder_=0;
}
double FlightController::velocity_magnitude() const noexcept {return std::sqrt(velocity_[0]*velocity_[0]+velocity_[1]*velocity_[1]+velocity_[2]*velocity_[2]);}
bool FlightController::update(const FreeCameraConfig& c,const FlightInput& in,bool certified,const std::array<float,16>* visible) noexcept {
 last_toggle_edge=false;
 if(!c.enabled||!certified||!in.focused){cancel();toggle_down_=in.toggle;return false;}
 if(!speed_initialized_){runtime_speed_=clamp_speed(c.speed,c);speed_initialized_=true;}
 if(!std::isfinite(runtime_speed_)){reset_for_race(c);}
 if(!focused_){focused_=true;toggle_down_=in.toggle;return false;}
 bool edge=in.toggle&&!toggle_down_;toggle_down_=in.toggle;
 bool activated=false;
 if(edge){last_toggle_edge=true;if(active){active=false;velocity_={};speed_up_down_=speed_down_down_=false;wheel_remainder_=0;horizon_elapsed_=previous_horizon_progress_=0;horizon_level_progress=0;current_roll_degrees=target_roll_degrees=0;horizon_leveling_active=false;}
  else if(visible&&rigid(*visible)){pose=*visible;active=true;activated=true;velocity_={};speed_up_down_=speed_down_down_=false;wheel_remainder_=0;orientation_valid=true;horizon_elapsed_=previous_horizon_progress_=0;horizon_level_progress=0;horizon_leveling_active=false;std::copy_n(pose.data(),3,horizon_right_.data());}}
 if(!active)return false;
 auto before=pose;
 // Activation is an exact visible-pose handoff. Begin look and horizon work
 // on the next sample so even an unusual first mouse packet cannot snap it.
 if(!activated&&std::isfinite(in.mouse_x)&&std::isfinite(in.mouse_y)){
  const float y[3]={0,1,0};double yaw=-std::clamp(double(in.mouse_x),-1000.,1000.)*c.sensitivity*PI/180;
  for(unsigned i=0;i<3;++i)rotate(pose.data()+i*4,y,yaw);
  double pitch=std::asin(std::clamp(-double(pose[9]),-1.,1.)),delta=-std::clamp(double(in.mouse_y),-1000.,1000.)*c.sensitivity*PI/180;
  delta=std::clamp(pitch+delta,-89*PI/180,89*PI/180)-pitch;
  float right[3]={pose[0],pose[1],pose[2]};rotate(pose.data()+4,right,delta);rotate(pose.data()+8,right,delta);
  if(yaw||delta)orthogonalize(pose);
 }
 orientation_valid=true;current_roll_degrees=target_roll_degrees=0;
 if(!c.auto_level_horizon){float target[3]{},back[3]={pose[8],pose[9],pose[10]};if(horizon_target(pose,horizon_right_,target))current_roll_degrees=static_cast<float>(signed_roll(pose.data(),target,back)*180/PI);}
 if(c.auto_level_horizon){
  float target[3]{};
  if(!horizon_target(pose,horizon_right_,target)){orientation_valid=false;pose=before;velocity_={};return active;}
  float back[3]={pose[8],pose[9],pose[10]};double roll=signed_roll(pose.data(),target,back);
  if(!std::isfinite(roll)){orientation_valid=false;pose=before;velocity_={};return active;}
  current_roll_degrees=static_cast<float>(roll*180/PI);target_roll_degrees=0;
  double dt=std::isfinite(in.seconds)?std::clamp(in.seconds,0.,.05):0.;
  if(!activated){horizon_elapsed_+=dt;}
  double progress=c.horizon_level_seconds<=0?(horizon_elapsed_>0?1.:0.):std::clamp(horizon_elapsed_/c.horizon_level_seconds,0.,1.);
  // Smoothstep gives a gentle start and exact completion at the configured
  // duration. Convert its cumulative progress to a per-frame fraction so the
  // correction remains frame-rate independent and follows a moving target.
  double smooth=progress*progress*(3-2*progress);
  double fraction=smooth>=1?1:(smooth>previous_horizon_progress_?(smooth-previous_horizon_progress_)/(1-previous_horizon_progress_):0);
  if(!activated&&fraction>0){rotate(pose.data(),back,roll*fraction);rotate(pose.data()+4,back,roll*fraction);orthogonalize(pose);}
  previous_horizon_progress_=smooth;horizon_level_progress=static_cast<float>(smooth);
  back[0]=pose[8];back[1]=pose[9];back[2]=pose[10];current_roll_degrees=static_cast<float>(signed_roll(pose.data(),target,back)*180/PI);
  horizon_leveling_active=std::abs(current_roll_degrees)>.05f&&smooth<1;
  // Record the target heading only when world-up yields a well-conditioned
  // horizontal direction; near vertical, keep the last usable heading.
  float world_up[3]={0,1,0},fresh[3];cross3(world_up,pose.data()+8,fresh);
  if(dot3(fresh,fresh)>=.0025&&normalize3(fresh))std::copy_n(fresh,3,horizon_right_.data());
 }else{horizon_leveling_active=false;horizon_level_progress=0;horizon_elapsed_=previous_horizon_progress_=0;}
 bool speed_up=in.speed_increase,speed_down=in.speed_decrease;
 bool speed_up_edge=speed_up&&!speed_up_down_,speed_down_edge=speed_down&&!speed_down_down_;
 speed_up_down_=speed_up;speed_down_down_=speed_down;
 if(speed_up_edge!=speed_down_edge){int step=speed_up_edge?1:-1;add_speed_steps(runtime_speed_,step,c.wheel_speed_factor,c);add_speed_count(speed_adjustment_count_,1);speed_input_source_="keyboard";}
 int wheel=std::clamp(in.wheel_delta,-1440,1440);int total=wheel_remainder_+wheel;int notches=total/WHEEL_DELTA;wheel_remainder_=total-notches*WHEEL_DELTA;
 if(notches){add_speed_steps(runtime_speed_,notches,c.wheel_speed_factor,c);add_speed_count(speed_adjustment_count_,static_cast<unsigned>(std::abs(std::clamp(notches,-12,12))));speed_input_source_="mouse_wheel";}
 double right=int(in.keys[3])-int(in.keys[2]),forward=int(in.keys[0])-int(in.keys[1]),up=int(in.keys[4])-int(in.keys[5]);double direction[3],length=0;
 for(unsigned j=0;j<3;++j){direction[j]=right*pose[j]-forward*pose[8+j]+(j==1?up:0);length+=direction[j]*direction[j];}
 double dt=std::isfinite(in.seconds)?std::clamp(in.seconds,0.,.05):0.;
 double speed=runtime_speed_*(in.keys[6]?c.fast:1)*(in.keys[7]?c.slow:1);
 if(length>0){double inv=1/std::sqrt(length);for(unsigned j=0;j<3;++j)direction[j]*=inv;}
 for(unsigned j=0;j<3;++j)direction[j]*=length>0?speed:0;
 double displacement[3]{};
 if(c.movement_smooth_seconds<=0){for(unsigned j=0;j<3;++j){velocity_[j]=direction[j];displacement[j]=velocity_[j]*dt;}}
 else if(dt>0){double alpha=-std::expm1(-dt/c.movement_smooth_seconds);for(unsigned j=0;j<3;++j){double prior=velocity_[j];velocity_[j]=prior+(direction[j]-prior)*alpha;displacement[j]=direction[j]*dt+(prior-direction[j])*c.movement_smooth_seconds*alpha;}}
 double velocity_sq=velocity_[0]*velocity_[0]+velocity_[1]*velocity_[1]+velocity_[2]*velocity_[2];
 if(length==0&&velocity_sq<.0001){velocity_={};velocity_sq=0;}
 for(unsigned j=0;j<3;++j)pose[12+j]+=static_cast<float>(displacement[j]);
 if(!rigid(pose)){pose=before;active=false;velocity_={};}return active;
}
FlightWindowInput* FlightWindowInput::current_=nullptr;
bool FlightWindowInput::attach(HWND w) noexcept {
 if(window_||current_||!w||GetWindowThreadProcessId(w,nullptr)!=GetCurrentThreadId())return false;
 window_=w;thread_=GetCurrentThreadId();original_=reinterpret_cast<WNDPROC>(GetWindowLongPtrW(w,GWLP_WNDPROC));if(!original_){window_=nullptr;return false;}
 current_=this;SetLastError(0);auto old=SetWindowLongPtrW(w,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(&procedure));
 if(!old&&GetLastError()){current_=nullptr;window_=nullptr;original_=nullptr;return false;}
 LARGE_INTEGER frequency{};BOOL frequency_ok=QueryPerformanceFrequency(&frequency);
 clock_.initialize_qpc(frequency_ok!=FALSE,frequency.QuadPart);
 return intact();
}
bool FlightWindowInput::intact() const noexcept {return window_&&GetCurrentThreadId()==thread_&&IsWindow(window_)&&reinterpret_cast<WNDPROC>(GetWindowLongPtrW(window_,GWLP_WNDPROC))==&procedure;}
void FlightWindowInput::release() noexcept {
 if(window_&&intact())SetWindowLongPtrW(window_,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(original_));
 // A newer subclass may retain our callback: module is pinned, and passthrough remains valid.
 if(!window_||!IsWindow(window_)||reinterpret_cast<WNDPROC>(GetWindowLongPtrW(window_,GWLP_WNDPROC))==original_){if(current_==this)current_=nullptr;window_=nullptr;original_=nullptr;}
 focus_lost();
}
void FlightWindowInput::key_event(unsigned scan,bool extended,bool down) noexcept {if(!extended&&scan<keypad_.size())keypad_[scan]=down;}
void FlightWindowInput::focus_lost() noexcept {keypad_.fill(false);mouse_ready_=false;clock_.reset_baseline();pending_wheel_delta_.store(0,std::memory_order_release);cursor_capture_active_.store(false,std::memory_order_release);}
void FlightWindowInput::set_cursor_capture(bool active) noexcept {
 bool allowed=active&&intact()&&!IsIconic(window_); // Caller admits only a focused controller sample; focus-loss messages clear synchronously.
 cursor_capture_active_.store(allowed,std::memory_order_release);
 if(!allowed)pending_wheel_delta_.store(0,std::memory_order_release);
}
namespace { void accumulate_wheel(std::atomic<int>& pending,int delta) noexcept {
 constexpr int limit=120*12;int old=pending.load(std::memory_order_relaxed);
 for(;;){int next=std::clamp(old+delta,-limit,limit);if(pending.compare_exchange_weak(old,next,std::memory_order_acq_rel,std::memory_order_relaxed))break;}
}}
LRESULT CALLBACK FlightWindowInput::procedure(HWND w,UINT msg,WPARAM wp,LPARAM lp){auto* p=current_;if(!p||w!=p->window_)return DefWindowProcW(w,msg,wp,lp);
 if(msg==WM_KILLFOCUS||(msg==WM_ACTIVATEAPP&&!wp))p->focus_lost();
 if(msg==WM_KEYDOWN||msg==WM_SYSKEYDOWN||msg==WM_KEYUP||msg==WM_SYSKEYUP)p->key_event((static_cast<uintptr_t>(lp)>>16)&255,(static_cast<uintptr_t>(lp)&(1u<<24))!=0,msg==WM_KEYDOWN||msg==WM_SYSKEYDOWN);
 if(msg==WM_SETCURSOR&&p->cursor_capture_active()&&LOWORD(lp)==HTCLIENT)return TRUE; // Keep native cursor handlers from undoing the Present-owned hide.
 if(msg==WM_MOUSEWHEEL&&p->cursor_capture_active())accumulate_wheel(p->pending_wheel_delta_,static_cast<short>(HIWORD(wp)));
 auto original=p->original_;return CallWindowProcW(original,w,msg,wp,lp); // All native vehicle/menu input is preserved.
}
FlightInput FlightWindowInput::sample(const FreeCameraConfig& c,bool mouse) noexcept {
 FlightInput in;in.focused=intact()&&GetForegroundWindow()==window_&&!IsIconic(window_);if(!in.focused){focus_lost();return in;}
 auto key=[&](unsigned k){return k>=0x100?k<0x180&&keypad_[k-0x100]:(GetAsyncKeyState(static_cast<int>(k))&0x8000)!=0;};
 in.toggle=key(c.toggle);in.speed_increase=key(c.speed_increase);in.speed_decrease=key(c.speed_decrease);for(size_t i=0;i<in.keys.size();++i)in.keys[i]=key(c.keys[i]);if(mouse)in.wheel_delta=take_wheel_delta();
 if(clock_.source()==FlightClockSource::qpc){LARGE_INTEGER counter{};BOOL ok=QueryPerformanceCounter(&counter);in.seconds=clock_.sample_qpc(ok!=FALSE,counter.QuadPart);if(!ok)clock_.establish_tick_count64_baseline(GetTickCount64());}
 else if(clock_.source()==FlightClockSource::tick_count64)in.seconds=clock_.sample_tick_count64(GetTickCount64());
 else in.seconds=0; // Missing attach-time clock setup stays fail-closed.
 if(mouse){RECT client{};POINT pos{},center{};if(GetClientRect(window_,&client)&&client.right>0&&client.bottom>0&&GetCursorPos(&pos)){
   center={client.right/2,client.bottom/2};if(ClientToScreen(window_,&center)){
    if(mouse_ready_&&center.x==center_.x&&center.y==center_.y){in.mouse_x=static_cast<float>(pos.x-center.x);in.mouse_y=static_cast<float>(pos.y-center.y);}
    mouse_ready_=SetCursorPos(center.x,center.y)!=FALSE;center_=center;
   }}else mouse_ready_=false;
 }else mouse_ready_=false;return in;
}
}
