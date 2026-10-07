#include "quality.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <sstream>
#include <cfenv>
namespace gfx2 {
namespace {
struct SavedFP {fenv_t env;SavedFP(){fegetenv(&env);}~SavedFP(){fesetenv(&env);}};
QualityPipeline* cursor_owner=nullptr;
LRESULT CALLBACK cursor_messages(int code,WPARAM w,LPARAM l){
 if(code>=0&&cursor_owner){auto* message=reinterpret_cast<CWPRETSTRUCT*>(l);auto* owner=cursor_owner;HWND target=owner->effective.hDeviceWindow?owner->effective.hDeviceWindow:owner->focus;
  if(message->hwnd==target){if(message->message==WM_KILLFOCUS||message->message==WM_DESTROY||(message->message==WM_ACTIVATEAPP&&!message->wParam))owner->cursor_focus_lost();
   else if(message->message==WM_SETCURSOR||message->message==WM_MOUSEMOVE||message->message==WM_ACTIVATEAPP)owner->cursor_tick();}
 }return CallNextHookEx(nullptr,code,w,l);
}
class NativeWindows final:public WindowApi {
 bool style(HWND w,int index,LONG value) noexcept {display_breadcrumb("SetWindowLong_begin");SetLastError(0);bool okay=SetWindowLongW(w,index,value)!=0||GetLastError()==0;display_breadcrumb("SetWindowLong_end",okay?S_OK:E_FAIL);return okay;}
public:
 bool snapshot(HWND w,WindowState& s) noexcept override {
  s={};if(!IsWindow(w))return false;MONITORINFO m{sizeof(m)};
  if(!GetWindowRect(w,&s.outer)||!GetClientRect(w,&s.client)||!GetMonitorInfoW(MonitorFromWindow(w,MONITOR_DEFAULTTONEAREST),&m))return false;
  s.hwnd=w;s.style=GetWindowLongW(w,GWL_STYLE);s.exstyle=GetWindowLongW(w,GWL_EXSTYLE);s.menu=GetMenu(w);s.monitor=m.rcMonitor;s.work=m.rcWork;s.maximized=IsZoomed(w)!=FALSE;s.valid=true;return true;
 }
 bool apply(const WindowState& s,const RECT& desired,bool client,bool popup) noexcept override {
  if(!s.valid)return false;
  LONG ws=(s.style&(WS_VISIBLE|WS_DISABLED|WS_CLIPCHILDREN|WS_CLIPSIBLINGS))|(popup?WS_POPUP:WS_OVERLAPPEDWINDOW);
  LONG ex=s.exstyle&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE|WS_EX_CLIENTEDGE|WS_EX_DLGMODALFRAME);
  RECT r=desired;HMENU menu=popup?nullptr:s.menu;
  if(client){RECT size{0,0,desired.right-desired.left,desired.bottom-desired.top};if(!AdjustWindowRectEx(&size,ws,menu!=nullptr,ex))return false;
   const auto& work=s.work.right>s.work.left?s.work:s.monitor;LONG width=size.right-size.left,height=size.bottom-size.top;
   if(width>work.right-work.left||height>work.bottom-work.top)return false;
   r.left=std::clamp(work.left+(work.right-work.left-width)/2,work.left,work.right-width);r.top=std::clamp(work.top+(work.bottom-work.top-height)/2,work.top,work.bottom-height);r.right=r.left+width;r.bottom=r.top+height;
  }
  if(!style(s.hwnd,GWL_STYLE,ws)||!style(s.hwnd,GWL_EXSTYLE,ex))return false;
  display_breadcrumb("SetMenu_begin");bool menu_ok=SetMenu(s.hwnd,menu)!=FALSE;display_breadcrumb("SetMenu_end",menu_ok?S_OK:E_FAIL);if(!menu_ok)return false;
  display_breadcrumb("SetWindowPos_begin");bool positioned=SetWindowPos(s.hwnd,HWND_NOTOPMOST,r.left,r.top,r.right-r.left,r.bottom-r.top,SWP_FRAMECHANGED|SWP_NOACTIVATE|SWP_NOOWNERZORDER)!=FALSE;display_breadcrumb("SetWindowPos_end",positioned?S_OK:E_FAIL);if(!positioned)return false;
  RECT actual{};return GetClientRect(s.hwnd,&actual)&&actual.right==desired.right-desired.left&&actual.bottom==desired.bottom-desired.top;
 }
 bool restore(const WindowState& s) noexcept override {
  if(!s.valid||!IsWindow(s.hwnd))return false;
  bool okay=style(s.hwnd,GWL_STYLE,s.style);okay=style(s.hwnd,GWL_EXSTYLE,s.exstyle)&&okay;okay=(SetMenu(s.hwnd,s.menu)!=FALSE)&&okay;
  return SetWindowPos(s.hwnd,(s.exstyle&WS_EX_TOPMOST)?HWND_TOPMOST:HWND_NOTOPMOST,s.outer.left,s.outer.top,s.outer.right-s.outer.left,s.outer.bottom-s.outer.top,SWP_FRAMECHANGED|SWP_NOACTIVATE|SWP_NOOWNERZORDER)!=FALSE&&okay;
 }
} native_windows;
bool lost(HRESULT hr){return hr==D3DERR_DEVICELOST||hr==D3DERR_DEVICENOTRESET;}
}
void display_breadcrumb(const char* step,HRESULT result) noexcept {try{session().write("{\"type\":\"display_breadcrumb\",\"step\":"+quote(step)+",\"hresult\":"+std::to_string(static_cast<uint32_t>(result))+"}");}catch(...){}}
WindowApi& native_window_api() noexcept{return native_windows;}
int camera_scene_family(const D3DMATRIX& source) noexcept {
 SavedFP fp;if(!symmetric_lh(source))return -1;double angle=source_camera_angle(source);
 if(std::abs(angle-90.)<=SOURCE_CAMERA_TOLERANCE_DEGREES)return 1;
 if(std::abs(angle-45.)<=SOURCE_CAMERA_TOLERANCE_DEGREES)return 0;
 return -1;
}
QualityPipeline::~QualityPipeline(){begin_shutdown();}
void QualityPipeline::begin_shutdown() noexcept {if(shutting_down_)return;shutting_down_=true;window_owned_=false;if(cursor_owner==this)cursor_owner=nullptr;if(cursor_hook_){UnhookWindowsHookEx(cursor_hook_);cursor_hook_=nullptr;}if(cursor_.hidden){SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));cursor_.hidden=false;}display_breadcrumb("shutdown_skip_window_restore");}
void QualityPipeline::configure(const VisualConfig& c,bool ui_supported,UINT a,D3DDEVTYPE t,HWND w){
 config=c;adapter=a;type=t;focus=w;display=c.display_mode;display_reason=c.display_reason;aa_reason=c.aa_reason;
 pinned_width_=pinned_height_=0;window_state_="unknown";
 if(!ui_supported){config.interface_mode="Stock";config.interface_reason="ui_owner_unsupported";}
 if(c.aa_mode=="Stock")aa_reason="Mode_Stock_Samples_ignored";
}
void QualityPipeline::restore_window() noexcept {
 if(!shutting_down_&&window_owned_){bool prior=committing_;committing_=true;if(windows_->restore(original))window_owned_=false;else {try{session().write("{\"type\":\"window_restore_failed\"}");}catch(...){}}committing_=prior;}
}
int CursorIdle::update(bool inside,POINT p,uint64_t now,unsigned delay) noexcept {
 if(!inside){observed=false;if(hidden){hidden=false;return 1;}return 0;}
 bool moved=!observed||p.x!=previous.x||p.y!=previous.y;
 previous=p;observed=true;if(moved){last_move=now;if(hidden){hidden=false;return 1;}return 0;}
 if(now-last_move>=delay&&!hidden){hidden=true;return -1;}return 0;
}
void QualityPipeline::cursor_watch() noexcept {
 if(cursor_owner&&cursor_owner!=this){config.auto_hide_cursor=false;config.cursor_reason="cursor_multiple_devices_unmanaged";return;}
 if(cursor_hook_||!config.auto_hide_cursor||(display!="Borderless"&&display!="ExclusiveFullscreen"))return;
 HWND w=effective.hDeviceWindow?effective.hDeviceWindow:focus;DWORD process=0;
 if(!IsWindow(w)||GetWindowThreadProcessId(w,&process)!=GetCurrentThreadId()||process!=GetCurrentProcessId()){config.auto_hide_cursor=false;config.cursor_reason="cursor_window_thread_unavailable";return;}
 HMODULE module=nullptr;GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(&cursor_messages),&module);
 cursor_hook_=SetWindowsHookExW(WH_CALLWNDPROCRET,&cursor_messages,module,GetCurrentThreadId());
 if(cursor_hook_)cursor_owner=this;else {config.auto_hide_cursor=false;config.cursor_reason="cursor_message_watch_unavailable";}
}
void QualityPipeline::cursor_focus_lost() noexcept {
 bool hidden=cursor_.hidden;cursor_.update(false,POINT{},GetTickCount64(),config.cursor_delay_ms);
 if(hidden&&!GetCursor())SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));saved_cursor_=nullptr;
}
void QualityPipeline::cursor_tick() noexcept {
 if(shutting_down_)return;cursor_watch();POINT p{};RECT r{};HWND w=effective.hDeviceWindow?effective.hDeviceWindow:focus;
 bool inside=config.auto_hide_cursor&&(display=="Borderless"||display=="ExclusiveFullscreen")&&GetForegroundWindow()==w&&GetCursorPos(&p)&&GetWindowRect(w,&r)&&PtInRect(&r,p);
 int action=cursor_.update(inside,p,GetTickCount64(),config.cursor_delay_ms);
 if(action<0){saved_cursor_=GetCursor();SetCursor(nullptr);}
 else if(action>0){if(!GetCursor())SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));saved_cursor_=nullptr;}
 else if(cursor_.hidden)SetCursor(nullptr); // WM_SETCURSOR may have installed the stock handle; display counter is untouched.
}
bool QualityPipeline::select_display(IDirect3D8& root,D3DPRESENT_PARAMETERS& p){
 display=config.display_mode;if(display=="Stock")return true;
 if(!windows_->snapshot(p.hDeviceWindow?p.hDeviceWindow:focus,current)){display_reason="invalid_window_or_monitor_stock";return false;}
 display_breadcrumb("monitor_selection_complete");
 if(!original.valid)original=current;
 D3DDISPLAYMODE desktop{};if(FAILED(root.GetAdapterDisplayMode(adapter,&desktop))){display_reason="adapter_display_query_failed_stock";return false;}
 p.hDeviceWindow=current.hwnd;
 if(display=="Borderless"){
  // A borderless fullscreen client/backbuffer always fills rcMonitor.
  p.BackBufferWidth=config.width?config.width:current.monitor.right-current.monitor.left;
  p.BackBufferHeight=config.height?config.height:current.monitor.bottom-current.monitor.top;
  if(p.BackBufferWidth!=static_cast<UINT>(current.monitor.right-current.monitor.left)||p.BackBufferHeight!=static_cast<UINT>(current.monitor.bottom-current.monitor.top)){
   display_reason="borderless_uses_monitor_native_size";p.BackBufferWidth=current.monitor.right-current.monitor.left;p.BackBufferHeight=current.monitor.bottom-current.monitor.top;
  }
 }else if(display=="Windowed"){
  p.BackBufferWidth=pinned_width_?pinned_width_:(config.width?config.width:(p.BackBufferWidth?p.BackBufferWidth:current.client.right));
  p.BackBufferHeight=pinned_height_?pinned_height_:(config.height?config.height:(p.BackBufferHeight?p.BackBufferHeight:current.client.bottom));
  if(!p.BackBufferWidth||!p.BackBufferHeight||p.BackBufferWidth>16384||p.BackBufferHeight>16384){display_reason="invalid_effective_dimensions_stock";return false;}
  RECT bounds{0,0,static_cast<LONG>(p.BackBufferWidth),static_cast<LONG>(p.BackBufferHeight)};
  LONG ws=(current.style&(WS_VISIBLE|WS_DISABLED|WS_CLIPCHILDREN|WS_CLIPSIBLINGS))|WS_OVERLAPPEDWINDOW;
  LONG ex=current.exstyle&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE|WS_EX_CLIENTEDGE|WS_EX_DLGMODALFRAME);
  auto work=current.work.right>current.work.left?current.work:current.monitor;
  if(!AdjustWindowRectEx(&bounds,ws,current.menu!=nullptr,ex)||bounds.right-bounds.left>work.right-work.left||bounds.bottom-bounds.top>work.bottom-work.top){display_reason="windowed_client_exceeds_work_area_stock";return false;}
  pinned_width_=p.BackBufferWidth;pinned_height_=p.BackBufferHeight;
  // The configured dimensions belong to the NORMAL window. A genuine OS
  // maximize temporarily owns the client/backbuffer without changing that target.
  if(current.maximized){p.BackBufferWidth=current.client.right-current.client.left;p.BackBufferHeight=current.client.bottom-current.client.top;}
 }else {p.BackBufferWidth=config.width?config.width:(p.BackBufferWidth?p.BackBufferWidth:current.client.right);p.BackBufferHeight=config.height?config.height:(p.BackBufferHeight?p.BackBufferHeight:current.client.bottom);}
 if(!p.BackBufferWidth||!p.BackBufferHeight||p.BackBufferWidth>16384||p.BackBufferHeight>16384){display_reason="invalid_effective_dimensions_stock";return false;}
 if(display=="ExclusiveFullscreen"){
  D3DDISPLAYMODE selected{};bool found=false;UINT count=root.GetAdapterModeCount(adapter);
  for(UINT i=0;i<std::min(count,UINT(65536));++i){D3DDISPLAYMODE mode{};if(FAILED(root.EnumAdapterModes(adapter,i,&mode)))continue;
   if(mode.Width!=p.BackBufferWidth||mode.Height!=p.BackBufferHeight||(config.refresh&&mode.RefreshRate!=config.refresh))continue;
   if(mode.Format!=p.BackBufferFormat&&mode.Format!=desktop.Format)continue;
   if(FAILED(root.CheckDeviceType(adapter,type,mode.Format,mode.Format,FALSE)))continue;
   if(!found||mode.Format==p.BackBufferFormat){selected=mode;found=true;if(config.refresh||mode.RefreshRate==desktop.RefreshRate)break;}
  }
  if(!found){display_reason="exclusive_mode_format_refresh_unavailable_stock";return false;}
  p.Windowed=FALSE;p.BackBufferFormat=selected.Format;p.FullScreen_RefreshRateInHz=config.refresh?selected.RefreshRate:0;
 }else {p.Windowed=TRUE;p.BackBufferFormat=desktop.Format;p.FullScreen_RefreshRateInHz=0;p.FullScreen_PresentationInterval=D3DPRESENT_INTERVAL_DEFAULT;
  if(FAILED(root.CheckDeviceType(adapter,type,desktop.Format,p.BackBufferFormat,TRUE))){display_reason="windowed_format_unavailable_stock";return false;}
 }
 return true;
}
bool QualityPipeline::apply_window(const D3DPRESENT_PARAMETERS& p){
 if(display=="Stock"){restore_window();committed_={};window_commit_status_="not_required";return true;}
 WindowState now{};if(!windows_->snapshot(p.hDeviceWindow?p.hDeviceWindow:focus,now)){display_reason="window_commit_snapshot_failed";window_commit_status_="failed_snapshot";return false;}
 if(display=="Windowed"&&now.maximized){
  // Windows owns placement while zoomed; no style/menu/SetWindowPos mutation.
  current=committed_=now;window_commit_status_="maximized_os_owned";window_transition(now);return true;
 }
 bool unchanged=committed_.valid&&now.hwnd==committed_.hwnd&&now.style==committed_.style&&now.exstyle==committed_.exstyle&&now.menu==committed_.menu&&
  !std::memcmp(&now.outer,&committed_.outer,sizeof(RECT))&&!std::memcmp(&now.client,&committed_.client,sizeof(RECT))&&
  now.client.right==static_cast<LONG>(p.BackBufferWidth)&&now.client.bottom==static_cast<LONG>(p.BackBufferHeight)&&
  ((display=="Windowed")==((now.style&WS_CAPTION)==WS_CAPTION))&&
  (display!="Borderless"||!std::memcmp(&now.outer,&now.monitor,sizeof(RECT)));
 if(unchanged){window_commit_status_="unchanged";window_transition(now);display_breadcrumb("window_commit_unchanged");return true;}
 current=now;RECT r=current.monitor;bool client=display=="Windowed";
 if(client){r.left=current.outer.left;r.top=current.outer.top;r.right=r.left+p.BackBufferWidth;r.bottom=r.top+p.BackBufferHeight;}
 else if(display=="ExclusiveFullscreen"){r.right=r.left+p.BackBufferWidth;r.bottom=r.top+p.BackBufferHeight;}
 display_breadcrumb("window_commit_begin");committing_=true;
 bool okay=windows_->apply(current,r,client,!client);
 if(!okay){window_commit_status_="failed_rollback_restored";if(!windows_->restore(now)){window_owned_=true;window_commit_status_="failed_rollback_unverified";display_breadcrumb("window_commit_rollback_failed",E_FAIL);}committing_=false;display_reason="window_commit_failed_native_parameters_retained";display_breadcrumb("window_commit_failed",E_FAIL);return false;}
 committing_=false;window_owned_=true;window_commit_status_="committed";windows_->snapshot(current.hwnd,committed_);window_transition(committed_);display_breadcrumb("window_commit_complete");return true;
}
void QualityPipeline::window_transition(const WindowState& state) noexcept {
 if(display!="Windowed"||!state.valid)return;
 const char* next=state.maximized?"maximized":"normal";if(window_state_==next)return;window_state_=next;
 try{session().write("{\"type\":\"window_state_transition\",\"window_state\":"+quote(next)+",\"normal_target\":{\"width\":"+std::to_string(pinned_width_)+",\"height\":"+std::to_string(pinned_height_)+"},\"actual_client\":{\"width\":"+std::to_string(state.client.right-state.client.left)+",\"height\":"+std::to_string(state.client.bottom-state.client.top)+"},\"effective_backbuffer\":{\"width\":"+std::to_string(effective.BackBufferWidth)+",\"height\":"+std::to_string(effective.BackBufferHeight)+"}}");}catch(...){}
}
D3DPRESENT_PARAMETERS QualityPipeline::plan(IDirect3D8& root,const D3DPRESENT_PARAMETERS& source){
 display_breadcrumb("display_plan_begin");auto logical=source;
 if(valid&&modified){
  // Reset may echo the effective descriptor returned by our preceding call.
  // Remove only fields still exactly equal to our own override; retain new game requests.
  #define UNMIX(field) if(source.field==effective.field&&effective.field!=fallback_.field)logical.field=fallback_.field
  UNMIX(BackBufferWidth);UNMIX(BackBufferHeight);UNMIX(BackBufferFormat);UNMIX(BackBufferCount);UNMIX(MultiSampleType);UNMIX(SwapEffect);UNMIX(hDeviceWindow);UNMIX(Windowed);UNMIX(Flags);UNMIX(FullScreen_RefreshRateInHz);UNMIX(FullScreen_PresentationInterval);
  #undef UNMIX
 }
 requested=source;fallback_=logical;viewport_domain_known=false;auto p=logical;
 if(config.display_mode!="Stock"&&!select_display(root,p)){p=fallback_;display="Stock";}
 auto before_aa=p;
 if(config.aa_mode=="MSAA"&&!aa_hazard){
  D3DDISPLAYMODE desktop{};bool pair=SUCCEEDED(root.GetAdapterDisplayMode(adapter,&desktop));
  if(p.BackBufferFormat==D3DFMT_UNKNOWN&&pair)p.BackBufferFormat=desktop.Format;
  pair=pair&&SUCCEEDED(root.CheckDeviceType(adapter,type,p.Windowed?desktop.Format:p.BackBufferFormat,p.BackBufferFormat,p.Windowed));
  if(p.EnableAutoDepthStencil)pair=pair&&SUCCEEDED(root.CheckDeviceFormat(adapter,type,p.Windowed?desktop.Format:p.BackBufferFormat,D3DUSAGE_DEPTHSTENCIL,D3DRTYPE_SURFACE,p.AutoDepthStencilFormat))&&SUCCEEDED(root.CheckDepthStencilMatch(adapter,type,p.Windowed?desktop.Format:p.BackBufferFormat,p.BackBufferFormat,p.AutoDepthStencilFormat));
  unsigned chosen=0;for(unsigned n:{8u,4u,2u}){
   if(n>config.samples||!pair)continue;auto sample=static_cast<D3DMULTISAMPLE_TYPE>(n);
   if(FAILED(root.CheckDeviceMultiSampleType(adapter,type,p.BackBufferFormat,p.Windowed,sample)))continue;
   if(p.EnableAutoDepthStencil&&FAILED(root.CheckDeviceMultiSampleType(adapter,type,p.AutoDepthStencilFormat,p.Windowed,sample)))continue;
   chosen=n;break;
  }
  if(chosen){p.MultiSampleType=static_cast<D3DMULTISAMPLE_TYPE>(chosen);p.SwapEffect=D3DSWAPEFFECT_DISCARD;p.BackBufferCount=1;p.Flags&=~D3DPRESENTFLAG_LOCKABLE_BACKBUFFER;aa_reason="color_and_depth_caps_supported_pending_create";}
  else {p=before_aa;aa_reason=pair?"requested_samples_unsupported_stock":"format_or_depth_pair_unavailable_stock";}
 }else if(aa_hazard)aa_reason="unreviewed_present_arguments_stock_on_next_reset";
 display_breadcrumb("presentation_transform_complete");return p;
}
D3DPRESENT_PARAMETERS QualityPipeline::without_aa(D3DPRESENT_PARAMETERS p) const noexcept {p.MultiSampleType=fallback_.MultiSampleType;p.SwapEffect=fallback_.SwapEffect;p.BackBufferCount=fallback_.BackBufferCount;p.Flags=fallback_.Flags;return p;}
HRESULT QualityPipeline::create(IDirect3D8& root,DWORD flags,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice8** out){
 D3DPRESENT_PARAMETERS input{};bool have=pp&&safe_copy(&input,pp,sizeof(input));
 if(!active()||!have){if(have){requested=fallback_=input;}HRESULT hr=root.CreateDevice(adapter,type,focus,flags,pp,out);if(SUCCEEDED(hr)&&pp&&safe_copy(&effective,pp,sizeof(effective)))valid=true;return hr;}
 auto candidate=plan(root,input);attempts=1;auto sent=candidate;auto invoke=[&](){display_breadcrumb("native_CreateDevice_begin");auto result=root.CreateDevice(adapter,type,focus,flags,&sent,out);display_breadcrumb("native_CreateDevice_end",result);return result;};HRESULT hr=invoke();
 if(FAILED(hr)&&!lost(hr)&&candidate.MultiSampleType!=fallback_.MultiSampleType){candidate=without_aa(candidate);sent=candidate;++attempts;aa_reason="native_create_rejected_msaa_stock";hr=invoke();}
 if(FAILED(hr)&&!lost(hr)&&std::memcmp(&candidate,&fallback_,sizeof(candidate))){display="Stock";display_reason="native_create_rejected_display_stock";sent=fallback_;++attempts;hr=invoke();}
 if(SUCCEEDED(hr)){effective=sent;valid=true;modified=std::memcmp(&effective,&fallback_,sizeof(effective))!=0;safe_copy(pp,&sent,sizeof(sent));if(out&&*out)observe(**out);apply_window(sent);}return hr;
}
HRESULT QualityPipeline::reset(IDirect3D8& root,IDirect3DDevice8& device,D3DPRESENT_PARAMETERS* pp){
 if(committing_){
  ++window_reset_echoes;D3DPRESENT_PARAMETERS input{};bool have=pp&&safe_copy(&input,pp,sizeof(input));
  // Probe uses the same planner, but cannot own or mutate a window or accepted state.
  QualityPipeline probe(*this);probe.window_owned_=false;probe.shutting_down_=true;
  auto candidate=have?probe.plan(root,input):D3DPRESENT_PARAMETERS{};
  bool equivalent=have&&valid&&!shutting_down_&&presentation_equivalent(candidate,effective);
  HRESULT hr=equivalent?S_OK:D3DERR_INVALIDCALL;
  if(equivalent&&!safe_copy(pp,&effective,sizeof(effective))){equivalent=false;hr=D3DERR_INVALIDCALL;}
  if(equivalent){++window_reset_echoes_suppressed;}
  else ++deferred_resets; // No safe synchronous deferral contract: reject the different request explicitly.
  try{session().write("{\"type\":\"reset_policy\",\"reset_request_source\":"+quote(equivalent?"window_commit_echo":"deferred_during_commit")+",\"requested\":"+(have?pp_json(input):"null")+",\"effective\":"+(have?pp_json(candidate):"null")+",\"echo_equivalent\":"+(equivalent?"true":"false")+",\"native_reset_called\":false,\"deferred_policy\":\"different_request_rejected_no_recursive_native_reset\",\"result\":"+std::to_string(static_cast<uint32_t>(hr))+"}");}catch(...){}
  return hr;
 }
 if(shutting_down_)return D3DERR_INVALIDCALL;
 const auto old_requested=requested,old_effective=effective,old_fallback=fallback_;const auto old_display=display;const auto old_current=current;
 const bool old_valid=valid,old_modified=modified,old_domain=viewport_domain_known,old_logical=viewport_logical;
 auto failed=[&](){requested=old_requested;effective=old_effective;fallback_=old_fallback;display=old_display;current=old_current;valid=old_valid;modified=old_modified;viewport_domain_known=old_domain;viewport_logical=old_logical;};
 D3DPRESENT_PARAMETERS input{};bool have=pp&&safe_copy(&input,pp,sizeof(input));
 if(!active()||!have){if(have){requested=fallback_=input;}++native_reset_calls;HRESULT hr=device.Reset(pp);if(SUCCEEDED(hr)&&pp&&safe_copy(&effective,pp,sizeof(effective)))valid=true;if(FAILED(hr))failed();return hr;}
 auto candidate=plan(root,input);attempts=1;auto sent=candidate;auto invoke=[&](){display_breadcrumb("native_Reset_begin");++native_reset_calls;auto result=device.Reset(&sent);display_breadcrumb("native_Reset_end",result);return result;};HRESULT hr=invoke();
 if(FAILED(hr)&&!lost(hr)&&candidate.MultiSampleType!=fallback_.MultiSampleType){candidate=without_aa(candidate);sent=candidate;++attempts;aa_reason="native_reset_rejected_msaa_stock";hr=invoke();}
 if(FAILED(hr)&&!lost(hr)&&std::memcmp(&candidate,&fallback_,sizeof(candidate))){display="Stock";display_reason="native_reset_rejected_display_stock";sent=fallback_;++attempts;hr=invoke();}
 if(SUCCEEDED(hr)){effective=sent;valid=true;modified=std::memcmp(&effective,&fallback_,sizeof(effective))!=0;safe_copy(pp,&sent,sizeof(sent));observe(device);ui_projection_live=false;apply_window(sent);}else failed();return hr;
}
void QualityPipeline::observe(IDirect3DDevice8& device) noexcept {
 if(!active())return;backbuffer_known=depth_known=false;IDirect3DSurface8* surface=nullptr;
 if(SUCCEEDED(device.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&surface))&&surface){backbuffer_known=SUCCEEDED(surface->GetDesc(&backbuffer));surface->Release();}
 surface=nullptr;if(SUCCEEDED(device.GetDepthStencilSurface(&surface))&&surface){depth_known=SUCCEEDED(surface->GetDesc(&depth));surface->Release();}
}
bool map_viewport(const D3DVIEWPORT8& v,UINT fw,UINT fh,UINT tw,UINT th,D3DVIEWPORT8& out) noexcept {
 if(!fw||!fh||!tw||!th||!v.Width||!v.Height||uint64_t(v.X)+v.Width>fw||uint64_t(v.Y)+v.Height>fh)return false;
 auto scale=[](uint64_t x,UINT to,UINT from){return static_cast<DWORD>((x*to+from/2)/from);};out=v;
 out.X=scale(v.X,tw,fw);out.Y=scale(v.Y,th,fh);out.Width=scale(uint64_t(v.X)+v.Width,tw,fw)-out.X;out.Height=scale(uint64_t(v.Y)+v.Height,th,fh)-out.Y;
 return out.Width&&out.Height;
}
bool QualityPipeline::viewport(const D3DVIEWPORT8& in,D3DVIEWPORT8& out) const noexcept {
 UINT width=fallback_.BackBufferWidth?fallback_.BackBufferWidth:requested.BackBufferWidth;
 UINT height=fallback_.BackBufferHeight?fallback_.BackBufferHeight:requested.BackBufferHeight;
 if(!valid||!modified||display=="Stock"||!width||!height)return false;
 if(in.X==0&&in.Y==0){
  if(in.Width==effective.BackBufferWidth&&in.Height==effective.BackBufferHeight){viewport_domain_known=true;viewport_logical=false;}
  else if(in.Width==width&&in.Height==height){viewport_domain_known=true;viewport_logical=true;}
 }
 return viewport_domain_known&&viewport_logical&&map_viewport(in,width,height,effective.BackBufferWidth,effective.BackBufferHeight,out);
}
bool presentation_equivalent(const D3DPRESENT_PARAMETERS& a,const D3DPRESENT_PARAMETERS& b) noexcept {
 return a.BackBufferWidth==b.BackBufferWidth&&a.BackBufferHeight==b.BackBufferHeight&&a.BackBufferFormat==b.BackBufferFormat&&a.BackBufferCount==b.BackBufferCount&&a.MultiSampleType==b.MultiSampleType&&a.SwapEffect==b.SwapEffect&&a.hDeviceWindow==b.hDeviceWindow&&bool(a.Windowed)==bool(b.Windowed)&&bool(a.EnableAutoDepthStencil)==bool(b.EnableAutoDepthStencil)&&(!a.EnableAutoDepthStencil||a.AutoDepthStencilFormat==b.AutoDepthStencilFormat)&&a.Flags==b.Flags&&(a.Windowed||(a.FullScreen_RefreshRateInHz==b.FullScreen_RefreshRateInHz&&a.FullScreen_PresentationInterval==b.FullScreen_PresentationInterval));
}
bool frontend_preview_projection(const D3DMATRIX& p,D3DMATRIX& out) noexcept {
 SavedFP fp;if(!symmetric_lh(p))return false;double source=source_camera_angle(p),aspect=double(p._22)/p._11;
 if(std::abs(source-45.)>SOURCE_CAMERA_TOLERANCE_DEGREES||aspect<1.||aspect>4.)return false;
 // Authored 004F2350 landscape rule: vertical angle = source angle / aspect.
 // Retain its 4:3 vertical framing, independently of gameplay VFOV.
 double y=1./std::tan((source/(4./3.))*3.14159265358979323846/360.);
 out=p;out._22=static_cast<float>(y);out._11=static_cast<float>(y/aspect);return true;
}
bool stock_ui_projection(const D3DMATRIX& p) noexcept {
 if(!std::isfinite(p._11)||!std::isfinite(p._22)||std::abs(p._11-2.f/640.f)>1e-8f||std::abs(p._22-2.f/480.f)>1e-8f||p._41!=-1||p._42!=-1||p._34!=0||p._44!=1||std::abs(p._33+.0005f)>1e-9f||p._43!=.5f)return false;
 const int zero[]={1,2,3,4,6,7,8,9};const float* f=&p.m[0][0];for(int k:zero)if(f[k]!=0)return false;return true;
}
bool ui_projection_dimensions(const D3DMATRIX& in,UINT width,UINT height,D3DMATRIX& out) noexcept {SavedFP fp;return height&&ui_projection(in,double(width)/height,out);}
bool ui_projection(const D3DMATRIX& in,double aspect,D3DMATRIX& out) noexcept {
 SavedFP fp;if(!stock_ui_projection(in)||!std::isfinite(aspect)||aspect<1.||aspect>4.)return false;
 double width=480.*aspect;out=in;out._11=static_cast<float>(2./width);out._41=static_cast<float>(-640./width);return true;
}
std::string QualityPipeline::json() const {
 SavedFP fp;
 std::ostringstream o;o<<"{\"window_state\":"<<quote(window_state_)<<",\"normal_target\":{\"width\":"<<pinned_width_<<",\"height\":"<<pinned_height_<<"},\"actual_client\":{\"width\":"<<(committed_.client.right-committed_.client.left)<<",\"height\":"<<(committed_.client.bottom-committed_.client.top)<<"},\"effective_backbuffer\":{\"width\":"<<effective.BackBufferWidth<<",\"height\":"<<effective.BackBufferHeight<<"},\"display_requested\":"<<quote(config.display_mode)<<",\"display_effective\":"<<quote(display)<<",\"display_reason\":"<<quote(display_reason)<<",\"cursor_auto_hide_effective\":"<<(config.auto_hide_cursor?"true":"false")<<",\"cursor_watch_installed\":"<<(cursor_hook_?"true":"false")<<",\"cursor_reason\":"<<quote(config.cursor_reason)<<",\"window_commit_status\":"<<quote(window_commit_status_)<<",\"native_reset_calls\":"<<native_reset_calls<<",\"window_reset_echoes\":"<<window_reset_echoes<<",\"window_reset_echoes_suppressed\":"<<window_reset_echoes_suppressed<<",\"deferred_resets\":"<<deferred_resets<<",\"windowed_target_width\":"<<pinned_width_<<",\"windowed_target_height\":"<<pinned_height_<<",\"aa_effective\":"<<quote(valid&&effective.MultiSampleType!=D3DMULTISAMPLE_NONE?"MSAA":"Stock")<<",\"aa_effective_samples\":"<<(valid?effective.MultiSampleType:0)<<",\"aa_requested\":"<<quote(config.aa_mode)<<",\"aa_requested_samples\":"<<config.samples<<",\"aa_swap_effect\":"<<quote(valid&&effective.SwapEffect==D3DSWAPEFFECT_DISCARD?"DISCARD":valid&&effective.SwapEffect==D3DSWAPEFFECT_COPY?"COPY":"OTHER")<<",\"aa_reason\":"<<quote(aa_reason)<<",\"attempts\":"<<attempts<<",\"requested\":"<<pp_json(requested)<<",\"logical_baseline\":"<<pp_json(fallback_)<<",\"effective\":"<<(valid?pp_json(effective):"null")<<",\"monitor_rect\":["<<current.monitor.left<<','<<current.monitor.top<<','<<current.monitor.right<<','<<current.monitor.bottom<<"],\"physical_backbuffer\":";
 if(backbuffer_known)o<<"{\"width\":"<<backbuffer.Width<<",\"height\":"<<backbuffer.Height<<",\"format\":"<<backbuffer.Format<<",\"multisample\":"<<backbuffer.MultiSampleType<<'}';else o<<"null";
 o<<",\"physical_depth\":";if(depth_known)o<<"{\"width\":"<<depth.Width<<",\"height\":"<<depth.Height<<",\"format\":"<<depth.Format<<",\"multisample\":"<<depth.MultiSampleType<<'}';else o<<"null";
 double aspect=valid&&effective.BackBufferHeight?double(effective.BackBufferWidth)/effective.BackBufferHeight:0;
 o<<",\"effective_aspect\":"<<aspect<<",\"ui\":{\"mode\":"<<quote(config.interface_mode)<<",\"reason\":"<<quote(config.interface_reason)<<",\"logical_width\":640,\"logical_height\":480,\"virtual_width\":"<<480.*aspect<<",\"extra_width\":"<<480.*aspect-640.<<",\"center_offset\":"<<(480.*aspect-640.)*.5<<"},\"dpi_policy\":\"game_awareness_unchanged\"}";return o.str();
}
}
