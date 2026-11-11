#pragma once
// Roster loader profile (MRLP v1): the roster-specific half of the SDK/G1 Challenge composition, carried inside
// roster.mrvr v2 instead of being compiled into dinput8.dll (Roster V4 stage 4, "loader independence").
//
// It used to be generated per roster into extra_sdk_profile.hpp / extra_options_package.hpp, so one loader build
// served exactly one roster; with a different roster the F3 boot refused the composition (BOOT_B_FAILED). The
// loader keeps only what belongs to its own code: the replay stub address of each Challenge hook.
//
//   0   char[4] "MRLP"          16  u32 extension_va       32  u8[32] immutable-range code SHA-256 (informational)
//   4   u32 version = 1         20  u32 extension_size     64  u32 check_count   68 u32 hook_count
//   8   u32 total size          24  u32 immutable_count    72  u32 vehicle_count 76 u32 challenge_human_offset
//   12  u32 registry_count      28  u32 reserved (0)
//   80  immutable ranges        {u32 offset, u32 size} x immutable_count
//       checks                  {u32 rva, u16 length, u16 0, bytes[length]} x check_count (SDK bytes as installed)
//       hooks                   {u32 rva, u8 id (0 preview, 1 consumer), u8 length = 7, u16 0, bytes[7]}
//       vehicles                {i32 physical_id, i32 class_id, u32 mode_mask} x vehicle_count
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "sdk_roster_abi.hpp"

namespace roster_profile {

struct Check {std::uint32_t rva = 0; std::vector<std::uint8_t> bytes;};
struct Hook {const char* id = ""; std::uint32_t rva = 0; std::array<std::uint8_t, 7> mapped{};};
struct Range {std::size_t offset = 0, size = 0;};
struct Profile {
    bool valid = false;
    std::uint32_t registry_count = 0, extension_va = 0, challenge_human_offset = 0;
    std::size_t extension_size = 0;
    std::vector<Range> immutable;
    std::vector<Check> checks;
    std::vector<Hook> hooks;
    std::vector<rmod1::SdkVehicleV1> vehicles;
};
inline constexpr const char* kHookIds[] = {"challenge-preview-identity", "challenge-race-consume"};

// The profile of the installed roster (set once by the VehicleRoster module in DllMain, read later by the F3 boot).
inline Profile& current() { static Profile p; return p; }

inline bool parse(const std::uint8_t* p, std::size_t n, Profile& out, char* why, std::size_t why_size) {
    auto fail = [&](const char* text) { std::snprintf(why, why_size, "%s", text); out = {}; return false; };
    auto u32 = [&](std::size_t at) { std::uint32_t v = 0; std::memcpy(&v, p + at, 4); return v; };
    auto u16 = [&](std::size_t at) { std::uint16_t v = 0; std::memcpy(&v, p + at, 2); return v; };
    out = {};
    if (n < 80 || std::memcmp(p, "MRLP", 4) || u32(4) != 1 || u32(8) != n) return fail("MRLP_HEADER_INVALID");
    out.registry_count = u32(12); out.extension_va = u32(16); out.extension_size = u32(20);
    const std::uint32_t ranges = u32(24), checks = u32(64), hooks = u32(68), vehicles = u32(72);
    out.challenge_human_offset = u32(76);
    if (!out.registry_count || out.registry_count > 4096 || !out.extension_size || ranges > 16 || !checks || checks > 4096 ||
        hooks != 2 || vehicles > 4096 || out.challenge_human_offset < 0x570 || out.challenge_human_offset > 0x7fffffff)
        return fail("MRLP_COUNTS_INVALID");
    std::size_t at = 80;
    for (std::uint32_t i = 0; i < ranges; ++i) {
        if (at + 8 > n) return fail("MRLP_TRUNCATED");
        Range r{u32(at), u32(at + 4)}; at += 8;
        if (r.offset > out.extension_size || r.size > out.extension_size - r.offset) return fail("MRLP_RANGE_INVALID");
        out.immutable.push_back(r);
    }
    for (std::uint32_t i = 0; i < checks; ++i) {
        if (at + 8 > n) return fail("MRLP_TRUNCATED");
        Check c; c.rva = u32(at); const std::uint16_t length = u16(at + 4); at += 8;
        if (!length || length > 256 || at + length > n) return fail("MRLP_CHECK_INVALID");
        c.bytes.assign(p + at, p + at + length); at += length;
        out.checks.push_back(std::move(c));
    }
    for (std::uint32_t i = 0; i < hooks; ++i) {
        if (at + 15 > n) return fail("MRLP_TRUNCATED");
        Hook h; h.rva = u32(at); const std::uint8_t id = p[at + 4], length = p[at + 5]; at += 8;
        if (id > 1 || length != 7) return fail("MRLP_HOOK_INVALID");
        h.id = kHookIds[id]; std::memcpy(h.mapped.data(), p + at, 7); at += 7;
        for (const auto& other : out.hooks) if (!std::strcmp(other.id, h.id)) return fail("MRLP_HOOK_DUPLICATE");
        out.hooks.push_back(h);
    }
    for (std::uint32_t i = 0; i < vehicles; ++i) {
        if (at + 12 > n) return fail("MRLP_TRUNCATED");
        rmod1::SdkVehicleV1 v{}; std::memcpy(&v.physical_id, p + at, 4); std::memcpy(&v.class_id, p + at + 4, 4); v.mode_mask = u32(at + 8); at += 12;
        if (v.physical_id < 0 || std::uint32_t(v.physical_id) >= out.registry_count || v.class_id < 0 || v.class_id > 3) return fail("MRLP_VEHICLE_INVALID");
        out.vehicles.push_back(v);
    }
    if (at != n) return fail("MRLP_TRAILING_BYTES");
    out.valid = true;
    std::snprintf(why, why_size, "MRLP checks=%u hooks=%u sdk_vehicles=%u registry=%u", checks, hooks, vehicles, out.registry_count);
    return true;
}

} // namespace roster_profile
