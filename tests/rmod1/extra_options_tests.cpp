#include "../../src/native/rmod1/extra_options.hpp"
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

int main(int argc, char** argv) {
    assert(argc == 2);
    std::ifstream input(argv[1], std::ios::binary);
    const std::string legacy((std::istreambuf_iterator<char>(input)), {});
    const auto v2 = rmod1::parse_ini(legacy);
    assert(v2.accepted && v2.config.config_version == 2);
    assert(v2.config.mode_policies[0] == rmod1::Policy::Full && v2.config.max_opponents == 5);
    // Do not accidentally extend the strict legacy grammar.
    assert(!rmod1::parse_ini(legacy + "\n[Customization]\nEnabled=1\n").accepted);
    const auto empty = extra_options::parse_config("[General]\nConfigVersion=1\n");
    assert(empty.accepted && !empty.config.enabled && !empty.config.tires && !empty.config.liveries);
    const auto options = extra_options::parse_config(
        "[General]\r\nConfigVersion=1\r\n[Customization]\r\nEnabled=1\r\nLiveries=1\r\nTires=1\r\n");
    assert(options.accepted && options.config.enabled && options.config.tires && options.config.liveries);
    for (const char* invalid : {"", "[General]\nConfigVersion=2\n",
             "[General]\nConfigVersion=1\n[Customization]\nEnabled=1\nEnabled=0\n",
             "[General]\nConfigVersion=1\n[Customization]\nTires=1\nSurprise=1\n",
             "[General]\nConfigVersion=1\n[Customization]\nEnabled=1\nTires=maybe\n"}) {
        auto bad = extra_options::parse_config(invalid);
        assert(!bad.accepted && !bad.config.enabled && !bad.config.tires && !bad.config.liveries);
    }
    const auto ghost = extra_options::parse_config(
        "[General]\nConfigVersion=1\n[Ghost]\nEnabled=1\nWithOpponents=1\nRecordAllModes=0\nUseAlphaModel=0\n[Difficulty]\nLevels=5\n");
    assert(ghost.accepted && ghost.config.ghost && ghost.config.ghost_with_opponents && !ghost.config.ghost_record_all_modes);
    assert(!ghost.config.ghost_use_alpha_model && ghost.config.five_difficulties && !ghost.config.enabled);
    assert(empty.config.ghost_use_alpha_model && !empty.config.ghost && !empty.config.five_difficulties);
    for (const char* invalid : {"[General]\nConfigVersion=1\n[Ghost]\nEnabled=true\n",
             "[General]\nConfigVersion=1\n[Ghost]\nEnabled=1\nEnabled=1\n",
             "[General]\nConfigVersion=1\n[Ghost]\nMatch=Any\n",
             "[General]\nConfigVersion=1\n[Difficulty]\nLevels=3\n",
             "[General]\nConfigVersion=1\n[Difficulty]\nLevels=5\n[Difficulty]\nLevels=5\n"})
        assert(!extra_options::parse_config(invalid).accepted);
    // Compounds: Stock is exact, every compound is best on its own surface and idempotent.
    for (unsigned s = 0; s < extra_options::kSurfaceCount; ++s) assert(extra_options::grip_scale(extra_options::Tire::Stock, s) == 1.0f);
    for (unsigned c = 1; c < extra_options::kTireCount; ++c)
        for (unsigned s = 0; s < extra_options::kSurfaceCount; ++s)
            assert(extra_options::grip_scale(static_cast<extra_options::Tire>(c), s) <= extra_options::grip_scale(static_cast<extra_options::Tire>(c), c - 1));
    float stock[extra_options::kSurfaceCount][extra_options::kTyreFields]{};
    for (unsigned s = 0; s < extra_options::kSurfaceCount; ++s)
        for (unsigned f = 0; f < extra_options::kTyreFields; ++f) stock[s][f] = 1.0f + 0.1f * float(s) + 0.01f * float(f);
    float records[6 * extra_options::kTyreFields]{};
    for (unsigned r = 0; r < 5; ++r) std::memcpy(records + r * extra_options::kTyreFields, stock[4 - r], sizeof(stock[0]));
    for (unsigned f = 0; f < extra_options::kTyreFields; ++f) records[5 * extra_options::kTyreFields + f] = 9.0f; // AI/foreign record
    assert(extra_options::apply_compound(records, 6, extra_options::Tire::Stock, stock) == 0);
    assert(extra_options::apply_compound(records, 6, extra_options::Tire::Gravel, stock) == 5);
    assert(extra_options::apply_compound(records, 6, extra_options::Tire::Gravel, stock) == 0);
    assert(records[2 * extra_options::kTyreFields + extra_options::kPeakMu] == stock[2][extra_options::kPeakMu] * 1.10f);
    assert(records[5 * extra_options::kTyreFields] == 9.0f && records[extra_options::kTyreFields + 1] == stock[3][1]);
    extra_options::Participant human{1, 21, false};
    assert(extra_options::tire_applies(options.config, human));
    auto ai = human; ai.player_type = 2; assert(!extra_options::tire_applies(options.config, ai));
    auto attract = human; attract.attract = true; assert(!extra_options::tire_applies(options.config, attract));
    auto off = options.config; off.tires = false; assert(!extra_options::tire_applies(off, human));
    std::cout << "PASS strict V2 preservation, optional Extra Options config, six tyre compounds, idempotent stock-record scaling, human-only any-mode scope\n";
}
