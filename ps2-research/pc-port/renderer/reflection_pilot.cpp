#include "reflection_pilot.hpp"
#include "ps2_port_extension.hpp"
#include "foliage_probe.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>

namespace gfx2::ps2port {
std::string reflection_geometry_sha(const DrawSnapshot& s) {
    if (!s.complete_mirror_coverage || s.primitive_type != D3DPT_TRIANGLELIST ||
        !reflection_layout(s.primitive_count,s.vertex_count) || s.fvf != 0x152 || s.stride != 36 ||
        !s.vertex_resource || !s.index_resource || !s.vertex_generation || !s.index_generation ||
        !s.vertex_revision || !s.index_revision) return {};
    const uint32_t index_size = s.index_format == D3DFMT_INDEX16 ? 2u : s.index_format == D3DFMT_INDEX32 ? 4u : 0u;
    if (!index_size || s.index_bytes.size() != uint64_t(s.primitive_count) * 3u * index_size) return {};
    const uint64_t begin = (uint64_t(s.base_vertex) + s.min_index) * s.stride;
    if (begin < s.vertex_byte_offset) return {};
    const uint64_t relative = begin - s.vertex_byte_offset;
    if (relative > s.vertex_bytes.size() || uint64_t(s.vertex_count) * 36u > s.vertex_bytes.size() - relative) return {};
    std::vector<std::string> faces;
    faces.reserve(s.primitive_count);
    for (uint32_t f = 0; f < s.primitive_count; ++f) {
        float xyz[9]{};
        for (uint32_t k = 0; k < 3; ++k) {
            uint32_t index = 0;
            std::memcpy(&index, s.index_bytes.data() + (f * 3u + k) * index_size, index_size);
            if (index < s.min_index || index - s.min_index >= s.vertex_count) return {};
            const uint64_t offset = relative + uint64_t(index - s.min_index) * 36u;
            std::memcpy(xyz + k * 3, s.vertex_bytes.data() + offset, 12);
        }
        auto hash = foliage_face_hash(xyz);
        if (hash.empty()) return {};
        faces.push_back(std::move(hash));
    }
    std::sort(faces.begin(), faces.end());
    std::string joined;
    joined.reserve(s.primitive_count * 64u);
    for (const auto& hash : faces) joined += hash;
    return sha256_bytes(joined.data(), joined.size());
}

ReflectionIdentity reflection_identity_for_hash(const ReflectionSnapshot& s, std::string_view hash, uint64_t reset_generation, bool expanded) {
    ReflectionIdentity result;
    result.geometry_sha256 = hash;
    const auto* g = s.geometry;
    const ReflectionMaterial* material=nullptr;
    if(g)for(size_t i=0;i<(expanded?kReflectionMaterials.size():1);++i){
        const auto& candidate=kReflectionMaterials[i];
        if(hash==candidate.geometry_sha&&g->primitive_count==candidate.triangles&&g->vertex_count==candidate.vertices)
            material=&candidate;
    }
    if(material)result.vehicle=material->vehicle;
    if (!g || !g->supported_build) result.reason = "unsupported_build";
    else if (!g->device_id || g->reset_generation != reset_generation) result.reason = "stale_device_or_reset";
    else if (!g->complete_mirror_coverage || !g->vertex_resource || !g->index_resource ||
             !g->vertex_generation || !g->index_generation || !g->vertex_revision || !g->index_revision)
        result.reason = "missing_current_upload_or_resource_identity";
    else if (g->primitive_type != D3DPT_TRIANGLELIST || !reflection_layout(g->primitive_count,g->vertex_count,expanded) ||
             g->fvf != 0x152 || g->stride != 36) result.reason = "wrong_geometry_layout";
    else if (!material) result.reason = "tata_bonnet_geometry_mismatch";
    else if (!s.live_race_verified || !s.race_generation || !s.owner_lifetime) result.reason = "live_race_owner_unverified";
    else if (!s.vehicle_body_verified) result.reason = "vehicle_body_unverified";
    else if (!s.stock_coordinate_policy) result.reason = "conflicting_viewdependent2d_policy";
    else if (!s.native_states_complete || !s.native_matches_effective || !s.texture_matrix_known)
        result.reason = "native_state_unknown_or_diverged";
    else if (!s.textures_are_2d || !s.textures[0] || !s.textures[1] ||
             !s.texture_generations[0] || !s.texture_generations[1]) result.reason = "missing_current_texture_identity";
    else if (s.render_states != std::array<DWORD,4>{FALSE,FALSE,TRUE,FALSE}) result.reason = "not_opaque_native_body";
    else if (s.stages[0] != std::array<DWORD,8>{D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,
              D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,0} ||
             s.stages[1] != std::array<DWORD,8>{D3DTOP_MODULATEALPHA_ADDCOLOR,D3DTA_CURRENT,D3DTA_TEXTURE,
              D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TEXTURE,D3DTSS_TCI_CAMERASPACENORMAL,D3DTTFF_COUNT2})
        result.reason = "native_material_stage_mismatch";
    else { result.accepted = true; result.vehicle=material->vehicle;
        result.reason = material==&kReflectionMaterials[0]?"exact_tata_bonnet_native_opaque_environment_material":
            "exact_verified_body_native_opaque_environment_material"; }
    return result;
}

ReflectionIdentity classify_reflection(const ReflectionSnapshot& s, uint64_t generation) noexcept {
    try { return reflection_identity_for_hash(s, s.geometry ? reflection_geometry_sha(*s.geometry) : "", generation); }
    catch (...) { ReflectionIdentity r; r.reason = "geometry_evaluation_failed"; return r; }
}

bool canonical_env_identity(const uint8_t* bytes, size_t size, std::string_view digest) noexcept {
    if (!bytes || size != 16392 || digest != kPS2EnvSourceSha) return false;
    uint32_t magic = 0; uint16_t width = 0, height = 0;
    std::memcpy(&magic, bytes, 4);
    std::memcpy(&width, bytes + 4, 2);
    std::memcpy(&height, bytes + 6, 2);
    return magic == 0x13039 && width == 64 && height == 64;
}

bool convert_static_env(const uint8_t* rgba, size_t size, std::vector<DWORD>& bgra) noexcept {
    bgra.clear();
    if (!rgba || size != 64u * 64u * 4u) return false;
    try {
        bgra.resize(64u * 64u);
        for (size_t n = 0; n < bgra.size(); ++n) {
            const auto* p = rgba + n * 4;
            const DWORD r = (DWORD(p[0]) * 80u) / 128u, g = (DWORD(p[1]) * 80u) / 128u, b = (DWORD(p[2]) * 80u) / 128u;
            // PS2's selected static contribution uses RGB (TCC=0), not image alpha.
            bgra[n] = 0xff000000u | (r << 16) | (g << 8) | b;
        }
        return true;
    } catch (...) { bgra.clear(); return false; }
}

HRESULT StaticEnvTexture::upload(IDirect3DDevice8& device, const std::vector<DWORD>& bgra, bool require_add) noexcept {
    release();
    if (bgra.size() != 4096) return E_INVALIDARG;
    D3DCAPS8 caps{};
    HRESULT hr = device.GetDeviceCaps(&caps);
    if (FAILED(hr)) return hr;
    if (caps.MaxSimultaneousTextures < 2 || (require_add && !(caps.TextureOpCaps & D3DTEXOPCAPS_ADD)) ||
        caps.MaxTextureWidth < 64 || caps.MaxTextureHeight < 64) return D3DERR_NOTAVAILABLE;
    hr = device.CreateTexture(64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture_);
    if (FAILED(hr) || !texture_) { release(); return FAILED(hr) ? hr : E_POINTER; }
    D3DLOCKED_RECT locked{};
    hr = texture_->LockRect(0,&locked,nullptr,0);
    if (FAILED(hr)) { release(); return hr; }
    bool valid = locked.pBits && locked.Pitch >= 64 * 4;
    if (valid) for (uint32_t row = 0; row < 64; ++row)
        std::memcpy(static_cast<uint8_t*>(locked.pBits) + size_t(row) * locked.Pitch,
                    bgra.data() + row * 64, 64 * 4);
    const HRESULT unlocked = texture_->UnlockRect(0);
    if (!valid || FAILED(unlocked)) { release(); return FAILED(unlocked) ? unlocked : E_FAIL; }
    return S_OK;
}

ReflectionPilot::ReflectionPilot(bool supported, const std::wstring& ini) noexcept {
    if (!supported) { reason_ = "unsupported_executable_stock"; return; }
    wchar_t value[32]{}, version[32]{};
    GetPrivateProfileStringW(L"PS2Port",L"ReflectionMode",L"0",value,32,ini.c_str());
    GetPrivateProfileStringW(L"PS2Port",L"ReflectionConfigVersion",L"1",version,32,ini.c_str());
    mode_ = reflection_mode(std::wstring_view(value),std::wstring_view(version),true);
    if (!requested()) { reason_ = std::wstring_view(value) == L"0" ? "stock_default" : "invalid_mode_or_version_stock"; return; }
    wchar_t coverage[16]{},precision[16]{};
    GetPrivateProfileStringW(L"PS2Port",L"ReflectionCoverage",L"0",coverage,16,ini.c_str());
    expanded_=std::wstring_view(coverage)==L"1";
    GetPrivateProfileStringW(L"PS2Port",L"ReflectionTargetPrecision",L"0",precision,16,ini.c_str());
    capture_.prefer_16bit(std::wstring_view(precision)==L"1");
    diagnostics_ = GetPrivateProfileIntW(L"PS2Port",L"ReflectionDiagnostics",0,ini.c_str()) == 1;
    if (mode_ == ReflectionMode::TataBodyNativeTextureAddOnly) {
        verified_asset_ = true; // This control uses only the already classified native texture.
        reason_ = "native_texture_colorop_control_waiting_for_device";
        return;
    }
    try {
        wchar_t path[32768]{};
        const DWORD count = GetPrivateProfileStringW(L"PS2Port",L"ReflectionSourceGXI",
            L"PS2EnvSource64x64.gxi",path,32768,ini.c_str());
        if (!count || count >= 32767) { reason_ = "missing_or_oversized_asset_path"; return; }
        std::filesystem::path input(path);
        if (input.is_relative()) input = std::filesystem::path(ini).parent_path() / input;
        std::ifstream file(input,std::ios::binary | std::ios::ate);
        if (!file || file.tellg() != 16392) { reason_ = "missing_or_wrong_size_local_env_gxi"; return; }
        std::vector<uint8_t> bytes(16392);
        file.seekg(0); file.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
        if (!file || !canonical_env_identity(bytes.data(),bytes.size(),sha256_bytes(bytes.data(),bytes.size()))) {
            reason_ = "local_env_gxi_hash_or_layout_mismatch"; return;
        }
        verified_asset_ = convert_static_env(bytes.data()+8,bytes.size()-8,pixels_);
        reason_ = verified_asset_ ? "verified_static_ps2_contribution_waiting_for_device" : "asset_conversion_failed";
    } catch (...) { reason_ = "local_asset_load_failed_stock"; verified_asset_ = false; }
}

bool ReflectionPilot::initialize(IDirect3DDevice8& device) noexcept {
    if (!active()) return false;
    if (mode_ == ReflectionMode::TataBodyNativeTextureAddOnly) {
        D3DCAPS8 caps{};
        upload_hresult_ = device.GetDeviceCaps(&caps);
        if (SUCCEEDED(upload_hresult_) && (caps.MaxSimultaneousTextures < 2 || !(caps.TextureOpCaps & D3DTEXOPCAPS_ADD)))
            upload_hresult_ = D3DERR_NOTAVAILABLE;
        if (FAILED(upload_hresult_)) {
            disabled_ = true; reason_ = "native_colorop_add_capability_failed_stock";
            return false;
        }
        reason_ = "native_texture_colorop_control_ready_no_private_asset";
        return true;
    }
    upload_hresult_ = texture_.upload(device,pixels_,mode_ != ReflectionMode::TataBodyPS2TextureOnly);
    if (FAILED(upload_hresult_)) { disabled_ = true; reason_ = "native_environment_texture_upload_failed_stock"; return false; }
    reason_ = needs_mixed_source() ? "static_ps2_term_ready_waiting_for_verified_framebuffer_capture" :
        mode_ == ReflectionMode::TataBodyPS2TextureOnly ? "static_ps2_texture_control_ready_native_colorop" :
        "static_ps2_contribution_ready_framebuffer_term_not_implemented";
    return true;
}

ReflectionRequest ReflectionPilot::request(const ReflectionIdentity& identity, IDirect3DTexture8* mixed_texture) const noexcept {
    ReflectionRequest result;
    if (!active() || !identity.accepted) return result;
    const uint32_t mask = reflection_override_mask(mode_);
    IDirect3DTexture8* selected = needs_mixed_source() ? mixed_texture : texture_.get();
    if (!mask || ((mask & 2u) && !selected)) return result;
    result.requested = true;
    result.override_mask = mask;
    result.texture = (mask & 2u) ? selected : nullptr;
    return result;
}

ReflectionIdentity ReflectionPilot::classify(const ReflectionSnapshot& s, uint64_t generation) noexcept {
    try {
        if (!s.geometry) return classify_reflection(s,generation);
        const auto& g=*s.geometry;
        const std::array<uint64_t,15> key={g.device_id,g.reset_generation,g.vertex_resource,g.index_resource,
            g.vertex_generation,g.index_generation,g.vertex_revision,g.index_revision,g.start_index,
            g.base_vertex,g.min_index,g.vertex_count,g.index_format,g.vertex_byte_offset,g.primitive_count};
        for (const auto& entry:geometry_cache_) if(entry.valid&&entry.key==key)
            return reflection_identity_for_hash(s,entry.digest,generation,expanded_);
        ++geometry_evaluations_;
        const auto digest=reflection_geometry_sha(g);
        auto& entry=geometry_cache_[next_cache_++ % geometry_cache_.size()];
        entry={key,digest,true};
        return reflection_identity_for_hash(s,digest,generation,expanded_);
    } catch (...) { ReflectionIdentity result;result.reason="geometry_evaluation_failed";return result; }
}

bool ReflectionPilot::claim_diagnostic(bool applied, const char* vehicle) noexcept {
    size_t index=kReflectionMaterials.size();
    for(size_t i=0;i<kReflectionMaterials.size();++i)if(!std::strcmp(vehicle,kReflectionMaterials[i].vehicle)){index=i;break;}
    const uint8_t bit=applied?2u:1u;
    if(!diagnostics_||(logged_[index]&bit))return false;
    logged_[index]|=bit;
    return true;
}

void ReflectionPilot::before_reset() noexcept {
    // Baseline attempts native repair first. If it could not repair, release held
    // references for Reset and prohibit draws until a real successful reset.
    if (transaction_.changed_mask || capture_.pending()) blocked_ = true;
    capture_.release();
    transaction_.release();
    texture_.release();
    for (auto& entry:geometry_cache_) entry={};
    next_cache_=0;
}

void ReflectionPilot::after_reset(IDirect3DDevice8& device, bool called, bool successful) noexcept {
    if (!requested() && !blocked_) return; // Stock must not acquire a new failed-Reset draw gate.
    if (called && successful) { blocked_ = false; suspended_ = false; }
    if (called && !successful) {
        suspended_ = true; reason_ = "device_reset_failed_reflection_suspended_stock";
        return; // Only an unrepaired native override (blocked_) can prohibit a later draw.
    }
    if (!blocked_ && active()) initialize(device);
}
} // namespace gfx2::ps2port
