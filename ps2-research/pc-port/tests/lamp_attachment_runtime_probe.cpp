// Offline actual-asset load -> snapshot -> deferred owner -> resolve probe.
#include "atmosphere.hpp"
#include <iostream>
#include <fstream>
#include <map>
#include <iomanip>
using namespace gfx2;using namespace gfx2::atmosphere;
namespace gfx2::atmosphere {Lifecycle lifecycle()noexcept{return {};}}
int main(int argc,char** argv){
 if(argc!=5)return 2;const auto ini=std::filesystem::path(argv[1]).wstring();
 const auto rigs=read_lamp_rigs(ini);if(!rigs.loaded)return 3;
 LampAttachments attachments;if(!attachments.load(argv[2],rigs)){std::cerr<<attachments.reason;return 4;}
 std::ifstream fixture(argv[3]);std::ofstream report(argv[4]);size_t cases=0;fixture>>cases;
 unsigned failures=0;float all_error=0,all_axis_error=0;report<<std::setprecision(9)<<"{\"rig_models\":"<<rigs.rigs.size()<<",\"cases\":[";
 for(size_t c=0;c<cases;++c){unsigned state,mutation;size_t count;fixture>>state>>mutation>>count;
  Pilot p(false,ini);p.lamp_rigs=rigs;p.lamp_attachments=attachments;const uint64_t frame=100+c,race=77,reset=9;p.rig_race=race;p.lamp_attachment_queue.begin(frame,race,reset);
  std::map<std::string,uintptr_t> instances;std::map<uintptr_t,std::pair<int,Mat4>> owners;
  struct Expected{LampVec position{},axis{};uint8_t kind=0;float distance=1e30f;};std::map<std::pair<uintptr_t,size_t>,Expected> expected;
  const LampVec delta{.31f,-.17f,.23f};const float co=std::cos(.47f),si=std::sin(.47f);
  auto rotate=[&](const LampVec& v){return LampVec{co*v[0]+si*v[2],v[1],-si*v[0]+co*v[2]};};
  for(size_t d=0;d<count;++d){std::string car,texture,expected_uv;unsigned verified;size_t nv,ni;fixture>>car>>texture>>expected_uv>>verified>>nv>>ni;
   if(!instances.count(car))instances[car]=1000+instances.size();const auto instance=instances[car];
   int rig=-1;for(size_t i=0;i<rigs.rigs.size();++i)if(rigs.rigs[i].car==car)rig=int(i);if(rig<0)return 5;
   Mat4 world{};world[0]=world[5]=world[10]=world[15]=1;world[12]=float(instance);world[13]=2;world[14]=30;owners[instance]={rig,world};
   std::vector<uint8_t> bytes(nv*24);for(size_t v=0;v<nv;++v){float xyz[3],uv[2];fixture>>xyz[0]>>xyz[1]>>xyz[2]>>uv[0]>>uv[1];std::memcpy(bytes.data()+v*24,xyz,12);std::memcpy(bytes.data()+v*24+16,uv,8);}
   std::vector<uint32_t> indices(ni);for(auto& i:indices)fixture>>i;
   std::vector<LampVec> original;std::string uv;if(!lamp_attachment_geometry(bytes,24,indices,original,uv)||uv!=expected_uv)return 6;
   std::vector<uint8_t> moved(nv,0);
   for(const auto& row:attachments.rows)if(row.rig==rig&&row.texture==texture&&row.uv==uv&&row.expanded_vertices==original.size()){
    LampVec position{},axis{};if(!row.anchor.evaluate(original,position,axis))return 7;
    if(mutation==1||mutation==3)for(unsigned k=0;k<3;++k)position[k]+=delta[k];else if(mutation==2){position=rotate(position);axis=rotate(axis);}
    for(auto v:row.anchor.vertices)moved[indices[v]]=1;
    for(unsigned k=0;k<3;++k)position[k]+=world[12+k];
    const auto& point=rigs.rigs[size_t(rig)].points[row.anchor.point];uint8_t kind=point.kind;
    if(kind==2&&!state){if(!point.tail)continue;kind=1;}
    const auto key=std::make_pair(instance,row.anchor.point);if(!expected.count(key)||row.anchor.distance<expected[key].distance)expected[key]={position,axis,kind,row.anchor.distance};
   }
   for(size_t v=0;v<nv;++v){LampVec position{};std::memcpy(position.data(),bytes.data()+v*24,12);
    if(mutation==1||(mutation==3&&moved[v]))for(unsigned k=0;k<3;++k)position[k]+=delta[k];else if(mutation==2)position=rotate(position);
    std::memcpy(bytes.data()+v*24,position.data(),12);}
   LampAttachmentDraw snapshot;snapshot.texture=texture;snapshot.world=world;snapshot.owner=verified?instance:0;
   if(!lamp_attachment_geometry(bytes,24,indices,snapshot.positions,snapshot.uv)||snapshot.uv!=expected_uv)return 8;
   if(!p.lamp_attachment_queue.push(std::move(snapshot)))return 9;
  }
  // Register ownership after every draw was queued: switch order is irrelevant.
  for(const auto& pair:owners){p.observe_car(pair.first,pair.second.second,frame);auto* owner=p.rig_owner(pair.first,frame,true);if(!owner)return 10;owner->rig=pair.second.first;if(state)owner->braking=frame;}
  if(!p.lamp_points.empty())return 11;resolve_lamp_attachments(p,frame,race,reset);
  std::map<std::pair<uintptr_t,size_t>,unsigned> emitted;float error=0,axis_error=0;unsigned role_failures=0;
  for(const auto& lamp:p.lamp_points){const auto key=std::make_pair(lamp.instance,lamp.rig_point);++emitted[key];
   const auto found=expected.find(key);if(found==expected.end()){++failures;continue;}if(lamp.kind!=found->second.kind)++role_failures;
   for(unsigned k=0;k<3;++k){error=std::max(error,std::abs(lamp.world[k]-found->second.position[k]));axis_error=std::max(axis_error,std::abs(lamp.axis[k]-found->second.axis[k]));}}
  for(const auto& point:expected)if(emitted[point.first]!=1)++failures;
  const size_t first=p.lamp_points.size();resolve_lamp_attachments(p,frame,race,reset);if(p.lamp_points.size()!=first)++failures;
  if(expected.size()!=10||first!=10||role_failures||error>.0002f||axis_error>.0001f)++failures;all_error=std::max(all_error,error);all_axis_error=std::max(all_axis_error,axis_error);
  if(c)report<<',';report<<"{\"state\":"<<state<<",\"mutation\":"<<mutation<<",\"expected\":"<<expected.size()<<",\"emitted\":"<<first<<",\"role_failures\":"<<role_failures<<",\"max_motion_error\":"<<error<<",\"max_axis_error\":"<<axis_error<<"}";
 }
 report<<"],\"failures\":"<<failures<<",\"max_motion_error\":"<<all_error<<",\"max_axis_error\":"<<all_axis_error<<"}\n";
 if(fixture.fail())return 12;std::cout<<"actual runtime attachment cases="<<cases<<" failures="<<failures<<" max_error="<<all_error<<'\n';return failures?1:0;
}
