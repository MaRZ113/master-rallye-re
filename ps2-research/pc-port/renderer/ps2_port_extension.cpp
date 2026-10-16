#include "ps2_port_extension.hpp"
#include "reflection_pilot.hpp"
#include "course_objects.hpp"
#include "grass_pilot.hpp"
#include "vehicle_partition.hpp"
#include "xtrail_fidelity.hpp"
#include "frontend_model.hpp"

#include "foliage_probe.hpp"
#include "provenance.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <iomanip>
#include <iterator>
#include <limits>
#include <sstream>

namespace gfx2::ps2port {
namespace {
constexpr char TARGET_EXE_SHA[] = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4";
constexpr char TARGET_GEOMETRY_SHA[] = "2b60b1f044601052bb5eaeca074615abe3947fdc1b0769c17d300a0b3b3e6f7d";
constexpr D3DRENDERSTATETYPE PIXEL_STATES[] = {
    D3DRS_ALPHATESTENABLE, D3DRS_ALPHAREF, D3DRS_ALPHAFUNC,
    D3DRS_ALPHABLENDENABLE, D3DRS_SRCBLEND, D3DRS_DESTBLEND,
    D3DRS_ZENABLE, D3DRS_ZWRITEENABLE, D3DRS_ZFUNC, D3DRS_COLORWRITEENABLE
};
constexpr const char* PIXEL_STATE_NAMES[] = {
    "ALPHATESTENABLE", "ALPHAREF", "ALPHAFUNC", "ALPHABLENDENABLE",
    "SRCBLEND", "DESTBLEND", "ZENABLE", "ZWRITEENABLE", "ZFUNC", "COLORWRITEENABLE"
};
constexpr D3DTEXTURESTAGESTATETYPE PIXEL_TEXTURE_STAGE_STATES[] = {
    D3DTSS_COLOROP, D3DTSS_COLORARG1, D3DTSS_COLORARG2,
    D3DTSS_ALPHAOP, D3DTSS_ALPHAARG1, D3DTSS_ALPHAARG2,
    D3DTSS_TEXCOORDINDEX, D3DTSS_TEXTURETRANSFORMFLAGS
};
constexpr const char* PIXEL_TEXTURE_STAGE_STATE_NAMES[] = {
    "COLOROP", "COLORARG1", "COLORARG2", "ALPHAOP", "ALPHAARG1", "ALPHAARG2",
    "TEXCOORDINDEX", "TEXTURETRANSFORMFLAGS"
};

struct SurfaceRelease {
    IDirect3DSurface8* value = nullptr;
    ~SurfaceRelease() { if (value) value->Release(); }
};
struct TextureRelease {
    IDirect3DBaseTexture8* value = nullptr;
    ~TextureRelease() { if (value) value->Release(); }
};

bool same_com_identity(IUnknown* left, IUnknown* right, HRESULT& left_hr, HRESULT& right_hr) noexcept {
    IUnknown* left_identity = nullptr;
    IUnknown* right_identity = nullptr;
    left_hr = left ? left->QueryInterface(IID_IUnknown, reinterpret_cast<void**>(&left_identity)) : E_POINTER;
    right_hr = right ? right->QueryInterface(IID_IUnknown, reinterpret_cast<void**>(&right_identity)) : E_POINTER;
    const bool same = SUCCEEDED(left_hr) && SUCCEEDED(right_hr) && left_identity &&
                      right_identity && left_identity == right_identity;
    if (left_identity) left_identity->Release();
    if (right_identity) right_identity->Release();
    return same;
}

std::string json_escape(const char* value) {
    std::string out = "\"";
    if (value) for (const unsigned char c : std::string_view(value)) {
        if (c == '\\' || c == '\"') { out.push_back('\\'); out.push_back(static_cast<char>(c)); }
        else if (c < 0x20) out += "\\u00" + std::string(1, "0123456789abcdef"[c >> 4]) + "0123456789abcdef"[c & 15];
        else out.push_back(static_cast<char>(c));
    }
    out.push_back('\"');
    return out;
}

std::string hresult_json(HRESULT value) {
    if (value == E_PENDING) return "null";
    std::ostringstream out;
    out << "\"0x" << std::hex << std::setw(8) << std::setfill('0')
        << static_cast<uint32_t>(value) << "\"";
    return out.str();
}

void append_matrix_json(std::ostringstream& out, const D3DMATRIX& matrix) {
    out << '[';
    for (unsigned row = 0; row < 4; ++row) {
        if (row) out << ',';
        out << '[';
        for (unsigned col = 0; col < 4; ++col) {
            if (col) out << ',';
            out << std::setprecision(std::numeric_limits<float>::max_digits10) << matrix.m[row][col];
        }
        out << ']';
    }
    out << ']';
}

void append_surface_json(std::ostringstream& out, const D3DSURFACE_DESC& desc, bool valid) {
    if (!valid) { out << "null"; return; }
    out << "{\"width\":" << desc.Width << ",\"height\":" << desc.Height
        << ",\"format\":" << static_cast<uint32_t>(desc.Format)
        << ",\"multisample\":" << static_cast<uint32_t>(desc.MultiSampleType)
        << ",\"pool\":" << static_cast<uint32_t>(desc.Pool)
        << ",\"usage\":" << desc.Usage << '}';
}

std::wstring port_ini_path(const std::wstring& renderer_ini) {
    const auto slash = renderer_ini.find_last_of(L"\\/");
    return (slash == std::wstring::npos ? std::wstring{} : renderer_ini.substr(0, slash + 1)) + L"PS2Port.ini";
}

bool same_sha(const std::string& a, const char* b) noexcept {
    if (a.size() != 64) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        char x = a[i], y = b[i];
        if (x >= 'A' && x <= 'F') x = static_cast<char>(x - 'A' + 'a');
        if (x != y) return false;
    }
    return true;
}

std::string geometry_sha(const DrawSnapshot& s) {
    if (!s.complete_mirror_coverage || s.primitive_type != D3DPT_TRIANGLELIST ||
        s.primitive_count != 48 || s.vertex_count == 0 || s.vertex_count > 2048 ||
        s.stride < 12 || s.stride > 256 || s.vertex_generation == 0 ||
        s.index_generation == 0 || s.vertex_revision == 0 || s.index_revision == 0)
        return {};
    unsigned index_size = s.index_format == D3DFMT_INDEX16 ? 2u :
                          s.index_format == D3DFMT_INDEX32 ? 4u : 0u;
    if (!index_size) return {};
    const uint64_t absolute_v_offset = (uint64_t(s.base_vertex) + s.min_index) * s.stride;
    if (absolute_v_offset < s.vertex_byte_offset) return {};
    const uint64_t v_offset = absolute_v_offset - s.vertex_byte_offset;
    const uint64_t v_size = uint64_t(s.vertex_count) * s.stride;
    const uint64_t i_size = uint64_t(s.primitive_count) * 3u * index_size;
    if (v_offset > s.vertex_bytes.size() || v_size > s.vertex_bytes.size() - v_offset ||
        i_size != s.index_bytes.size()) return {};
    uint32_t diffuse = 0;
    if (!foliage_layout(s.fvf, s.stride, diffuse)) return {};

    std::vector<std::string> faces;
    try { faces.reserve(s.primitive_count); } catch (...) { return {}; }
    for (uint32_t face = 0; face < s.primitive_count; ++face) {
        float xyz[9]{};
        for (unsigned k = 0; k < 3; ++k) {
            uint32_t index = 0;
            const auto* raw = s.index_bytes.data() + (uint64_t(face) * 3 + k) * index_size;
            if (index_size == 2) { unsigned short small_index = 0; std::memcpy(&small_index, raw, 2); index = small_index; }
            else std::memcpy(&index, raw, 4);
            if (index < s.min_index || uint64_t(index - s.min_index) >= s.vertex_count) return {};
            const uint64_t offset = v_offset + uint64_t(index - s.min_index) * s.stride;
            if (offset > s.vertex_bytes.size() || 12 > s.vertex_bytes.size() - offset) return {};
            std::memcpy(xyz + 3 * k, s.vertex_bytes.data() + offset, 12);
        }
        auto face_hash = foliage_face_hash(xyz);
        if (face_hash.empty()) return {};
        faces.push_back(std::move(face_hash));
    }
    std::sort(faces.begin(), faces.end());
    std::string canonical;
    try { canonical.reserve(faces.size() * 64); for (const auto& face : faces) canonical += face; }
    catch (...) { return {}; }
    return sha256_bytes(canonical.data(), canonical.size());
}

}

bool is_france1_bush01_geometry(std::string_view sha256) noexcept {
    if (sha256.size() != 64) return false;
    for (size_t i = 0; i < sha256.size(); ++i) {
        char x = sha256[i];
        if (x >= 'A' && x <= 'F') x = static_cast<char>(x - 'A' + 'a');
        if (x != TARGET_GEOMETRY_SHA[i]) return false;
    }
    return true;
}

PS2PortExtension::PS2PortExtension(bool exact_build, const std::string& exe_sha,
                                   const std::wstring& renderer_ini) noexcept {
    build_valid_ = exact_build && same_sha(exe_sha, TARGET_EXE_SHA);
    if (!build_valid_) { config_reason_ = "unsupported_build_stock"; return; }
    try {
        const auto ini = port_ini_path(renderer_ini);
        const UINT mode = GetPrivateProfileIntW(L"PS2Port", L"FoliageMode", 0, ini.c_str());
        diagnostics_ = GetPrivateProfileIntW(L"PS2Port", L"Diagnostics", 0, ini.c_str()) == 1;
        frontend_model_=std::make_unique<FrontendModel>(build_valid_,ini);
        race_model_=std::make_unique<FrontendModel>(build_valid_,ini,true);
        wheel_model_=std::make_unique<FrontendModel>(build_valid_,ini,2);
        frontend_geometry_diagnostics_ = GetPrivateProfileIntW(L"PS2Port", L"FrontendGeometryDiagnostics", 0, ini.c_str()) == 1;
        const UINT probe = GetPrivateProfileIntW(L"PS2Port", L"PixelProbe", 0, ini.c_str());
        pixel_probe_requested_ = probe == 1;
        if (mode == 0) { mode_ = PilotMode::Stock; config_reason_ = "stock_default_or_configured"; }
        else if (mode == 1) { mode_ = PilotMode::France1Bush01Treeblend; config_reason_ = "france1_bush01_opt_in"; }
        else if (mode == 2) { mode_ = PilotMode::France1Bush01AlphaBlendOnly; config_reason_ = "france1_bush01_alpha_blend_only"; }
        else if (mode == 3) { mode_ = PilotMode::France1Bush01DepthWriteOnly; config_reason_ = "france1_bush01_depth_write_only"; }
        else { config_reason_ = "invalid_mode_stock"; }
        if (probe == 1) {
            const INT x = static_cast<INT>(GetPrivateProfileIntW(L"PS2Port", L"PixelX", -1, ini.c_str()));
            const INT y = static_cast<INT>(GetPrivateProfileIntW(L"PS2Port", L"PixelY", -1, ini.c_str()));
            const INT later = static_cast<INT>(GetPrivateProfileIntW(L"PS2Port", L"PixelLaterDrawOrdinal", -1, ini.c_str()));
            if (!build_valid_) pixel_probe_status_ = "unsupported_build";
            else if (!pixel_probe_mode_supported(mode)) pixel_probe_status_ = "unsupported_mode_pixel_probe_allows_stock_or_mode3";
            else if (x < 0 || y < 0 || x >= 32768 || y >= 32768) pixel_probe_status_ = "pixel_coordinates_missing_or_out_of_range";
            else if (later < -1 || later > 1000000) pixel_probe_status_ = "later_draw_ordinal_out_of_range";
            else { pixel_probe_enabled_ = true; pixel_probe_x_ = x; pixel_probe_y_ = y;
                   pixel_probe_later_ordinal_ = later; pixel_probe_status_ = "configured_waiting_for_device"; }
        }
        reflection_ = std::make_unique<ReflectionPilot>(build_valid_, ini);
        vehicle_partitions_ = std::make_unique<VehiclePartitionPilot>(build_valid_, ini);
        xtrail_ = std::make_unique<XtrailFidelity>(build_valid_,ini);
        course_objects_ = std::make_unique<CourseObjectsPilot>(build_valid_, ini);
        grass_ = std::make_unique<GrassPilot>(build_valid_, ini);
        shrubs_ = std::make_unique<GrassPilot>(build_valid_, ini,GroundDetailKind::Shrubs);
    } catch (...) { mode_ = PilotMode::Stock; config_reason_ = "configuration_error_stock"; }
}

bool PS2PortExtension::requested() const noexcept {
    return mode_ != PilotMode::Stock || (reflection_ && reflection_->mirroring_required());
}
bool PS2PortExtension::active() const noexcept { return requested() && build_valid_ && !disabled_; }
bool PS2PortExtension::buffer_mirroring_required() const noexcept { return active() || pixel_probe_enabled() || frontend_geometry_diagnostics() || (wheel_model_ && wheel_model_->requested()) || (race_model_ && race_model_->requested()) || (frontend_model_ && frontend_model_->requested()); }
bool PS2PortExtension::analysis_enabled() const noexcept { return active() || pixel_probe_enabled() ||
    (!disabled_ && ((course_objects_ && course_objects_->identity_requested()) ||
                  (grass_ && grass_->identity_requested()) || (shrubs_ && shrubs_->identity_requested()))); }

bool PS2PortExtension::native_states_pending() const noexcept {
    return (wheel_model_ && wheel_model_->transaction.pending()) || (race_model_ && race_model_->states_pending()) || (frontend_model_ && frontend_model_->transaction.pending()) || (xtrail_ && (xtrail_->blocked() || xtrail_->transaction.pending() || xtrail_->glass_pending())) ||
        (reflection_ && (reflection_->blocked() || reflection_->transaction().changed_mask ||
            reflection_->mixed_capture().pending())) ||
        (course_objects_ && (course_objects_->blocked() || course_objects_->transaction.has_pending())) ||
        (grass_ && (grass_->blocked() || grass_->transaction.has_pending())) ||
        (shrubs_ && (shrubs_->blocked() || shrubs_->transaction.has_pending()));
}

PS2PortExtension::~PS2PortExtension() { pixel_probe_release(); }

const char* PS2PortExtension::mode_name() const noexcept {
    switch (mode_) {
    case PilotMode::France1Bush01Treeblend: return "treeblend_all_states";
    case PilotMode::France1Bush01AlphaBlendOnly: return "alpha_blend_only";
    case PilotMode::France1Bush01DepthWriteOnly: return "depth_write_only";
    case PilotMode::Stock: default: return "stock";
    }
}

bool PS2PortExtension::claim_draw_diagnostic() noexcept {
    if (!diagnostics_ || !active()) return false;
    bool expected = false;
    return draw_diagnostic_claimed_.compare_exchange_strong(expected, true);
}

Classification PS2PortExtension::classify(const DrawSnapshot& snapshot) const noexcept {
    Classification result;
    if (!analysis_enabled()) { result.identity = disabled_ ? "extension_disabled" : "stock_mode"; return result; }
    if (!snapshot.supported_build) { result.identity = "unsupported_build"; return result; }
    if (!snapshot.france1_course_verified || !snapshot.race_generation || !snapshot.owner_lifetime) {
        result.identity = "france1_runtime_owner_unverified"; return result;
    }
    if (snapshot.device_id == 0 || snapshot.reset_generation != reset_generation_) {
        result.identity = "stale_device_or_reset_generation"; return result;
    }
    if (!snapshot.vertex_resource || !snapshot.index_resource ||
        !snapshot.vertex_generation || !snapshot.index_generation) {
        result.identity = "missing_current_resource_identity"; return result;
    }
    if (!snapshot.vertex_revision || !snapshot.index_revision || !snapshot.complete_mirror_coverage) {
        result.identity = "missing_or_incomplete_current_upload_mirror"; return result;
    }
    try { result.geometry_sha256 = geometry_sha(snapshot); }
    catch (...) { result.identity = "geometry_hash_exception"; return result; }
    if (result.geometry_sha256.empty()) { result.identity = "unsupported_or_incomplete_draw_geometry"; return result; }
    if (!is_france1_bush01_geometry(result.geometry_sha256)) { result.identity = "geometry_signature_mismatch"; return result; }
    result.identity = "exact_france1_bush01_source_geometry_current_generations";
    result.state = state_request_for_mode(mode_);
    return result;
}

void PS2PortExtension::device_reset(bool successful) noexcept {
    if (!successful) return;
    if (reset_generation_ != UINT64_MAX) ++reset_generation_;
    else disable("reset_generation_overflow");
}

void PS2PortExtension::pixel_probe_release() noexcept {
    if (pixel_probe_gpu_surface_) { pixel_probe_gpu_surface_->Release(); pixel_probe_gpu_surface_ = nullptr; }
    if (pixel_probe_cpu_surface_) { pixel_probe_cpu_surface_->Release(); pixel_probe_cpu_surface_ = nullptr; }
    pixel_probe_ready_ = false;
}

bool PS2PortExtension::initialize_pixel_probe(IDirect3DDevice8& device) noexcept {
    pixel_probe_release();
    if (!pixel_probe_enabled()) return false;
    pixel_probe_initial_caps_ = {};
    pixel_probe_initial_color_desc_ = {};
    pixel_probe_initial_depth_desc_ = {};
    pixel_probe_initial_caps_hr_ = device.GetDeviceCaps(&pixel_probe_initial_caps_);
    if (FAILED(pixel_probe_initial_caps_hr_)) { pixel_probe_status_ = "get_device_caps_failed"; return false; }
    SurfaceRelease color;
    pixel_probe_initial_color_hr_ = device.GetRenderTarget(&color.value);
    if (FAILED(pixel_probe_initial_color_hr_) || !color.value) { pixel_probe_status_ = "get_render_target_failed"; return false; }
    pixel_probe_initial_color_hr_ = color.value->GetDesc(&pixel_probe_initial_color_desc_);
    if (FAILED(pixel_probe_initial_color_hr_)) { pixel_probe_status_ = "get_color_surface_desc_failed"; return false; }
    SurfaceRelease depth;
    pixel_probe_initial_depth_hr_ = device.GetDepthStencilSurface(&depth.value);
    if (SUCCEEDED(pixel_probe_initial_depth_hr_) && depth.value)
        pixel_probe_initial_depth_hr_ = depth.value->GetDesc(&pixel_probe_initial_depth_desc_);
    if (pixel_probe_initial_caps_.Caps2 & D3DCAPS2_NO2DDURING3DSCENE) {
        pixel_probe_status_ = "unsupported_no_2d_operations_during_scene";
        return false;
    }
    if (!pixel_probe_format_supported(pixel_probe_initial_color_desc_.Format)) {
        pixel_probe_status_ = "unsupported_color_surface_format";
        return false;
    }
    pixel_probe_format_ = pixel_probe_initial_color_desc_.Format;
    pixel_probe_gpu_create_hr_ = device.CreateRenderTarget(4, 1, pixel_probe_format_,
                                                           D3DMULTISAMPLE_NONE, FALSE,
                                                           &pixel_probe_gpu_surface_);
    if (FAILED(pixel_probe_gpu_create_hr_) || !pixel_probe_gpu_surface_) {
        pixel_probe_status_ = "create_gpu_scratch_failed";
        pixel_probe_release();
        return false;
    }
    pixel_probe_cpu_create_hr_ = device.CreateImageSurface(4, 1, pixel_probe_format_,
                                                           &pixel_probe_cpu_surface_);
    if (FAILED(pixel_probe_cpu_create_hr_) || !pixel_probe_cpu_surface_) {
        pixel_probe_status_ = "create_system_memory_readback_failed";
        pixel_probe_release();
        return false;
    }
    pixel_probe_ready_ = true;
    pixel_probe_status_ = "ready";
    return true;
}

void PS2PortExtension::pixel_probe_before_reset() noexcept {
    if (!pixel_probe_enabled()) return;
    if (pixel_probe_claimed_.load(std::memory_order_acquire) && !pixel_probe_finalized_) {
        pixel_probe_frame_.store(0, std::memory_order_release);
        pixel_probe_claimed_.store(false, std::memory_order_release);
        pixel_probe_target_ = {};
        pixel_probe_samples_ = {};
        pixel_probe_sample_count_ = 0;
        pixel_probe_copy_mask_ = 0;
        pixel_probe_finalized_ = false;
    }
    pixel_probe_release();
    pixel_probe_status_ = "waiting_for_reset_result";
}

void PS2PortExtension::pixel_probe_after_reset(IDirect3DDevice8& device,
                                                bool native_reset_called,
                                                bool reset_succeeded) noexcept {
    if (!pixel_probe_enabled()) return;
    if (native_reset_called && !reset_succeeded) {
        pixel_probe_status_ = "native_reset_failed_probe_unavailable_until_next_successful_reset";
        return;
    }
    initialize_pixel_probe(device);
}

uint32_t PS2PortExtension::note_indexed_draw(uint64_t frame) noexcept {
    if (indexed_draw_frame_ != frame) { indexed_draw_frame_ = frame; indexed_draw_count_ = 0; }
    const uint32_t ordinal = indexed_draw_count_;
    if (indexed_draw_count_ != UINT32_MAX) ++indexed_draw_count_;
    return ordinal;
}

uint32_t PS2PortExtension::indexed_draw_count(uint64_t frame) const noexcept {
    return indexed_draw_frame_ == frame ? indexed_draw_count_ : 0;
}

bool PS2PortExtension::begin_pixel_probe_target(uint64_t frame, uint32_t indexed_draw_ordinal,
                                                 const DrawSnapshot& snapshot,
                                                 const char* geometry_sha256,
                                                 uint32_t primitive_type, uint32_t min_index,
                                                 uint32_t vertex_count, uint32_t start_index,
                                                 uint32_t primitive_count,
                                                 uint32_t requested_mask, uint32_t applied_mask,
                                                 bool override_applied) noexcept {
    if (!pixel_probe_enabled() || !geometry_sha256 || std::strlen(geometry_sha256) != 64) return false;
    bool expected = false;
    if (!pixel_probe_claimed_.compare_exchange_strong(expected, true)) return false;
    pixel_probe_target_ = {};
    std::memcpy(pixel_probe_target_.geometry_sha256, geometry_sha256, 64);
    pixel_probe_target_.geometry_sha256[64] = '\0';
    pixel_probe_target_.device_id = snapshot.device_id;
    pixel_probe_target_.vertex_generation = snapshot.vertex_generation;
    pixel_probe_target_.index_generation = snapshot.index_generation;
    pixel_probe_target_.vertex_revision = snapshot.vertex_revision;
    pixel_probe_target_.index_revision = snapshot.index_revision;
    pixel_probe_target_.primitive_type = primitive_type;
    pixel_probe_target_.min_index = min_index;
    pixel_probe_target_.vertex_count = vertex_count;
    pixel_probe_target_.start_index = start_index;
    pixel_probe_target_.primitive_count = primitive_count;
    pixel_probe_target_.indexed_draw_ordinal = indexed_draw_ordinal;
    pixel_probe_target_.requested_mask = requested_mask;
    pixel_probe_target_.applied_mask = applied_mask;
    pixel_probe_target_.override_applied = override_applied;
    pixel_probe_target_.mode = mode_value();
    pixel_probe_frame_.store(frame, std::memory_order_release);
    pixel_probe_sample_count_ = 0;
    pixel_probe_copy_mask_ = 0;
    pixel_probe_samples_ = {};
    pixel_probe_finalized_ = false;
    pixel_probe_final_copy_hr_ = E_PENDING;
    pixel_probe_lock_hr_ = E_PENDING;
    pixel_probe_unlock_hr_ = E_PENDING;
    return true;
}

bool PS2PortExtension::pixel_probe_frame_active(uint64_t frame) const noexcept {
    return pixel_probe_enabled() && !pixel_probe_finalized_ &&
           pixel_probe_frame_.load(std::memory_order_acquire) == frame;
}

bool PS2PortExtension::pixel_probe_should_capture_later(uint64_t frame,
                                                          uint32_t indexed_draw_ordinal) const noexcept {
    return pixel_probe_frame_active(frame) && pixel_probe_later_ordinal_ >= 0 &&
           indexed_draw_ordinal > pixel_probe_target_.indexed_draw_ordinal &&
           indexed_draw_ordinal == static_cast<uint32_t>(pixel_probe_later_ordinal_);
}

void PS2PortExtension::capture_pixel_checkpoint(IDirect3DDevice8& device, const char* checkpoint,
                                                 uint64_t frame, uint32_t indexed_draw_ordinal,
                                                 uint32_t primitive_type, uint32_t min_index,
                                                 uint32_t vertex_count, uint32_t start_index,
                                                 uint32_t primitive_count, HRESULT draw_hresult,
                                                 bool draw_hresult_known, bool in_scene,
                                                 uint32_t indexed_draw_count_at_checkpoint) noexcept {
    if (!pixel_probe_frame_active(frame) || !pixel_probe_has_sample_capacity(pixel_probe_sample_count_)) return;
    const uint32_t slot = pixel_probe_sample_count_++;
    auto& sample = pixel_probe_samples_[slot];
    sample = {};
    sample.render_state_hresults.fill(E_PENDING);
    sample.get_texture_hresults.fill(E_PENDING);
    sample.get_texture_desc_hresults.fill(E_PENDING);
    for (auto& stage : sample.texture_stage_hresults) stage.fill(E_PENDING);
    sample.checkpoint = checkpoint ? checkpoint : "unknown";
    sample.frame = frame;
    sample.indexed_draw_ordinal = indexed_draw_ordinal;
    sample.indexed_draw_count_at_checkpoint = indexed_draw_count_at_checkpoint;
    sample.primitive_type = primitive_type;
    sample.min_index = min_index;
    sample.vertex_count = vertex_count;
    sample.start_index = start_index;
    sample.primitive_count = primitive_count;
    sample.draw_hresult = draw_hresult;
    sample.draw_hresult_known = draw_hresult_known;
    sample.pixel_x = static_cast<uint32_t>(pixel_probe_x_);
    sample.pixel_y = static_cast<uint32_t>(pixel_probe_y_);
    sample.depth_status = "not_attempted";
    sample.status = "metadata_capture_started";

    sample.get_caps_hresult = device.GetDeviceCaps(&sample.caps);
    SurfaceRelease color_surface;
    sample.get_render_target_hresult = device.GetRenderTarget(&color_surface.value);
    if (SUCCEEDED(sample.get_render_target_hresult) && color_surface.value) {
        sample.color_desc_hresult = color_surface.value->GetDesc(&sample.color_desc);
        sample.color_desc_valid = SUCCEEDED(sample.color_desc_hresult);
    }
    SurfaceRelease backbuffer;
    sample.get_backbuffer_hresult = device.GetBackBuffer(0, D3DBACKBUFFER_TYPE_MONO, &backbuffer.value);
    sample.active_target_is_backbuffer = SUCCEEDED(sample.get_render_target_hresult) &&
        SUCCEEDED(sample.get_backbuffer_hresult) &&
        same_com_identity(color_surface.value, backbuffer.value,
                          sample.get_render_target_identity_hresult,
                          sample.get_backbuffer_identity_hresult);
    SurfaceRelease depth_surface;
    sample.get_depth_surface_hresult = device.GetDepthStencilSurface(&depth_surface.value);
    if (SUCCEEDED(sample.get_depth_surface_hresult) && depth_surface.value) {
        sample.depth_desc_hresult = depth_surface.value->GetDesc(&sample.depth_desc);
        sample.depth_desc_valid = SUCCEEDED(sample.depth_desc_hresult);
        if (sample.depth_desc_valid) {
            if (sample.depth_desc.Format == D3DFMT_D24X8 || sample.depth_desc.Format == D3DFMT_D24S8 ||
                sample.depth_desc.Format == D3DFMT_D32)
                sample.depth_status = "not_readable_by_copyrects_depth_stencil_format_lock_not_attempted";
            else if (sample.depth_desc.Format == D3DFMT_D16_LOCKABLE &&
                     sample.depth_desc.MultiSampleType == D3DMULTISAMPLE_NONE)
                sample.depth_status = "lockable_format_but_cpu_readback_not_attempted";
            else sample.depth_status = "depth_cpu_readback_not_attempted";
        } else sample.depth_status = "depth_surface_desc_failed";
    } else sample.depth_status = "get_depth_surface_failed_or_unbound";
    sample.get_view_hresult = device.GetTransform(D3DTS_VIEW, &sample.view);
    sample.get_projection_hresult = device.GetTransform(D3DTS_PROJECTION, &sample.projection);
    sample.get_viewport_hresult = device.GetViewport(&sample.viewport);
    for (size_t i = 0; i < std::size(PIXEL_STATES); ++i)
        sample.render_state_hresults[i] = device.GetRenderState(PIXEL_STATES[i], &sample.render_state_values[i]);
    for (size_t stage = 0; stage < kPixelProbeTextureStages; ++stage) {
        for (size_t state = 0; state < std::size(PIXEL_TEXTURE_STAGE_STATES); ++state)
            sample.texture_stage_hresults[stage][state] = device.GetTextureStageState(
                static_cast<DWORD>(stage), PIXEL_TEXTURE_STAGE_STATES[state],
                &sample.texture_stage_values[stage][state]);
        TextureRelease texture;
        sample.get_texture_hresults[stage] = device.GetTexture(static_cast<DWORD>(stage), &texture.value);
        if (SUCCEEDED(sample.get_texture_hresults[stage]) && texture.value) {
            sample.texture_identities[stage] = static_cast<uint64_t>(reinterpret_cast<uintptr_t>(texture.value));
            const auto type = texture.value->GetType();
            sample.texture_types[stage] = static_cast<uint32_t>(type);
            if (type == D3DRTYPE_TEXTURE) {
                auto* texture2d = static_cast<IDirect3DTexture8*>(texture.value);
                sample.get_texture_desc_hresults[stage] = texture2d->GetLevelDesc(0, &sample.texture_descs[stage]);
                sample.texture_desc_valid[stage] = SUCCEEDED(sample.get_texture_desc_hresults[stage]);
            }
        }
    }

    if (FAILED(sample.get_caps_hresult)) { sample.status = "get_device_caps_failed"; return; }
    if (FAILED(sample.get_render_target_hresult) || !color_surface.value) {
        sample.status = "get_render_target_failed"; return;
    }
    if (FAILED(sample.color_desc_hresult)) { sample.status = "color_surface_desc_failed"; return; }
    if (FAILED(sample.get_backbuffer_hresult) || !backbuffer.value || !sample.active_target_is_backbuffer) {
        sample.status = "active_render_target_is_not_default_backbuffer"; return;
    }
    if (sample.caps.Caps2 & D3DCAPS2_NO2DDURING3DSCENE) {
        sample.status = in_scene ? "unsupported_no_2d_operations_during_scene" : "capability_reports_no_2d_operations_during_scene";
        return;
    }
    if (!pixel_probe_ready_ || !pixel_probe_gpu_surface_ || !pixel_probe_cpu_surface_) {
        sample.status = pixel_probe_status_;
        return;
    }
    if (sample.color_desc.Format != pixel_probe_format_) { sample.status = "active_color_format_changed"; return; }
    if (pixel_probe_x_ < 0 || pixel_probe_y_ < 0 ||
        static_cast<uint32_t>(pixel_probe_x_) >= sample.color_desc.Width ||
        static_cast<uint32_t>(pixel_probe_y_) >= sample.color_desc.Height) {
        sample.status = "pixel_outside_active_render_target"; return;
    }
    RECT source{pixel_probe_x_, pixel_probe_y_, pixel_probe_x_ + 1, pixel_probe_y_ + 1};
    POINT destination{static_cast<LONG>(slot), 0};
    sample.copy_attempted = true;
    sample.copy_rects_hresult = device.CopyRects(color_surface.value, &source, 1,
                                                 pixel_probe_gpu_surface_, &destination);
    sample.copy_succeeded = SUCCEEDED(sample.copy_rects_hresult);
    if (sample.copy_succeeded) {
        pixel_probe_copy_mask_ |= (1u << slot);
        sample.status = "pixel_copied_to_gpu_scratch";
    } else sample.status = "copy_rects_failed";
}

void PS2PortExtension::pixel_probe_target_result(HRESULT result) noexcept {
    pixel_probe_target_.draw_hresult = result;
    pixel_probe_target_.draw_hresult_known = true;
}

void PS2PortExtension::finish_pixel_probe_frame(IDirect3DDevice8& device, uint64_t frame,
                                                 bool scene_active) noexcept {
    if (!pixel_probe_frame_active(frame)) return;
    if (scene_active) {
        pixel_probe_status_ = "frame_end_skipped_scene_still_active";
        pixel_probe_finalized_ = true;
        return;
    }
    if (!pixel_probe_ready_ || !pixel_probe_gpu_surface_ || !pixel_probe_cpu_surface_ ||
        pixel_probe_copy_mask_ == 0) {
        pixel_probe_status_ = pixel_probe_ready_ ? "no_checkpoint_copy_succeeded" : pixel_probe_status_;
        pixel_probe_finalized_ = true;
        return;
    }
    RECT full{0, 0, 4, 1};
    POINT origin{0, 0};
    pixel_probe_final_copy_hr_ = device.CopyRects(pixel_probe_gpu_surface_, &full, 1,
                                                  pixel_probe_cpu_surface_, &origin);
    if (FAILED(pixel_probe_final_copy_hr_)) {
        pixel_probe_status_ = "final_gpu_to_cpu_copy_failed";
        pixel_probe_finalized_ = true;
        return;
    }
    D3DLOCKED_RECT locked{};
    pixel_probe_lock_hr_ = pixel_probe_cpu_surface_->LockRect(&locked, &full, D3DLOCK_READONLY);
    if (FAILED(pixel_probe_lock_hr_)) {
        pixel_probe_status_ = "readback_lock_failed_or_invalid_pitch";
        pixel_probe_finalized_ = true;
        return;
    }
    if (!locked.pBits || locked.Pitch < 16) {
        pixel_probe_unlock_hr_ = pixel_probe_cpu_surface_->UnlockRect();
        pixel_probe_status_ = "readback_lock_failed_or_invalid_pitch";
        pixel_probe_finalized_ = true;
        return;
    }
    for (uint32_t i = 0; i < pixel_probe_sample_count_; ++i) {
        auto& sample = pixel_probe_samples_[i];
        if ((pixel_probe_copy_mask_ & (1u << i)) == 0) continue;
        const auto* bytes = static_cast<const uint8_t*>(locked.pBits) + i * 4u;
        std::memcpy(&sample.pixel_raw, bytes, sizeof(sample.pixel_raw));
        sample.color_valid = decode_pixel_color(pixel_probe_format_, sample.pixel_raw, sample.color);
        if (sample.color_valid) sample.status = "color_readback_succeeded";
        else sample.status = "unsupported_readback_pixel_format";
    }
    pixel_probe_unlock_hr_ = pixel_probe_cpu_surface_->UnlockRect();
    pixel_probe_status_ = SUCCEEDED(pixel_probe_unlock_hr_) ? "readback_succeeded" : "readback_unlock_failed";
    pixel_probe_finalized_ = true;
}

std::string PS2PortExtension::pixel_probe_config_json() const noexcept {
    try {
        std::ostringstream out;
        out << "{\"requested\":" << (pixel_probe_requested_ ? "true" : "false")
            << ",\"enabled\":" << (pixel_probe_enabled() ? "true" : "false")
            << ",\"mode\":" << mode_value() << ",\"mode_name\":" << json_escape(mode_name())
            << ",\"pixel\":[" << pixel_probe_x_ << ',' << pixel_probe_y_ << ']'
            << ",\"later_indexed_draw_ordinal\":";
        if (pixel_probe_later_ordinal_ < 0) out << "null"; else out << pixel_probe_later_ordinal_;
        out << ",\"status\":" << json_escape(pixel_probe_status_)
            << ",\"caps_hresult\":" << hresult_json(pixel_probe_initial_caps_hr_)
            << ",\"caps2\":";
        if (SUCCEEDED(pixel_probe_initial_caps_hr_)) out << pixel_probe_initial_caps_.Caps2; else out << "null";
        out << ",\"no_2d_during_scene\":";
        if (FAILED(pixel_probe_initial_caps_hr_)) out << "null";
        else out << ((pixel_probe_initial_caps_.Caps2 & D3DCAPS2_NO2DDURING3DSCENE) ? "true" : "false");
        out << ",\"color_desc_hresult\":" << hresult_json(pixel_probe_initial_color_hr_)
            << ",\"color_surface\":";
        append_surface_json(out, pixel_probe_initial_color_desc_, SUCCEEDED(pixel_probe_initial_color_hr_));
        out << ",\"depth_desc_hresult\":" << hresult_json(pixel_probe_initial_depth_hr_)
            << ",\"depth_surface\":";
        append_surface_json(out, pixel_probe_initial_depth_desc_, SUCCEEDED(pixel_probe_initial_depth_hr_));
        out << ",\"create_gpu_scratch_hresult\":" << hresult_json(pixel_probe_gpu_create_hr_)
            << ",\"create_cpu_surface_hresult\":" << hresult_json(pixel_probe_cpu_create_hr_) << '}';
        return out.str();
    } catch (...) { return "{}"; }
}

std::string PS2PortExtension::pixel_probe_json() const noexcept {
    try {
        std::ostringstream out;
        out << "{\"type\":\"ps2_pixel_probe\",\"status\":" << json_escape(pixel_probe_status_)
            << ",\"frame\":" << pixel_probe_frame_.load(std::memory_order_acquire)
            << ",\"device_id\":" << pixel_probe_target_.device_id
            << ",\"mode\":" << pixel_probe_target_.mode
            << ",\"mode_name\":" << json_escape(mode_name())
            << ",\"requested_mask\":" << pixel_probe_target_.requested_mask
            << ",\"applied_mask\":" << pixel_probe_target_.applied_mask
            << ",\"override_applied\":" << (pixel_probe_target_.override_applied ? "true" : "false")
            << ",\"target\":{\"identity\":\"exact_france1_bush01_source_geometry_current_generations\",\"geometry_sha256\":"
            << json_escape(pixel_probe_target_.geometry_sha256)
            << ",\"vertex_generation\":" << pixel_probe_target_.vertex_generation
            << ",\"index_generation\":" << pixel_probe_target_.index_generation
            << ",\"vertex_revision\":" << pixel_probe_target_.vertex_revision
            << ",\"index_revision\":" << pixel_probe_target_.index_revision
            << ",\"indexed_draw_ordinal_zero_based\":" << pixel_probe_target_.indexed_draw_ordinal
            << ",\"draw_args\":[" << pixel_probe_target_.primitive_type << ','
            << pixel_probe_target_.min_index << ',' << pixel_probe_target_.vertex_count << ','
            << pixel_probe_target_.start_index << ',' << pixel_probe_target_.primitive_count << ']'
            << ",\"draw_hresult\":" << hresult_json(pixel_probe_target_.draw_hresult)
            << ",\"draw_hresult_known\":" << (pixel_probe_target_.draw_hresult_known ? "true" : "false") << '}'
            << ",\"coordinates\":\"D3D8_backbuffer_pixel_top_left_origin\",\"checkpoints\":[";
        for (uint32_t i = 0; i < pixel_probe_sample_count_; ++i) {
            if (i) out << ',';
            const auto& sample = pixel_probe_samples_[i];
            out << "{\"checkpoint\":" << json_escape(sample.checkpoint)
                << ",\"frame\":" << sample.frame
                << ",\"indexed_draw_ordinal_zero_based\":";
            if (std::strcmp(sample.checkpoint, "before_present") == 0) out << "null";
            else out << sample.indexed_draw_ordinal;
            out << ",\"indexed_draw_count_at_checkpoint\":" << sample.indexed_draw_count_at_checkpoint
                << ",\"sequence_semantics\":" << json_escape(std::strcmp(sample.checkpoint, "before_present") == 0 ? "draw_count_boundary" : "zero_based_draw_ordinal")
                << ",\"draw_args\":[" << sample.primitive_type << ',' << sample.min_index << ','
                << sample.vertex_count << ',' << sample.start_index << ',' << sample.primitive_count << ']'
                << ",\"draw_hresult\":" << hresult_json(sample.draw_hresult)
                << ",\"draw_hresult_known\":" << (sample.draw_hresult_known ? "true" : "false")
                << ",\"status\":" << json_escape(sample.status)
                << ",\"get_caps_hresult\":" << hresult_json(sample.get_caps_hresult)
                << ",\"caps2\":";
            if (SUCCEEDED(sample.get_caps_hresult)) out << sample.caps.Caps2; else out << "null";
            out << ",\"get_render_target_hresult\":" << hresult_json(sample.get_render_target_hresult)
                << ",\"get_backbuffer_hresult\":" << hresult_json(sample.get_backbuffer_hresult)
                << ",\"get_render_target_identity_hresult\":" << hresult_json(sample.get_render_target_identity_hresult)
                << ",\"get_backbuffer_identity_hresult\":" << hresult_json(sample.get_backbuffer_identity_hresult)
                << ",\"active_target_is_backbuffer\":" << (sample.active_target_is_backbuffer ? "true" : "false")
                << ",\"color_desc_hresult\":" << hresult_json(sample.color_desc_hresult)
                << ",\"color_surface\":";
            append_surface_json(out, sample.color_desc, sample.color_desc_valid);
            out << ",\"copy_rects_hresult\":" << hresult_json(sample.copy_rects_hresult)
                << ",\"copy_attempted\":" << (sample.copy_attempted ? "true" : "false")
                << ",\"get_depth_surface_hresult\":" << hresult_json(sample.get_depth_surface_hresult)
                << ",\"depth_desc_hresult\":" << hresult_json(sample.depth_desc_hresult)
                << ",\"depth_surface\":";
            append_surface_json(out, sample.depth_desc, sample.depth_desc_valid);
            out << ",\"depth_cpu_status\":" << json_escape(sample.depth_status)
                << ",\"view_hresult\":" << hresult_json(sample.get_view_hresult)
                << ",\"view_matrix\":";
            if (SUCCEEDED(sample.get_view_hresult)) append_matrix_json(out, sample.view); else out << "null";
            out << ",\"projection_hresult\":" << hresult_json(sample.get_projection_hresult)
                << ",\"projection_matrix\":";
            if (SUCCEEDED(sample.get_projection_hresult)) append_matrix_json(out, sample.projection); else out << "null";
            out << ",\"viewport_hresult\":" << hresult_json(sample.get_viewport_hresult)
                << ",\"viewport\":";
            if (SUCCEEDED(sample.get_viewport_hresult))
                out << "{\"x\":" << sample.viewport.X << ",\"y\":" << sample.viewport.Y
                    << ",\"width\":" << sample.viewport.Width << ",\"height\":" << sample.viewport.Height
                    << ",\"min_z\":" << sample.viewport.MinZ << ",\"max_z\":" << sample.viewport.MaxZ << '}';
            else out << "null";
            out << ",\"render_states\":[";
            for (size_t state = 0; state < std::size(PIXEL_STATES); ++state) {
                if (state) out << ',';
                out << "{\"name\":" << json_escape(PIXEL_STATE_NAMES[state])
                    << ",\"id\":" << static_cast<uint32_t>(PIXEL_STATES[state])
                    << ",\"get_hresult\":" << hresult_json(sample.render_state_hresults[state])
                    << ",\"value\":";
                if (SUCCEEDED(sample.render_state_hresults[state])) out << sample.render_state_values[state]; else out << "null";
                out << '}';
            }
            out << "],\"texture_stages\":[";
            for (size_t stage = 0; stage < kPixelProbeTextureStages; ++stage) {
                if (stage) out << ',';
                out << "{\"stage\":" << stage
                    << ",\"get_texture_hresult\":" << hresult_json(sample.get_texture_hresults[stage])
                    << ",\"texture_identity\":";
                if (SUCCEEDED(sample.get_texture_hresults[stage]) && sample.texture_identities[stage])
                    out << sample.texture_identities[stage];
                else out << "null";
                out << ",\"texture_type\":";
                if (SUCCEEDED(sample.get_texture_hresults[stage]) && sample.texture_identities[stage])
                    out << sample.texture_types[stage];
                else out << "null";
                out << ",\"level0_desc_hresult\":" << hresult_json(sample.get_texture_desc_hresults[stage])
                    << ",\"level0_surface\":";
                append_surface_json(out, sample.texture_descs[stage], sample.texture_desc_valid[stage]);
                out << ",\"states\":[";
                for (size_t state = 0; state < std::size(PIXEL_TEXTURE_STAGE_STATES); ++state) {
                    if (state) out << ',';
                    out << "{\"name\":" << json_escape(PIXEL_TEXTURE_STAGE_STATE_NAMES[state])
                        << ",\"id\":" << static_cast<uint32_t>(PIXEL_TEXTURE_STAGE_STATES[state])
                        << ",\"get_hresult\":" << hresult_json(sample.texture_stage_hresults[stage][state])
                        << ",\"value\":";
                    if (SUCCEEDED(sample.texture_stage_hresults[stage][state]))
                        out << sample.texture_stage_values[stage][state];
                    else out << "null";
                    out << '}';
                }
                out << "]}";
            }
            out << "],\"pixel\":{\"x\":" << sample.pixel_x << ",\"y\":" << sample.pixel_y
                << ",\"final_copy_hresult\":" << hresult_json(pixel_probe_final_copy_hr_)
                << ",\"lock_hresult\":" << hresult_json(pixel_probe_lock_hr_)
                << ",\"unlock_hresult\":" << hresult_json(pixel_probe_unlock_hr_)
                << ",\"raw\":";
            if (sample.color_valid) out << sample.pixel_raw; else out << "null";
            out << ",\"r\":"; if (sample.color_valid) out << static_cast<unsigned>(sample.color.r); else out << "null";
            out << ",\"g\":"; if (sample.color_valid) out << static_cast<unsigned>(sample.color.g); else out << "null";
            out << ",\"b\":"; if (sample.color_valid) out << static_cast<unsigned>(sample.color.b); else out << "null";
            out << ",\"a\":"; if (sample.color.alpha_valid) out << static_cast<unsigned>(sample.color.a); else out << "null";
            out << ",\"alpha_valid\":" << (sample.color.alpha_valid ? "true" : "false") << "}}";
        }
        out << "]}";
        return out.str();
    } catch (...) { return "{}"; }
}

void PS2PortExtension::disable(const char* reason) noexcept {
    disabled_ = true;
    if (reflection_) reflection_->disable(reason);
    if (course_objects_) course_objects_->disable(reason);
    if (grass_) grass_->disable(reason);
    if (shrubs_) shrubs_->disable(reason);
}

} // namespace gfx2::ps2port
