// COURSE-RENDER-FIX1 contracts of the portable diagnostics core (renderer/ps2_diag.hpp): PNG/JSON writers, image statistics,
// draw ledger, capture-timing decision, per-race ledger, disable log and the capped stream.
#include "ps2_diag.hpp"
#include "render_queue_order.hpp"
#include "vehicle_grime.hpp"
#include "vehicle_grime_overlay.hpp"
#include "vehicle_grime_shell.hpp"
#include <map>
#include <algorithm>
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

// Engine draw queue (render_queue_order.hpp): the cars sort behind every other opaque record.
void render_queue_tests() {
    using namespace gfx2::ps2port;
    constexpr uint32_t queue = 0x20000, begin = 0x30000, kCar = 0xCA0000, kCourse = 0xC0000;
    std::map<uint32_t, uint32_t> memory;
    const auto read = [&](uintptr_t a, uint32_t& v) { auto i = memory.find(uint32_t(a)); if (i == memory.end()) return false; v = i->second; return true; };
    const auto write = [&](uintptr_t a, uint32_t v) { if (!memory.count(uint32_t(a))) return false; memory[uint32_t(a)] = v; return true; };
    const auto is_vehicle = [&](uint32_t owner) { return owner == kCar; };
    const auto record = [&](unsigned i, uint32_t owner, uint32_t sub, uint32_t material, uint32_t texture, uint32_t high) {
        const uint32_t at = begin + i * kQueueRecordSize;
        memory[at] = owner; memory[at + 4] = 0x70000 + i; memory[at + 8] = sub; memory[at + 0xc] = 0;
        memory[at + 0x10] = (sub << 29) | (material << 16) | texture; memory[at + 0x14] = high;
    };
    // Converted SpainS2 order: car materials have smaller pool ids than the terrain.
    record(0, kCar, 0, 20, 634, 0); record(1, kCourse, 0, 30, 1067, 0); record(2, kCar, 0, 25, 645, 0);
    record(3, kCourse, 0, 31, 1075, 0); record(4, kCourse, 0, 10, 626, 0);
    memory[queue + 0x24] = begin; memory[queue + 0x28] = begin + 5 * kQueueRecordSize;
    const auto sorted = [&]() {   // the engine's order: high word, then low word
        std::vector<std::pair<uint64_t, uint32_t>> order;
        for (unsigned i = 0; i < 5; ++i) order.push_back({(uint64_t(memory[begin + i * 24 + 0x14]) << 32) | memory[begin + i * 24 + 0x10], memory[begin + i * 24]});
        std::sort(order.begin(), order.end());
        return order;
    };
    CHECK(sorted()[0].second == kCourse && sorted()[1].second == kCar);          // the defect: a car record draws before the terrain
    RenderQueueStats stats; RenderQueueSnapshot snapshot;
    CHECK(prioritize_vehicle_records(queue, read, write, is_vehicle, stats, &snapshot, false) && stats.promoted == 0 && memory[begin + 0x14] == 0);   // observe only
    CHECK(snapshot.records == 5 && snapshot.vehicles == 2 && snapshot.owners.size() == 2 && snapshot.runs.size() == 5);
    CHECK(prioritize_vehicle_records(queue, read, write, is_vehicle, stats, nullptr, true));
    CHECK(stats.promoted == 2 && stats.last_promoted == 2 && std::string(stats.last_reason) == "vehicles_moved_last");
    const auto order = sorted();
    CHECK(order[0].second == kCourse && order[1].second == kCourse && order[2].second == kCourse && order[3].second == kCar && order[4].second == kCar);
    CHECK(order[0].first == ((10ull << 16) | 626) && order[1].first == ((30ull << 16) | 1067) && order[2].first == ((31ull << 16) | 1075));   // engine order inside the groups is kept
    CHECK(order[3].first == ((1ull << 32) | (20ull << 16) | 634) && order[4].first == ((1ull << 32) | (25ull << 16) | 645));
    CHECK(prioritize_vehicle_records(queue, read, write, is_vehicle, stats, nullptr, true) && stats.last_promoted == 0 &&
          std::string(stats.last_reason) == "vehicles_already_last");                  // idempotent
    // Alpha records (high word set by the depth key) are never touched.
    record(1, kCar, 0, 30, 1067, 0x3f000000);
    CHECK(prioritize_vehicle_records(queue, read, write, is_vehicle, stats, nullptr, true) && memory[begin + 24 + 0x14] == 0x3f000000);
    // A queue that is not in the expected shape is left alone.
    memory[queue + 0x28] = begin + 5 * kQueueRecordSize + 4;
    const uint32_t keep = memory[begin + 0x14];
    CHECK(!prioritize_vehicle_records(queue, read, write, is_vehicle, stats) && stats.rejected == 1 && memory[begin + 0x14] == keep);
    memory[queue + 0x28] = begin + 5000 * kQueueRecordSize; CHECK(!prioritize_vehicle_records(queue, read, write, is_vehicle, stats) && stats.rejected == 2);
    memory[queue + 0x24] = 0; memory[queue + 0x28] = 0; CHECK(prioritize_vehicle_records(queue, read, write, is_vehicle, stats) && std::string(stats.last_reason) == "empty");
    CHECK(!prioritize_vehicle_records(0x10, read, write, is_vehicle, stats) && !prioritize_vehicle_records(queue + 0x1000, read, write, is_vehicle, stats) && stats.unreadable == 2);
    memory[queue + 0x24] = begin; memory[queue + 0x28] = begin + 5 * kQueueRecordSize; memory.erase(begin + 3 * 24 + 0x10);
    CHECK(!prioritize_vehicle_records(queue, read, write, is_vehicle, stats) && std::string(stats.last_reason) == "record_unreadable");
    // Diagnostic record.
    const auto json = render_queue_json(snapshot, 42, 1, true);
    CHECK(valid_json(json) && json.find("\"ps2_render_queue\"") != std::string::npos && json.find("\"runs\":[[") != std::string::npos);
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
// R-SURFACE1 G0: vehicle grime core (renderer/vehicle_grime.hpp).
void grime_overlay_tests() {
    using namespace gfx2::grimeoverlay;
    // Threshold growth needs the coverage noise in [0,.5]; the detail stays around .5 for MODULATE2X.
    unsigned amax = 0, gmin = 255, gmax = 0;
    for (unsigned y = 0; y < 64; ++y) for (unsigned x = 0; x < 64; ++x) { const uint32_t t = atlas_texel(x * 4, y * 4, 256);
        amax = std::max(amax, t >> 24); gmin = std::min(gmin, t & 255); gmax = std::max(gmax, t & 255); }
    CHECK(amax <= 128 && amax > 90 && gmin >= 100 && gmax <= 160);
    CHECK(atlas_texel(0, 5, 256) == atlas_texel(0, 5, 256));                                       // deterministic
    CHECK(std::fabs(coverage_noise(0.f, .3f) - coverage_noise(1.f, .3f)) < 1e-4f);                 // tiles in u
    // Zone caps: roof <= .2, upper <= .35, lower <= .9 (ends +.08).
    CHECK(zone_weight(.5f, 0.f) <= .2f && zone_weight(.5f, .4f) <= .36f && zone_weight(.5f, 1.f) >= .8f && zone_weight(.02f, 1.f) <= .9f);
    Look l; l.level = .5f; l.mud = 0.f; CHECK((factor(l) >> 24) == 128u && ((factor(l) >> 16) & 255) == 173u);   // G1.4 dust .68 (owner review 4: too light)
    l.mud = 1.f; l.level = 1.f; CHECK(factor(l) == 0xff4d3d2bu);
    // Matrices: bounds corners map to the ramp's [0,1] and the length axis is the longer horizontal extent.
    Bounds b; b.add({-1.f, 0.f, -2.f}, {1.f, 1.5f, 2.f}); CHECK(b.valid() && length_axis(b) == 2u);
    const auto r = ramp_matrix(b); auto top_front = apply(r, {0.f, 1.5f, -2.f}), bottom_rear = apply(r, {0.f, 0.f, 2.f});
    CHECK(std::fabs(top_front[0]) < 1e-5f && std::fabs(top_front[1]) < 1e-5f && std::fabs(bottom_rear[0] - 1.f) < 1e-5f && std::fabs(bottom_rear[1] - 1.f) < 1e-5f);
    const auto a = atlas_matrix(b); CHECK(std::fabs(apply(a, {0.f, 0.f, 4.f / 3.f})[0] - 1.f) < 1e-5f);  // three tiles per car length
    // G1.1 kinds: crew/interior never; blended car draws by texture names.
    CHECK(crew_or_interior("whitesuit32-tga") && crew_or_interior("head-tga") && crew_or_interior("mr-crew-52d2c422abb3486ed834-tga") && crew_or_interior("seat02-tga") && !crew_or_interior("tatabon-tga"));
    CHECK(blended_kind("whitesuit-tga", "null") == -1 && blended_kind("brakeglow-tga", "null") == -1);
    CHECK(blended_kind("icewin-tga", "glass-tga") == Glass && blended_kind("windscreen32-tga", "null") == Glass && blended_kind("inlights-tga", "null") == Lamp);
    CHECK(blended_kind("tergrill64-tga", "null") == Grille && blended_kind("navaralogo-tga", "whitepaint-tga") == Decal);
    CHECK(kind_masked(Grille) && kind_masked(Decal) && !kind_masked(Glass) && kind_level(Glass) < 1.f && kind_level(Body) == 1.f);
    CHECK(crew_or_interior("dcambell-tga") && crew_or_interior("drichard-tga") && crew_or_interior("dnissanslave3-tga") && !crew_or_interior("sus32a-tga"));
    // G2: per-car zone texture and tint.
    {   std::array<float, 8> za{}; CHECK(zone_amount(.5f, .9f, za) == 0.f && ((car_ramp_texel(10, 30, 64, 32, za) >> 24) == 0u));
        za[5] = 1.f; CHECK(zone_amount(.02f, .95f, za) > .95f && zone_amount(.98f, .95f, za) < .05f);          // rear zone -> rear end only
        za = {}; za[2] = za[3] = 1.f; CHECK(zone_amount(.5f, .95f, za) > .95f && zone_amount(.5f, .05f, za) < .05f);   // sides low, roof clean
        za.fill(.4f); const uint32_t low = car_ramp_texel(32, 30, 64, 32, za) >> 24, top = car_ramp_texel(32, 1, 64, 32, za) >> 24; CHECK(low > 60u && top < 30u);   // light dirt: roof stays clean
        za.fill(1.f); CHECK((car_ramp_texel(32, 1, 64, 32, za) >> 24) > 250u);   // G3.2: fully dirty -> whole car
        Look lk; CarTone dry; dry.dust = .5f; const auto d = car_tint(lk, dry); CHECK(std::fabs(d[0] - lk.dust[0]) < 1e-5f);
        CarTone mud; mud.mud = .5f; const auto m = car_tint(lk, mud); CHECK(std::fabs(m[0] - lk.mud_tint[0]) < 1e-5f);
        CarTone old = mud; old.mud_age = 200.f; CHECK(car_tint(lk, old)[0] > m[0]);                       // dried mud is lighter
        CarTone wet = mud; wet.wet = 1.f; CHECK(car_tint(lk, wet)[0] < m[0]);                             // wet is darker
        CHECK(car_factor({1.f, 0.f, .5f}, .5f) == 0x80ff0080u);
        // G2.1: surface tone keeps the configured brightness, opacity, tyre point, volume matrix.
        { const Vec3 grey{.5f, .5f, .5f}, green{.2f, .6f, .2f}; const auto st = surface_tone(grey, green, 1.f);
          CHECK(std::fabs(luma(st) - luma(grey)) < .02f && st[1] > st[0] && surface_tone(grey, Vec3{}, 1.f) == grey && surface_tone(grey, green, 0.f) == grey); }
        { Look lo; CarTone pd; pd.dust = 1.f; CarTone pm; pm.mud = 1.f; CHECK(std::fabs(car_opacity(lo, pd) - .8f) < 1e-5f && std::fabs(car_opacity(lo, pm) - 1.f) < 1e-5f); }
        { const auto uv = uniform_atlas_uv(); const uint32_t tx = atlas_texel(unsigned(uv[0] * 256), unsigned(uv[1] * 256), 256); CHECK(std::fabs(float(tx >> 24) / 255.f - .25f) < .03f); }
        { Bounds bb; bb.add({-1, 0, -2}, {1, 1.5f, 2}); const auto m3 = ramp_matrix3(bb); const auto lft = apply(m3, {-1, .75f, 0}), rgt = apply(m3, {1, .75f, 2});
          CHECK(std::fabs(lft[2]) < 1e-5f && std::fabs(rgt[2] - 1.f) < 1e-5f && std::fabs(rgt[0] - 1.f) < 1e-5f && std::fabs(lft[1] - .5f) < 1e-5f); }
        // G3: wiper arcs, wiper frame, windscreen detection.
        { CHECK(wiper_clean(.28f, .8f) > .99f && wiper_clean(.72f, .7f) > .99f && wiper_clean(.02f, .05f) < .01f && wiper_clean(.98f, .05f) < .01f);
          CHECK((wiper_texel(1, 1, 64, 64, .5f) >> 24) > 120u && (wiper_texel(18, 55, 64, 64, .5f) >> 24) == 0u);
          const auto wm = wiper_matrix(-.8f, .8f, 1.f, 1.5f); const auto tl = apply(wm, {-.8f, 1.5f, 0}), br = apply(wm, {.8f, 1.f, 0});
          CHECK(std::fabs(tl[0]) < 1e-5f && std::fabs(tl[1]) < 1e-5f && std::fabs(br[0] - 1.f) < 1e-5f && std::fabs(br[1] - 1.f) < 1e-5f);
          std::array<float, 8> clean{}; CHECK(windscreen_level(clean) == 0.f); clean.fill(1.f); CHECK(windscreen_level(clean) > .99f);
          clean = {}; clean[0] = .8f; CHECK(windscreen_level(clean) > .4f && wiper_clean(kGlassFilmU, kGlassFilmV) < .01f); }
        { using gfx2::grimeshell::Tri; using gfx2::grimeshell::glass_frame; using gfx2::grimeshell::outward;
          auto oriented = [](Tri t, gfx2::grimeshell::Vec3 n) { if (gfx2::grimeshell::dot(outward(t), n) < 0) std::swap(t.b, t.c); return t; };
          // Raked windscreen facing +z and up; a side window facing +x.
          const std::vector<Tri> front{oriented({{-.8f, 1.f, 1.f}, {.8f, 1.f, 1.f}, {0, 1.5f, .5f}}, {0, .7f, .7f}), oriented({{-.8f, 1.5f, .5f}, {.8f, 1.5f, .5f}, {.8f, 1.f, 1.f}}, {0, .7f, .7f})};
          const std::vector<Tri> side{oriented({{.9f, 1.f, -.5f}, {.9f, 1.f, .5f}, {.9f, 1.4f, 0}}, {1, 0, 0})};
          const auto ff = glass_frame(front); CHECK(ff.windscreen && std::fabs(ff.x0 + .8f) < 1e-5f && std::fabs(ff.y1 - 1.5f) < 1e-5f);
          CHECK(!glass_frame(side).windscreen && !glass_frame({}).windscreen); }
        // G3.3: eased wetness and the sheen curve.
        { float w = 0; w = ease_wet(w, 1.f, .5); CHECK(w > .15f && w < .2f); for (int i = 0; i < 20; ++i) w = ease_wet(w, 1.f, .5); CHECK(w > .95f);
          const float dry = ease_wet(1.f, 0.f, .5); CHECK(dry > .85f && dry < .9f); CHECK(ease_wet(.3f, .7f, 0) == .7f);
          CHECK(sheen_curve(0.f) == 0.f && sheen_curve(1.f) == 1.f && sheen_curve(.2f) < .11f && std::fabs(sheen_curve(.5f) - .5f) < 1e-5f); }
        const auto g = grime::start_state(.5f); CHECK(std::fabs(g.dust[0] - .5f) < 1e-6f && g.dust[7] < .11f && g.mud[0] == 0.f && grime::start_state(0.f).clean()); }
    CHECK(kind_wheel(Wheel) && kind_wheel(Rim) && !kind_wheel(Body) && kind_level(Rim) < kind_level(Wheel) && kind_tone(Wheel) < 1.f && kind_tiles(Wheel) < kind_tiles(Body));
    // G1.3: "head" no longer swallows headlamps / headlights.
    CHECK(!crew_or_interior("headlamp-tga") && !crew_or_interior("headlight64-tga") && crew_or_interior("head-tga") && crew_or_interior("headlamp-head-tga"));
    CHECK(blended_kind("headlamp-tga", "glass-tga") == Lamp);
    // G1.3 shell: an open-top box (cabin) inside a larger closed box with one wall missing. Outer faces see the sky, the
    // inner box (crew) does not; the floor of the open side stays exterior.
    {   using namespace gfx2::grimeshell;
        std::vector<Tri> tris;
        // Quad a-b-c-d wound so that outward(cross(c-a, b-a)) points along n.
        auto quad = [&](Vec3 a, Vec3 b, Vec3 c, Vec3 d, Vec3 n) { Tri t{a, b, c}; if (dot(outward(t), n) < 0) std::swap(t.b, t.c); tris.push_back(t);
            Tri u{a, c, d}; if (dot(outward(u), n) < 0) std::swap(u.b, u.c); tris.push_back(u); };
        auto box = [&](Vec3 lo, Vec3 hi, float sign, bool skip_top) {
            const float x0 = lo[0], y0 = lo[1], z0 = lo[2], x1 = hi[0], y1 = hi[1], z1 = hi[2];
            quad({x0, y0, z0}, {x1, y0, z0}, {x1, y0, z1}, {x0, y0, z1}, {0, -sign, 0});
            if (!skip_top) quad({x0, y1, z0}, {x1, y1, z0}, {x1, y1, z1}, {x0, y1, z1}, {0, sign, 0});
            quad({x0, y0, z0}, {x0, y1, z0}, {x0, y1, z1}, {x0, y0, z1}, {-sign, 0, 0}); quad({x1, y0, z0}, {x1, y1, z0}, {x1, y1, z1}, {x1, y0, z1}, {sign, 0, 0});
            quad({x0, y0, z0}, {x1, y0, z0}, {x1, y1, z0}, {x0, y1, z0}, {0, 0, -sign}); quad({x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1}, {0, 0, sign}); };
        box({-1, 0, -2}, {1, 1.5f, 2}, 1, false);          // closed body, outward faces
        const size_t body = tris.size();
        box({-.3f, .3f, -.3f}, {.3f, .9f, .3f}, 1, false); // crew block inside
        const auto g = build(tris);
        CHECK(g.valid() && g.dims[2] > g.dims[0]);
        unsigned outer = 0, inner = 0; for (size_t i = 0; i < tris.size(); ++i) (i < body ? outer : inner) += exterior(g, tris[i]);
        CHECK(outer == body && inner == 0);
        CHECK(visibility(g, tris[0]) > .9f && visibility(g, tris[body]) < .01f);
        CHECK(exterior(Grid{}, tris[body]));                // no grid: never culled
        Tri flat{{0, 0, 0}, {0, 0, 0}, {1, 0, 0}}; CHECK(visibility(g, flat) == 1.f);   // degenerate
        Tri reversed = tris[0]; std::swap(reversed.b, reversed.c); CHECK(exterior(g, reversed));   // G1.4: reversed winding stays exterior
        { Tri back = tris[body]; std::swap(back.b, back.c); CHECK(!exterior(g, back)); }
        // G1.5: culling only inside the cabin box (crew/seat bounds; z +-0.9 m, from 0.5 m below, full width).
        Cabin cab; CHECK(!cabin_contains(cab, tris[body])); for (size_t i = body; i < tris.size(); ++i) cabin_add(cab, tris[i]);
        CHECK(cab.valid() && cabin_contains(cab, tris[body]));
        Tri tail{{-.5f, .5f, -1.9f}, {.5f, .5f, -1.9f}, {0, 1, -1.9f}}; Tri floor{{-.5f, -.4f, 0}, {.5f, -.4f, 0}, {0, -.4f, .5f}}; Tri side{{.95f, .5f, 0}, {.95f, 1, 0}, {.95f, .5f, .5f}};
        CHECK(!cabin_contains(cab, tail) && !cabin_contains(cab, floor) && cabin_contains(cab, side));
        CHECK(gfx2::grimeoverlay::cabin_marker("whitesuit32-tga") && gfx2::grimeoverlay::cabin_marker("chair2-tga") && !gfx2::grimeoverlay::cabin_marker("underdash-tga") && !gfx2::grimeoverlay::cabin_marker("headlamp-tga"));
    }
}
void grime_tests() {
    using namespace grime;
    // G2.1: side and direction of particles, deposit colour.
    {   CarTrack car; car.now.ok = true; car.now.position = {0, 0, 0}; car.heading = {0, 1};   // heading +z: right = +x
        add(car, Family::Dust, {2, -1, -1}, 1.f, {.8f, .6f, .4f}); add(car, Family::Dust, {2, -1, -1}, 1.f, {.8f, .6f, .4f});
        CHECK(car.window.right[0] == 2 && car.window.left[0] == 0 && car.window.rear[0] == 2 && car.window.front[0] == 0);
        const auto w = direction_weights(car.window); CHECK(w[3] > w[2] && w[5] > w[0] && w[7] == 1.f);
        CarGrime g; accumulate(g, car.window, 1.0, 1.0); CHECK(g.dust[3] > g.dust[2] && g.dust[5] > g.dust[0] && std::fabs(g.dust_rgb[0] - .8f) < 1e-4f && g.mud_rgb[0] == 0.f);
        CHECK(direction_weights(Exposure{})[0] == 1.f); }
    {   CarTrack car; car.now.ok = true; car.heading = {0, 1}; for (int i = 0; i < 50; ++i) add(car, Family::Grass, {0, -1, -1}, 1.f, {.5f, .4f, .3f});   // brown particles
        CarGrime g; accumulate(g, car.window, 1.0, 1.0); CHECK(g.mud[0] > 0.f && g.mud_rgb[1] > g.mud_rgb[0] && g.mud_rgb[1] > g.mud_rgb[2]); }   // G2.2: grass deposits green
    CHECK(identify("294d44ef9e880c274d37b2d55fb6d3fde2aca90846f6b8ee2dc3d2e65ff32c0f")->family == Family::Mud);
    CHECK(identify("de99dad6bc7df5371a004630c511741c7beffba3f8a18bb2243b6739df082ec4")->family == Family::Water);
    CHECK(identify("6915b27bbcdfea7f9d41944c79d317cbee7b39bd21de7bfd28d79a81bc742817")->family == Family::Dust);
    CHECK(identify("00") == nullptr);
    for (size_t i = 0; i < kTextures.size(); ++i) for (size_t j = i + 1; j < kTextures.size(); ++j) CHECK(std::string(kTextures[i].sha) != kTextures[j].sha);
    // Attribution and motion.
    std::array<CarTrack, 8> cars{};
    update_motion(cars[0], CarSample{true, {0, 0, 0}}, 1.0); update_motion(cars[0], CarSample{true, {0, 0, 10}}, 2.0);
    update_motion(cars[1], CarSample{true, {50, 0, 0}}, 2.0);
    CHECK(std::abs(cars[0].speed - 10) < 1e-3 && cars[0].heading[1] > .99f);
    { CarTrack c; update_motion(c, CarSample{true, {0, 0, 0}}, 1.0); update_motion(c, CarSample{true, {0, 0, 10}}, 2.0);
      update_motion(c, CarSample{true, {0, 0, 10}}, 2.01); CHECK(std::abs(c.speed - 10) < 1e-3);   // repeated physics sample is not new
      update_motion(c, CarSample{true, {0, 0, 20}}, 3.0); CHECK(std::abs(c.speed - 10) < 1e-3); }
    CHECK(attribute(cars, 8, {1, -.5f, 8}, 4) == 0 && attribute(cars, 8, {49, 0, 1}, 4) == 1 && attribute(cars, 8, {25, 0, 0}, 4) == -1);
    add(cars[0], Family::Mud, {0, -.5f, 8}, .5f); add(cars[0], Family::Mud, {0, .5f, 12}, .5f);
    const auto m = static_cast<size_t>(Family::Mud);
    CHECK(cars[0].window.triangles[m] == 2 && cars[0].window.rear[m] == 1 && cars[0].window.front[m] == 1 && cars[0].window.low[m] == 1 && cars[0].race.triangles[m] == 2);
    CHECK(valid_json(exposure_json(cars[0].window)) && valid_json(exposure_json(Exposure{})));
    // Accumulation: mud grows on the lower body first, water rinses and wets, drying decays wetness.
    CarGrime g; Exposure e; e.triangles[m] = 8000; e.low[m] = 6400;   // 200 triangles/frame over 40 frames
    for (int i = 0; i < 20; ++i) accumulate(g, e, .5, 40);
    CHECK(g.mud[0] < 1 && g.mud[0] > .5f && g.mud[0] > g.mud[7] && g.mud[0] > 0 && g.mud[0] <= 1);
    const float before = g.mud[0];
    Exposure w; w.triangles[static_cast<size_t>(Family::Water)] = 4000; for (int i = 0; i < 4; ++i) accumulate(g, w, .5, 40);
    CHECK(g.mud[0] < before && g.wet[0] > .5f);
    const float wet = g.wet[0]; accumulate(g, Exposure{}, 2, 80); for (int i = 0; i < 20; ++i) accumulate(g, Exposure{}, 2, 80); CHECK(g.wet[0] < wet * .5f);
    CHECK(valid_json(grime_json(g)));
    // Service Park wash entry point.
    CarGrime washed = g; washed.wash(1); CHECK(washed.mud[0] == 0 && washed.dust[0] == 0 && washed.wet[0] == 1);
    CarGrime half = g; half.wash(.5f); CHECK(std::abs(half.mud[0] - g.mud[0] * .5f) < 1e-6f);
    // Master Rallye mode campaign identity.
    MasterState s; s.ok = true; s.stage = 2; s.vehicle_class = 0; s.difficulty = 2; s.saved = true;
    for (int i = 0; i < 6; ++i) { s.cars[i].ok = true; s.cars[i].car_id = i; s.cars[i].driver_id = 30 + i; s.cars[i].player = i == 0; float tt = 100.f * (i + 1); std::memcpy(&s.cars[i].total_time_bits, &tt, 4); }
    CHECK(valid_json(s.json()) && !s.campaign().empty() && s.campaign() != s.checkpoint());
    MasterState next = s; next.stage = 3; float tt = 250.f; std::memcpy(&next.cars[0].total_time_bits, &tt, 4);
    CHECK(next.campaign() == s.campaign() && next.checkpoint() != s.checkpoint() && next != s);
    // Race field <-> campaign field (order may differ; attract/quick race fields do not match).
    std::array<RaceCar, 8> field{}; for (int i = 0; i < 6; ++i) field[size_t(i)] = RaceCar{true, 5 - i, 35 - i, i == 5};
    const auto mm = match_master(field, 6, s); CHECK(mm.ok && mm.master_of_race[0] == 5 && mm.master_of_race[5] == 0);
    CHECK(!match_master(field, 4, s).ok);                                   // no human car among the first four
    { auto four = field; four[0] = RaceCar{true, 0, 30, true}; four[4] = four[5] = RaceCar{}; CHECK(match_master(four, 6, s).ok); }   // 4-car field, unused slots
    { auto wrong = field; wrong[5].human = false; wrong[4].human = true; CHECK(!match_master(wrong, 6, s).ok); }                      // human mismatch
    field[2].driver_id = 77; CHECK(!match_master(field, 6, s).ok);
    // Persistence: finish stage 2 -> game saves stage 3 checkpoint -> quit -> reload stage 3 -> still dirty.
    Store store; CampaignTracker tracker;
    CHECK(tracker.start(s, store) == nullptr);
    Snapshot end; end.campaign = s.campaign(); end.checkpoint = s.checkpoint(); end.cars[0] = g; end.present[0] = true;
    tracker.race_finished(s, end);
    CHECK(tracker.observe(s, store).kind == nullptr && tracker.pending());       // menu, nothing saved yet
    CHECK(std::string(tracker.observe(next, store).kind) == "checkpoint_bound" && !tracker.pending());
    const auto* restored = tracker.start(next, store);
    CHECK(restored && restored->present[0] && std::abs(restored->cars[0].mud[0] - g.mud[0]) < 1e-6f);
    // Restart of stage 3 without a new save: same checkpoint, same stored grime; a different campaign starts clean.
    CampaignTracker reloaded; CHECK(reloaded.start(next, store) == restored);
    MasterState other = next; other.cars[1].driver_id = 99; CHECK(reloaded.start(other, store) == nullptr);
    // A quit without save never binds the pending state to the old checkpoint.
    CampaignTracker quit; quit.race_finished(next, end); CHECK(quit.observe(next, store).kind == nullptr && quit.pending());
    // Store text round trip; malformed lines are skipped, values clamped.
    const auto text = store.serialize();
    Store copy; CHECK(copy.parse(text) == 1 && copy.find(next.campaign(), next.checkpoint()) && copy.serialize() == text);
    Store bad; CHECK(bad.parse(std::string(Store::kHeader) + "\nx|y|0|1,2|3\nx|y|9|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0\n"
                                "a|b|1|9,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0\n") == 1);
    CHECK(bad.find("a", "b")->cars[1].dust[0] == 1.f);
    Store headerless; CHECK(headerless.parse("a|b|1|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0|0,0,0,0,0,0,0,0\n") == 0);
}
}

int main() {
    json_helper_tests(); render_queue_tests(); png_tests(); image_tests(); draw_ledger_tests(); timing_tests(); ledger_tests(); stream_tests(); grime_tests(); grime_overlay_tests();
    if (failures) std::cerr << failures << " failures\n";
    else std::cout << "ps2_diag contracts ok\n";
    return failures ? 1 : 0;
}
