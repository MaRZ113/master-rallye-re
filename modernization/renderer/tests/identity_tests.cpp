#include "vehicle_classifier.hpp"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <algorithm>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
D3DMATRIX world(float x=0,float z=0){D3DMATRIX m{};m._11=m._22=m._33=m._44=1;m._41=x;m._43=z;return m;}
Classification observe_vehicle(TransformTracker& t,int tick=0,bool brake=false,int wheels=4,bool shuffled=false,uint64_t generation=100,bool unrelated=false,bool extra_wheel=false){
 float x=tick*.2f;auto b=world(x);uint32_t body=0;
 auto draw_body=[&]{
  if(shuffled&&brake)t.observe(b,5,{0x102,CL_OPAQUE,10,generation+2});
  body=t.observe(b,1,{0x152,ENV_STAGE|CL_OPAQUE,100,generation});
  t.observe(b,2,{0x152,ENV_STAGE|CL_OPAQUE,50,generation});
  t.observe(b,3,{0x142,CL_OPAQUE,20,generation+1});
  if(!brake)t.observe(b,4,{0x152,ENV_STAGE|CL_OPAQUE,10,generation});
  if(brake){if(!shuffled)t.observe(b,5,{0x102,CL_OPAQUE,10,generation+2});t.observe(b,6,{0x102,0,28,generation+2});}
 };
 auto draw_wheels=[&]{for(int k=0;k<wheels;++k){int j=shuffled?wheels-1-k:k;auto w=world(x+(j&1?.9f:-.9f),j&2?1.4f:-1.4f);
  t.observe(w,11,{0x112,ENV_STAGE|CL_OPAQUE,73,unrelated?generation+20+j:generation+10});
  t.observe(w,12,{0x112,ENV_STAGE|CL_OPAQUE,91,unrelated?generation+20+j:generation+10});}
  if(extra_wheel){auto w=world(x-.92f,-1.4f);t.observe(w,11,{0x112,ENV_STAGE|CL_OPAQUE,73,generation+10});t.observe(w,12,{0x112,ENV_STAGE|CL_OPAQUE,91,generation+10});}
 };
 if(shuffled){draw_wheels();draw_body();}else{draw_body();draw_wheels();}
 t.finish_frame();auto c=*t.result(body);t.next_frame();return c;
}
void stationary_and_mutation(){
 auto t=std::make_unique<TransformTracker>();Classification c;
 for(uint32_t i=0;i<STRUCTURAL_OBSERVATIONS;++i){c=observe_vehicle(*t);if(i+1<STRUCTURAL_OBSERVATIONS)CHECK(c.object==ObjectClass::Unknown);}
 CHECK(c.object==ObjectClass::Body&&!c.dynamic&&c.source==IdentitySource::Structural&&strong_vehicle_proof(c));
 auto id=c.constellation,track=c.track;
 c=observe_vehicle(*t,0,true);CHECK(c.constellation==id&&c.track==track&&c.source==IdentitySource::Retained&&(c.identity_reasons&BODY_MATERIAL_MUTATION));CHECK(t->stats().mutations==1);
 auto changed=t->predict(world(),5,102);CHECK(changed.constellation==id&&changed.object==ObjectClass::Body);
 DrawClassification d;d.reasons=255;d.fvf=0x102;d.transform=changed;CHECK(std::string(reflection_exclusion(d))!="eligible");
 auto eligible=t->predict(world(),1,100);d.fvf=0x152;d.transform=eligible;CHECK(std::string(reflection_exclusion(d))=="eligible");
 auto new_resource=t->predict(world(),999,999);CHECK(new_resource.object==ObjectClass::Body&&new_resource.material_only);d.transform=new_resource;CHECK(std::string(reflection_exclusion(d))=="unproven_draw_resource");
 c=observe_vehicle(*t,0,false);CHECK(c.constellation==id&&c.track==track);
 // Material-only changes retain immutable family anchors even when no old material signature remains.
 auto b=world();t->observe(b,101,{0x152,ENV_STAGE|CL_OPAQUE,100,100});t->observe(b,102,{0x152,ENV_STAGE|CL_OPAQUE,50,100});t->observe(b,103,{0x142,CL_OPAQUE,20,101});t->observe(b,104,{0x152,ENV_STAGE|CL_OPAQUE,10,100});
 for(int k=0;k<4;++k){auto w=world(k&1?.9f:-.9f,k&2?1.4f:-1.4f);t->observe(w,11,{0x112,ENV_STAGE|CL_OPAQUE,73,110});t->observe(w,12,{0x112,ENV_STAGE|CL_OPAQUE,91,110});}
 t->finish_frame();CHECK(t->result(0)->constellation==id&&t->result(0)->track==track);t->next_frame();
}
void retention_and_invalidation(){
 auto t=std::make_unique<TransformTracker>();Classification c;for(int i=0;i<5;++i)c=observe_vehicle(*t);auto id=c.constellation;
 c=observe_vehicle(*t,0,false,3);CHECK(c.constellation==id&&c.grace==1&&c.source==IdentitySource::Retained);
 c=observe_vehicle(*t);CHECK(c.constellation==id);c=observe_vehicle(*t);CHECK(c.constellation==id&&c.grace==0);
 for(uint32_t i=1;i<=IDENTITY_GRACE_FRAMES;++i){c=observe_vehicle(*t,0,false,3);CHECK(c.constellation==id&&c.grace==i);}
 c=observe_vehicle(*t,0,false,3);CHECK(!c.constellation&&t->stats().demotions==1);
 for(uint32_t i=0;i<STRUCTURAL_OBSERVATIONS+1;++i)c=observe_vehicle(*t);CHECK(c.constellation&&c.constellation!=id);id=c.constellation;
 c=observe_vehicle(*t,0,false,4,false,500);CHECK(c.constellation!=id&&c.age==1&&c.object==ObjectClass::Unknown);
 for(int i=0;i<5;++i)c=observe_vehicle(*t,0,false,4,false,500);id=c.constellation;auto epoch=t->epoch();t->reset();CHECK(t->epoch()!=epoch&&!t->predict(world(),1,500).constellation);
 for(int i=0;i<5;++i)c=observe_vehicle(*t,0,false,4,false,500);CHECK(c.constellation&&c.constellation!=id);id=c.constellation;
 t->finish_frame();CHECK(t->stats().demotions==1);t->next_frame();CHECK(!t->predict(world(),1,500).constellation); // Complete chassis disappearance expires proof immediately.
 c=observe_vehicle(*t,0,false,4,false,500);CHECK(c.constellation!=id&&c.age==1);
}
void conservative_and_order(){
 auto a=std::make_unique<TransformTracker>(),b=std::make_unique<TransformTracker>();Classification ca,cb;
 for(int i=0;i<6;++i){ca=observe_vehicle(*a,0,i>=4,4,false);cb=observe_vehicle(*b,0,i>=4,4,true);CHECK(ca.track==cb.track&&ca.constellation==cb.constellation&&ca.source==cb.source);}
 CHECK(ca.constellation);
 ca=observe_vehicle(*a,0,false,4,false,100,false,true);CHECK(!ca.constellation&&a->stats().demotions==1); // Strong five-wheel ambiguity defeats sticky retention.
 a->reset();for(int i=0;i<8;++i)ca=observe_vehicle(*a,0,false,3);CHECK(!ca.constellation);
 a->reset();for(int i=0;i<8;++i)ca=observe_vehicle(*a,0,false,4,false,100,true);CHECK(!ca.constellation); // Four unrelated static props, even if positioned as a rectangle.
 a->reset();for(int i=0;i<8;++i){auto body=a->observe(world(),1,{0x152,ENV_STAGE|CL_OPAQUE,10,100});a->observe(world(),2,{0x152,ENV_STAGE|CL_OPAQUE,20,100});
  for(int k=0;k<4;++k){auto w=world(k&1?.9f:-.9f,k&2?1.4f:-1.4f);a->observe(w,11,{0x112,ENV_STAGE|CL_OPAQUE,10,110});a->observe(w,12,{0x112,ENV_STAGE|CL_OPAQUE,20,110});}
  a->finish_frame();CHECK(!a->result(body)->constellation);a->next_frame();} // Weak body evidence does not admit stationary scenery.
 a->reset();for(int i=0;i<6;++i)ca=observe_vehicle(*a,i);CHECK(ca.dynamic&&ca.constellation&&strong_vehicle_proof(ca)); // Original dynamic path retained.
}
void replay(){
 auto t=std::make_unique<TransformTracker>();unsigned frames=0;CHECK(std::cin>>frames);CHECK(frames<=32);
 for(unsigned f=0;f<frames;++f){unsigned groups=0;CHECK(std::cin>>groups);CHECK(groups<=MAX_TRANSFORM_GROUPS);uint32_t body=UINT32_MAX;unsigned eligible=0;
  for(unsigned g=0;g<groups;++g){D3DMATRIX w{};// Matrix words follow the portable fixture protocol.
   for(int r=0;r<4;++r)for(int c=0;c<4;++c)CHECK(std::cin>>w.m[r][c]);unsigned count=0;CHECK(std::cin>>count);CHECK(count<=MAX_GROUP_SIGNATURES);
   for(unsigned n=0;n<count;++n){uint64_t signature=0,family=0;GroupDraw draw;CHECK(std::cin>>signature>>family>>draw.fvf>>draw.reasons>>draw.triangles);draw.resource_family=family;
    auto index=t->observe(w,signature,draw);if(draw.fvf==0x152&&count>=4)body=index;
    DrawClassification d;d.reasons=EXACT_BUILD|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|RIGID_WORLD|draw.reasons;d.fvf=draw.fvf;d.transform=t->predict(w,signature,family);
    eligible+=std::string(reflection_exclusion(d))=="eligible";
   }
  }
  t->finish_frame();auto c=body==UINT32_MAX?Classification{}:*t->result(body);auto stats=t->stats();
  std::cout<<"{\"frame\":"<<f<<",\"track\":"<<c.track<<",\"constellation\":"<<c.constellation<<",\"source\":\""<<identity_source(c.source)<<"\",\"mutations\":"<<stats.mutations<<",\"eligible\":"<<eligible<<"}\n";t->next_frame();
 }
}
int main(int argc,char** argv){try{if(argc==2&&std::string(argv[1])=="--replay"){replay();return 0;}stationary_and_mutation();retention_and_invalidation();conservative_and_order();std::cout<<"Structural admission / stable material mutation / bounded wheel grace / generation Reset scene invalidation / static exclusion / order: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
