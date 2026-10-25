#pragma once
// COURSE-RENDER-FIX1: the player's car must not appear in its own reflection.
//
// The late capture (end of the world pass) sees the finished frame, car included; the PS2 capture runs while the terrain is
// drawn and before the car. The car draws are the draws that sample the environment target (stage 1 texture coordinates
// are the camera space normal). Their local bounding boxes are projected with the transforms of the draw; the convex hull
// of all projected corners of a frame is the area that the capture refills with the static term instead of the frame term.
//
// Portable (no D3D types): matrices are 16 floats, row major, row vector convention (D3D).
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <vector>

namespace ps2diag {

struct Point2 { float x = 0, y = 0; };

struct Aabb {
    std::array<float, 3> lo{}, hi{};
    bool valid = false;
    float diagonal() const noexcept {
        float s = 0;
        for (int i = 0; i < 3; ++i) { const float d = hi[i] - lo[i]; s += d * d; }
        return std::sqrt(s);
    }
};

// Position is the first three floats of every XYZ vertex. Non-finite or out of range positions invalidate the box.
inline Aabb aabb_from_vertices(const uint8_t* bytes, size_t count, size_t stride) noexcept {
    Aabb box;
    if (!bytes || stride < 12 || !count) return box;
    for (int i = 0; i < 3; ++i) { box.lo[i] = 3.4e38f; box.hi[i] = -3.4e38f; }
    for (size_t v = 0; v < count; ++v) {
        float p[3];
        std::memcpy(p, bytes + v * stride, 12);
        for (int i = 0; i < 3; ++i) {
            if (!std::isfinite(p[i]) || std::fabs(p[i]) > 1.0e6f) return Aabb{};
            box.lo[i] = std::min(box.lo[i], p[i]);
            box.hi[i] = std::max(box.hi[i], p[i]);
        }
    }
    box.valid = true;
    return box;
}

// A car is a few metres; larger meshes that sample the environment (water, big props) are not part of the mask.
inline constexpr float kMaxCarBoxDiagonal = 9.0f;
inline constexpr size_t kMaxSilhouettePoints = 256;
inline constexpr float kMaxSilhouetteArea = 0.35f;   // fraction of the render target; larger hulls are a mismatch, not a car

struct ViewportRect { float x = 0, y = 0, width = 0, height = 0; };

inline void multiply(const float* a, const float* b, float* out) noexcept {
    float r[16];
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) {
            float s = 0;
            for (int k = 0; k < 4; ++k) s += a[i * 4 + k] * b[k * 4 + j];
            r[i * 4 + j] = s;
        }
    std::memcpy(out, r, sizeof(r));
}

// Eight projected corners in render target pixels. False when a corner is behind the near plane or not finite.
inline bool project_box(const Aabb& box, const float* world, const float* view, const float* projection, const ViewportRect& vp,
                        std::array<Point2, 8>& out) noexcept {
    if (!box.valid || vp.width <= 0 || vp.height <= 0) return false;
    float wv[16], wvp[16];
    multiply(world, view, wv);
    multiply(wv, projection, wvp);
    for (int c = 0; c < 8; ++c) {
        const float x = (c & 1) ? box.hi[0] : box.lo[0], y = (c & 2) ? box.hi[1] : box.lo[1], z = (c & 4) ? box.hi[2] : box.lo[2];
        const float cx = x * wvp[0] + y * wvp[4] + z * wvp[8] + wvp[12];
        const float cy = x * wvp[1] + y * wvp[5] + z * wvp[9] + wvp[13];
        const float cw = x * wvp[3] + y * wvp[7] + z * wvp[11] + wvp[15];
        if (!std::isfinite(cx) || !std::isfinite(cy) || !std::isfinite(cw) || cw <= 1.0e-4f) return false;
        out[c].x = vp.x + (cx / cw * 0.5f + 0.5f) * vp.width;
        out[c].y = vp.y + (0.5f - cy / cw * 0.5f) * vp.height;
    }
    return true;
}

inline float polygon_area(const std::vector<Point2>& p) noexcept {
    double a = 0;
    for (size_t i = 0; i < p.size(); ++i) {
        const auto& u = p[i]; const auto& v = p[(i + 1) % p.size()];
        a += double(u.x) * v.y - double(v.x) * u.y;
    }
    return static_cast<float>(std::fabs(a) * 0.5);
}

// Pixel points of the car draws of one frame.
class CarSilhouette {
    std::vector<Point2> points_;
    unsigned boxes_ = 0, rejected_ = 0;
public:
    void clear() noexcept { points_.clear(); boxes_ = rejected_ = 0; }
    bool add(const std::array<Point2, 8>& corners) noexcept {
        if (points_.size() + corners.size() > kMaxSilhouettePoints) { ++rejected_; return false; }
        try { points_.insert(points_.end(), corners.begin(), corners.end()); } catch (...) { ++rejected_; return false; }
        ++boxes_;
        return true;
    }
    unsigned boxes() const noexcept { return boxes_; }
    unsigned rejected() const noexcept { return rejected_; }
    bool empty() const noexcept { return points_.empty(); }
    // Convex hull (monotone chain), counter clockwise. False when fewer than three distinct points remain.
    bool hull(std::vector<Point2>& out) const {
        out.clear();
        std::vector<Point2> p = points_;
        if (p.size() < 3) return false;
        std::sort(p.begin(), p.end(), [](const Point2& a, const Point2& b) { return a.x < b.x || (a.x == b.x && a.y < b.y); });
        p.erase(std::unique(p.begin(), p.end(), [](const Point2& a, const Point2& b) { return a.x == b.x && a.y == b.y; }), p.end());
        if (p.size() < 3) return false;
        const auto cross = [](const Point2& o, const Point2& a, const Point2& b) { return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x); };
        std::vector<Point2> h(2 * p.size());
        size_t k = 0;
        for (size_t i = 0; i < p.size(); ++i) {
            while (k >= 2 && cross(h[k - 2], h[k - 1], p[i]) <= 0) --k;
            h[k++] = p[i];
        }
        for (size_t i = p.size() - 1, t = k + 1; i > 0; --i) {
            while (k >= t && cross(h[k - 2], h[k - 1], p[i - 1]) <= 0) --k;
            h[k++] = p[i - 1];
        }
        h.resize(k - 1);
        if (h.size() < 3) return false;
        out = std::move(h);
        return true;
    }
};

// Pixel hull of the render target -> points of the 64x64 environment target. The frame term is vertically flipped
// (row 0 of the target is the bottom of the frame), the static term is not; polygon uses target coordinates.
// False when the hull is larger than kMaxSilhouetteArea of the target.
inline bool hull_to_env(const std::vector<Point2>& hull, float width, float height, std::vector<Point2>& env) {
    env.clear();
    if (hull.size() < 3 || width <= 0 || height <= 0) return false;
    if (polygon_area(hull) > kMaxSilhouetteArea * width * height) return false;
    env.reserve(hull.size());
    for (const auto& q : hull) env.push_back({q.x / width * 64.f, (1.f - q.y / height) * 64.f});
    return true;
}

} // namespace ps2diag
