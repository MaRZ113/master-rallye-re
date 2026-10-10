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
 if(c.preset==1)c.keys={0x148,0x150,0x14b,0x14d,0x149,0x151,VK_LSHIFT,VK_LMENU};
 if(c.preset==2){const char* names[]={"Forward","Backward","Left","Right","Up","Down","Fast","Slow"};for(size_t i=0;i<8;++i){auto key=f.find(std::string("FreeCameraKeys.")+names[i]);if(key==f.end()){valid=false;continue;}c.keys[i]=free_camera_key(key->second);valid&=c.keys[i]!=0;}}
 for(size_t i=0;i<8;++i){valid&=c.keys[i]!=c.toggle;for(size_t j=0;j<i;++j)valid&=c.keys[i]!=c.keys[j];}
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
void orthogonalize(std::array<float,16>& p){auto norm=[](float* v){double n=std::sqrt(double(v[0])*v[0]+double(v[1])*v[1]+double(v[2])*v[2]);for(unsigned j=0;j<3;++j)v[j]=static_cast<float>(v[j]/n);};norm(p.data()+8);
 double dot=0;for(unsigned j=0;j<3;++j)dot+=p[j]*p[8+j];for(unsigned j=0;j<3;++j)p[j]-=static_cast<float>(dot*p[8+j]);norm(p.data());
 for(unsigned j=0;j<3;++j)p[4+j]=p[8+(j+1)%3]*p[(j+2)%3]-p[8+(j+2)%3]*p[(j+1)%3];norm(p.data()+4);}
}
bool pose_from_native_view(const D3DMATRIX& v,std::array<float,16>& p) noexcept {
 // Native VIEW uses columns Right, Up, -Back; invert its rigid affine translation.
 p={v._11,v._21,v._31,0,v._12,v._22,v._32,0,-v._13,-v._23,-v._33,0,0,0,0,1};
 for(unsigned j=0;j<3;++j)p[12+j]=-v._41*p[j]-v._42*p[4+j]+v._43*p[8+j];return rigid(p);
}
bool FlightController::update(const FreeCameraConfig& c,const FlightInput& in,bool certified,const std::array<float,16>* visible) noexcept {
 if(!c.enabled||!certified||!in.focused){active=false;toggle_down_=in.toggle;focused_=false;return false;}
 if(!focused_){focused_=true;toggle_down_=in.toggle;return false;}
 bool edge=in.toggle&&!toggle_down_;toggle_down_=in.toggle;
 if(edge){if(active)active=false;else if(visible&&rigid(*visible)){pose=*visible;active=true;}}
 if(!active)return false;
 auto before=pose;
 if(std::isfinite(in.mouse_x)&&std::isfinite(in.mouse_y)){
  const float y[3]={0,1,0};double yaw=-std::clamp(double(in.mouse_x),-1000.,1000.)*c.sensitivity*PI/180;
  for(unsigned i=0;i<3;++i)rotate(pose.data()+i*4,y,yaw);
  double pitch=std::asin(std::clamp(-double(pose[9]),-1.,1.)),delta=-std::clamp(double(in.mouse_y),-1000.,1000.)*c.sensitivity*PI/180;
  delta=std::clamp(pitch+delta,-89*PI/180,89*PI/180)-pitch;
  float right[3]={pose[0],pose[1],pose[2]};rotate(pose.data()+4,right,delta);rotate(pose.data()+8,right,delta);
  if(yaw||delta)orthogonalize(pose);
 }
 double right=int(in.keys[3])-int(in.keys[2]),forward=int(in.keys[0])-int(in.keys[1]),up=int(in.keys[4])-int(in.keys[5]);double movement[3];double length=0;
 for(unsigned j=0;j<3;++j){movement[j]=right*pose[j]-forward*pose[8+j]+(j==1?up:0);length+=movement[j]*movement[j];}
 double dt=std::isfinite(in.seconds)?std::clamp(in.seconds,0.,.05):0.;double speed=c.speed*(in.keys[6]?c.fast:1)*(in.keys[7]?c.slow:1);
 if(length>0){double scale=dt*speed/std::max(1.,std::sqrt(length));for(unsigned j=0;j<3;++j)pose[12+j]+=static_cast<float>(movement[j]*scale);}
 if(!rigid(pose)){pose=before;active=false;}return active;
}
FlightWindowInput* FlightWindowInput::current_=nullptr;
bool FlightWindowInput::attach(HWND w) noexcept {
 if(window_||current_||!w||GetWindowThreadProcessId(w,nullptr)!=GetCurrentThreadId())return false;
 window_=w;thread_=GetCurrentThreadId();original_=reinterpret_cast<WNDPROC>(GetWindowLongPtrW(w,GWLP_WNDPROC));if(!original_){window_=nullptr;return false;}
 current_=this;SetLastError(0);auto old=SetWindowLongPtrW(w,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(&procedure));
 if(!old&&GetLastError()){current_=nullptr;window_=nullptr;original_=nullptr;return false;}return intact();
}
bool FlightWindowInput::intact() const noexcept {return window_&&GetCurrentThreadId()==thread_&&IsWindow(window_)&&reinterpret_cast<WNDPROC>(GetWindowLongPtrW(window_,GWLP_WNDPROC))==&procedure;}
void FlightWindowInput::release() noexcept {
 if(window_&&intact())SetWindowLongPtrW(window_,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(original_));
 // A newer subclass may retain our callback: module is pinned, and passthrough remains valid.
 if(!window_||!IsWindow(window_)||reinterpret_cast<WNDPROC>(GetWindowLongPtrW(window_,GWLP_WNDPROC))==original_){if(current_==this)current_=nullptr;window_=nullptr;original_=nullptr;}
 focus_lost();
}
void FlightWindowInput::key_event(unsigned scan,bool extended,bool down) noexcept {if(!extended&&scan<keypad_.size())keypad_[scan]=down;}
void FlightWindowInput::focus_lost() noexcept {keypad_.fill(false);mouse_ready_=false;tick_=0;}
LRESULT CALLBACK FlightWindowInput::procedure(HWND w,UINT msg,WPARAM wp,LPARAM lp){auto* p=current_;if(!p||w!=p->window_)return DefWindowProcW(w,msg,wp,lp);
 if(msg==WM_KILLFOCUS||msg==WM_ACTIVATEAPP&&!wp)p->focus_lost();
 if(msg==WM_KEYDOWN||msg==WM_SYSKEYDOWN||msg==WM_KEYUP||msg==WM_SYSKEYUP)p->key_event((static_cast<uintptr_t>(lp)>>16)&255,(static_cast<uintptr_t>(lp)&(1u<<24))!=0,msg==WM_KEYDOWN||msg==WM_SYSKEYDOWN);
 auto original=p->original_;return CallWindowProcW(original,w,msg,wp,lp); // All native vehicle/menu input is preserved.
}
FlightInput FlightWindowInput::sample(const FreeCameraConfig& c,bool mouse) noexcept {
 FlightInput in;in.focused=intact()&&GetForegroundWindow()==window_&&!IsIconic(window_);if(!in.focused){focus_lost();return in;}
 auto key=[&](unsigned k){return k>=0x100?k<0x180&&keypad_[k-0x100]:(GetAsyncKeyState(static_cast<int>(k))&0x8000)!=0;};
 in.toggle=key(c.toggle);for(size_t i=0;i<in.keys.size();++i)in.keys[i]=key(c.keys[i]);auto now=GetTickCount64();in.seconds=tick_?double(now-tick_)/1000:0;tick_=now;
 if(mouse){RECT client{};POINT pos{},center{};if(GetClientRect(window_,&client)&&client.right>0&&client.bottom>0&&GetCursorPos(&pos)){
   center={client.right/2,client.bottom/2};if(ClientToScreen(window_,&center)){
    if(mouse_ready_&&center.x==center_.x&&center.y==center_.y){in.mouse_x=static_cast<float>(pos.x-center.x);in.mouse_y=static_cast<float>(pos.y-center.y);}
    mouse_ready_=SetCursorPos(center.x,center.y)!=FALSE;center_=center;
   }}else mouse_ready_=false;
 }else mouse_ready_=false;return in;
}
}
