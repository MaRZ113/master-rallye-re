#pragma once
#include "visual_policy.hpp"
#include "compatibility.hpp"
#include <memory>
namespace gfx2 {
struct WindowState {HWND hwnd=nullptr;LONG style=0,exstyle=0;HMENU menu=nullptr;RECT outer{},client{},monitor{},work{};bool valid=false;};
class WindowApi {
public: virtual ~WindowApi()=default;
 virtual bool snapshot(HWND,WindowState&) noexcept=0;
 virtual bool apply(const WindowState&,const RECT&,bool client,bool popup) noexcept=0;
 virtual bool restore(const WindowState&) noexcept=0;
};
WindowApi& native_window_api() noexcept;
// The same descriptor planner and bounded attempt sequence serve CreateDevice and Reset.
class QualityPipeline {
public:
 VisualConfig config;UINT adapter=0;D3DDEVTYPE type=D3DDEVTYPE_HAL;HWND focus=nullptr;
 D3DPRESENT_PARAMETERS requested{},effective{};bool valid=false,modified=false;
 D3DSURFACE_DESC backbuffer{},depth{};bool backbuffer_known=false,depth_known=false;
 WindowState original{},current{};std::string display="Stock",display_reason,aa_reason;
 unsigned attempts=0;bool aa_hazard=false;
 FeatureCapability ui_capability;bool ui_projection_live=false;
 mutable bool viewport_domain_known=false,viewport_logical=false;
 explicit QualityPipeline(WindowApi& api=native_window_api()):windows_(&api){}
 ~QualityPipeline();
 void configure(const VisualConfig&,bool ui_supported,UINT,D3DDEVTYPE,HWND);
 bool active() const noexcept {return config.display_mode!="Stock"||config.aa_mode!="Stock";}
 D3DPRESENT_PARAMETERS plan(IDirect3D8&,const D3DPRESENT_PARAMETERS&);
 HRESULT create(IDirect3D8&,DWORD,D3DPRESENT_PARAMETERS*,IDirect3DDevice8**);
 HRESULT reset(IDirect3D8&,IDirect3DDevice8&,D3DPRESENT_PARAMETERS*);
 void observe(IDirect3DDevice8&) noexcept;
 std::string json() const;
 bool viewport(const D3DVIEWPORT8&,D3DVIEWPORT8&) const noexcept;
 void restore_window() noexcept;
private:
 WindowApi* windows_;bool window_owned_=false,committing_=false;D3DPRESENT_PARAMETERS fallback_{};
 WindowState committed_{};UINT pinned_width_=0,pinned_height_=0;
 std::string window_commit_status_="not_required";
 bool select_display(IDirect3D8&,D3DPRESENT_PARAMETERS&);
 bool apply_window(const D3DPRESENT_PARAMETERS&);
 D3DPRESENT_PARAMETERS without_aa(D3DPRESENT_PARAMETERS) const noexcept;
};
bool map_viewport(const D3DVIEWPORT8&,UINT from_w,UINT from_h,UINT to_w,UINT to_h,D3DVIEWPORT8&) noexcept;
bool ui_projection_dimensions(const D3DMATRIX&,UINT width,UINT height,D3DMATRIX&) noexcept;
bool ui_projection(const D3DMATRIX&,double aspect,D3DMATRIX&) noexcept;
bool stock_ui_projection(const D3DMATRIX&) noexcept;
void display_breadcrumb(const char* step,HRESULT result=S_OK) noexcept;
}
