// Real PC source draw fixtures verify SDK-private-tree startup without warmup.
#include "../ps2-research/pc-port/renderer/fleet_damage.hpp"
#include "../ps2-research/pc-port/renderer/ps2_body_presence.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
using namespace gfx2::ps2port;
int main(int argc,char** argv){
 Ps2BodyPresence presence;
 assert(!presence.contains(1,1,1,10,20,30,"ForesterSTI"));
 presence.submitted(1,1,1,10,20,30,"ForesterSTI");presence.submitted(1,1,1,11,21,31,"Other");
 assert(presence.contains(1,1,1,10,20,30,"ForesterSTI"));
 assert(!presence.contains(1,1,1,11,21,31,"ForesterSTI"));
 assert(!presence.contains(1,2,1,10,20,30,"ForesterSTI"));
 presence.submitted(1,2,1,10,20,30,"ForesterSTI");
 assert(!presence.contains(1,2,2,10,20,30,"ForesterSTI"));
 // Body-scoped lamp sets: the directly preceding frame of the same owner also counts.
 assert(presence.recent(1,2,2,10,20,30,"ForesterSTI")&&!presence.recent(1,2,2,11,21,31,"ForesterSTI"));
 assert(presence.recent(1,2,3,10,20,30,"ForesterSTI")==false);
 presence.submitted(1,2,4,10,20,30,"ForesterSTI");assert(!presence.recent(1,2,6,10,20,30,"ForesterSTI"));
 presence.submitted(1,2,7,10,20,30,"ForesterSTI");assert(!presence.recent(1,3,8,10,20,30,"ForesterSTI"));
 assert(argc==2);std::ifstream f(argv[1],std::ios::binary);
 auto word=[&](){uint32_t x=0;f.read(reinterpret_cast<char*>(&x),4);assert(f);return x;};
 const FleetRaceProfile* p=nullptr;for(const auto& c:kRaceFleetProfiles)if(!std::strcmp(c.family,"ForesterSTI"))p=&c;
 assert(p&&word()==p->pcDrawCount);FleetDamageState state;auto profile=fleet_damage_profile("FORESTER");
 state.bind_context(profile,1,2,3,4,5);assert(state.eligible());
 for(unsigned i=0;i<p->pcDrawCount;++i){
  DrawSnapshot g;g.supported_build=true;g.device_id=1;g.complete_mirror_coverage=true;
  g.vertex_resource=16+i;g.index_resource=64+i;g.vertex_generation=g.index_generation=g.vertex_revision=g.index_revision=1;
  g.primitive_type=D3DPT_TRIANGLELIST;g.index_format=D3DFMT_INDEX16;g.fvf=0x112;g.stride=32;
  g.vertex_count=word();g.primitive_count=word();g.vertex_bytes.resize(word());f.read(reinterpret_cast<char*>(g.vertex_bytes.data()),g.vertex_bytes.size());
  g.index_bytes.resize(word());f.read(reinterpret_cast<char*>(g.index_bytes.data()),g.index_bytes.size());assert(f);
  std::vector<std::array<float,3>> points;std::string xyz,uv;assert(RaceDamageState::snapshot(g,points,xyz,uv));
  auto bad=g;float x;std::memcpy(&x,bad.vertex_bytes.data(),4);x+=.1f;std::memcpy(bad.vertex_bytes.data(),&x,4);
  std::string bx,bu;assert(RaceDamageState::snapshot(bad,points,bx,bu));
  assert(state.select(*p,bad,bx,bu,true,256+i,512+i)==p->pcDrawCount);
  assert(!state.observe(i,bad,p->source[i],true,256+i,512+i));
  assert(state.select(*p,g,xyz,uv,true,256+i,512+i)==i);
  assert(state.observe(i,g,p->source[i],true,256+i,512+i));
  assert(state.select(*p,bad,bx,bu,true,256+i,512+i)==i);
  assert(state.select(*p,g,xyz,uv,true,1024+i,512+i)==p->pcDrawCount);
  assert(!state.observe(i,g,p->source[i],true,1024+i,512+i));
  assert(state.observe(i,g,p->source[i],true,256+i,512+i));
 }
 assert(state.complete()&&state.healthy_complete());
 std::cout<<"ForesterSTI: "<<p->pcDrawCount<<" actual sources bootstrap in private tree; deformed first observation and foreign material rejected\n";
}
