// COURSE-ALIVE1 contracts: the portable PS2 spline controller, the asset layout, the per-race runtime and the course
// guard. With "--dump <asset> <ticks> <observers> <out>" the binary also writes every object's state after every
// invocation, which tests/test_spline_objects.py compares bit for bit with ps2-research/tools/spline_runtime.py.
#include "spline_objects.hpp"
#include "provenance.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
using namespace gfx2::ps2port;
using ps2spline::Vec3;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)

namespace {
bool approx(float a,float b,float e=1e-4f){return std::fabs(a-b)<=e;}
bool approx3(const Vec3& a,const Vec3& b,float e=1e-4f){return approx(a[0],b[0],e)&&approx(a[1],b[1],e)&&approx(a[2],b[2],e);}
ps2spline::Config config(bool constant,bool loop){ps2spline::Config c;c.const_speed=constant;c.loop=loop;c.speed=3.f;c.on=200.f;c.off=600.f;c.samples=30;return c;}
const Vec3 kSquare[4]={{0,0,0},{30,0,0},{30,0,40},{0,0,40}};

void basis(){
    // Uniform Catmull-Rom: weights sum to 1, interpolate the knot at u=0.
    for(float u:{0.f,.25f,.5f,.75f,.999f}){const auto w=ps2spline::weights(u);CHECK(approx(w[0]+w[1]+w[2]+w[3],1.f,1e-6f));}
    const auto w=ps2spline::weights(0.f);CHECK(w[0]==0.f&&w[1]==1.f&&w[2]==0.f&&w[3]==0.f);
}
void knots_and_clock(){
    ps2spline::Path p;
    CHECK(p.prepare(kSquare,4,config(true,true)));
    // Chord/speed: 30/3, 40/3, 30/3, closing 40/3.
    CHECK(approx(p.knots()[1],10.f)&&approx(p.knots()[2],10.f+40.f/3.f)&&approx(p.closing_time(),40.f/3.f)&&approx(p.duration(),140.f/3.f));
    for(size_t i=0;i<4;++i)CHECK(approx3(p.evaluate(p.knots()[i]),kSquare[i]));
    CHECK(approx3(p.evaluate(p.duration()),kSquare[0]));              // closed: t == duration wraps to Q(0)
    ps2spline::Path open;CHECK(open.prepare(kSquare,4,config(true,false)));
    CHECK(approx(open.closing_time(),40.f/3.f)&&approx(open.duration(),open.knots()[3]+40.f/3.f)); // open constant keeps the closing time
    CHECK(approx3(open.evaluate(open.duration()),kSquare[3]));        // ...but its position clamps at the last marker
    ps2spline::Path equal;CHECK(equal.prepare(kSquare,4,config(false,true)));
    CHECK(approx(equal.knots()[1],(140.f/3.f)/4.f)&&approx(equal.closing_time(),equal.knots()[1])); // (L/speed)/N per span
    ps2spline::Path open_equal;CHECK(open_equal.prepare(kSquare,4,config(false,false)));
    CHECK(open_equal.closing_time()==0.f&&approx(open_equal.knots()[1],(100.f/3.f)/4.f));      // open: L without closing chord
    // Contract rejections (no guessed repair).
    const Vec3 repeated[4]={{0,0,0},{0,0,0},{1,0,0},{2,0,0}};CHECK(!p.prepare(repeated,4,config(true,true)));
    CHECK(!p.prepare(kSquare,3,config(true,true)));
    auto slow=config(true,true);slow.speed=0.f;CHECK(!p.prepare(kSquare,4,slow));
    const Vec3 bad[4]={{0,0,0},{1,0,0},{std::numeric_limits<float>::quiet_NaN(),0,0},{2,0,0}};CHECK(!p.prepare(bad,4,config(true,true)));
    ps2spline::SplineClock clock;unsigned total=0;for(int i=0;i<100;++i)total+=clock.advance(1.0/144.0);
    CHECK(total==20);                                                // 100/144 s at 30 Hz = 20.8 invocations
    CHECK(clock.advance(10.0)==8);                                   // a stall is clamped to 0.25 s (7.5 + carried .83)
    CHECK(clock.advance(-1.0)==0&&clock.advance(0.0)==0);
}
void controller(){
    ps2spline::Controller c;CHECK(c.initialize(kSquare,4,config(true,true)));
    auto pose=c.pose();CHECK(approx3(pose.position,kSquare[0])&&c.active()&&c.time()==0.f);
    // Right is (F.z, F.y, -F.x), not a cross product.
    CHECK(pose.right[0]==pose.forward[2]&&pose.right[1]==pose.forward[1]&&pose.right[2]==-pose.forward[0]);
    CHECK(pose.up[0]==0.f&&pose.up[1]==1.f&&pose.up[2]==0.f);
    const Vec3 distant{1e5f,0,1e5f};
    CHECK(c.tick(nullptr)==ps2spline::TickStatus::NoObserver&&c.time()==0.f);   // no Car0 payload: nothing moves
    CHECK(c.tick(&distant)==ps2spline::TickStatus::Active&&approx(c.time(),1.f/30.f)); // trigger off: distance ignored
    for(int i=0;i<10000;++i)c.tick(&distant);
    CHECK(c.time()>=0.f&&c.time()<=c.path().duration());                         // closed wrap resets to 0
    // Trigger hysteresis: strict, squared, XZ only.
    auto t=config(true,true);t.trigger=true;t.on=10.f;t.off=20.f;
    ps2spline::Controller k;CHECK(k.initialize(kSquare,4,t)&&!k.active());
    const Vec3 at_on{10.f,999.f,0.f};CHECK(k.tick(&at_on)==ps2spline::TickStatus::Inactive); // equality keeps the state
    const Vec3 inside{9.f,-50.f,0.f};CHECK(k.tick(&inside)==ps2spline::TickStatus::Active);
    const float frozen=k.time();
    const Vec3 between{15.f,0.f,0.f};CHECK(k.tick(&between)==ps2spline::TickStatus::Active);
    const Vec3 outside{100.f,0.f,100.f};CHECK(k.tick(&outside)==ps2spline::TickStatus::Inactive&&k.time()>frozen);
    const float held=k.time();k.tick(&outside);CHECK(k.time()==held);           // frozen while inactive, resumes later
    // Open route with rest: endpoint, then rest_ticks overflow invocations, then restart.
    auto r=config(true,false);r.rest=true;r.rest_ticks=3;
    ps2spline::Controller o;CHECK(o.initialize(kSquare,4,r));
    unsigned guard=0;while(o.time()!=o.path().duration()&&guard<100000){o.tick(&distant);++guard;}
    CHECK(o.time()==o.path().duration()&&o.rest_counter()==1);      // the first overflow already counts
    o.tick(&distant);o.tick(&distant);CHECK(o.rest_counter()==3&&o.time()==o.path().duration());
    o.tick(&distant);CHECK(o.time()==0.f&&o.rest_counter()==0);
    // Open route without rest stays at the last marker.
    ps2spline::Controller s;CHECK(s.initialize(kSquare,4,config(true,false)));
    for(int i=0;i<5000;++i)s.tick(&distant);CHECK(approx3(s.pose().position,kSquare[3])&&s.time()==s.path().duration());
    // Banking moves only up and keeps the moving average bounded.
    auto b=config(false,true);b.banking=1.f;b.samples=4;
    ps2spline::Controller bank;CHECK(bank.initialize(kSquare,4,b));
    bool tilted=false;for(int i=0;i<600;++i){bank.tick(&distant);const auto q=bank.pose();
        tilted|=std::fabs(q.up[1]-1.f)>1e-3f;CHECK(q.right[0]==q.forward[2]&&q.right[2]==-q.forward[0]);}
    CHECK(tilted&&std::isfinite(bank.bank_mean()));
}

// Little synthetic asset in the PS2SPL01 layout: one 2x2 texture, one model (one triangle), one course, one object.
std::vector<uint8_t> synthetic(){
    std::vector<uint8_t> b;auto put=[&](const void* p,size_t n){const auto* c=static_cast<const uint8_t*>(p);b.insert(b.end(),c,c+n);};
    auto u32=[&](uint32_t v){put(&v,4);};auto f32=[&](float v){put(&v,4);};
    auto text=[&](const char* s,size_t n){std::vector<char> z(n,0);std::memcpy(z.data(),s,std::strlen(s));put(z.data(),n);};
    put("PS2SPL01",8);u32(1);u32(1);u32(1);u32(3);u32(1);u32(1);
    u32(2);u32(2);for(int i=0;i<4;++i)u32(0xff808080u);
    text("tri",16);u32(1);u32(0);u32(0);u32(3);u32(0);u32(0);u32(0);f32(1.5f);
    const ObjectVertex v[3]={{0,0,1,0xffffffffu,0,0},{1,0,0,0xffffffffu,1,0},{0,1,0,0xffffffffu,0,1}};put(v,sizeof(v));
    text("RaceTest/Synth",48);text("DataGx/Course/Synth/synth.dx",64);for(int i=0;i<32;++i)b.push_back(uint8_t(i));u32(0);u32(1);
    text("boat",32);u32(0);u32(0);u32(4);b.push_back(1);b.push_back(1);b.push_back(0);b.push_back(0);
    f32(3.f);f32(200.f);f32(600.f);f32(0.f);int32_t z=0,s=30;put(&z,4);put(&s,4);
    for(const auto& p:kSquare){f32(p[0]);f32(p[1]);f32(p[2]);}
    return b;
}
void asset_and_runtime(){
    auto bytes=synthetic();SplineObjectsAsset a;
    CHECK(decode_spline_objects_layout(bytes.data(),bytes.size(),a));
    CHECK(a.courses.size()==1&&a.objects.size()==1&&a.models[0].name=="tri"&&a.points.size()==4);
    CHECK(!decode_spline_objects_asset(bytes.data(),bytes.size(),"0000",a));            // runtime needs the pinned digest
    for(size_t cut:{size_t(0),size_t(8),bytes.size()-1}){std::vector<uint8_t> t(bytes.begin(),bytes.begin()+cut);SplineObjectsAsset x;CHECK(!decode_spline_objects_layout(t.data(),t.size(),x));}
    {auto t=bytes;t.push_back(0);SplineObjectsAsset x;CHECK(!decode_spline_objects_layout(t.data(),t.size(),x));}
    {auto t=bytes;t[12]=2;SplineObjectsAsset x;CHECK(!decode_spline_objects_layout(t.data(),t.size(),x));}       // texture count
    CHECK(decode_spline_objects_layout(bytes.data(),bytes.size(),a));
    CHECK(spline_course_index(a,"racetest/SYNTH")==0&&spline_course_index(a,"RaceTest/Synth2")==SIZE_MAX);
    // Course guard: only a loose course DX that is not the retail PC file is a PS2 package.
    std::string retail;for(int i=0;i<32;++i){char h[3];std::snprintf(h,3,"%02x",i);retail+=h;}
    CHECK(!std::strcmp(spline_course_guard(a.courses[0].retail_sha,false,""),"stock_pc_course_no_loose_course_dx"));
    CHECK(!std::strcmp(spline_course_guard(a.courses[0].retail_sha,true,retail),"stock_pc_course_retail_dx"));
    CHECK(!std::strcmp(spline_course_guard(a.courses[0].retail_sha,true,std::string(64,'f')),"ps2_course_package"));
    CHECK(!std::strcmp(spline_course_guard(a.courses[0].retail_sha,true,""),"course_dx_unreadable"));
    // Runtime: start, pause, restart on a new race generation, world vertices from the published pose.
    SplineCourseRuntime rt;CHECK(!rt.start(a,0,0)&&!rt.start(a,5,1));
    CHECK(rt.start(a,0,7)&&rt.ready()&&rt.race()==7);
    const Vec3 car{1e4f,0,1e4f};
    CHECK(rt.advance(1.0,true,&car)==0&&rt.ticks()==0);                                   // paused
    CHECK(rt.advance(.1,false,&car)==3&&rt.ticks()==3);                                  // 0.1 s at 30 Hz
    std::vector<SplineBatch> batches;CHECK(rt.build(batches)&&batches.size()==1&&batches[0].vertices.size()==3);
    const auto pose=rt.controllers()[0].pose();const auto w=ps2spline::transform(pose,{0,0,1});
    CHECK(batches[0].vertices[0].x==w[0]&&batches[0].vertices[0].y==w[1]&&batches[0].vertices[0].z==w[2]);
    CHECK(rt.start(a,0,8)&&rt.ticks()==0&&rt.controllers()[0].time()==0.f);              // re-initialised, not resumed
    rt.stop();CHECK(!rt.ready()&&!rt.build(batches)&&batches.empty());
}

// ---- dump for the bit comparison with spline_runtime.py
struct Row {uint8_t status,active,pad[2];float time,pos[3],fwd[3],up[3],bank;int32_t rest,ring;};
static_assert(sizeof(Row)==56);
int dump(const char* asset_path,unsigned ticks,const char* observers_path,const char* out_path){
    std::ifstream in(asset_path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(in)),{});
    SplineObjectsAsset a;
    if(!decode_spline_objects_asset(bytes.data(),bytes.size(),gfx2::sha256_bytes(bytes.data(),bytes.size()),a)){std::cerr<<"asset rejected\n";return 2;}
    // observers: per course, ticks x (x,y,z); NaN x = no Car0 payload.
    std::ifstream ob(observers_path,std::ios::binary);std::vector<float> obs((a.courses.size())*ticks*3);
    ob.read(reinterpret_cast<char*>(obs.data()),std::streamsize(obs.size()*4));if(!ob){std::cerr<<"observers short\n";return 3;}
    std::ofstream out(out_path,std::ios::binary);
    for(size_t c=0;c<a.courses.size();++c){
        SplineCourseRuntime rt;if(!rt.start(a,c,c+1)){std::cerr<<"start "<<a.courses[c].id<<"\n";return 4;}
        std::vector<ps2spline::Controller> ks=rt.controllers();
        for(unsigned t=0;t<ticks;++t){
            const float* o=obs.data()+(c*ticks+t)*3;const Vec3 v{o[0],o[1],o[2]};
            for(auto& k:ks){Row r{};r.status=uint8_t(k.tick(std::isnan(o[0])?nullptr:&v));r.active=k.active();
                const auto p=k.pose();r.time=k.time();std::memcpy(r.pos,p.position.data(),12);std::memcpy(r.fwd,p.forward.data(),12);
                std::memcpy(r.up,p.up.data(),12);r.bank=k.bank_mean();r.rest=k.rest_counter();r.ring=k.ring_index();
                out.write(reinterpret_cast<const char*>(&r),sizeof(r));}
        }
    }
    return out?0:5;
}
} // namespace

int main(int argc,char** argv){
    if(argc==6&&!std::strcmp(argv[1],"--dump"))return dump(argv[2],static_cast<unsigned>(std::strtoul(argv[3],nullptr,10)),argv[4],argv[5]);
    basis();knots_and_clock();controller();asset_and_runtime();
    if(failures){std::cerr<<failures<<" failures\n";return 1;}
    std::cout<<"spline objects contracts passed\n";return 0;
}
