#include "free_camera.hpp"
#include "race_epoch.hpp"
#include <iostream>
#include <stdexcept>
#include <cmath>
#include <cstring>
#include <vector>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
std::array<float,16> identity(){return {1,0,0,0,0,1,0,0,0,0,1,0,10,20,30,1};}
void controls(){
 wchar_t directory[MAX_PATH]{},name[MAX_PATH]{};CHECK(GetTempPathW(MAX_PATH,directory)&&GetTempFileNameW(directory,L"mcf",0,name));
 struct TempIni {const wchar_t* path;~TempIni(){DeleteFileW(path);}} cleanup{name};
 const char text[]="[Renderer]\r\nConfigVersion=1\r\n[FreeCamera]\r\nEnabled=1\r\nControlPreset=1\r\nToggleKey=F8\r\n[Trace]\r\nEnabled=0\r\n";
 HANDLE file=CreateFileW(name,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);CHECK(file!=INVALID_HANDLE_VALUE);DWORD written=0;bool stored=WriteFile(file,text,sizeof(text)-1,&written,nullptr)&&written==sizeof(text)-1;CloseHandle(file);CHECK(stored);
 auto loaded=read_visual_config(name);auto parsed=parse_free_camera_config(loaded.raw_fields);CHECK(loaded.version_ok&&parsed.enabled&&parsed.preset==1); // Actual INI reader, no tracing prerequisite.
 auto invalid=parse_visual_config({{"Renderer.ConfigVersion","2"},{"FreeCamera.Enabled","1"}},true);GameFov rejected;CHECK(!rejected.install(true,invalid,nullptr,true)&&!rejected.free_camera_configured());
 CHECK(!parse_free_camera_config({}).enabled);
 auto c=parse_free_camera_config({{"FreeCamera.Enabled","1"}});CHECK(c.enabled&&c.preset==0&&c.toggle==VK_F8);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.ToggleKey","F10"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MoveSpeed","NaN"}}).enabled);
 CHECK(!parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.MoveSpeed","40junk"}}).enabled);
 auto pad=parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.ControlPreset","1"}});CHECK(pad.enabled&&pad.keys[0]==0x148&&pad.keys[0]!=VK_UP&&pad.keys[0]!='8');
 std::map<std::string,std::string> custom{{"FreeCamera.Enabled","1"},{"FreeCamera.ControlPreset","2"},{"FreeCamera.ToggleKey","Q"}};
 const char* names[]={"Forward","Backward","Left","Right","Up","Down","Fast","Slow"};const char* keys[]={"Numpad8","Numpad2","Numpad4","Numpad6","Numpad9","Numpad3","LeftShift","LeftAlt"};
 for(size_t i=0;i<8;++i)custom[std::string("FreeCameraKeys.")+names[i]]=keys[i];CHECK(parse_free_camera_config(custom).enabled);custom["FreeCameraKeys.Forward"]="Q";CHECK(!parse_free_camera_config(custom).enabled);
 FlightWindowInput input;input.key_event(0x48,true,true);CHECK(!input.physical_down(0x48));input.key_event(0x48,false,true);CHECK(input.physical_down(0x48));input.key_event(0x48,false,false);CHECK(!input.physical_down(0x48));
 input.key_event(0x48,false,true);input.focus_lost();CHECK(!input.physical_down(0x48));CHECK(!input.sample(pad,true).focused);
 FlightController f;FlightInput in;auto visible=identity();in.focused=true;CHECK(!f.update(c,in,true,&visible));in.toggle=true;CHECK(f.update(c,in,true,&visible)&&f.pose==visible);
 // Held toggle does not oscillate; exact initial pose, no activation snap/flip.
 CHECK(f.update(c,in,true,&visible));in.toggle=false;CHECK(f.update(c,in,true,&visible));
 in.keys[0]=in.keys[3]=true;in.seconds=1;auto before=f.pose;CHECK(f.update(c,in,true,&visible));double length=0;for(unsigned j=0;j<3;++j)length+=std::pow(f.pose[12+j]-before[12+j],2);CHECK(std::abs(std::sqrt(length)-2)<.00001); // 40m/s, bounded .05sec diagonal.
 in.keys={};in.keys[4]=true;in.seconds=.01;before=f.pose;f.update(c,in,true,&visible);CHECK(f.pose[12]==before[12]&&f.pose[14]==before[14]&&f.pose[13]>before[13]);
 in.keys={};in.mouse_x=1000;in.mouse_y=-1000;for(unsigned n=0;n<100;++n)CHECK(f.update(c,in,true,&visible));CHECK(std::isfinite(f.pose[0])&&std::abs(f.pose[9])<1);
 in={};in.focused=false;CHECK(!f.update(c,in,true,&visible)&&!f.active);in.focused=true;in.toggle=true;CHECK(!f.update(c,in,true,&visible)); // Held toggle through Alt+Tab requires release.
 in.toggle=false;f.update(c,in,true,&visible);in.toggle=true;CHECK(f.update(c,in,true,&visible));CHECK(!f.update(c,in,false,&visible));
 // Frontend/unknown certificate and malformed visible view never activate.
 f.cancel();in.toggle=false;f.update(c,in,true,&visible);in.toggle=true;CHECK(!f.update(c,in,false,&visible));visible[0]=2;f.cancel();in.toggle=false;f.update(c,in,true,&visible);in.toggle=true;CHECK(!f.update(c,in,true,&visible));
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
int main(){try{controls();scopes();bridges();std::cout<<"Flight controls / displayed VIEW inversion / owned 176-byte scope / seven real scheduler RET4 ABI cases: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
