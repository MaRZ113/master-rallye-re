#include "quality.hpp"
#include "menu_freeze.hpp"
#include "ui_margins.hpp"
#include "margin_rules.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>
#include <cmath>
#include <cstring>
#include <cfenv>
#include <functional>
#define CHECK(x) do {if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
namespace gfx2::detail {struct UiMarginsContract {static void enable(UiMargins& ui){ui.enabled_=true;ui.thread_=GetCurrentThreadId();}};}
struct Windows:WindowApi {
 std::function<void()> on_apply;
 WindowState state{};RECT last{};bool client=false,popup=false,fail=false;bool native_completed=true;unsigned applies=0,restores=0;
 Windows(){state.hwnd=reinterpret_cast<HWND>(0x1234);state.valid=true;state.monitor={1920,0,3840,1080};state.work=state.monitor;state.client={0,0,640,480};state.outer={2000,50,2660,570};state.style=WS_OVERLAPPEDWINDOW;}
 bool snapshot(HWND,WindowState& s) noexcept override{s=state;return true;}
 bool apply(const WindowState&,const RECT& r,bool c,bool p) noexcept override{if(!native_completed)std::terminate();last=r;client=c;popup=p;++applies;if(fail)return false;state.outer=r;state.client={0,0,r.right-r.left,r.bottom-r.top};state.style=p?WS_POPUP:WS_OVERLAPPEDWINDOW;if(on_apply)on_apply();return true;}
 bool restore(const WindowState& saved) noexcept override{++restores;state=saved;return true;}
};
struct Surface:IDirect3DSurface8 {
 D3DSURFACE_DESC desc{};unsigned refs=0;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void**) override{return E_NOINTERFACE;}
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetContainer(REFIID,void**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetDesc(D3DSURFACE_DESC* p) override{*p=desc;return S_OK;}
 HRESULT STDMETHODCALLTYPE LockRect(D3DLOCKED_RECT*,const RECT*,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE UnlockRect() override{return E_NOTIMPL;}
};
struct Device:MockDeviceBase {
 Windows* order=nullptr;
 std::vector<D3DPRESENT_PARAMETERS> resets;HRESULT result=S_OK;bool reject_msaa=false,reject_ui=false;
 D3DVIEWPORT8 viewport{};D3DMATRIX projection{};Surface color,depth;
 HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS* p) override{resets.push_back(*p);if(order)order->native_completed=true;return reject_msaa&&p->MultiSampleType!=D3DMULTISAMPLE_NONE?D3DERR_INVALIDCALL:result;}
 HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT,D3DBACKBUFFER_TYPE,IDirect3DSurface8** p) override{color.AddRef();*p=&color;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetDepthStencilSurface(IDirect3DSurface8** p) override{depth.AddRef();*p=&depth;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{viewport=*p;return result;}
 HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{*p=viewport;return result;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE,const D3DMATRIX* p) override{if(reject_ui&&p->_11!=2.f/640)return D3DERR_INVALIDCALL;projection=*p;return result;}
 HRESULT STDMETHODCALLTYPE Present(const RECT*,const RECT*,HWND,const RGNDATA*) override{return result;}
 HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE,UINT,UINT) override{return result;}
};
struct Root:MockRootBase {
 Windows* order=nullptr;Device dev;std::vector<D3DPRESENT_PARAMETERS> creates;D3DDISPLAYMODE mode{1920,1080,60,D3DFMT_X8R8G8B8};unsigned support=4,depth_support=4;bool windowed_expected=true,modes=true,depth_pair=true;HRESULT result=S_OK;bool reject_msaa=false,reject_display=false;
 HRESULT STDMETHODCALLTYPE GetAdapterDisplayMode(UINT a,D3DDISPLAYMODE* m) override{CHECK(a==2);*m={1920,1080,60,D3DFMT_X8R8G8B8};return S_OK;}
 UINT STDMETHODCALLTYPE GetAdapterModeCount(UINT) override{return modes?1:0;}
 HRESULT STDMETHODCALLTYPE EnumAdapterModes(UINT,UINT,D3DDISPLAYMODE* m) override{*m=mode;return S_OK;}
 HRESULT STDMETHODCALLTYPE CheckDeviceType(UINT a,D3DDEVTYPE t,D3DFORMAT,D3DFORMAT,BOOL) override{CHECK(a==2&&t==D3DDEVTYPE_HAL);return S_OK;}
 HRESULT STDMETHODCALLTYPE CheckDeviceFormat(UINT,D3DDEVTYPE,D3DFORMAT,DWORD usage,D3DRESOURCETYPE,D3DFORMAT) override{CHECK(usage==D3DUSAGE_DEPTHSTENCIL);return S_OK;}
 HRESULT STDMETHODCALLTYPE CheckDepthStencilMatch(UINT,D3DDEVTYPE,D3DFORMAT,D3DFORMAT,D3DFORMAT) override{return depth_pair?S_OK:D3DERR_NOTAVAILABLE;}
 HRESULT STDMETHODCALLTYPE CheckDeviceMultiSampleType(UINT a,D3DDEVTYPE t,D3DFORMAT f,BOOL windowed,D3DMULTISAMPLE_TYPE n) override{CHECK(a==2&&t==D3DDEVTYPE_HAL&&bool(windowed)==windowed_expected);return n<=static_cast<int>(f==D3DFMT_D16?depth_support:support)?S_OK:D3DERR_NOTAVAILABLE;}
 HRESULT STDMETHODCALLTYPE CreateDevice(UINT,D3DDEVTYPE,HWND,DWORD,D3DPRESENT_PARAMETERS* p,IDirect3DDevice8** out) override{creates.push_back(*p);if(order)order->native_completed=true;if(reject_msaa&&p->MultiSampleType!=D3DMULTISAMPLE_NONE)return D3DERR_INVALIDCALL;if(reject_display&&p->BackBufferWidth!=640)return D3DERR_INVALIDCALL;if(FAILED(result))return result;*out=&dev;return S_OK;}
};
D3DPRESENT_PARAMETERS stock(){D3DPRESENT_PARAMETERS p{};p.BackBufferWidth=640;p.BackBufferHeight=480;p.BackBufferFormat=D3DFMT_X8R8G8B8;p.BackBufferCount=1;p.SwapEffect=D3DSWAPEFFECT_COPY;p.hDeviceWindow=reinterpret_cast<HWND>(0x1234);p.Windowed=TRUE;p.EnableAutoDepthStencil=TRUE;p.AutoDepthStencilFormat=D3DFMT_D16;return p;}
void configs(){
 auto c=parse_visual_config({},false);CHECK(c.display_mode=="Stock"&&c.aa_mode=="Stock"&&c.interface_mode=="Stock"&&!c.menu_freeze);
 c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Display.Mode","Borderless"},{"Display.Width","nan"},{"AntiAliasing.Mode","MSAA"},{"AntiAliasing.Samples","8"}},true);CHECK(c.display_mode=="Stock"&&c.aa_mode=="MSAA"&&c.samples==8);
 c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Display.Mode","Windowed"},{"Display.Width","1280"},{"Display.Height","720"},{"Widescreen.InterfaceMode","PreserveMargins"},{"Compatibility.MenuFreezeFix","true"}},true);CHECK(c.width==1280&&c.height==720&&c.interface_mode=="PreserveMargins"&&c.menu_freeze);
 for(auto key:{"Display.Mode","Widescreen.InterfaceMode","AntiAliasing.Mode","Compatibility.MenuFreezeFix"}){auto v=parse_visual_config({{"Renderer.ConfigVersion","1"},{key,"invalid"}},true);CHECK(v.display_mode=="Stock"&&v.interface_mode=="Stock"&&v.aa_mode=="Stock"&&!v.menu_freeze);}
}
void numeric_configs(){
 for(auto entry:std::vector<std::pair<std::string,std::vector<std::string>>>{{"Display.Mode",{"Stock","Windowed","Borderless","ExclusiveFullscreen"}},{"Widescreen.InterfaceMode",{"Stock","Centered4x3","PreserveMargins"}},{"AntiAliasing.Mode",{"Stock","MSAA"}},{"Shadows.Mode",{"Stock","Off"}},{"VehicleReflections.Mode",{"Stock","ViewDependent2D"}}}){
  for(size_t i=0;i<entry.second.size();++i){auto a=parse_visual_config({{"Renderer.ConfigVersion","1"},{entry.first,std::to_string(i)}},true),b=parse_visual_config({{"Renderer.ConfigVersion","1"},{entry.first,entry.second[i]}},true);CHECK(a.display_mode==b.display_mode&&a.interface_mode==b.interface_mode&&a.aa_mode==b.aa_mode&&a.shadow_off==b.shadow_off&&a.reflection_mode==b.reflection_mode);}
  for(auto bad:{"-1","99","1.5","2147483648"}){auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{entry.first,bad},{"Filtering.AnisotropicFiltering","1"}},true);CHECK(c.anisotropy&&c.display_mode=="Stock"&&c.interface_mode=="Stock"&&c.aa_mode=="Stock"&&!c.shadow_off&&c.reflection_mode=="Stock");}
 }
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Display.AutoHideCursor","0"},{"Display.CursorHideDelayMs","2500"},{"Compatibility.MenuFreezeFix","1"}},true);CHECK(!c.auto_hide_cursor&&c.cursor_delay_ms==2500&&c.menu_freeze);
 c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Display.CursorHideDelayMs","-1"}},true);CHECK(!c.auto_hide_cursor&&!c.cursor_reason.empty());
}
void reset_echo_shutdown(){
 Root root;Windows windows;QualityPipeline q(windows);VisualConfig c;auto p=stock();IDirect3DDevice8* out=nullptr;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);CHECK(q.create(root,0,&p,&out)==S_OK);
 c.display_mode="Windowed";c.width=1280;c.height=720;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);
 HRESULT echo=E_FAIL;windows.on_apply=[&](){auto same=stock();echo=q.reset(root,root.dev,&same);CHECK(same.BackBufferWidth==1280);};
 auto input=stock();CHECK(q.reset(root,root.dev,&input)==S_OK&&echo==S_OK&&root.dev.resets.size()==1&&q.window_reset_echoes_suppressed==1&&q.native_reset_calls==1&&q.json().find("\"successful_reset_epoch\":1")!=std::string::npos);
 c.display_mode="Borderless";q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);
 windows.on_apply=[&](){auto different=stock();different.EnableAutoDepthStencil=FALSE;echo=q.reset(root,root.dev,&different);};
 input=stock();CHECK(q.reset(root,root.dev,&input)==S_OK&&echo==D3DERR_INVALIDCALL&&root.dev.resets.size()==2&&q.deferred_resets==1);
 auto accepted=q.effective;root.dev.result=D3DERR_DEVICELOST;input=stock();CHECK(q.reset(root,root.dev,&input)==D3DERR_DEVICELOST&&presentation_equivalent(q.effective,accepted)&&q.json().find("\"successful_reset_epoch\":2")!=std::string::npos);
 auto restores=windows.restores,applies=windows.applies;q.begin_shutdown();q.restore_window();CHECK(windows.restores==restores&&windows.applies==applies);
 auto a=stock(),b=a;CHECK(presentation_equivalent(a,b));b.EnableAutoDepthStencil=FALSE;CHECK(!presentation_equivalent(a,b));b=a;b.Flags=1;CHECK(!presentation_equivalent(a,b));
 Windows final_window;auto policy=std::make_unique<QualityPipeline>(final_window);policy->configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);root.result=S_OK;p=stock();CHECK(policy->create(root,0,&p,&out)==S_OK);auto* parent=new Root8(&root);auto* device=new Device8(&root.dev,parent,std::move(policy));restores=final_window.restores;applies=final_window.applies;device->Release();parent->Release();CHECK(final_window.restores==restores&&final_window.applies==applies);
}
void preview_cursor_packets(){
 for(double aspect:{4./3,16./9,16./10,21./9}){
  D3DMATRIX p{},out{};double y=1/std::tan((45./aspect)*3.14159265358979323846/360.);p._11=float(y/aspect);p._22=float(y);p._33=1.01f;p._34=1;p._43=-.202f;
  CHECK(frontend_preview_projection(p,out)&&std::abs(vertical_fov(out)-33.75)<.001&&std::abs(out._22/out._11-aspect)<.0001&&out._43==p._43&&out._33==p._33);
  CHECK(camera_scene_family(p)==0);auto gameplay=p;gameplay._22=float(1/std::tan((90./aspect)*3.14159265358979323846/360.));gameplay._11=float(gameplay._22/aspect);CHECK(camera_scene_family(gameplay)==1);
  if(aspect==4./3)CHECK(std::abs(out._22-p._22)<.00001);
  auto bad=p;bad._22=1;CHECK(!frontend_preview_projection(bad,out));
 }
 UiMargins diagnostics;diagnostics.capture_window(true,20);CHECK(diagnostics.json().find("\"diagnostic_frames_remaining\":3")!=std::string::npos);for(int i=0;i<3;++i)CHECK(diagnostics.finish_frame());CHECK(diagnostics.json().find("\"diagnostic_frames_remaining\":0")!=std::string::npos);diagnostics.reset_diagnostics();
 CursorIdle cursor;POINT p{10,10};CHECK(cursor.update(true,p,0,1500)==0);CHECK(cursor.update(true,p,1499,1500)==0);CHECK(cursor.update(true,p,1500,1500)==-1&&cursor.hidden);
 for(int i=0;i<100;++i)CHECK(cursor.update(true,p,1501+i,1500)==0);p.x=11;CHECK(cursor.update(true,p,2000,1500)==1&&!cursor.hidden);CHECK(cursor.update(true,p,3500,1500)==-1);CHECK(cursor.update(false,p,3501,1500)==1);CHECK(cursor.update(false,p,9000,1500)==0);CHECK(cursor.update(true,p,9001,1500)==0);

}
void displays(){
 Root root;Windows windows;QualityPipeline q(windows);VisualConfig c;auto p=stock();IDirect3DDevice8* out=nullptr;
 q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);CHECK(q.create(root,0,&p,&out)==S_OK&&root.creates.size()==1&&windows.applies==0&&std::memcmp(&p,&q.requested,sizeof(p))==0);
 c.display_mode="Windowed";c.width=1280;c.height=720;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK);CHECK(p.Windowed&&p.BackBufferWidth==1280&&p.BackBufferHeight==720&&windows.client&&!windows.popup&&windows.last.right-windows.last.left==1280);
 q.restore_window();c.display_mode="Borderless";c.width=c.height=0;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK);CHECK(p.Windowed&&p.BackBufferWidth==1920&&p.BackBufferHeight==1080&&!windows.client&&windows.popup&&windows.last.left==1920&&windows.last.bottom==1080);
 c.display_mode="ExclusiveFullscreen";c.width=1920;c.height=1080;c.refresh=60;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK);CHECK(!p.Windowed&&p.FullScreen_RefreshRateInHz==60);
 c.refresh=75;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==D3DERR_NOTAVAILABLE&&p.Windowed&&p.BackBufferWidth==640&&q.display=="ExclusiveFullscreen");
 c.display_mode="Borderless";q.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);CHECK(q.active()&&q.config.interface_mode=="Stock");
 q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);windows.fail=true;++windows.state.outer.left;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.BackBufferWidth==1920&&q.display=="Borderless"&&q.display_reason=="window_commit_failed_native_parameters_retained"&&windows.restores>0);
}
void display_transactions(){
 Root root;Windows window;QualityPipeline q(window);VisualConfig c;c.display_mode="Borderless";auto p=stock();IDirect3DDevice8* out=nullptr;root.order=&window;root.dev.order=&window;
 q.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);window.native_completed=false;
 auto proposed=q.plan(root,p);CHECK(window.applies==0&&window.restores==0&&proposed.BackBufferWidth==1920);
 root.result=D3DERR_DEVICELOST;CHECK(q.create(root,0,&p,&out)==D3DERR_DEVICELOST&&window.applies==0&&window.restores==0);
 root.result=S_OK;window.native_completed=false;CHECK(q.create(root,0,&p,&out)==S_OK&&window.applies==1);
 auto effective=q.effective;auto applies=window.applies,restores=window.restores;root.dev.result=D3DERR_DEVICELOST;auto input=stock();window.native_completed=false;
 CHECK(q.reset(root,root.dev,&input)==D3DERR_DEVICELOST&&window.applies==applies&&window.restores==restores&&!std::memcmp(&q.effective,&effective,sizeof(effective)));
 root.dev.result=S_OK;window.native_completed=false;CHECK(q.reset(root,root.dev,&input)==S_OK&&window.applies==applies); // same placement: no synchronous window mutation
 c.display_mode="Windowed";c.width=1280;c.height=720;q.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);input=stock();window.native_completed=false;
 CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==1280&&input.BackBufferHeight==720);
 CHECK(q.json().find("\"normal_target\":{\"width\":1280,\"height\":720}")!=std::string::npos);
 // An arbitrary game Reset request without matching normal-client evidence
 // must not replace the configured target.
 input=stock();input.BackBufferWidth=1920;input.BackBufferHeight=1027;window.native_completed=false;
 CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==1280&&input.BackBufferHeight==720&&q.windowed_resize_admissions==0);
 // A real user resize is admitted only when both the HWND client and the
 // game's requested Reset agree, and only after the native Reset succeeds.
 window.state.client={0,0,1500,850};window.state.outer={2100,80,3620,970};input=stock();input.BackBufferWidth=1500;input.BackBufferHeight=850;window.native_completed=false;
 CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==1500&&input.BackBufferHeight==850&&q.windowed_resize_admissions==1);
 CHECK(q.json().find("\"normal_target\":{\"width\":1500,\"height\":850}")!=std::string::npos);
 for(const auto& size:std::vector<std::pair<UINT,UINT>>{{1734,920},{1024,768}}){
  window.state.client={0,0,static_cast<LONG>(size.first),static_cast<LONG>(size.second)};window.state.outer.left+=17;window.state.outer.right=window.state.outer.left+static_cast<LONG>(size.first+20);
  input=stock();input.BackBufferWidth=size.first;input.BackBufferHeight=size.second;window.native_completed=false;
  CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==size.first&&input.BackBufferHeight==size.second);
 }
 CHECK(q.windowed_resize_admissions==3&&q.json().find("\"normal_target\":{\"width\":1024,\"height\":768}")!=std::string::npos);
 // Moving a normal window without resizing accepts OS placement and does not
 // recenter or alter the normal client target.
 auto placements=window.applies;window.state.outer.left+=80;window.state.outer.right+=80;input=stock();window.native_completed=false;
 CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==1024&&input.BackBufferHeight==768&&window.applies==placements);
 // Minimize/zero-client resets keep the last normal target and never adopt 0x0.
 window.state.minimized=true;window.state.client={0,0,0,0};input=stock();window.native_completed=false;
 CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==1024&&input.BackBufferHeight==768&&q.windowed_resize_admissions==3);
 window.state.minimized=false;window.state.client={0,0,1024,768};window.native_completed=false;
 c.width=c.height=0;q.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);input=stock();CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==640);
 input=stock();input.BackBufferWidth=1920;input.BackBufferHeight=1027;CHECK(q.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==640&&input.BackBufferHeight==480);
 QualityPipeline auto_invalid(window);auto_invalid.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);input=stock();input.BackBufferWidth=20000;CHECK(auto_invalid.plan(root,input).BackBufferWidth==20000&&auto_invalid.display=="Stock");
 input=stock();CHECK(auto_invalid.reset(root,root.dev,&input)==S_OK&&input.BackBufferWidth==640); // invalid initial auto request never pins
 c.display_mode="Stock";c.aa_mode="Stock";c.samples=4;q.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);CHECK(q.aa_reason=="Mode_Stock_Samples_ignored");
 std::cout<<"Display plan/native/commit/failure/idempotence and corroborated Windowed resize ownership: PASS\n";
}
void windowed_live_resize(){
 Root root;Windows window;QualityPipeline q(window);VisualConfig c;c.display_mode="Windowed";c.width=1280;c.height=720;
 auto p=stock();IDirect3DDevice8* out=nullptr;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);
 CHECK(q.create(root,0,&p,&out)==S_OK&&p.BackBufferWidth==1280&&p.BackBufferHeight==720);
 auto applies=window.applies;
 // A normal-window resize followed by an exactly matching game Reset updates
 // the target only on success and leaves the OS-owned rectangle in place.
 window.state.client={0,0,1512,864};window.state.outer={1960,10,3492,914};p=stock();p.BackBufferWidth=1512;p.BackBufferHeight=864;
 CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1512&&p.BackBufferHeight==864&&window.applies==applies&&q.windowed_resize_admissions==1);
 // Since this Reset already requests the actual client size, the game-owned
 // viewport domain remains native; effective aspect follows the new size.
 CHECK(q.json().find("\"effective_aspect\":1.75")!=std::string::npos&&q.json().find("\"virtual_width\":840")!=std::string::npos);
 // A later live resize whose native Reset fails must not replace the target.
 window.state.client={0,0,1600,900};p=stock();p.BackBufferWidth=1600;p.BackBufferHeight=900;root.dev.result=D3DERR_DEVICELOST;
 CHECK(q.reset(root,root.dev,&p)==D3DERR_DEVICELOST&&q.windowed_resize_admissions==1&&q.json().find("\"normal_target\":{\"width\":1512,\"height\":864}")!=std::string::npos);
 root.dev.result=S_OK;
 // Restore to the last accepted normal target even when Reset echoes the
 // previous maximized dimensions.
 window.state.maximized=true;window.state.client={0,0,1900,1030};window.state.outer=window.state.work;p=stock();p.BackBufferWidth=1900;p.BackBufferHeight=1030;
 CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1900&&p.BackBufferHeight==1030);
 window.state.maximized=false;window.state.client={0,0,1512,864};window.state.outer={1960,10,3492,914};p=stock();p.BackBufferWidth=1900;p.BackBufferHeight=1030;
 CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1512&&p.BackBufferHeight==864&&window.applies==applies);
 // Width=Height=0 adopts the first game size, then admits subsequent live
 // resize only when the engine request matches the normal HWND client.
 Root auto_root;Windows auto_window;QualityPipeline automatic(auto_window);VisualConfig auto_config;auto_config.display_mode="Windowed";
 auto_config.width=auto_config.height=0;p=stock();p.BackBufferWidth=800;p.BackBufferHeight=600;automatic.configure(auto_config,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);
 CHECK(automatic.create(auto_root,0,&p,&out)==S_OK&&p.BackBufferWidth==800&&p.BackBufferHeight==600);
 auto_window.state.client={0,0,1024,768};p=stock();p.BackBufferWidth=1024;p.BackBufferHeight=768;
 CHECK(automatic.reset(auto_root,auto_root.dev,&p)==S_OK&&p.BackBufferWidth==1024&&p.BackBufferHeight==768&&automatic.windowed_resize_admissions==1);
 std::cout<<"Windowed live resize admission is corroborated and success-gated: PASS\n";
}
void windowed_maximize_restore(){
 Root root;Windows window;QualityPipeline q(window);VisualConfig c;c.display_mode="Windowed";c.width=1280;c.height=720;
 auto p=stock();IDirect3DDevice8* out=nullptr;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);
 CHECK(q.create(root,0,&p,&out)==S_OK&&p.BackBufferWidth==1280&&p.BackBufferHeight==720);
 CHECK(q.json().find("\"window_state\":\"normal\"")!=std::string::npos);
 for(int round=0;round<3;++round){
  auto applies=window.applies;auto resets=root.dev.resets.size();auto echoes=q.window_reset_echoes;
  window.state.maximized=true;window.state.client={0,0,1900,1027};window.state.outer=window.state.work;
  p=stock();p.BackBufferWidth=1900;p.BackBufferHeight=1027;
  CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1900&&p.BackBufferHeight==1027&&p.EnableAutoDepthStencil);
  CHECK(root.dev.resets.size()==resets+1&&window.applies==applies&&q.window_reset_echoes==echoes&&!q.window_commit_active());
  CHECK(q.json().find("\"normal_target\":{\"width\":1280,\"height\":720}")!=std::string::npos&&q.json().find("\"window_state\":\"maximized\"")!=std::string::npos);
  // Legacy logical viewport scales to the accepted maximized backbuffer.
  p=stock();CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1900&&window.applies==applies);
  D3DVIEWPORT8 in{0,0,640,480,0,1},scaled{};CHECK(q.viewport(in,scaled)&&scaled.Width==1900&&scaled.Height==1027);
  auto accepted=q.effective;root.dev.result=D3DERR_DEVICELOST;p=stock();CHECK(q.reset(root,root.dev,&p)==D3DERR_DEVICELOST&&presentation_equivalent(q.effective,accepted)&&window.applies==applies);root.dev.result=S_OK;
  window.state.maximized=false;window.state.client={0,0,1280,720};window.state.outer={2000,50,3280,770};
  p=stock();p.BackBufferWidth=1900;p.BackBufferHeight=1027;CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1280&&p.BackBufferHeight==720&&window.applies==applies);
  CHECK(q.json().find("\"window_state\":\"normal\"")!=std::string::npos);
 }
 // Genuine maximize uses actual client dimensions, never a bogus game Reset size.
 window.state.maximized=true;window.state.client={0,0,1880,1000};p=stock();p.BackBufferWidth=9000;CHECK(q.reset(root,root.dev,&p)==S_OK&&p.BackBufferWidth==1880&&p.BackBufferHeight==1000);
 std::cout<<"Windowed normal/maximize/restore, no placement mutation or echo swallow, fixed normal target: PASS\n";
}
void stable_margin_anchors(){
 for(int direction:{-1,1}){
  MarginAnchors anchors;float point[3]{direction>0?565.f:23.f,direction>0?75.f:370.f,0};
  MarginIdentity key{1,2,reinterpret_cast<uintptr_t>(point),3,1};uint64_t id=0;float last_engine=0,last_effective=0;
  for(int frame=0;frame<20;++frame){
   if(frame){point[0]=(direction>0?565.f:23.f)-3.f*frame;point[1]=(direction>0?75.f:370.f)+frame*.125f;}
   float engine=point[0];auto proof=anchors.resolve(key,point[0],point[1],point[2]);
   CHECK(proof.direction==direction&&(frame?proof.retained:proof.admitted));if(!frame)id=proof.id;CHECK(proof.id==id);
   float effective=engine+direction*100;
   if(frame)CHECK(effective-last_effective==engine-last_engine);
   auto duplicate=anchors.resolve(key,point[0],point[1],point[2]);CHECK(duplicate.id==id&&effective==point[0]+direction*100);
   last_engine=engine;last_effective=effective;CHECK(point[0]==engine);anchors.next_frame();
  }
  CHECK(anchors.admissions==1&&anchors.retained_anchor_without_current_rule_match>0&&anchors.size()==1);
 }
 MarginAnchors anchors;MarginIdentity key{1,2,3,4,1};
 CHECK(anchors.resolve(key,565,75,0).admitted);auto replacement=key;replacement.packet=5;
 CHECK(!anchors.resolve(replacement,300,300,0).direction&&anchors.size()==0);
 CHECK(anchors.resolve(key,565,75,0).admitted);replacement=key;replacement.mode=2;
 CHECK(!anchors.resolve(replacement,300,300,0).direction&&anchors.size()==0);
 CHECK(anchors.resolve(key,565,75,0).admitted);replacement=key;replacement.storage=6;
 CHECK(!anchors.resolve(replacement,300,300,0).direction&&anchors.size()==0);
 CHECK(anchors.resolve(key,565,75,0).admitted);replacement=key;replacement.point=7;
 CHECK(!anchors.resolve(replacement,300,300,0).direction&&anchors.size()==0);
 CHECK(anchors.resolve(key,565,75,0).admitted);anchors.begin_epoch("Reset");CHECK(!anchors.resolve(key,300,300,0).direction&&anchors.size()==0);
 anchors.scene_context(false);CHECK(anchors.resolve(key,565,75,0).admitted);auto epoch=anchors.epoch();anchors.scene_context(true);
 CHECK(anchors.epoch()==epoch+1&&!anchors.resolve(key,300,300,0).direction);
 CHECK(anchors.resolve(key,565,75,0).admitted);anchors.next_frame();
 for(uint64_t i=0;i<=MARGIN_ANCHOR_GRACE_FRAMES;++i)anchors.next_frame();
 CHECK(!anchors.resolve(key,300,300,0).direction&&anchors.size()==0&&anchors.grace_expired==1);
 for(int i=0;i<20;++i){CHECK(!anchors.resolve(key,300+i,300+i,0).direction);anchors.next_frame();}
 CHECK(anchors.resolve(key,565,75,0).admitted);CHECK(!anchors.resolve(key,560,74,1).direction&&anchors.size()==0);
 key.storage=0;CHECK(!anchors.resolve(key,565,75,0).direction);key.storage=4;
 MarginAnchors capacity;for(uintptr_t i=1;i<=512;++i){auto k=key;k.entity=i;CHECK(capacity.resolve(k,565,75,0).admitted);}key.entity=513;CHECK(!capacity.resolve(key,565,75,0).direction&&capacity.overflow==1);
 // Read the same production identity/layout and protect mode changes on restore.
 alignas(float) std::array<unsigned char,0x90> packet{};std::array<unsigned char,0x60> entity{};uintptr_t pp=reinterpret_cast<uintptr_t>(packet.data()),storage=0x1234;uint32_t mode=1;
 std::memcpy(entity.data()+0x4c,&pp,4);std::memcpy(packet.data()+8,&storage,4);std::memcpy(packet.data()+0x68,&mode,4);
 auto* point=reinterpret_cast<float*>(packet.data()+0x54);point[0]=565;point[1]=75;MarginIdentity read{};auto owner=reinterpret_cast<uintptr_t>(entity.data());CHECK(read_margin_identity(owner,pp+0x24,read)&&read.point==pp+0x54&&read.storage==storage&&read.mode==mode);
 CHECK(!read_margin_identity(1,1,read));
 std::cout<<"Historical admission/stable animated anchors, center exclusion, replacement/epoch/gap/overflow and no double offset: PASS\n";
}
void margin_short_grace(){
 const MarginIdentity key{1,2,3,4,1};
 for(uint64_t gap=0;gap<=MARGIN_ANCHOR_GRACE_FRAMES;++gap){
  MarginAnchors a;auto first=a.resolve(key,565,75,0);a.next_frame();
  for(uint64_t i=0;i<gap;++i)a.next_frame();
  auto retained=a.resolve(key,558,76,0);CHECK(retained.id==first.id&&retained.direction==1&&retained.retained);
  CHECK(retained.grace_retained==(gap>0)&&a.anchor_grace_retained==(gap>0?1:0));
 }
 MarginAnchors a;auto first=a.resolve(key,565,75,0);a.next_frame();
 // Conditional every-other-frame submission survives repeatedly, without refreshing coordinates.
 for(int i=0;i<20;++i){a.next_frame();auto d=a.resolve(key,558-i,76+i,0);CHECK(d.id==first.id&&d.grace_retained);a.next_frame();}
 CHECK(a.anchor_grace_retained==20&&a.grace_expired==0);
 a.next_frame();a.begin_epoch("Reset");CHECK(!a.resolve(key,300,300,0).direction);
 a.resolve(key,565,75,0);a.next_frame();a.next_frame();auto replaced=key;replaced.storage=9;
 CHECK(!a.resolve(replaced,300,300,0).direction&&a.size()==0);
 a.resolve(key,565,75,0);a.scene_context(false);a.next_frame();a.next_frame();a.scene_context(true);
 CHECK(!a.resolve(key,300,300,0).direction);
 a.resolve(key,565,75,0);a.next_frame();a.next_frame();a.reject(key.entity);CHECK(!a.resolve(key,300,300,0).direction);
 std::cout<<"Two absent completed frames survive; expiry, Reset/storage/context/reject override grace: PASS\n";
}
void trace_numeric_configs(){
 wchar_t temp[MAX_PATH],file[MAX_PATH];CHECK(GetTempPathW(MAX_PATH,temp)&&GetTempFileNameW(temp,L"gfx",0,file));
 CHECK(DeleteFileW(file));auto defaults=read_trace_config(file);CHECK(defaults.enabled&&defaults.summaries);
 for(auto pair:std::vector<std::pair<const wchar_t*,bool>>{{L"0",false},{L"1",true},{L"false",false},{L"true",true},{L"TRUE",true}}){
  CHECK(WritePrivateProfileStringW(L"Trace",L"Enabled",pair.first,file));CHECK(WritePrivateProfileStringW(L"Trace",L"FrameSummaries",pair.first,file));
  auto c=read_trace_config(file);CHECK(c.enabled_valid&&c.summaries_valid&&c.enabled==pair.second&&c.summaries==pair.second);
 }
 for(auto bad:{L"97",L"-1",L"1.5",L"invalid"}){
  CHECK(WritePrivateProfileStringW(L"Trace",L"Enabled",bad,file));CHECK(WritePrivateProfileStringW(L"Trace",L"FrameSummaries",L"1",file));auto c=read_trace_config(file);CHECK(!c.enabled&&!c.enabled_valid&&c.summaries&&c.summaries_valid);
  CHECK(WritePrivateProfileStringW(L"Trace",L"Enabled",L"1",file));CHECK(WritePrivateProfileStringW(L"Trace",L"FrameSummaries",bad,file));c=read_trace_config(file);CHECK(c.enabled&&c.enabled_valid&&!c.summaries&&!c.summaries_valid);
 }
 CHECK(DeleteFileW(file));
 for(auto key:{"Filtering.AnisotropicFiltering","Camera.GameplayFOV","Display.AutoHideCursor","Compatibility.MenuFreezeFix"}){
  for(auto value:{"0","1","false","true"}){auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{key,value}},true);bool expected=std::string(value)=="1"||std::string(value)=="true";CHECK((std::string(key)=="Filtering.AnisotropicFiltering"?c.anisotropy:std::string(key)=="Camera.GameplayFOV"?c.fov:std::string(key)=="Display.AutoHideCursor"?c.auto_hide_cursor:c.menu_freeze)==expected);}
  auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{key,"97"},{"AntiAliasing.Mode","1"}},true);CHECK(c.aa_mode=="MSAA");CHECK(!(std::string(key)=="Filtering.AnisotropicFiltering"?c.anisotropy:std::string(key)=="Camera.GameplayFOV"?c.fov:std::string(key)=="Display.AutoHideCursor"?c.auto_hide_cursor:c.menu_freeze));
 }
}
struct UiNative:MockDeviceBase {
 D3DMATRIX world{};unsigned sets=0,draws=0;unsigned fail_set=0;HRESULT get_hr=S_OK,draw_hr=S_OK;float observed=0;
 UiNative(){world._11=world._22=world._33=world._44=1;}
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE type,D3DMATRIX* p) override {CHECK(type==D3DTS_WORLD);if(SUCCEEDED(get_hr))*p=world;return get_hr;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* p) override {CHECK(type==D3DTS_WORLD);if(++sets==fail_set)return D3DERR_DEVICELOST;world=*p;return S_OK;}
 HRESULT STDMETHODCALLTYPE Present(const RECT*,const RECT*,HWND,const RGNDATA*) override {return S_OK;}
 HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE,UINT,UINT) override {++draws;observed=world._41;return draw_hr;}
};
struct UiFixture {
 alignas(float) std::array<unsigned char,0x90> packet{};std::array<unsigned char,0x60> entity{};std::array<float,16> cached_transform{};
 uintptr_t pp=reinterpret_cast<uintptr_t>(packet.data()),owner=reinterpret_cast<uintptr_t>(entity.data()),storage=0x1234;uint32_t mode=1;
 float* point=reinterpret_cast<float*>(packet.data()+0x54);
 UiFixture(){auto cache=reinterpret_cast<uintptr_t>(cached_transform.data());std::memcpy(packet.data()+0x84,&cache,4);cached_transform[0]=cached_transform[5]=cached_transform[10]=cached_transform[15]=1;std::memcpy(entity.data()+0x4c,&pp,4);std::memcpy(packet.data()+8,&storage,4);std::memcpy(packet.data()+0x68,&mode,4);point[0]=565;point[1]=75;}
};
void margin_consumer_retention(){
 UiFixture f;UiMargins ui;detail::UiMarginsContract::enable(ui);ui.dimensions(1920,1080);ui.scene_context(false);ui.capture_window(true,30);UiNative native;Trace trace;
 auto consume=[&](float x,float y){f.point[0]=x;f.point[1]=y;auto bytes=f.packet;auto cache=f.cached_transform;CHECK(ui.enter_consume(f.owner));auto d=ui.draw_decision();float offset=d.margin;if(x==565){CHECK(ui.enter_consume(f.owner)&&ui.draw_decision().anchor.id==d.anchor.id);ui.leave_consume();}
  for(int draw=0;draw<2;++draw){native.world._41=x;auto original=native.world;{UiWorldScope scope(native,trace,ui,0,true);CHECK(scope.changed()==(offset!=0));CHECK(native.DrawPrimitive(D3DPT_TRIANGLELIST,0,1)==S_OK&&native.observed==x+offset);CHECK(f.packet==bytes);}CHECK(!std::memcmp(&native.world,&original,sizeof(original))&&f.packet==bytes&&f.cached_transform==cache);}
  ui.leave_consume();CHECK(ui.finish_frame()&&f.packet==bytes);return offset;};
 CHECK(std::abs(consume(565,75)-106.6667f)<.0001f);
 CHECK(std::abs(consume(562,75.125f)-106.6667f)<.0001f&&ui.json().find("\"retained_anchor_without_current_rule_match\":1")!=std::string::npos);
 CHECK(std::abs(consume(558,75.25f)-106.6667f)<.0001f);
 ui.reset_anchors("Reset");ui.capture_window(false,33);ui.capture_window(true,33);CHECK(consume(300,300)==0);
 CHECK(consume(565,75)>100);f.storage=0x5678;std::memcpy(f.packet.data()+8,&f.storage,4);CHECK(consume(300,300)==0);
 CHECK(consume(565,75)>100);ui.scene_context(false);ui.scene_context(true);CHECK(consume(300,300)==0);
 std::cout<<"Production packet read-only context / repeated native WORLD copy / immediate exact restore: PASS\n";
}
void render_local_ui_contracts(){
 for(int direction:{-1,1}){UiFixture f;UiMargins ui;detail::UiMarginsContract::enable(ui);ui.dimensions(1734,480);UiNative native;Trace trace;uint64_t id=0;
  for(int frame=0;frame<30;++frame){int animation_step=frame<10?frame:frame<20?9:frame-10;f.point[0]=(direction>0?565.f:23.f)-animation_step*3.f;f.point[1]=(direction>0?75.f:370.f)+animation_step*.1f;f.cached_transform[12]=f.point[0];f.cached_transform[13]=f.point[1];auto bytes=f.packet;auto cache=f.cached_transform;
   CHECK(ui.enter_consume(f.owner));auto decision=ui.draw_decision();CHECK(decision.anchor.direction==direction&&decision.margin==direction*547);if(!frame)id=decision.anchor.id;CHECK(id==decision.anchor.id);
   native.world._41=f.point[0];native.world._42=f.point[1];native.world._11=2;auto original=native.world;
   trace.shadow.matrices[D3DTS_WORLD].set(original);for(int draw=0;draw<3;++draw){{UiWorldScope scope(native,trace,ui,0,true);CHECK(scope.changed()&&native.world._41==f.point[0]+direction*547&&native.world._42==f.point[1]);CHECK(native.DrawPrimitive(D3DPT_TRIANGLELIST,0,1)==S_OK);}CHECK(!std::memcmp(&native.world,&original,sizeof(original))&&f.packet==bytes&&f.cached_transform==cache&&!std::memcmp(&trace.shadow.matrices[D3DTS_WORLD].value,&original,sizeof(original)));}
   ui.leave_consume();CHECK(!ui.draw_decision().valid&&ui.finish_frame()&&f.packet==bytes);
  }CHECK(ui.render_draws==90&&ui.restore_exact==90&&ui.restore_failures==0);
 }
 UiFixture f,other;other.point[0]=other.point[1]=300;UiMargins ui;detail::UiMarginsContract::enable(ui);ui.dimensions(1734,480);UiNative native;Trace trace;
 CHECK(ui.enter_consume(f.owner));CHECK(ui.draw_decision().margin==547);CHECK(ui.enter_consume(other.owner)&&ui.draw_decision().margin==0);ui.leave_consume();CHECK(ui.draw_decision().margin==547);
 auto bytes=f.packet;native.world._41=565;native.draw_hr=E_FAIL;{UiWorldScope scope(native,trace,ui,0,true);CHECK(scope.changed()&&native.DrawPrimitive(D3DPT_TRIANGLELIST,0,1)==E_FAIL);}CHECK(native.world._41==565&&f.packet==bytes);
 f.storage=9;std::memcpy(f.packet.data()+8,&f.storage,4);CHECK(!ui.draw_decision().valid);ui.leave_consume();
 CHECK(ui.enter_consume(f.owner));ui.reset_anchors("Reset");CHECK(!ui.draw_decision().valid);ui.leave_consume();f.point[0]=f.point[1]=300;CHECK(ui.enter_consume(f.owner)&&ui.draw_decision().margin==0);ui.leave_consume();
 f.point[0]=565;f.point[1]=75;bytes=f.packet;CHECK(ui.enter_consume(f.owner));native.get_hr=E_FAIL;{UiWorldScope scope(native,trace,ui,0,true);CHECK(!scope.changed());}CHECK(ui.world_read_failed==1);native.get_hr=S_OK;
 native.fail_set=native.sets+1;{UiWorldScope scope(native,trace,ui,0,true);CHECK(!scope.changed());}CHECK(ui.temporary_set_failed==1&&native.world._41==565);
 native.fail_set=native.sets+2;{UiWorldScope scope(native,trace,ui,0,true);CHECK(scope.changed());}CHECK(ui.restore_failures==1&&!ui.finish_frame()&&!ui.draw_decision().valid&&f.packet==bytes);
 native.fail_set=native.sets+1;CHECK(ui.repair_world(native,trace,0)==D3DERR_DEVICELOST);native.fail_set=0;CHECK(ui.repair_world(native,trace,0)==S_OK&&native.world._41==565&&ui.finish_frame());ui.leave_consume();
 std::cout<<"Render-local UI animation/pause/extreme/repeat/nested/epoch/source immutability/failure repair: PASS\n";
}
// Reserve mapped synthetic EXE address space for the retail return RVA. No
// instructions or game bytes are executed here; draw_primitive_at receives it.
static volatile unsigned char synthetic_caller_image_extent[0x180000];
void render_local_wrapper_contract(){
 synthetic_caller_image_extent[0]=1;UiNative native;Root raw;auto* root=new Root8(&raw);auto policy=std::make_unique<QualityPipeline>();auto* device=new Device8(&native,root,std::move(policy));
 device->quality->config.interface_mode="PreserveMargins";device->quality->ui_projection_live=true;detail::UiMarginsContract::enable(device->ui_margins);
 device->trace.control.pending=true;CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==S_OK);device->ui_margins.dimensions(1734,480);
 UiFixture f;auto bytes=f.packet;CHECK(device->ui_margins.enter_consume(f.owner));D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1;
 device->trace.shadow.bindings.vertex_shader.set(0x142);device->trace.effective_shadow.matrices[D3DTS_VIEW].set(identity);native.world._41=565;auto original=native.world;
 device->trace.shadow.matrices[D3DTS_WORLD].set(original);device->trace.effective_shadow.matrices[D3DTS_WORLD].set(original);
 uintptr_t pc=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+UI_DRAW_RETURN_RVA;
 CHECK(device->draw_primitive_at(D3DPT_TRIANGLELIST,0,1,pc)==S_OK&&native.observed==1112&&native.sets==2&&native.draws==1&&f.packet==bytes&&native.world._41==565);
 auto stock=[&](uintptr_t caller,D3DPRIMITIVETYPE type){auto sets=native.sets,draws=native.draws;CHECK(device->draw_primitive_at(type,0,1,caller)==S_OK&&native.sets==sets&&native.draws==draws+1&&native.observed==565&&f.packet==bytes);};
 stock(pc+1,D3DPT_TRIANGLELIST);stock(pc,D3DPT_LINELIST);device->trace.shadow.bindings.vertex_shader.set(0x152);stock(pc,D3DPT_TRIANGLELIST);device->trace.shadow.bindings.vertex_shader.set(0x142);
 device->quality->ui_projection_live=false;stock(pc,D3DPT_TRIANGLELIST);device->quality->ui_projection_live=true;
 device->trace.effective_shadow.matrices[D3DTS_VIEW].value._41=1;stock(pc,D3DPT_TRIANGLELIST);device->trace.effective_shadow.matrices[D3DTS_VIEW].set(identity);
 device->quality->config.interface_mode="Centered4x3";stock(pc,D3DPT_TRIANGLELIST);device->quality->config.interface_mode="PreserveMargins";
 device->ui_margins.leave_consume();stock(pc,D3DPT_TRIANGLELIST);CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==S_OK);
 CHECK(!std::memcmp(&device->trace.shadow.matrices[D3DTS_WORLD].value,&original,sizeof(original))&&device->ui_margins.restore_exact==1);
 // Native draw HRESULT survives a successful immediate restore, and a failed
// restore is repaired before the next unrelated draw.
 CHECK(device->ui_margins.enter_consume(f.owner));native.draw_hr=E_FAIL;CHECK(device->draw_primitive_at(D3DPT_TRIANGLELIST,0,1,pc)==E_FAIL&&native.world._41==565);native.draw_hr=S_OK;
 native.fail_set=native.sets+2;CHECK(device->draw_primitive_at(D3DPT_TRIANGLELIST,0,1,pc)==S_OK&&device->ui_margins.restore_failures==1);native.fail_set=native.sets+1;auto draws=native.draws;CHECK(device->draw_primitive_at(D3DPT_TRIANGLELIST,0,1,pc+1)==D3DERR_DEVICELOST&&native.draws==draws);
 native.fail_set=0;CHECK(device->draw_primitive_at(D3DPT_TRIANGLELIST,0,1,pc+1)==S_OK&&native.world._41==565&&native.observed==565);device->ui_margins.leave_consume();device->Release();root->Release();
 std::cout<<"Production DrawPrimitive UI gate, exact native restoration, failure blocks unrelated draws: PASS\n";
}
void margin_candidate_diagnostics(){
 alignas(float) std::array<std::array<unsigned char,0x90>,3> packets{};
 std::array<std::array<unsigned char,0x60>,3> entities{};
 UiMargins ui;detail::UiMarginsContract::enable(ui);ui.dimensions(1920,1080);ui.scene_context(false);ui.capture_window(true,60);
 uintptr_t storage=0xabc0;uint32_t mode=1;
 for(size_t i=0;i<3;++i){
  auto pp=reinterpret_cast<uintptr_t>(packets[i].data());std::memcpy(entities[i].data()+0x4c,&pp,4);std::memcpy(packets[i].data()+8,&storage,4);std::memcpy(packets[i].data()+0x68,&mode,4);
  auto* point=reinterpret_cast<float*>(packets[i].data()+0x54);point[0]=i==0?565.f:i==1?23.f:300.f;point[1]=i==0?75.f:i==1?370.f:300.f;
  CHECK(ui.enter_consume(reinterpret_cast<uintptr_t>(entities[i].data())));ui.leave_consume();CHECK(i!=2||point[0]==300);
 }
 CHECK(ui.finish_frame());CHECK(ui.finish_frame()); // One completed absent frame.
 auto* point=reinterpret_cast<float*>(packets[0].data()+0x54);point[0]=550;point[1]=76;CHECK(ui.enter_consume(reinterpret_cast<uintptr_t>(entities[0].data())));CHECK(ui.draw_decision().margin>106);ui.leave_consume();
 CHECK(point[0]==550&&ui.json().find("\"anchor_grace_retained\":1")!=std::string::npos);
 CHECK(ui.finish_frame()&&point[0]==550&&ui.json().find("\"group_grace_retained\":0")!=std::string::npos);
}
void antialiasing(){
 Root root;Windows windows;QualityPipeline q(windows);VisualConfig c;c.display_mode="Borderless";c.aa_mode="MSAA";c.samples=8;auto p=stock();q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);IDirect3DDevice8* out=nullptr;
 CHECK(q.create(root,0,&p,&out)==S_OK&&p.MultiSampleType==4&&p.SwapEffect==D3DSWAPEFFECT_DISCARD&&q.attempts==1);
 root.depth_support=2;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.MultiSampleType==2);
 root.support=0;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.MultiSampleType==0&&p.SwapEffect==D3DSWAPEFFECT_COPY);
 root.support=root.depth_support=8;root.depth_pair=false;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.MultiSampleType==0);root.depth_pair=true;
 root.reject_msaa=true;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.MultiSampleType==0&&p.BackBufferWidth==1920&&q.attempts==2);
 root.reject_display=true;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.BackBufferWidth==640&&q.attempts==3);
 root.reject_msaa=root.reject_display=false;root.result=D3DERR_DEVICELOST;p=stock();CHECK(q.create(root,0,&p,&out)==D3DERR_DEVICELOST&&q.attempts==1);
 root.result=S_OK;root.dev.reject_msaa=true;p=stock();CHECK(q.reset(root,root.dev,&p)==S_OK&&q.attempts==2&&p.BackBufferWidth==1920&&p.MultiSampleType==0);
 root.dev.reject_msaa=false;root.dev.result=D3DERR_DEVICELOST;p=stock();CHECK(q.reset(root,root.dev,&p)==D3DERR_DEVICELOST&&q.attempts==1);
 root.dev.result=S_OK;q.aa_hazard=true;p=stock();CHECK(q.reset(root,root.dev,&p)==S_OK&&p.MultiSampleType==0&&p.SwapEffect==D3DSWAPEFFECT_COPY);
 q.aa_hazard=false;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.MultiSampleType==8);root.dev.reject_msaa=true;
 CHECK(q.reset(root,root.dev,&p)==S_OK&&p.MultiSampleType==0&&p.SwapEffect==D3DSWAPEFFECT_COPY&&q.attempts==2);root.dev.reject_msaa=false;
 D3DVIEWPORT8 logical_view{0,0,640,480,0,1},effective_view{};
 CHECK(q.viewport(logical_view,effective_view)&&effective_view.Width==1920&&effective_view.Height==1080); // Reset echoed physical PP, legacy viewport still uses logical baseline.
 // Actual Windowed argument and exclusive adapter mode are independently checked.
 root.windowed_expected=false;c.display_mode="ExclusiveFullscreen";c.width=1920;c.height=1080;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);q.aa_hazard=false;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&!p.Windowed&&p.MultiSampleType==8);
}
void exclusive_lifecycle(){
 Root root;root.mode={640,480,60,D3DFMT_X8R8G8B8};root.windowed_expected=false;Windows windows;QualityPipeline q(windows);VisualConfig c;c.display_mode="ExclusiveFullscreen";auto p=stock();p.Windowed=FALSE;IDirect3DDevice8* out=nullptr;
 q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);q.cooperative_result(S_OK);q.cooperative_result(S_OK);q.cooperative_result(D3DERR_DEVICELOST);q.cooperative_result(D3DERR_DEVICELOST);q.cooperative_result(D3DERR_DEVICENOTRESET);q.cooperative_result(S_OK);CHECK(q.create(root,0,&p,&out)==S_OK&&!p.Windowed&&p.BackBufferWidth==640&&p.BackBufferHeight==480&&p.FullScreen_RefreshRateInHz==0&&p.FullScreen_PresentationInterval==D3DPRESENT_INTERVAL_DEFAULT&&windows.applies==0&&windows.restores==0);
 for(bool windowed:{false,true}){auto input=stock();input.Windowed=windowed;input.BackBufferWidth=656;input.BackBufferHeight=519;windows.state.client={0,0,656,519};auto n=root.dev.resets.size();CHECK(q.reset(root,root.dev,&input)==S_OK&&root.dev.resets.size()==n+1&&!input.Windowed&&input.BackBufferWidth==640&&input.BackBufferHeight==480&&windows.applies==0&&windows.restores==0);}
 auto accepted=q.effective;root.dev.result=D3DERR_DEVICELOST;auto input=stock();auto n=root.dev.resets.size();CHECK(q.reset(root,root.dev,&input)==D3DERR_DEVICELOST&&root.dev.resets.size()==n+1&&presentation_equivalent(q.effective,accepted)&&q.attempts==1);root.dev.result=S_OK;
 root.modes=false;input=stock();n=root.dev.resets.size();CHECK(q.reset(root,root.dev,&input)==D3DERR_NOTAVAILABLE&&root.dev.resets.size()==n&&presentation_equivalent(q.effective,accepted)&&q.display=="ExclusiveFullscreen");root.modes=true;
 // Explicit unsupported dimensions or refresh reject without native call or mode alias.
 for(int invalid=0;invalid<3;++invalid){c.width=invalid==0?656:640;c.height=invalid==0?519:480;c.refresh=invalid==1?75:0;root.depth_pair=invalid!=2;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);input=stock();auto bytes=input;n=root.creates.size();CHECK(q.create(root,0,&input,&out)==D3DERR_NOTAVAILABLE&&root.creates.size()==n&&!std::memcmp(&input,&bytes,sizeof(input))&&q.display=="ExclusiveFullscreen"&&windows.applies==0&&windows.restores==0);}
 root.depth_pair=true;c.width=640;c.height=480;c.refresh=0;c.aa_mode="MSAA";c.samples=4;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);input=stock();CHECK(q.create(root,0,&input,&out)==S_OK&&!input.Windowed&&input.MultiSampleType==4&&q.attempts==1);
 root.reject_msaa=true;input=stock();CHECK(q.create(root,0,&input,&out)==S_OK&&!input.Windowed&&input.MultiSampleType==0&&input.SwapEffect==D3DSWAPEFFECT_COPY&&q.attempts==2);root.reject_msaa=false;
 root.support=0;input=stock();CHECK(q.create(root,0,&input,&out)==S_OK&&!input.Windowed&&input.MultiSampleType==0&&q.attempts==1);root.support=4;
 root.result=D3DERR_INVALIDCALL;input=stock();CHECK(q.create(root,0,&input,&out)==D3DERR_INVALIDCALL&&q.attempts==2&&q.display=="ExclusiveFullscreen");root.result=S_OK;
 std::cout<<"Exclusive native ownership / immutable selected mode / full-screen AA / reject-no-alias / bounded loss: PASS\n";
}
void viewports_ui(){
 D3DVIEWPORT8 v{0,0,640,480,0,1},out{};CHECK(map_viewport(v,640,480,1920,1080,out)&&out.Width==1920&&out.Height==1080);
 v={320,0,320,480,.1f,.9f};CHECK(map_viewport(v,640,480,1920,1080,out)&&out.X==960&&out.Width==960&&out.Height==1080&&out.MinZ==.1f);
 v={320,240,320,240,0,1};CHECK(map_viewport(v,640,480,1920,1080,out)&&out.X==960&&out.Y==540&&out.Height==540);
 CHECK(!map_viewport(v,0,480,1920,1080,out));v.X=641;CHECK(!map_viewport(v,640,480,1920,1080,out));
 QualityPipeline q;q.requested=stock();q.effective=q.requested;q.effective.BackBufferWidth=1920;q.effective.BackBufferHeight=1080;q.modified=q.valid=true;q.display="Borderless";
 v={0,0,1920,1080,0,1};CHECK(!q.viewport(v,out));v={0,0,480,270,0,1};CHECK(!q.viewport(v,out)); // Already physical quarter remains physical.
 v={0,0,640,480,0,1};CHECK(q.viewport(v,out)&&out.Width==1920);v={320,0,320,480,0,1};CHECK(q.viewport(v,out)&&out.X==960);
 D3DMATRIX p{};p._11=2.f/640;p._22=2.f/480;p._33=-.0005f;p._41=p._42=-1;p._43=.5;p._44=1;
 for(double aspect:{4./3,16./9,16./10,21./9}){D3DMATRIX wide{};CHECK(ui_projection(p,aspect,wide));CHECK(std::abs(wide._11-2./(480*aspect))<1e-8);CHECK(std::abs(wide._41+640./(480*aspect))<1e-7);CHECK(wide._22==p._22&&wide._33==p._33);}
 D3DMATRIX out_matrix{};auto bad=p;bad._34=1;CHECK(!ui_projection(bad,16./9,out_matrix));
 CHECK(margin_direction(565,75,0)==1&&margin_direction(23,370,0)==-1&&margin_direction(565,75,1)==0);
 for(auto& r:MARGIN_RULES)CHECK(margin_direction(r.x,r.y,0)==r.direction);
 CHECK(margin_direction(25,19,0)==-1&&margin_direction(106,99.9f,0)==-1&&margin_direction(106,100,0)==0&&margin_direction(50,259,0)==-1&&margin_direction(50,340,0)==0);

}
struct Memory:PatchMemory {
 unsigned writes=0,protects=0,flushes=0;int fail_write=0,fail_protect=0,fail_flush=0;DWORD protection=PAGE_EXECUTE_READ;
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool write(void* d,const void* s,size_t n) noexcept override{if(++writes==fail_write)return false;std::memcpy(d,s,n);return true;}
 bool protect(void*,size_t,DWORD p,DWORD& old) noexcept override{old=protection;if(++protects==fail_protect)return false;protection=p;return true;}
 bool flush(void*,size_t) noexcept override{return ++flushes!=fail_flush;}
};
void freeze_and_patch(){
 unsigned char bytes[sizeof(FREEZE_CONTEXT)];std::memcpy(bytes,FREEZE_CONTEXT,sizeof(bytes));Memory memory;
 auto r=apply_freeze_patch(memory,bytes,true,false);CHECK(!r.applied&&memory.writes==0);
 r=apply_freeze_patch(memory,bytes,false,true);CHECK(!r.applied&&memory.writes==0);
 bytes[2]=0x74;r=apply_freeze_patch(memory,bytes,true,true);CHECK(!r.applied&&memory.writes==0);bytes[2]=0x75;
 bytes[8]^=1;r=apply_freeze_patch(memory,bytes,true,true);CHECK(!r.applied&&memory.writes==0);bytes[8]^=1;
 r=apply_freeze_patch(memory,bytes,true,true);CHECK(r.context_validated&&r.applied&&r.owned&&bytes[3]==0&&memory.protection==PAGE_EXECUTE_READ);
 r=apply_freeze_patch(memory,bytes,true,true);CHECK(r.already&&!r.owned&&!r.applied&&memory.writes==1);
 for(int failure=0;failure<4;++failure){std::memcpy(bytes,FREEZE_CONTEXT,sizeof(bytes));Memory m;if(failure==0)m.fail_protect=1;if(failure==1)m.fail_write=1;if(failure==2)m.fail_flush=1;if(failure==3)m.fail_protect=2;
  r=apply_freeze_patch(m,bytes,true,true);CHECK(r.context_validated&&!r.applied&&bytes[3]==0x11&&m.protection==PAGE_EXECUTE_READ);if(failure)CHECK(r.rollback_verified);
 }
 std::array<unsigned char,5> code=UI_SORT_BYTES;UiJumpPatch p;Memory m;CHECK(p.install(m,code.data(),reinterpret_cast<uintptr_t>(code.data())+100)&&code[0]==0xe9);CHECK(p.remove(m)&&code==UI_SORT_BYTES&&m.protection==PAGE_EXECUTE_READ);
 code[0]=0x90;CHECK(!p.install(m,code.data(),123));code=UI_SORT_BYTES;
 for(int f=1;f<=3;++f){Memory bad;UiJumpPatch patch;if(f==1)bad.fail_write=1;if(f==2)bad.fail_flush=1;if(f==3)bad.fail_protect=2;CHECK(!patch.install(bad,code.data(),123));CHECK(code==UI_SORT_BYTES&&!patch.installed());}

}
void native_window(){
 // Hidden synthetic HWND; no game or visible interactive window is launched.
 HWND w=CreateWindowExW(0,L"STATIC",L"MRR quality contract",WS_OVERLAPPEDWINDOW,100,100,640,480,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);CHECK(w!=nullptr&&!IsWindowVisible(w));
 WindowState saved{};auto& api=native_window_api();CHECK(api.snapshot(w,saved));RECT target{saved.outer.left,saved.outer.top,saved.outer.left+1280,saved.outer.top+720};CHECK(api.apply(saved,target,true,false));RECT outer{};CHECK(GetWindowRect(w,&outer));CHECK(std::abs((outer.left+outer.right)-(saved.work.left+saved.work.right))<=1&&std::abs((outer.top+outer.bottom)-(saved.work.top+saved.work.bottom))<=1);RECT client{};CHECK(GetClientRect(w,&client)&&client.right==1280&&client.bottom==720&&!IsWindowVisible(w));
 // IsZoomed state detection on a hidden synthetic HWND; no visible maximize.
 auto style=GetWindowLongW(w,GWL_STYLE);SetWindowLongW(w,GWL_STYLE,style|WS_MAXIMIZE);WindowState zoomed{};CHECK(api.snapshot(w,zoomed)&&zoomed.maximized&&IsZoomed(w)&&!IsWindowVisible(w));SetWindowLongW(w,GWL_STYLE,style);CHECK(api.snapshot(w,zoomed)&&!zoomed.maximized);
 CHECK(api.apply(saved,saved.monitor,false,true));CHECK(GetClientRect(w,&client)&&client.right==saved.monitor.right-saved.monitor.left&&client.bottom==saved.monitor.bottom-saved.monitor.top);
 CHECK(!(GetWindowLongW(w,GWL_STYLE)&WS_CAPTION)&&!IsWindowVisible(w));CHECK(api.restore(saved));WindowState after{};CHECK(api.snapshot(w,after)&&after.style==saved.style&&after.exstyle==saved.exstyle&&std::memcmp(&after.outer,&saved.outer,sizeof(RECT))==0);{QualityPipeline q;q.valid=true;q.effective=stock();q.effective.hDeviceWindow=w;q.display="Borderless";q.cursor_watch();CHECK(q.cursor_watch_installed());SendMessageW(w,WM_KILLFOCUS,0,0);q.begin_shutdown();CHECK(!q.cursor_watch_installed());}CHECK(DestroyWindow(w));
}
void wrapper_trace(){
 Root raw;Windows windows;auto policy=std::make_unique<QualityPipeline>(windows);VisualConfig config;config.display_mode="Borderless";config.aa_mode="MSAA";
 policy->configure(config,true,2,D3DDEVTYPE_HAL,reinterpret_cast<HWND>(0x1234));auto p=stock();IDirect3DDevice8* output=nullptr;CHECK(policy->create(raw,0,&p,&output)==S_OK);
 raw.dev.color.desc.Width=raw.dev.depth.desc.Width=1920;raw.dev.color.desc.Height=raw.dev.depth.desc.Height=1080;raw.dev.color.desc.MultiSampleType=raw.dev.depth.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;
 raw.dev.color.desc.Format=D3DFMT_X8R8G8B8;raw.dev.depth.desc.Format=D3DFMT_D16;policy->observe(raw.dev);
 CHECK(policy->backbuffer_known&&policy->depth_known&&policy->backbuffer.Width==1920&&policy->depth.Height==1080&&raw.dev.color.refs==0&&raw.dev.depth.refs==0);
 auto* root=new Root8(&raw);auto* device=new Device8(&raw.dev,root,std::move(policy));device->trace.control.pending=true;CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==S_OK);
 D3DVIEWPORT8 v{0,0,640,480,0,1};CHECK(device->SetViewport(&v)==S_OK&&raw.dev.viewport.Width==1920&&raw.dev.viewport.Height==1080);D3DVIEWPORT8 got{};CHECK(device->GetViewport(&got)==S_OK&&got.Width==640&&got.Height==480);
 CHECK(device->DrawPrimitive(D3DPT_TRIANGLELIST,0,1)==S_OK);v={320,240,320,240,0,1};CHECK(device->SetViewport(&v)==S_OK&&raw.dev.viewport.X==960&&raw.dev.viewport.Y==540&&raw.dev.viewport.Width==960);CHECK(device->DrawPrimitive(D3DPT_TRIANGLELIST,3,1)==S_OK);CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==S_OK);
 raw.dev.reject_msaa=true;CHECK(device->Reset(&p)==S_OK&&p.BackBufferWidth==1920&&p.MultiSampleType==0&&p.SwapEffect==D3DSWAPEFFECT_COPY);
 D3DMATRIX ui{};ui._11=2.f/640;ui._22=2.f/480;ui._33=-.0005f;ui._41=ui._42=-1;ui._43=.5f;ui._44=1;
 device->quality->config.interface_mode="Centered4x3";device->quality->ui_projection_live=true;device->trace.shadow.matrices[D3DTS_PROJECTION].set(ui);device->trace.effective_shadow.matrices[D3DTS_PROJECTION].set(ui);
 v={0,0,1920,1080,0,1};CHECK(device->SetViewport(&v)==S_OK&&std::abs(raw.dev.projection._11-2.f/(480.f*16/9))<1e-8f);
 raw.dev.reject_ui=true;device->visuals.effective.anisotropy=true;v={0,0,960,600,0,1};
 CHECK(device->SetViewport(&v)==S_OK&&device->quality->config.interface_mode=="Stock"&&raw.dev.projection._11==ui._11&&device->visuals.effective.anisotropy);
 device->Release();root->Release();
}
void validated_ui_wrapper(){
 Root raw;Windows windows;auto policy=std::make_unique<QualityPipeline>(windows);VisualConfig config;config.display_mode="Borderless";config.interface_mode="Centered4x3";
 policy->configure(config,true,2,D3DDEVTYPE_HAL,reinterpret_cast<HWND>(0x1234));auto p=stock();IDirect3DDevice8* output=nullptr;CHECK(policy->create(raw,0,&p,&output)==S_OK);
 auto* root=new Root8(&raw);auto* device=new Device8(&raw.dev,root,std::move(policy));
 device->quality->config.interface_mode="Centered4x3"; // production session is the synthetic EXE; inject independently validated test owner.
 device->quality->ui_capability.status="SUPPORTED";device->quality->ui_capability.method="fingerprint";device->quality->ui_capability.candidate_rva=0x1000;
 auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));D3DVIEWPORT8 v{0,0,1920,1080,0,1};CHECK(device->SetViewport(&v)==S_OK);
 D3DMATRIX ui{};ui._11=2.f/640;ui._22=2.f/480;ui._33=-.0005f;ui._41=ui._42=-1;ui._43=.5;ui._44=1;
 CHECK(device->set_transform_at(D3DTS_PROJECTION,&ui,base+GAMEPLAY_PROJECTION_RETURN_RVA)==S_OK&&!device->quality->ui_projection_live&&raw.dev.projection._11==ui._11);
 CHECK(device->SetViewport(&v)==S_OK&&raw.dev.projection._11==ui._11); // shape alone cannot establish proof
 device->trace.control.pending=true;CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==S_OK);
 CHECK(device->set_transform_at(D3DTS_PROJECTION,&ui,base+0x1000)==S_OK&&device->quality->ui_projection_live&&std::abs(raw.dev.projection._11-2.f/(480.f*16/9))<1e-8f);
 D3DMATRIX logical{};CHECK(device->GetTransform(D3DTS_PROJECTION,&logical)==raw.dev.hr); // unrelated native HRESULT is preserved
 CHECK(device->DrawPrimitive(D3DPT_TRIANGLELIST,0,1)==S_OK&&device->Present(nullptr,nullptr,nullptr,nullptr)==S_OK);
 auto bad=ui;bad._41=0;CHECK(device->set_transform_at(D3DTS_PROJECTION,&bad,base+0x1000)==S_OK&&!device->quality->ui_projection_live&&raw.dev.projection._41==0);
 CHECK(device->SetViewport(&v)==S_OK&&raw.dev.projection._41==0);
 raw.dev.reject_ui=true;CHECK(device->set_transform_at(D3DTS_PROJECTION,&ui,base+0x1000)==S_OK&&!device->quality->ui_projection_live&&raw.dev.projection._11==ui._11);
 device->Release();root->Release();std::cout<<"Validated UI native setter, wrong caller/ortho, cached proof and rejected rewrite: PASS\n";
}
void ui_native_abi(){
 std::array<unsigned char,0x90> packet{};std::array<unsigned char,0x60> entity{};auto pp=reinterpret_cast<uintptr_t>(packet.data());std::memcpy(entity.data()+0x4c,&pp,4);uint32_t mode=1;std::memcpy(packet.data()+0x68,&mode,4);
 CHECK(eligible_ui_packet(reinterpret_cast<uintptr_t>(entity.data()),pp+0x24));mode=2;std::memcpy(packet.data()+0x68,&mode,4);CHECK(eligible_ui_packet(reinterpret_cast<uintptr_t>(entity.data()),pp+0x24));mode=0;std::memcpy(packet.data()+0x68,&mode,4);CHECK(!eligible_ui_packet(reinterpret_cast<uintptr_t>(entity.data()),pp+0x24));CHECK(!eligible_ui_packet(1,1));
 // Execute the production x86 bridge against synthetic executable memory only.
 unsigned char bytes[]={0xd8,0x60,0x30,0xd9,0xc0,0xd9,0x1a,0xd9,0x5a,0x04,0xc3};
 auto* code=static_cast<unsigned char*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(code);std::memcpy(code,bytes,sizeof(bytes));
 auto destination=detail::ui_bridge_for_contract(reinterpret_cast<uintptr_t>(code)+5);Memory memory;UiJumpPatch patch;CHECK(destination&&patch.install(memory,code,destination));
 float coordinates[16]{};coordinates[12]=2;float original=5,output[2]{};uint32_t stack_before=0,stack_after=0,ecx_after=0;unsigned short cw_before=0,cw_after=0;
 __asm {
  fnstcw cw_before
  mov stack_before,esp
  lea eax,coordinates
  lea edx,output
  mov ecx,12345678h
  fld original
  call code
  mov stack_after,esp
  mov ecx_after,ecx
  fnstcw cw_after
 }
 CHECK(output[0]==3&&output[1]==3&&stack_before==stack_after&&ecx_after==0x12345678&&cw_before==cw_after);CHECK(patch.remove(memory));CHECK(VirtualFree(code,0,MEM_RELEASE));
}
void packet_consumer_abi(){
 unsigned char bytes[]={0x81,0xec,0x08,0x01,0,0,0x8b,0x84,0x24,0x0c,0x01,0,0,0x81,0xc4,0x08,0x01,0,0,0xc2,4,0};
 auto* code=static_cast<unsigned char*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(code);std::memcpy(code,bytes,sizeof(bytes));Memory memory;UiPacketPatch patch;
 CHECK(patch.install(memory,code,detail::ui_packet_bridge_for_contract(reinterpret_cast<uintptr_t>(code)+6)));
 uint32_t before=0,after=0,result=0,ecx_after=0;float source=7,fp_after=0;
 __asm {mov before,esp
 mov ecx,12345678h
 fld source
 push 11223344h
 call code
 mov result,eax
 mov after,esp
 mov ecx_after,ecx
 fstp fp_after}
 CHECK(before==after&&result==0x11223344&&ecx_after==0x12345678&&fp_after==7&&detail::ui_packet_entity_for_contract()==0x11223344);CHECK(patch.remove(memory)&&!std::memcmp(code,UI_PACKET_BYTES.data(),6));
 // Both stock return paths use RET 0Ch. Exercise that actual cleanup size
 // with integer/flags/x87/SSE state preserved by entry and return bridges.
 unsigned char retail_return[]={0x81,0xec,0x08,0x01,0,0,0x8b,0x84,0x24,0x0c,0x01,0,0,0x81,0xc4,0x08,0x01,0,0,0xf9,0xc2,0x0c,0};
 std::memcpy(code,retail_return,sizeof(retail_return));CHECK(patch.install(memory,code,detail::ui_packet_bridge_for_contract(reinterpret_cast<uintptr_t>(code)+6)));
 float sse_in[4]{1,2,3,4},sse_out[4]{};unsigned short cw_before=0,cw_after=0;uint32_t mxcsr_before=0,mxcsr_after=0,flags_after=0;
 __asm {fnstcw cw_before
 stmxcsr mxcsr_before
 lea eax,sse_in
 movups xmm0,[eax]
 mov before,esp
 mov ecx,12345678h
 fld source
 push 3
 push 2
 push 11223344h
 call code
 mov result,eax
 pushfd
 pop flags_after
 mov after,esp
 mov ecx_after,ecx
 fstp fp_after
 fnstcw cw_after
 stmxcsr mxcsr_after
 lea eax,sse_out
 movups [eax],xmm0}
 CHECK(before==after&&result==0x11223344&&ecx_after==0x12345678&&fp_after==7&&cw_before==cw_after&&mxcsr_before==mxcsr_after&&(flags_after&1)&&!std::memcmp(sse_in,sse_out,sizeof(sse_in)));
 CHECK(patch.remove(memory));
 for(int failure=1;failure<=3;++failure){Memory bad;UiPacketPatch failed;if(failure==1)bad.fail_write=1;if(failure==2)bad.fail_flush=1;if(failure==3)bad.fail_protect=2;CHECK(!failed.install(bad,code,detail::ui_packet_bridge_for_contract(reinterpret_cast<uintptr_t>(code)+6)));CHECK(!failed.installed()&&!std::memcmp(code,UI_PACKET_BYTES.data(),6));}
 CHECK(VirtualFree(code,0,MEM_RELEASE));
}
void quality_fpu(){
 fenv_t saved;fegetenv(&saved);feclearexcept(FE_ALL_EXCEPT);fesetround(FE_DOWNWARD);feraiseexcept(FE_INVALID);
 int flags=fetestexcept(FE_ALL_EXCEPT);QualityPipeline q;q.valid=true;q.effective=stock();q.effective.BackBufferWidth=1920;q.effective.BackBufferHeight=1080;q.json();
 UiMargins ui;ui.dimensions(1920,1080);ui.json();D3DMATRIX matrix{},out{};matrix._11=2.f/640;matrix._22=2.f/480;matrix._33=-.0005f;matrix._41=matrix._42=-1;matrix._43=.5;matrix._44=1;
 flags=fetestexcept(FE_ALL_EXCEPT);ui_projection_dimensions(matrix,1920,1080,out);CHECK(fegetround()==FE_DOWNWARD&&fetestexcept(FE_ALL_EXCEPT)==flags);fesetenv(&saved);
 fegetenv(&saved);fesetround(FE_DOWNWARD);D3DMATRIX source{};source._22=float(1/std::tan((45./(16./9))*3.14159265358979323846/360.));source._11=source._22/float(16./9);source._33=1.01f;source._34=1;source._43=-.2f;flags=fetestexcept(FE_ALL_EXCEPT);CHECK(camera_scene_family(source)==0&&fegetround()==FE_DOWNWARD&&fetestexcept(FE_ALL_EXCEPT)==flags);fesetenv(&saved);
}
int main(){try{configs();numeric_configs();trace_numeric_configs();reset_echo_shutdown();preview_cursor_packets();displays();display_transactions();windowed_live_resize();windowed_maximize_restore();stable_margin_anchors();margin_short_grace();margin_consumer_retention();margin_candidate_diagnostics();render_local_ui_contracts();render_local_wrapper_contract();antialiasing();exclusive_lifecycle();viewports_ui();freeze_and_patch();native_window();wrapper_trace();validated_ui_wrapper();ui_native_abi();packet_consumer_abi();quality_fpu();std::cout<<"R-GFX5 config/display/viewport/UI/MSAA/Reset/freeze/hidden HWND/native bridge contracts: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
