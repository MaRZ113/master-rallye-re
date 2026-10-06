#include "game_fov.hpp"
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <intrin.h>
#include <cfenv>
namespace gfx2 {
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
bool FrustumFrame::begin(CameraFrame* camera,float vfov) noexcept {
 if(!restore())return false;
 CameraFrame c{};float hfov=0;std::array<float,12> planes{};
 if(!camera||!safe_copy(&c,camera,sizeof(c))||!effective_side_planes(c,vfov,planes,hfov)){status.reason="ineligible_camera";return false;}
 if(!safe_copy(camera->planes.data(),planes.data(),sizeof(planes))){
  // A guarded memcpy can have written a prefix before faulting across a page boundary.
  safe_copy(camera->planes.data(),c.planes.data(),sizeof(c.planes));CameraFrame check{};
  status.restored=safe_copy(&check,camera,sizeof(check))&&std::memcmp(check.planes.data(),c.planes.data(),sizeof(c.planes))==0;
  status.reason="camera_write_failed";++status.failures;return false;
 }
 camera_=camera;snapshot_=c;effective_=planes;status.synchronized=true;status.restored=false;
 status.width=c.width;status.height=c.height;status.source=c.source_angle;status.vfov=vfov;status.hfov=hfov;++status.synchronized_frames;status.reason="matched_side_planes";return true;
}
bool FrustumFrame::matches(const CameraFrame* camera,const D3DMATRIX& p) const noexcept {
 SavedFP fp;
 CameraFrame c{};
 return status.synchronized&&camera==camera_&&safe_copy(&c,camera,sizeof(c))&&snapshot_equal(c,snapshot_)&&
  std::memcmp(c.planes.data(),effective_.data(),sizeof(effective_))==0&&symmetric_lh(p)&&
  std::abs(double(p._22)/p._11-double(c.width)/c.height)<=.00001*double(c.width)/c.height&&
  std::abs(source_camera_angle(p)-90.)<=SOURCE_CAMERA_TOLERANCE_DEGREES;
}
bool FrustumFrame::restore() noexcept {
 SavedFP fp;
 status.synchronized=false;status.width=status.height=0;status.source=status.vfov=status.hfov=0;
 if(!camera_)return status.restored;
 CameraFrame c{};bool okay=safe_copy(&c,camera_,sizeof(c));
 if(okay&&std::memcmp(c.planes.data(),effective_.data(),sizeof(effective_))==0)
  okay=snapshot_equal(c,snapshot_)&&safe_copy(camera_->planes.data(),snapshot_.planes.data(),sizeof(snapshot_.planes));
 // Changed planes belong to the engine; never overwrite an intervening stock rebuild.
 camera_=nullptr;status.synchronized=false;status.restored=okay;
 if(!okay){++status.failures;status.reason="camera_restore_failed";}return okay;
}
bool GameFov::install(bool exact,const VisualConfig& c) noexcept {
 if(!exact||!c.fov){frame_.status.reason=exact?"disabled":"unsupported_build";return false;}
 if(active||ambiguous_devices){ambiguous_devices=true;if(active)active->disable("multiple_devices");frame_.status.reason="multiple_devices";report(frame_.status);return false;}
 base_=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));thread_=GetCurrentThreadId();vfov_=c.vfov;
 // The pristine PE uses absolute constants; unsupported placement stays stock.
 if(base_!=0x400000||!IsProcessorFeaturePresent(PF_XMMI64_INSTRUCTIONS_AVAILABLE)){frame_.status.reason="unsupported_image_or_cpu";report(frame_.status);return false;}
 constexpr unsigned char context[]={0x8b,0x40,0x20,0x3b,0xfb,0x0f,0x94,0xc1,0x51,0x57,0x8b,0xc8,0xe8,0x9e,0x63,0xeb,0xff};
 unsigned char observed[sizeof(context)]{};
 if(!safe_copy(observed,reinterpret_cast<void*>(base_+SUBMIT_CALL_RVA-12),sizeof(observed))||std::memcmp(context,observed,sizeof(context))){frame_.status.reason="call_signature_mismatch";report(frame_.status);return false;}
 HMODULE pinned=nullptr;
 if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&detail::submit_bridge),&pinned)){frame_.status.reason="module_pin_failed";report(frame_.status);return false;}
 detail::original_submit=base_+SUBMIT_OWNER_RVA;active=this;
 enabled_=patch_.install(memory,reinterpret_cast<void*>(base_+SUBMIT_CALL_RVA),reinterpret_cast<uintptr_t>(&detail::submit_bridge),SUBMIT_CALL_BYTES);
 frame_.status.installed=patch_.installed();frame_.status.reason=enabled_?"installed_before_device_return":"call_patch_failed";
 if(!enabled_){active=nullptr;patch_.remove(memory);frame_.status.installed=patch_.installed();}
 report(frame_.status);return enabled_;
}
void GameFov::before_submit(unsigned index) noexcept {
 if(!enabled_){frame_.status.reason="inactive";return;}
 if(GetCurrentThreadId()!=thread_){enabled_=false;frame_.status.synchronized=false;frame_.status.reason="wrong_render_thread";++frame_.status.failures;return;}
 uintptr_t manager=0,camera=0;int count=0;
 if(!safe_copy(&manager,reinterpret_cast<void*>(base_+CAMERA_MANAGER_RVA),4)||!manager||
    !safe_copy(&count,reinterpret_cast<void*>(manager+0x10),4)||count!=1||index!=0||
    !safe_copy(&camera,reinterpret_cast<void*>(manager+index*4),4)||!camera||
    current_camera(base_)!=reinterpret_cast<CameraFrame*>(camera)){
  frame_.restore();frame_.status.reason="unmapped_camera_schedule";return;
 }
 if(!frame_.begin(reinterpret_cast<CameraFrame*>(camera),vfov_)&&!frame_.status.restored)disable("camera_restore_failed");
}
bool GameFov::allows(const D3DMATRIX& p) const noexcept {
 return enabled_&&GetCurrentThreadId()==thread_&&frame_.matches(current_camera(base_),p);
}
void GameFov::finish_frame() noexcept {if(!frame_.restore())disable("camera_restore_failed");}
void GameFov::disable(const char* reason) noexcept {
 enabled_=false;frame_.restore();if(active==this)active=nullptr;
 // Startup/teardown are on the renderer thread; never hot-patch from an unreviewed thread.
 if(GetCurrentThreadId()==thread_)patch_.remove(memory);
 frame_.status.installed=patch_.installed();frame_.status.reason=reason;report(frame_.status);
}
GameFov::~GameFov(){if(patch_.installed())disable("device_release");}
}
