// COURSE-RENDER-FIX1 contracts of the portable diagnostics core (renderer/ps2_diag.hpp): PNG/JSON writers, image statistics,
// draw ledger, capture-timing decision, per-race ledger, disable log and the capped stream.
#include "ps2_diag.hpp"
#include "reflection_exclusion.hpp"
#include <cmath>
#include <cstring>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace ps2diag;
int failures = 0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)

namespace {
// Minimal strict JSON validator: every record written by the diagnostics must parse.
struct Json {
    const std::string& s; size_t i = 0;
    explicit Json(const std::string& text) : s(text) {}
    void ws() { while (i < s.size() && (s[i] == ' ' || s[i] == '\n' || s[i] == '\t' || s[i] == '\r')) ++i; }
    bool lit(const char* word) { const size_t n = std::strlen(word); if (s.compare(i, n, word) == 0) { i += n; return true; } return false; }
    bool str() {
        if (i >= s.size() || s[i] != '"') return false;
        ++i;
        while (i < s.size() && s[i] != '"') {
            if (static_cast<unsigned char>(s[i]) < 0x20) return false;
            if (s[i] == '\\') { ++i; if (i >= s.size()) return false; if (s[i] == 'u') { if (i + 4 >= s.size()) return false; i += 4; } }
            ++i;
        }
        if (i >= s.size()) return false;
        ++i; return true;
    }
    bool num() {
        const size_t start = i;
        if (i < s.size() && s[i] == '-') ++i;
        bool digits = false;
        while (i < s.size() && ((s[i] >= '0' && s[i] <= '9') || s[i] == '.' || s[i] == 'e' || s[i] == 'E' || s[i] == '+' || s[i] == '-')) { digits = true; ++i; }
        return digits && i > start;
    }
    bool value() {
        ws();
        if (i >= s.size()) return false;
        if (s[i] == '{') {
            ++i; ws();
            if (i < s.size() && s[i] == '}') { ++i; return true; }
            for (;;) {
                ws(); if (!str()) return false; ws();
                if (i >= s.size() || s[i] != ':') return false; ++i;
                if (!value()) return false; ws();
                if (i < s.size() && s[i] == ',') { ++i; continue; }
                if (i < s.size() && s[i] == '}') { ++i; return true; }
                return false;
            }
        }
        if (s[i] == '[') {
            ++i; ws();
            if (i < s.size() && s[i] == ']') { ++i; return true; }
            for (;;) {
                if (!value()) return false; ws();
                if (i < s.size() && s[i] == ',') { ++i; continue; }
                if (i < s.size() && s[i] == ']') { ++i; return true; }
                return false;
            }
        }
        if (s[i] == '"') return str();
        if (lit("true") || lit("false") || lit("null")) return true;
        return num();
    }
    bool valid() { const bool ok = value(); ws(); return ok && i == s.size(); }
};
bool valid_json(const std::string& text) { return Json(text).valid(); }

uint32_t be32(const std::vector<uint8_t>& v, size_t at) { return (uint32_t(v[at]) << 24) | (uint32_t(v[at + 1]) << 16) | (uint32_t(v[at + 2]) << 8) | v[at + 3]; }

// Decodes the PNG written by encode_png (stored deflate blocks only); false on any structural error.
bool decode_png(const std::vector<uint8_t>& png, uint32_t& w, uint32_t& h, std::vector<uint8_t>& rgb) {
    static const uint8_t sig[8] = {0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a};
    if (png.size() < 8 || std::memcmp(png.data(), sig, 8)) return false;
    size_t at = 8; std::vector<uint8_t> idat; bool seen_header = false, seen_end = false;
    while (at + 12 <= png.size()) {
        const uint32_t len = be32(png, at);
        if (at + 12 + len > png.size()) return false;
        const uint32_t crc = crc32_update(0, png.data() + at + 4, 4 + len);
        if (crc != be32(png, at + 8 + len)) return false;
        const std::string type(reinterpret_cast<const char*>(png.data() + at + 4), 4);
        if (type == "IHDR") { w = be32(png, at + 8); h = be32(png, at + 12); seen_header = png[at + 16] == 8 && png[at + 17] == 2; }
        else if (type == "IDAT") idat.insert(idat.end(), png.begin() + at + 8, png.begin() + at + 8 + len);
        else if (type == "IEND") seen_end = true;
        at += 12 + len;
    }
    if (!seen_header || !seen_end || idat.size() < 6 || idat[0] != 0x78) return false;
    std::vector<uint8_t> raw; size_t p = 2;
    for (;;) {
        if (p + 5 > idat.size()) return false;
        const bool last = idat[p] & 1; if ((idat[p] >> 1) & 3) return false;
        const uint32_t len = idat[p + 1] | (uint32_t(idat[p + 2]) << 8), nlen = idat[p + 3] | (uint32_t(idat[p + 4]) << 8);
        if ((len ^ 0xffffu) != nlen || p + 5 + len > idat.size()) return false;
        raw.insert(raw.end(), idat.begin() + p + 5, idat.begin() + p + 5 + len); p += 5 + len;
        if (last) break;
    }
    if (p + 4 != idat.size() || adler32(raw.data(), raw.size()) != be32(idat, p)) return false;
    if (raw.size() != size_t(h) * (size_t(w) * 3 + 1)) return false;
    rgb.clear();
    for (uint32_t y = 0; y < h; ++y) { if (raw[size_t(y) * (w * 3 + 1)]) return false; rgb.insert(rgb.end(), raw.begin() + size_t(y) * (w * 3 + 1) + 1, raw.begin() + size_t(y + 1) * (w * 3 + 1)); }
    return true;
}

void json_helper_tests() {
    CHECK(quote("a\"b\\c\n") == "\"a\\\"b\\\\c\\n\"");
    CHECK(valid_json(quote(std::string("ctl\x01tab\t"))));
    CHECK(number(1.5, 1) == "1.5" && number(std::nan("")) == "null");
    int64_t v = 0; std::string t;
    CHECK(extract_integer("{\"a\":1,\"request_generation\":-17,\"b\":2}", "request_generation", v) && v == -17);
    CHECK(!extract_integer("{\"a\":1}", "b", v) && !extract_integer("{\"a\":x}", "a", v));
    CHECK(extract_string("{\"state\":\"AWAITING_RACE_OWNER\"}", "state", t) && t == "AWAITING_RACE_OWNER");
    CHECK(valid_json("{\"a\":[1,2,{\"b\":null}],\"c\":\"x\"}") && !valid_json("{\"a\":}") && !valid_json("{\"a\":1,}"));
}

void png_tests() {
    // Standard check values.
    const uint8_t digits[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
    CHECK(crc32_update(0, digits, 9) == 0xCBF43926u);
    const uint8_t wiki[] = {'W', 'i', 'k', 'i', 'p', 'e', 'd', 'i', 'a'};
    CHECK(adler32(wiki, 9) == 0x11E60398u);
    // Round trip, including a block boundary (> 65535 raw bytes).
    for (const auto size : {std::pair<uint32_t, uint32_t>{1, 1}, {7, 5}, {64, 64}, {200, 120}}) {
        std::vector<uint8_t> rgb(size_t(size.first) * size.second * 3);
        for (size_t i = 0; i < rgb.size(); ++i) rgb[i] = uint8_t(i * 7 + i / 251);
        const auto png = encode_png(size.first, size.second, rgb);
        uint32_t w = 0, h = 0; std::vector<uint8_t> back;
        CHECK(!png.empty() && decode_png(png, w, h, back) && w == size.first && h == size.second && back == rgb);
    }
    CHECK(encode_png(0, 4, {}).empty() && encode_png(2, 2, std::vector<uint8_t>(5)).empty() && encode_png(20000, 1, {}).empty());
    const auto big = encode_png(256, 128, std::vector<uint8_t>(256 * 128 * 3, 9));
    uint32_t w = 0, h = 0; std::vector<uint8_t> back;
    CHECK(decode_png(big, w, h, back) && back.size() == 256 * 128 * 3);
    auto broken = big; broken[40] ^= 0xff;
    CHECK(!decode_png(broken, w, h, back));
}

void image_tests() {
    // Formats.
    const uint32_t px[2] = {0xff102030u, 0x00ffffffu};
    auto rgb = to_rgb(reinterpret_cast<const uint8_t*>(px), 8, 2, 1, PixelFormat::X8R8G8B8);
    CHECK(rgb.size() == 6 && rgb[0] == 0x10 && rgb[1] == 0x20 && rgb[2] == 0x30 && rgb[3] == 255);
    const uint16_t a1[2] = {uint16_t(0x8000 | (31 << 10)), uint16_t(31)};
    rgb = to_rgb(reinterpret_cast<const uint8_t*>(a1), 4, 2, 1, PixelFormat::A1R5G5B5);
    CHECK(rgb[0] == 255 && rgb[1] == 0 && rgb[2] == 0 && rgb[3] == 0 && rgb[5] == 255);
    const uint16_t r5[1] = {uint16_t(63 << 5)};
    rgb = to_rgb(reinterpret_cast<const uint8_t*>(r5), 2, 1, 1, PixelFormat::R5G6B5);
    CHECK(rgb[0] == 0 && rgb[1] == 255 && rgb[2] == 0);
    CHECK(to_rgb(nullptr, 8, 2, 1, PixelFormat::X8R8G8B8).empty() && to_rgb(reinterpret_cast<const uint8_t*>(px), 4, 2, 1, PixelFormat::X8R8G8B8).empty());

    // Statistics: top half sky grey, bottom half black.
    std::vector<uint8_t> frame(64 * 64 * 3, 0);
    for (size_t y = 0; y < 32; ++y) for (size_t x = 0; x < 64; ++x) for (int c = 0; c < 3; ++c) frame[(y * 64 + x) * 3 + c] = 200;
    const auto s = analyze(frame, 64, 64);
    CHECK(s.width == 64 && s.height == 64 && std::abs(s.black - .5f) < 1e-6f && std::abs(s.mean[0] - 100.f) < 1e-3f);
    CHECK(s.bands[0].black == 0.f && s.bands[kBands - 1].black == 1.f && std::abs(s.bands[0].r - 200.f) < 1e-3f);
    CHECK(s.hash == analyze(frame, 64, 64).hash && s.hash != analyze(std::vector<uint8_t>(64 * 64 * 3, 1), 64, 64).hash);
    CHECK(valid_json(stats_json(s)) && valid_json(stats_json(ImageStats{})));
    CHECK(analyze({}, 0, 0).width == 0 && analyze(frame, 65, 64).width == 0);

    // The probe: an empty ground (bottom third black) is incomplete, a lit one is not.
    std::vector<uint8_t> bottom(640 * 150 * 3, 0);
    CHECK(world_incomplete(analyze(bottom, 640, 150)));
    for (size_t i = 0; i < bottom.size(); ++i) bottom[i] = 60;
    CHECK(!world_incomplete(analyze(bottom, 640, 150)));
    for (size_t y = 0; y < 150; ++y) for (size_t x = 0; x < 640; ++x) bottom[(y * 640 + x) * 3] = (y < 18 ? 60 : 0), bottom[(y * 640 + x) * 3 + 1] = bottom[(y * 640 + x) * 3 + 2] = (y < 18 ? 60 : 0);
    CHECK(world_incomplete(analyze(bottom, 640, 150)));  // 88% black
    CHECK(!world_incomplete(ImageStats{}));

    // Scaling.
    std::vector<uint8_t> four(4 * 4 * 3, 100);
    CHECK(box_downsample(four, 4, 4, 2, 2) == std::vector<uint8_t>(12, 100) && box_downsample(four, 4, 4, 8, 8).empty());
    const auto up = scale_nearest(std::vector<uint8_t>{10, 20, 30}, 1, 1, 3, 2.f);
    CHECK(up.size() == 27 && up[0] == 20 && up[1] == 40 && up[2] == 60 && scale_nearest(std::vector<uint8_t>{200, 0, 0}, 1, 1, 1, 2.f)[0] == 255);
    std::vector<uint8_t> a(2 * 2 * 3, 1), b(3 * 1 * 3, 2);
    const auto m = make_montage({a, b}, {{2, 2}, {3, 1}});
    CHECK(m.width == 5 && m.height == 2 && m.rgb.size() == 30 && m.rgb[0] == 1 && m.rgb[2 * 3] == 2 && m.rgb[(1 * 5 + 2) * 3] == 24);
}

void draw_ledger_tests() {
    DrawLedger ledger; DrawLedger::Report r;
    ledger.note(10, 0x142, 5); ledger.note(10, 0x242, 7);
    ledger.mark_capture(10, false);
    ledger.note(10, 0x152, 100); ledger.note(10, 0x242, 9);
    CHECK(!ledger.take(r));
    ledger.note(11, 0x142, 1);   // frame rollover finishes frame 10
    CHECK(ledger.take(r) && r.frame == 10 && !r.late);
    CHECK(r.before.draws == 2 && r.before.triangles == 12 && r.total.draws == 4 && r.total.triangles == 121);
    CHECK(r.total.by_fvf[0].fvf == 0x142 && r.total.by_fvf[1].fvf == 0x242 && r.total.by_fvf[1].draws == 2 && r.total.by_fvf[1].triangles == 16);
    CHECK(!ledger.take(r));
    CHECK(valid_json(order_json(r)));
    // No mark: nothing is reported. A mark for another frame is ignored.
    ledger.note(12, 1, 1); ledger.mark_capture(99, true); ledger.note(13, 1, 1);
    CHECK(!ledger.take(r));
    // Late capture reports the whole frame.
    ledger.mark_capture(13, true); ledger.note(14, 1, 1);
    CHECK(ledger.take(r) && r.late && r.before.draws == 1);
    // More than eight formats are counted, not lost.
    FrameDraws f; for (uint32_t i = 0; i < 12; ++i) f.add(1000 + i, 1);
    CHECK(f.draws == 12 && f.other_fvf_draws == 4 && valid_json(frame_draws_json(f)));
}

void timing_tests() {
    CHECK(parse_timing(L"0") == CaptureTiming::InFrame && parse_timing(L"inframe") == CaptureTiming::InFrame &&
          parse_timing(L"2") == CaptureTiming::Late && parse_timing(L"late") == CaptureTiming::Late &&
          parse_timing(L"1") == CaptureTiming::Auto && parse_timing(L"") == CaptureTiming::Auto && parse_timing(L"junk") == CaptureTiming::Auto);
    {   // InFrame never probes, never switches.
        TimingDecision d(CaptureTiming::InFrame); d.on_race(5);
        for (int i = 0; i < 400; ++i) { d.note_capture(); CHECK(!d.probe_due()); }
        CHECK(!d.late() && !d.late_wanted());
    }
    {   // Late: always late inside a race, never outside.
        TimingDecision d(CaptureTiming::Late);
        CHECK(d.late() && !d.late_wanted()); d.on_race(3); CHECK(d.late_wanted()); d.on_race(0); CHECK(!d.late_wanted());
    }
    {   // Auto: probe at ordinals 1,16,48,120,300; three incomplete samples latch the race to the end-of-world capture.
        TimingDecision d(CaptureTiming::Auto); d.on_race(7);
        CHECK(!d.probe_due());
        std::vector<unsigned> probed;
        for (unsigned i = 1; i <= 300; ++i) { d.note_capture(); if (d.probe_due()) { probed.push_back(i); d.record_probe(true); } }
        CHECK((probed == std::vector<unsigned>{1, 16, 48}));
        CHECK(d.late() && d.late_wanted() && d.decided() && d.incomplete() == 3);
        d.on_race(8);                                   // the next race starts clean
        CHECK(!d.late() && !d.decided() && d.captures() == 0 && d.sampled() == 0);
        d.on_race(8); d.note_capture(); CHECK(d.captures() == 1);   // same race keeps its counters
    }
    {   // Auto, stock behaviour: three complete samples settle the race for in-frame capture.
        TimingDecision d(CaptureTiming::Auto); d.on_race(9);
        for (unsigned i = 1; i <= 300; ++i) { d.note_capture(); if (d.probe_due()) d.record_probe(false); }
        CHECK(d.decided() && !d.late() && d.sampled() == 3);
    }
    {   // Mixed samples: two incomplete, three complete -> in-frame (below the need of three).
        TimingDecision d(CaptureTiming::Auto); d.on_race(10);
        const bool pattern[5] = {true, false, true, false, false};
        unsigned k = 0;
        for (unsigned i = 1; i <= 300; ++i) { d.note_capture(); if (d.probe_due()) d.record_probe(pattern[k++]); }
        CHECK(k == 5 || d.decided());
        CHECK(!d.late());
    }
    {   // Outside a race (generation 0) nothing is probed or staged.
        TimingDecision d(CaptureTiming::Auto); d.configure(CaptureTiming::Auto, true);
        d.note_capture(); CHECK(!d.probe_due() && !d.stage_due());
    }
    {   // Stage reports: the fixed ordinals, at most seven per race and 64 per session.
        TimingDecision d(CaptureTiming::InFrame); d.configure(CaptureTiming::InFrame, true);
        unsigned total = 0;
        for (uint64_t race = 1; race <= 20; ++race) {
            d.on_race(race); unsigned in_race = 0;
            for (unsigned i = 1; i <= 2000; ++i) { d.note_capture(); if (d.stage_due()) ++in_race; }
            CHECK(in_race <= TimingDecision::kStageAt.size());
            total += in_race;
        }
        CHECK(total == TimingDecision::kSessionStageCap);
        TimingDecision off(CaptureTiming::InFrame); off.on_race(1); off.note_capture(); CHECK(!off.stage_due());
    }
}

void ledger_tests() {
    OutcomeSet set;
    set.add("a"); set.add("a", 2); set.add("b");
    CHECK(set.count("a") == 3 && set.count("b") == 1 && set.count("c") == 0 && set.total() == 4);
    for (int i = 0; i < 40; ++i) { static const char* names[] = {"k0","k1","k2","k3","k4","k5","k6","k7","k8","k9","k10","k11","k12","k13","k14","k15"}; set.add(names[i % 16]); }
    CHECK(set.other() > 0 && set.total() == 44 && valid_json(set.json()));

    RaceLedger ledger;
    ledger.note(Effect::Grass, "drawn");                   // outside a race: dropped
    CHECK(ledger.needs_new_race(1, 1) && !ledger.open());
    ledger.begin(6, 1, "RaceTest/SpainS2", 100);
    CHECK(ledger.open() && !ledger.needs_new_race(6, 1) && ledger.needs_new_race(6, 2) && ledger.needs_new_race(7, 1));
    ledger.note(Effect::Grass, "drawn", 5); ledger.note(Effect::Water, "replaced"); ledger.note(Effect::Hud, "not \"quoted\"");
    ledger.frame(100); ledger.frame(101); ledger.frame(102);
    CHECK(ledger.race().frames == 2 && ledger.outcomes(Effect::Grass).count("drawn") == 5);
    // The race is left: four presents without a certified HUD.
    CHECK(!ledger.note_present(true));
    for (unsigned i = 1; i < RaceLedger::kAbsentPresents; ++i) CHECK(!ledger.note_present(false));
    CHECK(ledger.note_present(false));
    {   // a certified present in between restarts the count (a transition frame is not the end of the race)
        RaceLedger other; other.begin(1, 1, "x", 1);
        for (unsigned i = 1; i < RaceLedger::kAbsentPresents; ++i) CHECK(!other.note_present(false));
        CHECK(!other.note_present(true));
        for (unsigned i = 1; i < RaceLedger::kAbsentPresents; ++i) CHECK(!other.note_present(false));
        CHECK(other.open());
    }
    CHECK(std::string(fleet_gate_name(3)) == "fleet_gate_3" && std::string(fleet_gate_name(99)) == "fleet_gate_other" &&
          std::string(model_gate_name(12)) == "model_gate_12" && fleet_gate_name(3) == fleet_gate_name(3));
    const auto line = ledger.finish("race_left", "{\"request_generation\":7}", "{\"reflection\":{\"active\":true}}");
    CHECK(valid_json(line) && line.find("\"course\":\"RaceTest/SpainS2\"") != std::string::npos && line.find("\"grass\":{\"drawn\":5}") != std::string::npos &&
          line.find("\"end_reason\":\"race_left\"") != std::string::npos && line.find("\"water\"") != std::string::npos);
    CHECK(!ledger.open() && ledger.finish("again", "", "").empty());
    // Counters of one race do not leak into the next one.
    ledger.begin(13, 2, "RaceTest/ItalyM1", 500);
    CHECK(ledger.outcomes(Effect::Grass).total() == 0 && ledger.race().frames == 0);
    ledger.note(Effect::Grass, "gate");
    const auto second = ledger.finish("new_race", "", "");
    CHECK(valid_json(second) && second.find("\"drawn\"") == std::string::npos && second.find("\"gate\":1") != std::string::npos);

    // 200 simulated races: constant size per record, sequence numbers consecutive, no growth.
    size_t largest = 0;
    for (uint64_t race = 1; race <= 200; ++race) {
        ledger.begin(race * 7, race, "RaceTest/Turkey3", race * 1000);
        for (int e = 0; e < int(Effect::Count); ++e) for (int k = 0; k < 20; ++k) ledger.note(static_cast<Effect>(e), k % 2 ? "drawn" : "skipped");
        const auto out = ledger.finish("new_race", "{}", "{}");
        CHECK(valid_json(out)); largest = std::max(largest, out.size());
    }
    CHECK(largest < 2500 && ledger.summaries() == 202);

    DisableLog log; DisableLog::Entry e;
    CHECK(!log.take(e) && log.recent_json() == "[]");
    log.note("grass", "native_grass_preview_draw_failed"); log.note("water", "water_draw_failed");
    CHECK(log.total() == 2 && log.take(e) && std::string(e.effect) == "grass" && log.take(e) && std::string(e.reason) == "water_draw_failed" && !log.take(e));
    for (int i = 0; i < 40; ++i) log.note("x", "r");
    CHECK(log.take(e) && e.sequence == 27 && valid_json(log.recent_json()));   // the ring keeps the last 16 (sequence 27..42)
}

void stream_tests() {
    const auto dir = std::filesystem::temp_directory_path() / "ps2diag-test";
    std::error_code error; std::filesystem::remove_all(dir, error);
    Stream stream; stream.configure(dir / "a" / "log.jsonl", 100);
    CHECK(stream.write("{\"a\":1}") && stream.write("{\"a\":2}"));
    CHECK(!stream.write(std::string(200, 'x')) && stream.dropped() == 1);
    std::ifstream in(dir / "a" / "log.jsonl"); std::string l1, l2;
    std::getline(in, l1); std::getline(in, l2);
    CHECK(l1 == "{\"a\":1}" && l2 == "{\"a\":2}" && stream.bytes() == 16);
    for (int i = 0; i < 40; ++i) stream.write("{\"i\":" + std::to_string(i) + "}");
    CHECK(stream.bytes() <= 100);
    Stream unset; CHECK(!unset.write("{}"));
    CHECK(write_file(dir / "b" / "x.bin", std::vector<uint8_t>{1, 2, 3}) && std::filesystem::file_size(dir / "b" / "x.bin") == 3);
    std::filesystem::remove_all(dir, error);
}
void exclusion_tests() {
    // AABB of a vertex stream (stride 36, position first); non-finite positions invalidate.
    std::vector<uint8_t> bytes(3 * 36, 0);
    const float pts[3][3] = {{-1, 0, -2}, {1, 1.5f, 2}, {0, 0.5f, 0}};
    for (int i = 0; i < 3; ++i) std::memcpy(bytes.data() + i * 36, pts[i], 12);
    const Aabb box = aabb_from_vertices(bytes.data(), 3, 36);
    CHECK(box.valid && box.lo[0] == -1 && box.hi[0] == 1 && box.lo[2] == -2 && box.hi[2] == 2 && box.hi[1] == 1.5f);
    CHECK(std::fabs(box.diagonal() - std::sqrt(4.f + 2.25f + 16.f)) < 1e-4f);
    const float nan = std::nanf(""); std::memcpy(bytes.data() + 36, &nan, 4);
    CHECK(!aabb_from_vertices(bytes.data(), 3, 36).valid && !aabb_from_vertices(nullptr, 3, 36).valid && !aabb_from_vertices(bytes.data(), 0, 36).valid &&
          !aabb_from_vertices(bytes.data(), 3, 8).valid);
    // Projection: identity world/view, perspective looking down +Z, car box 4 m ahead.
    const float identity[16] = {1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};
    float world[16]; std::memcpy(world, identity, sizeof(world)); world[14] = 10.f;   // 10 m in front
    float projection[16] = {1,0,0,0, 0,1,0,0, 0,0,1,1, 0,0,0,0};                      // x/z, y/z (w = z)
    Aabb car; car.valid = true; car.lo = {-1, -1, -2}; car.hi = {1, 1, 2};
    std::array<Point2, 8> corners{};
    CHECK(project_box(car, world, identity, projection, {0, 0, 640, 480}, corners));
    // near face z = 8: x in [-1/8, 1/8]; far face z = 12: x in [-1/12, 1/12]; screen x = (x*0.5+0.5)*640
    float minx = 1e9f, maxx = -1e9f, miny = 1e9f, maxy = -1e9f;
    for (const auto& p : corners) { minx = std::min(minx, p.x); maxx = std::max(maxx, p.x); miny = std::min(miny, p.y); maxy = std::max(maxy, p.y); }
    CHECK(std::fabs(minx - (0.5f - 0.0625f) * 640.f) < 0.01f && std::fabs(maxx - (0.5f + 0.0625f) * 640.f) < 0.01f);
    CHECK(std::fabs(miny - (0.5f - 0.0625f) * 480.f) < 0.01f && std::fabs(maxy - (0.5f + 0.0625f) * 480.f) < 0.01f);
    world[14] = 1.f;                                                                    // a corner behind the near plane
    CHECK(!project_box(car, world, identity, projection, {0, 0, 640, 480}, corners));
    CHECK(!project_box(Aabb{}, world, identity, projection, {0, 0, 640, 480}, corners));
    // Convex hull of two boxes plus interior points.
    CarSilhouette s; CHECK(s.empty());
    std::array<Point2, 8> a{}, b{};
    for (int i = 0; i < 8; ++i) { a[i] = {float(i & 1) * 10 + 100, float((i >> 1) & 1) * 10 + 100}; b[i] = {float(i & 1) * 10 + 105, float((i >> 1) & 1) * 10 + 105}; }
    CHECK(s.add(a) && s.add(b) && s.boxes() == 2);
    std::vector<Point2> hull; CHECK(s.hull(hull));
    CHECK(hull.size() == 6 && std::fabs(polygon_area(hull) - 200.f) < 0.01f);       // 15x15 minus the two corner triangles of 12.5
    CarSilhouette line; std::array<Point2, 8> c{}; for (int i = 0; i < 8; ++i) c[i] = {float(i), float(i)};
    CHECK(line.add(c) && !line.hull(hull));                                            // collinear
    CarSilhouette full; unsigned added = 0; while (full.add(a)) ++added;
    CHECK(added == kMaxSilhouettePoints / 8 && full.rejected() == 1);
    full.clear(); CHECK(full.empty() && full.boxes() == 0);
    // Pixel hull -> 64x64 target: x scaled, y flipped; a hull of more than a third of the target is no car.
    std::vector<Point2> px = {{320, 240}, {384, 240}, {384, 336}, {320, 336}}, env;
    CHECK(hull_to_env(px, 640, 480, env) && env.size() == 4 && std::fabs(env[0].x - 32.f) < 1e-4f && std::fabs(env[0].y - 32.f) < 1e-4f &&
          std::fabs(env[2].x - 38.4f) < 1e-3f && std::fabs(env[2].y - 19.2f) < 1e-3f);
    std::vector<Point2> huge = {{0, 0}, {640, 0}, {640, 400}, {0, 400}};
    CHECK(!hull_to_env(huge, 640, 480, env) && env.empty() && !hull_to_env(px, 0, 480, env));
    // Stage logging: only the capture that will be reported.
    TimingDecision d(CaptureTiming::Auto); d.configure(CaptureTiming::Auto, true); d.on_race(1);
    CHECK(d.stage_next());                                  // capture 1
    d.note_capture(); CHECK(d.stage_due() && d.stage_next());   // capture 2
    d.note_capture(); CHECK(d.stage_due() && d.stage_next());   // capture 3
    d.note_capture(); CHECK(d.stage_due() && !d.stage_next());  // capture 4 is not in the schedule
    TimingDecision off(CaptureTiming::Auto); off.on_race(1); CHECK(!off.stage_next());
}
}

int main() {
    exclusion_tests(); json_helper_tests(); png_tests(); image_tests(); draw_ledger_tests(); timing_tests(); ledger_tests(); stream_tests();
    if (failures) std::cerr << failures << " failures\n";
    else std::cout << "ps2_diag contracts ok\n";
    return failures ? 1 : 0;
}
