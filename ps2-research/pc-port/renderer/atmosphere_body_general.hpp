#pragma once
#include "atmosphere_body_common.hpp"
#include "atmosphere_body_binding.hpp"
namespace gfx2::atmospherebody {
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
inline HRESULT night_energy(Device8& d,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,bool& applied)noexcept {
    applied=false;auto* p=atmosphereintegration::pilot(d);
    if(!p||!p->enabled()||!p->lighting.active()||p->lighting.ambient_strength>=.5f||!count||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    try{
        auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
        DWORD fvf=0,pixel=1;if(FAILED(n.GetVertexShader(&fvf))||FAILED(n.GetPixelShader(&pixel))||pixel||!groundintegration::render(d,n,D3DRS_LIGHTING,FALSE))return S_OK;
        frontendmodelintegration::Context owner;atmosphere::NativeMaterialBinding binding;std::string material;bool lamp=false,rear_lamp=false,brake_zone=false,reversing=false,mixed=false;std::array<float,3> centroid{};
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
                     if(p->glint_style.enabled)record_lamp_points(*p,d.trace.frame_number(),owner.owner.instance,g.bytes,st,g.indices,w,nullptr,0,true,false);
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
        if(lamp&&(fvf==0x152||fvf==0x142)){atmosphereintegration::Geometry g;const unsigned st=fvf==0x152?36u:24u,co=fvf==0x152?24u:12u,uvo=co+4;
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
                D3DMATRIX w{};if(p->glint_style.enabled&&SUCCEEDED(n.GetTransform(D3DTS_WORLD,&w))){if(!tex)tex=lens_texture(d,*p,n);
                    record_lamp_points(*p,d.trace.frame_number(),owner.owner.instance,g.bytes,st,g.indices,w,tex,uvo,false,false);}}}
        if(p->first_reason(("vehicle_night_energy_"+material).c_str()))session().write("{\"type\":\"atmosphere_vehicle_night_energy\",\"factor\":"+std::to_string(factor)+",\"unit\":"+std::to_string(unit)+",\"material\":"+quote(material)+"}");
        return S_OK;
    }catch(...){if(!p->pending.any())p->pending.release();return atmosphereintegration::repair(d);}
}
inline HRESULT general(Device8& d,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc,bool& applied) {
    auto* p=atmosphereintegration::pilot(d);if(!p||!p->enabled()||!p->body_materials||!p->lighting.active()||!vertices||vertices>8192||!count||count>8192||type!=D3DPT_TRIANGLELIST||
       pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0x17707e||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||GetCurrentThreadId()!=d.trace.render_thread_id())return S_OK;
    Timing timer(*p);auto& n=*d.native();bool single=false;const auto cert=courseintegration::certificate(d,single);if(!single||!cert.valid)return S_OK;
    auto reject=[&](const char* why){if(!p->pending.any())p->pending.release();if(p->body_debug&&d.trace.control.active&&p->first_reason(why))atmosphereintegration::log(d,why);return S_OK;};
    DWORD fvf=0,pixel=1;
    if(FAILED(n.GetVertexShader(&fvf))||(fvf!=0x152&&fvf!=0x142&&fvf!=0x112)||FAILED(n.GetPixelShader(&pixel))||pixel||
       !groundintegration::render(d,n,D3DRS_LIGHTING,FALSE)||!groundintegration::render(d,n,D3DRS_ALPHABLENDENABLE,FALSE)||!groundintegration::render(d,n,D3DRS_ALPHATESTENABLE,FALSE)||
       !groundintegration::render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||!groundintegration::render(d,n,D3DRS_ZWRITEENABLE,TRUE)||
       !groundintegration::stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||!groundintegration::stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||
       !groundintegration::stage(d,n,0,D3DTSS_RESULTARG,D3DTA_CURRENT)||!groundintegration::stage(d,n,2,D3DTSS_COLOROP,D3DTOP_DISABLE)||
       !groundintegration::render(d,n,D3DRS_VERTEXBLEND,D3DVBF_DISABLE)||!groundintegration::render(d,n,D3DRS_INDEXEDVERTEXBLENDENABLE,FALSE))return S_OK;
    DWORD stage_op=0;if(FAILED(n.GetTextureStageState(1,D3DTSS_COLOROP,&stage_op)))return S_OK;
    const bool flat=stage_op==D3DTOP_DISABLE;
    if(!flat&&((fvf!=0x152&&fvf!=0x112)||(stage_op!=D3DTOP_ADD&&stage_op!=D3DTOP_MODULATEALPHA_ADDCOLOR)||
        !groundintegration::stage(d,n,1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACENORMAL)||!groundintegration::stage(d,n,1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2)))return S_OK;
    courseintegration::Ref<IDirect3DSurface8> target,back;
    if(FAILED(n.GetRenderTarget(&target.p))||FAILED(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p))||!courseintegration::same_identity(target.p,back.p))return S_OK;
    frontendmodelintegration::Context owner;
    if(!frontendmodelintegration::fleet_owner(frontendmodelintegration::caller_stack,pc,owner))return S_OK;
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
    const bool implicit=fvf==0x112;
    if(implicit&&(!p->native_wheel_lighting||part!="wheel"||(capability->role!=atmosphere::WheelRubber&&capability->role!=atmosphere::WheelMetal)||flat||!groundintegration::stage(d,n,3,D3DTSS_COLOROP,D3DTOP_DISABLE)))return reject("body_implicit_diffuse_not_certified_wheel");
    if(!p->body_capabilities.extended&&flat!=(capability->role==atmosphere::OpaqueFlat))return reject("body_material_flat_role_pass_mismatch");
    courseintegration::Ref<IDirect3DBaseTexture8> texture;
    if(FAILED(n.GetTexture(0,&texture.p))||reinterpret_cast<uintptr_t>(texture.p)!=binding.textures[0]||!d.trace.resources.generation(binding.textures[0]))return reject("body_material_live_texture_mismatch");
    if(p->pending.any())return D3DERR_DEVICELOST;
    const bool normals=fvf==0x152;const unsigned stride=implicit?32u:normals?36u:24u;atmosphereintegration::Geometry g;if(!atmosphereintegration::geometry(d,*p,min,vertices,start,count,g)||p->pending.stride!=stride)return reject("body_material_current_mirror_missing");
    ps2port::RaceDescriptors desc;uintptr_t vb=0,ib=0;
    if(!ps2port::race_descriptors(exe,owner.mesh,frontendmodelintegration::word,desc)||!frontendmodelintegration::pointer_word(desc.vd[0],vb)||!frontendmodelintegration::pointer_word(desc.id[0],ib)||
       d.unwrap_vertex_buffer(reinterpret_cast<IDirect3DVertexBuffer8*>(vb))!=p->pending.stream||d.unwrap_index_buffer(reinterpret_cast<IDirect3DIndexBuffer8*>(ib))!=p->pending.indices||
       desc.vd[2]!=min||desc.vd[3]!=vertices||desc.vd[4]!=fvf||desc.vd[5]!=stride||desc.id[2]!=start||desc.id[3]!=count*3)return reject("body_material_current_descriptor_mismatch");
    std::vector<uint8_t> debug_original;if(normals&&p->body_debug&&d.trace.control.active)debug_original=g.bytes;
    uint64_t changed=0;
    D3DMATRIX view{};const bool have_view=p->lighting.rim&&SUCCEEDED(n.GetTransform(D3DTS_VIEW,&view));
    if(implicit){const auto hr=atmosphere::native_wheel_energy(*p,n,[&](uint32_t slot,const Args& a,HRESULT h){atmosphereintegration::notify(d,slot,a,h);});
        if(hr!=S_OK)return FAILED(hr)?hr:reject("body_wheel_energy_unsupported");changed=vertices;}
    else if(!normals){for(size_t at=0;at<g.bytes.size();at+=24){uint32_t before=0;std::memcpy(&before,g.bytes.data()+at+12,4);const auto after=atmosphere::flat_body_color(before,p->lighting);std::memcpy(g.bytes.data()+at+12,&after,4);changed+=before!=after;}}
    else if(!shade(g.bytes,36,24,12,world,p->lighting,false,changed,capability->role,have_view?&view:nullptr))return reject("body_material_invalid_normal_transform");
    // 5.14 night: the opaque env stage is MODULATEALPHA_ADDCOLOR (current +
    // current.alpha * env). With blending and alpha test off (checked above)
    // vertex alpha only weights the reflection, so it carries the night
    // environment energy (same factor as static reflections). Day unchanged.
    if(normals&&!flat&&stage_op==D3DTOP_MODULATEALPHA_ADDCOLOR&&p->lighting.ambient_strength<.5f){
        const float k=float((atmosphere::world_environment_factor(p->lighting)>>8)&255)/255;
        for(size_t at=27;at<g.bytes.size();at+=36)g.bytes[at]=uint8_t(std::lround(float(g.bytes[at])*k));}
    const auto hr=implicit?S_OK:atmosphereintegration::upload(d,*p,min,vertices,g.bytes);if(FAILED(hr)){if(p->pending.any())return atmosphereintegration::repair(d);return reject("body_material_private_upload_failed");}
    if(FAILED(environment_exposure(d,*p)))return atmosphereintegration::repair(d);
    applied=true;p->body_vertices+=changed;
    // 6.7: this body draw receives the other cars' headlights (sun_world pass).
    if(p->headlight_style.enabled&&p->lighting.ambient_strength<.5f&&!implicit){const unsigned st=normals?36u:24u;std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};
        for(size_t at=0;at+12<=g.bytes.size();at+=st){float v3[3];std::memcpy(v3,g.bytes.data()+at,12);for(unsigned k=0;k<3;++k){lo[k]=std::min(lo[k],v3[k]);hi[k]=std::max(hi[k],v3[k]);}}
        if(std::isfinite(lo[0]+hi[0]+lo[1]+hi[1]+lo[2]+hi[2])&&hi[0]>=lo[0]){auto& c=p->headlight_candidate;c.frame=d.trace.frame_number();c.min=min;c.vertices=vertices;c.start=start;c.count=count;c.instance=owner.owner.instance;
            const float bx=(lo[0]+hi[0])*.5f,by=(lo[1]+hi[1])*.5f,bz=(lo[2]+hi[2])*.5f;c.centre={bx*world._11+by*world._21+bz*world._31+world._41,bx*world._12+by*world._22+bz*world._32+world._42,bx*world._13+by*world._23+bz*world._33+world._43};
            c.radius=.5f*std::sqrt((hi[0]-lo[0])*(hi[0]-lo[0])+(hi[1]-lo[1])*(hi[1]-lo[1])+(hi[2]-lo[2])*(hi[2]-lo[2]))*std::max({std::hypot(world._11,world._12,world._13),std::hypot(world._21,world._22,world._23),std::hypot(world._31,world._32,world._33)});}}
    if(!debug_original.empty())debug_sample(d,*p,"native_owner_material",family,debug_original.data(),g.bytes.data(),vertices,world);
    if(p->first_reason(("body_native_"+family+part+binding.names[0]).c_str()))session().write("{\"type\":\"atmosphere_body_material\",\"route\":\"native_owner_material\",\"family\":"+quote(family)+",\"primary\":"+quote(binding.names[0])+",\"secondary\":"+quote(binding.names[1])+",\"resource\":"+quote(part)+",\"metadata_payload_sha256\":"+quote(p->body_capabilities.payload_sha)+",\"surface_role\":"+quote(std::string(atmosphere::body_role_name(capability->role)))+",\"private_damage_tree\":"+(owner.owner.private_tree?"true":"false")+",\"geometry_hash_required\":false,\"changed_vertices\":"+std::to_string(changed)+",\"shared_buffer_mutated\":false,\"reflection_uv_changed\":false,\"environment_exposure_requested\":false,\"frame\":"+std::to_string(d.trace.frame_number())+"}");
    return S_OK;
}
}
