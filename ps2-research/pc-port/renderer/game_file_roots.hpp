#pragma once
// Game file roots for proxy-side readers (COLLISION-DEBUG1): where a relative game path such as
// "DataScene/RaceTest/Evo2Autumn.xml" or "DataGx/Course/<id>/<id>.dx" is found.
//
// Order (first hit wins):
//   1. Mod overlay roots, loose files only. The dinput8 VehicleRoster module serves the Vehicle Manager overlay
//      <game>\MRMods\Vehicles\active\resources to the game through import hooks; the proxy reads files itself, so it
//      has to look there explicitly. Configured extra roots come first, then the default Vehicle Manager root.
//      A relative overlay root is resolved against every game folder; an absolute one is used once.
//   2. The game folders (process working directory, then the proxy folder): in each, a loose file, then its Data.sma.
// Header-only and D3D-free so tests/collision_debug_tests.cpp checks the same code.
#include "sma_archive.hpp"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace gfx2::ps2port::gameroots {

inline constexpr wchar_t kVehicleManagerOverlay[]=L"MRMods\\Vehicles\\active\\resources";

struct Root {
    std::filesystem::path folder;
    std::unique_ptr<sma::Archive> archive; // game folders only
    bool overlay=false;
};

// Splits a ';'-separated list; blanks and surrounding spaces/quotes are dropped.
inline std::vector<std::wstring> split_list(std::wstring_view list) {
    std::vector<std::wstring> out;size_t at=0;
    while(at<=list.size()){
        size_t end=list.find(L';',at);if(end==std::wstring_view::npos)end=list.size();
        std::wstring_view item=list.substr(at,end-at);
        while(!item.empty()&&(item.front()==L' '||item.front()==L'\t'||item.front()==L'"'))item.remove_prefix(1);
        while(!item.empty()&&(item.back()==L' '||item.back()==L'\t'||item.back()==L'"'))item.remove_suffix(1);
        if(!item.empty())out.emplace_back(item);
        at=end+1;
    }
    return out;
}

inline bool read_loose(const std::filesystem::path& path,std::vector<uint8_t>& out,uint64_t limit) {
    out.clear();std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file)return false;
    const auto size=static_cast<std::streamoff>(file.tellg());
    if(size<=0||static_cast<uint64_t>(size)>limit)return false;
    out.resize(static_cast<size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(out.data()),size);
    if(!file){out.clear();return false;}
    return true;
}

inline bool contains(const std::vector<Root>& roots,const std::filesystem::path& folder) {
    std::error_code error;
    for(const auto& r:roots)if(std::filesystem::equivalent(r.folder,folder,error))return true;
    return false;
}

// game_folders: working directory first, then the proxy folder (duplicates collapse).
// overlays: extra overlay roots (searched before the Vehicle Manager root, which is always appended).
// archive_path: CollisionDebugArchive (default "<proxy folder>\Data.sma"); a relative one, or one in proxy_folder,
// means "<game folder>\<file name>" per game folder, an absolute one elsewhere is used as is.
inline std::vector<Root> build(const std::vector<std::filesystem::path>& game_folders,std::vector<std::wstring> overlays,
                               const std::filesystem::path& archive_path,const std::filesystem::path& proxy_folder) {
    std::vector<Root> roots;
    overlays.emplace_back(kVehicleManagerOverlay);
    for(const auto& spec:overlays){
        const std::filesystem::path p(spec);
        std::vector<std::filesystem::path> candidates;
        if(p.is_absolute())candidates.push_back(p);else for(const auto& f:game_folders)candidates.push_back(f/p);
        for(const auto& c:candidates){
            std::error_code error;if(!std::filesystem::is_directory(c,error))continue;
            const auto canon=std::filesystem::weakly_canonical(c,error);
            if(contains(roots,canon))continue;
            Root r;r.folder=canon;r.overlay=true;roots.push_back(std::move(r));
        }
    }
    for(const auto& f:game_folders){
        std::error_code error;const auto canon=std::filesystem::weakly_canonical(f,error);
        if(contains(roots,canon))continue;
        Root r;r.folder=canon;
        std::filesystem::path archive(archive_path);
        if(archive.is_relative()||archive.parent_path()==proxy_folder)archive=canon/archive.filename();
        r.archive=std::make_unique<sma::Archive>();r.archive->open(archive.wstring());
        roots.push_back(std::move(r));
    }
    return roots;
}

// Reads `rel` from the first root that has it. `where`: "LOOSE MOD" (overlay), "LOOSE CWD"/"SMA CWD" (working
// directory, when it differs from the proxy folder), "LOOSE"/"DATA.SMA" (proxy folder or the only game folder).
inline bool read(const std::vector<Root>& roots,const std::string& rel,std::vector<uint8_t>& out,std::string& where,
                 uint64_t limit) {
    out.clear();
    size_t games=0;for(const auto& r:roots)if(!r.overlay)++games;
    size_t game_index=0;
    for(const auto& r:roots){
        std::error_code error;const auto loose=r.folder/std::filesystem::path(rel);
        const bool first_game=!r.overlay&&game_index==0&&games>1;
        if(std::filesystem::is_regular_file(loose,error)&&read_loose(loose,out,limit)){
            where=r.overlay?"LOOSE MOD":first_game?"LOOSE CWD":"LOOSE";return true;
        }
        if(!r.overlay&&r.archive&&r.archive->is_open()&&r.archive->read(rel,out,limit)){
            where=first_game?"SMA CWD":"DATA.SMA";return true;
        }
        if(!r.overlay)++game_index;
    }
    out.clear();return false;
}

} // namespace gfx2::ps2port::gameroots
