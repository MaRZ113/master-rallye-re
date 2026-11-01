// COLLISION-DEBUG1 contracts: the portable course collision core (collision_debug.hpp): tag1400 parse of course DX bytes
// (including a false 1339/1400 candidate), the CourseCollision.mrcoll asset layout, surface names, modes, the overlay
// geometry and the legend font.
// "--dump <course.dx> <out>" and "--dump-asset <asset> <out>" write one digest line per course for
// tools/prepare_collision_debug.py --verify (C++ parse == loader-guided Python parse on the retail corpus).
#include "collision_debug.hpp"
#include "retail_layout.hpp"
#include "sma_archive.hpp"
#include <chrono>
#include <limits>
#include <filesystem>
#include <cstdlib>
#include <iterator>
#include "provenance.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace gfx2::colldebug;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)

namespace {
void put32(std::vector<uint8_t>& b,uint32_t v){for(int i=0;i<4;++i)b.push_back(static_cast<uint8_t>(v>>(i*8)));}
void putf(std::vector<uint8_t>& b,float f){uint32_t v;std::memcpy(&v,&f,4);put32(b,v);}
void put16(std::vector<uint8_t>& b,uint16_t v){b.push_back(static_cast<uint8_t>(v));b.push_back(static_cast<uint8_t>(v>>8));}
struct Tri{float v[9];uint32_t mat;};
// Plane of the retail convention: n = normalize(cross(v1-v0,v2-v0)), d = -n.v0.
void plane(const float* v,float* n){
    const float a[3]={v[3]-v[0],v[4]-v[1],v[5]-v[2]},b[3]={v[6]-v[0],v[7]-v[1],v[8]-v[2]};
    float c[3]={a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};
    const float l=std::sqrt(c[0]*c[0]+c[1]*c[1]+c[2]*c[2]);for(float& x:c)x/=l;
    n[0]=c[0];n[1]=c[1];n[2]=c[2];n[3]=-(c[0]*v[0]+c[1]*v[1]+c[2]*v[2]);
}
std::vector<uint8_t> tag1400(const std::vector<Tri>& tris,const std::vector<std::string>& mats){
    std::vector<uint8_t> b;put32(b,1400);putf(b,20.f);put32(b,2);put32(b,1);
    for(float f:{-10.f,-1.f,-10.f})putf(b,f);for(float f:{30.f,5.f,10.f})putf(b,f);
    put32(b,static_cast<uint32_t>(tris.size()));for(uint32_t i=0;i<tris.size();++i)put32(b,i);put32(b,0);
    put32(b,static_cast<uint32_t>(mats.size()));for(const auto& m:mats){put32(b,static_cast<uint32_t>(m.size()));b.insert(b.end(),m.begin(),m.end());}
    put32(b,static_cast<uint32_t>(tris.size()));
    for(const auto& t:tris){for(float f:t.v)putf(b,f);put32(b,t.mat);float n[4];plane(t.v,n);for(float f:n)putf(b,f);}
    put32(b,1500);putf(b,0.f);
    return b;
}
// Two ground triangles (a quad, wound so n points down like retail ground) and one wall.
std::vector<Tri> sample(){
    return {{{0,0,0, 10,0,0, 0,0,10},0},{{10,0,0, 10,0,10, 0,0,10},1},{{20,0,0, 20,5,0, 20,0,5},2}};
}
const std::vector<std::string> kMats={"$surfacetype(gravel) $shader(ground)Noise Pass","$surfacetype(TARMAC) $shader(ground)","walls $shader(object) $mip(1.0)"};

void parse(){
    const auto tris=sample();
    std::vector<uint8_t> dx(1000,0xcd);
    // false candidate: 1339 then 1400 44 bytes later, with an impossible header
    put32(dx,1339);for(int i=0;i<40;++i)dx.push_back(0);put32(dx,1400);putf(dx,1e-42f);put32(dx,9999);put32(dx,71);
    for(int i=0;i<200;++i)dx.push_back(0x11);
    const size_t real=dx.size()+44;
    put32(dx,1339);for(int i=0;i<40;++i)dx.push_back(0);
    const auto t=tag1400(tris,kMats);dx.insert(dx.end(),t.begin(),t.end());
    Mesh m;size_t at=0;
    CHECK(parse_course_dx(dx.data(),dx.size(),m,&at)==ParseResult::Ok);
    CHECK(at==real);
    CHECK(m.triangles()==3);CHECK(m.positions.size()==3*7);   // 9 corners, 2 shared by the quad
    CHECK(m.edges.size()==3*8);                                 // quad 5 edges + wall 3
    CHECK(m.materials.size()==3&&m.material_surface[0]==Surface::Gravel&&m.material_surface[1]==Surface::Tarmac&&m.material_surface[2]==Surface::Unknown);
    CHECK(m.planes[1]<-0.99f);                                  // ground plane points down
    CHECK(m.cell==20.f&&m.dim0==2&&m.dim1==1);
    // the same section twice is ambiguous
    auto twice=dx;twice.insert(twice.end(),dx.begin()+static_cast<long>(real-44),dx.end());
    CHECK(parse_course_dx(twice.data(),twice.size(),m)==ParseResult::Ambiguous);
    // a broken plane, a string index out of range, a missing tag1500 all reject
    size_t records=real+40+20+4;for(const auto& s:kMats)records+=4+s.size();records+=4;
    auto bad=dx;bad[records+7]^=0x40; // first record, v0.y off the stored plane
    CHECK(parse_course_dx(bad.data(),bad.size(),m)==ParseResult::NoCandidate);
    // cooked new courses (invspaingx.dx) end the file right after the last record: valid; a torn tail is not
    auto eof=dx;eof.resize(eof.size()-8);CHECK(parse_course_dx(eof.data(),eof.size(),m)==ParseResult::Ok&&m.triangles()==3);
    auto cut=dx;cut.resize(cut.size()-6);CHECK(parse_course_dx(cut.data(),cut.size(),m)==ParseResult::NoCandidate);
}
std::vector<uint8_t> asset_of(const Mesh& m){
    std::vector<uint8_t> blob;putf(blob,m.cell);put32(blob,m.dim0);put32(blob,m.dim1);for(float f:m.min)putf(blob,f);for(float f:m.max)putf(blob,f);
    put32(blob,static_cast<uint32_t>(m.materials.size()));for(const auto& s:m.materials){put16(blob,static_cast<uint16_t>(s.size()));blob.insert(blob.end(),s.begin(),s.end());}
    put32(blob,static_cast<uint32_t>(m.positions.size()/3));for(float f:m.positions)putf(blob,f);
    put32(blob,static_cast<uint32_t>(m.triangles()));for(uint32_t i:m.indices)put32(blob,i);for(uint16_t i:m.material)put16(blob,i);for(float f:m.planes)putf(blob,f);
    std::vector<uint8_t> a(kAssetMagic,kAssetMagic+8);put32(a,1);put32(a,1);
    std::vector<uint8_t> e(160,0);const char id[]="RaceTest/Sample",path[]="DataGx/Course/Sample/sample.dx";
    std::memcpy(e.data(),id,sizeof(id)-1);std::memcpy(e.data()+48,path,sizeof(path)-1);
    const uint32_t off=16+160,size=static_cast<uint32_t>(blob.size());std::memcpy(e.data()+144,&off,4);std::memcpy(e.data()+148,&size,4);
    a.insert(a.end(),e.begin(),e.end());a.insert(a.end(),blob.begin(),blob.end());return a;
}
void asset(){
    const auto tris=sample();std::vector<uint8_t> dx;put32(dx,1339);for(int i=0;i<40;++i)dx.push_back(0);
    const auto t=tag1400(tris,kMats);dx.insert(dx.end(),t.begin(),t.end());
    Mesh m;CHECK(parse_course_dx(dx.data(),dx.size(),m)==ParseResult::Ok);
    const auto a=asset_of(m);std::vector<AssetEntry> index;
    CHECK(decode_asset_index(a.data(),a.size(),index)&&index.size()==1&&index[0].race_id=="RaceTest/Sample");
    Mesh back;CHECK(!index.empty()&&decode_asset_mesh(a.data(),a.size(),index[0],back));
    CHECK(back.positions==m.positions&&back.indices==m.indices&&back.material==m.material&&back.planes==m.planes&&back.edges==m.edges);
    auto broken=a;broken[16+160+36+4+2]^=1;   // material name byte: still valid
    CHECK(decode_asset_mesh(broken.data(),broken.size(),index[0],back));
    broken=a;broken.back()^=0x7f;               // last plane float
    CHECK(!decode_asset_mesh(broken.data(),broken.size(),index[0],back));
    auto shorter=a;shorter.resize(a.size()-1);CHECK(!decode_asset_index(shorter.data(),shorter.size(),index));
}
void modes(){
    CHECK(next_mode(Mode::Off,false)==Mode::Surface);CHECK(next_mode(Mode::Off,true)==Mode::Objects);CHECK(next_mode(Mode::Solid,false)==Mode::Objects);CHECK(next_mode(Mode::Objects,false)==Mode::Off);
    Mode m{};CHECK(parse_mode("x-ray",m)&&m==Mode::XRay);CHECK(parse_mode("6",m)&&m==Mode::Solid);CHECK(parse_mode("objects",m)&&m==Mode::Objects);CHECK(!parse_mode("8",m));CHECK(!parse_mode("bogus",m));
    std::string type;CHECK(classify_surface("water $surfacetype(water) $shader(puddle)",&type)==Surface::Water&&type=="water");
    CHECK(classify_surface("$surfacetype(snow)")==Surface::Other);CHECK(classify_surface("roof $shader(object)")==Surface::Unknown);
    CHECK(landscape_dx_path("<Value Name=\"en3d Model Name\" Type=\"String\" Value=\"course\\france_m\\francem\" />")=="DataGx/Course/france_m/francem.dx");
    CHECK(landscape_dx_path("misc\\course\\x").empty());
    CHECK(landscape_dx_path("nothing here").empty());
    CHECK(same_path("DataGx/Course/France_M/francem.dx","datagx\\course\\france_m\\FRANCEM.DX"));
    CHECK(slope_band(-1.f)==0&&slope_band(0.f)==3&&slope_band(0.6f)==2);
}
void geometry(){
    const auto tris=sample();std::vector<uint8_t> dx;put32(dx,1339);for(int i=0;i<40;++i)dx.push_back(0);
    const auto t=tag1400(tris,kMats);dx.insert(dx.end(),t.begin(),t.end());
    Mesh m;CHECK(parse_course_dx(dx.data(),dx.size(),m)==ParseResult::Ok);
    const float cam[3]={5,10,5};Settings s;Batch b;
    build_batch(m,Mode::Off,cam,s,b);CHECK(b.fill.empty()&&b.lines.empty());
    build_batch(m,Mode::Surface,cam,s,b);CHECK(b.fill.size()==9&&b.lines.empty()&&b.visible_triangles==3&&b.fill_depth_test&&!b.fill_depth_write);
    CHECK(b.surface_triangles[size_t(Surface::Gravel)]==1&&b.surface_triangles[size_t(Surface::Unknown)]==1);
    // pulled toward the camera
    CHECK(b.fill[0].y>0.f&&b.fill[0].y<0.1f);
    build_batch(m,Mode::Wire,cam,s,b);CHECK(b.fill.empty()&&b.lines.size()==16&&b.lines_depth_test);
    build_batch(m,Mode::XRay,cam,s,b);CHECK(!b.lines_depth_test);
    build_batch(m,Mode::Solid,cam,s,b);CHECK(b.fill_depth_write&&(b.fill[0].color>>24)==0xff&&b.lines.size()==16);
    // front = the -n side faces the camera: ground (n=-y) from above, the wall (n=+x) from x<20
    build_batch(m,Mode::Facing,cam,s,b);CHECK(b.front==3&&b.back==0);
    const float behind[3]={30,10,5};build_batch(m,Mode::Facing,behind,s,b);CHECK(b.front==2&&b.back==1);
    build_batch(m,Mode::Slope,cam,s,b);CHECK(b.slope_triangles[0]==2&&b.slope_triangles[3]==1);
    s.range=1.f;const float distant[3]={1000,0,1000};build_batch(m,Mode::Surface,distant,s,b);CHECK(b.visible_triangles==0);
    Legend l;Batch lb;build_batch(m,Mode::Surface,cam,Settings{},lb);build_legend(l,Mode::Surface,lb,"LOOSE DX","F11",1920);
    CHECK(!l.quads.empty()&&l.quads.size()%6==0);
    build_legend(l,Mode::Off,lb,"LOOSE DX","F11",1920);CHECK(l.quads.empty());
    for(char c:std::string("COLLISION 0123456789 SURFACE WIRE X-RAY SLOPE FACING SOLID TARMAC GRAVEL HARDDIRT GRASS MUD WATER OTHER NO TYPE DEG WALL FRONT BACK TRIS RETAIL LOOSE DX % / ( ) . :"))
        if(c!=' ')CHECK(glyph(c)!=0);
}
// Digest of a mesh in record order: per triangle 3 corners (welded positions), the stored plane, the material index,
// then the material names. tools/prepare_collision_debug.py computes the same from the loader-guided Python parse.
std::string digest(const Mesh& m){
    std::vector<uint8_t> b;
    for(size_t t=0;t<m.triangles();++t){
        for(int k=0;k<3;++k)for(int a=0;a<3;++a)putf(b,m.positions[m.indices[t*3+k]*3+a]);
        for(int a=0;a<4;++a){const float f=m.planes[t*4+a];if(std::isnan(f))put32(b,0x7fc00000u);else putf(b,f);}put16(b,m.material[t]);
    }
    for(const auto& s:m.materials){put32(b,static_cast<uint32_t>(s.size()));b.insert(b.end(),s.begin(),s.end());}
    return gfx2::sha256_bytes(b.data(),b.size());
}
bool read(const char* path,std::vector<uint8_t>& out){std::ifstream f(path,std::ios::binary);if(!f)return false;out.assign(std::istreambuf_iterator<char>(f),{});return true;}
int dump(const char* path,const char* out_path){
    std::vector<uint8_t> dx;if(!read(path,dx)){std::cerr<<"unreadable "<<path<<"\n";return 2;}
    Mesh m;size_t at=0;const auto r=parse_course_dx(dx.data(),dx.size(),m,&at);
    std::ofstream out(out_path,std::ios::app);
    out<<"{\"path\":\""<<path<<"\",\"result\":"<<int(r)<<",\"tag1400_offset\":"<<at<<",\"triangles\":"<<m.triangles()
       <<",\"vertices\":"<<m.positions.size()/3<<",\"edges\":"<<m.edges.size()/3<<",\"digest\":\""<<(r==ParseResult::Ok?digest(m):"")<<"\"}\n";
    return r==ParseResult::Ok?0:1;
}
int dump_asset(const char* path,const char* out_path){
    std::vector<uint8_t> a;if(!read(path,a))return 2;std::vector<AssetEntry> index;
    if(!decode_asset_index(a.data(),a.size(),index)){std::cerr<<"asset index rejected\n";return 1;}
    std::ofstream out(out_path,std::ios::app);int bad=0;
    for(const auto& e:index){Mesh m;const bool ok=decode_asset_mesh(a.data(),a.size(),e,m);bad+=!ok;
        out<<"{\"race_id\":\""<<e.race_id<<"\",\"dx_path\":\""<<e.dx_path<<"\",\"ok\":"<<(ok?"true":"false")<<",\"triangles\":"<<m.triangles()
           <<",\"vertices\":"<<m.positions.size()/3<<",\"edges\":"<<m.edges.size()/3<<",\"digest\":\""<<(ok?digest(m):"")<<"\"}\n";}
    return bad?1:0;
}
} // namespace

// Joined courses: several landscape entities, each with its en3d Matrix (InvGrandFinal shape), equal pairs kept once.
void joined(){
    const std::string xml=
        "<Entity><Value Name=\"en3d Model Name\" Type=\"String\" Value=\"course\\invspain\\spain2\" />\n"
        "<Value Name=\"en3d Matrix\" Type=\"Matrix\" Row0=\"1.00 0.00 0.00 0.00\" Row1=\"0.00 1.00 0.00 0.00\" Row2=\"0.00 0.00 1.00 0.00\" Row3=\"0.00 0.00 0.00 1.00\" /></Entity>\n"
        "<Entity><Value Name=\"en3d Model Name\" Type=\"String\" Value=\"course\\invitaly\\italy_w1\" />\n"
        "<Value Name=\"en3d Matrix\" Type=\"Matrix\" Row0=\"0 0 -1 0\" Row1=\"0 1 0 0\" Row2=\"1 0 0 0\" Row3=\"100 5 -20 1\" /></Entity>\n"
        "<Entity><Value Name=\"en3d Model Name\" Type=\"String\" Value=\"course\\invspain\\spain2\" />\n"
        "<Value Name=\"en3d Matrix\" Type=\"Matrix\" Row0=\"1 0 0 0\" Row1=\"0 1 0 0\" Row2=\"0 0 1 0\" Row3=\"0 0 0 1\" /></Entity>\n"
        "<Entity><Value Name=\"en3d Model Name\" Type=\"String\" Value=\"course\\invfrance\\france1\" /></Entity>\n";
    const auto refs=landscape_refs(xml);
    CHECK(refs.size()==3);
    if(refs.size()==3){
        CHECK(refs[0].dx_path=="DataGx/Course/invspain/spain2.dx"&&refs[0].identity);
        CHECK(refs[1].dx_path=="DataGx/Course/invitaly/italy_w1.dx"&&!refs[1].identity&&refs[1].matrix[12]==100.f&&refs[1].matrix[2]==-1.f);
        CHECK(refs[2].dx_path=="DataGx/Course/invfrance/france1.dx"&&refs[2].identity);   // no matrix: identity
    }
    // transform: x' = x*M (row vectors); the rotated plane stays consistent with its vertices
    const auto tris=sample();std::vector<uint8_t> dx;put32(dx,1339);for(int i=0;i<40;++i)dx.push_back(0);
    const auto t=tag1400(tris,kMats);dx.insert(dx.end(),t.begin(),t.end());
    Mesh a;CHECK(parse_course_dx(dx.data(),dx.size(),a)==ParseResult::Ok);
    Mesh moved=a;if(refs.size()==3)transform_mesh(moved,refs[1].matrix);
    // (10,0,0) -> x'=0*.. : x'=x*0+z*1+100, y'=y+5, z'=-x-20
    bool found=false;for(size_t v=0;v+2<moved.positions.size();v+=3)found|=moved.positions[v]==100.f&&moved.positions[v+1]==5.f&&moved.positions[v+2]==-30.f;
    CHECK(found);
    for(size_t k=0;k<moved.triangles();++k){const float* n=&moved.planes[k*4];
        for(int c=0;c<3;++c){const float* p=&moved.positions[moved.indices[k*3+c]*3];CHECK(std::fabs(n[0]*p[0]+n[1]*p[1]+n[2]*p[2]+n[3])<1e-3f);}}
    CHECK(moved.planes[1]<-0.99f);   // ground still points down
    Mesh all;CHECK(merge_mesh(all,a)&&merge_mesh(all,moved));
    CHECK(all.triangles()==6&&all.materials.size()==6&&all.positions.size()==a.positions.size()*2&&all.edges.size()==a.edges.size()*2);
    CHECK(all.material[3]==3&&all.indices[9]==a.positions.size()/3+a.indices[0]);
}
// RETAIL-DERIVATIVE1: layout gate on synthetic bytes; with MRR_RETAIL_EXE the real retail EXE and a one-page edit.
void derivative(const char* retail_exe){
    gfx2::ps2port::RetailDerivative d;std::vector<uint8_t> junk(1000,0);
    gfx2::ps2port::check_retail_derivative_bytes(junk.data(),junk.size(),d);CHECK(!d.accepted&&!std::strcmp(d.reason,"file_size_differs_from_retail"));
    if(!retail_exe||!*retail_exe){std::cout<<"retail EXE derivative check: NOT_PERFORMED (set MRR_RETAIL_EXE)\n";return;}
    std::ifstream f(retail_exe,std::ios::binary);std::vector<uint8_t> exe((std::istreambuf_iterator<char>(f)),{});
    gfx2::ps2port::check_retail_derivative_bytes(exe.data(),exe.size(),d);CHECK(d.accepted&&d.changed_pages.empty());
    auto mod=exe;mod[0x2ad440]^=0x55;mod[0x59f5e]^=1;
    gfx2::ps2port::check_retail_derivative_bytes(mod.data(),mod.size(),d);
    CHECK(d.accepted&&d.changed_pages.size()==2&&d.changed_pages[0]==0x59000&&d.changed_pages[1]==0x2ad000);
    for(size_t p=0;p<70;++p)mod[0x1000+p*4096]^=0xff;
    gfx2::ps2port::check_retail_derivative_bytes(mod.data(),mod.size(),d);CHECK(!d.accepted&&!std::strcmp(d.reason,"too_many_changed_pages"));
    auto relinked=exe;relinked[0x210+12]^=0x10;   // .text VirtualAddress
    gfx2::ps2port::check_retail_derivative_bytes(relinked.data(),relinked.size(),d);CHECK(!d.accepted&&!std::strcmp(d.reason,"section_layout_differs_from_retail"));
    std::cout<<"retail EXE derivative check: PASS\n";
}

// tag100 wire: one node = u32 value, u32 0, bool plane [4f, code], bool list(0), bool child [bool class] ..., then the
// next flag after the child subtree. A cube [0,1]^3: six planes chained through the inside ("child") link, every
// outside ("next") link an empty leaf (1), the innermost child a solid leaf (-1).
void bsp_node(std::vector<uint8_t>& b,const float* plane,uint32_t code,int32_t value){
    put32(b,static_cast<uint32_t>(value));put32(b,0);
    b.push_back(plane?1:0);if(plane){for(int k=0;k<4;++k)putf(b,plane[k]);put32(b,code);}
    b.push_back(0);
}
std::vector<uint8_t> cube_tag100(bool with_splitter){
    const float planes[6][4]={{-1,0,0,0},{1,0,0,-1},{0,-1,0,0},{0,1,0,-1},{0,0,-1,0},{0,0,1,-1}};
    std::vector<uint8_t> b;const uint32_t planes_n=6+(with_splitter?1:0);
    put32(b,100);put32(b,1);put32(b,planes_n);put32(b,planes_n);put32(b,planes_n);put32(b,0);
    // optional splitter x=0.5 (code -1): both sides continue into a copy? keep it simple: splitter whose next side is empty
    if(with_splitter){const float sp[4]={0,0,0,0};(void)sp;}
    for(int i=0;i<6;++i){bsp_node(b,planes[i],uint32_t(10+i),0);b.push_back(1);b.push_back(i==5?1:0);}  // child present (leaf class for the last)
    bsp_node(b,nullptr,0,-1);b.push_back(0);b.push_back(0);   // solid leaf: no child, no next
    for(int i=0;i<6;++i){b.push_back(1);b.push_back(1);bsp_node(b,nullptr,0,1);b.push_back(0);b.push_back(0);} // next of each plane: empty leaf
    return b;
}
void bsp(){
    // header counts: c0 (child leaves)=1, c1 (next leaves)=6, c2=c3=planes=6
    auto tree=cube_tag100(false);
    tree[4]=1;tree[8]=6;
    std::vector<uint8_t> dx(64,0xee);const size_t at=dx.size();dx.insert(dx.end(),tree.begin(),tree.end());
    const size_t t1339=dx.size();put32(dx,1339);for(float f:{.5f,.5f,.5f,1.f,-1.f,-1.f,-1.f,2.f,2.f,2.f})putf(dx,f);
    Bsp b;CHECK(parse_tag100(dx.data(),dx.size(),at,b)==tree.size());
    CHECK(b.nodes.size()==13&&b.nodes[0].plane&&b.nodes[0].child==1&&b.nodes[0].next>=0);
    Bsp found;CHECK(find_tag100(dx.data(),dx.size(),t1339,found)&&found.nodes.size()==13&&found.min[0]==-1.f&&found.max[1]==2.f);
    BspStats st;const auto faces=bsp_solid_faces(found,st);
    CHECK(st.solid_cells==1&&st.empty_cells==6&&faces.size()==6);
    float area=0;for(const auto& f:faces){CHECK(f.points.size()==4);
        for(const auto& p:f.points)for(float x:p)CHECK(std::fabs(x)<1e-4f||std::fabs(x-1.f)<1e-4f);
        area+=1.f;}
    CHECK(area==6.f);
    // all six faces are objects (no tag1400 plane matches); 2 fan triangles each, 4 visible edges per face
    Mesh m;BspStats s2=st;add_bsp_objects(m,faces,s2);
    CHECK(s2.object_faces==6&&m.triangles()==12&&m.material_surface.back()==Surface::Object&&m.edges.size()/3==6*4);
    // one face coplanar with a "ground" triangle (y=0 plane, stored pointing down like tag1400) -> its code is ground
    Mesh g;g.positions={0,0,0, 1,0,0, 0,0,1};g.indices={0,1,2};g.planes={0,-1,0,0};g.material={0};g.materials={"$surfacetype(grass)"};
    g.material_surface={Surface::Grass};finish_indexed(g);
    BspStats s3=st;add_bsp_objects(g,faces,s3);CHECK(s3.ground_codes==1&&s3.object_faces==5&&g.triangles()==1+10);
    // Objects mode draws only the object faces
    const float cam[3]={3,3,3};Batch batch;build_batch(g,Mode::Objects,cam,Settings{},batch);
    CHECK(batch.fill.size()==30&&batch.fill_depth_write&&batch.surface_triangles[size_t(Surface::Object)]==10);
    // a truncated tree is rejected
    CHECK(!parse_tag100(dx.data(),at+tree.size()-1,at,b));
}
int sma_check(const char* archive,const char* root){
    gfx2::sma::Archive a;if(!a.open(std::filesystem::path(archive).wstring())){std::cerr<<"archive not opened\n";return 2;}
    size_t ok=0,bad=0,missing=0;
    for(const auto& e:std::filesystem::recursive_directory_iterator(root)){
        if(!e.is_regular_file())continue;
        const auto rel=std::filesystem::relative(e.path(),root).generic_string();
        std::vector<uint8_t> want,got;if(!read(e.path().string().c_str(),want))continue;
        if(!a.find(rel)){++missing;continue;}
        if(a.read(rel,got)&&got==want)++ok;else{++bad;std::cerr<<"MISMATCH "<<rel<<"\n";}
    }
    std::cout<<"sma members "<<a.size()<<" equal "<<ok<<" mismatch "<<bad<<" not_in_archive "<<missing<<"\n";
    return bad?1:0;
}
int dump_bsp(const char* path,const char* out_path){
    std::vector<uint8_t> dx;if(!read(path,dx)){std::cerr<<"unreadable "<<path<<"\n";return 2;}
    Mesh m;BspStats st;bool objects=false;
    const auto t0=std::chrono::steady_clock::now();
    const auto r=parse_course_dx_full(dx.data(),dx.size(),m,st,objects);
    const double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t0).count();
    std::ofstream out(out_path,std::ios::app);
    out<<"{\"path\":\""<<path<<"\",\"result\":"<<int(r)<<",\"bsp\":"<<(objects?"true":"false")<<",\"solid_cells\":"<<st.solid_cells
       <<",\"empty_cells\":"<<st.empty_cells<<",\"lost_cells\":"<<st.lost_cells<<",\"faces\":"<<st.faces<<",\"object_faces\":"<<st.object_faces
       <<",\"ground_codes\":"<<st.ground_codes<<",\"object_codes\":"<<st.object_codes<<",\"triangles\":"<<m.triangles()<<",\"ms\":"<<ms<<"}\n";
    return r==ParseResult::Ok&&objects?0:1;
}

// Round 4: vehicle hull (tag101 wire), vehicle pose, race markers.
void put_geometry(std::vector<uint8_t>& b,const std::vector<float>& v){put32(b,uint32_t(v.size()/3));put32(b,0);for(float f:v)putf(b,f);}
void put_rep(std::vector<uint8_t>& b,const std::vector<float>& v,const std::vector<std::vector<int>>& faces){
    put_geometry(b,v);put_geometry(b,{0,0,0});put32(b,0);put32(b,0);put32(b,uint32_t(faces.size()));
    for(const auto& f:faces){put32(b,uint32_t(f.size()));for(int i:f)put32(b,uint32_t(i));put32(b,0);}
    for(size_t i=0;i<faces.size();++i)put32(b,0);
    for(size_t i=0;i<faces.size();++i)putf(b,1.f);
}
void hulls_and_markers(){
    const std::vector<float> cube={-1,0,-2, 1,0,-2, 1,1,-2, -1,1,-2, -1,0,2, 1,0,2, 1,1,2, -1,1,2};
    const std::vector<std::vector<int>> faces={{0,3,2,1},{4,5,6,7},{0,1,5,4},{2,3,7,6},{1,2,6,5},{0,4,7,3}};
    std::vector<uint8_t> dx(40,0x65);   // junk with the byte 101 (0x65) everywhere
    put32(dx,101);put_geometry(dx,{0,.5f,0});putf(dx,2.3f);put_rep(dx,cube,{});put_rep(dx,cube,faces);
    put32(dx,1339);for(int i=0;i<10;++i)putf(dx,0.f);
    Hull h;size_t at=0;CHECK(parse_vehicle_hull(dx.data(),dx.size(),h,&at)&&at==40);
    CHECK(h.points.size()==24&&h.edges.size()==24&&h.radius==2.3f&&h.centre[1]==.5f&&h.box[2]==-2.f&&h.box[4]==1.f);
    auto bad=dx;bad[bad.size()-44]=0;CHECK(!parse_vehicle_hull(bad.data(),bad.size(),h));   // no tag102/1339 after it
    // pose: orthonormal block used as is; a skewed one falls back to the forward yaw
    float m[16]={0,0,-1,0, 0,1,0,0, 1,0,0,0, 10,2,3,1};VehiclePose pose;
    CHECK(pose_from_world(m,pose));
    const float local[3]={0,0,2};float w[3];pose_point(pose,local,w);CHECK(w[0]==12.f&&w[1]==2.f&&w[2]==3.f);
    // the render matrix is taken as drawn (a scale is kept); a projective or degenerate matrix is refused
    float scaled[16]={2,0,0,0, 0,1,0,0, 0,0,3,0, 0,0,0,1};CHECK(pose_from_world(scaled,pose)&&pose.rows[0]==2.f&&pose.rows[8]==3.f);
    float projective[16]={1,0,0,0, 0,1,0,0, 0,0,1,1, 0,0,0,0};CHECK(!pose_from_world(projective,pose));
    float flat[16]={0,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};CHECK(!pose_from_world(flat,pose));
    CHECK(pose_from_world(m,pose));
    float nan[16]={};nan[0]=std::numeric_limits<float>::quiet_NaN();CHECK(!pose_from_world(nan,pose));
    // wheel.dx tail: tag102 (radius 0.4, width 0.2) right before tag1339
    std::vector<uint8_t> wheel(100,0);put32(wheel,102);putf(wheel,.4f);putf(wheel,.2f);put32(wheel,1339);for(int i=0;i<10;++i)putf(wheel,0.f);
    WheelCylinder cyl;CHECK(parse_wheel_cylinder(wheel.data(),wheel.size(),cyl)&&cyl.radius==.4f&&cyl.width==.2f);
    auto nowheel=wheel;nowheel[nowheel.size()-56]=7;CHECK(!parse_wheel_cylinder(nowheel.data(),nowheel.size(),cyl));
    std::vector<Vertex> cl;float id[16]={1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};CHECK(pose_from_world(id,pose));
    cylinder_lines(cyl,pose,0xffffffffu,cl,16);CHECK(cl.size()==2*(16*2+8));
    for(const auto& v:cl){CHECK(std::fabs(std::fabs(v.x)-.1f)<1e-6f);CHECK(std::fabs(std::sqrt(v.y*v.y+v.z*v.z)-.4f)<1e-5f);}
    CHECK(pose_from_world(m,pose));
    std::vector<Vertex> lines;hull_lines(h,pose,0xffffffffu,lines);CHECK(lines.size()==24);
    // markers
    const std::string xml="<MarkerLists>\n<List Name=\"RaceLine\">\n<Marker No=\"0\">\n<Value Name=\"Marker Type\" Type=\"String\" Value=\"markers\\green_marker\"/>\n"
        "<Value Name=\"Marker Pos\" Type=\"Vector3\" Value=\"1.00 2.00 3.00\"/>\n<Value Name=\"Marker Dir\" Type=\"Vector3\" Value=\"1.00 0.00 0.00\"/>\n</Marker>\n"
        "<Marker No=\"1\">\n<Value Name=\"Marker Pos\" Type=\"Vector3\" Value=\"11.00 2.00 3.00\"/>\n</Marker>\n</List>\n"
        "<List Name=\"StartArea\"><Marker No=\"0\"><Value Name=\"Marker Pos\" Type=\"Vector3\" Value=\"0 0 0\"/></Marker>"
        "<Marker No=\"1\"><Value Name=\"Marker Pos\" Type=\"Vector3\" Value=\"1 0 0\"/></Marker><Marker No=\"2\"><Value Name=\"Marker Pos\" Type=\"Vector3\" Value=\"1 0 1\"/></Marker></List>\n"
        "<List Name=\"Empty\"></List>\n</MarkerLists>";
    const auto lists=marker_lists(xml);
    CHECK(lists.size()==2&&lists[0].name=="RaceLine"&&lists[0].pos.size()==6&&lists[0].pos[3]==11.f&&lists[0].dir[0]==1.f&&lists[1].pos.size()==9);
    std::vector<Vertex> ml;std::vector<uint32_t> counts;const float cam[3]={0,0,0};
    marker_lines(lists,cam,1000.f,ml,counts);
    // RaceLine: 2 posts + 1 direction tick + 1 segment; StartArea: 3 posts + 3 closing segments (no direction)
    CHECK(counts.size()==2&&counts[0]==2&&counts[1]==3&&ml.size()==2*(2+1+1+3+3));
    CHECK(marker_label("LeftInnerLimit")=="L-INNER"&&marker_label("RaceLine")=="RACELINE"&&marker_rgb("RaceLine")!=marker_rgb("FinishArea"));
    Legend l;Batch b;build_legend(l,Mode::Off,b,"","F11",1920,1080,"",{{"RACELINE 2",marker_rgb("RaceLine")}});CHECK(!l.quads.empty());
    build_legend(l,Mode::Off,b,"","F11",1920,1080);CHECK(l.quads.empty());
}
int dump_hull(const char* path,const char* out_path){
    std::vector<uint8_t> dx;if(!read(path,dx))return 2;Hull h;size_t at=0;const bool ok=parse_vehicle_hull(dx.data(),dx.size(),h,&at);
    std::ofstream out(out_path,std::ios::app);
    out<<"{\"path\":\""<<path<<"\",\"ok\":"<<(ok?"true":"false")<<",\"tag101_offset\":"<<at<<",\"vertices\":"<<h.points.size()/3<<",\"edges\":"<<h.edges.size()/2<<"}\n";
    return ok?0:1;
}

int main(int argc,char** argv){
    if(argc==4&&!std::strcmp(argv[1],"--dump"))return dump(argv[2],argv[3]);
    if(argc==4&&!std::strcmp(argv[1],"--dump-asset"))return dump_asset(argv[2],argv[3]);
    if(argc==4&&!std::strcmp(argv[1],"--dump-bsp"))return dump_bsp(argv[2],argv[3]);
    if(argc==4&&!std::strcmp(argv[1],"--dump-hull"))return dump_hull(argv[2],argv[3]);
    if(argc==4&&!std::strcmp(argv[1],"--sma-check"))return sma_check(argv[2],argv[3]);
    parse();asset();modes();geometry();joined();bsp();hulls_and_markers();derivative(std::getenv("MRR_RETAIL_EXE"));
    if(failures){std::cerr<<failures<<" failures\n";return 1;}
    std::cout<<"collision debug contracts passed\n";return 0;
}
