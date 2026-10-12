#pragma once
#include "game_fov.hpp"
#include <memory>
#include <sstream>
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
// Current draw facts, not packet motion or a reconstructed sibling roster.
struct CarouselRowDraw {
 bool allowed=false,caller_in_game_image=false,vertex_shader_token_known=false,suppressed=false,forwarded=false;
 uint32_t caller_rva=0,vertex_shader_token=0;D3DPRIMITIVETYPE primitive=D3DPT_TRIANGLELIST;UINT primitive_count=0;
};
inline constexpr float CAROUSEL_ROW_Y=309.f,CAROUSEL_ROW_Y_TOLERANCE=1.f/4096.f; // 8 float ULP at 309
const char* carousel_row_reason(bool feature_enabled,bool exact_profile,const SceneContextDecision&,
 const MarginIdentity&,float x,float y,const CarouselRowDraw&) noexcept;
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
 bool intact(PatchMemory& m) const noexcept {std::array<unsigned char,6> seen{};return installed_&&m.read(seen.data(),site_,6)&&seen==after_;}
};
class Trace;
struct MarginDrawDecision {
 MarginIdentity key{};MarginAnchorDecision anchor{};float native_x=0,native_y=0,margin=0,standard_margin=0;
 uint64_t carousel_id=0;bool carousel_override=false,valid=false;const char* carousel_status="disabled";
 const char* carousel_group_status="disabled";const char* carousel_group_policy="unchanged";
 const char* carousel_group_membership_status="not_evaluated";
 const char* carousel_group_fallback_reason="none";bool carousel_group_override=false;
 SceneContextDecision scene_context{};
 bool row_card_match=false;const char* carousel_row_reason="feature_disabled";
};
inline constexpr uint32_t UI_DRAW_RETURN_RVA=0x0016d7c4;
inline constexpr unsigned UI_OWNERSHIP_DRAW_LIMIT=1024;
inline constexpr unsigned UI_OWNERSHIP_IDENTITY_LIMIT=512;
inline constexpr unsigned UI_OWNERSHIP_STAGE_FIELD_COUNT=6;
inline constexpr uint32_t UI_OWNERSHIP_ENTITY_KNOWN=1u,UI_OWNERSHIP_PACKET_KNOWN=2u,
 UI_OWNERSHIP_POINT_KNOWN=4u,UI_OWNERSHIP_STORAGE_KNOWN=8u,UI_OWNERSHIP_MODE_KNOWN=16u,
 UI_OWNERSHIP_IDENTITY_COMPLETE=31u;
struct UiOwnershipDrawState {
 bool fvf_known=false,texture0_known=false,texture1_known=false;
 uint32_t fvf=0;uintptr_t texture0=0,texture1=0;uint64_t texture0_generation=0,texture1_generation=0;
 std::array<uint8_t,UI_OWNERSHIP_STAGE_FIELD_COUNT> stage_known{};
 std::array<uint32_t,UI_OWNERSHIP_STAGE_FIELD_COUNT> stage_values{};
};
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
 bool row_card_match=false;const char* carousel_row_reason="feature_disabled";
};
class UiMargins {
 friend struct detail::UiMarginsContract;
 UiPacketPatch patch_;MarginAnchors anchors_;
 struct Scope {
  MarginIdentity key{};MarginAnchorDecision anchor{};bool valid=false,capture_active=false;
  uintptr_t ownership_entity=0,ownership_packet=0,ownership_point=0,ownership_storage=0;
  uint32_t ownership_mode=0,ownership_field_mask=0;uint64_t ownership_scope_id=0,ownership_epoch=0;
  bool ownership_mode_known=false;const char* ownership_identity_status="not_captured";
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
 struct OwnershipIdentity {
  uintptr_t entity=0,packet=0,point=0,storage=0;uint32_t mode=0,field_mask=0;uint64_t epoch=0,id=0;
 };
 struct OwnershipDraw {
  uint64_t frame=0,draw_sequence=0,consumer_scope_id=0,identity_id=0,ui_epoch=0,race_generation=0;
  uintptr_t entity=0,packet=0,observed_packet=0,point=0,storage=0,texture0=0,texture1=0;
  uint64_t texture0_generation=0,texture1_generation=0;
  uint32_t field_mask=0,packet_mode=0,caller_rva=0,primitive=0,primitive_count=0,fvf=0;
  std::array<uint8_t,UI_OWNERSHIP_STAGE_FIELD_COUNT> stage_known{};
  std::array<uint32_t,UI_OWNERSHIP_STAGE_FIELD_COUNT> stage_values{};
  bool mode_known=false,race_generation_known=false,fvf_known=false,texture0_known=false,texture1_known=false;
  bool forwarded=false,suppressed=false;
  int32_t draw_hresult=0;
  const char* identity_status="not_read";const char* owner_mapping_status="unmapped";
 };
 std::unique_ptr<OwnershipIdentity[]> ownership_identities_;
 std::unique_ptr<OwnershipDraw[]> ownership_draws_;
 uint64_t ownership_next_scope_id_=0,ownership_next_identity_id_=0,ownership_draw_sequence_=0;
 uint64_t ownership_draw_attempts_=0,ownership_draw_drops_=0,ownership_unmapped_draws_=0,ownership_identity_overflow_=0;
 unsigned ownership_identity_count_=0,ownership_draw_count_=0;
 bool ownership_probe_requested_=false,ownership_probe_enabled_=false,ownership_capture_active_=false;
 uint64_t clean_view_eligible_draws_=0,clean_view_suppressed_draws_=0,clean_view_forwarded_unverified_draws_=0,
  clean_view_non_ui_draws_untouched_=0,clean_view_scope_invalidations_=0,clean_view_ui_scope_seen_=0,
  clean_view_ui_draw_candidates_=0,clean_view_draw_admission_rejections_=0,
  clean_view_rejected_inflight_=0,clean_view_rejected_stale_=0,
  clean_view_reject_snapshot_invalid_=0,clean_view_reject_scheduler_generation_=0,
  clean_view_reject_trace_frame_=0,clean_view_reject_render_thread_=0,clean_view_reject_device_=0,
  clean_view_reject_timestamp_=0,clean_view_reject_ui_scope_=0,clean_view_reject_scheduler_phase_=0;
 bool clean_view_user_requested_=false,clean_view_context_valid_=false,clean_view_toggle_edge_=false,clean_view_initial_armed_=false;
 uint64_t clean_view_request_disarm_count_=0,clean_view_context_trace_frame_=0,clean_view_context_scheduler_generation_=0;
 CleanViewFrameCheck clean_view_frame_check_{};
 const char* clean_view_last_admission_reason_="not_requested",*clean_view_last_scope_reason_="not_checked";
 const char* clean_view_context_reason_="not_requested",*clean_view_last_draw_rejection_reason_="none",*clean_view_first_draw_rejection_reason_="none",*clean_view_last_disarm_reason_="none";
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
 uint64_t carousel_row_draws_matched_=0,carousel_row_left_margins_suppressed_=0,carousel_row_nonleft_draws_matched_=0;
 bool carousel_exact_profile_=false;
 bool capturing_=false,capture_completed_=false,capture_close_pending_=false;DWORD thread_=0;float half_=0;bool enabled_=false,carousel_alignment_requested_=false,carousel_alignment_enabled_=false;int scene_family_=-1;const char* scene_invalidation_reason_="unknown_scene";const char* capture_end_reason_="none",*capture_close_reason_="none";
 SceneContextDecision scene_context_for_draw() const noexcept;
 void clear_scene_context(const char* reason) noexcept;
 std::string packet_observation_json(const Scope&) const;
 int find_observation(const MarginIdentity&,uint64_t epoch) const noexcept;
 int promote_observation(Scope&) noexcept;
 static uint64_t observation_priority(const MarginIdentity&,uint64_t epoch) noexcept;
 void reset_capture_local() noexcept;
 void reset_ownership_capture() noexcept;
 void ownership_capture_json(std::ostringstream&,bool include_draws) const;
 void finish_ownership_capture(uint64_t frame,const char* end_reason) noexcept;
 uint64_t ownership_identity_id(const Scope&,bool& overflow) noexcept;
 bool scope_identity_current(const Scope&,uint64_t expected_epoch,MarginIdentity* stable_identity=nullptr) const noexcept;
 bool emit_capture_record(const std::string&,bool packet_record,bool render_local_record) noexcept;
 void finish_capture(uint64_t frame,uint64_t device_id,const char* reason) noexcept;
 void emit_group_candidates() noexcept;
public:
 const char* reason="disabled";
 uint64_t draw_observations_captured=0,draw_observations_dropped=0;
 ~UiMargins();
 bool install(bool exact,bool requested) noexcept;
 void configure_carousel_alignment(bool requested,bool exact_profile) noexcept;
 void configure_ownership_probe(bool requested,bool exact_build) noexcept;
 void dimensions(UINT width,UINT height) noexcept;
 void capture_window(bool active,uint64_t frame,uint64_t device_id=0,const char* end_reason="present") noexcept;
 void reset_diagnostics() noexcept;
 void reset_anchors(const char* reason) noexcept;
 void scene_context(bool race) noexcept;
 void present_completed(bool succeeded) noexcept;
 bool enter_consume(uintptr_t entity) noexcept;
 void leave_consume() noexcept;
 bool consumer_hook_intact() const noexcept;
 bool clean_view_scope_identity(uint64_t& scope_id,uint64_t& epoch,const char*& reason,MarginIdentity* stable_identity=nullptr) noexcept;
 void note_clean_view_draw(bool eligible,bool suppressed,bool requested,bool draw_requested,bool ui_callsite,bool scope_invalidated,
  const char* admission_reason,const char* scope_reason,bool context_valid,const char* context_reason,
  bool toggle_edge,bool initial_armed,uint64_t disarm_count,const char* disarm_reason,bool consumer_scope_seen,
  uint64_t context_trace_frame,uint64_t context_scheduler_generation,const CleanViewFrameCheck&) noexcept;
 void observe_ownership_draw(uint64_t frame,bool race_generation_known,uint64_t race_generation,
  uint32_t caller_rva,D3DPRIMITIVETYPE primitive,UINT primitive_count,const UiOwnershipDrawState&,
  bool forwarded,bool suppressed,HRESULT result) noexcept;
 MarginDrawDecision draw_decision(bool verified_ui_draw=false,const CarouselRowDraw& draw={}) noexcept;
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
