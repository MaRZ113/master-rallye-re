// COURSE-ALIVE2 contracts: the portable PS2 BirdManager (ps2_birds.hpp), the asset layout and the render geometry.
// "--dump <asset> <ticks> <cameras> <out>" runs every course of the asset over a fixed camera path and writes the full
// manager state after every tick; tools/verify_ps2_birds.py compares it bit for bit with tools/ps2_bird_model.py.
#include "ps2_birds_pilot.hpp"
#include "provenance.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
using namespace gfx2::ps2port;
using ps2birds::Vec3;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)

namespace {
void rng(){
    // Schrage form == 48271*s mod (2^31-1) for positive states; output = low 24 bits * 2^-24.
    ps2birds::Rng r(12345);uint64_t s=12345;
    for(int i=0;i<100000;++i){const float u=r.unit();s=(s*48271u)%2147483647u;CHECK(r.state()==s);
        CHECK(u==static_cast<float>(s&0xffffffu)*(1.f/16777216.f));if(failures)return;}
    ps2birds::Rng q(7);for(int i=0;i<1000;++i){const int v=q.integer(0,3);CHECK(v>=0&&v<3);}
    ps2birds::Rng z(9);CHECK(z.integer(0,0)==0);
}
void switcher(){
    ps2birds::BankSwitcher s;int keys[16];for(int i=0;i<16;++i){s.step();keys[i]=s.key;}
    // fresh counter 0: the key changes on the 5th tick, then every 5 ticks, 0 -> 1 -> 2 -> 0
    const int expect[16]={0,0,0,0,1,1,1,1,1,2,2,2,2,2,0,0};for(int i=0;i<16;++i)CHECK(keys[i]==expect[i]);
}
ps2birds::CourseConfig course(bool mill=true){
    ps2birds::CourseConfig c;c.flight={{0,10,0},{200,10,0},{400,10,0},{600,10,0}};c.flight_present=true;c.mill_present=mill;
    c.min_fly=100.f;c.max_fly=900.f;c.rnd_fly=10;return c;
}
void manager(){
    ps2birds::Manager m;CHECK(m.start(course(false)));
    const Vec3 cam{-300,20,0};
    for(int i=0;i<20000;++i)m.tick(cam);
    CHECK(m.flying_count()==0&&m.pending_count()==0&&m.free_count()==ps2birds::kPool&&m.rng().state()==ps2birds::kSeed); // gate closed: nothing
    CHECK(m.start(course(false),true));for(int i=0;i<4000;++i)m.tick(cam);CHECK(m.flying_count()>0);                     // diagnostic only
    CHECK(m.start(course()));
    size_t seen=0,max_flying=0;uint64_t first=0;std::vector<ps2birds::BirdView> v;
    for(int i=0;i<20000;++i){
        m.tick(cam);
        if(m.flying_count()&&!first)first=m.ticks();
        if(m.flying_count()>max_flying)max_flying=m.flying_count();
        CHECK(m.flying_count()+m.pending_count()+m.free_count()==ps2birds::kPool);
        m.snapshot(v);for(const auto& b:v){CHECK(b.key>=0&&b.key<=2);++seen;
            const float dx=b.position[0]-cam[0],dz=b.position[2]-cam[2];CHECK(dx*dx+dz*dz<=900.f*900.f*1.01f+50000.f);}
        if(failures)return;
    }
    // The burst probability needs clock*0.1 > 0.1: no burst in the first 333 ticks (11 s at 30 Hz).
    CHECK(first>333&&seen>0&&max_flying<=ps2birds::kPool);
    // Restart: identical state, identical timeline.
    ps2birds::Manager a,b;CHECK(a.start(course())&&b.start(course()));
    for(int i=0;i<3000;++i){a.tick(cam);b.tick(cam);}
    CHECK(a.rng().state()==b.rng().state()&&a.flying_count()==b.flying_count());
}
void flybird(){
    ps2birds::Rng r(4242);ps2birds::FlyBird f;f.origin={10,0,10};f.initialize({0,0,0},r);
    CHECK(f.direction[1]>0.f&&f.speed>=15.f&&f.speed<=30.f);
    // Mostly away from the observer in X/Z.
    CHECK(f.direction[0]>0.f&&f.direction[2]>0.f);
    float last_y=f.direction[1];for(int i=0;i<3000;++i){f.step(r);CHECK(f.direction[1]>=last_y);last_y=f.direction[1];}
    CHECK(f.direction[1]<.35f+.05f/30.f+1e-6f);  // rise stops at 0.35 (+ one step)
}
void ambient2_trace(){
    // AMBIENT2 committed synthetic trace (ambient2/synthetic-flight-trace.json): origin (0,10,0), observer (100,10,0), seed 12345.
    ps2birds::Rng r(12345);ps2birds::FlyBird f;f.origin={0.f,10.f,0.f};f.initialize({100.f,10.f,0.f},r);
    CHECK(f.speed==22.7810307f&&f.unused24==47.5096893f);
    CHECK(f.direction[0]==-0.997333348f&&f.direction[1]==0.0410173796f&&f.direction[2]==-0.0603627078f);
    ps2birds::BankSwitcher s;Vec3 p{};
    for(int i=0;i<15;++i){p=f.step(r);s.step();}
    CHECK(p[0]==-11.5821686f&&p[1]==10.6333427f&&p[2]==-0.701000392f);
    CHECK(f.travel==11.6131372f&&r.state()==1911361012u&&s.key==0);
}
void geometry(){
    // Level camera looking along +z: side = look x up = (0,0,1)x(0,1,0) = (-1,0,0); F = (side.z, 0, look.z) = (0,0,1).
    const Vec3 look{0,0,1},up{0,1,0};const auto s=ps2birds::camera_side(look,up);CHECK(s[0]==-1.f&&s[1]==0.f&&s[2]==0.f);
    const auto bb=ps2birds::billboard(s,look);CHECK(bb.r[0]==.1f&&bb.r[2]==-0.f&&bb.u[1]==.1f);
    const auto w=ps2birds::world_vertex({1,2,3},bb,8.f,-3.f);CHECK(w[0]==1.f+7.5f*.1f&&w[1]==2.f+3.5f*.1f&&w[2]==3.f);
    // Vertical camera fallback: F.x = 1.
    const auto v=ps2birds::billboard({0,0,0},{0,-1,0});CHECK(v.r[2]==-.1f&&v.r[0]==0.f);
    // D3D view of a camera at (5,6,7) looking along +x (look at): position/look/up recovered.
    D3DMATRIX m{};m._11=0;m._21=0;m._31=-1;m._12=0;m._22=1;m._32=0;m._13=1;m._23=0;m._33=0;
    m._41=-(5*m._11+6*m._21+7*m._31);m._42=-(5*m._12+6*m._22+7*m._32);m._43=-(5*m._13+6*m._23+7*m._33);m._44=1;
    Vec3 p{},l{},u{};CHECK(birds_camera(m,p,l,u));CHECK(p[0]==5.f&&p[1]==6.f&&p[2]==7.f&&l[0]==1.f&&u[1]==1.f);
    m._11=std::numeric_limits<float>::quiet_NaN();CHECK(!birds_camera(m,p,l,u));
}
std::vector<uint8_t> load(const char* path){std::ifstream in(path,std::ios::binary);return std::vector<uint8_t>((std::istreambuf_iterator<char>(in)),{});}
void asset_layout(const char* path){
    if(!path)return;
    auto bytes=load(path);BirdsAsset a;
    CHECK(decode_birds_asset(bytes.data(),bytes.size(),gfx2::sha256_bytes(bytes.data(),bytes.size()),a));
    CHECK(a.courses.size()==36);
    size_t open=0;for(const auto& c:a.courses)open+=c.flight_present&&c.mill_present;CHECK(open==10);
    CHECK(!decode_birds_asset(bytes.data(),bytes.size(),"0",a));
    auto cut=bytes;cut.pop_back();BirdsAsset b;CHECK(!decode_birds_layout(cut.data(),cut.size(),b));
    auto alpha=bytes;alpha[24+3]=0x7f;CHECK(!decode_birds_layout(alpha.data(),alpha.size(),b));   // non-binary alpha refused
}

// ---- dump
#pragma pack(push,1)
struct EntityRow {uint8_t flying;int8_t key;uint8_t pad[2];float en2d[3],carrier[3];};
struct TickRow {uint32_t rng;float clock;uint8_t free,pending,flying,pad;int32_t cache;EntityRow e[ps2birds::kPool];};
#pragma pack(pop)
int dump(const char* asset_path,unsigned ticks,const char* cameras_path,const char* out_path){
    auto bytes=load(asset_path);BirdsAsset a;
    if(!decode_birds_asset(bytes.data(),bytes.size(),gfx2::sha256_bytes(bytes.data(),bytes.size()),a)){std::cerr<<"asset rejected\n";return 2;}
    // cameras: per course, per tick: position, look, up (9 floats)
    auto cams=load(cameras_path);if(cams.size()!=a.courses.size()*size_t(ticks)*36){std::cerr<<"camera file size\n";return 3;}
    std::ofstream out(out_path,std::ios::binary);std::vector<ps2birds::BirdView> v;std::vector<BirdBatch> batches;
    for(size_t c=0;c<a.courses.size();++c){
        ps2birds::Manager m;if(!m.start(birds_course_config(a,c))){std::cerr<<"start\n";return 4;}
        for(unsigned t=0;t<ticks;++t){
            float f[9];std::memcpy(f,cams.data()+(c*ticks+t)*36,36);
            m.tick({f[0],f[1],f[2]});
            TickRow r{};r.rng=m.rng().state();r.clock=m.clock();r.free=uint8_t(m.free_count());r.pending=uint8_t(m.pending_count());
            r.flying=uint8_t(m.flying_count());r.cache=m.cache();
            for(size_t i=0;i<ps2birds::kPool;++i){const auto& e=m.entity(i);r.e[i].flying=e.flying;r.e[i].key=int8_t(e.sw.key);
                std::memcpy(r.e[i].en2d,e.en2d.data(),12);std::memcpy(r.e[i].carrier,e.carrier.data(),12);}
            out.write(reinterpret_cast<const char*>(&r),sizeof(r));
            m.snapshot(v);
            if(!birds_build(a,v,{f[3],f[4],f[5]},{f[6],f[7],f[8]},batches)){std::cerr<<"build\n";return 5;}
            // world vertices in snapshot order (entity order), 6 per bird, xyz only
            for(const auto& b:v){const auto& fr=a.frames[size_t(b.key)];
                const auto side=ps2birds::camera_side({f[3],f[4],f[5]},{f[6],f[7],f[8]});const auto bb=ps2birds::billboard(side,{f[3],f[4],f[5]});
                for(const auto& tr:fr.tri)for(int i=0;i<3;++i){const auto w=ps2birds::world_vertex(b.position,bb,tr.xy[i*2],tr.xy[i*2+1]);
                    out.write(reinterpret_cast<const char*>(w.data()),12);}}
        }
    }
    return out?0:6;
}
} // namespace

int main(int argc,char** argv){
    if(argc==6&&!std::strcmp(argv[1],"--dump"))return dump(argv[2],static_cast<unsigned>(std::strtoul(argv[3],nullptr,10)),argv[4],argv[5]);
    rng();switcher();manager();flybird();ambient2_trace();geometry();asset_layout(argc==2?argv[1]:std::getenv("MRR_PS2_BIRDS_TEST_ASSET"));
    if(failures){std::cerr<<failures<<" failures\n";return 1;}
    std::cout<<"ps2 birds contracts passed\n";return 0;
}
