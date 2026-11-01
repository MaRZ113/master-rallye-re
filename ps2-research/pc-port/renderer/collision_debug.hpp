#pragma once
// COLLISION-DEBUG1 (opt-in CollisionDebug=1, docs/collision-debug1): the course collision surface drawn over the game.
// Portable core: no D3D, no Windows, no proxy (tests/collision_debug_tests.cpp).
//
// Source = the course DX tag1400 section (wire layout R5T-F.2.1, research/r5t_f21/tag1400-layout.md; loader 0x5541d0).
// COLLISION-DEBUG1 assigns the record meaning, verified on all 36 retail courses (967,735/967,735 records,
// docs/collision-debug1/README.md):
//   record = 9 floats v0,v1,v2 | uint32 string-table index | plane n.x,n.y,n.z,d with |n|=1, n.p+d=0 for v0..v2,
//   n has the direction of cross(v1-v0,v2-v0); ground planes point down (-Y), so the drivable (front) side is -n.
//   strings = the course material names ("$surfacetype(gravel) $shader(ground)..."), cells = a scalar-metre XZ grid
//   (dimension_0 x dimension_1 over vector_a..vector_b) of record indices.
// The tag100 plane tree (finish gate posts and other compiled colliders, R5T-F.2.1) is NOT drawn: it holds planes, not
// polygons.
#include <algorithm>
#include <cctype>
#include <cfloat>
#include <cstdlib>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace gfx2::colldebug {

inline constexpr uint32_t kTag1339=1339,kTag1400=1400,kTag1500=1500;
inline constexpr size_t kTag1339Size=44,kRecordSize=56;
inline constexpr uint32_t kMaxCells=4000000,kMaxCellEntries=8000000,kMaxStrings=65536,kMaxRecords=1000000;

// Object = a face of a solid tag100 BSP cell that is not part of the tag1400 ground (banners, posts, rails, bridge ends).
enum class Surface : uint8_t { Unknown=0, Tarmac, Gravel, HardDirt, Grass, Mud, Water, Other, Object };
inline constexpr size_t kSurfaceCount=9;
inline const char* surface_name(Surface s) noexcept {
    static constexpr const char* names[kSurfaceCount]={"NO TYPE","TARMAC","GRAVEL","HARDDIRT","GRASS","MUD","WATER","OTHER","OBJECT"};
    const auto i=static_cast<size_t>(s);return i<kSurfaceCount?names[i]:names[0];
}
// "$surfacetype(<name>)" of a material; materials without it (roof, walls, waterfall objects) are Unknown.
inline Surface classify_surface(std::string_view material,std::string* type=nullptr) {
    constexpr std::string_view key="$surfacetype(";
    const size_t at=material.find(key);if(at==std::string_view::npos)return Surface::Unknown;
    const size_t end=material.find(')',at+key.size());if(end==std::string_view::npos)return Surface::Unknown;
    std::string name(material.substr(at+key.size(),end-at-key.size()));
    for(auto& c:name)c=static_cast<char>(c>='A'&&c<='Z'?c-'A'+'a':c);
    if(type)*type=name;
    if(name=="tarmac")return Surface::Tarmac;
    if(name=="gravel")return Surface::Gravel;
    if(name=="harddirt")return Surface::HardDirt;
    if(name=="grass")return Surface::Grass;
    if(name=="mud")return Surface::Mud;
    if(name=="water")return Surface::Water;
    return name.empty()?Surface::Unknown:Surface::Other;
}

struct Mesh {
    std::vector<float> positions;      // xyz per welded vertex
    std::vector<uint32_t> indices;     // 3 per triangle, record order
    std::vector<float> planes;         // n.x,n.y,n.z,d per triangle (the stored plane)
    std::vector<uint16_t> material;    // per triangle: index into materials
    std::vector<std::string> materials;
    std::vector<Surface> material_surface;
    std::vector<uint32_t> edges;       // unique welded edges: a,b,owner triangle
    std::vector<float> centre;         // x,y,z,radius per triangle (culling)
    std::vector<uint8_t> edge_mask;    // per triangle, bit e = draw edge e (empty = all; BSP polygon fans hide diagonals)
    float cell=0;uint32_t dim0=0,dim1=0;
    std::array<float,3> min{},max{};
    size_t triangles() const noexcept {return material.size();}
    void clear() noexcept {*this=Mesh{};}
};

namespace detail {
inline uint32_t u32(const uint8_t* p) noexcept {uint32_t v;std::memcpy(&v,p,4);return v;}
inline float f32(const uint8_t* p) noexcept {float v;std::memcpy(&v,p,4);return v;}
inline bool finite3(const float* v) noexcept {return std::isfinite(v[0])&&std::isfinite(v[1])&&std::isfinite(v[2]);}
// Plane consistency of one record (all 967,735 retail records pass with |n|-1 < 4e-7 and residual < 2e-2).
inline bool record_plane(const float* v,const float* n) noexcept {
    for(int i=0;i<9;++i)if(!std::isfinite(v[i]))return false;
    for(int i=0;i<4;++i)if(!std::isfinite(n[i]))return false;
    const float length=std::sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]);
    if(std::fabs(length-1.f)>1e-3f)return false;
    for(int k=0;k<3;++k){const float r=n[0]*v[k*3]+n[1]*v[k*3+1]+n[2]*v[k*3+2]+n[3];
        if(!(std::fabs(r)<=0.05f+1e-5f*std::fabs(n[3])))return false;}
    return true;
}
// Retail also stores degenerate records (collinear or repeated vertices, 19 in the retail corpus) with an all-NaN plane.
inline bool degenerate(const float* v) noexcept {
    for(int i=0;i<9;++i)if(!std::isfinite(v[i]))return false;
    const double a[3]={double(v[3])-v[0],double(v[4])-v[1],double(v[5])-v[2]},b[3]={double(v[6])-v[0],double(v[7])-v[1],double(v[8])-v[2]};
    const double c[3]={a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};
    return std::sqrt(c[0]*c[0]+c[1]*c[1]+c[2]*c[2])<=1e-3;
}
inline bool record_valid(const float* v,const float* n) noexcept {
    if(record_plane(v,n))return true;
    return std::isnan(n[0])&&std::isnan(n[1])&&std::isnan(n[2])&&std::isnan(n[3])&&degenerate(v);
}
} // namespace detail
inline bool degenerate_plane(const float* n) noexcept {return std::isnan(n[0]);}

inline void finish_indexed(Mesh& m);
// Welds equal positions (bit-exact), builds unique edges and per-triangle culling spheres. Expects positions as raw
// per-corner triangles (3 corners per triangle) in `corners`.
inline void finish_mesh(Mesh& m,const std::vector<float>& corners) {
    const size_t tris=corners.size()/9;
    m.positions.clear();m.indices.clear();m.indices.reserve(tris*3);
    struct Key{uint32_t x,y,z;bool operator==(const Key& o)const noexcept{return x==o.x&&y==o.y&&z==o.z;}};
    struct Hash{size_t operator()(const Key& k)const noexcept{return (size_t(k.x)*73856093u)^(size_t(k.y)*19349663u)^(size_t(k.z)*83492791u);}};
    std::unordered_map<Key,uint32_t,Hash> weld;weld.reserve(tris*2);
    for(size_t c=0;c<tris*3;++c){
        Key k;std::memcpy(&k.x,&corners[c*3],4);std::memcpy(&k.y,&corners[c*3+1],4);std::memcpy(&k.z,&corners[c*3+2],4);
        auto it=weld.find(k);
        if(it==weld.end()){it=weld.emplace(k,static_cast<uint32_t>(m.positions.size()/3)).first;
            m.positions.insert(m.positions.end(),{corners[c*3],corners[c*3+1],corners[c*3+2]});}
        m.indices.push_back(it->second);
    }
    finish_indexed(m);
}
inline void finish_indexed(Mesh& m) {
    const size_t tris=m.indices.size()/3;
    m.edges.clear();m.centre.clear();m.centre.reserve(tris*4);
    std::unordered_set<uint64_t> seen;seen.reserve(tris*2);
    for(size_t t=0;t<tris;++t){
        const uint32_t* i=&m.indices[t*3];
        const bool flat=t*4<m.planes.size()&&degenerate_plane(&m.planes[t*4]);
        const uint8_t mask=t<m.edge_mask.size()?m.edge_mask[t]:uint8_t(7);
        for(int e=0;e<3&&!flat;++e){if(!((mask>>e)&1))continue;uint32_t a=i[e],b=i[(e+1)%3];if(a>b)std::swap(a,b);
            if(a!=b&&seen.insert((uint64_t(a)<<32)|b).second)m.edges.insert(m.edges.end(),{a,b,static_cast<uint32_t>(t)});}
        float c[3]={0,0,0};
        for(int k=0;k<3;++k)for(int a=0;a<3;++a)c[a]+=m.positions[i[k]*3+a]/3.f;
        float r=0;for(int k=0;k<3;++k){float d=0;for(int a=0;a<3;++a){const float x=m.positions[i[k]*3+a]-c[a];d+=x*x;}r=std::max(r,std::sqrt(d));}
        m.centre.insert(m.centre.end(),{c[0],c[1],c[2],r});
    }
}

// One tag1400 section at `at` (its tag). Returns the number of bytes, 0 if the bytes are not a valid tag1400 followed by
// tag1500. Fills `out` only when valid (corners = raw per-record triangles).
inline size_t parse_tag1400(const uint8_t* data,size_t size,size_t at,Mesh& out,std::vector<float>& corners) {
    using namespace detail;
    if(at>size||size-at<40||u32(data+at)!=kTag1400)return 0;
    const float scalar=f32(data+at+4);const uint32_t d0=u32(data+at+8),d1=u32(data+at+12);
    float a[3],b[3];for(int i=0;i<3;++i){a[i]=f32(data+at+16+i*4);b[i]=f32(data+at+28+i*4);}
    if(!std::isfinite(scalar)||!(scalar>0.f)||scalar>10000.f||!d0||!d1||d0>65536||d1>65536||uint64_t(d0)*d1>kMaxCells||
       !finite3(a)||!finite3(b)||!(a[0]<=b[0])||!(a[1]<=b[1])||!(a[2]<=b[2]))return 0;
    size_t o=at+40;uint64_t entries=0;
    const uint64_t cells=uint64_t(d0)*d1;
    std::vector<std::pair<size_t,uint32_t>> cell_lists;cell_lists.reserve(static_cast<size_t>(cells));
    for(uint64_t c=0;c<cells;++c){
        if(size-o<4)return 0;const uint32_t n=u32(data+o);o+=4;entries+=n;
        if(entries>kMaxCellEntries||uint64_t(n)*4>size-o)return 0;
        cell_lists.emplace_back(o,n);o+=size_t(n)*4;
    }
    if(size-o<4)return 0;const uint32_t strings=u32(data+o);o+=4;if(strings>kMaxStrings)return 0;
    std::vector<std::string> names;names.reserve(strings);
    for(uint32_t s=0;s<strings;++s){
        if(size-o<4)return 0;const uint32_t n=u32(data+o);o+=4;if(n>size-o||n>65536)return 0;
        names.emplace_back(reinterpret_cast<const char*>(data+o),n);o+=n;
    }
    if(size-o<4)return 0;const uint32_t records=u32(data+o);o+=4;
    if(!records||records>kMaxRecords||uint64_t(records)*kRecordSize>size-o)return 0;
    const size_t first=o;o+=size_t(records)*kRecordSize;
    // Retail: tag1500 follows. Cooked new courses (invspaingx.dx) end the file with the last record.
    if(o!=size&&(size-o<4||u32(data+o)!=kTag1500))return 0;
    for(const auto& [offset,n]:cell_lists)for(uint32_t e=0;e<n;++e)if(u32(data+offset+e*4)>=records)return 0;
    Mesh m;corners.assign(size_t(records)*9,0.f);m.planes.resize(size_t(records)*4);m.material.resize(records);
    for(uint32_t r=0;r<records;++r){
        const uint8_t* p=data+first+size_t(r)*kRecordSize;float v[9],n[4];
        for(int i=0;i<9;++i)v[i]=f32(p+i*4);for(int i=0;i<4;++i)n[i]=f32(p+40+i*4);
        const uint32_t ref=u32(p+36);
        if(ref>=strings||ref>0xffff||!record_valid(v,n))return 0;
        std::memcpy(&corners[size_t(r)*9],v,sizeof(v));std::memcpy(&m.planes[size_t(r)*4],n,sizeof(n));
        m.material[r]=static_cast<uint16_t>(ref);
    }
    m.materials=std::move(names);
    for(const auto& s:m.materials)m.material_surface.push_back(classify_surface(s));
    m.cell=scalar;m.dim0=d0;m.dim1=d1;for(int i=0;i<3;++i){m.min[i]=a[i];m.max[i]=b[i];}
    out=std::move(m);return o-at;
}

// Course DX bytes (loose file): tag1339 (44 bytes) is immediately followed by tag1400 in every retail course. The render
// prefix is not parsed here: candidates are every byte offset with u32 1339 and u32 1400 44 bytes later, and exactly one
// must pass the full tag1400 validation (retail Turkey_s2 has one false candidate inside its tag100 tree that fails).
// Verified equal to the loader-guided Python parse on all 36 retail courses (tools/prepare_collision_debug.py --verify).
enum class ParseResult : uint8_t { Ok, NoCandidate, Ambiguous };
inline ParseResult parse_course_dx(const uint8_t* data,size_t size,Mesh& out,size_t* tag_offset=nullptr) {
    size_t found=SIZE_MAX;Mesh best;std::vector<float> corners,best_corners;
    if(size<kTag1339Size+48)return ParseResult::NoCandidate;
    for(size_t o=0;o+kTag1339Size+40<=size;++o){
        if(data[o]!=0x3b||data[o+1]!=0x05||data[o+2]||data[o+3]||detail::u32(data+o+kTag1339Size)!=kTag1400)continue;
        Mesh m;
        if(!parse_tag1400(data,size,o+kTag1339Size,m,corners))continue;
        if(found!=SIZE_MAX)return ParseResult::Ambiguous;
        found=o+kTag1339Size;best=std::move(m);best_corners.swap(corners);
    }
    if(found==SIZE_MAX)return ParseResult::NoCandidate;
    finish_mesh(best,best_corners);
    if(tag_offset)*tag_offset=found;
    out=std::move(best);return ParseResult::Ok;
}


// ---------------------------------------------------------------------------------------------------------------------
// tag100 = the course BSP ("BSP memory %d", loader 0x57e2d0/0x57e550). Wire (R5T-F.2 grammar): node = u32 value,
// u32 reserved, bool plane [f32 n.x,n.y,n.z,d, u32 code], bool list [...], bool child [bool class], child subtree,
// bool next [bool class], next subtree. COLLISION-DEBUG1 round 3 semantics from the retail query 0x61ff90:
// s = n.p + d; s < 1e-4 -> the "child" link (node+0x1c), else the "next" link (node+0x20): a binary BSP whose next link
// is the second child (the serializer 0x57e3a0 recurses into child and iterates next). Leaves: value -1 = solid (point
// inside), 1 = empty. Check on France1 COLLIDE_finishline03: post centre -1, 2 m beside it and above it 1, deep under the
// terrain -1. Planes with code 0xffffffff are pure splitters; the nearest-face query 0x61fff0 only reports code >= 0.
struct BspNode { float n[4]={0,0,0,0}; uint32_t code=0xffffffffu; int32_t value=0; int32_t child=-1,next=-1; bool plane=false; };
struct Bsp { std::vector<BspNode> nodes; std::array<float,3> min{},max{}; };

// Parses the tree at `at` (tag 100). Returns the consumed size, 0 if invalid.
inline size_t parse_tag100(const uint8_t* data,size_t size,size_t at,Bsp& out) {
    using namespace detail;
    if(at>size||size-at<24||u32(data+at)!=100)return 0;
    const uint32_t c0=u32(data+at+4),c1=u32(data+at+8),c2=u32(data+at+12),c3=u32(data+at+16),c4=u32(data+at+20);
    if(!c2||c3!=c2||uint64_t(c0)+c1!=uint64_t(c2)+1||uint64_t(c0)+c1+c2>4000000||c4>4000000)return 0;
    std::vector<BspNode> nodes;nodes.reserve(size_t(c0)+c1+c2);
    size_t o=at+24;
    auto boolean=[&](bool& v)->bool{if(o>=size||data[o]>1)return false;v=data[o++]!=0;return true;};
    // Pending node: (link source, link kind 0=root 1=child 2=next). after_child: nodes whose next flag is still unread.
    struct Pending{int32_t source;int kind;};
    bool have=true;Pending pending{-1,0};std::vector<int32_t> after_child;uint64_t lists=0;
    while(have||!after_child.empty()){
        if(!have){
            const int32_t waiting=after_child.back();after_child.pop_back();
            bool has=false;if(!boolean(has))return 0;
            if(has){bool cls=false;if(!boolean(cls))return 0;pending={waiting,2};have=true;}
            continue;
        }
        have=false;
        if(nodes.size()>=size_t(c0)+c1+c2||size-o<9)return 0;
        BspNode n;n.value=static_cast<int32_t>(u32(data+o));o+=8;
        bool has_plane=false;if(!boolean(has_plane))return 0;
        if(has_plane){if(size-o<20)return 0;for(int k=0;k<4;++k)n.n[k]=f32(data+o+k*4);n.code=u32(data+o+16);o+=20;n.plane=true;
            if(!std::isfinite(n.n[0])||!std::isfinite(n.n[1])||!std::isfinite(n.n[2])||!std::isfinite(n.n[3]))return 0;}
        bool has_list=false;if(!boolean(has_list))return 0;
        if(has_list){if(size-o<4)return 0;const uint32_t k=u32(data+o);o+=4;lists+=k;if(lists>c4||uint64_t(k)*20>size-o)return 0;o+=size_t(k)*20;}
        bool has_child=false;if(!boolean(has_child))return 0;
        const int32_t index=static_cast<int32_t>(nodes.size());
        if(pending.kind==1)nodes[pending.source].child=index;else if(pending.kind==2)nodes[pending.source].next=index;
        nodes.push_back(n);
        if(has_child){bool cls=false;if(!boolean(cls))return 0;after_child.push_back(index);pending={index,1};have=true;}
        else{bool has=false;if(!boolean(has))return 0;if(has){bool cls=false;if(!boolean(cls))return 0;pending={index,2};have=true;}}
    }
    for(const auto& n:nodes)if(n.plane?(n.child<0||n.next<0):(n.child>=0||n.next>=0))return 0;   // full binary tree
    out.nodes=std::move(nodes);return o-at;
}
// Loose DX: the tree ends exactly where tag1339 begins (tag1400 at +44). Candidates: u32 100 with the header
// invariants (leaves = planes + 1, plane records = planes); exactly one must parse to that end.
inline bool find_tag100(const uint8_t* data,size_t size,size_t tag1339,Bsp& out) {
    if(tag1339>size||tag1339<24+44)return false;
    int found=0;Bsp best;
    for(size_t o=tag1339-24;o-- >0;){
        if(data[o]!=100||data[o+1]||data[o+2]||data[o+3])continue;
        const uint32_t c0=detail::u32(data+o+4),c1=detail::u32(data+o+8),c2=detail::u32(data+o+12),c3=detail::u32(data+o+16);
        if(!c2||c3!=c2||uint64_t(c0)+c1!=uint64_t(c2)+1)continue;
        // Retail size rule T = 23 + 13N + 20P (no lists): the tree must reach tag1339 at least.
        const uint64_t nodes=uint64_t(c0)+c1+c2;if(o+23+13*nodes+20ull*c3>tag1339)continue;
        Bsp b;const size_t used=parse_tag100(data,size,o,b);
        if(used&&o+used==tag1339){++found;best=std::move(b);}
        if(found>1)return false;
        if(tag1339-o>64ull*1024*1024)break;
    }
    if(found!=1)return false;
    std::memcpy(best.min.data(),data+tag1339+20,12);std::memcpy(best.max.data(),data+tag1339+32,12);
    out=std::move(best);return true;
}

// Solid leaf cells -> their faces on real planes (code != 0xffffffff) where the cell is on the inside (s<0): the outward
// collision faces. Ground faces (code of a face coplanar with any tag1400 triangle) are dropped: tag1400 shows them.
struct BspFace { std::vector<std::array<float,3>> points; uint32_t code=0; std::array<float,4> outward{}; };
struct BspStats { size_t solid_cells=0,empty_cells=0,lost_cells=0,faces=0,object_faces=0,ground_codes=0,object_codes=0; };
namespace detail {
using V3=std::array<double,3>;
struct CPoly { std::vector<V3> v; int32_t src=-1; int8_t side=0; };
inline double side_of(const double* n,const V3& p) noexcept {return n[0]*p[0]+n[1]*p[1]+n[2]*p[2]+n[3];}
inline bool clip_cell(const std::vector<CPoly>& cell,const double* n,bool keep_negative,int32_t src,std::vector<CPoly>& out) {
    out.clear();std::vector<V3> on;
    for(const auto& poly:cell){
        CPoly q;q.src=poly.src;q.side=poly.side;const size_t m=poly.v.size();
        for(size_t i=0;i<m;++i){
            const V3& a=poly.v[i];const V3& b=poly.v[(i+1)%m];
            double sa=side_of(n,a),sb=side_of(n,b);if(!keep_negative){sa=-sa;sb=-sb;}
            const bool ia=sa<=0,ib=sb<=0;
            if(ia){q.v.push_back(a);if(std::fabs(sa)<1e-6)on.push_back(a);}
            if(ia!=ib){const double t=sa/(sa-sb);V3 p{a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t};q.v.push_back(p);on.push_back(p);}
        }
        if(q.v.size()>=3)out.push_back(std::move(q));
    }
    if(out.size()<3)return false;
    // Cap on the plane: the unique points on it, ordered around their centroid.
    std::vector<V3> pts;
    for(const auto& p:on){bool dup=false;for(const auto& q:pts)if(std::fabs(p[0]-q[0])+std::fabs(p[1]-q[1])+std::fabs(p[2]-q[2])<1e-5){dup=true;break;}if(!dup)pts.push_back(p);}
    if(pts.size()>=3){
        V3 c{0,0,0};for(const auto& p:pts)for(int k=0;k<3;++k)c[k]+=p[k]/double(pts.size());
        const V3 a=std::fabs(n[0])<0.9?V3{1,0,0}:V3{0,1,0};
        V3 u{n[1]*a[2]-n[2]*a[1],n[2]*a[0]-n[0]*a[2],n[0]*a[1]-n[1]*a[0]};const double l=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);for(auto& x:u)x/=l;
        const V3 w{n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0]};
        auto angle=[&](const V3& p){double x=0,y=0;for(int k=0;k<3;++k){x+=(p[k]-c[k])*u[k];y+=(p[k]-c[k])*w[k];}return std::atan2(y,x);};
        std::sort(pts.begin(),pts.end(),[&](const V3& p,const V3& q){return angle(p)<angle(q);});
        if(!keep_negative)std::reverse(pts.begin(),pts.end());
        CPoly cap;cap.v=std::move(pts);cap.src=src;cap.side=keep_negative?1:-1;out.push_back(std::move(cap));
    }
    return true;
}
} // namespace detail

inline std::vector<BspFace> bsp_solid_faces(const Bsp& bsp,BspStats& stats) {
    using namespace detail;
    std::vector<BspFace> faces;stats={};
    if(bsp.nodes.empty())return faces;
    const double x0=bsp.min[0]-1,y0=bsp.min[1]-1,z0=bsp.min[2]-1,x1=bsp.max[0]+1,y1=bsp.max[1]+1,z1=bsp.max[2]+1;
    const V3 v[8]={{x0,y0,z0},{x1,y0,z0},{x1,y1,z0},{x0,y1,z0},{x0,y0,z1},{x1,y0,z1},{x1,y1,z1},{x0,y1,z1}};
    static constexpr int quads[6][4]={{0,3,2,1},{4,5,6,7},{0,1,5,4},{2,3,7,6},{1,2,6,5},{0,4,7,3}};
    std::vector<CPoly> box;for(const auto& q:quads){CPoly p;for(int i:q)p.v.push_back(v[i]);box.push_back(std::move(p));}
    struct Item{int32_t node;std::vector<CPoly> cell;};
    std::vector<Item> stack;stack.push_back({0,std::move(box)});
    std::vector<CPoly> a,b;
    while(!stack.empty()){
        Item it=std::move(stack.back());stack.pop_back();
        const BspNode& node=bsp.nodes[static_cast<size_t>(it.node)];
        if(!node.plane){
            if(node.value!=-1){++stats.empty_cells;continue;}
            ++stats.solid_cells;
            for(const auto& poly:it.cell){
                if(poly.src<0||poly.side!=1)continue;const BspNode& s=bsp.nodes[static_cast<size_t>(poly.src)];
                if(s.code==0xffffffffu)continue;
                BspFace f;f.code=s.code;for(int k=0;k<4;++k)f.outward[k]=s.n[k];
                for(const auto& p:poly.v)f.points.push_back({float(p[0]),float(p[1]),float(p[2])});
                faces.push_back(std::move(f));
            }
            continue;
        }
        const double n[4]={node.n[0],node.n[1],node.n[2],node.n[3]};
        if(node.child>=0){if(clip_cell(it.cell,n,true,it.node,a))stack.push_back({node.child,a});else ++stats.lost_cells;}
        if(node.next>=0){if(clip_cell(it.cell,n,false,it.node,b))stack.push_back({node.next,b});else ++stats.lost_cells;}
    }
    stats.faces=faces.size();
    return faces;
}
// Appends the object faces (codes with no face coplanar to a tag1400 triangle of `surface`) to `m` as fan triangles of
// material "OBJECT (BSP)" in the mesh convention (stored normal = into the solid, so the outward BSP normal is negated).
inline void add_bsp_objects(Mesh& m,const std::vector<BspFace>& faces,BspStats& stats) {
    auto key=[](const float* n,float d){return std::array<int32_t,4>{int32_t(std::lround(n[0]*100.f)),int32_t(std::lround(n[1]*100.f)),
        int32_t(std::lround(n[2]*100.f)),int32_t(std::lround(d*10.f))};};
    struct KeyHash{size_t operator()(const std::array<int32_t,4>& k)const noexcept{return size_t(k[0])*73856093u^size_t(k[1])*19349663u^size_t(k[2])*83492791u^size_t(k[3])*2654435761u;}};
    std::unordered_set<std::array<int32_t,4>,KeyHash> ground;
    for(size_t t=0;t<m.triangles();++t){const float* n=&m.planes[t*4];if(degenerate_plane(n))continue;
        const float neg[3]={-n[0],-n[1],-n[2]};ground.insert(key(n,n[3]));ground.insert(key(neg,-n[3]));}
    std::unordered_set<uint32_t> ground_codes,all_codes;
    for(const auto& f:faces){all_codes.insert(f.code);if(ground.count(key(f.outward.data(),f.outward[3])))ground_codes.insert(f.code);}
    stats.ground_codes=ground_codes.size();stats.object_codes=all_codes.size()-ground_codes.size();
    if(m.materials.size()>=0xffff)return;
    const uint16_t mat=static_cast<uint16_t>(m.materials.size());
    m.materials.push_back("OBJECT (BSP)");m.material_surface.push_back(Surface::Object);
    if(m.edge_mask.size()<m.triangles())m.edge_mask.resize(m.triangles(),7);
    for(const auto& f:faces){
        if(ground_codes.count(f.code)||f.points.size()<3)continue;
        ++stats.object_faces;
        const uint32_t base=static_cast<uint32_t>(m.positions.size()/3);
        for(const auto& p:f.points)m.positions.insert(m.positions.end(),{p[0],p[1],p[2]});
        const size_t k=f.points.size();
        for(size_t i=1;i+1<k;++i){
            m.indices.insert(m.indices.end(),{base,base+uint32_t(i),base+uint32_t(i+1)});
            m.planes.insert(m.planes.end(),{-f.outward[0],-f.outward[1],-f.outward[2],-f.outward[3]});
            m.material.push_back(mat);
            // fan: v0-vi only for the first, vi-vi+1 always, vi+1-v0 only for the last triangle
            m.edge_mask.push_back(static_cast<uint8_t>((i==1?1:0)|2|(i+2==k?4:0)));
        }
    }
    finish_indexed(m);
}

// Loose course DX with its BSP objects: tag1400 surface + tag100 object faces. Returns the surface result; `objects`
// tells whether the tree was found (a DX without a valid tree still draws its surface).
inline ParseResult parse_course_dx_full(const uint8_t* data,size_t size,Mesh& out,BspStats& stats,bool& objects) {
    objects=false;stats={};size_t at=0;
    const auto r=parse_course_dx(data,size,out,&at);
    if(r!=ParseResult::Ok)return r;
    Bsp bsp;
    if(find_tag100(data,size,at-kTag1339Size,bsp)){
        try{const auto faces=bsp_solid_faces(bsp,stats);add_bsp_objects(out,faces,stats);objects=true;}catch(...){objects=false;}
    }
    return r;
}

// ---------------------------------------------------------------------------------------------------------------------
// Asset CourseCollision.mrcoll (tools/prepare_collision_debug.py): the retail courses, which live inside Data.sma.
//   "MRCOLL01" u32 version(1) u32 entries
//   entry[160]: race_id[48] dx_path[64] dx_sha256[32] u32 offset u32 size u32 reserved[2]
//   blob: f32 cell u32 dim0 u32 dim1 f32 min[3] f32 max[3]
//         u32 materials {u16 length, bytes}  u32 vertices {f32 xyz}  u32 triangles {u32 i0,i1,i2} {u16 material}
//         {f32 plane[4]}
struct AssetEntry { std::string race_id,dx_path; std::array<uint8_t,32> dx_sha{}; uint32_t offset=0,size=0; };
inline constexpr char kAssetMagic[8]={'M','R','C','O','L','L','0','1'};
inline constexpr size_t kAssetEntrySize=160;

inline std::string fixed_text(const uint8_t* p,size_t n) {size_t k=0;while(k<n&&p[k])++k;return std::string(reinterpret_cast<const char*>(p),k);}
inline bool decode_asset_index(const uint8_t* data,size_t size,std::vector<AssetEntry>& out) {
    out.clear();if(size<16||std::memcmp(data,kAssetMagic,8)||detail::u32(data+8)!=1)return false;
    const uint32_t n=detail::u32(data+12);if(!n||n>4096||uint64_t(n)*kAssetEntrySize>size-16)return false;
    for(uint32_t i=0;i<n;++i){
        const uint8_t* e=data+16+size_t(i)*kAssetEntrySize;AssetEntry a;
        a.race_id=fixed_text(e,48);a.dx_path=fixed_text(e+48,64);std::memcpy(a.dx_sha.data(),e+112,32);
        a.offset=detail::u32(e+144);a.size=detail::u32(e+148);
        if(a.race_id.empty()||a.dx_path.empty()||a.offset<16+uint64_t(n)*kAssetEntrySize||a.size<40||a.offset>size||a.size>size-a.offset)return false;
        out.push_back(std::move(a));
    }
    return true;
}
inline bool decode_asset_mesh(const uint8_t* data,size_t size,const AssetEntry& e,Mesh& out) {
    using namespace detail;
    if(e.offset>size||e.size>size-e.offset)return false;
    const uint8_t* p=data+e.offset;const size_t n=e.size;size_t o=0;
    auto need=[&](uint64_t k){return k<=n-o;};
    Mesh m;if(!need(40))return false;
    m.cell=f32(p);m.dim0=u32(p+4);m.dim1=u32(p+8);for(int i=0;i<3;++i){m.min[i]=f32(p+12+i*4);m.max[i]=f32(p+24+i*4);}o=36;
    if(!need(4))return false;const uint32_t mats=u32(p+o);o+=4;if(!mats||mats>kMaxStrings)return false;
    for(uint32_t i=0;i<mats;++i){if(!need(2))return false;uint16_t l;std::memcpy(&l,p+o,2);o+=2;if(!need(l))return false;
        m.materials.emplace_back(reinterpret_cast<const char*>(p+o),l);o+=l;m.material_surface.push_back(classify_surface(m.materials.back()));}
    if(!need(4))return false;const uint32_t verts=u32(p+o);o+=4;if(!verts||verts>3*kMaxRecords||!need(uint64_t(verts)*12))return false;
    m.positions.resize(size_t(verts)*3);std::memcpy(m.positions.data(),p+o,size_t(verts)*12);o+=size_t(verts)*12;
    for(float v:m.positions)if(!std::isfinite(v))return false;
    if(!need(4))return false;const uint32_t tris=u32(p+o);o+=4;if(!tris||tris>kMaxRecords||!need(uint64_t(tris)*(12+2+16)))return false;
    m.indices.resize(size_t(tris)*3);std::memcpy(m.indices.data(),p+o,size_t(tris)*12);o+=size_t(tris)*12;
    m.material.resize(tris);std::memcpy(m.material.data(),p+o,size_t(tris)*2);o+=size_t(tris)*2;
    m.planes.resize(size_t(tris)*4);std::memcpy(m.planes.data(),p+o,size_t(tris)*16);o+=size_t(tris)*16;
    if(o!=n)return false;
    for(uint32_t i:m.indices)if(i>=verts)return false;
    for(uint16_t i:m.material)if(i>=mats)return false;
    for(size_t t=0;t<tris;++t){float v[9];for(int k=0;k<3;++k)for(int a=0;a<3;++a)v[k*3+a]=m.positions[m.indices[t*3+k]*3+a];
        if(!record_valid(v,&m.planes[t*4]))return false;}
    finish_indexed(m);out=std::move(m);return true;
}

// ---------------------------------------------------------------------------------------------------------------------
// Overlay modes, cycled by the hotkey (CollisionDebugKey, default F11; Shift = back).
enum class Mode : uint8_t { Off=0, Surface, Wire, XRay, Slope, Facing, Solid, Objects };
inline constexpr uint32_t kModeCount=8;
inline const char* mode_name(Mode m) noexcept {
    static constexpr const char* n[kModeCount]={"OFF","SURFACE","WIRE","X-RAY","SLOPE","FACING","SOLID","OBJECTS"};
    const auto i=static_cast<uint32_t>(m);return i<kModeCount?n[i]:n[0];
}
inline Mode next_mode(Mode m,bool back) noexcept {
    const uint32_t i=static_cast<uint32_t>(m)%kModeCount;
    return static_cast<Mode>(back?(i+kModeCount-1)%kModeCount:(i+1)%kModeCount);
}
inline bool parse_mode(const char* s,Mode& out) noexcept {
    for(uint32_t i=0;i<kModeCount;++i){const char* n=mode_name(static_cast<Mode>(i));
        size_t k=0;bool eq=true;for(;n[k]||s[k];++k){char c=s[k];if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');if(c!=n[k]){eq=false;break;}}
        if(eq){out=static_cast<Mode>(i);return true;}}
    if(s[0]>='0'&&s[0]<='9'&&!s[1]&&uint32_t(s[0]-'0')<kModeCount){out=static_cast<Mode>(s[0]-'0');return true;}
    return false;
}

inline constexpr uint32_t argb(uint32_t a,uint32_t r,uint32_t g,uint32_t b) noexcept {return (a<<24)|(r<<16)|(g<<8)|b;}
inline uint32_t surface_rgb(Surface s) noexcept {
    switch(s){
    case Surface::Tarmac:return argb(0,120,130,150);
    case Surface::Gravel:return argb(0,240,150,40);
    case Surface::HardDirt:return argb(0,165,100,50);
    case Surface::Grass:return argb(0,60,200,60);
    case Surface::Mud:return argb(0,170,80,200);
    case Surface::Water:return argb(0,40,130,255);
    case Surface::Other:return argb(0,245,235,60);
    case Surface::Object:return argb(0,245,245,245);
    case Surface::Unknown:default:return argb(0,255,40,200);
    }
}
// Slope bands of the plane normal: <=20, <=35, <=60, >60 degrees from horizontal ground.
inline constexpr std::array<float,3> kSlopeCos={0.9397f,0.8192f,0.5f};
inline constexpr std::array<const char*,4> kSlopeNames={"0-20 DEG","20-35 DEG","35-60 DEG","60-90 DEG WALL"};
inline constexpr std::array<uint32_t,4> kSlopeRgb={argb(0,60,210,80),argb(0,240,220,50),argb(0,250,140,30),argb(0,240,40,40)};
inline uint32_t slope_band(float ny) noexcept {const float c=std::fabs(ny);return c>=kSlopeCos[0]?0:c>=kSlopeCos[1]?1:c>=kSlopeCos[2]?2:3;}
inline constexpr uint32_t kFrontRgb=argb(0,40,220,230),kBackRgb=argb(0,240,40,40);
inline uint32_t with_alpha(uint32_t rgb,uint32_t a) noexcept {return (rgb&0xffffffu)|(a<<24);}
inline uint32_t scale_rgb(uint32_t c,float k) noexcept {
    auto ch=[&](int s){return std::min<uint32_t>(255u,static_cast<uint32_t>(float((c>>s)&0xff)*k+.5f));};
    return (c&0xff000000u)|(ch(16)<<16)|(ch(8)<<8)|ch(0);
}

struct Vertex {float x,y,z;uint32_t color;float u,v;};
static_assert(sizeof(Vertex)==24);

struct Settings {
    float range=500.f;       // metres around the camera (triangle sphere test)
    float depth_pull=0.003f; // fraction of the camera distance the overlay is moved toward the camera (depth fight)
};
struct Batch {
    std::vector<Vertex> fill,lines;
    bool fill_depth_test=true,lines_depth_test=true,fill_depth_write=false;
    uint32_t visible_triangles=0;
    std::array<uint32_t,kSurfaceCount> surface_triangles{};
    std::array<uint32_t,4> slope_triangles{};
    uint32_t front=0,back=0;
    void clear() noexcept {fill.clear();lines.clear();visible_triangles=0;surface_triangles={};slope_triangles={};front=back=0;}
};

inline bool triangle_visible(const Mesh& m,size_t t,const float* cam,float range) noexcept {
    const float* c=&m.centre[t*4];const float dx=c[0]-cam[0],dy=c[1]-cam[1],dz=c[2]-cam[2];const float r=range+c[3];
    return dx*dx+dy*dy+dz*dz<=r*r;
}
inline void pulled(const float* p,const float* cam,float k,Vertex& v) noexcept {
    v.x=p[0]+(cam[0]-p[0])*k;v.y=p[1]+(cam[1]-p[1])*k;v.z=p[2]+(cam[2]-p[2])*k;v.u=v.v=0.f;
}
// Per-triangle colour for the current mode (front/back facing needs the camera).
inline uint32_t triangle_rgb(const Mesh& m,size_t t,Mode mode,const float* cam,Batch& b) {
    const float* n=&m.planes[t*4];
    const Surface s=m.material_surface[m.material[t]];
    ++b.surface_triangles[static_cast<size_t>(s)];
    const uint32_t band=slope_band(n[1]);++b.slope_triangles[band];
    const float* c=&m.centre[t*4];
    // Front = -n faces the camera (drivable side of the ground; one-sided walls show their solid side).
    const bool front=-(n[0]*(cam[0]-c[0])+n[1]*(cam[1]-c[1])+n[2]*(cam[2]-c[2]))>=0.f;
    if(front)++b.front;else ++b.back;
    switch(mode){
    case Mode::Slope:return kSlopeRgb[band];
    case Mode::Facing:return front?kFrontRgb:kBackRgb;
    case Mode::Solid:case Mode::Objects:{
        // Fixed light from above: brightness from the drivable-side normal.
        const float L[3]={0.3f,0.9f,0.3162f};const float k=0.35f+0.65f*std::max(0.f,-(n[0]*L[0]+n[1]*L[1]+n[2]*L[2]));
        return scale_rgb(surface_rgb(s),k);}
    default:return surface_rgb(s);
    }
}
inline void build_batch(const Mesh& m,Mode mode,const float* cam,const Settings& cfg,Batch& b) {
    b.clear();if(mode==Mode::Off||!m.triangles())return;
    // OBJECTS: only the tag100 object faces, opaque and shaded with dark edges (the ground stays the game render).
    const bool objects_only=mode==Mode::Objects;
    const bool fill=mode==Mode::Surface||mode==Mode::Slope||mode==Mode::Facing||mode==Mode::Solid||objects_only;
    const bool lines=mode==Mode::Wire||mode==Mode::XRay||mode==Mode::Solid||objects_only;
    b.fill_depth_test=true;b.lines_depth_test=mode!=Mode::XRay;b.fill_depth_write=mode==Mode::Solid||objects_only;
    const uint32_t fill_alpha=mode==Mode::Solid||objects_only?0xff:mode==Mode::Surface?0x78:0x8c;
    const uint32_t line_alpha=mode==Mode::XRay?0xa0:mode==Mode::Solid||objects_only?0x70:0xe0;
    const float range=std::max(1.f,cfg.range);
    std::vector<uint32_t> rgb(m.triangles(),0);std::vector<uint8_t> vis(m.triangles(),0);
    for(size_t t=0;t<m.triangles();++t){
        if(degenerate_plane(&m.planes[t*4])||!triangle_visible(m,t,cam,range))continue;
        if(objects_only&&m.material_surface[m.material[t]]!=Surface::Object)continue;
        vis[t]=1;++b.visible_triangles;rgb[t]=triangle_rgb(m,t,mode,cam,b);
        if(!fill)continue;
        const uint32_t color=with_alpha(rgb[t],fill_alpha);
        for(int k=0;k<3;++k){Vertex v;pulled(&m.positions[m.indices[t*3+k]*3],cam,cfg.depth_pull,v);v.color=color;b.fill.push_back(v);}
    }
    if(!lines)return;
    const float pull=cfg.depth_pull*1.5f;
    for(size_t e=0;e+2<m.edges.size();e+=3){
        const uint32_t t=m.edges[e+2];if(!vis[t])continue;
        const uint32_t color=mode==Mode::Solid||objects_only?argb(line_alpha,0,0,0):with_alpha(scale_rgb(rgb[t],1.25f),line_alpha);
        Vertex a,c;pulled(&m.positions[m.edges[e]*3],cam,pull,a);pulled(&m.positions[m.edges[e+1]*3],cam,pull,c);
        a.color=c.color=color;b.lines.push_back(a);b.lines.push_back(c);
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Legend: 3x5 pixel font as screen-space quads (top-left corner), drawn with an orthographic pixel projection.
inline uint16_t glyph(char c) noexcept {
    // 5 rows of 3 bits (bit 2 = left column), top row in bits 14..12.
    switch(c>='a'&&c<='z'?static_cast<char>(c-'a'+'A'):c){
    case 'A':return 0x2bed;case 'B':return 0x6bae;case 'C':return 0x3923;case 'D':return 0x6b6e;case 'E':return 0x79a7;case 'F':return 0x79a4;case 'G':return 0x396b;case 'H':return 0x5bed;
    case 'I':return 0x7497;case 'J':return 0x126a;case 'K':return 0x5bad;case 'L':return 0x4927;case 'M':return 0x5fed;case 'N':return 0x6b6d;case 'O':return 0x2b6a;case 'P':return 0x6ba4;
    case 'Q':return 0x2b73;case 'R':return 0x6bad;case 'S':return 0x388e;case 'T':return 0x7492;case 'U':return 0x5b6f;case 'V':return 0x5b6a;case 'W':return 0x5bfd;case 'X':return 0x5aad;
    case 'Y':return 0x5a92;case 'Z':return 0x72a7;case '0':return 0x7b6f;case '1':return 0x2c97;case '2':return 0x73e7;case '3':return 0x72cf;case '4':return 0x5bc9;case '5':return 0x79cf;
    case '6':return 0x79ef;case '7':return 0x7249;case '8':return 0x7bef;case '9':return 0x7bcf;case '-':return 0x01c0;case ':':return 0x0410;case '/':return 0x12a4;case '.':return 0x0002;
    case '%':return 0x52a5;case '>':return 0x4454;case '<':return 0x1511;case '(':return 0x1491;case ')':return 0x4494;case '=':return 0x0e38;case '+':return 0x05d0;
    default:return 0;
    }
}
enum class LegendAnchor : uint8_t { TopCenter=0, TopLeft, TopRight, BottomCenter };
inline bool parse_anchor(const char* s,LegendAnchor& out) noexcept {
    static constexpr const char* names[4]={"TOPCENTER","TOPLEFT","TOPRIGHT","BOTTOMCENTER"};
    for(uint32_t i=0;i<4;++i){size_t k=0;bool eq=true;
        for(;names[i][k]||s[k];++k){char c=s[k];if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');if(c!=names[i][k]){eq=false;break;}}
        if(eq){out=static_cast<LegendAnchor>(i);return true;}}
    return false;
}
struct Legend {
    // Pixel coordinates of the legend's top-left corner (set by build_legend from the anchor and the screen size).
    float x=16,y=16,scale=3;LegendAnchor anchor=LegendAnchor::TopCenter;float margin=12;
    std::vector<Vertex> quads;   // 6 vertices per rectangle: a,b,c, b,d,c
    void rect(float x0,float y0,float w,float h,uint32_t color){
        const Vertex a{x0,y0,.5f,color,0,0},b{x0+w,y0,.5f,color,0,0},c{x0,y0+h,.5f,color,0,0},d{x0+w,y0+h,.5f,color,0,0};
        quads.insert(quads.end(),{a,b,c,b,d,c});
    }
    // Returns the text width in pixels.
    float text(float x0,float y0,std::string_view s,uint32_t color){
        const float px=scale;float cx=x0;
        for(char ch:s){const uint16_t gl=glyph(ch);
            for(int r=0;r<5;++r)for(int c=0;c<3;++c)if(gl&(1u<<(14-(r*3+c))))rect(cx+c*px,y0+r*px,px,px,color);
            cx+=4*px;}
        return cx-x0;
    }
    float text_width(std::string_view s) const noexcept {return static_cast<float>(s.size())*4*scale;}
};
inline std::string percent(uint32_t part,uint32_t total){
    if(!total)return "0%";const uint32_t p=static_cast<uint32_t>((uint64_t(part)*1000+total/2)/total);
    return std::to_string(p/10)+"."+std::to_string(p%10)+"%";
}
// One legend for the current mode: title, colour rows with the share of the visible triangles, source line.
// TOPCENTER/BOTTOMCENTER: two compact lines (title + source, then the colours side by side); corners: one column.
// `extra`: rows appended after the mode colours (vehicle hulls, race marker lists); the legend also shows with the
// collision overlay OFF when there are extra rows.
inline void build_legend(Legend& l,Mode mode,const Batch& b,std::string_view source,std::string_view key,uint32_t width,uint32_t height=0,std::string_view info={},
                         const std::vector<std::pair<std::string,uint32_t>>& extra={}) {
    l.quads.clear();if((mode==Mode::Off&&extra.empty())||!width)return;
    l.scale=width>=2400?4.f:width>=1600?3.f:2.f;
    const float line=7*l.scale,sw=5*l.scale,gap=2*l.scale,pad=3*l.scale;
    std::vector<std::pair<std::string,uint32_t>> rows;
    if(mode==Mode::Slope)for(size_t i=0;i<4;++i)rows.emplace_back(std::string(kSlopeNames[i])+" "+percent(b.slope_triangles[i],b.visible_triangles),kSlopeRgb[i]);
    else if(mode==Mode::Facing){rows.emplace_back("FRONT (SOLID SIDE) "+percent(b.front,b.visible_triangles),kFrontRgb);
        rows.emplace_back("BACK "+percent(b.back,b.visible_triangles),kBackRgb);}
    else for(size_t i=0;i<kSurfaceCount;++i)if(b.surface_triangles[i])
        rows.emplace_back(std::string(surface_name(static_cast<Surface>(i)))+" "+percent(b.surface_triangles[i],b.visible_triangles),surface_rgb(static_cast<Surface>(i)));
    if(mode==Mode::Off)rows.clear();
    rows.insert(rows.end(),extra.begin(),extra.end());
    const std::string title="COLLISION "+std::to_string(static_cast<uint32_t>(mode))+"/"+std::to_string(kModeCount-1)+" "+mode_name(mode)+" ("+std::string(key)+")";
    const std::string foot=std::string(source)+" TRIS "+std::to_string(b.visible_triangles);
    const bool wide=l.anchor==LegendAnchor::TopCenter||l.anchor==LegendAnchor::BottomCenter;
    float w=0,h=0;
    // Wide: colour rows side by side, wrapped at 90% of the screen width.
    const float limit=static_cast<float>(width)*0.9f;
    std::vector<std::pair<float,float>> place(rows.size());size_t row_lines=rows.empty()?0:1;
    if(wide){
        float x=0,colours=0;
        for(size_t i=0;i<rows.size();++i){const float rw=sw+gap+l.text_width(rows[i].first)+3*gap;
            if(x>0&&x+rw>limit){++row_lines;x=0;}place[i]={x,float(row_lines-1)*line};x+=rw;colours=std::max(colours,x);}
        w=std::max({l.text_width(title)+4*gap+l.text_width(foot),colours,l.text_width(info)});
        h=float(1+row_lines+(info.empty()?0:1))*line-2*l.scale;
    }else{
        w=std::max(l.text_width(title),l.text_width(foot));
        for(const auto& r:rows)w=std::max(w,sw+gap+l.text_width(r.first));
        w=std::max(w,l.text_width(info));
        h=line*((info.empty()?2.f:3.f)+static_cast<float>(rows.size()))-2*l.scale;
    }
    const float W=static_cast<float>(width),H=static_cast<float>(height?height:width*3/4);
    const float m=l.margin*l.scale/3.f+pad;
    switch(l.anchor){
    case LegendAnchor::TopLeft:l.x=m;l.y=m;break;
    case LegendAnchor::TopRight:l.x=W-m-w;l.y=m;break;
    case LegendAnchor::BottomCenter:l.x=(W-w)*.5f;l.y=H-m-h;break;
    case LegendAnchor::TopCenter:default:l.x=(W-w)*.5f;l.y=m;break;
    }
    l.x=std::floor(std::max(pad,l.x));l.y=std::floor(std::max(pad,l.y));
    l.rect(l.x-pad,l.y-pad,w+2*pad,h+2*pad,argb(0xb0,0,0,0));
    const uint32_t white=argb(0xff,255,255,255),grey=argb(0xff,175,175,175),text=argb(0xff,230,230,230);
    if(wide){
        const float tw=l.text(l.x,l.y,title,white);
        l.text(l.x+tw+4*gap,l.y,foot,grey);
        for(size_t i=0;i<rows.size();++i){const float x=l.x+place[i].first,y=l.y+line+place[i].second;
            l.rect(x,y,sw,sw,with_alpha(rows[i].second,0xff));l.text(x+sw+gap,y,rows[i].first,text);}
        if(!info.empty())l.text(l.x,l.y+line*float(1+row_lines),info,argb(0xff,255,230,120));
    }else{
        float y=l.y;l.text(l.x,y,title,white);y+=line;
        for(const auto& r:rows){l.rect(l.x,y,sw,sw,with_alpha(r.second,0xff));l.text(l.x+sw+gap,y,r.first,text);y+=line;}
        l.text(l.x,y,foot,grey);
        if(!info.empty())l.text(l.x,y+line,info,argb(0xff,255,230,120));
    }
}

// Collision under a point: the highest surface (tag1400, not BSP objects) triangle whose XZ projection contains (x,z),
// at most `above` metres over y. Height and surface for the legend's car line.
struct GroundProbe { bool hit=false; float height=0; Surface surface=Surface::Unknown; };
inline GroundProbe probe_ground(const Mesh& m,float x,float y,float z,float above=3.f) {
    GroundProbe g;
    for(size_t t=0;t<m.triangles();++t){
        const float* c=&m.centre[t*4];const float dx=c[0]-x,dz=c[2]-z;if(dx*dx+dz*dz>c[3]*c[3])continue;
        const float* n=&m.planes[t*4];if(degenerate_plane(n)||std::fabs(n[1])<1e-4f)continue;
        const Surface s=m.material_surface[m.material[t]];if(s==Surface::Object)continue;
        const float* a=&m.positions[m.indices[t*3]*3];const float* b=&m.positions[m.indices[t*3+1]*3];const float* d=&m.positions[m.indices[t*3+2]*3];
        const float d0=(b[0]-a[0])*(z-a[2])-(b[2]-a[2])*(x-a[0]),d1=(d[0]-b[0])*(z-b[2])-(d[2]-b[2])*(x-b[0]),d2=(a[0]-d[0])*(z-d[2])-(a[2]-d[2])*(x-d[0]);
        if(!((d0>=0&&d1>=0&&d2>=0)||(d0<=0&&d1<=0&&d2<=0)))continue;
        const float h=-(n[0]*x+n[2]*z+n[3])/n[1];
        if(h>y+above||(g.hit&&h<=g.height))continue;
        g.hit=true;g.height=h;g.surface=s;
    }
    return g;
}


// ---------------------------------------------------------------------------------------------------------------------
// COLLISION-DEBUG1 round 4: vehicle collision hulls. car.dx tag101 (R4B, docs/formats/dx-collision.md): base geometry
// (1 vertex = centre), f32 radius, representation A (8-vertex AABB helper), representation B (closed convex hull:
// geometry_a vertices + triangles, then per face a primary vertex loop = the polygon boundary). The hull is drawn as its
// face polygons (no triangulation diagonals).
struct Hull { std::vector<float> points; std::vector<uint32_t> edges; std::array<float,3> centre{}; float radius=0; std::array<float,6> box{}; };
namespace detail {
struct Cursor { const uint8_t* p; size_t n,o; bool ok=true;
    int32_t i32() noexcept {if(!ok||n-o<4){ok=false;return 0;}int32_t v;std::memcpy(&v,p+o,4);o+=4;return v;}
    float f() noexcept {if(!ok||n-o<4){ok=false;return 0;}float v;std::memcpy(&v,p+o,4);o+=4;return v;}
    bool count(int32_t c,size_t each) noexcept {if(!ok||c<0||c>2000000||uint64_t(c)*each>n-o){ok=false;return false;}return true;}
};
struct Geometry { std::vector<float> v; std::vector<int32_t> t; };
inline bool geometry(Cursor& c,Geometry* out) {
    const int32_t vc=c.i32(),tc=c.i32();if(!c.count(vc,12))return false;
    if(out){out->v.resize(size_t(vc)*3);for(auto& x:out->v){x=c.f();if(!std::isfinite(x))c.ok=false;}}else c.o+=size_t(vc)*12;
    if(!c.count(tc,12))return false;
    if(out){out->t.resize(size_t(tc)*3);for(auto& x:out->t){x=c.i32();if(x<0||x>=vc)c.ok=false;}}else c.o+=size_t(tc)*12;
    return c.ok;
}
// One representation; `loops` receives the primary vertex loops of the faces (indices into geometry_a).
inline bool representation(Cursor& c,Geometry* a,std::vector<std::vector<int32_t>>* loops) {
    if(!geometry(c,a)||!geometry(c,nullptr))return false;
    const int32_t refs=c.i32();if(!c.count(refs,4))return false;c.o+=size_t(refs)*4;
    const int32_t edges=c.i32();if(!c.count(edges,8))return false;c.o+=size_t(edges)*8;
    const int32_t faces=c.i32();if(c.ok&&(faces<0||faces>200000))c.ok=false;if(!c.ok)return false;
    for(int32_t f=0;f<faces;++f){
        const int32_t pc=c.i32();if(!c.count(pc,4))return false;
        std::vector<int32_t> loop;if(loops){loop.resize(size_t(pc));for(auto& x:loop)x=c.i32();}else c.o+=size_t(pc)*4;
        const int32_t sc=c.i32();if(!c.count(sc,4))return false;c.o+=size_t(sc)*4;
        if(loops)loops->push_back(std::move(loop));
    }
    if(!c.count(edges,8))return false;c.o+=size_t(edges)*8;
    for(int32_t f=0;f<faces;++f){const int32_t lc=c.i32();if(!c.count(lc,4))return false;c.o+=size_t(lc)*4;}
    if(!c.count(faces,4))return false;c.o+=size_t(faces)*4;
    return c.ok;
}
} // namespace detail
// Candidates: u32 101 with a 1-vertex/0-triangle base block; exactly one must parse to a following tag102 or tag1339.
inline bool parse_vehicle_hull(const uint8_t* data,size_t size,Hull& out,size_t* at=nullptr) {
    int found=0;Hull best;
    for(size_t o=0;o+12<=size;++o){
        if(data[o]!=101||data[o+1]||data[o+2]||data[o+3]||detail::u32(data+o+4)!=1||detail::u32(data+o+8)!=0)continue;
        detail::Cursor c{data,size,o+4};detail::Geometry base,a;std::vector<std::vector<int32_t>> loops;
        if(!detail::geometry(c,&base)||base.v.size()!=3)continue;
        const float radius=c.f();
        if(!detail::representation(c,nullptr,nullptr)||!detail::representation(c,&a,&loops)||!c.ok)continue;
        if(size-c.o<4)continue;const uint32_t next=detail::u32(data+c.o);if(next!=102&&next!=1339)continue;
        if(a.v.size()<12||loops.empty()||!std::isfinite(radius))continue;
        Hull h;h.points=a.v;h.centre={base.v[0],base.v[1],base.v[2]};h.radius=radius;
        const uint32_t nv=uint32_t(a.v.size()/3);bool bad=false;
        std::unordered_set<uint64_t> seen;
        for(const auto& loop:loops)for(size_t i=0;i<loop.size()&&!bad;++i){
            uint32_t p=uint32_t(loop[i]),q=uint32_t(loop[(i+1)%loop.size()]);if(p>=nv||q>=nv){bad=true;break;}
            if(p>q)std::swap(p,q);if(p!=q&&seen.insert((uint64_t(p)<<32)|q).second)h.edges.insert(h.edges.end(),{p,q});}
        if(bad)continue;
        h.box={FLT_MAX,FLT_MAX,FLT_MAX,-FLT_MAX,-FLT_MAX,-FLT_MAX};
        for(size_t i=0;i<h.points.size();i+=3)for(int k=0;k<3;++k){h.box[k]=std::min(h.box[k],h.points[i+k]);h.box[3+k]=std::max(h.box[3+k],h.points[i+k]);}
        ++found;best=std::move(h);if(at)*at=o;
        if(found>1)return false;
    }
    if(found!=1)return false;
    out=std::move(best);return true;
}
// Vehicle pose from gaVehicleOutputData: rows +0xbc (x), +0xcc (y), +0xdc (z = the forward the GPS reads), +0xec
// (position, the field every reader uses). The 3x3 part is used only when it is orthonormal; otherwise the pose is the
// yaw of the forward XZ vector with world up (`exact=false`).
struct VehiclePose { std::array<float,12> rows{}; bool exact=false; };
inline bool vehicle_pose(const float* m16,VehiclePose& out) noexcept {
    for(int i=0;i<16;++i)if(!std::isfinite(m16[i]))return false;
    const float* r[3]={m16,m16+4,m16+8};
    bool ortho=true;
    for(int i=0;i<3&&ortho;++i)for(int j=0;j<3;++j){float d=r[i][0]*r[j][0]+r[i][1]*r[j][1]+r[i][2]*r[j][2];if(std::fabs(d-(i==j?1.f:0.f))>2e-3f){ortho=false;break;}}
    if(ortho){for(int i=0;i<3;++i)for(int k=0;k<3;++k)out.rows[i*3+k]=r[i][k];out.exact=true;}
    else{
        float fx=m16[8],fz=m16[10];const float l=std::sqrt(fx*fx+fz*fz);if(!(l>1e-4f))return false;fx/=l;fz/=l;
        out.rows={fz,0,-fx, 0,1,0, fx,0,fz};out.exact=false;
    }
    out.rows[9]=m16[12];out.rows[10]=m16[13];out.rows[11]=m16[14];
    return true;
}
inline void pose_point(const VehiclePose& p,const float* l,float* w) noexcept {
    for(int k=0;k<3;++k)w[k]=l[0]*p.rows[k]+l[1]*p.rows[3+k]+l[2]*p.rows[6+k]+p.rows[9+k];
}
inline constexpr uint32_t kHullRgb=argb(0,255,90,40),kHullLocalRgb=argb(0,255,220,0);
inline void hull_lines(const Hull& h,const VehiclePose& pose,uint32_t color,std::vector<Vertex>& out) {
    for(size_t e=0;e+1<h.edges.size();e+=2){
        Vertex a{},b{};float w[3];
        pose_point(pose,&h.points[h.edges[e]*3],w);a.x=w[0];a.y=w[1];a.z=w[2];
        pose_point(pose,&h.points[h.edges[e+1]*3],w);b.x=w[0];b.y=w[1];b.z=w[2];
        a.color=b.color=color;out.push_back(a);out.push_back(b);
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Race markers: <MarkerLists><List Name="RaceLine"><Marker No="i"> "Marker Pos" / "Marker Dir" Vector3 values.
struct MarkerList { std::string name; std::vector<float> pos,dir; };
inline bool vector3_after(std::string_view s,size_t from,size_t to,std::string_view key,float* out) {
    const size_t k=s.find(key,from);if(k==std::string_view::npos||k>=to)return false;
    const size_t v=s.find("Value=\"",k);if(v==std::string_view::npos||v>=to)return false;
    const size_t e=s.find('"',v+7);if(e==std::string_view::npos||e>to)return false;
    std::string text(s.substr(v+7,e-v-7));const char* p=text.c_str();
    for(int i=0;i<3;++i){char* end=nullptr;const double d=std::strtod(p,&end);if(end==p||!std::isfinite(d))return false;out[i]=float(d);p=end;}
    return true;
}
inline std::vector<MarkerList> marker_lists(std::string_view xml) {
    std::vector<MarkerList> out;
    const size_t begin=xml.find("<MarkerLists>");if(begin==std::string_view::npos)return out;
    const size_t end=xml.find("</MarkerLists>",begin);const size_t stop=end==std::string_view::npos?xml.size():end;
    for(size_t at=xml.find("<List Name=\"",begin);at!=std::string_view::npos&&at<stop;at=xml.find("<List Name=\"",at+1)){
        const size_t ne=xml.find('"',at+12);if(ne==std::string_view::npos)break;
        MarkerList l;l.name=std::string(xml.substr(at+12,ne-at-12));
        const size_t le=std::min(stop,xml.find("</List>",ne));
        for(size_t m=xml.find("<Marker ",ne);m!=std::string_view::npos&&m<le;m=xml.find("<Marker ",m+1)){
            const size_t me=std::min(le,xml.find("</Marker>",m));float p[3],d[3]={0,0,0};
            if(!vector3_after(xml,m,me,"\"Marker Pos\"",p))continue;
            vector3_after(xml,m,me,"\"Marker Dir\"",d);
            l.pos.insert(l.pos.end(),p,p+3);l.dir.insert(l.dir.end(),d,d+3);
        }
        if(!l.pos.empty())out.push_back(std::move(l));
    }
    return out;
}
inline uint32_t marker_rgb(std::string_view name) noexcept {
    if(name=="RaceLine")return argb(0,255,235,40);
    if(name=="LeftInnerLimit")return argb(0,60,230,255);
    if(name=="LeftOuterLimit")return argb(0,40,110,255);
    if(name=="RightInnerLimit")return argb(0,255,160,40);
    if(name=="RightOuterLimit")return argb(0,255,50,50);
    if(name=="StartArea")return argb(0,60,255,90);
    if(name=="FinishArea")return argb(0,255,255,255);
    if(name=="Cameras")return argb(0,255,80,230);
    uint32_t h=2166136261u;for(char c:name)h=(h^uint8_t(c))*16777619u;
    return argb(0,128+(h&127),128+((h>>8)&127),128+((h>>16)&127));
}
// Short legend name ("RaceLine" -> "RACELINE", "LeftInnerLimit" -> "L-INNER").
inline std::string marker_label(std::string_view name) {
    if(name=="LeftInnerLimit")return "L-INNER";if(name=="LeftOuterLimit")return "L-OUTER";
    if(name=="RightInnerLimit")return "R-INNER";if(name=="RightOuterLimit")return "R-OUTER";
    std::string s(name.substr(0,14));for(auto& c:s)c=static_cast<char>(c>='a'&&c<='z'?c-'a'+'A':c);return s;
}
// Lines: consecutive markers joined (areas closed), a 1.5 m post at every marker, a 2 m tick along its direction.
inline void marker_lines(const std::vector<MarkerList>& lists,const float* cam,float range,std::vector<Vertex>& out,std::vector<uint32_t>& counts) {
    counts.assign(lists.size(),0);const float r2=range*range;
    auto in_range=[&](const float* p){const float dx=p[0]-cam[0],dy=p[1]-cam[1],dz=p[2]-cam[2];return dx*dx+dy*dy+dz*dz<=r2;};
    auto line=[&](const float* a,const float* b,uint32_t c){Vertex u{a[0],a[1],a[2],c,0,0},v{b[0],b[1],b[2],c,0,0};out.push_back(u);out.push_back(v);};
    for(size_t li=0;li<lists.size();++li){
        const auto& l=lists[li];const uint32_t c=with_alpha(marker_rgb(l.name),0xe8);const size_t n=l.pos.size()/3;
        const bool area=(l.name=="StartArea"||l.name=="FinishArea")&&n>=3;const bool path=l.name!="Cameras";
        for(size_t i=0;i<n;++i){
            const float* p=&l.pos[i*3];if(!in_range(p))continue;++counts[li];
            const float top[3]={p[0],p[1]+1.5f,p[2]};line(p,top,c);
            const float* d=&l.dir[i*3];const float dl=std::sqrt(d[0]*d[0]+d[1]*d[1]+d[2]*d[2]);
            if(dl>1e-3f){const float tip[3]={top[0]+d[0]/dl*2.f,top[1]+d[1]/dl*2.f,top[2]+d[2]/dl*2.f};line(top,tip,c);}
            if(path&&(i+1<n||area)){const float* q=&l.pos[((i+1)%n)*3];line(p,q,c);}
        }
    }
}

// Course-name helpers for the runtime resolver.
// A race XML (DataScene/<race>.xml) places every landscape as an entity: "en3d Model Name" = "course\<dir>\<name>"
// (DX = DataGx/Course/<dir>/<name>.dx) followed by "en3d Matrix" Row0..Row3 (row vectors, Row3 = translation).
// Retail races have one landscape with the identity; joined new courses (InvSpain, InvGrandFinal) have several,
// some rotated and moved. Equal (path, matrix) pairs are kept once.
struct LandscapeRef { std::string dx_path; std::array<float,16> matrix{1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1}; bool identity=true; };
inline bool valid_name(std::string_view s) noexcept {
    if(s.empty())return false;
    for(char c:s)if(!(std::isalnum(static_cast<unsigned char>(c))||c=='_'||c=='-'))return false;
    return true;
}
inline bool parse_row(std::string_view block,std::string_view key,float* out) {
    const size_t at=block.find(key);if(at==std::string_view::npos)return false;
    size_t q=block.find('"',at+key.size());if(q==std::string_view::npos)return false;
    const size_t e=block.find('"',q+1);if(e==std::string_view::npos)return false;
    std::string text(block.substr(q+1,e-q-1));const char* p=text.c_str();
    for(int i=0;i<4;++i){char* end=nullptr;const double v=std::strtod(p,&end);if(end==p||!std::isfinite(v))return false;out[i]=static_cast<float>(v);p=end;}
    return true;
}
inline std::vector<LandscapeRef> landscape_refs(std::string_view xml) {
    std::vector<LandscapeRef> out;
    constexpr std::string_view model="=\"course\\";
    for(size_t at=0;(at=xml.find(model,at))!=std::string_view::npos;at+=model.size()){
        const size_t d0=at+model.size(),s=xml.find('\\',d0),e=s==std::string_view::npos?s:xml.find('"',s);
        if(s==std::string_view::npos||e==std::string_view::npos||e-d0>200)continue;
        const auto dir=xml.substr(d0,s-d0),name=xml.substr(s+1,e-s-1);
        if(!valid_name(dir)||!valid_name(name))continue;
        LandscapeRef r;r.dx_path="DataGx/Course/"+std::string(dir)+"/"+std::string(name)+".dx";
        // The matrix of this entity: before the next model reference, within the entity's value list.
        const size_t next=xml.find(model,e);
        const auto block=xml.substr(e,std::min<size_t>(next==std::string_view::npos?xml.size()-e:next-e,4096));
        const size_t mat=block.find("\"en3d Matrix\"");
        if(mat!=std::string_view::npos){
            const auto rows=block.substr(mat,600);float m[16];
            if(parse_row(rows,"Row0=",m)&&parse_row(rows,"Row1=",m+4)&&parse_row(rows,"Row2=",m+8)&&parse_row(rows,"Row3=",m+12)){
                std::copy(m,m+16,r.matrix.begin());
                static constexpr float I[16]={1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};
                r.identity=std::equal(m,m+16,I);
            }
        }
        bool dup=false;
        for(const auto& o:out){bool same=o.dx_path.size()==r.dx_path.size()&&o.matrix==r.matrix;
            for(size_t k=0;same&&k<r.dx_path.size();++k)same=std::tolower(static_cast<unsigned char>(o.dx_path[k]))==std::tolower(static_cast<unsigned char>(r.dx_path[k]));
            dup|=same;}
        if(!dup)out.push_back(std::move(r));
    }
    return out;
}
inline std::string landscape_dx_path(std::string_view xml) {const auto r=landscape_refs(xml);return r.empty()?std::string():r.front().dx_path;}

// Places a landscape mesh with its entity matrix (row vectors: p' = p*M). Planes: n' = n*R renormalised,
// d' = -n'.v0' (rigid placements, as in every owner race XML).
inline void transform_mesh(Mesh& m,const std::array<float,16>& M) {
    const auto point=[&](const float* p,float* o){for(int c=0;c<3;++c)o[c]=p[0]*M[c]+p[1]*M[4+c]+p[2]*M[8+c]+M[12+c];};
    for(size_t v=0;v+2<m.positions.size();v+=3){float o[3];point(&m.positions[v],o);std::copy(o,o+3,&m.positions[v]);}
    for(size_t t=0;t<m.triangles();++t){
        float* n=&m.planes[t*4];if(degenerate_plane(n))continue;
        float r[3];for(int c=0;c<3;++c)r[c]=n[0]*M[c]+n[1]*M[4+c]+n[2]*M[8+c];
        const float l=std::sqrt(r[0]*r[0]+r[1]*r[1]+r[2]*r[2]);if(l>0)for(float& x:r)x/=l;
        const float* p=&m.positions[m.indices[t*3]*3];
        n[0]=r[0];n[1]=r[1];n[2]=r[2];n[3]=-(r[0]*p[0]+r[1]*p[1]+r[2]*p[2]);
    }
    std::array<float,3> lo{FLT_MAX,FLT_MAX,FLT_MAX},hi{-FLT_MAX,-FLT_MAX,-FLT_MAX};
    for(size_t v=0;v+2<m.positions.size();v+=3)for(int c=0;c<3;++c){lo[c]=std::min(lo[c],m.positions[v+c]);hi[c]=std::max(hi[c],m.positions[v+c]);}
    if(!m.positions.empty()){m.min=lo;m.max=hi;}
    finish_indexed(m);
}
// Appends src to dst (materials re-indexed). Returns false if the material count would not fit 16 bits.
inline bool merge_mesh(Mesh& dst,const Mesh& src) {
    if(dst.materials.size()+src.materials.size()>0xffff)return false;
    if(!dst.triangles()){dst=src;return true;}
    const uint32_t base=static_cast<uint32_t>(dst.positions.size()/3);const uint16_t mbase=static_cast<uint16_t>(dst.materials.size());
    dst.positions.insert(dst.positions.end(),src.positions.begin(),src.positions.end());
    for(uint32_t i:src.indices)dst.indices.push_back(i+base);
    dst.planes.insert(dst.planes.end(),src.planes.begin(),src.planes.end());
    for(uint16_t i:src.material)dst.material.push_back(static_cast<uint16_t>(i+mbase));
    if(!dst.edge_mask.empty()||!src.edge_mask.empty()){
        const size_t before=dst.material.size()-src.material.size();dst.edge_mask.resize(before,7);
        for(size_t t=0;t<src.material.size();++t)dst.edge_mask.push_back(t<src.edge_mask.size()?src.edge_mask[t]:uint8_t(7));
    }
    dst.materials.insert(dst.materials.end(),src.materials.begin(),src.materials.end());
    dst.material_surface.insert(dst.material_surface.end(),src.material_surface.begin(),src.material_surface.end());
    for(int c=0;c<3;++c){dst.min[c]=std::min(dst.min[c],src.min[c]);dst.max[c]=std::max(dst.max[c],src.max[c]);}
    finish_indexed(dst);
    return true;
}
inline bool same_path(std::string_view a,std::string_view b) noexcept {
    if(a.size()!=b.size())return false;
    for(size_t i=0;i<a.size();++i){char x=a[i],y=b[i];if(x=='\\')x='/';if(y=='\\')y='/';
        if(x>='A'&&x<='Z')x=static_cast<char>(x-'A'+'a');if(y>='A'&&y<='Z')y=static_cast<char>(y-'A'+'a');if(x!=y)return false;}
    return true;
}
} // namespace gfx2::colldebug
