#include "hud_visibility.hpp"
#include "provenance.hpp"
#include <new>
#include <cstring>
#include <sstream>

namespace gfx2 {
namespace {
bool supported_ui_identity(const HudDrawFacts& f) noexcept {
 return f.ui_identity_complete&&f.ui_epoch&&f.device_id&&f.ui_entity&&f.ui_packet&&f.ui_point&&f.ui_storage&&
  (f.ui_packet_mode==1||f.ui_packet_mode==2);
}
}

bool global_hud_draw_should_suppress(bool requested,const HudDrawFacts& f) noexcept {
 return requested&&f.exact_build&&f.render_thread&&f.device_valid&&f.scene_active&&
  f.race_context_valid&&!f.paused&&(f.pause_known||f.attract_context)&&f.context_current&&f.race_generation&&f.owner_lifetime&&f.hook_owned&&f.consumer_scope&&
  f.identity_current&&f.callsite_exact&&f.fvf_known&&f.fvf==0x142&&
  f.primitive==D3DPT_TRIANGLELIST&&f.primitive_count>0;
}

bool hud_toggle_edge(bool focused,bool down,bool& previous) noexcept {
 if(!focused){previous=down;return false;}
 const bool edge=down&&!previous;previous=down;return edge;
}

void HudVisibility::clear_replay_signatures() noexcept {
 if(replay_signatures_)for(size_t i=0;i<replay_signature_count_;++i)replay_signatures_[i]={};
 replay_signature_count_=0;replay_signature_device_id_=0;
}

bool HudVisibility::learn_replay_signature(const HudDrawFacts& f) noexcept {
 if(!supported_ui_identity(f))return false;
 if(replay_signature_device_id_&&replay_signature_device_id_!=f.device_id)clear_replay_signatures();
 replay_signature_device_id_=f.device_id;
 for(size_t i=0;i<replay_signature_count_;++i){const auto& s=replay_signatures_[i];
  if(s.race_generation==f.race_generation&&s.owner_lifetime==f.owner_lifetime&&s.ui_epoch==f.ui_epoch&&s.device_id==f.device_id&&
     s.entity==f.ui_entity&&s.packet==f.ui_packet&&s.point==f.ui_point&&s.storage==f.ui_storage&&s.mode==f.ui_packet_mode)return true;
 }
 if(!replay_signatures_||replay_signature_count_>=REPLAY_SIGNATURE_CAPACITY){++replay_signature_overflow_;return false;}
 auto& s=replay_signatures_[replay_signature_count_++];
 s={f.race_generation,f.owner_lifetime,f.ui_epoch,f.device_id,f.ui_entity,f.ui_packet,f.ui_point,f.ui_storage,f.ui_packet_mode};
 return true;
}

bool HudVisibility::has_replay_signature(const HudDrawFacts& f) const noexcept {
 if(!replay_signatures_||!supported_ui_identity(f)||f.device_id!=replay_signature_device_id_)return false;
 for(size_t i=0;i<replay_signature_count_;++i){const auto& s=replay_signatures_[i];
  if(s.race_generation==f.race_generation&&s.owner_lifetime==f.owner_lifetime&&s.ui_epoch==f.ui_epoch&&s.device_id==f.device_id&&
     s.entity==f.ui_entity&&s.packet==f.ui_packet&&s.point==f.ui_point&&s.storage==f.ui_storage&&s.mode==f.ui_packet_mode)return true;
 }
 return false;
}

size_t HudVisibility::replay_signatures_for_current_context() const noexcept {
 if(!replay_signatures_||!context_.valid||!context_.replay||!context_.race_generation||!context_.owner_lifetime||!replay_signature_device_id_)return 0;
 size_t count=0;
 for(size_t i=0;i<replay_signature_count_;++i){const auto& s=replay_signatures_[i];
  if(s.race_generation==context_.race_generation&&s.owner_lifetime==context_.owner_lifetime&&s.device_id==replay_signature_device_id_)++count;
 }
 return count;
}

void HudVisibility::configure(const VisualConfig& c,bool exact,bool hook_expected) noexcept {
 exact_build_=exact;hook_expected_=hook_expected;config_valid_=c.version_ok&&c.hud_toggle_valid;
 toggle_enabled_=config_valid_&&exact_build_&&hook_expected_&&c.hud_toggle_enabled;key_=c.hud_toggle_key?c.hud_toggle_key:'H';
 requested_hidden_=config_valid_&&c.hud_hidden_at_startup;previous_key_down_=false;
 context_=RaceHudContext{};context_sample_frame_=UINT64_MAX;scene_active_=device_valid_=hook_owned_=false;
 known_hud_draws_=suppressed_hud_draws_=rejected_ambiguous_draws_=0;
 replay_pause_suppressed_draws_=replay_pause_overlay_suppressed_draws_=0;
 replay_pause_preserved_draws_=replay_signature_overflow_=0;
 clear_replay_signatures();replay_signatures_.reset();clean_view_suppressed_=false;
 if(toggle_enabled_)replay_signatures_.reset(new(std::nothrow) ReplayHudSignature[REPLAY_SIGNATURE_CAPACITY]{});
 const std::string reason=!c.version_ok?"config_version_unavailable":!c.hud_toggle_valid?c.hud_reason:!exact?"unsupported_build":!hook_expected?"consumer_hook_not_requested":c.hud_reason;
 try{session().write("{\"type\":\"hud_hide_config\",\"toggle_enabled\":"+std::string(toggle_enabled_?"true":"false")+
  ",\"toggle_key\":"+std::to_string(key_)+",\"initially_hidden\":"+(requested_hidden_?"true":"false")+
  ",\"preserve_menus\":true,\"exact_build\":"+(exact_build_?"true":"false")+
  ",\"consumer_hook_expected\":"+(hook_expected_?"true":"false")+
  ",\"valid\":"+(config_valid_?"true":"false")+",\"reason\":"+quote(reason)+"}");}catch(...){}
 log_state("startup");
}

bool HudVisibility::sample_key(bool focused,bool down) noexcept {
 if(hud_toggle_edge(focused,down,previous_key_down_)&&toggle_enabled_){
  requested_hidden_=!requested_hidden_;log_state("user_toggle");return true;
 }
 return false;
}

void HudVisibility::observe_context(const RaceHudContext& context,bool exact,bool device,bool hook,bool scene_active,uint64_t frame) noexcept {
 const bool changed=context.valid!=context_.valid||context.pause_known!=context_.pause_known||context.paused!=context_.paused||
  context.replay!=context_.replay||context.attract!=context_.attract||context.startup_countdown!=context_.startup_countdown||
  context.race_generation!=context_.race_generation||context.owner_lifetime!=context_.owner_lifetime||
  !context.reason||!context_.reason||std::strcmp(context.reason,context_.reason)!=0;
 const bool new_semantic_owner=context.valid&&context_.valid&&
  (context.race_generation!=context_.race_generation||context.owner_lifetime!=context_.owner_lifetime||
   context.replay!=context_.replay||context.attract!=context_.attract);
 if(new_semantic_owner)clear_replay_signatures();
 context_=context;context_sample_frame_=frame;exact_build_=exact;device_valid_=device;hook_owned_=hook;scene_active_=scene_active;
 if(changed)log_state("ui_context_transition");
}

void HudVisibility::reset_context() noexcept {
 context_=RaceHudContext{};context_.reason="device_reset";scene_active_=false;device_valid_=false;hook_owned_=false;
 context_sample_frame_=UINT64_MAX;
 clear_replay_signatures();log_state("device_reset");
}

bool HudVisibility::should_suppress(const HudDrawFacts& facts) noexcept {
 if(!facts.callsite_exact)return false;
 if(facts.device_id){
  if(replay_signature_device_id_&&replay_signature_device_id_!=facts.device_id)clear_replay_signatures();
  if(!replay_signature_device_id_)replay_signature_device_id_=facts.device_id;
 }
 const bool same_scene=context_.valid&&facts.context_current&&facts.race_context_valid&&
  facts.paused==context_.paused&&facts.replay_context==context_.replay&&facts.attract_context==context_.attract&&
  facts.startup_countdown==context_.startup_countdown&&facts.race_generation==context_.race_generation&&
  facts.owner_lifetime==context_.owner_lifetime;
 const bool owned_base=config_valid_&&exact_build_&&scene_active_&&device_valid_&&hook_owned_&&same_scene&&
  facts.exact_build&&facts.render_thread&&facts.device_valid&&facts.scene_active&&facts.hook_owned&&
  facts.consumer_scope&&facts.identity_current&&facts.callsite_exact&&facts.fvf_known&&facts.fvf==0x142&&
  facts.primitive==D3DPT_TRIANGLELIST&&facts.primitive_count>0;
 const bool running_context=owned_base&&!facts.paused&&(facts.pause_known||facts.attract_context);
 const bool running_replay=running_context&&context_.replay&&facts.replay_context&&facts.pause_known&&
  global_hud_draw_should_suppress(true,facts);

 // Discover UI identities while replay is running, even with the HUD visible.
 // Paused replay can then hide only packets proven to belong to its live HUD.
 if(running_replay&&supported_ui_identity(facts))learn_replay_signature(facts);
 if(!requested_hidden_)return false;

 if(running_context&&global_hud_draw_should_suppress(true,facts)){
  ++known_hud_draws_;++suppressed_hud_draws_;return true;
 }

 const bool paused_replay=owned_base&&context_.replay&&context_.paused&&facts.replay_context&&facts.paused&&
  facts.pause_known&&!facts.attract_context;
 if(paused_replay){
  if(supported_ui_identity(facts)){
   // Replay pause adds native pause-window packets that are absent from the
   // running-HUD signature set. In this exact, typed replay-pause context,
   // every verified draw at the native UI packet consumer belongs to the
   // interface the user asked to hide. Keep the learned set as provenance,
   // but do not let its absence leave the pause window visible.
   if(has_replay_signature(facts))++known_hud_draws_;
   else ++replay_pause_overlay_suppressed_draws_;
   ++suppressed_hud_draws_;++replay_pause_suppressed_draws_;return true;
  }
  ++replay_pause_preserved_draws_;++rejected_ambiguous_draws_;return false;
 }

 ++rejected_ambiguous_draws_;return false;
}

void HudVisibility::log_state(const char* reason) noexcept {
 try{session().write("{\"type\":\"hud_hide_state\",\"requested_hidden\":"+(requested_hidden_?std::string("true"):"false")+
  ",\"effective_hidden\":"+(effective_hidden()?std::string("true"):"false")+
  ",\"current_ui_context\":"+quote(scene_active_&&context_.valid?(context_.attract?"attract_demo":context_.startup_countdown?"gameplay_start_countdown":context_.replay?(context_.paused?"replay_paused":"replay_running"):(context_.paused?"paused_race":"gameplay_running")):"unknown")+
  ",\"replay_mode\":"+(context_.replay?"true":"false")+
  ",\"attract_mode\":"+(context_.attract?"true":"false")+
  ",\"startup_countdown\":"+(context_.startup_countdown?"true":"false")+
  ",\"race_generation\":"+std::to_string(context_.race_generation)+",\"owner_lifetime\":"+std::to_string(context_.owner_lifetime)+
  ",\"learned_replay_signatures\":"+std::to_string(replay_signatures_for_current_context())+
  ",\"reason\":"+quote(reason?reason:"unknown")+",\"context_reason\":"+quote(context_.reason?context_.reason:"unknown")+"}");}catch(...){}
 last_state_reason_=reason?reason:"unknown";
}

void HudVisibility::finish_frame() noexcept {
 known_hud_draws_=suppressed_hud_draws_=rejected_ambiguous_draws_=0;
 replay_pause_suppressed_draws_=replay_pause_overlay_suppressed_draws_=0;
 replay_pause_preserved_draws_=0;clean_view_suppressed_=false;
}

std::string HudVisibility::json() const {
 std::ostringstream o;o<<"{\"requested_hidden\":"<<(requested_hidden_?"true":"false")
  <<",\"effective_hidden\":"<<(effective_hidden()?"true":"false")
  <<",\"toggle_enabled\":"<<(toggle_enabled_?"true":"false")<<",\"toggle_key\":"<<key_
  <<",\"current_ui_context\":"<<quote(scene_active_&&context_.valid?(context_.attract?"attract_demo":context_.startup_countdown?"gameplay_start_countdown":context_.replay?(context_.paused?"replay_paused":"replay_running"):(context_.paused?"paused_race":"gameplay_running")):"unknown")
  <<",\"replay_mode\":"<<(context_.replay?"true":"false")
  <<",\"attract_mode\":"<<(context_.attract?"true":"false")
  <<",\"startup_countdown\":"<<(context_.startup_countdown?"true":"false")
  <<",\"policy_ready\":"<<(policy_ready()?"true":"false")
  <<",\"context_reason\":"<<quote(context_.reason?context_.reason:"unknown")
  <<",\"race_generation\":"<<context_.race_generation<<",\"owner_lifetime\":"<<context_.owner_lifetime
  <<",\"scene_active\":"<<(scene_active_?"true":"false")<<",\"exact_build\":"<<(exact_build_?"true":"false")
  <<",\"device_valid\":"<<(device_valid_?"true":"false")<<",\"consumer_hook_owned\":"<<(hook_owned_?"true":"false")
  <<",\"known_hud_draws\":"<<known_hud_draws_<<",\"suppressed_hud_draws\":"<<suppressed_hud_draws_
  <<",\"preserved_menu_draws\":null,\"rejected_ambiguous_draws\":"<<rejected_ambiguous_draws_
  <<",\"learned_replay_signatures\":"<<replay_signatures_for_current_context()
  <<",\"replay_pause_suppressed_draws\":"<<replay_pause_suppressed_draws_
  <<",\"replay_pause_overlay_suppressed_draws\":"<<replay_pause_overlay_suppressed_draws_
  <<",\"replay_pause_preserved_unknown_draws\":"<<replay_pause_preserved_draws_
  <<",\"replay_signature_overflow\":"<<replay_signature_overflow_
  <<",\"clean_view_suppressed_draws\":"<<(clean_view_suppressed_?1:0)
  <<",\"policy_reason\":"<<quote(!requested_hidden_?"user_visible":!config_valid_?"invalid_config":!exact_build_?"unsupported_build":!scene_active_?"outside_scene":!context_.valid?context_.reason:clean_view_suppressed_&&context_.paused?"paused_freecam_clean_view":clean_view_suppressed_?"verified_clean_view_draw_suppressed":context_.paused&&context_.replay&&replay_pause_suppressed_draws_?"paused_replay_ui_suppressed":context_.paused&&context_.replay&&replay_pause_preserved_draws_?"replay_pause_unverified_ui_preserved":context_.paused&&context_.replay?"replay_pause_no_ui_draw_seen":context_.paused?"interactive_pause_preserved":!context_.pause_known&&!context_.attract?"pause_state_unknown":!hook_owned_?"consumer_hook_unowned":policy_ready()?(context_.attract?"certified_attract_demo_hud":context_.startup_countdown?"certified_start_countdown_hud":context_.replay?"certified_replay_ui":"certified_gameplay_ui"):"draw_scope_unavailable")<<"}";
 return o.str();
}
}
