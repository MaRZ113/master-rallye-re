#include "hud_visibility.hpp"
#include "clean_view.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;

HudDrawFacts eligible(){
 HudDrawFacts f{};f.exact_build=f.render_thread=f.device_valid=f.scene_active=true;
 f.race_context_valid=f.pause_known=f.hook_owned=f.consumer_scope=f.identity_current=f.callsite_exact=f.fvf_known=true;
 f.context_current=true;f.race_generation=4;f.owner_lifetime=9;
 f.ui_identity_complete=true;f.ui_epoch=7;f.device_id=2;f.ui_entity=0x1000;f.ui_packet=0x2000;f.ui_point=0x3000;f.ui_storage=0x4000;f.ui_packet_mode=2;
 f.fvf=0x142;f.primitive=D3DPT_TRIANGLELIST;f.primitive_count=1;return f;
}
RaceHudContext race(bool paused=false,bool replay=false){RaceHudContext c;c.valid=c.pause_known=true;c.paused=paused;c.replay=replay;c.race_generation=4;c.owner_lifetime=9;c.reason=replay?(paused?"certified_paused_replay":"certified_active_replay"):(paused?"certified_paused_race":"certified_active_race");return c;}
void edge_contracts(){
 bool down=false;CHECK(!hud_toggle_edge(false,true,down)&&down);CHECK(!hud_toggle_edge(true,true,down));
 CHECK(!hud_toggle_edge(true,true,down));CHECK(!hud_toggle_edge(true,false,down));CHECK(hud_toggle_edge(true,true,down));
 CHECK(!hud_toggle_edge(false,false,down)&&!down);CHECK(!hud_toggle_edge(true,false,down));CHECK(hud_toggle_edge(true,true,down));
}
void strict_draw_contracts(){
 auto f=eligible();CHECK(global_hud_draw_should_suppress(true,f));CHECK(!global_hud_draw_should_suppress(false,f));
 auto reject=[&](auto mutate){auto bad=f;mutate(bad);CHECK(!global_hud_draw_should_suppress(true,bad));};
 reject([](auto& v){v.exact_build=false;});reject([](auto& v){v.render_thread=false;});reject([](auto& v){v.device_valid=false;});
 reject([](auto& v){v.scene_active=false;});reject([](auto& v){v.race_context_valid=false;});reject([](auto& v){v.pause_known=false;});
 reject([](auto& v){v.paused=true;});reject([](auto& v){v.hook_owned=false;});reject([](auto& v){v.consumer_scope=false;});
 reject([](auto& v){v.identity_current=false;});reject([](auto& v){v.callsite_exact=false;});reject([](auto& v){v.fvf_known=false;});
 reject([](auto& v){v.fvf=0x112;});reject([](auto& v){v.primitive=D3DPT_TRIANGLESTRIP;});reject([](auto& v){v.primitive_count=0;});
 auto attract=eligible();attract.pause_known=false;attract.attract_context=true;CHECK(global_hud_draw_should_suppress(true,attract));
 attract.attract_context=false;CHECK(!global_hud_draw_should_suppress(true,attract));
}
void visibility_lifetime(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"},
  {"HUD.HiddenAtStartup","0"},{"HUD.PreserveMenus","0"}},true);
 CHECK(c.hud_toggle_enabled&&c.hud_toggle_key=='H'&&!c.hud_hidden_at_startup&&c.hud_preserve_menus&&c.hud_reason=="preserve_menus_enforced");
 HudVisibility h;h.configure(c,true,true);CHECK(!h.requested_hidden()&&h.toggle_enabled());
 CHECK(h.sample_key(true,true)&&h.requested_hidden());CHECK(!h.sample_key(true,true)&&h.requested_hidden());
 HudVisibility replay_h;replay_h.configure(c,true,true);CHECK(replay_h.sample_key(true,true));
 auto replay_context=race(false,true);replay_h.observe_context(replay_context,true,true,true,true);
 auto replay_draw=eligible();replay_draw.replay_context=true;
 CHECK(replay_h.should_suppress(replay_draw)&&replay_h.policy_ready());
 CHECK(replay_h.json().find("\"current_ui_context\":\"replay_running\"")!=std::string::npos);
 CHECK(replay_h.json().find("\"replay_mode\":true")!=std::string::npos);
 CHECK(replay_h.json().find("\"policy_reason\":\"certified_replay_ui\"")!=std::string::npos);
 replay_context.paused=true;replay_context.reason="certified_paused_replay";replay_h.observe_context(replay_context,true,true,true,true);
 replay_draw.paused=true;
 CHECK(replay_h.should_suppress(replay_draw)&&replay_h.policy_ready()&&replay_h.requested_hidden());
 CHECK(replay_h.json().find("\"policy_reason\":\"paused_replay_ui_suppressed\"")!=std::string::npos);
 auto replay_pause_control=replay_draw;++replay_pause_control.ui_packet;++replay_pause_control.ui_entity;
 CHECK(replay_h.should_suppress(replay_pause_control));
 CHECK(replay_h.json().find("\"replay_pause_overlay_suppressed_draws\":1")!=std::string::npos);
 HudVisibility attract_h;attract_h.configure(c,true,true);CHECK(attract_h.sample_key(true,true));
 RaceHudContext attract_context{};attract_context.valid=true;attract_context.attract=true;attract_context.race_generation=4;attract_context.owner_lifetime=9;attract_context.reason="certified_attract_demo_hud";
 attract_h.observe_context(attract_context,true,true,true,true);auto attract_draw=eligible();attract_draw.pause_known=false;attract_draw.attract_context=true;
 CHECK(attract_h.should_suppress(attract_draw)&&attract_h.policy_ready());
 auto mismatched_attract_draw=attract_draw;mismatched_attract_draw.attract_context=false;CHECK(!attract_h.should_suppress(mismatched_attract_draw));
 CHECK(attract_h.json().find("\"current_ui_context\":\"attract_demo\"")!=std::string::npos);
 CHECK(attract_h.json().find("\"policy_reason\":\"certified_attract_demo_hud\"")!=std::string::npos);
 auto start_context=race();start_context.startup_countdown=true;start_context.reason="certified_start_countdown";
 HudVisibility countdown_h;countdown_h.configure(c,true,true);CHECK(countdown_h.sample_key(true,true));countdown_h.observe_context(start_context,true,true,true,true);
 auto countdown_draw=eligible();countdown_draw.startup_countdown=true;CHECK(countdown_h.should_suppress(countdown_draw)&&countdown_h.policy_ready());
 auto mismatched_countdown_draw=countdown_draw;mismatched_countdown_draw.startup_countdown=false;CHECK(!countdown_h.should_suppress(mismatched_countdown_draw));
 CHECK(countdown_h.json().find("\"current_ui_context\":\"gameplay_start_countdown\"")!=std::string::npos);
 h.observe_context(race(),true,true,true,true);CHECK(h.should_suppress(eligible()));CHECK(h.effective_hidden());CHECK(h.policy_ready());
 auto ambiguous=eligible();ambiguous.identity_current=false;CHECK(!h.should_suppress(ambiguous));
 auto stale=eligible();stale.context_current=false;CHECK(!h.should_suppress(stale));
 stale=eligible();stale.race_generation++;CHECK(!h.should_suppress(stale));
 stale=eligible();stale.owner_lifetime++;CHECK(!h.should_suppress(stale));
 auto paused=race(true);h.observe_context(paused,true,true,true,true);auto paused_draw=eligible();paused_draw.paused=true;CHECK(h.should_suppress(paused_draw));CHECK(h.policy_ready());
 h.end_scene();CHECK(h.requested_hidden());CHECK(!h.should_suppress(eligible()));
 h.reset_context();CHECK(h.requested_hidden());
 auto active=race();h.observe_context(active,true,true,true,true);CHECK(h.should_suppress(eligible()));
 CHECK(h.json().find("\"suppressed_hud_draws\":3")!=std::string::npos);
 h.end_scene();h.finish_frame();CHECK(!h.effective_hidden()&&h.requested_hidden());
 auto hidden=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.HiddenAtStartup","1"},{"HUD.ToggleEnabled","0"}},true);
 HudVisibility startup;startup.configure(hidden,true,true);CHECK(startup.requested_hidden()&&!startup.toggle_enabled());
 CHECK(!startup.sample_key(true,true)&&startup.requested_hidden());
 auto reset=hidden;reset.hud_hidden_at_startup=false;startup.configure(reset,false,false);CHECK(!startup.requested_hidden());startup.observe_context(race(),false,true,false,true);CHECK(!startup.should_suppress(eligible()));
}
void config_conflicts(){
 auto legacy=parse_visual_config({{"Renderer.ConfigVersion","1"},{"FreeCameraKeys.ToggleCleanView","G"}},true);
 CHECK(legacy.hud_toggle_key=='G'&&legacy.hud_toggle_valid&&legacy.hud_toggle_enabled);
 auto explicit_key=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleKey","H"},{"FreeCameraKeys.ToggleCleanView","G"}},true);
 CHECK(explicit_key.hud_toggle_key=='H'&&explicit_key.hud_toggle_valid);
 auto f10=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleKey","F10"}},true);
 CHECK(!f10.hud_toggle_enabled&&!f10.hud_toggle_valid);
 auto conflict=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleKey","C"}},true);
 CHECK(!conflict.hud_toggle_enabled&&!conflict.hud_toggle_valid&&conflict.hud_reason=="toggle_conflicts_with_free_camera_binding");
 auto legacy_start=parse_visual_config({{"Renderer.ConfigVersion","1"},{"FreeCamera.CleanViewEnabled","1"}},true);
 CHECK(legacy_start.hud_hidden_at_startup);
 auto preserve_default=parse_visual_config({{"Renderer.ConfigVersion","1"}},true);CHECK(preserve_default.hud_preserve_pause);
 auto preserve_off=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.PreservePause","0"}},true);CHECK(!preserve_off.hud_preserve_pause&&config_json(preserve_off).find("\"hud_preserve_pause\":false")!=std::string::npos);
 auto preserve_invalid=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.PreservePause","maybe"}},true);CHECK(preserve_invalid.hud_preserve_pause);
}
void paused_clean_view_contract(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"}},true);
 HudVisibility h;h.configure(c,true,true);CHECK(h.sample_key(true,true)&&h.requested_hidden());
 h.observe_context(race(true),true,true,true,true);auto paused_draw=eligible();paused_draw.paused=true;
 CHECK(!h.should_suppress(paused_draw)&&!h.effective_hidden());
 CHECK(h.json().find("\"policy_reason\":\"paused_race_unknown_ui_preserved\"")!=std::string::npos);
 CleanViewDrawFacts clean{};clean.exact_build=clean.hook_owned=clean.render_thread=clean.consumer_scope=clean.identity_complete=clean.identity_current=clean.callsite_exact=clean.fvf_known=true;
 clean.fvf=0x142;clean.primitive=D3DPT_TRIANGLELIST;clean.primitive_count=3;
 CHECK(clean_view_draw_eligible(clean)&&clean_view_should_suppress(true,h.requested_hidden(),true));
 h.note_clean_view_suppressed();CHECK(h.effective_hidden());
 CHECK(h.json().find("\"policy_reason\":\"paused_freecam_clean_view\"")!=std::string::npos);
}
void normal_pause_learned_hud_contract(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"}},true);
 HudVisibility h;h.configure(c,true,true);
 auto running=race();h.observe_context(running,true,true,true,true);
 auto hud=eligible();CHECK(!h.should_suppress(hud)); // Learning is independent of the user's current visibility preference.
 CHECK(h.json().find("\"learned_race_hud_signatures\":1")!=std::string::npos);
 CHECK(h.json().find("\"learned_replay_signatures\":0")!=std::string::npos);
 CHECK(h.sample_key(true,true)&&h.requested_hidden());
 auto paused=race(true);h.observe_context(paused,true,true,true,true);hud.paused=true;
 CHECK(h.policy_ready()&&h.should_suppress(hud)&&h.effective_hidden());
 CHECK(h.json().find("\"paused_race_suppressed_draws\":1")!=std::string::npos);
 auto pause_menu=hud;++pause_menu.ui_entity;++pause_menu.ui_packet;++pause_menu.ui_point;++pause_menu.ui_storage;
 CHECK(!h.should_suppress(pause_menu)); // New pause-menu identity fails open.
 CHECK(h.json().find("\"paused_race_preserved_unknown_draws\":1")!=std::string::npos);
 CHECK(h.json().find("\"policy_reason\":\"paused_race_known_hud_suppressed\"")!=std::string::npos);

 HudVisibility no_history;no_history.configure(c,true,true);CHECK(no_history.sample_key(true,true));
 no_history.observe_context(paused,true,true,true,true);CHECK(!no_history.policy_ready());
 CHECK(!no_history.should_suppress(hud)); // Joining directly into pause has no learned HUD ownership: preserve all UI.
}
void normal_pause_config_contract(){
 auto base=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"}},true);
 auto full_ui=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"},{"HUD.PreservePause","0"}},true);
 HudVisibility preserve;preserve.configure(base,true,true);CHECK(preserve.sample_key(true,true));preserve.observe_context(race(true),true,true,true,true);
 auto pause_ui=eligible();pause_ui.paused=true;CHECK(!preserve.should_suppress(pause_ui));
 CHECK(preserve.json().find("\"policy_reason\":\"paused_race_unknown_ui_preserved\"")!=std::string::npos);
 HudVisibility hide;hide.configure(full_ui,true,true);CHECK(hide.sample_key(true,true));hide.observe_context(race(true),true,true,true,true);
 CHECK(hide.policy_ready()&&hide.should_suppress(pause_ui));
 CHECK(hide.json().find("\"paused_race_overlay_suppressed_draws\":1")!=std::string::npos);
 auto ambiguous=pause_ui;ambiguous.identity_current=false;CHECK(!hide.should_suppress(ambiguous));

 // A fully verified paused-Freecam context always hides complete pause UI,
 // regardless of PreservePause. The production wrapper supplies this only
 // after the shared fresh-snapshot/device/race/camera admission succeeds.
 HudVisibility freecam;freecam.configure(base,true,true);CHECK(freecam.sample_key(true,true));freecam.observe_context(race(true),true,true,true,true);
 auto freecam_pause=pause_ui;freecam_pause.paused_freecam_context=true;
 CHECK(freecam.should_suppress(freecam_pause)&&freecam.policy_ready());
 CHECK(freecam.json().find("\"paused_freecam_suppressed_draws\":1")!=std::string::npos);
 auto stale_freecam=pause_ui;stale_freecam.paused_freecam_context=false;CHECK(!freecam.should_suppress(stale_freecam));
 HudVisibility freecam_config_off;freecam_config_off.configure(full_ui,true,true);CHECK(freecam_config_off.sample_key(true,true));freecam_config_off.observe_context(race(true),true,true,true,true);
 CHECK(freecam_config_off.should_suppress(freecam_pause)&&freecam_config_off.json().find("\"paused_freecam_suppressed_draws\":1")!=std::string::npos);
}
void replay_pause_learned_identity_contract(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"}},true);
 HudVisibility h;h.configure(c,true,true);auto active=race(false,true);h.observe_context(active,true,true,true,true);
 auto draw=eligible();draw.replay_context=true;
 CHECK(!h.requested_hidden()&&!h.should_suppress(draw));
 CHECK(h.json().find("\"learned_replay_signatures\":1")!=std::string::npos);
 CHECK(h.sample_key(true,true)&&h.requested_hidden());
 auto paused=race(true,true);h.observe_context(paused,true,true,true,true);draw.paused=true;
 CHECK(h.should_suppress(draw)&&h.policy_ready());
 auto pause_window=draw;pause_window.ui_storage+=4;pause_window.ui_packet+=0x100;pause_window.ui_entity+=0x100;
 CHECK(h.should_suppress(pause_window));
 auto new_epoch_identity=draw;new_epoch_identity.ui_epoch++;CHECK(h.should_suppress(new_epoch_identity));
 auto unknown=draw;unknown.ui_identity_complete=false;CHECK(!h.should_suppress(unknown));
 unknown=draw;unknown.owner_lifetime++;CHECK(!h.should_suppress(unknown));
 unknown=draw;unknown.identity_current=false;CHECK(!h.should_suppress(unknown));
 CHECK(h.json().find("\"replay_pause_suppressed_draws\":3")!=std::string::npos);
 CHECK(h.json().find("\"replay_pause_overlay_suppressed_draws\":2")!=std::string::npos);
 CHECK(h.json().find("\"replay_pause_preserved_unknown_draws\":1")!=std::string::npos);
 h.reset_context();CHECK(h.json().find("\"learned_replay_signatures\":0")!=std::string::npos);
 h.observe_context(paused,true,true,true,true);CHECK(h.should_suppress(draw));
 CHECK(h.json().find("\"replay_pause_overlay_suppressed_draws\":3")!=std::string::npos);
}
void replay_signature_capacity_and_lifecycle(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"}},true);
 HudVisibility h;h.configure(c,true,true);auto running=race(false,true);h.observe_context(running,true,true,true,true);
 auto draw=eligible();draw.replay_context=true;
 for(uintptr_t i=0;i<512;++i){draw.ui_entity=0x10000+i;CHECK(!h.should_suppress(draw));}
 CHECK(h.json().find("\"learned_replay_signatures\":512")!=std::string::npos);
 draw.ui_entity=0x20000;CHECK(!h.should_suppress(draw));
 CHECK(h.json().find("\"replay_signature_overflow\":1")!=std::string::npos);
 CHECK(h.sample_key(true,true));auto paused=race(true,true);h.observe_context(paused,true,true,true,true);draw.paused=true;
 draw.ui_entity=0x10000+511;CHECK(h.should_suppress(draw));draw.ui_entity=0x20000;CHECK(h.should_suppress(draw));
 CHECK(h.json().find("\"replay_pause_overlay_suppressed_draws\":1")!=std::string::npos);
 auto new_owner=paused;new_owner.owner_lifetime++;new_owner.reason="new_replay_owner";h.observe_context(new_owner,true,true,true,true);
 draw.owner_lifetime=new_owner.owner_lifetime;CHECK(h.should_suppress(draw));
 CHECK(h.json().find("\"learned_replay_signatures\":0")!=std::string::npos);
}
void replay_pause_overlay_admission_contract(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"}},true);
 HudVisibility h;h.configure(c,true,true);CHECK(h.sample_key(true,true));
 auto paused=race(true,true);h.observe_context(paused,true,true,true,true);
 auto first=eligible();first.paused=true;first.replay_context=true;
 CHECK(h.policy_ready());CHECK(h.should_suppress(first));
 CHECK(h.json().find("\"learned_replay_signatures\":0")!=std::string::npos);
 auto incomplete=first;incomplete.ui_identity_complete=false;CHECK(!h.should_suppress(incomplete));
 auto wrong_site=first;wrong_site.callsite_exact=false;CHECK(!h.should_suppress(wrong_site));
 auto non_replay_pause=race(true,false);h.observe_context(non_replay_pause,true,true,true,true);
 auto pause_menu=eligible();pause_menu.paused=true;CHECK(!h.should_suppress(pause_menu));
 CHECK(h.json().find("\"policy_reason\":\"paused_race_unknown_ui_preserved\"")!=std::string::npos);
 RaceHudContext frontend{};frontend.reason="committed_scene_not_race_hud";
 h.observe_context(frontend,true,true,true,true);auto menu=eligible();menu.context_current=false;
 CHECK(!h.should_suppress(menu));
}
int main(){try{edge_contracts();strict_draw_contracts();visibility_lifetime();config_conflicts();paused_clean_view_contract();
 normal_pause_learned_hud_contract();normal_pause_config_contract();replay_pause_learned_identity_contract();replay_signature_capacity_and_lifecycle();
 replay_pause_overlay_admission_contract();
 std::cout<<"HUD edge input / strict native draw policy / live scene identity / persistent request / fail-open reset / key compatibility: PASS\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
