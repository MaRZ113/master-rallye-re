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
uint32_t TransformTracker::observe(const D3DMATRIX& world,uint64_t signature) noexcept {
 FP fp;if(overflow_||!signature||!rigid(world))return UINT32_MAX;
 size_t i=0;for(;i<current_size_;++i)if(same(current_[i].world,world))break;
 if(i==current_size_){if(i==MAX_TRANSFORM_GROUPS){overflow_=true;return UINT32_MAX;}current_[i]=TransformGroup{};current_[i].world=world;++current_size_;}
 auto& g=current_[i];for(size_t j=0;j<g.size;++j)if(g.signatures[j]==signature)return static_cast<uint32_t>(i);
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
 previous_size_=current_size_;for(size_t i=0;i<current_size_;++i)previous_[i]=current_[i];
 // Current results remain available until the next observation starts a new frame.
}
const Classification* TransformTracker::result(uint32_t group) const noexcept {return !overflow_&&group<current_size_?&current_[group].result:nullptr;}
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
 if(c.transform.dynamic&&(c.reasons&ENV_STAGE))return "DYNAMIC_ENV_OBJECT";
 return "CANDIDATE"; // Motion alone never proves vehicle identity.
}
}
