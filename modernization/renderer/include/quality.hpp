#pragma once
#include "visual_policy.hpp"
#include "compatibility.hpp"
#include <memory>
#include <array>
namespace gfx2 {
#ifndef MRR_DIAGNOSTIC_NO_MESSAGE_HOOKS
#define MRR_DIAGNOSTIC_NO_MESSAGE_HOOKS 0
#endif
inline constexpr bool quality_message_hooks_enabled() noexcept {return !MRR_DIAGNOSTIC_NO_MESSAGE_HOOKS;}
struct WindowState {HWND hwnd=nullptr;LONG style=0,exstyle=0;HMENU menu=nullptr;RECT outer{},client{},monitor{},work{};bool valid=false,maximized=false,minimized=false;};
class WindowApi {
public: virtual ~WindowApi()=default;
 virtual bool snapshot(HWND,WindowState&) noexcept=0;
 virtual bool apply(const WindowState&,const RECT&,bool client,bool popup) noexcept=0;
 virtual bool restore(const WindowState&) noexcept=0;
};
WindowApi& native_window_api() noexcept;
class MessageHookApi {
public: virtual ~MessageHookApi()=default;
 virtual HHOOK install(int,HOOKPROC,HMODULE,DWORD) noexcept=0;
 virtual bool remove(HHOOK) noexcept=0;
};
MessageHookApi& native_message_hook_api() noexcept;
// Read-only, exact-retail window-owner observation; never calls or edits game state.
struct GameWindowOwner {
 bool known=false;uintptr_t address=0;unsigned windowed=0,pp_windowed=0,initialized=0,device_created=0,active=0,device_ready=0,in_size_move=0;
 uint32_t saved_style=0;std::string reason="unsupported_build";
 std::string json() const;
};
GameWindowOwner inspect_game_window_owner(uintptr_t image,bool exact_retail,HWND expected) noexcept;
struct CursorIdle {
 bool hidden=false,observed=false;POINT previous{};uint64_t last_move=0;
 // -1 hides, +1 restores, 0 leaves Win32 ownership alone. Never touches ShowCursor.
 int update(bool focused_inside,POINT position,uint64_t now,unsigned delay) noexcept;
};
// The same descriptor planner and bounded attempt sequence serve CreateDevice and Reset.
class QualityPipeline {
public:
 VisualConfig config;UINT adapter=0;D3DDEVTYPE type=D3DDEVTYPE_HAL;HWND focus=nullptr;
 D3DPRESENT_PARAMETERS requested{},effective{};bool valid=false,modified=false;
 D3DSURFACE_DESC backbuffer{},depth{};bool backbuffer_known=false,depth_known=false;
 WindowState original{},current{};std::string display="Stock",display_reason,aa_reason;
 unsigned attempts=0;bool aa_hazard=false;
 FeatureCapability ui_capability,preview_capability;bool ui_projection_live=false;
 mutable bool viewport_domain_known=false,viewport_logical=false;
 explicit QualityPipeline(WindowApi& api=native_window_api(),MessageHookApi& hooks=native_message_hook_api()):windows_(&api),hooks_(&hooks){}
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
 void begin_shutdown() noexcept;
 void cursor_tick() noexcept;
 void cooperative_result(HRESULT) noexcept;
 void cursor_watch() noexcept;
 void display_watch() noexcept;
 void window_message(HWND,UINT,WPARAM,LPARAM,bool before) noexcept;
 void flush_window_messages() noexcept;
 size_t pending_window_messages() const noexcept {return message_count_;}
 void cursor_focus_lost() noexcept;
 bool cursor_watch_installed() const noexcept {return cursor_hook_!=nullptr;}
 bool window_commit_active() const noexcept {return committing_;}
 uint64_t native_reset_calls=0,window_reset_echoes=0,window_reset_echoes_suppressed=0,deferred_resets=0;
 uint64_t windowed_resize_admissions=0;
private:
 CursorIdle cursor_;HCURSOR saved_cursor_=nullptr;HHOOK cursor_hook_=nullptr,message_hook_=nullptr;HWND watched_window_=nullptr;
 WindowApi* windows_;MessageHookApi* hooks_;bool window_owned_=false,committing_=false,shutting_down_=false;D3DPRESENT_PARAMETERS fallback_{};
 WindowState committed_{};
 bool initial_window_commit_complete_=false;
 UINT normal_target_width_=0,normal_target_height_=0;bool normal_target_valid_=false;
 UINT planned_normal_target_width_=0,planned_normal_target_height_=0;
 bool planned_normal_target_valid_=false,planned_normal_target_update_=false,planned_live_resize_=false;
 UINT exclusive_width_=0,exclusive_height_=0;bool exclusive_rejected_=false;
 uint64_t attempt_sequence_=0,device_lifetime_id_=0,successful_reset_epoch_=0;unsigned attempt_records_=0,cooperative_records_=0;Known<HRESULT> cooperative_;
 unsigned admission_records_=0,message_records_=0;DWORD creating_thread_id_=0;
 Known<HRESULT> reset_readiness_;bool display_watch_attempted_=false;std::string display_watch_reason_="not_installed";
 struct MessageRecord {HWND hwnd=nullptr;UINT message=0;WPARAM w=0;LPARAM l=0;bool before=false,committing=false,styles_known=false;STYLESTRUCT styles{};uint64_t sequence=0,tick=0,epoch=0;};
 std::array<MessageRecord,64> messages_{};size_t message_count_=0;uint64_t message_dropped_=0;bool flushing_messages_=false,message_budget_reported_=false;
 void reset_readiness(IDirect3DDevice8&,const D3DPRESENT_PARAMETERS&) noexcept;
 void native_attempt(const char*,const D3DPRESENT_PARAMETERS&,const D3DPRESENT_PARAMETERS&,HRESULT) noexcept;
 void native_begin(const char*,const D3DPRESENT_PARAMETERS&) noexcept;
 std::string window_commit_status_="not_required";
 std::string window_state_="unknown";
 std::string windowed_target_reason_="uninitialized";
 std::string window_transition_key_;
 std::string window_context_json(HWND) const;
 const char* windowed_resize_decision(const D3DPRESENT_PARAMETERS&,const WindowState&) const noexcept;
 void windowed_admission(const D3DPRESENT_PARAMETERS&,const char*) noexcept;
 void accept_planned_windowed_target() noexcept;
 void window_transition(const WindowState&) noexcept;
 bool select_display(IDirect3D8&,D3DPRESENT_PARAMETERS&);
 bool apply_window(const D3DPRESENT_PARAMETERS&);
 D3DPRESENT_PARAMETERS without_aa(D3DPRESENT_PARAMETERS) const noexcept;
};
bool map_viewport(const D3DVIEWPORT8&,UINT from_w,UINT from_h,UINT to_w,UINT to_h,D3DVIEWPORT8&) noexcept;
bool ui_projection_dimensions(const D3DMATRIX&,UINT width,UINT height,D3DMATRIX&) noexcept;
bool ui_projection(const D3DMATRIX&,double aspect,D3DMATRIX&) noexcept;
bool presentation_equivalent(const D3DPRESENT_PARAMETERS&,const D3DPRESENT_PARAMETERS&) noexcept;
bool frontend_preview_projection(const D3DMATRIX&,D3DMATRIX&) noexcept;
int camera_scene_family(const D3DMATRIX&) noexcept;
bool stock_ui_projection(const D3DMATRIX&) noexcept;
void display_breadcrumb(const char* step,HRESULT result=S_OK) noexcept;
}
