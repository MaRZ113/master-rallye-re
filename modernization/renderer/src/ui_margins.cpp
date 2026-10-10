#include "ui_margins.hpp"
#include "margin_rules.hpp"
#include "provenance.hpp"
#include "trace.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <sstream>
#include <cfenv>
#include <exception>
namespace gfx2 {
namespace {struct MarginFP {fenv_t saved;MarginFP(){fegetenv(&saved);}~MarginFP(){fesetenv(&saved);}};}
namespace {
void json_float(std::ostringstream& out,float value) {if(std::isfinite(value))out<<value;else out<<"null";}
const char* scene_family_name(int value) noexcept {return value==0?"frontend":value==1?"race":"unknown";}
std::array<uint64_t,6> observation_identity_order(const MarginIdentity& key,uint64_t epoch) noexcept {
 return {static_cast<uint64_t>(key.entity),static_cast<uint64_t>(key.packet),static_cast<uint64_t>(key.point),static_cast<uint64_t>(key.storage),key.mode,epoch};
}
}
int margin_direction(float x,float y,float z) noexcept {
 if(z!=0||!std::isfinite(x)||!std::isfinite(y))return 0;
 for(const auto& rule:MARGIN_RULES)if(x==rule.x&&y==rule.y)return rule.direction;
 if(x>=25&&x<=106&&((y>=19&&y<100)||(y>=259&&y<340)))return -1;return 0;
}
const char* margin_source(float x,float y,float z) noexcept {
 if(!margin_direction(x,y,z))return "none";
 for(const auto& rule:MARGIN_RULES)if(x==rule.x&&y==rule.y)return "exact_historical_rule";
 return "left_text_band";
}
bool eligible_ui_packet(uintptr_t entity,uintptr_t coordinates) noexcept {
 uintptr_t packet=0;uint32_t mode=0;
 return entity&&safe_copy(&packet,reinterpret_cast<void*>(entity+0x4c),4)&&packet&&
  coordinates==packet+0x24&&safe_copy(&mode,reinterpret_cast<void*>(packet+0x68),4)&&(mode==1||mode==2);
}
bool read_margin_identity(uintptr_t entity,uintptr_t coordinates,MarginIdentity& key) noexcept {
 key={};uintptr_t packet=0,storage=0;uint32_t mode=0;
 if(!eligible_ui_packet(entity,coordinates)||!safe_copy(&packet,reinterpret_cast<void*>(entity+0x4c),4)||
    !safe_copy(&mode,reinterpret_cast<void*>(packet+0x68),4)||!safe_copy(&storage,reinterpret_cast<void*>(packet+8),4))return false;
 // +8 is the content row-vector allocation read by the verified consumer.
 // XYZ, colors, UVs and changing strings are deliberately not part of identity.
 key={entity,packet,coordinates+0x30,storage,mode};return true;
}
size_t MarginAnchors::size() const noexcept {size_t n=0;for(const auto& a:entries_)if(a.id)++n;return n;}
void MarginAnchors::begin_epoch(const char* reason) noexcept {
 invalidations+=size();entries_={};clear_carousels();++epoch_;epoch_reason_=reason;context_=-1;
}
void MarginAnchors::scene_context(bool race) noexcept {
 int next=race?1:0;if(context_>=0&&context_!=next)begin_epoch("scene_family_changed");context_=next;
}
void MarginAnchors::reject(uintptr_t entity) noexcept {
 for(auto& a:entries_)if(a.id&&a.key.entity==entity){a={};++invalidations;}
 for(auto& track:carousel_)if(track.id&&track.key.entity==entity){track={};++carousel_invalidations;}
}
void MarginAnchors::next_frame() noexcept {
 // Grace covers short submission gaps, never packet/storage/epoch replacement.
 // Expire at the completion of the third absent frame, not during animation.
 for(auto& a:entries_)if(a.id&&frame_-a.last>MARGIN_ANCHOR_GRACE_FRAMES){a={};++invalidations;++grace_expired;}
 for(auto& track:carousel_)if(track.id&&frame_-track.last>MARGIN_ANCHOR_GRACE_FRAMES){track={};++carousel_invalidations;}
 ++frame_;
}
MarginAnchorDecision MarginAnchors::resolve(const MarginIdentity& key,float x,float y,float z) noexcept {
 MarginAnchorDecision d;d.epoch=epoch_;d.current_rule=margin_direction(x,y,z);d.invalidated=epoch_reason_;
 if(!key.entity||!key.packet||!key.point||!key.storage||(key.mode!=1&&key.mode!=2)||z!=0||!std::isfinite(x)||!std::isfinite(y)){
  reject(key.entity);d.invalidated="invalid_packet_or_point";return d;
 }
 Anchor* free=nullptr;
 for(auto& a:entries_){
  if(a.id&&a.key.entity==key.entity){
   const char* changed=a.key.packet!=key.packet?"packet_replacement":a.key.point!=key.point?"point_replacement":a.key.mode!=key.mode?"packet_mode_changed":a.key.storage!=key.storage?"content_storage_replacement":nullptr;
   if(changed){a={};++invalidations;d.invalidated=changed;}
   else {d.grace_retained=frame_>a.last+1;if(d.grace_retained)++anchor_grace_retained;a.last=frame_;d.id=a.id;d.direction=a.direction;d.retained=true;d.source="retained_identity";d.invalidated="none";if(!d.current_rule)++retained_anchor_without_current_rule_match;return d;}
  }
  if(!a.id&&!free)free=&a;
 }
 if(!d.current_rule)return d;
 if(!free){++overflow;d.invalidated="anchor_capacity";return d;}
 *free={key,++next_id_,frame_,d.current_rule};++admissions;d.id=free->id;d.direction=free->direction;d.admitted=true;d.source=margin_source(x,y,z);return d;
}
CarouselSemanticDecision MarginAnchors::observe_carousel(const MarginIdentity& key,float x,float y,uint64_t frame,
 bool frontend_context,bool verified_ui_draw,bool left_anchor_evidence) noexcept {
 CarouselSemanticDecision result;
 if(!frontend_context){result.status="context_not_frontend";return result;}
 if(!verified_ui_draw){result.status="draw_not_verified";return result;}
 if(!key.entity||!key.packet||!key.point||!key.storage||(key.mode!=1&&key.mode!=2)||
    !std::isfinite(x)||!std::isfinite(y)||y<CAROUSEL_LANE_MIN_Y||y>CAROUSEL_LANE_MAX_Y){result.status="outside_carousel_lane";return result;}
 CarouselTrack* found=nullptr;CarouselTrack* free=nullptr;CarouselTrack* oldest=nullptr;
 for(auto& track:carousel_){
  if(!track.id){if(!free)free=&track;continue;}
  if(track.epoch!=epoch_){track={};++carousel_invalidations;if(!free)free=&track;continue;}
  if(track.key.entity==key.entity){
   if(track.key.packet==key.packet&&track.key.point==key.point&&track.key.storage==key.storage&&track.key.mode==key.mode)found=&track;
   else {track={};++carousel_invalidations;if(!free)free=&track;}
  }
  if(!oldest||track.last<oldest->last)oldest=&track;
 }
 if(!found){
  if(!free){if(!oldest){++carousel_overflow;result.status="capacity_unavailable";return result;}free=oldest;*free={};++carousel_overflow;++carousel_invalidations;}
  found=free;*found={};found->key=key;found->id=++next_carousel_id_;found->epoch=epoch_;found->first=frame;found->last=frame;
  found->min_x=found->max_x=x;found->samples=1;found->saw_center=x>=CAROUSEL_CENTER_MIN_X&&x<=CAROUSEL_CENTER_MAX_X;
  found->saw_outer_left=x<=CAROUSEL_OUTER_LEFT_MAX_X;found->saw_outer_right=x>=CAROUSEL_OUTER_RIGHT_MIN_X;
 }else if(frame!=found->last){
  if(frame<found->last||frame-found->last>MARGIN_ANCHOR_GRACE_FRAMES){
   *found={};++carousel_invalidations;found->key=key;found->id=++next_carousel_id_;found->epoch=epoch_;found->first=frame;found->last=frame;
   found->min_x=found->max_x=x;found->samples=1;found->saw_center=x>=CAROUSEL_CENTER_MIN_X&&x<=CAROUSEL_CENTER_MAX_X;
   found->saw_outer_left=x<=CAROUSEL_OUTER_LEFT_MAX_X;found->saw_outer_right=x>=CAROUSEL_OUTER_RIGHT_MIN_X;
  }else{
   found->last=frame;++found->samples;found->min_x=std::min(found->min_x,x);found->max_x=std::max(found->max_x,x);
   found->saw_center|=x>=CAROUSEL_CENTER_MIN_X&&x<=CAROUSEL_CENTER_MAX_X;
   found->saw_outer_left|=x<=CAROUSEL_OUTER_LEFT_MAX_X;found->saw_outer_right|=x>=CAROUSEL_OUTER_RIGHT_MIN_X;
  }
 }
 found->saw_left_anchor|=left_anchor_evidence;
 result.id=found->id;result.candidate=true;result.proven=found->proven;
 if(!found->proven&&found->saw_left_anchor&&found->samples>=2&&found->saw_center&&
    (found->saw_outer_left||found->saw_outer_right)&&found->max_x-found->min_x>=CAROUSEL_MIN_TRAVEL_X){
  found->proven=true;result.proven=true;result.promoted=true;++carousel_promotions;
 }
 result.status=result.promoted?"promoted_motion_path":result.proven?"proven_motion_path":"candidate_motion_path";return result;
}
bool MarginAnchors::discard_for_carousel(const MarginIdentity& key) noexcept {
 for(auto& anchor:entries_)if(anchor.id&&anchor.key.entity==key.entity&&anchor.key.packet==key.packet&&
    anchor.key.point==key.point&&anchor.key.storage==key.storage&&anchor.key.mode==key.mode){anchor={};++carousel_anchor_discards;return true;}
 return false;
}
void MarginAnchors::clear_carousels() noexcept {for(auto& track:carousel_)if(track.id)++carousel_invalidations;carousel_={};}
bool UiJumpPatch::exchange(PatchMemory& m,const std::array<unsigned char,5>& from,const std::array<unsigned char,5>& to) noexcept {
 std::array<unsigned char,5> seen{};DWORD old=0,ignored=0;
 if(!m.read(seen.data(),site_,5)||seen!=from||!m.protect(site_,5,PAGE_EXECUTE_READWRITE,old))return false;
 bool okay=m.write(site_,to.data(),5)&&m.flush(site_,5)&&m.read(seen.data(),site_,5)&&seen==to;
 bool protected_ok=m.protect(site_,5,old,ignored);
 if(!okay||!protected_ok){DWORD roll=0;if(m.protect(site_,5,PAGE_EXECUTE_READWRITE,roll)){m.write(site_,from.data(),5);m.flush(site_,5);m.protect(site_,5,old,ignored);}okay=false;}
 if(m.read(seen.data(),site_,5))installed_=seen==after_;return okay;
}
bool UiJumpPatch::install(PatchMemory& m,void* site,uintptr_t destination) noexcept {
 if(installed_||!site||!destination)return false;site_=site;after_[0]=0xe9;
 uint32_t relative=static_cast<uint32_t>(destination)-static_cast<uint32_t>(reinterpret_cast<uintptr_t>(site)+5);std::memcpy(after_.data()+1,&relative,4);return exchange(m,UI_SORT_BYTES,after_);
}
bool UiJumpPatch::remove(PatchMemory& m) noexcept{return !installed_||exchange(m,after_,UI_SORT_BYTES);}
bool UiPacketPatch::exchange(PatchMemory& m,const std::array<unsigned char,6>& from,const std::array<unsigned char,6>& to) noexcept {
 std::array<unsigned char,6> seen{};DWORD old=0,ignored=0;
 if(!m.read(seen.data(),site_,6)||seen!=from||!m.protect(site_,6,PAGE_EXECUTE_READWRITE,old))return false;
 bool okay=m.write(site_,to.data(),6)&&m.flush(site_,6)&&m.read(seen.data(),site_,6)&&seen==to;
 bool protected_ok=m.protect(site_,6,old,ignored);
 if(!okay||!protected_ok){DWORD roll=0;if(m.protect(site_,6,PAGE_EXECUTE_READWRITE,roll)){m.write(site_,from.data(),6);m.flush(site_,6);m.protect(site_,6,old,ignored);}okay=false;}
 if(m.read(seen.data(),site_,6))installed_=seen==after_;return okay;
}
bool UiPacketPatch::install(PatchMemory& m,void* site,uintptr_t destination) noexcept {
 if(installed_||!site||!destination)return false;site_=site;after_[0]=0xe9;after_[5]=0x90;
 uint32_t relative=static_cast<uint32_t>(destination)-static_cast<uint32_t>(reinterpret_cast<uintptr_t>(site)+5);std::memcpy(after_.data()+1,&relative,4);return exchange(m,UI_PACKET_BYTES,after_);
}
bool UiPacketPatch::remove(PatchMemory& m) noexcept{return !installed_||exchange(m,after_,UI_PACKET_BYTES);}
namespace {
class NativeMemory final:public PatchMemory {public:
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
 bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
} memory;
UiMargins* active=nullptr;
bool multiple=false;
uintptr_t sort_return=0,packet_return=0,contract_entity=0;bool contract_probe=false;
struct ReturnScope {uintptr_t address=0;UiMargins* owner=nullptr;};
thread_local std::array<ReturnScope,16> returns{};thread_local unsigned return_depth=0;
void packet_end_bridge();
void __stdcall consume_packet(uintptr_t entity,uintptr_t* return_slot) noexcept {
 if(!active&&!contract_probe)return;
 if(return_depth==returns.size()){if(active)active->disable("consumer_scope_overflow");return;}
 UiMargins* owner=active;if(owner&&!owner->enter_consume(entity))return;
 if(contract_probe)contract_entity=entity;
 returns[return_depth++]={*return_slot,owner};*return_slot=reinterpret_cast<uintptr_t>(&packet_end_bridge);
}
uintptr_t __stdcall finish_packet() noexcept {
 if(!return_depth)std::terminate();auto saved=returns[--return_depth];if(saved.owner)saved.owner->leave_consume();return saved.address;
}
// Old sort bridge is retained only for the existing native ABI contract; no UI action.
void __stdcall shift_packet(uintptr_t,uintptr_t) noexcept {}
// Preserve flags, integer registers, stack, x87 and SSE. Replay exactly the two
// overwritten instructions with the original x87 stack before returning.
__declspec(naked) void sort_bridge(){__asm {
 pushfd
 pushad
 mov ebp,esp
 and esp,-16
 sub esp,528
 fxsave [esp]
 fninit
 mov dword ptr [esp+512],01f80h
 ldmxcsr [esp+512]
 cld
 push dword ptr [ebp+28]
 push dword ptr [ebp+24]
 call shift_packet
 fxrstor [esp]
 mov esp,ebp
 popad
 popfd
 fsub dword ptr [eax+30h]
 fld st(0)
 jmp dword ptr [sort_return]
}}
__declspec(naked) void packet_bridge(){__asm {
 pushfd
 pushad
 mov ebp,esp
 and esp,-16
 sub esp,528
 fxsave [esp]
 fninit
 mov dword ptr [esp+512],01f80h
 ldmxcsr [esp+512]
 cld
 mov eax,dword ptr [ebp+12]
 lea edx,[eax+4]
 push edx
 push dword ptr [eax+8]
 call consume_packet
 fxrstor [esp]
 mov esp,ebp
 popad
 popfd
 sub esp,108h
 jmp dword ptr [packet_return]
}}

__declspec(naked) void packet_end_bridge(){__asm {
 push 0
 pushfd
 pushad
 mov ebp,esp
 and esp,-16
 sub esp,528
 fxsave [esp]
 fninit
 mov dword ptr [esp+512],01f80h
 ldmxcsr [esp+512]
 cld
 call finish_packet
 mov dword ptr [ebp+36],eax
 fxrstor [esp]
 mov esp,ebp
 popad
 popfd
 ret
}}

}
bool UiMargins::install(bool exact,bool requested,bool carousel_alignment) noexcept {
 configure_carousel_alignment(carousel_alignment,exact);
 if(!requested||!exact){reason=exact?"disabled":"unsupported_build";return false;}
 if(active||multiple){multiple=true;if(active)active->disable("multiple_devices");reason="multiple_devices";return false;}
 uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
 constexpr unsigned char expected[]={0x81,0xec,0x08,0x01,0,0,0x8b,0x84,0x24,0x0c,0x01,0,0,0x53,0x57,0x89,0x4c,0x24,0x14,0x8b,0x78,0x4c};unsigned char seen[sizeof(expected)]{};
 if(base!=0x400000||!IsProcessorFeaturePresent(PF_XMMI64_INSTRUCTIONS_AVAILABLE)||!safe_copy(seen,reinterpret_cast<void*>(base+UI_PACKET_RVA),sizeof(seen))||std::memcmp(seen,expected,sizeof(seen))){reason="ui_packet_consumer_signature_or_placement_mismatch";return false;}
 HMODULE pin=nullptr;if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&sort_bridge),&pin)){reason="module_pin_failed";return false;}
 contract_probe=false;packet_return=base+UI_PACKET_RVA+6;thread_=GetCurrentThreadId();active=this;
 enabled_=patch_.install(memory,reinterpret_cast<void*>(base+UI_PACKET_RVA),reinterpret_cast<uintptr_t>(&packet_bridge));
 configure_carousel_alignment(carousel_alignment,exact);
 reason=enabled_?"ui_packet_consumer_installed":"ui_jump_patch_failed";if(!enabled_){active=nullptr;patch_.remove(memory);}return enabled_;
}
void UiMargins::configure_carousel_alignment(bool requested,bool exact_profile) noexcept {
 carousel_alignment_requested_=requested;carousel_alignment_enabled_=enabled_&&exact_profile&&requested;
 if(!carousel_alignment_enabled_)anchors_.clear_carousels();
}
void UiMargins::dimensions(UINT w,UINT h) noexcept {MarginFP fp;half_=0;if(w&&h&&double(w)/h>=1.&&double(w)/h<=4.)half_=static_cast<float>((480.*double(w)/h-640.)*.5);}
void UiMargins::reset_capture_local() noexcept {
 observations_={};capture_records_=capture_render_local_records_=0;capture_packet_consumers_=capture_draw_observations_captured_=capture_packets_with_draws_=0;capture_consumers_without_draw_=0;
 capture_non_ui_draws_=capture_relevant_draws_=0;capture_adjusted_draws_=capture_unadjusted_draws_=0;
 capture_adjusted_packets_=capture_unadjusted_packets_=0;capture_candidate_rejections_=capture_candidate_evictions_=0;
 capture_packet_record_drops_=capture_render_local_drops_=capture_draw_drops_=capture_identity_invalidations_=capture_log_failures_=0;
 capture_draw_observation_attempts_=0;
}
bool UiMargins::emit_capture_record(const std::string& record,bool packet_record,bool render_local_record) noexcept {
 if(packet_record&&capture_records_>=UI_CAPTURE_PACKET_RECORD_LIMIT){++capture_packet_record_drops_;return false;}
 if(render_local_record&&capture_render_local_records_>=UI_CAPTURE_RENDER_LOCAL_RECORD_LIMIT){++capture_render_local_drops_;return false;}
 if(!session().write(record)){++capture_log_failures_;return false;}
 ++records_;if(render_local_record)++render_local_records_;if(packet_record)++capture_records_;if(render_local_record)++capture_render_local_records_;return true;
}
void UiMargins::capture_window(bool capture_active,uint64_t frame,uint64_t device_id,const char* end_reason) noexcept {
 MarginFP fp;frame_id_=frame;
 if(capture_active){
  if(capturing_&&device_id&&device_id_&&device_id!=device_id_)finish_capture(frame,device_id_,"device_identity_changed");
  if(!capturing_){reset_capture_local();device_id_=device_id;capture_start_frame_=capture_trace_frame_=frame;capture_completed_=false;capture_end_reason_="active";++capture_count_;capturing_=true;
   try{std::ostringstream out;out<<"{\"type\":\"ui_diagnostic_capture_start\",\"device_id\":"<<device_id_<<",\"capture_id\":"<<(device_id_?quote(trace_capture_id(device_id_,capture_start_frame_)):"null")<<",\"start_frame\":"<<capture_start_frame_<<",\"trace_frame\":"<<capture_trace_frame_<<",\"capture_frame_index\":0,\"record_budget\":"<<UI_CAPTURE_PACKET_RECORD_LIMIT<<",\"candidate_capacity\":"<<UI_CAPTURE_PACKET_CANDIDATE_LIMIT<<",\"adjusted_candidate_quota\":"<<UI_CAPTURE_ADJUSTED_CANDIDATE_QUOTA<<",\"unadjusted_candidate_quota\":"<<UI_CAPTURE_UNADJUSTED_CANDIDATE_QUOTA<<",\"draw_observations_per_packet\":"<<UI_PACKET_DRAW_OBSERVATION_LIMIT<<",\"draw_observations_per_capture\":"<<UI_CAPTURE_TOTAL_DRAW_OBSERVATION_LIMIT<<",\"window_policy\":\"one_trace_capture\",\"sample_policy\":\"verified_ui_draws_deterministic_hash_priority_adjustment_strata\"}";if(session().write(out.str()))++records_;else ++capture_log_failures_;}catch(...){++capture_log_failures_;}
  }
  capture_trace_frame_=frame;
  return;
 }
 if(capturing_)finish_capture(frame,device_id?device_id:device_id_,end_reason?end_reason:"capture_ended");
}
void UiMargins::finish_capture(uint64_t frame,uint64_t device_id,const char* end_reason) noexcept {
 if(!capturing_)return;if(device_id&&device_id!=device_id_)++capture_identity_invalidations_;capture_end_reason_=end_reason?end_reason:"capture_ended";capture_completed_=std::strcmp(capture_end_reason_,"present")==0;capture_close_pending_=false;capture_close_reason_="none";
 emit_group_candidates();
 const bool incomplete=capture_packet_record_drops_||capture_render_local_drops_||capture_draw_drops_||capture_candidate_rejections_||capture_candidate_evictions_||capture_identity_invalidations_||capture_log_failures_;
 try{std::ostringstream out;out<<"{\"type\":\"ui_diagnostic_capture_end\",\"device_id\":"<<device_id_<<",\"capture_id\":"<<(device_id_?quote(trace_capture_id(device_id_,capture_start_frame_)):"null")<<",\"start_frame\":"<<capture_start_frame_<<",\"trace_frame\":"<<capture_trace_frame_<<",\"end_frame_boundary\":"<<frame<<",\"trace_frames_observed\":"<<(capture_trace_frame_>=capture_start_frame_?capture_trace_frame_-capture_start_frame_+1:0)<<",\"complete\":"<<(capture_completed_?"true":"false")<<",\"reason\":"<<quote(capture_end_reason_)<<",\"coverage_status\":"<<quote(incomplete?"incomplete_bounded_or_write_loss":capture_relevant_draws_?"observed":capture_packet_consumers_?"no_relevant_ui_draw":"no_valid_packet_consumer")
  <<",\"packet_consumers_seen\":"<<capture_packet_consumers_<<",\"packet_consumers_without_relevant_draw\":"<<capture_consumers_without_draw_<<",\"packets_with_draws\":"<<capture_packets_with_draws_<<",\"promoted_packet_records\":"<<capture_records_<<",\"relevant_draws_seen\":"<<capture_relevant_draws_<<",\"not_ui_draws\":"<<capture_non_ui_draws_
  <<",\"adjusted_draw_candidates\":"<<capture_adjusted_draws_<<",\"unadjusted_draw_candidates\":"<<capture_unadjusted_draws_<<",\"promoted_adjusted_packets\":"<<capture_adjusted_packets_<<",\"promoted_unadjusted_packets\":"<<capture_unadjusted_packets_
  <<",\"draw_observations_captured\":"<<capture_draw_observations_captured_<<",\"draw_observations_dropped\":"<<capture_draw_drops_<<",\"candidate_capacity_rejections\":"<<capture_candidate_rejections_<<",\"candidate_evictions\":"<<capture_candidate_evictions_
  <<",\"capture_record_budget_limit\":"<<UI_CAPTURE_PACKET_RECORD_LIMIT<<",\"capture_records_emitted\":"<<capture_records_<<",\"capture_record_budget_dropped\":"<<capture_packet_record_drops_<<",\"render_local_record_limit\":"<<UI_CAPTURE_RENDER_LOCAL_RECORD_LIMIT<<",\"render_local_records_emitted\":"<<capture_render_local_records_<<",\"render_local_records_dropped\":"<<capture_render_local_drops_
  <<",\"identity_invalidations\":"<<capture_identity_invalidations_<<",\"log_write_failures\":"<<capture_log_failures_<<",\"budget_exhausted\":"<<(capture_packet_record_drops_||capture_render_local_drops_||capture_draw_drops_?"true":"false")<<",\"anchor_state_reset\":false}";
  if(session().write(out.str()))++records_;else ++capture_log_failures_;
 }catch(...){++capture_log_failures_;}
 capturing_=false;
}
void UiMargins::reset_diagnostics() noexcept {
 if(capturing_)finish_capture(capture_trace_frame_,device_id_,"device_reset");reset_capture_local();device_id_=capture_start_frame_=capture_trace_frame_=0;capture_completed_=false;capture_end_reason_="reset";
}
void UiMargins::reset_anchors(const char* why) noexcept {anchors_.begin_epoch(why);scene_family_=-1;scene_family_frame_=0;for(auto& s:scopes_)s.valid=false;}
void UiMargins::scene_context(bool race) noexcept {scene_family_=race?1:0;scene_family_frame_=frame_id_;auto epoch=anchors_.epoch();anchors_.scene_context(race);if(anchors_.epoch()!=epoch)for(auto& s:scopes_)s.valid=false;}
int UiMargins::find_observation(const MarginIdentity& key,uint64_t epoch) const noexcept {
 for(size_t i=0;i<observations_.size();++i){const auto& o=observations_[i];if(o.id&&o.epoch==epoch&&o.key.entity==key.entity&&o.key.packet==key.packet&&o.key.point==key.point&&o.key.storage==key.storage&&o.key.mode==key.mode)return static_cast<int>(i);}return -1;
}
uint64_t UiMargins::observation_priority(const MarginIdentity& key,uint64_t epoch) noexcept {
 // Deterministic sampling by validated packet identity prevents traversal
 // order alone from deciding which useful UI draws survive the bounded table.
 uint64_t h=1469598103934665603ull;const uint64_t words[]={static_cast<uint64_t>(key.entity),static_cast<uint64_t>(key.packet),static_cast<uint64_t>(key.point),static_cast<uint64_t>(key.storage),key.mode,epoch};
 for(uint64_t word:words)for(unsigned i=0;i<8;++i){h^=static_cast<uint8_t>(word>>(i*8));h*=1099511628211ull;}return h;
}
int UiMargins::promote_observation(Scope& scope) noexcept {
 const int existing=find_observation(scope.key,scope.anchor.epoch);
 if(existing>=0){auto& o=observations_[static_cast<size_t>(existing)];scope.packet_id=o.id;scope.first_frame=o.first;scope.previous_frame=o.last;scope.restored_frame=o.restored;scope.consume_count=++o.visits;scope.promotion_status="existing";scope.candidate_class_adjusted=o.adjusted;if(scope.anchor.current_rule<0)o.rule_mask|=1;else if(scope.anchor.current_rule>0)o.rule_mask|=2;o.last=frame_id_;o.logical=scope.engine_x;o.effective=scope.effective_x;o.rule=scope.anchor.current_rule;return existing;}
 bool adjusted=false;for(unsigned i=0;i<scope.draw_count;++i)adjusted|=scope.draws[i].margin_applied!=0;
 scope.candidate_class_adjusted=adjusted;const uint64_t priority=observation_priority(scope.key,scope.anchor.epoch);
 unsigned in_stratum=0;for(const auto& o:observations_)if(o.id&&o.adjusted==adjusted)++in_stratum;
 const unsigned limit=adjusted?UI_CAPTURE_ADJUSTED_CANDIDATE_QUOTA:UI_CAPTURE_UNADJUSTED_CANDIDATE_QUOTA;
 size_t index=observations_.size(),worst_index=observations_.size();uint64_t worst=0;
 for(size_t i=0;i<observations_.size();++i){const auto& o=observations_[i];if(!o.id){if(index==observations_.size())index=i;continue;}if(o.adjusted==adjusted&&(worst_index==observations_.size()||o.priority>worst||(o.priority==worst&&observation_identity_order(o.key,o.epoch)>observation_identity_order(observations_[worst_index].key,observations_[worst_index].epoch)))){worst=o.priority;worst_index=i;}}
 if(in_stratum>=limit){if(worst_index==observations_.size()){scope.packet_id=0;scope.first_frame=frame_id_;scope.promotion_status="candidate_capacity_exhausted_total";++capture_candidate_rejections_;return -1;}
  const auto& current_worst=observations_[worst_index];const auto candidate_order=observation_identity_order(scope.key,scope.anchor.epoch);const auto worst_order=observation_identity_order(current_worst.key,current_worst.epoch);
  if(priority>worst||(priority==worst&&!(candidate_order<worst_order))){scope.packet_id=0;scope.first_frame=frame_id_;scope.previous_frame=0;scope.restored_frame=0;scope.consume_count=1;scope.promotion_status=adjusted?"candidate_capacity_exhausted_adjusted":"candidate_capacity_exhausted_unadjusted";++capture_candidate_rejections_;return -1;}index=worst_index;auto& evicted=observations_[index];if(evicted.adjusted){if(capture_adjusted_packets_)--capture_adjusted_packets_;}else if(capture_unadjusted_packets_)--capture_unadjusted_packets_;++capture_candidate_evictions_;}
 if(index==observations_.size()){scope.packet_id=0;scope.first_frame=frame_id_;scope.consume_count=1;scope.promotion_status="candidate_capacity_exhausted_total";++capture_candidate_rejections_;return -1;}
 auto& o=observations_[index];o={};o.key=scope.key;o.id=++next_id_;o.epoch=scope.anchor.epoch;o.first=o.last=frame_id_;o.priority=priority;o.logical=scope.engine_x;o.effective=scope.effective_x;o.visits=1;o.rule=scope.anchor.current_rule;o.rule_mask=scope.anchor.current_rule<0?1:scope.anchor.current_rule>0?2:0;o.adjusted=adjusted;
 scope.packet_id=o.id;scope.first_frame=o.first;scope.previous_frame=0;scope.restored_frame=0;scope.consume_count=1;scope.promotion_status="promoted";
 if(adjusted)++capture_adjusted_packets_;else ++capture_unadjusted_packets_;return static_cast<int>(index);
}
bool UiMargins::enter_consume(uintptr_t entity) noexcept {
 MarginFP fp;
 if(!enabled_||GetCurrentThreadId()!=thread_)return false;
 if(scope_depth_==scopes_.size()){++scope_failures;disable("consumer_scope_overflow");return false;}
 auto& scope=scopes_[scope_depth_++];scope={};scope.capture_active=capturing_;if(capturing_){++capture_packet_consumers_;++packet_consumers_seen;}uintptr_t packet=0;MarginIdentity identity{};float engine[3]{};
 if(!safe_copy(&packet,reinterpret_cast<void*>(entity+0x4c),4)||!read_margin_identity(entity,packet+0x24,identity)||!safe_copy(engine,reinterpret_cast<void*>(identity.point),sizeof(engine))){anchors_.reject(entity);if(capturing_)++capture_identity_invalidations_;return true;}
 auto anchor=anchors_.resolve(identity,engine[0],engine[1],engine[2]);scope.key=identity;scope.anchor=anchor;scope.valid=true;
 scope.first_frame=frame_id_;scope.engine_x=engine[0];scope.engine_y=engine[1];scope.effective_x=engine[0]+half_*anchor.direction;
 int existing=find_observation(identity,anchor.epoch);if(existing>=0){const auto& o=observations_[static_cast<size_t>(existing)];scope.packet_id=o.id;scope.first_frame=o.first;scope.previous_frame=o.last;scope.restored_frame=o.restored;scope.consume_count=o.visits+1;scope.engine_rewrite=o.last&&engine[0]!=o.logical;scope.promotion_status="existing";}
 return true;
}
std::string UiMargins::packet_observation_json(const Scope& s) const {
 MarginFP fp;std::ostringstream out;
 out<<"{\"type\":\"ui_packet_lifetime\",\"event\":\"consume\",\"packet_id\":"<<s.packet_id<<",\"entity\":"<<s.key.entity<<",\"packet\":"<<s.key.packet<<",\"point_storage\":"<<s.key.point<<",\"content_storage\":"<<s.key.storage<<",\"packet_mode\":"<<s.key.mode
  <<",\"ui_epoch\":"<<s.anchor.epoch<<",\"capture_id\":"<<(device_id_?quote(trace_capture_id(device_id_,capture_start_frame_)):"null")<<",\"device_id\":"<<device_id_<<",\"capture_start_frame\":"<<capture_start_frame_<<",\"trace_frame\":"<<capture_trace_frame_<<",\"capture_frame_index\":"<<(capture_trace_frame_>=capture_start_frame_?capture_trace_frame_-capture_start_frame_:0)
  <<",\"projection_scene_family_last_classified\":"<<quote(scene_family_name(scene_family_))<<",\"projection_scene_family_frame\":"<<scene_family_frame_<<",\"half_extra\":";json_float(out,half_);
 out<<",\"current_screen_status\":\"not_proven\",\"frontend_screen\":null,\"screen_owner_status\":\"not_proven\",\"carousel_owner\":null,\"carousel_owner_status\":\"not_proven\",\"selection_state_read\":false,\"selected_index\":null"
  <<",\"anchor_id\":"<<s.anchor.id<<",\"anchor_direction\":"<<quote(s.anchor.direction<0?"left":s.anchor.direction>0?"right":"none")<<",\"anchor_source\":"<<quote(s.anchor.source)<<",\"anchor_new\":"<<(s.anchor.admitted?"true":"false")<<",\"anchor_retained\":"<<(s.anchor.retained?"true":"false")<<",\"anchor_grace_retained\":"<<(s.anchor.grace_retained?"true":"false")
  <<",\"group_id\":null,\"group_direction\":null,\"group_owner_status\":\"not_proven\",\"candidate_group_ids\":{\"entity\":"<<s.key.entity<<",\"packet\":"<<s.key.packet<<",\"content_storage\":"<<s.key.storage<<"}"
  <<",\"current_rule_match\":"<<s.anchor.current_rule<<",\"engine_x\":";json_float(out,s.engine_x);out<<",\"engine_y\":";json_float(out,s.engine_y);
 out<<",\"anchor_invalidated_reason\":"<<quote(s.anchor.invalidated)<<",\"owner_rva\":"<<UI_PACKET_RVA<<",\"first_frame\":"<<s.first_frame<<",\"frame\":"<<frame_id_<<",\"ui_frame\":"<<frame_id_<<",\"previous_frame\":"<<s.previous_frame<<",\"restored_frame\":"<<s.restored_frame<<",\"original_x\":";json_float(out,s.engine_x);out<<",\"effective_x\":";json_float(out,s.effective_x);
 out<<",\"observed_x\":";json_float(out,s.engine_x);out<<",\"engine_rewrite\":"<<(s.engine_rewrite?"true":"false")<<",\"persistent_packet_writes\":0,\"shifted\":false,\"consume_count\":"<<s.consume_count<<",\"promotion_status\":"<<quote(s.promotion_status)<<",\"candidate_class\":"<<quote(s.candidate_class_adjusted?"adjusted":"unadjusted")<<",\"candidate_sampling\":\"verified_ui_draws_deterministic_hash_priority_adjustment_strata\",\"draw_observations\":[";
 for(unsigned i=0;i<s.draw_count;++i){const auto& d=s.draws[i];if(i)out<<',';
  out<<"{\"draw_index\":"<<i<<",\"caller_va\":"<<d.caller_va<<",\"caller_rva\":"<<d.caller_rva<<",\"caller_in_game_image\":"<<(d.caller_in_game_image?"true":"false")
    <<",\"primitive_type\":"<<d.primitive<<",\"start_vertex\":"<<d.start_vertex<<",\"primitive_count\":"<<d.primitive_count<<",\"adjustment_gate_allowed\":"<<(d.adjustment_gate_allowed?"true":"false")<<",\"suppressed\":"<<(d.suppressed?"true":"false")<<",\"forwarded\":"<<(d.forwarded?"true":"false")<<",\"diagnostic_relevant\":"<<(d.diagnostic_relevant?"true":"false")
   <<",\"vertex_shader_token_known\":"<<(d.vertex_shader_token_known?"true":"false")<<",\"vertex_shader_token\":";if(d.vertex_shader_token_known)out<<d.vertex_shader_token;else out<<"null";
  out<<",\"fvf_value\":";if(d.vertex_shader_token_known&&d.vertex_shader_token==0x142)out<<d.vertex_shader_token;else out<<"null";
   out<<",\"fvf_status\":"<<quote(d.vertex_shader_token_known&&d.vertex_shader_token==0x142?"gate_confirmed_0x142":"not_identified")<<",\"margin_requested\":";json_float(out,d.margin_requested);out<<",\"margin_applied\":";json_float(out,d.margin_applied);
   out<<",\"margin_effective_request\":";json_float(out,d.margin_effective_request);out<<",\"carousel_status\":"<<quote(d.carousel_status)<<",\"carousel_id\":";if(d.carousel_id)out<<d.carousel_id;else out<<"null";out<<",\"carousel_override\":"<<(d.carousel_override?"true":"false");
   out<<",\"packet_point_known\":"<<(d.packet_point_known?"true":"false")<<",\"packet_x\":";if(d.packet_point_known)json_float(out,d.packet_x);else out<<"null";
   out<<",\"packet_y\":";if(d.packet_point_known)json_float(out,d.packet_y);else out<<"null";
  out<<",\"get_transform_attempted\":"<<(d.get_transform_attempted?"true":"false")<<",\"get_transform_hresult\":";if(d.get_transform_attempted)out<<d.get_transform_hresult;else out<<"null";
  out<<",\"world_known\":"<<(d.world_known?"true":"false")<<",\"native_world_x\":";if(d.world_known)json_float(out,d.native_world_x);else out<<"null";
  out<<",\"native_world_y\":";if(d.world_known)json_float(out,d.native_world_y);else out<<"null";
   out<<",\"effective_world_known\":"<<(d.effective_world_known?"true":"false")<<",\"effective_world_x\":";
   if(d.effective_world_known)json_float(out,d.effective_world_x);else out<<"null";
   out<<",\"effective_world_y\":";if(d.effective_world_known)json_float(out,d.effective_world_y);else out<<"null";
  out<<",\"world_status\":"<<quote(d.world_status)<<",\"temporary_set_attempted\":"<<(d.temporary_set_attempted?"true":"false")<<",\"temporary_set_hresult\":";if(d.temporary_set_attempted)out<<d.temporary_set_hresult;else out<<"null";
  out<<",\"requested_adjusted_world_x\":";if(d.temporary_set_attempted)json_float(out,d.requested_world_x);else out<<"null";
  out<<",\"requested_adjusted_world_y\":";if(d.temporary_set_attempted)json_float(out,d.requested_world_y);else out<<"null";
  out<<",\"draw_result_known\":"<<(d.draw_result_known?"true":"false")<<",\"draw_hresult\":";if(d.draw_result_known)out<<d.draw_hresult;else out<<"null";
  out<<",\"restore_attempted\":"<<(d.restore_attempted?"true":"false")<<",\"restore_requested_original_exact\":"<<(d.restore_requested_original_exact?"true":"false")<<",\"restore_succeeded\":"<<(d.restore_succeeded?"true":"false")<<",\"restore_hresult\":";if(d.restore_attempted)out<<d.restore_hresult;else out<<"null";
  out<<",\"restore_readback_performed\":false}";
 }
 out<<"],\"draw_observations_dropped\":"<<s.draw_dropped<<'}';return out.str();
}
void UiMargins::leave_consume() noexcept {
 if(!scope_depth_)return;auto& s=scopes_[scope_depth_-1];
 if(s.capture_active&&capturing_){
  if(s.draw_count){++capture_packets_with_draws_;promote_observation(s);if(s.packet_id){try{emit_capture_record(packet_observation_json(s),true,false);}catch(...){++capture_log_failures_;}}}
  else ++capture_consumers_without_draw_;
 }
 s={};--scope_depth_;if(!scope_depth_&&capturing_&&capture_close_pending_)finish_capture(capture_trace_frame_,device_id_,capture_close_reason_);
}
MarginDrawDecision UiMargins::draw_decision(bool verified_ui_draw) noexcept {
 MarginFP fp;MarginDrawDecision d;if(!enabled_||GetCurrentThreadId()!=thread_||!scope_depth_)return d;
 auto& s=scopes_[scope_depth_-1];if(!s.valid||s.anchor.epoch!=anchors_.epoch())return d;
 MarginIdentity current{};float point[3]{};
 if(!read_margin_identity(s.key.entity,s.key.packet+0x24,current)||current.packet!=s.key.packet||current.point!=s.key.point||current.storage!=s.key.storage||current.mode!=s.key.mode||!safe_copy(point,reinterpret_cast<void*>(current.point),sizeof(point))||point[2]!=0||!std::isfinite(point[0])||!std::isfinite(point[1])){anchors_.reject(s.key.entity);s.valid=false;return d;}
 d.key=s.key;d.anchor=s.anchor;d.native_x=point[0];d.native_y=point[1];d.standard_margin=half_*s.anchor.direction;d.margin=d.standard_margin;d.carousel_status=carousel_alignment_enabled_?"not_classified":"disabled";d.valid=true;
 if(carousel_alignment_enabled_){
  const bool frontend=scene_family_==0&&scene_family_frame_==frame_id_;
  auto semantic=anchors_.observe_carousel(s.key,point[0],point[1],frame_id_,frontend,verified_ui_draw,s.anchor.direction<0);
  d.carousel_id=semantic.id;d.carousel_status=semantic.status;
  if(semantic.proven){d.carousel_override=true;d.margin=0;++carousel_override_draws_;anchors_.discard_for_carousel(s.key);}
 }
 return d;
}
UiDrawObservation* UiMargins::begin_draw(uintptr_t caller_va,uint32_t caller_rva,bool caller_in_game_image,
 D3DPRIMITIVETYPE primitive,UINT start_vertex,UINT primitive_count,bool adjustment_gate_allowed,bool suppressed,bool forwarded,
 bool vertex_shader_token_known,uint32_t vertex_shader_token) noexcept {
 MarginFP fp;if(!capturing_||GetCurrentThreadId()!=thread_||!scope_depth_)return nullptr;auto& s=scopes_[scope_depth_-1];if(!s.capture_active)return nullptr;
 const bool relevant=caller_in_game_image&&caller_rva==UI_DRAW_RETURN_RVA&&primitive==D3DPT_TRIANGLELIST&&!suppressed&&forwarded&&vertex_shader_token_known&&vertex_shader_token==0x142;
 if(!relevant){++s.non_ui_draws;++capture_non_ui_draws_;++non_ui_draws_seen;return nullptr;}
 ++capture_relevant_draws_;++capture_draw_observation_attempts_;
 if(capture_draw_observation_attempts_>UI_CAPTURE_TOTAL_DRAW_OBSERVATION_LIMIT||s.draw_count>=s.draws.size()){
  ++s.draw_dropped;++draw_observations_dropped;++capture_draw_drops_;return nullptr;
 }
  auto decision=draw_decision();if(!decision.valid){++capture_identity_invalidations_;++s.draw_dropped;++draw_observations_dropped;++capture_draw_drops_;return nullptr;}
 auto& d=s.draws[s.draw_count++];d={};d.caller_va=caller_va;d.caller_rva=caller_rva;d.caller_in_game_image=caller_in_game_image;d.primitive=static_cast<uint32_t>(primitive);d.start_vertex=start_vertex;d.primitive_count=primitive_count;d.adjustment_gate_allowed=adjustment_gate_allowed;d.suppressed=suppressed;d.forwarded=forwarded;d.diagnostic_relevant=true;d.vertex_shader_token_known=vertex_shader_token_known;d.vertex_shader_token=vertex_shader_token;
 ++draw_observations_captured;++capture_draw_observations_captured_;return &d;
}
void UiMargins::failed_restore(const D3DMATRIX& original) noexcept {pending_world_=original;restore_pending_=true;++restore_failures;disable("native_ui_world_restore_failed");}
HRESULT UiMargins::repair_world(IDirect3DDevice8& native,Trace& trace,uintptr_t pc) noexcept {
 if(!restore_pending_)return S_OK;auto args=pack(D3DTS_WORLD,&pending_world_);HRESULT hr=native.SetTransform(D3DTS_WORLD,&pending_world_);++native_writes;trace.after(37,args,static_cast<uint32_t>(hr),pc,&args,128,false,true);if(SUCCEEDED(hr)){restore_pending_=false;++restore_exact;}return hr;
}
void UiMargins::observe_draw(const MarginDrawDecision& d,UiDrawObservation& draw) noexcept {
 MarginFP fp;if(!capturing_||!draw.diagnostic_relevant||!draw.world_known||!draw.effective_world_known||!scope_depth_)return;
 if(draw.margin_applied!=0)++capture_adjusted_draws_;else ++capture_unadjusted_draws_;
 try{
  std::ostringstream o;o<<"{\"type\":\"ui_render_local\",\"capture_id\":"<<(device_id_?quote(trace_capture_id(device_id_,capture_start_frame_)):"null")
   <<",\"device_id\":"<<device_id_<<",\"capture_start_frame\":"<<capture_start_frame_<<",\"trace_frame\":"<<capture_trace_frame_
   <<",\"capture_frame_index\":"<<(capture_trace_frame_>=capture_start_frame_?capture_trace_frame_-capture_start_frame_:0)
   <<",\"packet\":"<<d.key.packet<<",\"entity\":"<<d.key.entity<<",\"ui_epoch\":"<<d.anchor.epoch<<",\"anchor_id\":"<<d.anchor.id
   <<",\"anchor_direction\":"<<quote(d.anchor.direction<0?"left":d.anchor.direction>0?"right":"none")<<",\"caller_rva\":"<<draw.caller_rva
   <<",\"diagnostic_relevant\":true,\"draw_class\":"<<quote(draw.margin_applied!=0?"adjusted":"unadjusted")
   <<",\"carousel_status\":"<<quote(draw.carousel_status)<<",\"carousel_id\":";if(draw.carousel_id)o<<draw.carousel_id;else o<<"null";
  o<<",\"carousel_override\":"<<(draw.carousel_override?"true":"false")<<",\"margin_standard\":";json_float(o,d.standard_margin);
  o<<",\"margin_effective_request\":";json_float(o,d.margin);o<<",\"native_x\":";json_float(o,d.native_x);o<<",\"native_y\":";json_float(o,d.native_y);
  o<<",\"native_world_x\":";json_float(o,draw.native_world_x);o<<",\"native_world_y\":";json_float(o,draw.native_world_y);
  o<<",\"half_extra\":";json_float(o,half_);o<<",\"margin\":";json_float(o,draw.margin_applied);
  o<<",\"effective_render_x\":";json_float(o,draw.effective_world_x);o<<",\"effective_render_y\":";json_float(o,draw.effective_world_y);
  o<<",\"persistent_packet_writes\":0,\"override_path\":\"draw_local_native_world_copy\",\"draw_hresult\":";
  if(draw.draw_result_known)o<<draw.draw_hresult;else o<<"null";
  o<<",\"restore_attempted\":"<<(draw.restore_attempted?"true":"false")<<",\"restore_succeeded\":"<<(draw.restore_succeeded?"true":"false")<<",\"restore_hresult\":";
  if(draw.restore_attempted)o<<draw.restore_hresult;else o<<"null";
  o<<",\"restore_readback_performed\":false,\"ui_frame\":"<<frame_id_<<'}';emit_capture_record(o.str(),false,true);
 }catch(...){++capture_log_failures_;}
}
UiWorldScope::UiWorldScope(IDirect3DDevice8& native,Trace& trace,UiMargins& ui,uintptr_t pc,bool allowed,
 D3DPRIMITIVETYPE primitive,UINT start_vertex,UINT primitive_count,uint32_t caller_rva,bool caller_in_game_image,bool suppressed,bool forwarded,
 bool vertex_shader_token_known,uint32_t vertex_shader_token) noexcept
 :native_(native),trace_(trace),ui_(ui),pc_(pc){
  MarginFP fp;observation_=ui_.begin_draw(pc,caller_rva,caller_in_game_image,primitive,start_vertex,primitive_count,allowed,suppressed,forwarded,vertex_shader_token_known,vertex_shader_token);
  decision_=ui_.draw_decision(allowed);const bool apply=allowed&&decision_.valid&&decision_.margin!=0;
  if(observation_){observation_->margin_requested=decision_.valid?decision_.standard_margin:0;observation_->margin_effective_request=decision_.valid?decision_.margin:0;observation_->carousel_status=decision_.carousel_status;observation_->carousel_id=decision_.carousel_id;observation_->carousel_override=decision_.carousel_override;observation_->packet_point_known=decision_.valid;observation_->packet_x=decision_.native_x;observation_->packet_y=decision_.native_y;}
 if(!apply&&!observation_)return;
 HRESULT hr=native_.GetTransform(D3DTS_WORLD,&original_);auto get=pack(D3DTS_WORLD,&original_);if(apply)trace_.after(38,get,static_cast<uint32_t>(hr),pc_,&get,128,false,true);
 if(observation_){observation_->get_transform_attempted=true;observation_->get_transform_hresult=static_cast<uint32_t>(hr);}
 if(FAILED(hr)){if(apply)++ui_.world_read_failed;if(observation_)observation_->world_status="get_transform_failed";return;}
  if(observation_){observation_->world_known=true;observation_->effective_world_known=true;observation_->native_world_x=original_._41;observation_->native_world_y=original_._42;observation_->effective_world_x=original_._41;observation_->effective_world_y=original_._42;observation_->world_status="native";}
 if(!apply)return;
 const float* values=&original_.m[0][0];for(int i=0;i<16;++i)if(!std::isfinite(values[i])){++ui_.world_read_failed;if(observation_)observation_->world_status="nonfinite_world";return;}
 if(original_._14||original_._24||original_._34||original_._44!=1){if(observation_)observation_->world_status="projective_world";return;}
 effective_=original_;effective_._41+=decision_.margin;if(!std::isfinite(effective_._41)){if(observation_)observation_->world_status="nonfinite_adjusted_world";return;}
 if(observation_){observation_->temporary_set_attempted=true;observation_->requested_world_x=effective_._41;observation_->requested_world_y=effective_._42;}
 auto set=pack(D3DTS_WORLD,&effective_);hr=native_.SetTransform(D3DTS_WORLD,&effective_);++ui_.native_writes;trace_.after(37,set,static_cast<uint32_t>(hr),pc_,&set,128,false,true);
 if(observation_)observation_->temporary_set_hresult=static_cast<uint32_t>(hr);
  if(FAILED(hr)){++ui_.temporary_set_failed;if(observation_){observation_->effective_world_known=false;observation_->world_status="temporary_set_failed";}return;}
 changed_=true;++ui_.render_draws;if(observation_){observation_->effective_world_x=effective_._41;observation_->effective_world_y=effective_._42;observation_->margin_applied=decision_.margin;observation_->world_status="adjusted";}
}
UiWorldScope::~UiWorldScope() noexcept {
 MarginFP fp;bool failed_restore=false;
 if(changed_){auto args=pack(D3DTS_WORLD,&original_);HRESULT hr=native_.SetTransform(D3DTS_WORLD,&original_);++ui_.native_writes;trace_.after(37,args,static_cast<uint32_t>(hr),pc_,&args,128,false,true);
  if(observation_){observation_->restore_attempted=true;observation_->restore_requested_original_exact=true;observation_->restore_succeeded=SUCCEEDED(hr);observation_->restore_hresult=static_cast<uint32_t>(hr);}
   if(FAILED(hr))failed_restore=true;else ++ui_.restore_exact;
 }
 if(observation_)ui_.observe_draw(decision_,*observation_);
 if(failed_restore)ui_.failed_restore(original_);
}
void UiMargins::emit_group_candidates() noexcept {
 if(!capturing_)return;try{
  // Shared addresses are emitted only for draw-promoted packets and remain
  // candidate evidence; no group membership is asserted by this record.
  std::ostringstream out;out<<"{\"type\":\"ui_group_candidates\",\"capture_id\":"<<(device_id_?quote(trace_capture_id(device_id_,capture_start_frame_)):"null")<<",\"device_id\":"<<device_id_<<",\"capture_start_frame\":"<<capture_start_frame_<<",\"trace_frame\":"<<capture_trace_frame_<<",\"ui_frame\":"<<frame_id_<<",\"ui_epoch\":"<<anchors_.epoch()<<",\"group_owner_status\":\"not_proven\",\"observed_prefix_only\":true,\"candidates\":[";bool first=true;
  auto in_capture=[&](const Observation& o){return o.id&&o.epoch==anchors_.epoch();};
  for(int kind=0;kind<3;++kind)for(size_t i=0;i<observations_.size();++i){
   const auto& o=observations_[i];if(!in_capture(o))continue;
   auto value=[&](const Observation& v){return kind==0?v.key.entity:kind==1?v.key.packet:v.key.storage;};auto id=value(o);if(!id)continue;
   bool seen=false;for(size_t j=0;j<i;++j)if(in_capture(observations_[j])&&value(observations_[j])==id)seen=true;if(seen)continue;
   bool left=false,right=false;unsigned count=0;for(const auto& v:observations_)if(in_capture(v)&&value(v)==id){++count;left|=(v.rule_mask&1)!=0;right|=(v.rule_mask&2)!=0;}
   if(!first)out<<',';first=false;out<<"{\"kind\":"<<quote(kind==0?"entity":kind==1?"packet":"content_storage")<<",\"candidate_id\":"<<id<<",\"observed_member_count\":"<<count<<",\"strong_rule_conflict\":"<<(left&&right?"true":"false")<<",\"group_id\":null,\"group_direction\":null,\"member_packet_ids\":[";bool member_first=true;
   for(const auto& v:observations_)if(in_capture(v)&&value(v)==id){if(!member_first)out<<',';member_first=false;out<<v.id;}out<<"]}";
  }out<<"]}";if(session().write(out.str()))++records_;else ++capture_log_failures_;
 }catch(...){++capture_log_failures_;}
}
bool UiMargins::finish_frame() noexcept {bool okay=!restore_pending_;anchors_.next_frame();++frame_id_;return okay;}
void UiMargins::disable(const char* why) noexcept {if(capturing_){if(scope_depth_){capture_close_pending_=true;capture_close_reason_=why?why:"feature_disabled";}else finish_capture(capture_trace_frame_,device_id_,why?why:"feature_disabled");}enabled_=false;carousel_alignment_enabled_=false;half_=0;scene_family_=-1;scene_family_frame_=0;anchors_.begin_epoch(why);for(auto& s:scopes_)s.valid=false;if(active==this)active=nullptr;patch_.remove(memory);reason=why;}
UiMargins::~UiMargins(){for(auto& r:returns)if(r.owner==this)r.owner=nullptr;disable("device_release");}
std::string UiMargins::json() const {
 MarginFP fp;std::ostringstream o;
 o<<"{\"architecture\":\"render_local_world_v2\",\"persistent_packet_writes\":0,\"anchor_count\":"<<anchors_.size()
  <<",\"ui_epoch\":"<<anchors_.epoch()<<",\"anchor_admissions\":"<<anchors_.admissions<<",\"anchor_invalidations\":"<<anchors_.invalidations
  <<",\"retained_anchor_without_current_rule_match\":"<<anchors_.retained_anchor_without_current_rule_match<<",\"anchor_grace_frames\":"<<MARGIN_ANCHOR_GRACE_FRAMES
  <<",\"anchor_grace_retained\":"<<anchors_.anchor_grace_retained<<",\"group_grace_retained\":0,\"group_owner_status\":\"not_proven\",\"anchor_overflow\":"<<anchors_.overflow
  <<",\"carousel_alignment_requested\":"<<(carousel_alignment_requested_?"true":"false")<<",\"carousel_alignment_enabled\":"<<(carousel_alignment_enabled_?"true":"false")
  <<",\"carousel_classifier\":"<<quote(carousel_alignment_enabled_?"frontend_verified_draw_motion_lane_opt_in":"disabled")
  <<",\"carousel_promotions\":"<<anchors_.carousel_promotions<<",\"carousel_invalidations\":"<<anchors_.carousel_invalidations
  <<",\"carousel_capacity_evictions\":"<<anchors_.carousel_overflow<<",\"carousel_anchor_discards\":"<<anchors_.carousel_anchor_discards
  <<",\"carousel_override_draws\":"<<carousel_override_draws_
  <<",\"installed\":"<<(patch_.installed()?"true":"false")<<",\"enabled\":"<<(enabled_?"true":"false")<<",\"reason\":"<<quote(reason)
  <<",\"half_extra\":"<<half_<<",\"restore_boundary\":\"immediate_native_draw_return\",\"capture_active\":"<<(capturing_?"true":"false")
  <<",\"capture_id\":"<<(capturing_&&device_id_?quote(trace_capture_id(device_id_,capture_start_frame_)):"null")<<",\"capture_start_frame\":"<<capture_start_frame_
  <<",\"trace_frame\":"<<capture_trace_frame_<<",\"capture_frame_index\":"<<(capture_trace_frame_>=capture_start_frame_?capture_trace_frame_-capture_start_frame_:0)
  <<",\"capture_count\":"<<capture_count_<<",\"capture_record_budget_limit\":"<<UI_CAPTURE_PACKET_RECORD_LIMIT<<",\"capture_records_emitted\":"<<capture_records_
  <<",\"capture_records_dropped\":"<<capture_packet_record_drops_<<",\"capture_candidate_capacity\":"<<UI_CAPTURE_PACKET_CANDIDATE_LIMIT
  <<",\"capture_candidates_adjusted\":"<<capture_adjusted_packets_<<",\"capture_candidates_unadjusted\":"<<capture_unadjusted_packets_
  <<",\"capture_candidate_rejections\":"<<capture_candidate_rejections_<<",\"capture_candidate_evictions\":"<<capture_candidate_evictions_
  <<",\"capture_relevant_draws\":"<<capture_relevant_draws_<<",\"capture_non_ui_draws\":"<<capture_non_ui_draws_
  <<",\"capture_draw_observations_captured\":"<<capture_draw_observations_captured_<<",\"capture_draw_observations_dropped\":"<<capture_draw_drops_
  <<",\"bounded_lifetime_records\":"<<records_<<",\"bounded_lifetime_render_local_records\":"<<render_local_records_
  <<",\"draw_observations_captured\":"<<draw_observations_captured<<",\"draw_observations_dropped\":"<<draw_observations_dropped
  <<",\"max_draw_observations_per_packet\":"<<UI_PACKET_DRAW_OBSERVATION_LIMIT<<",\"render_draws\":"<<render_draws
  <<",\"native_writes\":"<<native_writes<<",\"restore_exact\":"<<restore_exact<<",\"restore_failures\":"<<restore_failures
  <<",\"restore_pending\":"<<(restore_pending_?"true":"false")<<",\"world_read_failed\":"<<world_read_failed
  <<",\"temporary_set_failed\":"<<temporary_set_failed<<",\"scope_failures\":"<<scope_failures<<'}';
 return o.str();
}
uintptr_t detail::ui_packet_entity_for_contract() noexcept {return contract_entity;}
uintptr_t detail::ui_packet_bridge_for_contract(uintptr_t address) noexcept {if(active)return 0;contract_probe=true;contract_entity=0;packet_return=address;return reinterpret_cast<uintptr_t>(&packet_bridge);}
uintptr_t detail::ui_bridge_for_contract(uintptr_t address) noexcept {if(active)return 0;sort_return=address;return reinterpret_cast<uintptr_t>(&sort_bridge);}
}
