// COURSE-WATER1 contracts: the portable PS2 water core (ps2_water.hpp) and the asset layout. With
// "--dump <asset> <out> <counter>..." the binary writes, for every asset vertex and every counter, the pass UVs and colours
// that tests/test_ps2_water.py compares bit for bit with tools/ps2_water_model.py.
#include "ps2_water.hpp"
#include "ps2_water_pilot.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace ps2water;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)

namespace {
uint32_t bits(float f){uint32_t b;std::memcpy(&b,&f,4);return b;}
template<class T> void put(std::vector<uint8_t>& o,T v){const auto* p=reinterpret_cast<const uint8_t*>(&v);o.insert(o.end(),p,p+sizeof(T));}

// Synthetic asset: one course, one key with one puddle part (3 vertices), one water part, one waterfall part.
std::vector<uint8_t> synthetic(){
    std::vector<uint8_t> o(kMagic,kMagic+8);
    for(uint32_t v:{kVersion,2u,1u,1u,3u,9u,0u})put(o,v);
    for(int t=0;t<2;++t){put<uint32_t>(o,2);put<uint32_t>(o,2);for(int i=0;i<4;++i)put<uint32_t>(o,0xff000000u|uint32_t(i*40));}
    char id[48]{};std::memcpy(id,"RaceTest/Turkey3",16);o.insert(o.end(),id,id+48);put<uint32_t>(o,0);put<uint32_t>(o,1);put<uint32_t>(o,1);
    put<uint32_t>(o,3);put<uint32_t>(o,1);for(int i=0;i<32;++i)put<uint8_t>(o,uint8_t(i));put<uint32_t>(o,0);put<uint32_t>(o,3);
    const uint32_t modes[3]={kModePuddle,kModeWater,kModeWaterfall};
    for(uint32_t i=0;i<3;++i){put(o,modes[i]);put<uint32_t>(o,0);put<uint32_t>(o,1);put<uint32_t>(o,0);put(o,i*3);put<uint32_t>(o,3);put(o,12.5f);}
    for(int i=0;i<9;++i){
        const float p[3]={100.f+i,20.f,-300.f+2*i},n[3]={0,1,0},uv[2]={.25f*i,.5f};
        for(float c:p)put(o,c);for(float c:n)put(o,c);for(float c:uv)put(o,c);
        for(int k=0;k<4;++k)put<uint8_t>(o,uint8_t(100+i));for(int k=0;k<4;++k)put(o,.1f*k);
    }
    return o;
}

void math(){
    CHECK(bits(circle())==0x40c90fdbu);
    CHECK(table()[0]==0.f);
    CHECK(std::fabs(table()[1024]-1.f)<1e-6f&&std::fabs(table()[3072]+1.f)<1e-6f);
    // EE cvt.w.s rounds toward zero; the masked index wraps negative values.
    CHECK(trunc_index(-0.5f)==0u&&(trunc_index(-1.5f)&0xfffu)==0xfffu&&trunc_index(4097.9f)==4097u);
    // The inline conversion: floor, except normalized negatives in (-1, 0).
    CHECK(inline_int(1.5f)==1&&inline_int(-1.5f)==-2&&inline_int(-0.5f)==0&&inline_int(-1.f)==-1&&inline_int(0.f)==0&&inline_int(7.f)==7);
    CHECK(phase(11056)==11056.f/150.f);
    // Packet colour = byte * 0.5 (128 = 1.0) in D3D bytes.
    CHECK(gs_byte(254)==253&&gs_byte(255)==253&&gs_byte(2)==2&&gs_byte(0)==0);
    // Waterfall: frac(2T) / frac(4T) minus floor(.05 * first Y + 6).
    const auto w=waterfall_v(40.f,12.5f,1.25f);
    CHECK(w.primary==(40.f*.05f+.5f)-6.f&&w.secondary==(40.f*.05f+0.f)-6.f);
    // Water UV has no basis input; puddle with the fixed rows equals the water layout at its own frequencies.
    const float p[3]={10,2,30},n[3]={0,1,0};
    const auto a=puddle_uv(p,n,3.f,kWaterBasis);
    CHECK(std::isfinite(a.u0)&&std::isfinite(a.v1));
    float view[4][4]{{1,0,0,0},{0,1,0,0},{0,0,1,0},{0,0,0,1}};
    const auto b=basis_from_view(view);CHECK(b.m00==1.f&&b.m11==-1.f&&b.m01==-0.f&&b.m21==-0.f);
}
void materials(){
    const auto p0=pass_material(kModePuddle,0),p1=pass_material(kModePuddle,1);
    CHECK(p0.blend==Blend::SourceAlpha&&p0.fog&&p0.z_write&&p0.texture_alpha);
    CHECK(p1.blend==Blend::AddFix56&&!p1.fog&&!p1.z_write&&!p1.texture_alpha);
    const auto w1=pass_material(kModeWater,1);CHECK(w1.blend==Blend::SourceAlpha&&w1.fog&&!w1.z_write&&w1.texture_alpha);
    const auto f1=pass_material(kModeWaterfall,1);CHECK(f1.z_write&&f1.fog);
    CHECK(kPuddleFixFactor>>24==112u);   // 56/128 as a D3D alpha byte
}
void asset_layout(){
    auto bytes=synthetic();Asset a;
    CHECK(decode_asset(bytes.data(),bytes.size(),a));
    CHECK(a.textures.size()==2&&a.courses.size()==1&&a.keys.size()==1&&a.parts.size()==3&&a.vertices.size()==9);
    CHECK(course_index(a,"racetest/turkey3")==0&&course_index(a,"RaceTest\\Turkey3")==0&&course_index(a,"RaceTest/Turkey2")==SIZE_MAX);
    std::vector<PassVertex> f,s;
    for(const auto& part:a.parts){
        CHECK(build_part(a,part,7.25f,kWaterBasis,f,s));CHECK(f.size()==3&&s.size()==3);
        CHECK(f[0].x==s[0].x&&f[0].color==s[0].color);
    }
    // Water parts use the stored static UV; waterfall keeps the authored U in both layers.
    build_part(a,a.parts[1],7.25f,kWaterBasis,f,s);CHECK(f[0].u==0.f&&f[0].v==.1f&&s[0].u==.2f&&s[0].v==.3f);
    build_part(a,a.parts[2],7.25f,kWaterBasis,f,s);CHECK(f[1].u==a.vertices[7].uv[0]&&s[1].u==f[1].u);
    // Rejections: truncation, bad magic, wrong vertex total, trailing bytes.
    Asset b;
    CHECK(!decode_asset(bytes.data(),bytes.size()-1,b));
    auto bad=bytes;bad[0]='X';CHECK(!decode_asset(bad.data(),bad.size(),b));
    bad=bytes;bad.push_back(0);CHECK(!decode_asset(bad.data(),bad.size(),b));
    bad=bytes;bad[8+4*5]=7;CHECK(!decode_asset(bad.data(),bad.size(),b));   // vertex count
}
void geometry_key(){
    // Order-free in triangle order and corner order.
    const float t1[9]={1,2,3,4,5,6,7,8,9},t2[9]={10,11,12,13,14,15,16,17,18};
    float ab[18],ba[18];std::memcpy(ab,t1,36);std::memcpy(ab+9,t2,36);
    const float t2r[9]={16,17,18,10,11,12,13,14,15};std::memcpy(ba,t2r,36);std::memcpy(ba+9,t1,36);
    std::vector<uint8_t> x,y;CHECK(canonical_triangles(ab,2,x)&&canonical_triangles(ba,2,y));CHECK(x==y&&x.size()==72);
}
void phase_clock(){
    Clock c;c.advance(5.0/kCountsPerSecond+1e-9,false);CHECK(c.counter()==5);
    c.advance(0.5,true);CHECK(c.counter()==5);                   // paused: frozen (316808 PauseMenuEnabled)
    c.advance(5.0,false);CHECK(c.counter()==5+7);                // 0.25 s stall clamp (7.5 at 30 per second)
    CHECK(c.t()==phase(12));
}
void transaction_layout(){
    using gfx2::ps2port::kWaterOps;using gfx2::ps2port::WaterStateKind;
    CHECK(kWaterOps[gfx2::ps2port::kWaterStreamOp].kind==WaterStateKind::Stream);
    CHECK(kWaterOps.size()<64);
    CHECK(gfx2::ps2port::water_op(WaterStateKind::Render,0,D3DRS_TEXTUREFACTOR)!=SIZE_MAX);
    CHECK(gfx2::ps2port::water_op(WaterStateKind::Stage,1,D3DTSS_COLOROP)!=SIZE_MAX);
}

int dump(const char* asset_path,const char* out_path,int argc,char** argv){
    std::ifstream f(asset_path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),{});
    Asset a;if(!decode_asset(bytes.data(),bytes.size(),a)){std::cerr<<"asset decode failed\n";return 2;}
    std::ofstream o(out_path,std::ios::binary);
    // A fixed camera basis (unit rows, y down) for the puddle second layer.
    const Basis m{0.75341f,0.19122f,0.00022f,-0.95678f,-0.65726f,0.21924f};
    std::vector<PassVertex> p,s;
    for(int i=0;i<argc;++i){
        const uint32_t counter=static_cast<uint32_t>(std::stoul(argv[i]));
        const float t=phase(counter);
        for(const auto& part:a.parts){
            if(!build_part(a,part,t,m,p,s)){std::cerr<<"build failed\n";return 3;}
            for(size_t k=0;k<p.size();++k){
                const float v[4]={p[k].u,p[k].v,s[k].u,s[k].v};o.write(reinterpret_cast<const char*>(v),16);
                o.write(reinterpret_cast<const char*>(&p[k].color),4);
            }
        }
    }
    return o?0:4;
}
}

int main(int argc,char** argv){
    if(argc>=4&&!std::strcmp(argv[1],"--dump"))return dump(argv[2],argv[3],argc-4,argv+4);
    math();materials();asset_layout();geometry_key();phase_clock();transaction_layout();
    if(failures){std::cerr<<failures<<" failure(s)\n";return 1;}
    std::cout<<"ps2_water_contracts PASS\n";return 0;
}
