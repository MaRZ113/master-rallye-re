#include "course_objects.hpp"
#include "ps2_port_extension.hpp"
#include <iostream>
#include <cstring>
using namespace gfx2;using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
namespace {
CourseAdmission valid(){CourseAdmission a;a.supported_build=a.render_thread=a.scene_active=a.asset_ready=true;
 a.ui_callsite=a.ui_consumer=a.camera_single=a.race_valid=true;a.view_site=a.projection_site=a.world_draw=true;
 a.target_matches=a.depth_matches=a.viewport_matches=a.pc_depth_convention=a.native_dependency_states=true;
 a.course="RaceTest/Turkey3";a.frame=a.proof_frame=1;a.device=a.proof_device=2;
 a.reset=a.proof_reset=3;a.race=a.proof_race=4;a.owner=a.proof_owner=5;a.camera=a.proof_camera=6;return a;}
void admission(){auto a=valid();CHECK(!std::strcmp(course_object_admission(a),"eligible"));
 auto recording=valid();recording.state_block_recording=true;CHECK(std::strcmp(course_object_admission(recording),"eligible"));
 CHECK(turkey3_course("racetest/TURKEY3"));CHECK(!turkey3_course("RaceTest/Turkey3_extra"));
 for(auto key:{&CourseAdmission::supported_build,&CourseAdmission::render_thread,&CourseAdmission::scene_active,
    &CourseAdmission::asset_ready,&CourseAdmission::ui_callsite,&CourseAdmission::ui_consumer,&CourseAdmission::camera_single,
    &CourseAdmission::race_valid,&CourseAdmission::view_site,&CourseAdmission::projection_site,&CourseAdmission::world_draw,
    &CourseAdmission::target_matches,&CourseAdmission::depth_matches,&CourseAdmission::viewport_matches,
    &CourseAdmission::pc_depth_convention,&CourseAdmission::native_dependency_states}){
    auto b=valid();b.*key=false;CHECK(std::strcmp(course_object_admission(b),"eligible"));}
 for(int i=0;i<8;++i){auto b=valid();switch(i){case 0:b.course="RaceTest/France1";break;case 1:++b.frame;break;
    case 2:++b.device;break;case 3:++b.reset;break;case 4:++b.race;break;case 5:++b.owner;break;
    case 6:++b.camera;break;case 7:b.camera=0;break;}CHECK(std::strcmp(course_object_admission(b),"eligible"));}
}
void menu_preflight(){
 CourseWorldProof p;CourseBoundaryContext c{10,2,3,true,true,true,false};
 int broker_reads=0,gpu_reads=0;
 auto enter=[&](){if(!course_world_preflight(p,c))return; ++broker_reads;++gpu_reads;};
 for(int i=0;i<10000;++i)enter();CHECK(broker_reads==0&&gpu_reads==0);
 p.frame=10;p.device=2;p.reset=3;p.race=4;p.owner=5;p.camera=6;
 p.view_site=p.projection_site=p.world_draw=true;CHECK(course_world_preflight(p,c));enter();
 CHECK(broker_reads==1&&gpu_reads==1);
 for(int i=0;i<11;++i){auto old=c;switch(i){
 case 0:c.frame++;break;case 1:c.device++;break;case 2:c.reset++;break;
 case 3:c.render_thread=false;break;case 4:c.scene_active=false;break;
 case 5:c.ui_consumer=false;break;case 6:c.state_block_recording=true;break;
 case 7:p.view_site=false;break;case 8:p.projection_site=false;break;
 case 9:p.world_draw=false;break;case 10:p.owner=0;break;}
 CHECK(!course_world_preflight(p,c));enter();CHECK(broker_reads==1&&gpu_reads==1);
 c=old;p.view_site=p.projection_site=p.world_draw=true;p.owner=5;}
 p.clear();enter();CHECK(broker_reads==1&&gpu_reads==1);
}
class Texture:public IDirect3DTexture8{
public:ULONG refs=1;DWORD pixels[4096]{};
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** o)override{*o=this;AddRef();return S_OK;}
 ULONG STDMETHODCALLTYPE AddRef()override{return ++refs;}ULONG STDMETHODCALLTYPE Release()override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID)override{return E_NOTIMPL;}
 DWORD STDMETHODCALLTYPE SetPriority(DWORD)override{return 0;}DWORD STDMETHODCALLTYPE GetPriority()override{return 0;}
 void STDMETHODCALLTYPE PreLoad()override{}D3DRESOURCETYPE STDMETHODCALLTYPE GetType()override{return D3DRTYPE_TEXTURE;}
 DWORD STDMETHODCALLTYPE SetLOD(DWORD)override{return 0;}DWORD STDMETHODCALLTYPE GetLOD()override{return 0;}
 DWORD STDMETHODCALLTYPE GetLevelCount()override{return 1;}
 HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC*)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* p,const RECT*,DWORD)override{p->Pitch=256;p->pBits=pixels;return S_OK;}
 HRESULT STDMETHODCALLTYPE UnlockRect(UINT)override{return S_OK;}
 HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*)override{return S_OK;}
};
struct Native:MockDeviceBase{Texture image;int creates=0;
 HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* caps)override{*caps={};caps->MaxTextureWidth=caps->MaxTextureHeight=64;caps->MaxPrimitiveCount=1000;return S_OK;}
 HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT f,D3DPOOL pool,IDirect3DTexture8** o)override{
    CHECK(w==64&&h==64&&levels==1&&!usage&&f==D3DFMT_A8R8G8B8&&pool==D3DPOOL_MANAGED);
    ++creates;image.refs=1;*o=&image;return S_OK;}
};
void defaults_and_asset(){Native n;CourseObjectsPilot stock(false,L"");CHECK(!stock.requested()&&!stock.active()&&!stock.initialize(n)&&n.creates==0);
 wchar_t directory[MAX_PATH]{},ini[MAX_PATH]{},asset[32768]{};CHECK(GetTempPathW(MAX_PATH,directory));CHECK(GetTempFileNameW(directory,L"obj",0,ini));
 CourseObjectsPilot absent(true,ini);CHECK(!absent.requested()&&!absent.active()&&!absent.initialize(n));
 CHECK(WritePrivateProfileStringW(L"PS2Port",L"CourseObjectsMode",L"1garbage",ini));
 CourseObjectsPilot bad(true,ini);CHECK(!bad.requested());
 CHECK(WritePrivateProfileStringW(L"PS2Port",L"CourseObjectsMode",L"1",ini));
 CourseObjectsPilot missing(true,ini);CHECK(missing.requested()&&!missing.identity_requested()&&!missing.active());
 const auto length=GetEnvironmentVariableW(L"MRR_COURSE_OBJECT_TEST_ASSET",asset,32768);
 if(length&&length<32768){
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"CourseObjectsAsset",asset,ini));CourseObjectsPilot enabled(true,ini);
    CHECK(enabled.requested()&&enabled.identity_requested()&&enabled.initialize(n)&&enabled.active());
    CHECK(enabled.asset().meshes.size()==17&&enabled.asset().vertices.size()==2235);
    CHECK(enabled.consume_boundary(1,2,3)&&!enabled.consume_boundary(1,2,3)&&enabled.consume_boundary(2,2,3));
    enabled.before_reset();CHECK(n.image.refs==0&&!enabled.active());enabled.after_reset(n,true,false);CHECK(!enabled.active());
    const auto creates=n.creates;enabled.after_reset(n,false,true);CHECK(!enabled.active()&&n.creates==creates);
    enabled.after_reset(n,true,true);CHECK(enabled.active()&&n.creates==creates+1);
    enabled.shutdown();CHECK(!enabled.active()&&n.image.refs==0);
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"CourseObjectsVersion",L"2",ini));CourseObjectsPilot version(true,ini);CHECK(!version.requested());
    std::cout<<"Canonical local course artifact/lifetime/reset: PASS\n";
 }else{CHECK(length==0);std::cout<<"Canonical course artifact integration: NOT_PERFORMED (set MRR_COURSE_OBJECT_TEST_ASSET)\n";}
 CourseObjectAsset decoded;uint8_t wrong[88]{};CHECK(!decode_course_object_asset(wrong,sizeof(wrong),kTurkey3ObjectArtifactSha,decoded));
 CHECK(DeleteFileW(ini));
}
}
int main(){admission();menu_preflight();defaults_and_asset();if(failures)return 1;std::cout<<"Course identity/frame/target gates, menu preflight, Stock, resource lifecycle: PASS\n";return 0;}
