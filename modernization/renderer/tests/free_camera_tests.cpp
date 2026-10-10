#include "free_camera.hpp"
#include "flight_clock.hpp"
#include "race_epoch.hpp"
#include <iostream>
#include <stdexcept>
#include <cmath>
#include <cstring>
#include <vector>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
std::array<float,16> identity(){return {1,0,0,0,0,1,0,0,0,0,1,0,10,20,30,1};}
std::array<float,16> rolled_pose(double yaw,double pitch,double roll){
 // Build a right-handed level basis for the requested look direction, then
 // apply a known roll around Back. Yaw/pitch make the horizon test nontrivial.
 double cy=std::cos(yaw),sy=std::sin(yaw),cp=std::cos(pitch),sp=std::sin(pitch);
 std::array<float,16> p=identity();float back[3]={static_cast<float>(sy*cp),static_cast<float>(sp),static_cast<float>(cy*cp)};
 float right[3]={static_cast<float>(cy),0,static_cast<float>(-sy)};
 float up[3]={back[1]*right[2]-back[2]*right[1],back[2]*right[0]-back[0]*right[2],back[0]*right[1]-back[1]*right[0]};
 for(unsigned j=0;j<3;++j){p[j]=static_cast<float>(right[j]*std::cos(roll)+up[j]*std::sin(roll));p[4+j]=static_cast<float>(up[j]*std::cos(roll)-right[j]*std::sin(roll));p[8+j]=back[j];}
 return p;
}
void activate(FlightController& f,const FreeCameraConfig& c,const std::array<float,16>& p){FlightInput in;in.focused=true;CHECK(!f.update(c,in,true,&p));in.toggle=true;CHECK(f.update(c,in,true,&p)&&f.pose==p);}
void controls(){
 wchar_t directory[MAX_PATH]{},name[MAX_PATH]{};CHECK(GetTempPathW(MAX_PATH,directory)&&GetTempFileNameW(directory,L"mcf",0,name));
 struct TempIni {const wchar_t* path;~TempIni(){DeleteFileW(path);}} cleanup{name};
 const char text[]="[Renderer]\r\nConfigVersion=1\r\n[FreeCamera]\r\nEnabled=1\r\nControlPreset=1\r\nToggleKey=F8\r\nMovementSmoothSeconds=0.12\r\nCinematicFOVEnabled=1\r\nCinematicVerticalFOVDegrees=65\r\nFOVStepDegrees=5\r\n[FreeCameraKeys]\r\nSpeedIncrease=PageUp\r\nSpeedDecrease=PageDown\r\nFOVDecrease=Z\r\nFOVIncrease=X\r\n[Trace]\r\nEnabled=0\r\n";
 HANDLE file=CreateFileW(name,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);CHECK(file!=INVALID_HANDLE_VALUE);DWORD written=0;bool stored=WriteFile(file,text,sizeof(text)-1,&written,nullptr)&&written==sizeof(text)-1;CloseHandle(file);CHECK(stored);
 auto loaded=read_visual_config(name);auto parsed=parse_free_camera_config(loaded.raw_fields);CHECK(loaded.version_ok&&parsed.enabled&&parsed.preset==1&&parsed.speed_increase==VK_PRIOR&&parsed.movement_smooth_seconds==.12f&&parsed.cinematic_fov_enabled&&parsed.cinematic_vfov==65&&parsed.fov_decrease=='Z'&&parsed.fov_increase=='X'); // Actual INI reader, no tracing prerequisite.
 auto invalid=parse_visual_config({{"Renderer.ConfigVersion","2"},{"FreeCamera.Enabled","1"}},true);GameFov rejected;CHECK(!rejected.install(true,invalid,nullptr,true)&&!rejected.free_camera_configured());
 CHECK(!parse_free_camera_config({}).enabled);
 auto c=parse_free_camera_config({{"FreeCamera.Enabled","1"}});CHECK(c.enabled&&c.preset==0&&c.toggle==VK_F8);
 CHECK(c.keys[0]=='W'&&c.keys[1]=='S'&&c.keys[2]=='A'&&c.keys[3]=='D'&&c.keys[4]=='E'&&c.keys[5]=='Q'&&c.keys[4]!=VK_SPACE);
 CHECK(c.speed_increase==VK_PRIOR&&c.speed_decrease==VK_NEXT&&c.min_speed==.25f&&c.max_speed==300.f&&c.movement_smooth_seconds==.12f);
 CHECK(c.auto_level_horizon&&std::abs(c.horizon_level_seconds-.30f)<.0001f);
 CHECK(c.cinematic_fov_enabled&&c.cinematic_vfov==0&&c.min_vfov==35&&c.max_vfov==100&&c.fov_step==5&&c.fov_smooth_seconds==.25f&&c.fov_decrease=='Z'&&c.fov_increase=='X');
 CHECK(c.manual_roll_enabled&&c.roll_speed==45&&c.roll_smooth_seconds==.10f&&c.max_roll_degrees==90&&c.roll_left=='C'&&c.roll_right=='V'&&c.roll_reset=='B');
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.CinematicVerticalFOVDegrees","101"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MinVerticalFOVDegrees","80"},{"FreeCamera.MaxVerticalFOVDegrees","70"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCameraKeys.FOVDecrease","W"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCameraKeys.RollLeft","W"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCameraKeys.RollLeft","C"},{"FreeCameraKeys.RollRight","C"}}).enabled);
 std::map<std::string,std::string> fov_conflict{{"FreeCamera.Enabled","1"},{"FreeCamera.ControlPreset","2"}};const char* conflict_names[]={"Forward","Backward","Left","Right","Up","Down","Fast","Slow"};const char* conflict_keys[]={"Z","Numpad2","Numpad4","Numpad6","Numpad9","Numpad3","LeftShift","LeftAlt"};for(size_t i=0;i<8;++i)fov_conflict[std::string("FreeCameraKeys.")+conflict_names[i]]=conflict_keys[i];CHECK(!parse_free_camera_config(fov_conflict).enabled);
 auto level_off=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","false"},{"FreeCamera.HorizonLevelSeconds","0"}});CHECK(level_off.enabled&&!level_off.auto_level_horizon&&level_off.horizon_level_seconds==0);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","maybe"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.HorizonLevelSeconds","5.01"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.ToggleKey","F10"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MoveSpeed","NaN"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MoveSpeed","40junk"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.WheelSpeedFactor","1"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MinMoveSpeed","3"},{"FreeCamera.MaxMoveSpeed","2"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCameraKeys.SpeedIncrease","PageDown"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCameraKeys.SpeedIncrease","W"}}).enabled);
 auto no_smoothing=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MovementSmoothSeconds","0"}});CHECK(no_smoothing.enabled&&no_smoothing.movement_smooth_seconds==0);
 auto pad=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.ControlPreset","1"}});CHECK(pad.enabled&&pad.keys[0]==0x148&&pad.keys[0]!=VK_UP&&pad.keys[0]!='8');
 std::map<std::string,std::string> custom{{"FreeCamera.Enabled","1"},{"FreeCamera.ControlPreset","2"},{"FreeCamera.ToggleKey","Q"}};
 const char* names[]={"Forward","Backward","Left","Right","Up","Down","Fast","Slow"};const char* keys[]={"Numpad8","Numpad2","Numpad4","Numpad6","Numpad9","Numpad3","LeftShift","LeftAlt"};
 for(size_t i=0;i<8;++i)custom[std::string("FreeCameraKeys.")+names[i]]=keys[i];CHECK(parse_free_camera_config(custom).enabled);custom["FreeCameraKeys.Forward"]="Q";CHECK(!parse_free_camera_config(custom).enabled);
 custom["FreeCameraKeys.Forward"]="W";custom["FreeCameraKeys.Up"]="Space";CHECK(parse_free_camera_config(custom).enabled); // Space remains available to deliberate custom layouts.
 FlightWindowInput input;input.key_event(0x48,true,true);CHECK(!input.physical_down(0x48));input.key_event(0x48,false,true);CHECK(input.physical_down(0x48));input.key_event(0x48,false,false);CHECK(!input.physical_down(0x48));
 input.key_event(0x48,false,true);input.focus_lost();CHECK(!input.physical_down(0x48));CHECK(!input.sample(pad,true).focused);
 FlightController f;FlightInput in;auto visible=identity();in.focused=true;CHECK(!f.update(c,in,true,&visible)&&!f.last_toggle_edge);in.toggle=true;CHECK(f.update(c,in,true,&visible)&&f.pose==visible&&f.last_toggle_edge);
 // Held toggle does not oscillate; exact initial pose, no activation snap/flip.
 CHECK(f.update(c,in,true,&visible)&&!f.last_toggle_edge);in.toggle=false;CHECK(f.update(c,in,true,&visible)&&!f.last_toggle_edge);
 in.keys[0]=in.keys[3]=true;in.seconds=1;auto before=f.pose;CHECK(f.update(no_smoothing,in,true,&visible));double length=0;for(unsigned j=0;j<3;++j)length+=std::pow(f.pose[12+j]-before[12+j],2);CHECK(std::abs(std::sqrt(length)-2)<.00001); // 40m/s, bounded .05sec diagonal.
 in.keys={};in.keys[4]=true;in.seconds=.01;before=f.pose;f.update(no_smoothing,in,true,&visible);CHECK(f.pose[12]==before[12]&&f.pose[14]==before[14]&&f.pose[13]>before[13]);
 in.keys={};in.mouse_x=1000;in.mouse_y=-1000;for(unsigned n=0;n<100;++n)CHECK(f.update(c,in,true,&visible));CHECK(std::isfinite(f.pose[0])&&std::abs(f.pose[9])<1);
 in={};in.focused=false;CHECK(!f.update(c,in,true,&visible)&&!f.active&&!f.last_toggle_edge);in.focused=true;in.toggle=true;CHECK(!f.update(c,in,true,&visible)&&!f.last_toggle_edge); // Held toggle through Alt+Tab requires release.
 in.toggle=false;f.update(c,in,true,&visible);in.toggle=true;CHECK(f.update(c,in,true,&visible));CHECK(!f.update(c,in,false,&visible));
 // Frontend/unknown certificate and malformed visible view never activate.
 f.cancel();in.toggle=false;f.update(c,in,true,&visible);in.toggle=true;CHECK(!f.update(c,in,false,&visible));visible[0]=2;f.cancel();in.toggle=false;f.update(c,in,true,&visible);in.toggle=true;CHECK(!f.update(c,in,true,&visible));
}
void clock_timing(){
 constexpr int64_t hz=10000000;
 FlightClock qpc;qpc.initialize_qpc(true,hz);CHECK(qpc.source()==FlightClockSource::qpc&&qpc.frequency()==hz);
 CHECK(qpc.sample_qpc(true,100000000)==0); // First sample establishes a baseline.
 CHECK(std::abs(qpc.sample_qpc(true,100083330)-.008333)<1e-9);
 double pair_sum=qpc.sample_qpc(true,100250000);CHECK(std::abs(pair_sum-.016667)<1e-9&&std::abs(.008333+pair_sum-.025)<1e-12);
 CHECK(std::abs(qpc.sample_qpc(true,100251234)-.0001234)<1e-9); // Sub-millisecond precision.
 CHECK(qpc.sample_qpc(true,100251234)==0); // A genuine zero interval is harmless and counted.
 CHECK(std::abs(qpc.sample_qpc(true,100751234)-.05)<1e-9);
 CHECK(std::abs(qpc.sample_qpc(true,110751234)-1.)<1e-9); // Raw diagnostic sees the gap; controller still caps at 50 ms.
 const auto& s=qpc.stats();CHECK(s.samples==6&&s.zero_samples==1&&s.clamped_samples==1&&s.invalid_samples==0);
 CHECK(s.min_seconds==0&&std::abs(s.max_seconds-1.)<1e-9);
 CHECK(s.mean_seconds>0&&s.mean_seconds<1.);
 qpc.reset_baseline();CHECK(qpc.sample_qpc(true,900000000)==0); // Focus return starts a fresh QPC interval.
 CHECK(std::abs(qpc.sample_qpc(true,900100000)-.01)<1e-12);

 FlightClock invalid_frequency;invalid_frequency.initialize_qpc(true,0);CHECK(invalid_frequency.source()==FlightClockSource::tick_count64&&invalid_frequency.frequency()==1000&&invalid_frequency.stats().invalid_samples==1);
 CHECK(invalid_frequency.sample_tick_count64(5000)==0);CHECK(std::abs(invalid_frequency.sample_tick_count64(5016)-.016)<1e-12);
 CHECK(invalid_frequency.sample_tick_count64(5015)==0&&invalid_frequency.stats().invalid_samples==2); // Backward time rejected and rebaselined.
 CHECK(std::abs(invalid_frequency.sample_tick_count64(5025)-.01)<1e-12);

 FlightClock failed_query;failed_query.initialize_qpc(true,hz);CHECK(failed_query.sample_qpc(true,500000000)==0);
 CHECK(failed_query.sample_qpc(false,0)==0&&failed_query.source()==FlightClockSource::tick_count64&&failed_query.frequency()==1000&&failed_query.stats().invalid_samples==1);
 failed_query.establish_tick_count64_baseline(100000);CHECK(std::abs(failed_query.sample_tick_count64(100017)-.017)<1e-12); // No subtraction across QPC/tick domains.
 CHECK(failed_query.sample_tick_count64(100017)==0&&failed_query.stats().zero_samples==1);
 failed_query.reset_baseline();CHECK(failed_query.sample_tick_count64(9000000000ull)==0);CHECK(failed_query.sample_tick_count64(9000000008ull)==.008);

 FlightClock failed_frequency_call;failed_frequency_call.initialize_qpc(false,0);CHECK(failed_frequency_call.source()==FlightClockSource::tick_count64&&failed_frequency_call.stats().invalid_samples==1);
 CHECK(failed_frequency_call.sample_tick_count64(0)==0);CHECK(std::abs(failed_frequency_call.sample_tick_count64(1)-.001)<1e-12);
 FlightClock negative;negative.initialize_qpc(true,hz);CHECK(negative.sample_qpc(true,10)==0);CHECK(negative.sample_qpc(true,-1)==0&&negative.stats().invalid_samples==1);CHECK(negative.sample_qpc(true,20)==0);CHECK(std::abs(negative.sample_qpc(true,30)-1e-6)<1e-12);
 FlightClock extreme;extreme.initialize_qpc(true,1);CHECK(extreme.sample_qpc(true,0)==0);double enormous=extreme.sample_qpc(true,INT64_MAX);CHECK(std::isfinite(enormous)&&enormous>9e18&&extreme.stats().clamped_samples==1); // Wide counter deltas stay finite and are left to the controller's 50 ms cap.
}
void movement_and_speed(){
 auto c=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MovementSmoothSeconds","0.12"}});auto p=identity();
 FlightController f;activate(f,c,p);FlightInput in;in.focused=true;in.seconds=.05;CHECK(f.update(c,in,true,&p)); // release F8
 in.keys[0]=true;double z=f.pose[14];CHECK(f.update(c,in,true,&p));double first=f.pose[14]-z;CHECK(first<0&&std::abs(first)<2&&f.velocity_magnitude()>0);
 for(unsigned n=0;n<8;++n)CHECK(f.update(c,in,true,&p));CHECK(f.velocity_magnitude()>39);
 in.keys={};double prior=f.velocity_magnitude();z=f.pose[14];CHECK(f.update(c,in,true,&p));CHECK(f.velocity_magnitude()<prior&&f.velocity_magnitude()>0&&f.pose[14]<z); // Smooth stop coasts briefly.
 for(unsigned n=0;n<200;++n)CHECK(f.update(c,in,true,&p));CHECK(f.velocity_magnitude()==0);
 // A held speed key emits one multiplicative adjustment; a release is required before the next.
 double initial=f.current_speed();in.speed_increase=true;CHECK(f.update(c,in,true,&p));CHECK(std::abs(f.current_speed()-initial*1.25)<.0001);for(unsigned n=0;n<20;++n)CHECK(f.update(c,in,true,&p));CHECK(std::abs(f.current_speed()-initial*1.25)<.0001);
 in.speed_increase=false;CHECK(f.update(c,in,true,&p));in.speed_decrease=true;CHECK(f.update(c,in,true,&p));CHECK(std::abs(f.current_speed()-initial)<.0001);CHECK(f.speed_adjustment_count()==2);
 in.speed_decrease=false;in.wheel_delta=60;CHECK(f.update(c,in,true,&p));CHECK(f.current_speed()==initial);in.wheel_delta=60;CHECK(f.update(c,in,true,&p));CHECK(std::abs(f.current_speed()-initial*1.25)<.0001);
 in.wheel_delta=-240;CHECK(f.update(c,in,true,&p));CHECK(std::abs(f.current_speed()-initial/1.25)<.0001); // Two negative notches.
 in.wheel_delta=0;f.reset_for_race(c);CHECK(f.current_speed()==c.speed&&f.speed_adjustment_count()==0&&!f.active); // Race identity resets configured starting speed and disarms flight.
 activate(f,c,p);in={};in.focused=true;
 in.speed_increase=true;for(unsigned n=0;n<1600;++n){CHECK(f.update(c,in,true,&p));in.speed_increase=false;CHECK(f.update(c,in,true,&p));in.speed_increase=true;}CHECK(f.current_speed()==c.max_speed&&std::isfinite(f.current_speed()));
 in.speed_increase=false;in.speed_decrease=true;for(unsigned n=0;n<2200;++n){CHECK(f.update(c,in,true,&p));in.speed_decrease=false;CHECK(f.update(c,in,true,&p));in.speed_decrease=true;}CHECK(f.current_speed()==c.min_speed&&std::isfinite(f.current_speed()));
 // Focus/certificate loss clears momentum; a new activation starts at rest.
 in={};in.focused=true;in.toggle=true;CHECK(!f.update(c,in,false,&p)&&!f.active&&f.velocity_magnitude()==0);in.toggle=false;CHECK(!f.update(c,in,true,&p));in.toggle=true;CHECK(f.update(c,in,true,&p));in={};in.focused=true;in.seconds=.05;CHECK(f.update(c,in,true,&p));in.keys[0]=true;CHECK(f.update(c,in,true,&p));CHECK(f.velocity_magnitude()>0);in.focused=false;CHECK(!f.update(c,in,true,&p)&&f.velocity_magnitude()==0&&!f.active);
 // Instant mode retains the former displacement, normalized diagonals and bounded dt.
 auto instant=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MovementSmoothSeconds","0"}});FlightController i;activate(i,instant,p);in={};in.focused=true;in.seconds=.05;CHECK(i.update(instant,in,true,&p));in.keys[0]=true;double z0=i.pose[14];CHECK(i.update(instant,in,true,&p));CHECK(std::abs((i.pose[14]-z0)+2)<.00001);in.keys={};in.keys[0]=in.keys[3]=true;z0=i.pose[14];double x0=i.pose[12];CHECK(i.update(instant,in,true,&p));CHECK(std::abs(std::hypot(i.pose[12]-x0,i.pose[14]-z0)-2)<.00001);
 in.keys={};in.keys[4]=true;double y0=i.pose[13];CHECK(i.update(instant,in,true,&p));CHECK(i.pose[13]-y0==2);in.keys={};in.keys[0]=true;in.seconds=100;z0=i.pose[14];CHECK(i.update(instant,in,true,&p));CHECK(std::abs((i.pose[14]-z0)+2)<.00001);
 // Fast and Slow remain multiplicative and base speed remains unchanged.
 in.seconds=.05;in.keys={};in.keys[0]=true;in.keys[6]=in.keys[7]=true;z0=i.pose[14];CHECK(i.update(instant,in,true,&p));CHECK(std::abs((i.pose[14]-z0)+2.4)<.0001&&i.current_speed()==instant.speed);
 auto travel=[&](double step,unsigned count){FlightController x;activate(x,c,p);FlightInput q;q.focused=true;CHECK(x.update(c,q,true,&p));q.keys[0]=true;q.seconds=step;for(unsigned n=0;n<count;++n)CHECK(x.update(c,q,true,&p));return x.pose[14];};
 CHECK(std::abs(travel(.01,20)-travel(.025,8))<.0002); // Exact exponential integration is independent of frame subdivision.
 FlightController coasting;activate(coasting,c,p);in={};in.focused=true;in.seconds=.05;CHECK(coasting.update(c,in,true,&p));in.keys[0]=true;CHECK(coasting.update(c,in,true,&p));in.keys={};in.mouse_x=150;double x_before=coasting.pose[12],z_before=coasting.pose[14];CHECK(coasting.update(c,in,true,&p));CHECK(std::abs(coasting.pose[12]-x_before)<.00001&&coasting.pose[14]<z_before); // Camera yaw does not rotate existing world-space momentum.
}
namespace {unsigned input_window_calls=0;LRESULT CALLBACK input_window_proc(HWND,UINT,WPARAM,LPARAM){++input_window_calls;return 0x1234;}}
void window_input(){
 HINSTANCE instance=GetModuleHandleW(nullptr);WNDCLASSW cls{};cls.lpfnWndProc=input_window_proc;cls.hInstance=instance;cls.lpszClassName=L"MRRFreeCameraInputFixture";CHECK(RegisterClassW(&cls));
 HWND game=CreateWindowExW(0,cls.lpszClassName,L"game fixture",WS_OVERLAPPEDWINDOW,20,20,320,240,nullptr,nullptr,instance,nullptr);HWND other=CreateWindowExW(0,cls.lpszClassName,L"other fixture",WS_OVERLAPPEDWINDOW,20,20,320,240,nullptr,nullptr,instance,nullptr);CHECK(game&&other);
 {FlightWindowInput input;CHECK(input.attach(game)&&input.intact()&&input.wheel_input_available());input.set_cursor_capture(true);CHECK(input.cursor_capture_active());
  input_window_calls=0;CHECK(SendMessageW(game,WM_SETCURSOR,0,MAKELPARAM(HTCLIENT,WM_MOUSEMOVE))==TRUE&&input_window_calls==0); // Narrow active client suppression.
  CHECK(SendMessageW(game,WM_SETCURSOR,0,MAKELPARAM(HTCAPTION,WM_NCMOUSEMOVE))==0x1234&&input_window_calls==1);
  CHECK(SendMessageW(game,WM_MOUSEWHEEL,MAKEWPARAM(0,120),0)==0x1234&&input_window_calls==2&&input.take_wheel_delta()==120);
  SendMessageW(game,WM_MOUSEWHEEL,MAKEWPARAM(0,60),0);SendMessageW(game,WM_MOUSEWHEEL,MAKEWPARAM(0,60),0);CHECK(input.take_wheel_delta()==120);
  SendMessageW(game,WM_MOUSEWHEEL,MAKEWPARAM(0,static_cast<WORD>(-120)),0);CHECK(input.take_wheel_delta()==-120);
  for(unsigned n=0;n<40;++n)SendMessageW(game,WM_MOUSEWHEEL,MAKEWPARAM(0,120),0);CHECK(input.take_wheel_delta()==1440);
  SendMessageW(game,WM_MOUSEWHEEL,MAKEWPARAM(0,120),0);input.focus_lost();CHECK(!input.cursor_capture_active()&&input.take_wheel_delta()==0);
  SendMessageW(game,WM_SETCURSOR,0,MAKELPARAM(HTCLIENT,WM_MOUSEMOVE));CHECK(input_window_calls>0); // Native behavior resumes outside capture.
  input.set_cursor_capture(false);SendMessageW(other,WM_SETCURSOR,0,MAKELPARAM(HTCLIENT,WM_MOUSEMOVE));CHECK(input_window_calls>0);input.release();CHECK(!input.intact());}
 CHECK(DestroyWindow(other)&&DestroyWindow(game));CHECK(UnregisterClassW(cls.lpszClassName,instance));
}
void cinematic_fov(){
 auto c=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.CinematicVerticalFOVDegrees","60"},{"FreeCamera.FOVSmoothSeconds",".25"}});auto p=identity();FlightController f;FlightInput in;in.focused=true;in.inherited_vfov=70;CHECK(!f.update(c,in,true,&p));in.toggle=true;CHECK(f.update(c,in,true,&p)&&f.current_vertical_fov()==70&&f.target_vertical_fov()==60&&f.fov_transition_active());
 in.toggle=false;in.seconds=.05;CHECK(f.update(c,in,true,&p));double after_one=f.current_vertical_fov();CHECK(after_one<70&&after_one>60&&f.fov_transition_active());for(unsigned i=0;i<80;++i)CHECK(f.update(c,in,true,&p));CHECK(std::abs(f.current_vertical_fov()-60)<.001&&!f.fov_transition_active());
 // Z/X are edge-triggered, bounded lens steps and do not consume repeated key-down samples.
 in.fov_decrease=true;CHECK(f.update(c,in,true,&p)&&f.target_vertical_fov()==55);for(unsigned i=0;i<8;++i)CHECK(f.update(c,in,true,&p)&&f.target_vertical_fov()==55);in.fov_decrease=false;CHECK(f.update(c,in,true,&p));in.fov_increase=true;CHECK(f.update(c,in,true,&p)&&f.target_vertical_fov()==60);
 in.fov_increase=false;for(unsigned i=0;i<20;++i){in.fov_decrease=true;CHECK(f.update(c,in,true,&p));in.fov_decrease=false;CHECK(f.update(c,in,true,&p));}CHECK(f.target_vertical_fov()==c.min_vfov);in.fov_decrease=true;CHECK(f.update(c,in,true,&p)&&f.target_vertical_fov()==c.min_vfov);
 // The exponential response is independent of sample rate and uses the same wall-clock dt while paused.
 auto reach=[&](double step,unsigned n){FlightController x;FlightInput q;q.focused=true;q.inherited_vfov=70;CHECK(!x.update(c,q,true,&p));q.toggle=true;CHECK(x.update(c,q,true,&p));q.toggle=false;q.seconds=step;for(unsigned k=0;k<n;++k)CHECK(x.update(c,q,true,&p));return x.current_vertical_fov();};CHECK(std::abs(reach(.01,10)-reach(.025,4))<.0001);
 auto inherit=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.CinematicVerticalFOVDegrees","0"},{"FreeCamera.FOVSmoothSeconds","0"}});FlightController inherited;FlightInput inherit_input;inherit_input.focused=true;inherit_input.inherited_vfov=72;CHECK(!inherited.update(inherit,inherit_input,true,&p));inherit_input.toggle=true;CHECK(inherited.update(inherit,inherit_input,true,&p)&&inherited.current_vertical_fov()==72&&inherited.target_vertical_fov()==72); // Zero inherits without an activation snap.
 auto instant=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.CinematicVerticalFOVDegrees","60"},{"FreeCamera.FOVSmoothSeconds","0"}});FlightController instant_lens;inherit_input={};inherit_input.focused=true;inherit_input.inherited_vfov=72;CHECK(!instant_lens.update(instant,inherit_input,true,&p));inherit_input.toggle=true;CHECK(instant_lens.update(instant,inherit_input,true,&p)&&instant_lens.current_vertical_fov()==72);inherit_input.toggle=false;inherit_input.seconds=.01;CHECK(instant_lens.update(instant,inherit_input,true,&p)&&instant_lens.current_vertical_fov()==60);
 auto no_lens=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.CinematicFOVEnabled","0"}});FlightController native;activate(native,no_lens,p);in={};in.focused=true;in.inherited_vfov=72;in.seconds=.05;in.fov_decrease=true;CHECK(native.update(no_lens,in,true,&p)&&!native.fov_transition_active()&&native.current_vertical_fov()==0);
 in.focused=false;CHECK(!f.update(c,in,true,&p)&&!f.active&&f.current_vertical_fov()==0);
}
void manual_roll(){
 constexpr double pi=3.14159265358979323846;auto c=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","0"},{"FreeCamera.RollSmoothSeconds","0"},{"FreeCamera.RollSpeedDegreesPerSecond","45"},{"FreeCamera.MaxRollDegrees","30"}});auto p=rolled_pose(.4,.2,0);FlightController left;activate(left,c,p);FlightInput in;in.focused=true;in.seconds=.05;in.roll_left=true;CHECK(left.update(c,in,true,&p));CHECK(std::abs(left.manual_roll_degrees-2.25)<.001&&left.manual_roll_target_degrees==2.25f&&left.pose[1]>0);in.roll_left=false;for(unsigned i=0;i<20;++i)CHECK(left.update(c,in,true,&p));CHECK(std::abs(left.manual_roll_degrees-2.25)<.001); // Key release retains the offset.
 auto right_controller=[&](){FlightController f;activate(f,c,p);FlightInput q;q.focused=true;q.seconds=.05;q.roll_right=true;CHECK(f.update(c,q,true,&p));return f;};auto right=right_controller();CHECK(std::abs(right.manual_roll_degrees+2.25)<.001&&right.pose[1]<0);
 // Requested angle and smoothing use elapsed wall time, not update count.
 auto roll_after=[&](double dt,unsigned n){auto smooth=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","0"},{"FreeCamera.RollSmoothSeconds",".10"}});FlightController f;activate(f,smooth,p);FlightInput q;q.focused=true;q.roll_left=true;q.seconds=dt;for(unsigned k=0;k<n;++k)CHECK(f.update(smooth,q,true,&p));return std::pair<double,double>{f.manual_roll_target_degrees,f.manual_roll_degrees};};auto a=roll_after(.01,10),b=roll_after(.025,4);CHECK(std::abs(a.first-b.first)<.0001&&std::abs(a.second-b.second)<.0001);
 // Reset wins over simultaneous roll input and eases to level without overshoot.
 auto soft=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","1"},{"FreeCamera.RollSmoothSeconds",".10"}});FlightController reset;activate(reset,soft,rolled_pose(.4,.2,0));in={};in.focused=true;in.seconds=.05;in.roll_left=true;CHECK(reset.update(soft,in,true,&p));for(unsigned i=0;i<15;++i)CHECK(reset.update(soft,in,true,&p));in.roll_reset=true;double before=reset.manual_roll_degrees;CHECK(reset.update(soft,in,true,&p)&&reset.manual_roll_target_degrees==0&&reset.manual_roll_degrees<before&&reset.manual_roll_degrees>0);in.roll_left=false;for(unsigned i=0;i<100;++i)CHECK(reset.update(soft,in,true,&p));CHECK(std::abs(reset.manual_roll_degrees)<.001&&!reset.manual_roll_transition_active);
 // Auto-level owns the base orientation while manual bank survives beside it.
 auto tilted=rolled_pose(.7,.2,9*pi/180);FlightController layering;activate(layering,soft,tilted);in={};in.focused=true;in.seconds=.05;in.roll_left=true;for(unsigned i=0;i<6;++i)CHECK(layering.update(soft,in,true,&tilted));CHECK(layering.horizon_level_progress==1&&std::abs(layering.manual_roll_target_degrees-13.5)<.01);
 // Yaw/pitch cannot feed into or erase the separately stored offset; the smooth controller settles after release.
 in.roll_left=false;in.mouse_x=18;in.mouse_y=-11;for(unsigned i=0;i<40;++i)CHECK(layering.update(soft,in,true,&tilted));CHECK(std::abs(layering.manual_roll_degrees-13.5)<.01&&std::abs(layering.current_roll_degrees+13.5)<.1&&layering.orientation_valid);for(float value:layering.pose)CHECK(std::isfinite(value));
 in.mouse_x=in.mouse_y=0;in.keys[0]=true;double move_before=layering.pose[14];CHECK(layering.update(soft,in,true,&tilted)&&layering.pose[14]<move_before&&std::abs(layering.manual_roll_degrees-13.5)<.01);in.keys={};
 auto native_roll_config=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","0"},{"FreeCamera.RollSmoothSeconds","0"}});auto native_rolled=rolled_pose(-.3,.25,9*pi/180);FlightController native_layer;activate(native_layer,native_roll_config,native_rolled);in={};in.focused=true;in.seconds=.05;in.roll_left=true;CHECK(native_layer.update(native_roll_config,in,true,&native_rolled));CHECK(std::abs(native_layer.manual_roll_degrees-2.25)<.001);for(unsigned j=0;j<3;++j)CHECK(std::abs(native_layer.pose[8+j]-native_rolled[8+j])<.0001); // Native roll remains in the base while the manual layer adds its offset.
 auto vertical=rolled_pose(.2,pi/2,0);FlightController pole;activate(pole,soft,vertical);in={};in.focused=true;in.seconds=.05;in.roll_right=true;for(unsigned i=0;i<5;++i)CHECK(pole.update(soft,in,true,&vertical));CHECK(pole.orientation_valid&&std::abs(pole.manual_roll_target_degrees+11.25)<.01&&pole.manual_roll_degrees<0);for(float value:pole.pose)CHECK(std::isfinite(value));
 // Configured bounds hold; reset and focus loss clear only controller-owned state. Re-toggle starts from stock pose.
 auto bounded=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","0"},{"FreeCamera.RollSmoothSeconds","0"},{"FreeCamera.MaxRollDegrees","20"}});FlightController limit;activate(limit,bounded,p);in={};in.focused=true;in.seconds=.05;in.roll_left=true;for(unsigned i=0;i<80;++i)CHECK(limit.update(bounded,in,true,&p));CHECK(limit.manual_roll_target_degrees==20&&limit.manual_roll_degrees==20);in.toggle=true;CHECK(!limit.update(bounded,in,true,&p)&&limit.manual_roll_degrees==0);in.toggle=false;CHECK(!limit.update(bounded,in,true,&p));in.toggle=true;CHECK(limit.update(bounded,in,true,&p)&&limit.pose==p);in={};in.focused=false;CHECK(!limit.update(bounded,in,true,&p)&&!limit.active&&limit.manual_roll_degrees==0);
 // The independent lens and roll controllers remain active together.
 auto combo=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.CinematicVerticalFOVDegrees","60"},{"FreeCamera.AutoLevelHorizon","0"},{"FreeCamera.RollSmoothSeconds","0"}});FlightController both;FlightInput q;q.focused=true;q.inherited_vfov=70;CHECK(!both.update(combo,q,true,&p));q.toggle=true;CHECK(both.update(combo,q,true,&p));q.toggle=false;q.seconds=.05;q.roll_left=true;CHECK(both.update(combo,q,true,&p));CHECK(both.manual_roll_degrees>0&&both.current_vertical_fov()<70&&both.current_vertical_fov()>60);
}
void horizon(){
 auto c=parse_free_camera_config({{"FreeCamera.Enabled","1"}});auto identity_pose=identity();FlightController zero;FlightInput in;in.focused=true;CHECK(!zero.update(c,in,true,&identity_pose));in.toggle=true;in.mouse_x=500;in.mouse_y=-400;in.seconds=.05;CHECK(zero.update(c,in,true,&identity_pose));CHECK(zero.pose==identity_pose); // Activation is exact even with unusual first packet.
 in.toggle=false;in.mouse_x=in.mouse_y=0;in.seconds=.05;for(unsigned i=0;i<6;++i)CHECK(zero.update(c,in,true,&identity_pose));CHECK(std::abs(zero.current_roll_degrees)<.01f&&zero.horizon_level_progress==1&&zero.orientation_valid);
 for(double roll:{9*3.141592653589793/180.,-9*3.141592653589793/180.}){
  auto p=rolled_pose(.73,.31,roll);auto original=p;FlightController f;activate(f,c,p);
  in={};in.focused=true;in.seconds=.05;for(unsigned i=0;i<6;++i)CHECK(f.update(c,in,true,&p));
  CHECK(std::abs(f.current_roll_degrees)<.01f&&f.orientation_valid&&f.horizon_level_progress==1);
  for(unsigned j=0;j<3;++j)CHECK(std::abs(f.pose[12+j]-original[12+j])<1e-6f);
  for(unsigned j=0;j<3;++j)CHECK(std::abs(f.pose[8+j]-original[8+j])<.0002f); // Pure roll correction preserves look direction.
  for(unsigned row=0;row<3;++row){double len=0;for(unsigned j=0;j<3;++j)len+=double(f.pose[row*4+j])*f.pose[row*4+j];CHECK(std::abs(len-1)<.0001);for(unsigned other=0;other<row;++other){double d=0;for(unsigned j=0;j<3;++j)d+=double(f.pose[row*4+j])*f.pose[other*4+j];CHECK(std::abs(d)<.0001);}}
  double det=f.pose[0]*(f.pose[5]*f.pose[10]-f.pose[6]*f.pose[9])-f.pose[1]*(f.pose[4]*f.pose[10]-f.pose[6]*f.pose[8])+f.pose[2]*(f.pose[4]*f.pose[9]-f.pose[5]*f.pose[8]);CHECK(det>.999&&det<1.001);
 }
 // Different frame subdivisions produce the same configured correction time.
 auto tilted=rolled_pose(-.4,.2,9*3.141592653589793/180.);FlightController a,b;activate(a,c,tilted);activate(b,c,tilted);in={};in.focused=true;in.seconds=.025;for(unsigned i=0;i<12;++i)CHECK(a.update(c,in,true,&tilted));in.seconds=.05;for(unsigned i=0;i<6;++i)CHECK(b.update(c,in,true,&tilted));CHECK(a.horizon_level_progress==b.horizon_level_progress&&std::abs(a.current_roll_degrees-b.current_roll_degrees)<.01f);
 // Zero duration is immediate on the first post-activation sample, never on activation.
 auto instant=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.HorizonLevelSeconds","0"}});FlightController immediate;activate(immediate,instant,tilted);CHECK(std::abs(immediate.current_roll_degrees)>8);in.seconds=.001;CHECK(immediate.update(instant,in,true,&tilted));CHECK(immediate.horizon_level_progress==1&&std::abs(immediate.current_roll_degrees)<.01f);
 // Disabled auto-level retains cinematic native roll and mouse yaw/pitch stays rigid.
 auto cinematic=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.AutoLevelHorizon","0"}});FlightController native;activate(native,cinematic,tilted);in={};in.focused=true;in.seconds=.05;CHECK(native.update(cinematic,in,true,&tilted));CHECK(std::abs(std::abs(native.current_roll_degrees)-9)<.05f&&native.pose==tilted);
 for(double pitch:{89*3.141592653589793/180.,3.141592653589793/2.,-3.141592653589793/2.}){auto vertical=rolled_pose(.2,pitch,.4);FlightController near_vertical;activate(near_vertical,c,vertical);in={};in.focused=true;in.seconds=.05;for(unsigned i=0;i<6;++i)CHECK(near_vertical.update(c,in,true,&vertical));for(float v:near_vertical.pose)CHECK(std::isfinite(v));CHECK(near_vertical.orientation_valid);}
 // Once leveled, repeated yaw/pitch input cannot accumulate roll or invert at pitch bounds.
 auto level_start=identity();FlightController look;activate(look,c,level_start);in={};in.focused=true;in.seconds=.05;for(unsigned i=0;i<6;++i)CHECK(look.update(c,in,true,&level_start));in.mouse_x=20;in.mouse_y=-20;for(unsigned i=0;i<200;++i)CHECK(look.update(c,in,true,&level_start));CHECK(look.orientation_valid&&std::abs(look.current_roll_degrees)<.05f);for(float v:look.pose)CHECK(std::isfinite(v));
 in.mouse_x=-20;in.mouse_y=20;for(unsigned i=0;i<200;++i)CHECK(look.update(c,in,true,&level_start));CHECK(look.orientation_valid&&std::abs(look.current_roll_degrees)<.05f);
 FlightController reversible;activate(reversible,c,level_start);in={};in.focused=true;in.mouse_x=20;CHECK(reversible.update(c,in,true,&level_start));in.mouse_x=-20;CHECK(reversible.update(c,in,true,&level_start));for(unsigned j=0;j<12;++j)CHECK(std::abs(reversible.pose[j]-level_start[j])<.001f);
 // A nearly half-turn initial roll follows a bounded shortest correction over
 // the configured interval rather than flipping the basis on one sample.
 auto half_turn=rolled_pose(0,0,179*3.141592653589793/180.);FlightController shortest;activate(shortest,c,half_turn);in={};in.focused=true;in.seconds=.05;CHECK(shortest.update(c,in,true,&half_turn));CHECK(std::abs(shortest.current_roll_degrees)<179&&std::abs(shortest.current_roll_degrees)>150);
}
D3DMATRIX view_of(const std::array<float,16>& p){D3DMATRIX v{};for(unsigned j=0;j<3;++j){v.m[j][0]=p[j];v.m[j][1]=p[4+j];v.m[j][2]=-p[8+j];v.m[3][0]-=p[12+j]*p[j];v.m[3][1]-=p[12+j]*p[4+j];v.m[3][2]+=p[12+j]*p[8+j];}v._44=1;return v;}
void scopes(){
 auto pose=identity();auto view=view_of(pose);std::array<float,16> observed{};CHECK(pose_from_native_view(view,observed)&&observed==pose);view._11=2;CHECK(!pose_from_native_view(view,observed));
 // Recorded A3c VIEW is interpolated and differs from Current Pose. Invert actual displayed VIEW.
 view={};float values[]={.532325149f,.096113041f,.841066122f,0,-7.4505806e-9f,.99353385f,-.113536328f,0,.846539974f,-.0604382344f,-.52888304f,0,738.643311f,115.719849f,1489.48071f,1};std::memcpy(&view,values,64);CHECK(pose_from_native_view(view,observed));CHECK(observed[8]<0&&observed[10]>0);
 for(bool fov:{false,true})for(bool fly:{false,true}){
  CameraFrame camera;camera.source_angle=90;camera.flags=0x12;camera.width=1280;camera.height=720;camera.pose=camera.previous_pose=identity();camera.snap_frames=9;for(unsigned i=0;i<12;++i)camera.planes[i]=float(i+1);
  auto stock=camera;auto flight=camera.pose;flight[12]+=100;FrustumFrame scope;
  if(fov||fly){CHECK(scope.begin(&camera,fov?75.f:90.f/(1280.f/720),fly?&flight:nullptr));
   if(fly)CHECK(camera.pose==flight&&camera.previous_pose==flight&&camera.planes!=stock.planes);
   // Traverse/finalize/particle/late-debug readers run before completion, all see effective fields.
   for(unsigned reader=0;reader<5;++reader){CHECK(scope.status.synchronized);if(fly)CHECK(camera.pose==flight);}
   camera.x=13;camera.y=17;camera.width=1920;camera.height=1080;camera.flags=0x56;camera.snap_frames=7;
   CHECK(scope.restore());CHECK(camera.pose==stock.pose&&camera.previous_pose==stock.previous_pose&&camera.planes==stock.planes);
   CHECK(camera.width==1920&&camera.height==1080&&camera.x==13&&camera.y==17&&camera.flags==0x56&&camera.snap_frames==7);
  }else CHECK(!scope.status.synchronized&&std::memcmp(&camera,&stock,sizeof(camera))==0);
 }
 CameraFrame c;c.source_angle=90;c.width=640;c.height=480;c.pose=c.previous_pose=identity();auto p=c.pose;p[12]+=100;FrustumFrame scope;CHECK(scope.begin(&c,75,&p));scope.abandon();CHECK(!scope.restore()); // No stale dereference.
 GameFov shared;VisualConfig cfg;CHECK(!shared.install(false,cfg));shared.scheduler_begin();shared.finish_frame();shared.scheduler_end();CHECK(!shared.free_camera_active());
}
namespace {
uint32_t native_calls=0,callbacks=0,callback_alignment=0,last_kind=0,native_ecx=0,native_edx=0,native_flags=0,output_flags=0;
uint32_t native_ebx=0,native_esi=0,native_edi=0,native_ebp=0,args[3]{},after_eax=0,after_edx=0,after_flags=0,stack_before=0,stack_after=0;
alignas(16) unsigned char host_fp[512],input_fp[512],native_fp[512],output_fp[512],after_fp[512];
alignas(16) unsigned int mxcsr_input=0x3f80,mxcsr_output=0x5f80;
uintptr_t selected_bridge=0;bool callback_enabled=true,want_reentry=false,in_reentry=false;
camera_bridge::Saved callback_input{};
void __stdcall callback_body(uint32_t kind,const camera_bridge::Saved* input){++callbacks;last_kind=kind;if(callback_enabled)callback_input=*input;
 if(kind==0&&want_reentry&&!in_reentry){in_reentry=true;__asm {push 03f123456h} __asm {call selected_bridge}in_reentry=false;}
 __asm {fninit} __asm {fldz} __asm {pxor xmm0,xmm0} __asm {pxor xmm7,xmm7} __asm {clc}
}
__declspec(naked) void callback_fixture(){__asm {mov eax,esp} __asm {and eax,15} __asm {mov callback_alignment,eax} __asm {jmp callback_body}}
#define NATIVE_BODY \
 __asm {mov native_ecx,ecx} __asm {mov native_edx,edx} \
 __asm {mov native_ebx,ebx} __asm {mov native_esi,esi} __asm {mov native_edi,edi} __asm {mov native_ebp,ebp} \
 __asm {pushfd} __asm {pop native_flags} __asm {fxsave native_fp} \
 __asm {inc native_calls} __asm {fninit} __asm {fldlg2} __asm {ldmxcsr mxcsr_output} \
 __asm {pxor xmm0,xmm0} __asm {pcmpeqd xmm7,xmm7} \
 __asm {mov eax,012345678h} __asm {mov edx,0aabbccddh} \
 __asm {cmp eax,eax} __asm {pushfd} __asm {pop output_flags} __asm {fxsave output_fp}
__declspec(naked) void original0(){NATIVE_BODY __asm {ret}}
__declspec(naked) void original1(){__asm {mov eax,[esp+4]} __asm {mov args,eax} NATIVE_BODY __asm {ret 4}}
__declspec(naked) void original2(){__asm {mov eax,[esp+4]} __asm {mov args,eax} __asm {mov eax,[esp+8]} __asm {mov args+4,eax} NATIVE_BODY __asm {ret 8}}
__declspec(naked) void original3(){__asm {mov eax,[esp+4]} __asm {mov args,eax} __asm {mov eax,[esp+8]} __asm {mov args+4,eax} __asm {mov eax,[esp+12]} __asm {mov args+8,eax} NATIVE_BODY __asm {ret 12}}
#define START \
 __asm {pushfd} __asm {pushad} __asm {mov stack_before,esp} __asm {fxsave host_fp} \
 __asm {fninit} __asm {fld1} __asm {fldpi} __asm {ldmxcsr mxcsr_input} \
 __asm {pcmpeqd xmm0,xmm0} __asm {pxor xmm7,xmm7} __asm {fxsave input_fp} \
 __asm {mov ecx,011223344h} __asm {mov edx,055667788h} __asm {mov ebx,010203040h} \
 __asm {mov esi,020304050h} __asm {mov edi,030405060h} __asm {mov ebp,040506070h} __asm {stc}
#define FINISH \
 __asm {mov after_eax,eax} __asm {mov after_edx,edx} __asm {pushfd} __asm {pop after_flags} \
 __asm {fxsave after_fp} __asm {mov stack_after,esp} __asm {fxrstor host_fp} __asm {popad} __asm {popfd} __asm {ret}
__declspec(naked) void run0(){START __asm {call selected_bridge} FINISH}
__declspec(naked) void run1(){START __asm {push 03f123456h} __asm {call selected_bridge} FINISH}
__declspec(naked) void run2(){START __asm {push 055aa55aah} __asm {push 03f123456h} __asm {call selected_bridge} FINISH}
__declspec(naked) void run3(){START __asm {push 022332233h} __asm {push 055aa55aah} __asm {push 03f123456h} __asm {call selected_bridge} FINISH}
bool fp_equal(const unsigned char* a,const unsigned char* b){
 if(std::memcmp(a,b,5)||std::memcmp(a+6,b+6,8)||std::memcmp(a+16,b+16,6)||std::memcmp(a+24,b+24,8))return false;
 for(unsigned i=0;i<8;++i)if(std::memcmp(a+32+i*16,b+32+i*16,10))return false;
 return !std::memcmp(a+160,b+160,128);
}
void bridge_case(uintptr_t bridge,uintptr_t& target,uintptr_t original,void(*run)(),uint32_t kind,uint32_t expected_callbacks,unsigned nargs){
 selected_bridge=bridge;target=original;native_calls=callbacks=0;camera_bridge::callback=reinterpret_cast<camera_bridge::Callback>(&callback_fixture);run();
 CHECK(native_calls==(want_reentry?2u:1u)&&callbacks==expected_callbacks&&last_kind==kind&&callback_alignment==12);
 CHECK(native_ecx==0x11223344&&native_edx==0x55667788&&(native_flags&1));
 CHECK(native_ebx==0x10203040&&native_esi==0x20304050&&native_edi==0x30405060&&native_ebp==0x40506070);
 CHECK(after_eax==0x12345678&&after_edx==0xaabbccdd&&after_flags==output_flags&&stack_before==stack_after);
 CHECK(fp_equal(input_fp,native_fp)&&fp_equal(output_fp,after_fp));
 if(nargs)CHECK(args[0]==0x3f123456);if(nargs>1)CHECK(args[1]==0x55aa55aa);if(nargs>2)CHECK(args[2]==0x22332233);
 if(callback_enabled){CHECK(callback_input.ecx==0x11223344&&callback_input.edx==0x55667788);if(nargs)CHECK(callback_input.args[0]==0x3f123456);}
}
void bridges(){
 using namespace camera_bridge;
 for(bool enabled:{true,false}){callback_enabled=enabled;for(unsigned frame=0;frame<3;++frame)
  bridge_case(reinterpret_cast<uintptr_t>(&scheduler),scheduler_original,reinterpret_cast<uintptr_t>(&original1),&run1,1,2,1);}
 callback_enabled=true;want_reentry=true;
 bridge_case(reinterpret_cast<uintptr_t>(&scheduler),scheduler_original,reinterpret_cast<uintptr_t>(&original1),&run1,1,4,1);want_reentry=false;
}

}
int main(){try{controls();clock_timing();movement_and_speed();window_input();cinematic_fov();manual_roll();horizon();scopes();bridges();std::cout<<"High precision flight clock / movement and speed / cinematic FOV / manual roll / cursor and wheel HWND policy / horizon stabilization / displayed VIEW inversion / owned 176-byte scope / seven real scheduler RET4 ABI cases: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
