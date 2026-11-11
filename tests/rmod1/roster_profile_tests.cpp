// Offline checks of the MRLP loader profile carried by roster.mrvr v2 (no game process).
// argv[1] = a roster.mrvr v2 produced by tools/roster_loader_profile.py.
#include "../../src/native/rmod1/roster_loader_profile.hpp"
#include <fstream>
#include <iterator>
#include <vector>

static int failures = 0;
#define CHECK(x) do { if (!(x)) { std::printf("FAIL %d: %s\n", __LINE__, #x); ++failures; } } while (0)

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    std::ifstream f(argv[1], std::ios::binary);
    const std::vector<std::uint8_t> roster((std::istreambuf_iterator<char>(f)), {});
    CHECK(roster.size() > 256 && !std::memcmp(roster.data(), "MRVR", 4));
    std::uint32_t version = 0, at = 0, size = 0;
    std::memcpy(&version, roster.data() + 4, 4); std::memcpy(&at, roster.data() + 248, 4); std::memcpy(&size, roster.data() + 252, 4);
    CHECK(version == 2 && at >= 256 && std::size_t(at) + size == roster.size());
    char why[160]{};
    roster_profile::Profile p;
    CHECK(roster_profile::parse(roster.data() + at, size, p, why, sizeof(why)));
    CHECK(p.valid && p.registry_count == 35 && p.extension_va == 0x10000000u && p.hooks.size() == 2 && p.checks.size() > 200);
    CHECK(p.challenge_human_offset == 1860 && !std::strcmp(p.hooks[0].id, "challenge-preview-identity"));
    for (const auto& h : p.hooks) CHECK(h.mapped[0] == 0x8b && h.mapped[3] == 0x48 && h.mapped[4] == 0x07);
    bool retired = false; for (const auto& v : p.vehicles) retired = retired || v.physical_id == 34;
    CHECK(!retired && p.vehicles.size() == 8);
    // Fail closed: truncation, wrong size field, trailing bytes, bad hook count.
    const std::vector<std::uint8_t> profile(roster.begin() + at, roster.end());
    roster_profile::Profile bad;
    CHECK(!roster_profile::parse(profile.data(), profile.size() - 1, bad, why, sizeof(why)) && !bad.valid);
    auto extra = profile; extra.push_back(0); std::uint32_t n = std::uint32_t(extra.size()); std::memcpy(extra.data() + 8, &n, 4);
    CHECK(!roster_profile::parse(extra.data(), extra.size(), bad, why, sizeof(why)));
    auto hooks = profile; hooks[68] = 3;
    CHECK(!roster_profile::parse(hooks.data(), hooks.size(), bad, why, sizeof(why)));
    std::printf("%s (%d failures)\n", failures ? "FAILED" : "PASS", failures);
    return failures ? 1 : 0;
}
