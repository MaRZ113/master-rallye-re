// Offline authoring oracle: uses the exact renderer anchor implementation.
#include "atmosphere_lamp_surface.hpp"
#include <iostream>
#include <iomanip>
#include <numeric>
using namespace gfx2::atmosphere;
int main(){size_t cases=0;std::cin>>cases;std::cout<<std::setprecision(9);
 for(size_t c=0;c<cases;++c){size_t n;bool front;LampVec seed{};std::cin>>n>>front>>seed[0]>>seed[1]>>seed[2];
  std::vector<LampVec> p(n);for(auto& v:p)for(auto& x:v)std::cin>>x;
  std::vector<uint32_t> ix(n);std::iota(ix.begin(),ix.end(),0);LampSurfaceAnchor a;
  if(!bind_lamp_surface(seed,front,p,ix,a)){std::cout<<"0\n";continue;}
  LampVec rest{},normal{};if(!a.evaluate(p,rest,normal))return 2;
  float translation_error=0,rotation_error=0,damage_error=0;const LampVec delta{.31f,-.17f,.23f};
  auto q=p;for(auto& v:q)for(unsigned k=0;k<3;++k)v[k]+=delta[k];LampVec out{},axis{};
  if(!a.evaluate(q,out,axis))return 3;for(unsigned k=0;k<3;++k)translation_error=std::max(translation_error,std::abs(out[k]-rest[k]-delta[k]));
  const float co=std::cos(.47f),si=std::sin(.47f);auto rotate=[&](const LampVec& v){return LampVec{co*v[0]+si*v[2],v[1],-si*v[0]+co*v[2]};};
  q=p;for(auto& v:q)v=rotate(v);if(!a.evaluate(q,out,axis))return 4;const auto wanted=rotate(rest);
  for(unsigned k=0;k<3;++k)rotation_error=std::max(rotation_error,std::abs(out[k]-wanted[k]));
  q=p;for(auto i:a.vertices)for(unsigned k=0;k<3;++k)q[i][k]+=delta[k];if(!a.evaluate(q,out,axis))return 5;
  for(unsigned k=0;k<3;++k)damage_error=std::max(damage_error,std::abs(out[k]-rest[k]-delta[k]));
  q=p;for(auto i:a.vertices)q[i]=p[a.vertices[0]];const bool collapsed_rejected=!a.evaluate(q,out,axis);
  std::cout<<"1 "<<a.vertices[0]/3<<' '<<a.weights[0]<<' '<<a.weights[1]<<' '<<a.weights[2]<<' '<<a.offset<<' '<<a.sign<<' '<<a.distance<<' '
   <<translation_error<<' '<<rotation_error<<' '<<damage_error<<' '<<collapsed_rejected<<'\n';
 }return std::cin.fail()?6:0;}
