#include "../../src/native/rmod1/extra_options.hpp"
#include <cassert>
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
    extra_options::RaceContext c{2, 1, 0, 1, 21, 21, false, false, false};
    auto stock = extra_options::plan_tires(options.config, extra_options::Tire::Stock, c, 0);
    assert(stock.applies && stock.passthrough && !stock.front && !stock.rear);
    for (unsigned index = 1; index <= 5; ++index) {
        const auto tire = static_cast<extra_options::Tire>(index);
        assert(!extra_options::plan_tires(options.config, tire, c, 0).applies);
        const auto p = extra_options::plan_tires(options.config, tire, c, 1u << index);
        assert(p.applies && !p.passthrough && std::string(p.front) == extra_options::kTireNames[index]);
        assert(std::string(p.front) == p.rear);
    }
    auto reject = [&](const extra_options::RaceContext& bad) {
        assert(!extra_options::plan_tires(options.config, extra_options::Tire::Gravel, bad, 0x3e).applies);
    };
    auto bad = c; bad.participant = 1; reject(bad);
    bad = c; bad.player_type = 0; reject(bad);
    bad = c; bad.players = 2; reject(bad);
    bad = c; bad.race_type = 6; reject(bad);
    bad = c; bad.selected_car_id = 20; reject(bad);
    bad = c; bad.already_initialized = true; reject(bad);
    bad = c; bad.attract = true; reject(bad);
    bad = c; bad.replay = true; reject(bad);
    std::cout << "PASS strict V2 preservation, optional Extra Options config, six source-table-gated tire choices and player-only scope\n";
}
