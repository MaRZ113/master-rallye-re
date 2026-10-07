#include "vehicle_classifier.hpp"
#include <algorithm>
#include <cmath>
#include <cfenv>
namespace gfx2 {
namespace {
struct FP {fenv_t f;FP(){fegetenv(&f);}~FP(){fesetenv(&f);}};
bool rigid(const D3DMATRIX& w){
 const float* f=&w.m[0][0];for(int i=0;i<16;++i)if(!std::isfinite(f[i]))return false;
 if(w._14!=0||w._24!=0||w._34!=0||w._44!=1)return false;
 for(int a=0;a<3;++a)for(int b=a;b<3;++b){double dot=0;for(int j=0;j<3;++j)dot+=static_cast<double>(w.m[a][j])*w.m[b][j];if(std::abs(dot-(a==b?1.:0.))>.02)return false;}
 return true;
}
double distance(const D3DMATRIX& a,const D3DMATRIX& b){double d=0;for(int i=0;i<3;++i){double v=static_cast<double>(a.m[3][i])-b.m[3][i];d+=v*v;}return d;}
double orientation(const D3DMATRIX& a,const D3DMATRIX& b){double d=0;for(int i=0;i<3;++i)for(int j=0;j<3;++j){double v=static_cast<double>(a.m[i][j])-b.m[i][j];d+=v*v;}return d;}
bool same(const D3DMATRIX& a,const D3DMATRIX& b){return distance(a,b)<1.e-6&&orientation(a,b)<1.e-8;}
bool overlap(const TransformGroup& a,const TransformGroup& b){size_t i=0,j=0;while(i<a.size&&j<b.size){if(a.signatures[i]==b.signatures[j])return true;if(a.signatures[i]<b.signatures[j])++i;else ++j;}return false;}
bool family(const TransformGroup& g,uint64_t f){return f&&std::find(g.families.begin(),g.families.begin()+g.family_size,f)!=g.families.begin()+g.family_size;}
bool anchors(const TransformGroup& a,const TransformGroup& b){for(size_t i=0;i<a.family_size;++i)if(family(b,a.families[i]))return true;return (!a.family_size||!b.family_size)&&overlap(a,b);}
LocalWheel local_wheel(const D3DMATRIX& body,const D3DMATRIX& wheel){
 std::array<float,3> p{};for(int a=0;a<3;++a){double v=0;for(int k=0;k<3;++k)v+=(double(wheel.m[3][k])-body.m[3][k])*body.m[a][k];p[a]=static_cast<float>(v);}return {p[0],p[1],p[2]};
}
bool nearby(LocalWheel p){return std::abs(p.x)>=.35&&std::abs(p.x)<=2.5&&std::abs(p.z)>=.5&&std::abs(p.z)<=4.&&p.y>=-2.&&p.y<=1.5;}
bool wheel_group(const TransformGroup& g){return !g.saturated&&g.result.track&&!g.result.ambiguous&&g.wheel_draws>=2&&g.wheel_draws==g.draws;}
double position_error(LocalWheel p,const std::array<float,3>& a){return (p.x-a[0])*(p.x-a[0])+(p.y-a[1])*(p.y-a[1])+(p.z-a[2])*(p.z-a[2]);}
void semantic_clear(Classification& c){c.object=ObjectClass::Unknown;c.constellation=0;c.vehicle_reasons=0;c.wheels={};c.symmetry_error=0;c.source=IdentitySource::None;c.identity_reasons=0;c.grace=0;c.material_only=false;}
}
uint32_t TransformTracker::observe(const D3DMATRIX& world,uint64_t signature,GroupDraw draw) noexcept {
 FP fp;if(overflow_||!signature||!rigid(world))return UINT32_MAX;
 size_t i=0;for(;i<current_size_;++i)if(same(current_[i].world,world))break;
 if(i==current_size_){if(i==MAX_TRANSFORM_GROUPS){overflow_=true;return UINT32_MAX;}current_[i]=TransformGroup{};current_[i].world=world;++current_size_;}
 auto& g=current_[i];
 ++g.draws;g.triangles+=draw.triangles;
 if(draw.fvf==0x142||draw.fvf==0x152||draw.fvf==0x242||draw.fvf==0x252)++g.body_draws;
 if(draw.fvf==0x142||draw.fvf==0x242)++g.body_base_draws;
 if(draw.fvf==0x102||draw.fvf==0x142||draw.fvf==0x152||draw.fvf==0x242||draw.fvf==0x252)++g.local_draws;
 if(draw.fvf==0x152&&(draw.reasons&(ENV_STAGE|CL_OPAQUE))==(ENV_STAGE|CL_OPAQUE))++g.body_env_draws;
 if(draw.fvf==0x112&&(draw.reasons&(ENV_STAGE|CL_OPAQUE))==(ENV_STAGE|CL_OPAQUE))++g.wheel_draws;
 if(draw.resource_family&&!family(g,draw.resource_family)){
  if(g.family_size==MAX_RESOURCE_FAMILIES){g.saturated=true;return UINT32_MAX;}g.families[g.family_size++]=draw.resource_family;
 }
 for(size_t j=0;j<g.size;++j)if(g.signatures[j]==signature)return static_cast<uint32_t>(i);
 if(g.size==MAX_GROUP_SIGNATURES){g.saturated=true;return UINT32_MAX;}g.signatures[g.size++]=signature;return static_cast<uint32_t>(i);
}
void TransformTracker::reset() noexcept {current_size_=previous_size_=0;overflow_=false;events_={};++epoch_;} // Monotonic IDs never reused.
void TransformTracker::finish_frame() noexcept {
 FP fp;
 events_={};
 if(overflow_){previous_size_=0;for(size_t i=0;i<current_size_;++i)current_[i].result={};return;}
 for(size_t i=0;i<current_size_;++i)std::sort(current_[i].signatures.begin(),current_[i].signatures.begin()+current_[i].size);
 std::array<int,MAX_TRANSFORM_GROUPS> best{},reverse{};best.fill(-1);reverse.fill(-1);
 std::array<double,MAX_TRANSFORM_GROUPS> cost{},back{};cost.fill(1.e100);back.fill(1.e100);
 std::array<bool,MAX_TRANSFORM_GROUPS> ambiguous{},reverse_ambiguous{};
 for(size_t i=0;i<current_size_;++i)for(size_t j=0;j<previous_size_;++j){
  if(current_[i].saturated||previous_[j].saturated)continue;double d=distance(current_[i].world,previous_[j].world),o=orientation(current_[i].world,previous_[j].world);
  if(d>100.||o>2.||!anchors(current_[i],previous_[j]))continue;double score=d+o;
  if(score+1.e-6<cost[i]){cost[i]=score;best[i]=static_cast<int>(j);ambiguous[i]=false;}else if(std::abs(score-cost[i])<=1.e-6)ambiguous[i]=true;
  if(score+1.e-6<back[j]){back[j]=score;reverse[j]=static_cast<int>(i);reverse_ambiguous[j]=false;}else if(std::abs(score-back[j])<=1.e-6)reverse_ambiguous[j]=true;
 }
 // Sort only new-ID assignment, not draws: equivalent draw permutations receive the same track IDs.
 std::array<size_t,MAX_TRANSFORM_GROUPS> order{};for(size_t i=0;i<current_size_;++i)order[i]=i;
 std::array<int,MAX_TRANSFORM_GROUPS> matched{};matched.fill(-1);
 std::sort(order.begin(),order.begin()+current_size_,[&](size_t a,size_t b){const float* x=&current_[a].world.m[0][0];const float* y=&current_[b].world.m[0][0];for(int i=0;i<16;++i)if(x[i]!=y[i])return x[i]<y[i];return false;});
 for(size_t n=0;n<current_size_;++n){size_t i=order[n];auto& g=current_[i];int j=best[i];bool match=j>=0&&!ambiguous[i]&&!reverse_ambiguous[j]&&reverse[j]==static_cast<int>(i);
  if(g.saturated){g.result={};g.motion=0;continue;}
  if(match){matched[i]=j;const auto& old=previous_[j];g.result=old.result;g.result.ambiguous=false;++g.result.age;g.motion=old.motion;
   g.structure_frames=old.structure_frames;g.structural_positions=old.structural_positions;
   if(distance(g.world,old.world)>.0025||orientation(g.world,old.world)>.0001)++g.motion;
   g.result.dynamic=g.result.age>=4&&g.motion>=2;
  }else {g.result={++next_id_,1,false,j>=0};g.motion=0;}
 }
 classify_constellations(current_.data(),current_size_);
 // Retention proposes associations simultaneously; a shared wheel never gets a traversal-order winner.
 std::array<std::array<int,4>,MAX_TRANSFORM_GROUPS> retained_wheels{};
 std::array<bool,MAX_TRANSFORM_GROUPS> retained{};std::array<unsigned,MAX_TRANSFORM_GROUPS> uses{};
 for(size_t i=0;i<current_size_;++i){auto& g=current_[i];int j=matched[i];auto& slots=retained_wheels[i];slots.fill(-1);
  if(j<0||g.saturated||g.result.ambiguous)continue;const auto& old=previous_[j].result;
  if(old.object!=ObjectClass::Body||!strong_vehicle_proof(old))continue;
  // Hard ambiguous geometry or incompatible associations invalidate immediately, without grace.
  if(g.result.object!=ObjectClass::Body&&g.result.vehicle_reasons)continue;
  unsigned found=0,nearby_count=0;bool bad=false;
  for(size_t w=0;w<current_size_;++w)if(wheel_group(current_[w])){
   auto p=local_wheel(g.world,current_[w].world);if(!nearby(p))continue;++nearby_count;int slot=-1;
   for(int k=0;k<4;++k)if(position_error(p,previous_[j].wheel_positions[k])<=.1225){
    bool support=current_[w].result.track==old.wheels[k]||family(current_[w],previous_[j].wheel_families[k])||
     std::binary_search(current_[w].signatures.begin(),current_[w].signatures.begin()+current_[w].size,previous_[j].wheel_signatures[k]);
    if(support){if(slot!=-1){bad=true;break;}slot=k;}
   }
   if(slot<0||slots[slot]!=-1){bad=true;continue;}slots[slot]=static_cast<int>(w);++found;
  }
  if(bad||nearby_count>4||found<3||found!=nearby_count||(found==3&&old.grace>=IDENTITY_GRACE_FRAMES))continue;
  // The current chassis must still contain observed body geometry; material set equality is irrelevant.
  if(!g.body_draws)continue;
  retained[i]=true;for(int w:slots)if(w>=0)++uses[w];
 }
 // Include fresh admissions in the same conflict pass, excluding their own retained proposal.
 for(size_t i=0;i<current_size_;++i)if(!retained[i]&&current_[i].result.object==ObjectClass::Body)
  for(auto id:current_[i].result.wheels)for(size_t w=0;w<current_size_;++w)if(current_[w].result.track==id)++uses[w];
 std::array<bool,MAX_TRANSFORM_GROUPS> consumed{};
 for(size_t n=0;n<current_size_;++n){size_t i=order[n];auto& g=current_[i];int j=matched[i];
  const Classification* old=j>=0?&previous_[j].result:nullptr;bool conflict=false;
  if(retained[i]){for(int w:retained_wheels[i])if(w>=0&&uses[w]!=1)conflict=true;}
  else if(g.result.object==ObjectClass::Body){for(auto id:g.result.wheels)for(size_t w=0;w<current_size_;++w)if(current_[w].result.track==id&&uses[w]!=1)conflict=true;}
  if(retained[i]&&!conflict){
   auto track=g.result.track;auto age=g.result.age;auto dynamic=g.result.dynamic;g.result=*old;
   g.result.track=track;g.result.age=age;g.result.dynamic=dynamic;g.result.source=IdentitySource::Retained;
   g.result.identity_reasons=SAME_CHASSIS_TRACK|SAME_WHEEL_CONSTELLATION;g.wheel_positions=previous_[j].wheel_positions;g.wheel_families=previous_[j].wheel_families;g.wheel_signatures=previous_[j].wheel_signatures;unsigned found=0;
   for(int w:retained_wheels[i])found+=w>=0;
   g.result.grace=found==4?0:old->grace+1;if(found<4)g.result.identity_reasons|=MISSING_WHEEL_GRACE;
   const auto& prev=previous_[j];if(g.size!=prev.size||!std::equal(g.signatures.begin(),g.signatures.begin()+g.size,prev.signatures.begin())){g.result.identity_reasons|=BODY_MATERIAL_MUTATION;++events_.mutations;}
   // Keep admission wheel IDs through short occlusion; refresh observed slots after a full proof.
   if(found==4)for(int k=0;k<4;++k)g.result.wheels[k]=current_[retained_wheels[i][k]].result.track;
   ++events_.retained;consumed[j]=true;
  }else if(g.result.object==ObjectClass::Body&&!conflict){
   g.result.constellation=++next_vehicle_id_;
   if(g.result.source==IdentitySource::Dynamic)++events_.dynamic_admissions;else ++events_.structural_admissions;
  }else {if(g.result.object==ObjectClass::Body)semantic_clear(g.result);}
 }
 for(size_t j=0;j<previous_size_;++j)if(previous_[j].result.object==ObjectClass::Body&&!consumed[j])++events_.demotions;
 // Clear provisional wheel labels and publish only globally conflict-free owners.
 for(size_t w=0;w<current_size_;++w)if(current_[w].result.object==ObjectClass::Wheel)semantic_clear(current_[w].result);
 for(size_t i=0;i<current_size_;++i)if(current_[i].result.object==ObjectClass::Body){const auto& b=current_[i].result;
  for(size_t w=0;w<current_size_;++w)for(auto id:b.wheels)if(current_[w].result.track==id){
   auto& c=current_[w].result;c.object=ObjectClass::Wheel;c.constellation=b.constellation;c.vehicle_reasons=b.vehicle_reasons;c.source=b.source;c.identity_reasons=b.identity_reasons;c.grace=b.grace;
  }
 }
 previous_size_=current_size_;for(size_t i=0;i<current_size_;++i)previous_[i]=current_[i];
 // Current results remain available until the next observation starts a new frame.
}
const Classification* TransformTracker::result(uint32_t group) const noexcept {return !overflow_&&group<current_size_?&current_[group].result:nullptr;}
Classification TransformTracker::predict(const D3DMATRIX& w,uint64_t signature,uint64_t resource_family) const noexcept {
 FP fp;Classification out{};if(overflow_||!signature||!rigid(w))return out;
 const TransformGroup* observed=nullptr;for(size_t j=0;j<current_size_;++j)if(same(w,current_[j].world)){observed=&current_[j];break;}
 double best=1.e100;int index=-1;bool tie=false;
 for(size_t i=0;i<previous_size_;++i){const auto& g=previous_[i];
  bool support=std::binary_search(g.signatures.begin(),g.signatures.begin()+g.size,signature)||family(g,resource_family);
  bool current_anchor=!support&&g.result.object==ObjectClass::Body&&observed&&!observed->saturated&&anchors(*observed,g);
  if(g.saturated||(!support&&!(g.result.object==ObjectClass::Body&&(same(w,g.world)||current_anchor))))continue;
  double d=distance(w,g.world),o=orientation(w,g.world);if(d>100.||o>2.)continue;
  double score=d+o;if(score+1.e-6<best){best=score;index=static_cast<int>(i);tie=false;}else if(std::abs(score-best)<=1.e-6)tie=true;
 }
 if(index>=0&&!tie){const auto& g=previous_[index];out=g.result;out.material_only=!std::binary_search(g.signatures.begin(),g.signatures.begin()+g.size,signature);}
 // Duplicate current instances mapping to one previous track are rejected as soon as observed.
 if(out.track)for(size_t i=0;i<current_size_;++i){const auto& g=current_[i];if(same(w,g.world)){if(g.saturated)return Classification{};continue;}
  if((family(g,resource_family)||std::find(g.signatures.begin(),g.signatures.begin()+g.size,signature)!=g.signatures.begin()+g.size)&&distance(g.world,previous_[index].world)<=best+1.e-6)return Classification{};
 }
 return out;
}
bool wheel_rectangle(const std::array<LocalWheel,4>& p,float& error) noexcept {
 FP fp;std::array<LocalWheel,4> q{};unsigned mask=0;
 for(auto a:p){if(!std::isfinite(a.x)||!std::isfinite(a.y)||!std::isfinite(a.z)||std::abs(a.x)<.35||std::abs(a.x)>2.5||std::abs(a.z)<.5||std::abs(a.z)>4.||a.y<-2.||a.y>1.5)return false;
  unsigned k=(a.x>0?1:0)+(a.z>0?2:0);if(mask&(1u<<k))return false;mask|=1u<<k;q[k]=a;
 }
 if(mask!=15)return false;
 double halfwidth=0,halfbase=0,ymin=q[0].y,ymax=ymin;for(auto a:q){halfwidth+=std::abs(a.x)/4.;halfbase+=std::abs(a.z)/4.;ymin=std::min(ymin,static_cast<double>(a.y));ymax=std::max(ymax,static_cast<double>(a.y));}
 double bilateral=std::max(std::abs(q[0].x+q[1].x),std::abs(q[2].x+q[3].x));
 double axle=std::max(std::abs(q[0].z-q[1].z),std::abs(q[2].z-q[3].z));
 double width=std::max(std::abs(q[0].x-q[2].x),std::abs(q[1].x-q[3].x));
 double centered=std::abs((q[0].z+q[1].z+q[2].z+q[3].z)/4.);
 if(bilateral>.15+.15*halfwidth||axle>.15+.15*halfbase||width>.15+.15*halfwidth||centered>.2+.2*halfbase||ymax-ymin>.5)return false;
 error=static_cast<float>(bilateral/halfwidth+axle/halfbase+width/halfwidth+centered/halfbase+(ymax-ymin));return true;
}
void classify_constellations(TransformGroup* g,size_t count) noexcept {
 FP fp;if(count>MAX_TRANSFORM_GROUPS)return;
 std::array<ConstellationProposal,MAX_TRANSFORM_GROUPS> proposals{};
 for(size_t i=0;i<count;++i)semantic_clear(g[i].result);
 for(size_t i=0;i<count;++i){auto& body=g[i];auto& prop=proposals[i];
  bool common=!body.saturated&&body.result.track&&!body.result.ambiguous&&body.body_draws>=2&&body.size>=2&&body.body_env_draws;
  bool dynamic=common&&body.result.dynamic&&(body.body_draws==body.draws||body.local_draws==body.draws);
  bool structural=common&&body.result.age>=STRUCTURAL_OBSERVATIONS&&body.body_draws>=4&&body.size>=3&&body.body_base_draws&&body.local_draws==body.draws;
  if(!common){body.structure_frames=0;continue;}
  std::array<uint32_t,MAX_NEAR_WHEELS> candidates{};std::array<LocalWheel,MAX_NEAR_WHEELS> local{};size_t n=0;bool full=false;
  for(size_t j=0;j<count;++j){if(!wheel_group(g[j]))continue;auto p=local_wheel(body.world,g[j].world);if(!nearby(p))continue;
   if(n==MAX_NEAR_WHEELS){full=true;break;}candidates[n]=static_cast<uint32_t>(j);local[n++]=p;
  }
  // An unresolved temporal wheel competing for an already observed slot is negative evidence,
  // not permission to ignore a fifth wheel. A lone cold/culled slot may still use bounded retention.
  bool unresolved_duplicate=false;
  for(size_t j=0;j<count;++j)if(!wheel_group(g[j])&&g[j].wheel_draws>=2&&g[j].wheel_draws==g[j].draws){
   auto p=local_wheel(body.world,g[j].world);if(!nearby(p))continue;
   for(size_t k=0;k<n;++k)if(position_error(p,{local[k].x,local[k].y,local[k].z})<=.1225)unresolved_duplicate=true;
  }
  if(full||unresolved_duplicate){prop.ambiguous=true;body.structure_frames=0;continue;}
  unsigned matches=0;for(size_t a=0;a<n;++a)for(size_t b=a+1;b<n;++b)for(size_t c=b+1;c<n;++c)for(size_t d=c+1;d<n;++d){float error=0;
   if(wheel_rectangle({local[a],local[b],local[c],local[d]},error)){++matches;prop.wheels={candidates[a],candidates[b],candidates[c],candidates[d]};prop.error=error;}
  }
  prop.ambiguous=matches>1;
  bool coherent=false;std::array<std::array<float,3>,4> positions{};
  if(matches==1&&n==4){
   // All four wheels must share an observed generation/layout family; coincidental nearby props fail.
   const auto& first=g[prop.wheels[0]];
   for(size_t f=0;f<first.family_size;++f){bool shared=true;for(auto w:prop.wheels)shared=shared&&family(g[w],first.families[f]);coherent|=shared;}
   for(auto w:prop.wheels){auto p=local_wheel(body.world,g[w].world);auto k=(p.x>0?1:0)+(p.z>0?2:0);positions[k]={p.x,p.y,p.z};}
  }
  if(coherent){bool continuous=body.structure_frames>0;for(int k=0;k<4;++k)continuous=continuous&&position_error({positions[k][0],positions[k][1],positions[k][2]},body.structural_positions[k])<=.1225;
   body.structure_frames=continuous?std::min(body.structure_frames+1,STRUCTURAL_OBSERVATIONS):1;body.structural_positions=positions;
  }else body.structure_frames=0;
  prop.accepted=matches==1&&(dynamic||(structural&&coherent&&body.structure_frames>=STRUCTURAL_OBSERVATIONS));
 }
 std::array<unsigned,MAX_TRANSFORM_GROUPS> uses{};
 for(size_t i=0;i<count;++i)if(proposals[i].accepted)for(auto w:proposals[i].wheels)++uses[w];
 for(size_t i=0;i<count;++i){auto& p=proposals[i];auto& c=g[i].result;
  if(p.accepted)for(auto w:p.wheels)if(uses[w]!=1){p.accepted=false;p.ambiguous=true;}
  if(p.ambiguous){c.vehicle_reasons=(c.dynamic?DYNAMIC_CHASSIS:STRUCTURAL_CHASSIS)|BODY_CLUSTER;g[i].structure_frames=0;continue;}
  if(!p.accepted)continue;c.object=ObjectClass::Body;c.constellation=c.track;c.vehicle_reasons=126|(c.dynamic?DYNAMIC_CHASSIS:STRUCTURAL_CHASSIS);c.symmetry_error=p.error;
  c.source=c.dynamic?IdentitySource::Dynamic:IdentitySource::Structural;c.identity_reasons=c.dynamic?ADMITTED_DYNAMIC:ADMITTED_STRUCTURAL;
  // Slots describe quadrants, never authored wheel names. Ordering is independent of draw order.
  for(auto w:p.wheels){auto point=local_wheel(g[i].world,g[w].world);int k=(point.x>0?1:0)+(point.z>0?2:0);
   c.wheels[k]=g[w].result.track;g[i].wheel_positions[k]={point.x,point.y,point.z};g[i].wheel_families[k]=g[w].family_size?g[w].families[0]:0;g[i].wheel_signatures[k]=g[w].size?g[w].signatures[0]:0;
   auto& wheel=g[w].result;wheel.object=ObjectClass::Wheel;wheel.constellation=c.track;wheel.vehicle_reasons=c.vehicle_reasons;wheel.symmetry_error=p.error;wheel.source=c.source;wheel.identity_reasons=c.identity_reasons;
  }
 }
}
bool strong_vehicle_proof(const Classification& c) noexcept {
 return (c.vehicle_reasons&126)==126&&(c.vehicle_reasons&(DYNAMIC_CHASSIS|STRUCTURAL_CHASSIS))&&!c.ambiguous;
}
const char* identity_source(IdentitySource s) noexcept {
 switch(s){case IdentitySource::Dynamic:return "dynamic";case IdentitySource::Structural:return "structural";case IdentitySource::Retained:return "retained";default:return "none";}
}
uint64_t geometry_resource_family(const Shadow& s,const ResourceRegistry& r) noexcept {
 if(!s.bindings.streams[0].known||!s.bindings.indices.known||!s.bindings.vertex_shader.known)return 0;
 auto vb=r.generation(s.bindings.streams[0].value.pointer),ib=r.generation(s.bindings.indices.value.pointer);if(!vb||!ib)return 0;
 uint64_t h=14695981039346656037ull;for(uint64_t v:{vb,ib,uint64_t(s.bindings.streams[0].value.stride),uint64_t(s.bindings.vertex_shader.value)})
  for(int i=0;i<8;++i){h^=(v>>(8*i))&255;h*=1099511628211ull;}return h?h:1;
}
ClassifierStats TransformTracker::stats() const noexcept {
 ClassifierStats out=events_;if(overflow_)return out;
 for(size_t i=0;i<current_size_;++i){const auto& g=current_[i];const auto& c=g.result;out.dynamic+=c.dynamic;
  out.chassis+=!c.ambiguous&&(c.object==ObjectClass::Body||((c.dynamic||c.age>=STRUCTURAL_OBSERVATIONS)&&g.body_draws>=2&&g.body_env_draws&&(g.body_draws==g.draws||g.local_draws==g.draws)));
  out.constellations+=c.object==ObjectClass::Body;out.body_draws+=c.object==ObjectClass::Body?g.draws:0;out.wheel_draws+=c.object==ObjectClass::Wheel?g.draws:0;
  out.ambiguities+=c.ambiguous||(c.object==ObjectClass::Unknown&&c.vehicle_reasons!=0);
 }return out;
}
uint64_t geometry_signature(const Shadow& s,const ResourceRegistry& resources,const Args& args,uint32_t rva) noexcept {
 if(!s.bindings.streams[0].known||!s.bindings.indices.known||!s.bindings.vertex_shader.known)return 0;
 auto vb=resources.generation(s.bindings.streams[0].value.pointer),ib=resources.generation(s.bindings.indices.value.pointer);
 if(!vb||!ib)return 0;uint64_t h=14695981039346656037ull;auto add=[&](uint64_t v){for(int i=0;i<8;++i){h^=(v>>(8*i))&255;h*=1099511628211ull;}};
 add(71);add(rva);add(vb);add(ib);add(s.bindings.streams[0].value.stride);add(s.bindings.indices.value.base);add(s.bindings.vertex_shader.value);
 for(auto a:args.a)add(a);
 for(int i=0;i<2;++i){if(!s.bindings.textures[i].known)return 0;auto p=s.bindings.textures[i].value;auto serial=resources.generation(p);if(p&&!serial)return 0;add(serial);for(int k:{1,2,3,4,5,6,11,24}){if(!s.tss[i][k].known)return 0;add(s.tss[i][k].value);}}
 if(s.tss[1][24].value!=D3DTTFF_DISABLE){if(!s.matrices[17].known)return 0;const float* f=&s.matrices[17].value.m[0][0];for(int i=0;i<16;++i){uint32_t bits;std::memcpy(&bits,f+i,4);add(bits);}}
 for(int k:{14,15,27}){if(!s.rs[k].known)return 0;add(s.rs[k].value);}return h?h:1;
}
uint32_t draw_reasons(const Shadow& s,bool known,bool race,bool owner) noexcept {
 uint32_t r=(known?VEHICLE_SEMANTICS_CAPABILITY:0)|(race?RACE_PROJECTION:0)|(owner?SHARED_OWNER:0);
 if(s.matrices[256].known&&rigid(s.matrices[256].value))r|=RIGID_WORLD;
 if(s.bindings.vertex_shader.known){auto f=s.bindings.vertex_shader.value;if((f==0x112||f==0x152||f==0x252)&&(f&D3DFVF_NORMAL))r|=NORMAL_FVF;}
 auto eq=[&](int k,DWORD v){return s.tss[1][k].known&&s.tss[1][k].value==v;};
 if(eq(1,D3DTOP_MODULATEALPHA_ADDCOLOR)&&eq(2,D3DTA_CURRENT)&&eq(3,D3DTA_TEXTURE)&&eq(4,D3DTOP_MODULATE)&&eq(5,D3DTA_CURRENT)&&eq(6,D3DTA_TEXTURE)&&s.tss[1][11].known&&(s.tss[1][11].value&0xffff0000)==D3DTSS_TCI_CAMERASPACENORMAL&&eq(24,D3DTTFF_COUNT2)&&s.bindings.textures[1].known&&s.bindings.textures[1].value)r|=ENV_STAGE;
 if(s.rs[27].known&&s.rs[27].value==0&&s.rs[14].known&&s.rs[14].value==1)r|=CL_OPAQUE;return r;
}
const char* object_classification(const DrawClassification& c) noexcept {
 constexpr uint32_t required=VEHICLE_SEMANTICS_CAPABILITY|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|RIGID_WORLD;
 if((c.reasons&required)!=required||!c.transform.track||c.transform.ambiguous)return "UNKNOWN";
 if(c.transform.object==ObjectClass::Body&&c.transform.constellation)return "VEHICLE_BODY";
 if(c.transform.object==ObjectClass::Wheel&&c.transform.constellation)return "VEHICLE_WHEEL";
 if(c.transform.dynamic&&(c.reasons&ENV_STAGE))return "DYNAMIC_ENV_OBJECT";
 return "CANDIDATE"; // Motion alone never proves vehicle identity.
}

const char* material_classification(const DrawClassification& c) noexcept {
 if(c.transform.object==ObjectClass::Wheel)return (c.reasons&ENV_STAGE)?"VEHICLE_WHEEL_ENV":"UNKNOWN_VEHICLE_MATERIAL";
 if(c.transform.object!=ObjectClass::Body)return "UNKNOWN_VEHICLE_MATERIAL";
 if(c.fvf==0x102)return c.alpha_blended?"VEHICLE_ALPHA_UNLIT":"UNKNOWN_VEHICLE_MATERIAL";
 if(c.reasons&ENV_STAGE)return (c.reasons&CL_OPAQUE)?"VEHICLE_BODY_ENV_OPAQUE":c.alpha_blended?"VEHICLE_BODY_ALPHA_ENV":"UNKNOWN_VEHICLE_MATERIAL";
 return "VEHICLE_BODY_BASE";
}
const char* reflection_material_exclusion(const DrawClassification& c) noexcept {
 constexpr uint32_t required=VEHICLE_SEMANTICS_CAPABILITY|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|RIGID_WORLD|NORMAL_FVF;
 if(!(c.reasons&VEHICLE_SEMANTICS_CAPABILITY))return "vehicle_semantics_unsupported";
 if(!(c.reasons&RACE_PROJECTION))return "non_race_context";
 if((c.reasons&required)!=required)return "unmapped_or_unknown_geometry";
 if(c.fvf!=0x152)return "excluded_fvf";
 if(!(c.reasons&CL_OPAQUE)||c.alpha_blended)return "alpha_or_no_depth_write";
 if(!(c.reasons&ENV_STAGE))return "non_stock_env_stage";
 return "eligible";
}
const char* reflection_exclusion(const DrawClassification& c) noexcept {
 if(c.semantic_source==VehicleSemanticSource::Learned&&c.semantic_id)return reflection_material_exclusion(c);
 constexpr uint32_t required=VEHICLE_SEMANTICS_CAPABILITY|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|RIGID_WORLD;
 if(!(c.reasons&VEHICLE_SEMANTICS_CAPABILITY))return "vehicle_semantics_unsupported";
 if(!(c.reasons&RACE_PROJECTION))return "non_race_context";
 if((c.reasons&required)!=required)return "unmapped_or_unknown_geometry";
 if(c.transform.object==ObjectClass::Wheel)return "vehicle_wheel_stock";
 if(c.transform.object==ObjectClass::Unknown&&c.transform.track&&c.transform.age>=4&&!c.transform.dynamic&&!c.transform.ambiguous)return "static_transform_without_vehicle_proof";
 if(c.transform.object!=ObjectClass::Body||!c.transform.constellation||!strong_vehicle_proof(c.transform)||c.transform.ambiguous)return "unproven_object";
 for(size_t i=0;i<4;++i){if(!c.transform.wheels[i])return "incomplete_constellation";for(size_t j=0;j<i;++j)if(c.transform.wheels[i]==c.transform.wheels[j])return "incomplete_constellation";}
 if(c.transform.material_only)return "unproven_draw_resource";
 if(c.fvf!=0x152)return "excluded_fvf";
 if(!(c.reasons&CL_OPAQUE))return "alpha_or_no_depth_write";
 if(!(c.reasons&ENV_STAGE))return "non_stock_env_stage";
 return "eligible";
}
}
