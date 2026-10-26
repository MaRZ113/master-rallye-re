#include "ps2_birds_pilot.hpp"
#include "ps2_config.hpp"
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>

namespace gfx2::ps2port {
namespace {
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
bool finite(float v) noexcept {return std::isfinite(v);}
}

bool decode_birds_layout(const uint8_t* p,size_t n,BirdsAsset& out) noexcept {
    out={};
    if(!p||n<24||n>1024*1024||std::memcmp(p,"PS2BRD01",8))return false;
    try{
        Reader r{p,n,8};
        const uint32_t version=r.get<uint32_t>(),frames=r.get<uint32_t>(),courses=r.get<uint32_t>(),points=r.get<uint32_t>();
        if(!r.ok||version!=1||frames!=4||!courses||courses>64||points>64*ps2birds::kMaxPoints)return false;
        BirdsAsset a;
        for(auto& cell:a.cells){const auto* px=r.bytes(kBirdCell*kBirdCell*4);if(!px)return false;
            cell.resize(kBirdCell*kBirdCell);std::memcpy(cell.data(),px,cell.size()*4);
            for(DWORD c:cell)if((c>>24)!=0&&(c>>24)!=255)return false;}               // binary PS2 alpha
        for(uint32_t f=0;f<4;++f){
            auto& fr=a.frames[f];
            for(uint32_t t=0;t<2;++t){
                const uint32_t cell=r.get<uint32_t>();auto& tr=fr.tri[t];
                for(auto& v:tr.xy)v=r.get<float>();for(auto& v:tr.uv)v=r.get<float>();
                if(!r.ok||cell>3||(t&&cell!=fr.cell))return false;
                fr.cell=cell;
                for(float v:tr.xy)if(!finite(v)||std::fabs(v)>64.f)return false;
                for(float v:tr.uv)if(!finite(v)||v<0.f||v>1.f)return false;
            }
            fr.u0=fr.v0=1.f;for(const auto& t:fr.tri)for(int i=0;i<3;++i){if(t.uv[i*2]<fr.u0)fr.u0=t.uv[i*2];if(t.uv[i*2+1]<fr.v0)fr.v0=t.uv[i*2+1];}
            if(fr.v0!=.75f||fr.u0!=static_cast<float>(fr.cell)*.25f)return false;
        }
        uint32_t first=0;
        for(uint32_t i=0;i<courses;++i){
            BirdCourseDef c;c.id=r.text(48);c.dx_path=r.text(64);const auto* sha=r.bytes(32);
            c.min_fly=r.get<float>();c.max_fly=r.get<float>();c.min_mil=r.get<float>();c.max_mil=r.get<float>();
            c.rnd_fly=r.get<int32_t>();c.rnd_mil=r.get<int32_t>();
            const uint8_t fl=r.get<uint8_t>(),ml=r.get<uint8_t>();r.get<uint16_t>();
            c.first=r.get<uint32_t>();c.count=r.get<uint32_t>();
            if(!r.ok||!sha||fl>1||ml>1||c.first!=first||c.count>ps2birds::kMaxPoints||c.count>points-first||(!fl&&c.count))return false;
            if(!finite(c.min_fly)||!finite(c.max_fly)||!finite(c.min_mil)||!finite(c.max_mil)||c.rnd_fly<0||c.rnd_fly>10||c.rnd_mil<0||c.rnd_mil>10)return false;
            std::memcpy(c.retail_sha.data(),sha,32);c.flight_present=fl;c.mill_present=ml;first+=c.count;
            for(const auto& o:a.courses)if(course_id_matches(o.id,c.id))return false;
            a.courses.push_back(std::move(c));
        }
        if(first!=points)return false;
        for(uint32_t i=0;i<points;++i){ps2birds::Vec3 v{r.get<float>(),r.get<float>(),r.get<float>()};
            if(!r.ok||!finite(v[0])||!finite(v[1])||!finite(v[2])||std::fabs(v[0])>100000.f||std::fabs(v[1])>100000.f||std::fabs(v[2])>100000.f)return false;
            a.points.push_back(v);}
        if(!r.ok||r.at!=n)return false;
        out=std::move(a);return true;
    }catch(...){out={};return false;}
}
bool decode_birds_asset(const uint8_t* p,size_t n,std::string_view digest,BirdsAsset& out) noexcept {
    out={};return digest==kPS2BirdsArtifactSha&&decode_birds_layout(p,n,out);
}
size_t birds_course_index(const BirdsAsset& a,std::string_view id) noexcept {
    for(size_t i=0;i<a.courses.size();++i)if(course_id_matches(id,a.courses[i].id))return i;
    return SIZE_MAX;
}
ps2birds::CourseConfig birds_course_config(const BirdsAsset& a,size_t i) {
    ps2birds::CourseConfig c;const auto& d=a.courses[i];
    c.flight.assign(a.points.begin()+d.first,a.points.begin()+d.first+d.count);
    c.flight_present=d.flight_present;c.mill_present=d.mill_present;c.min_fly=d.min_fly;c.max_fly=d.max_fly;c.rnd_fly=d.rnd_fly;
    return c;
}
bool birds_camera(const D3DMATRIX& v,ps2birds::Vec3& pos,ps2birds::Vec3& look,ps2birds::Vec3& up) noexcept {
    for(const auto& row:v.m)for(float x:row)if(!std::isfinite(x))return false;
    if(std::fabs(v._14)>.0002f||std::fabs(v._24)>.0002f||std::fabs(v._34)>.0002f||std::fabs(v._44-1.f)>.0002f)return false;
    for(int i=0;i<3;++i)pos[i]=-(v._41*v.m[i][0]+v._42*v.m[i][1]+v._43*v.m[i][2]);
    look={v._13,v._23,v._33};up={v._12,v._22,v._32};
    const float l2=look[0]*look[0]+look[1]*look[1]+look[2]*look[2],u2=up[0]*up[0]+up[1]*up[1]+up[2]*up[2];
    return std::fabs(l2-1.f)<.001f&&std::fabs(u2-1.f)<.001f;
}
bool birds_build(const BirdsAsset& a,const std::vector<ps2birds::BirdView>& birds,const ps2birds::Vec3& look,const ps2birds::Vec3& up,
                 std::vector<BirdBatch>& out) noexcept {
    out.clear();
    try{
        const auto side=ps2birds::camera_side(look,up);
        const auto bb=ps2birds::billboard(side,look);
        for(const auto& b:birds){
            if(b.key<0||b.key>2)return false;
            const auto& fr=a.frames[static_cast<size_t>(b.key)];
            BirdBatch* batch=nullptr;for(auto& x:out)if(x.cell==fr.cell)batch=&x;
            if(!batch){out.push_back({fr.cell,{}});batch=&out.back();}
            for(const auto& t:fr.tri)for(int i=0;i<3;++i){
                const auto w=ps2birds::world_vertex(b.position,bb,t.xy[i*2],t.xy[i*2+1]);
                if(!std::isfinite(w[0])||!std::isfinite(w[1])||!std::isfinite(w[2])){out.clear();return false;}
                // Cell texture: u' = (u-u0)*4, v' = (v-0.75)*4 (CLAMP = PS2 REGION_CLAMP of the atlas rectangle).
                batch->vertices.push_back({w[0],w[1],w[2],0xffffffffu,(t.uv[i*2]-fr.u0)*4.f,(t.uv[i*2+1]-fr.v0)*4.f});
            }
        }
        return true;
    }catch(...){out.clear();return false;}
}

PS2BirdsPilot::PS2BirdsPilot(bool supported,const std::wstring& ini) noexcept {
    if(!supported){reason_="unsupported_build_stock";return;}
    if(config::read_int(L"PS2Birds",0,ini.c_str())!=1)return;
    requested_=true;
    diagnostics_=config::read_int(L"PS2BirdsDiagnostics",0,ini.c_str())==1;
    stock_courses_=config::read_int(L"PS2BirdsStockCourses",0,ini.c_str())==1;
    ignore_gate_=config::read_int(L"PS2BirdsIgnoreListGate",0,ini.c_str())==1;
    try{
        game_root_=std::filesystem::path(ini).parent_path().wstring();
        wchar_t dir[32768]{},path[32768]{};
        config::read_string(L"GrassAssetDirectory",L".",dir,32768,ini.c_str());
        const std::wstring fallback=std::wstring(dir)+L"\\PS2Birds.ps2bird";
        const auto count=config::read_string(L"PS2BirdsAsset",fallback.c_str(),path,32768,ini.c_str());
        if(!count||count>=32767){reason_="invalid_asset_path";return;}
        std::filesystem::path input(path);if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
        std::ifstream file(input,std::ios::binary|std::ios::ate);
        if(!file){reason_="missing_birds_asset";return;}
        const auto size=static_cast<std::streamoff>(file.tellg());
        if(size<=0||size>1024*1024){reason_="wrong_size_birds_asset";return;}
        std::vector<uint8_t> bytes(static_cast<size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),size);
        verified_=file&&decode_birds_asset(bytes.data(),bytes.size(),sha256_bytes(bytes.data(),bytes.size()),asset_);
        reason_=verified_?"verified_birds_waiting_for_device":"birds_asset_hash_or_layout_mismatch";
    }catch(...){reason_="birds_asset_load_failed_stock";verified_=false;}
}
void PS2BirdsPilot::release_textures() noexcept {for(auto*& t:textures_){if(t)t->Release();t=nullptr;}}
bool PS2BirdsPilot::initialize(IDirect3DDevice8& device) noexcept {
    if(!identity_requested()||suspended_||blocked_)return false;
    release_textures();
    D3DCAPS8 caps{};HRESULT hr=device.GetDeviceCaps(&caps);
    if(FAILED(hr)||caps.MaxPrimitiveCount<256){disable("unsupported_birds_device_caps");return false;}
    for(size_t c=0;c<textures_.size();++c){
        hr=device.CreateTexture(kBirdCell,kBirdCell,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&textures_[c]);
        if(FAILED(hr)||!textures_[c]){release_textures();disable("birds_texture_creation_failed");return false;}
        D3DLOCKED_RECT lock{};hr=textures_[c]->LockRect(0,&lock,nullptr,0);
        if(SUCCEEDED(hr)){
            const bool valid=lock.pBits&&lock.Pitch>=INT(kBirdCell*4);
            if(valid)for(size_t row=0;row<kBirdCell;++row)std::memcpy(static_cast<uint8_t*>(lock.pBits)+row*lock.Pitch,asset_.cells[c].data()+row*kBirdCell,kBirdCell*4);
            const auto unlocked=textures_[c]->UnlockRect(0);if(!valid||FAILED(unlocked))hr=E_FAIL;
        }
        if(FAILED(hr)){release_textures();disable("birds_texture_upload_failed");return false;}
    }
    reason_="birds_ready";return true;
}
bool PS2BirdsPilot::select_course(std::string_view id,uint64_t race) noexcept {
    if(!active()||!race){course_=SIZE_MAX;race_=0;return false;}
    const size_t course=birds_course_index(asset_,id);
    if(course==SIZE_MAX){course_=SIZE_MAX;race_=0;guard_reason_="not_a_ps2_course";return false;}
    if(course_==course&&race_==race)return true;
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
    if(std::strcmp(guard_reason_,"ps2_course_package")&&std::strcmp(guard_reason_,"stock_pc_course_allowed_by_ini")){course_=SIZE_MAX;race_=0;return false;}
    if(manager_started_)session_rng_=manager_.rng().state();
    try{manager_started_=true;if(!manager_.start(birds_course_config(asset_,course),ignore_gate_,session_rng_)){guard_reason_="birds_course_contract_failed";course_=SIZE_MAX;race_=0;return false;}}
    catch(...){guard_reason_="birds_course_contract_failed";course_=SIZE_MAX;race_=0;return false;}
    course_=course;race_=race;clock_.reset();last_qpc_=0;last_log_slot_=0;advanced_frame_=UINT64_MAX;
    return true;
}
unsigned PS2BirdsPilot::advance_frame(uint64_t frame,bool paused,const ps2birds::Vec3& camera) noexcept {
    if(course_==SIZE_MAX||advanced_frame_==frame)return 0;
    advanced_frame_=frame;
    LARGE_INTEGER now{},frequency{};QueryPerformanceCounter(&now);QueryPerformanceFrequency(&frequency);
    const uint64_t previous=last_qpc_;last_qpc_=static_cast<uint64_t>(now.QuadPart);
    if(!previous||frequency.QuadPart<=0||paused)return 0;   // the first race frame only starts the clock
    const unsigned n=clock_.advance(double(static_cast<uint64_t>(now.QuadPart)-previous)/double(frequency.QuadPart));
    for(unsigned i=0;i<n;++i)manager_.tick(camera);
    return n;
}
bool PS2BirdsPilot::claim_state_log() noexcept {
    if(!diagnostics_||course_==SIZE_MAX)return false;
    const uint64_t slot=manager_.ticks()/150+1;if(slot==last_log_slot_)return false;last_log_slot_=slot;return true;  // every 5 s
}
bool PS2BirdsPilot::consume_boundary(uint64_t frame,uint64_t race,uint64_t reset) noexcept {
    if(consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset)return false;
    consumed_frame_=frame;consumed_race_=race;consumed_reset_=reset;return true;
}
bool PS2BirdsPilot::claim_log(bool draw) noexcept {auto& done=draw?logged_draw_:logged_rejection_;if(!diagnostics_||done)return false;done=true;return true;}
void PS2BirdsPilot::before_reset() noexcept {proof.clear();if(transaction.has_pending())blocked_=true;transaction.release();release_textures();consumed_frame_=UINT64_MAX;}
void PS2BirdsPilot::after_reset(IDirect3DDevice8& device,bool called,bool success) noexcept {
    if(!called)return;if(!success){suspended_=true;return;}
    blocked_=suspended_=false;initialize(device);
}
void PS2BirdsPilot::shutdown() noexcept {proof.clear();transaction.release();release_textures();course_=SIZE_MAX;race_=0;disabled_=true;}
} // namespace gfx2::ps2port
