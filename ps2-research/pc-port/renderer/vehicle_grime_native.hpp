#pragma once
// R-SURFACE1 G0: Vehicle Grime probe (diagnostics only, never changes a draw or a device state).
//
// Independent of Atmosphere, Extra Options (dinput8) and every other feature switch: its own config file
// <game>\VehicleGrime.ini and its own log MRRRenderer\logs\grime-*.jsonl. Two entry points are called from the
// existing DrawPrimitive integration (atmosphere_native.hpp only hosts the call sites):
//   observe_particles(): every non-UI DrawPrimitive. Identifies the stage-0 texture by level-0 BGRA SHA-256, and for
//                        surface particle families reads the triangles from the proxy's buffer shadow and attributes
//                        their centroids to the nearest car (Broker gaVehicleOutputData +0xb0 positions).
//   tick():              once per frame (menus included). Samples MasterRallye/* (the Master Rallye *mode* save
//                        state), Race/Type, PlayerState.xml writes, emits exposure samples and race summaries, and
//                        runs the persistence dry run (end-of-stage grime bound to the next saved checkpoint).
#include "vehicle_grime.hpp"
#include "vehicle_grime_overlay.hpp"
#include "vehicle_grime_shell.hpp"
#include "course_objects_native_integration.hpp"
#include "ps2_hud_damage_feed.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <unordered_map>
#include <unordered_set>

namespace gfx2::grimeintegration {

struct Config {
    // probe = G0 diagnostics log; simulate = the per-car grime state runs (probe, or G2 Enabled=1 + Dynamic=1).
    bool loaded = false, probe = false, persistence = true, simulate = false;
    float rate = 1.f, race_start = 0.f, dry_seconds = 45.f; std::array<float, 3> grass_rgb{.34f, .42f, .18f};
    float radius = 4.f; unsigned sample_ms = 500, heartbeat_ms = 5000;
    std::filesystem::path game, store;
};
struct TextureEntry { bool seen = false; uint64_t generation = 0; grime::Family family = grime::Family::Unknown; std::string sha; const char* source = "";
                      std::array<float, 3> rgb{-1.f, -1.f, -1.f}; };   // G2.1: alpha-weighted mean colour (0..1)
struct BrokerRaw { bool present = false; uint32_t tag = UINT32_MAX, word = 0; };

struct Probe {
    Config cfg;
    ps2diag::Stream stream;
    ps2port::HudDamageFeedReader reader;
    std::unordered_map<uintptr_t, TextureEntry> textures;
    std::unordered_map<uint64_t, uint64_t> census;       // (rva << 8 | family) -> draws this race
    std::array<grime::RaceCar, 8> race_cars{}; unsigned race_car_count = 0; grime::MasterMatch match{}; bool attract = false;
    std::array<grime::CarTrack, 8> cars{};
    std::array<grime::CarGrime, 8> grime{}; uint64_t grime_serial = 0;   // serial: +1 whenever any car's state changed
    uint64_t race = 0, cars_frame = UINT64_MAX, tick_frame = UINT64_MAX, last_alive_frame = 0, race_frames = 0;
    bool paused = false, replay_now = false, replay_seen = false; uint64_t window_frames = 0;
    std::string pending; double last_flush = 0;
    // Frame pacing: render frame deltas and distinct Broker pose updates of the human car per sample window.
    double last_tick = 0; std::vector<float> frame_ms; uint32_t pose_updates = 0; std::array<float, 3> last_pose{}; bool last_pose_ok = false; int human = -1;
    uint32_t render_pose_frames = 0, render_pose_changes = 0;
    double probe_ms_max = 0, master_ms_max = 0;   // own cost: worst tick and worst MasterRallye/* read in the window   // drawn car body WORLD matrix: frames compared / frames it moved
    double race_start = 0, last_sample = 0, last_heartbeat = 0, last_master = -10, last_file = -10;
    uint64_t particle_draws = 0, surface_draws = 0, shadow_failures = 0, triangles = 0;
    grime::MasterState master{}, race_master{};
    int race_type = INT32_MIN, replay = -1;
    std::array<int, 8> race_car_ids{}, race_player_types{};
    uint64_t playerstate_write = 0;
    grime::Store store; grime::CampaignTracker tracker; bool store_loaded = false;
    std::map<std::string, BrokerRaw> tags_seen;
};
inline Probe& probe() noexcept { static Probe p; return p; }

inline double now_seconds() noexcept {
    LARGE_INTEGER f{}, c{}; QueryPerformanceFrequency(&f); QueryPerformanceCounter(&c);
    return f.QuadPart ? double(c.QuadPart) / double(f.QuadPart) : 0;
}
// Buffered: the stream opens and closes the file per write; on the render thread that is a frame-time hitch
// (owner run 2026-11-12 felt stutter). Lines are flushed in one write every ~10 s, at race ends and at 64 KiB.
inline void flush(Probe& p) noexcept {
    if (p.pending.empty()) return;
    if (p.pending.back() == '\n') p.pending.pop_back();
    p.stream.write(p.pending); p.pending.clear(); p.last_flush = now_seconds();
}
inline void write(Probe& p, const std::string& line) noexcept {
    if (!p.cfg.probe) return;   // G2 simulation without the G0 diagnostics log
    try { p.pending += line; p.pending += '\n'; } catch (...) { p.pending.clear(); return; }
    if (p.pending.size() >= 64 * 1024 || now_seconds() - p.last_flush >= 10) flush(p);
}

inline void configure(Probe& p) noexcept {
    if (p.cfg.loaded) return;
    p.cfg.loaded = true;
    try {
        wchar_t exe[MAX_PATH]{}; GetModuleFileNameW(nullptr, exe, MAX_PATH);
        p.cfg.game = std::filesystem::path(exe).parent_path();
        const auto ini = (p.cfg.game / L"VehicleGrime.ini").wstring();
        p.cfg.probe = GetPrivateProfileIntW(L"VehicleGrime", L"Probe", 0, ini.c_str()) == 1;
        p.cfg.persistence = GetPrivateProfileIntW(L"Persistence", L"MasterRallye", 1, ini.c_str()) == 1;
        const auto radius_cm = GetPrivateProfileIntW(L"VehicleGrime", L"ProbeRadiusCm", 400, ini.c_str());
        p.cfg.radius = std::clamp(float(radius_cm) / 100.f, 1.f, 15.f);
        p.cfg.sample_ms = std::clamp<unsigned>(GetPrivateProfileIntW(L"VehicleGrime", L"SampleMs", 500, ini.c_str()), 100u, 5000u);
        wchar_t store[MAX_PATH]{};
        GetPrivateProfileStringW(L"Persistence", L"Store", L"MRRRenderer\\grime\\master-rallye-grime.txt", store, MAX_PATH, ini.c_str());
        p.cfg.store = std::filesystem::path(store).is_absolute() ? std::filesystem::path(store) : p.cfg.game / store;
        auto real = [&](const wchar_t* key, float def, float lo, float hi) { wchar_t b[64]{}; GetPrivateProfileStringW(L"VehicleGrime", key, L"", b, 64, ini.c_str());
            if (!b[0]) return def; try { const float v = std::stof(b); return std::isfinite(v) ? std::clamp(v, lo, hi) : def; } catch (...) { return def; } };
        const bool visual = GetPrivateProfileIntW(L"VehicleGrime", L"Enabled", 0, ini.c_str()) == 1 && GetPrivateProfileIntW(L"VehicleGrime", L"Dynamic", 1, ini.c_str()) == 1;
        p.cfg.simulate = p.cfg.probe || visual;
        p.cfg.rate = real(L"Rate", 1.f, 0.f, 20.f); p.cfg.race_start = real(L"RaceStart", 0.f, 0.f, 1.f); p.cfg.dry_seconds = real(L"DryTime", 45.f, 1.f, 3600.f);
        { wchar_t b[96]{}; GetPrivateProfileStringW(L"Look", L"GrassRGB", L"", b, 96, ini.c_str()); float r = 0, g = 0, bl = 0;
          if (b[0] && swscanf_s(b, L"%f , %f , %f", &r, &g, &bl) == 3) p.cfg.grass_rgb = {std::clamp(r, 0.f, 1.f), std::clamp(g, 0.f, 1.f), std::clamp(bl, 0.f, 1.f)}; }
        if (!p.cfg.probe) return;
        SYSTEMTIME t{}; GetLocalTime(&t);
        wchar_t stem[96]{};
        std::swprintf(stem, std::size(stem), L"grime-%04u%02u%02u-%02u%02u%02u-%lu.jsonl", t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond,
                      static_cast<unsigned long>(GetCurrentProcessId()));
        const std::filesystem::path dir = session().directory.empty() ? p.cfg.game / L"MRRRenderer" / L"logs" : std::filesystem::path(session().directory);
        p.stream.configure(dir / stem, 8ull * 1024 * 1024);
        write(p, "{\"type\":\"grime_session\",\"schema\":1,\"phase\":\"R-SURFACE1-G0\",\"observation_only\":true,\"exe_sha256\":" + ps2diag::quote(session().exe_sha) +
                     ",\"proxy_sha256\":" + ps2diag::quote(session().proxy_sha) + ",\"radius\":" + ps2diag::number(p.cfg.radius, 2) +
                     ",\"sample_ms\":" + std::to_string(p.cfg.sample_ms) + ",\"persistence_dry_run\":" + (p.cfg.persistence ? "true" : "false") + "}");
    } catch (...) { p.cfg.probe = false; }
}

// ---- Broker reads (read-only, every pointer validated; never calls native getters) ------------------------------------
// Key -> pool id cache. resolve_id scans the game's string pool: ~40 MasterRallye/* lookups cost 6.3 ms, which was
// a 1.5x frame-time hitch twice a second (owner run 2026-11-12). Ids are stable for the process; every cached id is
// still re-validated against its record, and a mismatch drops it. Render thread only.
inline bool broker_id(ps2port::HudLiveMemory& m, const char* key, uint32_t& id) noexcept {
    static std::unordered_map<std::string, uint32_t> ids;
    try {
        if (const auto it = ids.find(key); it != ids.end()) { id = it->second; return true; }
        if (!m.resolve_id(0x400000, key, id)) return false;
        if (ids.size() < 4096) ids.emplace(key, id);
        return true;
    } catch (...) { return m.resolve_id(0x400000, key, id); }
}
inline BrokerRaw broker_raw(ps2port::HudLiveMemory& m, const char* key) noexcept {
    BrokerRaw r; uint32_t id = 0, manager = 0, begin = 0, end = 0, native_id = 0, payload = 0;
    if (!broker_id(m, key, id) || !m.read(0x400000 + ps2port::kHudBrokerRva, &manager, 4) || manager < 0x10000 || (manager & 3) ||
        !m.read(manager + 4, &begin, 4) || !m.read(manager + 8, &end, 4) || begin < 0x10000 || end < begin || (end - begin) % 0x1c || id >= (end - begin) / 0x1c)
        return r;
    const uint32_t rec = begin + id * 0x1c;
    if (!m.read(rec, &native_id, 4) || native_id != id || !m.read(rec + 8, &r.tag, 4) || !m.read(rec + 4, &payload, 4) || payload < 0x10000) return r;
    if (r.tag == 0) { uint8_t b = 0; if (!m.read(payload, &b, 1) || b > 1) return r; r.word = b; }
    else if (r.tag == 12) return r;   // unpublished slot
    else if (!m.read(payload, &r.word, 4)) return r;
    r.present = true; return r;
}
inline grime::MasterState read_master(Probe& p, ps2port::HudLiveMemory& m) noexcept {
    grime::MasterState s;
    auto i32 = [&](const char* k, int& out) { const auto r = broker_raw(m, k); if (r.present && r.tag == 2) { out = int32_t(r.word); return true; } return false; };
    auto bit = [&](const char* k, bool& out) { const auto r = broker_raw(m, k); if (r.present && r.tag == 0) { out = r.word != 0; return true; } return false; };
    auto raw = [&](const char* k, uint32_t& out) {
        const auto r = broker_raw(m, k); if (!r.present) return false;
        auto& seen = p.tags_seen[k]; if (!seen.present) { seen = r; } out = r.word; return true; };
    const bool stage = i32("MasterRallye/Stage", s.stage), cls = i32("MasterRallye/VehicleClass", s.vehicle_class);
    i32("MasterRallye/DifficultyLevel", s.difficulty); bit("MasterRallye/GameSaved", s.saved);
    for (unsigned i = 0; i < s.cars.size(); ++i) {
        char k[64]; auto& c = s.cars[i];
        std::snprintf(k, sizeof(k), "MasterRallye/Car%u/CarID", i); const bool a = i32(k, c.car_id);
        std::snprintf(k, sizeof(k), "MasterRallye/Car%u/DriverID", i); const bool b = i32(k, c.driver_id);
        std::snprintf(k, sizeof(k), "MasterRallye/Car%u/Player", i); bit(k, c.player);
        std::snprintf(k, sizeof(k), "MasterRallye/Car%u/TotalTime", i); raw(k, c.total_time_bits);
        std::snprintf(k, sizeof(k), "MasterRallye/Car%u/RaceTime", i); raw(k, c.race_time_bits);
        c.ok = a && b;
    }
    s.ok = stage && cls;
    return s;
}

inline void load_store(Probe& p) noexcept {
    if (p.store_loaded) return;
    p.store_loaded = true;
    try {
        std::ifstream in(p.cfg.store, std::ios::binary); if (!in) return;
        std::string text((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        const auto n = p.store.parse(text);
        write(p, "{\"type\":\"grime_store_loaded\",\"records\":" + std::to_string(n) + ",\"snapshots\":" + std::to_string(p.store.size()) + "}");
    } catch (...) {}
}
inline void save_store(Probe& p) noexcept {
    try {
        std::error_code e; std::filesystem::create_directories(p.cfg.store.parent_path(), e);
        const auto tmp = p.cfg.store.wstring() + L".tmp";
        { std::ofstream out(tmp, std::ios::binary | std::ios::trunc); out << p.store.serialize(); if (!out) return; }
        MoveFileExW(tmp.c_str(), p.cfg.store.c_str(), MOVEFILE_REPLACE_EXISTING);
    } catch (...) {}
}

// ---- texture identity --------------------------------------------------------------------------------------------------
inline const TextureEntry* texture(Device8& d, Probe& p, IDirect3DDevice8& n, uintptr_t rva, DWORD fvf) noexcept {
    courseintegration::Ref<IDirect3DBaseTexture8> base;
    if (FAILED(n.GetTexture(0, &base.p)) || !base.p) return nullptr;
    const auto pointer = reinterpret_cast<uintptr_t>(base.p);
    const auto generation = d.trace.resources.generation(pointer);
    // Untracked textures (generation 0) are identified once per pointer, never re-hashed per draw.
    if (const auto it = p.textures.find(pointer); it != p.textures.end() && it->second.generation == generation) return &it->second;
    if (p.textures.size() > 8192) p.textures.clear();
    auto& e = p.textures[pointer];
    e = {}; e.seen = true; e.generation = generation;
    std::string reason = "not_a_2d_texture"; D3DSURFACE_DESC desc{}; double mean[4]{};
    try {
        if (base.p->GetType() == D3DRTYPE_TEXTURE) {
            auto* t = static_cast<IDirect3DTexture8*>(base.p);
            if (FAILED(t->GetLevelDesc(0, &desc))) reason = "level_desc_failed";
            else if (desc.Format != D3DFMT_A8R8G8B8 && desc.Format != D3DFMT_X8R8G8B8) reason = "format_not_8888";
            else if (desc.Pool == D3DPOOL_DEFAULT || desc.Width > 256 || desc.Height > 256 || !desc.Width || !desc.Height) reason = "pool_or_size_unsupported";
            else {
                std::vector<BYTE> px(size_t(desc.Width) * desc.Height * 4); D3DLOCKED_RECT lock{};
                if (FAILED(t->LockRect(0, &lock, nullptr, D3DLOCK_READONLY))) reason = "lock_failed";
                else {
                    const bool ok = lock.pBits && lock.Pitch >= int(desc.Width * 4);
                    if (ok) for (UINT y = 0; y < desc.Height; ++y) std::memcpy(px.data() + size_t(y) * desc.Width * 4, static_cast<BYTE*>(lock.pBits) + size_t(y) * lock.Pitch, desc.Width * 4);
                    t->UnlockRect(0);
                    if (!ok) reason = "lock_invalid";
                    else {
                        if (desc.Format == D3DFMT_X8R8G8B8) for (size_t i = 3; i < px.size(); i += 4) px[i] = 255;
                        for (size_t i = 0; i < px.size(); i += 4) for (int c = 0; c < 4; ++c) mean[c] += px[i + c];
                        { double w = 0, rgb[3]{}; for (size_t i = 0; i < px.size(); i += 4) { const double a = px[i + 3]; w += a; rgb[0] += a * px[i + 2]; rgb[1] += a * px[i + 1]; rgb[2] += a * px[i]; }
                          if (w > 0) for (unsigned c = 0; c < 3; ++c) e.rgb[c] = float(rgb[c] / w / 255.0); }
                        for (double& v : mean) v /= double(px.size() / 4);
                        e.sha = sha256_bytes(px.data(), px.size());
                        if (const auto* id = grime::identify(e.sha)) { e.family = id->family; e.source = id->source; reason = "retail_particle_matched"; }
                        else reason = "unknown_content";
                    }
                }
            }
        }
        // One record per new texture identity: lets G0 prove the surface textures really reach these draw sites.
        if (p.textures.size() <= 4096)
            write(p, "{\"type\":\"grime_texture\",\"rva\":" + std::to_string(rva) + ",\"fvf\":" + std::to_string(fvf) + ",\"pointer\":" + std::to_string(pointer) +
                         ",\"generation\":" + std::to_string(generation) + ",\"format\":" + std::to_string(desc.Format) + ",\"width\":" + std::to_string(desc.Width) +
                         ",\"height\":" + std::to_string(desc.Height) + ",\"pool\":" + std::to_string(desc.Pool) + ",\"bgra_sha256\":" + ps2diag::quote(e.sha) +
                         ",\"family\":" + ps2diag::quote(grime::family_name(e.family)) + ",\"source\":" + ps2diag::quote(e.source) + ",\"reason\":" + ps2diag::quote(reason) +
                         ",\"mean_bgra\":[" + ps2diag::number(mean[0], 1) + "," + ps2diag::number(mean[1], 1) + "," + ps2diag::number(mean[2], 1) + "," + ps2diag::number(mean[3], 1) +
                         "],\"race_generation\":" + std::to_string(p.race) + "}");
    } catch (...) {}
    return &e;
}

// ---- race lifecycle ---------------------------------------------------------------------------------------------------
inline std::string cars_json(Probe& p, bool race_totals) {
    std::string out = "[";
    bool first = true;
    for (unsigned i = 0; i < p.cars.size(); ++i) {
        const auto& c = p.cars[i];
        const auto& e = race_totals ? c.race : c.window;
        if (!c.now.ok && e.empty()) continue;
        if (!first) out += ",";
        first = false;
        out += "{\"car\":" + std::to_string(i) + ",\"pos\":[" + ps2diag::number(c.now.position[0], 2) + "," + ps2diag::number(c.now.position[1], 2) + "," +
               ps2diag::number(c.now.position[2], 2) + "],\"speed\":" + ps2diag::number(c.speed, 2) + ",\"exposure\":" + grime::exposure_json(e) +
               ",\"grime_dry_run\":" + grime::grime_json(p.grime[i]) + "}";
    }
    return out + "]";
}
inline std::string census_json(const Probe& p) {
    std::string out = "{"; bool first = true;
    std::map<uint64_t, uint64_t> sorted(p.census.begin(), p.census.end());
    for (const auto& [k, v] : sorted) { if (!first) out += ","; first = false;
        out += ps2diag::quote(std::to_string(k >> 8) + ":" + grime::family_name(static_cast<grime::Family>(k & 255))) + ":" + std::to_string(v); }
    return out + "}";
}
inline void race_end(Probe& p, const char* why) noexcept {
    if (!p.race) return;
    try {
        write(p, "{\"type\":\"grime_race_end\",\"race_generation\":" + std::to_string(p.race) + ",\"why\":" + ps2diag::quote(why) + ",\"seconds\":" +
                     ps2diag::number(now_seconds() - p.race_start, 1) + ",\"frames\":" + std::to_string(p.race_frames) + ",\"race_type\":" + std::to_string(p.race_type) +
                     ",\"particle_draws\":" + std::to_string(p.particle_draws) + ",\"surface_draws\":" + std::to_string(p.surface_draws) +
                     ",\"triangles\":" + std::to_string(p.triangles) + ",\"shadow_failures\":" + std::to_string(p.shadow_failures) +
                     ",\"census\":" + census_json(p) + ",\"cars\":" + cars_json(p, true) + ",\"master_at_start\":" + p.race_master.json() + "}");
        // Persistence dry run: the end-of-stage grime waits for the next saved checkpoint of the same campaign.
        if (p.cfg.persistence && p.match.ok && p.replay != 1 && !p.replay_seen && !p.attract) {
            grime::Snapshot s; s.campaign = p.race_master.campaign(); s.checkpoint = p.race_master.checkpoint();
            for (unsigned i = 0; i < p.race_car_count; ++i) { const int m = p.match.master_of_race[i]; if (m < 0) continue;
                s.cars[size_t(m)] = p.grime[i]; s.present[size_t(m)] = true; }
            p.tracker.race_finished(p.race_master, s);
            write(p, "{\"type\":\"grime_persist_pending\",\"campaign\":" + ps2diag::quote(s.campaign) + ",\"from_checkpoint\":" + ps2diag::quote(s.checkpoint) +
                         ",\"note\":\"bound to the next checkpoint of this campaign; a quit or restart without save keeps the old checkpoint\"}");
        }
    } catch (...) {}
    flush(p);
    p.race = 0; p.replay_seen = false; p.attract = false; p.match = {}; p.race_car_count = 0; p.census.clear(); p.particle_draws = p.surface_draws = p.triangles = p.shadow_failures = 0; p.race_frames = 0;
    for (auto& c : p.cars) c = {};
}
inline void race_begin(Probe& p, ps2port::HudLiveMemory& m, uint64_t generation) noexcept {
    p.human = -1; p.race_cars = {}; p.frame_ms.clear(); p.pose_updates = 0; p.last_pose_ok = false;
    p.race = generation; p.race_start = p.last_sample = p.last_heartbeat = now_seconds(); p.race_frames = 0;
    p.race_master = read_master(p, m);
    const auto type = broker_raw(m, "Race/Type"), replay = broker_raw(m, "Race/PlaybackReplay");
    p.race_type = type.present ? int32_t(type.word) : INT32_MIN; p.replay = replay.present ? int(replay.word) : -1;
    std::string race_cars = "[";
    for (unsigned i = 0; i < 8; ++i) {
        char k[64]; std::snprintf(k, sizeof(k), "Race/Car%u/PlayerType", i); const auto pt = broker_raw(m, k);
        if (!pt.present) break;
        std::string extra;
        std::snprintf(k, sizeof(k), "Race/Car%u/CarID", i); const auto car_id = broker_raw(m, k);
        std::snprintf(k, sizeof(k), "Race/Car%u/DriverID", i); const auto driver_id = broker_raw(m, k);
        auto& rc = p.race_cars[i]; rc.ok = car_id.present && car_id.tag == 2 && driver_id.present && driver_id.tag == 2;
        rc.car_id = int32_t(car_id.word); rc.driver_id = int32_t(driver_id.word); rc.human = pt.present && pt.tag == 2 && pt.word == 1; p.race_car_count = i + 1;
        if (rc.human) p.human = int(i);
        extra = ",\"car_id\":" + std::to_string(rc.ok ? rc.car_id : -1) + ",\"driver_id\":" + std::to_string(rc.ok ? rc.driver_id : -1);
        race_cars += std::string(i ? "," : "") + "{\"car\":" + std::to_string(i) + ",\"player_type\":" + std::to_string(pt.word) + extra + "}";
    }
    race_cars += "]";
    p.match = grime::match_master(p.race_cars, p.race_car_count, p.race_master);
    { const auto hud = ps2port::ps2_race_hud_context(); p.attract = hud.valid && hud.attract; }
    // Dry run of the restore rule: the grime stored for the current checkpoint (nullptr = clean start).
    for (auto& g : p.grime) g = grime::start_state(p.cfg.race_start);
    ++p.grime_serial;
    std::string applied = "null";
    if (p.cfg.persistence && p.match.ok && p.replay != 1 && !p.attract) {
        load_store(p);
        if (const auto* s = p.tracker.start(p.race_master, p.store)) {
            applied = "[";
            for (unsigned i = 0; i < s->cars.size(); ++i) {
                for (unsigned r = 0; r < p.race_car_count; ++r) if (p.match.master_of_race[r] == int(i) && s->present[i]) p.grime[r] = s->cars[i];
                applied += std::string(i ? "," : "") + (s->present[i] ? grime::grime_json(s->cars[i]) : "null"); }
            applied += "]";
        }
    }
    write(p, "{\"type\":\"grime_race_start\",\"race_generation\":" + std::to_string(generation) + ",\"race_type\":" + std::to_string(p.race_type) +
                 ",\"replay\":" + std::to_string(p.replay) + ",\"attract\":" + (p.attract ? "true" : "false") + ",\"master_mode_match\":" + (p.match.ok ? "true" : "false") + ",\"race_cars\":" + race_cars + ",\"master\":" + p.race_master.json() +
                 ",\"restored_dry_run\":" + applied + "}");
}

// Car positions once per frame inside a certified race.
inline void refresh_cars(Device8& d, Probe& p) noexcept {
    const auto frame = d.trace.frame_number();
    if (p.cars_frame == frame) return;
    p.cars_frame = frame;
    bool single = false; const auto cert = courseintegration::certificate(d, single);
    if (!cert.valid || !cert.race_generation) return;
    ps2port::HudLiveMemory m;
    if (cert.race_generation != p.race) { race_end(p, "generation_changed"); race_begin(p, m, cert.race_generation); }
    p.last_alive_frame = frame; ++p.race_frames;
    std::array<ps2port::HudDamageFeedReader::CarGear, 8> gears{};
    p.reader.car_gears(m, 0x400000, cert.race_generation, gears);
    const double t = now_seconds();
    for (unsigned i = 0; i < 8; ++i) grime::update_motion(p.cars[i], grime::CarSample{gears[i].ok, gears[i].position}, t);
}

inline void observe_particles(Device8& d, D3DPRIMITIVETYPE type, UINT start, UINT count, uintptr_t pc) noexcept {
    auto& p = probe(); configure(p);
    if (!p.cfg.simulate || type != D3DPT_TRIANGLELIST || !count || count > 32768 || !d.trace.scene_active || d.trace.shadow.recording ||
        d.trace.effective_shadow.recording || GetCurrentThreadId() != d.trace.render_thread_id()) return;
    try {
        refresh_cars(d, p);
        if (!p.race) return;
        auto& n = *d.native(); DWORD fvf = 0;
        if (FAILED(n.GetVertexShader(&fvf))) return;
        const auto exe = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
        const uintptr_t rva = pc >= exe ? pc - exe : 0;
        const auto* t = texture(d, p, n, rva, fvf);
        if (!t) return;
        ++p.census[(uint64_t(rva) << 8) | uint64_t(t->family)];
        if (t->family == grime::Family::Unknown || t->family == grime::Family::OtherKnown) return;
        ++p.particle_draws;
        if (fvf != 0x142) return;
        courseintegration::Ref<IDirect3DVertexBuffer8> vb; UINT stride = 0;
        if (FAILED(n.GetStreamSource(0, &vb.p, &stride)) || !vb.p || stride != 24) { ++p.shadow_failures; return; }
        const uint64_t gen = d.trace.resources.generation(reinterpret_cast<uintptr_t>(vb.p));
        const UINT tris = std::min<UINT>(count, 4096);
        std::vector<BYTE> bytes; uint64_t revision = 0;
        if (!gen || !d.copy_buffer_shadow(vb.p, BufferKind::Vertex, gen, uint64_t(start) * stride, size_t(tris) * 3 * stride, bytes, revision) ||
            bytes.size() != size_t(tris) * 3 * stride) {
            if (!p.shadow_failures++) write(p, "{\"type\":\"grime_shadow_unavailable\",\"rva\":" + std::to_string(rva) + ",\"generation\":" + std::to_string(gen) + "}");
            return;
        }
        ++p.surface_draws;
        for (UINT k = 0; k < tris; ++k) {
            std::array<float, 3> c{}, vc{}; float alpha = 0;
            for (unsigned v = 0; v < 3; ++v) {
                const BYTE* at = bytes.data() + (size_t(k) * 3 + v) * stride; float xyz[3]; uint32_t diffuse = 0;
                std::memcpy(xyz, at, 12); std::memcpy(&diffuse, at + 12, 4);
                for (unsigned a = 0; a < 3; ++a) c[a] += xyz[a] / 3.f;
                alpha += float(diffuse >> 24) / (255.f * 3.f);
                vc[0] += float((diffuse >> 16) & 255) / 765.f; vc[1] += float((diffuse >> 8) & 255) / 765.f; vc[2] += float(diffuse & 255) / 765.f;
            }
            // G2.1: particle colour = texture mean x vertex colour (the course tints its particles).
            std::array<float, 3> colour{-1.f, -1.f, -1.f}; if (t->rgb[0] >= 0) for (unsigned a = 0; a < 3; ++a) colour[a] = t->rgb[a] * vc[a];
            if (!std::isfinite(c[0] + c[1] + c[2])) continue;
            ++p.triangles;
            const int owner = grime::attribute(p.cars, 8, c, p.cfg.radius);
            if (owner >= 0) grime::add(p.cars[size_t(owner)], t->family, c, alpha, colour);
        }
    } catch (...) {}
}

// Frame pacing of one sample window: render frame time percentiles and the rate at which the game publishes a new
// pose of the human car (the simulation/update rate as seen by the renderer).
inline std::string pacing_json(Probe& p, double seconds) {
    std::vector<float> v = p.frame_ms; std::sort(v.begin(), v.end());
    auto q = [&](double f) { return v.empty() ? 0.0 : double(v[std::min(v.size() - 1, size_t(f * double(v.size())))]); };
    return "{\"frames\":" + std::to_string(v.size()) + ",\"p50_ms\":" + ps2diag::number(q(.5), 2) + ",\"p95_ms\":" + ps2diag::number(q(.95), 2) +
           ",\"max_ms\":" + ps2diag::number(v.empty() ? 0 : v.back(), 2) + ",\"pose_updates\":" + std::to_string(p.pose_updates) +
           ",\"pose_hz\":" + ps2diag::number(seconds > 0 ? p.pose_updates / seconds : 0, 1) +
           ",\"probe_ms_max\":" + ps2diag::number(p.probe_ms_max, 3) + ",\"master_read_ms_max\":" + ps2diag::number(p.master_ms_max, 3) +
           ",\"render_pose_frames\":" + std::to_string(p.render_pose_frames) + ",\"render_pose_changes\":" + std::to_string(p.render_pose_changes) + "}";
}
// Called by the Atmosphere host (which observes the drawn car body WORLD matrices): did the drawn pose of one car
// change between two consecutive frames? With a 30 Hz simulation, a renderer that interpolates moves every frame.
inline void note_render_pose(bool changed) noexcept {
    auto& p = probe(); if (!p.cfg.probe || !p.race || p.paused || p.replay_now) return;
    ++p.render_pose_frames; if (changed) ++p.render_pose_changes;
}
inline void tick(Device8& d) noexcept {
    auto& p = probe(); configure(p);
    if (!p.cfg.simulate || GetCurrentThreadId() != d.trace.render_thread_id()) return;
    const auto frame = d.trace.frame_number();
    if (p.tick_frame == frame) return;
    p.tick_frame = frame;
    const double tick_start = now_seconds();
    try {
        refresh_cars(d, p);
        const double t = now_seconds();
        // Race end: the native race HUD context (valid while paused, in replay and countdown) is gone for ~1 s.
        const auto hud = ps2port::ps2_race_hud_context();
        const bool alive = p.race && hud.valid && hud.race_generation == p.race;
        if (alive) { p.last_alive_frame = frame; p.paused = hud.pause_known && hud.paused; p.replay_now = hud.replay; p.replay_seen = p.replay_seen || hud.replay; p.attract = p.attract || hud.attract; }
        if (p.race && frame > p.last_alive_frame + 60) race_end(p, "race_context_lost");
        if (p.race && p.last_alive_frame == frame && !p.paused && !p.replay_now) {
            ++p.window_frames;
            if (p.last_tick > 0 && t - p.last_tick < 1.0 && p.frame_ms.size() < 4096) p.frame_ms.push_back(float((t - p.last_tick) * 1000));
            const size_t paced = p.human >= 0 ? size_t(p.human) : 0;   // attract/replay: no human car, use Car0
            if (p.cars[paced].now.ok) {
                const auto& pos = p.cars[paced].now.position;
                if (!p.last_pose_ok || pos != p.last_pose) { ++p.pose_updates; p.last_pose = pos; p.last_pose_ok = true; }
            }
        }
        p.last_tick = t;
        // Exposure samples inside a race; paused and replay time does not accumulate.
        if (p.race && (p.paused || p.replay_now)) { p.last_sample = t; p.window_frames = 0; p.frame_ms.clear(); p.pose_updates = 0; for (auto& c : p.cars) c.window.clear(); }
        else if (p.race && (t - p.last_sample) * 1000 >= p.cfg.sample_ms) {
            const double dt = t - p.last_sample; const double frames = double(p.window_frames); p.last_sample = t; p.window_frames = 0;
            bool any = false;
            grime::Rates rates; rates.dust *= p.cfg.rate; rates.mud *= p.cfg.rate; rates.stones *= p.cfg.rate; rates.grass *= p.cfg.rate; rates.dry_seconds = p.cfg.dry_seconds; rates.grass_rgb = p.cfg.grass_rgb;
            for (unsigned i = 0; i < 8; ++i) { if (!p.cars[i].window.empty()) any = true; if (p.cars[i].now.ok) grime::accumulate(p.grime[i], p.cars[i].window, dt, frames, rates); }
            ++p.grime_serial;
            if (any || (t - p.last_heartbeat) * 1000 >= p.cfg.heartbeat_ms) {
                p.last_heartbeat = t;
                write(p, "{\"type\":\"grime_sample\",\"race_generation\":" + std::to_string(p.race) + ",\"t\":" + ps2diag::number(t - p.race_start, 2) +
                             ",\"frame\":" + std::to_string(frame) + ",\"window_frames\":" + std::to_string(uint64_t(frames)) + ",\"pacing\":" + pacing_json(p, dt) + ",\"cars\":" + cars_json(p, false) + "}");
            }
            for (auto& c : p.cars) c.window.clear();
            p.frame_ms.clear(); p.pose_updates = 0; p.render_pose_frames = p.render_pose_changes = 0; p.probe_ms_max = p.master_ms_max = 0;
        }
        // Master Rallye mode state, menus included (2 Hz). Logged on change only.
        // Master Rallye mode values change only in menus; inside a race they were read once at race start.
        if (!p.race && t - p.last_master >= .5) {
            p.last_master = t;
            ps2port::HudLiveMemory m;
            const double master_start = now_seconds();
            const auto s = read_master(p, m);
            p.master_ms_max = std::max(p.master_ms_max, (now_seconds() - master_start) * 1000);
            const auto type = broker_raw(m, "Race/Type");
            if (s != p.master) {
                p.master = s;
                std::string event = "null";
                if (p.cfg.persistence) {
                    load_store(p);
                    const auto e = p.tracker.observe(s, p.store);
                    if (e.kind) { event = ps2diag::quote(e.kind); save_store(p); }
                }
                std::string tags = "{"; bool first = true;
                for (const auto& [k, r] : p.tags_seen) { if (!first) tags += ","; first = false; tags += ps2diag::quote(k) + ":" + std::to_string(r.tag); }
                tags += "}";
                write(p, "{\"type\":\"grime_master\",\"frame\":" + std::to_string(frame) + ",\"in_race\":" + (p.race ? "true" : "false") +
                             ",\"race_type\":" + std::to_string(type.present ? int32_t(type.word) : INT32_MIN) + ",\"state\":" + s.json() +
                             ",\"event\":" + event + ",\"pending\":" + (p.tracker.pending() ? "true" : "false") + ",\"float_tags\":" + tags + "}");
            }
        }
        // PlayerState.xml writes (the game's own save moments).
        if (t - p.last_file >= 1.0) {
            p.last_file = t;
            WIN32_FILE_ATTRIBUTE_DATA a{};
            if (GetFileAttributesExW((p.cfg.game / L"DataGame" / L"PlayerState.xml").c_str(), GetFileExInfoStandard, &a)) {
                const uint64_t w = (uint64_t(a.ftLastWriteTime.dwHighDateTime) << 32) | a.ftLastWriteTime.dwLowDateTime;
                if (p.playerstate_write && w != p.playerstate_write)
                    write(p, "{\"type\":\"grime_playerstate_written\",\"frame\":" + std::to_string(frame) + ",\"in_race\":" + (p.race ? "true" : "false") +
                                 ",\"master\":" + p.master.json() + "}");
                p.playerstate_write = w;
            }
        }
        p.probe_ms_max = std::max(p.probe_ms_max, (now_seconds() - tick_start) * 1000);
    } catch (...) {}
}


// ---- G1 static look: config, body candidates (recorded by the Atmosphere body route), textures --------------------
struct Overlay {
    bool loaded = false, census = false; grimeoverlay::Look look;
    std::unordered_set<uint64_t> bounded, censused, not_car; uint64_t not_car_race = UINT64_MAX;   // not_car: draws proven not to be a car (course etc.), skipped without the owner walk   // fallback draws whose bounds were read once; census keys already logged
    // subset: draw only the exterior triangles from the shell index arena (G1.3), sub_start/sub_count in arena indices.
    struct Candidate { uint64_t frame = UINT64_MAX; UINT min = 0, vertices = 0, start = 0, count = 0; uintptr_t instance = 0; D3DMATRIX world{}; unsigned kind = 0; bool subset = false; UINT sub_start = 0, sub_count = 0;
                       grimeshell::GlassFrame glass; };   // G3: windscreen frame (wiper mask)
    Candidate cand;
    std::unordered_map<uintptr_t, grimeoverlay::Bounds> bounds, wheel_bounds; uint64_t bounds_race = UINT64_MAX;   // car bodies / wheels (wheel-local)
    IDirect3DTexture8* atlas = nullptr; IDirect3DTexture8* ramp = nullptr; bool textures_failed = false; int caps = 0;   // 0 unknown, 1 ok, 2 unsupported
    // G2: zone texture per race car (0..7) and one for the static look (8); rebuilt when the car state changed.
    // G2.1: volume textures (64x32x2: left/right slices) when the device supports them, else 2D (sides averaged).
    std::array<IDirect3DBaseTexture8*, 9> car_ramps{}; std::array<uint64_t, 9> car_serial{}; bool car_ramps_failed = false; int volume = 0;   // 0 unknown, 1 yes, 2 no
    std::array<float, 2> tyre_uv{-1.f, -1.f};
    std::array<IDirect3DTexture8*, 9> wipers{}; std::array<uint64_t, 9> wiper_serial{}; uint64_t wiper_draws = 0, sheen_draws = 0;   // G3
    std::array<float, 8> wet_shown{}; std::array<double, 8> wet_time{}; uint64_t wet_race = UINT64_MAX;   // G3.3 eased wetness
    std::unordered_map<uintptr_t, int> car_of_instance; uint64_t car_map_race = UINT64_MAX;
    uint64_t draws = 0, skipped_far = 0, log_frame = 0, kind_draws[7]{}, subset_draws = 0, switch_draws = 0, fleet_draws = 0;
    // G1.3: cars drawn this frame (instance, WORLD, family), for draws under $switch nodes that the owner walk does not reach
    // (the blight-off brake lens, windows). switch_miss counts frames a no-owner draw matched no car before it is memoised.
    struct FrameCar { uint64_t frame = UINT64_MAX; uintptr_t instance = 0; D3DMATRIX world{}; std::string family; };
    std::array<FrameCar, 16> frame_cars{}; std::unordered_map<uint64_t, unsigned> switch_miss;
};
inline Overlay& overlay() noexcept { static Overlay o; return o; }
inline const grimeoverlay::Look& look() noexcept {
    auto& o = overlay(); if (o.loaded) return o.look; o.loaded = true;
    try {
        wchar_t exe[MAX_PATH]{}; GetModuleFileNameW(nullptr, exe, MAX_PATH);
        const auto ini = (std::filesystem::path(exe).parent_path() / L"VehicleGrime.ini").wstring();
        auto real = [&](const wchar_t* sec, const wchar_t* key, float def) { wchar_t b[64]{}; GetPrivateProfileStringW(sec, key, L"", b, 64, ini.c_str()); if (!b[0]) return def; try { return std::stof(b); } catch (...) { return def; } };
        auto rgb = [&](const wchar_t* key, grimeoverlay::Vec3& out) { wchar_t b[96]{}; GetPrivateProfileStringW(L"Look", key, L"", b, 96, ini.c_str()); float r = 0, g = 0, bl = 0;
            if (b[0] && swscanf_s(b, L"%f , %f , %f", &r, &g, &bl) == 3) out = {std::clamp(r, 0.f, 1.f), std::clamp(g, 0.f, 1.f), std::clamp(bl, 0.f, 1.f)}; };
        o.look.enabled = GetPrivateProfileIntW(L"VehicleGrime", L"Enabled", 0, ini.c_str()) == 1;
        o.look.level = std::clamp(real(L"VehicleGrime", L"StartLevel", 0.f), 0.f, 1.f);
        o.look.mud = std::clamp(real(L"VehicleGrime", L"StartMud", 0.f), 0.f, 1.f);
        o.look.max_distance = std::clamp(real(L"VehicleGrime", L"MaxDistance", 80.f), 5.f, 1000.f);
        o.census = GetPrivateProfileIntW(L"VehicleGrime", L"Census", 0, ini.c_str()) == 1;
        o.look.dynamic = GetPrivateProfileIntW(L"VehicleGrime", L"Dynamic", 1, ini.c_str()) == 1;
        o.look.race_start = std::clamp(real(L"VehicleGrime", L"RaceStart", 0.f), 0.f, 1.f);
        o.look.dust_opacity = std::clamp(real(L"Look", L"DustOpacity", .8f), 0.f, 1.f);
        o.look.surface_tint = std::clamp(real(L"Look", L"SurfaceTint", .75f), 0.f, 1.f);
        o.look.wipers = GetPrivateProfileIntW(L"Look", L"Wipers", 1, ini.c_str()) == 1;
        o.look.sheen = std::clamp(real(L"Look", L"Sheen", .35f), 0.f, 1.f);
        rgb(L"DustRGB", o.look.dust); rgb(L"MudRGB", o.look.mud_tint);
        session().write("{\"type\":\"grime_look\",\"enabled\":" + std::string(o.look.enabled ? "true" : "false") + ",\"level\":" + ps2diag::number(o.look.level, 3) +
            ",\"mud\":" + ps2diag::number(o.look.mud, 3) + ",\"max_distance\":" + ps2diag::number(o.look.max_distance, 1) + "}");
    } catch (...) { o.look.enabled = false; }
    return o.look;
}
inline bool overlay_active() noexcept { const auto& l = look(); return l.enabled && (l.dynamic || l.level > 0.004f); }
// G2: race car index (Broker Race/Car<N>) of a drawn car instance: the car whose physics position is nearest to the
// WORLD translation (positions are published at the physics rate, the drawn pose is interpolated). Cached per race and
// re-checked every call; -1 when no car is within 6 m.
inline int car_index(uintptr_t instance, const D3DMATRIX& world) noexcept {
    auto& p = probe(); auto& o = overlay();
    if (!p.cfg.simulate || !p.race) return -1;
    if (o.car_map_race != p.race) { o.car_of_instance.clear(); o.car_map_race = p.race; }
    const float x = world._41, y = world._42, z = world._43;
    auto dist2 = [&](int i) { const auto& c = p.cars[size_t(i)].now.position; const float dx = c[0] - x, dy = c[1] - y, dz = c[2] - z; return dx * dx + dy * dy + dz * dz; };
    if (const auto it = o.car_of_instance.find(instance); it != o.car_of_instance.end() && p.cars[size_t(it->second)].now.ok && dist2(it->second) < 25.f) return it->second;
    int best = -1; float best_d = 36.f;
    for (int i = 0; i < 8; ++i) if (p.cars[size_t(i)].now.ok) { const float d = dist2(i); if (d < best_d) { best_d = d; best = i; } }
    if (best >= 0) { if (o.car_of_instance.size() > 64) o.car_of_instance.clear(); o.car_of_instance[instance] = best; }
    return best;
}
// Zone texture of one race car (index 0..7) or of the static look (index < 0), rebuilt when the state changed.
// Volume: slice 0 = left side (zone 2), slice 1 = right side (zone 3); the other zones are the same in both.
inline IDirect3DBaseTexture8* car_ramp(IDirect3DDevice8& n, int index) noexcept {
    auto& o = overlay(); auto& p = probe(); const size_t slot = index < 0 ? 8 : size_t(std::min(index, 7));
    if (o.car_ramps_failed) return nullptr;
    try {
        if (!o.volume) { D3DCAPS8 caps{}; o.volume = SUCCEEDED(n.GetDeviceCaps(&caps)) && (caps.TextureCaps & D3DPTEXTURECAPS_VOLUMEMAP) && caps.MaxVolumeExtent >= 64 ? 1 : 2;
            session().write(std::string("{\"type\":\"grime_zone_texture\",\"volume\":") + (o.volume == 1 ? "true" : "false") + "}"); }
        auto& tex = o.car_ramps[slot];
        if (!tex) {
            HRESULT hr = E_FAIL;
            if (o.volume == 1) { IDirect3DVolumeTexture8* v = nullptr; hr = n.CreateVolumeTexture(64, 32, 2, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &v); tex = v; }
            else { IDirect3DTexture8* t = nullptr; hr = n.CreateTexture(64, 32, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &t); tex = t; }
            if (FAILED(hr) || !tex) { tex = nullptr; o.car_ramps_failed = true; return nullptr; }
        }
        const uint64_t serial = index < 0 ? 1 : p.grime_serial + 2;
        if (o.car_serial[slot] == serial) return tex;
        std::array<float, 8> amounts{};
        if (index < 0) amounts.fill(std::clamp(o.look.level, 0.f, 1.f));
        else { const auto& g = p.grime[slot]; for (size_t z = 0; z < 8; ++z) amounts[z] = std::min(1.f, g.dust[z] + g.mud[z]); }
        if (o.volume == 1) {
            auto* v = static_cast<IDirect3DVolumeTexture8*>(tex); D3DLOCKED_BOX box{}; if (FAILED(v->LockBox(0, &box, nullptr, 0))) return nullptr;
            for (unsigned sl = 0; sl < 2; ++sl) { auto side = amounts; side[2] = side[3] = amounts[sl ? 3 : 2];
                for (unsigned y = 0; y < 32; ++y) { auto* row = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(box.pBits) + size_t(sl) * box.SlicePitch + size_t(y) * box.RowPitch);
                    for (unsigned x = 0; x < 64; ++x) row[x] = grimeoverlay::car_ramp_texel(x, y, 64, 32, side); } }
            v->UnlockBox(0);
        } else {
            auto* t = static_cast<IDirect3DTexture8*>(tex); D3DLOCKED_RECT r{}; if (FAILED(t->LockRect(0, &r, nullptr, 0))) return nullptr;
            for (unsigned y = 0; y < 32; ++y) { auto* row = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(r.pBits) + size_t(y) * r.Pitch);
                for (unsigned x = 0; x < 64; ++x) row[x] = grimeoverlay::car_ramp_texel(x, y, 64, 32, amounts); }
            t->UnlockRect(0);
        }
        o.car_serial[slot] = serial; return tex;
    } catch (...) { return nullptr; }
}
// G3: windscreen wiper texture of one race car (or the static look): the windscreen glass level outside the arcs.
inline IDirect3DTexture8* car_wiper(IDirect3DDevice8& n, int index) noexcept {
    auto& o = overlay(); auto& p = probe(); const size_t slot = index < 0 ? 8 : size_t(std::min(index, 7));
    try {
        auto& tex = o.wipers[slot];
        if (!tex && (FAILED(n.CreateTexture(64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &tex)) || !tex)) { tex = nullptr; return nullptr; }
        const uint64_t serial = index < 0 ? 1 : p.grime_serial + 2;
        if (o.wiper_serial[slot] == serial) return tex;
        std::array<float, 8> amounts{};
        if (index < 0) amounts.fill(std::clamp(o.look.level, 0.f, 1.f));
        else { const auto& g = p.grime[slot]; for (size_t z = 0; z < 8; ++z) amounts[z] = std::min(1.f, g.dust[z] + g.mud[z]); }
        const float level = grimeoverlay::windscreen_level(amounts);
        D3DLOCKED_RECT r{}; if (FAILED(tex->LockRect(0, &r, nullptr, 0))) return nullptr;
        for (unsigned y = 0; y < 64; ++y) { auto* row = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(r.pBits) + size_t(y) * r.Pitch);
            for (unsigned x = 0; x < 64; ++x) row[x] = grimeoverlay::wiper_texel(x, y, 64, 64, level); }
        tex->UnlockRect(0); o.wiper_serial[slot] = serial; return tex;
    } catch (...) { return nullptr; }
}
// Adds a draw's car-local extent to the car's bounds (wheel kinds: the wheel's own bounds).
inline void add_bounds(uintptr_t instance, const void* bytes, size_t size, unsigned stride, uint64_t race_generation, unsigned kind) noexcept {
    auto& o = overlay(); if (!instance || stride < 12) return;
    if (o.bounds_race != race_generation) { o.bounds.clear(); o.wheel_bounds.clear(); o.bounded.clear(); o.bounds_race = race_generation; }
    grimeoverlay::Vec3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f}; const auto* b = static_cast<const uint8_t*>(bytes);
    for (size_t at = 0; at + 12 <= size; at += stride) { float v[3]; std::memcpy(v, b + at, 12); for (unsigned k = 0; k < 3; ++k) { lo[k] = std::min(lo[k], v[k]); hi[k] = std::max(hi[k], v[k]); } }
    if (!std::isfinite(lo[0] + lo[1] + lo[2] + hi[0] + hi[1] + hi[2]) || hi[0] < lo[0]) return;
    auto& map = grimeoverlay::kind_wheel(kind) ? o.wheel_bounds : o.bounds; if (map.size() > 64) map.clear(); map[instance].add(lo, hi);
}
// Tint inputs of one race car (zone means), or of the static look.
inline grimeoverlay::CarTone car_tone(int index) noexcept {
    grimeoverlay::CarTone t; if (index < 0) return t;
    const auto& g = probe().grime[size_t(std::min(index, 7))];
    for (size_t z = 0; z < 8; ++z) { t.dust += g.dust[z] / 8; t.mud += g.mud[z] / 8; t.wet += g.wet[z] / 8; t.mud_age += g.mud_age[z] / 8; }
    t.dust_rgb = g.dust_rgb; t.mud_rgb = g.mud_rgb;
    // G3.3: eased wetness (tint darkening and sheen), updated whenever the car is drawn.
    { auto& o = overlay(); auto& p = probe(); const size_t i = size_t(std::min(index, 7)); const double now = now_seconds();
      if (o.wet_race != p.race) { o.wet_race = p.race; o.wet_shown.fill(-1.f); }
      if (o.wet_shown[i] < 0) o.wet_shown[i] = t.wet; else o.wet_shown[i] = grimeoverlay::ease_wet(o.wet_shown[i], t.wet, now - o.wet_time[i]);
      o.wet_time[i] = now; t.wet = o.wet_shown[i]; }
    return t;
}
// ---- G1.3 interior culling (vehicle_grime_shell.hpp) -----------------------------------------------------------------
// Every car-resource draw of a model is collected once (car-local triangles, keyed by content), the model's occupancy
// grid is built two frames after its first draw, and each draw's triangles are classified within ~1 ms per frame. A
// draw whose mask is not ready yet gets no grime that frame. Draws with interior triangles are drawn from a 16-bit index
// arena that holds only their exterior triangles (same VB, base vertex and range). Grids and masks live for the process.
struct ShellDraw { std::vector<grimeshell::Tri> tris; std::vector<uint32_t> local; std::vector<uint8_t> keep; size_t next = 0, kept = 0; bool done = false; };
struct Shell {
    uint64_t first_frame = UINT64_MAX; bool built = false, logged = false; grimeshell::Grid grid; grimeshell::Cabin cabin;
    std::vector<grimeshell::Tri> collected; std::unordered_set<uint64_t> collected_draws; std::unordered_map<uint64_t, ShellDraw> draws;
    double build_ms = 0, mask_ms = 0; uint64_t masked = 0, interior = 0;
};
enum class FilterState : uint8_t { Waiting, Full, Subset, None };
struct Filter { uint64_t content = 0; std::string family; FilterState state = FilterState::Waiting; UINT min = 0, start = 0, count = 0; grimeshell::GlassFrame glass; };
struct Shells {
    std::unordered_map<std::string, Shell> families; std::unordered_map<uint64_t, Filter> filters; uint64_t race = UINT64_MAX, frame = UINT64_MAX;
    IDirect3DDevice8* device = nullptr; IDirect3DIndexBuffer8* arena = nullptr; UINT used = 0; bool failed = false, full_logged = false;
    std::unordered_map<uint64_t, std::pair<UINT, UINT>> placed;   // content ^ min -> arena start, count
};
inline Shells& shells() noexcept { static Shells s; return s; }
constexpr UINT kShellArena = 256u * 1024u;   // 16-bit indices, 512 KiB managed
constexpr double kShellBudgetMs = 1.0;
inline uint64_t draw_key(const void* vb, const void* ib, UINT base, UINT min, UINT vertices, UINT start, UINT count) noexcept {
    return (uint64_t(reinterpret_cast<uintptr_t>(vb)) * 0x9E3779B97F4A7C15ull) ^ (uint64_t(reinterpret_cast<uintptr_t>(ib)) * 0xC2B2AE3D27D4EB4Full) ^
           (uint64_t(base) << 50) ^ (uint64_t(min) << 36) ^ (uint64_t(vertices) << 22) ^ (uint64_t(start) << 8) ^ count;
}
inline uint64_t content_key(const std::vector<uint8_t>& bytes, unsigned stride, const std::vector<uint32_t>& local) noexcept {
    uint64_t h = 1469598103934665603ull; auto mix = [&](const void* v, size_t n) { const auto* b = static_cast<const uint8_t*>(v); for (size_t i = 0; i < n; ++i) { h ^= b[i]; h *= 1099511628211ull; } };
    for (size_t at = 0; at + 12 <= bytes.size(); at += stride) mix(bytes.data() + at, 12);
    mix(local.data(), local.size() * 4); return h;
}
inline double shell_ms() noexcept { LARGE_INTEGER f{}, c{}; QueryPerformanceFrequency(&f); QueryPerformanceCounter(&c); return f.QuadPart ? double(c.QuadPart) * 1000.0 / double(f.QuadPart) : 0; }
// Once per frame: build the grids that are due, then classify triangles until the budget is spent.
inline void shell_step(uint64_t frame) noexcept {
    auto& s = shells(); if (s.frame == frame) return; s.frame = frame;
    try {
        const double t0 = shell_ms();
        for (auto& [name, sh] : s.families) {
            if (!sh.built) {
                if (sh.first_frame == UINT64_MAX || frame < sh.first_frame + 2) continue;
                const double b = shell_ms(); sh.grid = grimeshell::build(sh.collected); sh.built = true; sh.build_ms = shell_ms() - b;
                sh.collected.clear(); sh.collected.shrink_to_fit(); sh.collected_draws.clear();
                return;   // at most one grid per frame (a few ms each); masks continue next frame
            }
            for (auto& [key, dr] : sh.draws) {
                if (dr.done) continue;
                const double m = shell_ms();
                while (dr.next < dr.tris.size()) {
                    if ((dr.next & 7) == 0 && shell_ms() - t0 > kShellBudgetMs) { sh.mask_ms += shell_ms() - m; return; }
                    const auto& tri = dr.tris[dr.next];
                    const bool e = !sh.grid.valid() || !grimeshell::cabin_contains(sh.cabin, tri) || grimeshell::exterior(sh.grid, tri);
                    dr.keep[dr.next] = e; dr.kept += e; sh.interior += !e; ++sh.masked; ++dr.next;
                }
                dr.done = true; sh.mask_ms += shell_ms() - m;
            }
            if (!sh.logged) { sh.logged = true;
                session().write("{\"type\":\"grime_shell\",\"family\":" + ps2diag::quote(name) + ",\"grid\":" + std::string(sh.grid.valid() ? "true" : "false") +
                    ",\"dims\":[" + std::to_string(sh.grid.dims[0]) + "," + std::to_string(sh.grid.dims[1]) + "," + std::to_string(sh.grid.dims[2]) + "],\"draws\":" + std::to_string(sh.draws.size()) +
                    ",\"triangles\":" + std::to_string(sh.masked) + ",\"interior\":" + std::to_string(sh.interior) + ",\"build_ms\":" + ps2diag::number(sh.build_ms, 2) +
                    ",\"mask_ms\":" + ps2diag::number(sh.mask_ms, 2) + ",\"cabin\":" + std::string(sh.cabin.valid() ? "true" : "false") + ",\"frame\":" + std::to_string(frame) + "}"); }
        }
    } catch (...) {}
}
// Places the exterior triangles of one draw in the arena (index values local + min, used with the draw's own base vertex).
inline bool shell_place(IDirect3DDevice8& n, uint64_t content, const ShellDraw& dr, UINT min, UINT& start, UINT& count) noexcept {
    auto& s = shells();
    if (s.device != &n) { if (s.arena) s.arena->Release(); s.arena = nullptr; s.device = &n; s.used = 0; s.placed.clear(); s.failed = false; }
    const uint64_t key = content ^ (uint64_t(min) * 0x9E3779B97F4A7C15ull);
    if (const auto it = s.placed.find(key); it != s.placed.end()) { start = it->second.first; count = it->second.second; return true; }
    if (!s.arena) { if (s.failed) return false;
        if (FAILED(n.CreateIndexBuffer(kShellArena * 2, D3DUSAGE_WRITEONLY, D3DFMT_INDEX16, D3DPOOL_MANAGED, &s.arena)) || !s.arena) { s.arena = nullptr; s.failed = true; return false; } }
    std::vector<uint16_t> idx; idx.reserve(dr.kept * 3);
    for (size_t t = 0; t < dr.tris.size(); ++t) { if (!dr.keep[t]) continue;
        for (unsigned k = 0; k < 3; ++k) { const uint64_t v = uint64_t(dr.local[t * 3 + k]) + min; if (v > 0xffff) return false; idx.push_back(uint16_t(v)); } }
    if (idx.empty() || s.used + idx.size() > kShellArena) {
        if (!s.full_logged && !idx.empty()) { s.full_logged = true; session().write("{\"type\":\"grime_shell_arena_full\",\"used\":" + std::to_string(s.used) + "}"); }
        return false; }
    BYTE* data = nullptr;
    if (FAILED(s.arena->Lock(s.used * 2, UINT(idx.size() * 2), &data, 0)) || !data) return false;
    std::memcpy(data, idx.data(), idx.size() * 2); s.arena->Unlock();
    start = s.used; count = UINT(idx.size() / 3); s.used += UINT(idx.size()); s.placed.emplace(key, std::make_pair(start, count)); return true;
}
// The grime filter of a car-resource draw. bytes/local (vertex copy, indices relative to min) are needed only the first
// time a draw is seen in a race; without them an unknown draw returns nullptr ("read the geometry and ask again").
inline const Filter* shell_filter(Device8& d, uint64_t race, uint64_t key, const std::string& family, const std::vector<uint8_t>* bytes, unsigned stride,
                                  const std::vector<uint32_t>* local, UINT min, bool cabin_marker = false) noexcept {
    try {
        auto& s = shells(); if (s.race != race) { s.filters.clear(); s.race = race; }
        shell_step(d.trace.frame_number());
        auto it = s.filters.find(key);
        if (it == s.filters.end()) {
            if (!bytes || !local || stride < 12 || local->empty() || local->size() % 3 || local->size() > 3u * 65536u) return nullptr;
            if (s.filters.size() > 16384) s.filters.clear();
            Filter f; f.content = content_key(*bytes, stride, *local); f.family = family; f.min = min;
            auto& sh = s.families[family]; if (sh.first_frame == UINT64_MAX) sh.first_frame = d.trace.frame_number();
            auto& dr = sh.draws[f.content];
            if (dr.tris.empty()) {
                const size_t n = local->size() / 3; std::vector<grimeshell::Tri> tris(n);
                for (size_t t = 0; t < n; ++t) { grimeshell::Vec3* corner[3]{&tris[t].a, &tris[t].b, &tris[t].c};
                    for (unsigned k = 0; k < 3; ++k) { const size_t at = size_t((*local)[t * 3 + k]) * stride; if (at + 12 > bytes->size()) { sh.draws.erase(f.content); return nullptr; }
                        std::memcpy(corner[k]->data(), bytes->data() + at, 12); } }
                dr.tris = std::move(tris); dr.local = *local; dr.keep.assign(n, 1);
                if (cabin_marker) for (const auto& t : dr.tris) grimeshell::cabin_add(sh.cabin, t);
            }
            if (!sh.built && sh.collected_draws.insert(f.content).second) sh.collected.insert(sh.collected.end(), dr.tris.begin(), dr.tris.end());
            f.glass = grimeshell::glass_frame(dr.tris);   // G3: windscreen or not (used by Glass kinds only)
            it = s.filters.emplace(key, std::move(f)).first;
        }
        auto& f = it->second;
        if (f.state == FilterState::Waiting) {
            auto& sh = s.families[f.family]; const auto dr = sh.draws.find(f.content);
            if (dr == sh.draws.end()) f.state = FilterState::Full;
            else if (dr->second.done) {
                if (dr->second.kept == dr->second.tris.size()) f.state = FilterState::Full;
                else if (!dr->second.kept) f.state = FilterState::None;
                else f.state = shell_place(*d.native(), f.content, dr->second, f.min, f.start, f.count) ? FilterState::Subset : FilterState::Full;
            }
        }
        return &f;
    } catch (...) { return nullptr; }
}
// Applies a filter to the next candidate: false = no grime pass for this draw this frame.
inline bool apply_filter(Overlay::Candidate& c, const Filter* f) noexcept {
    c.subset = false; c.glass = {}; if (!f) return true;
    c.glass = f->glass;
    switch (f->state) { case FilterState::Full: return true; case FilterState::Subset: c.subset = true; c.sub_start = f->start; c.sub_count = f->count; return true; default: return false; }
}
inline void remember_car(uint64_t frame, uintptr_t instance, const D3DMATRIX& world, const std::string& family) noexcept {
    auto& o = overlay(); Overlay::FrameCar* slot = nullptr;
    for (auto& c : o.frame_cars) if (c.instance == instance) { slot = &c; break; }
    if (!slot) for (auto& c : o.frame_cars) if (c.frame != frame) { slot = &c; break; }
    if (!slot || (slot->frame == frame && slot->instance == instance)) return;
    slot->frame = frame; slot->instance = instance; slot->world = world; if (slot->family != family) slot->family = family;
}
inline const Overlay::FrameCar* match_car(uint64_t frame, const D3DMATRIX& world) noexcept {
    for (const auto& c : overlay().frame_cars) if (c.frame == frame && c.instance && !std::memcmp(&c.world, &world, sizeof(world))) return &c;
    return nullptr;
}
// Atmosphere body route, after an accepted car body draw was shaded: remember it for the post-draw pass.
// bytes = the draw's vertex copy (position first), stride 24/36. Roles: paint, panels, trim, flat underbody, wheel covers.
inline void note_body(Device8& d, uintptr_t instance, const D3DMATRIX& world, UINT min, UINT vertices, UINT start, UINT count,
                      const std::vector<uint8_t>& bytes, unsigned stride, uint64_t race_generation, unsigned kind = grimeoverlay::Body, const Filter* filter = nullptr) noexcept {
    if (!overlay_active() || !instance || !stride) return;
    auto& o = overlay();
    try {
        if (o.bounds_race != race_generation) { o.bounds.clear(); o.wheel_bounds.clear(); o.bounded.clear(); o.bounds_race = race_generation; }
        grimeoverlay::Vec3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f};
        for (size_t at = 0; at + 12 <= bytes.size(); at += stride) { float v[3]; std::memcpy(v, bytes.data() + at, 12);
            for (unsigned k = 0; k < 3; ++k) { lo[k] = std::min(lo[k], v[k]); hi[k] = std::max(hi[k], v[k]); } }
        if (!std::isfinite(lo[0] + lo[1] + lo[2] + hi[0] + hi[1] + hi[2]) || hi[0] < lo[0]) return;
        auto& map = grimeoverlay::kind_wheel(kind) ? o.wheel_bounds : o.bounds;
        if (map.size() > 64) map.clear();
        map[instance].add(lo, hi);
        Overlay::Candidate c; if (!apply_filter(c, filter)) return;
        c.frame = d.trace.frame_number(); c.min = min; c.vertices = vertices; c.start = start; c.count = count; c.instance = instance; c.world = world; c.kind = kind; o.cand = c;
    } catch (...) {}
}
// A blended / alpha-tested part of a car whose body bounds are already known (glass, lamps, grille, decals): no vertex copy.
inline void note_part(Device8& d, uintptr_t instance, const D3DMATRIX& world, UINT min, UINT vertices, UINT start, UINT count, unsigned kind, uint64_t race_generation,
                      const Filter* filter = nullptr) noexcept {
    if (!overlay_active() || !instance) return;
    auto& o = overlay(); const auto& map = grimeoverlay::kind_wheel(kind) ? o.wheel_bounds : o.bounds;
    if (o.bounds_race != race_generation || map.find(instance) == map.end()) return;
    Overlay::Candidate c; if (!apply_filter(c, filter)) return;
    c.frame = d.trace.frame_number(); c.min = min; c.vertices = vertices; c.start = start; c.count = count; c.instance = instance; c.world = world; c.kind = kind; o.cand = c;
}
// Managed textures with full mip chains (box filtered), created once.
inline bool overlay_textures(IDirect3DDevice8& n) noexcept {
    auto& o = overlay(); if (o.atlas && o.ramp) return true; if (o.textures_failed) return false;
    auto make = [&](unsigned w, unsigned h, bool mips, auto texel, IDirect3DTexture8*& out) -> bool {
        if (FAILED(n.CreateTexture(w, h, mips ? 0 : 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &out)) || !out) return false;
        std::vector<uint32_t> level(size_t(w) * h); for (unsigned y = 0; y < h; ++y) for (unsigned x = 0; x < w; ++x) level[size_t(y) * w + x] = texel(x, y);
        const DWORD count = out->GetLevelCount();
        for (DWORD l = 0; l < count; ++l) {
            D3DLOCKED_RECT r{}; if (FAILED(out->LockRect(l, &r, nullptr, 0))) return false;
            for (unsigned y = 0; y < h; ++y) std::memcpy(static_cast<uint8_t*>(r.pBits) + size_t(y) * r.Pitch, level.data() + size_t(y) * w, size_t(w) * 4);
            out->UnlockRect(l);
            if (w == 1 && h == 1) break;
            const unsigned nw = std::max(1u, w / 2), nh = std::max(1u, h / 2); std::vector<uint32_t> next(size_t(nw) * nh);
            for (unsigned y = 0; y < nh; ++y) for (unsigned x = 0; x < nw; ++x) { uint32_t sum[4]{};
                for (unsigned dy = 0; dy < 2; ++dy) for (unsigned dx = 0; dx < 2; ++dx) { const uint32_t t = level[size_t(std::min(h - 1, y * 2 + dy)) * w + std::min(w - 1, x * 2 + dx)];
                    for (unsigned c = 0; c < 4; ++c) sum[c] += (t >> (8 * c)) & 255; }
                uint32_t v = 0; for (unsigned c = 0; c < 4; ++c) v |= ((sum[c] + 2) / 4) << (8 * c); next[size_t(y) * nw + x] = v; }
            level.swap(next); w = nw; h = nh;
        }
        return true;
    };
    const bool ok = make(256, 256, true, [](unsigned x, unsigned y) { return grimeoverlay::atlas_texel(x, y, 256); }, o.atlas) &&
                    make(64, 32, false, [](unsigned x, unsigned y) { return grimeoverlay::ramp_texel(x, y, 64, 32); }, o.ramp);
    if (!ok) { if (o.atlas) { o.atlas->Release(); o.atlas = nullptr; } if (o.ramp) { o.ramp->Release(); o.ramp = nullptr; } o.textures_failed = true; }
    try { session().write(std::string("{\"type\":\"grime_overlay_textures\",\"ok\":") + (ok ? "true" : "false") + "}"); } catch (...) {}
    return ok;
}

} // namespace gfx2::grimeintegration
