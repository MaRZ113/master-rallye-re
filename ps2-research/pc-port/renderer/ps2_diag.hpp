#pragma once
// COURSE-RENDER-FIX1 portable diagnostics core (no D3D, Windows or proxy types): PNG/JSON helpers, image statistics, the
// per-frame draw ledger, the capture-timing decision, the per-race effect ledger and a size-capped JSONL stream. Used by
// reflection_capture.cpp, reflection_native_integration.hpp and ps2_port_extension.cpp; tests/ps2_diag_tests.cpp covers it.
//
// Why this exists (docs/course-render-fix1/README.md):
//  * The baseline session log is capped at 16 MiB and 29% of it is race_epoch_snapshot records, so a long session of
//    race -> menu -> race cycles is cut off after about seven races. The PS2 diagnostics therefore write their own small
//    stream (ps2diag-*.jsonl, 4 MiB cap) that records one summary per race.
//  * The reflection records of the baseline log are claimed once per vehicle per session, so they cannot show a failure in
//    a later race. The stage report below can be repeated in every race.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace ps2diag {

// ---- JSON -------------------------------------------------------------------------------------------------------------

inline std::string quote(std::string_view text) {
    std::string out = "\"";
    for (const unsigned char c : text) {
        switch (c) {
        case '"': out += "\\\""; break;
        case '\\': out += "\\\\"; break;
        case '\n': out += "\\n"; break;
        case '\r': out += "\\r"; break;
        case '\t': out += "\\t"; break;
        default:
            if (c < 0x20) { char tmp[8]; std::snprintf(tmp, sizeof(tmp), "\\u%04x", c); out += tmp; }
            else out += static_cast<char>(c);
        }
    }
    return out + "\"";
}
inline std::string number(double value, int digits = 2) {
    if (!std::isfinite(value)) return "null";
    char tmp[48]; std::snprintf(tmp, sizeof(tmp), "%.*f", digits, value);
    return tmp;
}
// Integer value of "key":N (the first occurrence) in a flat JSON text; false when absent.
inline bool extract_integer(std::string_view json, std::string_view key, int64_t& out) {
    std::string pattern = "\"" + std::string(key) + "\":";
    const auto at = json.find(pattern);
    if (at == std::string_view::npos) return false;
    size_t i = at + pattern.size();
    bool negative = false;
    if (i < json.size() && json[i] == '-') { negative = true; ++i; }
    if (i >= json.size() || json[i] < '0' || json[i] > '9') return false;
    int64_t value = 0;
    while (i < json.size() && json[i] >= '0' && json[i] <= '9') { value = value * 10 + (json[i] - '0'); ++i; }
    out = negative ? -value : value;
    return true;
}
inline bool extract_string(std::string_view json, std::string_view key, std::string& out) {
    std::string pattern = "\"" + std::string(key) + "\":\"";
    const auto at = json.find(pattern);
    if (at == std::string_view::npos) return false;
    const size_t begin = at + pattern.size();
    const auto end = json.find('"', begin);
    if (end == std::string_view::npos) return false;
    out.assign(json.substr(begin, end - begin));
    return true;
}

// ---- PNG (stored deflate blocks: no zlib dependency) -------------------------------------------------------------------

inline uint32_t crc32_update(uint32_t crc, const uint8_t* data, size_t size) {
    static const auto table = [] {
        std::array<uint32_t, 256> t{};
        for (uint32_t n = 0; n < 256; ++n) { uint32_t c = n; for (int k = 0; k < 8; ++k) c = (c & 1) ? 0xedb88320u ^ (c >> 1) : c >> 1; t[n] = c; }
        return t;
    }();
    crc = ~crc;
    for (size_t i = 0; i < size; ++i) crc = table[(crc ^ data[i]) & 0xff] ^ (crc >> 8);
    return ~crc;
}
inline uint32_t adler32(const uint8_t* data, size_t size) {
    uint32_t a = 1, b = 0;
    for (size_t i = 0; i < size; ++i) { a = (a + data[i]) % 65521u; b = (b + a) % 65521u; }
    return (b << 16) | a;
}
inline void put_be32(std::vector<uint8_t>& out, uint32_t v) { for (int s = 24; s >= 0; s -= 8) out.push_back(static_cast<uint8_t>(v >> s)); }
inline void png_chunk(std::vector<uint8_t>& out, const char (&type)[5], const std::vector<uint8_t>& body) {
    put_be32(out, static_cast<uint32_t>(body.size()));
    const size_t start = out.size();
    out.insert(out.end(), type, type + 4);
    out.insert(out.end(), body.begin(), body.end());
    put_be32(out, crc32_update(0, out.data() + start, out.size() - start));
}
// 8-bit RGB, no filtering, zlib stored blocks. Empty result for an invalid size.
inline std::vector<uint8_t> encode_png(uint32_t width, uint32_t height, const std::vector<uint8_t>& rgb) {
    if (!width || !height || width > 16384 || height > 16384 || rgb.size() != size_t(width) * height * 3u) return {};
    std::vector<uint8_t> raw;
    raw.reserve(size_t(width) * height * 3u + height);
    for (uint32_t y = 0; y < height; ++y) {
        raw.push_back(0);
        raw.insert(raw.end(), rgb.begin() + size_t(y) * width * 3u, rgb.begin() + size_t(y + 1) * width * 3u);
    }
    std::vector<uint8_t> z{0x78, 0x01};
    size_t at = 0;
    do {
        const size_t block = std::min<size_t>(65535, raw.size() - at);
        const bool last = at + block >= raw.size();
        z.push_back(last ? 1 : 0);
        z.push_back(static_cast<uint8_t>(block)); z.push_back(static_cast<uint8_t>(block >> 8));
        z.push_back(static_cast<uint8_t>(~block)); z.push_back(static_cast<uint8_t>((~block) >> 8));
        z.insert(z.end(), raw.begin() + at, raw.begin() + at + block);
        at += block;
    } while (at < raw.size());
    put_be32(z, adler32(raw.data(), raw.size()));
    std::vector<uint8_t> out{0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a};
    std::vector<uint8_t> header;
    put_be32(header, width); put_be32(header, height);
    header.insert(header.end(), {8, 2, 0, 0, 0});
    png_chunk(out, "IHDR", header);
    png_chunk(out, "IDAT", z);
    png_chunk(out, "IEND", {});
    return out;
}
inline bool write_file(const std::filesystem::path& path, const std::vector<uint8_t>& bytes) noexcept {
    try {
        std::error_code error;
        std::filesystem::create_directories(path.parent_path(), error);
        std::ofstream file(path, std::ios::binary | std::ios::trunc);
        if (!file) return false;
        file.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
        return static_cast<bool>(file);
    } catch (...) { return false; }
}

// ---- image statistics --------------------------------------------------------------------------------------------------

enum class PixelFormat : uint8_t { X8R8G8B8, A8R8G8B8, A1R5G5B5, R5G6B5 };

// Tightly packed RGB bytes from a locked surface; empty for a bad request.
inline std::vector<uint8_t> to_rgb(const uint8_t* bits, uint32_t pitch, uint32_t width, uint32_t height, PixelFormat format) {
    const uint32_t bytes = (format == PixelFormat::A1R5G5B5 || format == PixelFormat::R5G6B5) ? 2u : 4u;
    if (!bits || !width || !height || pitch < width * bytes) return {};
    std::vector<uint8_t> out(size_t(width) * height * 3u);
    for (uint32_t y = 0; y < height; ++y) {
        const uint8_t* row = bits + size_t(y) * pitch;
        uint8_t* dst = out.data() + size_t(y) * width * 3u;
        for (uint32_t x = 0; x < width; ++x) {
            uint8_t r, g, b;
            if (bytes == 4) { uint32_t v; std::memcpy(&v, row + size_t(x) * 4, 4); r = uint8_t(v >> 16); g = uint8_t(v >> 8); b = uint8_t(v); }
            else {
                uint16_t v; std::memcpy(&v, row + size_t(x) * 2, 2);
                if (format == PixelFormat::A1R5G5B5) { r = uint8_t(((v >> 10) & 31) * 255 / 31); g = uint8_t(((v >> 5) & 31) * 255 / 31); b = uint8_t((v & 31) * 255 / 31); }
                else { r = uint8_t(((v >> 11) & 31) * 255 / 31); g = uint8_t(((v >> 5) & 63) * 255 / 63); b = uint8_t((v & 31) * 255 / 31); }
            }
            dst[0] = r; dst[1] = g; dst[2] = b; dst += 3;
        }
    }
    return out;
}

// Box filter to (tw, th); the target must not be larger than the source.
inline std::vector<uint8_t> box_downsample(const std::vector<uint8_t>& rgb, uint32_t w, uint32_t h, uint32_t tw, uint32_t th) {
    if (!w || !h || !tw || !th || tw > w || th > h || rgb.size() != size_t(w) * h * 3u) return {};
    std::vector<uint8_t> out(size_t(tw) * th * 3u);
    for (uint32_t ty = 0; ty < th; ++ty) {
        const uint32_t y0 = uint64_t(ty) * h / th, y1 = std::max(y0 + 1, uint32_t(uint64_t(ty + 1) * h / th));
        for (uint32_t tx = 0; tx < tw; ++tx) {
            const uint32_t x0 = uint64_t(tx) * w / tw, x1 = std::max(x0 + 1, uint32_t(uint64_t(tx + 1) * w / tw));
            uint64_t sum[3] = {0, 0, 0}; uint32_t n = 0;
            for (uint32_t y = y0; y < y1; ++y) for (uint32_t x = x0; x < x1; ++x) {
                const uint8_t* p = rgb.data() + (size_t(y) * w + x) * 3u;
                sum[0] += p[0]; sum[1] += p[1]; sum[2] += p[2]; ++n;
            }
            uint8_t* d = out.data() + (size_t(ty) * tw + tx) * 3u;
            for (int c = 0; c < 3; ++c) d[c] = uint8_t((sum[c] + n / 2) / n);
        }
    }
    return out;
}
inline std::vector<uint8_t> scale_nearest(const std::vector<uint8_t>& rgb, uint32_t w, uint32_t h, uint32_t factor, float gain = 1.f) {
    if (!w || !h || !factor || rgb.size() != size_t(w) * h * 3u) return {};
    std::vector<uint8_t> out(size_t(w) * factor * h * factor * 3u);
    for (uint32_t y = 0; y < h * factor; ++y) for (uint32_t x = 0; x < w * factor; ++x) {
        const uint8_t* s = rgb.data() + (size_t(y / factor) * w + x / factor) * 3u;
        uint8_t* d = out.data() + (size_t(y) * w * factor + x) * 3u;
        for (int c = 0; c < 3; ++c) d[c] = uint8_t(std::min(255.f, s[c] * gain + .5f));
    }
    return out;
}

inline constexpr size_t kBands = 8;
struct Band { float r = 0, g = 0, b = 0, black = 0; };
struct ImageStats {
    uint32_t width = 0, height = 0, hash = 0;
    float mean[3]{}, black = 0;          // black = fraction of pixels with r+g+b <= threshold
    std::array<Band, kBands> bands{};    // horizontal bands, top to bottom
};
inline ImageStats analyze(const std::vector<uint8_t>& rgb, uint32_t w, uint32_t h, int black_threshold = 12) {
    ImageStats s;
    if (!w || !h || rgb.size() != size_t(w) * h * 3u) return s;
    s.width = w; s.height = h;
    uint32_t hash = 2166136261u;
    for (const uint8_t byte : rgb) { hash ^= byte; hash *= 16777619u; }
    s.hash = hash;
    double total[3] = {0, 0, 0}; uint64_t black = 0;
    const uint32_t bands = static_cast<uint32_t>(std::min<size_t>(kBands, h));
    std::array<std::array<double, 4>, kBands> band{};
    std::array<uint64_t, kBands> counts{};
    for (uint32_t y = 0; y < h; ++y) {
        const uint32_t b = std::min(bands - 1, uint32_t(uint64_t(y) * bands / h));
        for (uint32_t x = 0; x < w; ++x) {
            const uint8_t* p = rgb.data() + (size_t(y) * w + x) * 3u;
            const bool dark = int(p[0]) + p[1] + p[2] <= black_threshold;
            for (int c = 0; c < 3; ++c) { total[c] += p[c]; band[b][c] += p[c]; }
            if (dark) { ++black; band[b][3] += 1; }
            ++counts[b];
        }
    }
    const double n = double(w) * h;
    for (int c = 0; c < 3; ++c) s.mean[c] = float(total[c] / n);
    s.black = float(black / n);
    for (uint32_t b = 0; b < bands; ++b) if (counts[b]) {
        s.bands[b] = {float(band[b][0] / counts[b]), float(band[b][1] / counts[b]), float(band[b][2] / counts[b]), float(band[b][3] / counts[b])};
    }
    return s;
}
inline std::string stats_json(const ImageStats& s) {
    std::string out = "{\"w\":" + std::to_string(s.width) + ",\"h\":" + std::to_string(s.height) + ",\"mean\":[" + number(s.mean[0], 1) + "," +
        number(s.mean[1], 1) + "," + number(s.mean[2], 1) + "],\"black\":" + number(s.black, 3) + ",\"hash\":\"" ;
    char tmp[16]; std::snprintf(tmp, sizeof(tmp), "%08x", s.hash);
    out += tmp; out += "\",\"bands\":[";
    for (size_t i = 0; i < kBands; ++i) {
        if (i) out += ",";
        out += "[" + number(s.bands[i].r, 1) + "," + number(s.bands[i].g, 1) + "," + number(s.bands[i].b, 1) + "," + number(s.bands[i].black, 2) + "]";
    }
    return out + "]}";
}

// The frame bottom (the ground) is empty when the capture ran before the terrain was drawn: the bottom third of the
// 640x448 PS2 frame is (almost) pure black.
inline constexpr float kIncompleteBlackFraction = 0.85f;
inline bool world_incomplete(const ImageStats& bottom) noexcept { return bottom.width && bottom.black >= kIncompleteBlackFraction; }

// Side by side [source | PS2 frame | env | env - static x gain], every tile 128 pixels high. Returns the montage size.
struct Montage { uint32_t width = 0, height = 0; std::vector<uint8_t> rgb; };
inline Montage make_montage(const std::vector<std::vector<uint8_t>>& tiles, const std::vector<std::pair<uint32_t, uint32_t>>& sizes) {
    Montage m;
    if (tiles.size() != sizes.size() || tiles.empty()) return m;
    uint32_t width = 0, height = 0;
    for (const auto& s : sizes) { width += s.first; height = std::max(height, s.second); }
    m.width = width; m.height = height; m.rgb.assign(size_t(width) * height * 3u, 24);
    uint32_t x0 = 0;
    for (size_t t = 0; t < tiles.size(); ++t) {
        const auto [w, h] = sizes[t];
        if (tiles[t].size() == size_t(w) * h * 3u)
            for (uint32_t y = 0; y < h; ++y) std::memcpy(m.rgb.data() + (size_t(y) * width + x0) * 3u, tiles[t].data() + size_t(y) * w * 3u, size_t(w) * 3u);
        x0 += w;
    }
    return m;
}

// ---- draw ledger -------------------------------------------------------------------------------------------------------

struct FvfCount { uint32_t fvf = 0, draws = 0, triangles = 0; };
struct FrameDraws {
    uint64_t frame = 0; uint32_t draws = 0, triangles = 0, other_fvf_draws = 0;
    std::array<FvfCount, 8> by_fvf{};
    void add(uint32_t fvf, uint32_t tris) noexcept {
        ++draws; triangles += tris;
        for (auto& e : by_fvf) {
            if (e.draws && e.fvf == fvf) { ++e.draws; e.triangles += tris; return; }
            if (!e.draws) { e = {fvf, 1, tris}; return; }
        }
        ++other_fvf_draws;
    }
};
inline std::string frame_draws_json(const FrameDraws& f) {
    std::string out = "{\"draws\":" + std::to_string(f.draws) + ",\"triangles\":" + std::to_string(f.triangles) + ",\"fvf\":{";
    bool first = true;
    for (const auto& e : f.by_fvf) {
        if (!e.draws) break;
        if (!first) out += ",";
        first = false;
        out += "\"" + std::to_string(e.fvf) + "\":[" + std::to_string(e.draws) + "," + std::to_string(e.triangles) + "]";
    }
    return out + "},\"other_fvf_draws\":" + std::to_string(f.other_fvf_draws) + "}";
}
// Indexed draws of the current frame by vertex format, the counters at the environment capture and the totals of the same
// frame (reported when the next frame starts). This is what shows whether the terrain was drawn before the car.
class DrawLedger {
    FrameDraws cur_{}, marked_{}, previous_{};
    bool has_mark_ = false, late_ = false, has_report_ = false;
    uint64_t mark_frame_ = 0;
public:
    struct Report { uint64_t frame = 0; bool late = false; FrameDraws before, total, previous; };
    // Counts one indexed draw. When the frame changes after a capture mark, the finished frame becomes a report.
    void note(uint64_t frame, uint32_t fvf, uint32_t triangles) noexcept {
        if (cur_.frame != frame) {
            if (has_mark_ && mark_frame_ == cur_.frame) {
                report_.frame = mark_frame_; report_.late = late_; report_.before = marked_; report_.total = cur_; report_.previous = previous_;
                has_report_ = true; has_mark_ = false;
            }
            previous_ = cur_;
            cur_ = {}; cur_.frame = frame;
        }
        cur_.add(fvf, triangles);
    }
    // late = the capture serves the next frame (end of world pass): its "before" is the whole frame so far.
    void mark_capture(uint64_t frame, bool late) noexcept {
        if (cur_.frame != frame) return;
        marked_ = cur_; mark_frame_ = frame; has_mark_ = true; late_ = late;
    }
    bool take(Report& out) noexcept { if (!has_report_) return false; out = report_; has_report_ = false; return true; }
    const FrameDraws& current() const noexcept { return cur_; }
    const FrameDraws& previous() const noexcept { return previous_; }
private:
    Report report_{};
};
inline std::string order_json(const DrawLedger::Report& r) {
    return "{\"type\":\"ps2_reflection_order\",\"frame\":" + std::to_string(r.frame) + ",\"late\":" + (r.late ? "true" : "false") +
        ",\"before_capture\":" + frame_draws_json(r.before) + ",\"frame_total\":" + frame_draws_json(r.total) +
        ",\"previous_frame\":" + frame_draws_json(r.previous) + "}";
}

// ---- capture timing ----------------------------------------------------------------------------------------------------

// ReflectionCaptureTiming: the environment target samples the frame buffer. The PS2 takes it after the course and before
// the car. In converted course DX files the terrain is drawn after the car, so an in-frame capture sees only the sky.
//   InFrame (0): at the first car draw of the frame (the original behaviour of every earlier build)
//   Auto    (1): in-frame, but a short per-race probe of the captured frame; when its bottom third is empty the race
//                switches to EndOfWorld (default)
//   Late    (2): end of the world pass (the first UI draw) of the previous frame, always
enum class CaptureTiming : uint8_t { InFrame = 0, Auto = 1, Late = 2 };
inline CaptureTiming parse_timing(std::wstring_view text) noexcept {
    if (text == L"0" || text == L"InFrame" || text == L"inframe") return CaptureTiming::InFrame;
    if (text == L"2" || text == L"Late" || text == L"late") return CaptureTiming::Late;
    return CaptureTiming::Auto;
}
inline const char* timing_name(CaptureTiming t) noexcept { return t == CaptureTiming::InFrame ? "inframe" : t == CaptureTiming::Late ? "late" : "auto"; }

class TimingDecision {
public:
    static constexpr unsigned kSamples = 5, kNeed = 3;
    static constexpr std::array<unsigned, kSamples> kSampleAt = {1, 16, 48, 120, 300};   // in-frame capture ordinals per race
    static constexpr std::array<unsigned, 7> kStageAt = {1, 2, 3, 30, 120, 480, 1200};
    static constexpr unsigned kSessionStageCap = 64;
    explicit TimingDecision(CaptureTiming t = CaptureTiming::InFrame) noexcept : timing_(t) {}
    void configure(CaptureTiming t, bool stage_diag) noexcept { timing_ = t; stage_diag_ = stage_diag; }
    CaptureTiming timing() const noexcept { return timing_; }
    bool stage_diag() const noexcept { return stage_diag_; }
    // A new race (race generation) restarts the per-race probe; 0 = outside a race.
    void on_race(uint64_t generation) noexcept {
        if (generation == race_) return;
        race_ = generation; captures_ = sampled_ = incomplete_ = complete_ = stages_ = 0; late_latched_ = false; decided_ = false;
        ++races_seen_;
    }
    uint64_t race() const noexcept { return race_; }
    uint64_t races_seen() const noexcept { return races_seen_; }
    // Capture ordinal bookkeeping: call once per finished in-frame capture, before probe_due()/stage_due().
    unsigned note_capture() noexcept { return ++captures_; }
    unsigned captures() const noexcept { return captures_; }
    bool probe_due() const noexcept {
        if (timing_ != CaptureTiming::Auto || decided_ || !race_) return false;
        for (unsigned at : kSampleAt) if (captures_ == at) return true;
        return false;
    }
    void record_probe(bool incomplete) noexcept {
        ++sampled_; (incomplete ? incomplete_ : complete_) += 1;
        if (incomplete_ >= kNeed) { decided_ = true; late_latched_ = true; }
        else if (complete_ >= kNeed || sampled_ >= kSamples) decided_ = true;
    }
    // The capture about to run is a stage report capture (the draw order is logged only for those frames).
    bool stage_next() const noexcept {
        if (!stage_diag_ || !race_ || stages_ >= kStageAt.size() || session_stages_ >= kSessionStageCap) return false;
        for (unsigned at : kStageAt) if (captures_ + 1 == at) return true;
        return false;
    }
    bool stage_due() noexcept {
        if (!stage_diag_ || !race_ || stages_ >= kStageAt.size() || session_stages_ >= kSessionStageCap) return false;
        for (unsigned at : kStageAt) if (captures_ == at) { ++stages_; ++session_stages_; return true; }
        return false;
    }
    bool decided() const noexcept { return decided_; }
    bool late() const noexcept { return timing_ == CaptureTiming::Late || (timing_ == CaptureTiming::Auto && late_latched_); }
    // The late capture runs only inside a race.
    bool late_wanted() const noexcept { return race_ && late(); }
    unsigned sampled() const noexcept { return sampled_; }
    unsigned incomplete() const noexcept { return incomplete_; }
    const char* mode_now() const noexcept { return late() ? "late" : "inframe"; }
private:
    CaptureTiming timing_;
    bool stage_diag_ = false, late_latched_ = false, decided_ = false;
    uint64_t race_ = 0, races_seen_ = 0;
    unsigned captures_ = 0, sampled_ = 0, incomplete_ = 0, complete_ = 0, stages_ = 0, session_stages_ = 0;
};

// Gate numbers of the PS2 car draw paths as literal outcome keys (OutcomeSet keeps the pointers).
inline constexpr const char* fleet_gate_name(unsigned gate) noexcept {
    constexpr const char* names[] = {"fleet_gate_0", "fleet_gate_1", "fleet_gate_2", "fleet_gate_3", "fleet_gate_4", "fleet_gate_5", "fleet_gate_6",
                                     "fleet_gate_7", "fleet_gate_8", "fleet_gate_9", "fleet_gate_10", "fleet_gate_11", "fleet_gate_12"};
    return gate < std::size(names) ? names[gate] : "fleet_gate_other";
}
inline constexpr const char* model_gate_name(unsigned gate) noexcept {
    constexpr const char* names[] = {"model_gate_0", "model_gate_1", "model_gate_2", "model_gate_3", "model_gate_4", "model_gate_5", "model_gate_6",
                                     "model_gate_7", "model_gate_8", "model_gate_9", "model_gate_10", "model_gate_11", "model_gate_12"};
    return gate < std::size(names) ? names[gate] : "model_gate_other";
}

// ---- per-race effect ledger --------------------------------------------------------------------------------------------

enum class Effect : uint8_t {
    ReflectionCapture, ReflectionBody, Fleet, FleetWheels, Grass, Shrubs, GroundDetail, Water, Spline, Hud, PostFx, Models, Count
};
inline constexpr const char* effect_name(Effect e) noexcept {
    constexpr const char* names[] = {"reflection_capture", "reflection_body", "fleet", "fleet_wheels", "grass", "shrubs",
                                     "ground_detail", "water", "spline", "hud", "postfx", "models"};
    return static_cast<size_t>(e) < std::size(names) ? names[static_cast<size_t>(e)] : "unknown";
}
// Outcome counters keyed by string literal; the number of distinct outcomes per effect is bounded.
class OutcomeSet {
public:
    static constexpr size_t kSlots = 12;
    void add(const char* key, uint32_t n = 1) noexcept {
        if (!key) key = "unnamed";
        for (auto& s : slots_) {
            if (!s.key) { s.key = key; s.count = n; return; }
            if (s.key == key || !std::strcmp(s.key, key)) { s.count += n; return; }
        }
        other_ += n;
    }
    uint64_t total() const noexcept { uint64_t t = other_; for (const auto& s : slots_) t += s.count; return t; }
    uint32_t count(const char* key) const noexcept { for (const auto& s : slots_) if (s.key && !std::strcmp(s.key, key)) return s.count; return 0; }
    uint32_t other() const noexcept { return other_; }
    std::string json() const {
        std::string out = "{"; bool first = true;
        for (const auto& s : slots_) { if (!s.key) break; if (!first) out += ","; first = false; out += quote(s.key) + ":" + std::to_string(s.count); }
        if (other_) { if (!first) out += ","; out += "\"_other\":" + std::to_string(other_); }
        return out + "}";
    }
private:
    struct Slot { const char* key = nullptr; uint32_t count = 0; };
    std::array<Slot, kSlots> slots_{};
    uint32_t other_ = 0;
};

class RaceLedger {
public:
    struct Open { bool open = false; uint64_t generation = 0, owner = 0, first_frame = 0, last_frame = 0, frames = 0; std::string course; };
    void note(Effect e, const char* outcome, uint32_t n = 1) noexcept {
        if (!race_.open) { ++outside_notes_; return; }
        effects_[static_cast<size_t>(e)].add(outcome, n);
    }
    // Called once per rendered race frame; true when a new race started (the previous one, if still open, must be finished
    // by the caller with finish("new_race") BEFORE begin()).
    bool needs_new_race(uint64_t generation, uint64_t owner) const noexcept { return !race_.open || race_.generation != generation || race_.owner != owner; }
    void begin(uint64_t generation, uint64_t owner, std::string_view course, uint64_t frame) {
        race_ = {}; race_.open = true; race_.generation = generation; race_.owner = owner; race_.first_frame = race_.last_frame = frame; race_.course.assign(course);
        for (auto& e : effects_) e = {};
        ++races_;
    }
    void frame(uint64_t frame) noexcept { if (race_.open && frame != race_.last_frame) { race_.last_frame = frame; ++race_.frames; } }
    bool open() const noexcept { return race_.open; }
    const Open& race() const noexcept { return race_; }
    uint32_t races() const noexcept { return races_; }
    uint32_t summaries() const noexcept { return summaries_; }
    const OutcomeSet& outcomes(Effect e) const noexcept { return effects_[static_cast<size_t>(e)]; }
    // Race left: HUD context invalid for several consecutive presents.
    bool note_present(bool race_hud_valid) noexcept {
        if (!race_.open) { absent_ = 0; return false; }
        if (race_hud_valid) { absent_ = 0; return false; }
        return ++absent_ >= kAbsentPresents;
    }
    std::string finish(const char* reason, std::string_view epoch_json, std::string_view state_json) {
        if (!race_.open) return {};
        std::string out = "{\"type\":\"ps2_race_summary\",\"seq\":" + std::to_string(++summaries_) + ",\"course\":" + quote(race_.course) +
            ",\"race_generation\":" + std::to_string(race_.generation) + ",\"owner_lifetime\":" + std::to_string(race_.owner) +
            ",\"first_frame\":" + std::to_string(race_.first_frame) + ",\"last_frame\":" + std::to_string(race_.last_frame) +
            ",\"frames\":" + std::to_string(race_.frames) + ",\"end_reason\":" + quote(reason ? reason : "unknown") +
            ",\"races_seen\":" + std::to_string(races_) + ",\"epoch\":" + std::string(epoch_json.empty() ? "{}" : epoch_json) + ",\"effects\":{";
        bool first = true;
        for (size_t i = 0; i < effects_.size(); ++i) {
            if (!effects_[i].total()) continue;
            if (!first) out += ",";
            first = false;
            out += quote(effect_name(static_cast<Effect>(i))) + ":" + effects_[i].json();
        }
        out += "},\"state\":" + std::string(state_json.empty() ? "{}" : state_json) + "}";
        race_ = {}; absent_ = 0;
        return out;
    }
    // About half a second at 60 fps without a certified race HUD: the race has been left (a transition frame is not).
    static constexpr unsigned kAbsentPresents = 30;
private:
    Open race_{};
    std::array<OutcomeSet, static_cast<size_t>(Effect::Count)> effects_{};
    uint32_t races_ = 0, summaries_ = 0, outside_notes_ = 0, absent_ = 0;
};

// ---- disable log -------------------------------------------------------------------------------------------------------

// Every session-wide switch-off of an effect (pilot disable(), model disable()) is recorded with its reason, so that a
// permanent failure can be told from an intentional "not on this course" gate. Render thread only.
class DisableLog {
public:
    struct Entry { const char* effect = ""; const char* reason = ""; uint64_t sequence = 0; };
    void note(const char* effect, const char* reason) noexcept {
        ring_[total_ % ring_.size()] = {effect ? effect : "", reason ? reason : "", total_ + 1};
        ++total_;
    }
    uint64_t total() const noexcept { return total_; }
    bool take(Entry& out) noexcept {
        if (reported_ >= total_) return false;
        if (total_ - reported_ > ring_.size()) reported_ = total_ - ring_.size();
        out = ring_[reported_ % ring_.size()]; ++reported_;
        return true;
    }
    std::string recent_json() const {
        std::string out = "[";
        const uint64_t first = total_ > ring_.size() ? total_ - ring_.size() : 0;
        for (uint64_t i = first; i < total_; ++i) {
            if (i != first) out += ",";
            const auto& e = ring_[i % ring_.size()];
            out += "{\"effect\":" + quote(e.effect) + ",\"reason\":" + quote(e.reason) + "}";
        }
        return out + "]";
    }
private:
    std::array<Entry, 16> ring_{};
    uint64_t total_ = 0, reported_ = 0;
};
inline DisableLog& disable_log() noexcept { static DisableLog log; return log; }

// ---- stream ------------------------------------------------------------------------------------------------------------

// Append-only JSONL with its own byte cap; never throws.
class Stream {
public:
    void configure(std::filesystem::path path, uint64_t cap) { path_ = std::move(path); cap_ = cap; bytes_ = 0; failed_ = false; opened_ = false; }
    bool write(const std::string& line) noexcept {
        try {
            if (path_.empty() || failed_ || bytes_ + line.size() + 1 > cap_) { ++dropped_; return false; }
            if (!opened_) {
                std::error_code error;
                std::filesystem::create_directories(path_.parent_path(), error);
                std::ofstream create(path_, std::ios::binary | std::ios::trunc);
                if (!create) { failed_ = true; return false; }
                opened_ = true;
            }
            std::ofstream file(path_, std::ios::binary | std::ios::app);
            if (!file) { failed_ = true; return false; }
            file << line << '\n';
            bytes_ += line.size() + 1;
            return static_cast<bool>(file);
        } catch (...) { failed_ = true; return false; }
    }
    uint64_t bytes() const noexcept { return bytes_; }
    uint64_t dropped() const noexcept { return dropped_; }
    const std::filesystem::path& path() const noexcept { return path_; }
private:
    std::filesystem::path path_;
    uint64_t cap_ = 0, bytes_ = 0, dropped_ = 0;
    bool failed_ = false, opened_ = false;
};

} // namespace ps2diag
