#pragma once
// Opt-in PS2HudMap (default 0): the PS2 race minimap (gaHudAiMap) in place of the PC round GPS radar.
//
// Evidence: ps2-research/ui2/minimap.md + minimap-format.json (R5900 146118/1469f0/146d80/147038, 318e10)
// and ps2-research/hud-dump1/findings.md (GS dumps: background, frame, chevron, colours).
// * Player-centred, heading-up: local = 0.4*(Hz*dx-Hx*dz, Hx*dx+Hz*dz), centre (74,392) of the 640x480 HUD.
// * Heading H = -normalize_xz(forward + 0.1*velocity); each frame Z (else X) steps toward zero by 0.045
//   when it differs from the previous value by more than that (PS2 owner +74/+78), then renormalised.
// * Route: RaceLine markers max(last-32,0) <= i < min(last+32,finish), each segment Cohen-Sutherland clipped to
//   +-45 x +-43 and stroked on its own (146d80 flushes ordinary segments separately): shadow width 6 RGB
//   (0.2,0.6,0.1)*127 alpha 127, front width 3 RGB *250 alpha 250 (GS alpha = command alpha >> 1).
// * Finish crossbar white across the finish segment. Background, frame and chevron from the GS dump vertices.
// PC side: the RaceLine list is the one the PC GPS (4a57a0) reads; the round radar (hud-template_001) and its
// pointer (hud-template_007) UI draws are replaced only on exact level-0 identity, placed by the radar WVP.
#include "ps2_hud_damage.hpp"
#include <cmath>
#include <vector>

namespace gfx2::ps2port {

inline constexpr float kMapScale=.4f,kMapHalfW=45.f,kMapHalfH=43.f,kMapCx=74.f,kMapCy=392.f;
inline constexpr int kMapWindow=32;
inline constexpr float kMapHeadingStep=.045f;
// PC radar entity (Hud0.xml / F10: WORLD translate 65,60 bottom-origin); the PS2 map is placed in the same
// 640x480 frame through the radar draw's WORLD*VIEW*PROJ.
inline constexpr float kPcRadarX=65.f,kPcRadarY=60.f;
// PC DataGx/Hud/hud-template_001_000.dxt (radar, 128x128) and _007_000.dxt (GPS pointer, 8x8), stored rows.
inline constexpr char kPcRadarSha[]="8ab77428394f8a65211c7459cad50509146203931abc21479c9b6eb807058026";
inline constexpr char kPcPointerSha[]="7a4d7f7dfa6bc68062893b641020b0a6da48bdac3bf6f89e5b0e6046b4a760cd";

inline std::string pc_level0_sha(const BYTE* bits,INT pitch,D3DFORMAT format,UINT w,UINT h) noexcept {
    try {
        if(!bits||!w||!h||pitch<INT(w*4)||(format!=D3DFMT_A8R8G8B8&&format!=D3DFMT_X8R8G8B8))return {};
        std::vector<BYTE> rows(size_t(w)*h*4);
        for(UINT y=0;y<h;++y)std::memcpy(rows.data()+size_t(y)*w*4,bits+size_t(y)*pitch,w*4);
        if(format==D3DFMT_X8R8G8B8)for(size_t i=3;i<rows.size();i+=4)rows[i]=0xff;
        return sha256_bytes(rows.data(),rows.size());
    } catch(...) { return {}; }
}

struct MapPoint { float x=0,y=0; };

// PS2 heading filter (147038 owner +74 Z / +78 X).
class MapHeading {
    bool seeded_=false; float x_=0.f,z_=-1.f;
public:
    void reset() noexcept {seeded_=false;x_=0.f;z_=-1.f;}
    float x() const noexcept {return x_;}
    float z() const noexcept {return z_;}
    bool update(float fx,float fz,float vx,float vz) noexcept {
        float cx=fx+.1f*vx,cz=fz+.1f*vz;float n=std::sqrt(cx*cx+cz*cz);
        if(!(n>1e-6f)||!std::isfinite(n))return seeded_;
        cx=-cx/n;cz=-cz/n;
        if(seeded_){
            if(std::fabs(cz-z_)>kMapHeadingStep)cz+=cz>0.f?-kMapHeadingStep:kMapHeadingStep;
            else if(std::fabs(cx-x_)>kMapHeadingStep)cx+=cx>0.f?-kMapHeadingStep:kMapHeadingStep;
            n=std::sqrt(cx*cx+cz*cz);if(!(n>1e-6f))return true;cx/=n;cz/=n;
        }
        x_=cx;z_=cz;seeded_=true;return true;
    }
};

inline MapPoint map_local(float wx,float wz,float px,float pz,float hx,float hz) noexcept {
    const float dx=wx-px,dz=wz-pz;
    return {kMapScale*(hz*dx-hx*dz),kMapScale*(hx*dx+hz*dz)};
}
// Cohen-Sutherland against the inclusive rectangle +-halfW, +-halfH (outcodes top 1, bottom 2, right 4, left 8).
inline unsigned map_outcode(const MapPoint& p) noexcept {
    unsigned c=0;if(p.y<-kMapHalfH)c|=1;else if(p.y>kMapHalfH)c|=2;if(p.x>kMapHalfW)c|=4;else if(p.x<-kMapHalfW)c|=8;return c;
}
inline bool map_clip(MapPoint& a,MapPoint& b) noexcept {
    unsigned ca=map_outcode(a),cb=map_outcode(b);
    for(int guard=0;guard<8;++guard){
        if(!(ca|cb))return true;
        if(ca&cb)return false;
        const unsigned c=ca?ca:cb;MapPoint p;
        const float dx=b.x-a.x,dy=b.y-a.y;
        if(c&1){p.y=-kMapHalfH;p.x=a.x+dx*(p.y-a.y)/dy;}
        else if(c&2){p.y=kMapHalfH;p.x=a.x+dx*(p.y-a.y)/dy;}
        else if(c&4){p.x=kMapHalfW;p.y=a.y+dy*(p.x-a.x)/dx;}
        else {p.x=-kMapHalfW;p.y=a.y+dy*(p.x-a.x)/dx;}
        if(c==ca){a=p;ca=map_outcode(a);}else{b=p;cb=map_outcode(b);}
    }
    return false;
}

// Map frame (authored, top-down) to the PC screen through the radar placement.
inline bool map_screen(const HudPlacement& radar,float ax,float ay,float& sx,float& sy) noexcept {
    return hud_project(radar,ax-kPcRadarX,(480.f-ay)-kPcRadarY,sx,sy);
}
inline DWORD map_colour(unsigned r,unsigned g,unsigned b,unsigned gs_alpha) noexcept {
    const auto c=[](unsigned v){return DWORD(v>255?255:v);};
    return (c(gs_alpha*2)<<24)|(c(r)<<16)|(c(g)<<8)|c(b);
}
using MapStrip=std::vector<HudVertex>;
// Authored strip -> screen strip.
inline bool map_strip(const HudPlacement& radar,const std::vector<MapPoint>& pts,DWORD colour,MapStrip& out) noexcept {
    out.clear();
    for(const auto& p:pts){float sx=0,sy=0;if(!map_screen(radar,p.x,p.y,sx,sy))return false;out.push_back({sx-.5f,sy-.5f,0.f,1.f,colour,0.f,0.f});}
    return out.size()>=3;
}
// One stroked segment (map-local endpoints, offset by the centre) of full width w.
inline std::vector<MapPoint> map_segment(MapPoint a,MapPoint b,float w) {
    float nx=-(b.y-a.y),ny=b.x-a.x;const float n=std::sqrt(nx*nx+ny*ny);
    if(!(n>1e-6f))return {};
    nx*=.5f*w/n;ny*=.5f*w/n;
    return {{kMapCx+a.x+nx,kMapCy+a.y+ny},{kMapCx+a.x-nx,kMapCy+a.y-ny},{kMapCx+b.x+nx,kMapCy+b.y+ny},{kMapCx+b.x-nx,kMapCy+b.y-ny}};
}

// GS dump 195341 vertices, converted to the 640x480 HUD frame (top-down).
inline const std::vector<MapPoint>& map_background(){static const std::vector<MapPoint> v{{29.f,352.97f},{118.94f,352.97f},{29.f,430.96f},{118.94f,430.96f}};return v;}
inline const std::vector<MapPoint>& map_frame_shadow(){static const std::vector<MapPoint> v{{30.12f,353.14f},{23.81f,346.82f},{117.81f,353.14f},{124.12f,346.82f},{117.81f,430.78f},{124.12f,437.17f},{30.12f,430.78f},{23.81f,437.17f},{30.12f,353.14f},{23.81f,346.82f}};return v;}
inline const std::vector<MapPoint>& map_frame(){static const std::vector<MapPoint> v{{28.38f,351.39f},{25.56f,348.57f},{119.56f,351.39f},{122.38f,348.57f},{119.56f,432.54f},{122.38f,435.41f},{28.38f,432.54f},{25.56f,435.41f},{28.38f,351.39f},{25.56f,348.57f}};return v;}
inline const std::vector<MapPoint>& map_chevron_shadow(){static const std::vector<MapPoint> v{{73.75f,400.84f},{70.19f,399.08f},{76.94f,391.99f},{76.94f,387.95f},{80.19f,400.84f},{83.75f,399.08f}};return v;}
inline const std::vector<MapPoint>& map_chevron(){static const std::vector<MapPoint> v{{70.75f,397.85f},{67.19f,396.09f},{74.f,388.95f},{74.f,384.96f},{77.19f,397.85f},{80.75f,396.09f}};return v;}

struct MapInput {
    bool ok=false;
    float px=0,pz=0,fx=0,fz=0,vx=0,vz=0;
    int last=0,finish=0;                 // finish: route end index (exclusive)
    int first=0;                         // index of points[0]
    std::vector<MapPoint> points;        // world X/Z of RaceLine markers first..first+points.size()-1
    std::vector<int> splits;             // split BestMarker indices (Race/SplitTime%d/Percentage * count)
    struct Opponent { float x=0,z=0,r=1,g=1,b=1; };
    std::vector<Opponent> opponents;     // every other car: world X/Z and Race/Car%d/Colour (default white)
};
// Crossbar across the route at marker m (direction of segment m-1 -> m), half-length h, width 3 (GS dumps
// 195654 finish: 23.2 x 3.0; 161115 split: 19.9 x 3.0; EE factors 3 / 2.5 of 4).
inline bool map_crossbar(const MapInput& in,int m,float px,float pz,float hx,float hz,float h,std::vector<MapPoint>& out) {
    const int count=in.first+int(in.points.size());
    if(m<1||m>=count||m-1<in.first)return false;
    const auto& w0=in.points[size_t(m-1-in.first)];const auto& w1=in.points[size_t(m-in.first)];
    const MapPoint a=map_local(w0.x,w0.y,px,pz,hx,hz),b=map_local(w1.x,w1.y,px,pz,hx,hz);
    float dx=b.x-a.x,dy=b.y-a.y;const float n=std::sqrt(dx*dx+dy*dy);
    if(!(n>1e-6f))return false;
    dx/=n;dy/=n;MapPoint c{b.x-h*dy,b.y+h*dx},e{b.x+h*dy,b.y-h*dx};
    if(!map_clip(c,e))return false;
    out=map_segment(c,e,3.f);return !out.empty();
}
// Opponent X (EE 147038): two clipped diagonals +/-4 around the car, width 4; the shadow is the same X moved +2,+2.
inline void map_cross(MapPoint p,float shift,std::vector<std::vector<MapPoint>>& out) {
    const MapPoint d[2][2]={{{p.x-4.f+shift,p.y-4.f+shift},{p.x+4.f+shift,p.y+4.f+shift}},{{p.x-4.f+shift,p.y+4.f+shift},{p.x+4.f+shift,p.y-4.f+shift}}};
    for(const auto& s:d){MapPoint a=s[0],b=s[1];if(map_clip(a,b)){auto q=map_segment(a,b,4.f);if(!q.empty())out.push_back(std::move(q));}}
}
inline unsigned map_byte(float colour,float scale) noexcept {const float v=colour*scale;return v<=0.f?0u:v>=255.f?255u:unsigned(v);}

class PS2HudMap {
    bool requested_=false,disabled_=false;
    std::array<HudPcIdentity,8> identities_{};size_t next_identity_=0;
    HudPlacement radar_{};bool seen_=false;
    MapHeading heading_;uint64_t race_generation_=0;bool feed_ok_=false;
    uint64_t suppressed_=0;
public:
    PS2HudLayer layer;
    PS2HudMap(bool supported,const std::wstring& ini) noexcept {
        if(!supported)return;
        try{requested_=config::read_int(L"PS2HudMap",0,ini.c_str())==1;}catch(...){requested_=false;}
    }
    bool requested() const noexcept {return requested_&&!disabled_;}
    void disable() noexcept {disabled_=true;}
    bool feed_ok() const noexcept {return feed_ok_;}
    uint64_t suppressed() const noexcept {return suppressed_;}
    const MapHeading& heading() const noexcept {return heading_;}
    // 0 radar, 1 pointer, -1 other.
    HudPcIdentity identify(IDirect3DBaseTexture8* base,uint64_t generation) noexcept {
        const auto id=reinterpret_cast<uintptr_t>(base);
        if(!base||!generation)return {id,generation,-1,"stage0_texture_untracked"};
        for(const auto& c:identities_)if(c.texture==id&&c.generation==generation)return c;
        HudPcIdentity result{id,generation,-1,"not_pc_gps"};
        if(base->GetType()==D3DRTYPE_TEXTURE){
            auto* t=static_cast<IDirect3DTexture8*>(base);D3DSURFACE_DESC desc{};
            if(SUCCEEDED(t->GetLevelDesc(0,&desc))&&((desc.Width==128&&desc.Height==128)||(desc.Width==8&&desc.Height==8))&&
               (desc.Format==D3DFMT_A8R8G8B8||desc.Format==D3DFMT_X8R8G8B8)&&desc.Pool!=D3DPOOL_DEFAULT){
                D3DLOCKED_RECT lock{};
                if(SUCCEEDED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY))){
                    const auto sha=pc_level0_sha(static_cast<const BYTE*>(lock.pBits),lock.Pitch,desc.Format,desc.Width,desc.Height);
                    t->UnlockRect(0);
                    if(desc.Width==128&&sha==kPcRadarSha){result.index=0;result.reason="exact_pc_gps_radar";}
                    else if(desc.Width==8&&sha==kPcPointerSha){result.index=1;result.reason="exact_pc_gps_pointer";}
                }else result.reason="pc_gps_lock_failed";
            }
        }
        identities_[next_identity_]=result;next_identity_=(next_identity_+1)%identities_.size();
        return result;
    }
    void note_pc_draw(int index,const HudPlacement& placement) noexcept {
        ++suppressed_;if(index==0){radar_=placement;seen_=true;}
    }
    // Present: strips for this frame (empty when the PC drew no radar or the feed is down).
    std::vector<MapStrip> frame(const MapInput& in,uint64_t race_generation) {
        std::vector<MapStrip> strips;
        feed_ok_=in.ok;
        if(race_generation!=race_generation_){heading_.reset();race_generation_=race_generation;}
        const bool seen=seen_;seen_=false;const auto radar=radar_;radar_={};
        if(!in.ok)return strips;
        if(!heading_.update(in.fx,in.fz,in.vx,in.vz))return strips;
        if(!seen||!radar.valid)return strips;
        const auto add=[&](const std::vector<MapPoint>& pts,DWORD colour){MapStrip s;if(map_strip(radar,pts,colour,s))strips.push_back(std::move(s));};
        add(map_background(),map_colour(22,22,22,31));
        // Route window (PS2: LastMarker outside [1,count) becomes 0).
        const int count=in.first+int(in.points.size());
        const int last=(in.last<=0||in.last>=count)?0:in.last;
        const int lo=std::max(last-kMapWindow,0),hi=std::min(last+kMapWindow,in.finish);
        std::vector<std::pair<MapPoint,MapPoint>> segments;
        for(int i=lo;i+1<hi&&i+1<count;++i){
            if(i<in.first)continue;
            const auto& w0=in.points[size_t(i-in.first)];const auto& w1=in.points[size_t(i+1-in.first)];
            MapPoint a=map_local(w0.x,w0.y,in.px,in.pz,heading_.x(),heading_.z()),b=map_local(w1.x,w1.y,in.px,in.pz,heading_.x(),heading_.z());
            if(map_clip(a,b))segments.push_back({a,b});
        }
        for(const auto& s:segments)add(map_segment(s.first,s.second,6.f),map_colour(25,76,12,63));
        for(const auto& s:segments)add(map_segment(s.first,s.second,3.f),map_colour(50,150,25,125));
        // Split crossbars (green) and the finish crossbar (white) when their marker is inside the window.
        std::vector<MapPoint> bar;
        for(int m:in.splits)
            if(m-1>=lo&&m-1<hi&&map_crossbar(in,m,in.px,in.pz,heading_.x(),heading_.z(),10.f,bar))add(bar,map_colour(125,200,25,125));
        if(in.finish-1>=lo&&in.finish-1<hi&&map_crossbar(in,in.finish-1,in.px,in.pz,heading_.x(),heading_.z(),12.f,bar))add(bar,map_colour(250,250,250,125));
        add(map_chevron_shadow(),map_colour(6,12,25,125));
        // Opponents: shadow X (colour x 40) then X (colour x 250), per car.
        for(const auto& o:in.opponents){
            const MapPoint p=map_local(o.x,o.z,in.px,in.pz,heading_.x(),heading_.z());
            std::vector<std::vector<MapPoint>> shadow,cross;map_cross(p,2.f,shadow);map_cross(p,0.f,cross);
            for(const auto& q:shadow)add(q,map_colour(map_byte(o.r,40.f),map_byte(o.g,40.f),map_byte(o.b,40.f),125));
            for(const auto& q:cross)add(q,map_colour(map_byte(o.r,250.f),map_byte(o.g,250.f),map_byte(o.b,250.f),125));
        }
        add(map_chevron(),map_colour(38,78,160,125));
        add(map_frame_shadow(),map_colour(9,9,9,31));
        add(map_frame(),map_colour(216,216,216,125));
        return strips;
    }
};

}  // namespace gfx2::ps2port
