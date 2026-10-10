#include "quality.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <sstream>
#include <cfenv>
#include <atomic>
namespace gfx2 {
namespace {
struct SavedFP {fenv_t env;SavedFP(){fegetenv(&env);}~SavedFP(){fesetenv(&env);}};
std::atomic<uint64_t> next_display_device_id{1};
std::atomic<uint64_t> next_display_event_id{1};
uint64_t display_event_id() noexcept {return next_display_event_id.fetch_add(1,std::memory_order_relaxed);}
uint64_t allocate_display_device_id() noexcept {auto id=next_display_device_id.fetch_add(1,std::memory_order_relaxed);return id?id:next_display_device_id.fetch_add(1,std::memory_order_relaxed);}
std::string transition_stack_json() {
 void* addresses[16]{};USHORT count=CaptureStackBackTrace(1,16,addresses,nullptr);std::ostringstream o;o<<'[';
 for(USHORT i=0;i<count;++i){if(i)o<<',';auto caller=caller_info(reinterpret_cast<uintptr_t>(addresses[i]));
  o<<"{\"module\":"<<quote(caller.module)<<",\"return_rva\":"<<(caller.known?caller.address-caller.base:0)<<'}';}
 return o.str()+']';
}
class NativeWindows final:public WindowApi {
 bool style(HWND w,int index,LONG value) noexcept {display_breadcrumb("SetWindowLong_begin");SetLastError(0);bool okay=SetWindowLongW(w,index,value)!=0||GetLastError()==0;display_breadcrumb("SetWindowLong_end",okay?S_OK:E_FAIL);return okay;}
public:
 bool snapshot(HWND w,WindowState& s) noexcept override {
  s={};if(!IsWindow(w))return false;MONITORINFO m{sizeof(m)};
  if(!GetWindowRect(w,&s.outer)||!GetClientRect(w,&s.client)||!GetMonitorInfoW(MonitorFromWindow(w,MONITOR_DEFAULTTONEAREST),&m))return false;
   s.hwnd=w;s.style=GetWindowLongW(w,GWL_STYLE);s.exstyle=GetWindowLongW(w,GWL_EXSTYLE);s.menu=GetMenu(w);s.monitor=m.rcMonitor;s.work=m.rcWork;s.maximized=IsZoomed(w)!=FALSE;s.minimized=IsIconic(w)!=FALSE;s.valid=true;return true;
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
void display_breadcrumb(const char* step,HRESULT result) noexcept {try{session().write("{\"type\":\"display_breadcrumb\",\"event_sequence\":"+std::to_string(display_event_id())+",\"step\":"+quote(step)+",\"hresult\":"+std::to_string(static_cast<uint32_t>(result))+"}");}catch(...){}}
WindowApi& native_window_api() noexcept{return native_windows;}
GameWindowOwner inspect_game_window_owner(uintptr_t image,bool exact,HWND expected) noexcept {
 GameWindowOwner result;if(!exact)return result;
 result.reason="owner_chain_not_readable";
 if(!image||image>UINTPTR_MAX-0x2f9d84||!expected)return result;
 uintptr_t renderer=0,owner=0,owned=0;
 if(!safe_copy(&renderer,reinterpret_cast<const void*>(image+0x2f9cf0),sizeof(renderer))||
    !safe_copy(&owner,reinterpret_cast<const void*>(image+0x2f9d80),sizeof(owner))||
    !renderer||!owner||renderer>UINTPTR_MAX-0x24||owner>UINTPTR_MAX-0x1b4||
    !safe_copy(&owned,reinterpret_cast<const void*>(renderer+0x20),sizeof(owned)))return result;
 if(owned!=owner){result.reason="singleton_and_wndproc_owner_disagree";return result;}
 unsigned char bytes[0x1b4]{};if(!safe_copy(bytes,reinterpret_cast<const void*>(owner),sizeof(bytes)))return result;
 uintptr_t vtable=0;HWND hwnd=nullptr;std::memcpy(&vtable,bytes,sizeof(vtable));std::memcpy(&hwnd,bytes+0x5c,sizeof(hwnd));
 if(vtable!=image+0x29228c||hwnd!=expected){result.reason="owner_vtable_or_hwnd_mismatch";return result;}
 uint32_t pp_windowed=0;std::memcpy(&pp_windowed,bytes+0x44,sizeof(pp_windowed));
 for(unsigned offset:{5u,6u,0x1cu,0x24u,0x25u,0x1b0u})if(bytes[offset]>1){result.reason="owner_flags_out_of_range";return result;}
 if(pp_windowed>1){result.reason="owner_presentation_flag_out_of_range";return result;}
 result.known=true;result.address=owner;result.windowed=bytes[0x1c];result.pp_windowed=pp_windowed;result.initialized=bytes[5];result.device_created=bytes[6];
 result.active=bytes[0x24];result.device_ready=bytes[0x25];result.in_size_move=bytes[0x1b0];std::memcpy(&result.saved_style,bytes+0x164,sizeof(result.saved_style));result.reason="exact_retail_read_only_owner_chain";return result;
}
std::string GameWindowOwner::json() const {
 if(!known)return "{\"known\":false,\"reason\":"+quote(reason)+"}";
 std::ostringstream o;o<<"{\"known\":true,\"reason\":"<<quote(reason)<<",\"address\":"<<address<<",\"windowed\":"<<windowed<<",\"presentation_windowed\":"<<pp_windowed
  <<",\"initialized\":"<<initialized<<",\"device_created\":"<<device_created<<",\"active\":"<<active<<",\"device_ready\":"<<device_ready<<",\"in_size_move\":"<<in_size_move<<",\"saved_style\":"<<saved_style<<'}';return o.str();
}
int camera_scene_family(const D3DMATRIX& source) noexcept {
 SavedFP fp;if(!symmetric_lh(source))return -1;double angle=source_camera_angle(source);
 if(std::abs(angle-90.)<=SOURCE_CAMERA_TOLERANCE_DEGREES)return 1;
 if(std::abs(angle-45.)<=SOURCE_CAMERA_TOLERANCE_DEGREES)return 0;
 return -1;
}
QualityPipeline::~QualityPipeline(){begin_shutdown();}
void QualityPipeline::begin_shutdown() noexcept {if(shutting_down_)return;shutting_down_=true;window_owned_=false;if(cursor_.hidden||free_camera_cursor_hidden_){if(!GetCursor())SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));cursor_.hidden=false;free_camera_cursor_hidden_=false;saved_cursor_=nullptr;}display_breadcrumb("shutdown_skip_window_restore");}
void QualityPipeline::configure(const VisualConfig& c,bool ui_supported,UINT a,D3DDEVTYPE t,HWND w){
 config=c;adapter=a;type=t;focus=w;display=c.display_mode;display_reason=c.display_reason;aa_reason=c.aa_reason;
 normal_target_width_=normal_target_height_=exclusive_width_=exclusive_height_=0;normal_target_valid_=false;
 initial_window_commit_complete_=false;
 planned_normal_target_width_=planned_normal_target_height_=0;planned_normal_target_valid_=planned_normal_target_update_=planned_live_resize_=false;
 exclusive_rejected_=false;window_state_="unknown";window_transition_key_.clear();windowed_target_reason_="uninitialized";
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
void QualityPipeline::cursor_focus_lost() noexcept {
 bool hidden=cursor_.hidden||free_camera_cursor_hidden_;cursor_.update(false,POINT{},GetTickCount64(),config.cursor_delay_ms);free_camera_cursor_hidden_=false;
 if(hidden&&!GetCursor())SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));saved_cursor_=nullptr;
}
void QualityPipeline::cursor_tick() noexcept {
 if(shutting_down_)return;POINT p{};RECT r{};HWND w=effective.hDeviceWindow?effective.hDeviceWindow:focus;
 bool freecam=free_camera_cursor&&w&&GetForegroundWindow()==w&&!IsIconic(w);
 if(freecam){if(!free_camera_cursor_hidden_&&!cursor_.hidden)saved_cursor_=GetCursor();free_camera_cursor_hidden_=true;SetCursor(nullptr);return;}
 if(free_camera_cursor_hidden_){free_camera_cursor_hidden_=false;if(!cursor_.hidden){if(!GetCursor())SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));saved_cursor_=nullptr;}}
 bool inside=config.auto_hide_cursor&&(display=="Borderless"||display=="ExclusiveFullscreen")&&GetForegroundWindow()==w&&GetCursorPos(&p)&&GetWindowRect(w,&r)&&PtInRect(&r,p);
 int action=cursor_.update(inside,p,GetTickCount64(),config.cursor_delay_ms);
 if(action<0){saved_cursor_=GetCursor();SetCursor(nullptr);}
 else if(action>0){if(!GetCursor())SetCursor(saved_cursor_?saved_cursor_:LoadCursorW(nullptr,MAKEINTRESOURCEW(32512)));saved_cursor_=nullptr;}
 else if(cursor_.hidden)SetCursor(nullptr); // WM_SETCURSOR may have installed the stock handle; display counter is untouched.
}
bool QualityPipeline::select_display(IDirect3D8& root,D3DPRESENT_PARAMETERS& p){
 planned_normal_target_width_=planned_normal_target_height_=0;planned_normal_target_valid_=planned_normal_target_update_=planned_live_resize_=false;
 windowed_target_reason_="not_windowed";
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
   const LONG client_width=current.client.right-current.client.left,client_height=current.client.bottom-current.client.top;
   const bool client_valid=!current.minimized&&client_width>0&&client_height>0&&client_width<=16384&&client_height<=16384;
   const bool initial_target=!normal_target_valid_;
   UINT normal_width=normal_target_valid_?normal_target_width_:(config.width?config.width:(p.BackBufferWidth?p.BackBufferWidth:(client_valid?static_cast<UINT>(client_width):0)));
   UINT normal_height=normal_target_valid_?normal_target_height_:(config.height?config.height:(p.BackBufferHeight?p.BackBufferHeight:(client_valid?static_cast<UINT>(client_height):0)));
   if(!normal_width||!normal_height||normal_width>16384||normal_height>16384){display_reason="invalid_effective_dimensions_stock";return false;}
   planned_normal_target_width_=normal_width;planned_normal_target_height_=normal_height;planned_normal_target_valid_=true;
   planned_normal_target_update_=initial_target;windowed_target_reason_=initial_target?(config.width?"initial_configured_target":"initial_game_or_client_target"):"accepted_normal_target";
   if(initial_target){
    RECT bounds{0,0,static_cast<LONG>(normal_width),static_cast<LONG>(normal_height)};
    LONG ws=(current.style&(WS_VISIBLE|WS_DISABLED|WS_CLIPCHILDREN|WS_CLIPSIBLINGS))|WS_OVERLAPPEDWINDOW;
    LONG ex=current.exstyle&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE|WS_EX_CLIENTEDGE|WS_EX_DLGMODALFRAME);
    auto work=current.work.right>current.work.left?current.work:current.monitor;
    if(!AdjustWindowRectEx(&bounds,ws,current.menu!=nullptr,ex)||bounds.right-bounds.left>work.right-work.left||bounds.bottom-bounds.top>work.bottom-work.top){display_reason="windowed_initial_client_exceeds_work_area_stock";return false;}
   }
   const char* admission=windowed_resize_decision(requested,current);
   if(current.minimized||!client_valid)windowed_target_reason_=initial_target?windowed_target_reason_:"minimized_or_zero_client_saved_target";
   if(current.maximized&&client_valid){p.BackBufferWidth=static_cast<UINT>(client_width);p.BackBufferHeight=static_cast<UINT>(client_height);windowed_target_reason_="maximized_os_client";}
   else if(!std::strcmp(admission,"accepted_hwnd_client_change")){
    p.BackBufferWidth=static_cast<UINT>(client_width);p.BackBufferHeight=static_cast<UINT>(client_height);
    // Validate the original Reset against the HWND, before removing echoed
    // overrides. An unchanged axis may equal both our effective override and
    // a genuine user size. Once admitted, both axes belong to the new game
    // viewport domain, rather than a hybrid of old logical and new OS sizes.
    fallback_.BackBufferWidth=p.BackBufferWidth;fallback_.BackBufferHeight=p.BackBufferHeight;
    planned_normal_target_width_=p.BackBufferWidth;planned_normal_target_height_=p.BackBufferHeight;planned_normal_target_update_=true;planned_live_resize_=true;
    windowed_target_reason_="corroborated_live_resize";
   }else {p.BackBufferWidth=normal_width;p.BackBufferHeight=normal_height;}
   windowed_admission(p,admission);
 }else {
  // Exclusive owns a display mode, never the decorated HWND's transient client.
  p.BackBufferWidth=config.width?config.width:exclusive_width_?exclusive_width_:p.BackBufferWidth?p.BackBufferWidth:desktop.Width;
  p.BackBufferHeight=config.height?config.height:exclusive_height_?exclusive_height_:p.BackBufferHeight?p.BackBufferHeight:desktop.Height;
 }
 if(!p.BackBufferWidth||!p.BackBufferHeight||p.BackBufferWidth>16384||p.BackBufferHeight>16384){display_reason="invalid_effective_dimensions_stock";return false;}
 if(display=="ExclusiveFullscreen"){
  D3DDISPLAYMODE selected{};bool found=false;UINT count=root.GetAdapterModeCount(adapter);
  for(UINT i=0;i<std::min(count,UINT(65536));++i){D3DDISPLAYMODE mode{};if(FAILED(root.EnumAdapterModes(adapter,i,&mode)))continue;
   if(mode.Width!=p.BackBufferWidth||mode.Height!=p.BackBufferHeight||(config.refresh&&mode.RefreshRate!=config.refresh))continue;
   if(mode.Format!=p.BackBufferFormat&&mode.Format!=desktop.Format)continue;
   if(FAILED(root.CheckDeviceType(adapter,type,mode.Format,mode.Format,FALSE)))continue;
   if(!found||mode.Format==p.BackBufferFormat){selected=mode;found=true;if(config.refresh||mode.RefreshRate==desktop.RefreshRate)break;}
  }
  if(!found){display_reason="exclusive_mode_format_refresh_unavailable_rejected";return false;}
  if(p.EnableAutoDepthStencil&&(FAILED(root.CheckDeviceFormat(adapter,type,selected.Format,D3DUSAGE_DEPTHSTENCIL,D3DRTYPE_SURFACE,p.AutoDepthStencilFormat))||FAILED(root.CheckDepthStencilMatch(adapter,type,selected.Format,selected.Format,p.AutoDepthStencilFormat)))){display_reason="exclusive_depth_format_pair_unavailable_rejected";return false;}
  p.Windowed=FALSE;p.BackBufferFormat=selected.Format;p.FullScreen_RefreshRateInHz=config.refresh?selected.RefreshRate:0;
  p.FullScreen_PresentationInterval=D3DPRESENT_INTERVAL_DEFAULT;
 }else {p.Windowed=TRUE;p.BackBufferFormat=desktop.Format;p.FullScreen_RefreshRateInHz=0;p.FullScreen_PresentationInterval=D3DPRESENT_INTERVAL_DEFAULT;
  if(FAILED(root.CheckDeviceType(adapter,type,desktop.Format,p.BackBufferFormat,TRUE))){display_reason="windowed_format_unavailable_stock";return false;}
 }
 return true;
}
bool QualityPipeline::apply_window(const D3DPRESENT_PARAMETERS& p){
 if(display=="ExclusiveFullscreen"){
  // D3D8/the game own exclusive display, style, placement and focus. No popup
  // conversion or SetWindowPos after Create/Reset; that caused real reentrant resets.
  windows_->snapshot(p.hDeviceWindow?p.hDeviceWindow:focus,committed_);current=committed_;window_commit_status_="exclusive_native_owned";display_breadcrumb("exclusive_skip_window_commit");return true;
 }
 if(display=="Stock"){restore_window();committed_={};window_commit_status_="not_required";return true;}
 WindowState now{};if(!windows_->snapshot(p.hDeviceWindow?p.hDeviceWindow:focus,now)){display_reason="window_commit_snapshot_failed";window_commit_status_="failed_snapshot";return false;}
 if(display=="Windowed"){
  const LONG client_width=now.client.right-now.client.left,client_height=now.client.bottom-now.client.top;
  if(now.maximized||now.minimized||client_width<=0||client_height<=0){
   // Windows owns maximized/minimized placement. A zero-size client is never
   // adopted as a normal target and must not trigger a window commit.
   current=committed_=now;window_commit_status_=now.maximized?"maximized_os_owned":"minimized_or_zero_client_os_owned";window_transition(now);return true;
  }
  const bool normal_style=committed_.valid&&now.hwnd==committed_.hwnd&&now.style==committed_.style&&now.exstyle==committed_.exstyle&&now.menu==committed_.menu&&
   (now.style&WS_CAPTION)==WS_CAPTION&&(now.style&WS_POPUP)==0;
  const bool client_matches=client_width==static_cast<LONG>(p.BackBufferWidth)&&client_height==static_cast<LONG>(p.BackBufferHeight);
  if(normal_style&&client_matches){
   // A normal user move or resize owns outer placement. Accept its fresh
   // snapshot instead of recentering because the outer rectangle changed.
   current=committed_=now;initial_window_commit_complete_=true;window_commit_status_="windowed_os_geometry_accepted";window_transition(now);display_breadcrumb("windowed_os_geometry_accepted");return true;
  }
 }
 bool unchanged=committed_.valid&&now.hwnd==committed_.hwnd&&now.style==committed_.style&&now.exstyle==committed_.exstyle&&now.menu==committed_.menu&&
  !std::memcmp(&now.outer,&committed_.outer,sizeof(RECT))&&!std::memcmp(&now.client,&committed_.client,sizeof(RECT))&&
  now.client.right==static_cast<LONG>(p.BackBufferWidth)&&now.client.bottom==static_cast<LONG>(p.BackBufferHeight)&&
  ((display=="Windowed")==((now.style&WS_CAPTION)==WS_CAPTION))&&
  (display!="Borderless"||!std::memcmp(&now.outer,&now.monitor,sizeof(RECT)));
 if(unchanged){if(display=="Windowed")initial_window_commit_complete_=true;window_commit_status_="unchanged";window_transition(now);display_breadcrumb("window_commit_unchanged");return true;}
 current=now;RECT r=current.monitor;bool client=display=="Windowed";
 if(client){r.left=current.outer.left;r.top=current.outer.top;r.right=r.left+p.BackBufferWidth;r.bottom=r.top+p.BackBufferHeight;}

 display_breadcrumb("window_commit_begin");committing_=true;
 bool okay=windows_->apply(current,r,client,!client);
 if(!okay){window_commit_status_="failed_rollback_restored";if(!windows_->restore(now)){window_owned_=true;window_commit_status_="failed_rollback_unverified";display_breadcrumb("window_commit_rollback_failed",E_FAIL);}committing_=false;display_reason="window_commit_failed_native_parameters_retained";display_breadcrumb("window_commit_failed",E_FAIL);return false;}
 committing_=false;window_owned_=true;window_commit_status_="committed";bool synchronized=windows_->snapshot(current.hwnd,committed_)&&committed_.valid&&committed_.client.right-committed_.client.left==static_cast<LONG>(p.BackBufferWidth)&&committed_.client.bottom-committed_.client.top==static_cast<LONG>(p.BackBufferHeight);if(display=="Windowed")initial_window_commit_complete_=synchronized;window_transition(committed_);display_breadcrumb("window_commit_complete");return true;
}
void QualityPipeline::window_transition(const WindowState& state) noexcept {
 if(display!="Windowed"||!state.valid)return;
 const char* next=state.maximized?"maximized":(state.minimized?"minimized":"normal");
 const LONG client_width=state.client.right-state.client.left,client_height=state.client.bottom-state.client.top;
 const std::string key=std::string(next)+":"+std::to_string(normal_target_width_)+"x"+std::to_string(normal_target_height_)+":"+
  std::to_string(client_width)+"x"+std::to_string(client_height)+":"+std::to_string(effective.BackBufferWidth)+"x"+std::to_string(effective.BackBufferHeight);
 if(window_transition_key_==key)return;window_transition_key_=key;window_state_=next;
 try{session().write("{\"type\":\"window_state_transition\",\"event_sequence\":"+std::to_string(display_event_id())+",\"device_lifetime_id\":"+std::to_string(device_lifetime_id_)+",\"successful_reset_epoch\":"+std::to_string(successful_reset_epoch_)+",\"window_state\":"+quote(next)+",\"normal_target\":{\"width\":"+std::to_string(normal_target_width_)+",\"height\":"+std::to_string(normal_target_height_)+"},\"actual_client\":{\"width\":"+std::to_string(client_width)+",\"height\":"+std::to_string(client_height)+"},\"effective_backbuffer\":{\"width\":"+std::to_string(effective.BackBufferWidth)+",\"height\":"+std::to_string(effective.BackBufferHeight)+"},\"target_source\":"+quote(windowed_target_reason_)+"}");}catch(...){}
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
 exclusive_rejected_=false;
 if(config.display_mode!="Stock"&&!select_display(root,p)){p=fallback_;if(config.display_mode=="ExclusiveFullscreen"){exclusive_rejected_=true;display="ExclusiveFullscreen";return p;}display="Stock";}
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
const char* QualityPipeline::windowed_resize_decision(const D3DPRESENT_PARAMETERS& input,const WindowState& state) const noexcept {
 if(display!="Windowed")return "not_windowed";
 if(committing_)return "renderer_window_commit_echo";
 if(shutting_down_)return "shutdown_or_echo_probe";
 if(!state.valid)return "hwnd_snapshot_unavailable";
 if(state.maximized)return "maximized_os_client";
 if(state.minimized)return "minimized_client";
 if(!normal_target_valid_)return "initial_normal_target_not_initialized";
 if(!initial_window_commit_complete_)return "initial_window_commit_not_complete";
 if(!committed_.valid||state.hwnd!=committed_.hwnd)return "committed_hwnd_identity_mismatch";
 const LONG width=state.client.right-state.client.left,height=state.client.bottom-state.client.top;
 if(width<=0||height<=0||width>16384||height>16384)return "unsupported_or_zero_client_size";
 if(input.BackBufferWidth!=static_cast<UINT>(width)||input.BackBufferHeight!=static_cast<UINT>(height))return "original_request_not_corroborated_by_hwnd";
 if(width==static_cast<LONG>(normal_target_width_)&&height==static_cast<LONG>(normal_target_height_))return "unchanged_normal_target";
 const LONG old_width=committed_.client.right-committed_.client.left,old_height=committed_.client.bottom-committed_.client.top;
 if(width==old_width&&height==old_height)return "unchanged_committed_client";
 // The engine request must match a real normal-client transition while the
 // last accepted style, extended style, menu and HWND identity remain intact.
 if(state.style!=committed_.style||state.exstyle!=committed_.exstyle||state.menu!=committed_.menu)return "committed_style_or_menu_mismatch";
 if((state.style&WS_CAPTION)!=WS_CAPTION||(state.style&(WS_POPUP|WS_CHILD)))return "not_decorated_normal_window";
 return "accepted_hwnd_client_change";
}
void QualityPipeline::accept_planned_windowed_target() noexcept {
 if(display=="Windowed"&&planned_normal_target_valid_&&planned_normal_target_update_){
  normal_target_width_=planned_normal_target_width_;normal_target_height_=planned_normal_target_height_;normal_target_valid_=true;
  if(planned_live_resize_)++windowed_resize_admissions;
 }
 planned_normal_target_valid_=planned_normal_target_update_=planned_live_resize_=false;
}
D3DPRESENT_PARAMETERS QualityPipeline::without_aa(D3DPRESENT_PARAMETERS p) const noexcept {p.MultiSampleType=fallback_.MultiSampleType;p.SwapEffect=fallback_.SwapEffect;p.BackBufferCount=fallback_.BackBufferCount;p.Flags=fallback_.Flags;return p;}
HRESULT QualityPipeline::create(IDirect3D8& root,DWORD flags,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice8** out){
 if(!device_lifetime_id_)device_lifetime_id_=allocate_display_device_id();
 creating_thread_id_=GetCurrentThreadId();
 D3DPRESENT_PARAMETERS input{};bool have=pp&&safe_copy(&input,pp,sizeof(input));
 if(!active()||!have){if(have){requested=fallback_=input;}HRESULT hr=root.CreateDevice(adapter,type,focus,flags,pp,out);D3DPRESENT_PARAMETERS post{};if(have&&safe_copy(&post,pp,sizeof(post)))native_attempt("CreateDevice",input,post,hr);if(SUCCEEDED(hr)&&pp&&safe_copy(&effective,pp,sizeof(effective)))valid=true;return hr;}
 auto candidate=plan(root,input);attempts=0;if(exclusive_rejected_){native_attempt("CreateDevice_validation_rejected",input,input,D3DERR_NOTAVAILABLE);return D3DERR_NOTAVAILABLE;}
 attempts=1;auto sent=candidate;auto invoke=[&](){auto before=sent;native_begin("CreateDevice",before);display_breadcrumb("native_CreateDevice_begin");auto result=root.CreateDevice(adapter,type,focus,flags,&sent,out);native_attempt("CreateDevice",before,sent,result);display_breadcrumb("native_CreateDevice_end",result);return result;};HRESULT hr=invoke();
 if(FAILED(hr)&&!lost(hr)&&candidate.MultiSampleType!=fallback_.MultiSampleType){candidate=without_aa(candidate);sent=candidate;++attempts;aa_reason="native_create_rejected_msaa_stock";hr=invoke();}
 if(FAILED(hr)&&!lost(hr)&&config.display_mode!="ExclusiveFullscreen"&&std::memcmp(&candidate,&fallback_,sizeof(candidate))){display="Stock";display_reason="native_create_rejected_display_stock";sent=fallback_;++attempts;hr=invoke();}
 if(SUCCEEDED(hr)){effective=sent;valid=true;modified=std::memcmp(&effective,&fallback_,sizeof(effective))!=0;if(display=="ExclusiveFullscreen"){exclusive_width_=sent.BackBufferWidth;exclusive_height_=sent.BackBufferHeight;}accept_planned_windowed_target();safe_copy(pp,&sent,sizeof(sent));if(out&&*out)observe(**out);apply_window(sent);}else{planned_normal_target_valid_=planned_normal_target_update_=planned_live_resize_=false;}return hr;
}
HRESULT QualityPipeline::reset(IDirect3D8& root,IDirect3DDevice8& device,D3DPRESENT_PARAMETERS* pp){
 if(!device_lifetime_id_)device_lifetime_id_=allocate_display_device_id();
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
  if(!active()||!have){if(have){requested=fallback_=input;}++native_reset_calls;HRESULT hr=device.Reset(pp);if(SUCCEEDED(hr))++successful_reset_epoch_;D3DPRESENT_PARAMETERS post{};if(have&&safe_copy(&post,pp,sizeof(post)))native_attempt("Reset",input,post,hr);if(SUCCEEDED(hr)&&pp&&safe_copy(&effective,pp,sizeof(effective)))valid=true;if(FAILED(hr))failed();return hr;}
 auto candidate=plan(root,input);attempts=0;if(exclusive_rejected_){native_attempt("Reset_validation_rejected",input,input,D3DERR_NOTAVAILABLE);failed();return D3DERR_NOTAVAILABLE;}
  attempts=1;auto sent=candidate;auto invoke=[&](){auto before=sent;native_begin("Reset",before);reset_readiness(device,before);display_breadcrumb("native_Reset_begin");++native_reset_calls;auto result=device.Reset(&sent);if(SUCCEEDED(result))++successful_reset_epoch_;native_attempt("Reset",before,sent,result);display_breadcrumb("native_Reset_end",result);return result;};HRESULT hr=invoke();
 if(FAILED(hr)&&!lost(hr)&&candidate.MultiSampleType!=fallback_.MultiSampleType){candidate=without_aa(candidate);sent=candidate;++attempts;aa_reason="native_reset_rejected_msaa_stock";hr=invoke();}
 if(FAILED(hr)&&!lost(hr)&&config.display_mode!="ExclusiveFullscreen"&&std::memcmp(&candidate,&fallback_,sizeof(candidate))){display="Stock";display_reason="native_reset_rejected_display_stock";sent=fallback_;++attempts;hr=invoke();}
 if(SUCCEEDED(hr)){effective=sent;valid=true;modified=std::memcmp(&effective,&fallback_,sizeof(effective))!=0;if(display=="ExclusiveFullscreen"){exclusive_width_=sent.BackBufferWidth;exclusive_height_=sent.BackBufferHeight;}accept_planned_windowed_target();safe_copy(pp,&sent,sizeof(sent));observe(device);ui_projection_live=false;apply_window(sent);}else{failed();planned_normal_target_valid_=planned_normal_target_update_=planned_live_resize_=false;}return hr;
}
void QualityPipeline::cooperative_result(HRESULT hr) noexcept {
 if(cooperative_.known&&cooperative_.value==hr)return;cooperative_.set(hr);if(cooperative_records_>=64)return;++cooperative_records_;
 try{session().write("{\"type\":\"display_cooperative_transition\",\"event_sequence\":"+std::to_string(display_event_id())+",\"device_lifetime_id\":"+std::to_string(device_lifetime_id_)+",\"successful_reset_epoch\":"+std::to_string(successful_reset_epoch_)+",\"display\":"+quote(display)+",\"hresult\":"+std::to_string(static_cast<uint32_t>(hr))+",\"policy\":\"forward_unchanged_game_owns_retry\",\"window_context\":"+window_context_json(effective.hDeviceWindow?effective.hDeviceWindow:focus)+"}");}catch(...){}
}
void QualityPipeline::reset_readiness(IDirect3DDevice8& device,const D3DPRESENT_PARAMETERS& sent) noexcept {
 if(display!="ExclusiveFullscreen")return;
 reset_readiness_={};const bool thread_ok=creating_thread_id_&&creating_thread_id_==GetCurrentThreadId();
 if(thread_ok)reset_readiness_.set(device.TestCooperativeLevel());
 if(attempt_records_>=128)return;
 try{session().write("{\"type\":\"display_reset_readiness\",\"event_sequence\":"+std::to_string(display_event_id())+",\"device_lifetime_id\":"+std::to_string(device_lifetime_id_)+",\"successful_reset_epoch\":"+std::to_string(successful_reset_epoch_)+",\"requested_display_mode\":"+quote(config.display_mode)+",\"effective_display_mode\":"+quote(display)+",\"native_windowed_flag\":"+std::to_string(sent.Windowed)+",\"cooperative_hresult\":"+(reset_readiness_.known?std::to_string(static_cast<uint32_t>(reset_readiness_.value)):"null")+",\"cooperative_query_reason\":"+quote(thread_ok?"same_creation_thread_immediately_before_native_reset":"creation_thread_unknown_or_mismatch")+",\"requested\":"+pp_json(requested)+",\"sent\":"+pp_json(sent)+",\"window_context\":"+window_context_json(sent.hDeviceWindow?sent.hDeviceWindow:focus)+",\"transition_stack\":"+transition_stack_json()+",\"policy\":\"diagnostic_only_no_retry_no_hresult_translation\"}");}catch(...){}
}
void QualityPipeline::windowed_admission(const D3DPRESENT_PARAMETERS& sent,const char* decision) noexcept {
 if(shutting_down_||admission_records_>=128)return;++admission_records_;
 try{
  const auto& s=current;auto rect=[](const RECT& r){return "["+std::to_string(r.left)+","+std::to_string(r.top)+","+std::to_string(r.right)+","+std::to_string(r.bottom)+"]";};
  const LONG width=s.client.right-s.client.left,height=s.client.bottom-s.client.top;
  const bool candidate=requested.BackBufferWidth&&requested.BackBufferHeight&&requested.BackBufferWidth<=16384&&requested.BackBufferHeight<=16384;
  std::ostringstream o;o<<"{\"type\":\"windowed_resize_admission\",\"event_sequence\":"<<display_event_id()<<",\"device_lifetime_id\":"<<device_lifetime_id_<<",\"successful_reset_epoch\":"<<successful_reset_epoch_
   <<",\"display_mode\":"<<quote(display)<<",\"configured_initial_width\":"<<config.width<<",\"configured_initial_height\":"<<config.height<<",\"requested\":"<<pp_json(requested)<<",\"normalized_logical\":"<<pp_json(fallback_)
   <<",\"actual_client_width\":"<<width<<",\"actual_client_height\":"<<height<<",\"current_normal_width\":"<<normal_target_width_<<",\"current_normal_height\":"<<normal_target_height_
   <<",\"is_maximized\":"<<(s.maximized?"true":"false")<<",\"is_minimized\":"<<(s.minimized?"true":"false")<<",\"window_style\":"<<static_cast<uint32_t>(s.style)<<",\"window_exstyle\":"<<static_cast<uint32_t>(s.exstyle)
   <<",\"previous_committed_style\":"<<static_cast<uint32_t>(committed_.style)<<",\"previous_committed_exstyle\":"<<static_cast<uint32_t>(committed_.exstyle)
   <<",\"window_commit_active\":"<<(committing_?"true":"false")<<",\"initial_window_commit_complete\":"<<(initial_window_commit_complete_?"true":"false")<<",\"normal_target_initialized\":"<<(normal_target_valid_?"true":"false")
   <<",\"previous_committed_client\":"<<rect(committed_.client)<<",\"previous_committed_outer\":"<<rect(committed_.outer)<<",\"resize_candidate_valid\":"<<(candidate?"true":"false")
   <<",\"resize_corroborated_by_hwnd\":"<<(candidate&&!s.minimized&&requested.BackBufferWidth==static_cast<UINT>(width)&&requested.BackBufferHeight==static_cast<UINT>(height)?"true":"false")
   <<",\"decision\":"<<quote(decision)<<",\"accepted_target_source\":"<<quote(windowed_target_reason_)<<",\"planned_target_update\":"<<(planned_normal_target_update_?"true":"false")<<",\"effective_backbuffer_width\":"<<sent.BackBufferWidth<<",\"effective_backbuffer_height\":"<<sent.BackBufferHeight<<'}';session().write(o.str());
 }catch(...){}
}
std::string QualityPipeline::window_context_json(HWND hwnd) const {
 try{
  WindowState state{};bool have=windows_&&windows_->snapshot(hwnd,state)&&state.valid;
  auto handle=[](HWND w){return static_cast<uint64_t>(reinterpret_cast<uintptr_t>(w));};
  std::ostringstream o;o<<"{\"device_window\":"<<handle(hwnd)<<",\"focus_window\":"<<handle(focus)
   <<",\"foreground_window\":"<<handle(GetForegroundWindow())<<",\"active_window\":"<<handle(GetActiveWindow())
   <<",\"focus_handle\":"<<handle(GetFocus());
  if(have)o<<",\"style\":"<<static_cast<uint32_t>(state.style)<<",\"exstyle\":"<<static_cast<uint32_t>(state.exstyle)
   <<",\"is_zoomed\":"<<(state.maximized?"true":"false")<<",\"is_iconic\":"<<(state.minimized?"true":"false")
   <<",\"window_rect\":["<<state.outer.left<<','<<state.outer.top<<','<<state.outer.right<<','<<state.outer.bottom<<']'
   <<",\"client_rect\":["<<state.client.left<<','<<state.client.top<<','<<state.client.right<<','<<state.client.bottom<<']';
  else o<<",\"style\":null,\"exstyle\":null,\"is_zoomed\":null,\"is_iconic\":null,\"window_rect\":null,\"client_rect\":null";
  auto game=inspect_game_window_owner(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),session().target,hwnd);
  o<<",\"window_commit_in_progress\":"<<(committing_?"true":"false")
   <<",\"game_windowed_flag_0x1c\":"<<(game.known?std::to_string(game.windowed):"null")<<",\"game_windowed_flag_reason\":"<<quote(game.reason)<<",\"game_window_owner\":"<<game.json()<<'}';
  return o.str();
 }catch(...){return "null";}
}
void QualityPipeline::native_attempt(const char* operation,const D3DPRESENT_PARAMETERS& before,const D3DPRESENT_PARAMETERS& after,HRESULT hr) noexcept {
 ++attempt_sequence_;if(attempt_records_>=128)return;++attempt_records_;
 try{HWND hwnd=before.hDeviceWindow?before.hDeviceWindow:(after.hDeviceWindow?after.hDeviceWindow:focus);session().write("{\"type\":\"display_native_attempt\",\"event_sequence\":"+std::to_string(display_event_id())+",\"device_lifetime_id\":"+std::to_string(device_lifetime_id_)+",\"successful_reset_epoch\":"+std::to_string(successful_reset_epoch_)+",\"sequence\":"+std::to_string(attempt_sequence_)+",\"operation\":"+quote(operation)+",\"display_requested\":"+quote(config.display_mode)+",\"display_effective\":"+quote(display)+",\"reason\":"+quote(display_reason)+",\"windowed_target_reason\":"+quote(windowed_target_reason_)+",\"windowed_target\":{\"width\":"+std::to_string(normal_target_width_)+",\"height\":"+std::to_string(normal_target_height_)+"},\"aa_requested\":"+quote(config.aa_mode)+",\"aa_requested_samples\":"+std::to_string(config.samples)+",\"aa_reason\":"+quote(aa_reason)+",\"requested\":"+pp_json(requested)+",\"sent\":"+pp_json(before)+",\"returned\":"+pp_json(after)+",\"window_context\":"+window_context_json(hwnd)+",\"hresult\":"+std::to_string(static_cast<uint32_t>(hr))+"}");}catch(...){}
}
void QualityPipeline::native_begin(const char* operation,const D3DPRESENT_PARAMETERS& sent) noexcept {
 if(attempt_records_>=128)return;
 try{session().write("{\"type\":\"display_native_begin\",\"event_sequence\":"+std::to_string(display_event_id())+",\"device_lifetime_id\":"+std::to_string(device_lifetime_id_)+",\"successful_reset_epoch\":"+std::to_string(successful_reset_epoch_)+",\"operation\":"+quote(operation)+",\"requested_display_mode\":"+quote(config.display_mode)+",\"effective_display_mode\":"+quote(display)+",\"native_windowed_flag\":"+std::to_string(sent.Windowed)+",\"requested\":"+pp_json(requested)+",\"sent\":"+pp_json(sent)+",\"transition_owner\":"+quote(committing_?"renderer_window_commit":"game_d3d_call")+",\"window_context\":"+window_context_json(sent.hDeviceWindow?sent.hDeviceWindow:focus)+"}");}catch(...){}
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
 std::ostringstream o;o<<"{\"device_lifetime_id\":"<<device_lifetime_id_<<",\"successful_reset_epoch\":"<<successful_reset_epoch_<<",\"window_state\":"<<quote(window_state_)<<",\"normal_target\":{\"width\":"<<normal_target_width_<<",\"height\":"<<normal_target_height_<<"},\"actual_client\":{\"width\":"<<(committed_.client.right-committed_.client.left)<<",\"height\":"<<(committed_.client.bottom-committed_.client.top)<<"},\"effective_backbuffer\":{\"width\":"<<effective.BackBufferWidth<<",\"height\":"<<effective.BackBufferHeight<<"},\"display_requested\":"<<quote(config.display_mode)<<",\"display_effective\":"<<quote(display)<<",\"display_reason\":"<<quote(display_reason)<<",\"cursor_auto_hide_effective\":"<<(config.auto_hide_cursor?"true":"false")<<",\"cursor_watch_installed\":"<<"false"<<",\"cursor_reason\":"<<quote(config.cursor_reason)<<",\"window_commit_status\":"<<quote(window_commit_status_)<<",\"native_reset_calls\":"<<native_reset_calls<<",\"window_reset_echoes\":"<<window_reset_echoes<<",\"window_reset_echoes_suppressed\":"<<window_reset_echoes_suppressed<<",\"deferred_resets\":"<<deferred_resets<<",\"windowed_target_width\":"<<normal_target_width_<<",\"windowed_target_height\":"<<normal_target_height_<<",\"windowed_target_reason\":"<<quote(windowed_target_reason_)<<",\"windowed_resize_admissions\":"<<windowed_resize_admissions<<",\"exclusive_target\":{\"width\":"<<exclusive_width_<<",\"height\":"<<exclusive_height_<<"},\"aa_effective\":"<<quote(valid&&effective.MultiSampleType!=D3DMULTISAMPLE_NONE?"MSAA":"Stock")<<",\"aa_effective_samples\":"<<(valid?effective.MultiSampleType:0)<<",\"aa_requested\":"<<quote(config.aa_mode)<<",\"aa_requested_samples\":"<<config.samples<<",\"aa_swap_effect\":"<<quote(valid&&effective.SwapEffect==D3DSWAPEFFECT_DISCARD?"DISCARD":valid&&effective.SwapEffect==D3DSWAPEFFECT_COPY?"COPY":"OTHER")<<",\"aa_reason\":"<<quote(aa_reason)<<",\"attempts\":"<<attempts<<",\"requested\":"<<pp_json(requested)<<",\"logical_baseline\":"<<pp_json(fallback_)<<",\"effective\":"<<(valid?pp_json(effective):"null")<<",\"monitor_rect\":["<<current.monitor.left<<','<<current.monitor.top<<','<<current.monitor.right<<','<<current.monitor.bottom<<"],\"physical_backbuffer\":";
 if(backbuffer_known)o<<"{\"width\":"<<backbuffer.Width<<",\"height\":"<<backbuffer.Height<<",\"format\":"<<backbuffer.Format<<",\"multisample\":"<<backbuffer.MultiSampleType<<'}';else o<<"null";
 o<<",\"physical_depth\":";if(depth_known)o<<"{\"width\":"<<depth.Width<<",\"height\":"<<depth.Height<<",\"format\":"<<depth.Format<<",\"multisample\":"<<depth.MultiSampleType<<'}';else o<<"null";
 double aspect=valid&&effective.BackBufferHeight?double(effective.BackBufferWidth)/effective.BackBufferHeight:0;
 o<<",\"effective_aspect\":"<<aspect<<",\"ui\":{\"mode\":"<<quote(config.interface_mode)<<",\"reason\":"<<quote(config.interface_reason)<<",\"logical_width\":640,\"logical_height\":480,\"virtual_width\":"<<480.*aspect<<",\"extra_width\":"<<480.*aspect-640.<<",\"center_offset\":"<<(480.*aspect-640.)*.5<<"},\"dpi_policy\":\"game_awareness_unchanged\",\"initial_window_commit_complete\":"<<(initial_window_commit_complete_?"true":"false")<<",\"normal_target_initialized\":"<<(normal_target_valid_?"true":"false")<<",\"display_watch\":"<<quote("disabled_by_standard_policy")<<",\"display_window_message_records\":"<<0<<",\"display_message_pending\":"<<0<<",\"display_message_dropped\":"<<0<<",\"thread_message_hooks_enabled\":false,\"cursor_handling\":\"present_polling_and_shutdown\",\"window_message_telemetry\":\"unavailable_hooks_retired\""<<",\"last_reset_readiness\":"<<(reset_readiness_.known?std::to_string(static_cast<uint32_t>(reset_readiness_.value)):"null")<<'}';return o.str();
}
}
