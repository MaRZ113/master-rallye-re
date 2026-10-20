#pragma once
// COURSE-ALIVE1: the PS2 gaEntitySpline controller (SLES_509.06 owner vtable 473b10) as portable C++.
//
// No D3D, Windows or proxy types: the PS2 PC-port proxy can take this header as it is. Every operation follows
// the AMBIENT1 contract (ps2-research/ambient1/) in the order of the reference reconstruction
// ps2-research/tools/spline_runtime.py, in IEEE float32, so both give the same bits (tests/spline_motion_tests.cpp
// and tests/test_spline_objects.py compare them):
// * prep 1a8330: N controls, cumulative knot times; Const=True: chord/speed per span and a closing chord time that is
//   kept also on open routes; Const=False: equal time (L/speed)/N per span (L adds the closing chord only if closed);
// * eval 1a9498: x = i + (t-Ti)/(Ti+1-Ti), uniform Catmull-Rom basis in the original operation order, controls clamped
//   (open) or modulo N (closed); the weight cache compares the global x with the stored local u (kept as in the ELF);
// * forward 1a9e08: normalised displacement with the two small-vector tests; up 1a9fd0: bank angle moving average over
//   Number Of Samples, only up is rotated; right 1aa2e0: (F.z, F.y, -F.x), no cross product;
// * tick 1a80e8: Car0 XZ distance, strict squared hysteresis, ring index, evaluate, publish, then 1aa3b8 advance by
//   float32 1/30 with closed wrap to 0, open clamp, open rest counter.
// Cadence (not in the owner): 30 invocations per second. PS2 draws every 50 Hz field with interpolated poses (Egg
// "en3d Interpolated"), but the game state advances about 30 times a second: the Spain_S2 red dinghy moves ~0.6 ticks
// per field and the 316808 frame counter steps 11 times in 18 fields (docs/course-water1/README.md, owner GS dumps),
// matching the owner's 1/30 per invocation (route time in seconds). SplineClock turns host seconds into these ticks.
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <vector>

namespace ps2spline {

using Vec3 = std::array<float, 3>;

inline constexpr float kTickIncrement = 1.f / 30.f;   // 0x3d088889, owner +64
inline constexpr double kTicksPerSecond = 30.0;         // PS2 game ticks (one dispatch each), see above
inline constexpr float kPi = 3.14159265358979323846f;   // 0x40490fdb (15acb0)
inline constexpr size_t kMaxPoints = 64;
inline constexpr int kMaxSamples = 100000;

struct Config {
    bool const_speed = false, loop = false, trigger = false, rest = false;
    float speed = 0.f, on = 0.f, off = 0.f, banking = 0.f;
    int32_t rest_ticks = 0;   // Rest Time (sec) * 30, signed low 32 bits (config 1a7dc8)
    int32_t samples = 0;      // Number Of Samples (bank history ring)
};

// Diagnostic domain of the reference tool (not PS2 clamps): finite, speed > 0.0001, 1..100000 samples, 4..64 points,
// no repeated adjacent point.
inline bool finite(float v) noexcept { return std::isfinite(v); }
inline float fsqrt(float v) noexcept { return static_cast<float>(std::sqrt(static_cast<double>(v))); }
inline float dot(const Vec3& a, const Vec3& b) noexcept { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
inline Vec3 sub(const Vec3& a, const Vec3& b) noexcept { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
inline float norm(const Vec3& a) noexcept { return fsqrt(dot(a, a)); }

// 001a9ccc..001a9d1c basis weights, original scalar operation order.
inline std::array<float, 4> weights(float u) noexcept {
    const float h = u * .5f, a = h * u, b = a * u, d = a + a, e = d + d, c = b * 3.f;
    return {(-b + d) - h, (c - (e + a)) + 1.f, (-c + e) + h, b - a};
}

// 001a9e08: secant forward with the original small-vector fallbacks.
inline Vec3 forward(const Vec3& now, const Vec3& old, const Vec3& previous) noexcept {
    const Vec3 d = sub(now, old);
    const float eps = .0001f;
    if (std::fabs(d[0]) <= eps && std::fabs(d[1]) <= eps && std::fabs(d[2]) <= eps) return previous;
    const float l2 = dot(d, d);
    if (l2 <= 1.f / 8388608.f) return previous;  // 2^-23
    const float r = 1.f / fsqrt(l2);
    const Vec3 v{d[0] * r, d[1] * r, d[2] * r};
    return dot(v, v) < eps ? previous : v;
}

class Path {
    std::vector<Vec3> points_;
    std::vector<float> knots_;
    float closing_ = 0.f, duration_ = 0.f;
    bool loop_ = false, valid_ = false;
    bool cache_valid_ = false;
    float cached_local_ = 0.f;
    std::array<float, 4> cached_weights_{};

public:
    Path() = default;
    // 001a8330 preparation. Returns false outside the supported domain (no guessed repair).
    bool prepare(const Vec3* points, size_t count, const Config& c) noexcept {
        valid_ = false;
        points_.clear();
        knots_.clear();
        cache_valid_ = false;
        if (!points || count < 4 || count > kMaxPoints || !finite(c.speed) || !(c.speed > .0001f)) return false;
        try {
            points_.assign(points, points + count);
            for (const auto& p : points_) for (float v : p) if (!finite(v)) return false;
            std::vector<float> lengths;
            for (size_t i = 1; i < count; ++i) {
                const float d = norm(sub(points_[i], points_[i - 1]));
                if (!(d != 0.f) || !finite(d)) return false;
                lengths.push_back(d);
            }
            const float closing = norm(sub(points_[0], points_[count - 1]));
            std::vector<float> intervals;
            if (c.const_speed) {
                for (float d : lengths) intervals.push_back(d / c.speed);
                closing_ = closing / c.speed;  // 001a8694..001a869c: also for an OPEN constant-speed route
            } else {
                float total = 0.f;
                for (float d : lengths) total = total + d;
                if (c.loop) total = total + closing;
                const float interval = (total / c.speed) / static_cast<float>(count);
                intervals.assign(count - 1, interval);
                closing_ = c.loop ? interval : 0.f;
            }
            knots_.push_back(0.f);
            for (float d : intervals) knots_.push_back(knots_.back() + d);
            duration_ = knots_.back() + closing_;
            for (float k : knots_) if (!finite(k)) return false;
            if (!(duration_ > 0.f) || !finite(duration_)) return false;
            loop_ = c.loop;
            valid_ = true;
            return true;
        } catch (...) {
            points_.clear();
            knots_.clear();
            return false;
        }
    }
    bool valid() const noexcept { return valid_; }
    float duration() const noexcept { return duration_; }
    float closing_time() const noexcept { return closing_; }
    const std::vector<float>& knots() const noexcept { return knots_; }
    const std::vector<Vec3>& points() const noexcept { return points_; }

    // 001a9498. Time must be finite and >= 0 (the controller never produces anything else).
    Vec3 evaluate(float t) noexcept {
        const size_t n = points_.size();
        if (!valid_ || !(t >= 0.f)) return points_.empty() ? Vec3{} : points_[0];
        if (loop_) {
            for (int guard = 0; t >= duration_ && guard < 100000; ++guard) t = t - duration_;
        } else if (t > knots_.back()) {
            t = knots_.back();
        }
        size_t segment = n - 1;
        for (size_t i = 0; i + 1 < knots_.size(); ++i)
            if (t < knots_[i + 1]) { segment = i; break; }
        const float start = knots_[segment];
        const float end = (segment == n - 1 && loop_) ? start + closing_ : knots_[segment + 1 < n ? segment + 1 : n - 1];
        const float coordinate = end != start ? static_cast<float>(segment) + (t - start) / (end - start)
                                              : static_cast<float>(segment);
        const long index = static_cast<long>(std::floor(coordinate));
        const float local = coordinate - static_cast<float>(index);
        // The ELF compares the global coordinate with the cached LOCAL value; closed evaluation clears the cache.
        if (loop_ || !cache_valid_ || cached_local_ != coordinate) {
            cached_weights_ = weights(local);
            cached_local_ = local;
            cache_valid_ = true;
        }
        const auto& w = cached_weights_;
        auto point = [&](long i) -> const Vec3& {
            const long count = static_cast<long>(n);
            if (loop_) return points_[static_cast<size_t>(((i % count) + count) % count)];
            return points_[static_cast<size_t>(i < 0 ? 0 : (i > count - 1 ? count - 1 : i))];
        };
        const Vec3* c[4] = {&point(index - 1), &point(index), &point(index + 1), &point(index + 2)};
        Vec3 out{};
        for (int axis = 0; axis < 3; ++axis) {
            float q = (*c[0])[axis] * w[0];
            q = q + (*c[1])[axis] * w[1];
            q = q + (*c[2])[axis] * w[2];
            q = q + (*c[3])[axis] * w[3];
            out[axis] = q;
        }
        return out;
    }
};

// Published pose: row-vector affine world matrix, world = x*right + y*up + z*forward + position (1ca568).
struct Pose {
    Vec3 right{}, up{0.f, 1.f, 0.f}, forward{0.f, 0.f, 1.f}, position{};
};
inline Pose make_pose(const Vec3& position, const Vec3& f, const Vec3& up) noexcept {
    return {Vec3{f[2], f[1], -f[0]}, up, f, position};  // 001aa2e0 is deliberately not a cross product
}
inline Vec3 transform(const Pose& p, const Vec3& local) noexcept {
    Vec3 out{};
    for (int i = 0; i < 3; ++i)
        out[i] = local[0] * p.right[i] + local[1] * p.up[i] + local[2] * p.forward[i] + p.position[i];
    return out;
}

enum class TickStatus : uint8_t { NoObserver, Inactive, Active };

class Controller {
    Config config_{};
    Path path_;
    std::vector<float> history_;
    Vec3 position_{}, direction_{}, up_{0.f, 1.f, 0.f};
    float time_ = 0.f, bank_mean_ = 0.f;
    int32_t rest_counter_ = 0, ring_index_ = 0;
    bool active_ = false, valid_ = false;
    uint64_t invocations_ = 0;

    Vec3 bank_up(const Vec3& now, const Vec3& direction) noexcept {
        const auto& c = config_;
        if (c.banking == 0.f) return {0.f, 1.f, 0.f};
        const float ratio = (norm(sub(now, position_)) * 30.f) / c.speed;
        float b = (1.f - dot(direction, direction_)) * .5f;
        b = (((b * ratio) * c.banking) * kPi) * 5000.f;
        const Vec3 sideways{-direction_[2], direction_[1], direction_[0]};
        if (dot(direction, sideways) > 0.f) b = -b;
        const float n = static_cast<float>(c.samples);
        bank_mean_ = (bank_mean_ - history_[static_cast<size_t>(ring_index_)] / n) + b / n;
        history_[static_cast<size_t>(ring_index_)] = b;
        const float half = bank_mean_ * .5f;
        const float sine = static_cast<float>(std::sin(static_cast<double>(half)));
        const float cosine = static_cast<float>(std::cos(static_cast<double>(half)));
        const float x = sine * direction[0], y = sine * direction[1], z = sine * direction[2];
        const float xx = (x + x) * x, zz = (z + z) * z;
        // Row 1 of the quaternion matrix: (0,1,0) transformed by 1ca568.
        return {(y + y) * x + (z + z) * cosine, 1.f - (xx + zz), (z + z) * y - (x + x) * cosine};
    }

public:
    // 1a7ef8 init: Q(1) and Q(0), forward from Q(1)-Q(0), up (0,1,0) (bank flag +128 assumed 0 before the first pose,
    // AMBIENT1 object-layout.md), time 0, active unless triggered.
    bool initialize(const Vec3* points, size_t count, const Config& c) noexcept {
        valid_ = false;
        config_ = c;
        if (c.samples < 1 || c.samples > kMaxSamples || !finite(c.on) || !finite(c.off) || !finite(c.banking)) return false;
        if (!path_.prepare(points, count, c)) return false;
        try { history_.assign(static_cast<size_t>(c.samples), 0.f); } catch (...) { return false; }
        const Vec3 ahead = path_.evaluate(1.f);
        position_ = path_.evaluate(0.f);
        direction_ = forward(ahead, position_, Vec3{});
        if (dot(direction_, direction_) == 0.f) return false;
        up_ = {0.f, 1.f, 0.f};
        time_ = 0.f;
        bank_mean_ = 0.f;
        rest_counter_ = ring_index_ = 0;
        active_ = !c.trigger;
        invocations_ = 0;
        valid_ = true;
        return true;
    }
    bool valid() const noexcept { return valid_; }
    const Config& config() const noexcept { return config_; }
    const Path& path() const noexcept { return path_; }
    Pose pose() const noexcept { return make_pose(position_, direction_, up_); }
    float time() const noexcept { return time_; }
    bool active() const noexcept { return active_; }
    int32_t rest_counter() const noexcept { return rest_counter_; }
    int32_t ring_index() const noexcept { return ring_index_; }
    float bank_mean() const noexcept { return bank_mean_; }
    uint64_t invocations() const noexcept { return invocations_; }

    // One 1a80e8 invocation. observer = Car0 gaVehicleOutputData position, or nullptr when the Broker has none
    // (then nothing changes, also without a trigger).
    TickStatus tick(const Vec3* observer) noexcept {
        if (!valid_) return TickStatus::NoObserver;
        ++invocations_;
        if (!observer) return TickStatus::NoObserver;
        const auto& c = config_;
        const float dx = (*observer)[0] - position_[0], dz = (*observer)[2] - position_[2];
        const float distance2 = (dx * dx + 0.f) + dz * dz;
        if (c.trigger) {  // 1aa438, strict squared hysteresis
            if (active_) active_ = !(c.off * c.off < distance2);
            else active_ = distance2 < c.on * c.on;
        }
        if (!active_) return TickStatus::Inactive;
        ring_index_ = (ring_index_ + 1) % c.samples;
        const Vec3 now = path_.evaluate(time_);
        const Vec3 direction = forward(now, position_, direction_);
        up_ = bank_up(now, direction);
        position_ = now;
        direction_ = direction;
        // 1aa3b8 after publication.
        time_ = time_ + kTickIncrement;
        if (path_.duration() < time_) {
            if (c.loop) time_ = 0.f;
            else {
                time_ = path_.duration();
                if (c.rest) {
                    if (rest_counter_ < c.rest_ticks) ++rest_counter_;
                    else { time_ = 0.f; rest_counter_ = 0; }
                }
            }
        }
        return TickStatus::Active;
    }
};

// Host seconds -> PS2 controller invocations at 30 Hz. A long host stall (loading, alt-tab) is clamped so the
// objects never jump far ahead; the remainder carries over so the long-run rate stays exact.
class SplineClock {
    double pending_ = 0.0;
public:
    static constexpr double kMaxFrameSeconds = .25;
    void reset() noexcept { pending_ = 0.0; }
    unsigned advance(double seconds) noexcept {
        if (!(seconds > 0.0)) return 0;
        if (seconds > kMaxFrameSeconds) seconds = kMaxFrameSeconds;
        pending_ += seconds * kTicksPerSecond;
        const double whole = std::floor(pending_);
        pending_ -= whole;
        return static_cast<unsigned>(whole);
    }
};

}  // namespace ps2spline
