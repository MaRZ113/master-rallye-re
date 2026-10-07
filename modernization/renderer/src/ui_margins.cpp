#include "ui_margins.hpp"
#include "margin_rules.hpp"
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <sstream>
#include <cfenv>
namespace gfx2 {
namespace {struct MarginFP {fenv_t saved;MarginFP(){fegetenv(&saved);}~MarginFP(){fesetenv(&saved);}};}
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
 invalidations+=size();entries_={};++epoch_;epoch_reason_=reason;context_=-1;
}
void MarginAnchors::scene_context(bool race) noexcept {
 int next=race?1:0;if(context_>=0&&context_!=next)begin_epoch("scene_family_changed");context_=next;
}
void MarginAnchors::reject(uintptr_t entity) noexcept {for(auto& a:entries_)if(a.id&&a.key.entity==entity){a={};++invalidations;}}
void MarginAnchors::next_frame() noexcept {
 // Grace covers short submission gaps, never packet/storage/epoch replacement.
 // Expire at the completion of the third absent frame, not during animation.
 for(auto& a:entries_)if(a.id&&frame_-a.last>MARGIN_ANCHOR_GRACE_FRAMES){a={};++invalidations;++grace_expired;}
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
bool MarginFrame::shift(float* xyz,float half,uintptr_t owner) noexcept {
 float point[3]{};if(!logical_point(xyz,owner,point))return false;
 return shift_direction(xyz,half,margin_direction(point[0],point[1],point[2]),owner);
}
bool MarginFrame::logical_point(float* xyz,uintptr_t owner,float (&point)[3],uint32_t mode,uintptr_t storage) const noexcept {
 if(!xyz||!safe_copy(point,xyz,sizeof(point)))return false;
 for(size_t i=0;i<count_;++i)if(edits_[i].x==xyz&&edits_[i].owner==owner&&edits_[i].mode==mode&&edits_[i].storage==storage&&point[0]==edits_[i].effective){point[0]=edits_[i].original;break;}
 return true;
}
bool MarginFrame::shift_direction(float* xyz,float half,int direction,uintptr_t owner,uint32_t mode,uintptr_t storage) noexcept {
 if(!std::isfinite(half)||half==0)return false;
 float point[3]{};if(!xyz||!safe_copy(point,xyz,sizeof(point))||point[2]!=0||!std::isfinite(point[0])||!std::isfinite(point[1]))return false;
 if(direction!=1&&direction!=-1)return false;
 for(size_t i=0;i<count_;++i)if(edits_[i].x==xyz){float seen[3]{};if(!safe_copy(seen,xyz,sizeof(seen)))return false;
  if(edits_[i].owner==owner&&edits_[i].mode==mode&&edits_[i].storage==storage&&seen[0]==edits_[i].effective){
   point[0]=edits_[i].original;
   if(seen[0]==point[0]+half*direction&&seen[1]==edits_[i].y&&seen[2]==edits_[i].z)return false;
  }
  edits_[i]=edits_[--count_];break; // Intervening engine rewrite owns a new logical value.
 }
 if(count_==edits_.size()){++overflow;return false;}
 float value=point[0]+half*direction;if(!std::isfinite(value))return false;
 auto& e=edits_[count_++];e={xyz,point[0],value,point[1],point[2],owner,mode,storage};float check=0;
 if(!safe_copy(xyz,&value,4)||!safe_copy(&check,xyz,4)||std::memcmp(&check,&value,4)){
  ++failures;safe_copy(xyz,&point[0],4);return false;
 }
 ++changed;return true;
}
bool MarginFrame::restore() noexcept {
 bool okay=true;for(size_t i=0;i<count_;++i){auto& e=edits_[i];float seen[3]{};
  if(e.owner&&!eligible_ui_packet(e.owner,reinterpret_cast<uintptr_t>(e.x)-0x30))continue; // Owner replacement invalidates the edit.
  uint32_t mode=0;if(e.mode&&(!safe_copy(&mode,reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(e.x)+0x14),4)||mode!=e.mode))continue;
  uintptr_t storage=0;if(e.storage&&(!safe_copy(&storage,reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(e.x)-0x4c),4)||storage!=e.storage))continue;
  if(!safe_copy(seen,e.x,sizeof(seen))){okay=false;continue;}
  // An intervening engine write owns its new coordinates. Never overwrite it.
  if(std::memcmp(seen,&e.effective,4)||std::memcmp(seen+1,&e.y,4)||std::memcmp(seen+2,&e.z,4))continue;
  if(!safe_copy(e.x,&e.original,4)||!safe_copy(seen,e.x,4)||std::memcmp(seen,&e.original,4))okay=false;
 }count_=0;if(!okay)++failures;return okay;
}
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
void __stdcall consume_packet(uintptr_t entity) noexcept {if(active)active->before_consume(entity);else if(contract_probe)contract_entity=entity;}
void __stdcall shift_packet(uintptr_t entity,uintptr_t coordinates) noexcept {if(active)active->before_sort(entity,coordinates);}
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
 push dword ptr [eax+8]
 call consume_packet
 fxrstor [esp]
 mov esp,ebp
 popad
 popfd
 sub esp,108h
 jmp dword ptr [packet_return]
}}

}
bool UiMargins::install(bool exact,bool requested) noexcept {
 if(!requested||!exact){reason=exact?"disabled":"unsupported_build";return false;}
 if(active||multiple){multiple=true;if(active)active->disable("multiple_devices");reason="multiple_devices";return false;}
 uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
 constexpr unsigned char expected[]={0x81,0xec,0x08,0x01,0,0,0x8b,0x84,0x24,0x0c,0x01,0,0,0x53,0x57,0x89,0x4c,0x24,0x14,0x8b,0x78,0x4c};unsigned char seen[sizeof(expected)]{};
 if(base!=0x400000||!IsProcessorFeaturePresent(PF_XMMI64_INSTRUCTIONS_AVAILABLE)||!safe_copy(seen,reinterpret_cast<void*>(base+UI_PACKET_RVA),sizeof(seen))||std::memcmp(seen,expected,sizeof(seen))){reason="ui_packet_consumer_signature_or_placement_mismatch";return false;}
 HMODULE pin=nullptr;if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&sort_bridge),&pin)){reason="module_pin_failed";return false;}
 contract_probe=false;packet_return=base+UI_PACKET_RVA+6;thread_=GetCurrentThreadId();active=this;
 enabled_=patch_.install(memory,reinterpret_cast<void*>(base+UI_PACKET_RVA),reinterpret_cast<uintptr_t>(&packet_bridge));
 reason=enabled_?"ui_packet_consumer_installed":"ui_jump_patch_failed";if(!enabled_){active=nullptr;patch_.remove(memory);}return enabled_;
}
void UiMargins::dimensions(UINT w,UINT h) noexcept {MarginFP fp;half_=0;if(w&&h&&double(w)/h>=1.&&double(w)/h<=4.)half_=static_cast<float>((480.*double(w)/h-640.)*.5);}
void UiMargins::capture_window(bool active,uint64_t frame) noexcept {frame_id_=frame;if(active&&!capturing_&&records_<256){observations_={};diagnostic_frames_=3;}capturing_=active;}
void UiMargins::reset_diagnostics() noexcept {diagnostic_frames_=0;observations_={};capturing_=false;}
void UiMargins::reset_anchors(const char* why) noexcept {bool okay=frame_.restore();anchors_.begin_epoch(why);if(!okay)disable("ui_epoch_restore_failed");}
void UiMargins::scene_context(bool race) noexcept {auto epoch=anchors_.epoch();anchors_.scene_context(race);if(anchors_.epoch()!=epoch&&!frame_.restore())disable("ui_epoch_restore_failed");}
void UiMargins::before_consume(uintptr_t entity) noexcept {
 uintptr_t packet=0;if(safe_copy(&packet,reinterpret_cast<void*>(entity+0x4c),4)&&packet)before_sort(entity,packet+0x24);
}
void UiMargins::before_sort(uintptr_t entity,uintptr_t coordinates) noexcept {
 if(!enabled_||GetCurrentThreadId()!=thread_)return;
 // Called by the final packet consumer; coordinates are derived from entity+4C.
 MarginIdentity identity{};if(!read_margin_identity(entity,coordinates,identity)){anchors_.reject(entity);return;}
 auto point=reinterpret_cast<float*>(identity.point);float before[3]{},engine[3]{},after[3]{};
 if(!safe_copy(before,point,sizeof(before))||!frame_.logical_point(point,entity,engine,identity.mode,identity.storage)){anchors_.reject(entity);return;}
 auto anchor=anchors_.resolve(identity,engine[0],engine[1],engine[2]);
 bool changed=frame_.shift_direction(point,half_,anchor.direction,entity,identity.mode,identity.storage);if(!safe_copy(after,point,sizeof(after)))return;
 if(!diagnostic_frames_)return;
 Observation* observation=nullptr;for(auto& o:observations_)if(o.id&&o.entity==entity&&o.point==identity.point&&o.packet==identity.packet&&o.storage==identity.storage){observation=&o;break;}
 if(!observation)for(auto& o:observations_)if(!o.id){observation=&o;o.entity=entity;o.point=identity.point;o.packet=identity.packet;o.storage=identity.storage;o.id=++next_id_;o.first=frame_id_;break;}
 if(!observation)return;auto& o=*observation;auto previous=o.last;bool rewrite=o.last&&before[0]!=o.logical&&before[0]!=o.effective;
 o.logical=engine[0];o.effective=after[0];o.last=frame_id_;o.rule=anchor.current_rule;++o.visits;
 if(records_<256){++records_;try{std::ostringstream out;out<<"{\"type\":\"ui_packet_lifetime\",\"event\":\"consume\",\"packet_id\":"<<o.id<<",\"entity\":"<<entity<<",\"packet\":"<<identity.packet<<",\"point_storage\":"<<identity.point<<",\"content_storage\":"<<identity.storage<<",\"packet_mode\":"<<identity.mode<<",\"ui_epoch\":"<<anchor.epoch<<",\"anchor_id\":"<<anchor.id<<",\"anchor_direction\":"<<quote(anchor.direction<0?"left":anchor.direction>0?"right":"none")<<",\"anchor_source\":"<<quote(anchor.source)<<",\"anchor_new\":"<<(anchor.admitted?"true":"false")<<",\"anchor_retained\":"<<(anchor.retained?"true":"false")<<",\"anchor_grace_retained\":"<<(anchor.grace_retained?"true":"false")<<",\"group_id\":null,\"group_direction\":null,\"group_owner_status\":\"not_proven\",\"candidate_group_ids\":{\"entity\":"<<entity<<",\"packet\":"<<identity.packet<<",\"content_storage\":"<<identity.storage<<"}"<<",\"current_rule_match\":"<<anchor.current_rule<<",\"engine_x\":"<<engine[0]<<",\"engine_y\":"<<engine[1]<<",\"anchor_invalidated_reason\":"<<quote(anchor.invalidated)<<",\"owner_rva\":"<<UI_PACKET_RVA<<",\"first_frame\":"<<o.first<<",\"frame\":"<<frame_id_<<",\"previous_frame\":"<<previous<<",\"restored_frame\":"<<o.restored<<",\"original_x\":"<<o.logical<<",\"effective_x\":"<<o.effective<<",\"observed_x\":"<<before[0]<<",\"engine_rewrite\":"<<(rewrite?"true":"false")<<",\"shifted\":"<<(changed?"true":"false")<<",\"consume_count\":"<<o.visits<<"}";session().write(out.str());}catch(...){}}

}
bool UiMargins::finish_frame() noexcept {bool okay=frame_.restore();
 if(diagnostic_frames_&&records_<256){++records_;try{
  // Candidate buckets use only fields already read by the verified consumer.
  // Observed sharing is evidence for investigation, never permission to inherit.
  std::ostringstream out;out<<"{\"type\":\"ui_group_candidates\",\"frame\":"<<frame_id_<<",\"ui_epoch\":"<<anchors_.epoch()<<",\"group_owner_status\":\"not_proven\",\"observed_prefix_only\":true,\"candidates\":[";bool first=true;
  for(int kind=0;kind<3;++kind)for(size_t i=0;i<observations_.size();++i){
   const auto& o=observations_[i];if(!o.id||o.last!=frame_id_)continue;
   auto value=[&](const Observation& v){return kind==0?v.entity:kind==1?v.packet:v.storage;};auto id=value(o);if(!id)continue;
   bool seen=false;for(size_t j=0;j<i;++j)if(observations_[j].id&&observations_[j].last==frame_id_&&value(observations_[j])==id)seen=true;if(seen)continue;
   bool left=false,right=false;unsigned count=0;for(const auto& v:observations_)if(v.id&&v.last==frame_id_&&value(v)==id){++count;left|=v.rule<0;right|=v.rule>0;}
   if(!first)out<<',';first=false;out<<"{\"kind\":"<<quote(kind==0?"entity":kind==1?"packet":"content_storage")<<",\"candidate_id\":"<<id<<",\"observed_member_count\":"<<count<<",\"strong_rule_conflict\":"<<(left&&right?"true":"false")<<",\"group_id\":null,\"group_direction\":null,\"member_packet_ids\":[";bool member_first=true;
   for(const auto& v:observations_)if(v.id&&v.last==frame_id_&&value(v)==id){if(!member_first)out<<',';member_first=false;out<<v.id;}out<<"]}";
  }out<<"]}";session().write(out.str());
 }catch(...){}}
 for(auto& o:observations_)if(o.id&&o.last==frame_id_){o.restored=frame_id_;if(records_<256){++records_;try{session().write("{\"type\":\"ui_packet_lifetime\",\"event\":\"restore\",\"packet_id\":"+std::to_string(o.id)+",\"frame\":"+std::to_string(frame_id_)+",\"success\":"+(okay?"true":"false")+"}");}catch(...){}}}anchors_.next_frame();if(diagnostic_frames_)--diagnostic_frames_;++frame_id_;if(!okay)disable("ui_coordinate_restore_failed");return okay;}
void UiMargins::disable(const char* why) noexcept {enabled_=false;half_=0;frame_.restore();anchors_.begin_epoch(why);if(active==this)active=nullptr;patch_.remove(memory);reason=why;}
UiMargins::~UiMargins(){disable("device_release");}
std::string UiMargins::json() const {MarginFP fp;std::ostringstream o;o<<"{\"anchor_count\":"<<anchors_.size()<<",\"ui_epoch\":"<<anchors_.epoch()<<",\"anchor_admissions\":"<<anchors_.admissions<<",\"anchor_invalidations\":"<<anchors_.invalidations<<",\"retained_anchor_without_current_rule_match\":"<<anchors_.retained_anchor_without_current_rule_match<<",\"anchor_grace_frames\":"<<MARGIN_ANCHOR_GRACE_FRAMES<<",\"anchor_grace_retained\":"<<anchors_.anchor_grace_retained<<",\"group_grace_retained\":0,\"grace_expired\":"<<anchors_.grace_expired<<",\"group_owner_status\":\"not_proven\",\"status\":\"EXPERIMENTAL_LEGACY_COMPATIBILITY\""<<",\"anchor_overflow\":"<<anchors_.overflow<<",\"installed\":"<<(patch_.installed()?"true":"false")<<",\"enabled\":"<<(enabled_?"true":"false")<<",\"reason\":"<<quote(reason)<<",\"half_extra\":"<<half_<<",\"restore_boundary\":\"post_consumer_present_or_reset\",\"bounded_lifetime_records\":"<<records_<<",\"diagnostic_frames_remaining\":"<<diagnostic_frames_<<",\"packet_shifts\":"<<frame_.changed<<",\"restore_failures\":"<<frame_.failures<<",\"overflow\":"<<frame_.overflow<<'}';return o.str();}
uintptr_t detail::ui_packet_entity_for_contract() noexcept {return contract_entity;}
uintptr_t detail::ui_packet_bridge_for_contract(uintptr_t address) noexcept {if(active)return 0;contract_probe=true;contract_entity=0;packet_return=address;return reinterpret_cast<uintptr_t>(&packet_bridge);}
uintptr_t detail::ui_bridge_for_contract(uintptr_t address) noexcept {if(active)return 0;sort_return=address;return reinterpret_cast<uintptr_t>(&sort_bridge);}
}
