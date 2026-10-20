#include "spline_objects.hpp"
#include "ps2_config.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>

namespace gfx2::ps2port {
namespace {
std::string hex(const uint8_t* p,size_t n){std::string s;for(size_t i=0;i<n;++i){s+="0123456789abcdef"[p[i]>>4];s+="0123456789abcdef"[p[i]&15];}return s;}
struct Reader {
    const uint8_t* p;size_t n,at=0;bool ok=true;
    template<class T> T get() noexcept {T v{};if(!ok||n-at<sizeof(T)){ok=false;return v;}std::memcpy(&v,p+at,sizeof(T));at+=sizeof(T);return v;}
    std::string text(size_t size) noexcept {
        if(!ok||n-at<size){ok=false;return {};}
        const auto* s=reinterpret_cast<const char*>(p+at);size_t len=0;while(len<size&&s[len])++len;
        // Zero padded, printable ASCII only.
        for(size_t i=0;i<size;++i){const unsigned char c=static_cast<unsigned char>(s[i]);if(i<len?(c<32||c>126):c!=0){ok=false;return {};}}
        at+=size;if(!len)ok=false;return std::string(s,len);
    }
    const uint8_t* bytes(size_t size) noexcept {if(!ok||n-at<size){ok=false;return nullptr;}const auto* r=p+at;at+=size;return r;}
};
bool finite3(const ps2spline::Vec3& v) noexcept {return std::isfinite(v[0])&&std::isfinite(v[1])&&std::isfinite(v[2]);}
}

bool decode_spline_objects_layout(const uint8_t* p,size_t n,SplineObjectsAsset& out) noexcept {
    out={};
    if(!p||n<32||n>kSplineObjectsMaximumAssetBytes||std::memcmp(p,"PS2SPL01",8))return false;
    try {
        Reader r{p,n,8};
        const uint32_t version=r.get<uint32_t>(),textures=r.get<uint32_t>(),models=r.get<uint32_t>();
        const uint32_t vertices=r.get<uint32_t>(),courses=r.get<uint32_t>(),objects=r.get<uint32_t>();
        if(!r.ok||version!=1||!textures||textures>16||!models||models>16||!vertices||vertices>65536||
           !courses||courses>64||!objects||objects>256)return false;
        SplineObjectsAsset a;
        for(uint32_t i=0;i<textures;++i){
            SplineTexture t;t.width=r.get<uint32_t>();t.height=r.get<uint32_t>();
            if(!r.ok||!t.width||!t.height||t.width>1024||t.height>1024||(t.width&(t.width-1))||(t.height&(t.height-1)))return false;
            const auto* px=r.bytes(size_t(t.width)*t.height*4);if(!px)return false;
            t.bgra.resize(size_t(t.width)*t.height);std::memcpy(t.bgra.data(),px,t.bgra.size()*4);
            a.textures.push_back(std::move(t));
        }
        uint32_t next=0;
        for(uint32_t i=0;i<models;++i){
            SplineModel m;m.name=r.text(16);const uint32_t draws=r.get<uint32_t>();
            uint32_t f[6]{};for(auto& v:f)v=r.get<uint32_t>();m.radius=r.get<float>();
            if(!r.ok||draws<1||draws>2||!std::isfinite(m.radius)||!(m.radius>0.f)||m.radius>1000.f)return false;
            for(uint32_t d=0;d<draws;++d){
                SplineModelDraw draw{f[d*3],f[d*3+1],f[d*3+2]};
                if(draw.texture>=textures||draw.first!=next||!draw.count||draw.count%3||draw.count>vertices-next)return false;
                next+=draw.count;m.draws.push_back(draw);
            }
            for(uint32_t d=draws;d<2;++d)if(f[d*3]||f[d*3+1]||f[d*3+2])return false;
            a.models.push_back(std::move(m));
        }
        if(next!=vertices)return false;
        const auto* vb=r.bytes(size_t(vertices)*sizeof(ObjectVertex));if(!vb)return false;
        a.vertices.resize(vertices);std::memcpy(a.vertices.data(),vb,size_t(vertices)*sizeof(ObjectVertex));
        for(const auto& v:a.vertices)if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)||!std::isfinite(v.u)||!std::isfinite(v.v)||
            std::fabs(v.x)>1000.f||std::fabs(v.y)>1000.f||std::fabs(v.z)>1000.f)return false;
        uint32_t first=0;
        for(uint32_t i=0;i<courses;++i){
            SplineCourseDef c;c.id=r.text(48);c.dx_path=r.text(64);
            const auto* sha=r.bytes(32);c.first=r.get<uint32_t>();c.count=r.get<uint32_t>();
            if(!r.ok||!sha||c.first!=first||!c.count||c.count>kSplineMaximumObjectsPerCourse||c.count>objects-first)return false;
            std::memcpy(c.retail_sha.data(),sha,32);first+=c.count;
            for(const auto& other:a.courses)if(course_id_matches(other.id,c.id))return false;
            a.courses.push_back(std::move(c));
        }
        if(first!=objects)return false;
        uint32_t points=0;
        for(uint32_t i=0;i<objects;++i){
            SplineObjectDef o;o.egg=r.text(32);o.model=r.get<uint32_t>();o.first_point=r.get<uint32_t>();o.point_count=r.get<uint32_t>();
            uint8_t flags[4]{};for(auto& f:flags)f=r.get<uint8_t>();
            auto& c=o.config;c.speed=r.get<float>();c.on=r.get<float>();c.off=r.get<float>();c.banking=r.get<float>();
            c.rest_ticks=r.get<int32_t>();c.samples=r.get<int32_t>();
            if(!r.ok||o.model>=models||o.first_point!=points||o.point_count<4||o.point_count>ps2spline::kMaxPoints)return false;
            for(auto f:flags)if(f>1)return false;
            c.const_speed=flags[0];c.loop=flags[1];c.trigger=flags[2];c.rest=flags[3];
            if(!std::isfinite(c.speed)||!(c.speed>.0001f)||!std::isfinite(c.on)||!std::isfinite(c.off)||!std::isfinite(c.banking)||
               c.samples<1||c.samples>ps2spline::kMaxSamples)return false;
            points+=o.point_count;a.objects.push_back(std::move(o));
        }
        for(uint32_t i=0;i<points;++i){ps2spline::Vec3 v{r.get<float>(),r.get<float>(),r.get<float>()};
            if(!r.ok||!finite3(v)||std::fabs(v[0])>100000.f||std::fabs(v[1])>100000.f||std::fabs(v[2])>100000.f)return false;
            a.points.push_back(v);}
        if(!r.ok||r.at!=n)return false;
        // Every route must pass the controller's own preparation and initial pose.
        for(const auto& o:a.objects){ps2spline::Controller c;if(!c.initialize(a.points.data()+o.first_point,o.point_count,o.config))return false;}
        out=std::move(a);return true;
    } catch(...) {out={};return false;}
}
bool decode_spline_objects_asset(const uint8_t* p,size_t n,std::string_view digest,SplineObjectsAsset& out) noexcept {
    out={};
    return std::string_view(kSplineObjectsArtifactSha).size()==64&&digest==kSplineObjectsArtifactSha&&decode_spline_objects_layout(p,n,out);
}
size_t spline_course_index(const SplineObjectsAsset& a,std::string_view id) noexcept {
    for(size_t i=0;i<a.courses.size();++i)if(course_id_matches(id,a.courses[i].id))return i;
    return SIZE_MAX;
}
const char* spline_course_guard(const std::array<uint8_t,32>& retail,bool loose,std::string_view sha) noexcept {
    if(!loose)return "stock_pc_course_no_loose_course_dx";
    if(sha.size()!=64)return "course_dx_unreadable";
    try{if(sha==hex(retail.data(),retail.size()))return "stock_pc_course_retail_dx";}catch(...){return "course_dx_unreadable";}
    return "ps2_course_package";
}

bool SplineCourseRuntime::start(const SplineObjectsAsset& a,size_t course,uint64_t race) noexcept {
    stop();
    if(course>=a.courses.size()||!race)return false;
    try{
        const auto& c=a.courses[course];
        controllers_.resize(c.count);
        for(uint32_t i=0;i<c.count;++i){const auto& o=a.objects[c.first+i];
            if(!controllers_[i].initialize(a.points.data()+o.first_point,o.point_count,o.config)){stop();return false;}}
    }catch(...){stop();return false;}
    asset_=&a;course_=course;race_=race;return true;
}
unsigned SplineCourseRuntime::advance(double seconds,bool paused,const ps2spline::Vec3* observer) noexcept {
    if(!ready()||paused)return 0;
    const unsigned n=clock_.advance(seconds);tick(n,observer);return n;
}
void SplineCourseRuntime::tick(unsigned n,const ps2spline::Vec3* observer) noexcept {
    if(!ready())return;
    for(unsigned i=0;i<n;++i){for(auto& c:controllers_)c.tick(observer);++ticks_;}
}
bool SplineCourseRuntime::build(std::vector<SplineBatch>& out) const noexcept {
    out.clear();if(!ready())return false;
    try{
        const auto& c=asset_->courses[course_];
        for(uint32_t i=0;i<c.count;++i){
            const auto& o=asset_->objects[c.first+i];const auto& m=asset_->models[o.model];
            const auto pose=controllers_[i].pose();
            for(const auto& d:m.draws){
                auto batch=std::find_if(out.begin(),out.end(),[&](const SplineBatch& b){return b.texture==d.texture;});
                if(batch==out.end()){out.push_back({d.texture,{}});batch=out.end()-1;}
                for(uint32_t v=d.first;v<d.first+d.count;++v){
                    auto vertex=asset_->vertices[v];
                    const auto w=ps2spline::transform(pose,{vertex.x,vertex.y,vertex.z});
                    if(!finite3(w)){out.clear();return false;}
                    vertex.x=w[0];vertex.y=w[1];vertex.z=w[2];batch->vertices.push_back(vertex);
                }
            }
        }
        return true;
    }catch(...){out.clear();return false;}
}

SplineObjectsPilot::SplineObjectsPilot(bool supported,const std::wstring& ini) noexcept {
    if(!supported){reason_="unsupported_build_stock";return;}
    if(config::read_int(L"SplineObjects",0,ini.c_str())!=1)return;
    requested_=true;
    diagnostics_=config::read_int(L"SplineObjectsDiagnostics",0,ini.c_str())==1;
    stock_courses_=config::read_int(L"SplineObjectsStockCourses",0,ini.c_str())==1;
    try{
        game_root_=std::filesystem::path(ini).parent_path().wstring();
        wchar_t dir[32768]{},path[32768]{};
        config::read_string(L"GrassAssetDirectory",L".",dir,32768,ini.c_str());
        const std::wstring fallback=std::wstring(dir)+L"\\PS2SplineObjects.ps2spl";
        const auto count=config::read_string(L"SplineObjectsAsset",fallback.c_str(),path,32768,ini.c_str());
        if(!count||count>=32767){reason_="invalid_asset_path";return;}
        std::filesystem::path input(path);if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
        std::ifstream file(input,std::ios::binary|std::ios::ate);
        if(!file){reason_="missing_spline_objects_asset";return;}
        const auto size=static_cast<std::streamoff>(file.tellg());
        if(size<=0||static_cast<uint64_t>(size)>kSplineObjectsMaximumAssetBytes){reason_="wrong_size_spline_objects_asset";return;}
        std::vector<uint8_t> bytes(static_cast<size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),size);
        verified_=file&&decode_spline_objects_asset(bytes.data(),bytes.size(),sha256_bytes(bytes.data(),bytes.size()),asset_);
        reason_=verified_?"verified_spline_objects_waiting_for_device":"spline_objects_asset_hash_or_layout_mismatch";
    }catch(...){reason_="spline_objects_asset_load_failed_stock";verified_=false;}
}
void SplineObjectsPilot::release_textures() noexcept {for(auto* t:textures_)if(t)t->Release();textures_.clear();}
bool SplineObjectsPilot::initialize(IDirect3DDevice8& device) noexcept {
    if(!identity_requested()||suspended_||blocked_)return false;
    release_textures();
    D3DCAPS8 caps{};HRESULT hr=device.GetDeviceCaps(&caps);
    if(FAILED(hr)||caps.MaxPrimitiveCount<1024){disable("unsupported_spline_device_caps");return false;}
    try{
        for(const auto& t:asset_.textures){
            if(caps.MaxTextureWidth<t.width||caps.MaxTextureHeight<t.height){release_textures();disable("unsupported_spline_texture_size");return false;}
            IDirect3DTexture8* texture=nullptr;
            hr=device.CreateTexture(t.width,t.height,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture);
            if(FAILED(hr)||!texture){if(texture)texture->Release();release_textures();disable("spline_texture_creation_failed");return false;}
            textures_.push_back(texture);
            D3DLOCKED_RECT lock{};hr=texture->LockRect(0,&lock,nullptr,0);
            if(SUCCEEDED(hr)){
                const bool valid=lock.pBits&&lock.Pitch>=INT(t.width*4);
                // DXT rows as stored: the PC game uploads its DXT files the same way (ps2_hud_map.hpp level-0 SHA).
                if(valid)for(uint32_t row=0;row<t.height;++row)std::memcpy(static_cast<uint8_t*>(lock.pBits)+size_t(row)*lock.Pitch,t.bgra.data()+size_t(row)*t.width,size_t(t.width)*4);
                const auto unlocked=texture->UnlockRect(0);if(!valid||FAILED(unlocked))hr=E_FAIL;
            }
            if(FAILED(hr)){release_textures();disable("spline_texture_upload_failed");return false;}
        }
    }catch(...){release_textures();disable("spline_texture_creation_failed");return false;}
    reason_="spline_objects_ready";return true;
}
bool SplineObjectsPilot::select_course(std::string_view id,uint64_t race) noexcept {
    if(!active()||!race){runtime_.stop();return false;}
    const size_t course=spline_course_index(asset_,id);
    if(course==SIZE_MAX){runtime_.stop();guard_reason_="not_a_spline_course";return false;}
    if(runtime_.ready()&&runtime_.course()==course&&runtime_.race()==race)return true;
    // Course guard once per race generation (one file hash at race start).
    if(guard_race_!=race||guard_course_!=course){
        guard_race_=race;guard_course_=course;
        try{
            const auto file=std::filesystem::path(game_root_)/std::filesystem::path(asset_.courses[course].dx_path);
            std::error_code error;const bool loose=std::filesystem::is_regular_file(file,error);
            guard_reason_=spline_course_guard(asset_.courses[course].retail_sha,loose,loose?sha256_file(file.wstring()):std::string());
        }catch(...){guard_reason_="course_dx_unreadable";}
        if(stock_courses_&&std::strncmp(guard_reason_,"stock_pc_course",15)==0)guard_reason_="stock_pc_course_allowed_by_ini";
        course_log_pending_=true;
    }
    if(std::strcmp(guard_reason_,"ps2_course_package")&&std::strcmp(guard_reason_,"stock_pc_course_allowed_by_ini")){runtime_.stop();return false;}
    if(!runtime_.start(asset_,course,race)){guard_reason_="spline_route_contract_failed";runtime_.stop();return false;}
    last_qpc_=0;last_pose_log_=0;advanced_frame_=UINT64_MAX;
    return true;
}
unsigned SplineObjectsPilot::advance_frame(uint64_t frame,bool paused,const ps2spline::Vec3* observer) noexcept {
    if(!runtime_.ready()||advanced_frame_==frame)return 0;
    advanced_frame_=frame;
    LARGE_INTEGER now{},frequency{};QueryPerformanceCounter(&now);QueryPerformanceFrequency(&frequency);
    const uint64_t previous=last_qpc_;last_qpc_=static_cast<uint64_t>(now.QuadPart);
    // The first frame of a race only starts the clock (the PS2 owner publishes its initial pose at hatch).
    if(!previous||frequency.QuadPart<=0)return 0;
    return runtime_.advance(double(static_cast<uint64_t>(now.QuadPart)-previous)/double(frequency.QuadPart),paused,observer);
}
bool SplineObjectsPilot::claim_pose_log() noexcept {
    if(!diagnostics_||!runtime_.ready())return false;
    // One pose record per 150 invocations (5 s at 30 Hz) and the first one.
    const uint64_t slot=runtime_.ticks()/150+1;if(slot==last_pose_log_)return false;last_pose_log_=slot;return true;
}
bool SplineObjectsPilot::consume_boundary(uint64_t frame,uint64_t race,uint64_t reset) noexcept {
    if(consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset)return false;
    consumed_frame_=frame;consumed_race_=race;consumed_reset_=reset;return true;
}
bool SplineObjectsPilot::claim_log(bool draw) noexcept {auto& done=draw?logged_draw_:logged_rejection_;if(!diagnostics_||done)return false;done=true;return true;}
void SplineObjectsPilot::before_reset() noexcept {
    proof.clear();if(transaction.has_pending())blocked_=true;transaction.release();
    release_textures();consumed_frame_=UINT64_MAX;
}
void SplineObjectsPilot::after_reset(IDirect3DDevice8& device,bool called,bool success) noexcept {
    if(!called)return;if(!success){suspended_=true;return;}
    blocked_=suspended_=false;initialize(device);
}
void SplineObjectsPilot::shutdown() noexcept {proof.clear();transaction.release();release_textures();runtime_.stop();disabled_=true;}
} // namespace gfx2::ps2port
