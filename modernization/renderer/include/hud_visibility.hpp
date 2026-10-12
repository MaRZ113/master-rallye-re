#pragma once
#include "race_epoch.hpp"
#include "visual_policy.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace gfx2 {
struct HudDrawFacts {
 bool exact_build=false,render_thread=false,device_valid=false,scene_active=false;
 bool race_context_valid=false,pause_known=false,paused=false,attract_context=false,startup_countdown=false,hook_owned=false;
 bool consumer_scope=false,identity_current=false,callsite_exact=false,fvf_known=false;
 bool context_current=false,replay_context=false,ui_identity_complete=false,paused_freecam_context=false;
 uint64_t race_generation=0,owner_lifetime=0;
 uint64_t ui_epoch=0,device_id=0;
 uintptr_t ui_entity=0,ui_packet=0,ui_point=0,ui_storage=0;
 uint32_t ui_packet_mode=0;
 DWORD fvf=0;D3DPRIMITIVETYPE primitive=D3DPT_FORCE_DWORD;UINT primitive_count=0;
};
bool global_hud_draw_should_suppress(bool requested_hidden,const HudDrawFacts&) noexcept;
bool hud_toggle_edge(bool focused,bool key_down,bool& previous_down) noexcept;

class HudVisibility {
 static constexpr size_t RACE_HUD_SIGNATURE_CAPACITY=512;
 struct RaceHudSignature {
  uint64_t race_generation=0,owner_lifetime=0,ui_epoch=0,device_id=0;
  uintptr_t entity=0,packet=0,point=0,storage=0;
  uint32_t mode=0;
 };
 bool config_valid_=false,exact_build_=false,hook_expected_=false;
 bool toggle_enabled_=false,requested_hidden_=false,previous_key_down_=false;
 unsigned key_='H';
 RaceHudContext context_{};
 uint64_t context_sample_frame_=UINT64_MAX;
 bool scene_active_=false,device_valid_=false,hook_owned_=false;
 uint64_t known_hud_draws_=0,suppressed_hud_draws_=0,rejected_ambiguous_draws_=0;
 uint64_t replay_pause_suppressed_draws_=0,replay_pause_overlay_suppressed_draws_=0;
 uint64_t replay_pause_preserved_draws_=0,race_hud_signature_overflow_=0;
 uint64_t paused_race_suppressed_draws_=0,paused_race_preserved_unknown_draws_=0,paused_race_overlay_suppressed_draws_=0;
 uint64_t paused_freecam_suppressed_draws_=0;
 std::unique_ptr<RaceHudSignature[]> race_hud_signatures_;
 size_t race_hud_signature_count_=0;
 uint64_t race_hud_signature_device_id_=0;
 bool clean_view_suppressed_=false,paused_freecam_context_seen_=false,preserve_pause_=true;
 const char* last_state_reason_="startup";
 void log_state(const char* reason) noexcept;
 void clear_race_hud_signatures() noexcept;
 bool learn_race_hud_signature(const HudDrawFacts&) noexcept;
 bool has_race_hud_signature(const HudDrawFacts&) const noexcept;
 size_t signatures_for_current_context() const noexcept;
 size_t race_hud_signatures_for_current_context() const noexcept;
public:
 void configure(const VisualConfig&,bool exact_build,bool hook_expected) noexcept;
 bool sample_key(bool focused,bool key_down) noexcept;
 void observe_context(const RaceHudContext&,bool exact_build,bool device_valid,bool hook_owned,bool scene_active,uint64_t frame=0) noexcept;
 bool context_sampled_this_frame(uint64_t frame) const noexcept{return context_sample_frame_==frame;}
 RaceHudContext context_snapshot() const noexcept{return context_;}
 void end_scene() noexcept {scene_active_=false;}
 void reset_context() noexcept;
 bool should_suppress(const HudDrawFacts&) noexcept;
 void note_clean_view_suppressed() noexcept {clean_view_suppressed_=true;}
 bool requested_hidden() const noexcept{return requested_hidden_;}
 bool toggle_enabled() const noexcept{return toggle_enabled_;}
 unsigned toggle_key() const noexcept{return key_;}
 bool policy_ready() const noexcept{return requested_hidden_&&config_valid_&&exact_build_&&scene_active_&&device_valid_&&hook_owned_&&
  context_.valid&&((!context_.paused&&(context_.pause_known||context_.attract))||
   (context_.paused&&context_.replay&&context_.pause_known)||
   (context_.paused&&!context_.replay&&context_.pause_known&&
    (paused_freecam_context_seen_||!preserve_pause_||signatures_for_current_context()>0)));}
 bool effective_hidden() const noexcept{return suppressed_hud_draws_>0||clean_view_suppressed_;}
 void finish_frame() noexcept;
 std::string json() const;
};
}
