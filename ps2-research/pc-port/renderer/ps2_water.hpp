#pragma once
// COURSE-WATER1 portable core (no D3D, Windows or proxy types): the PS2 water shaders of SLES_509.06 for the proxy
// PS2Water=1 path (ps2_water_pilot.hpp) and any later PS2 PC-port renderer.
//
// Modes (material $shader, 3a6c58 registry): 9 puddle, 10 water, 19 waterfall/waterall. Every water strip is drawn twice
// on the same vertices (GS dumps, docs/course-water1/README.md):
//   primary   = course map (CT16, alpha 1.0) x vertex colour, (Cs-Cd)*As+Cd, fog, Z test GEQUAL, Z write
//   secondary = WATERSURFACE2 x vertex colour; puddle: Cs*56/128+Cd, TCC0, no fog;  water: (Cs-Cd)*As+Cd, fog;
//               both without Z write. Waterfall: WATERFALL / WATERFALL2, (Cs-Cd)*As+Cd, fog, Z write in both layers.
// UV / colour (float32, the order of the EE code; tools/ps2_water_model.py is the reference, the tests compare both):
//   328c90 table L[i] = sinf(i * C * 2^-12); 316808 T = counter / 150 (frozen while paused)
//   320938 puddle RGBA from the ground gap (offline, in the asset); 320c78 puddle UV per frame with the camera rows
//   321098 water UV once at load (offline, in the asset); 321838 waterfall V per frame
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

namespace ps2water {

inline constexpr char kMagic[8] = {'P','S','2','W','T','R','0','1'};
inline constexpr uint32_t kVersion = 1;
inline constexpr size_t kMaximumAssetBytes = 32u * 1024u * 1024u;
inline constexpr uint32_t kModePuddle = 9, kModeWater = 10, kModeWaterfall = 19;
// The counter of 316808 is the game frame counter: solved per field from the camera-free puddle UV of six Turkey2 dumps it
// steps 11 times in 18 fields (30.6 per second); the waterfall dump agrees and the Spain_S2 dinghy advances ~0.6 spline
// ticks per field. PS2 draws every field with interpolated poses, the game state runs at ~30 per second
// (docs/course-water1/README.md). Same cadence as ps2spline::kTicksPerSecond.
inline constexpr double kCountsPerSecond = 30.0;
inline constexpr float kPhaseDivisor = 150.f;       // 316808: T = float(counter) / 150.0

struct Texture { uint32_t width = 0, height = 0; std::vector<uint32_t> argb; };     // rows in D3D order (row 0 = v 0)
struct Vertex { float position[3]{}, normal[3]{}, uv[2]{}; uint8_t rgba[4]{}; float water_uv[4]{}; };
struct Part { uint32_t mode = 0, primary = 0, secondary = 0, clamp = 0, first = 0, count = 0; float first_y = 0.f; };
struct Key { uint32_t triangles = 0, source = 0; std::array<uint8_t, 32> sha{}; uint32_t first_part = 0, parts = 0; };
struct Course { std::string id; uint32_t first_key = 0, keys = 0, flags = 0; };
struct Asset {
    std::vector<Texture> textures;
    std::vector<Course> courses;
    std::vector<Key> keys;
    std::vector<Part> parts;
    std::vector<Vertex> vertices;
};

// Output vertex of one pass: the layout of D3DFVF_XYZ | D3DFVF_DIFFUSE | D3DFVF_TEX1 (and ps2port::ObjectVertex).
struct PassVertex { float x, y, z; uint32_t color; float u, v; };
static_assert(sizeof(PassVertex) == 24, "PassVertex must match the XYZ|DIFFUSE|TEX1 vertex");

// ---- asset ------------------------------------------------------------------------------------------------------------

namespace detail {
struct Reader {
    const uint8_t* p; size_t n, at = 0; bool ok = true;
    template<class T> T get() noexcept { T v{}; if (!ok || n - at < sizeof(T)) { ok = false; return v; } std::memcpy(&v, p + at, sizeof(T)); at += sizeof(T); return v; }
    const uint8_t* bytes(size_t size) noexcept { if (!ok || n - at < size) { ok = false; return nullptr; } const auto* r = p + at; at += size; return r; }
};
inline bool finite(float v) noexcept { return std::isfinite(v) && std::fabs(v) < 1.0e6f; }
}  // namespace detail

inline bool decode_asset(const uint8_t* p, size_t n, Asset& out) noexcept {
    out = {};
    if (!p || n < 36 || n > kMaximumAssetBytes || std::memcmp(p, kMagic, 8)) return false;
    try {
        detail::Reader r{p, n, 8};
        const uint32_t version = r.get<uint32_t>(), textures = r.get<uint32_t>(), courses = r.get<uint32_t>();
        const uint32_t keys = r.get<uint32_t>(), parts = r.get<uint32_t>(), vertices = r.get<uint32_t>(), reserved = r.get<uint32_t>();
        if (!r.ok || version != kVersion || reserved || !textures || textures > 64 || !courses || courses > 64 || !keys || keys > 4096 ||
            !parts || parts > 16384 || !vertices || vertices > 1000000 || vertices % 3) return false;
        Asset a;
        for (uint32_t i = 0; i < textures; ++i) {
            Texture t; t.width = r.get<uint32_t>(); t.height = r.get<uint32_t>();
            if (!r.ok || !t.width || !t.height || t.width > 512 || t.height > 512 || (t.width & (t.width - 1)) || (t.height & (t.height - 1))) return false;
            const auto* px = r.bytes(size_t(t.width) * t.height * 4); if (!px) return false;
            t.argb.resize(size_t(t.width) * t.height); std::memcpy(t.argb.data(), px, t.argb.size() * 4);
            a.textures.push_back(std::move(t));
        }
        uint32_t next_key = 0;
        for (uint32_t i = 0; i < courses; ++i) {
            const auto* id = r.bytes(48); Course c; c.first_key = r.get<uint32_t>(); c.keys = r.get<uint32_t>(); c.flags = r.get<uint32_t>();
            if (!r.ok || !id) return false;
            size_t len = 0; while (len < 48 && id[len]) ++len;
            if (!len || len == 48) return false;
            for (size_t k = 0; k < 48; ++k) if (k < len ? (id[k] < 32 || id[k] > 126) : id[k] != 0) return false;
            c.id.assign(reinterpret_cast<const char*>(id), len);
            if (c.first_key != next_key || !c.keys || c.keys > keys - next_key || c.flags > 1) return false;
            next_key += c.keys; a.courses.push_back(std::move(c));
        }
        if (next_key != keys) return false;
        uint32_t next_part = 0;
        for (uint32_t i = 0; i < keys; ++i) {
            Key k; k.triangles = r.get<uint32_t>(); k.source = r.get<uint32_t>();
            const auto* sha = r.bytes(32); k.first_part = r.get<uint32_t>(); k.parts = r.get<uint32_t>();
            if (!r.ok || !sha || !k.triangles || k.triangles > 65535 || (k.source != 1 && k.source != 2) ||
                k.first_part != next_part || !k.parts || k.parts > parts - next_part) return false;
            std::memcpy(k.sha.data(), sha, 32); next_part += k.parts; a.keys.push_back(k);
        }
        if (next_part != parts) return false;
        uint32_t next_vertex = 0;
        for (uint32_t i = 0; i < parts; ++i) {
            Part q; q.mode = r.get<uint32_t>(); q.primary = r.get<uint32_t>(); q.secondary = r.get<uint32_t>(); q.clamp = r.get<uint32_t>();
            q.first = r.get<uint32_t>(); q.count = r.get<uint32_t>(); q.first_y = r.get<float>();
            if (!r.ok || (q.mode != kModePuddle && q.mode != kModeWater && q.mode != kModeWaterfall) || q.primary >= textures ||
                q.secondary >= textures || q.clamp > 3 || q.first != next_vertex || !q.count || q.count % 3 ||
                q.count > vertices - next_vertex || !detail::finite(q.first_y)) return false;
            next_vertex += q.count; a.parts.push_back(q);
        }
        if (next_vertex != vertices) return false;
        // Every key's parts cover exactly its triangle count.
        for (const auto& k : a.keys) {
            uint64_t sum = 0; for (uint32_t i = 0; i < k.parts; ++i) sum += a.parts[k.first_part + i].count;
            if (sum != uint64_t(k.triangles) * 3) return false;
        }
        a.vertices.resize(vertices);
        for (auto& v : a.vertices) {
            for (auto& c : v.position) c = r.get<float>();
            for (auto& c : v.normal) c = r.get<float>();
            for (auto& c : v.uv) c = r.get<float>();
            for (auto& c : v.rgba) c = r.get<uint8_t>();
            for (auto& c : v.water_uv) c = r.get<float>();
            if (!r.ok) return false;
            for (float c : v.position) if (!detail::finite(c)) return false;
            for (float c : v.normal) if (!detail::finite(c)) return false;
            for (float c : v.uv) if (!detail::finite(c)) return false;
            for (float c : v.water_uv) if (!detail::finite(c)) return false;
        }
        if (!r.ok || r.at != n) return false;
        out = std::move(a); return true;
    } catch (...) { out = {}; return false; }
}

inline bool course_id_equal(std::string_view a, std::string_view b) noexcept {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        char x = a[i], y = b[i];
        if (x >= 'A' && x <= 'Z') x = char(x + 32); if (y >= 'A' && y <= 'Z') y = char(y + 32);
        if (x == '\\') x = '/'; if (y == '\\') y = '/';
        if (x != y) return false;
    }
    return true;
}
inline size_t course_index(const Asset& a, std::string_view id) noexcept {
    for (size_t i = 0; i < a.courses.size(); ++i) if (course_id_equal(a.courses[i].id, id)) return i;
    return SIZE_MAX;
}

// ---- float32 math of the EE code ------------------------------------------------------------------------------------

inline float circle() noexcept { uint32_t b = 0x40c90fdbu; float f; std::memcpy(&f, &b, 4); return f; }   // 15acc8

inline const std::array<float, 4096>& table() noexcept {
    static const std::array<float, 4096> t = [] {
        std::array<float, 4096> out{};
        const float c = circle();
        for (int i = 0; i < 4096; ++i) {
            volatile float arg = static_cast<float>(i) * c;   // fVar5 * fVar3 * 0.00024414062 (328c90)
            arg = arg * 0.000244140625f;
            out[size_t(i)] = static_cast<float>(std::sin(static_cast<double>(arg)));
        }
        return out;
    }();
    return t;
}
inline float index_scale() noexcept { static const float s = 4096.0f / circle(); return s; }
// EE cvt.w.s (round toward zero) and the caller's `& 0xfff`.
inline uint32_t trunc_index(float x) noexcept {
    if (!(std::fabs(x) < 2147483520.f)) return 0;
    return static_cast<uint32_t>(static_cast<int32_t>(x));
}
inline float lut(uint32_t index) noexcept { return table()[index & 0xfffu]; }

// The inline float -> int sequence of 321098 / 321838 (detail_runtime.ee_floor): floor, except normalized values in
// (-1, 0) give 0.
inline int32_t inline_int(float x) noexcept {
    if (!(std::fabs(x) < 2147483520.f)) return 0;
    uint32_t b; std::memcpy(&b, &x, 4);
    const int32_t exponent = int32_t((b & 0x7fffffffu) >> 23) - 127;
    const int32_t sign = (b >> 31) ? -1 : 0;
    const uint32_t mantissa = b & 0x7fffffu;
    const uint32_t magnitude = (((mantissa | 0x800000u) << 8)) >> (uint32_t(31 - exponent) & 31u);
    int32_t value = int32_t(exponent >= 0 ? magnitude : 0u) ^ sign;
    const uint32_t mask = (uint32_t(1) << (uint32_t(31 - (exponent > 0 ? exponent : 0)) & 31u)) - 1u;
    if (((mantissa << 8) & mask) == 0) value -= sign;
    return value;
}

inline float phase(uint32_t counter) noexcept { return static_cast<float>(counter) / kPhaseDivisor; }

struct Waves { float a, b; };
inline Waves waves(float x, float z, float t, float frequency) noexcept {
    const float s = index_scale();
    const float a = x * frequency + t * 1.61368f;
    const float b = z * frequency + t;
    const float b178 = b * 1.78f;
    const float A = lut(trunc_index((a * 1.13f) * s)) - lut(trunc_index(b178 * s) + 0x400u);
    const float B1 = lut(trunc_index((a * 2.19f) * s) + 0x400u);
    const float B2 = lut(trunc_index((b * 2.93f) * s));
    return {A, B1 + B2};
}

// PS2 camera rows of 42dc00 as 320c78 reads them: (dc00, dc04), (dc10, dc14), (dc20, dc24); PS2 view x right, y down.
struct Basis { float m00, m01, m10, m11, m20, m21; };
inline constexpr Basis kWaterBasis{1.f, 0.f, 0.f, 1.f, 0.f, 0.f};
// From a D3D row-vector view matrix (x right, y up): the y column changes sign.
inline Basis basis_from_view(const float view[4][4]) noexcept {
    return {view[0][0], -view[0][1], view[1][0], -view[1][1], view[2][0], -view[2][1]};
}

struct Uv4 { float u0, v0, u1, v1; };
inline Uv4 puddle_uv(const float p[3], const float n[3], float t, const Basis& m) noexcept {
    const float x = p[0], z = p[2];
    const auto w = waves(x, z, t, 0.1f);
    Uv4 r{};
    r.u0 = x * 0.05f + w.a * 0.05f;
    r.v0 = z * 0.05f + w.b * 0.05f;
    const float px = n[0] + w.a * 0.6f, py = n[1], pz = n[2] + w.b * 0.6f;
    r.v1 = ((px * m.m01 + py * m.m11) + pz * m.m21) * -0.5f + 0.5f;
    r.v1 = r.v1 + z * 0.02f;
    r.u1 = ((px * m.m00 + py * m.m10) + pz * m.m20) * 0.5f + 0.5f;
    r.u1 = r.u1 + x * 0.02f;
    return r;
}
inline Uv4 water_uv(const float p[3], const float n[3], float t) noexcept {   // 321098 before the rebase
    const float x = p[0], z = p[2];
    const auto w = waves(x, z, t, 0.05f);
    Uv4 r{};
    r.u0 = x * 0.01f + w.a * 0.05f;
    r.v0 = z * 0.01f + w.b * 0.05f;
    const float px = n[0] + w.a * 0.6f, py = n[1], pz = n[2] + w.b * 0.6f;
    r.v1 = (((px * 0.0f + py * 1.0f) + pz * 0.0f) * -0.5f + 0.5f) + z * 0.02f;
    r.u1 = (((px * 1.0f + py * 0.0f) + pz * 0.0f) * 0.5f + 0.5f) + x * 0.02f;
    return r;
}
struct WaterfallV { float primary, secondary; };
inline WaterfallV waterfall_v(float source_y, float first_y, float t) noexcept {
    const float doubled = t + t, quadrupled = t * 4.0f;
    const float base = static_cast<float>(inline_int(first_y * 0.05f + 6.0f));
    const float y = source_y * 0.05f;
    return {(y + (doubled - static_cast<float>(inline_int(doubled)))) - base,
            (y + (quadrupled - static_cast<float>(inline_int(quadrupled)))) - base};
}

// PS2 packet colour = source byte * 0.5 (128 = 1.0); D3D MODULATE / blend use byte / 255.
inline uint8_t gs_byte(uint8_t source) noexcept {
    const uint32_t half = source >> 1;
    const uint32_t v = (half * 255u + 64u) / 128u;
    return static_cast<uint8_t>(v > 255u ? 255u : v);
}
inline uint32_t argb(const uint8_t rgba[4]) noexcept {
    return (uint32_t(gs_byte(rgba[3])) << 24) | (uint32_t(gs_byte(rgba[0])) << 16) | (uint32_t(gs_byte(rgba[1])) << 8) | gs_byte(rgba[2]);
}
// Puddle second layer: Cs * 56/128 + Cd. D3D has no FIX factor; the alpha of the second stage carries 56/128 (112/255).
inline constexpr uint32_t kPuddleFixFactor = 0x70000000u;

// The two pass vertex arrays of one part at phase t (camera rows m for puddles).
inline bool build_part(const Asset& a, const Part& part, float t, const Basis& m, std::vector<PassVertex>& first,
                       std::vector<PassVertex>& second) noexcept {
    try {
        first.resize(part.count); second.resize(part.count);
        for (uint32_t i = 0; i < part.count; ++i) {
            const auto& v = a.vertices[part.first + i];
            const uint32_t c = argb(v.rgba);
            PassVertex p{v.position[0], v.position[1], v.position[2], c, 0.f, 0.f}, s = p;
            if (part.mode == kModePuddle) {
                const auto uv = puddle_uv(v.position, v.normal, t, m);
                p.u = uv.u0; p.v = uv.v0; s.u = uv.u1; s.v = uv.v1;
            } else if (part.mode == kModeWater) {
                p.u = v.water_uv[0]; p.v = v.water_uv[1]; s.u = v.water_uv[2]; s.v = v.water_uv[3];
            } else {
                const auto wv = waterfall_v(v.position[1], part.first_y, t);
                p.u = v.uv[0]; p.v = wv.primary; s.u = v.uv[0]; s.v = wv.secondary;
            }
            if (!std::isfinite(p.u) || !std::isfinite(p.v) || !std::isfinite(s.u) || !std::isfinite(s.v)) return false;
            first[i] = p; second[i] = s;
        }
        return true;
    } catch (...) { first.clear(); second.clear(); return false; }
}

// Pass material (the D3D values are applied by the pilot): blend, fog, depth write, alpha source.
enum class Blend : uint8_t { SourceAlpha, AddFix56 };
struct PassMaterial { Blend blend; bool fog; bool z_write; bool texture_alpha; };
inline PassMaterial pass_material(uint32_t mode, int pass) noexcept {
    if (pass == 0) return {Blend::SourceAlpha, true, true, true};
    if (mode == kModePuddle) return {Blend::AddFix56, false, false, false};
    if (mode == kModeWater) return {Blend::SourceAlpha, true, false, true};
    return {Blend::SourceAlpha, true, true, true};   // waterfall: ZMSK 0 in both contexts
}

// 2x2 box reduction of an A8R8G8B8 level (mip chain; the GS used trilinear MMIN 5 with up to 4 levels).
inline std::vector<uint32_t> half_level(const std::vector<uint32_t>& src, uint32_t w, uint32_t h) {
    const uint32_t hw = w > 1 ? w / 2 : 1, hh = h > 1 ? h / 2 : 1;
    std::vector<uint32_t> dst(size_t(hw) * hh);
    for (uint32_t y = 0; y < hh; ++y) for (uint32_t x = 0; x < hw; ++x) {
        uint32_t sum[4]{};
        for (uint32_t dy = 0; dy < 2; ++dy) for (uint32_t dx = 0; dx < 2; ++dx) {
            const uint32_t sx = w > 1 ? 2 * x + dx : 0, sy = h > 1 ? 2 * y + dy : 0;
            const uint32_t p = src[size_t(sy) * w + sx];
            for (int k = 0; k < 4; ++k) sum[k] += (p >> (8 * k)) & 0xffu;
        }
        uint32_t out = 0; for (int k = 0; k < 4; ++k) out |= ((sum[k] + 2) / 4) << (8 * k);
        dst[size_t(y) * hw + x] = out;
    }
    return dst;
}

// Order-free geometry key of a draw: SHA-256 input = the triangles' 36-byte corner sets (each sorted by bytes), sorted.
// The hash itself comes from the caller (proxy provenance helper); this builds the canonical bytes.
inline bool canonical_triangles(const float* positions, size_t triangles, std::vector<uint8_t>& out) noexcept {
    try {
        std::vector<std::array<uint8_t, 36>> tris(triangles);
        for (size_t t = 0; t < triangles; ++t) {
            std::array<std::array<uint8_t, 12>, 3> c{};
            for (size_t k = 0; k < 3; ++k) std::memcpy(c[k].data(), positions + (t * 3 + k) * 3, 12);
            std::sort(c.begin(), c.end());
            for (size_t k = 0; k < 3; ++k) std::memcpy(tris[t].data() + 12 * k, c[k].data(), 12);
        }
        std::sort(tris.begin(), tris.end());
        out.resize(triangles * 36);
        for (size_t t = 0; t < triangles; ++t) std::memcpy(out.data() + 36 * t, tris[t].data(), 36);
        return true;
    } catch (...) { out.clear(); return false; }
}

// Host time -> PS2 renderer counter (kCountsPerSecond), frozen while paused; 0.25 s stall clamp (SplineClock rule).
class Clock {
    double pending_ = 0.0;
    uint32_t counter_ = 0;
public:
    uint32_t counter() const noexcept { return counter_; }
    float t() const noexcept { return phase(counter_); }
    void advance(double seconds, bool paused) noexcept {
        if (paused || !(seconds > 0.0)) return;
        if (seconds > 0.25) seconds = 0.25;
        pending_ += seconds * kCountsPerSecond;
        const double whole = std::floor(pending_);
        pending_ -= whole;
        counter_ += static_cast<uint32_t>(whole);
    }
    void set(uint32_t counter) noexcept { counter_ = counter; pending_ = 0.0; }
};

}  // namespace ps2water
