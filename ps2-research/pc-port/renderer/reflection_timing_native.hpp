#pragma once
// COURSE-RENDER-FIX1 native side (docs/course-render-fix1): the per-frame hooks of the reflection capture timing, the stage
// report writer and the per-race ledger. Compiled only into the staged baseline; included after reflection_native_integration.hpp.
//  * note_draw      first line of draw_indexed_at: draw ledger (draw order of the frame), per-frame race bookkeeping
//  * before_ui      typed pre-UI boundary: end-of-world reflection capture for the next frame, stage report output
//  * note / note_result  outcome counters of the per-race ledger (ps2diag::Effect)
#include "reflection_native_integration.hpp"
#include "reflection_inspect.hpp"
#include "course_objects_native_integration.hpp"
#include "ps2_diag.hpp"
#include "reflection_exclusion.hpp"
#include <array>
#include <cstdio>
#include <cstring>
#include <string>

namespace gfx2::reflectionintegration {

inline void note(Device8& d, ps2diag::Effect effect, const char* outcome, uint32_t n = 1) noexcept {
    if (auto* x = d.ps2_port()) x->note(effect, outcome, n);
}
inline void note_result(Device8& d, ps2diag::Effect effect, const char* ok, const char* failed, HRESULT hr) noexcept {
    note(d, effect, SUCCEEDED(hr) ? ok : failed);
}

// Capture observer (set once per frame, see frame_begin): marks the draw ledger where a capture starts and counts outcomes.
inline void capture_event(void* context, const ps2port::ReflectionCaptureEvent& e) noexcept {
    auto& d = *static_cast<Device8*>(context);
    auto* x = d.ps2_port();
    if (!x || !x->ledger_enabled()) return;
    if (e.begin) {
        auto* p = x->reflection();
        if (p && p->mixed_capture().decision().stage_next()) x->draw_ledger().mark_capture(d.trace.frame_number(), e.late);
        return;
    }
    x->note(ps2diag::Effect::ReflectionCapture, SUCCEEDED(e.hr) ? (e.late ? "late_ready" : "inframe_ready") : (e.reason ? e.reason : "failed"));
}

// The diagnostics readbacks live outside the capture (reflection_inspect.hpp). One instance for the process, never destroyed:
// the capture releases its surfaces with its own (Reset, shutdown), so no COM call happens at process exit.
inline ps2port::DeviceInspector* inspector() noexcept { static ps2port::DeviceInspector* instance = new ps2port::DeviceInspector; return instance; }

struct FrameState { uint64_t frame = UINT64_MAX; uint64_t race = 0; std::array<char, 64> course{}; };
inline FrameState& frame_state() noexcept { static thread_local FrameState state; return state; }

// First indexed draw of a frame: the race of this frame (certificate cached per frame), the capture's race, the ledger.
inline void frame_begin(Device8& d, ps2port::PS2PortExtension& x, ps2port::ReflectionPilot* p) noexcept {
    auto& state = frame_state();
    bool single = false;
    const auto cert = courseintegration::certificate(d, single);
    const uint64_t previous_race = state.race;
    state.race = cert.valid ? cert.race_generation : 0;
    if (p && state.race && state.race != previous_race) p->new_race();
    state.course.fill(0);
    if (cert.valid) { const size_t length = ::strnlen(cert.course_id.data(), state.course.size() - 1); std::memcpy(state.course.data(), cert.course_id.data(), length); }
    if (p && p->active() && p->needs_mixed_source()) {
        auto& capture = p->mixed_capture();
        capture.set_observer(&d, capture_event);
        capture.set_inspector(inspector());
        capture.set_race(state.race);
    }
    if (x.ledger_enabled() && cert.valid)
        x.ledger_race_frame(d.trace.frame_number(), cert.race_generation, cert.owner_lifetime, state.course.data(),
                            d.trace.resources.items.size(), d.trace.resources.next_serial);
}


// ---- the player car in its own reflection ---------------------------------------------------------------------------------
// Draws that sample the environment target (stage 1 coordinates = camera space normal) are the car. Their projected local
// bounding boxes make the mask that the late capture refills (reflection_exclusion.hpp). One instance per render thread.
struct CarMaskState {
    struct Entry { uintptr_t buffer = 0; uint64_t generation = 0, offset = 0, size = 0; ps2diag::Aabb box; };
    ps2diag::CarSilhouette silhouette;
    uint64_t frame = UINT64_MAX;
    std::array<Entry, 64> cache{};
    size_t next = 0;
    unsigned boxes_total = 0, no_shadow = 0;
};
inline CarMaskState& car_mask() noexcept { static thread_local CarMaskState state; return state; }

inline void note_env_draw(Device8& d, uint32_t min_index, uint32_t vertices) noexcept {
    try {
        auto& mask = car_mask();
        const uint64_t frame = d.trace.frame_number();
        if (mask.frame != frame) { mask.frame = frame; mask.silhouette.clear(); }
        auto& n = *d.native();
        DWORD coord = 0, fvf = 0;
        if (FAILED(n.GetTextureStageState(1, D3DTSS_TEXCOORDINDEX, &coord)) || coord != D3DTSS_TCI_CAMERASPACENORMAL) return;
        if (FAILED(n.GetVertexShader(&fvf)) || (fvf & D3DFVF_POSITION_MASK) != D3DFVF_XYZ || !vertices) return;
        IDirect3DVertexBuffer8* vb = nullptr; IDirect3DIndexBuffer8* ib = nullptr; UINT stride = 0, base = 0;
        const bool have = SUCCEEDED(n.GetStreamSource(0, &vb, &stride)) && vb && SUCCEEDED(n.GetIndices(&ib, &base)) && ib;
        const auto release = [&]() noexcept { if (vb) vb->Release(); if (ib) ib->Release(); };
        if (!have || stride < 12) { release(); return; }
        const uint64_t offset = (uint64_t(base) + min_index) * stride, size = uint64_t(vertices) * stride;
        const uintptr_t buffer = reinterpret_cast<uintptr_t>(vb);
        const uint64_t generation = d.trace.resources.generation(buffer);
        ps2diag::Aabb box; bool cached = false;
        for (const auto& e : mask.cache)
            if (e.buffer == buffer && e.generation == generation && e.offset == offset && e.size == size) { box = e.box; cached = true; break; }
        if (!cached) {
            std::vector<BYTE> bytes; uint64_t revision = 0;
            if (!generation || !d.copy_buffer_shadow(vb, BufferKind::Vertex, generation, offset, static_cast<size_t>(size), bytes, revision)) {
                ++mask.no_shadow; release(); return;
            }
            box = ps2diag::aabb_from_vertices(bytes.data(), vertices, stride);
            mask.cache[mask.next++ % mask.cache.size()] = {buffer, generation, offset, size, box};
        }
        release();
        if (!box.valid || box.diagonal() > ps2diag::kMaxCarBoxDiagonal) return;
        D3DMATRIX world{}, view{}, projection{}; D3DVIEWPORT8 vp{};
        if (FAILED(n.GetTransform(D3DTS_WORLD, &world)) || FAILED(n.GetTransform(D3DTS_VIEW, &view)) ||
            FAILED(n.GetTransform(D3DTS_PROJECTION, &projection)) || FAILED(n.GetViewport(&vp))) return;
        std::array<ps2diag::Point2, 8> corners;
        if (!ps2diag::project_box(box, &world.m[0][0], &view.m[0][0], &projection.m[0][0],
                                  {float(vp.X), float(vp.Y), float(vp.Width), float(vp.Height)}, corners)) return;
        if (mask.silhouette.add(corners)) ++mask.boxes_total;
    } catch (...) {}
}

// Before the late capture of `frame`: the hull of the car draws of that frame, in 64x64 target coordinates.
inline void publish_car_mask(Device8& d, ps2port::ReflectionPilot& p, uint64_t frame) noexcept {
    try {
        auto& capture = p.mixed_capture();
        if (!capture.excludes_car()) return;
        auto& mask = car_mask();
        if (mask.frame != frame || mask.silhouette.empty()) return;
        IDirect3DSurface8* back = nullptr; D3DSURFACE_DESC desc{};
        if (FAILED(d.native()->GetBackBuffer(0, D3DBACKBUFFER_TYPE_MONO, &back)) || !back) return;
        const bool ok = SUCCEEDED(back->GetDesc(&desc));
        back->Release();
        if (!ok) return;
        std::vector<ps2diag::Point2> hull, env;
        if (mask.silhouette.hull(hull) && ps2diag::hull_to_env(hull, float(desc.Width), float(desc.Height), env))
            capture.set_exclusion(frame, std::move(env));
    } catch (...) {}
}

// Every indexed draw (before the integrations see it). Cheap when neither the ledger nor the capture timing is in use.
inline void note_draw(Device8& d, uint32_t triangles, uint32_t min_index, uint32_t vertices) noexcept {
    auto* x = d.ps2_port();
    if (!x) return;
    auto* p = x->reflection();
    const bool reflect = p && p->active() && p->needs_mixed_source();
    if (!x->ledger_enabled() && !reflect) return;
    const uint64_t frame = d.trace.frame_number();
    auto& state = frame_state();
    if (state.frame != frame) { state.frame = frame; try { frame_begin(d, *x, p); } catch (...) {} }
    if (reflect && p->mixed_capture().excludes_car() && p->mixed_capture().late_wanted()) note_env_draw(d, min_index, vertices);
    if (reflect && x->ledger_enabled() && p->mixed_capture().decision().stage_diag()) {
        const auto& fvf = d.trace.shadow.bindings.vertex_shader;
        x->draw_ledger().note(frame, fvf.known ? fvf.value : 0u, triangles);
    }
}

inline void write_stage_report(Device8& d, ps2port::PS2PortExtension& x, ps2port::ReflectionPilot& p, const ps2port::ReflectionStageReport& r) noexcept {
    try {
        const auto& state = frame_state();
        std::string png_name;
        if (!r.montage.rgb.empty()) {
            png_name = "stage-r" + std::to_string(r.race) + "-f" + std::to_string(r.frame) + (r.late ? "-late" : "-inframe") + ".png";
            x.diag_write_file(png_name, ps2diag::encode_png(r.montage.width, r.montage.height, r.montage.rgb));
        }
        const auto& decision = p.mixed_capture().decision();
        const auto& status = p.mixed_capture().last_status();
        std::string json = "{\"type\":\"ps2_reflection_stage\",\"frame\":" + std::to_string(r.frame) + ",\"race_generation\":" + std::to_string(r.race) +
            ",\"course\":" + ps2diag::quote(state.course.data()) + ",\"ordinal\":" + std::to_string(r.ordinal) +
            ",\"late\":" + (r.late ? "true" : "false") + ",\"timing\":" + ps2diag::quote(ps2diag::timing_name(decision.timing())) +
            ",\"timing_now\":" + ps2diag::quote(decision.mode_now()) + ",\"reason\":" + ps2diag::quote(r.reason) +
            ",\"readback_ok\":" + (r.readback_ok ? "true" : "false") + ",\"source_format\":" + std::to_string(static_cast<uint32_t>(r.source_format)) +
            ",\"source_multisample\":" + std::to_string(static_cast<uint32_t>(r.source_multisample)) + ",\"env_format\":" + std::to_string(static_cast<uint32_t>(r.env_format)) +
            ",\"capture\":{\"copy_hr\":" + std::to_string(static_cast<uint32_t>(status.copy_hr)) + ",\"restore_hr\":" + std::to_string(static_cast<uint32_t>(status.restore_hr)) +
            ",\"private_draws\":" + std::to_string(status.private_draws) + ",\"layout\":[" + std::to_string(status.layout.source_width) + "," +
            std::to_string(status.layout.source_height) + "," + std::to_string(status.layout.texture_width) + "," + std::to_string(status.layout.texture_height) + "]}" +
            ",\"served\":{\"total\":" + std::to_string(p.mixed_capture().served_total()) + ",\"last_frame\":" + std::to_string(p.mixed_capture().served_last_frame()) +
            ",\"frame_count\":" + std::to_string(p.mixed_capture().served_in_frame()) + "}" +
            ",\"source\":" + ps2diag::stats_json(r.source) + ",\"ps2frame\":" + ps2diag::stats_json(r.ps2frame) +
            ",\"bottom_third\":" + ps2diag::stats_json(r.bottom) + ",\"world_incomplete\":" + (ps2diag::world_incomplete(r.bottom) ? "true" : "false") +
            ",\"static\":" + ps2diag::stats_json(r.static_term) + ",\"env\":" + ps2diag::stats_json(r.env) + ",\"dynamic\":" + ps2diag::stats_json(r.dynamic) +
            ",\"png\":" + ps2diag::quote(png_name) + "}";
        x.diag_write(json);
        (void)d;
    } catch (...) {}
}

inline void flush_reports(Device8& d, ps2port::PS2PortExtension& x, ps2port::ReflectionPilot* p) noexcept {
    try {
        ps2diag::DrawLedger::Report order;
        if (x.draw_ledger().take(order)) x.diag_write(ps2diag::order_json(order));
        if (!p) return;
        ps2port::ReflectionStageReport report;
        if (p->mixed_capture().take_stage_report(report) && report.valid) write_stage_report(d, x, *p, report);
    } catch (...) {}
}

// The typed pre-UI boundary of a frame (first UI draw): the course and every car of the frame are drawn.
inline HRESULT before_ui(Device8& d, bool ui_callsite) noexcept {
    auto* x = d.ps2_port();
    if (!x || !ui_callsite) return S_OK;
    auto* p = x->reflection();
    const bool reflect = p && p->active() && p->needs_mixed_source();
    if (!reflect && !x->ledger_enabled()) return S_OK;
    if (!d.trace.scene_active || GetCurrentThreadId() != d.trace.render_thread_id()) return S_OK;
    static thread_local uint64_t last_frame = UINT64_MAX;
    const uint64_t frame = d.trace.frame_number();
    if (last_frame == frame) return S_OK;
    last_frame = frame;
    flush_reports(d, *x, p);
    if (!reflect) return S_OK;
    auto& capture = p->mixed_capture();
    if (!capture.late_wanted()) return S_OK;
    capture.set_observer(&d, capture_event);
    capture.set_writer(&d, [](void* owner, uint32_t slot, const Args& args, HRESULT hr) noexcept {
        auto& device = *static_cast<Device8*>(owner);
        device.trace.after(slot, args, static_cast<uint32_t>(hr), 0, &args, 256, false, true);
    });
    publish_car_mask(d, *p, frame);
    capture.capture_late(*d.native(), p->static_texture(), frame, d.trace.shadow.recording || d.trace.effective_shadow.recording);
    if (capture.pending()) {
        const HRESULT restored = ps2integration::repair(d);
        if (FAILED(restored)) { p->disable("mixed_capture_restore_failed"); return restored; }
    }
    return S_OK;
}

} // namespace gfx2::reflectionintegration
