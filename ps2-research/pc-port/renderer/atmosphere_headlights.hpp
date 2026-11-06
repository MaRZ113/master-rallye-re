#pragma once
// ATMOSPHERE6.3 P2: projected car headlights and tail-light ground glow on
// fixed function (no shaders). After a lit course draw the same geometry is
// drawn once more, additively: texture * light colour * cookie * range ramp.
//  * cookie: TCI_CAMERASPACEPOSITION -> camera space -> world (inverse view)
//    -> light space -> projector, COUNT3|PROJECTED (beam shape, low-beam cut);
//  * ramp:   same position -> distance along the beam / range, COUNT2; texel 0
//    is black, so everything behind the lamp (and beyond the range) gets none.
// Fog colour is black for the pass, so the light fades with the course fog.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <string>
#include <fstream>
#include <sstream>
#include <vector>
#include <windows.h>

namespace gfx2::atmosphere {
using Mat4=std::array<float,16>;   // D3D row-vector layout: m[row*4+col], translation in row 3

struct Projector {float range=48,half_h_degrees=38,half_v_degrees=16,pitch_degrees=3.5f;std::array<float,3> origin{0,.65f,2.1f};float yaw_sign=1;};
struct HeadlightStyle {
    bool enabled=false,tail=true;unsigned cars=4;float intensity=1.25f,tail_intensity=.85f,tail_brake=1.9f,lamp_emissive=1.35f;
    std::array<float,3> rgb{1.f,.93f,.80f},tail_rgb{1.f,.12f,.06f};
    Projector head{},rear{7.f,62.f,30.f,32.f,{0,.55f,-2.35f},-1};
};
// 6.6 GT3-like lamp glints (sprites at every lit lamp lens).
struct GlintStyle {std::wstring texture;bool enabled=false;float glow_degrees=1.3f,streak_degrees=7.5f,front=.9f,rear=.95f,streak=.6f,brake=1.8f,reverse=.9f;};
inline GlintStyle read_glint_style(const std::wstring& ini,bool night=false){
    GlintStyle s;
    auto number=[&](const wchar_t* key,float fallback,float lo,float hi){wchar_t b[64]{};GetPrivateProfileStringW(L"Atmosphere",key,L"",b,64,ini.c_str());
        wchar_t* end=nullptr;const float v=std::wcstof(b,&end);return end!=b&&*end==0&&std::isfinite(v)?std::clamp(v,lo,hi):fallback;};
    s.enabled=GetPrivateProfileIntW(L"Atmosphere",L"LampGlints",night?1:0,ini.c_str())==1;
    s.glow_degrees=number(L"LampGlintSize",s.glow_degrees,.2f,6);s.streak_degrees=number(L"LampGlintStreak",s.streak_degrees,0,20);
    wchar_t path[512]{};GetPrivateProfileStringW(L"Atmosphere",L"LampGlintTexture",L"",path,512,ini.c_str());
    if(path[0]){std::wstring t(path);if(t.size()<2||(t[1]!=L':'&&t[0]!=L'\\'&&t[0]!=L'/')){const auto slash=ini.find_last_of(L"\\/");t=(slash==std::wstring::npos?std::wstring():ini.substr(0,slash+1))+t;}s.texture=t;}
    const float k=number(L"LampGlintIntensity",1,0,3);s.front*=k;s.rear*=k;s.reverse*=k;s.streak=number(L"LampGlintStreakIntensity",s.streak,0,2);
    return s;
}
// 6.15 lamp rigs: whole lamp units per car in car space, solved offline by tools/atmosphere_lamp_rig.py
// from car.dx ($switch(blight) OFF mesh = brake, lens texels = head/tail/reverse; works for mod cars too).
// A car instance is matched once by one of its lens draws (texture + indexed vertex count + car-space
// bounds within 6 cm); matched cars get exactly the rig's glints, unmatched ones keep the 6.14 path.
struct LampRigPoint {uint8_t kind=0;bool tail=false,dark=false;std::array<float,3> pos{};float size=.2f;};   // kind: 0 head, 1 tail, 2 brake, 3 reverse, 4 fog/aux (front)
struct LampRigDraw {std::string texture;unsigned vertices=0;std::array<float,3> lo{},hi{};};
struct LampRig {std::string car;std::vector<LampRigDraw> draws;std::vector<LampRigPoint> points;};
struct LampRigs {
    std::vector<LampRig> rigs;std::wstring path;bool loaded=false;
    // best rig for one lens draw; -1 = none
    int match(const std::string& texture,unsigned vertices,const std::array<float,3>& lo,const std::array<float,3>& hi)const noexcept{
        int best=-1;float best_score=1e9f;
        for(size_t r=0;r<rigs.size();++r)for(const auto& d:rigs[r].draws){if(d.texture!=texture)continue;float e=0;
            for(unsigned k=0;k<3;++k)e=std::max({e,std::abs(d.lo[k]-lo[k]),std::abs(d.hi[k]-hi[k])});
            if(e>=.06f)continue;const float score=e+(d.vertices==vertices?0.f:.05f);if(score<best_score){best_score=score;best=int(r);}}
        return best;
    }
};
inline LampRigs read_lamp_rigs(const std::wstring& ini){
    LampRigs s;wchar_t path[512]{};GetPrivateProfileStringW(L"Atmosphere",L"LampRigs",L"Atmosphere/vehicles/lamp_rigs.txt",path,512,ini.c_str());
    if(!path[0]||GetPrivateProfileIntW(L"Atmosphere",L"LampRigsEnabled",1,ini.c_str())!=1)return s;
    std::wstring t(path);if(t.size()<2||(t[1]!=L':'&&t[0]!=L'\\'&&t[0]!=L'/')){const auto slash=ini.find_last_of(L"\\/");t=(slash==std::wstring::npos?std::wstring():ini.substr(0,slash+1))+t;}
    s.path=t;std::ifstream in(t);if(!in)return s;std::string line;
    while(std::getline(in,line)){if(line.empty()||line[0]=='#')continue;std::istringstream q(line);std::string tag;q>>tag;
        if(tag=="car"){LampRig r;q>>r.car;s.rigs.push_back(std::move(r));continue;}
        if(s.rigs.empty())continue;auto& r=s.rigs.back();
        if(tag=="draw"){LampRigDraw d;q>>d.texture>>d.vertices>>d.lo[0]>>d.lo[1]>>d.lo[2]>>d.hi[0]>>d.hi[1]>>d.hi[2];if(q)r.draws.push_back(std::move(d));}
        else if(tag=="point"){unsigned kind=0,tail=0,dark=0;LampRigPoint p;q>>kind>>p.pos[0]>>p.pos[1]>>p.pos[2]>>p.size>>tail>>dark;
            if(q&&kind<=4&&std::isfinite(p.pos[0]+p.pos[1]+p.pos[2]+p.size)){p.kind=uint8_t(kind);p.tail=tail!=0;p.dark=dark!=0;r.points.push_back(p);}}}
    s.loaded=!s.rigs.empty();return s;
}
inline HeadlightStyle read_headlight_style(const std::wstring& ini,bool night=false){
    HeadlightStyle s;
    auto number=[&](const wchar_t* key,float fallback,float lo,float hi){wchar_t b[64]{};GetPrivateProfileStringW(L"Atmosphere",key,L"",b,64,ini.c_str());
        wchar_t* end=nullptr;const float v=std::wcstof(b,&end);return end!=b&&*end==0&&std::isfinite(v)?std::clamp(v,lo,hi):fallback;};
    s.enabled=GetPrivateProfileIntW(L"Atmosphere",L"Headlights",night?1:0,ini.c_str())==1;
    s.tail=GetPrivateProfileIntW(L"Atmosphere",L"TailLightGlow",1,ini.c_str())==1;
    s.intensity=number(L"HeadlightIntensity",s.intensity,0,3);s.head.range=number(L"HeadlightRange",s.head.range,5,150);
    s.head.half_h_degrees=number(L"HeadlightSpread",s.head.half_h_degrees,10,70);s.head.half_v_degrees=number(L"HeadlightHeight",s.head.half_v_degrees,5,45);
    s.head.pitch_degrees=number(L"HeadlightPitch",s.head.pitch_degrees,-10,30);
    s.head.origin={number(L"HeadlightX",s.head.origin[0],-3,3),number(L"HeadlightY",s.head.origin[1],-1,3),number(L"HeadlightZ",s.head.origin[2],-5,5)};
    const wchar_t* colour[3]{L"HeadlightR",L"HeadlightG",L"HeadlightB"};for(unsigned i=0;i<3;++i)s.rgb[i]=number(colour[i],s.rgb[i],0,1);
    s.lamp_emissive=number(L"LampEmissive",s.lamp_emissive,0,2);s.cars=unsigned(std::lround(number(L"HeadlightCars",4,1,4)));
    s.tail_intensity=number(L"TailLightIntensity",s.tail_intensity,0,3);s.tail_brake=number(L"TailLightBrake",s.tail_brake,1,5);s.rear.range=number(L"TailLightRange",s.rear.range,1,30);
    return s;
}
// Low beam: wide soft lateral fall-off, bright just below the horizon line,
// a soft cut above it; zero on the border texels (clamp keeps outside dark).
inline float headlight_cookie(float u,float v)noexcept{
    if(u<=0||u>=1||v<=0||v>=1)return 0;
    const float x=u*2-1,y=1-v*2;                                  // y>0 = above the beam axis
    const float lateral=std::exp(-x*x*2.2f);
    const float cut=y>.08f?std::exp(-(y-.08f)*(y-.08f)*60.f):1.f;  // sharp-ish upper cut-off
    const float lower=std::exp(-std::max(0.f,-y-.2f)*std::max(0.f,-y-.2f)*3.f);
    const float hot=1+.6f*std::exp(-(x*x*9+(y+.05f)*(y+.05f)*40));
    const float border=std::clamp((1-std::abs(x))*10,0.f,1.f)*std::clamp((1-std::abs(y))*10,0.f,1.f);
    return std::clamp(lateral*cut*lower*hot*.62f*border,0.f,1.f);
}
// Soft round pool for the tail lamps.
inline float tail_cookie(float u,float v)noexcept{
    if(u<=0||u>=1||v<=0||v>=1)return 0;const float x=u*2-1,y=v*2-1,r2=x*x+y*y;return r2>=1?0:std::pow(1-r2,1.6f);
}
// Distance ramp along the beam, u = distance / range: dark at the lamp glass,
// quick rise, inverse-square-like fall-off, zero at the range.
inline float headlight_ramp(float u)noexcept{
    if(u<=.004f||u>=1)return 0;
    const float rise=std::clamp((u-.004f)/.03f,0.f,1.f),d=u*12;
    return std::clamp(rise*(1/(1+d*d*.35f))*(1-u*u)*1.15f,0.f,1.f);
}
inline Mat4 mat_mul(const Mat4& a,const Mat4& b)noexcept{Mat4 r{};for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j){float s=0;for(unsigned k=0;k<4;++k)s+=a[i*4+k]*b[k*4+j];r[i*4+j]=s;}return r;}
inline bool mat_inverse(const Mat4& m,Mat4& out)noexcept{
    std::array<double,32> a{};for(unsigned i=0;i<4;++i){for(unsigned j=0;j<4;++j)a[i*8+j]=m[i*4+j];a[i*8+4+i]=1;}
    for(unsigned c=0;c<4;++c){unsigned p=c;for(unsigned r=c+1;r<4;++r)if(std::abs(a[r*8+c])>std::abs(a[p*8+c]))p=r;
        if(std::abs(a[p*8+c])<1e-12)return false;if(p!=c)for(unsigned j=0;j<8;++j)std::swap(a[c*8+j],a[p*8+j]);
        const double inv=1/a[c*8+c];for(unsigned j=0;j<8;++j)a[c*8+j]*=inv;
        for(unsigned r=0;r<4;++r)if(r!=c){const double f=a[r*8+c];if(f!=0)for(unsigned j=0;j<8;++j)a[r*8+j]-=f*a[c*8+j];}}
    for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)out[i*4+j]=float(a[i*8+4+j]);
    for(float x:out)if(!std::isfinite(x))return false;return true;
}
inline std::array<float,3> normalized(std::array<float,3> v)noexcept{const float l=std::sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);if(l<1e-6f)return {0,0,0};return {v[0]/l,v[1]/l,v[2]/l};}
inline std::array<float,3> cross3(const std::array<float,3>& a,const std::array<float,3>& b)noexcept{return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
inline float dot3(const std::array<float,3>& a,const std::array<float,3>& b)noexcept{return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
// Projector frame in world space from the car WORLD matrix (rows 0..2 = car
// axes, possibly scaled; +Z forward, +Y up). yaw_sign -1 aims backwards.
struct LightFrame {std::array<float,3> position{},right{},up{},forward{};bool valid=false;};
inline LightFrame light_frame(const Mat4& car,const Projector& p)noexcept{
    LightFrame f;const std::array<float,3> cx=normalized({car[0],car[1],car[2]}),cy=normalized({car[4],car[5],car[6]}),cz=normalized({car[8],car[9],car[10]});
    if(dot3(cx,cx)<.5f||dot3(cy,cy)<.5f||dot3(cz,cz)<.5f)return f;
    for(unsigned i=0;i<3;++i)f.position[i]=p.origin[0]*car[i]+p.origin[1]*car[4+i]+p.origin[2]*car[8+i]+car[12+i];
    const float pitch=p.pitch_degrees*.017453293f;
    for(unsigned i=0;i<3;++i)f.forward[i]=p.yaw_sign*std::cos(pitch)*cz[i]-std::sin(pitch)*cy[i];
    f.forward=normalized(f.forward);f.right=normalized(cross3(cy,f.forward));f.up=cross3(f.forward,f.right);
    f.valid=dot3(f.right,f.right)>.5f;return f;
}
inline Mat4 light_view(const LightFrame& f)noexcept{
    return {f.right[0],f.up[0],f.forward[0],0, f.right[1],f.up[1],f.forward[1],0, f.right[2],f.up[2],f.forward[2],0,
            -dot3(f.position,f.right),-dot3(f.position,f.up),-dot3(f.position,f.forward),1};
}
// Camera space -> projected cookie coordinates (u*w, v*w, w) for COUNT3|PROJECTED.
inline Mat4 cookie_matrix(const Mat4& inverse_view,const LightFrame& f,const Projector& p)noexcept{
    const float th=std::tan(p.half_h_degrees*.017453293f),tv=std::tan(p.half_v_degrees*.017453293f);
    const Mat4 projector{.5f/th,0,0,0, 0,-.5f/tv,0,0, .5f,.5f,1,0, 0,0,0,1};
    return mat_mul(mat_mul(inverse_view,light_view(f)),projector);
}
// Camera space -> (distance along the beam / range, .5) for COUNT2.
inline Mat4 ramp_matrix(const Mat4& inverse_view,const LightFrame& f,const Projector& p)noexcept{
    const Mat4 ramp{0,0,0,0, 0,0,0,0, 1/p.range,0,0,0, 0,.5f,0,1};
    return mat_mul(mat_mul(inverse_view,light_view(f)),ramp);
}
// Sphere (world) against the lamp's reach: in front of the lamp and within range.
inline bool light_reaches(const LightFrame& f,const Projector& p,const std::array<float,3>& centre,float radius)noexcept{
    const std::array<float,3> d{centre[0]-f.position[0],centre[1]-f.position[1],centre[2]-f.position[2]};
    const float along=dot3(d,f.forward);if(along<-radius||along>p.range+radius)return false;
    const float spread=std::tan(std::max(p.half_h_degrees,p.half_v_degrees)*.017453293f)*std::max(0.f,along)+radius;
    const float side=std::sqrt(std::max(0.f,dot3(d,d)-along*along));return side<=spread*1.15f+1;
}
// CPU light of one projector at a world point (same cookie * ramp as the GPU
// pass): proxy-drawn layers (PS2 grass, physics props) add it to vertex colour.
inline float projector_light(const LightFrame& f,const Projector& p,bool head,const std::array<float,3>& point)noexcept{
    const std::array<float,3> d{point[0]-f.position[0],point[1]-f.position[1],point[2]-f.position[2]};
    const float lz=dot3(d,f.forward);if(lz<=.05f||lz>=p.range)return 0;
    const float th=std::tan(p.half_h_degrees*.017453293f),tv=std::tan(p.half_v_degrees*.017453293f);
    const float u=.5f+.5f*dot3(d,f.right)/(lz*th),v=.5f-.5f*dot3(d,f.up)/(lz*tv);
    return (head?headlight_cookie(u,v):tail_cookie(u,v))*headlight_ramp(lz/p.range)*2;
}
} // namespace gfx2::atmosphere
