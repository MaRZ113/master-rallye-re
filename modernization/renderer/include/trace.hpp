#pragma once
#include "state_tracker.hpp"
#include "provenance.hpp"
#include "vehicle_classifier.hpp"
#include "vehicle_semantics.hpp"
#include "game_fov.hpp"
#include "foliage_probe.hpp"
#include <mutex>
#include <memory>
#include <atomic>
namespace gfx2 {
inline constexpr size_t MAX_DRAWS=8192,MAX_EVENTS=16384,MAX_BUFFER_BYTES=32*1024*1024;
struct Event {uint32_t slot=0,result=0;Args args;uintptr_t pc=0;uint32_t draw=UINT32_MAX;
 bool suppressed=false,native_only=false,culling_synchronized=false;uint32_t feature=0;Args effective_args{};uint32_t effective_payload[16]{};uint32_t effective_words=0;
 uint32_t payload[32]{};uint32_t payload_words=0;};
struct ReflectionOutcome {
 Known<uint32_t> requested_tci,effective_tci;
 bool candidate=false,applied=false,restore_attempted=false,restore_success=false;
 uint32_t native_writes=0;const char* mode="Stock";const char* reason="not_evaluated";
};
struct EffectiveDraw {Known<uint32_t> filtering[4];Known<D3DMATRIX> projection;Known<float> world_x;};
struct Draw { DrawClassification classification;Classification at_draw;ReflectionOutcome reflection;Snapshot state;EffectiveDraw effective;std::array<uint64_t,8> texture_generation{};
 std::array<uint64_t,16> stream_generation{};uint64_t index_generation=0; };
struct FrameBuffer {Known<D3DVIEWPORT8> initial_effective_viewport;std::array<Event,MAX_EVENTS> events;std::array<Draw,MAX_DRAWS> draws;
 size_t event_count=0,draw_count=0;bool truncated=false;uint64_t dropped=0;};
static_assert(sizeof(FrameBuffer)<=MAX_BUFFER_BYTES,"hard capture allocation limit");
class Trace {
public:
 Trace() noexcept;
 ~Trace();
 class Guard {
  Trace& t_;bool held_;
 public:explicit Guard(Trace& t) noexcept;~Guard();Guard(const Guard&)=delete;
 };
 Guard guard() noexcept {return Guard(*this);}
 DrawClassification before(uint32_t slot,const Args& args,uintptr_t pc) noexcept;
 void foliage_result(const FoliageEvidence& e) noexcept;
 FoliageBudget foliage_budget;
 void reflection_result(const ReflectionOutcome& outcome,uint32_t triangles) noexcept;
 void configure_classifier(bool known,uintptr_t base) noexcept {classifier_known_=known;exe_base_=base;tracker_.reset();if(semantics_)semantics_->clear();race_context_=race_seen_this_frame_=race_history_=false;}
 uint64_t frame_number() const noexcept {return frame_;}
 uint64_t device_id() const noexcept {return device_;}
 bool claim_camera_observation_frame() noexcept {if(camera_observation_frame_==frame_)return false;camera_observation_frame_=frame_;return true;}
 size_t learned_signatures() const noexcept {return semantics_?semantics_->size():0;}
 bool race_context() const noexcept {return race_context_;}
 uint64_t classifier_epoch() const noexcept {return tracker_.epoch();}
 Known<uint32_t> reflection_restore_pending;bool reflection_disabled=false;
 void after(uint32_t slot,const Args& args,uint32_t result,uintptr_t pc,const Args* effective=nullptr,uint32_t feature=0,bool suppressed=false,bool native_only=false) noexcept;
 void shutdown(uint32_t real_refs) noexcept;
 std::atomic<bool> enabled{false};
 Shadow shadow,effective_shadow;
 FovCullStatus culling;
 std::string quality_metadata="null",ui_metadata="null";
 CaptureControl control;
 ResourceRegistry resources;
private:
 std::map<uint32_t,std::string> foliage_records_;
 TransformTracker tracker_;std::unique_ptr<VehicleSemantics> semantics_;uint32_t pending_semantic_=UINT32_MAX;
 VehicleSemanticSource pending_semantic_source_=VehicleSemanticSource::None;
 uint64_t live_body_draws_=0,learned_reflection_draws_=0,live_reflection_draws_=0;bool classifier_known_=false,race_context_=false,race_seen_this_frame_=false,race_history_=false;uintptr_t exe_base_=0;
 CRITICAL_SECTION lock_{};bool lock_ok_=false;
 uint64_t device_=0,frame_=1,primitives_=0,camera_observation_frame_=0;
 std::array<uint64_t,97> counts_{};
 uint64_t reset_count_=0,relearn_count_=0;size_t reset_removed_=0;bool waiting_relearn_=false;
 uint64_t reflection_candidates_=0,reflection_draws_=0,reflection_triangles_=0,reflection_writes_=0;
 std::unique_ptr<FrameBuffer> capture_;
 uint32_t pending_draw_=UINT32_MAX;
 Known<uint32_t> last_cooperative_;
 Known<D3DPRESENT_PARAMETERS> reset_before_;
 void finish(uint32_t result,bool complete,const char* reason) noexcept;
 void start_capture() noexcept;
 void resource(uint32_t slot,const Args& args,uint32_t result,uintptr_t caller_pc);
};
}
