#pragma once
#include "game_fov.hpp"
namespace gfx2 {
inline constexpr uint32_t UI_SORT_RVA=0x00109a21;
inline constexpr std::array<unsigned char,5> UI_SORT_BYTES={0xd8,0x60,0x30,0xd9,0xc0};
inline constexpr uint32_t UI_PACKET_RVA=0x0016d110;
inline constexpr std::array<unsigned char,6> UI_PACKET_BYTES={0x81,0xec,0x08,0x01,0,0};
int margin_direction(float x,float y,float z) noexcept;
const char* margin_source(float x,float y,float z) noexcept;
bool eligible_ui_packet(uintptr_t entity,uintptr_t coordinates) noexcept;
struct MarginIdentity {uintptr_t entity=0,packet=0,point=0,storage=0;uint32_t mode=0;};
bool read_margin_identity(uintptr_t entity,uintptr_t coordinates,MarginIdentity&) noexcept;
struct MarginAnchorDecision {
 uint64_t id=0,epoch=0;int direction=0,current_rule=0;bool admitted=false,retained=false,grace_retained=false;
 const char* source="none";const char* invalidated="none";
};
// Semantic direction only. This registry never owns coordinates or writes memory.
// At most two completed absent frames; observable identity/epoch changes win immediately.
inline constexpr uint64_t MARGIN_ANCHOR_GRACE_FRAMES=2;
class MarginAnchors {
 struct Anchor {MarginIdentity key{};uint64_t id=0,last=0;int direction=0;};
 std::array<Anchor,512> entries_{};uint64_t frame_=1,epoch_=1,next_id_=0;
 int context_=-1;const char* epoch_reason_="initial";
public:
 uint64_t admissions=0,invalidations=0,retained_anchor_without_current_rule_match=0,overflow=0;
 uint64_t anchor_grace_retained=0,grace_expired=0;
 MarginAnchorDecision resolve(const MarginIdentity&,float x,float y,float z) noexcept;
 void next_frame() noexcept;
 void begin_epoch(const char* reason) noexcept;
 void scene_context(bool race) noexcept;
 void reject(uintptr_t entity) noexcept;
 uint64_t epoch() const noexcept{return epoch_;}
 size_t size() const noexcept;
};
namespace detail {struct UiMarginsContract;uintptr_t ui_bridge_for_contract(uintptr_t return_address) noexcept;uintptr_t ui_packet_entity_for_contract() noexcept;uintptr_t ui_packet_bridge_for_contract(uintptr_t return_address) noexcept;}
class UiJumpPatch {
 void* site_=nullptr;std::array<unsigned char,5> after_{};bool installed_=false;
 bool exchange(PatchMemory&,const std::array<unsigned char,5>&,const std::array<unsigned char,5>&) noexcept;
public:
 bool install(PatchMemory&,void*,uintptr_t) noexcept;
 bool remove(PatchMemory&) noexcept;
 bool installed() const noexcept {return installed_;}
};
class UiPacketPatch {
 void* site_=nullptr;std::array<unsigned char,6> after_{};bool installed_=false;
 bool exchange(PatchMemory&,const std::array<unsigned char,6>&,const std::array<unsigned char,6>&) noexcept;
public:
 bool install(PatchMemory&,void*,uintptr_t) noexcept;
 bool remove(PatchMemory&) noexcept;
 bool installed() const noexcept {return installed_;}
};
class Trace;
struct MarginDrawDecision {MarginIdentity key{};MarginAnchorDecision anchor{};float native_x=0,native_y=0,margin=0;bool valid=false;};
inline constexpr uint32_t UI_DRAW_RETURN_RVA=0x0016d7c4;
class UiMargins {
 friend struct detail::UiMarginsContract;
 UiPacketPatch patch_;MarginAnchors anchors_;
 struct Scope {MarginIdentity key{};MarginAnchorDecision anchor{};bool valid=false;};
 std::array<Scope,16> scopes_{};unsigned scope_depth_=0;
 D3DMATRIX pending_world_{};bool restore_pending_=false;
 struct Observation {uintptr_t entity=0,point=0,packet=0,storage=0;uint64_t id=0,first=0,last=0,restored=0;float logical=0,effective=0;unsigned visits=0;int rule=0;};
 std::array<Observation,64> observations_{};uint64_t frame_id_=1,next_id_=0;unsigned records_=0,diagnostic_frames_=0;bool capturing_=false;DWORD thread_=0;float half_=0;bool enabled_=false;
public:
 const char* reason="disabled";
 ~UiMargins();
 bool install(bool exact,bool requested) noexcept;
 void dimensions(UINT width,UINT height) noexcept;
 void capture_window(bool active,uint64_t frame) noexcept;
 void reset_diagnostics() noexcept;
 void reset_anchors(const char* reason) noexcept;
 void scene_context(bool race) noexcept;
 bool enter_consume(uintptr_t entity) noexcept;
 void leave_consume() noexcept;
 MarginDrawDecision draw_decision() noexcept;
 void observe_draw(const MarginDrawDecision&,float native_world_x,float effective_world_x,HRESULT restore) noexcept;
 HRESULT repair_world(IDirect3DDevice8&,Trace&,uintptr_t) noexcept;
 void native_reset_succeeded() noexcept {restore_pending_=false;}
 void failed_restore(const D3DMATRIX&) noexcept;
 uint64_t render_draws=0,native_writes=0,restore_exact=0,restore_failures=0,world_read_failed=0,temporary_set_failed=0,scope_failures=0;
 bool finish_frame() noexcept;
 void disable(const char*) noexcept;
 std::string json() const;
};
}

namespace gfx2 {
class UiWorldScope {
 IDirect3DDevice8& native_;Trace& trace_;UiMargins& ui_;uintptr_t pc_;
 MarginDrawDecision decision_{};D3DMATRIX original_{},effective_{};bool changed_=false;
public:
 UiWorldScope(IDirect3DDevice8&,Trace&,UiMargins&,uintptr_t,bool allowed) noexcept;
 ~UiWorldScope() noexcept;
 bool changed() const noexcept{return changed_;}
 UiWorldScope(const UiWorldScope&)=delete;
};
}
