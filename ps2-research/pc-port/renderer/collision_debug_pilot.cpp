#include "collision_debug_pilot.hpp"
#include "ps2_config.hpp"
#include "provenance.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <filesystem>
#include <fstream>

namespace gfx2::ps2port {
namespace {
bool read_file(const std::filesystem::path& path,std::vector<uint8_t>& out,uint64_t limit) {
    out.clear();std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file)return false;
    const auto size=static_cast<std::streamoff>(file.tellg());
    if(size<=0||static_cast<uint64_t>(size)>limit)return false;
    out.resize(static_cast<size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(out.data()),size);
    return static_cast<bool>(file);
}
std::string hex(const std::array<uint8_t,32>& v) {
    static constexpr char d[]="0123456789abcdef";std::string s;for(uint8_t b:v){s+=d[b>>4];s+=d[b&15];}return s;
}
std::string narrow(const wchar_t* s) {std::string out;for(;*s;++s)out+=*s<128?static_cast<char>(*s):'?';return out;}
} // namespace

UINT collision_debug_key(const wchar_t* name) noexcept {
    if(!name||!*name)return 0;
    wchar_t up[32]{};size_t n=0;for(;name[n]&&n<31;++n){wchar_t c=name[n];if(c>=L'a'&&c<=L'z')c=static_cast<wchar_t>(c-L'a'+L'A');up[n]=c;}
    if(name[n])return 0;
    UINT key=0;
    if(up[0]==L'F'&&up[1]>=L'1'&&up[1]<=L'9'){const long f=std::wcstol(up+1,nullptr,10);if(f>=1&&f<=24)key=static_cast<UINT>(VK_F1+f-1);}
    else if(!std::wcscmp(up,L"INSERT"))key=VK_INSERT;else if(!std::wcscmp(up,L"HOME"))key=VK_HOME;
    else if(!std::wcscmp(up,L"END"))key=VK_END;else if(!std::wcscmp(up,L"PAGEUP"))key=VK_PRIOR;
    else if(!std::wcscmp(up,L"PAGEDOWN"))key=VK_NEXT;else if(!std::wcscmp(up,L"PAUSE"))key=VK_PAUSE;
    else if(!std::wcscmp(up,L"SCROLLLOCK"))key=VK_SCROLL;
    else if(up[0]>=L'0'&&up[0]<=L'9'&&up[1]){wchar_t* end=nullptr;const unsigned long v=std::wcstoul(up,&end,0);if(end&&!*end&&v<256)key=static_cast<UINT>(v);}
    if(key==VK_F10)return 0; // reserved: baseline F10 trace snapshot
    return key;
}

CollisionDebugPilot::CollisionDebugPilot(bool supported,const std::wstring& ini) noexcept {
    if(!supported){reason_="unsupported_build_stock";return;}
    if(config::read_int(L"CollisionDebug",0,ini.c_str())!=1)return;
    requested_=true;reason_="waiting_for_device";
    try{
        game_root_=std::filesystem::path(ini).parent_path().wstring();
        legend_=config::read_int(L"CollisionDebugLegend",1,ini.c_str())==1;
        wchar_t text[64]{};
        config::read_string(L"CollisionDebugKey",L"F11",text,64,ini.c_str());
        key_=collision_debug_key(text);key_name_=narrow(text);
        if(!key_){key_=VK_F11;key_name_="F11";}
        for(auto& c:key_name_)if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');
        // Race markers (RaceLine, limits, start/finish areas, cameras) on their own key; vehicle hulls with the overlay.
        config::read_string(L"CollisionDebugMarkersKey",L"F12",text,64,ini.c_str());
        markers_key_=collision_debug_key(text);markers_key_name_=narrow(text);
        if(!markers_key_||markers_key_==key_){markers_key_=markers_key_==key_?0:VK_F12;markers_key_name_=markers_key_?"F12":"NONE";}
        for(auto& c:markers_key_name_)if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');
        cars_=config::read_int(L"CollisionDebugCars",1,ini.c_str())==1;
        config::read_string(L"CollisionDebugCarsKey",L"F9",text,64,ini.c_str());
        cars_key_=collision_debug_key(text);cars_key_name_=narrow(text);
        if(!cars_key_||cars_key_==key_||cars_key_==markers_key_){cars_key_=0;cars_key_name_="NONE";}
        for(auto& c:cars_key_name_)if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');
        config::read_string(L"CollisionDebugMode",L"OFF",text,64,ini.c_str());
        colldebug::Mode mode{};if(colldebug::parse_mode(narrow(text).c_str(),mode))mode_=mode;
        config::read_string(L"CollisionDebugRange",L"500",text,64,ini.c_str());
        const double range=std::wcstod(text,nullptr);if(range>=10&&range<=20000)settings_.range=static_cast<float>(range);
        config::read_string(L"CollisionDebugDepthPull",L"0.003",text,64,ini.c_str());
        const double pull=std::wcstod(text,nullptr);if(pull>=0&&pull<=0.1)settings_.depth_pull=static_cast<float>(pull);
        config::read_string(L"CollisionDebugLegendPosition",L"TOPCENTER",text,64,ini.c_str());
        colldebug::LegendAnchor anchor{};if(colldebug::parse_anchor(narrow(text).c_str(),anchor))anchor_=anchor;
        legend.anchor=anchor_;
        {
            wchar_t archive[32768]{};
            config::read_string(L"CollisionDebugArchive",L"Data.sma",archive,32768,ini.c_str());
            std::filesystem::path a(archive);if(a.is_relative())a=std::filesystem::path(ini).parent_path()/a;
            archive_path_=a.wstring();
        }
        wchar_t dir[32768]{},path[32768]{};
        config::read_string(L"GrassAssetDirectory",L".",dir,32768,ini.c_str());
        const std::wstring fallback=std::wstring(dir)+L"\\CourseCollision.mrcoll";
        const auto count=config::read_string(L"CollisionDebugAsset",fallback.c_str(),path,32768,ini.c_str());
        std::filesystem::path input(count&&count<32767?path:fallback.c_str());
        if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
        if(!read_file(input,asset_bytes_,256ull*1024*1024))asset_reason_="not_present_data_sma_used";
        else{
            asset_sha_=sha256_bytes(asset_bytes_.data(),asset_bytes_.size());
            if(asset_sha_!=kCollisionDebugArtifactSha)asset_reason_="asset_sha_mismatch_ignored";
            else if(!colldebug::decode_asset_index(asset_bytes_.data(),asset_bytes_.size(),asset_index_))asset_reason_="asset_layout_rejected_ignored";
            else{asset_ok_=true;asset_reason_="verified";}
            if(!asset_ok_){asset_bytes_.clear();asset_bytes_.shrink_to_fit();asset_index_.clear();}
        }
    }catch(...){asset_ok_=false;asset_bytes_.clear();asset_index_.clear();asset_reason_="asset_load_failed_ignored";}
}

void CollisionDebugPilot::release_texture() noexcept {if(white_)white_->Release();white_=nullptr;}

bool CollisionDebugPilot::initialize(IDirect3DDevice8& device) noexcept {
    if(!requested_||disabled_||suspended_||blocked_)return false;
    release_texture();
    HRESULT hr=device.CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&white_);
    if(FAILED(hr)||!white_){release_texture();disable("collision_texture_creation_failed");return false;}
    D3DLOCKED_RECT lock{};hr=white_->LockRect(0,&lock,nullptr,0);
    if(SUCCEEDED(hr)){if(lock.pBits)*static_cast<DWORD*>(lock.pBits)=0xffffffffu;else hr=E_FAIL;if(FAILED(white_->UnlockRect(0)))hr=E_FAIL;}
    if(FAILED(hr)){release_texture();disable("collision_texture_upload_failed");return false;}
    reason_="ready";return true;
}

bool CollisionDebugPilot::poll_hotkey() noexcept {
    const bool down=(GetAsyncKeyState(static_cast<int>(key_))&0x8000)!=0;
    const bool pressed=down&&!key_down_;key_down_=down;
    const bool markers_down=markers_key_&&(GetAsyncKeyState(static_cast<int>(markers_key_))&0x8000)!=0;
    const bool markers_pressed=markers_down&&!markers_key_down_;markers_key_down_=markers_down;
    const bool cars_down=cars_&&cars_key_&&(GetAsyncKeyState(static_cast<int>(cars_key_))&0x8000)!=0;
    const bool cars_pressed=cars_down&&!cars_key_down_;cars_key_down_=cars_down;
    if(!pressed&&!markers_pressed&&!cars_pressed)return false;
    DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);
    if(pid!=GetCurrentProcessId())return false;
    const bool back=(GetAsyncKeyState(VK_SHIFT)&0x8000)!=0;
    if(pressed)mode_=colldebug::next_mode(mode_,back);
    // Markers: OFF -> ON (depth tested) -> X-RAY -> OFF.
    if(markers_pressed)markers_mode_=static_cast<uint8_t>(back?(markers_mode_+2)%3:(markers_mode_+1)%3);
    // Vehicle collision: OFF -> ON (through the body) -> depth tested -> OFF.
    if(cars_pressed)cars_mode_=static_cast<uint8_t>(back?(cars_mode_+2)%3:(cars_mode_+1)%3);
    mode_log_pending_=true;logged_draw_=false;
    return true;
}

// Game file roots, in the order the game itself resolves them: the process working directory first (the game opens
// relative "DataGx/..." paths; launchers such as the vehicles SDK runtime start MRallye.exe with their own resource
// root as working directory), then the proxy folder. In each root a loose file wins over that root's Data.sma.
// Opened once on the render thread before any worker starts; read-only afterwards.
void CollisionDebugPilot::ensure_roots() noexcept {
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
            std::filesystem::path archive(archive_path_);
            if(archive.is_relative()||archive.parent_path()==std::filesystem::path(game_root_))archive=canon/archive.filename();
            r.archive=std::make_unique<sma::Archive>();r.archive->open(archive.wstring());
            roots_.push_back(std::move(r));
        }
    }catch(...){}
}
bool CollisionDebugPilot::archive_open() const noexcept {for(const auto& r:roots_)if(r.archive&&r.archive->is_open())return true;return false;}
// Reads a game file: loose in root 0, Data.sma of root 0, loose in root 1, ... `where` names the source.
bool CollisionDebugPilot::read_game_file(const std::string& rel,std::vector<uint8_t>& out,std::string& where,uint64_t limit) const {
    out.clear();
    for(size_t i=0;i<roots_.size();++i){
        const auto& r=roots_[i];std::error_code error;const auto loose=r.folder/std::filesystem::path(rel);
        if(std::filesystem::is_regular_file(loose,error)&&read_file(loose,out,limit)){where=i==0&&roots_.size()>1?"LOOSE CWD":"LOOSE";return true;}
        if(r.archive&&r.archive->is_open()&&r.archive->read(rel,out,limit)){where=i==0&&roots_.size()>1?"SMA CWD":"DATA.SMA";return true;}
    }
    out.clear();return false;
}

// Wheel collision cylinder of vehicles/<folder>/wheel (tag102 of wheel.dx), cached.
const colldebug::WheelCylinder* CollisionDebugPilot::wheel(const std::string& folder) noexcept {
    try{
        ensure_roots();
        std::string key=folder;for(auto& c:key)c=static_cast<char>(c>='A'&&c<='Z'?c-'A'+'a':c);
        const auto it=wheels_.find(key);if(it!=wheels_.end())return it->second.get();
        std::unique_ptr<colldebug::WheelCylinder> w;std::vector<uint8_t> bytes;std::string where;
        if(read_game_file("DataGx/Vehicles/"+folder+"/wheel.dx",bytes,where,64ull*1024*1024)){
            auto c=std::make_unique<colldebug::WheelCylinder>();if(colldebug::parse_wheel_cylinder(bytes.data(),bytes.size(),*c))w=std::move(c);}
        auto* raw=w.get();wheels_.emplace(key,std::move(w));hull_log_pending_=true;
        return raw;
    }catch(...){return nullptr;}
}

// Vehicle collision hull of vehicles/<folder>/car (car.dx from the game roots), cached.
const colldebug::Hull* CollisionDebugPilot::hull(const std::string& folder) noexcept {
    try{
        ensure_roots();
        std::string key=folder;for(auto& c:key)c=static_cast<char>(c>='A'&&c<='Z'?c-'A'+'a':c);
        const auto it=hulls_.find(key);if(it!=hulls_.end())return it->second.get();
        std::unique_ptr<colldebug::Hull> h;std::vector<uint8_t> bytes;std::string where;
        if(read_game_file("DataGx/Vehicles/"+folder+"/car.dx",bytes,where,64ull*1024*1024)){
            auto parsed=std::make_unique<colldebug::Hull>();if(colldebug::parse_vehicle_hull(bytes.data(),bytes.size(),*parsed))h=std::move(parsed);}
        else missing_cars_+=(missing_cars_.empty()?"":",")+folder;
        auto* raw=h.get();hulls_.emplace(key,std::move(h));hull_log_pending_=true;
        return raw;
    }catch(...){return nullptr;}
}

// One course DX's bytes -> surface + BSP objects.
const char* CollisionDebugPilot::parse_landscape(const std::vector<uint8_t>& bytes,colldebug::Mesh& out,CollisionLandscape& info,const char* ok) {
    colldebug::BspStats stats;bool objects=false;
    const auto result=colldebug::parse_course_dx_full(bytes.data(),bytes.size(),out,stats,objects);
    if(result!=colldebug::ParseResult::Ok){out.clear();
        return result==colldebug::ParseResult::Ambiguous?"course_dx_tag1400_ambiguous":"course_dx_has_no_tag1400";}
    info.bsp=objects;info.object_faces=stats.object_faces;info.solid_cells=stats.solid_cells;info.object_codes=stats.object_codes;
    return ok;
}

const char* CollisionDebugPilot::load_landscape(const std::string& dx_path,colldebug::Mesh& out,CollisionLandscape& info) {
    // 1. The game roots (loose file, then Data.sma; working directory first).
    std::vector<uint8_t> bytes;std::string where;
    if(read_game_file(dx_path,bytes,where,512ull*1024*1024)){
        info.sha=sha256_bytes(bytes.data(),bytes.size());
        info.source=where.rfind("LOOSE",0)==0?"LOOSE DX":where;
        return parse_landscape(bytes,out,info,where.rfind("LOOSE",0)==0?"loose_course_dx_parsed":"data_sma_course_dx_parsed");
    }
    // 2. Optional pinned asset: surface only (no BSP objects).
    const colldebug::AssetEntry* entry=nullptr;
    for(const auto& e:asset_index_)if(colldebug::same_path(e.dx_path,dx_path)){entry=&e;break;}
    if(!entry)return archive_open()?"course_dx_not_in_any_game_root":"course_dx_not_loose_and_no_data_sma";
    if(!colldebug::decode_asset_mesh(asset_bytes_.data(),asset_bytes_.size(),*entry,out)){out.clear();return "asset_course_rejected";}
    info.sha=hex(entry->dx_sha);info.source="ASSET";return "retail_asset_surface_only";
}

// Worker thread: resolves the race landscapes and builds the merged mesh (tag1400 + BSP objects). Reads only the
// archive indexes, the asset bytes and files; writes only `r`.
void CollisionDebugPilot::load_course(const std::string& id,CourseLoad& r) noexcept {
    try{
        LARGE_INTEGER t0{},t1{},freq{};QueryPerformanceCounter(&t0);
        // 1. Landscapes of the race (race XML from the game roots, else the asset table: retail, one landscape).
        //    Joined courses place several landscapes with their en3d Matrix.
        std::vector<colldebug::LandscapeRef> refs;std::vector<uint8_t> bytes;std::string where;
        if(read_game_file("DataScene/"+id+".xml",bytes,where,64ull*1024*1024)){
            r.race_xml=where;
            const std::string_view text(reinterpret_cast<const char*>(bytes.data()),bytes.size());
            refs=colldebug::landscape_refs(text);r.markers=colldebug::marker_lists(text);
            if(refs.empty()){r.reason="race_xml_has_no_landscape";return;}
        }else{
            for(const auto& e:asset_index_)if(colldebug::same_path(e.race_id,id)){colldebug::LandscapeRef l;l.dx_path=e.dx_path;refs.push_back(l);break;}
            r.race_xml=refs.empty()?"none":"asset";
            if(refs.empty()){r.reason=archive_open()?"race_xml_not_in_any_game_root":"race_xml_not_loose_and_no_data_sma";return;}
        }
        // 2. Every landscape: loose DX, else Data.sma, else the asset; placed with its matrix and merged. A landscape that
        //    fails is reported and the others are still drawn.
        size_t loaded=0,loose=0,objects=0;
        for(const auto& ref:refs){
            CollisionLandscape info;info.dx_path=ref.dx_path;info.identity=ref.identity;
            colldebug::Mesh part;info.status=load_landscape(ref.dx_path,part,info);
            if(part.triangles()){
                if(!ref.identity)colldebug::transform_mesh(part,ref.matrix);
                info.triangles=part.triangles();
                if(!colldebug::merge_mesh(r.mesh,part)){info.status="material_table_full";info.triangles=0;}
                else{++loaded;loose+=info.source=="LOOSE DX";objects+=info.bsp;}
            }
            r.landscapes.push_back(std::move(info));
        }
        QueryPerformanceCounter(&t1);QueryPerformanceFrequency(&freq);
        r.ms=freq.QuadPart?double(t1.QuadPart-t0.QuadPart)*1000.0/double(freq.QuadPart):0.0;
        if(!r.mesh.triangles()){r.reason=r.landscapes.size()==1?r.landscapes[0].status:"no_landscape_loaded";return;}
        r.source=loose==loaded?"LOOSE DX":loose?"MIXED":r.landscapes[0].source;
        if(r.landscapes.size()>1)r.source+=" "+std::to_string(loaded)+"/"+std::to_string(r.landscapes.size())+" PARTS";
        if(objects<loaded)r.source+=" NO BSP";
        r.reason=loaded==r.landscapes.size()?"loaded":"loaded_partially";r.ok=true;
    }catch(...){r=CourseLoad{};r.reason="course_load_failed";}
}

void CollisionDebugPilot::apply_load() noexcept {
    if(worker_.joinable())worker_.join();
    loading_=false;job_done_.store(false,std::memory_order_relaxed);
    mesh_=std::move(job_.mesh);landscapes_=std::move(job_.landscapes);markers_=std::move(job_.markers);source_=job_.source;race_xml_=job_.race_xml;
    course_reason_=job_.reason;load_ms_=job_.ms;course_ok_=job_.ok;course_log_pending_=true;logged_draw_=false;job_=CourseLoad{};
}

bool CollisionDebugPilot::select_course(std::string_view id,uint64_t race) noexcept {
    if(!race||id.empty())return false;
    if(course_race_==race&&course_id_==id){
        if(loading_&&job_done_.load(std::memory_order_acquire))apply_load();
        return course_ok_&&!loading_;
    }
    // New race or course: the previous load (if any) finishes first, then this one starts in the background.
    if(loading_){if(worker_.joinable())worker_.join();loading_=false;job_done_.store(false);job_=CourseLoad{};}
    course_race_=race;course_ok_=false;logged_draw_=false;
    try{
        course_id_=std::string(id);mesh_.clear();landscapes_.clear();markers_.clear();source_="none";race_xml_="none";course_reason_="loading";
        ensure_roots();
        loading_=true;job_done_.store(false);
        try{worker_=std::thread([this,key=course_id_]{load_course(key,job_);job_done_.store(true,std::memory_order_release);});}
        catch(...){load_course(course_id_,job_);job_done_.store(true);}   // no thread: load here
    }catch(...){loading_=false;course_reason_="course_load_failed";course_log_pending_=true;}
    return false;
}

HRESULT CollisionDebugPilot::draw_legend(IDirect3DDevice8& device,bool scene_active,bool recording) noexcept {
    legend_ready_=false;
    try{
        std::vector<std::vector<HudVertex>> strips;strips.reserve(legend.quads.size()/6);
        for(size_t i=0;i+5<legend.quads.size();i+=6){
            const auto& a=legend.quads[i];const auto& b=legend.quads[i+1];const auto& c=legend.quads[i+2];const auto& d=legend.quads[i+4];
            strips.push_back({{a.x,a.y,0.f,1.f,a.color,0,0},{b.x,b.y,0.f,1.f,b.color,0,0},{c.x,c.y,0.f,1.f,c.color,0,0},{d.x,d.y,0.f,1.f,d.color,0,0}});
        }
        const HRESULT hr=legend_layer.draw_strips(device,strips,legend_width_,legend_height_,scene_active,recording);
        if(legend_layer.pending())blocked_=true;
        return hr;
    }catch(...){return E_OUTOFMEMORY;}
}

void CollisionDebugPilot::before_reset() noexcept {proof.clear();if(transaction.has_pending()||legend_layer.pending())blocked_=true;transaction.release();release_texture();consumed_frame_=UINT64_MAX;legend_ready_=false;}
void CollisionDebugPilot::after_reset(IDirect3DDevice8& device,bool called,bool success) noexcept {
    if(!called)return;if(!success){suspended_=true;return;}
    blocked_=suspended_=false;initialize(device);
}
void CollisionDebugPilot::shutdown() noexcept {if(worker_.joinable())worker_.join();loading_=false;proof.clear();transaction.release();release_texture();mesh_.clear();disabled_=true;legend_ready_=false;}

} // namespace gfx2::ps2port
