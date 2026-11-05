#pragma once
#include <array>
#include <cmath>
#include <algorithm>
#include <cstdint>
namespace gfx2::atmosphere {
inline bool rigid_camera_position(const std::array<float,16>& view,std::array<float,3>& eye)noexcept{
    for(float x:view)if(!std::isfinite(x))return false;
    if(std::abs(view[3])+std::abs(view[7])+std::abs(view[11])+std::abs(view[15]-1)>.002f)return false;
    for(unsigned r=0;r<3;++r)for(unsigned c=0;c<3;++c){float dot=0;for(unsigned j=0;j<3;++j)dot+=view[r*4+j]*view[c*4+j];if(std::abs(dot-float(r==c))>.002f)return false;}
    for(unsigned i=0;i<3;++i)eye[i]=-(view[12]*view[i*4]+view[13]*view[i*4+1]+view[14]*view[i*4+2]);return true;
}
// Existing panorama encodes tan(elevation), not the native cylinder's absolute Y.
// Uniform yaw-only sky WORLD and rigid VIEW are required; cap UVs stay authored.
inline bool sky_panorama_v(const std::array<float,16>& w,const std::array<float,16>& view,const std::array<float,3>& p,float source_v,float& v)noexcept{
    v=source_v;for(float x:w)if(!std::isfinite(x))return false;for(float x:view)if(!std::isfinite(x))return false;
    for(float x:p)if(!std::isfinite(x))return false;if(!std::isfinite(source_v))return false;
    std::array<float,3> eye{};if(!rigid_camera_position(view,eye))return false;
    const float scale=std::hypot(w[0],w[2]);if(scale<1e-6f||std::abs(w[5]-scale)>.002f*scale||std::abs(std::hypot(w[8],w[10])-scale)>.002f*scale||std::abs(w[1])+std::abs(w[4])+std::abs(w[6])+std::abs(w[9])>.002f*scale)return false;
    if(std::abs(w[3])+std::abs(w[7])+std::abs(w[11])+std::abs(w[15]-1)>.002f||std::abs(w[0]*w[8]+w[2]*w[10])>.002f*scale*scale||w[0]*w[10]-w[2]*w[8]<=0)return false;
    if(source_v>=.97f)return true;
    const float radius=std::hypot(p[0],p[2])*scale;if(radius<1)return false;
    const float camera_y=eye[1];
    v=std::clamp(.003f+.995f*(p[1]*w[5]+w[13]-camera_y)/radius,0.f,1.f);return std::isfinite(v);
}
inline float ordered_dither(unsigned x,unsigned y)noexcept{
    static constexpr unsigned matrix[4][4]={{0,8,2,10},{12,4,14,6},{3,11,1,9},{15,7,13,5}};
    return (float(matrix[y&3][x&3])+.5f)/16-.5f;
}
inline unsigned sun_quantize(float intensity,unsigned x,unsigned y,float strength)noexcept{
    if(!std::isfinite(intensity)||!std::isfinite(strength)||intensity<=0)return 0;
    float noise=ordered_dither(x,y);
    if(strength>2){uint32_t h=(x&255u)*0x9e3779b9u+(y&255u)*0x85ebca6bu;h^=h>>16;h*=0x7feb352du;h^=h>>15;noise=(float(h&65535u)+.5f)/65536-.5f;}
    const float amount=std::min(std::clamp(strength,0.f,16.f),intensity*510);
    return unsigned(std::clamp(std::lround(intensity*255+noise*amount),0l,255l));
}
inline float sun_layer_dither(float strength,float layer_gain)noexcept{
    if(!std::isfinite(strength)||!std::isfinite(layer_gain)||strength<=0||layer_gain<=0)return 0;
    // Five additive visibility samples each use 1/5 of the layer energy.
    // Dither must survive that multiplication before framebuffer quantization.
    return std::clamp(strength/std::max(layer_gain*.2f,.0625f),0.f,16.f);
}
inline float rim_amount(const std::array<float,3>& n,const std::array<float,3>& eye,const std::array<float,3>& sun,float power)noexcept{
    float a=0,b=0,c=0;for(unsigned i=0;i<3;++i){if(!std::isfinite(n[i])||!std::isfinite(eye[i])||!std::isfinite(sun[i]))return 0;a+=n[i]*n[i];b+=eye[i]*eye[i];c+=sun[i]*sun[i];}if(a<1e-8f||b<1e-8f||c<1e-8f||!std::isfinite(power))return 0;
    float facing=0,lit=0;for(unsigned i=0;i<3;++i){facing+=n[i]*eye[i]/std::sqrt(a*b);lit+=n[i]*sun[i]/std::sqrt(a*c);}if(facing<0)return 0;return std::pow(1-std::clamp(facing,0.f,1.f),std::clamp(power,1.f,8.f))*std::max(0.f,lit);
}
}
