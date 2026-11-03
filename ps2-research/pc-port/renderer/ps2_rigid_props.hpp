#pragma once
// COURSE-ALIVE3: portable PS2 rigid prop physics (gaAiRigidBody hay bales and tumbleweeds). C++17 standard library only;
// no D3D, Windows or proxy type, so a future PS2 PC port can take it as it is.
//
// What follows the PS2 (ps2-research/rigid1, static reverse of SLES_509.06):
// * one game tick = one owner/manager invocation, 30 per second (PS2 game tick rate, docs/course-water1); the manager
//   runs two half steps of float32(1/30)/2 per invocation (1733a0 -> 173b68, global 0x479c98);
// * body state: position, quaternion (wxyz), momentum P, angular momentum L; v = P/m, omega = R I^-1 R^T L (266e20);
//   only force = gravity F = (0, -9.81 m, 0) (27d060, word 0x411cf5c3); the authored Mass and diagonal MOI;
// * centre of mass = model origin (tag101 base centre is the origin on both families), drawn pose = R, position (267f60);
// * collision shape = the model's tag101 convex representation B (hay 16 points / 10 faces, tumbleweed 26 / 32);
// * activation (1a0258): near = camera-visible with radius 4 and 3D squared camera distance <= 10000. A paused settled
//   body is not woken by proximity, only by a contact with an active vehicle (16e498); an active body that goes far is
//   paused and its momenta scaled by float32(1/60) per invocation for 60 invocations (zero on the last); coming near
//   again resumes it;
// * rest (267e00, 174178): after a half step with |v| + |omega| < 0.3 the backup pose is restored and a rest counter
//   grows; counter * half step >= MaxClampTime (constructor default 1) pauses the body;
// * initial placement (16f2f0): while the hull touches the landscape, lift by an increment that grows by 0.01 per
//   iteration (1000 iteration guard).
//
// What is NOT the PS2 (RIGID1 leaves it open: contact impulse magnitude, friction/restitution mixing, narrowphase):
// * contacts are point-in-convex tests (hull points against landscape triangles, car hulls and other props; a
//   face-normal separating-axis test when no point lies inside the other hull) solved by
//   sequential impulses with restitution, Coulomb friction and a small penetration bias, in 4 micro steps per PS2 half
//   step (the PS2 RK4 of a constant gravity force is exact, so free flight is unchanged), with a spin damping while a
//   prop touches the ground (rolling resistance; the PS2 surface coefficients are not identified);
// * vehicles are kinematic: the car pushes the prop with an effective mass (kCarEffectiveMass) but is not slowed down by
//   it (the proxy does not write the PC vehicle body);
// * a prop that touches an active prop is woken as well (the PS2 dispatcher is only proved for vehicle/prop pairs).
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace ps2rigid {

using V3 = std::array<float, 3>;
inline V3 operator+(const V3& a, const V3& b) noexcept { return {a[0] + b[0], a[1] + b[1], a[2] + b[2]}; }
inline V3 operator-(const V3& a, const V3& b) noexcept { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
inline V3 operator*(const V3& a, float k) noexcept { return {a[0] * k, a[1] * k, a[2] * k}; }
inline float dot(const V3& a, const V3& b) noexcept { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
inline V3 cross(const V3& a, const V3& b) noexcept {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}
inline float length(const V3& a) noexcept { return std::sqrt(dot(a, a)); }
inline bool finite(const V3& a) noexcept { return std::isfinite(a[0]) && std::isfinite(a[1]) && std::isfinite(a[2]); }

inline constexpr float kTick = 1.f / 30.f;                 // float32 0x3d088889
inline constexpr float kHalfStep = kTick * .5f;            // 0.01666666753590107
inline constexpr double kTicksPerSecond = 30.0;
inline constexpr float kGravity = 9.81f;                   // 0x411cf5c3
inline constexpr float kNearDistanceSq = 10000.f;          // 1a0258, inclusive, 3D
inline constexpr float kNearRadius = 4.f;                  // 200550 radius argument
inline constexpr int kFarDecayInvocations = 60;
inline constexpr float kFarDecayFactor = 1.f / 60.f;
inline constexpr float kRestSpeed = .3f;                   // 267e00: |v| + |omega|
inline constexpr float kMaxClampTime = 1.f;                // Physics/RigidBody/MaxClampTime constructor default
inline constexpr float kPlacementIncrement = .01f;         // 16f2f0
inline constexpr int kPlacementGuard = 1000;
// Port choices (not PS2):
inline constexpr int kMicroSteps = 4;
inline constexpr int kIterations = 8;
inline constexpr float kMaxTerrainDepth = .75f;
inline constexpr float kSlop = .005f, kBias = .2f, kMaxBiasSpeed = 2.f, kBounceThreshold = 1.f;
inline constexpr float kCarEffectiveMass = 1300.f;
inline constexpr float kMaxCarSpeed = 120.f, kTeleportDistance = 15.f;

struct Quat { float w = 1, x = 0, y = 0, z = 0; };
// Row-major rotation acting on column vectors: world = R * local + position (PS2 body R, 205580).
struct M3 { std::array<float, 9> m{1, 0, 0, 0, 1, 0, 0, 0, 1}; };
inline V3 mul(const M3& r, const V3& v) noexcept {
    return {r.m[0] * v[0] + r.m[1] * v[1] + r.m[2] * v[2], r.m[3] * v[0] + r.m[4] * v[1] + r.m[5] * v[2],
            r.m[6] * v[0] + r.m[7] * v[1] + r.m[8] * v[2]};
}
inline V3 mul_t(const M3& r, const V3& v) noexcept {
    return {r.m[0] * v[0] + r.m[3] * v[1] + r.m[6] * v[2], r.m[1] * v[0] + r.m[4] * v[1] + r.m[7] * v[2],
            r.m[2] * v[0] + r.m[5] * v[1] + r.m[8] * v[2]};
}
inline Quat normalized(Quat q) noexcept {
    const float l = std::sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    if (!(l >= .001f) || !std::isfinite(l)) return {};  // 2661e0: length < 0.001 -> identity
    return {q.w / l, q.x / l, q.y / l, q.z / l};
}
inline M3 rotation(const Quat& q) noexcept {
    const float w = q.w, x = q.x, y = q.y, z = q.z;
    return {{1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
             2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
             2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)}};
}
// Authored en3d rows (right, up, forward; row vectors: world = l.x*row0 + l.y*row1 + l.z*row2 + row3) -> quaternion of
// R = [row0 row1 row2] as columns. Rows are orthonormalised first (the XML keeps two decimals).
inline Quat quat_from_rows(const std::array<float, 9>& rows) noexcept {
    V3 x{rows[0], rows[1], rows[2]}, y{rows[3], rows[4], rows[5]};
    const float lx = length(x);
    if (!(lx > 1e-6f)) return {};
    x = x * (1.f / lx);
    y = y - x * dot(x, y);
    const float ly = length(y);
    if (!(ly > 1e-6f)) return {};
    y = y * (1.f / ly);
    const V3 z = cross(x, y);
    // R columns x, y, z.
    const float m00 = x[0], m01 = y[0], m02 = z[0], m10 = x[1], m11 = y[1], m12 = z[1], m20 = x[2], m21 = y[2], m22 = z[2];
    const float tr = m00 + m11 + m22;
    Quat q;
    if (tr > 0) {
        const float s = std::sqrt(tr + 1.f) * 2.f;
        q = {.25f * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s};
    } else if (m00 > m11 && m00 > m22) {
        const float s = std::sqrt(1.f + m00 - m11 - m22) * 2.f;
        q = {(m21 - m12) / s, .25f * s, (m01 + m10) / s, (m02 + m20) / s};
    } else if (m11 > m22) {
        const float s = std::sqrt(1.f + m11 - m00 - m22) * 2.f;
        q = {(m02 - m20) / s, (m01 + m10) / s, .25f * s, (m12 + m21) / s};
    } else {
        const float s = std::sqrt(1.f + m22 - m00 - m11) * 2.f;
        q = {(m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, .25f * s};
    }
    return normalized(q);
}
inline Quat slerp(Quat a, Quat b, float t) noexcept {
    float c = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z;
    if (c < 0) { b = {-b.w, -b.x, -b.y, -b.z}; c = -c; }
    float ka = 1 - t, kb = t;
    if (c < .9995f) {
        const float th = std::acos(std::min(1.f, c)), s = std::sin(th);
        ka = std::sin((1 - t) * th) / s; kb = std::sin(t * th) / s;
    }
    return normalized({a.w * ka + b.w * kb, a.x * ka + b.x * kb, a.y * ka + b.y * kb, a.z * ka + b.z * kb});
}

struct Pose { M3 r; V3 t{}; };
inline V3 apply(const Pose& p, const V3& l) noexcept { return mul(p.r, l) + p.t; }

// Convex hull: points and outward unit planes (n.p + d <= 0 inside), in model space.
struct Hull {
    std::vector<V3> points;
    std::vector<std::array<float, 4>> planes;
    float radius = 0;
    bool valid() const noexcept { return points.size() >= 4 && planes.size() >= 4 && radius > 0 && std::isfinite(radius); }
};
// Planes from points and polygon loops (car.dx tag101 representation B face loops): Newell normal, oriented away from
// the point centroid, coplanar duplicates dropped. False when the result is not a closed convex set.
inline bool hull_from_loops(const std::vector<V3>& pts, const std::vector<std::vector<uint32_t>>& loops, Hull& out) {
    out = {};
    if (pts.size() < 4) return false;
    V3 c{};
    for (const auto& p : pts) c = c + p;
    c = c * (1.f / float(pts.size()));
    for (const auto& loop : loops) {
        if (loop.size() < 3) continue;
        V3 n{}, centre{};
        for (size_t i = 0; i < loop.size(); ++i) {
            if (loop[i] >= pts.size()) return false;
            const V3& a = pts[loop[i]];
            const V3& b = pts[loop[(i + 1) % loop.size()]];
            n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1]);
            centre = centre + a;
        }
        const float l = length(n);
        if (!(l > 1e-9f)) continue;
        n = n * (1.f / l);
        centre = centre * (1.f / float(loop.size()));
        float d = -dot(n, centre);
        if (dot(n, c) + d > 0) { n = n * -1.f; d = -d; }
        bool dup = false;
        for (const auto& q : out.planes)
            if (std::fabs(q[0] - n[0]) < 1e-4f && std::fabs(q[1] - n[1]) < 1e-4f && std::fabs(q[2] - n[2]) < 1e-4f && std::fabs(q[3] - d) < 1e-3f) dup = true;
        if (!dup) out.planes.push_back({n[0], n[1], n[2], d});
    }
    float tolerance = 0;
    for (const auto& p : pts) tolerance = std::max(tolerance, length(p - c));
    tolerance = std::max(1e-3f, tolerance * 2e-3f);
    for (const auto& q : out.planes)
        for (const auto& p : pts)
            if (q[0] * p[0] + q[1] * p[1] + q[2] * p[2] + q[3] > tolerance) { out = {}; return false; }
    out.points = pts;
    for (const auto& p : pts) out.radius = std::max(out.radius, length(p));
    if (!out.valid()) { out = {}; return false; }
    return true;
}

// Landscape collision triangles (course DX tag1400). The stored plane points away from the solid side (drivable side
// = -n, COLLISION-DEBUG1); ground-like triangles (|n.y| > 0.5) are always solid below, whatever their stored winding.
class Terrain {
    std::vector<float> tri_;     // 9 per triangle
    std::vector<float> plane_;   // n (solid side towards +n), d
    std::vector<uint8_t> water_; // $surfacetype(water): no shadow is cast on it (332628)
    std::vector<uint32_t> start_, items_;
    mutable std::vector<uint32_t> stamp_;
    mutable uint32_t stamp_value_ = 0;
    float x0_ = 0, z0_ = 0, cell_ = 8.f;
    uint32_t nx_ = 0, nz_ = 0;
public:
    size_t triangles() const noexcept { return plane_.size() / 4; }
    bool empty() const noexcept { return plane_.empty(); }
    void clear() noexcept { *this = Terrain{}; }
    // corners: 9 floats per triangle; planes: n, d per triangle (tag1400 record plane). Degenerate records are skipped.
    bool build(const std::vector<float>& corners, const std::vector<float>& planes, float cell = 8.f,
               const std::vector<uint8_t>* water = nullptr) {
        clear();
        const size_t n = planes.size() / 4;
        if (corners.size() != n * 9 || !n || !(cell > .5f)) return false;
        float minx = 1e30f, minz = 1e30f, maxx = -1e30f, maxz = -1e30f;
        for (size_t t = 0; t < n; ++t) {
            const float* p = &planes[t * 4];
            if (!std::isfinite(p[0]) || !std::isfinite(p[1]) || !std::isfinite(p[2]) || !std::isfinite(p[3])) continue;
            float nn[4] = {p[0], p[1], p[2], p[3]};
            if (nn[1] > .5f) { nn[0] = -nn[0]; nn[1] = -nn[1]; nn[2] = -nn[2]; nn[3] = -nn[3]; }
            for (int k = 0; k < 9; ++k) tri_.push_back(corners[t * 9 + k]);
            for (int k = 0; k < 4; ++k) plane_.push_back(nn[k]);
            water_.push_back(water && t < water->size() ? (*water)[t] : 0);
            for (int v = 0; v < 3; ++v) {
                minx = std::min(minx, corners[t * 9 + v * 3]); maxx = std::max(maxx, corners[t * 9 + v * 3]);
                minz = std::min(minz, corners[t * 9 + v * 3 + 2]); maxz = std::max(maxz, corners[t * 9 + v * 3 + 2]);
            }
        }
        const size_t m = plane_.size() / 4;
        if (!m) { clear(); return false; }
        cell_ = cell; x0_ = minx - 1.f; z0_ = minz - 1.f;
        const double sx = std::ceil((double(maxx) - x0_ + 1.0) / cell), sz = std::ceil((double(maxz) - z0_ + 1.0) / cell);
        if (!(sx >= 1 && sz >= 1) || sx * sz > 4.0e6) { clear(); return false; }
        nx_ = uint32_t(sx); nz_ = uint32_t(sz);
        std::vector<uint32_t> count(size_t(nx_) * nz_ + 1, 0);
        auto range = [&](size_t t, uint32_t& ax, uint32_t& az, uint32_t& bx, uint32_t& bz) {
            const float* c = &tri_[t * 9];
            const float lx = std::min({c[0], c[3], c[6]}) - .5f, hx = std::max({c[0], c[3], c[6]}) + .5f;
            const float lz = std::min({c[2], c[5], c[8]}) - .5f, hz = std::max({c[2], c[5], c[8]}) + .5f;
            ax = uint32_t(std::clamp((lx - x0_) / cell_, 0.f, float(nx_ - 1))); bx = uint32_t(std::clamp((hx - x0_) / cell_, 0.f, float(nx_ - 1)));
            az = uint32_t(std::clamp((lz - z0_) / cell_, 0.f, float(nz_ - 1))); bz = uint32_t(std::clamp((hz - z0_) / cell_, 0.f, float(nz_ - 1)));
        };
        for (size_t t = 0; t < m; ++t) {
            uint32_t ax, az, bx, bz; range(t, ax, az, bx, bz);
            for (uint32_t z = az; z <= bz; ++z) for (uint32_t x = ax; x <= bx; ++x) ++count[size_t(z) * nx_ + x];
        }
        start_.assign(count.size(), 0);
        for (size_t i = 1; i < count.size(); ++i) start_[i] = start_[i - 1] + count[i - 1];
        if (start_.back() > 64u * 1024u * 1024u) { clear(); return false; }
        items_.assign(start_.back(), 0);
        std::vector<uint32_t> fill(start_.begin(), start_.end() - 1);
        for (size_t t = 0; t < m; ++t) {
            uint32_t ax, az, bx, bz; range(t, ax, az, bx, bz);
            for (uint32_t z = az; z <= bz; ++z) for (uint32_t x = ax; x <= bx; ++x) items_[fill[size_t(z) * nx_ + x]++] = uint32_t(t);
        }
        stamp_.assign(m, 0);
        return true;
    }
    // Every triangle whose cell lies within the XZ square of half size r around (x, z), once each:
    // fn(corners[9], plane[4] (solid towards +n), water).
    template <class F>
    void for_near(float x, float z, float r, F&& fn) const {
        if (plane_.empty() || !(r > 0)) return;
        if (++stamp_value_ == 0) { std::fill(stamp_.begin(), stamp_.end(), 0u); stamp_value_ = 1; }
        const int ax = int(std::floor((x - r - x0_) / cell_)), bx = int(std::floor((x + r - x0_) / cell_));
        const int az = int(std::floor((z - r - z0_) / cell_)), bz = int(std::floor((z + r - z0_) / cell_));
        for (int cz = std::max(az, 0); cz <= std::min(bz, int(nz_) - 1); ++cz)
            for (int cx = std::max(ax, 0); cx <= std::min(bx, int(nx_) - 1); ++cx) {
                const size_t c = size_t(cz) * nx_ + size_t(cx);
                for (uint32_t i = start_[c]; i < start_[c + 1]; ++i) {
                    const uint32_t t = items_[i];
                    if (stamp_[t] == stamp_value_) continue;
                    stamp_[t] = stamp_value_;
                    fn(&tri_[size_t(t) * 9], &plane_[size_t(t) * 4], water_[t] != 0);
                }
            }
    }
    // Deepest-first is wrong at seams; the closest surface behind which p lies (0 < depth <= max_depth) wins.
    bool contact(const V3& p, float max_depth, V3& normal, float& depth) const noexcept {
        if (plane_.empty()) return false;
        const float fx = (p[0] - x0_) / cell_, fz = (p[2] - z0_) / cell_;
        if (!(fx >= 0 && fz >= 0 && fx < float(nx_) && fz < float(nz_))) return false;
        const size_t c = size_t(uint32_t(fz)) * nx_ + uint32_t(fx);
        bool hit = false;
        for (uint32_t i = start_[c]; i < start_[c + 1]; ++i) {
            const uint32_t t = items_[i];
            const float* q = &plane_[size_t(t) * 4];
            const V3 n{q[0], q[1], q[2]};
            const float s = dot(n, p) + q[3];
            if (!(s > 0) || s > max_depth || (hit && s >= depth)) continue;
            const V3 x = p - n * s;
            const float* v = &tri_[size_t(t) * 9];
            const V3 a{v[0], v[1], v[2]}, b{v[3], v[4], v[5]}, d{v[6], v[7], v[8]};
            const float e0 = dot(cross(b - a, x - a), n), e1 = dot(cross(d - b, x - b), n), e2 = dot(cross(a - d, x - d), n);
            constexpr float tol = -1e-4f;
            if (!((e0 >= tol && e1 >= tol && e2 >= tol) || (e0 <= -tol && e1 <= -tol && e2 <= -tol))) continue;
            hit = true; depth = s; normal = n * -1.f;
        }
        return hit;
    }
    // Highest ground surface under (x, z) at most `above` over y (diagnostics, tests).
    bool ground(float x, float y, float z, float above, float& h) const noexcept {
        if (plane_.empty()) return false;
        const float fx = (x - x0_) / cell_, fz = (z - z0_) / cell_;
        if (!(fx >= 0 && fz >= 0 && fx < float(nx_) && fz < float(nz_))) return false;
        const size_t c = size_t(uint32_t(fz)) * nx_ + uint32_t(fx);
        bool hit = false;
        for (uint32_t i = start_[c]; i < start_[c + 1]; ++i) {
            const uint32_t t = items_[i];
            const float* q = &plane_[size_t(t) * 4];
            if (!(q[1] < -.5f)) continue;  // ground only (solid below)
            const float* v = &tri_[size_t(t) * 9];
            const float d0 = (v[3] - v[0]) * (z - v[2]) - (v[5] - v[2]) * (x - v[0]);
            const float d1 = (v[6] - v[3]) * (z - v[5]) - (v[8] - v[5]) * (x - v[3]);
            const float d2 = (v[0] - v[6]) * (z - v[8]) - (v[2] - v[8]) * (x - v[6]);
            if (!((d0 >= 0 && d1 >= 0 && d2 >= 0) || (d0 <= 0 && d1 <= 0 && d2 <= 0))) continue;
            const float g = -(q[0] * x + q[2] * z + q[3]) / q[1];
            if (g > y + above || (hit && g <= h)) continue;
            hit = true; h = g;
        }
        return hit;
    }
};

// A vehicle: kinematic convex hull at its render pose, with velocity from consecutive poses.
struct Kinematic {
    const Hull* hull = nullptr;
    Pose pose;
    V3 v{}, w{};
    bool valid = false;
    // Two-way coupling: the PC vehicle body mass and centre (body+0x20, +0xA0). mass 0 = kinematic only (the car pushes
    // with kCarEffectiveMass and feels nothing). Otherwise the solver changes v by the reaction and sums what the car
    // receives: linear impulse and angular impulse about com, for the caller to add to the body momenta.
    float mass = 0;
    V3 com{};
    V3 impulse{}, angular{};
    uint32_t body = 0;  // opaque caller id of the coupled body
};
// Car pose (D3D row vectors from the render instance world matrix: rows x, y, z, translation) -> Pose; false when not
// orthonormal within 2e-3.
inline bool pose_from_rows(const float* m12, Pose& out) noexcept {
    for (int i = 0; i < 12; ++i) if (!std::isfinite(m12[i])) return false;
    for (int r = 0; r < 3; ++r) {
        const V3 a{m12[r * 3], m12[r * 3 + 1], m12[r * 3 + 2]};
        if (std::fabs(length(a) - 1.f) > 2e-3f) return false;
        for (int s = r + 1; s < 3; ++s) if (std::fabs(dot(a, V3{m12[s * 3], m12[s * 3 + 1], m12[s * 3 + 2]})) > 2e-3f) return false;
    }
    for (int r = 0; r < 3; ++r) for (int c = 0; c < 3; ++c) out.r.m[r * 3 + c] = m12[c * 3 + r];
    out.t = {m12[9], m12[10], m12[11]};
    return true;
}
// Velocity of a pose sequence: linear from the translation, angular from R1 R0^T; zero for a teleport or a bad interval.
inline void pose_velocity(const Pose& a, const Pose& b, double seconds, V3& v, V3& w) noexcept {
    v = {}; w = {};
    if (!(seconds > 1e-4) || seconds > .25) return;
    const V3 dt = b.t - a.t;
    if (length(dt) > kTeleportDistance) return;
    v = dt * float(1.0 / seconds);
    const float sp = length(v);
    if (sp > kMaxCarSpeed) v = v * (kMaxCarSpeed / sp);
    M3 d;  // b.r * a.r^T
    for (int r = 0; r < 3; ++r) for (int c = 0; c < 3; ++c) {
        float s = 0; for (int k = 0; k < 3; ++k) s += b.r.m[r * 3 + k] * a.r.m[c * 3 + k];
        d.m[r * 3 + c] = s;
    }
    const float tr = std::clamp((d.m[0] + d.m[4] + d.m[8] - 1.f) * .5f, -1.f, 1.f);
    const float angle = std::acos(tr);
    if (!(angle > 1e-6f)) return;
    V3 axis{d.m[7] - d.m[5], d.m[2] - d.m[6], d.m[3] - d.m[1]};
    const float l = length(axis);
    if (!(l > 1e-6f)) return;
    w = axis * (angle / (l * float(seconds)));
    if (!finite(w) || length(w) > 30.f) w = {};
}

struct BodyDef {
    const Hull* hull = nullptr;
    float mass = 1;
    V3 moi{1, 1, 1};
    std::array<float, 12> matrix{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};  // authored en3d rows 0..3 (xyz)
    float restitution = .2f, friction = .6f;
    float rolling = 1.f;  // port: spin damping per second while touching the landscape (rolling resistance)
};
enum class State : uint8_t { Asleep, Active, Far };
struct Body {
    BodyDef def;
    V3 x{}, P{}, L{};
    Quat q;
    float inv_m = 1;
    V3 inv_i{1, 1, 1};
    State state = State::Asleep;
    int far_decay = 0, rest = 0;
    bool in_view = false;
    // Previous tick pose (draw interpolation).
    V3 prev_x{};
    Quat prev_q;
    // Derived per step.
    M3 r;
    V3 v{}, w{};
    float lifted = 0;
    uint32_t wakes = 0;
    bool grounded = false;
    V3 push{};
};

struct Contact {
    int a = -1, b = -1, k = -1;  // body a; second body b or kinematic k (or landscape)
    V3 p{}, n{};                 // point, normal pushing a out
    float depth = 0, mu = .5f, e = .2f, jn = 0, jt = 0, bounce = 0;
    V3 t{};
};

struct TickInput {
    V3 camera{};
    bool have_camera = false;
    // Side planes of the view (a.x + b.y + c.z + d >= -radius inside), as many as known (0 = only the distance test).
    std::vector<std::array<float, 4>> frustum;
    std::vector<Kinematic> cars;
};

class World {
    const Terrain* terrain_ = nullptr;
    std::vector<Body> bodies_;
    std::vector<Contact> contacts_;
    uint64_t ticks_ = 0;
    uint32_t contacts_last_ = 0, car_contacts_last_ = 0;

    static void derive(Body& b) noexcept {
        b.q = normalized(b.q);
        b.r = rotation(b.q);
        b.v = b.P * b.inv_m;
        b.w = world_inverse_inertia(b, b.L);
    }
    static V3 world_inverse_inertia(const Body& b, const V3& vec) noexcept {
        V3 l = mul_t(b.r, vec);
        l = {l[0] * b.inv_i[0], l[1] * b.inv_i[1], l[2] * b.inv_i[2]};
        return mul(b.r, l);
    }
    static void commit(Body& b) noexcept {
        b.P = b.v * b.def.mass;
        const V3 l = mul_t(b.r, b.w);
        b.L = mul(b.r, V3{l[0] / b.inv_i[0], l[1] / b.inv_i[1], l[2] / b.inv_i[2]});
    }
    static Pose pose_of(const Body& b) noexcept { return {b.r, b.x}; }
    bool touches_terrain(const Body& b) const noexcept {
        if (!terrain_) return false;
        const Pose p = pose_of(b);
        for (const auto& l : b.def.hull->points) { V3 n; float d; if (terrain_->contact(apply(p, l), kMaxTerrainDepth, n, d)) return true; }
        return false;
    }
    // Points of hull A (at pa) inside hull B (at pb): fn(point, normal out of B, depth).
    template <class F>
    // rel (world, optional) = velocity of A's points relative to B. With it, a point is pushed out through the face it
    // entered by (smallest time back to the face along -rel among the faces it moves into) instead of the shallowest
    // face: a car moves up to 0.7 m per frame into a prop, and the shallowest face is then often a side or the top.
    static void points_in(const Hull& a, const Pose& pa, const Hull& b, const Pose& pb, F&& fn, const V3* rel = nullptr) {
        const V3 lr = rel ? mul_t(pb.r, *rel) : V3{};
        const bool moving = rel && length(lr) > .5f;
        for (const auto& l : a.points) {
            const V3 p = apply(pa, l);
            const V3 lb = mul_t(pb.r, p - pb.t);
            float best = -1e30f; size_t bi = 0;
            for (size_t i = 0; i < b.planes.size(); ++i) {
                const auto& q = b.planes[i];
                const float s = q[0] * lb[0] + q[1] * lb[1] + q[2] * lb[2] + q[3];
                if (s > best) { best = s; bi = i; if (best >= 0) break; }
            }
            if (best >= 0) continue;
            if (moving) {
                float t_best = 1e30f;
                for (size_t i = 0; i < b.planes.size(); ++i) {
                    const auto& q = b.planes[i];
                    const float into = q[0] * lr[0] + q[1] * lr[1] + q[2] * lr[2];
                    if (!(into < -.1f)) continue;
                    const float depth = -(q[0] * lb[0] + q[1] * lb[1] + q[2] * lb[2] + q[3]);
                    const float t = depth / -into;
                    if (t < t_best) { t_best = t; bi = i; best = -depth; }
                }
            }
            fn(p, mul(pb.r, V3{b.planes[bi][0], b.planes[bi][1], b.planes[bi][2]}), -best);
        }
    }
    // Separating axes = face normals of both hulls (edge-edge axes are not tested, so near an edge the overlap is
    // conservative). When A and B overlap on every axis, fn(point, normal pushing A out of B, depth) once, at the
    // middle of the two support points along the least-overlap axis.
    template <class F>
    static void sat(const Hull& a, const Pose& pa, const Hull& b, const Pose& pb, F&& fn) {
        float best = 1e30f; V3 axis{};
        auto project = [](const Hull& h, const Pose& p, const V3& n, float& lo, float& hi) {
            lo = 1e30f; hi = -1e30f;
            for (const auto& l : h.points) { const float s = dot(apply(p, l), n); lo = std::min(lo, s); hi = std::max(hi, s); }
        };
        auto test = [&](const V3& n) {
            float al, ah, bl, bh; project(a, pa, n, al, ah); project(b, pb, n, bl, bh);
            const float o = std::min(ah - bl, bh - al);
            if (o < best) { best = o; axis = (ah - bl < bh - al) ? n * -1.f : n; }
            return o > 0;
        };
        for (const auto& q : a.planes) if (!test(mul(pa.r, V3{q[0], q[1], q[2]}))) return;
        for (const auto& q : b.planes) if (!test(mul(pb.r, V3{q[0], q[1], q[2]}))) return;
        // axis points from B towards A (push direction for A).
        V3 sa{}, sb{}; float ma = 1e30f, mb = -1e30f;
        for (const auto& l : a.points) { const V3 p = apply(pa, l); const float s = dot(p, axis); if (s < ma) { ma = s; sa = p; } }
        for (const auto& l : b.points) { const V3 p = apply(pb, l); const float s = dot(p, axis); if (s > mb) { mb = s; sb = p; } }
        fn((sa + sb) * .5f, axis, best);
    }
    static bool spheres(const V3& a, float ra, const V3& b, float rb) noexcept {
        const V3 d = a - b; const float r = ra + rb; return dot(d, d) <= r * r;
    }
    void wake(Body& b) noexcept {
        if (b.state == State::Active) return;
        b.state = State::Active; b.rest = 0; b.far_decay = 0; ++b.wakes;
    }
    void collect(const TickInput& in, bool wake_only) {
        contacts_.clear();
        for (size_t i = 0; i < bodies_.size(); ++i) {
            Body& b = bodies_[i];
            const bool active = b.state == State::Active;
            if (!active && !wake_only) continue;
            const Pose pa = pose_of(b);
            const Hull& h = *b.def.hull;
            if (active && terrain_) {
                for (const auto& l : h.points) {
                    const V3 p = apply(pa, l); V3 n; float d;
                    if (terrain_->contact(p, kMaxTerrainDepth, n, d)) {
                        Contact c; c.a = int(i); c.p = p; c.n = n; c.depth = d; c.mu = b.def.friction; c.e = b.def.restitution;
                        contacts_.push_back(c);
                    }
                }
            }
            for (size_t k = 0; k < in.cars.size(); ++k) {
                const auto& car = in.cars[k];
                if (!car.valid || !car.hull || !spheres(b.x, h.radius, car.pose.t, car.hull->radius)) continue;
                bool hit = false;
                auto add = [&](const V3& p, const V3& n, float d) {
                    hit = true;
                    Contact c; c.a = int(i); c.k = int(k); c.p = p; c.n = n; c.depth = d; c.mu = .5f; c.e = b.def.restitution;
                    contacts_.push_back(c);
                };
                // Relative motion: prop points move by v_prop - v_car through the car, car points the other way.
                const V3 rel = b.v - car.v, back = rel * -1.f;
                points_in(h, pa, *car.hull, car.pose, add, &rel);
                points_in(*car.hull, car.pose, h, pa, [&](const V3& p, const V3& n, float d) { add(p, n * -1.f, d); }, &back);
                if (!hit) sat(h, pa, *car.hull, car.pose, add);
                if (hit && !active) wake(b);
            }
        }
        // Prop pairs: an active prop pushes and wakes a resting one.
        for (size_t i = 0; i < bodies_.size(); ++i)
            for (size_t j = i + 1; j < bodies_.size(); ++j) {
                Body& a = bodies_[i]; Body& b = bodies_[j];
                const bool aa = a.state == State::Active, ba = b.state == State::Active;
                if (!aa && !ba) continue;
                if (!spheres(a.x, a.def.hull->radius, b.x, b.def.hull->radius)) continue;
                bool hit = false;
                auto add = [&](const V3& p, const V3& n, float d) {
                    hit = true;
                    Contact c; c.a = int(i); c.b = int(j); c.p = p; c.n = n; c.depth = d;
                    c.mu = std::sqrt(a.def.friction * b.def.friction); c.e = std::min(a.def.restitution, b.def.restitution);
                    contacts_.push_back(c);
                };
                points_in(*a.def.hull, pose_of(a), *b.def.hull, pose_of(b), add);
                points_in(*b.def.hull, pose_of(b), *a.def.hull, pose_of(a), [&](const V3& p, const V3& n, float d) { add(p, n * -1.f, d); });
                if (!hit) sat(*a.def.hull, pose_of(a), *b.def.hull, pose_of(b), add);
                if (hit) { wake(a); wake(b); }
            }
        if (wake_only) contacts_.clear();
    }
    static float car_inverse_mass(const Kinematic& k) noexcept { return k.mass > 0 ? 1.f / k.mass : 1.f / kCarEffectiveMass; }
    // Reaction of a prop impulse j (on the prop at point p) on a coupled car.
    static void car_reaction(Kinematic& k, const V3& p, const V3& j) noexcept {
        if (!(k.mass > 0)) return;
        k.v = k.v - j * (1.f / k.mass);
        k.impulse = k.impulse - j;
        k.angular = k.angular - cross(p - k.com, j);
    }
    float effective(const Body& b, const V3& r, const V3& n) const noexcept {
        return b.inv_m + dot(n, cross(world_inverse_inertia(b, cross(r, n)), r));
    }
    void impulse(Body& b, const V3& r, const V3& j) noexcept {
        b.v = b.v + j * b.inv_m;
        b.w = b.w + world_inverse_inertia(b, cross(r, j));
    }
    static V3 other_velocity(const Contact& c, const std::vector<Body>& bodies, const TickInput& in) noexcept {
        if (c.b >= 0) { const Body& o = bodies[size_t(c.b)]; return o.v + cross(o.w, c.p - o.x); }
        if (c.k >= 0) { const auto& k = in.cars[size_t(c.k)]; return k.v + cross(k.w, c.p - k.pose.t); }
        return {};
    }
    void solve(TickInput& in, float h) {
        // Bounce targets from the approach speed before the iterations.
        for (auto& c : contacts_) {
            const Body& a = bodies_[size_t(c.a)];
            const float vn = dot(a.v + cross(a.w, c.p - a.x) - other_velocity(c, bodies_, in), c.n);
            c.bounce = vn < -kBounceThreshold ? -c.e * vn : 0.f;
        }
        for (int it = 0; it < kIterations; ++it)
            for (auto& c : contacts_) {
                Body& a = bodies_[size_t(c.a)];
                Body* b = c.b >= 0 ? &bodies_[size_t(c.b)] : nullptr;
                const V3 ra = c.p - a.x, rb = b ? c.p - b->x : V3{};
                const V3 vrel = a.v + cross(a.w, ra) - other_velocity(c, bodies_, in);
                const float vn = dot(vrel, c.n);
                float k = effective(a, ra, c.n) + (b ? effective(*b, rb, c.n) : c.k >= 0 ? car_inverse_mass(in.cars[size_t(c.k)]) : 0.f);
                if (!(k > 1e-9f)) continue;
                // Car contacts: no velocity bias (it would hand the car momentum for a position error); their
                // penetration is projected out after the solve instead.
                const float bias = c.k >= 0 ? 0.f : std::min(kMaxBiasSpeed, kBias / h * std::max(0.f, c.depth - kSlop));
                const float target = std::max(c.bounce, bias);
                const float jn = std::max(0.f, c.jn + (target - vn) / k);
                const float dj = jn - c.jn; c.jn = jn;
                impulse(a, ra, c.n * dj);
                if (b) impulse(*b, rb, c.n * -dj);
                if (c.k >= 0) car_reaction(in.cars[size_t(c.k)], c.p, c.n * dj);
                // Friction along the current sliding direction, |jt| <= mu jn.
                const V3 v2 = a.v + cross(a.w, ra) - other_velocity(c, bodies_, in);
                V3 tv = v2 - c.n * dot(v2, c.n);
                const float tl = length(tv);
                if (tl < 1e-5f) continue;
                tv = tv * (1.f / tl);
                float kt = effective(a, ra, tv) + (b ? effective(*b, rb, tv) : c.k >= 0 ? car_inverse_mass(in.cars[size_t(c.k)]) : 0.f);
                if (!(kt > 1e-9f)) continue;
                const float jt = std::clamp(-tl / kt, -c.mu * c.jn, c.mu * c.jn);
                impulse(a, ra, tv * jt);
                if (b) impulse(*b, rb, tv * -jt);
                if (c.k >= 0) car_reaction(in.cars[size_t(c.k)], c.p, tv * jt);
            }
    }
    void integrate(Body& b, float h) noexcept {
        b.x = b.x + b.v * h;
        const Quat& q = b.q;
        const V3& w = b.w;
        // dq = 0.5 (0, omega) * q (Hamilton product, world omega; 266e20).
        const Quat dq{-.5f * (w[0] * q.x + w[1] * q.y + w[2] * q.z), .5f * (w[0] * q.w + w[1] * q.z - w[2] * q.y),
                      .5f * (w[1] * q.w + w[2] * q.x - w[0] * q.z), .5f * (w[2] * q.w + w[0] * q.y - w[1] * q.x)};
        b.q = normalized({q.w + dq.w * h, q.x + dq.x * h, q.y + dq.y * h, q.z + dq.z * h});
        b.r = rotation(b.q);
    }
    void half_step(TickInput& in) {
        std::vector<std::pair<V3, Quat>> backup(bodies_.size());
        for (size_t i = 0; i < bodies_.size(); ++i) backup[i] = {bodies_[i].x, bodies_[i].q};
        // Contact wake of paused props (vehicle or active prop), then the active set moves.
        collect(in, true);
        const float h = kHalfStep / float(kMicroSteps);
        uint32_t contacts = 0, car_contacts = 0;
        for (int s = 0; s < kMicroSteps; ++s) {
            bool any = false;
            for (auto& b : bodies_) if (b.state == State::Active) {
                derive(b); b.v[1] -= kGravity * h; any = true;
            }
            if (!any) break;
            collect(in, false);
            contacts += uint32_t(contacts_.size());
            for (const auto& c : contacts_) car_contacts += c.k >= 0;
            solve(in, h);
            // Position projection of car penetration (deepest contact per prop, half of it per micro step).
            for (auto& b : bodies_) b.push = {};
            for (const auto& c : contacts_)
                if (c.k >= 0) {
                    Body& b = bodies_[size_t(c.a)];
                    const V3 want = c.n * (std::max(0.f, c.depth - kSlop) * .5f);
                    if (dot(want, want) > dot(b.push, b.push)) b.push = want;
                }
            for (auto& b : bodies_) if (b.state == State::Active) b.x = b.x + b.push;
            for (auto& b : bodies_) b.grounded = false;
            for (const auto& c : contacts_) if (c.b < 0 && c.k < 0 && c.n[1] > .5f) bodies_[size_t(c.a)].grounded = true;
            for (auto& b : bodies_) if (b.state == State::Active) {
                if (b.grounded) b.w = b.w * std::max(0.f, 1.f - b.def.rolling * h);
                integrate(b, h); commit(b);
            }
        }
        contacts_last_ = contacts; car_contacts_last_ = car_contacts;
        for (size_t i = 0; i < bodies_.size(); ++i) {
            Body& b = bodies_[i];
            if (b.state != State::Active) continue;
            derive(b);
            if (!finite(b.x) || !finite(b.P) || !finite(b.L)) { b.x = backup[i].first; b.q = backup[i].second; b.P = b.L = {}; b.state = State::Asleep; continue; }
            if (length(b.v) + length(b.w) < kRestSpeed) {
                b.x = backup[i].first; b.q = backup[i].second; ++b.rest;
                if (float(b.rest) * kHalfStep >= kMaxClampTime) { b.state = State::Asleep; b.P = b.L = {}; b.rest = 0; }
            } else b.rest = 0;
            derive(b);
        }
    }
public:
    bool start(const Terrain* terrain, const std::vector<BodyDef>& defs) {
        bodies_.clear(); contacts_.clear(); ticks_ = 0; terrain_ = terrain;
        for (const auto& d : defs) {
            if (!d.hull || !d.hull->valid() || !(d.mass > 0) || !(d.moi[0] > 0 && d.moi[1] > 0 && d.moi[2] > 0)) { bodies_.clear(); return false; }
            Body b; b.def = d;
            b.inv_m = 1.f / d.mass; b.inv_i = {1.f / d.moi[0], 1.f / d.moi[1], 1.f / d.moi[2]};
            std::array<float, 9> rows{};
            for (int k = 0; k < 9; ++k) rows[size_t(k)] = d.matrix[size_t(k)];
            b.q = quat_from_rows(rows);
            b.x = {d.matrix[9], d.matrix[10], d.matrix[11]};
            if (!finite(b.x)) { bodies_.clear(); return false; }
            b.r = rotation(b.q);
            // 16f2f0: lift out of the landscape by a growing increment.
            float inc = 0;
            for (int g = 0; g < kPlacementGuard && touches_terrain(b); ++g) { inc += kPlacementIncrement; b.x[1] += inc; b.lifted += inc; }
            b.prev_x = b.x; b.prev_q = b.q;
            bodies_.push_back(b);
        }
        return true;
    }
    void stop() noexcept { bodies_.clear(); contacts_.clear(); terrain_ = nullptr; ticks_ = 0; }
    bool ready() const noexcept { return !bodies_.empty(); }
    uint64_t ticks() const noexcept { return ticks_; }
    const std::vector<Body>& bodies() const noexcept { return bodies_; }
    uint32_t last_contacts() const noexcept { return contacts_last_; }
    uint32_t last_car_contacts() const noexcept { return car_contacts_last_; }
    // Camera-visible (radius 4) and within 100 units: the PS2 near predicate for one body.
    static bool is_near(const Body& b, const TickInput& in) noexcept {
        if (!in.have_camera) return false;
        const V3 d = b.x - in.camera;
        if (dot(d, d) > kNearDistanceSq) return false;
        for (const auto& p : in.frustum) if (p[0] * b.x[0] + p[1] * b.x[1] + p[2] * b.x[2] + p[3] < -kNearRadius) return false;
        return true;
    }
    // One PS2 game tick. Coupled cars (Kinematic::mass > 0) keep their changed velocity and summed impulses in `in`.
    void tick(TickInput&& in) { tick(in); }
    void tick(TickInput& in) {
        if (bodies_.empty()) return;
        for (auto& b : bodies_) {
            b.prev_x = b.x; b.prev_q = b.q;
            b.in_view = is_near(b, in);
            // 1a0258 owner: far pause with 60-invocation decay, resume when near again.
            if (b.state == State::Active && !b.in_view) { b.state = State::Far; b.far_decay = kFarDecayInvocations; }
            else if (b.state == State::Far && b.in_view) { b.state = State::Active; b.rest = 0; b.far_decay = 0; }
            if (b.state == State::Far && b.far_decay > 0) {
                if (b.far_decay > 1) { b.P = b.P * kFarDecayFactor; b.L = b.L * kFarDecayFactor; } else { b.P = b.L = {}; }
                --b.far_decay;
            }
        }
        half_step(in);
        half_step(in);
        ++ticks_;
    }
    // Drawn pose between the previous and the current tick (en3d Interpolated), alpha in [0, 1].
    Pose pose(size_t i, float alpha) const noexcept {
        const Body& b = bodies_[i];
        alpha = std::clamp(alpha, 0.f, 1.f);
        return {rotation(slerp(b.prev_q, b.q, alpha)), b.prev_x + (b.x - b.prev_x) * alpha};
    }
    // Tests: direct state access.
    Body& body(size_t i) noexcept { return bodies_[i]; }
};

// Host seconds -> PS2 ticks, with the fraction of the next tick for drawing (0.25 s stall clamp as SplineClock).
class TickClock {
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
    float fraction() const noexcept { return float(pending_); }
};

}  // namespace ps2rigid
