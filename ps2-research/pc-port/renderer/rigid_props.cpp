#include "rigid_props.hpp"
#include "collision_debug.hpp"
#include "ps2_config.hpp"
#include "spline_objects.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <fstream>

namespace gfx2::ps2port {
using ps2rigid::operator+;using ps2rigid::operator-;using ps2rigid::operator*;
namespace {
std::string hex(const uint8_t* p,size_t n){std::string s;for(size_t i=0;i<n;++i){s+="0123456789abcdef"[p[i]>>4];s+="0123456789abcdef"[p[i]&15];}return s;}
struct Reader {
    const uint8_t* p;size_t n,at=0;bool ok=true;
    template<class T> T get() noexcept {T v{};if(!ok||n-at<sizeof(T)){ok=false;return v;}std::memcpy(&v,p+at,sizeof(T));at+=sizeof(T);return v;}
    std::string text(size_t size) noexcept {
        if(!ok||n-at<size){ok=false;return {};}
        const auto* s=reinterpret_cast<const char*>(p+at);size_t len=0;while(len<size&&s[len])++len;
        for(size_t i=0;i<size;++i){const unsigned char c=static_cast<unsigned char>(s[i]);if(i<len?(c<32||c>126):c!=0){ok=false;return {};}}
        at+=size;if(!len)ok=false;return std::string(s,len);
    }
    const uint8_t* bytes(size_t size) noexcept {if(!ok||n-at<size){ok=false;return nullptr;}const auto* r=p+at;at+=size;return r;}
};
bool read_file(const std::filesystem::path& path,std::vector<uint8_t>& out,uint64_t limit) {
    out.clear();std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file)return false;
    const auto size=static_cast<std::streamoff>(file.tellg());
    if(size<=0||static_cast<uint64_t>(size)>limit)return false;
    out.resize(static_cast<size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(out.data()),size);
    return static_cast<bool>(file);
}
bool bounded(float v,float limit) noexcept {return std::isfinite(v)&&std::fabs(v)<=limit;}
std::string lower(std::string s){for(auto& c:s)c=static_cast<char>(c>='A'&&c<='Z'?c-'A'+'a':c);return s;}
}

bool decode_rigid_props_layout(const uint8_t* p,size_t n,RigidPropsAsset& out) noexcept {
    out={};
    if(!p||n<44||n>kRigidPropsMaximumAssetBytes||std::memcmp(p,"PS2RGD02",8))return false;
    try {
        Reader r{p,n,8};
        const uint32_t version=r.get<uint32_t>(),textures=r.get<uint32_t>(),models=r.get<uint32_t>(),vertices=r.get<uint32_t>();
        const uint32_t points=r.get<uint32_t>(),planes=r.get<uint32_t>(),courses=r.get<uint32_t>(),props=r.get<uint32_t>();
        const uint32_t shadow=r.get<uint32_t>();
        if(!r.ok||version!=2||shadow>=textures||!textures||textures>16||!models||models>16||!vertices||vertices>65536||!points||points>4096||
           !planes||planes>4096||!courses||courses>64||!props||props>1024)return false;
        RigidPropsAsset a;
        for(uint32_t i=0;i<textures;++i){
            RigidTexture t;t.width=r.get<uint32_t>();t.height=r.get<uint32_t>();
            if(!r.ok||!t.width||!t.height||t.width>1024||t.height>1024||(t.width&(t.width-1))||(t.height&(t.height-1)))return false;
            const auto* px=r.bytes(size_t(t.width)*t.height*4);if(!px)return false;
            t.bgra.resize(size_t(t.width)*t.height);std::memcpy(t.bgra.data(),px,t.bgra.size()*4);
            a.textures.push_back(std::move(t));
        }
        struct HullRange{uint32_t first_point,point_count,first_plane,plane_count;float radius;};
        std::vector<HullRange> ranges;
        uint32_t next=0,next_point=0,next_plane=0;
        for(uint32_t i=0;i<models;++i){
            RigidModel m;m.name=r.text(16);m.material=r.get<uint32_t>();const uint32_t draws=r.get<uint32_t>();
            uint32_t f[6]{};for(auto& v:f)v=r.get<uint32_t>();m.radius=r.get<float>();
            HullRange h{};h.first_point=r.get<uint32_t>();h.point_count=r.get<uint32_t>();h.first_plane=r.get<uint32_t>();h.plane_count=r.get<uint32_t>();h.radius=r.get<float>();
            m.env=r.get<int32_t>();for(auto& x:m.aabb)x=r.get<float>();
            if(!r.ok||m.env< -1||m.env>=int32_t(textures))return false;
            for(int k=0;k<3;++k)if(!bounded(m.aabb[size_t(k)],100.f)||!bounded(m.aabb[size_t(k)+3],100.f)||!(m.aabb[size_t(k)+3]>m.aabb[size_t(k)]))return false;
            if(!r.ok||m.material>kRigidMaterialMetal||draws<1||draws>2||!bounded(m.radius,100.f)||!(m.radius>0.f))return false;
            if(h.first_point!=next_point||h.point_count<4||h.point_count>points-next_point||h.first_plane!=next_plane||h.plane_count<4||
               h.plane_count>planes-next_plane||!bounded(h.radius,100.f)||!(h.radius>0.f))return false;
            next_point+=h.point_count;next_plane+=h.plane_count;
            for(uint32_t d=0;d<draws;++d){
                RigidModelDraw draw{f[d*3],f[d*3+1],f[d*3+2]};
                if(draw.texture>=textures||draw.first!=next||!draw.count||draw.count%3||draw.count>vertices-next)return false;
                next+=draw.count;m.draws.push_back(draw);
            }
            for(uint32_t d=draws;d<2;++d)if(f[d*3]||f[d*3+1]||f[d*3+2])return false;
            a.models.push_back(std::move(m));ranges.push_back(h);
        }
        if(next!=vertices||next_point!=points||next_plane!=planes)return false;
        const auto* vb=r.bytes(size_t(vertices)*sizeof(ObjectVertex));if(!vb)return false;
        a.vertices.resize(vertices);std::memcpy(a.vertices.data(),vb,size_t(vertices)*sizeof(ObjectVertex));
        for(const auto& v:a.vertices)if(!bounded(v.x,100.f)||!bounded(v.y,100.f)||!bounded(v.z,100.f)||!std::isfinite(v.u)||!std::isfinite(v.v))return false;
        a.normals.resize(vertices);
        for(auto& q:a.normals){q={r.get<float>(),r.get<float>(),r.get<float>()};if(!r.ok||!bounded(q[0],2.f)||!bounded(q[1],2.f)||!bounded(q[2],2.f))return false;}
        a.shadow_texture=shadow;
        std::vector<ps2rigid::V3> pts(points);
        for(auto& q:pts){q={r.get<float>(),r.get<float>(),r.get<float>()};if(!r.ok||!bounded(q[0],100.f)||!bounded(q[1],100.f)||!bounded(q[2],100.f))return false;}
        std::vector<std::array<float,4>> pls(planes);
        for(auto& q:pls){for(auto& x:q)x=r.get<float>();if(!r.ok)return false;
            const float l=std::sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]);if(!std::isfinite(q[3])||std::fabs(l-1.f)>1e-3f)return false;}
        for(size_t i=0;i<a.models.size();++i){
            auto& h=a.models[i].hull;const auto& g=ranges[i];
            h.points.assign(pts.begin()+g.first_point,pts.begin()+g.first_point+g.point_count);
            h.planes.assign(pls.begin()+g.first_plane,pls.begin()+g.first_plane+g.plane_count);
            h.radius=g.radius;
            // Convexity: every point on or inside every plane; the radius bounds every point.
            for(const auto& q:h.planes)for(const auto& v:h.points)if(q[0]*v[0]+q[1]*v[1]+q[2]*v[2]+q[3]>1e-3f)return false;
            for(const auto& v:h.points)if(ps2rigid::length(v)>h.radius+1e-3f)return false;
            if(!h.valid())return false;
        }
        uint32_t first=0;
        for(uint32_t i=0;i<courses;++i){
            RigidCourseDef c;c.id=r.text(48);c.dx_path=r.text(64);
            const auto* sha=r.bytes(32);c.first=r.get<uint32_t>();c.count=r.get<uint32_t>();
            if(!r.ok||!sha||c.first!=first||!c.count||c.count>kRigidMaximumPropsPerCourse||c.count>props-first)return false;
            std::memcpy(c.retail_sha.data(),sha,32);first+=c.count;
            for(const auto& other:a.courses)if(course_id_matches(other.id,c.id))return false;
            a.courses.push_back(std::move(c));
        }
        if(first!=props)return false;
        for(uint32_t i=0;i<props;++i){
            RigidPropDef o;o.egg=r.text(32);o.model=r.get<uint32_t>();const uint32_t flags=r.get<uint32_t>();
            o.mass=r.get<float>();for(auto& x:o.moi)x=r.get<float>();o.trigger=r.get<float>();
            for(auto& x:o.matrix)x=r.get<float>();
            if(!r.ok||o.model>=models||flags>3||!bounded(o.mass,100000.f)||!(o.mass>0.f)||!std::isfinite(o.trigger))return false;
            for(auto x:o.moi)if(!bounded(x,1e7f)||!(x>0.f))return false;
            for(int k=0;k<9;++k)if(!bounded(o.matrix[size_t(k)],1.1f))return false;
            for(int k=9;k<12;++k)if(!bounded(o.matrix[size_t(k)],100000.f))return false;
            o.casts_shadow=flags&kRigidFlagShadow;o.checkpoint=(flags&kRigidFlagCheckpoint)!=0;
            // Barrels are always the checkpoint model, never an authored family; the other props never carry the flag.
            if(o.checkpoint!=(a.models[o.model].name=="checkpoint"))return false;
            a.props.push_back(std::move(o));
        }
        if(!r.ok||r.at!=n)return false;
        out=std::move(a);return true;
    } catch(...) {out={};return false;}
}
bool decode_rigid_props_asset(const uint8_t* p,size_t n,std::string_view digest,RigidPropsAsset& out) noexcept {
    out={};
    return std::string_view(kRigidPropsArtifactSha).size()==64&&digest==kRigidPropsArtifactSha&&decode_rigid_props_layout(p,n,out);
}
size_t rigid_course_index(const RigidPropsAsset& a,std::string_view id) noexcept {
    for(size_t i=0;i<a.courses.size();++i)if(course_id_matches(id,a.courses[i].id))return i;
    return SIZE_MAX;
}
void rigid_material_coefficients(uint32_t material,float& restitution,float& friction,float& rolling) noexcept {
    // Port values: a pressed hay bale barely bounces and grips; a tumbleweed is light, springy and rolls.
    if(material==kRigidMaterialTreeblend){restitution=.35f;friction=.45f;rolling=1.f;}
    // A steel drum rings off a bumper, slides on gravel and rolls on its side.
    else if(material==kRigidMaterialMetal){restitution=.3f;friction=.5f;rolling=1.5f;}
    else{restitution=.15f;friction=.7f;rolling=2.5f;}
}
std::vector<uint32_t> rigid_members(const RigidPropsAsset& a,size_t course,RigidSelection s) noexcept {
    std::vector<uint32_t> out;
    try{
        if(course>=a.courses.size())return out;
        const auto& c=a.courses[course];
        for(uint32_t i=0;i<c.count;++i){const auto& o=a.props[c.first+i];if(o.checkpoint?s.barrels:s.props)out.push_back(c.first+i);}
    }catch(...){out.clear();}
    return out;
}

bool rigid_terrain_from_course_dx(const uint8_t* data,size_t size,ps2rigid::Terrain& out,size_t& records) noexcept {
    out.clear();records=0;
    try{
        colldebug::Mesh m;
        if(colldebug::parse_course_dx(data,size,m)!=colldebug::ParseResult::Ok)return false;
        const size_t n=m.triangles();records=n;
        std::vector<float> corners(n*9);std::vector<uint8_t> water(n,0);
        for(size_t t=0;t<n;++t){
            for(int k=0;k<3;++k)for(int c=0;c<3;++c)corners[t*9+size_t(k)*3+size_t(c)]=m.positions[size_t(m.indices[t*3+size_t(k)])*3+size_t(c)];
            water[t]=m.material[t]<m.material_surface.size()&&m.material_surface[m.material[t]]==colldebug::Surface::Water;
        }
        return out.build(corners,m.planes,8.f,&water);
    }catch(...){out.clear();return false;}
}

bool rigid_vehicle_hull(const uint8_t* data,size_t size,ps2rigid::Hull& out) noexcept {
    out={};
    try{
        int found=0;ps2rigid::Hull best;
        for(size_t o=0;o+12<=size;++o){
            if(data[o]!=101||data[o+1]||data[o+2]||data[o+3]||colldebug::detail::u32(data+o+4)!=1||colldebug::detail::u32(data+o+8)!=0)continue;
            colldebug::detail::Cursor c{data,size,o+4};colldebug::detail::Geometry base,a;std::vector<std::vector<int32_t>> loops;
            if(!colldebug::detail::geometry(c,&base)||base.v.size()!=3)continue;
            const float radius=c.f();
            if(!colldebug::detail::representation(c,nullptr,nullptr)||!colldebug::detail::representation(c,&a,&loops)||!c.ok)continue;
            if(size-c.o<4)continue;const uint32_t next=colldebug::detail::u32(data+c.o);if(next!=102&&next!=1339)continue;
            if(a.v.size()<12||loops.empty()||!std::isfinite(radius))continue;
            std::vector<ps2rigid::V3> pts(a.v.size()/3);
            for(size_t i=0;i<pts.size();++i)pts[i]={a.v[i*3],a.v[i*3+1],a.v[i*3+2]};
            std::vector<std::vector<uint32_t>> l;
            bool bad=false;
            for(const auto& loop:loops){std::vector<uint32_t> q;for(auto x:loop){if(x<0||size_t(x)>=pts.size()){bad=true;break;}q.push_back(uint32_t(x));}l.push_back(std::move(q));}
            ps2rigid::Hull h;
            if(bad||!ps2rigid::hull_from_loops(pts,l,h))continue;
            ++found;best=std::move(h);
            if(found>1)return false;
        }
        if(found!=1)return false;
        out=std::move(best);return true;
    }catch(...){out={};return false;}
}

bool RigidCourseRuntime::start(const RigidPropsAsset& a,size_t course,const ps2rigid::Terrain& terrain,uint64_t race,RigidSelection selection) noexcept {
    stop();
    if(course>=a.courses.size()||!race||terrain.empty())return false;
    try{
        members_=rigid_members(a,course,selection);
        if(members_.empty()){stop();return false;}
        std::vector<ps2rigid::BodyDef> defs;
        for(const uint32_t index:members_){
            const auto& o=a.props[index];const auto& m=a.models[o.model];barrels_+=o.checkpoint;
            ps2rigid::BodyDef d;d.hull=&m.hull;d.mass=o.mass;d.moi=o.moi;d.matrix=o.matrix;
            rigid_material_coefficients(m.material,d.restitution,d.friction,d.rolling);
            defs.push_back(d);
        }
        if(!world_.start(&terrain,defs)){stop();return false;}
    }catch(...){stop();return false;}
    asset_=&a;terrain_=&terrain;course_=course;race_=race;return true;
}
void RigidCourseRuntime::cars(const std::vector<RigidCarInput>& in,const std::unordered_map<std::string,const ps2rigid::Hull*>& hulls,double now,
                              std::vector<ps2rigid::Kinematic>& out) noexcept {
    out.clear();
    try{
        for(const auto& car:in){
            if(!car.pose_valid||!car.instance)continue;
            const auto h=hulls.find(lower(car.folder));if(h==hulls.end()||!h->second)continue;
            ps2rigid::Pose pose;if(!ps2rigid::pose_from_rows(car.rows.data(),pose))continue;
            ps2rigid::Kinematic k;k.hull=h->second;k.pose=pose;k.valid=true;
            if(car.body&&car.mass>0.f&&std::isfinite(car.mass)&&ps2rigid::finite(car.com)){k.mass=car.mass;k.com=car.com;k.body=car.body;}
            auto& track=cars_[car.instance];
            if(track.have)ps2rigid::pose_velocity(track.pose,pose,now-track.time,k.v,k.w);
            track.pose=pose;track.time=now;track.have=true;
            out.push_back(k);
        }
    }catch(...){out.clear();}
}
unsigned RigidCourseRuntime::advance(double seconds,bool paused,ps2rigid::TickInput& in) noexcept {
    if(!ready()||paused)return 0;
    const unsigned n=clock_.advance(seconds);tick(n,in);return n;
}
void RigidCourseRuntime::tick(unsigned n,ps2rigid::TickInput& in) noexcept {
    if(!ready())return;
    try{for(unsigned i=0;i<n;++i)world_.tick(in);}catch(...){world_.stop();}
}
void rigid_shadow_triangles(const ps2rigid::Terrain& t,const ps2rigid::Pose& pose,const std::array<float,6>& aabb,std::vector<ObjectVertex>& out) {
    using ps2rigid::V3;
    // Yaw frame from the prop's forward axis (R column 2), as 332628 builds it: right = (f.z, 0, -f.x), forward = (f.x, 0, f.z).
    const V3 f{pose.r.m[2],pose.r.m[5],pose.r.m[8]},up{pose.r.m[1],pose.r.m[4],pose.r.m[7]};
    V3 right{f[2],0,-f[0]};float l=ps2rigid::length(right);
    if(!(l>1e-4f)){right={1,0,0};l=1;}
    right=right*(1.f/l);const V3 fwd{-right[2],0,right[0]};
    const float cx=(aabb[0]+aabb[3])*.5f,cy=(aabb[1]+aabb[4])*.5f,cz=(aabb[2]+aabb[5])*.5f;
    const float sx=(aabb[3]-aabb[0])*1.75f,sz=(aabb[5]-aabb[2])*1.5f;
    const V3 centre=ps2rigid::apply(pose,{cx,cy,cz});
    const float radius=std::max(sx,sz)*.5f;
    t.for_near(centre[0],centre[2],radius,[&](const float* c,const float* q,bool water){
        // Solid side towards +n: the up normal of a ground triangle is -n.
        const float ny=-q[1];
        if(water||!(ny>.05f))return;
        if(!(c[1]<centre[1]||c[4]<centre[1]||c[7]<centre[1]))return;
        ObjectVertex v[3];
        for(int k=0;k<3;++k){
            const V3 p{c[k*3],c[k*3+1]+.1f,c[k*3+2]};
            const V3 d=p-pose.t;
            const float lx=ps2rigid::dot(d,right),lz=ps2rigid::dot(d,fwd);
            const float depth=ps2rigid::dot(centre-p,up)-.5f;
            const float att=depth>=0.f?1.f/(depth*.75f+1.f):1.f;
            const float a=std::clamp(ny*.85f*att,0.f,1.f);
            v[k]={p[0],p[1],p[2],DWORD(uint32_t(a*255.f+.5f))<<24,(lx-cx)/sx+.5f,(lz-cz)/sz+.5f};
        }
        // The texture border is transparent; skip triangles entirely outside the box.
        const float u0=std::min({v[0].u,v[1].u,v[2].u}),u1=std::max({v[0].u,v[1].u,v[2].u});
        const float v0=std::min({v[0].v,v[1].v,v[2].v}),v1=std::max({v[0].v,v[1].v,v[2].v});
        if(u1<0.f||u0>1.f||v1<0.f||v0>1.f)return;
        out.push_back(v[0]);out.push_back(v[1]);out.push_back(v[2]);
    });
}

bool RigidCourseRuntime::build(const ps2rigid::V3& camera,const float* view,float shadow_range,std::vector<RigidBatch>& out) const noexcept {
    out.clear();if(!ready()||!view)return false;
    try{
        const float alpha=clock_.fraction();
        std::vector<RigidBatch> objects,env,blend;RigidBatch shadow{asset_->shadow_texture,kRigidMaterialObject,RigidPass::Shadow,0,{}};
        auto batch=[](std::vector<RigidBatch>& list,uint32_t texture,uint32_t material,RigidPass pass)->RigidBatch& {
            for(auto& b:list)if(b.texture==texture&&b.material==material)return b;
            list.push_back({texture,material,pass,0,{}});return list.back();
        };
        for(size_t i=0;i<members_.size();++i){
            const auto& o=asset_->props[members_[i]];const auto& m=asset_->models[o.model];
            const auto pose=world_.pose(i,alpha);
            const auto d=pose.t-camera;const float distance=ps2rigid::dot(d,d);
            if(o.casts_shadow&&terrain_&&distance<=shadow_range*shadow_range)rigid_shadow_triangles(*terrain_,pose,m.aabb,shadow.vertices);
            for(const auto& draw:m.draws){
                RigidBatch* target=nullptr;
                if(m.material==kRigidMaterialTreeblend){blend.push_back({draw.texture,m.material,RigidPass::Treeblend,distance,{}});target=&blend.back();}
                else target=&batch(objects,draw.texture,m.material,RigidPass::Object);
                RigidBatch* layer=m.env>=0?&batch(env,uint32_t(m.env),m.material,RigidPass::Env):nullptr;
                for(uint32_t v=draw.first;v<draw.first+draw.count;++v){
                    auto vertex=asset_->vertices[v];
                    const auto w=ps2rigid::apply(pose,{vertex.x,vertex.y,vertex.z});
                    if(!ps2rigid::finite(w)){out.clear();return false;}
                    vertex.x=w[0];vertex.y=w[1];vertex.z=w[2];target->vertices.push_back(vertex);
                    if(layer){
                        // REFL1 environment coordinates: UV = (0.5, 0.5) + (0.5 n.x, -0.5 n.y) of the view-space normal.
                        const auto n=ps2rigid::mul(pose.r,asset_->normals[v]);
                        const float nx=n[0]*view[0]+n[1]*view[4]+n[2]*view[8],ny=n[0]*view[1]+n[1]*view[5]+n[2]*view[9];
                        ObjectVertex e=vertex;e.color=0xffffffffu;e.u=.5f+.5f*nx;e.v=.5f-.5f*ny;layer->vertices.push_back(e);
                    }
                }
            }
        }
        std::stable_sort(blend.begin(),blend.end(),[](const RigidBatch& a,const RigidBatch& b){return a.distance>b.distance;});
        if(!shadow.vertices.empty())out.push_back(std::move(shadow));
        for(auto& b:objects)out.push_back(std::move(b));
        for(auto& b:env)out.push_back(std::move(b));
        for(auto& b:blend)out.push_back(std::move(b));
        return true;
    }catch(...){out.clear();return false;}
}

RigidPropsPilot::RigidPropsPilot(bool supported,const std::wstring& ini) noexcept {
    if(!supported){reason_="unsupported_build_stock";return;}
    // RigidProps=1: hay bales and tumbleweeds; PS2CheckpointBarrels=1: checkpoint barrels (COURSE-ALIVE4). Either one loads
    // the shared asset and World.
    selection_.props=config::read_int(L"RigidProps",0,ini.c_str())==1;
    selection_.barrels=config::read_int(L"PS2CheckpointBarrels",0,ini.c_str())==1;
    if(!selection_.props&&!selection_.barrels)return;
    requested_=true;
    diagnostics_=config::read_int(L"RigidPropsDiagnostics",0,ini.c_str())==1;
    stock_courses_=config::read_int(L"RigidPropsStockCourses",0,ini.c_str())==1;
    car_impulse_=config::read_int(L"RigidPropsCarImpulse",1,ini.c_str())==1;
    try{
        game_root_=std::filesystem::path(ini).parent_path().wstring();
        archive_path_=(std::filesystem::path(game_root_)/L"Data.sma").wstring();
        wchar_t dir[32768]{},path[32768]{};
        config::read_string(L"GrassAssetDirectory",L".",dir,32768,ini.c_str());
        const std::wstring fallback=std::wstring(dir)+L"\\PS2RigidProps.ps2rgd";
        const auto count=config::read_string(L"RigidPropsAsset",fallback.c_str(),path,32768,ini.c_str());
        if(!count||count>=32767){reason_="invalid_asset_path";return;}
        std::filesystem::path input(path);if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
        std::vector<uint8_t> bytes;
        if(!read_file(input,bytes,kRigidPropsMaximumAssetBytes)){reason_="missing_or_wrong_size_rigid_props_asset";return;}
        verified_=decode_rigid_props_asset(bytes.data(),bytes.size(),sha256_bytes(bytes.data(),bytes.size()),asset_);
        reason_=verified_?"verified_rigid_props_waiting_for_device":"rigid_props_asset_hash_or_layout_mismatch";
    }catch(...){reason_="rigid_props_asset_load_failed_stock";verified_=false;}
}
void RigidPropsPilot::release_textures() noexcept {for(auto* t:textures_)if(t)t->Release();textures_.clear();}
bool RigidPropsPilot::initialize(IDirect3DDevice8& device) noexcept {
    if(!identity_requested()||suspended_||blocked_)return false;
    release_textures();
    D3DCAPS8 caps{};HRESULT hr=device.GetDeviceCaps(&caps);
    if(FAILED(hr)||caps.MaxPrimitiveCount<1024){disable("unsupported_rigid_device_caps");return false;}
    try{
        for(const auto& t:asset_.textures){
            if(caps.MaxTextureWidth<t.width||caps.MaxTextureHeight<t.height){release_textures();disable("unsupported_rigid_texture_size");return false;}
            IDirect3DTexture8* texture=nullptr;
            hr=device.CreateTexture(t.width,t.height,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture);
            if(FAILED(hr)||!texture){if(texture)texture->Release();release_textures();disable("rigid_texture_creation_failed");return false;}
            textures_.push_back(texture);
            D3DLOCKED_RECT lock{};hr=texture->LockRect(0,&lock,nullptr,0);
            if(SUCCEEDED(hr)){
                const bool valid=lock.pBits&&lock.Pitch>=INT(t.width*4);
                if(valid)for(uint32_t row=0;row<t.height;++row)std::memcpy(static_cast<uint8_t*>(lock.pBits)+size_t(row)*lock.Pitch,t.bgra.data()+size_t(row)*t.width,size_t(t.width)*4);
                const auto unlocked=texture->UnlockRect(0);if(!valid||FAILED(unlocked))hr=E_FAIL;
            }
            if(FAILED(hr)){release_textures();disable("rigid_texture_upload_failed");return false;}
        }
    }catch(...){release_textures();disable("rigid_texture_creation_failed");return false;}
    reason_="rigid_props_ready";return true;
}
void RigidPropsPilot::finish_job() noexcept {
    if(!loading_||!job_done_.load())return;
    if(worker_.joinable())worker_.join();
    loading_=false;
    terrain_path_=job_.dx_path;terrain_=std::move(job_.terrain);terrain_records_=job_.records;terrain_reason_=job_.reason;terrain_ms_=job_.ms;
    job_=TerrainJob{};
    course_log_pending_=true;
}
bool RigidPropsPilot::select_course(std::string_view id,uint64_t race) noexcept {
    if(!active()||!race){runtime_.stop();return false;}
    const size_t course=rigid_course_index(asset_,id);
    if(course==SIZE_MAX||rigid_members(asset_,course,selection_).empty()){runtime_.stop();barrel_race_=0;guard_reason_="not_a_prop_course";return false;}
    if(runtime_.ready()&&runtime_.course()==course&&runtime_.race()==race)return true;
    // A new race or course: the old World refers to the current landscape, which the finished job may replace.
    runtime_.stop();barrel_race_=0;
    finish_job();
    const auto& def=asset_.courses[course];
    std::filesystem::path file;
    try{file=std::filesystem::path(game_root_)/std::filesystem::path(def.dx_path);}catch(...){guard_reason_="course_dx_unreadable";return false;}
    if(guard_race_!=race||guard_course_!=course){
        guard_race_=race;guard_course_=course;
        try{
            std::error_code error;const bool loose=std::filesystem::is_regular_file(file,error);
            guard_reason_=spline_course_guard(def.retail_sha,loose,loose?sha256_file(file.wstring()):std::string());
        }catch(...){guard_reason_="course_dx_unreadable";}
        if(stock_courses_&&std::strncmp(guard_reason_,"stock_pc_course",15)==0)guard_reason_="stock_pc_course_allowed_by_ini";
        course_log_pending_=true;
    }
    if(std::strcmp(guard_reason_,"ps2_course_package")&&std::strcmp(guard_reason_,"stock_pc_course_allowed_by_ini")){runtime_.stop();return false;}
    // Landscape of this course: loaded once on a worker thread, kept while the course stays the same.
    if(terrain_path_!=def.dx_path||terrain_.empty()){
        if(loading_)return false;
        if(terrain_path_==def.dx_path&&std::strcmp(terrain_reason_,"loaded"))return false;  // failed before: stay off
        try{
            job_=TerrainJob{};job_.dx_path=def.dx_path;job_done_=false;loading_=true;terrain_reason_="loading";
            std::wstring path=file.wstring();
            worker_=std::thread([this,path]() noexcept {
                const auto t0=std::chrono::steady_clock::now();
                try{
                    std::vector<uint8_t> bytes;
                    if(!read_file(path,bytes,512ull*1024*1024))job_.reason="course_dx_unreadable";
                    else job_.reason=rigid_terrain_from_course_dx(bytes.data(),bytes.size(),job_.terrain,job_.records)?"loaded":"course_collision_not_parsed";
                }catch(...){job_.reason="course_collision_load_failed";}
                job_.ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t0).count();
                job_done_=true;
            });
        }catch(...){loading_=false;terrain_reason_="worker_not_started";}
        return false;
    }
    if(!runtime_.start(asset_,course,terrain_,race,selection_)){guard_reason_="rigid_world_start_failed";runtime_.stop();return false;}
    barrel_race_=runtime_.barrels()?race:0;
    last_qpc_=0;last_state_log_=0;advanced_frame_=UINT64_MAX;course_log_pending_=true;
    return true;
}
void RigidPropsPilot::ensure_roots() noexcept {
    if(roots_ready_)return;roots_ready_=true;
    try{
        std::vector<std::filesystem::path> folders;
        wchar_t cwd[32768]{};const DWORD n=GetCurrentDirectoryW(32768,cwd);
        if(n&&n<32768)folders.emplace_back(cwd);
        folders.emplace_back(game_root_);
        for(const auto& f:folders){
            std::error_code error;const auto canon=std::filesystem::weakly_canonical(f,error);
            bool seen=false;for(const auto& r:roots_)if(std::filesystem::equivalent(r.folder,canon,error))seen=true;
            if(seen)continue;
            GameRoot r;r.folder=canon;
            r.archive=std::make_unique<sma::Archive>();r.archive->open((canon/L"Data.sma").wstring());
            roots_.push_back(std::move(r));
        }
    }catch(...){}
}
bool RigidPropsPilot::read_game_file(const std::string& rel,std::vector<uint8_t>& out,uint64_t limit) const {
    out.clear();
    for(const auto& r:roots_){
        std::error_code error;const auto loose=r.folder/std::filesystem::path(rel);
        if(std::filesystem::is_regular_file(loose,error)&&read_file(loose,out,limit))return true;
        if(r.archive&&r.archive->is_open()&&r.archive->read(rel,out,limit))return true;
    }
    out.clear();return false;
}
const ps2rigid::Hull* RigidPropsPilot::hull(const std::string& folder) noexcept {
    try{
        const std::string key=lower(folder);
        const auto it=hulls_.find(key);if(it!=hulls_.end())return it->second.get();
        ensure_roots();
        std::unique_ptr<ps2rigid::Hull> h;std::vector<uint8_t> bytes;
        if(read_game_file("DataGx/Vehicles/"+folder+"/car.dx",bytes,64ull*1024*1024)){
            auto parsed=std::make_unique<ps2rigid::Hull>();if(rigid_vehicle_hull(bytes.data(),bytes.size(),*parsed))h=std::move(parsed);}
        if(!h)missing_hulls_+=(missing_hulls_.empty()?"":",")+folder;
        auto* raw=h.get();hulls_.emplace(key,std::move(h));
        return raw;
    }catch(...){return nullptr;}
}
double RigidPropsPilot::host_seconds() const noexcept {
    LARGE_INTEGER now{},frequency{};QueryPerformanceCounter(&now);QueryPerformanceFrequency(&frequency);
    return frequency.QuadPart>0?double(now.QuadPart)/double(frequency.QuadPart):0.0;
}
unsigned RigidPropsPilot::advance_frame(uint64_t frame,bool paused,ps2rigid::TickInput& in) noexcept {
    if(!runtime_.ready()||advanced_frame_==frame)return 0;
    advanced_frame_=frame;
    LARGE_INTEGER now{},frequency{};QueryPerformanceCounter(&now);QueryPerformanceFrequency(&frequency);
    const uint64_t previous=last_qpc_;last_qpc_=static_cast<uint64_t>(now.QuadPart);
    if(!previous||frequency.QuadPart<=0)return 0;
    return runtime_.advance(double(static_cast<uint64_t>(now.QuadPart)-previous)/double(frequency.QuadPart),paused,in);
}
bool RigidPropsPilot::claim_state_log() noexcept {
    if(!diagnostics_||!runtime_.ready())return false;
    const uint64_t slot=runtime_.world().ticks()/150+1;if(slot==last_state_log_)return false;last_state_log_=slot;return true;
}
int RigidPropsPilot::board_texture(IDirect3DBaseTexture8* base,uint64_t generation) noexcept {
    const auto id=reinterpret_cast<uintptr_t>(base);
    if(!base||!generation)return 0;
    for(const auto& c:boards_)if(c.texture==id&&c.generation==generation)return c.kind;
    BoardIdentity result{id,generation,0};
    try{
        D3DSURFACE_DESC desc{};
        if(base->GetType()==D3DRTYPE_TEXTURE){
            auto* t=static_cast<IDirect3DTexture8*>(base);
            if(SUCCEEDED(t->GetLevelDesc(0,&desc))&&desc.Width==128&&desc.Height==128&&desc.Pool!=D3DPOOL_DEFAULT&&
               (desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8)){
                D3DLOCKED_RECT lock{};
                if(SUCCEEDED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY))){
                    std::vector<uint8_t> rows(128u*128u*4u);bool ok=lock.pBits&&lock.Pitch>=INT(128*4);
                    if(ok)for(UINT y=0;y<128;++y)std::memcpy(rows.data()+size_t(y)*512,static_cast<const uint8_t*>(lock.pBits)+size_t(y)*lock.Pitch,512);
                    t->UnlockRect(0);
                    if(ok&&desc.Format==D3DFMT_X8R8G8B8)for(size_t i=3;i<rows.size();i+=4)rows[i]=0xff;
                    if(ok){const auto sha=sha256_bytes(rows.data(),rows.size());result.kind=sha==kPcCheckpointPlanksSha?1:sha==kPcCheckpointStampSha?2:0;}
                }
            }
        }
    }catch(...){result.kind=0;}
    boards_[next_board_]=result;next_board_=(next_board_+1)%boards_.size();
    return result.kind;
}
void RigidPropsPilot::before_reset() noexcept {
    proof.clear();if(transaction.has_pending())blocked_=true;transaction.release();
    release_textures();consumed_frame_=UINT64_MAX;
}
void RigidPropsPilot::after_reset(IDirect3DDevice8& device,bool called,bool success) noexcept {
    if(!called)return;if(!success){suspended_=true;return;}
    blocked_=suspended_=false;initialize(device);
}
void RigidPropsPilot::shutdown() noexcept {
    proof.clear();transaction.release();release_textures();runtime_.stop();disabled_=true;
    if(worker_.joinable())worker_.join();
    loading_=false;
}
} // namespace gfx2::ps2port
