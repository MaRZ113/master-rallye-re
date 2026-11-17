#pragma once
// RCX-PERF1 course culling (docs/rcx-perf1/README.md).
// Retail courses carry a sector visibility graph (DX tag1500) and hierarchical
// render batches, so the game submits only ~100-200 course draws per frame.
// Course Studio writes the Retail cooker's flat layout: every record of an
// imported course (RCX, Evo 2) is submitted every frame, and each one then pays
// the full per-draw cost of the renderer (Atmosphere relight + ring upload,
// headlight passes, classifiers) and of the GPU.
// The native course draw loop (0x57707e) draws with an identity WORLD, so the
// world-space box of a draw's vertex range is fixed for the life of its buffer.
// A draw whose box lies outside the current VIEW*PROJECTION frustum (or beyond
// MaxDistance) is consumed here without being drawn.
// Pure core below (no Direct3D); the device glue is course_cull_native.hpp.
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <string>
#include <unordered_map>
#include <vector>
#include <windows.h>

namespace gfx2::coursecull {

struct Box {float lo[3]{},hi[3]{};bool valid=false;};
struct Plane {float a=0,b=0,c=0,d=0;};
struct Frustum {std::array<Plane,6> planes{};float eye[3]{};float znear=0,zfar=0;bool valid=false;};

// D3D row vectors: clip = v * (VIEW * PROJECTION).
inline void multiply(const float a[4][4],const float b[4][4],float out[4][4]) noexcept {
    for(int r=0;r<4;++r)for(int c=0;c<4;++c){float s=0;for(int k=0;k<4;++k)s+=a[r][k]*b[k][c];out[r][c]=s;}
}
inline Plane plane(float a,float b,float c,float d) noexcept {
    const float n=std::sqrt(a*a+b*b+c*c);if(!(n>1e-12f))return {0,0,0,1};return {a/n,b/n,c/n,d/n};
}
inline Frustum frustum(const float view[4][4],const float projection[4][4]) noexcept {
    Frustum f{};float m[4][4];multiply(view,projection,m);
    auto col=[&](int j,int r){return m[r][j];};
    auto make=[&](int j,float sign){return plane(col(3,0)+sign*col(j,0),col(3,1)+sign*col(j,1),col(3,2)+sign*col(j,2),col(3,3)+sign*col(j,3));};
    f.planes[0]=make(0,1.f);f.planes[1]=make(0,-1.f);f.planes[2]=make(1,1.f);f.planes[3]=make(1,-1.f);
    f.planes[4]=plane(col(2,0),col(2,1),col(2,2),col(2,3));   // near: z >= 0
    f.planes[5]=make(2,-1.f);                                    // far: z <= w
    // Camera position of an orthonormal VIEW: eye_j = -(t . row_j).
    for(int j=0;j<3;++j)f.eye[j]=-(view[3][0]*view[j][0]+view[3][1]*view[j][1]+view[3][2]*view[j][2]);
    const float p33=projection[2][2],p43=projection[3][2];
    if(std::fabs(p33)>1e-9f){f.znear=-p43/p33;if(std::fabs(p33-1.f)>1e-9f)f.zfar=p33*f.znear/(p33-1.f);}
    f.valid=true;for(const auto& p:f.planes)if(!std::isfinite(p.a)||!std::isfinite(p.b)||!std::isfinite(p.c)||!std::isfinite(p.d))f.valid=false;
    return f;
}
// True when the box lies completely outside one plane (by more than margin) or
// farther than max_distance (0 = no distance limit) from the eye.
inline bool outside(const Frustum& f,const Box& b,float margin,float max_distance) noexcept {
    if(!f.valid||!b.valid)return false;
    for(const auto& p:f.planes){
        const float x=p.a>=0?b.hi[0]:b.lo[0],y=p.b>=0?b.hi[1]:b.lo[1],z=p.c>=0?b.hi[2]:b.lo[2];
        if(p.a*x+p.b*y+p.c*z+p.d<-margin)return true;
    }
    if(max_distance>0){float s=0;for(int i=0;i<3;++i){const float v=f.eye[i]<b.lo[i]?b.lo[i]-f.eye[i]:f.eye[i]>b.hi[i]?f.eye[i]-b.hi[i]:0.f;s+=v*v;}
        if(s>max_distance*max_distance)return true;}
    return false;
}
// Positions are the first 12 bytes of each vertex (FVF XYZ).
inline Box box(const uint8_t* bytes,size_t count,size_t stride) noexcept {
    Box b{};if(!bytes||!count||stride<12)return b;
    for(int i=0;i<3;++i){b.lo[i]=INFINITY;b.hi[i]=-INFINITY;}
    for(size_t v=0;v<count;++v){float p[3];std::memcpy(p,bytes+v*stride,12);
        for(int i=0;i<3;++i){if(!std::isfinite(p[i]))return Box{};if(p[i]<b.lo[i])b.lo[i]=p[i];if(p[i]>b.hi[i])b.hi[i]=p[i];}}
    b.valid=true;return b;
}
// Courses= comma list of RaceTest ids or prefixes ("Rcx,Evo2"); "*" = every course.
inline bool course_listed(const std::string& list,const char* course) noexcept {
    if(!course||!*course)return false;std::string id(course);const auto slash=id.rfind('/');if(slash!=std::string::npos)id=id.substr(slash+1);
    size_t at=0;while(at<=list.size()){size_t end=list.find(',',at);if(end==std::string::npos)end=list.size();
        std::string item=list.substr(at,end-at);while(!item.empty()&&item.front()==' ')item.erase(item.begin());while(!item.empty()&&item.back()==' ')item.pop_back();
        if(item=="*")return true;
        if(!item.empty()&&id.size()>=item.size()&&_strnicmp(id.c_str(),item.c_str(),item.size())==0)return true;
        at=end+1;}
    return false;
}

struct Key {uintptr_t stream=0;uint64_t generation=0;uint32_t first=0,count=0,stride=0;
    bool operator==(const Key& o)const noexcept{return stream==o.stream&&generation==o.generation&&first==o.first&&count==o.count&&stride==o.stride;}};
struct KeyHash {size_t operator()(const Key& k)const noexcept{uint64_t h=k.stream*0x9E3779B97F4A7C15ull;h^=k.generation+0x632BE59BD9B4E019ull+(h<<6)+(h>>2);
    h^=(uint64_t(k.first)<<32|k.count)+(h<<6)+(h>>2);h^=k.stride+(h<<6)+(h>>2);return size_t(h);}};
struct Entry {Box box;uint64_t revision=0;};

struct State {
    bool loaded=false,enabled=true,stats=true,toggle_down=false;std::string courses="Rcx,Evo2";float margin=2.f,max_distance=0.f;
    // Course gate, cached per race generation.
    uint64_t gate_race=UINT64_MAX;bool gate=false;std::string gate_course;
    // Per frame.
    uint64_t frustum_frame=UINT64_MAX;Frustum frust{};
    // The draw decided by observe() and consumed by the ground handler.
    bool pending=false;uint64_t pending_frame=0;uint32_t pending_args[4]{};
    std::unordered_map<Key,Entry,KeyHash> boxes;
    // Counters since the last stats record.
    uint64_t stats_frame=0,considered=0,culled=0,kept_vertices=0,culled_vertices=0,box_builds=0,box_failures=0,revision_rebuilds=0;
    void load() noexcept {
        if(loaded)return;loaded=true;
        wchar_t exe[MAX_PATH]{};if(!GetModuleFileNameW(nullptr,exe,MAX_PATH))return;std::wstring ini(exe);const auto slash=ini.find_last_of(L"\\/");
        ini=(slash==std::wstring::npos?std::wstring():ini.substr(0,slash+1))+L"PS2Port.ini";
        enabled=GetPrivateProfileIntW(L"CourseCull",L"Enabled",1,ini.c_str())==1;
        stats=GetPrivateProfileIntW(L"CourseCull",L"Stats",1,ini.c_str())==1;
        wchar_t text[256]{};GetPrivateProfileStringW(L"CourseCull",L"Courses",L"Rcx,Evo2",text,256,ini.c_str());
        courses.clear();for(const wchar_t* c=text;*c;++c)courses.push_back(*c<128?char(*c):'?');
        margin=float(GetPrivateProfileIntW(L"CourseCull",L"Margin",2,ini.c_str()));if(margin<0)margin=0;
        max_distance=float(GetPrivateProfileIntW(L"CourseCull",L"MaxDistance",0,ini.c_str()));if(max_distance<0)max_distance=0;
    }
    bool take(uint64_t frame,UINT min,UINT vertices,UINT start,UINT count) noexcept {
        if(!pending)return false;pending=false;
        return pending_frame==frame&&pending_args[0]==min&&pending_args[1]==vertices&&pending_args[2]==start&&pending_args[3]==count;
    }
    bool is_pending(uint64_t frame,UINT min,UINT vertices,UINT start,UINT count) const noexcept {
        return pending&&pending_frame==frame&&pending_args[0]==min&&pending_args[1]==vertices&&pending_args[2]==start&&pending_args[3]==count;
    }
};
inline State& state() noexcept {static State s;return s;}

} // namespace gfx2::coursecull
