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
// SPLIT-GRASS1: per-pass world proofs of a two-camera split-screen frame.
constexpr D3DVIEWPORT8 kTop{0,0,640,238,0.f,1.f},kBottom{0,240,640,238,0.f,1.f},kFull{0,0,640,480,0.f,1.f};
void prove(CourseSplitProof& p,uint32_t camera,const D3DVIEWPORT8& viewport){
 auto* pass=p.begin_pass(10,2,3,4,5,camera);CHECK(pass!=nullptr);if(!pass)return;
 pass->view_site=pass->projection_site=pass->world_draw=true;pass->viewport=viewport;}
CourseSplitAdmission split_valid(){CourseSplitAdmission a;
 a.supported_build=a.render_thread=a.scene_active=a.asset_ready=a.ui_callsite=a.ui_consumer=true;
 a.race_valid=a.split_certificate=a.native_dependency_states=true;a.course="RaceTest/Turkey2";
 a.frame=10;a.device=2;a.reset=3;a.race=4;a.owner=5;a.camera=7;a.target_width=640;a.target_height=480;
 a.target_matches={true,true};a.depth_matches={true,true};a.pc_depth_convention={true,true};return a;}
bool eligible(const CourseSplitAdmission& a,const CourseSplitProof& p){return !std::strcmp(course_split_admission(a,p,"RaceTest/Turkey2"),"eligible");}
void split_passes(){
 CourseSplitProof p;CHECK(p.count==0&&!p.current_pass());
 auto* first=p.begin_pass(10,2,3,4,5,7);CHECK(first==&p.passes[0]&&p.count==1&&p.current_pass()==first&&first->camera==7);
 first->view_site=first->projection_site=true;
 auto* second=p.begin_pass(10,2,3,4,5,8);CHECK(second==&p.passes[1]&&p.count==2&&p.current==1&&second->camera==8);
 CHECK(!second->view_site&&!second->projection_site&&first->view_site); // Camera 2 starts its own proof.
 CHECK(p.begin_pass(10,2,3,4,5,7)==first&&p.current==0&&first->view_site&&p.count==2); // Re-selected, not reopened.
 CHECK(p.begin_pass(10,2,3,4,5,9)==nullptr&&p.count==0&&p.frame==UINT64_MAX&&!p.passes[0].camera); // Third camera.
 for(int i=0;i<5;++i){CourseSplitProof q;prove(q,7,kTop);prove(q,8,kBottom);CHECK(q.count==2);
  CourseWorldPass* reopened=nullptr;switch(i){ // Any new frame/device/reset/race/owner starts over.
  case 0:reopened=q.begin_pass(11,2,3,4,5,7);break;case 1:reopened=q.begin_pass(10,9,3,4,5,7);break;
  case 2:reopened=q.begin_pass(10,2,9,4,5,7);break;case 3:reopened=q.begin_pass(10,2,3,9,5,7);break;
  case 4:reopened=q.begin_pass(10,2,3,4,9,7);break;}
  CHECK(reopened==&q.passes[0]&&q.count==1&&!reopened->world_draw&&!reopened->view_site&&!q.passes[1].camera);}
 for(int i=0;i<4;++i){CourseSplitProof q;prove(q,7,kTop);
  CourseWorldPass* r=i==0?q.begin_pass(10,2,3,4,5,0):i==1?q.begin_pass(10,0,3,4,5,7):i==2?q.begin_pass(10,2,3,0,5,7):q.begin_pass(10,2,3,4,0,7);
  CHECK(!r&&q.count==0);}
 // Render-target / Z-clear hooks call proof.invalidate_depth(); BeginScene/EndScene call proof.clear().
 CourseWorldProof w;prove(w.split,7,kTop);prove(w.split,8,kBottom);w.split.projection_site=true;
 w.invalidate_single_depth();CHECK(w.split.passes[0].world_draw&&w.split.passes[1].world_draw);
 w.clear_single();CHECK(w.split.count==2&&w.split.projection_site);
 w.invalidate_depth();CHECK(!w.split.passes[0].world_draw&&!w.split.passes[1].world_draw&&w.split.passes[0].view_site&&w.split.count==2);
 w.clear();CHECK(w.split.count==0&&!w.split.projection_site&&!w.split.passes[0].camera&&w.frame==UINT64_MAX);
}
void split_viewports(){
 CHECK(course_split_viewport(kTop,640,480)&&course_split_viewport(kBottom,640,480)&&course_split_viewport(kFull,640,480));
 CHECK(course_viewports_disjoint(kTop,kBottom)&&course_viewports_disjoint(kBottom,kTop));
 CHECK(!course_viewports_disjoint(kTop,kFull)&&!course_viewports_disjoint(kTop,kTop));
 D3DVIEWPORT8 v=kBottom;v.Height=241;CHECK(!course_split_viewport(v,640,480));
 v=kBottom;v.Y=480;v.Height=1;CHECK(!course_split_viewport(v,640,480));
 v=kTop;v.Width=0;CHECK(!course_split_viewport(v,640,480));
 v=kTop;v.MinZ=.5f;CHECK(!course_split_viewport(v,640,480));
 v=kTop;v.MaxZ=.5f;CHECK(!course_split_viewport(v,640,480));
 v=kTop;v.X=0xffffffffu;CHECK(!course_split_viewport(v,640,480));
 v=kTop;v.Width=0xffffffffu;CHECK(!course_split_viewport(v,640,480)); // No unsigned wrap.
 v=kTop;v.Height=241;CHECK(!course_viewports_disjoint(v,kBottom));
}
void split_admission(){
 CourseSplitProof p;prove(p,7,kTop);prove(p,8,kBottom);
 CHECK(eligible(split_valid(),p));
 {auto a=split_valid();a.camera=8;CHECK(eligible(a,p));} // Either pass camera may be bound at the UI.
 {auto a=split_valid();a.camera=9;CHECK(!std::strcmp(course_split_admission(a,p,"RaceTest/Turkey2"),"split_ui_camera_not_a_pass"));}
 {auto a=split_valid();a.course="racetest/TURKEY2";CHECK(eligible(a,p));}
 for(auto key:{&CourseSplitAdmission::supported_build,&CourseSplitAdmission::render_thread,&CourseSplitAdmission::scene_active,
    &CourseSplitAdmission::asset_ready,&CourseSplitAdmission::ui_callsite,&CourseSplitAdmission::ui_consumer,
    &CourseSplitAdmission::race_valid,&CourseSplitAdmission::split_certificate,&CourseSplitAdmission::native_dependency_states}){
    auto a=split_valid();a.*key=false;CHECK(!eligible(a,p));}
 {auto a=split_valid();a.state_block_recording=true;CHECK(!eligible(a,p));}
 for(int i=0;i<12;++i){auto a=split_valid();switch(i){case 0:a.course="RaceTest/France1";break;case 1:++a.frame;break;
    case 2:++a.device;break;case 3:++a.reset;break;case 4:++a.race;break;case 5:++a.owner;break;case 6:a.camera=0;break;
    case 7:a.device=0;break;case 8:a.race=0;break;case 9:a.owner=0;break;case 10:a.target_width=320;break;case 11:a.target_height=400;break;}
    CHECK(!eligible(a,p));}
 for(size_t i=0;i<2;++i)for(int k=0;k<3;++k){auto a=split_valid();
    (k==0?a.target_matches:k==1?a.depth_matches:a.pc_depth_convention)[i]=false;CHECK(!eligible(a,p));}
 for(size_t i=0;i<2;++i)for(int k=0;k<3;++k){CourseSplitProof q;prove(q,7,kTop);prove(q,8,kBottom);
    auto& pass=q.passes[i];(k==0?pass.view_site:k==1?pass.projection_site:pass.world_draw)=false;
    CHECK(!eligible(split_valid(),q));}
 {CourseSplitProof one;prove(one,7,kTop);CHECK(!std::strcmp(course_split_admission(split_valid(),one,"RaceTest/Turkey2"),"split_two_camera_passes_missing"));}
 {CourseSplitProof q;prove(q,7,kTop);prove(q,8,kBottom);q.passes[1].camera=7; // Duplicate camera cannot stand in for pass 2.
  CHECK(!eligible(split_valid(),q));}
 {CourseSplitProof q;prove(q,7,kTop);prove(q,8,kFull);CHECK(!std::strcmp(course_split_admission(split_valid(),q,"RaceTest/Turkey2"),"split_viewports_overlap"));}
 {CourseSplitProof q;prove(q,7,kTop);prove(q,8,kTop);CHECK(!eligible(split_valid(),q));}
 {CourseSplitProof q;prove(q,7,kTop);D3DVIEWPORT8 off=kBottom;off.Height=300;prove(q,8,off);CHECK(!eligible(split_valid(),q));}
 {CourseSplitProof q;CHECK(!eligible(split_valid(),q));}
 // The single-camera admission is untouched and still refuses a half viewport proof via its own fields.
 auto single=valid();CHECK(!std::strcmp(course_object_admission(single),"eligible"));
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
int main(){admission();menu_preflight();split_passes();split_viewports();split_admission();defaults_and_asset();if(failures)return 1;std::cout<<"Course identity/frame/target gates, menu preflight, Stock, resource lifecycle: PASS\n";return 0;}
