#include "game_fov.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <cfenv>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
namespace gfx2::detail {extern uintptr_t original_submit;void submit_bridge();}
CameraFrame camera(int w=640,int h=480){CameraFrame c;c.source_angle=90;c.width=w;c.height=h;c.pose[0]=c.pose[5]=c.pose[10]=c.pose[15]=1;for(int i=0;i<12;++i)c.planes[i]=float(i+1);return c;}
D3DMATRIX projection(const CameraFrame& c){D3DMATRIX p{};double v=c.source_angle/std::max(1.,double(c.width)/c.height);p._22=static_cast<float>(1./std::tan(v*3.14159265358979323846/360));p._11=p._22/(float(c.width)/c.height);p._33=1.0002f;p._34=1;p._43=-.20004f;return p;}
bool visible(const std::array<float,12>& planes,float x,float y,float z,float radius=0){for(int i=0;i<4;++i)if(planes[i*3]*x+planes[i*3+1]*y+planes[i*3+2]*z>=radius)return false;return true;}
void frustum(){
 constexpr double pi=3.14159265358979323846;
 VisualPolicy policy;policy.configure(parse_visual_config({{"Renderer.ConfigVersion","1"},{"Camera.GameplayFOV","true"},{"Camera.VerticalFOVDegrees","80"}},true),true,nullptr,E_FAIL);
 CHECK(policy.effective.fov);
 for(auto size:{std::pair<int,int>{640,480},{1920,1027},{480,640}}){
  auto c=camera(size.first,size.second),stock=c;FrustumFrame frame;CHECK(frame.begin(&c,80));CHECK(frame.status.synchronized&&frame.status.vfov==80);
  auto original=projection(c);D3DMATRIX effective{};CHECK(frame.matches(&c,original));CHECK(policy.projection(D3DTS_PROJECTION,&original,effective,true,GAMEPLAY_PROJECTION_RETURN_RVA));
  CHECK(std::abs(vertical_fov(effective)-frame.status.vfov)<.0001);
  double h=frame.status.hfov*pi/360.;CHECK(std::abs(std::tan(h)-1./effective._11)<.00001);
  // A small object beyond the stock CPU horizontal edge is retained inside the widened perspective.
  if(size.first>size.second){double stock_h=45*pi/180.;float x=static_cast<float>(10*(std::tan(stock_h)+std::tan(h))/2);CHECK(visible(c.planes,x,0,-10));}
  float edge=static_cast<float>(10/effective._11);CHECK(visible(c.planes,edge*.999f,0,-10));CHECK(!visible(c.planes,edge*1.001f,0,-10));
  float top=static_cast<float>(10/effective._22);CHECK(visible(c.planes,0,top*.999f,-10));CHECK(!visible(c.planes,0,top*1.001f,-10));
  CHECK(frame.restore()&&!frame.status.synchronized&&frame.status.restored&&std::memcmp(&c,&stock,sizeof(c))==0);
  CHECK(!frame.matches(&c,original));
 }
 // Freecam may replace only the lens value while retaining the exact same CPU-frustum scope.
 auto freecam_only=parse_visual_config({{"Renderer.ConfigVersion","1"}},true);VisualPolicy cinematic;cinematic.configure(freecam_only,true,nullptr,E_FAIL);
 auto cam=camera(1920,1080);FrustumFrame synchronized;CHECK(synchronized.begin(&cam,65));auto native_projection=projection(cam);D3DMATRIX cinematic_projection{};
 CHECK(!cinematic.projection(D3DTS_PROJECTION,&native_projection,cinematic_projection,true,GAMEPLAY_PROJECTION_RETURN_RVA));
 CHECK(cinematic.projection(D3DTS_PROJECTION,&native_projection,cinematic_projection,true,GAMEPLAY_PROJECTION_RETURN_RVA,65));CHECK(std::abs(vertical_fov(cinematic_projection)-65)<.0001&&std::abs(synchronized.status.vfov-vertical_fov(cinematic_projection))<.0001);
 CHECK(synchronized.matches(&cam,native_projection));CHECK(!cinematic.projection(D3DTS_PROJECTION,&native_projection,cinematic_projection,true,GAMEPLAY_PROJECTION_RETURN_RVA,111));CHECK(synchronized.restore());
 auto combined=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Camera.GameplayFOV","true"},{"Camera.VerticalFOVDegrees","80"}},true);VisualPolicy coexist;coexist.configure(combined,true,nullptr,E_FAIL);
 CHECK(coexist.projection(D3DTS_PROJECTION,&native_projection,cinematic_projection,true,GAMEPLAY_PROJECTION_RETURN_RVA,65)&&std::abs(vertical_fov(cinematic_projection)-65)<.0001);
 // No unsafe source angle (110*1920/1027 >180) is passed to stock trig: actual HFOV stays below180.
 auto c=camera(1920,1027);std::array<float,12> planes{};float hfov=0;CHECK(effective_side_planes(c,110,planes,hfov)&&hfov>110&&hfov<180);
 for(float invalid:{NAN,29.f,111.f})CHECK(!effective_side_planes(c,invalid,planes,hfov));
 c.source_angle=45;CHECK(!effective_side_planes(c,80,planes,hfov));c.source_angle=89;CHECK(!effective_side_planes(c,80,planes,hfov));c=camera();c.width=0;CHECK(!effective_side_planes(c,80,planes,hfov));
 c=camera();c.pose[0]=2;CHECK(!effective_side_planes(c,80,planes,hfov));c=camera();c.pose[6]=.3f;CHECK(!effective_side_planes(c,80,planes,hfov));
 c=camera();c.pose[12]=NAN;CHECK(!effective_side_planes(c,80,planes,hfov));
 // Five camera orientations plus active-camera lookback: all use the same rigid basis math.
 for(double angle:{0.,.2,.8,1.4,2.2,pi}){c=camera();c.pose[0]=c.pose[10]=static_cast<float>(std::cos(angle));c.pose[2]=static_cast<float>(-std::sin(angle));c.pose[8]=static_cast<float>(std::sin(angle));
  CHECK(effective_side_planes(c,80,planes,hfov));CHECK(visible(planes,-10*c.pose[8],0,-10*c.pose[10]));CHECK(!visible(planes,10*c.pose[8],0,10*c.pose[10]));}
 // Proof expires on changed dimensions, orientation, source family or intervening stock rebuild.
 c=camera();FrustumFrame frame;auto stock=c;CHECK(frame.begin(&c,80));auto p=projection(c);c.width=1920;CHECK(!frame.matches(&c,p));c.width=640;c.pose[12]=1;CHECK(!frame.matches(&c,p));c.pose[12]=0;c.source_angle=45;CHECK(!frame.matches(&c,p));c.source_angle=90;
 c.planes=stock.planes;CHECK(!frame.matches(&c,p));CHECK(frame.restore()&&c.planes==stock.planes);
 CHECK(!frame.begin(nullptr,80));
 GameFov hook;CHECK(!hook.install(false,policy.effective)&&!hook.status().installed);auto off=policy.effective;off.fov=false;CHECK(!hook.install(true,off)&&!hook.status().installed);
 CHECK(!hook.allows(p)); // Unsupported/disabled never becomes a projection-only fallback.
 // Even a caller erroneously supplying exact=true cannot bypass the live byte signature.
 CHECK(!hook.install(true,policy.effective)&&!hook.status().installed);
 fenv_t saved;fegetenv(&saved);fesetround(FE_DOWNWARD);feclearexcept(FE_ALL_EXCEPT);feraiseexcept(FE_DIVBYZERO);
 c=camera();auto exceptions=fetestexcept(FE_ALL_EXCEPT);CHECK(effective_side_planes(c,80,planes,hfov));CHECK(fegetround()==FE_DOWNWARD&&fetestexcept(FE_ALL_EXCEPT)==exceptions);fesetenv(&saved);
}
struct MockMemory:PatchMemory {
 std::array<unsigned char,5> bytes=SUBMIT_CALL_BYTES;DWORD protection=PAGE_EXECUTE_READ;
 int writes=0,protects=0,flushes=0,fail_write=0,fail_protect=0,fail_flush=0;bool partial=false;
 bool read(void* d,const void*,size_t n) noexcept override{std::memcpy(d,bytes.data(),n);return true;}
 bool write(void*,const void* s,size_t n) noexcept override{++writes;if(writes==fail_write){if(partial)std::memcpy(bytes.data(),s,2);return false;}std::memcpy(bytes.data(),s,n);return true;}
 bool protect(void*,size_t,DWORD p,DWORD& old) noexcept override{++protects;if(protects==fail_protect)return false;old=protection;protection=p;return true;}
 bool flush(void*,size_t) noexcept override{return ++flushes!=fail_flush;}
};
void failures(){
 auto site=reinterpret_cast<void*>(0x6532dd);
 for(int kind=0;kind<4;++kind){MockMemory m;CallPatch patch;if(kind==0)m.fail_protect=1;if(kind==1){m.fail_write=1;m.partial=true;}if(kind==2)m.fail_flush=1;if(kind==3)m.fail_protect=2;
  CHECK(!patch.install(m,site,0x60000000,SUBMIT_CALL_BYTES)&&m.bytes==SUBMIT_CALL_BYTES&&!patch.installed()&&m.protection==PAGE_EXECUTE_READ);}
 MockMemory m;CallPatch patch;m.bytes[4]^=1;auto wrong=m.bytes;CHECK(!patch.install(m,site,0x60000000,SUBMIT_CALL_BYTES)&&m.writes==0&&m.protects==0&&m.bytes==wrong);
 m.bytes=SUBMIT_CALL_BYTES;CHECK(patch.install(m,site,0x60000000,SUBMIT_CALL_BYTES)&&patch.installed()&&m.protection==PAGE_EXECUTE_READ);
 auto replacement=m.bytes;CHECK(!patch.install(m,site,0x60000000,SUBMIT_CALL_BYTES));m.fail_protect=m.protects+1;CHECK(!patch.remove(m)&&patch.installed()&&m.bytes==replacement);
 m.fail_protect=0;CHECK(patch.remove(m)&&!patch.installed()&&m.bytes==SUBMIT_CALL_BYTES);
 for(int kind=0;kind<3;++kind){MockMemory failure;CallPatch removal;CHECK(removal.install(failure,site,0x60000000,SUBMIT_CALL_BYTES));auto bytes=failure.bytes;
  if(kind==0){failure.fail_write=failure.writes+1;failure.partial=true;}if(kind==1)failure.fail_flush=failure.flushes+1;if(kind==2)failure.fail_protect=failure.protects+2;
  CHECK(!removal.remove(failure)&&removal.installed()&&failure.bytes==bytes&&failure.protection==PAGE_EXECUTE_READ);
  failure.fail_write=failure.fail_flush=failure.fail_protect=0;CHECK(removal.remove(failure)&&failure.bytes==SUBMIT_CALL_BYTES);}
 CHECK(patch.install(m,site,0x60000000,SUBMIT_CALL_BYTES));m.bytes[4]^=1;wrong=m.bytes;auto n=m.writes;CHECK(!patch.remove(m)&&m.bytes==wrong&&m.writes==n); // Never clobber another hook.
}
alignas(16) unsigned char actual_fp[512];uintptr_t actual_return=0;DWORD actual_ecx=0,actual_edx=0,actual_flags=0,actual_index=0,actual_primary=0;
__declspec(naked) void original_fixture(){__asm{
 mov actual_ecx,ecx
 mov actual_edx,edx
 mov eax,[esp]
 mov actual_return,eax
 mov eax,[esp+4]
 mov actual_index,eax
 mov eax,[esp+8]
 mov actual_primary,eax
 pushfd
 pop eax
 mov actual_flags,eax
 fxsave actual_fp
 mov eax,012345678h
 ret 8
}}
struct NativeMemory:PatchMemory {
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
 bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
};
void native_bridge(){
 // Synthetic executable memory, never the game: same CALL + thiscall tail-return ABI.
 auto code=static_cast<unsigned char*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(code);
 const unsigned char prefix[]={0x6a,0x01,0x6a,0x03,0xb9,0x05,0,0,0,0xba,0x78,0x56,0x34,0x12,0xf9,0xe8,0,0,0,0,0xc3};
 std::memcpy(code,prefix,sizeof(prefix));uint32_t relative=static_cast<uint32_t>(reinterpret_cast<uintptr_t>(&original_fixture)-reinterpret_cast<uintptr_t>(code+20));std::memcpy(code+16,&relative,4);
 std::array<unsigned char,5> expected{};std::memcpy(expected.data(),code+15,5);DWORD old=0;CHECK(VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old));
 NativeMemory m;CallPatch patch;detail::original_submit=reinterpret_cast<uintptr_t>(&original_fixture);
 CHECK(patch.install(m,code+15,reinterpret_cast<uintptr_t>(&detail::submit_bridge),expected));
 alignas(16) unsigned char host[512],before[512];auto function=reinterpret_cast<DWORD(__cdecl*)()>(code);
 __asm {
  fxsave host
  fninit
  fld1
  fldpi
  fxsave before
 }
 auto result=function();
 __asm {fxrstor host}
 CHECK(result==0x12345678&&actual_ecx==5&&actual_edx==0x12345678&&actual_index==3&&actual_primary==1&&actual_return==reinterpret_cast<uintptr_t>(code+20)&&(actual_flags&1));
 // Compare environment and all register payloads; reserved bytes are architecturally unspecified.
 CHECK(std::memcmp(before,actual_fp,5)==0&&std::memcmp(before+6,actual_fp+6,8)==0&&std::memcmp(before+16,actual_fp+16,6)==0&&std::memcmp(before+24,actual_fp+24,8)==0);
 for(int i=0;i<8;++i)CHECK(std::memcmp(before+32+i*16,actual_fp+32+i*16,10)==0);
 CHECK(std::memcmp(before+160,actual_fp+160,128)==0); // x86 has eight XMM registers.
 CHECK(patch.remove(m)&&!patch.installed()&&std::memcmp(code+15,expected.data(),5)==0);CHECK(VirtualFree(code,0,MEM_RELEASE));detail::original_submit=0;
}
int main(){try{frustum();failures();native_bridge();std::cout<<"FOV/CPU planes / preview / rotated-lookback / frame restore / exact CALL failure rollback / native x86 ABI and FPU preservation: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
