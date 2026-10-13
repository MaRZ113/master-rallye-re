#pragma once
#include "sdk.hpp"
#include "reflection_capture.hpp"
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {
struct DrawSnapshot;

enum class ReflectionMode : uint8_t {
    Stock = 0,
    TataBonnetPS2StaticContribution = 1, // Historical identifier; record 19 includes hood and roof.
    TataBodyPS2TextureOnly = 2,
    TataBodyNativeTextureAddOnly = 3,
    TataBodyPS2MixedContribution = 4
};
constexpr ReflectionMode reflection_mode(uint32_t value, uint32_t version, bool supported) noexcept {
    return supported && version == 1 && value <= 4 ?
        static_cast<ReflectionMode>(value) : ReflectionMode::Stock;
}
constexpr ReflectionMode reflection_mode(std::wstring_view value, std::wstring_view version, bool supported) noexcept {
    return supported && version == L"1" && value.size() == 1 && value[0] >= L'0' && value[0] <= L'4' ?
        static_cast<ReflectionMode>(value[0] - L'0') : ReflectionMode::Stock;
}
constexpr uint32_t reflection_override_mask(ReflectionMode mode) noexcept {
    switch (mode) {
    case ReflectionMode::TataBonnetPS2StaticContribution:
    case ReflectionMode::TataBodyPS2MixedContribution: return 3u;
    case ReflectionMode::TataBodyPS2TextureOnly: return 2u;
    case ReflectionMode::TataBodyNativeTextureAddOnly: return 1u;
    default: return 0u;
    }
}
inline constexpr char kTataBonnetGeometrySha[] =
    "f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669";
inline constexpr char kKiaBonnetGeometrySha[] =
    "03f88e7a81ae783819b1ad64ac54284b0b330a4c488c851411aee0378706d729";
struct ReflectionMaterial {
    const char* vehicle;
    const char* geometry_sha;
    uint32_t triangles, vertices;
};
inline constexpr std::array<ReflectionMaterial,2> kReflectionMaterials = {{
    {"Tata",kTataBonnetGeometrySha,55,48},
    {"KiaSportage",kKiaBonnetGeometrySha,206,234}
}};
constexpr bool reflection_layout(uint32_t triangles,uint32_t vertices,bool expanded=true) noexcept {
    return (triangles==55&&vertices==48)||(expanded&&triangles==206&&vertices==234);
}
inline constexpr char kPS2EnvSourceSha[] =
    "aa15159a5f3f668244dd3b1c5c7b8322d8f41ac626c3a1741222b797252ad1e4";
inline constexpr std::array<D3DRENDERSTATETYPE, 4> kReflectionRenderStates = {
    D3DRS_ALPHATESTENABLE, D3DRS_ALPHABLENDENABLE, D3DRS_ZWRITEENABLE, D3DRS_LIGHTING};
inline constexpr std::array<D3DTEXTURESTAGESTATETYPE, 8> kReflectionStageStates = {
    D3DTSS_COLOROP, D3DTSS_COLORARG1, D3DTSS_COLORARG2, D3DTSS_ALPHAOP,
    D3DTSS_ALPHAARG1, D3DTSS_ALPHAARG2, D3DTSS_TEXCOORDINDEX, D3DTSS_TEXTURETRANSFORMFLAGS};

struct ReflectionSnapshot {
    const DrawSnapshot* geometry = nullptr; // Immutable; valid through this synchronous classification.
    bool live_race_verified = false, vehicle_body_verified = false;
    bool stock_coordinate_policy = false, native_states_complete = false;
    bool native_matches_effective = false, texture_matrix_known = false;
    uint64_t race_generation = 0, owner_lifetime = 0;
    uintptr_t textures[2]{};
    uint64_t texture_generations[2]{};
    bool textures_are_2d = false;
    std::array<DWORD, 4> render_states{};
    std::array<std::array<DWORD, 8>, 2> stages{};
};

struct ReflectionIdentity {
    bool accepted = false;
    const char* reason = "not_classified";
    const char* vehicle = "UNKNOWN";
    std::string geometry_sha256;
};
std::string reflection_geometry_sha(const DrawSnapshot& geometry);
ReflectionIdentity reflection_identity_for_hash(const ReflectionSnapshot&, std::string_view, uint64_t reset_generation, bool expanded=false);
ReflectionIdentity classify_reflection(const ReflectionSnapshot&, uint64_t reset_generation) noexcept;

struct ReflectionRequest {
    bool requested = false;
    IDirect3DTexture8* texture = nullptr; // Extension-owned; baseline retains original binding separately.
    DWORD color_op = D3DTOP_ADD;
    uint32_t override_mask = 0; // bit0 COLOROP, bit1 texture stage1; 0 never activates.
};

// Native-only state is owned and applied by the staged baseline integration.
// Retain a failed restoration for repair before any subsequent draw/state block.
struct ReflectionTransaction {
    DWORD original_color_op = 0;
    IDirect3DBaseTexture8* original_texture = nullptr;
    uint32_t changed_mask = 0; // bit0 COLOROP, bit1 texture stage1
    HRESULT last_failure = S_OK;
    ReflectionTransaction() = default;
    ReflectionTransaction(const ReflectionTransaction&) = delete;
    ~ReflectionTransaction() { release(); }
    void release() noexcept {
        if (original_texture) original_texture->Release();
        original_texture = nullptr;
        changed_mask = 0;
    }
};

template<class ColorWriter, class TextureWriter>
HRESULT restore_reflection_transaction(ReflectionTransaction& t, ColorWriter&& color, TextureWriter&& texture) noexcept {
    if (t.changed_mask & ~3u) return E_INVALIDARG;
    HRESULT result = S_OK;
    if (t.changed_mask & 2u) {
        const HRESULT hr = texture(t.original_texture);
        if (SUCCEEDED(hr)) t.changed_mask &= ~2u;
        else result = hr;
    }
    if (t.changed_mask & 1u) {
        const HRESULT hr = color(t.original_color_op);
        if (SUCCEEDED(hr)) t.changed_mask &= ~1u;
        else if (SUCCEEDED(result)) result = hr;
    }
    if (!t.changed_mask) t.release();
    t.last_failure = result;
    return result;
}

template<class ColorReader, class TextureReader, class ColorWriter, class TextureWriter>
HRESULT apply_reflection_transaction(const ReflectionRequest& request, ReflectionTransaction& t,
    ColorReader&& read_color, TextureReader&& read_texture, ColorWriter&& color,
    TextureWriter&& texture, bool& applied) noexcept {
    applied = false;
    const uint32_t mask = request.override_mask;
    if (!request.requested || !mask || (mask & ~3u) || t.changed_mask ||
        ((mask & 1u) && request.color_op != D3DTOP_ADD) || ((mask & 2u) && !request.texture))
        return E_INVALIDARG;
    t.release();
    HRESULT hr = S_OK;
    if (mask & 1u) {
        hr = read_color(t.original_color_op);
        if (FAILED(hr)) return hr;
    }
    if (mask & 2u) {
        hr = read_texture(t.original_texture); // Reader transfers one GetTexture reference.
        if (FAILED(hr) || !t.original_texture) { t.release(); return FAILED(hr) ? hr : E_POINTER; }
    }
    if (mask & 1u) {
        t.changed_mask |= 1u; // A failed native writer can still mutate: repair every attempted write.
        hr = color(request.color_op);
        if (FAILED(hr)) { restore_reflection_transaction(t, color, texture); return hr; }
    }
    if (mask & 2u) {
        t.changed_mask |= 2u;
        hr = texture(request.texture);
        if (FAILED(hr)) { restore_reflection_transaction(t, color, texture); return hr; }
    }
    applied = true;
    return S_OK;
}

bool canonical_env_identity(const uint8_t* bytes, size_t size, std::string_view digest) noexcept;
bool convert_static_env(const uint8_t* rgba, size_t size, std::vector<DWORD>& bgra) noexcept;

class StaticEnvTexture {
    IDirect3DTexture8* texture_ = nullptr;
public:
    ~StaticEnvTexture() { release(); }
    StaticEnvTexture() = default;
    StaticEnvTexture(const StaticEnvTexture&) = delete;
    HRESULT upload(IDirect3DDevice8&, const std::vector<DWORD>& bgra, bool require_add = true) noexcept;
    void release() noexcept { if (texture_) texture_->Release(); texture_ = nullptr; }
    IDirect3DTexture8* get() const noexcept { return texture_; }
};

class ReflectionPilot {
    struct CachedGeometry {
        std::array<uint64_t,14> key{};
        std::string digest;
        bool valid=false;
    };
    std::array<CachedGeometry,16> geometry_cache_{};
    size_t next_cache_=0;
    uint64_t geometry_evaluations_=0;
    ReflectionMode mode_ = ReflectionMode::Stock;
    bool verified_asset_ = false, disabled_ = false, blocked_ = false, suspended_ = false;
    uint8_t logged_ = 0;
    bool diagnostics_ = false;
    bool expanded_ = false;
    const char* reason_ = "stock_default";
    std::vector<DWORD> pixels_;
    StaticEnvTexture texture_;
    ReflectionTransaction transaction_;
    MixedReflectionCapture capture_;
    HRESULT upload_hresult_ = E_PENDING;
public:
    ReflectionPilot(bool supported_build, const std::wstring& port_ini) noexcept;
    bool requested() const noexcept { return mode_ != ReflectionMode::Stock; }
    bool active() const noexcept { return requested() && verified_asset_ && !disabled_ && !blocked_ && !suspended_; }
    // Keep upload provenance and proxy ownership through a temporary Reset
    // suspension; an effect resuming later must not have exposed raw buffers.
    bool mirroring_required() const noexcept { return requested() && verified_asset_ && !disabled_; }
    bool blocked() const noexcept { return blocked_; }
    uint32_t mode_value() const noexcept { return static_cast<uint32_t>(mode_); }
    const char* reason() const noexcept { return reason_; }
    bool diagnostics() const noexcept { return diagnostics_; }
    bool expanded() const noexcept { return expanded_; }
    HRESULT upload_hresult() const noexcept { return upload_hresult_; }
    bool initialize(IDirect3DDevice8&) noexcept;
    ReflectionIdentity classify(const ReflectionSnapshot&, uint64_t reset_generation) noexcept;
    uint64_t geometry_evaluations() const noexcept { return geometry_evaluations_; }
    ReflectionRequest request(const ReflectionIdentity&, IDirect3DTexture8* mixed_texture = nullptr) const noexcept;
    IDirect3DTexture8* static_texture() const noexcept { return texture_.get(); }
    bool needs_mixed_source() const noexcept { return mode_ == ReflectionMode::TataBodyPS2MixedContribution; }
    ReflectionTransaction& transaction() noexcept { return transaction_; }
    MixedReflectionCapture& mixed_capture() noexcept { return capture_; }
    bool claim_diagnostic(bool applied, const char* vehicle="Tata") noexcept;
    void disable(const char* reason) noexcept { disabled_ = true; reason_ = reason; }
    void before_reset() noexcept;
    void after_reset(IDirect3DDevice8&, bool native_reset_called, bool successful) noexcept;
    void shutdown() noexcept { capture_.release(); transaction_.release(); texture_.release(); disabled_=true; }
};
} // namespace gfx2::ps2port
