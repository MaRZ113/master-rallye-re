#pragma once
// COURSE-ALIVE2: the PS2 gaAnimals_BirdManager (SLES_509.06 vtable 473c10) as portable C++ (no D3D, Windows or proxy
// types). Same operation order and float32 rounding as the reference tools/ps2_bird_model.py (built on the AMBIENT2
// primitives of ps2-research/tools/bird_runtime.py); tests/ps2_birds_tests.cpp and tools/verify_ps2_birds.py compare them.
//
// One tick() = one game tick (dispatch 21f088, 30 per second as for splines and water). Recovered contract
// (docs/course-alive2/README.md):
// * Manager update 1af330 runs only when BOTH its MarkerList pointers resolve (FlightList and MillList of the course
//   scene; the registry is cleared at every scene teardown 2a1ea8 -> 1fda80). 26 of the 36 PS2 courses have no MillList,
//   so no bird ever flies there on the PS2.
// * Observer = camera position (camera manager 201350 entry 0, +c0..c8 = camera world translation).
// * Burst 1afa20, retirement 1b0238, one pending conversion 1affe0 per tick, carrier -> en2d copy 1b0508; the ground
//   (Miller) population producers 1af770/1aff58 have no reference in the ELF, so the ground vector stays empty.
// * FlyBird init 1b0a40 (six draws) / step 1b0e68; ImageBankSwitcher 1b17e8: key 0..2, next key after every 5 ticks.
// * Global RNG 1d5df0: Schrage 48271 mod 2^31-1, output = low 24 bits * 2^-24.
// * Render 337a98/330530: Y-locked billboard from the view matrix row 2, scale 0.1, local (vx-0.5, 0.5-vy).
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace ps2birds {

using Vec3 = std::array<float, 3>;
inline constexpr size_t kPool = 16;               // constructor +34; no Animals/MaxBirds producer exists
inline constexpr uint32_t kSeed = 12345;          // 1d5de0 constructor seed (in-race global state is unknown)
inline constexpr float kScale = 0.1f;             // 1af460 en2d uniform scale
inline constexpr size_t kMaxPoints = 256;

// 1d5df0 / 1d5e70 / 1d5eb0.
class Rng {
    uint32_t state_ = kSeed;
public:
    explicit Rng(uint32_t s = kSeed) noexcept : state_(s) {}
    uint32_t state() const noexcept { return state_; }
    float unit() noexcept {
        const int32_t s = static_cast<int32_t>(state_);
        const int32_t q = s / 44488;               // truncation toward zero, as DIV
        const int32_t r = s - q * 44488;
        int32_t v = static_cast<int32_t>(static_cast<uint32_t>(r) * 48271u - static_cast<uint32_t>(q) * 3399u);
        if (v <= 0) v = static_cast<int32_t>(static_cast<uint32_t>(v) + 2147483647u);
        state_ = static_cast<uint32_t>(v);
        return static_cast<float>(state_ & 0x00ffffffu) * (1.0f / 16777216.0f);
    }
    float real(float lo, float hi) noexcept { const float u = unit(); return lo + u * (hi - lo); }
    int32_t integer(int32_t lo, int32_t hi) noexcept {
        const float u = unit() * static_cast<float>(hi - lo);
        const int32_t v = lo + static_cast<int32_t>(std::floor(u));
        return v == hi ? lo : v;
    }
};

inline Vec3 normalized(const Vec3& v) noexcept {
    const float n2 = (v[0] * v[0] + v[1] * v[1]) + v[2] * v[2];
    if (n2 <= 1.0f / 8388608.0f) return {0.f, 0.f, 0.f};
    const float inv = 1.f / static_cast<float>(std::sqrt(static_cast<double>(n2)));
    return {v[0] * inv, v[1] * inv, v[2] * inv};
}

// FlyBird (0x30, vtable 473bd0).
struct FlyBird {
    Vec3 origin{}, direction{0.f, 0.f, 1.f};
    float unused24 = 100.f, speed = 15.f, travel = 0.f;
    void initialize(const Vec3& camera, Rng& rng) noexcept {  // 1b0a40
        speed = speed + rng.real(0.f, 15.f);
        const float t = rng.real(0.f, 60.f);
        unused24 = rng.unit() > .5f ? unused24 + t : unused24 - t;
        const Vec3 w = normalized({camera[0] - origin[0], 0.f, camera[2] - origin[2]});
        const float mix = rng.real(0.f, .12f);
        const float lateral = rng.unit() > .5f ? mix : -mix;
        const float away = -(1.f - mix);
        const float x = w[0] * away + w[2] * lateral;
        const float z = w[2] * away + (-w[0]) * lateral;
        direction = normalized({x, rng.real(.001f, .2f), z});
        travel = 0.f;
    }
    Vec3 step(Rng& rng) noexcept {  // 1b0e68 + 1b0f88
        if (direction[1] < .35f) direction[1] = direction[1] + rng.real(.001f, .05f) / 30.f;
        speed = speed + rng.real(.1f, 2.5f) / 30.f;
        travel = travel + speed / 30.f;
        return {origin[0] + direction[0] * travel, origin[1] + direction[1] * travel, origin[2] + direction[2] * travel};
    }
};

// gaImageBankSwitcher (0x20, vtable 473210): first 0, last 2, threshold 3.
struct BankSwitcher {
    int32_t key = 0, counter = 0;
    void step() noexcept {
        if (3 < counter) { counter = 0; if (++key > 2) key = 0; }
        else ++counter;
    }
};

struct CourseConfig {
    std::vector<Vec3> flight;     // FlightList in source order
    bool flight_present = false;  // the named list exists in the scene (may be empty)
    bool mill_present = false;
    float min_fly = 0.f, max_fly = 0.f;
    int32_t rnd_fly = 0;          // <=10 after 1af0b0
    bool gate() const noexcept { return flight_present && mill_present; }
};

struct Entity {
    Vec3 carrier{}, en2d{};
    FlyBird bird;
    BankSwitcher sw;
    bool flying = false;          // FlyBird + switcher attached (slots 0/1), en2d drawn
};

struct BirdView { size_t entity; Vec3 position; int32_t key; };

class Manager {
    CourseConfig config_;
    Rng rng_;
    std::array<Entity, kPool> e_{};
    std::vector<size_t> free_, flying_, pending_;
    float clock_ = 0.f;
    int32_t cache_ = -1;
    Vec3 observer_{};
    uint64_t ticks_ = 0;
    bool ignore_gate_ = false;

    float xz2(const Vec3& p) const noexcept {
        const float dx = p[0] - observer_[0], dz = p[2] - observer_[2];
        return (dx * dx + 0.f) + dz * dz;
    }
    // 1b0878 / 1b0780.
    int32_t nearest() const noexcept {
        const auto& pts = config_.flight;
        const int32_t n = static_cast<int32_t>(pts.size());
        int32_t lo = 0, hi = n, best = 0;
        if (cache_ != -1) { lo = cache_ - 5 < 0 ? 0 : cache_ - 5; hi = cache_ + 5 < n ? cache_ + 5 : n; best = cache_; }
        float d = 3.4028234663852886e+38f;
        for (int32_t i = lo; i < hi; ++i) {
            const float dx = pts[static_cast<size_t>(i)][0] - observer_[0], dz = pts[static_cast<size_t>(i)][2] - observer_[2];
            const float v = (dx * dx + 0.f) + dz * dz;
            if (v < d) { best = i; d = v; }
        }
        return best;
    }
    void burst() noexcept {  // 1afa20
        const auto& pts = config_.flight;
        if (free_.empty() || !config_.flight_present || pts.empty()) return;
        const float u = rng_.real(.1f, 1.f);
        clock_ = clock_ + .003f;
        if (!(u < clock_ * .1f)) return;
        clock_ = 0.f;
        int32_t n = rng_.integer(0, config_.rnd_fly);
        if (static_cast<uint32_t>(n) > free_.size()) n = static_cast<int32_t>(free_.size());
        if (n <= 0) return;
        const int32_t base = nearest();  // 1b06d8
        cache_ = base;
        int32_t idx = base + rng_.integer(0, 3);
        if (idx < 0) idx = 0;
        if (idx > static_cast<int32_t>(pts.size()) - 1) idx = static_cast<int32_t>(pts.size()) - 1;
        const Vec3 p = pts[static_cast<size_t>(idx)];
        const float dx = p[0] - observer_[0], dy = p[1] - p[1], dz = p[2] - observer_[2];
        const float d2 = (dx * dx + dy * dy) + dz * dz;
        if (!(config_.min_fly * config_.min_fly < d2 && d2 < config_.max_fly * config_.max_fly)) return;
        for (int32_t i = 0; i < n; ++i) {
            const size_t e = free_.back(); free_.pop_back();
            e_[e].carrier = p;
            pending_.insert(pending_.begin(), e);
        }
    }
    void retire() noexcept {  // 1b0238
        const float limit = config_.max_fly * config_.max_fly;
        for (size_t i = 0; i < flying_.size();) {
            const size_t e = flying_[i];
            if (limit < xz2(e_[e].carrier)) {
                e_[e].flying = false; e_[e].carrier = {}; e_[e].sw = {};
                free_.push_back(e);
                flying_.erase(flying_.begin() + static_cast<std::ptrdiff_t>(i));
            } else ++i;
        }
    }
    void convert(const Vec3& camera) noexcept {  // 1affe0 -> 1b0138 / 1b0410 / 1b0a40
        if (pending_.empty()) return;
        const size_t e = pending_.back(); pending_.pop_back();
        auto& x = e_[e];
        x.bird = FlyBird{};
        x.bird.origin = x.carrier;
        x.sw = BankSwitcher{};
        x.flying = true;
        x.bird.initialize(camera, rng_);
        x.carrier = x.bird.origin;
        flying_.push_back(e);
    }

public:
    // ignore_gate: DIAGNOSTIC only (PS2Birds diagnostics key); the PS2 never ignores the MillList gate.
    bool start(const CourseConfig& c, bool ignore_gate = false, uint32_t seed = kSeed) noexcept {
        try {
            config_ = c; rng_ = Rng(seed); e_ = {}; clock_ = 0.f; cache_ = -1; observer_ = {}; ticks_ = 0; ignore_gate_ = ignore_gate;
            free_.clear(); flying_.clear(); pending_.clear();
            free_.reserve(kPool); flying_.reserve(kPool); pending_.reserve(kPool);
            for (size_t i = 0; i < kPool; ++i) free_.push_back(i);
            return config_.flight.size() <= kMaxPoints;
        } catch (...) { return false; }
    }
    bool active() const noexcept { return config_.gate() || (ignore_gate_ && config_.flight_present); }
    uint64_t ticks() const noexcept { return ticks_; }
    const Rng& rng() const noexcept { return rng_; }
    size_t flying_count() const noexcept { return flying_.size(); }
    size_t pending_count() const noexcept { return pending_.size(); }
    size_t free_count() const noexcept { return free_.size(); }
    float clock() const noexcept { return clock_; }
    int32_t cache() const noexcept { return cache_; }
    const Entity& entity(size_t i) const noexcept { return e_[i]; }

    void tick(const Vec3& camera) noexcept {
        ++ticks_;
        if (active()) {
            observer_ = camera;
            burst();
            retire();
            convert(camera);
            for (size_t e : flying_) e_[e].en2d = e_[e].carrier;
        }
        for (auto& x : e_)  // birds, pool order, after their manager
            if (x.flying) { x.carrier = x.bird.step(rng_); x.sw.step(); }
    }
    // Flying birds in entity order with their drawn en2d translation and image key.
    void snapshot(std::vector<BirdView>& out) const {
        out.clear();
        for (size_t i = 0; i < kPool; ++i)
            if (e_[i].flying) out.push_back({i, e_[i].en2d, e_[i].sw.key});
    }
};

// ---- render geometry (337a98 + 330530 + 36fc18) ----------------------------------------------------------------------

// Camera side as the PS2 view builder makes it: normalize(look x up), DAT_00435e88 = 1 (not negated).
inline Vec3 camera_side(const Vec3& look, const Vec3& up) noexcept {
    const Vec3 s{look[1] * up[2] - look[2] * up[1], look[2] * up[0] - look[0] * up[2], look[0] * up[1] - look[1] * up[0]};
    const float n2 = (s[0] * s[0] + s[1] * s[1]) + s[2] * s[2];
    if (n2 <= 1.1920929e-07f) return {0.f, 0.f, 0.f};
    const float r = 1.f / static_cast<float>(std::sqrt(static_cast<double>(n2)));
    return {s[0] * r, s[1] * r, s[2] * r};
}
// Billboard rows R and U (scaled). View row 2 = (side.z, up.z, look.z); F = (row2.x, 0, row2.z), not normalised.
struct Billboard { Vec3 r{}, u{}; };
inline Billboard billboard(const Vec3& side, const Vec3& look) noexcept {
    float fx = side[2], fz = look[2];
    const float eps = 1.1920929e-6f;
    if (-eps <= fx && fx <= eps && -eps <= fz && fz <= eps) fx = 1.f;
    return {Vec3{fz * kScale, 0.f, -fx * kScale}, Vec3{0.f, kScale, 0.f}};
}
inline Vec3 world_vertex(const Vec3& t, const Billboard& b, float vx, float vy) noexcept {
    const float lx = -.5f + vx, ly = .5f - vy;
    return {(lx * b.r[0] + ly * b.u[0]) + t[0], (lx * b.r[1] + ly * b.u[1]) + t[1], (lx * b.r[2] + ly * b.u[2]) + t[2]};
}

}  // namespace ps2birds
