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
}
uint32_t TransformTracker::observe(const D3DMATRIX& world,uint64_t signature,GroupDraw draw) noexcept {
 FP fp;if(overflow_||!signature||!rigid(world))return UINT32_MAX;
 size_t i=0;for(;i<current_size_;++i)if(same(current_[i].world,world))break;
 if(i==current_size_){if(i==MAX_TRANSFORM_GROUPS){overflow_=true;return UINT32_MAX;}current_[i]=TransformGroup{};current_[i].world=world;++current_size_;}
 auto& g=current_[i];
 ++g.draws;g.triangles+=draw.triangles;
 if(draw.fvf==0x142||draw.fvf==0x152||draw.fvf==0x242||draw.fvf==0x252)++g.body_draws;
 if(draw.fvf==0x152&&(draw.reasons&(ENV_STAGE|CL_OPAQUE))==(ENV_STAGE|CL_OPAQUE))++g.body_env_draws;
 if(draw.fvf==0x112&&(draw.reasons&(ENV_STAGE|CL_OPAQUE))==(ENV_STAGE|CL_OPAQUE))++g.wheel_draws;
 for(size_t j=0;j<g.size;++j)if(g.signatures[j]==signature)return static_cast<uint32_t>(i);
 if(g.size==MAX_GROUP_SIGNATURES){g.saturated=true;return UINT32_MAX;}g.signatures[g.size++]=signature;return static_cast<uint32_t>(i);
}
void TransformTracker::reset() noexcept {current_size_=previous_size_=0;overflow_=false;++epoch_;} // Monotonic IDs never reused.
void TransformTracker::finish_frame() noexcept {
 FP fp;
 if(overflow_){previous_size_=0;for(size_t i=0;i<current_size_;++i)current_[i].result={};return;}
 for(size_t i=0;i<current_size_;++i)std::sort(current_[i].signatures.begin(),current_[i].signatures.begin()+current_[i].size);
 std::array<int,MAX_TRANSFORM_GROUPS> best{},reverse{};best.fill(-1);reverse.fill(-1);
 std::array<double,MAX_TRANSFORM_GROUPS> cost{},back{};cost.fill(1.e100);back.fill(1.e100);
 std::array<bool,MAX_TRANSFORM_GROUPS> ambiguous{},reverse_ambiguous{};
 for(size_t i=0;i<current_size_;++i)for(size_t j=0;j<previous_size_;++j){
  if(current_[i].saturated||previous_[j].saturated)continue;double d=distance(current_[i].world,previous_[j].world),o=orientation(current_[i].world,previous_[j].world);
  if(d>100.||o>2.||!overlap(current_[i],previous_[j]))continue;double score=d+o;
  if(score+1.e-6<cost[i]){cost[i]=score;best[i]=static_cast<int>(j);ambiguous[i]=false;}else if(std::abs(score-cost[i])<=1.e-6)ambiguous[i]=true;
  if(score+1.e-6<back[j]){back[j]=score;reverse[j]=static_cast<int>(i);reverse_ambiguous[j]=false;}else if(std::abs(score-back[j])<=1.e-6)reverse_ambiguous[j]=true;
 }
 // Sort only new-ID assignment, not draws: equivalent draw permutations receive the same track IDs.
 std::array<size_t,MAX_TRANSFORM_GROUPS> order{};for(size_t i=0;i<current_size_;++i)order[i]=i;
 std::sort(order.begin(),order.begin()+current_size_,[&](size_t a,size_t b){const float* x=&current_[a].world.m[0][0];const float* y=&current_[b].world.m[0][0];for(int i=0;i<16;++i)if(x[i]!=y[i])return x[i]<y[i];return false;});
 for(size_t n=0;n<current_size_;++n){size_t i=order[n];auto& g=current_[i];int j=best[i];bool match=j>=0&&!ambiguous[i]&&!reverse_ambiguous[j]&&reverse[j]==static_cast<int>(i);
  if(g.saturated){g.result={};g.motion=0;continue;}
  if(match){const auto& old=previous_[j];g.result=old.result;g.result.ambiguous=false;++g.result.age;g.motion=old.motion;
   if(distance(g.world,old.world)>.0025||orientation(g.world,old.world)>.0001)++g.motion;
   g.result.dynamic=g.result.age>=4&&g.motion>=2;
  }else {g.result={++next_id_,1,false,j>=0};g.motion=0;}
 }
 classify_constellations(current_.data(),current_size_);
 previous_size_=current_size_;for(size_t i=0;i<current_size_;++i)previous_[i]=current_[i];
 // Current results remain available until the next observation starts a new frame.
}
const Classification* TransformTracker::result(uint32_t group) const noexcept {return !overflow_&&group<current_size_?&current_[group].result:nullptr;}
Classification TransformTracker::predict(const D3DMATRIX& w,uint64_t signature) const noexcept {
 FP fp;Classification out{};if(overflow_||!signature||!rigid(w))return out;
 double best=1.e100;int index=-1;bool tie=false;
 for(size_t i=0;i<previous_size_;++i){const auto& g=previous_[i];
  if(g.saturated||!std::binary_search(g.signatures.begin(),g.signatures.begin()+g.size,signature))continue;
  double d=distance(w,g.world),o=orientation(w,g.world);if(d>100.||o>2.)continue;
  double score=d+o;if(score+1.e-6<best){best=score;index=static_cast<int>(i);tie=false;}else if(std::abs(score-best)<=1.e-6)tie=true;
 }
 if(index>=0&&!tie)out=previous_[index].result;
 // Duplicate current instances mapping to one previous track are rejected as soon as observed.
 if(out.track)for(size_t i=0;i<current_size_;++i){const auto& g=current_[i];if(same(w,g.world)){if(g.saturated)return Classification{};continue;}
  if(std::find(g.signatures.begin(),g.signatures.begin()+g.size,signature)!=g.signatures.begin()+g.size&&distance(g.world,previous_[index].world)<=best+1.e-6)return Classification{};
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
 for(size_t i=0;i<count;++i){auto& c=g[i].result;c.object=ObjectClass::Unknown;c.constellation=0;c.vehicle_reasons=0;c.wheels={};c.symmetry_error=0;}
 for(size_t i=0;i<count;++i){auto& body=g[i];auto& prop=proposals[i];
  if(body.saturated||!body.result.track||body.result.ambiguous||!body.result.dynamic||body.body_draws<2||body.size<2||!body.body_env_draws||body.body_draws!=body.draws)continue;
  std::array<uint32_t,MAX_NEAR_WHEELS> candidates{};std::array<LocalWheel,MAX_NEAR_WHEELS> local{};size_t n=0;bool full=false;
  for(size_t j=0;j<count;++j){const auto& wheel=g[j];if(wheel.saturated||!wheel.result.track||wheel.result.ambiguous||wheel.wheel_draws<2||wheel.wheel_draws!=wheel.draws)continue;
   std::array<float,3> coordinates{};for(int a=0;a<3;++a){double v=0;for(int k=0;k<3;++k)v+=(static_cast<double>(wheel.world.m[3][k])-body.world.m[3][k])*body.world.m[a][k];coordinates[a]=static_cast<float>(v);}LocalWheel p{coordinates[0],coordinates[1],coordinates[2]};
   if(std::abs(p.x)<.35||std::abs(p.x)>2.5||std::abs(p.z)<.5||std::abs(p.z)>4.||p.y<-2.||p.y>1.5)continue;
   if(n==MAX_NEAR_WHEELS){full=true;break;}candidates[n]=static_cast<uint32_t>(j);local[n++]=p;
  }
  if(full){prop.ambiguous=true;continue;}
  unsigned matches=0;for(size_t a=0;a<n;++a)for(size_t b=a+1;b<n;++b)for(size_t c=b+1;c<n;++c)for(size_t d=c+1;d<n;++d){float error=0;
   if(wheel_rectangle({local[a],local[b],local[c],local[d]},error)){++matches;prop.wheels={candidates[a],candidates[b],candidates[c],candidates[d]};prop.error=error;}
  }
  prop.accepted=matches==1;prop.ambiguous=matches>1;
 }
 // Conflict pass is simultaneous: traversal order cannot win a shared wheel.
 std::array<unsigned,MAX_TRANSFORM_GROUPS> uses{};
 for(size_t i=0;i<count;++i)if(proposals[i].accepted)for(auto w:proposals[i].wheels)++uses[w];
 for(size_t i=0;i<count;++i){auto& p=proposals[i];auto& c=g[i].result;
  if(p.accepted)for(auto w:p.wheels)if(uses[w]!=1){p.accepted=false;p.ambiguous=true;}
  if(p.ambiguous){c.vehicle_reasons=DYNAMIC_CHASSIS|BODY_CLUSTER;continue;}
  if(!p.accepted)continue;c.object=ObjectClass::Body;c.constellation=c.track;c.vehicle_reasons=127;c.symmetry_error=p.error;
  std::sort(p.wheels.begin(),p.wheels.end(),[&](uint32_t a,uint32_t b){return g[a].result.track<g[b].result.track;});
  for(size_t k=0;k<4;++k){auto& wheel=g[p.wheels[k]].result;c.wheels[k]=wheel.track;wheel.object=ObjectClass::Wheel;wheel.constellation=c.track;wheel.vehicle_reasons=127;wheel.symmetry_error=p.error;}
 }
}
ClassifierStats TransformTracker::stats() const noexcept {
 ClassifierStats out{};if(overflow_)return out;
 for(size_t i=0;i<current_size_;++i){const auto& g=current_[i];const auto& c=g.result;out.dynamic+=c.dynamic;
  out.chassis+=c.dynamic&&!c.ambiguous&&g.body_draws>=2&&g.body_draws==g.draws&&g.body_env_draws>0;
  out.constellations+=c.object==ObjectClass::Body;out.body_draws+=c.object==ObjectClass::Body?g.draws:0;out.wheel_draws+=c.object==ObjectClass::Wheel?g.draws:0;
  out.ambiguities+=c.ambiguous||c.vehicle_reasons==3;
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
 uint32_t r=(known?EXACT_BUILD:0)|(race?RACE_PROJECTION:0)|(owner?SHARED_OWNER:0);
 if(s.matrices[256].known&&rigid(s.matrices[256].value))r|=RIGID_WORLD;
 if(s.bindings.vertex_shader.known){auto f=s.bindings.vertex_shader.value;if((f==0x112||f==0x152||f==0x252)&&(f&D3DFVF_NORMAL))r|=NORMAL_FVF;}
 auto eq=[&](int k,DWORD v){return s.tss[1][k].known&&s.tss[1][k].value==v;};
 if(eq(1,D3DTOP_MODULATEALPHA_ADDCOLOR)&&eq(2,D3DTA_CURRENT)&&eq(3,D3DTA_TEXTURE)&&eq(4,D3DTOP_MODULATE)&&eq(5,D3DTA_CURRENT)&&eq(6,D3DTA_TEXTURE)&&s.tss[1][11].known&&(s.tss[1][11].value&0xffff0000)==D3DTSS_TCI_CAMERASPACENORMAL&&eq(24,D3DTTFF_COUNT2)&&s.bindings.textures[1].known&&s.bindings.textures[1].value)r|=ENV_STAGE;
 if(s.rs[27].known&&s.rs[27].value==0&&s.rs[14].known&&s.rs[14].value==1)r|=CL_OPAQUE;return r;
}
const char* object_classification(const DrawClassification& c) noexcept {
 constexpr uint32_t required=EXACT_BUILD|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|RIGID_WORLD;
 if((c.reasons&required)!=required||!c.transform.track||c.transform.ambiguous)return "UNKNOWN";
 if(c.transform.object==ObjectClass::Body&&c.transform.constellation)return "VEHICLE_BODY";
 if(c.transform.object==ObjectClass::Wheel&&c.transform.constellation)return "VEHICLE_WHEEL";
 if(c.transform.dynamic&&(c.reasons&ENV_STAGE))return "DYNAMIC_ENV_OBJECT";
 return "CANDIDATE"; // Motion alone never proves vehicle identity.
}

const char* material_classification(const DrawClassification& c) noexcept {
 if(c.transform.object==ObjectClass::Wheel)return (c.reasons&ENV_STAGE)?"VEHICLE_WHEEL_ENV":"UNKNOWN_VEHICLE_MATERIAL";
 if(c.transform.object!=ObjectClass::Body)return "UNKNOWN_VEHICLE_MATERIAL";
 if(c.reasons&ENV_STAGE)return (c.reasons&CL_OPAQUE)?"VEHICLE_BODY_ENV_OPAQUE":c.alpha_blended?"VEHICLE_BODY_ALPHA_ENV":"UNKNOWN_VEHICLE_MATERIAL";
 return "VEHICLE_BODY_BASE";
}
const char* reflection_exclusion(const DrawClassification& c) noexcept {
 constexpr uint32_t required=EXACT_BUILD|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|RIGID_WORLD;
 if(!(c.reasons&EXACT_BUILD))return "unknown_build";
 if(!(c.reasons&RACE_PROJECTION))return "non_race_context";
 if((c.reasons&required)!=required)return "unmapped_or_unknown_geometry";
 if(c.transform.object==ObjectClass::Wheel)return "vehicle_wheel_stock";
 if(c.transform.object==ObjectClass::Unknown&&c.transform.track&&c.transform.age>=4&&!c.transform.dynamic&&!c.transform.ambiguous)return "static_transform_without_vehicle_proof";
 if(c.transform.object!=ObjectClass::Body||!c.transform.constellation||c.transform.vehicle_reasons!=127||c.transform.ambiguous)return "unproven_object";
 for(size_t i=0;i<4;++i){if(!c.transform.wheels[i])return "incomplete_constellation";for(size_t j=0;j<i;++j)if(c.transform.wheels[i]==c.transform.wheels[j])return "incomplete_constellation";}
 if(c.fvf!=0x152)return "excluded_fvf";
 if(!(c.reasons&CL_OPAQUE))return "alpha_or_no_depth_write";
 if(!(c.reasons&ENV_STAGE))return "non_stock_env_stage";
 return "eligible";
}
}
