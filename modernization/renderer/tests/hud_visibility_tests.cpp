#include "hud_visibility.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;

HudDrawFacts eligible(){
 HudDrawFacts f{};f.exact_build=f.render_thread=f.device_valid=f.scene_active=true;
 f.race_context_valid=f.pause_known=f.hook_owned=f.consumer_scope=f.identity_current=f.callsite_exact=f.fvf_known=true;
 f.context_current=true;f.race_generation=4;f.owner_lifetime=9;
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
}
void visibility_lifetime(){
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"HUD.ToggleEnabled","1"},{"HUD.ToggleKey","H"},
  {"HUD.HiddenAtStartup","0"},{"HUD.PreserveMenus","0"}},true);
 CHECK(c.hud_toggle_enabled&&c.hud_toggle_key=='H'&&!c.hud_hidden_at_startup&&c.hud_preserve_menus&&c.hud_reason=="preserve_menus_enforced");
 HudVisibility h;h.configure(c,true,true);CHECK(!h.requested_hidden()&&h.toggle_enabled());
 CHECK(h.sample_key(true,true)&&h.requested_hidden());CHECK(!h.sample_key(true,true)&&h.requested_hidden());
 HudVisibility replay_h;replay_h.configure(c,true,true);CHECK(replay_h.sample_key(true,true));
 auto replay_context=race(false,true);replay_h.observe_context(replay_context,true,true,true,true);
 CHECK(replay_h.should_suppress(eligible())&&replay_h.policy_ready());
 CHECK(replay_h.json().find("\"current_ui_context\":\"replay_running\"")!=std::string::npos);
 CHECK(replay_h.json().find("\"replay_mode\":true")!=std::string::npos);
 CHECK(replay_h.json().find("\"policy_reason\":\"certified_replay_ui\"")!=std::string::npos);
 replay_context.paused=true;replay_context.reason="certified_paused_replay";replay_h.observe_context(replay_context,true,true,true,true);
 CHECK(!replay_h.should_suppress(eligible())&&!replay_h.policy_ready()&&replay_h.requested_hidden());
 h.observe_context(race(),true,true,true,true);CHECK(h.should_suppress(eligible()));CHECK(h.effective_hidden());CHECK(h.policy_ready());
 auto ambiguous=eligible();ambiguous.identity_current=false;CHECK(!h.should_suppress(ambiguous));
 auto stale=eligible();stale.context_current=false;CHECK(!h.should_suppress(stale));
 stale=eligible();stale.race_generation++;CHECK(!h.should_suppress(stale));
 stale=eligible();stale.owner_lifetime++;CHECK(!h.should_suppress(stale));
 auto paused=race(true);h.observe_context(paused,true,true,true,true);CHECK(!h.should_suppress(eligible()));CHECK(!h.policy_ready());
 h.end_scene();CHECK(h.requested_hidden());CHECK(!h.should_suppress(eligible()));
 h.reset_context();CHECK(h.requested_hidden());
 auto active=race();h.observe_context(active,true,true,true,true);CHECK(h.should_suppress(eligible()));
 CHECK(h.json().find("\"suppressed_hud_draws\":2")!=std::string::npos);
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
}
int main(){try{edge_contracts();strict_draw_contracts();visibility_lifetime();config_conflicts();
 std::cout<<"HUD edge input / strict native draw policy / live scene identity / persistent request / fail-open reset / key compatibility: PASS\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
