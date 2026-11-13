#pragma once
#include "atmosphere_body_common.hpp"
#include "atmosphere_body_binding.hpp"
#include "reflection_pilot.hpp"
#include "reflection_paint_authority.hpp"
#include <unordered_map>
#include <set>
namespace gfx2::atmospherebody {
// Capture before private body uploads/emissive changes. Switch nodes may precede
// their parent's verified draw: owner resolution happens once at before-UI.
inline void collect_lamp_attachment(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc)noexcept {
    auto* p=atmosphereintegration::pilot(d);
    if(!p||!p->enabled()||!p->lighting.active()||p->lighting.ambient_strength>=.5f||!p->glint_style.enabled||!p->lamp_attachments.ready||
       type!=D3DPT_TRIANGLELIST||!count||!vertices||vertices>4096||count>32768||p->pending.any()||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||d.trace.shadow.recording||
       d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return;
    try {
        auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return;
        DWORD fvf=0,pixel=1;if(FAILED(n.GetVertexShader(&fvf))||(fvf!=0x142&&fvf!=0x152)||FAILED(n.GetPixelShader(&pixel))||pixel||
           !groundintegration::render(d,n,D3DRS_LIGHTING,FALSE))return;
        courseintegration::Ref<IDirect3DSurface8> target,back;
        if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return;
        courseintegration::Ref<IDirect3DBaseTexture8> texture;if(FAILED(n.GetTexture(0,&texture.p))||!texture.p)return;
        const auto pointer=reinterpret_cast<uintptr_t>(texture.p);const auto generation=d.trace.resources.generation(pointer);if(!generation)return;
        const std::string* cached=nullptr;
        for(const auto& entry:p->attachment_textures)if(entry.pointer==pointer&&entry.generation==generation){cached=&entry.sha;break;}
        if(!cached){auto& entry=p->attachment_textures[p->attachment_texture_next++%p->attachment_textures.size()];
            entry.pointer=pointer;entry.generation=generation;entry.sha=atmosphereintegration::material_sha(d,*p,texture.p);cached=&entry.sha;}
        const auto& sha=*cached;if(!p->lamp_attachments.texture_known(sha))return;
        D3DMATRIX matrix{};if(FAILED(n.GetTransform(D3DTS_WORLD,&matrix)))return;atmosphere::Mat4 world{};std::memcpy(world.data(),&matrix,64);
        for(float x:world)if(!std::isfinite(x))return;
        uintptr_t instance=0;frontendmodelintegration::Context owner;
        if(frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner)&&frontendmodelintegration::fleet_owner_world(owner,matrix)){
            uint32_t name_id=0;std::string resource;const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
            if(frontendmodelintegration::word(owner.owner.packet+0xc,name_id)&&atmosphere::native_name(exe,name_id,frontendmodelintegration::word,resource)){
                for(auto& c:resource){c=char(std::tolower(static_cast<unsigned char>(c)));if(c=='\\')c='/';}
                const auto slash=resource.find('/',9);
                if(resource.rfind("vehicles/",0)==0&&slash!=std::string::npos&&resource.substr(slash+1)=="car"){
                    instance=owner.owner.instance;p->observe_car(instance,world,d.trace.frame_number());}
            }
        }
        auto& queue=p->lamp_attachment_queue;queue.begin(d.trace.frame_number(),cert.race_generation,d.ps2_port()->reset_generation());
        if(queue.resolved==queue.frame)return;++queue.candidates;
        p->pending.release();struct Release{atmosphere::Pilot& p;~Release(){p.pending.release();}}release{*p};
        atmosphereintegration::Geometry geometry;if(!atmosphereintegration::geometry(d,*p,min,vertices,start,count,geometry))return;
        const unsigned stride=fvf==0x152?36u:24u;if(p->pending.stride!=stride)return;
        atmosphere::LampAttachmentDraw draw;draw.texture=sha;draw.world=world;draw.owner=instance;
        if(!atmosphere::lamp_attachment_geometry(geometry.bytes,stride,geometry.indices,draw.positions,draw.uv)||
           !p->lamp_attachments.signature_known(sha,draw.uv,unsigned(draw.positions.size()))){++queue.signature_misses;return;}
        queue.push(std::move(draw));
    }catch(...){if(!p->pending.any())p->pending.release();}
}
// Night only (AmbientStrength < .5): vehicle passes the body path does not
// light (glass, lamp lenses, mirrors, reflection-only parts) keep full texture
// brightness. Scale their final colour by the night body energy with one extra
// TFACTOR stage (after the native stages; alpha, blend, UV untouched).
// Emissive lamp layers (*lightson*, *glow*) are left bright on purpose.
// 6.7: car-space centroid of the current draw's vertex range (CPU mirror).
// 6.13: share of the current draw's vertices inside a car's brake boxes (+3 cm).
inline float brake_share(Device8& d,IDirect3DDevice8& n,UINT min,UINT vertices,const atmosphere::Pilot::BrakeBoxes& boxes)noexcept{
    try{
        if(!vertices||vertices>4096)return 0;
        courseintegration::Ref<IDirect3DVertexBuffer8> vb;UINT stride=0;if(FAILED(n.GetStreamSource(0,&vb.p,&stride))||!vb.p||stride<12||stride>128)return 0;
        courseintegration::Ref<IDirect3DIndexBuffer8> ib;UINT base=0;if(FAILED(n.GetIndices(&ib.p,&base)))return 0;
        const auto generation=d.trace.resources.generation(reinterpret_cast<uintptr_t>(vb.p));if(!generation)return 0;
        std::vector<uint8_t> bytes;uint64_t revision=0;
        if(!d.copy_buffer_shadow(vb.p,BufferKind::Vertex,generation,(uint64_t(base)+min)*stride,size_t(vertices)*stride,bytes,revision)||bytes.size()<size_t(vertices)*stride)return 0;
        unsigned inside=0;for(UINT i=0;i<vertices;++i){float v[3];std::memcpy(v,bytes.data()+size_t(i)*stride,12);
            for(unsigned b=0;b<boxes.count;++b){bool in=true;for(unsigned k=0;k<3;++k)if(v[k]<boxes.lo[b][k]-.03f||v[k]>boxes.hi[b][k]+.03f){in=false;break;}if(in){++inside;break;}}}
        return float(inside)/float(vertices);
    }catch(...){return 0;}
}
inline bool lamp_centroid(Device8& d,IDirect3DDevice8& n,UINT min,UINT vertices,std::array<float,3>& out)noexcept{
    try{
        if(!vertices||vertices>4096)return false;
        courseintegration::Ref<IDirect3DVertexBuffer8> vb;UINT stride=0;if(FAILED(n.GetStreamSource(0,&vb.p,&stride))||!vb.p||stride<12||stride>128)return false;
        courseintegration::Ref<IDirect3DIndexBuffer8> ib;UINT base=0;if(FAILED(n.GetIndices(&ib.p,&base)))return false;
        const auto generation=d.trace.resources.generation(reinterpret_cast<uintptr_t>(vb.p));if(!generation)return false;
        std::vector<uint8_t> bytes;uint64_t revision=0;
        if(!d.copy_buffer_shadow(vb.p,BufferKind::Vertex,generation,(uint64_t(base)+min)*stride,size_t(vertices)*stride,bytes,revision)||bytes.size()<size_t(vertices)*stride)return false;
        double s[3]{};for(UINT i=0;i<vertices;++i){float v[3];std::memcpy(v,bytes.data()+size_t(i)*stride,12);if(!std::isfinite(v[0]+v[1]+v[2]))return false;for(unsigned k=0;k<3;++k)s[k]+=v[k];}
        for(unsigned k=0;k<3;++k)out[k]=float(s[k]/vertices);return true;
    }catch(...){return false;}
}
// 6.6: centres of a lamp lens draw (CPU vertex mirror, never locks), split
// into left/right halves; front/rear from the car-space Z of each centre.
// 6.13 lens texel classes (HSV of the texel under the triangle centroid): white (headlight / reverse;
// reddish hues need lower saturation so pale pink tail sections stay red), red (tail / brake),
// amber (indicators: no glint). Offline-checked on all retail car.dx lamp draws.
enum LensClass : uint8_t {LensNone=0,LensWhite=1,LensRed=2,LensAmber=3,LensOther=4,LensDark=5};
// 6.14: Other = bright non-red/amber (bluish headlamp glass: headlight at the front); Dark = unlit lens
// part (hi < .25: an off reverse lamp when the car has no white rear section, e.g. Terrano bumper lamps).
inline LensClass lens_class(uint32_t argb)noexcept{
    const float r=((argb>>16)&255)/255.f,g=((argb>>8)&255)/255.f,b=(argb&255)/255.f,hi=std::max({r,g,b}),lo=std::min({r,g,b});
    if(hi<.25f)return LensDark;const float sat=hi>0?(hi-lo)/hi:0;float h=0;
    if(hi>lo){if(hi==r)h=std::fmod(60*(g-b)/(hi-lo)+360,360.f);else if(hi==g)h=60*(b-r)/(hi-lo)+120;else h=60*(r-g)/(hi-lo)+240;}
    const bool reddish=h>=330||h<=15;
    if(sat<(reddish?.22f:.38f))return hi>=.45f?LensWhite:LensNone;
    if(reddish)return LensRed;if(h<=65)return LensAmber;return hi>=.45f?LensOther:LensNone;
}
// 6.14 glints: one point per lens SECTION. Sections are built per class (a vertex on a white/red seam
// belongs to both), vertices at one position are joined across UV seams; the point is the section's
// bounds centre on its outer face. Front white/other = headlight (per side at most the two largest,
// >= 40% of the side's largest); rear white = reverse (only in R), rear red = tail, rear dark = reverse
// fallback (only in R, only for cars without a white rear section). Sections: >= 3 vertices, 5..60 cm.
inline void lamp_points_begin(atmosphere::Pilot& p,uint64_t frame)noexcept{if(p.lamp_points_frame!=frame){p.lamp_points.clear();p.lamp_points_frame=frame;}}
inline void record_lamp_points(atmosphere::Pilot& p,uint64_t frame,uintptr_t instance,const std::vector<uint8_t>& bytes,unsigned stride,const std::vector<uint32_t>& indices,
                               const D3DMATRIX& w,const atmosphere::Pilot::LensTexture* tex,unsigned uv,bool brake_layer,bool red_only)noexcept{
    try{
        lamp_points_begin(p,frame);
        const size_t n=stride?bytes.size()/stride:0;if(p.lamp_points.size()>=96||!n||n>4096||indices.size()<3||(tex&&uv+8>stride))return;
        auto f=[&](size_t i,unsigned o){float x=0;std::memcpy(&x,bytes.data()+i*stride+o,4);return x;};
        const size_t tris=indices.size()/3;std::vector<uint8_t> cls(tris,LensNone);
        for(size_t t=0;t<tris;++t){const auto a=indices[t*3],b=indices[t*3+1],c=indices[t*3+2];if(a>=n||b>=n||c>=n)return;
            if(brake_layer){cls[t]=LensRed;continue;}
            const bool front=(f(a,8)+f(b,8)+f(c,8))>0;
            if(tex){float u=(f(a,uv)+f(b,uv)+f(c,uv))/3,v=(f(a,uv+4)+f(b,uv+4)+f(c,uv+4))/3;if(!std::isfinite(u+v))continue;u-=std::floor(u);v-=std::floor(v);
                const unsigned x=std::min(tex->width-1,unsigned(u*tex->width)),y=std::min(tex->height-1,unsigned(v*tex->height));cls[t]=lens_class(tex->pixels[size_t(y)*tex->width+x]);}
            else cls[t]=front?LensWhite:LensRed;   // no readable texture: ends decide
            if(front&&cls[t]==LensOther)cls[t]=LensWhite;
            if(front&&cls[t]==LensDark)cls[t]=LensNone;
            if(red_only&&cls[t]!=LensRed)cls[t]=LensNone;}
        struct Part{std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};unsigned count=0;uint8_t cls=0;};std::vector<Part> parts;
        std::vector<uint32_t> parent(n);std::vector<int> slot(n);std::vector<uint8_t> used(n);
        for(const uint8_t c:{uint8_t(LensWhite),uint8_t(LensRed),uint8_t(LensDark)}){
            bool any=false;for(size_t t=0;t<tris;++t)if(cls[t]==c){any=true;break;}if(!any)continue;
            for(uint32_t i=0;i<n;++i){parent[i]=i;slot[i]=-1;used[i]=0;}
            auto find=[&](uint32_t a){while(parent[a]!=a){parent[a]=parent[parent[a]];a=parent[a];}return a;};
            auto join=[&](uint32_t a,uint32_t b){a=find(a);b=find(b);if(a!=b)parent[b]=a;};
            for(size_t t=0;t<tris;++t)if(cls[t]==c){const auto a=indices[t*3],b=indices[t*3+1],d=indices[t*3+2];used[a]=used[b]=used[d]=1;join(a,b);join(a,d);}
            std::vector<uint32_t> order;for(uint32_t i=0;i<n;++i)if(used[i])order.push_back(i);
            std::sort(order.begin(),order.end(),[&](uint32_t a,uint32_t b){return f(a,0)<f(b,0);});
            for(size_t a=0;a<order.size();++a)for(size_t b=a+1;b<order.size();++b){const auto i=order[a],j=order[b];if(f(j,0)-f(i,0)>.001f)break;
                if(std::abs(f(i,4)-f(j,4))<=.001f&&std::abs(f(i,8)-f(j,8))<=.001f)join(i,j);}
            for(const auto i:order){const auto r=find(i);if(slot[r]<0){slot[r]=int(parts.size());parts.emplace_back();parts.back().cls=c;}
                auto& q=parts[size_t(slot[r])];const std::array<float,3> v{f(i,0),f(i,4),f(i,8)};if(!std::isfinite(v[0]+v[1]+v[2]))return;
                for(unsigned k=0;k<3;++k){q.lo[k]=std::min(q.lo[k],v[k]);q.hi[k]=std::max(q.hi[k],v[k]);}++q.count;}}
        auto face=[](const Part& q){return std::hypot(q.hi[0]-q.lo[0],q.hi[1]-q.lo[1]);};
        std::vector<const Part*> keep;
        for(const auto& q:parts){const float cz=(q.lo[2]+q.hi[2])*.5f,sz=face(q);
            if(std::abs(cz)<1.2f||q.count<3||sz<.05f||sz>.6f)continue;   // 6.8: side markers get no glint; lone long triangles neither
            if(cz>0&&q.cls!=LensWhite)continue;keep.push_back(&q);}
        // headlights: per side the two largest sections, each >= 40% of that side's largest
        for(int side=0;side<2;++side){std::vector<const Part*> heads;
            for(auto* q:keep)if((q->lo[2]+q->hi[2])>0&&((q->lo[0]+q->hi[0])<0)==(side==0))heads.push_back(q);
            std::sort(heads.begin(),heads.end(),[&](const Part* a,const Part* b){return face(*a)>face(*b);});
            // 6.14: a smaller section wholly outboard of the side's largest lens is a side/corner indicator glass (Xtrail, Pajero, Kia).
            if(!heads.empty()){const float edge=std::max(std::abs(heads[0]->lo[0]),std::abs(heads[0]->hi[0]));
                for(size_t k=1;k<heads.size();){const float cx=std::abs((heads[k]->lo[0]+heads[k]->hi[0])*.5f);
                    if(cx>edge-.03f&&face(*heads[k])<.6f*face(*heads[0])){keep.erase(std::find(keep.begin(),keep.end(),heads[k]));heads.erase(heads.begin()+long(k));}else ++k;}}
            for(size_t k=0;k<heads.size();++k)if(k>=2||face(*heads[k])<.4f*face(*heads[0]))keep.erase(std::find(keep.begin(),keep.end(),heads[k]));}
        const std::array<float,3> forward=atmosphere::normalized({w._31,w._32,w._33});
        for(const auto* q:keep){
            const bool front=(q->lo[2]+q->hi[2])>0;
            const uint8_t kind=brake_layer?2:front?0:q->cls==LensWhite?3:q->cls==LensDark?4:1;
            const float x=(q->lo[0]+q->hi[0])*.5f,y=(q->lo[1]+q->hi[1])*.5f,z=front?q->hi[2]:q->lo[2];   // outer face
            atmosphere::Pilot::LampPoint lp;lp.instance=instance;lp.front=front;lp.kind=kind;
            lp.world={x*w._11+y*w._21+z*w._31+w._41,x*w._12+y*w._22+z*w._32+w._42,x*w._13+y*w._23+z*w._33+w._43};
            for(unsigned k=0;k<3;++k)lp.axis[k]=front?forward[k]:-forward[k];
            bool duplicate=false;for(const auto& o:p.lamp_points){const float dx=o.world[0]-lp.world[0],dy=o.world[1]-lp.world[1],dz=o.world[2]-lp.world[2];
                if(o.instance==instance&&o.kind==kind&&dx*dx+dy*dy+dz*dz<.0025f){duplicate=true;break;}}
            if(!duplicate)p.lamp_points.push_back(lp);}
    }catch(...){}
}
// Keep the automatic rig's lamp roles and units, but bind each unit to the lens
// triangles that are actually drawn. Never emit the entire static rig from one
// unrelated lens draw. Front lamps require current nondegenerate geometry.
// Rear OFF/ON switch nodes are not all fleet-owned; preserve their established
// automatic placement until a current lens can provide a better surface anchor.
inline bool rig_lamp_points(atmosphere::Pilot& p,uint64_t frame,uintptr_t instance,const std::string& texture,const std::vector<uint8_t>& bytes,unsigned stride,
                            const std::vector<uint32_t>& indices,const D3DMATRIX& w,uint64_t race)noexcept{
    try{
        if(p.rig_race!=race){for(auto& owner:p.rig_owners)owner={};p.rig_race=race;}
        if(!p.lamp_rigs.loaded||!instance)return false;auto* o=p.rig_owner(instance,frame,true);if(!o)return false;
        const size_t n=stride?bytes.size()/stride:0;if(stride<24||stride>128||!n||n>4096||indices.empty()||indices.size()%3)return false;
        std::vector<atmosphere::LampVec> positions(n);std::vector<uint8_t> identity;
        identity.insert(identity.end(),reinterpret_cast<const uint8_t*>(indices.data()),reinterpret_cast<const uint8_t*>(indices.data()+indices.size()));
        for(size_t i=0;i<n;++i){std::memcpy(positions[i].data(),bytes.data()+i*stride,12);for(auto x:positions[i])if(!std::isfinite(x))return false;
            // UVs survive damage, unlike positions/normals. They distinguish
            // different lens draws even when local indices happen to coincide.
            identity.insert(identity.end(),bytes.data()+(i+1)*stride-8,bytes.data()+(i+1)*stride);}
        const auto key=texture+"/"+std::to_string(stride)+"/"+sha256_bytes(identity.data(),identity.size());
        int matched=-1;
        {
            std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};std::vector<uint8_t> used(n,0);unsigned count=0;
            for(const auto i:indices){if(i>=n)return false;if(used[i])continue;used[i]=1;++count;float v[3];std::memcpy(v,bytes.data()+size_t(i)*stride,12);
                for(unsigned k=0;k<3;++k){lo[k]=std::min(lo[k],v[k]);hi[k]=std::max(hi[k],v[k]);}}
            const int r=p.lamp_rigs.match(texture,count,lo,hi);
            matched=r;
            if(r<0&&o->rig>=0&&p.lamp_rigs.owns_texture(o->rig,texture)){}   // 6.15.1: a deformed lens of the same car keeps its rig
            else if(r<0){o->rig=-1;o->surfaces.clear();++p.rig_misses;return false;}
            else if(r!=o->rig){if(o->rig>=0)++p.rig_rematches;o->surfaces.clear();o->rig=r;++p.rig_matches;session().write("{\"type\":\"atmosphere_lamp_rig_match\",\"frame\":"+std::to_string(frame)+",\"car\":"+quote(p.lamp_rigs.rigs[size_t(o->rig)].car)+",\"texture\":"+quote(texture)+",\"points\":"+std::to_string(p.lamp_rigs.rigs[size_t(o->rig)].points.size())+"}");}}
        auto* surface=static_cast<atmosphere::LampDrawAnchors*>(nullptr);
        for(auto& s:o->surfaces)if(s.identity==key){surface=&s;break;}
        const auto& rig=p.lamp_rigs.rigs[size_t(o->rig)];
        if(!surface){
            // If the first observation is already deformed, use the existing
            // live section detector rather than binding to a wrong rest point.
            if(matched<0||o->surfaces.size()>=16)return false;
            atmosphere::LampDrawAnchors s;s.identity=key;
            for(size_t i=0;i<rig.points.size();++i){const auto& q=rig.points[i];atmosphere::LampSurfaceAnchor a;a.point=i;
                if(atmosphere::bind_lamp_surface(q.pos,q.kind==0||q.kind==4,positions,indices,a))s.anchors.push_back(a);}
            o->surfaces.push_back(std::move(s));surface=&o->surfaces.back();
        }
        lamp_points_begin(p,frame);
        const bool braking=o->braking!=UINT64_MAX&&o->braking+2>=frame;
        if(o->emitted!=frame){o->emitted=frame;const auto forward=atmosphere::normalized({w._31,w._32,w._33});
            for(size_t i=0;i<rig.points.size()&&p.lamp_points.size()<128;++i){const auto& q=rig.points[i];if(q.kind==0||q.kind==4||p.lamp_attachments.manages(o->rig,i))continue;
                uint8_t kind=q.kind;if(kind==2){if(braking)kind=2;else if(q.tail)kind=1;else continue;}
                atmosphere::Pilot::LampPoint lp;lp.instance=instance;lp.kind=kind;lp.size=q.size;lp.rig_point=i;
                for(unsigned k=0;k<3;++k){lp.world[k]=q.pos[0]*(&w._11)[k]+q.pos[1]*(&w._11)[4+k]+q.pos[2]*(&w._11)[8+k]+(&w._11)[12+k];lp.axis[k]=-forward[k];}
                p.lamp_points.push_back(lp);}}
        for(const auto& a:surface->anchors){const auto& q=rig.points[a.point];
            atmosphere::LampVec position{},normal{};if(!a.evaluate(positions,position,normal)){
                p.lamp_points.erase(std::remove_if(p.lamp_points.begin(),p.lamp_points.end(),[&](const auto& point){return point.instance==instance&&point.rig_point==a.point;}),p.lamp_points.end());continue;}
            uint8_t kind=q.kind==4?0:q.kind;if(q.kind==2){if(braking)kind=2;else if(q.tail)kind=1;else continue;}
            const bool front=q.kind==0||q.kind==4;const float x=position[0],y=position[1],z=position[2];
            atmosphere::Pilot::LampPoint lp;lp.instance=instance;lp.front=front;lp.kind=kind;lp.size=q.kind==4?q.size*.8f:q.size;
            lp.rig_point=a.point;lp.surface_error=a.distance;
            lp.world={x*w._11+y*w._21+z*w._31+w._41,x*w._12+y*w._22+z*w._32+w._42,x*w._13+y*w._23+z*w._33+w._43};
            atmosphere::Mat4 world{};std::memcpy(world.data(),&w,64);if(!atmosphere::transformed_normal(normal,world,lp.axis))continue;
            bool duplicate=false;for(auto& other:p.lamp_points)if(other.instance==instance&&other.rig_point==a.point){if(lp.surface_error<other.surface_error)other=lp;duplicate=true;break;}
            if(!duplicate&&p.lamp_points.size()<128){p.lamp_points.push_back(lp);++p.rig_points;}}
        return true;
    }catch(...){return false;}
}
// 6.13: remember the car-space boxes of a car's breaklightson layer (connected parts).
inline void remember_brake_boxes(atmosphere::Pilot& p,uint64_t frame,uintptr_t instance,const std::vector<uint8_t>& bytes,unsigned stride,const std::vector<uint32_t>& indices)noexcept{
    const size_t n=stride?bytes.size()/stride:0;if(!n||n>4096)return;
    atmosphere::Pilot::BrakeBoxes* slot=nullptr;for(auto& b:p.brake_boxes)if(b.instance==instance){slot=&b;break;}
    if(!slot){for(auto& b:p.brake_boxes)if(!b.instance||b.frame==UINT64_MAX||frame>b.frame+3600){slot=&b;break;}if(!slot)return;}
    if(slot->instance==instance&&slot->frame+30>frame&&slot->count)return;   // refreshed twice a second at most
    std::vector<uint32_t> parent(n);for(uint32_t i=0;i<n;++i)parent[i]=i;
    auto find=[&](uint32_t a){while(parent[a]!=a){parent[a]=parent[parent[a]];a=parent[a];}return a;};
    for(size_t t=0;t+2<indices.size();t+=3){if(indices[t]>=n||indices[t+1]>=n||indices[t+2]>=n)return;for(unsigned k=1;k<3;++k){auto a=find(indices[t]),b=find(indices[t+k]);if(a!=b)parent[b]=a;}}
    atmosphere::Pilot::BrakeBoxes out;out.instance=instance;out.frame=frame;std::vector<int> map(n,-1);
    for(uint32_t i=0;i<n;++i){const auto r=find(i);if(map[r]<0){if(out.count>=out.lo.size())continue;map[r]=int(out.count++);out.lo[size_t(map[r])]={1e30f,1e30f,1e30f};out.hi[size_t(map[r])]={-1e30f,-1e30f,-1e30f};}
        const size_t m=size_t(map[r]);float v[3];std::memcpy(v,bytes.data()+size_t(i)*stride,12);for(unsigned k=0;k<3;++k){out.lo[m][k]=std::min(out.lo[m][k],v[k]);out.hi[m][k]=std::max(out.hi[m][k],v[k]);}}
    *slot=out;
}
// 6.12 reverse section: rear lens triangles whose texels are white (low saturation, bright) are the
// reverse lamp. Lens pixels cached by pointer+generation (A8R8G8B8/X8R8G8B8/R5G6B5/X1R5G5B5/A1R5G5B5).
inline const atmosphere::Pilot::LensTexture* lens_texture(Device8& d,atmosphere::Pilot& p,IDirect3DDevice8& n)noexcept{
    try{
        courseintegration::Ref<IDirect3DBaseTexture8> base;if(FAILED(n.GetTexture(0,&base.p))||!base.p||base.p->GetType()!=D3DRTYPE_TEXTURE)return nullptr;
        const auto pointer=reinterpret_cast<uintptr_t>(base.p);const auto generation=d.trace.resources.generation(pointer);if(!generation)return nullptr;
        for(auto& c:p.lens_textures)if(c.pointer==pointer&&c.generation==generation)return c.width?&c:nullptr;
        auto& c=p.lens_textures[p.lens_texture_next++%p.lens_textures.size()];c={};c.pointer=pointer;c.generation=generation;
        auto* t=static_cast<IDirect3DTexture8*>(base.p);D3DSURFACE_DESC desc{};
        if(FAILED(t->GetLevelDesc(0,&desc))||!desc.Width||!desc.Height||desc.Width>512||desc.Height>512||desc.Pool==D3DPOOL_DEFAULT)return nullptr;
        const unsigned bpp=desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8?4:desc.Format==D3DFMT_R5G6B5||desc.Format==D3DFMT_X1R5G5B5||desc.Format==D3DFMT_A1R5G5B5?2:0;
        if(!bpp)return nullptr;
        D3DLOCKED_RECT lock{};if(FAILED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY)))return nullptr;
        std::vector<uint32_t> px(size_t(desc.Width)*desc.Height);const bool valid=lock.pBits&&lock.Pitch>=INT(desc.Width*bpp);
        if(valid)for(unsigned y=0;y<desc.Height;++y){const auto* row=static_cast<const BYTE*>(lock.pBits)+size_t(y)*lock.Pitch;
            for(unsigned x=0;x<desc.Width;++x){uint32_t v=0;if(bpp==4)std::memcpy(&v,row+x*4,4);else{uint16_t h=0;std::memcpy(&h,row+x*2,2);unsigned r=0,g=0,b=0;
                if(desc.Format==D3DFMT_R5G6B5){r=((h>>11)&31)*255/31;g=((h>>5)&63)*255/63;b=(h&31)*255/31;}else{r=((h>>10)&31)*255/31;g=((h>>5)&31)*255/31;b=(h&31)*255/31;}
                v=0xff000000u|r<<16|g<<8|b;}px[size_t(y)*desc.Width+x]=v;}}
        if(FAILED(t->UnlockRect(0))||!valid)return nullptr;
        c.width=desc.Width;c.height=desc.Height;c.pixels=std::move(px);return &c;
    }catch(...){return nullptr;}
}
inline bool reverse_texel(const atmosphere::Pilot::LensTexture& t,float u,float v)noexcept{
    if(!std::isfinite(u+v))return false;u-=std::floor(u);v-=std::floor(v);
    const unsigned x=std::min(t.width-1,unsigned(u*t.width)),y=std::min(t.height-1,unsigned(v*t.height));return lens_class(t.pixels[size_t(y)*t.width+x])==LensWhite;
}
// 6.15.1: the $switch(blight) OFF lens (no fleet owner) is the rear lamp at night: recognised by the vertex-range
// bounds of a rig's 'off' entry (1.5 cm); it then gets the same emissive stage as the other lamp lenses.
inline bool rig_blight_off_draw(Device8& d,atmosphere::Pilot& p,IDirect3DDevice8& n,DWORD fvf,UINT min,UINT vertices)noexcept{
    try{
        if(!p.lamp_rigs.loaded||!p.headlight_style.enabled||p.headlight_style.lamp_emissive<=0||(fvf!=0x152&&fvf!=0x142)||!vertices||vertices>256)return false;
        courseintegration::Ref<IDirect3DVertexBuffer8> vb;UINT stride=0;if(FAILED(n.GetStreamSource(0,&vb.p,&stride))||!vb.p||stride<12||stride>128)return false;
        courseintegration::Ref<IDirect3DIndexBuffer8> ib;UINT base=0;if(FAILED(n.GetIndices(&ib.p,&base)))return false;
        const auto generation=d.trace.resources.generation(reinterpret_cast<uintptr_t>(vb.p));if(!generation)return false;
        std::vector<uint8_t> bytes;uint64_t revision=0;
        if(!d.copy_buffer_shadow(vb.p,BufferKind::Vertex,generation,(uint64_t(base)+min)*stride,size_t(vertices)*stride,bytes,revision)||bytes.size()<size_t(vertices)*stride)return false;
        std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};
        for(UINT i=0;i<vertices;++i){float v[3];std::memcpy(v,bytes.data()+size_t(i)*stride,12);if(!std::isfinite(v[0]+v[1]+v[2]))return false;for(unsigned k=0;k<3;++k){lo[k]=std::min(lo[k],v[k]);hi[k]=std::max(hi[k],v[k]);}}
        if(hi[2]>-.5f)return false;   // rear lamps only
        return p.lamp_rigs.blight_off(vertices,lo,hi);
    }catch(...){return false;}
}
inline HRESULT night_energy(Device8& d,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,bool& applied)noexcept {
    applied=false;if(ps2port::perf::atmo(ps2port::perf::AtmoBodies))return S_OK;auto* p=atmosphereintegration::pilot(d);
    if(!p||!p->enabled()||!p->lighting.active()||p->lighting.ambient_strength>=.5f||!count||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    try{
        auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
        DWORD fvf=0,pixel=1;if(FAILED(n.GetVertexShader(&fvf))||FAILED(n.GetPixelShader(&pixel))||pixel||!groundintegration::render(d,n,D3DRS_LIGHTING,FALSE))return S_OK;
        frontendmodelintegration::Context owner;atmosphere::NativeMaterialBinding binding;std::string material;bool lamp=false,rear_lamp=false,brake_zone=false,reversing=false,mixed=false,blight_off=false;std::array<float,3> centroid{};
        if(frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner)){
            const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
            if(!atmosphere::native_material_binding(exe,owner.mesh,frontendmodelintegration::word,binding))return S_OK;
            {std::string primary=binding.names[0];for(auto& c:primary)c=char(std::tolower(static_cast<unsigned char>(c)));
             // 6.13: the breaklightson layer (drawn only while braking) marks the brake sections: its parts become
             // brake glints this frame and the car's brake boxes (brake-zone lens draws). The draw stays native.
             if(primary.find("breaklightson")!=std::string::npos&&primary.find("glow")==std::string::npos&&(fvf==0x152||fvf==0x142)&&!p->pending.any()){
                 atmosphereintegration::Geometry g;const unsigned st=fvf==0x152?36u:24u;D3DMATRIX w{};
                 if(atmosphereintegration::geometry(d,*p,min,vertices,start,count,g)&&p->pending.stride==st&&SUCCEEDED(n.GetTransform(D3DTS_WORLD,&w))){
                     remember_brake_boxes(*p,d.trace.frame_number(),owner.owner.instance,g.bytes,st,g.indices);
                     if(p->glint_style.enabled&&!(p->lamp_rigs.loaded&&p->rig_owner(owner.owner.instance,d.trace.frame_number(),false)&&p->rig_owner(owner.owner.instance,d.trace.frame_number(),false)->rig>=0))record_lamp_points(*p,d.trace.frame_number(),owner.owner.instance,g.bytes,st,g.indices,w,nullptr,0,true,false);
                     if(p->first_reason("brake_layer_observed"))session().write("{\"type\":\"atmosphere_brake_layer\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"vertices\":"+std::to_string(vertices)+"}");}
                 if(!p->pending.any())p->pending.release();return S_OK;}}
            for(const auto& raw:binding.names){std::string name=raw;for(auto& c:name)c=char(std::tolower(static_cast<unsigned char>(c)));
                if(name.find("lightson")!=std::string::npos||name.find("glow")!=std::string::npos)return S_OK;}
            // 6.5: lamp lens textures (front white / rear red share one atlas) are
            // emissive while the headlights are on: boost instead of darkening.
            {std::string primary=binding.names[0];for(auto& c:primary)c=char(std::tolower(static_cast<unsigned char>(c)));
             // 6.14: also rear lens textures named *bl (kbl, bl) and indicator lenses (cuindicate64).
             const auto stem=primary.substr(0,primary.find("-tga"));const bool bl_stem=stem=="bl"||(stem.size()==3&&stem.compare(1,2,"bl")==0);
             lamp=p->headlight_style.enabled&&p->headlight_style.lamp_emissive>0&&(primary.find("light")!=std::string::npos||primary.find("lamp")!=std::string::npos||
                  primary.find("indicat")!=std::string::npos||bl_stem)&&
                  primary.find("windscreen")==std::string::npos&&primary.find("glass")==std::string::npos;}
            // 6.7: car-space centroid of this pass (CPU mirror) -> front/rear; the
            // off-state brake lamp mesh sits where the glow card was observed.
            if(p->headlight_style.enabled&&p->headlight_style.lamp_emissive>0&&lamp_centroid(d,n,min,vertices,centroid)){
                rear_lamp=centroid[2]<-1.2f;
                if(!lamp&&rear_lamp)if(const auto* boxes=p->brake_boxes_for(owner.owner.instance))if(brake_share(d,n,min,vertices,*boxes)>=.5f){lamp=true;brake_zone=true;}}
            material=binding.names[0];
        }else if(rig_blight_off_draw(d,*p,n,fvf,min,vertices)){
            lamp=true;brake_zone=true;blight_off=true;rear_lamp=true;material="rig_blight_off";++p->rig_blight_off;
        }else{
            // 5.13: windows live under $switch(screen*) nodes, which the fleet
            // owner walk does not cover. Accept only this exact call when the
            // draw classifier proved it a blended vehicle body env pass
            // (SRCALPHA/INVSRCALPHA glass). Emissive lamps are opaque or 0x102.
            const auto& v=p->blended_vehicle;
            const bool proven=v.frame==d.trace.frame_number()&&v.min==min&&v.vertices==vertices&&v.start==start&&v.count==count;
            if((fvf!=0x152&&fvf!=0x142)||!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,TRUE)||!groundintegration::render(d,n,D3DRS_SRCBLEND,D3DBLEND_SRCALPHA)||
               !groundintegration::render(d,n,D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA))return S_OK;
            courseintegration::Ref<IDirect3DBaseTexture8> glass;if(FAILED(n.GetTexture(0,&glass.p))||!glass.p)return S_OK;
            const auto pointer=reinterpret_cast<uintptr_t>(glass.p);const auto generation=d.trace.resources.generation(pointer);
            // Remembered textures need the env glass stage too (0x152 + camera-normal env).
            const bool remembered=!proven&&fvf==0x152&&p->known_glass(pointer,generation)&&groundintegration::stage(d,n,1,D3DTSS_COLOROP,D3DTOP_MODULATEALPHA_ADDCOLOR)&&
                groundintegration::stage(d,n,1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACENORMAL);
            if(!proven&&!remembered)return S_OK;
            if(proven)p->remember_glass(pointer,generation);
            p->blended_vehicle={};material=proven?"classifier_blended_vehicle_glass":"remembered_vehicle_glass";++p->night_glass_draws;
        }
        DWORD op1=0,op2=0,op3=0;if(FAILED(n.GetTextureStageState(1,D3DTSS_COLOROP,&op1))||FAILED(n.GetTextureStageState(2,D3DTSS_COLOROP,&op2)))return S_OK;
        const DWORD unit=op1==D3DTOP_DISABLE?1:op2==D3DTOP_DISABLE?2:0;if(!unit)return S_OK;
        if(unit==2&&(FAILED(n.GetTextureStageState(3,D3DTSS_COLOROP,&op3))||op3!=D3DTOP_DISABLE))return S_OK;
        if(!p->wheel_caps){D3DCAPS8 caps{};p->wheel_caps=SUCCEEDED(n.GetDeviceCaps(&caps))&&caps.MaxTextureBlendStages>=3&&(caps.TextureOpCaps&D3DTEXOPCAPS_MODULATE)&&(caps.TextureOpCaps&D3DTEXOPCAPS_SELECTARG1)?1:2;}
        if(p->wheel_caps!=1)return S_OK;
        auto& s=p->pending;if(s.any())return S_OK; // another atmosphere change owns this draw
        constexpr D3DTEXTURESTAGESTATETYPE keys[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_RESULTARG,D3DTSS_ALPHAARG2};
        for(unsigned i=0;i<7;++i)if(FAILED(n.GetTextureStageState(unit,keys[i],&s.body_stage[i])))return S_OK;
        if(FAILED(n.GetRenderState(D3DRS_TEXTUREFACTOR,&s.body_factor)))return S_OK;
        s.body_unit=unit;const DWORD values[]{lamp?DWORD(D3DTOP_MODULATE2X):DWORD(D3DTOP_MODULATE),D3DTA_CURRENT,D3DTA_TFACTOR,D3DTOP_SELECTARG1,D3DTA_CURRENT,D3DTA_CURRENT,D3DTA_CURRENT};
        DWORD factor=(s.body_factor&0xff000000u)|(atmosphere::flat_body_color(0xffffffffu,p->lighting)&0x00ffffffu);
        if(lamp){const DWORD k=DWORD(std::clamp(std::lround(p->headlight_style.lamp_emissive*.5f*255),0l,255l));
            // Rear lenses glow red; their white reverse-lamp texels only while reversing.
            const auto* own=p->lamp_projectors.frame!=UINT64_MAX&&p->lamp_projectors.frame+2>=d.trace.frame_number()?p->lamp_projectors.find(owner.owner.instance):nullptr;
            reversing=own&&own->reversing;mixed=!brake_zone&&(fvf==0x152||fvf==0x142);
            (void)rear_lamp;const DWORD gb=k;   // 6.12: lenses keep their own colours (tail, indicators, reverse)
            factor=(s.body_factor&0xff000000u)|k<<16|gb<<8|gb;material+=brake_zone?"#brake_zone":rear_lamp?"#rear_emissive":"#emissive";}
        for(unsigned i:{7u,1u,2u,3u,4u,5u,6u,0u}){s.body_pending|=1u<<i;const auto hr=i==7?n.SetRenderState(D3DRS_TEXTUREFACTOR,factor):n.SetTextureStageState(unit,keys[i],values[i]);
            if(i==7)atmosphereintegration::notify(d,50,pack(D3DRS_TEXTUREFACTOR,factor),hr);else atmosphereintegration::notify(d,63,pack(unit,keys[i],values[i]),hr);if(FAILED(hr))return atmosphereintegration::repair(d);}
        applied=true;
        // 6.12: one lens draw may hold front and rear lenses. Only the reverse section changes: rear
        // triangles (car z < -1.2) whose texels are white; their vertices are dimmed while not in reverse
        // and native (bright through the emissive stage) in reverse. Cars without such texels: unchanged.
        if(lamp&&!blight_off&&(fvf==0x152||fvf==0x142)){atmosphereintegration::Geometry g;const unsigned st=fvf==0x152?36u:24u,co=fvf==0x152?24u:12u,uvo=co+4;
            if(atmosphereintegration::geometry(d,*p,min,vertices,start,count,g)&&p->pending.stride==st&&g.bytes.size()>=size_t(vertices)*st){
                const auto* tex=mixed?lens_texture(d,*p,n):nullptr;unsigned dimmed=0;
                if(tex){std::vector<uint8_t> mark(vertices,0);   // bit0 reverse triangle, bit1 other triangle
                    auto f=[&](uint32_t i,unsigned o){float x=0;std::memcpy(&x,g.bytes.data()+size_t(i)*st+o,4);return x;};
                    for(size_t t=0;t+2<g.indices.size();t+=3){const uint32_t a=g.indices[t],b=g.indices[t+1],c=g.indices[t+2];if(a>=vertices||b>=vertices||c>=vertices)break;
                        const bool rear=f(a,8)<-1.2f&&f(b,8)<-1.2f&&f(c,8)<-1.2f;
                        const bool rev=rear&&reverse_texel(*tex,(f(a,uvo)+f(b,uvo)+f(c,uvo))/3,(f(a,uvo+4)+f(b,uvo+4)+f(c,uvo+4))/3);
                        for(auto v:{a,b,c})mark[v]|=rev?1:2;}
                    unsigned reverse_vertices=0;for(auto m:mark)reverse_vertices+=m==1;p->lamp_reverse_vertices+=reverse_vertices;
                    if(!reversing)for(UINT v=0;v<vertices;++v)if(mark[v]==1){auto* col=g.bytes.data()+size_t(v)*st+co;for(unsigned k=0;k<3;++k)col[k]=uint8_t(col[k]*2/5);++dimmed;}}
                if(dimmed){const auto hr=atmosphereintegration::upload(d,*p,min,vertices,g.bytes);if(FAILED(hr))return atmosphereintegration::repair(d);++p->lamp_rear_tints;}
                D3DMATRIX w{};if(p->glint_style.enabled&&SUCCEEDED(n.GetTransform(D3DTS_WORLD,&w))){
                    std::string texture=binding.names[0];for(auto& c:texture)c=char(std::tolower(static_cast<unsigned char>(c)));
                    if(!rig_lamp_points(*p,d.trace.frame_number(),owner.owner.instance,texture,g.bytes,st,g.indices,w,cert.race_generation)){if(!tex)tex=lens_texture(d,*p,n);
                        record_lamp_points(*p,d.trace.frame_number(),owner.owner.instance,g.bytes,st,g.indices,w,tex,uvo,false,false);}}}}
        // 6.16: rig cars draw their emissive lens pass with the night lens texture (indicators, stickers, glass
        // around the lamp darkened offline) so only the lamp's working area glows.
        if(lamp&&!blight_off&&p->lamp_rigs.loaded&&!p->pending.texture_changed)if(const auto* ro=p->rig_owner(owner.owner.instance,d.trace.frame_number(),false);ro&&ro->rig>=0){
            std::string texture=binding.names[0];for(auto& c:texture)c=char(std::tolower(static_cast<unsigned char>(c)));
            if(auto* night=p->lens_night_texture(n,ro->rig,texture)){auto& s2=p->pending;
                if(SUCCEEDED(n.GetTexture(0,&s2.texture))){s2.texture_changed=true;const auto hr=n.SetTexture(0,night);atmosphereintegration::notify(d,61,pack(0,night),hr);if(FAILED(hr))return atmosphereintegration::repair(d);
                    ++p->lens_night_draws;material+="#night_lens";}}}
        if(p->first_reason(("vehicle_night_energy_"+material).c_str()))session().write("{\"type\":\"atmosphere_vehicle_night_energy\",\"factor\":"+std::to_string(factor)+",\"unit\":"+std::to_string(unit)+",\"material\":"+quote(material)+"}");
        return S_OK;
    }catch(...){if(!p->pending.any())p->pending.release();return atmosphereintegration::repair(d);}
}
// PERF-ATMO2: relit copies of body draws whose source vertices, WORLD (and VIEW
// for the rim term) and lighting are unchanged (stationary cars, menus, the
// start grid). A hit requires byte-equal source bytes.
// PERF-ATMO3 (2026-11-12): the relight depends only on the body ROTATION (directional sun/ambient: world normals) and,
// for the rim term, on the camera position in the body's own space. A moving car with a chase camera keeps both nearly
// constant, so the hit test is rotation within kBodyShadeRotationTolerance and object-space camera within 2 % of its
// distance, against the pose the entry was shaded at (no drift accumulates). Translation alone never invalidates.
constexpr float kBodyShadeRotationTolerance=.008f;   // max |dR| element, about 0.45 degree (Lambert change <= ~2/255)
struct BodyShadeEntry {uintptr_t stream=0;UINT min=0,vertices=0;DWORD fvf=0,stage=0;uint32_t role=0;uint64_t lighting=0;bool rim=false;D3DMATRIX world{},view{};std::array<float,3> camera_local{};std::vector<uint8_t> source,out;uint64_t changed=0;};
// Camera position in the body's object space (rows 0..2 of WORLD are the model axes, row 3 the translation).
inline bool body_camera_local(const D3DMATRIX& world,const D3DMATRIX& view,std::array<float,3>& out)noexcept{
    std::array<float,16> vm{};std::memcpy(vm.data(),&view,64);std::array<float,3> eye{};if(!atmosphere::rigid_camera_position(vm,eye))return false;
    const float d[3]{eye[0]-world._41,eye[1]-world._42,eye[2]-world._43};const float* r[3]{&world._11,&world._21,&world._31};
    for(unsigned i=0;i<3;++i){const float l2=r[i][0]*r[i][0]+r[i][1]*r[i][1]+r[i][2]*r[i][2];if(!(l2>1e-12f))return false;out[i]=(d[0]*r[i][0]+d[1]*r[i][1]+d[2]*r[i][2])/l2;}
    return std::isfinite(out[0]+out[1]+out[2]);}
inline bool body_pose_close(const BodyShadeEntry& e,const D3DMATRIX& world,bool rim,const std::array<float,3>& camera_local)noexcept{
    const float* a=&e.world._11;const float* b=&world._11;
    for(unsigned r=0;r<3;++r)for(unsigned c=0;c<3;++c)if(std::fabs(a[r*4+c]-b[r*4+c])>kBodyShadeRotationTolerance)return false;
    if(!rim)return true;
    float dd=0,ll=0;for(unsigned i=0;i<3;++i){const float x=camera_local[i]-e.camera_local[i];dd+=x*x;ll+=e.camera_local[i]*e.camera_local[i];}
    return dd<=ll*4e-4f;}
struct BodyShadeCache {std::unordered_map<uint64_t,BodyShadeEntry> entries;uint64_t race=UINT64_MAX,hits=0,misses=0,log_at=0;};
inline BodyShadeCache& body_shade_cache()noexcept{static BodyShadeCache c;return c;}
// Every Lighting field the body colour reads (regional atmospheres change it without an INI reload).
inline uint64_t lighting_key(const atmosphere::Lighting& s)noexcept{
    uint64_t h=1469598103934665603ull;auto mix=[&](const void* v,size_t n){const auto* b=static_cast<const uint8_t*>(v);for(size_t i=0;i<n;++i){h^=b[i];h*=1099511628211ull;}};
    const float f[]{s.strength,s.exposure,s.ambient_strength,s.sun_strength,s.fog_strength,s.world_brightness,s.prelight_contrast,s.prelight_visibility,s.tone_contrast,s.tone_shoulder,s.rim_strength,s.rim_power,
        s.ambient[0],s.ambient[1],s.ambient[2],s.sun[0],s.sun[1],s.sun[2],s.direction[0],s.direction[1],s.direction[2]};
    const uint32_t m[]{uint32_t(s.mode),uint32_t(s.surface_tone),uint32_t(s.rim),uint32_t(s.fog_enabled),s.fog};mix(f,sizeof f);mix(m,sizeof m);return h;}
inline HRESULT general(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,bool& applied) {
    auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||!p->body_materials||!p->lighting.active()||!vertices||vertices>8192||!count||count>8192||type!=D3DPT_TRIANGLELIST||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    if(ps2port::perf::atmo(ps2port::perf::AtmoBodies))return S_OK;   // PERF-ATMO1 A/B: native PC car look
    Timing timer(*p);auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
    // PERF-ATMO1 staged timing: gate (state checks + owner lookup), owner (binding/resource/capability),
    // geometry (mirror copy + descriptors), shade (relight; upload is atmo_upload).
    uint64_t stage_at=ps2port::perf::enabled()?ps2port::perf::now():0;
    auto stage=[&](unsigned c){if(!stage_at)return;const auto t=ps2port::perf::now();ps2port::perf::add(c,t-stage_at);stage_at=t;};
    auto reject=[&](const char* why){if(!p->pending.any())p->pending.release();if(p->body_debug&&d.trace.control.active&&p->first_reason(why))atmosphereintegration::log(d,why);return S_OK;};
    DWORD fvf=0,pixel=1;
    if(FAILED(n.GetVertexShader(&fvf))||(fvf!=0x152&&fvf!=0x142&&fvf!=0x112)||FAILED(n.GetPixelShader(&pixel))||pixel||
       !groundintegration::render(d,n,D3DRS_LIGHTING,FALSE)||!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,FALSE)||
       !groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||!groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)||
       !groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||
       !groundintegration::stage(d,n,0,D3DTSS_RESULTARG,D3DTA_CURRENT)||!groundintegration::stage(d,n,2,D3DTSS_COLOROP,D3DTOP_DISABLE)||
       !groundintegration::render(d,n,D3DRS_VERTEXBLEND,D3DVBF_DISABLE)||!groundintegration::render(d,n,D3DRS_INDEXEDVERTEXBLENDENABLE,FALSE))return S_OK;
    // G1.5 (owner review 5): imported GT4 bodies cut panel shapes with alpha test (Lancer Evo IV: 9 paint materials). They
    // stayed native-bright, so their grime looked too light. Alpha-tested opaque draws are now relit RGB-only for body
    // roles: vertex alpha is never changed for them (the night env weight below would move the test threshold).
    DWORD alpha_test=FALSE;if(FAILED(n.GetRenderState(D3DRS_ALPHATESTENABLE,&alpha_test)))return S_OK;
    DWORD stage_op=0;if(FAILED(n.GetTextureStageState(1,D3DTSS_COLOROP,&stage_op)))return S_OK;
    const bool flat=stage_op==D3DTOP_DISABLE;
    if(!flat&&((fvf!=0x152&&fvf!=0x112)||(stage_op!=D3DTOP_ADD&&stage_op!=D3DTOP_MODULATEALPHA_ADDCOLOR)||
        !groundintegration::stage(d,n,1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACENORMAL)||!groundintegration::stage(d,n,1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2)))return S_OK;
    courseintegration::Ref<IDirect3DSurface8> target,back;
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return S_OK;
    frontendmodelintegration::Context owner;
    const bool owned=frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner);stage(ps2port::perf::AtmoBodyGate);if(!owned)return S_OK;
    D3DMATRIX world{};if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||!frontendmodelintegration::fleet_owner_world(owner,world))return reject("body_material_owner_world_mismatch");
    const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));atmosphere::NativeMaterialBinding binding;
    if(!atmosphere::native_material_binding(exe,owner.mesh,frontendmodelintegration::word,binding))return reject("body_material_native_binding_missing");
    uint32_t name_id=0;std::string resource;
    if(!frontendmodelintegration::word(owner.owner.packet+0xc,name_id)||!atmosphere::native_name(exe,name_id,frontendmodelintegration::word,resource))return reject("body_material_resource_missing");
    for(auto& c:resource){c=char(std::tolower(static_cast<unsigned char>(c)));if(c=='\\')c='/';}
    const auto slash=resource.find('/',9);if(resource.rfind("vehicles/",0)!=0||slash==std::string::npos)return reject("body_material_not_vehicle_resource");
    const auto part=resource.substr(slash+1);if(part!="car"&&part!="wheel")return reject("body_material_not_race_car_or_wheel_resource");
    // 6.4: headlight pose = the car body only; wheel instances spin with their own matrices.
    if(part=="car"){atmosphere::Mat4 pose{};std::memcpy(pose.data(),&world,64);p->observe_car(owner.owner.instance,pose,d.trace.frame_number());}
    const auto family=resource.substr(9,slash-9);p->body_capabilities.load(p->body_path);
    const auto* capability=p->body_capabilities.native_capability(family,binding.names[0],binding.names[1],part);
    if(!capability)return reject("body_material_not_authorized_surface");
    if(alpha_test&&capability->role!=atmosphere::Paint&&capability->role!=atmosphere::OpaquePanel&&capability->role!=atmosphere::OpaqueTrim&&capability->role!=atmosphere::OpaqueFlat)
        return reject("body_material_alpha_test_non_body_role");
    const bool implicit=fvf==0x112;
    if(implicit&&(!p->native_wheel_lighting||part!="wheel"||(capability->role!=atmosphere::WheelRubber&&capability->role!=atmosphere::WheelMetal)||flat||!groundintegration::stage(d,n,3,D3DTSS_COLOROP,D3DTOP_DISABLE)))return reject("body_implicit_diffuse_not_certified_wheel");
    if(!p->body_capabilities.extended&&flat!=(capability->role==atmosphere::OpaqueFlat))return reject("body_material_flat_role_pass_mismatch");
    courseintegration::Ref<IDirect3DBaseTexture8> texture;
    if(FAILED(n.GetTexture(0,&texture.p))||reinterpret_cast<uintptr_t>(texture.p)!=binding.textures[0]||!d.trace.resources.generation(binding.textures[0]))return reject("body_material_live_texture_mismatch");
    // R-SURFACE1 G1.3: another Atmosphere route already changed this draw (the course resolver had taken the Lancer Evo IV
    // tread for a course tyre stack). Returning an error here made the wrapper skip the draw: the tread was invisible.
    if(p->pending.any())return reject("body_material_draw_owned_by_other_route");
    stage(ps2port::perf::AtmoBodyOwner);
    const bool normals=fvf==0x152;const unsigned stride=implicit?32u:normals?36u:24u;atmosphereintegration::Geometry g;if(!atmosphereintegration::geometry(d,*p,min,vertices,start,count,g)||p->pending.stride!=stride)return reject("body_material_current_mirror_missing");
    ps2port::RaceDescriptors desc;uintptr_t vb=0,ib=0;
    if(!ps2port::race_descriptors(exe,owner.mesh,frontendmodelintegration::word,desc)||!frontendmodelintegration::pointer_word(desc.vd[0],vb)||!frontendmodelintegration::pointer_word(desc.id[0],ib)||
       d.unwrap_vertex_buffer(reinterpret_cast<IDirect3DVertexBuffer8*>(vb))!=p->pending.stream||d.unwrap_index_buffer(reinterpret_cast<IDirect3DIndexBuffer8*>(ib))!=p->pending.indices||
       desc.vd[2]!=min||desc.vd[3]!=vertices||desc.vd[4]!=fvf||desc.vd[5]!=stride||desc.id[2]!=start||desc.id[3]!=count*3)return reject("body_material_current_descriptor_mismatch");
    stage(ps2port::perf::AtmoBodyGeometry);
    std::vector<uint8_t> debug_original;if(normals&&p->body_debug&&d.trace.control.active)debug_original=g.bytes;
    uint64_t changed=0;
    D3DMATRIX view{};const bool have_view=p->lighting.rim&&SUCCEEDED(n.GetTransform(D3DTS_VIEW,&view));
    auto& cache=body_shade_cache();if(cache.race!=cert.race_generation){cache.entries.clear();cache.race=cert.race_generation;}
    const uint64_t cache_key=(uint64_t(reinterpret_cast<uintptr_t>(p->pending.stream))*0x9E3779B97F4A7C15ull)^(uint64_t(min)<<40)^(uint64_t(vertices)<<20)^(uint64_t(fvf)<<8)^capability->role;
    BodyShadeEntry* cached=nullptr;const uint64_t light_key=lighting_key(p->lighting);
    std::array<float,3> camera_local{};const bool rim_pose=have_view&&body_camera_local(world,view,camera_local);
    if(!implicit){auto it=cache.entries.find(cache_key);
        if(it!=cache.entries.end()){auto& e=it->second;
            if(e.stream==reinterpret_cast<uintptr_t>(p->pending.stream)&&e.min==min&&e.vertices==vertices&&e.fvf==fvf&&e.stage==stage_op&&e.role==capability->role&&e.lighting==light_key&&
               e.rim==have_view&&(have_view==rim_pose)&&body_pose_close(e,world,rim_pose,camera_local)&&e.source==g.bytes)cached=&e;}}
    if(cached){g.bytes=cached->out;changed=cached->changed;++cache.hits;}
    else if(implicit){const auto hr=atmosphere::native_wheel_energy(*p,n,[&](uint32_t slot,const Args& a,HRESULT h){atmosphereintegration::notify(d,slot,a,h);});
        if(hr!=S_OK)return FAILED(hr)?hr:reject("body_wheel_energy_unsupported");changed=vertices;}
    else{std::vector<uint8_t> source=g.bytes;
    if(!normals){for(size_t at=0;at<g.bytes.size();at+=24){uint32_t before=0;std::memcpy(&before,g.bytes.data()+at+12,4);const auto after=atmosphere::flat_body_color(before,p->lighting);std::memcpy(g.bytes.data()+at+12,&after,4);changed+=before!=after;}}
    else if(!shade(g.bytes,36,24,12,world,p->lighting,false,changed,capability->role,have_view?&view:nullptr))return reject("body_material_invalid_normal_transform");
    // 5.14 night: the opaque env stage is MODULATEALPHA_ADDCOLOR (current +
    // current.alpha * env). With blending and alpha test off (checked above)
    // vertex alpha only weights the reflection, so it carries the night
    // environment energy (same factor as static reflections). Day unchanged.
    if(normals&&!flat&&!alpha_test&&stage_op==D3DTOP_MODULATEALPHA_ADDCOLOR&&p->lighting.ambient_strength<.5f){
        const float k=float((atmosphere::world_environment_factor(p->lighting)>>8)&255)/255;
        for(size_t at=27;at<g.bytes.size();at+=36)g.bytes[at]=uint8_t(std::lround(float(g.bytes[at])*k));}
    ++cache.misses;if(cache.entries.size()>=1024)cache.entries.clear();
    auto& e=cache.entries[cache_key];e.stream=reinterpret_cast<uintptr_t>(p->pending.stream);e.min=min;e.vertices=vertices;e.fvf=fvf;e.stage=stage_op;e.role=capability->role;
    e.lighting=light_key;e.rim=have_view;e.world=world;e.view=view;e.camera_local=camera_local;e.source=std::move(source);e.out=g.bytes;e.changed=changed;}
    stage(ps2port::perf::AtmoBodyShade);
    if(const auto now=GetTickCount64();now-cache.log_at>10000){if(cache.log_at)try{session().write("{\"type\":\"atmosphere_body_shade_cache\",\"hits\":"+std::to_string(cache.hits)+",\"misses\":"+std::to_string(cache.misses)+",\"entries\":"+std::to_string(cache.entries.size())+"}");}catch(...){}cache.log_at=now;cache.hits=cache.misses=0;}
    const auto hr=implicit?S_OK:atmosphereintegration::upload(d,*p,min,vertices,g.bytes);if(FAILED(hr)){if(p->pending.any())return atmosphereintegration::repair(d);return reject("body_material_private_upload_failed");}
    if(FAILED(environment_exposure(d,*p)))return atmosphereintegration::repair(d);
    applied=true;p->body_vertices+=changed;
    // R-SURFACE1 G1: the grime pass covers paint, panels, trim, flat underbody and wheel covers of car bodies (never glass,
    // lamps, wheels, interior or crew).
    // G1.1: crew and cabin interior never (registry roles call suits/heads "flat" and seats "paint"); wheels and tyres get a
    // uniform layer in wheel-local space.
    // G1.3: every car-resource draw (crew and interior included) feeds the model's shell; the candidate keeps only the
    // exterior triangles (vehicle_grime_shell.hpp). Wheel resources are never culled.
    if(grimeintegration::overlay_active()){
        const grimeintegration::Filter* gf=nullptr;
        if(part=="car"){grimeintegration::remember_car(d.trace.frame_number(),owner.owner.instance,world,family);
            gf=grimeintegration::shell_filter(d,cert.race_generation,grimeintegration::draw_key(p->pending.stream,p->pending.indices,p->pending.base,min,vertices,start,count),family,&g.bytes,stride,&g.indices,min,grimeoverlay::cabin_marker(binding.names[0]));}
        if(!grimeoverlay::crew_or_interior(binding.names[0])){
            // G2.2: metal of the car resource (bull bars, bumpers, racks) is body, not a rim (it got the faint rim layer).
            const auto role=capability->role;const bool tyre=role==atmosphere::WheelRubber,rim=role==atmosphere::WheelMetal&&part=="wheel";
            if(tyre||rim)   // wheel resource (wheel-local) or tyres/rims modelled inside the car resource (imported cars)
                grimeintegration::note_body(d,owner.owner.instance,world,min,vertices,start,count,g.bytes,stride,cert.race_generation,tyre?grimeoverlay::Wheel:grimeoverlay::Rim,gf);
            else if(part=="car"&&!implicit&&(role==atmosphere::Paint||role==atmosphere::OpaquePanel||role==atmosphere::OpaqueTrim||role==atmosphere::OpaqueFlat||role==atmosphere::OpaqueCover||role==atmosphere::WheelMetal))
                grimeintegration::note_body(d,owner.owner.instance,world,min,vertices,start,count,g.bytes,stride,cert.race_generation,alpha_test?grimeoverlay::Decal:grimeoverlay::Body,gf);   // cut-outs stay holes
        }
    }
    // 6.7: this body draw receives the other cars' headlights (sun_world pass).
    if(p->headlight_style.enabled&&p->lighting.ambient_strength<.5f&&!implicit){const unsigned st=normals?36u:24u;std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};
        for(size_t at=0;at+12<=g.bytes.size();at+=st){float v3[3];std::memcpy(v3,g.bytes.data()+at,12);for(unsigned k=0;k<3;++k){lo[k]=std::min(lo[k],v3[k]);hi[k]=std::max(hi[k],v3[k]);}}
        if(std::isfinite(lo[0]+hi[0]+lo[1]+hi[1]+lo[2]+hi[2])&&hi[0]>=lo[0]){auto& c=p->headlight_candidate;c.frame=d.trace.frame_number();c.min=min;c.vertices=vertices;c.start=start;c.count=count;c.instance=owner.owner.instance;
            const float bx=(lo[0]+hi[0])*.5f,by=(lo[1]+hi[1])*.5f,bz=(lo[2]+hi[2])*.5f;c.centre={bx*world._11+by*world._21+bz*world._31+world._41,bx*world._12+by*world._22+bz*world._32+world._42,bx*world._13+by*world._23+bz*world._33+world._43};
            c.radius=.5f*std::sqrt((hi[0]-lo[0])*(hi[0]-lo[0])+(hi[1]-lo[1])*(hi[1]-lo[1])+(hi[2]-lo[2])*(hi[2]-lo[2]))*std::max({std::hypot(world._11,world._12,world._13),std::hypot(world._21,world._22,world._23),std::hypot(world._31,world._32,world._33)});}}
    if(!debug_original.empty())debug_sample(d,*p,"native_owner_material",family,debug_original.data(),g.bytes.data(),vertices,world);
    if(p->first_reason(("body_native_"+family+part+binding.names[0]).c_str()))session().write("{\"type\":\"atmosphere_body_material\",\"route\":\"native_owner_material\",\"family\":"+quote(family)+",\"primary\":"+quote(binding.names[0])+",\"secondary\":"+quote(binding.names[1])+",\"resource\":"+quote(part)+",\"capability_source\":"+quote(std::string(p->body_capabilities.registered(family)?"registry":"addon_naming_contract"))+",\"metadata_payload_sha256\":"+quote(p->body_capabilities.payload_sha)+",\"surface_role\":"+quote(std::string(atmosphere::body_role_name(capability->role)))+",\"private_damage_tree\":"+(owner.owner.private_tree?"true":"false")+",\"geometry_hash_required\":false,\"changed_vertices\":"+std::to_string(changed)+",\"shared_buffer_mutated\":false,\"reflection_uv_changed\":false,\"environment_exposure_requested\":false,\"frame\":"+std::to_string(d.trace.frame_number())+"}");
    return S_OK;
}
// REFLECT-ADDON1: registered paint authority for the PS2 reflection (reflection_paint_authority.hpp). A body draw of
// vehicles/<family>/car whose BodyMaterials role is paint, for families without an exact kReflectionMaterials entry
// (retail cars keep their PS2-verified carshiny groups). Answers are remembered per race and draw.
inline const char* registered_paint_authority(void* device,UINT min,UINT vertices,UINT start,UINT count)noexcept{
    try{
        auto& d=*static_cast<Device8*>(device);auto* p=atmosphereintegration::pilot(d);
        if(!p||!vertices||vertices>8192||!count||count>8192||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id())return nullptr;
        const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),pc=exe+0x17707e;
        bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return nullptr;
        if(!atmosphereintegration::vehicle_draw_probe||!atmosphereintegration::vehicle_draw_probe(d,pc,min,vertices,start,count,cert.race_generation))return nullptr;
        auto& n=*d.native();IDirect3DVertexBuffer8* vb=nullptr;IDirect3DIndexBuffer8* ib=nullptr;UINT stride=0,base=0;n.GetStreamSource(0,&vb,&stride);n.GetIndices(&ib,&base);
        const auto key=grimeintegration::draw_key(vb,ib,base,min,vertices,start,count);if(vb)vb->Release();if(ib)ib->Release();
        struct Memo{uint64_t race=UINT64_MAX;std::unordered_map<uint64_t,const char*> known;};static Memo memo;static std::set<std::string> names;
        if(memo.race!=cert.race_generation){memo.known.clear();memo.race=cert.race_generation;}
        if(const auto it=memo.known.find(key);it!=memo.known.end())return it->second;
        const char* answer=nullptr;
        frontendmodelintegration::Context owner;atmosphere::NativeMaterialBinding binding;uint32_t name_id=0;std::string resource;
        if(frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner)&&atmosphere::native_material_binding(exe,owner.mesh,frontendmodelintegration::word,binding)&&
           frontendmodelintegration::word(owner.owner.packet+0xc,name_id)&&atmosphere::native_name(exe,name_id,frontendmodelintegration::word,resource)){
            for(auto& c:resource){c=char(std::tolower(static_cast<unsigned char>(c)));if(c=='\\')c='/';}
            const auto slash=resource.find('/',9);
            if(resource.rfind("vehicles/",0)==0&&slash!=std::string::npos&&resource.substr(slash+1)=="car"){
                const auto family=resource.substr(9,slash-9);bool table=false;
                for(const auto& m:ps2port::kReflectionMaterials){std::string v=m.vehicle;for(auto& c:v)c=char(std::tolower(static_cast<unsigned char>(c)));if(v==family){table=true;break;}}
                p->body_capabilities.load(p->body_path);
                const auto* capability=table?nullptr:p->body_capabilities.native_capability(family,binding.names[0],binding.names[1],"car");
                if(capability&&capability->role==atmosphere::Paint&&!grimeoverlay::crew_or_interior(binding.names[0]))answer=names.insert(family).first->c_str();
            }
        }
        if(memo.known.size()>65536)memo.known.clear();memo.known.emplace(key,answer);
        if(answer&&p->first_reason(("reflect_addon_"+std::string(answer)).c_str()))session().write("{\"type\":\"ps2_reflection_addon_family\",\"family\":"+quote(std::string(answer))+"}");
        return answer;
    }catch(...){return nullptr;}
}
inline const bool registered_paint_authority_installed=(ps2integration::paint_authority_hook=&registered_paint_authority,true);
// R-SURFACE1 G1.3: a car draw under a $switch node (the blight-off brake lens that the PS2 glow is built on, windows): the
// owner walk does not reach it, but the game draws it with its car's WORLD. Matched against the cars drawn earlier this
// frame. Opaque -> Lamp, alpha-tested -> Decal (masked), SRCALPHA glass with the env stage -> Glass; plain blended cards
// (glow layers) never. Returns false when no car matched (the caller memoises the draw after 30 such frames).
inline bool grime_switch_part(Device8& d,atmosphere::Pilot& p,IDirect3DDevice8& n,UINT min,UINT vertices,UINT start,UINT count,DWORD blend,DWORD test,DWORD fvf,uint64_t race,uint64_t key)noexcept{
    try{
        D3DMATRIX world{};if(FAILED(n.GetTransform(D3DTS_WORLD,&world)))return false;
        const auto frame=d.trace.frame_number();const auto* car=grimeintegration::match_car(frame,world);if(!car)return false;
        const uintptr_t instance=car->instance;const std::string family=car->family;
        int kind=-1;
        if(blend){DWORD src=0,dst=0,op1=D3DTOP_DISABLE;n.GetRenderState(D3DRS_SRCBLEND,&src);n.GetRenderState(D3DRS_DESTBLEND,&dst);n.GetTextureStageState(1,D3DTSS_COLOROP,&op1);
            if(src==D3DBLEND_SRCALPHA&&dst==D3DBLEND_INVSRCALPHA&&op1!=D3DTOP_DISABLE&&fvf==0x152)kind=grimeoverlay::Glass;}
        else kind=test?grimeoverlay::Decal:grimeoverlay::Lamp;
        auto& o=grimeintegration::overlay();
        if(o.census){const uint64_t ck=0x5157ull^(key*31)^(uint64_t(blend)<<1)^(uint64_t(test)<<2);
            if(o.censused.size()<4096&&o.censused.insert(ck).second)session().write("{\"type\":\"grime_census\",\"family\":"+quote(family)+",\"part\":\"switch\",\"blend\":"+std::to_string(blend)+
                ",\"test\":"+std::to_string(test)+",\"fvf\":"+std::to_string(fvf)+",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(count)+",\"kind\":"+std::to_string(kind)+"}");}
        if(kind<0)return true;   // glow cards: no grime, and never an occluder of the shell
        IDirect3DVertexBuffer8* vb=nullptr;IDirect3DIndexBuffer8* ib=nullptr;UINT vstride=0,base=0;n.GetStreamSource(0,&vb,&vstride);n.GetIndices(&ib,&base);
        const auto fkey=grimeintegration::draw_key(vb,ib,base,min,vertices,start,count);if(vb)vb->Release();if(ib)ib->Release();
        const auto* gf=grimeintegration::shell_filter(d,race,fkey,family,nullptr,0,nullptr,min);
        if(!gf&&!p.pending.any()){atmosphereintegration::Geometry g;const bool ok=atmosphereintegration::geometry(d,p,min,vertices,start,count,g);const unsigned stride=p.pending.stride;
            if(!p.pending.any())p.pending.release();if(ok&&stride>=12)gf=grimeintegration::shell_filter(d,race,fkey,family,&g.bytes,stride,&g.indices,min);}
        if(!gf)return true;
        const auto before=o.cand.frame;
        grimeintegration::note_part(d,instance,world,min,vertices,start,count,unsigned(kind),race,gf);
        if(o.cand.frame!=before)++o.switch_draws;
        return true;
    }catch(...){return true;}
}
// R-SURFACE1 G1.2: every car draw that the opaque body route did not accept: opaque lamps/logos/stickers (registry role
// "native"), blended and alpha-tested glass/lamps/grilles/decals, rims with a paint env, and whole bodies the route rejected
// by state (imported cars). Records a grime candidate only; car-local bounds are read once per draw from the buffer shadow.
// VehicleGrime.ini Census=1 logs every (family, part, texture pair, state) once with the decision.
inline void grime_blended(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc)noexcept{
    try{
        if(!grimeintegration::overlay_active()||type!=D3DPT_TRIANGLELIST||!vertices||!count||pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||
           !d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return;
        auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||p->pending.any())return;
        auto& n=*d.native();DWORD blend=FALSE,test=FALSE,dest=0,fvf=0;
        if(FAILED(n.GetRenderState(D3DRS_ALPHABLENDENABLE,&blend))||FAILED(n.GetRenderState(D3DRS_ALPHATESTENABLE,&test))||FAILED(n.GetVertexShader(&fvf)))return;
        if(blend&&(FAILED(n.GetRenderState(D3DRS_DESTBLEND,&dest))||dest==D3DBLEND_ONE))return;   // additive glow: never
        bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return;
        // PERF: most draws at this return address are course draws. Draws that proved not to be a car (static VB/IB/range)
        // are remembered per race, so the owner stack walk runs once per such draw instead of every frame.
        auto& og=grimeintegration::overlay();if(og.not_car_race!=cert.race_generation){og.not_car.clear();og.not_car_race=cert.race_generation;}
        uint64_t draw_key=0;{IDirect3DVertexBuffer8* vb=nullptr;IDirect3DIndexBuffer8* ib=nullptr;UINT vstride=0,base=0;
            if(SUCCEEDED(n.GetStreamSource(0,&vb,&vstride))&&vb){draw_key^=uint64_t(reinterpret_cast<uintptr_t>(vb))*0x9E3779B97F4A7C15ull;vb->Release();}
            if(SUCCEEDED(n.GetIndices(&ib,&base))&&ib){draw_key^=(uint64_t(reinterpret_cast<uintptr_t>(ib))*0xC2B2AE3D27D4EB4Full)^base;ib->Release();}
            draw_key^=(uint64_t(min)<<44)^(uint64_t(vertices)<<24)^(uint64_t(start)<<4)^count;}
        if(og.not_car.count(draw_key))return;
        auto not_car=[&]{if(og.not_car.size()>65536)og.not_car.clear();og.not_car.insert(draw_key);};
        frontendmodelintegration::Context owner;if(!frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner)){
            // G1.3: draws under $switch nodes (blight-off brake lens, windows) have no owner but the car's exact WORLD.
            if(!grime_switch_part(d,*p,n,min,vertices,start,count,blend,test,fvf,cert.race_generation,draw_key)){auto& miss=og.switch_miss[draw_key];if(++miss>=30){og.switch_miss.erase(draw_key);not_car();}}
            return;}
        D3DMATRIX world{};if(FAILED(n.GetTransform(D3DTS_WORLD,&world))||!frontendmodelintegration::fleet_owner_world(owner,world))return;
        const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));atmosphere::NativeMaterialBinding binding;
        if(!atmosphere::native_material_binding(exe,owner.mesh,frontendmodelintegration::word,binding))return;
        uint32_t name_id=0;std::string resource;
        if(!frontendmodelintegration::word(owner.owner.packet+0xc,name_id)||!atmosphere::native_name(exe,name_id,frontendmodelintegration::word,resource))return;
        for(auto& c:resource){c=char(std::tolower(static_cast<unsigned char>(c)));if(c=='\\')c='/';}
        const auto slash=resource.find('/',9);if(resource.rfind("vehicles/",0)!=0||slash==std::string::npos){not_car();return;}
        const auto part=resource.substr(slash+1),family=resource.substr(9,slash-9);if(part!="car"&&part!="wheel"){not_car();return;}
        const auto& primary=binding.names[0];const auto& secondary=binding.names[1];
        // Geometry is read at most once per draw and race (bounds, shell collection).
        atmosphereintegration::Geometry g;unsigned stride=0;int have=-1;
        auto read=[&]()->bool{if(have<0){const bool ok=atmosphereintegration::geometry(d,*p,min,vertices,start,count,g);stride=p->pending.stride;if(!p->pending.any())p->pending.release();have=ok&&stride>=12;}return have==1;};
        const grimeintegration::Filter* gf=nullptr;
        // Glow / flare / shadow cards are never occluders (a brake glow card in front of the lens would hide the lens).
        if(part=="car"&&!grimeoverlay::has_any(primary,{"glow","flare","shadow"})){grimeintegration::remember_car(d.trace.frame_number(),owner.owner.instance,world,family);
            IDirect3DVertexBuffer8* vb=nullptr;IDirect3DIndexBuffer8* ib=nullptr;UINT vstride=0,base=0;n.GetStreamSource(0,&vb,&vstride);n.GetIndices(&ib,&base);
            const auto fkey=grimeintegration::draw_key(vb,ib,base,min,vertices,start,count);if(vb)vb->Release();if(ib)ib->Release();
            gf=grimeintegration::shell_filter(d,cert.race_generation,fkey,family,nullptr,0,nullptr,min);
            if(!gf&&read())gf=grimeintegration::shell_filter(d,cert.race_generation,fkey,family,&g.bytes,stride,&g.indices,min,grimeoverlay::cabin_marker(primary));}
        p->body_capabilities.load(p->body_path);
        const auto* capability=p->body_capabilities.native_capability(family,primary,secondary,part);
        const uint32_t role=capability?capability->role:0;
        int kind=-1;const char* why="";
        if(grimeoverlay::crew_or_interior(primary)){why="crew_or_interior";}
        else if(role==atmosphere::WheelRubber)kind=grimeoverlay::Wheel;
        else if(part=="wheel")kind=grimeoverlay::Rim;   // rims, also with a paint env (imported wheels)
        else if(!blend&&!test&&(role==atmosphere::Paint||role==atmosphere::OpaquePanel||role==atmosphere::OpaqueTrim||role==atmosphere::OpaqueFlat||role==atmosphere::OpaqueCover||role==atmosphere::WheelMetal))kind=grimeoverlay::Body;
        else{kind=grimeoverlay::blended_kind(primary,secondary);if(kind<0)why="glow_or_excluded";}
        auto& o=grimeintegration::overlay();
        if(o.census){const uint64_t key=std::hash<std::string>{}(family+"|"+part+"|"+primary+"|"+secondary)^(uint64_t(blend)<<1)^(uint64_t(test)<<2)^(uint64_t(fvf)<<8);
            if(o.censused.size()<4096&&o.censused.insert(key).second){DWORD lighting=0,op1=0;n.GetRenderState(D3DRS_LIGHTING,&lighting);n.GetTextureStageState(1,D3DTSS_COLOROP,&op1);
                session().write("{\"type\":\"grime_census\",\"family\":"+quote(family)+",\"part\":"+quote(part)+",\"primary\":"+quote(primary)+",\"secondary\":"+quote(secondary)+
                    ",\"role\":"+std::to_string(role)+",\"blend\":"+std::to_string(blend)+",\"test\":"+std::to_string(test)+",\"fvf\":"+std::to_string(fvf)+",\"lighting\":"+std::to_string(lighting)+
                    ",\"stage1_op\":"+std::to_string(op1)+",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(count)+",\"kind\":"+std::to_string(kind)+",\"shell\":"+std::to_string(gf?int(gf->state):-1)+",\"skip\":"+quote(std::string(why))+"}");}}
        if(kind<0)return;
        // Car-local bounds: wheels always contribute their own; body-type draws contribute when the body route never saw this car.
        const bool wheel=grimeoverlay::kind_wheel(unsigned(kind));
        const bool need=wheel||kind==grimeoverlay::Body||o.bounds.find(owner.owner.instance)==o.bounds.end();
        const uint64_t bkey=(uint64_t(owner.owner.instance)*0x9E3779B97F4A7C15ull)^(uint64_t(min)<<40)^(uint64_t(vertices)<<20)^start;
        if(need&&(o.bounds_race!=cert.race_generation||!o.bounded.count(bkey))){
            if(read()){if(o.bounded.size()>8192)o.bounded.clear();
                grimeintegration::note_body(d,owner.owner.instance,world,min,vertices,start,count,g.bytes,stride,cert.race_generation,unsigned(kind),gf);o.bounded.insert(bkey);return;}
        }
        grimeintegration::note_part(d,owner.owner.instance,world,min,vertices,start,count,unsigned(kind),cert.race_generation,gf);
    }catch(...){}
}
}
