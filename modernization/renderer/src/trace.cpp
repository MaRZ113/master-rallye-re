#include "trace.hpp"
#include "method_names.hpp"
#include "quality.hpp"
#include <sstream>
#include <iomanip>
#include <cmath>
#include <cfenv>
#include <cstdio>
namespace gfx2 {
namespace {
struct FloatEnvironment { fenv_t f;FloatEnvironment(){fegetenv(&f);}~FloatEnvironment(){fesetenv(&f);} };
struct FileHandle { HANDLE value;~FileHandle(){if(value!=INVALID_HANDLE_VALUE)CloseHandle(value);} };
template<class T> void scalar(std::ostream& o,const Known<T>& k){if(k.known)o<<k.value;else o<<"null";}
void matrix(std::ostream& o,const Known<D3DMATRIX>& k){
 if(!k.known){o<<"null";return;}o<<"{\"values\":[";const float* f=&k.value.m[0][0];
 for(int i=0;i<16;++i){if(i)o<<',';if(std::isfinite(f[i]))o<<std::setprecision(9)<<f[i];else o<<"null";}
 o<<"],\"bits\":[";for(int i=0;i<16;++i){uint32_t b;std::memcpy(&b,f+i,4);if(i)o<<',';o<<b;}o<<"]}";
}
void viewport(std::ostream& o,const Known<D3DVIEWPORT8>& k){
 if(!k.known){o<<"null";return;}const auto& v=k.value;o<<"["<<v.X<<','<<v.Y<<','<<v.Width<<','<<v.Height<<',';
 if(std::isfinite(v.MinZ))o<<std::setprecision(9)<<v.MinZ;else o<<"null";o<<',';
 if(std::isfinite(v.MaxZ))o<<std::setprecision(9)<<v.MaxZ;else o<<"null";o<<']';
}
void caller(std::ostream& o,uintptr_t pc){
 auto c=caller_info(pc);o<<"{\"address\":"<<pc<<",\"module\":"<<(c.known?quote(c.module):"null")<<",\"base\":";
 if(c.known)o<<c.base;else o<<"null";o<<",\"return_rva\":";if(c.known)o<<pc-c.base;else o<<"null";o<<"}";
}
void state(std::ostream& o,const Draw& d){
 const auto& s=d.state;o<<"{\"viewport\":";viewport(o,s.viewport);o<<",\"vertex_shader\":";scalar(o,s.vertex_shader);o<<",\"pixel_shader\":";scalar(o,s.pixel_shader);
 o<<",\"render_states\":{";for(int i=0;i<24;++i){if(i)o<<',';o<<'"'<<RS_KEYS[i]<<"\":";scalar(o,s.rs[i]);}o<<"},\"texture_stage_states\":[";
 for(int i=0;i<8;++i){if(i)o<<',';o<<'{';for(int j=0;j<32;++j){if(j)o<<',';o<<'"'<<j+1<<"\":";scalar(o,s.tss[i][j]);}o<<'}';}o<<"],\"matrices\":{";
 for(int i=0;i<5;++i){if(i)o<<',';o<<'"'<<MATRIX_KEYS[i]<<"\":";matrix(o,s.matrices[i]);}o<<"},\"textures\":[";
 for(int i=0;i<8;++i){if(i)o<<',';o<<"{\"pointer\":";scalar(o,s.textures[i]);o<<",\"last_creation_serial\":"<<d.texture_generation[i]<<'}';}o<<"],\"streams\":[";
 for(int i=0;i<16;++i){if(i)o<<',';if(s.streams[i].known)o<<"{\"pointer\":"<<s.streams[i].value.pointer<<",\"stride\":"<<s.streams[i].value.stride<<",\"last_creation_serial\":"<<d.stream_generation[i]<<'}';else o<<"null";}o<<"],\"indices\":";
 if(s.indices.known)o<<"{\"pointer\":"<<s.indices.value.pointer<<",\"base\":"<<s.indices.value.base<<",\"last_creation_serial\":"<<d.index_generation<<'}';else o<<"null";
 o<<",\"render_target\":";scalar(o,s.target);o<<",\"depth_target\":";scalar(o,s.depth);o<<'}';
}
}
Trace::Trace() noexcept {
 semantics_.reset(new(std::nothrow)VehicleSemantics);
 lock_ok_=InitializeCriticalSectionEx(&lock_,2000,0)!=FALSE;
 try {auto& s=session();enabled=lock_ok_&&s.enabled;device_=s.device_serial();classifier_known_=s.compatibility.vehicle.supported();camera_probe_profile_supported_=s.target&&s.compatibility.fov.supported();exe_base_=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));}catch(...){enabled=false;}
}
Trace::~Trace(){if(lock_ok_)DeleteCriticalSection(&lock_);}
Trace::Guard::Guard(Trace& t) noexcept :t_(t),held_(t.lock_ok_){if(held_)EnterCriticalSection(&t.lock_);}
Trace::Guard::~Guard(){if(held_)LeaveCriticalSection(&t_.lock_);}
DrawClassification Trace::before(uint32_t slot,const Args& a,uintptr_t pc) noexcept {
 DrawClassification classification{};
 FloatEnvironment fp;
 try {
  if(enabled&&(slot==15||slot==34)){bool down=(GetAsyncKeyState(VK_F10)&0x8000)!=0;DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
   if(pid==GetCurrentProcessId())control.poll(down);else control.key_down=down;}
  if(slot<97)++counts_[slot];
  if(slot==14)reset_before_.read(reinterpret_cast<const D3DPRESENT_PARAMETERS*>(a.a[0]));
  if(slot>=70&&slot<=73){pending_semantic_=UINT32_MAX;pending_semantic_source_=VehicleSemanticSource::None;}
  if(slot==71){uint32_t rva=pc>=exe_base_&&pc-exe_base_<=UINT32_MAX?static_cast<uint32_t>(pc-exe_base_):0;
   bool owner=classifier_known_&&rva==SHARED_WORLD_RETURN_RVA;classification.reasons=draw_reasons(shadow,classifier_known_,race_context_,owner);classification.fvf=shadow.bindings.vertex_shader.known?shadow.bindings.vertex_shader.value:0;classification.alpha_blended=shadow.rs[27].known&&shadow.rs[27].value!=0;
   if(owner&&race_context_&&a.a[0]==D3DPT_TRIANGLELIST&&(classification.reasons&RIGID_WORLD)){
    race_seen_this_frame_=true; // A cached perspective may remain active across Present.
    classification.signature=geometry_signature(shadow,resources,a,rva);
    if(classification.signature){classification.reasons|=KNOWN_GEOMETRY;classification.resource_family=geometry_resource_family(shadow,resources);classification.group=tracker_.observe(shadow.matrices[256].value,classification.signature,{classification.fvf,classification.reasons,static_cast<uint32_t>(a.a[4]),classification.resource_family});classification.epoch=tracker_.epoch();classification.transform=tracker_.predict(shadow.matrices[256].value,classification.signature,classification.resource_family);}
   }
   if(classification.transform.object==ObjectClass::Body&&classification.transform.constellation&&strong_vehicle_proof(classification.transform))++live_body_draws_;
   if(semantics_&&classification.signature&&std::strcmp(reflection_material_exclusion(classification),"eligible")==0){
    auto key=vehicle_signature_key(shadow,resources,a,rva);
    const auto* entry=semantics_->find(key,resources);
    bool live=std::strcmp(reflection_exclusion(classification),"eligible")==0;
    bool material=std::strcmp(reflection_material_exclusion(classification),"eligible")==0;
    if(live){classification.semantic_source=VehicleSemanticSource::Live;}
    else if(entry&&material)classification.semantic_source=VehicleSemanticSource::Learned;
    if(entry&&material)classification.semantic_id=entry->id;
    pending_semantic_=entry?UINT32_MAX:semantics_->observe(key,classification);
    pending_semantic_source_=classification.semantic_source;
   }
  }
  if(slot>=70&&slot<=73){primitives_+=a.a[slot==70?2:slot==71?4:slot==72?1:3];
   pending_draw_=UINT32_MAX;
   if(enabled&&control.active&&capture_&&!capture_->truncated){
    if(capture_->draw_count==MAX_DRAWS){capture_->truncated=true;++capture_->dropped;}
    else {pending_draw_=static_cast<uint32_t>(capture_->draw_count++);auto& d=capture_->draws[pending_draw_];d.state=shadow.snapshot();d.classification=classification;d.at_draw=classification.transform;d.reflection=ReflectionOutcome{};d.reflection.requested_tci=shadow.tss[1][11];d.reflection.effective_tci=effective_shadow.tss[1][11];
     for(int i=0;i<4;++i)d.effective.filtering[i]=effective_shadow.tss[0][i==3?21:16+i];d.effective.projection=effective_shadow.matrices[3];d.effective.world_x.known=false;if(effective_shadow.matrices[D3DTS_WORLD].known)d.effective.world_x.set(effective_shadow.matrices[D3DTS_WORLD].value._41);
     for(int i=0;i<8;++i)d.texture_generation[i]=d.state.textures[i].known?resources.generation(d.state.textures[i].value):0;
     for(int i=0;i<16;++i)d.stream_generation[i]=d.state.streams[i].known?resources.generation(d.state.streams[i].value.pointer):0;
     d.index_generation=d.state.indices.known?resources.generation(d.state.indices.value.pointer):0;
    }
   }
  }
 }catch(...){enabled=false;tracker_.reset();if(semantics_)semantics_->clear();classification={};}
 return classification;
}
void Trace::foliage_result(const FoliageEvidence& e) noexcept {
 try{if(e.attempted&&enabled&&control.active&&capture_&&pending_draw_!=UINT32_MAX&&pending_draw_<capture_->draw_count&&foliage_records_.size()<FOLIAGE_PROBE_LIMIT)foliage_records_[pending_draw_]=foliage_json(e);}catch(...){}
}
void Trace::reflection_result(const ReflectionOutcome& outcome,uint32_t triangles) noexcept {
 if(outcome.applied){learned_reflection_draws_+=pending_semantic_source_==VehicleSemanticSource::Learned;live_reflection_draws_+=pending_semantic_source_==VehicleSemanticSource::Live;}
 reflection_candidates_+=outcome.candidate;reflection_draws_+=outcome.applied;reflection_triangles_+=outcome.applied?triangles:0;reflection_writes_+=outcome.native_writes;
 if(enabled&&capture_&&pending_draw_!=UINT32_MAX&&pending_draw_<capture_->draw_count)capture_->draws[pending_draw_].reflection=outcome;
}
void Trace::resource(uint32_t slot,const Args& a,uint32_t result,uintptr_t pc){
 if(static_cast<int32_t>(result)<0||slot<20||slot>27)return;
 const uint32_t output[]={6,7,5,4,4,5,4,3};uintptr_t p=0;
 if(!safe_copy(&p,reinterpret_cast<const void*>(a.a[output[slot-20]]),4)||!p)return;
 if(resources.items.find(p)!=resources.items.end()||resources.items.size()>=8192)tracker_.reset();auto r=resources.add(p,slot,a,pc);if(semantics_)semantics_->prune(resources);if(!enabled)return;std::ostringstream o;o<<"{\"type\":\"resource_create\",\"device\":"<<device_<<",\"frame\":"<<frame_<<",\"method\":"<<quote(METHOD_NAMES[slot])<<",\"pointer\":"<<p<<",\"creation_caller\":";caller(o,pc);o<<",\"serial\":"<<r.serial<<",\"arguments\":[";
 for(int i=0;i<8;++i){if(i)o<<',';o<<a.a[i];}o<<"],\"pool\":";scalar(o,r.pool);o<<",\"survives_reset\":"<<(r.reset_survivor?"true":"false")<<",\"lifetime_observed\":false}";session().write(o.str());
}
void Trace::after(uint32_t slot,const Args& args,uint32_t result,uintptr_t pc,const Args* effective,uint32_t feature,bool suppressed,bool native_only) noexcept {
 const Args& native=effective?*effective:args;
 if(!native_only)shadow.update(slot,args,result);effective_shadow.update(slot,native,result);
 FloatEnvironment fp;
 try {
  // Classification/lifetime state is independent of capture and logger availability.
  resource(slot,args,result,pc);
  if(slot==71&&semantics_)semantics_->submitted(pending_semantic_,static_cast<int32_t>(result)>=0);
  if(slot==63&&args.a[0]==1&&args.a[1]==11&&static_cast<int32_t>(result)>=0&&reflection_restore_pending.known&&native.a[2]==reflection_restore_pending.value)reflection_restore_pending.known=false;
  if(slot==37&&!native_only&&args.a[0]==D3DTS_PROJECTION&&static_cast<int32_t>(result)>=0){
   bool race=classifier_known_&&pc==exe_base_+GAMEPLAY_PROJECTION_RETURN_RVA&&shadow.matrices[3].known&&symmetric_lh(shadow.matrices[3].value)&&std::abs(source_camera_angle(shadow.matrices[3].value)-90.)<=SOURCE_CAMERA_TOLERANCE_DEGREES;
   race_context_=race;if(race)race_seen_this_frame_=true;
  }
  if(slot==15){
   if(static_cast<int32_t>(result)>=0&&race_seen_this_frame_){tracker_.finish_frame();if(semantics_)semantics_->learn(tracker_,resources,frame_);race_history_=true;}
   else if(race_history_||race_seen_this_frame_){tracker_.reset();if(semantics_)semantics_->clear();race_history_=false;}
   if(waiting_relearn_&&tracker_.stats().constellations){++relearn_count_;waiting_relearn_=false;}
  }
  if(slot==14&&static_cast<int32_t>(result)>=0){reset_removed_=resources.successful_reset();tracker_.reset();if(semantics_)semantics_->clear();race_context_=race_seen_this_frame_=race_history_=false;++reset_count_;waiting_relearn_=true;reflection_restore_pending.known=false;}
  if(!enabled){if(slot==15){tracker_.next_frame();if(semantics_)semantics_->next_frame();live_body_draws_=learned_reflection_draws_=live_reflection_draws_=0;race_seen_this_frame_=false;camera_probe_diagnostic=CameraProbeFrameDiagnostic{};++frame_;counts_.fill(0);primitives_=0;reflection_candidates_=reflection_draws_=reflection_triangles_=reflection_writes_=0;}return;}
  if(control.active&&capture_){
   if(capture_->event_count==MAX_EVENTS){capture_->truncated=true;++capture_->dropped;}
   else if(!capture_->truncated){auto& e=capture_->events[capture_->event_count++];e=Event{};e.slot=slot;e.result=result;e.args=args;e.pc=pc;e.effective_args=native;e.feature=feature;e.suppressed=suppressed;e.native_only=native_only;e.culling_synchronized=culling.synchronized;
    if((slot==37||slot==38)&&safe_copy(e.effective_payload,(void*)native.a[1],64))e.effective_words=16;
    else if((slot==40||slot==41)&&safe_copy(e.effective_payload,(void*)native.a[0],24))e.effective_words=6;
    if(slot>=70&&slot<=73){e.draw=pending_draw_;if(e.draw!=UINT32_MAX){const auto& d=capture_->draws[e.draw];for(int j=0;j<4;++j){const auto& l=d.state.tss[0][j==3?20:15+j];const auto& n=d.effective.filtering[j];if(l.known&&n.known&&l.value!=n.value)e.feature|=1;}if(d.state.matrices[2].known&&d.effective.projection.known&&std::memcmp(&d.state.matrices[2].value,&d.effective.projection.value,sizeof(D3DMATRIX)))e.feature|=stock_ui_projection(d.state.matrices[2].value)?32u:2u;}}
    if((slot==37||slot==38)&&safe_copy(e.payload,(void*)args.a[1],64))e.payload_words=16;
    else if(slot==40&&safe_copy(e.payload,(void*)args.a[0],24))e.payload_words=6;
    else if(slot==42&&safe_copy(e.payload,(void*)args.a[0],sizeof(D3DMATERIAL8)))e.payload_words=sizeof(D3DMATERIAL8)/4;
    else if(slot==44&&safe_copy(e.payload,(void*)args.a[1],sizeof(D3DLIGHT8)))e.payload_words=sizeof(D3DLIGHT8)/4;
    else if(slot==14&&reset_before_.known){std::memcpy(e.payload,&reset_before_.value,52);e.payload_words=13;if(safe_copy(e.payload+13,(void*)args.a[0],52))e.payload_words=26;}
    else if(slot==15){if(args.a[0]&&safe_copy(e.payload,(void*)args.a[0],16))e.payload_words=4;if(args.a[1]&&safe_copy(e.payload+4,(void*)args.a[1],16))e.payload_words=8;}
   }else ++capture_->dropped;
  }
  if(slot==14){D3DPRESENT_PARAMETERS p{};bool valid=safe_copy(&p,(void*)args.a[0],sizeof(p));
   session().write("{\"type\":\"reset\",\"device\":"+std::to_string(device_)+",\"hresult\":"+std::to_string(result)+",\"frame\":"+std::to_string(frame_)+",\"metadata_removed\":"+std::to_string(static_cast<int32_t>(result)>=0?reset_removed_:0)+",\"metadata_retained\":"+std::to_string(resources.items.size())+",\"classifier_epoch\":"+std::to_string(tracker_.epoch())+",\"parameters_before\":"+(reset_before_.known?pp_json(reset_before_.value):"null")+",\"parameters_after\":"+(valid?pp_json(p):"null")+"}");
   if(control.active)finish(result,false,"reset");control.abort();control.boundary=false;camera_probe_diagnostic=CameraProbeFrameDiagnostic{};
  }
  if(slot==3&&(!last_cooperative_.known||last_cooperative_.value!=result)){last_cooperative_.set(result);session().write("{\"type\":\"cooperative_level\",\"device\":"+std::to_string(device_)+",\"frame\":"+std::to_string(frame_)+",\"hresult\":"+std::to_string(result)+"}");}
  if(slot==15){finish(result,control.boundary,"present");tracker_.next_frame();if(semantics_)semantics_->next_frame();live_body_draws_=learned_reflection_draws_=live_reflection_draws_=0;race_seen_this_frame_=false;camera_probe_diagnostic=CameraProbeFrameDiagnostic{};++frame_;counts_.fill(0);primitives_=0;reflection_candidates_=reflection_draws_=reflection_triangles_=reflection_writes_=0;control.finish_present();if(control.active)start_capture();}
 }catch(...){enabled=false;tracker_.reset();if(semantics_)semantics_->clear();control.abort();OutputDebugStringA("R-GFX3 trace disabled after instrumentation failure\n");}
}
void Trace::start_capture() noexcept {
 foliage_records_.clear();foliage_budget.frame=frame_;foliage_budget.draws=0;foliage_budget.bytes=0;
 if(!capture_)capture_.reset(new(std::nothrow)FrameBuffer);
 if(!capture_){control.abort();return;}capture_->initial_effective_viewport=effective_shadow.bindings.viewport;capture_->event_count=0;capture_->draw_count=0;capture_->truncated=false;capture_->dropped=0;
}
void Trace::finish(uint32_t result,bool complete,const char* reason) noexcept {
 try {
  auto stats=tracker_.stats();
  auto& s=session();std::ostringstream summary;summary<<"{\"type\":\"frame_summary\",\"device\":"<<device_<<",\"frame\":"<<frame_<<",\"complete_interval\":"<<(complete?"true":"false")<<",\"present_hresult\":"<<result<<",\"primitive_total\":"<<primitives_<<",\"classifier\":{\"dynamic_tracks\":"<<stats.dynamic<<",\"chassis_candidates\":"<<stats.chassis<<",\"vehicle_constellations\":"<<stats.constellations<<",\"vehicle_body_draws\":"<<stats.body_draws<<",\"vehicle_wheel_draws\":"<<stats.wheel_draws<<",\"ambiguities\":"<<stats.ambiguities<<",\"vehicle_structural_admissions\":"<<stats.structural_admissions<<",\"vehicle_dynamic_admissions\":"<<stats.dynamic_admissions<<",\"vehicle_retained_identities\":"<<stats.retained<<",\"vehicle_identity_demotions\":"<<stats.demotions<<",\"body_material_mutations\":"<<stats.mutations<<",\"reflection_candidate_draws\":"<<reflection_candidates_<<",\"reflection_modified_draws\":"<<reflection_draws_<<",\"reflection_modified_triangles\":"<<reflection_triangles_<<",\"reflection_native_writes\":"<<reflection_writes_<<",\"learned_vehicle_body_signatures\":"<<learned_signatures()<<",\"live_vehicle_body_draws\":"<<live_body_draws_<<",\"learned_signature_reflection_draws\":"<<learned_reflection_draws_<<",\"live_constellation_reflection_draws\":"<<live_reflection_draws_<<",\"vehicle_signature_promotions\":"<<(semantics_?semantics_->promotions:0)<<",\"vehicle_signature_invalidations\":"<<(semantics_?semantics_->invalidations:0)<<",\"unproven_semantic_observations\":"<<(semantics_?semantics_->rejections:0)<<",\"reset_count\":"<<reset_count_<<",\"relearn_count\":"<<relearn_count_<<",\"epoch\":"<<tracker_.epoch()<<",\"race_seen_this_frame\":"<<(race_seen_this_frame_?"true":"false")<<"},\"fov_culling\":{\"installed\":"<<(culling.installed?"true":"false")<<",\"synchronized\":"<<(culling.synchronized?"true":"false")<<",\"restored\":"<<(culling.restored?"true":"false")<<",\"width\":"<<culling.width<<",\"height\":"<<culling.height<<",\"source_angle\":"<<culling.source<<",\"vfov\":"<<culling.vfov<<",\"hfov\":"<<culling.hfov<<",\"synchronized_frames\":"<<culling.synchronized_frames<<",\"failures\":"<<culling.failures<<",\"reason\":"<<quote(culling.reason)<<"},\"quality\":"<<quality_metadata<<",\"ui_margins\":"<<ui_metadata<<",\"counts\":{";
  for(int i=0;i<97;++i){if(i)summary<<',';summary<<quote(METHOD_NAMES[i])<<':'<<counts_[i];}summary<<"},\"bypass_suspected\":"<<((counts_[15]&&(!counts_[34]||!counts_[35]))?"true":"false")<<",\"camera_probe\":"<<camera_probe_frame_summary_json(camera_probe_diagnostic)<<'}';
  if(s.summaries&&(frame_==1||frame_%60==0||control.active))s.write(summary.str());
  if(!control.active||!capture_)return;
  wchar_t name[100];swprintf_s(name,L"\\frame-%lu-d%llu-%08llu.jsonl",GetCurrentProcessId(),device_,frame_);
  auto final=s.directory+name,tmp=final+L".tmp";
  HANDLE f=CreateFileW(tmp.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(f==INVALID_HANDLE_VALUE)return;
  FileHandle file{f};
  uint64_t written=0;bool okay=true;
  auto line=[&](const std::string& record){std::string text=record+'\n';DWORD n=0;
   if(!okay)return;
   if(written+text.size()>64*1024*1024||!WriteFile(f,text.data(),static_cast<DWORD>(text.size()),&n,nullptr)||n!=text.size()){
    okay=false;LARGE_INTEGER at;at.QuadPart=written;SetFilePointerEx(f,at,nullptr,FILE_BEGIN);SetEndOfFile(f);return;
   }written+=n;};
  line("{\"type\":\"frame_begin\",\"schema_version\":1,\"proxy_version\":\"R-GFX5-8\",\"exe_sha256\":"+quote(s.exe_sha)+",\"exe_path\":"+quote(s.exe_path)+",\"proxy_sha256\":"+quote(s.proxy_sha)+",\"real_d3d8_path\":"+quote(s.real_path)+",\"build\":"+quote(s.target?"PRISTINE_RETAIL":"UNKNOWN_BUILD")+",\"vehicle_semantics_capability\":"+(classifier_known_?"true":"false")+",\"device\":"+std::to_string(device_)+",\"frame\":"+std::to_string(frame_)+",\"quality\":"+quality_metadata+",\"ui_margins\":"+ui_metadata+"}");
  if(semantics_)for(size_t i=0;i<semantics_->size();++i){const auto& e=semantics_->entry(i);std::ostringstream o;
   o<<"{\"type\":\"vehicle_semantic_signature\",\"semantic_signature_id\":"<<e.id<<",\"semantic_signature_state\":\"PROVEN_VEHICLE_BODY_ENV\",\"geometry_signature\":"<<e.key.hash<<",\"learned_frame\":"<<e.learned_frame<<",\"learned_epoch\":"<<e.epoch<<",\"origin_constellation_id\":"<<e.origin.constellation<<",\"origin_reason_mask\":"<<e.origin.vehicle_reasons<<",\"origin_grace_frames\":"<<e.origin.grace<<",\"origin_identity_source\":"<<quote(identity_source(e.origin.source))<<",\"origin_wheel_track_ids\":[";
   for(int j=0;j<4;++j){if(j)o<<',';o<<e.origin.wheels[j];}o<<"],\"resource_generations\":[";for(int j=0;j<4;++j){if(j)o<<',';o<<e.key.generations[j];}
   o<<"],\"canonical_key_words\":[";for(size_t j=0;j<e.key.words.size();++j){if(j)o<<',';o<<e.key.words[j];}o<<"]}";line(o.str());
  }
  Known<D3DVIEWPORT8> native_viewport=capture_->initial_effective_viewport;
  for(size_t i=0;i<capture_->event_count;++i){const auto& e=capture_->events[i];
   if(SUCCEEDED(static_cast<HRESULT>(e.result))){
    if((e.slot==40||e.slot==41)&&e.effective_words==6){D3DVIEWPORT8 v{};std::memcpy(&v,e.effective_payload,24);native_viewport.set(v);}
    else if(e.slot==14||e.slot==31||e.slot==52||e.slot==53||e.slot==54)native_viewport.known=false;
   }
   std::ostringstream o;
   o<<"{\"type\":"<<quote(e.draw==UINT32_MAX?(e.native_only?"native_override":"event"):"draw")<<",\"sequence\":"<<i<<",\"frame\":"<<frame_<<",\"method\":"<<quote(METHOD_NAMES[e.slot])<<",\"slot\":"<<e.slot<<",\"result\":"<<e.result<<",\"caller\":";caller(o,e.pc);o<<",\"arguments\":[";
   for(int j=0;j<8;++j){if(j)o<<',';o<<e.args.a[j];}o<<"],\"payload_bits\":[";
   for(uint32_t j=0;j<e.payload_words;++j){if(j)o<<',';o<<e.payload[j];}o<<']';
   o<<",\"native_only\":"<<(e.native_only?"true":"false")<<",\"feature_mask\":"<<(e.feature|(e.draw!=UINT32_MAX&&capture_->draws[e.draw].reflection.applied?8u:0u))<<",\"forwarded\":"<<(e.suppressed?"false":"true")<<",\"effective_arguments\":[";for(int j=0;j<8;++j){if(j)o<<',';o<<e.effective_args.a[j];}o<<"],\"effective_payload_bits\":[";for(uint32_t j=0;j<e.effective_words;++j){if(j)o<<',';o<<e.effective_payload[j];}o<<']';
   if((e.feature&32)&&e.slot==37&&e.effective_words==16){D3DMATRIX effective{};std::memcpy(&effective,e.effective_payload,64);
    double width=effective._11?2./effective._11:0.;o<<",\"widescreen_applied\":true,\"widescreen_source\":"<<quote(e.native_only?"validated_ui_projection_owner_cached":"validated_ui_projection_owner")<<",\"virtual_width\":"<<width<<",\"widescreen_extra\":"<<width-640.<<",\"center_offset\":"<<(width-640.)*.5;
   }
   if((e.feature&64)&&e.slot==37&&e.payload_words==16&&e.effective_words==16){D3DMATRIX a{},b{};std::memcpy(&a,e.payload,64);std::memcpy(&b,e.effective_payload,64);o<<",\"frontend_preview_aspect_correction\":true,\"source_angle\":"<<source_camera_angle(a)<<",\"effective_vfov\":"<<vertical_fov(b);}
   if(e.feature&2 && e.slot==37 && e.payload_words==16 && e.effective_words==16){D3DMATRIX original{},effective{};std::memcpy(&original,e.payload,64);std::memcpy(&effective,e.effective_payload,64);if(symmetric_lh(original)&&symmetric_lh(effective))o<<",\"projection_override\":{\"original_vfov\":"<<vertical_fov(original)<<",\"effective_vfov\":"<<vertical_fov(effective)<<",\"configured_vfov\":"<<s.visual_config.vfov<<",\"original_aspect\":"<<original._22/original._11<<",\"culling_synchronized\":"<<(e.culling_synchronized?"true":"false")<<'}';}
   if(e.draw!=UINT32_MAX){auto classification=capture_->draws[e.draw].classification;auto result=tracker_.result(classification.group);if(result&&classification.epoch==tracker_.epoch())classification.transform=*result;
    o<<",\"object_classification\":"<<quote(object_classification(classification))<<",\"classification_confidence\":"<<quote(object_classification(classification))<<",\"classification_evidence\":\"D3D_TEMPORAL_ONLY\",\"classification_reasons\":[";bool first_reason=true;
    const char* reasons[]={"vehicle_semantics_capability","race_projection","shared_world_owner","known_resource_generations","rigid_world","normal_fvf","stock_env_stage","opaque"};
    for(int j=0;j<8;++j)if(classification.reasons&(1u<<j)){if(!first_reason)o<<',';first_reason=false;o<<quote(reasons[j]);}
    o<<"],\"geometry_signature\":"<<classification.signature<<",\"geometry_resource_family\":"<<classification.resource_family<<",\"transform_track_id\":"<<classification.transform.track<<",\"transform_track_age\":"<<classification.transform.age<<",\"transform_dynamic\":"<<(classification.transform.dynamic?"true":"false")<<",\"transform_ambiguous\":"<<(classification.transform.ambiguous?"true":"false")<<",\"classifier_overflow\":"<<(tracker_.overflowed()?"true":"false")<<",\"reflection_feature\":"<<quote(capture_->draws[e.draw].reflection.applied?"ViewDependent2D":"Stock");
    const auto& d=capture_->draws[e.draw];const auto& refl=d.reflection;
    auto at_draw=classification;at_draw.transform=d.at_draw;auto decision=refl.applied?at_draw:classification;
    o<<",\"object_class\":"<<quote(object_classification(decision))<<",\"object_class_frame_end\":"<<quote(object_classification(classification))<<",\"material_class\":"<<quote(material_classification(decision))<<",\"constellation_id\":"<<decision.transform.constellation
     <<",\"classifier_confidence\":"<<quote(decision.transform.constellation?(decision.transform.vehicle_reasons&STRUCTURAL_CHASSIS?"STRONG_STRUCTURAL_FOUR_WHEEL":"STRONG_FOUR_WHEEL"):"UNPROVEN")<<",\"classifier_reasons\":[";
    const char* vehicle_reasons[]={"dynamic_chassis","body_draw_cluster","wheel_signature","four_wheel_match","bilateral_symmetry","axle_pairing","unambiguous_assignment","structural_chassis"};
    bool first=true;for(int j=0;j<8;++j)if(decision.transform.vehicle_reasons&(1u<<j)){if(!first)o<<',';first=false;o<<quote(vehicle_reasons[j]);}o<<"]";
    o<<",\"semantic_owner_return_rva\":"<<((d.classification.reasons&SHARED_OWNER)?SHARED_WORLD_RETURN_RVA:0);
    o<<",\"vehicle_semantic_source\":"<<quote(vehicle_semantic_source(d.classification.semantic_source))<<",\"semantic_signature_id\":"<<d.classification.semantic_id
     <<",\"semantic_signature_state\":"<<quote(d.classification.semantic_id?"PROVEN_VEHICLE_BODY_ENV":d.classification.semantic_source==VehicleSemanticSource::Live?"OBSERVED_ON_VEHICLE":"UNKNOWN_SIGNATURE")
     <<",\"object_constellation_id\":"<<d.at_draw.constellation;
    o<<",\"object_identity_source\":"<<quote(identity_source(decision.transform.source))<<",\"object_identity_source_at_draw\":"<<quote(identity_source(d.at_draw.source))
     <<",\"identity_reason_mask\":"<<decision.transform.identity_reasons<<",\"identity_grace_frames\":"<<decision.transform.grace
     <<",\"reflection_eligible\":"<<(std::strcmp(reflection_exclusion(at_draw),"eligible")==0?"true":"false")<<",\"reflection_modified\":"<<(refl.applied?"true":"false");
    if(decision.transform.object==ObjectClass::Body){o<<",\"associated_wheel_track_ids\":[";for(int j=0;j<4;++j){if(j)o<<',';o<<decision.transform.wheels[j];}o<<"],\"symmetry_error\":"<<decision.transform.symmetry_error;}
    o<<",\"object_class_at_draw\":"<<quote(object_classification(at_draw))<<",\"constellation_id_at_draw\":"<<d.at_draw.constellation<<",\"race_context\":"<<((classification.reasons&RACE_PROJECTION)?"true":"false")
     <<",\"requested_stage1_tci\":";scalar(o,refl.requested_tci);o<<",\"effective_stage1_tci_for_draw\":";scalar(o,refl.effective_tci);
    o<<",\"reflection_mode\":"<<quote(refl.mode)<<",\"reflection_candidate\":"<<(refl.candidate?"true":"false")<<",\"native_override_applied\":"<<(refl.applied?"true":"false")
     <<",\"native_restore_attempted\":"<<(refl.restore_attempted?"true":"false")<<",\"native_restore_success\":"<<(refl.restore_success?"true":"false")<<",\"reflection_reason\":"<<quote(refl.reason);
    auto probe=foliage_records_.find(e.draw);if(probe!=foliage_records_.end())o<<",\"ps2_foliage_probe\":"<<probe->second;
    o<<",\"draw_index\":"<<e.draw<<",\"primitive_type\":"<<e.args.a[0]<<",\"primitive_count\":"<<e.args.a[e.slot==70?2:e.slot==71?4:e.slot==72?1:3]<<",\"state\":";state(o,capture_->draws[e.draw]);const auto& eff=capture_->draws[e.draw].effective;o<<",\"state_semantics\":\"logical\",\"effective_state\":{\"inherits_logical\":true,\"stage0\":{";for(int j=0;j<4;++j){if(j)o<<',';o<<'"'<<(j==3?21:16+j)<<"\":";scalar(o,eff.filtering[j]);}o<<"},\"viewport\":";viewport(o,native_viewport);o<<",\"projection\":";matrix(o,eff.projection);o<<",\"world_translation_x\":";if(eff.world_x.known)o<<eff.world_x.value;else o<<"null";o<<",\"stage1\":{\"11\":";scalar(o,refl.effective_tci);o<<"}}";}o<<'}';line(o.str());
  }
  if(!foliage_records_.empty())line("{\"type\":\"foliage_probe_budget\",\"draws\":"+std::to_string(foliage_budget.draws)+",\"bytes\":"+std::to_string(foliage_budget.bytes)+",\"limit\":"+std::to_string(FOLIAGE_PROBE_LIMIT)+",\"disabled\":"+(foliage_budget.disabled?"true":"false")+"}");
  line(summary.str());line("{\"type\":\"frame_end\",\"frame\":"+std::to_string(frame_)+",\"complete\":"+(complete?"true":"false")+",\"reason\":"+quote(reason)+",\"truncated\":"+(capture_->truncated?"true":"false")+",\"dropped_records\":"+std::to_string(capture_->dropped)+",\"draw_records\":"+std::to_string(capture_->draw_count)+"}");
  if(!FlushFileBuffers(f))okay=false;CloseHandle(f);file.value=INVALID_HANDLE_VALUE;
  if(okay&&!MoveFileExW(tmp.c_str(),final.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))okay=false;
  s.write("{\"type\":\"capture_written\",\"path\":"+quote(utf8(okay?final:tmp))+",\"complete_file\":"+(okay?"true":"false")+"}");
 }catch(...){OutputDebugStringA("R-GFX3 capture output failed; forwarding unchanged\n");}
}
void Trace::shutdown(uint32_t refs) noexcept {
 if(!enabled)return;FloatEnvironment fp;try{auto g=guard();if(control.active)finish(0,false,"release");control.abort();session().write("{\"type\":\"device_release\",\"device\":"+std::to_string(device_)+",\"native_refcount\":"+std::to_string(refs)+"}");}catch(...){}
}
}
