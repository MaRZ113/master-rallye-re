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
class NativeWindows final:public WindowApi {
 bool style(HWND w,int index,LONG value) noexcept {SetLastError(0);return SetWindowLongW(w,index,value)!=0||GetLastError()==0;}
public:
 bool snapshot(HWND w,WindowState& s) noexcept override {
  s={};if(!IsWindow(w))return false;MONITORINFO m{sizeof(m)};
  if(!GetWindowRect(w,&s.outer)||!GetClientRect(w,&s.client)||!GetMonitorInfoW(MonitorFromWindow(w,MONITOR_DEFAULTTONEAREST),&m))return false;
  s.hwnd=w;s.style=GetWindowLongW(w,GWL_STYLE);s.exstyle=GetWindowLongW(w,GWL_EXSTYLE);s.menu=GetMenu(w);s.monitor=m.rcMonitor;s.valid=true;return true;
 }
 bool apply(const WindowState& s,const RECT& desired,bool client,bool popup) noexcept override {
  if(!s.valid)return false;
  LONG ws=(s.style&(WS_VISIBLE|WS_DISABLED|WS_CLIPCHILDREN|WS_CLIPSIBLINGS))|(popup?WS_POPUP:WS_OVERLAPPEDWINDOW);
  LONG ex=s.exstyle&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE|WS_EX_CLIENTEDGE|WS_EX_DLGMODALFRAME);
  RECT r=desired;HMENU menu=popup?nullptr:s.menu;
  if(client&&!AdjustWindowRectEx(&r,ws,menu!=nullptr,ex))return false;
  if(!style(s.hwnd,GWL_STYLE,ws)||!style(s.hwnd,GWL_EXSTYLE,ex)||!SetMenu(s.hwnd,menu))return false;
  if(!SetWindowPos(s.hwnd,HWND_NOTOPMOST,r.left,r.top,r.right-r.left,r.bottom-r.top,SWP_FRAMECHANGED|SWP_NOACTIVATE|SWP_NOOWNERZORDER))return false;
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
WindowApi& native_window_api() noexcept{return native_windows;}
QualityPipeline::~QualityPipeline(){restore_window();}
void QualityPipeline::configure(const VisualConfig& c,bool exact,UINT a,D3DDEVTYPE t,HWND w){
 config=c;adapter=a;type=t;focus=w;display=c.display_mode;display_reason=c.display_reason;aa_reason=c.aa_reason;
 if(!exact){config.display_mode=config.aa_mode="Stock";config.interface_mode="Stock";config.menu_freeze=false;display="Stock";display_reason=aa_reason="unsupported_build";}
}
void QualityPipeline::restore_window() noexcept {
 if(window_owned_){if(windows_->restore(original))window_owned_=false;else {try{session().write("{\"type\":\"window_restore_failed\"}");}catch(...){}}}
}
bool QualityPipeline::select_display(IDirect3D8& root,D3DPRESENT_PARAMETERS& p){
 display=config.display_mode;if(display=="Stock")return true;
 if(!windows_->snapshot(p.hDeviceWindow?p.hDeviceWindow:focus,current)){display_reason="invalid_window_or_monitor_stock";return false;}
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
 if(display=="Stock")return true;
 RECT r=current.monitor;bool client=display=="Windowed";
 if(client){r.left=current.outer.left;r.top=current.outer.top;r.right=r.left+p.BackBufferWidth;r.bottom=r.top+p.BackBufferHeight;}
 else if(display=="ExclusiveFullscreen"){r.right=r.left+p.BackBufferWidth;r.bottom=r.top+p.BackBufferHeight;}
 window_owned_=true;
 if(!windows_->apply(current,r,client,!client)){restore_window();display_reason="window_transaction_failed_stock";return false;}
 return true;
}
D3DPRESENT_PARAMETERS QualityPipeline::plan(IDirect3D8& root,const D3DPRESENT_PARAMETERS& source){
 auto logical=source;
 if(valid&&modified){
  // Reset may echo the effective descriptor returned by our preceding call.
  // Remove only fields still exactly equal to our own override; retain new game requests.
  #define UNMIX(field) if(source.field==effective.field&&effective.field!=fallback_.field)logical.field=fallback_.field
  UNMIX(BackBufferWidth);UNMIX(BackBufferHeight);UNMIX(BackBufferFormat);UNMIX(BackBufferCount);UNMIX(MultiSampleType);UNMIX(SwapEffect);UNMIX(hDeviceWindow);UNMIX(Windowed);UNMIX(Flags);UNMIX(FullScreen_RefreshRateInHz);UNMIX(FullScreen_PresentationInterval);
  #undef UNMIX
 }
 requested=source;fallback_=logical;viewport_domain_known=false;auto p=logical;
 if(config.display_mode!="Stock"&&(!select_display(root,p)||!apply_window(p))){p=fallback_;display="Stock";restore_window();}
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
 return p;
}
D3DPRESENT_PARAMETERS QualityPipeline::without_aa(D3DPRESENT_PARAMETERS p) const noexcept {p.MultiSampleType=fallback_.MultiSampleType;p.SwapEffect=fallback_.SwapEffect;p.BackBufferCount=fallback_.BackBufferCount;p.Flags=fallback_.Flags;return p;}
HRESULT QualityPipeline::create(IDirect3D8& root,DWORD flags,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice8** out){
 D3DPRESENT_PARAMETERS input{};bool have=pp&&safe_copy(&input,pp,sizeof(input));
 if(!active()||!have){if(have){requested=fallback_=input;}HRESULT hr=root.CreateDevice(adapter,type,focus,flags,pp,out);if(SUCCEEDED(hr)&&pp&&safe_copy(&effective,pp,sizeof(effective)))valid=true;return hr;}
 auto candidate=plan(root,input);attempts=1;auto sent=candidate;HRESULT hr=root.CreateDevice(adapter,type,focus,flags,&sent,out);
 if(FAILED(hr)&&!lost(hr)&&candidate.MultiSampleType!=fallback_.MultiSampleType){candidate=without_aa(candidate);sent=candidate;++attempts;aa_reason="native_create_rejected_msaa_stock";hr=root.CreateDevice(adapter,type,focus,flags,&sent,out);}
 if(FAILED(hr)&&!lost(hr)&&std::memcmp(&candidate,&fallback_,sizeof(candidate))){restore_window();display="Stock";display_reason="native_create_rejected_display_stock";sent=fallback_;++attempts;hr=root.CreateDevice(adapter,type,focus,flags,&sent,out);}
 if(SUCCEEDED(hr)){effective=sent;valid=true;modified=std::memcmp(&effective,&fallback_,sizeof(effective))!=0;safe_copy(pp,&sent,sizeof(sent));if(out&&*out)observe(**out);}else restore_window();return hr;
}
HRESULT QualityPipeline::reset(IDirect3D8& root,IDirect3DDevice8& device,D3DPRESENT_PARAMETERS* pp){
 D3DPRESENT_PARAMETERS input{};bool have=pp&&safe_copy(&input,pp,sizeof(input));
 if(!active()||!have){if(have){requested=fallback_=input;}HRESULT hr=device.Reset(pp);if(SUCCEEDED(hr)&&pp&&safe_copy(&effective,pp,sizeof(effective)))valid=true;return hr;}
 auto candidate=plan(root,input);attempts=1;auto sent=candidate;HRESULT hr=device.Reset(&sent);
 if(FAILED(hr)&&!lost(hr)&&candidate.MultiSampleType!=fallback_.MultiSampleType){candidate=without_aa(candidate);sent=candidate;++attempts;aa_reason="native_reset_rejected_msaa_stock";hr=device.Reset(&sent);}
 if(FAILED(hr)&&!lost(hr)&&std::memcmp(&candidate,&fallback_,sizeof(candidate))){restore_window();display="Stock";display_reason="native_reset_rejected_display_stock";sent=fallback_;++attempts;hr=device.Reset(&sent);}
 if(SUCCEEDED(hr)){effective=sent;valid=true;modified=std::memcmp(&effective,&fallback_,sizeof(effective))!=0;safe_copy(pp,&sent,sizeof(sent));observe(device);}return hr;
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
bool stock_ui_projection(const D3DMATRIX& p) noexcept {
 if(!std::isfinite(p._11)||!std::isfinite(p._22)||std::abs(p._11-2.f/640.f)>1e-8f||std::abs(p._22-2.f/480.f)>1e-8f||p._41!=-1||p._42!=-1||p._34!=0||p._44!=1||std::abs(p._33+.0005f)>1e-9f||p._43!=.5f)return false;
 const int zero[]={1,2,3,4,6,7,8,9};const float* f=&p.m[0][0];for(int k:zero)if(f[k]!=0)return false;return true;
}
bool ui_projection(const D3DMATRIX& in,double aspect,D3DMATRIX& out) noexcept {
 SavedFP fp;if(!stock_ui_projection(in)||!std::isfinite(aspect)||aspect<1.||aspect>4.)return false;
 double width=480.*aspect;out=in;out._11=static_cast<float>(2./width);out._41=static_cast<float>(-640./width);return true;
}
std::string QualityPipeline::json() const {
 SavedFP fp;
 std::ostringstream o;o<<"{\"display_requested\":"<<quote(config.display_mode)<<",\"display_effective\":"<<quote(display)<<",\"display_reason\":"<<quote(display_reason)<<",\"aa_requested\":"<<quote(config.aa_mode)<<",\"aa_reason\":"<<quote(aa_reason)<<",\"attempts\":"<<attempts<<",\"requested\":"<<pp_json(requested)<<",\"logical_baseline\":"<<pp_json(fallback_)<<",\"effective\":"<<(valid?pp_json(effective):"null")<<",\"monitor_rect\":["<<current.monitor.left<<','<<current.monitor.top<<','<<current.monitor.right<<','<<current.monitor.bottom<<"],\"physical_backbuffer\":";
 if(backbuffer_known)o<<"{\"width\":"<<backbuffer.Width<<",\"height\":"<<backbuffer.Height<<",\"format\":"<<backbuffer.Format<<",\"multisample\":"<<backbuffer.MultiSampleType<<'}';else o<<"null";
 o<<",\"physical_depth\":";if(depth_known)o<<"{\"width\":"<<depth.Width<<",\"height\":"<<depth.Height<<",\"format\":"<<depth.Format<<",\"multisample\":"<<depth.MultiSampleType<<'}';else o<<"null";
 double aspect=valid&&effective.BackBufferHeight?double(effective.BackBufferWidth)/effective.BackBufferHeight:0;
 o<<",\"effective_aspect\":"<<aspect<<",\"ui\":{\"mode\":"<<quote(config.interface_mode)<<",\"reason\":"<<quote(config.interface_reason)<<",\"logical_width\":640,\"logical_height\":480,\"virtual_width\":"<<480.*aspect<<",\"extra_width\":"<<480.*aspect-640.<<",\"center_offset\":"<<(480.*aspect-640.)*.5<<"},\"dpi_policy\":\"game_awareness_unchanged\"}";return o.str();
}
}
