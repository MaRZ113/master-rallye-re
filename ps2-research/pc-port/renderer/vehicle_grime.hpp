#pragma once
// R-SURFACE1 Vehicle Grime: portable core (no D3D, Windows or proxy types). Design: docs/r-surface1/DESIGN.md.
//
// G0 (this phase) is diagnostics only: it never changes a draw. The core holds
//  * the particle family table (level-0 BGRA SHA-256 of the retail DataGx/Particles/*.dxt payloads; the .dxt files
//    are a 20-byte 0xFEED header followed by raw BGRA, so the hash is reproducible offline),
//  * per-car exposure accumulation (particle triangle centroids attributed to the nearest car),
//  * the grime state model and its persistence store, keyed by the Master Rallye *mode* campaign (Broker
//    MasterRallye/* values saved in PlayerState.xml), with the Service Park wash entry point reserved.
// The renderer side (vehicle_grime_native.hpp) feeds it; tests/ps2_diag_tests.cpp covers it.
#include "ps2_diag.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace grime {

// ---- particle families ------------------------------------------------------------------------------------------------

enum class Family : uint8_t { Dust, Mud, Water, Grass, Stones, Tarmac, OtherKnown, Unknown, Count };
inline constexpr const char* family_name(Family f) noexcept {
    constexpr const char* names[] = {"dust", "mud", "water", "grass", "stones", "tarmac", "other_known", "unknown"};
    const auto i = static_cast<size_t>(f);
    return i < std::size(names) ? names[i] : "unknown";
}
inline constexpr size_t kFamilies = static_cast<size_t>(Family::Count);

struct TextureIdentity { const char* sha; Family family; const char* source; };
// GameParticles.xml: dirt_drive/dirt_drive_persist -> dirtdust2, mud_drive -> newmud, water_drive_front/rear ->
// watersplash3, grass_drive -> grassdirt, stones_drive -> brownstone, tarmac_skid -> smokey.
inline constexpr std::array<TextureIdentity, 15> kTextures{{
    {"6915b27bbcdfea7f9d41944c79d317cbee7b39bd21de7bfd28d79a81bc742817", Family::Dust, "particles/dirtdust2"},
    {"dbe6cf4f989c53cf7417f94c7c4f5c7f098dce0fa90e7e2b7f476da3ebbf61c5", Family::Dust, "particles/dirtdust"},
    {"1148f1725abd4d4ea5fdd0b346cf2cefa3b78d868511d7ae8a20bdb6544494ed", Family::Dust, "particles/dustcloud"},
    {"baff882864639929623c7c0f1fd376a768450709f178ad69385ad4b6a4a9f9ef", Family::Dust, "particles/grassdust"},
    {"294d44ef9e880c274d37b2d55fb6d3fde2aca90846f6b8ee2dc3d2e65ff32c0f", Family::Mud, "particles/newmud"},
    {"a6b0da3820b488926c850cc52a25f7cc6096c79899b905bcefe2ca8d74ef80f0", Family::Mud, "particles/mud"},
    {"de99dad6bc7df5371a004630c511741c7beffba3f8a18bb2243b6739df082ec4", Family::Water, "particles/watersplash3"},
    {"ca8905b205e19c654724deb6855a6b1b6f15e1f2d5eeb7dcc29f04a6d375ba1f", Family::Water, "particles/watersplash"},
    {"042ee5e9beecd5f0a190395aee1228ea9af2c55de416f21b65c4a46d51db56d2", Family::Grass, "particles/grassdirt"},
    {"984e3aea5ffce77e786dea5dcfc52ffbbf1668a733cffb237eabdf092d2ce092", Family::Stones, "particles/brownstone"},
    {"45e5d4d3c99c8e5536eb6b603ffe4513d1bc78ec3b6be9afc603842ad50592c9", Family::Stones, "particles/greystone"},
    {"3b590ad5fad1a18d93ee09cfbabb4b46f794c1a33352c0a015350143582ebda7", Family::Tarmac, "particles/smokey"},
    {"242a6e34d144d24aac616614bd3bf9fafcf5abc27b68c989ef2d2bcd7a56abfd", Family::OtherKnown, "particles/spark"},
    // All six misc/tracks/<surface>.dxt are byte-identical (black 16x16): tyre tracks prove contact, never the surface.
    {"9503245a0161a939de15c2414db2d336e761822fa6cff8136e4148f58f1f782e", Family::OtherKnown, "misc/tracks/*"},
    {"c5ce1fd2dc785143b8228f74c048ee9d9a30a0bee556c088b56f9a789e0a263a", Family::Dust, "particles/dusty2"},
}};
inline const TextureIdentity* identify(std::string_view sha) noexcept {
    for (const auto& t : kTextures) if (sha == t.sha) return &t;
    return nullptr;
}

// ---- per-car exposure -------------------------------------------------------------------------------------------------

struct CarSample { bool ok = false; std::array<float, 3> position{}; };
struct Exposure {
    // Per family: triangles, of them in front/rear half (by travel direction), low (< car centre height).
    std::array<uint32_t, kFamilies> triangles{}, front{}, rear{}, low{};
    std::array<uint32_t, kFamilies> left{}, right{};   // G2.1: side of the car relative to the travel direction
    std::array<double, kFamilies> alpha{};   // sum of mean vertex alpha (0..1) per triangle
    std::array<std::array<double, 3>, kFamilies> rgb{};   // G2.1: sum of particle colours (texture mean x vertex colour), 0..1
    void clear() noexcept { *this = {}; }
    bool empty() const noexcept { for (auto t : triangles) if (t) return false; return true; }
};
struct CarTrack {
    CarSample now{}, previous{};
    double previous_seconds = -1, speed = 0;
    std::array<float, 2> heading{0, 0};   // normalised XZ travel direction, zero when unknown
    Exposure window{}, race{};
};

// Attribute one particle triangle (world-space centroid) to the nearest car within radius; -1 when none.
inline int attribute(const std::array<CarTrack, 8>& cars, unsigned count, const std::array<float, 3>& c, float radius) noexcept {
    int best = -1; float best_d = radius * radius;
    for (unsigned i = 0; i < count && i < cars.size(); ++i) {
        const auto& car = cars[i];
        if (!car.now.ok) continue;
        const float dx = c[0] - car.now.position[0], dy = c[1] - car.now.position[1], dz = c[2] - car.now.position[2];
        const float d = dx * dx + dy * dy + dz * dz;
        if (d <= best_d) { best_d = d; best = int(i); }
    }
    return best;
}
// rgb: the particle colour (0..1), {-1,...} when unknown. MR world space is left-handed with y up, so the right-hand
// side of a car heading (hx, hz) is (hz, -hx).
inline void add(CarTrack& car, Family f, const std::array<float, 3>& c, float alpha, const std::array<float, 3>& rgb = {-1.f, -1.f, -1.f}) noexcept {
    const auto i = static_cast<size_t>(f);
    const float dx = c[0] - car.now.position[0], dz = c[2] - car.now.position[2];
    const float along = dx * car.heading[0] + dz * car.heading[1], across = dx * car.heading[1] - dz * car.heading[0];
    const bool heading = car.heading[0] != 0 || car.heading[1] != 0;
    for (Exposure* e : {&car.window, &car.race}) {
        ++e->triangles[i];
        if (heading) { (along >= 0 ? e->front : e->rear)[i] += 1; (across >= 0 ? e->right : e->left)[i] += 1; }
        if (c[1] < car.now.position[1]) ++e->low[i];
        e->alpha[i] += alpha;
        if (rgb[0] >= 0) for (unsigned k = 0; k < 3; ++k) e->rgb[i][k] += rgb[k];
    }
}
// Speed/heading from consecutive *distinct* Broker positions (Y is up in MR world space). The position is published at
// the physics rate, not per frame: repeated positions are not new samples (G0 smoke run showed 0 / inflated speeds).
inline void update_motion(CarTrack& car, const CarSample& s, double seconds) noexcept {
    if (car.now.ok && s.ok && s.position == car.now.position) return;
    if (car.now.ok && s.ok && car.previous_seconds >= 0 && seconds > car.previous_seconds) {
        const float dx = s.position[0] - car.now.position[0], dz = s.position[2] - car.now.position[2];
        const double dt = seconds - car.previous_seconds, dist = std::sqrt(double(dx) * dx + double(dz) * dz);
        if (dt < 2) {
            car.speed = dist / dt;
            if (dist > 0.05) car.heading = {float(dx / dist), float(dz / dist)};
        }
    }
    car.previous = car.now; car.now = s; car.previous_seconds = seconds;
}
inline std::string exposure_json(const Exposure& e) {
    std::string out = "{";
    bool first = true;
    for (size_t i = 0; i < kFamilies; ++i) {
        if (!e.triangles[i]) continue;
        if (!first) out += ",";
        first = false;
        out += ps2diag::quote(family_name(static_cast<Family>(i))) + ":{\"tri\":" + std::to_string(e.triangles[i]) +
               ",\"front\":" + std::to_string(e.front[i]) + ",\"rear\":" + std::to_string(e.rear[i]) + ",\"low\":" + std::to_string(e.low[i]) +
               ",\"alpha\":" + ps2diag::number(e.alpha[i] / e.triangles[i], 3) + "}";
    }
    return out + "}";
}

// ---- Master Rallye mode campaign identity -----------------------------------------------------------------------------
// Broker values of the in-game "Master Rallye" mode (DataGame/PlayerState.xml, SavePlayerState=True):
// MasterRallye/Stage, GameSaved, VehicleClass, DifficultyLevel, Car<i>/{CarID,DriverID,Player,TotalTime,RaceTime}, i<6.
struct MasterCar { bool ok = false; int car_id = -1, driver_id = -1; bool player = false; uint32_t total_time_bits = 0, race_time_bits = 0; };
struct MasterState {
    bool ok = false;           // Stage + VehicleClass readable
    int stage = -1, vehicle_class = -1, difficulty = -1; bool saved = false;
    std::array<MasterCar, 6> cars{};
    // Campaign = which drivers in which cars at which class/difficulty; stable through a whole campaign.
    std::string campaign() const {
        if (!ok) return {};
        std::string out = "c" + std::to_string(vehicle_class) + "d" + std::to_string(difficulty);
        for (const auto& c : cars) out += c.ok ? ("-" + std::to_string(c.car_id) + "." + std::to_string(c.driver_id) + (c.player ? "p" : "")) : "-x";
        return out;
    }
    // Checkpoint = the saved progress point inside a campaign: next stage index and the accumulated times. Exiting
    // and reloading a stage returns to the same checkpoint, so the stored grime of that checkpoint applies again.
    std::string checkpoint() const {
        if (!ok) return {};
        char tmp[16];
        std::string out = "s" + std::to_string(stage);
        for (const auto& c : cars) { std::snprintf(tmp, sizeof(tmp), "-%08x", c.ok ? c.total_time_bits : 0u); out += tmp; }
        return out;
    }
    std::string json() const {
        std::string out = "{\"ok\":" + std::string(ok ? "true" : "false") + ",\"stage\":" + std::to_string(stage) + ",\"vehicle_class\":" +
                          std::to_string(vehicle_class) + ",\"difficulty\":" + std::to_string(difficulty) + ",\"saved\":" + (saved ? "true" : "false") +
                          ",\"campaign\":" + ps2diag::quote(campaign()) + ",\"checkpoint\":" + ps2diag::quote(checkpoint()) + ",\"cars\":[";
        for (size_t i = 0; i < cars.size(); ++i) {
            const auto& c = cars[i]; float total = 0, race = 0; std::memcpy(&total, &c.total_time_bits, 4); std::memcpy(&race, &c.race_time_bits, 4);
            if (i) out += ",";
            out += "{\"ok\":" + std::string(c.ok ? "true" : "false") + ",\"car_id\":" + std::to_string(c.car_id) + ",\"driver_id\":" + std::to_string(c.driver_id) +
                   ",\"player\":" + (c.player ? "true" : "false") + ",\"total_time\":" + ps2diag::number(total, 3) + ",\"race_time\":" + ps2diag::number(race, 3) + "}";
        }
        return out + "]}";
    }
    bool operator==(const MasterState& o) const noexcept {
        if (ok != o.ok || stage != o.stage || vehicle_class != o.vehicle_class || difficulty != o.difficulty || saved != o.saved) return false;
        for (size_t i = 0; i < cars.size(); ++i) {
            const auto& a = cars[i]; const auto& b = o.cars[i];
            if (a.ok != b.ok || a.car_id != b.car_id || a.driver_id != b.driver_id || a.player != b.player || a.total_time_bits != b.total_time_bits ||
                a.race_time_bits != b.race_time_bits) return false;
        }
        return true;
    }
    bool operator!=(const MasterState& o) const noexcept { return !(*this == o); }
};

// A race belongs to the Master Rallye mode campaign only when every car of its field (Race/Car<N>/CarID + DriverID,
// readable slots only) matches a distinct MasterRallye/Car<i>, at least two cars are compared and the human car
// matches the campaign's player car. The campaign table has 6 slots; a 4-car Master Rallye field leaves slots 4..5
// as 0/0 (owner run 2026-11-12), so unused campaign slots are allowed. The match also gives the race->campaign
// order. Attract, Quick Race and cups use other car/driver pairs and do not match.
struct RaceCar { bool ok = false; int car_id = -1, driver_id = -1; bool human = false; };
struct MasterMatch { bool ok = false; std::array<int, 8> master_of_race{-1, -1, -1, -1, -1, -1, -1, -1}; };
inline MasterMatch match_master(const std::array<RaceCar, 8>& race, unsigned count, const MasterState& m) noexcept {
    MasterMatch r;
    if (!m.ok || !count || count > race.size()) return r;
    std::array<bool, 6> used{}; unsigned compared = 0; bool player_seen = false;
    for (unsigned i = 0; i < count; ++i) {
        if (!race[i].ok) continue;
        int found = -1;
        for (unsigned j = 0; j < m.cars.size(); ++j)
            if (!used[j] && m.cars[j].ok && m.cars[j].car_id == race[i].car_id && m.cars[j].driver_id == race[i].driver_id) { found = int(j); break; }
        if (found < 0) return r;
        if (race[i].human != m.cars[size_t(found)].player) return r;
        player_seen = player_seen || race[i].human;
        used[size_t(found)] = true; r.master_of_race[i] = found; ++compared;
    }
    r.ok = compared >= 2 && player_seen; return r;
}

// ---- grime state and persistence --------------------------------------------------------------------------------------

inline constexpr size_t kZones = 8;   // front-low, front-arch, side-low-left, side-low-right, rear-arch, rear, bonnet, roof
inline constexpr std::array<const char*, kZones> kZoneNames{"front_low", "front_arch", "side_low_l", "side_low_r", "rear_arch", "rear", "bonnet", "roof"};
struct CarGrime {
    std::array<float, kZones> dust{}, mud{}, wet{}, mud_age{};
    // G2.1: colour of the deposited dust and mud (0..1), taken from the particles that hit the car; {0,0,0} = unknown
    // (the configured tints apply). Not persisted.
    std::array<float, 3> dust_rgb{}, mud_rgb{};
    void clamp() noexcept {
        for (auto* a : {&dust, &mud, &wet}) for (auto& v : *a) v = std::isfinite(v) ? std::clamp(v, 0.f, 1.f) : 0.f;
        for (auto& v : mud_age) v = std::isfinite(v) ? std::max(v, 0.f) : 0.f;
        for (auto* c : {&dust_rgb, &mud_rgb}) for (auto& v : *c) v = std::isfinite(v) ? std::clamp(v, 0.f, 1.f) : 0.f;
    }
    // Service Park wash (reserved entry point, G4): fraction 1 = fully clean, partial washes keep the pattern.
    void wash(float fraction) noexcept {
        const float k = 1.f - std::clamp(std::isfinite(fraction) ? fraction : 0.f, 0.f, 1.f);
        for (size_t z = 0; z < kZones; ++z) { dust[z] *= k; mud[z] *= k; wet[z] = std::max(wet[z], 1.f - k); }
    }
    bool clean() const noexcept { for (size_t z = 0; z < kZones; ++z) if (dust[z] > 0 || mud[z] > 0 || wet[z] > 0) return false; return true; }
};
// Provisional G0 accumulation (dry run only; tuned in G2). Live particles are counted on every frame, so the input is
// the *intensity* = particle triangles near the car per frame (window triangles / window frames), integrated over time.
// Calibrated on the G0 smoke runs: a car inside a dense dust trail sees ~150-250 triangles per frame; that reaches
// ~85 % dust in about a minute (rate * intensity ~= .032 / s).
// G2.2 (owner review): grass was invisible -> grass builds up 3x faster (.00008 -> .00025) and deposits its own green
// colour (grass_rgb, [Look] GrassRGB) instead of the particle colour (grassdirt is brown).
struct Rates { float dust = .00016f, mud = .0004f, stones = .00012f, grass = .00025f, water_wet = .01f, water_wash = .003f, dry_seconds = 45.f;
               std::array<float, 3> grass_rgb{.34f, .42f, .18f}; };
// Per-zone direction weights from the depositing families (dust, mud, stones, grass) of one window.
inline std::array<float, kZones> direction_weights(const Exposure& e) noexcept {
    double front = 0, rear = 0, left = 0, right = 0;
    for (auto f : {Family::Dust, Family::Mud, Family::Stones, Family::Grass}) { const auto i = static_cast<size_t>(f); front += e.front[i]; rear += e.rear[i]; left += e.left[i]; right += e.right[i]; }
    const float fr = front + rear > 0 ? float(front / (front + rear)) : .5f, rs = left + right > 0 ? float(right / (left + right)) : .5f;
    //                     front_low   front_arch  side_l        side_r       rear_arch     rear          bonnet      roof
    return {.5f + fr, .5f + fr, 1.5f - rs, .5f + rs, 1.5f - fr, 1.5f - fr, .5f + fr, 1.f};
}
inline void accumulate(CarGrime& g, const Exposure& e, double seconds, double frames, const Rates& r = {}) noexcept {
    const float dt = float(std::clamp(seconds, 0.0, 2.0)), inv = frames >= 1 ? float(1.0 / frames) : 0.f;
    auto n = [&](Family f) { return float(e.triangles[static_cast<size_t>(f)]) * inv; };
    auto low = [&](Family f) { const auto i = static_cast<size_t>(f); return e.triangles[i] ? float(e.low[i]) / float(e.triangles[i]) : 0.f; };
    const float dust = (n(Family::Dust) * r.dust + n(Family::Stones) * r.stones * .5f) * dt;
    const float mud = (n(Family::Mud) * r.mud + n(Family::Grass) * r.grass + n(Family::Stones) * r.stones * .5f) * dt;
    const float water = n(Family::Water);
    // Zone weights: lower body and arches first, roof last (G3.2: bonnet .25 -> .4, roof .1 -> .2, so a long dusty stage
    // reaches the top of the car too).
    constexpr std::array<float, kZones> lower{1.f, 1.f, .9f, .9f, 1.f, .8f, .4f, .2f};
    const float low_share = std::max(low(Family::Mud), low(Family::Dust));
    // G2.1: where the particles were relative to the car. Particles ahead (another car's trail) dirty the front, the
    // own trail the rear; one side more than the other. Weights .5..1.5 around 1 (no particles -> 1).
    const auto dir = direction_weights(e);
    for (size_t z = 0; z < kZones; ++z) {
        const float w = lower[z] * dir[z] * (z >= 6 ? 1.f - .5f * low_share : 1.f);
        g.dust[z] += (1.f - g.dust[z]) * std::min(1.f, dust * w);
        g.mud[z] += (1.f - g.mud[z]) * std::min(1.f, mud * w);
        if (mud * w > 0) g.mud_age[z] = 0;
        if (water > 0) {
            g.wet[z] = std::min(1.f, g.wet[z] + water * r.water_wet * lower[z] * dt);
            const float wash = std::min(1.f, water * r.water_wash * lower[z] * dt);
            g.mud[z] *= 1.f - wash; g.dust[z] *= 1.f - std::min(1.f, 1.5f * wash);
        }
    }
    const float dry = r.dry_seconds > 0 ? std::exp(-dt / r.dry_seconds) : 1.f;
    for (size_t z = 0; z < kZones; ++z) { g.wet[z] *= water > 0 ? 1.f : dry; g.mud_age[z] += dt; }
    // G2.1: deposit colour. The new particles' mean colour blends in by the share of grime they added.
    auto mix_colour = [&](std::array<float, 3>& into, std::initializer_list<Family> fams, float added, float total) {
        double sum[3]{}, count = 0;
        for (auto f : fams) { const auto i = static_cast<size_t>(f);
            for (unsigned k = 0; k < 3; ++k) sum[k] += f == Family::Grass ? double(r.grass_rgb[k]) * e.triangles[i] * 3.0 : e.rgb[i][k];   // grass x3: matches its rate
            count += f == Family::Grass ? e.triangles[i] * 3.0 : e.triangles[i]; }
        if (count <= 0 || added <= 0 || !(sum[0] + sum[1] + sum[2] > 0)) return;
        const float k = into[0] + into[1] + into[2] > 0 ? std::clamp(added / std::max(total, 1e-4f), 0.f, 1.f) : 1.f;
        for (unsigned c = 0; c < 3; ++c) into[c] += (float(sum[c] / count) - into[c]) * k;
    };
    float dust_total = 0, mud_total = 0; for (size_t z = 0; z < kZones; ++z) { dust_total += g.dust[z]; mud_total += g.mud[z]; }
    mix_colour(g.dust_rgb, {Family::Dust, Family::Stones}, dust * kZones, dust_total);
    mix_colour(g.mud_rgb, {Family::Mud, Family::Grass, Family::Stones}, mud * kZones, mud_total);
    g.clamp();
}
// G2: Quick Race / attract start state: a light dust film, lower body first (same zone weights as accumulate()).
inline CarGrime start_state(float level) noexcept {
    CarGrime g; constexpr std::array<float, kZones> lower{1.f, 1.f, .9f, .9f, 1.f, .8f, .4f, .2f};
    for (size_t z = 0; z < kZones; ++z) g.dust[z] = std::isfinite(level) ? std::clamp(level * lower[z], 0.f, 1.f) : 0.f;
    return g;
}
inline std::string grime_json(const CarGrime& g) {
    auto arr = [](const std::array<float, kZones>& a) { std::string o = "["; for (size_t z = 0; z < kZones; ++z) o += (z ? "," : "") + ps2diag::number(a[z], 3); return o + "]"; };
    return "{\"dust\":" + arr(g.dust) + ",\"mud\":" + arr(g.mud) + ",\"wet\":" + arr(g.wet) + "}";
}

// One persisted line per (campaign, checkpoint): "<campaign>|<checkpoint>|<car>|d0..d7|m0..m7|w0..w7|a0..a7".
// Plain text on purpose: line-oriented, append/replace without a JSON parser, and readable by a future Service tool.
struct Snapshot { std::string campaign, checkpoint; std::array<CarGrime, 6> cars{}; std::array<bool, 6> present{}; };
class Store {
public:
    static constexpr const char* kHeader = "# mr-vehicle-grime-store/1";
    void put(const Snapshot& s) {
        auto& slot = snapshots_[s.campaign + "|" + s.checkpoint];
        slot = s;
    }
    const Snapshot* find(const std::string& campaign, const std::string& checkpoint) const noexcept {
        const auto it = snapshots_.find(campaign + "|" + checkpoint);
        return it == snapshots_.end() ? nullptr : &it->second;
    }
    // Keep only the newest campaigns' history bounded (a campaign has at most ~30 checkpoints).
    void trim(size_t limit = 512) { while (snapshots_.size() > limit) snapshots_.erase(snapshots_.begin()); }
    size_t size() const noexcept { return snapshots_.size(); }
    std::string serialize() const {
        std::string out = std::string(kHeader) + "\n";
        char tmp[24];
        for (const auto& [key, s] : snapshots_) {
            for (size_t c = 0; c < s.cars.size(); ++c) {
                if (!s.present[c]) continue;
                out += s.campaign + "|" + s.checkpoint + "|" + std::to_string(c);
                for (const auto* a : {&s.cars[c].dust, &s.cars[c].mud, &s.cars[c].wet, &s.cars[c].mud_age}) {
                    out += "|";
                    for (size_t z = 0; z < kZones; ++z) { std::snprintf(tmp, sizeof(tmp), z ? ",%.4f" : "%.4f", (*a)[z]); out += tmp; }
                }
                out += "\n";
            }
        }
        return out;
    }
    // Malformed lines are skipped (never fatal); returns the number of accepted car records.
    size_t parse(std::string_view text) {
        snapshots_.clear(); size_t accepted = 0;
        std::istringstream in{std::string(text)}; std::string line;
        bool header = false;
        while (std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (line == kHeader) { header = true; continue; }
            if (!header || line.empty() || line[0] == '#') continue;
            std::vector<std::string> f; size_t at = 0;
            while (true) { const auto bar = line.find('|', at); f.push_back(line.substr(at, bar - at)); if (bar == std::string::npos) break; at = bar + 1; }
            if (f.size() != 7 || f[0].empty() || f[1].empty() || f[2].size() != 1 || f[2][0] < '0' || f[2][0] > '5') continue;
            CarGrime g; bool ok = true;
            std::array<std::array<float, kZones>*, 4> arrays{&g.dust, &g.mud, &g.wet, &g.mud_age};
            for (size_t k = 0; k < 4 && ok; ++k) {
                std::istringstream values(f[3 + k]); std::string v; size_t z = 0;
                while (std::getline(values, v, ',')) {
                    if (z >= kZones) { ok = false; break; }
                    char* end = nullptr; const float x = std::strtof(v.c_str(), &end);
                    if (!end || *end || !std::isfinite(x)) { ok = false; break; }
                    (*arrays[k])[z++] = x;
                }
                ok = ok && z == kZones;
            }
            if (!ok) continue;
            g.clamp();
            auto& s = snapshots_[f[0] + "|" + f[1]]; s.campaign = f[0]; s.checkpoint = f[1];
            const size_t car = size_t(f[2][0] - '0'); s.cars[car] = g; s.present[car] = true; ++accepted;
        }
        return accepted;
    }
private:
    std::map<std::string, Snapshot> snapshots_;
};

// Lifecycle of the Master Rallye mode as seen by the renderer: the game returns to the stage menu after each race
// (next-stage preview, setup) and the race starts from a menu button; PlayerState.xml is written when progress is
// saved. A finished race leaves a *pending* end state; it is bound to the first new checkpoint observed afterwards.
class CampaignTracker {
public:
    struct Event { const char* kind = nullptr; std::string campaign, checkpoint; };
    // Race end inside the Master Rallye mode: remember the end-of-stage grime for the next checkpoint.
    void race_finished(const MasterState& at_finish, const Snapshot& end) { pending_ = end; pending_from_ = at_finish.checkpoint(); pending_valid_ = at_finish.ok; }
    // Called whenever MasterRallye/* values change (menus included). Returns the event that the change caused.
    Event observe(const MasterState& s, Store& store) {
        Event e;
        if (!s.ok) return e;
        e.campaign = s.campaign(); e.checkpoint = s.checkpoint();
        if (pending_valid_ && e.checkpoint != pending_from_ && e.campaign == pending_.campaign) {
            Snapshot bound = pending_; bound.checkpoint = e.checkpoint; store.put(bound); store.trim();
            pending_valid_ = false; e.kind = "checkpoint_bound";
        }
        return e;
    }
    // Race start: grime to apply for the current checkpoint (nullptr = start clean).
    const Snapshot* start(const MasterState& s, const Store& store) const noexcept { return s.ok ? store.find(s.campaign(), s.checkpoint()) : nullptr; }
    bool pending() const noexcept { return pending_valid_; }
private:
    Snapshot pending_{}; std::string pending_from_; bool pending_valid_ = false;
};

} // namespace grime
