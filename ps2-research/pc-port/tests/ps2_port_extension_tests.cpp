#include "ps2_port_extension.hpp"
#include "ps2_config.hpp"
#include "provenance.hpp"

#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <initializer_list>
#include <string>
#include <vector>

namespace {
int failures = 0;
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " #x "\n"; ++failures; } } while (0)

std::wstring temp_dir() {
    wchar_t root[MAX_PATH]{};
    const DWORD length = GetTempPathW(MAX_PATH, root);
    if (!length || length >= MAX_PATH) return {};
    std::wstring path(root, length);
    path += L"MRR-PS2Port-" + std::to_wstring(GetCurrentProcessId());
    CreateDirectoryW(path.c_str(), nullptr);
    return path;
}

std::wstring renderer_ini(const std::wstring& dir) { return dir + L"\\MRRRenderer.ini"; }

bool write_config(const std::wstring& dir, const wchar_t* body) {
    const std::wstring path = dir + L"\\PS2Port.ini";
    HANDLE file = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    const size_t bytes = wcslen(body) * sizeof(wchar_t);
    DWORD written = 0;
    const bool okay = WriteFile(file, body, static_cast<DWORD>(bytes), &written, nullptr) && written == bytes;
    CloseHandle(file);
    return okay;
}

void cleanup(const std::wstring& dir) {
    DeleteFileW((dir + L"\\PS2Port.ini").c_str());
    DeleteFileW((dir + L"\\MRRRenderer.ini").c_str());
    RemoveDirectoryW(dir.c_str());
}

void mode_and_mirror_policy() {
    const auto dir = temp_dir();
    CHECK(!dir.empty());
    gfx2::ps2port::PS2PortExtension missing(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(!missing.requested());
    CHECK(!missing.buffer_mirroring_required());

    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=0\r\nDiagnostics=1\r\n"));
    gfx2::ps2port::PS2PortExtension stock(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(!stock.requested());
    CHECK(!stock.active());
    CHECK(!stock.buffer_mirroring_required());
    CHECK(stock.diagnostics());
    CHECK(stock.mode_value() == 0);
    CHECK(std::string(stock.mode_name()) == "stock");
    CHECK(!stock.claim_draw_diagnostic());

    for (UINT mode = 1; mode <= 3; ++mode) {
        const std::wstring config = L"[PS2Port]\r\nFoliageMode=" + std::to_wstring(mode) + L"\r\nDiagnostics=0\r\n";
        CHECK(write_config(dir, config.c_str()));
        gfx2::ps2port::PS2PortExtension enabled(true, gfx2::TARGET_SHA, renderer_ini(dir));
        CHECK(enabled.requested());
        CHECK(enabled.active());
        CHECK(enabled.buffer_mirroring_required());
        CHECK(enabled.mode_value() == mode);
        CHECK(!enabled.diagnostics());
        CHECK(!enabled.claim_draw_diagnostic());
    }

    gfx2::ps2port::PS2PortExtension wrong_build(true, "unknown", renderer_ini(dir));
    CHECK(!wrong_build.active());
    CHECK(!wrong_build.buffer_mirroring_required());
    gfx2::ps2port::PS2PortExtension unsupported(false, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(!unsupported.active());
    CHECK(!unsupported.buffer_mirroring_required());

    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=99\r\n"));
    gfx2::ps2port::PS2PortExtension invalid(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(!invalid.active());
    CHECK(!invalid.buffer_mirroring_required());

    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=1\r\nDiagnostics=1\r\n"));
    gfx2::ps2port::PS2PortExtension one_shot(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(one_shot.claim_draw_diagnostic());
    CHECK(!one_shot.claim_draw_diagnostic());
    cleanup(dir);
}

void pixel_probe_configuration_and_format_contract() {
    using namespace gfx2::ps2port;
    CHECK(pixel_probe_mode_supported(0));
    CHECK(!pixel_probe_mode_supported(1));
    CHECK(!pixel_probe_mode_supported(2));
    CHECK(pixel_probe_mode_supported(3));
    CHECK(pixel_probe_format_supported(D3DFMT_X8R8G8B8));
    CHECK(pixel_probe_format_supported(D3DFMT_A8R8G8B8));
    CHECK(!pixel_probe_format_supported(D3DFMT_R5G6B5));
    CHECK(kPixelProbeMaxSamples == 4);
    CHECK(kPixelProbeTextureStages == 2);
    CHECK(pixel_probe_has_sample_capacity(0));
    CHECK(pixel_probe_has_sample_capacity(3));
    CHECK(!pixel_probe_has_sample_capacity(4));
    CHECK(!pixel_probe_has_sample_capacity(5));

    PixelColor color{};
    CHECK(decode_pixel_color(D3DFMT_X8R8G8B8, 0x12345678u, color));
    CHECK(color.r == 0x34 && color.g == 0x56 && color.b == 0x78);
    CHECK(!color.alpha_valid && color.a == 0);
    CHECK(decode_pixel_color(D3DFMT_A8R8G8B8, 0x12345678u, color));
    CHECK(color.r == 0x34 && color.g == 0x56 && color.b == 0x78);
    CHECK(color.alpha_valid && color.a == 0x12);

    const auto dir = temp_dir();
    CHECK(!dir.empty());
    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=0\r\nPixelProbe=1\r\nPixelX=321\r\nPixelY=654\r\nPixelLaterDrawOrdinal=500\r\n"));
    PS2PortExtension stock(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(stock.pixel_probe_requested() && stock.pixel_probe_enabled());
    CHECK(stock.analysis_enabled() && stock.buffer_mirroring_required());
    CHECK(stock.pixel_probe_x() == 321 && stock.pixel_probe_y() == 654);
    CHECK(stock.pixel_probe_later_ordinal() == 500);
    CHECK(state_request_for_mode(PilotMode::Stock).override_mask == 0);

    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=3\r\nPixelProbe=1\r\nPixelX=321\r\nPixelY=654\r\n"));
    PS2PortExtension depth(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(depth.pixel_probe_enabled() && depth.mode_value() == 3);
    CHECK(state_request_for_mode(PilotMode::France1Bush01DepthWriteOnly).override_mask == 0x10);

    for (UINT mode : {1u, 2u}) {
        const auto config = L"[PS2Port]\r\nFoliageMode=" + std::to_wstring(mode) + L"\r\nPixelProbe=1\r\nPixelX=321\r\nPixelY=654\r\n";
        CHECK(write_config(dir, config.c_str()));
        PS2PortExtension unsupported_mode(true, gfx2::TARGET_SHA, renderer_ini(dir));
        CHECK(unsupported_mode.pixel_probe_requested());
        CHECK(!unsupported_mode.pixel_probe_enabled());
    }

    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=0\r\nPixelProbe=1\r\nPixelX=-1\r\nPixelY=654\r\n"));
    PS2PortExtension missing_pixel(true, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(missing_pixel.pixel_probe_requested() && !missing_pixel.pixel_probe_enabled());
    CHECK(std::string(missing_pixel.pixel_probe_status()) == "pixel_coordinates_missing_or_out_of_range");

    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=0\r\nPixelProbe=1\r\nPixelX=321\r\nPixelY=654\r\n"));
    PS2PortExtension wrong_build(false, gfx2::TARGET_SHA, renderer_ini(dir));
    CHECK(!wrong_build.pixel_probe_requested() && !wrong_build.pixel_probe_enabled());
    CHECK(std::string(wrong_build.pixel_probe_status()) == "disabled");
    CHECK(!wrong_build.buffer_mirroring_required());
    cleanup(dir);
}

void state_mode_contract() {
    using namespace gfx2::ps2port;
    const auto stock = state_request_for_mode(PilotMode::Stock);
    const auto combined = state_request_for_mode(PilotMode::France1Bush01Treeblend);
    const auto alpha = state_request_for_mode(PilotMode::France1Bush01AlphaBlendOnly);
    const auto depth = state_request_for_mode(PilotMode::France1Bush01DepthWriteOnly);
    CHECK(!stock.requested && stock.override_mask == 0);
    CHECK(combined.requested && combined.override_mask == 0x1f);
    CHECK(alpha.requested && alpha.override_mask == 0x0f);
    CHECK(depth.requested && depth.override_mask == 0x10);
    CHECK(combined.alpha_test_enable == FALSE && combined.alpha_blend_enable == TRUE);
    CHECK(combined.source_blend == D3DBLEND_SRCALPHA && combined.destination_blend == D3DBLEND_INVSRCALPHA);
    CHECK(combined.z_write_enable == FALSE);
    CHECK(alpha.z_write_enable == FALSE); // Mask excludes ZWRITE; the native value is not read or changed.
    CHECK(depth.z_write_enable == FALSE); // Mask excludes all four alpha/blend states.
    CHECK(valid_state_override_mask(0x1f));
    CHECK(valid_state_override_mask(0x0f));
    CHECK(valid_state_override_mask(0x10));
    CHECK(!valid_state_override_mask(0));
    CHECK(!valid_state_override_mask(0x20));
    CHECK(!valid_state_override_mask(0x21));
}

struct MockStates {
    std::array<DWORD, 5> values{TRUE, FALSE, D3DBLEND_ONE, D3DBLEND_ZERO, TRUE};
    uint32_t reads = 0;
    std::vector<size_t> writes;
    bool fail_after_mutating_index_one_once = false;
};

void state_transaction_contract() {
    using namespace gfx2::ps2port;
    const PilotMode modes[] = {PilotMode::France1Bush01Treeblend,
                               PilotMode::France1Bush01AlphaBlendOnly,
                               PilotMode::France1Bush01DepthWriteOnly};
    for (const PilotMode mode : modes) {
        MockStates native;
        const auto original = native.values;
        const auto request = state_request_for_mode(mode);
        StateTransaction transaction{};
        uint32_t applied = 0;
        auto read = [&](size_t index, DWORD& value) noexcept {
            native.reads |= 1u << index;
            value = native.values[index];
            return true;
        };
        auto write = [&](size_t index, DWORD value) noexcept {
            native.writes.push_back(index);
            native.values[index] = value;
            return true;
        };
        CHECK(apply_state_transaction(request, transaction, read, write, applied));
        CHECK(applied == request.override_mask);
        CHECK(native.reads == request.override_mask);
        for (size_t i = 0; i < native.values.size(); ++i) {
            if ((request.override_mask & (1u << i)) == 0) CHECK(native.values[i] == original[i]);
        }
        CHECK(restore_state_transaction(transaction, write));
        CHECK(native.values == original);
        CHECK(transaction.changed_mask == 0);
        for (size_t i = 0; i < native.values.size(); ++i) {
            if ((request.override_mask & (1u << i)) == 0)
                CHECK(std::find(native.writes.begin(), native.writes.end(), i) == native.writes.end());
        }
    }

    for (const uint32_t invalid_mask : {0u, 0x20u, 0x21u}) {
        MockStates native;
        const auto original = native.values;
        auto request = state_request_for_mode(PilotMode::France1Bush01Treeblend);
        request.override_mask = invalid_mask;
        StateTransaction transaction{};
        uint32_t applied = 99;
        auto read = [&](size_t, DWORD&) noexcept { ++native.reads; return true; };
        auto write = [&](size_t, DWORD) noexcept { native.writes.push_back(0); return true; };
        CHECK(!apply_state_transaction(request, transaction, read, write, applied));
        CHECK(applied == 0 && native.reads == 0 && native.writes.empty());
        CHECK(native.values == original && transaction.changed_mask == 0);
    }
    {
        StateTransaction malformed{};
        malformed.changed_mask = 0x20;
        unsigned writes = 0;
        auto write = [&](size_t, DWORD) noexcept { ++writes; return true; };
        CHECK(!restore_state_transaction(malformed, write));
        CHECK(writes == 0 && malformed.changed_mask == 0x20);
    }

    {
        MockStates native;
        StateTransaction transaction{};
        uint32_t applied = 99;
        const auto request = state_request_for_mode(PilotMode::Stock);
        auto read = [&](size_t, DWORD&) noexcept { ++native.reads; return true; };
        auto write = [&](size_t, DWORD) noexcept { native.writes.push_back(0); return true; };
        CHECK(!apply_state_transaction(request, transaction, read, write, applied));
        CHECK(applied == 0 && native.reads == 0 && native.writes.empty());
    }

    MockStates native;
    const auto original = native.values;
    native.fail_after_mutating_index_one_once = true;
    const auto request = state_request_for_mode(PilotMode::France1Bush01Treeblend);
    StateTransaction transaction{};
    uint32_t applied = 99;
    auto read = [&](size_t index, DWORD& value) noexcept {
        native.reads |= 1u << index;
        value = native.values[index];
        return true;
    };
    auto write = [&](size_t index, DWORD value) noexcept {
        native.writes.push_back(index);
        native.values[index] = value;
        if (index == 1 && native.fail_after_mutating_index_one_once) {
            native.fail_after_mutating_index_one_once = false;
            return false;
        }
        return true;
    };
    CHECK(!apply_state_transaction(request, transaction, read, write, applied));
    CHECK(applied == 0);
    CHECK(native.values == original);
    CHECK(transaction.changed_mask == 0);
    CHECK((native.writes == std::vector<size_t>{0, 1, 1, 0}));
}

void exact_identity_contract() {
    constexpr char target[] = "2b60b1f044601052bb5eaeca074615abe3947fdc1b0769c17d300a0b3b3e6f7d";
    CHECK(gfx2::ps2port::is_france1_bush01_geometry(target));
    std::string upper(target);
    for (char& c : upper) if (c >= 'a' && c <= 'f') c = static_cast<char>(c - 'a' + 'A');
    CHECK(gfx2::ps2port::is_france1_bush01_geometry(upper));
    CHECK(!gfx2::ps2port::is_france1_bush01_geometry("a92ad14c7e7904a2029a620a02d15558af69ce984a04c38ecefc2a7f43a23d68"));
    CHECK(!gfx2::ps2port::is_france1_bush01_geometry(std::string(target) + "0"));

    const auto dir = temp_dir();
    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=1\r\n"));
    gfx2::ps2port::PS2PortExtension extension(true, gfx2::TARGET_SHA, renderer_ini(dir));
    gfx2::ps2port::DrawSnapshot empty{};
    empty.supported_build = true;
    empty.device_id = 1;
    empty.france1_course_verified = true;
    empty.race_generation = 10;
    empty.owner_lifetime = 12;
    auto no_data = extension.classify(empty);
    CHECK(!no_data.state.requested);
    CHECK(std::string(no_data.identity) == "missing_current_resource_identity");

    empty.vertex_resource = 11;
    empty.index_resource = 12;
    empty.vertex_generation = 4;
    empty.index_generation = 5;
    empty.vertex_revision = 7;
    empty.index_revision = 9;
    empty.complete_mirror_coverage = true;
    empty.primitive_type = D3DPT_TRIANGLELIST;
    empty.primitive_count = 48;
    empty.vertex_count = 3;
    empty.stride = 20;
    empty.fvf = 0x102;
    empty.index_format = D3DFMT_INDEX16;
    empty.vertex_bytes.resize(60);
    empty.index_bytes.resize(48 * 3 * 2);
    for (unsigned i = 0; i < 48 * 3; ++i) {
        const uint16_t index = static_cast<uint16_t>(i % 3);
        std::memcpy(empty.index_bytes.data() + i * 2, &index, 2);
    }
    extension.device_reset(false);
    CHECK(extension.reset_generation() == 0);
    empty.reset_generation = 1;
    CHECK(std::string(extension.classify(empty).identity) == "stale_device_or_reset_generation");
    extension.device_reset(true);
    CHECK(extension.reset_generation() == 1);
    auto mismatch = extension.classify(empty);
    CHECK(!mismatch.state.requested);
    CHECK(std::string(mismatch.identity) == "geometry_signature_mismatch");

    auto current_generation = empty;
    current_generation.reset_generation = 0;
    for (UINT mode = 2; mode <= 3; ++mode) {
        const std::wstring config = L"[PS2Port]\r\nFoliageMode=" + std::to_wstring(mode) + L"\r\n";
        CHECK(write_config(dir, config.c_str()));
        gfx2::ps2port::PS2PortExtension diagnostic_mode(true, gfx2::TARGET_SHA, renderer_ini(dir));
        const auto rejected = diagnostic_mode.classify(current_generation);
        CHECK(diagnostic_mode.active());
        CHECK(!rejected.state.requested && rejected.state.override_mask == 0);
        CHECK(std::string(rejected.identity) == "geometry_signature_mismatch");
    }
    CHECK(write_config(dir, L"[PS2Port]\r\nFoliageMode=0\r\n"));
    gfx2::ps2port::PS2PortExtension stock(true, gfx2::TARGET_SHA, renderer_ini(dir));
    const auto stock_result = stock.classify(current_generation);
    CHECK(!stock_result.state.requested && stock_result.state.override_mask == 0);
    CHECK(std::string(stock_result.identity) == "stock_mode");

    extension.disable("test");
    CHECK(!extension.active());
    CHECK(!extension.buffer_mirroring_required());
    cleanup(dir);
}
}

void config_v2_contract() {
    namespace cfg = gfx2::ps2port::config;
    const auto dir = temp_dir();
    CHECK(!dir.empty());
    const std::wstring ini = dir + L"\\PS2Port.ini";
    CHECK(write_config(dir, L"[PS2Port]\r\nRaceFleet=1\r\nReflection=4\r\nFrontendModel=2\r\nDiagnostics=1\r\nRaceModelAssetDirectory=PS2Vehicles\r\nRacePS2WheelMode=0\r\nReflectionMode=1\r\n"));
    for (const wchar_t* key : {L"RacePS2FleetMode", L"RacePS2ModelMode", L"RacePS2WheelMode", L"RacePS2ModelParts", L"RacePS2CrewMode", L"XtrailFidelityMode", L"RaceModelMode"})
        CHECK(cfg::read_int(key, 0, ini.c_str()) == 1);
    CHECK(cfg::read_int(L"ReflectionMode", 0, ini.c_str()) == 4);  // v2 wins over the legacy key
    CHECK(cfg::read_int(L"FrontendModelMode", 0, ini.c_str()) == 2);
    for (const wchar_t* key : {L"ReflectionDiagnostics", L"RacePS2FleetCapture", L"RacePS2FleetDamageCapture", L"GrassDiagnostics"})
        CHECK(cfg::read_int(key, 0, ini.c_str()) == 1);
    wchar_t text[64]{};
    cfg::read_string(L"RacePS2ModelAssetDirectory", L".", text, 64, ini.c_str());
    CHECK(std::wstring(text) == L"PS2Vehicles");
    CHECK(cfg::read_int(L"GrassMode", 7, ini.c_str()) == 7);  // neither key present: caller default
    CHECK(write_config(dir, L"[PS2Port]\r\nRacePS2WheelMode=1\r\nReflectionMode=3\r\nGrassDiagnostics=1\r\n"));
    CHECK(cfg::read_int(L"RacePS2WheelMode", 0, ini.c_str()) == 1);  // legacy-only INI keeps working
    CHECK(cfg::read_int(L"RacePS2ModelMode", 0, ini.c_str()) == 0);
    CHECK(cfg::read_int(L"ReflectionMode", 0, ini.c_str()) == 3);
    CHECK(cfg::read_int(L"GrassDiagnostics", 0, ini.c_str()) == 1);
    CHECK(cfg::read_int(L"ShrubsDiagnostics", 0, ini.c_str()) == 0);
    CHECK(cfg::v2_key(L"FrontendModelAsset") == nullptr && cfg::v2_key(L"Diagnostics") == nullptr);
    CHECK(cfg::v2_key(L"FrontendGeometryDiagnostics") == nullptr);  // heavy research probe stays legacy-only
    cleanup(dir);
}
int main() {
    mode_and_mirror_policy();
    pixel_probe_configuration_and_format_contract();
    state_mode_contract();
    state_transaction_contract();
    exact_identity_contract();
    config_v2_contract();
    if (failures) return 1;
    std::cout << "PS2 pilot modes, masked state transactions, rollback, fail-closed identity, mirroring and reset contracts passed\n";
    return 0;
}
