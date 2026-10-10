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
struct CarouselSemanticDecision {
 uint64_t id=0;bool candidate=false,proven=false,promoted=false;
 const char* status="disabled";
};
struct SceneContextDecision {
 int family=-1;uint64_t source_frame=0,consumer_frame=0,age=0;
 bool source_frame_known=false,valid=false,frontend_allowed=false;
 const char* phase="unknown_scene";const char* rejection_reason="unknown_scene";
};
// Semantic direction only. This registry never owns coordinates or writes memory.
// At most two completed absent frames; observable identity/epoch changes win immediately.
inline constexpr uint64_t MARGIN_ANCHOR_GRACE_FRAMES=2;
inline constexpr unsigned CAROUSEL_TRACK_CAPACITY=128;
inline constexpr float CAROUSEL_LANE_MIN_Y=299.f,CAROUSEL_LANE_MAX_Y=319.f;
inline constexpr float CAROUSEL_CENTER_MIN_X=350.f,CAROUSEL_CENTER_MAX_X=400.f;
inline constexpr float CAROUSEL_OUTER_LEFT_MAX_X=295.f,CAROUSEL_OUTER_RIGHT_MIN_X=455.f;
inline constexpr float CAROUSEL_MIN_TRAVEL_X=80.f;
class MarginAnchors {
 struct Anchor {MarginIdentity key{};uint64_t id=0,last=0;int direction=0;};
 struct CarouselTrack {
  MarginIdentity key{};uint64_t id=0,epoch=0,first=0,last=0;
  float min_x=0,max_x=0;unsigned samples=0;
  bool saw_left_anchor=false,saw_center=false,saw_outer_left=false,saw_outer_right=false,proven=false;
 };
 std::array<Anchor,512> entries_{};uint64_t frame_=1,epoch_=1,next_id_=0;
 std::array<CarouselTrack,CAROUSEL_TRACK_CAPACITY> carousel_{};uint64_t next_carousel_id_=0;
 int context_=-1;const char* epoch_reason_="initial";
public:
 uint64_t admissions=0,invalidations=0,retained_anchor_without_current_rule_match=0,overflow=0;
 uint64_t anchor_grace_retained=0,grace_expired=0;
 uint64_t carousel_promotions=0,carousel_invalidations=0,carousel_overflow=0,carousel_anchor_discards=0;
 MarginAnchorDecision resolve(const MarginIdentity&,float x,float y,float z) noexcept;
 CarouselSemanticDecision observe_carousel(const MarginIdentity&,float x,float y,uint64_t frame,
  bool frontend_context,bool verified_ui_draw,bool left_anchor_evidence) noexcept;
 void clear_carousels() noexcept;
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
struct MarginDrawDecision {
 MarginIdentity key{};MarginAnchorDecision anchor{};float native_x=0,native_y=0,margin=0,standard_margin=0;
 uint64_t carousel_id=0;bool carousel_override=false,valid=false;const char* carousel_status="disabled";
 const char* carousel_group_status="disabled";const char* carousel_group_policy="unchanged";
 const char* carousel_group_membership_status="not_evaluated";
 const char* carousel_group_fallback_reason="none";bool carousel_group_override=false;
 SceneContextDecision scene_context{};
};
inline constexpr uint32_t UI_DRAW_RETURN_RVA=0x0016d7c4;
inline constexpr unsigned UI_PACKET_DRAW_OBSERVATION_LIMIT=8;
inline constexpr unsigned UI_CAPTURE_PACKET_CANDIDATE_LIMIT=64;
inline constexpr unsigned UI_CAPTURE_ADJUSTED_CANDIDATE_QUOTA=32;
inline constexpr unsigned UI_CAPTURE_UNADJUSTED_CANDIDATE_QUOTA=32;
inline constexpr unsigned UI_CAPTURE_PACKET_RECORD_LIMIT=256;
inline constexpr unsigned UI_CAPTURE_RENDER_LOCAL_RECORD_LIMIT=64;
inline constexpr unsigned UI_CAPTURE_TOTAL_DRAW_OBSERVATION_LIMIT=UI_CAPTURE_PACKET_CANDIDATE_LIMIT*UI_PACKET_DRAW_OBSERVATION_LIMIT;
struct UiDrawObservation {
 uintptr_t caller_va=0;uint32_t caller_rva=0,primitive=0,start_vertex=0,primitive_count=0;
 bool caller_in_game_image=false,adjustment_gate_allowed=false,suppressed=false,forwarded=false,diagnostic_relevant=false;
 bool vertex_shader_token_known=false;uint32_t vertex_shader_token=0;float margin_requested=0,margin_applied=0;
 bool get_transform_attempted=false,world_known=false,effective_world_known=false,packet_point_known=false;uint32_t get_transform_hresult=0;
 float packet_x=0,packet_y=0;
 float native_world_x=0,native_world_y=0,effective_world_x=0,effective_world_y=0;
 const char* world_status="not_read";
 bool temporary_set_attempted=false;uint32_t temporary_set_hresult=0;float requested_world_x=0,requested_world_y=0;
 uint32_t draw_hresult=0;bool draw_result_known=false;
 bool restore_attempted=false,restore_requested_original_exact=false,restore_succeeded=false;uint32_t restore_hresult=0;
 const char* carousel_status="disabled";uint64_t carousel_id=0;bool carousel_override=false;
 const char* carousel_group_status="disabled";const char* carousel_group_policy="unchanged";
 const char* carousel_group_membership_status="not_evaluated";
 const char* carousel_group_fallback_reason="none";bool carousel_group_override=false;
 float margin_effective_request=0;
 SceneContextDecision scene_context{};
};
class UiMargins {
 friend struct detail::UiMarginsContract;
 UiPacketPatch patch_;MarginAnchors anchors_;
 struct Scope {
  MarginIdentity key{};MarginAnchorDecision anchor{};bool valid=false,capture_active=false;
  uint64_t packet_id=0,first_frame=0,previous_frame=0,restored_frame=0,consume_count=0;
  float engine_x=0,engine_y=0,effective_x=0;bool engine_rewrite=false;
  const char* promotion_status="pending_draw";
   bool candidate_class_adjusted=false;
   unsigned draw_count=0,draw_dropped=0,non_ui_draws=0;std::array<UiDrawObservation,UI_PACKET_DRAW_OBSERVATION_LIMIT> draws{};
 };
 std::array<Scope,16> scopes_{};unsigned scope_depth_=0;
 D3DMATRIX pending_world_{};bool restore_pending_=false;
 struct Observation {
  MarginIdentity key{};uint64_t id=0,epoch=0,first=0,last=0,restored=0;
   uint64_t priority=0;float logical=0,effective=0;unsigned visits=0;int rule=0;uint8_t rule_mask=0;bool adjusted=false;
 };
 std::array<Observation,UI_CAPTURE_PACKET_CANDIDATE_LIMIT> observations_{};
 uint64_t frame_id_=1,next_id_=0,scene_family_frame_=0,scene_family_epoch_=0;
 uint64_t completed_scene_frame_=0,completed_scene_epoch_=0,pending_present_frame_=0,pending_present_epoch_=0;
 int completed_scene_family_=-1,pending_present_family_=-1;
 bool scene_family_conflicted_=false,scene_evidence_valid_=false,pending_present_=false,pending_scene_valid_=false;
 uint64_t scene_context_same_frame_uses_=0,scene_context_previous_frame_uses_=0,scene_context_rejections_=0;
 uint64_t device_id_=0,capture_start_frame_=0,capture_trace_frame_=0;
 uint64_t records_=0,render_local_records_=0;
 uint64_t capture_count_=0,capture_records_=0,capture_render_local_records_=0,capture_packet_consumers_=0,capture_draw_observations_captured_=0;
 uint64_t capture_packets_with_draws_=0;
 uint64_t capture_consumers_without_draw_=0,capture_non_ui_draws_=0,capture_relevant_draws_=0;
 uint64_t capture_adjusted_draws_=0,capture_unadjusted_draws_=0,capture_adjusted_packets_=0,capture_unadjusted_packets_=0;
 uint64_t capture_candidate_rejections_=0,capture_candidate_evictions_=0,capture_packet_record_drops_=0;
 uint64_t capture_render_local_drops_=0,capture_draw_drops_=0,capture_identity_invalidations_=0,capture_log_failures_=0;
 uint64_t capture_draw_observation_attempts_=0;
 uint64_t carousel_override_draws_=0,carousel_group_blocked_draws_=0;
 bool capturing_=false,capture_completed_=false,capture_close_pending_=false;DWORD thread_=0;float half_=0;bool enabled_=false,carousel_alignment_requested_=false,carousel_alignment_enabled_=false;int scene_family_=-1;const char* scene_invalidation_reason_="unknown_scene";const char* capture_end_reason_="none",*capture_close_reason_="none";
 SceneContextDecision scene_context_for_draw() const noexcept;
 void clear_scene_context(const char* reason) noexcept;
 std::string packet_observation_json(const Scope&) const;
 int find_observation(const MarginIdentity&,uint64_t epoch) const noexcept;
 int promote_observation(Scope&) noexcept;
 static uint64_t observation_priority(const MarginIdentity&,uint64_t epoch) noexcept;
 void reset_capture_local() noexcept;
 bool emit_capture_record(const std::string&,bool packet_record,bool render_local_record) noexcept;
 void finish_capture(uint64_t frame,uint64_t device_id,const char* reason) noexcept;
 void emit_group_candidates() noexcept;
public:
 const char* reason="disabled";
 uint64_t draw_observations_captured=0,draw_observations_dropped=0;
 ~UiMargins();
 bool install(bool exact,bool requested,bool carousel_alignment=false) noexcept;
 void configure_carousel_alignment(bool requested,bool exact_profile) noexcept;
 void dimensions(UINT width,UINT height) noexcept;
 void capture_window(bool active,uint64_t frame,uint64_t device_id=0,const char* end_reason="present") noexcept;
 void reset_diagnostics() noexcept;
 void reset_anchors(const char* reason) noexcept;
 void scene_context(bool race) noexcept;
 void present_completed(bool succeeded) noexcept;
 bool enter_consume(uintptr_t entity) noexcept;
 void leave_consume() noexcept;
 MarginDrawDecision draw_decision(bool verified_ui_draw=false) noexcept;
 UiDrawObservation* begin_draw(uintptr_t caller_va,uint32_t caller_rva,bool caller_in_game_image,
  D3DPRIMITIVETYPE primitive,UINT start_vertex,UINT primitive_count,bool adjustment_gate_allowed,
  bool suppressed,bool forwarded,bool vertex_shader_token_known,uint32_t vertex_shader_token) noexcept;
 void observe_draw(const MarginDrawDecision&,UiDrawObservation&) noexcept;
 HRESULT repair_world(IDirect3DDevice8&,Trace&,uintptr_t) noexcept;
 void native_reset_succeeded() noexcept {restore_pending_=false;}
 void failed_restore(const D3DMATRIX&) noexcept;
 uint64_t render_draws=0,native_writes=0,restore_exact=0,restore_failures=0,world_read_failed=0,temporary_set_failed=0,scope_failures=0;
 bool finish_frame() noexcept;
 void disable(const char*) noexcept;
 std::string json() const;
 uint64_t packet_consumers_seen=0,packet_consumers_without_relevant_draw=0,non_ui_draws_seen=0;
};
}

namespace gfx2 {
class UiWorldScope {
 IDirect3DDevice8& native_;Trace& trace_;UiMargins& ui_;uintptr_t pc_;
 MarginDrawDecision decision_{};UiDrawObservation* observation_=nullptr;D3DMATRIX original_{},effective_{};bool changed_=false;
public:
 UiWorldScope(IDirect3DDevice8&,Trace&,UiMargins&,uintptr_t,bool allowed,
  D3DPRIMITIVETYPE primitive=D3DPT_TRIANGLELIST,UINT start_vertex=0,UINT primitive_count=0,
  uint32_t caller_rva=0,bool caller_in_game_image=false,bool suppressed=false,bool forwarded=true,
  bool vertex_shader_token_known=false,uint32_t vertex_shader_token=0) noexcept;
 ~UiWorldScope() noexcept;
 void draw_result(HRESULT result) noexcept {if(observation_){observation_->draw_hresult=static_cast<uint32_t>(result);observation_->draw_result_known=true;}}
 bool changed() const noexcept{return changed_;}
 UiWorldScope(const UiWorldScope&)=delete;
};
}
