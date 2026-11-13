#pragma once
// R-SURFACE1 G1.3: which car triangles can get grime. Owner review 3: dust inside the Kia cabin and on the dark side of
// the drivers' helmets. Texture names cannot tell an inner door panel or a roll cage from the outer body (same
// black-tga / paint / rubber materials), and rally cabins are open (no side windows), so a closed-volume flood fill
// does not work either. The test used here is sky visibility: every car-resource triangle of a model is rasterised
// into a coarse occupancy grid (64 cells along the longest axis), and a triangle is exterior when at least 15 % of the
// rays it sends into its outward hemisphere leave the grid without hitting the car. Measured offline on Kia, Patrol,
// Navara, Impreza and Lancer Evo IV: crew, helmets, seats, dash, cage, the reflectors inside lamp housings and the
// back faces of bumpers score about 0; outer panels, stickers, the pickup bed and the roof about 0.9-1.0.
// Pure code (no Direct3D): tests in tests/ps2_diag_tests.cpp.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>

namespace gfx2::grimeshell {

using Vec3 = std::array<float, 3>;
struct Tri { Vec3 a{}, b{}, c{}; };
constexpr float kExteriorVisibility = .15f;
constexpr unsigned kCells = 64, kDirections = 32;

struct Grid {
    Vec3 lo{}; float size = 0; std::array<int, 3> dims{}; std::vector<uint8_t> solid;
    bool valid() const noexcept { return size > 0 && !solid.empty(); }
    bool inside(int x, int y, int z) const noexcept { return x >= 0 && y >= 0 && z >= 0 && x < dims[0] && y < dims[1] && z < dims[2]; }
    uint8_t& at(int x, int y, int z) noexcept { return solid[(size_t(z) * dims[1] + y) * dims[0] + x]; }
    uint8_t get(int x, int y, int z) const noexcept { return solid[(size_t(z) * dims[1] + y) * dims[0] + x]; }
};

inline Vec3 sub(const Vec3& a, const Vec3& b) noexcept { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
inline Vec3 cross(const Vec3& a, const Vec3& b) noexcept { return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]}; }
inline float dot(const Vec3& a, const Vec3& b) noexcept { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
inline float length(const Vec3& a) noexcept { return std::sqrt(dot(a, a)); }
// Outward face normal. MR car models wind their triangles so that cross(c - a, b - a) agrees with the authored vertex
// normals (Kia 2322/2323, Patrol 1997/1998 triangles).
inline Vec3 outward(const Tri& t) noexcept { return cross(sub(t.c, t.a), sub(t.b, t.a)); }

// Unit directions spread evenly over the sphere (Fibonacci lattice).
inline const std::array<Vec3, kDirections>& directions() noexcept {
    static const auto d = [] { std::array<Vec3, kDirections> r{}; const double g = (1 + std::sqrt(5.0)) / 2;
        for (unsigned i = 0; i < kDirections; ++i) { const double phi = std::acos(1 - 2 * (i + .5) / kDirections), th = 2 * 3.14159265358979 * (i + .5) / g;
            r[i] = {float(std::cos(th) * std::sin(phi)), float(std::cos(phi)), float(std::sin(th) * std::sin(phi))}; }
        return r; }();
    return d;
}

// Occupancy grid of the model; one empty cell of margin on every side.
inline Grid build(const std::vector<Tri>& tris, unsigned cells = kCells) {
    Grid g; if (tris.empty() || !cells) return g;
    Vec3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f};
    for (const auto& t : tris) for (const auto* p : {&t.a, &t.b, &t.c}) for (unsigned k = 0; k < 3; ++k) { lo[k] = std::min(lo[k], (*p)[k]); hi[k] = std::max(hi[k], (*p)[k]); }
    const float extent = std::max({hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]});
    if (!std::isfinite(extent) || extent <= 1e-4f || extent > 100.f) return g;
    g.size = extent / float(cells);
    for (unsigned k = 0; k < 3; ++k) { g.lo[k] = lo[k] - g.size; g.dims[k] = int(std::ceil((hi[k] - g.lo[k]) / g.size)) + 2; }
    g.solid.assign(size_t(g.dims[0]) * g.dims[1] * g.dims[2], 0);
    for (const auto& t : tris) {
        const auto ab = sub(t.b, t.a), ac = sub(t.c, t.a);
        const float edge = std::max({length(ab), length(ac), length(sub(t.c, t.b))});
        const int n = std::clamp(int(std::ceil(edge / (g.size * .5f))) + 1, 1, 512);
        for (int i = 0; i <= n; ++i) for (int j = 0; i + j <= n; ++j) {
            const float u = float(i) / n, v = float(j) / n;
            const int x = int((t.a[0] + ab[0] * u + ac[0] * v - g.lo[0]) / g.size), y = int((t.a[1] + ab[1] * u + ac[1] * v - g.lo[1]) / g.size),
                      z = int((t.a[2] + ab[2] * u + ac[2] * v - g.lo[2]) / g.size);
            if (g.inside(x, y, z)) g.at(x, y, z) = 1;
        }
    }
    return g;
}

// Share of the rays into the hemisphere around n that leave the grid unblocked, from point c (rays start 1.5 cells off).
inline float visibility_at(const Grid& g, const Vec3& c, const Vec3& n) noexcept {
    const Vec3 start{c[0] + n[0] * 1.5f * g.size, c[1] + n[1] * 1.5f * g.size, c[2] + n[2] * 1.5f * g.size};
    const int steps = 2 * (g.dims[0] + g.dims[1] + g.dims[2]);
    unsigned front = 0, escaped = 0;
    for (const auto& d : directions()) {
        if (dot(n, d) <= .05f) continue;
        ++front;
        for (int s = 0; s <= steps; ++s) {
            const float k = s * .5f * g.size;
            const int x = int(std::floor((start[0] + d[0] * k - g.lo[0]) / g.size)), y = int(std::floor((start[1] + d[1] * k - g.lo[1]) / g.size)),
                      z = int(std::floor((start[2] + d[2] * k - g.lo[2]) / g.size));
            if (!g.inside(x, y, z)) { ++escaped; break; }
            if (g.get(x, y, z)) break;
        }
    }
    return front ? float(escaped) / float(front) : 1.f;
}
// Owner review 4: a single centroid sample on the outward side cut whole large panels behind spare wheels (Tata,
// NewRav, Patrol) and imported faces with reversed winding (Lancer Evo IV front). A triangle now counts as visible
// from its centroid and from three points 60 % of the way to its corners, on both sides; the first sample that reaches
// `stop` ends the search. Crew, helmets and seats stay at about 0 (offline check on Patrol, NewRav, Kia, Lancer).
inline float visibility(const Grid& g, const Tri& t, float stop = 2.f) noexcept {
    if (!g.valid()) return 1.f;
    auto n = outward(t); const float len = length(n); if (!(len > 1e-12f)) return 1.f;
    for (auto& v : n) v /= len;
    const Vec3 m{-n[0], -n[1], -n[2]};
    const Vec3 c{(t.a[0] + t.b[0] + t.c[0]) / 3, (t.a[1] + t.b[1] + t.c[1]) / 3, (t.a[2] + t.b[2] + t.c[2]) / 3};
    float best = 0;
    for (int i = -1; i < 3; ++i) {
        Vec3 q = c;
        if (i >= 0) { const Vec3& v = i == 0 ? t.a : i == 1 ? t.b : t.c; for (unsigned k = 0; k < 3; ++k) q[k] = c[k] + (v[k] - c[k]) * .6f; }
        best = std::max(best, visibility_at(g, q, n)); if (best >= stop) return best;
        best = std::max(best, visibility_at(g, q, m)); if (best >= stop) return best;
    }
    return best;
}
inline bool exterior(const Grid& g, const Tri& t) noexcept { return visibility(g, t, kExteriorVisibility) >= kExteriorVisibility; }

// G1.5 (owner review 5): a spare wheel on the tailgate still hid parts of the rear panel from the sky (Patrol, NewRav,
// Tata). Culling is limited to the cabin: the bounds of the crew and seat draws, extended 0.9 m forward and back, from
// 0.5 m below them upwards, over the full width. Everything else of the car always keeps its grime.
struct Cabin { Vec3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f}; bool valid() const noexcept { return hi[0] >= lo[0]; } };
inline void cabin_add(Cabin& c, const Tri& t) noexcept {
    for (const auto* p : {&t.a, &t.b, &t.c}) for (unsigned k = 0; k < 3; ++k) { c.lo[k] = std::min(c.lo[k], (*p)[k]); c.hi[k] = std::max(c.hi[k], (*p)[k]); }
}
inline bool cabin_contains(const Cabin& c, const Tri& t) noexcept {
    if (!c.valid()) return false;
    const float y = (t.a[1] + t.b[1] + t.c[1]) / 3, z = (t.a[2] + t.b[2] + t.c[2]) / 3;
    return y >= c.lo[1] - .5f && z >= c.lo[2] - .9f && z <= c.hi[2] + .9f;
}

// G3: a glass draw is a windscreen when its area-weighted outward normal faces the front (+z, MR car space) and up
// (windscreens are raked), rather than the sides or the rear. Returns its car-local x/y extent for the wiper mask.
struct GlassFrame { bool windscreen = false; float x0 = 0, x1 = 0, y0 = 0, y1 = 0; };
inline GlassFrame glass_frame(const std::vector<Tri>& tris) noexcept {
    GlassFrame f; Vec3 sum{}; float area = 0; Vec3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f};
    for (const auto& t : tris) { const auto n = outward(t); const float a = length(n); if (!(a > 1e-12f)) continue;
        for (unsigned k = 0; k < 3; ++k) sum[k] += n[k]; area += a;   // |n| = 2 x area: the sum is area-weighted
        for (const auto* p : {&t.a, &t.b, &t.c}) for (unsigned k = 0; k < 3; ++k) { lo[k] = std::min(lo[k], (*p)[k]); hi[k] = std::max(hi[k], (*p)[k]); } }
    if (!(area > 1e-8f)) return f;
    const Vec3 m{sum[0] / area, sum[1] / area, sum[2] / area};
    f.windscreen = m[2] > .35f && m[1] > -.1f && std::fabs(m[0]) < .5f && hi[0] - lo[0] > .3f;
    f.x0 = lo[0]; f.x1 = hi[0]; f.y0 = lo[1]; f.y1 = hi[1]; return f;
}

} // namespace gfx2::grimeshell
