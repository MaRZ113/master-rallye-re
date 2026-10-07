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
#define CHECK(x) do {if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
struct Windows:WindowApi {
 WindowState state{};RECT last{};bool client=false,popup=false,fail=false;unsigned applies=0,restores=0;
 Windows(){state.hwnd=reinterpret_cast<HWND>(0x1234);state.valid=true;state.monitor={1920,0,3840,1080};state.client={0,0,640,480};state.outer={2000,50,2660,570};state.style=WS_OVERLAPPEDWINDOW;}
 bool snapshot(HWND,WindowState& s) noexcept override{s=state;return true;}
 bool apply(const WindowState&,const RECT& r,bool c,bool p) noexcept override{last=r;client=c;popup=p;++applies;return !fail;}
 bool restore(const WindowState&) noexcept override{++restores;return true;}
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
 std::vector<D3DPRESENT_PARAMETERS> resets;HRESULT result=S_OK;bool reject_msaa=false,reject_ui=false;
 D3DVIEWPORT8 viewport{};D3DMATRIX projection{};Surface color,depth;
 HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS* p) override{resets.push_back(*p);return reject_msaa&&p->MultiSampleType!=D3DMULTISAMPLE_NONE?D3DERR_INVALIDCALL:result;}
 HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT,D3DBACKBUFFER_TYPE,IDirect3DSurface8** p) override{color.AddRef();*p=&color;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetDepthStencilSurface(IDirect3DSurface8** p) override{depth.AddRef();*p=&depth;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{viewport=*p;return result;}
 HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{*p=viewport;return result;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE,const D3DMATRIX* p) override{if(reject_ui&&p->_11!=2.f/640)return D3DERR_INVALIDCALL;projection=*p;return result;}
 HRESULT STDMETHODCALLTYPE Present(const RECT*,const RECT*,HWND,const RGNDATA*) override{return result;}
 HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE,UINT,UINT) override{return result;}
};
struct Root:MockRootBase {
 Device dev;std::vector<D3DPRESENT_PARAMETERS> creates;unsigned support=4,depth_support=4;bool windowed_expected=true,modes=true,depth_pair=true;HRESULT result=S_OK;bool reject_msaa=false,reject_display=false;
 HRESULT STDMETHODCALLTYPE GetAdapterDisplayMode(UINT a,D3DDISPLAYMODE* m) override{CHECK(a==2);*m={1920,1080,60,D3DFMT_X8R8G8B8};return S_OK;}
 UINT STDMETHODCALLTYPE GetAdapterModeCount(UINT) override{return modes?1:0;}
 HRESULT STDMETHODCALLTYPE EnumAdapterModes(UINT,UINT,D3DDISPLAYMODE* m) override{*m={1920,1080,60,D3DFMT_X8R8G8B8};return S_OK;}
 HRESULT STDMETHODCALLTYPE CheckDeviceType(UINT a,D3DDEVTYPE t,D3DFORMAT,D3DFORMAT,BOOL) override{CHECK(a==2&&t==D3DDEVTYPE_HAL);return S_OK;}
 HRESULT STDMETHODCALLTYPE CheckDeviceFormat(UINT,D3DDEVTYPE,D3DFORMAT,DWORD usage,D3DRESOURCETYPE,D3DFORMAT) override{CHECK(usage==D3DUSAGE_DEPTHSTENCIL);return S_OK;}
 HRESULT STDMETHODCALLTYPE CheckDepthStencilMatch(UINT,D3DDEVTYPE,D3DFORMAT,D3DFORMAT,D3DFORMAT) override{return depth_pair?S_OK:D3DERR_NOTAVAILABLE;}
 HRESULT STDMETHODCALLTYPE CheckDeviceMultiSampleType(UINT a,D3DDEVTYPE t,D3DFORMAT f,BOOL windowed,D3DMULTISAMPLE_TYPE n) override{CHECK(a==2&&t==D3DDEVTYPE_HAL&&bool(windowed)==windowed_expected);return n<=static_cast<int>(f==D3DFMT_D16?depth_support:support)?S_OK:D3DERR_NOTAVAILABLE;}
 HRESULT STDMETHODCALLTYPE CreateDevice(UINT,D3DDEVTYPE,HWND,DWORD,D3DPRESENT_PARAMETERS* p,IDirect3DDevice8** out) override{creates.push_back(*p);if(reject_msaa&&p->MultiSampleType!=D3DMULTISAMPLE_NONE)return D3DERR_INVALIDCALL;if(reject_display&&p->BackBufferWidth!=640)return D3DERR_INVALIDCALL;if(FAILED(result))return result;*out=&dev;return S_OK;}
};
D3DPRESENT_PARAMETERS stock(){D3DPRESENT_PARAMETERS p{};p.BackBufferWidth=640;p.BackBufferHeight=480;p.BackBufferFormat=D3DFMT_X8R8G8B8;p.BackBufferCount=1;p.SwapEffect=D3DSWAPEFFECT_COPY;p.hDeviceWindow=reinterpret_cast<HWND>(0x1234);p.Windowed=TRUE;p.EnableAutoDepthStencil=TRUE;p.AutoDepthStencilFormat=D3DFMT_D16;return p;}
void configs(){
 auto c=parse_visual_config({},false);CHECK(c.display_mode=="Stock"&&c.aa_mode=="Stock"&&c.interface_mode=="Stock"&&!c.menu_freeze);
 c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Display.Mode","Borderless"},{"Display.Width","nan"},{"AntiAliasing.Mode","MSAA"},{"AntiAliasing.Samples","8"}},true);CHECK(c.display_mode=="Stock"&&c.aa_mode=="MSAA"&&c.samples==8);
 c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"Display.Mode","Windowed"},{"Display.Width","1280"},{"Display.Height","720"},{"Widescreen.InterfaceMode","PreserveMargins"},{"Compatibility.MenuFreezeFix","true"}},true);CHECK(c.width==1280&&c.height==720&&c.interface_mode=="PreserveMargins"&&c.menu_freeze);
 for(auto key:{"Display.Mode","Widescreen.InterfaceMode","AntiAliasing.Mode","Compatibility.MenuFreezeFix"}){auto v=parse_visual_config({{"Renderer.ConfigVersion","1"},{key,"invalid"}},true);CHECK(v.display_mode=="Stock"&&v.interface_mode=="Stock"&&v.aa_mode=="Stock"&&!v.menu_freeze);}
}
void displays(){
 Root root;Windows windows;QualityPipeline q(windows);VisualConfig c;auto p=stock();IDirect3DDevice8* out=nullptr;
 q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);CHECK(q.create(root,0,&p,&out)==S_OK&&root.creates.size()==1&&windows.applies==0&&std::memcmp(&p,&q.requested,sizeof(p))==0);
 c.display_mode="Windowed";c.width=1280;c.height=720;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK);CHECK(p.Windowed&&p.BackBufferWidth==1280&&p.BackBufferHeight==720&&windows.client&&!windows.popup&&windows.last.right-windows.last.left==1280);
 q.restore_window();c.display_mode="Borderless";c.width=c.height=0;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK);CHECK(p.Windowed&&p.BackBufferWidth==1920&&p.BackBufferHeight==1080&&!windows.client&&windows.popup&&windows.last.left==1920&&windows.last.bottom==1080);
 c.display_mode="ExclusiveFullscreen";c.width=1920;c.height=1080;c.refresh=60;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK);CHECK(!p.Windowed&&p.FullScreen_RefreshRateInHz==60);
 c.refresh=75;q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.Windowed&&p.BackBufferWidth==640&&q.display=="Stock");
 c.display_mode="Borderless";q.configure(c,false,2,D3DDEVTYPE_HAL,p.hDeviceWindow);CHECK(!q.active());
 q.configure(c,true,2,D3DDEVTYPE_HAL,p.hDeviceWindow);windows.fail=true;p=stock();CHECK(q.create(root,0,&p,&out)==S_OK&&p.BackBufferWidth==640&&q.display=="Stock"&&windows.restores>0);
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
 MarginFrame frame;float right[3]={565,75,0},left[3]={23,370,0},unknown[3]={300,300,0};CHECK(frame.shift(right,100)&&right[0]==665);CHECK(!frame.shift(right,100));CHECK(frame.shift(left,100)&&left[0]==-77);CHECK(!frame.shift(unknown,100));CHECK(frame.restore()&&right[0]==565&&left[0]==23);
 CHECK(frame.shift(right,100));right[0]=123;CHECK(frame.restore()&&right[0]==123); // Engine owns intervening mutations.
 right[0]=565;CHECK(frame.shift(right,100));right[1]=76;CHECK(frame.restore()&&right[0]==665); // Reused storage/changed Y is no longer our point.
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
 MarginFrame edits;std::array<std::array<float,3>,513> points{};for(auto& point:points){point={565,75,0};edits.shift(point.data(),100);}CHECK(edits.size()==512&&edits.overflow==1&&points.back()[0]==565);CHECK(edits.restore());for(auto& point:points)CHECK(point[0]==565);
}
void native_window(){
 // Hidden synthetic HWND; no game or visible interactive window is launched.
 HWND w=CreateWindowExW(0,L"STATIC",L"MRR quality contract",WS_OVERLAPPEDWINDOW,100,100,640,480,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);CHECK(w!=nullptr&&!IsWindowVisible(w));
 WindowState saved{};auto& api=native_window_api();CHECK(api.snapshot(w,saved));RECT target{saved.outer.left,saved.outer.top,saved.outer.left+1280,saved.outer.top+720};CHECK(api.apply(saved,target,true,false));RECT client{};CHECK(GetClientRect(w,&client)&&client.right==1280&&client.bottom==720&&!IsWindowVisible(w));
 CHECK(api.apply(saved,saved.monitor,false,true));CHECK(GetClientRect(w,&client)&&client.right==saved.monitor.right-saved.monitor.left&&client.bottom==saved.monitor.bottom-saved.monitor.top);
 CHECK(!(GetWindowLongW(w,GWL_STYLE)&WS_CAPTION)&&!IsWindowVisible(w));CHECK(api.restore(saved));WindowState after{};CHECK(api.snapshot(w,after)&&after.style==saved.style&&after.exstyle==saved.exstyle&&std::memcmp(&after.outer,&saved.outer,sizeof(RECT))==0);CHECK(DestroyWindow(w));
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
 device->quality->config.interface_mode="Centered4x3";device->trace.shadow.matrices[D3DTS_PROJECTION].set(ui);device->trace.effective_shadow.matrices[D3DTS_PROJECTION].set(ui);
 v={0,0,1920,1080,0,1};CHECK(device->SetViewport(&v)==S_OK&&std::abs(raw.dev.projection._11-2.f/(480.f*16/9))<1e-8f);
 raw.dev.reject_ui=true;device->visuals.effective.anisotropy=true;v={0,0,960,600,0,1};
 CHECK(device->SetViewport(&v)==S_OK&&device->quality->config.interface_mode=="Stock"&&raw.dev.projection._11==ui._11&&device->visuals.effective.anisotropy);
 device->Release();root->Release();
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
void quality_fpu(){
 fenv_t saved;fegetenv(&saved);feclearexcept(FE_ALL_EXCEPT);fesetround(FE_DOWNWARD);feraiseexcept(FE_INVALID);
 int flags=fetestexcept(FE_ALL_EXCEPT);QualityPipeline q;q.valid=true;q.effective=stock();q.effective.BackBufferWidth=1920;q.effective.BackBufferHeight=1080;q.json();
 UiMargins ui;ui.dimensions(1920,1080);ui.json();CHECK(fegetround()==FE_DOWNWARD&&fetestexcept(FE_ALL_EXCEPT)==flags);fesetenv(&saved);
}
int main(){try{configs();displays();antialiasing();viewports_ui();freeze_and_patch();native_window();wrapper_trace();ui_native_abi();quality_fpu();std::cout<<"R-GFX5 config/display/viewport/UI/MSAA/Reset/freeze/hidden HWND/native bridge contracts: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
