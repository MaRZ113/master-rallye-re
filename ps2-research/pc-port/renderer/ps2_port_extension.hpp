#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <vector>
#include "sdk.hpp"

namespace gfx2::ps2port {
class ReflectionPilot;
class CourseObjectsPilot;
class GrassPilot;
class VehiclePartitionPilot;

enum class PilotMode : uint8_t {
    Stock = 0,
    France1Bush01Treeblend = 1,
    France1Bush01AlphaBlendOnly = 2,
    France1Bush01DepthWriteOnly = 3,
};

constexpr uint32_t kStateAlphaTest = 1u << 0;
constexpr uint32_t kStateAlphaBlend = 1u << 1;
constexpr uint32_t kStateSourceBlend = 1u << 2;
constexpr uint32_t kStateDestinationBlend = 1u << 3;
constexpr uint32_t kStateZWrite = 1u << 4;
constexpr uint32_t kStateMaskAll = kStateAlphaTest | kStateAlphaBlend |
                                   kStateSourceBlend | kStateDestinationBlend | kStateZWrite;

constexpr bool valid_state_override_mask(uint32_t mask) noexcept {
    return mask != 0 && (mask & ~kStateMaskAll) == 0;
}

struct DrawSnapshot {
    bool supported_build = false;
    bool france1_course_verified = false;
    uint64_t race_generation = 0;
    uint64_t owner_lifetime = 0;
    uint64_t device_id = 0;
    uint64_t reset_generation = 0;
    uint32_t primitive_type = 0;
    uint32_t min_index = 0;
    uint32_t vertex_count = 0;
    uint32_t start_index = 0;
    uint32_t primitive_count = 0;
    uint32_t fvf = 0;
    uint32_t stride = 0;
    uint32_t base_vertex = 0;
    uint32_t index_format = 0;
    uint64_t vertex_byte_offset = 0;
    uintptr_t vertex_resource = 0;
    uintptr_t index_resource = 0;
    uint64_t vertex_generation = 0;
    uint64_t index_generation = 0;
    uint64_t vertex_revision = 0;
    uint64_t index_revision = 0;
    bool complete_mirror_coverage = false;
    std::vector<uint8_t> vertex_bytes;
    std::vector<uint8_t> index_bytes;
};

struct StateRequest {
    bool requested = false;
    uint32_t override_mask = 0;
    const char* reason = "stock";
    DWORD alpha_test_enable = FALSE;
    DWORD alpha_blend_enable = TRUE;
    DWORD source_blend = D3DBLEND_SRCALPHA;
    DWORD destination_blend = D3DBLEND_INVSRCALPHA;
    DWORD z_write_enable = FALSE;
};

constexpr StateRequest state_request_for_mode(PilotMode mode) noexcept {
    StateRequest request{};
    switch (mode) {
    case PilotMode::France1Bush01Treeblend:
        request.requested = true;
        request.override_mask = kStateMaskAll;
        request.reason = "treeblend_all_states";
        break;
    case PilotMode::France1Bush01AlphaBlendOnly:
        request.requested = true;
        request.override_mask = kStateAlphaTest | kStateAlphaBlend |
                               kStateSourceBlend | kStateDestinationBlend;
        request.reason = "treeblend_alpha_blend_only";
        break;
    case PilotMode::France1Bush01DepthWriteOnly:
        request.requested = true;
        request.override_mask = kStateZWrite;
        request.reason = "treeblend_depth_write_only";
        break;
    case PilotMode::Stock:
    default:
        break;
    }
    return request;
}

struct StateTransaction {
    std::array<DWORD, 5> original{};
    std::array<DWORD, 5> desired{};
    uint32_t changed_mask = 0;
};

template<class Writer>
bool restore_state_transaction(StateTransaction& transaction, Writer&& write) noexcept {
    if ((transaction.changed_mask & ~kStateMaskAll) != 0) return false;
    bool okay = true;
    for (std::size_t n = transaction.original.size(); n > 0; --n) {
        const std::size_t index = n - 1;
        const uint32_t bit = 1u << index;
        if ((transaction.changed_mask & bit) == 0) continue;
        if (write(index, transaction.original[index])) transaction.changed_mask &= ~bit;
        else okay = false;
    }
    return okay;
}

template<class Reader, class Writer>
bool apply_state_transaction(const StateRequest& request, StateTransaction& transaction,
                             Reader&& read, Writer&& write, uint32_t& applied_mask) noexcept {
    transaction = {};
    applied_mask = 0;
    if (!request.requested || !valid_state_override_mask(request.override_mask)) return false;

    transaction.desired = {request.alpha_test_enable, request.alpha_blend_enable,
                           request.source_blend, request.destination_blend,
                           request.z_write_enable};
    for (std::size_t index = 0; index < transaction.original.size(); ++index) {
        const uint32_t bit = 1u << index;
        if ((request.override_mask & bit) == 0) continue;
        if (!read(index, transaction.original[index])) {
            transaction = {};
            return false;
        }
    }

    for (std::size_t index = 0; index < transaction.original.size(); ++index) {
        const uint32_t bit = 1u << index;
        if ((request.override_mask & bit) == 0 ||
            transaction.original[index] == transaction.desired[index]) continue;
        // Track the attempted state before SetRenderState: a failed call may
        // still have changed native state, so rollback must include this slot.
        transaction.changed_mask |= bit;
        if (!write(index, transaction.desired[index])) {
            restore_state_transaction(transaction, write);
            return false;
        }
    }
    applied_mask = request.override_mask;
    return true;
}

struct Classification {
    StateRequest state;
    std::string geometry_sha256;
    const char* identity = "TARGET_IDENTITY_NOT_FOUND";
};

constexpr bool pixel_probe_mode_supported(uint32_t mode) noexcept {
    return mode == static_cast<uint32_t>(PilotMode::Stock) ||
           mode == static_cast<uint32_t>(PilotMode::France1Bush01DepthWriteOnly);
}

constexpr bool pixel_probe_format_supported(D3DFORMAT format) noexcept {
    return format == D3DFMT_X8R8G8B8 || format == D3DFMT_A8R8G8B8;
}
constexpr std::size_t kPixelProbeMaxSamples = 4;
constexpr std::size_t kPixelProbeTextureStages = 2;
constexpr std::size_t kPixelProbeTextureStageStateCount = 8;
constexpr bool pixel_probe_has_sample_capacity(std::size_t sample_count) noexcept {
    return sample_count < kPixelProbeMaxSamples;
}

struct PixelColor {
    uint8_t r = 0, g = 0, b = 0, a = 0;
    bool alpha_valid = false;
};

inline bool decode_pixel_color(D3DFORMAT format, DWORD raw, PixelColor& color) noexcept {
    if (!pixel_probe_format_supported(format)) return false;
    color.r = static_cast<uint8_t>((raw >> 16) & 0xff);
    color.g = static_cast<uint8_t>((raw >> 8) & 0xff);
    color.b = static_cast<uint8_t>(raw & 0xff);
    color.alpha_valid = format == D3DFMT_A8R8G8B8;
    color.a = color.alpha_valid ? static_cast<uint8_t>((raw >> 24) & 0xff) : 0;
    return true;
}

struct PixelProbeTarget {
    char geometry_sha256[65]{};
    uint64_t device_id = 0;
    uint64_t vertex_generation = 0;
    uint64_t index_generation = 0;
    uint64_t vertex_revision = 0;
    uint64_t index_revision = 0;
    uint32_t primitive_type = 0;
    uint32_t min_index = 0;
    uint32_t vertex_count = 0;
    uint32_t start_index = 0;
    uint32_t primitive_count = 0;
    uint32_t indexed_draw_ordinal = 0;
    HRESULT draw_hresult = E_PENDING;
    bool draw_hresult_known = false;
    uint32_t requested_mask = 0;
    uint32_t applied_mask = 0;
    bool override_applied = false;
    uint32_t mode = 0;
};

struct PixelProbeSample {
    const char* checkpoint = "unknown";
    uint64_t frame = 0;
    uint32_t indexed_draw_ordinal = 0;
    uint32_t indexed_draw_count_at_checkpoint = 0;
    uint32_t primitive_type = 0;
    uint32_t min_index = 0;
    uint32_t vertex_count = 0;
    uint32_t start_index = 0;
    uint32_t primitive_count = 0;
    HRESULT draw_hresult = E_PENDING;
    bool draw_hresult_known = false;
    HRESULT get_caps_hresult = E_FAIL;
    HRESULT get_render_target_hresult = E_FAIL;
    HRESULT get_backbuffer_hresult = E_FAIL;
    HRESULT get_render_target_identity_hresult = E_FAIL;
    HRESULT get_backbuffer_identity_hresult = E_FAIL;
    HRESULT color_desc_hresult = E_FAIL;
    HRESULT copy_rects_hresult = E_FAIL;
    HRESULT get_depth_surface_hresult = E_FAIL;
    HRESULT depth_desc_hresult = E_FAIL;
    HRESULT get_view_hresult = E_FAIL;
    HRESULT get_projection_hresult = E_FAIL;
    HRESULT get_viewport_hresult = E_FAIL;
    std::array<DWORD, 10> render_state_values{};
    std::array<HRESULT, 10> render_state_hresults{};
    std::array<std::array<DWORD, kPixelProbeTextureStageStateCount>, kPixelProbeTextureStages> texture_stage_values{};
    std::array<std::array<HRESULT, kPixelProbeTextureStageStateCount>, kPixelProbeTextureStages> texture_stage_hresults{};
    std::array<HRESULT, kPixelProbeTextureStages> get_texture_hresults{};
    std::array<HRESULT, kPixelProbeTextureStages> get_texture_desc_hresults{};
    std::array<uint64_t, kPixelProbeTextureStages> texture_identities{};
    std::array<uint32_t, kPixelProbeTextureStages> texture_types{};
    std::array<D3DSURFACE_DESC, kPixelProbeTextureStages> texture_descs{};
    std::array<bool, kPixelProbeTextureStages> texture_desc_valid{};
    D3DCAPS8 caps{};
    D3DSURFACE_DESC color_desc{};
    D3DSURFACE_DESC depth_desc{};
    D3DVIEWPORT8 viewport{};
    D3DMATRIX view{};
    D3DMATRIX projection{};
    uint32_t pixel_x = 0;
    uint32_t pixel_y = 0;
    uint32_t pixel_raw = 0;
    PixelColor color{};
    bool color_desc_valid = false;
    bool depth_desc_valid = false;
    bool active_target_is_backbuffer = false;
    bool copy_attempted = false;
    bool copy_succeeded = false;
    bool color_valid = false;
    const char* depth_status = "not_queried";
    const char* status = "not_started";
};

bool is_france1_bush01_geometry(std::string_view sha256) noexcept;

class PS2PortExtension {
public:
    PS2PortExtension(bool exact_build, const std::string& exe_sha,
                     const std::wstring& renderer_ini) noexcept;
    ~PS2PortExtension();

    bool buffer_mirroring_required() const noexcept;
    bool frontend_geometry_diagnostics() const noexcept { return frontend_geometry_diagnostics_ && build_valid_ && !disabled_; }
    bool claim_frontend_probe_attempt() noexcept { return frontend_attempts_<128 && ++frontend_attempts_<=128; }
    bool claim_frontend_geometry(size_t source_index) noexcept {
        if(source_index>=frontend_logged_.size() || frontend_logged_[source_index])return false;
        frontend_logged_[source_index]=true;return true;
    }
    bool analysis_enabled() const noexcept;
    bool foliage_analysis_enabled() const noexcept {
        return !disabled_&&build_valid_&&(mode_!=PilotMode::Stock||pixel_probe_enabled());
    }
    bool requested() const noexcept;
    bool active() const noexcept;
    ReflectionPilot* reflection() noexcept { return reflection_.get(); }
    VehiclePartitionPilot* vehicle_partitions() noexcept { return vehicle_partitions_.get(); }
    bool native_states_pending() const noexcept;
    CourseObjectsPilot* course_objects() noexcept { return course_objects_.get(); }
    GrassPilot* grass() noexcept { return grass_.get(); }
    GrassPilot* shrubs() noexcept { return shrubs_.get(); }
    std::array<GrassPilot*,2> ground_details() noexcept {return {grass_.get(),shrubs_.get()};}
    Classification classify(const DrawSnapshot& snapshot) const noexcept;
    void device_reset(bool successful) noexcept;
    void disable(const char* reason) noexcept;
    uint64_t reset_generation() const noexcept { return reset_generation_; }
    const char* config_reason() const noexcept { return config_reason_; }
    bool diagnostics() const noexcept { return diagnostics_; }
    uint32_t mode_value() const noexcept { return static_cast<uint32_t>(mode_); }
    const char* mode_name() const noexcept;
    bool claim_draw_diagnostic() noexcept;
    bool pixel_probe_requested() const noexcept { return pixel_probe_requested_; }
    bool pixel_probe_enabled() const noexcept { return pixel_probe_enabled_ && build_valid_ && !disabled_; }
    bool pixel_probe_ready() const noexcept { return pixel_probe_ready_; }
    int pixel_probe_x() const noexcept { return pixel_probe_x_; }
    int pixel_probe_y() const noexcept { return pixel_probe_y_; }
    int pixel_probe_later_ordinal() const noexcept { return pixel_probe_later_ordinal_; }
    const char* pixel_probe_status() const noexcept { return pixel_probe_status_; }
    bool initialize_pixel_probe(IDirect3DDevice8& device) noexcept;
    void pixel_probe_before_reset() noexcept;
    void pixel_probe_after_reset(IDirect3DDevice8& device, bool native_reset_called,
                                 bool reset_succeeded) noexcept;
    uint32_t note_indexed_draw(uint64_t frame) noexcept;
    uint32_t indexed_draw_count(uint64_t frame) const noexcept;
    bool begin_pixel_probe_target(uint64_t frame, uint32_t indexed_draw_ordinal,
                                  const DrawSnapshot& snapshot, const char* geometry_sha256,
                                  uint32_t primitive_type, uint32_t min_index, uint32_t vertex_count,
                                  uint32_t start_index, uint32_t primitive_count,
                                  uint32_t requested_mask, uint32_t applied_mask,
                                  bool override_applied) noexcept;
    bool pixel_probe_frame_active(uint64_t frame) const noexcept;
    bool pixel_probe_should_capture_later(uint64_t frame, uint32_t indexed_draw_ordinal) const noexcept;
    const PixelProbeTarget& pixel_probe_target() const noexcept { return pixel_probe_target_; }
    void capture_pixel_checkpoint(IDirect3DDevice8& device, const char* checkpoint,
                                  uint64_t frame, uint32_t indexed_draw_ordinal,
                                  uint32_t primitive_type, uint32_t min_index,
                                  uint32_t vertex_count, uint32_t start_index,
                                  uint32_t primitive_count, HRESULT draw_hresult,
                                  bool draw_hresult_known, bool in_scene,
                                  uint32_t indexed_draw_count_at_checkpoint) noexcept;
    void pixel_probe_target_result(HRESULT result) noexcept;
    void finish_pixel_probe_frame(IDirect3DDevice8& device, uint64_t frame,
                                  bool scene_active) noexcept;
    std::string pixel_probe_json() const noexcept;
    std::string pixel_probe_config_json() const noexcept;

private:
    std::unique_ptr<ReflectionPilot> reflection_;
    std::unique_ptr<VehiclePartitionPilot> vehicle_partitions_;
    std::unique_ptr<CourseObjectsPilot> course_objects_;
    std::unique_ptr<GrassPilot> grass_;
    std::unique_ptr<GrassPilot> shrubs_;
    void pixel_probe_release() noexcept;
    PilotMode mode_ = PilotMode::Stock;
    bool build_valid_ = false;
    bool disabled_ = false;
    bool diagnostics_ = false;
    bool frontend_geometry_diagnostics_ = false;
    std::array<bool,17> frontend_logged_{};
    uint32_t frontend_attempts_=0;
    bool pixel_probe_enabled_ = false;
    bool pixel_probe_requested_ = false;
    int pixel_probe_x_ = -1;
    int pixel_probe_y_ = -1;
    int pixel_probe_later_ordinal_ = -1;
    std::atomic<bool> draw_diagnostic_claimed_{false};
    std::atomic<bool> pixel_probe_claimed_{false};
    std::atomic<uint64_t> pixel_probe_frame_{0};
    uint64_t indexed_draw_frame_ = 0;
    uint32_t indexed_draw_count_ = 0;
    PixelProbeTarget pixel_probe_target_{};
    std::array<PixelProbeSample, kPixelProbeMaxSamples> pixel_probe_samples_{};
    uint32_t pixel_probe_sample_count_ = 0;
    uint32_t pixel_probe_copy_mask_ = 0;
    IDirect3DSurface8* pixel_probe_gpu_surface_ = nullptr;
    IDirect3DSurface8* pixel_probe_cpu_surface_ = nullptr;
    D3DFORMAT pixel_probe_format_ = D3DFMT_UNKNOWN;
    D3DCAPS8 pixel_probe_initial_caps_{};
    D3DSURFACE_DESC pixel_probe_initial_color_desc_{};
    D3DSURFACE_DESC pixel_probe_initial_depth_desc_{};
    HRESULT pixel_probe_initial_caps_hr_ = E_FAIL;
    HRESULT pixel_probe_initial_color_hr_ = E_FAIL;
    HRESULT pixel_probe_initial_depth_hr_ = E_FAIL;
    HRESULT pixel_probe_gpu_create_hr_ = E_FAIL;
    HRESULT pixel_probe_cpu_create_hr_ = E_FAIL;
    HRESULT pixel_probe_final_copy_hr_ = E_PENDING;
    HRESULT pixel_probe_lock_hr_ = E_PENDING;
    HRESULT pixel_probe_unlock_hr_ = E_PENDING;
    bool pixel_probe_ready_ = false;
    bool pixel_probe_finalized_ = false;
    const char* pixel_probe_status_ = "disabled";
    uint64_t reset_generation_ = 0;
    const char* config_reason_ = "stock_default";
};

} // namespace gfx2::ps2port
