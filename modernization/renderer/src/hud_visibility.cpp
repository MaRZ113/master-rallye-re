#include "hud_visibility.hpp"
#include "provenance.hpp"
#include <cstring>
#include <sstream>

namespace gfx2 {
bool global_hud_draw_should_suppress(bool requested,const HudDrawFacts& f) noexcept {
 return requested&&f.exact_build&&f.render_thread&&f.device_valid&&f.scene_active&&
  f.race_context_valid&&f.pause_known&&!f.paused&&f.context_current&&f.race_generation&&f.owner_lifetime&&f.hook_owned&&f.consumer_scope&&
  f.identity_current&&f.callsite_exact&&f.fvf_known&&f.fvf==0x142&&
  f.primitive==D3DPT_TRIANGLELIST&&f.primitive_count>0;
}
bool hud_toggle_edge(bool focused,bool down,bool& previous) noexcept {
 if(!focused){previous=down;return false;}
 const bool edge=down&&!previous;previous=down;return edge;
}
void HudVisibility::configure(const VisualConfig& c,bool exact,bool hook_expected) noexcept {
 exact_build_=exact;hook_expected_=hook_expected;config_valid_=c.version_ok&&c.hud_toggle_valid;
 toggle_enabled_=config_valid_&&exact_build_&&hook_expected_&&c.hud_toggle_enabled;key_=c.hud_toggle_key?c.hud_toggle_key:'H';
 requested_hidden_=config_valid_&&c.hud_hidden_at_startup;previous_key_down_=false;
 context_=RaceHudContext{};scene_active_=device_valid_=hook_owned_=false;
 known_hud_draws_=suppressed_hud_draws_=rejected_ambiguous_draws_=0;clean_view_suppressed_=false;
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
void HudVisibility::observe_context(const RaceHudContext& context,bool exact,bool device,bool hook,bool scene_active) noexcept {
 const bool changed=context.valid!=context_.valid||context.pause_known!=context_.pause_known||context.paused!=context_.paused||
  context.replay!=context_.replay||
  context.race_generation!=context_.race_generation||context.owner_lifetime!=context_.owner_lifetime||
  !context.reason||!context_.reason||std::strcmp(context.reason,context_.reason)!=0;
 context_=context;exact_build_=exact;device_valid_=device;hook_owned_=hook;scene_active_=scene_active;
 if(changed)log_state("ui_context_transition");
}
void HudVisibility::reset_context() noexcept {
 context_=RaceHudContext{};context_.reason="device_reset";scene_active_=false;device_valid_=false;hook_owned_=false;
 log_state("device_reset");
}
bool HudVisibility::should_suppress(const HudDrawFacts& facts) noexcept {
 if(!facts.callsite_exact)return false;
 if(!requested_hidden_)return false;
 const bool same_scene=context_.valid&&facts.context_current&&facts.race_generation==context_.race_generation&&
  facts.owner_lifetime==context_.owner_lifetime;
 const bool owned_context=config_valid_&&exact_build_&&scene_active_&&device_valid_&&hook_owned_&&
  context_.valid&&context_.pause_known&&!context_.paused&&same_scene;
 if(owned_context&&global_hud_draw_should_suppress(true,facts)){
  ++known_hud_draws_;++suppressed_hud_draws_;return true;
 }
 ++rejected_ambiguous_draws_;return false;
}
void HudVisibility::log_state(const char* reason) noexcept {
 try{session().write("{\"type\":\"hud_hide_state\",\"requested_hidden\":"+(requested_hidden_?std::string("true"):"false")+
  ",\"effective_hidden\":"+(effective_hidden()?std::string("true"):"false")+
  ",\"current_ui_context\":"+quote(scene_active_&&context_.valid?(context_.replay?(context_.paused?"replay_paused":"replay_running"):(context_.paused?"paused_race":"gameplay_running")):"unknown")+
  ",\"replay_mode\":"+(context_.replay?"true":"false")+
  ",\"race_generation\":"+std::to_string(context_.race_generation)+",\"owner_lifetime\":"+std::to_string(context_.owner_lifetime)+
  ",\"reason\":"+quote(reason?reason:"unknown")+",\"context_reason\":"+quote(context_.reason?context_.reason:"unknown")+"}");}catch(...){}
 last_state_reason_=reason?reason:"unknown";
}
void HudVisibility::finish_frame() noexcept {
 known_hud_draws_=suppressed_hud_draws_=rejected_ambiguous_draws_=0;clean_view_suppressed_=false;
}
std::string HudVisibility::json() const {
 std::ostringstream o;o<<"{\"requested_hidden\":"<<(requested_hidden_?"true":"false")
  <<",\"effective_hidden\":"<<(effective_hidden()?"true":"false")
  <<",\"toggle_enabled\":"<<(toggle_enabled_?"true":"false")<<",\"toggle_key\":"<<key_
  <<",\"current_ui_context\":"<<quote(scene_active_&&context_.valid?(context_.replay?(context_.paused?"replay_paused":"replay_running"):(context_.paused?"paused_race":"gameplay_running")):"unknown")
  <<",\"replay_mode\":"<<(context_.replay?"true":"false")
  <<",\"policy_ready\":"<<(policy_ready()?"true":"false")
  <<",\"context_reason\":"<<quote(context_.reason?context_.reason:"unknown")
  <<",\"race_generation\":"<<context_.race_generation<<",\"owner_lifetime\":"<<context_.owner_lifetime
  <<",\"scene_active\":"<<(scene_active_?"true":"false")<<",\"exact_build\":"<<(exact_build_?"true":"false")
  <<",\"device_valid\":"<<(device_valid_?"true":"false")<<",\"consumer_hook_owned\":"<<(hook_owned_?"true":"false")
  <<",\"known_hud_draws\":"<<known_hud_draws_<<",\"suppressed_hud_draws\":"<<suppressed_hud_draws_
  <<",\"preserved_menu_draws\":null,\"rejected_ambiguous_draws\":"<<rejected_ambiguous_draws_
  <<",\"clean_view_suppressed_draws\":"<<(clean_view_suppressed_?1:0)
  <<",\"policy_reason\":"<<quote(!requested_hidden_?"user_visible":!config_valid_?"invalid_config":!exact_build_?"unsupported_build":!scene_active_?"outside_scene":!context_.valid?context_.reason:!context_.pause_known?"pause_state_unknown":context_.paused?"interactive_pause_preserved":!hook_owned_?"consumer_hook_unowned":policy_ready()?(context_.replay?"certified_replay_ui":"certified_gameplay_ui"):"draw_scope_unavailable")<<"}";
 return o.str();
}
}
