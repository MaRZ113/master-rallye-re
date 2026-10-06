#include "vehicle_semantics.hpp"
namespace gfx2 {
bool VehicleSignatureKey::valid(const ResourceRegistry& resources) const noexcept {
 if(!hash||!generations[0]||!generations[1])return false;
 for(size_t i=0;i<4;++i)if(pointers[i]&&resources.generation(pointers[i])!=generations[i])return false;
 return true;
}
VehicleSignatureKey vehicle_signature_key(const Shadow& s,const ResourceRegistry& resources,const Args& args,uint32_t rva) noexcept {
 VehicleSignatureKey key;key.hash=geometry_signature(s,resources,args,rva);if(!key.hash)return key;
 key.pointers={s.bindings.streams[0].value.pointer,s.bindings.indices.value.pointer,s.bindings.textures[0].value,s.bindings.textures[1].value};
 for(size_t i=0;i<4;++i)key.generations[i]=resources.generation(key.pointers[i]);
 size_t n=0;auto add=[&](uint64_t v){key.words[n++]=v;};
 add(71);add(rva);add(key.generations[0]);add(key.generations[1]);add(s.bindings.streams[0].value.stride);add(s.bindings.indices.value.base);add(s.bindings.vertex_shader.value);
 for(auto a:args.a)add(a);
 for(int i=0;i<2;++i){add(key.generations[2+i]);for(int k:{1,2,3,4,5,6,11,24})add(s.tss[i][k].value);}
 bool transformed=s.tss[1][24].value!=D3DTTFF_DISABLE;add(transformed);
 for(int i=0;i<16;++i){uint32_t bits=0;if(transformed)std::memcpy(&bits,&s.matrices[17].value.m[i/4][i%4],4);add(bits);}
 for(int k:{14,15,27})add(s.rs[k].value);
 return key;
}
void VehicleSemantics::prune(const ResourceRegistry& resources) noexcept {
 for(size_t i=0;i<size_;)if(!entries_[i].key.valid(resources)){entries_[i]=entries_[--size_];++invalidations;}else ++i;
}
const VehicleSemanticEntry* VehicleSemantics::find(const VehicleSignatureKey& key,const ResourceRegistry& resources) noexcept {
 // Lookup validates dependencies even when a caller changes metadata directly.
 if(!key.valid(resources))return nullptr;
 for(size_t i=0;i<size_;++i)if(entries_[i].key==key&&entries_[i].key.valid(resources))return &entries_[i];return nullptr;
}
const VehicleSemanticEntry* VehicleSemantics::by_id(uint64_t id) const noexcept {
 for(size_t i=0;i<size_;++i)if(entries_[i].id==id)return &entries_[i];return nullptr;
}
uint32_t VehicleSemantics::observe(const VehicleSignatureKey& key,const DrawClassification& draw) noexcept {
 if(!key.hash||draw.group==UINT32_MAX||std::strcmp(reflection_material_exclusion(draw),"eligible"))return UINT32_MAX;
 for(size_t i=0;i<pending_size_;++i)if(pending_[i].group==draw.group&&pending_[i].epoch==draw.epoch&&pending_[i].key==key)return static_cast<uint32_t>(i);
 if(pending_size_==MAX_SEMANTIC_PENDING)return UINT32_MAX;
 auto i=static_cast<uint32_t>(pending_size_++);pending_[i]={key,draw.group,draw.epoch,false};return i;
}
void VehicleSemantics::submitted(uint32_t i,bool success) noexcept {if(i<pending_size_)pending_[i].successful|=success;}
void VehicleSemantics::learn(const TransformTracker& tracker,const ResourceRegistry& resources,uint64_t frame) noexcept {
 prune(resources);
 for(size_t i=0;i<pending_size_;++i){const auto& p=pending_[i];
  if(!p.successful||p.epoch!=tracker.epoch()||!p.key.valid(resources)||find(p.key,resources))continue;
  const auto* c=tracker.result(p.group);
  bool proven=c&&c->object==ObjectClass::Body&&c->constellation&&strong_vehicle_proof(*c)&&!c->grace;
  if(proven)for(size_t a=0;a<4;++a){if(!c->wheels[a])proven=false;for(size_t b=0;b<a;++b)if(c->wheels[a]==c->wheels[b])proven=false;}
  if(!proven){++rejections;continue;}
  if(size_==MAX_VEHICLE_SIGNATURES)continue; // Bounded, no eviction/churn of existing proof.
  entries_[size_++]={p.key,++next_id_,frame,tracker.epoch(),*c};++promotions;
 }
}
void VehicleSemantics::clear() noexcept {invalidations+=size_;size_=pending_size_=0;}
const char* vehicle_semantic_source(VehicleSemanticSource source) noexcept {
 switch(source){case VehicleSemanticSource::Live:return "live_constellation";case VehicleSemanticSource::Learned:return "learned_signature";default:return "none";}
}
}
