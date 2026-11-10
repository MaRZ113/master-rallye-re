#pragma once
#include <array>
#include <vector>
#include <cmath>
#include <algorithm>
#include <cstdint>
#include <string>

namespace gfx2::atmosphere {
using LampVec=std::array<float,3>;
inline LampVec lamp_sub(const LampVec& a,const LampVec& b)noexcept{return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
inline float lamp_dot(const LampVec& a,const LampVec& b)noexcept{return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
inline LampVec lamp_mix(const LampVec& a,const LampVec& b,const LampVec& c,const LampVec& w)noexcept{
    return {a[0]*w[0]+b[0]*w[1]+c[0]*w[2],a[1]*w[0]+b[1]*w[1]+c[1]*w[2],a[2]*w[0]+b[2]*w[1]+c[2]*w[2]};
}
inline bool lamp_normal(const LampVec& a,const LampVec& b,const LampVec& c,LampVec& n)noexcept{
    const auto u=lamp_sub(b,a),v=lamp_sub(c,a);n={u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]};
    const float d=lamp_dot(n,n);if(!std::isfinite(d)||d<1e-12f)return false;for(auto& x:n)x/=std::sqrt(d);return true;
}
struct LampSurfaceAnchor {
    size_t point=0;std::array<uint32_t,3> vertices{};LampVec weights{};float offset=0,sign=1,distance=0;
    bool evaluate(const std::vector<LampVec>& current,LampVec& position,LampVec& normal)const noexcept{
        for(auto i:vertices)if(i>=current.size())return false;
        const auto &a=current[vertices[0]],&b=current[vertices[1]],&c=current[vertices[2]];
        if(!lamp_normal(a,b,c,normal))return false;position=lamp_mix(a,b,c,weights);
        for(unsigned k=0;k<3;++k){normal[k]*=sign;position[k]+=normal[k]*offset;if(!std::isfinite(position[k]))return false;}return true;
    }
};
// Bind once on a recognised rest lens. Only topology/UV identity is reused;
// positions and normals are always read again from the current draw's mirror.
inline bool bind_lamp_surface(const LampVec& seed,bool front,const std::vector<LampVec>& p,
                              const std::vector<uint32_t>& indices,LampSurfaceAnchor& out)noexcept{
    float best=.25f*.25f;bool found=false;
    for(size_t t=0;t+2<indices.size();t+=3){const auto ia=indices[t],ib=indices[t+1],ic=indices[t+2];if(ia>=p.size()||ib>=p.size()||ic>=p.size())return false;
        const auto &a=p[ia],&b=p[ib],&c=p[ic];LampVec normal{};if(!lamp_normal(a,b,c,normal)||std::abs(normal[2])<.35f)continue;
        const auto ab=lamp_sub(b,a),ac=lamp_sub(c,a),ap=lamp_sub(seed,a);
        const float aa=lamp_dot(ab,ab),bb=lamp_dot(ab,ac),cc=lamp_dot(ac,ac),d=aa*cc-bb*bb;
        if(d<=1e-14f)continue;const float v=(cc*lamp_dot(ap,ab)-bb*lamp_dot(ap,ac))/d,w=(aa*lamp_dot(ap,ac)-bb*lamp_dot(ap,ab))/d;
        LampVec weights{1-v-w,v,w};
        if(*std::min_element(weights.begin(),weights.end())<0){
            float edge_best=1e30f;
            for(unsigned e=0;e<3;++e){const auto& x=p[indices[t+e]];const auto& y=p[indices[t+(e+1)%3]];const auto xy=lamp_sub(y,x);
                const float len=lamp_dot(xy,xy);if(len<1e-14f)continue;const float f=std::clamp(lamp_dot(lamp_sub(seed,x),xy)/len,0.f,1.f);
                LampVec ew{};ew[e]=1-f;ew[(e+1)%3]=f;const auto delta=lamp_sub(seed,lamp_mix(a,b,c,ew));const float distance=lamp_dot(delta,delta);
                if(distance<edge_best){edge_best=distance;weights=ew;}}
        }
        const auto delta=lamp_sub(seed,lamp_mix(a,b,c,weights));const float distance=lamp_dot(delta,delta);
        if(!std::isfinite(distance)||distance>=best)continue;
        const float sign=(normal[2]>0)==front?1.f:-1.f;
        best=distance;out.vertices={ia,ib,ic};out.weights=weights;out.sign=sign;out.distance=distance;out.offset=std::clamp(lamp_dot(delta,normal)*sign,0.f,.06f);found=true;
    }
    return found;
}
struct LampDrawAnchors {std::string identity;std::vector<LampSurfaceAnchor> anchors;};
}
