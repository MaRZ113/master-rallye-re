#pragma once
// R-SURFACE1 G1: static grime look. Portable part (no D3D): procedural textures, zone weights, texture matrices and the
// colour factor. The D3D pass lives next to the Atmosphere headlight pass (atmosphere_native.hpp grime_overlay()).
//
// Pass over the body draw that just ran (same VB/IB/range/WORLD/fog):
//   stage 0: colour = DIFFUSE (the lit vertex colour) x TFACTOR.rgb (grime tint)       alpha = TFACTOR.a (level L)
//   stage 1: atlas, camera-space position -> car-local side projection (tiles ~1/3 of the car length)
//            colour = MODULATE2X(atlas detail, current)    alpha = ADDSIGNED2X(noise, L) = 2(n + L - .5), n in [0,.5]
//            -> L = 0: nothing; L = .5: noise peaks only; L = 1: full coverage (threshold growth, not a fade)
//   stage 2: zone ramp, the same projection normalised to the car bounds (u along the length, v top->bottom)
//            colour = current                               alpha = ramp.a x current (height caps: roof .2, upper .35, lower .85)
//   blend SRCALPHA/INVSRCALPHA, z-write off, z LESSEQUAL. L == 0 or Enabled=0 -> no pass at all (identical frame).
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>
#include <string>
#include <initializer_list>
namespace gfx2::grimeoverlay {

using Vec3 = std::array<float, 3>;
using Mat = std::array<float, 16>;   // D3D row-vector layout, m[row*4+col]

struct Look {
    bool enabled = false;
    float level = 0.f;                             // StartLevel 0..1 (G1: fixed for every car)
    float mud = 0.f;                               // StartMud 0..1: tint mix dust -> mud
    Vec3 dust{.68f, .57f, .43f}, mud_tint{.30f, .24f, .17f};
    float max_distance = 80.f;                     // metres (game units); farther bodies skip the pass
    // G2: per-car dynamic grime (accumulation, wash, drying) instead of the fixed StartLevel.
    bool dynamic = false; float race_start = 0.f, rate = 1.f, dry_seconds = 45.f;
    // G2.1: opacity of a fully dusty patch (mud is always 1): thin dust dims the paint and its reflection instead of
    // hiding them. SurfaceTint: share of the surface colour (particles) in the tint, 0 = configured tints only.
    float dust_opacity = .8f, surface_tint = .75f;
    // G3: windscreen wiper arcs stay clean (Wipers=1); wet sheen strength of a fully wet car (Sheen, 0 = off).
    bool wipers = true; float sheen = .35f;
};

// Tileable value noise (integer lattice hash, smooth interpolation), period `period` cells.
inline float lattice(int x, int y, int period, uint32_t seed) noexcept {
    x = ((x % period) + period) % period; y = ((y % period) + period) % period;
    uint32_t h = uint32_t(x) * 374761393u + uint32_t(y) * 668265263u + seed * 2246822519u;
    h = (h ^ (h >> 13)) * 1274126177u; h ^= h >> 16;
    return float(h & 0xffffu) / 65535.f;
}
inline float value_noise(float u, float v, int period, uint32_t seed) noexcept {
    const float x = u * period, y = v * period; const int x0 = int(std::floor(x)), y0 = int(std::floor(y));
    float fx = x - x0, fy = y - y0; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
    const float a = lattice(x0, y0, period, seed), b = lattice(x0 + 1, y0, period, seed), c = lattice(x0, y0 + 1, period, seed), d = lattice(x0 + 1, y0 + 1, period, seed);
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy;
}
// Large blobs (coverage) and a finer detail layer; both tile over [0,1)^2.
inline float coverage_noise(float u, float v) noexcept {
    const float n = .55f * value_noise(u, v, 3, 11) + .28f * value_noise(u, v, 7, 23) + .17f * value_noise(u, v, 17, 37);
    return std::clamp((n - .2f) / .6f, 0.f, 1.f);
}
inline float detail_noise(float u, float v) noexcept {
    return .6f * value_noise(u, v, 23, 41) + .4f * value_noise(u, v, 61, 53);
}
// Atlas texel (A8R8G8B8): rgb = grey detail around .5 (MODULATE2X keeps the tint brightness), a = coverage noise in [0,.5].
inline uint32_t atlas_texel(unsigned x, unsigned y, unsigned size) noexcept {
    const float u = (x + .5f) / size, v = (y + .5f) / size;
    const float grey = std::clamp(.40f + .22f * detail_noise(u, v), 0.f, 1.f), a = .5f * coverage_noise(u, v);
    const uint32_t g = uint32_t(std::lround(grey * 255)), al = uint32_t(std::lround(a * 255));
    return (al << 24) | (g << 16) | (g << 8) | g;
}
inline float smooth(float a, float b, float x) noexcept { const float t = std::clamp((x - a) / (b - a), 0.f, 1.f); return t * t * (3 - 2 * t); }
// Zone weight: u along the car length (0..1), v from the top (0) to the bottom (1). Design caps: roof <= .2 (.12 used), upper body
// <= .35, lower body <= .85; both ends (rear plate, bumpers, wheel arches) get more, capped at .9.
inline float zone_weight(float u, float v) noexcept {
    float w = .12f + (.35f - .12f) * smooth(.15f, .45f, v) + (.85f - .35f) * smooth(.45f, .80f, v);
    const float end = std::max(1.f - smooth(.0f, .16f, u), smooth(.84f, 1.f, u));
    w += .22f * end * smooth(.2f, .55f, v);   // front/rear plate and wheel arches
    return std::clamp(w, 0.f, .9f);
}
inline uint32_t ramp_texel(unsigned x, unsigned y, unsigned w, unsigned h) noexcept {
    const float u = (x + .5f) / w, v = (y + .5f) / h;
    return (uint32_t(std::lround(zone_weight(u, v) * 255)) << 24) | 0xffffffu;
}
// ---- G2 dynamic grime: per-car zone texture -------------------------------------------------------------------------
// The 8 zones of grime::CarGrime: 0 front_low, 1 front_arch, 2 side_low_l, 3 side_low_r, 4 rear_arch, 5 rear, 6 bonnet,
// 7 roof. u runs along the car length from the rear (0) to the front (1, +z in MR car space), v from the top (0) down.
// Amount of one zone = dust + mud (both cover the paint), capped at 1.
inline float zone_amount(float u, float v, const std::array<float, 8>& a) noexcept {
    const float side = .5f * (a[2] + a[3]);
    // Lower body along the length: rear, rear arch, sides, front arch, front.
    const float lower = u < .15f ? a[5] + (a[4] - a[5]) * smooth(.05f, .2f, u)
                      : u < .5f ? a[4] + (side - a[4]) * smooth(.25f, .45f, u)
                      : u < .85f ? side + (a[1] - side) * smooth(.55f, .75f, u)
                      : a[1] + (a[0] - a[1]) * smooth(.8f, .95f, u);
    const float upper = a[7] + (a[6] - a[7]) * smooth(.55f, .75f, u);   // roof -> bonnet towards the front
    return std::clamp(upper + (lower - upper) * smooth(.3f, .6f, v), 0.f, 1.f);
}
// Zone texel: alpha = the per-zone threshold level for the atlas noise, shape (zone_weight, max .9) x zone amount
// normalised so that amount 1 reaches the full shape. Stage 2 makes coverage 2 (noise + alpha - .5): patches appear
// first where the shape is high and the zone is dirty, the roof stays light.
inline uint32_t car_ramp_texel(unsigned x, unsigned y, unsigned w, unsigned h, const std::array<float, 8>& amounts) noexcept {
    const float u = (x + .5f) / w, v = (y + .5f) / h;
    // G3.2 (owner: can dust cover the whole car?): the body shape caps the upper body only while the car is lightly dirty;
    // a heavily dirty zone (amount -> 1) loses the cap, so the whole car can end up covered.
    const float amount = zone_amount(u, v, amounts), shape = zone_weight(u, v) / .9f;
    const float level = std::clamp(amount * (shape + (1.f - shape) * amount * amount), 0.f, 1.f);
    return (uint32_t(std::lround(level * 255)) << 24) | 0xffffffu;
}
// Car tint (TFACTOR rgb): dust -> mud by the mud share, fresh mud dark and dried mud lighter (about 90 s), wet darker.
struct CarTone { float dust = 0, mud = 0, wet = 0, mud_age = 0; Vec3 dust_rgb{}, mud_rgb{}; };
inline float luma(const Vec3& c) noexcept { return .299f * c[0] + .587f * c[1] + .114f * c[2]; }
// G2.1: surface colour (the particles that hit the car) with the brightness of the configured tint: the hue follows the
// ground, the exposure stays stable at night and on bright particle textures. share 0 = configured tint only.
inline Vec3 surface_tone(const Vec3& configured, const Vec3& surface, float share) noexcept {
    const float ls = luma(surface); if (!(ls > .02f) || share <= 0) return configured;
    const float k = luma(configured) / ls; Vec3 out{};
    for (unsigned i = 0; i < 3; ++i) out[i] = std::clamp(configured[i] + (surface[i] * k - configured[i]) * std::clamp(share, 0.f, 1.f), 0.f, 1.f);
    return out;
}
inline Vec3 car_tint(const Look& l, const CarTone& t) noexcept {
    const float total = t.dust + t.mud, share = total > 1e-4f ? std::clamp(t.mud / total, 0.f, 1.f) : std::clamp(l.mud, 0.f, 1.f);
    const float dried = smooth(0.f, 90.f, t.mud_age) * .45f;
    const float wet = 1.f - .35f * std::clamp(t.wet, 0.f, 1.f);
    const Vec3 dust = surface_tone(l.dust, t.dust_rgb, l.surface_tint), mud_fresh = surface_tone(l.mud_tint, t.mud_rgb, l.surface_tint);
    Vec3 out{};
    for (unsigned i = 0; i < 3; ++i) { const float mud = mud_fresh[i] + (dust[i] - mud_fresh[i]) * dried; out[i] = std::clamp((dust[i] + (mud - dust[i]) * share) * wet, 0.f, 1.f); }
    return out;
}
// G3.3: displayed wetness eases toward the simulated one (the state changes in 0.5 s steps and a water crossing wets a
// car in about a second): rise time constant 2.5 s, dry 4 s. The sheen follows a smoothstep of it, so a damp car
// barely shines and a soaked one shines fully.
inline float ease_wet(float shown, float target, double seconds) noexcept {
    if (!(seconds > 0) || !std::isfinite(shown)) return std::isfinite(target) ? target : 0.f;
    const double tau = target > shown ? 2.5 : 4.0; const float k = float(1.0 - std::exp(-std::min(seconds, 5.0) / tau));
    return std::clamp(shown + (target - shown) * k, 0.f, 1.f);
}
inline float sheen_curve(float wet) noexcept { const float w = std::clamp(wet, 0.f, 1.f); return w * w * (3.f - 2.f * w); }
// Patch opacity of a car: dust_opacity for pure dust, 1 for pure mud.
inline float car_opacity(const Look& l, const CarTone& t) noexcept {
    const float total = t.dust + t.mud, share = total > 1e-4f ? std::clamp(t.mud / total, 0.f, 1.f) : std::clamp(l.mud, 0.f, 1.f);
    const float d = std::clamp(l.dust_opacity, 0.f, 1.f); return d + (1.f - d) * share;
}
inline uint32_t car_factor(const Vec3& tint, float alpha) noexcept {
    auto ch = [&](float v) { return uint32_t(std::lround(std::clamp(v, 0.f, 1.f) * 255)); };
    return (ch(alpha) << 24) | (ch(tint[0]) << 16) | (ch(tint[1]) << 8) | ch(tint[2]);
}

// ---- G3 windscreen wiper arcs ----------------------------------------------------------------------------------------
// u across the windscreen (0..1 along car-local x), v from its top (0) to its bottom (1). Two wipers pivot just below
// the bottom edge at u = .28 and .72 and sweep half-discs of radius .58; inside them the glass stays clean.
inline float wiper_clean(float u, float v) noexcept {
    float best = 0;
    for (float pu : {.28f, .72f}) {
        const float du = (u - pu) * 1.6f, dv = v - 1.02f, d = std::sqrt(du * du + dv * dv);   // 1.6: windscreens are wider than tall
        best = std::max(best, 1.f - smooth(.52f, .6f, d));
    }
    return best;
}
// Wiper texel: alpha = glass threshold level outside the arcs, 0 inside (rgb white).
inline uint32_t wiper_texel(unsigned x, unsigned y, unsigned w, unsigned h, float level) noexcept {
    const float u = (x + .5f) / w, v = (y + .5f) / h;
    return (uint32_t(std::lround(std::clamp(level * (1.f - wiper_clean(u, v)), 0.f, 1.f) * 255)) << 24) | 0xffffffu;
}
// Glass threshold level of a car: half the car's mean dirt, half the dirtiest front zone (spray from the cars ahead and
// the own front wheels). G3.2: the upper-body zone level used in G3 stayed near 5 %, so glass looked clean.
inline float windscreen_level(const std::array<float, 8>& amounts) noexcept {
    float mean = 0; for (float a : amounts) mean += a / 8;
    return std::clamp(.5f * mean + .5f * std::max({amounts[0], amounts[1], amounts[6]}), 0.f, 1.f);
}
// A wiper-texture point outside both arcs (side and rear glass: one even film at the glass level).
constexpr float kGlassFilmU = .03f, kGlassFilmV = .05f;
// Car-local windscreen frame -> wiper uv: u = (x - x0) / (x1 - x0), v = (y1 - y) / (y1 - y0).
inline Mat wiper_matrix(float x0, float x1, float y0, float y1) noexcept {
    const float w = std::max(x1 - x0, 1e-4f), h = std::max(y1 - y0, 1e-4f); Mat m{};
    m[0] = 1.f / w; m[12] = -x0 / w; m[5] = -1.f / h; m[13] = y1 / h; m[15] = 1; return m;
}

// TFACTOR: rgb = dust..mud tint, a = level.
inline uint32_t factor(const Look& l) noexcept {
    const float m = std::clamp(l.mud, 0.f, 1.f);
    auto ch = [&](unsigned i) { return uint32_t(std::lround(std::clamp(l.dust[i] + (l.mud_tint[i] - l.dust[i]) * m, 0.f, 1.f) * 255)); };
    return (uint32_t(std::lround(std::clamp(l.level, 0.f, 1.f) * 255)) << 24) | (ch(0) << 16) | (ch(1) << 8) | ch(2);
}

// Car-local bounds (union over the car's body draws). The length axis is the longer horizontal extent (x or z), y is up.
struct Bounds { Vec3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f}; bool valid() const noexcept { return hi[0] > lo[0] && hi[1] > lo[1] && hi[2] > lo[2]; }
    void add(const Vec3& a, const Vec3& b) noexcept { for (unsigned i = 0; i < 3; ++i) { lo[i] = std::min(lo[i], a[i]); hi[i] = std::max(hi[i], b[i]); } } };
inline unsigned length_axis(const Bounds& b) noexcept { return (b.hi[0] - b.lo[0]) >= (b.hi[2] - b.lo[2]) ? 0u : 2u; }
// Local position -> atlas uv (side projection, tile = 1/3 of the car length) and -> ramp uv (normalised to the bounds).
inline Mat atlas_matrix(const Bounds& b, float tiles = 3.f) noexcept {
    // u = L + .7 W, v = -Y + .4 W: sides (W const) get the plain side view; the front/rear faces (L const) and the roof
    // (Y const) still get a non-degenerate 2D projection, so they show patches instead of stretched streaks.
    const unsigned a = length_axis(b), w = 2u - a; const float len = b.hi[a] - b.lo[a], s = len > 1e-4f ? tiles / len : 1.f;
    Mat m{}; m[a * 4 + 0] = s; m[w * 4 + 0] = .7f * s; m[1 * 4 + 1] = -s; m[w * 4 + 1] = .4f * s; m[15] = 1; return m;
}
// G2.1: atlas point for tyres: a texel whose coverage noise is mid-range (alpha ~ .25 of .5) and whose detail is neutral,
// so the whole tread gets one even layer whose density follows the car's lower-body level.
inline std::array<float, 2> uniform_atlas_uv(unsigned size = 256) noexcept {
    std::array<float, 2> best{.5f, .5f}; float best_d = 1e9f;
    for (unsigned y = 0; y < size; y += 2) for (unsigned x = 0; x < size; x += 2) {
        const uint32_t t = atlas_texel(x, y, size); const float a = float(t >> 24) / 255.f, g = float(t & 255) / 255.f;
        const float d = std::fabs(a - .25f) + .5f * std::fabs(g - .5f);
        if (d < best_d) { best_d = d; best = {(x + .5f) / size, (y + .5f) / size}; }
    }
    return best;
}
// G2.1: zone volume coordinate w across the car width (0 = -x side = left, 1 = +x = right in MR's left-handed car space).
inline Mat ramp_matrix3(const Bounds& b) noexcept {
    const unsigned a = length_axis(b), w = 2u - a; Mat m{};
    const float len = std::max(b.hi[a] - b.lo[a], 1e-4f), h = std::max(b.hi[1] - b.lo[1], 1e-4f), wid = std::max(b.hi[w] - b.lo[w], 1e-4f);
    m[a * 4 + 0] = 1.f / len; m[12] = -b.lo[a] / len; m[1 * 4 + 1] = -1.f / h; m[13] = b.hi[1] / h; m[w * 4 + 2] = 1.f / wid; m[14] = -b.lo[w] / wid; m[15] = 1; return m;
}
inline Mat ramp_matrix(const Bounds& b) noexcept {
    const unsigned a = length_axis(b); const float len = std::max(b.hi[a] - b.lo[a], 1e-4f), h = std::max(b.hi[1] - b.lo[1], 1e-4f);
    Mat m{}; m[a * 4 + 0] = 1.f / len; m[12] = -b.lo[a] / len; m[1 * 4 + 1] = -1.f / h; m[13] = b.hi[1] / h; m[15] = 1; return m;
}
inline Vec3 apply(const Mat& m, const Vec3& p) noexcept {
    return {p[0] * m[0] + p[1] * m[4] + p[2] * m[8] + m[12], p[0] * m[1] + p[1] * m[5] + p[2] * m[9] + m[13], p[0] * m[2] + p[1] * m[6] + p[2] * m[10] + m[14]};
}

// ---- Surface kinds (G1.1, owner review 2026-11-12) ------------------------------------------------------------------
// Body: opaque paint/panels/trim/underbody (Atmosphere body route). Wheel: rubber + rim, uniform weight, spins with the
// wheel. Glass / Lamp / Grille / Decal: blended or alpha-tested car draws; Grille and Decal follow the texture alpha
// (grille holes stay holes, a sticker gets exactly the dirt of the body under it).
enum Kind : unsigned { Body = 0, Wheel = 1, Glass = 2, Lamp = 3, Grille = 4, Decal = 5, Rim = 6 };
inline bool kind_wheel(unsigned k) noexcept { return k == Wheel || k == Rim; }
// Owner review 2 (2026-11-12): tyres and rims were one bright beige blob -> tyre .7, rim .4 (the rim stays readable), and
// wheels use a darker tone and larger blobs; grilles and lamps were too faint at .55.
inline float kind_level(unsigned k) noexcept { switch (k) { case Wheel: return .7f; case Rim: return .4f; case Glass: return .6f; case Lamp: return .7f; case Grille: return .8f; default: return 1.f; } }
inline float kind_tone(unsigned k) noexcept { return kind_wheel(k) ? .62f : 1.f; }       // tint multiplier
inline float kind_tiles(unsigned k) noexcept { return kind_wheel(k) ? .8f : 3.f; }       // atlas tiles across the bounds length
inline bool kind_masked(unsigned k) noexcept { return k == Grille || k == Decal; }
inline bool has_any(const std::string& s, std::initializer_list<const char*> parts) noexcept { for (auto* p : parts) if (s.find(p) != std::string::npos) return true; return false; }
// Crew and cabin interior never get grime (registry roles alone are not enough: whitesuit/head/mr-crew are "flat",
// seats are "paint").
inline bool crew_or_interior(const std::string& primary) noexcept {
    // Driver faces are named after the drivers (dcambell, drichard, dbruno, dnissan*), owner review 2.
    // Owner review 3: "head" also matched headlamp-tga / headlight textures (Impreza, Navara front lamps had no grime).
    if (has_any(primary, {"suit", "crew", "face", "helmet", "driver", "pilot", "glove", "gorrilla", "seat", "belt", "harness", "interior", "dash", "cockpit", "steer", "chair",
                          "dcambell", "drichard", "dbruno", "dnissan"})) return true;
    for (size_t at = primary.find("head"); at != std::string::npos; at = primary.find("head", at + 4))
        if (primary.compare(at, 5, "headl") != 0) return true;
    return false;
}
// G1.5: draws that mark the cabin (crew and seats; not underdash / interior, which span the whole car). Their car-local
// bounds define where the shell may cull (vehicle_grime_shell.hpp cabin_contains).
inline bool cabin_marker(const std::string& primary) noexcept {
    if (has_any(primary, {"suit", "crew", "face", "helmet", "driver", "pilot", "glove", "gorrilla", "seat", "chair", "dcambell", "drichard", "dbruno", "dnissan"})) return true;
    for (size_t at = primary.find("head"); at != std::string::npos; at = primary.find("head", at + 4)) if (primary.compare(at, 5, "headl") != 0) return true;
    return false;
}
// Kind of a blended / alpha-tested car draw from its texture names (canonical, lower case), or -1 to skip.
inline int blended_kind(const std::string& primary, const std::string& secondary) noexcept {
    if (crew_or_interior(primary)) return -1;
    if (has_any(primary, {"glow", "emissive", "blight", "flare", "shadow"})) return -1;
    if (has_any(primary, {"light", "lamp", "indicat", "lens", "spot"})) return Lamp;   // before glass: lamp lenses often use the glass env
    if (secondary == "glass-tga" || has_any(primary, {"glass", "window", "windscreen", "screen", "win"})) return Glass;
    if (has_any(primary, {"grill", "mesh", "net"})) return Grille;
    return Decal;
}
}
