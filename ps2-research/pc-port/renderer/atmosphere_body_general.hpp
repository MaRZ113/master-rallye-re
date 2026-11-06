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
// 6.12 glints: one point per lens = connected triangle components (vertices at the same position are
// joined across UV seams, touching parts merged), centred on the component's bounds; per quadrant
// (left/right x front/rear) only lenses >= 50% of the largest face size. Uses the draw's CPU mirror
// (geometry), never the live stream (a private upload replaces it).
inline void record_lamp_points(atmosphere::Pilot& p,uint64_t frame,uintptr_t instance,const std::vector<uint8_t>& bytes,unsigned stride,const std::vector<uint32_t>& indices,const D3DMATRIX& w)noexcept{
    try{
        if(p.lamp_points_frame!=frame){p.lamp_points.clear();p.lamp_points_frame=frame;}
        const size_t n=stride?bytes.size()/stride:0;if(p.lamp_points.size()>=96||!n||n>4096||indices.size()<3)return;
        std::vector<uint32_t> parent(n);for(uint32_t i=0;i<n;++i)parent[i]=i;
        auto find=[&](uint32_t a){while(parent[a]!=a){parent[a]=parent[parent[a]];a=parent[a];}return a;};
        auto join=[&](uint32_t a,uint32_t b){a=find(a);b=find(b);if(a!=b)parent[b]=a;};
        auto pos=[&](size_t i){std::array<float,3> v{};std::memcpy(v.data(),bytes.data()+i*stride,12);return v;};
        for(size_t t=0;t+2<indices.size();t+=3){if(indices[t]>=n||indices[t+1]>=n||indices[t+2]>=n)return;join(indices[t],indices[t+1]);join(indices[t],indices[t+2]);}
        {std::vector<uint32_t> order(n);for(uint32_t i=0;i<n;++i)order[i]=i;std::sort(order.begin(),order.end(),[&](uint32_t a,uint32_t b){return pos(a)[0]<pos(b)[0];});
         for(size_t a=0;a<n;++a)for(size_t b=a+1;b<n;++b){const auto pa=pos(order[a]),pb=pos(order[b]);if(pb[0]-pa[0]>.001f)break;
             if(std::abs(pa[1]-pb[1])<=.001f&&std::abs(pa[2]-pb[2])<=.001f)join(order[a],order[b]);}}
        struct Part{std::array<float,3> lo{1e30f,1e30f,1e30f},hi{-1e30f,-1e30f,-1e30f};unsigned count=0;bool live=true;};std::vector<Part> parts;std::vector<int> slot(n,-1);
        std::vector<uint8_t> used(n,0);for(auto i:indices)used[i]=1;
        for(uint32_t i=0;i<n;++i){if(!used[i])continue;const auto r=find(i);if(slot[r]<0){slot[r]=int(parts.size());parts.emplace_back();}auto& q=parts[size_t(slot[r])];const auto v=pos(i);
            if(!std::isfinite(v[0]+v[1]+v[2]))return;for(unsigned k=0;k<3;++k){q.lo[k]=std::min(q.lo[k],v[k]);q.hi[k]=std::max(q.hi[k],v[k]);}++q.count;}
        for(bool merged=true;merged;){merged=false;   // lens glass + rim / bulb: touching parts are one lamp
            for(size_t a=0;a<parts.size();++a)for(size_t b=a+1;b<parts.size();++b){auto& A=parts[a];auto& B=parts[b];if(!A.live||!B.live)continue;bool touch=true;
                for(unsigned k=0;k<3;++k)if(A.lo[k]>B.hi[k]+.02f||B.lo[k]>A.hi[k]+.02f){touch=false;break;}
                if(touch){for(unsigned k=0;k<3;++k){A.lo[k]=std::min(A.lo[k],B.lo[k]);A.hi[k]=std::max(A.hi[k],B.hi[k]);}A.count+=B.count;B.live=false;merged=true;}}}
        auto centre=[](const Part& q,unsigned k){return (q.lo[k]+q.hi[k])*.5f;};
        auto quadrant=[&](const Part& q){return unsigned(centre(q,0)<0?0:1)+unsigned(centre(q,2)<0?2:0);};
        auto extent=[](const Part& q){const float x=q.hi[0]-q.lo[0],y=q.hi[1]-q.lo[1];return std::sqrt(x*x+y*y);};   // face size (lenses face +-Z)
        std::array<float,4> largest{};for(const auto& q:parts)if(q.live&&q.count>=3)largest[quadrant(q)]=std::max(largest[quadrant(q)],extent(q));
        const std::array<float,3> forward=atmosphere::normalized({w._31,w._32,w._33});
        for(const auto& q:parts){if(!q.live||q.count<3||extent(q)<.5f*largest[quadrant(q)])continue;
            if(std::abs(centre(q,2))<1.2f)continue;   // 6.8: side repeaters / marker lamps get no glint
            const float x=centre(q,0),y=centre(q,1),z=std::abs(q.hi[2])>std::abs(q.lo[2])?q.hi[2]:q.lo[2];   // outer face of the lens
            atmosphere::Pilot::LampPoint lp;lp.instance=instance;lp.front=z>0;
            lp.world={x*w._11+y*w._21+z*w._31+w._41,x*w._12+y*w._22+z*w._32+w._42,x*w._13+y*w._23+z*w._33+w._43};
            for(unsigned k=0;k<3;++k)lp.axis[k]=lp.front?forward[k]:-forward[k];
            bool duplicate=false;for(const auto& o:p.lamp_points){const float dx=o.world[0]-lp.world[0],dy=o.world[1]-lp.world[1],dz=o.world[2]-lp.world[2];
                if(o.instance==instance&&dx*dx+dy*dy+dz*dz<.0025f){duplicate=true;break;}}
            if(!duplicate)p.lamp_points.push_back(lp);}
    }catch(...){}
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
    const unsigned x=std::min(t.width-1,unsigned(u*t.width)),y=std::min(t.height-1,unsigned(v*t.height));const auto c=t.pixels[size_t(y)*t.width+x];
    const unsigned r=(c>>16)&255,g=(c>>8)&255,b=c&255,lo=std::min({r,g,b}),hi=std::max({r,g,b});return lo>=140&&hi-lo<=60;
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
            for(const auto& raw:binding.names){std::string name=raw;for(auto& c:name)c=char(std::tolower(static_cast<unsigned char>(c)));
                if(name.find("lightson")!=std::string::npos||name.find("glow")!=std::string::npos)return S_OK;}
            // 6.5: lamp lens textures (front white / rear red share one atlas) are
            // emissive while the headlights are on: boost instead of darkening.
            {std::string primary=binding.names[0];for(auto& c:primary)c=char(std::tolower(static_cast<unsigned char>(c)));
             lamp=p->headlight_style.enabled&&p->headlight_style.lamp_emissive>0&&(primary.find("light")!=std::string::npos||primary.find("lamp")!=std::string::npos)&&
                  primary.find("windscreen")==std::string::npos&&primary.find("glass")==std::string::npos;}
            // 6.7: car-space centroid of this pass (CPU mirror) -> front/rear; the
            // off-state brake lamp mesh sits where the glow card was observed.
            if(p->headlight_style.enabled&&p->headlight_style.lamp_emissive>0&&lamp_centroid(d,n,min,vertices,centroid)){
                rear_lamp=centroid[2]<-1.2f;
                if(!lamp&&p->brake_local_valid&&std::abs(centroid[1]-p->brake_local[1])<.35f&&std::abs(centroid[2]-p->brake_local[2])<.5f){lamp=true;rear_lamp=true;brake_zone=true;}}
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
                D3DMATRIX w{};if(p->glint_style.enabled&&SUCCEEDED(n.GetTransform(D3DTS_WORLD,&w)))record_lamp_points(*p,d.trace.frame_number(),owner.owner.instance,g.bytes,st,g.indices,w);}}
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
