#pragma once
// COURSE-RENDER-FIX1 diagnostics only: the GPU readbacks of the reflection capture (timing probe and stage report).
//
// reflection_capture.cpp itself stays free of CPU readbacks (one CopyRects, three private draws; tests/test_reflection_contract.py,
// test_full_coverage.py, test_reflection11_integration.py). After a successful capture it hands its surfaces to a
// ReflectionInspector, which is installed only by the native glue (reflection_timing_native.hpp) and by tests. Nothing here runs
// in the default InFrame mode without ReflectionStageDiag.
#include "reflection_capture.hpp"
#include <array>
#include <vector>

namespace gfx2::ps2port {

class DeviceInspector final : public ReflectionInspector {
    struct Slot { IDirect3DSurface8* surface = nullptr; UINT width = 0, height = 0; D3DFORMAT format = D3DFMT_UNKNOWN; };
    std::array<Slot, 4> slots_{};
    static void drop(IDirect3DSurface8*& surface) noexcept { if (surface) surface->Release(); surface = nullptr; }
    static bool to_pixel_format(D3DFORMAT format, ps2diag::PixelFormat& out) noexcept {
        switch (format) {
        case D3DFMT_X8R8G8B8: out = ps2diag::PixelFormat::X8R8G8B8; return true;
        case D3DFMT_A8R8G8B8: out = ps2diag::PixelFormat::A8R8G8B8; return true;
        case D3DFMT_A1R5G5B5: out = ps2diag::PixelFormat::A1R5G5B5; return true;
        case D3DFMT_R5G6B5: out = ps2diag::PixelFormat::R5G6B5; return true;
        default: return false;
        }
    }
    // Copies `rect` of a render-target surface into a cached system-memory image surface and converts it to RGB.
    bool read(IDirect3DDevice8& native, IDirect3DSurface8* source, const RECT& rect, D3DFORMAT format, std::vector<uint8_t>& rgb,
              UINT& width, UINT& height) noexcept {
        rgb.clear();
        ps2diag::PixelFormat pixel;
        if (!source || rect.right <= rect.left || rect.bottom <= rect.top || !to_pixel_format(format, pixel)) return false;
        width = UINT(rect.right - rect.left); height = UINT(rect.bottom - rect.top);
        Slot* slot = nullptr;
        for (auto& s : slots_) if (s.surface && s.width == width && s.height == height && s.format == format) { slot = &s; break; }
        if (!slot) {
            for (auto& s : slots_) if (!s.surface) { slot = &s; break; }
            if (!slot) { slot = &slots_[0]; drop(slot->surface); *slot = {}; }
            IDirect3DSurface8* image = nullptr;
            const HRESULT created = native.CreateImageSurface(width, height, format, &image);
            if (FAILED(created) || !image) { drop(image); return false; }
            *slot = {image, width, height, format};
        }
        const POINT origin{0, 0};
        if (FAILED(native.CopyRects(source, &rect, 1, slot->surface, &origin))) return false;
        D3DLOCKED_RECT locked{};
        if (FAILED(slot->surface->LockRect(&locked, nullptr, D3DLOCK_READONLY)) || !locked.pBits) return false;
        try { rgb = ps2diag::to_rgb(static_cast<const uint8_t*>(locked.pBits), UINT(locked.Pitch), width, height, pixel); } catch (...) { rgb.clear(); }
        slot->surface->UnlockRect();
        return !rgb.empty();
    }
public:
    ~DeviceInspector() override { release(); }
    void release() noexcept override { for (auto& s : slots_) { drop(s.surface); s = {}; } }
    void inspect(const ReflectionInspectInput& in, ReflectionInspectResult& out) noexcept override {
        out = {};
        try {
            ReflectionStageReport& report = out.report;
            report.frame = in.frame; report.late = in.late; report.race = in.race; report.ordinal = in.ordinal; report.reason = in.reason;
            report.source_format = in.source_format; report.source_multisample = in.source_multisample;
            const UINT top = kPS2FrameHeight * 2 / 3, fw = kPS2FrameWidth, fh = kPS2FrameHeight;
            std::vector<uint8_t> frame_rgb, bottom_rgb; UINT w = 0, h = 0;
            const RECT area = in.stage ? RECT{0, 0, LONG(fw), LONG(fh)} : RECT{0, LONG(top), LONG(fw), LONG(fh)};
            if (!read(*in.native, in.ps2frame, area, in.copy_format, frame_rgb, w, h)) return;
            if (in.stage) bottom_rgb.assign(frame_rgb.begin() + size_t(top) * fw * 3u, frame_rgb.end()); else bottom_rgb = frame_rgb;
            report.bottom = ps2diag::analyze(bottom_rgb, fw, fh - top);
            out.probe_ok = true;
            out.incomplete = ps2diag::world_incomplete(report.bottom);
            if (!in.stage) return;
            report.ps2frame = ps2diag::analyze(frame_rgb, fw, fh);
            std::vector<uint8_t> source_rgb, env_rgb, dynamic_rgb; UINT sw = 0, sh = 0, ew = 0, eh = 0;
            const RECT source_area{0, 0, LONG(in.source_width), LONG(in.source_height)};
            const RECT env_area{0, 0, 64, 64};
            const bool source_ok = read(*in.native, in.copy, source_area, in.copy_format, source_rgb, sw, sh);
            const bool env_ok = read(*in.native, in.target, env_area, in.target_format, env_rgb, ew, eh);
            if (source_ok) report.source = ps2diag::analyze(source_rgb, sw, sh);
            if (env_ok) {
                report.env = ps2diag::analyze(env_rgb, 64, 64); report.env_format = in.target_format;
                if (in.static_rgb && in.static_rgb->size() == env_rgb.size()) {
                    report.static_term = ps2diag::analyze(*in.static_rgb, 64, 64);
                    dynamic_rgb.resize(env_rgb.size());
                    for (size_t i = 0; i < env_rgb.size(); ++i)
                        dynamic_rgb[i] = env_rgb[i] > (*in.static_rgb)[i] ? uint8_t(env_rgb[i] - (*in.static_rgb)[i]) : uint8_t(0);
                    report.dynamic = ps2diag::analyze(dynamic_rgb, 64, 64);
                }
            }
            if (source_ok && env_ok) {
                std::vector<std::vector<uint8_t>> tiles; std::vector<std::pair<uint32_t, uint32_t>> sizes;
                tiles.push_back(ps2diag::box_downsample(source_rgb, sw, sh, 128, 96)); sizes.push_back({128, 96});
                tiles.push_back(ps2diag::box_downsample(frame_rgb, fw, fh, 128, 112)); sizes.push_back({128, 112});
                tiles.push_back(ps2diag::scale_nearest(env_rgb, 64, 64, 2)); sizes.push_back({128, 128});
                tiles.push_back(dynamic_rgb.empty() ? std::vector<uint8_t>(128u * 128u * 3u, 0) : ps2diag::scale_nearest(dynamic_rgb, 64, 64, 2, 2.7f));
                sizes.push_back({128, 128});
                report.montage = ps2diag::make_montage(tiles, sizes);
            }
            report.readback_ok = source_ok && env_ok;
            report.valid = true;
        } catch (...) { out = {}; }
    }
};

} // namespace gfx2::ps2port
