#include "../../src/native/rmod1/core.hpp"
#include "../../src/native/rmod1/exception_report.hpp"
#include "../../src/native/rmod1/image_mapping.hpp"

#include <iostream>
#include <fstream>
#include <map>
#include <iterator>

using namespace rmod1;

namespace {
int checks = 0;
int failures = 0;

void check(bool condition, const char* name) {
    ++checks;
    if (!condition) {
        ++failures;
        std::cerr << "FAIL " << name << '\n';
    }
}

struct FakeMemory final : ReadOnlyMemory {
    std::map<std::pair<PatchTargetKind, std::string>, std::map<std::uint32_t, std::uint8_t>> bytes;
    bool read(PatchTargetKind kind, const std::string& region, std::uint32_t address,
              std::size_t size, std::vector<std::uint8_t>& output) const override {
        output.clear();
        const auto area = bytes.find({kind, region});
        if (area == bytes.end()) return false;
        for (std::size_t i = 0; i < size; ++i) {
            const auto found = area->second.find(address + static_cast<std::uint32_t>(i));
            if (found == area->second.end()) return false;
            output.push_back(found->second);
        }
        return true;
    }
};

ImageIdentity good_image() {
    return {kRetailSha256, kRetailFileSize, kPe32MachineI386, 0x311000, 0x50000000u, true};
}

PatchBundle one_patch() {
    PatchBundle bundle;
    PatchOperation operation;
    operation.id = "quickrace-count-owner";
    operation.owner = "participant-count";
    operation.semantic = "test-only exact preimage path";
    operation.rva_or_offset = 0x1000;
    operation.expected = {0x8b, 0x45, 0x08};
    operation.replacement = {0x8b, 0x45, 0x0c};
    bundle.operations.push_back(operation);
    return bundle;
}

bool safe_defaults(const Config& config) {
    return !config.randomizer_enabled && config.quick_race == Policy::Stock &&
        config.duplicates_when_needed && !config.opponents_enabled &&
        config.max_opponents == 3 && config.addons == AddonMode::StockOnly &&
        !config.experimental_extended_ai && !config.logging_enabled &&
        std::all_of(config.mode_policies.begin(), config.mode_policies.end(),
                    [](Policy policy) { return policy == Policy::Stock; });
}

void test_config(const std::string& public_ini_path) {
    const std::string valid =
        "[General]\r\nConfigVersion=1\r\n"
        "[Randomizer]\r\nEnabled=true\r\nQuickRace=Full\r\nDuplicates=WhenNeeded\r\n"
        "[Opponents]\r\nEnabled=true\r\nMaxOpponents=7\r\n"
        "[Experimental]\r\nExtendedAI=true\r\n"
        "[Addons]\r\nInclude=Auto\r\n[Logging]\r\nEnabled=false\r\n";
    auto parsed = parse_ini(valid);
    check(parsed.accepted, "valid versioned configuration accepted");
    check(parsed.config.randomizer_enabled && parsed.config.quick_race == Policy::Full, "randomizer settings parsed");
    check(parsed.config.opponents_enabled && parsed.config.max_opponents == 7, "one through seven limit parsed");
    check(parsed.config.experimental_extended_ai, "experimental five-participant option parsed explicitly");
    check(parsed.config.duplicates_when_needed && !parsed.config.logging_enabled, "strict duplicate and logging settings parsed");
    check(parsed.config.addons == AddonMode::RegisteredOnly, "legacy Auto means only a verified registered-entry provider");
    const auto experimental_without_extender = parse_ini(
        "[General]\nConfigVersion=1\n[Experimental]\nExtendedAI=1\n");
    check(!experimental_without_extender.accepted && safe_defaults(experimental_without_extender.config),
          "experimental capacity without the opponent extender fails closed to whole-file defaults");
    const auto experimental_below_four = parse_ini(
        "[General]\nConfigVersion=1\n[Opponents]\nEnabled=1\nMaxOpponents=3\n"
        "[Experimental]\nExtendedAI=1\n");
    check(!experimental_below_four.accepted && safe_defaults(experimental_below_four.config),
          "experimental capacity with MaxOpponents below four is rejected");

    const std::array<const char*, 7> legacy_names{{"Stock", "Full", "T1", "T2", "T3", "Mixed", "Diverse"}};
    const std::array<Policy, 7> expected_policies{{Policy::Stock, Policy::Full, Policy::T1,
        Policy::T2, Policy::T3, Policy::Mixed, Policy::Diverse}};
    for (unsigned id = 0; id <= 6; ++id) {
        const std::string numeric = std::string("[General]\nConfigVersion=1\n[Randomizer]\nEnabled=1\nQuickRace=") +
            std::to_string(id) + "\nDuplicates=0\n[Opponents]\nEnabled=1\nMaxOpponents=7\n[Addons]\nInclude=1\n[Logging]\nEnabled=1\n";
        const auto numeric_result = parse_ini(numeric);
        const std::string legacy = std::string("[General]\nConfigVersion=1\n[Randomizer]\nEnabled=true\nQuickRace=") +
            legacy_names[id] + "\nDuplicates=Never\n[Opponents]\nEnabled=true\nMaxOpponents=7\n[Addons]\nInclude=Auto\n[Logging]\nEnabled=true\n";
        const auto legacy_result = parse_ini(legacy);
        check(numeric_result.accepted && legacy_result.accepted, "numeric and textual policy configuration parses");
        check(numeric_result.config.quick_race == expected_policies[id] &&
              legacy_result.config.quick_race == numeric_result.config.quick_race,
              "numeric and textual QuickRace selectors map to identical policy semantics");
        check(numeric_result.config.randomizer_enabled && numeric_result.config.opponents_enabled &&
              numeric_result.config.logging_enabled && !numeric_result.config.duplicates_when_needed &&
              numeric_result.config.addons == AddonMode::RegisteredOnly,
              "numeric Boolean, Duplicates and Addons values map to their documented semantics");
    }
    const auto omitted = parse_ini("[General]\nConfigVersion=1\n");
    check(omitted.accepted && safe_defaults(omitted.config), "omitted settings use safe stock defaults");

    const std::array<Policy, 7> v2_expected{{Policy::Stock, Policy::T1, Policy::T2,
        Policy::T3, Policy::Full, Policy::Mixed, Policy::Diverse}};
    for (unsigned id = 0; id <= 6; ++id) {
        const std::string v2 = std::string("[General]\nConfigVersion=2\n[Randomizer]\n") +
            "QuickRace=" + std::to_string(id) + "\nRallyeCup=" + std::to_string(id) +
            "\nMasterRallye=" + std::to_string(id) + "\nInvitation=" + std::to_string(id) +
            "\nChallenge=" + std::to_string(id) + "\nDuplicates=1\n[Opponents]\nMaxOpponents=7\n" +
            "[Addons]\nInclude=0\n[Logging]\nEnabled=1\n";
        const auto parsed_v2 = parse_ini(v2);
        check(parsed_v2.accepted, "complete ConfigVersion=2 snapshot accepted");
        check(std::all_of(parsed_v2.config.mode_policies.begin(), parsed_v2.config.mode_policies.end(),
                          [&](Policy policy) { return policy == v2_expected[id]; }),
              "ConfigVersion=2 numeric policy ordering is independent from V1");
        check(parsed_v2.config.config_version == 2 && parsed_v2.config.max_opponents == 7 &&
              parsed_v2.config.experimental_extended_ai && parsed_v2.config.opponents_enabled,
              "V2 derives extension from MaxOpponents without hidden enable switches");
    }
    const auto v2_t1_full = parse_ini(
        "[General]\nConfigVersion=2\n[Randomizer]\nQuickRace=1\nRallyeCup=4\n"
        "MasterRallye=0\nInvitation=0\nChallenge=0\nDuplicates=WhenNeeded\n"
        "[Opponents]\nMaxOpponents=3\n[Addons]\nInclude=0\n[Logging]\nEnabled=0\n");
    check(v2_t1_full.accepted && v2_t1_full.config.mode_policies[0] == Policy::T1 &&
          v2_t1_full.config.mode_policies[1] == Policy::Full,
          "V2 interprets numeric 1 as T1 and numeric 4 as Full");
    check(!config_requests_opponent_extension(v2_t1_full.config) &&
          config_needs_randomizer_hooks(v2_t1_full.config),
          "V2 randomizer callbacks remain installed with Stock policies for live edits");
    const auto v2_four = parse_ini(
        "[General]\nConfigVersion=2\n[Randomizer]\nQuickRace=0\nRallyeCup=0\n"
        "MasterRallye=0\nInvitation=0\nChallenge=0\nDuplicates=1\n"
        "[Opponents]\nMaxOpponents=4\n[Addons]\nInclude=0\n[Logging]\nEnabled=0\n");
    check(v2_four.accepted && config_requests_opponent_extension(v2_four.config) &&
          config_allows_extended_ai(v2_four.config) &&
          plan_quick_race(2, 4, true, v2_four.config).allowed,
          "V2 MaxOpponents=4 enables bounded Quick Race extension without a hidden opt-in");

    const std::vector<std::string> invalid_inputs = {
            "[General]\nConfigVersion=2\n",
            "[General]\nConfigVersion=2\n[Randomizer]\nEnabled=1\n",
            "[General]\nConfigVersion=2\n[Experimental]\nExtendedAI=1\n",
            "[General]\nConfigVersion=2\n[Randomizer]\nQuickRace=1\n",
            "[General]\nConfigVersion=-1\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nMystery=true\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nEnabled=true\nEnabled=false\n",
            "[General]\nConfigVersion=1\n[General]\n",
            "[General]\nConfigVersion=1\n[Opponents]\nMaxOpponents=8\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nQuickRace=-1\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nQuickRace=7\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nDuplicates=2\n",
            "[General]\nConfigVersion=1\n[Addons]\nInclude=2\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nEnabled=1\nDuplicates=0\n",
            "[General]\nConfigVersion=1\n[Opponents]\nEnabled=2\n",
            "[General]\nConfigVersion=1\n[Logging]\nEnabled=\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nQuickRace=Stock;unsafe\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nQuickRace=2 ; inline comments are invalid\n",
            "[General]\nConfigVersion=1\n[Addons]\nInclude=ScanDirectories\n",
            "[General]\nConfigVersion=1\n[Experimental]\nExtendedAI=maybe\n",
            "[General]\nConfigVersion=1\n[Unknown]\nEnabled=1\n",
            "[Randomizer]\nEnabled=1\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nEnabled\n",
            std::string("[General]\nConfigVersion=1\n") + char(0)};
    for (const auto& invalid : invalid_inputs) {
        const auto rejected = parse_ini(invalid);
        check(!rejected.accepted && !rejected.config.randomizer_enabled &&
              safe_defaults(rejected.config),
              "malformed input rejects whole file and restores safe defaults");
    }
    check(!parse_ini(std::string(kMaxConfigBytes + 1, 'x')).accepted, "oversized config rejected");
    check(!parse_ini("[General]\nConfigVersion=1\r[Randomizer]\nEnabled=1\n").accepted,
          "bare carriage return rejected");
    const std::string non_ascii = std::string("[General]\nConfigVersion=1\n[Randomizer]\nEnabled=") +
        static_cast<char>(0xff) + "\n";
    check(!parse_ini(non_ascii).accepted,
          "non-ASCII configuration rejected");

    std::ifstream public_ini(public_ini_path, std::ios::binary);
    const std::string public_bytes((std::istreambuf_iterator<char>(public_ini)),
                                   std::istreambuf_iterator<char>());
    const auto shipped = parse_ini(public_bytes);
    check(public_ini.good() || public_ini.eof(), "canonical public INI fixture is readable");
    check(public_bytes.size() <= kMaxConfigBytes && shipped.accepted &&
          shipped.config.config_version == 2 && shipped.config.max_opponents == 5 &&
          std::all_of(shipped.config.mode_policies.begin(), shipped.config.mode_policies.end(),
                      [](Policy policy) { return policy == Policy::Full; }) &&
          shipped.config.addons == AddonMode::StockOnly && !shipped.config.logging_enabled,
          "actual public release INI parses to the documented Full/five-AI stock-addon configuration");
}

void test_vehicle_pools_and_selection() {
    const auto pool = eligible_vehicles(GameMode::QuickRace);
    check(pool.size() == 21, "stock core pool is IDs zero through twenty");
    check(std::none_of(pool.begin(), pool.end(), [](const Vehicle& v) { return v.physical_id == 25; }), "incomplete Trooper ID25 excluded");
    check(std::none_of(pool.begin(), pool.end(), [](const Vehicle& v) { return v.physical_id >= 26; }), "standalone pool has no addon discovery");
    const auto reward_pool = eligible_vehicles(GameMode::QuickRace, 0x0f);
    check(std::count_if(reward_pool.begin(), reward_pool.end(), [](const Vehicle& v) { return v.physical_id >= 21 && v.physical_id <= 24; }) == 4,
          "T3 rewards require their audited unlock bits");
    const auto invitation_pool = eligible_vehicles(GameMode::Invitation, 0x0f);
    check(invitation_pool.size() == 21 &&
          std::none_of(invitation_pool.begin(), invitation_pool.end(),
                       [](const Vehicle& v) { return v.physical_id >= 21; }),
          "Invitation keeps its ordinary stock pool and excludes T3 bonus/progression entries");

    RegisteredAddon unverified{27, 1, false, true, true, true};
    RegisteredAddon verified{27, 1, true, true, true, true};
    check(eligible_vehicles(GameMode::QuickRace, 0, {unverified}, AddonMode::RegisteredOnly).size() == 21, "addon directory/manifest alone cannot register an ID");
    check(eligible_vehicles(GameMode::QuickRace, 0, {verified}, AddonMode::StockOnly).size() == 21, "Stock-only excludes even supplied addon registrations");
    check(eligible_vehicles(GameMode::QuickRace, 0, {verified}, AddonMode::RegisteredOnly).size() == 22, "Auto includes only process-registered materializable addon entries");
    RegisteredAddon sdk_t2{31,1,true,true,true,true,7};
    RegisteredAddon sdk_t3{32,2,true,true,true,true,15};
    check(eligible_vehicles(GameMode::RallyeCup,0,{sdk_t2,sdk_t3},AddonMode::RegisteredOnly).size()==23,"SDK Cup mask preserves registered addons");
    check(eligible_vehicles(GameMode::MasterRallye,0,{sdk_t2,sdk_t3},AddonMode::RegisteredOnly).size()==23,"SDK Master Rallye mask preserves registered addons");
    check(eligible_vehicles(GameMode::Invitation,0,{sdk_t2,sdk_t3},AddonMode::RegisteredOnly).size()==22,"Invitation admits only qualified T3 addon");
    check(eligible_vehicles(GameMode::Challenge,0,{sdk_t2,sdk_t3},AddonMode::RegisteredOnly).size()==21,"authored Challenge exclusion retained");

    const auto t1 = eligible_vehicles(GameMode::QuickRace);
    std::vector<int> prior;
    std::vector<int> selected;
    for (unsigned i = 0; i < 7; ++i) {
        auto result = choose_vehicle(Policy::T1, true, 7, 0, 0, t1, prior, nullptr,
                                     [](int) { return 0; });
        check(result.kind == SelectionKind::SelectedId && result.class_id == 0, "T1 restricted choice remains T1");
        prior.push_back(result.physical_id);
        selected.push_back(result.physical_id);
    }
    const std::set<int> unique(selected.begin(), selected.end());
    check(unique.size() == 6, "seven T1 AI prefer all six non-human T1 IDs before one repeat");
    check(std::none_of(selected.begin(), selected.end(), [](int id) { return id == 0; }), "human ID excluded when other T1 IDs exist");

    const auto disabled = choose_vehicle(Policy::Full, false, 3, 1, 7, t1, {}, nullptr,
                                         [](int) { return 0; });
    check(disabled.kind == SelectionKind::NativeStock, "randomizer disabled preserves native selection");
    const auto extended_stock = choose_vehicle(Policy::Full, false, 4, 0, 0, t1, {}, nullptr,
                                               [](int) { return 0; });
    check(extended_stock.kind == SelectionKind::SelectedId && extended_stock.class_id == 0,
          "opponent extension remains stock-class-compatible when randomizer is off");

    const auto all = eligible_vehicles(GameMode::QuickRace, 0x0f);
    auto full = choose_vehicle(Policy::Full, true, 3, 0, 0, all, {}, nullptr,
                               [](int upper) { return upper - 1; });
    check(full.kind == SelectionKind::SelectedId && full.physical_id != 0,
          "Full samples the verified union and excludes human ID when feasible");
    auto full_class = choose_class(Policy::Full, true, 3, 0, 0, all, {}, nullptr,
                                   [](int upper) { return upper - 1; });
    check(full_class.kind == ClassSelectionKind::SelectedClass && full_class.class_id == full.class_id,
          "class-only native seam shares Full union eligibility with physical selector semantics");
    auto mixed = choose_vehicle(Policy::Mixed, true, 3, 0, 0, all, {}, nullptr,
                                [](int) { return 1; });
    check(mixed.kind == SelectionKind::SelectedId && mixed.class_id == 1,
          "Mixed chooses class before physical ID");
    auto mixed_class = choose_class(Policy::Mixed, true, 3, 0, 0, all, {}, nullptr,
                                    [](int) { return 1; });
    check(mixed_class.kind == ClassSelectionKind::SelectedClass && mixed_class.class_id == mixed.class_id,
          "class-only native seam retains Mixed class-first policy");
    ClassCycle cycle;
    check(cycle.begin(0x7, [](int) { return 0; }), "Diverse class cycle initializes");
    std::set<int> classes;
    for (int i = 0; i < 3; ++i) {
        auto diverse = choose_vehicle(Policy::Diverse, true, 3, 0, 0, all, {}, &cycle,
                                      [](int) { return 0; });
        check(diverse.kind == SelectionKind::SelectedId, "Diverse selects a registered vehicle");
        classes.insert(diverse.class_id);
    }
    check(classes.size() == 3, "Diverse covers all eligible classes before cycling");
    ClassCycle class_cycle;
    check(class_cycle.begin(0x7, [](int upper) { return upper - 1; }), "class-only Diverse cycle initializes");
    auto diverse_class = choose_class(Policy::Diverse, true, 3, 0, 0, all, {}, &class_cycle,
                                      [](int) { return 0; });
    check(diverse_class.kind == ClassSelectionKind::SelectedClass && diverse_class.class_id == 0,
          "class-only native seam consumes the shared Diverse cycle");
    std::vector<int> all_t1_used = {1, 2, 3, 4, 5, 6};
    const std::vector<Vehicle> stock_t1 = {{0,0,false},{1,0,false},{2,0,false},{3,0,false},
                                           {4,0,false},{5,0,false},{6,0,false}};
    auto repeated_class = choose_class(Policy::T1, true, 7, 0, 0, stock_t1, all_t1_used, nullptr,
                                       [](int) { return 0; });
    check(repeated_class.kind == ClassSelectionKind::SelectedClass && repeated_class.class_id == 0 &&
          repeated_class.duplicates_needed && repeated_class.reason.find("exhausted") != std::string::npos,
          "class-only selector signals the native repeat path when eligible IDs are exhausted");
    check(choose_class(Policy::T1, true, 7, 0, 0, stock_t1, all_t1_used, nullptr,
                       [](int) { return 0; }, false).kind == ClassSelectionKind::Refused,
          "Duplicates=Never refuses once all eligible class IDs are consumed");
    check(choose_vehicle(Policy::T1, true, 7, 0, 0, stock_t1, all_t1_used, nullptr,
                         [](int) { return 0; }, false).kind == SelectionKind::Refused,
          "physical selector policy refuses roster exhaustion when duplicates are disabled");
    const std::vector<Vehicle> only_t1 = {{0, 0, false}, {1, 0, false}};
    check(choose_vehicle(Policy::T2, true, 1, 0, 0, only_t1, {}, nullptr,
                         [](int) { return 0; }).kind == SelectionKind::Refused,
          "empty restricted pool fails closed");
    auto t2 = choose_vehicle(Policy::T2, true, 1, 0, 0, all, {}, nullptr,
                             [](int) { return 0; });
    auto t3 = choose_vehicle(Policy::T3, true, 1, 0, 0, all, {}, nullptr,
                             [](int) { return 0; });
    check(t2.kind == SelectionKind::SelectedId && t2.class_id == 1, "T2 policy returns a T2 vehicle for a T1 human");
    check(t3.kind == SelectionKind::SelectedId && t3.class_id == 2, "T3 policy returns a T3 vehicle for a T1 human");

    for (unsigned count = 1; count <= kMaximumAi; ++count) {
        auto t2_class = choose_class(Policy::T2, true, count, 0, 0, all, {}, nullptr,
                                     [](int) { return 0; });
        check(t2_class.kind == ClassSelectionKind::SelectedClass && t2_class.class_id == 1,
              "class-restricted T2 selection remains independent of count and player class");
    }
    for (unsigned count = 4; count <= kMaximumAi; ++count) {
        for (Policy policy : {Policy::Stock, Policy::Full, Policy::T1, Policy::T2,
                              Policy::T3, Policy::Mixed, Policy::Diverse}) {
            ClassCycle extended_cycle;
            if (policy == Policy::Diverse)
                check(extended_cycle.begin(0x7, [](int) { return 0; }),
                      "extended Diverse cycle initializes");
            auto selection = choose_class(policy, true, count, 0, 0, all, {},
                                          policy == Policy::Diverse ? &extended_cycle : nullptr,
                                          [](int) { return 0; });
            check(selection.kind == ClassSelectionKind::SelectedClass,
                  "all Randomizer policies produce an extended-count class decision");
            const int expected = policy_class(policy);
            if (expected >= 0)
                check(selection.class_id == expected,
                      "extended fixed-class policy remains class restricted");
        }
    }
    std::vector<int> t1_used = {1,2,3,4,5,6};
    auto refill_class = choose_class(Policy::T1, true, 7, 0, 0, stock_t1, t1_used, nullptr,
                                     [](int) { return 0; }, true);
    check(refill_class.kind == ClassSelectionKind::SelectedClass && refill_class.class_id == 0 &&
          refill_class.reason.find("native participant chooser repeat") != std::string::npos,
          "WhenNeeded keeps the restricted class after unique IDs are exhausted for native pool refill");

    // Exercise the Quick Race class seam and the physical selector together:
    // six alternatives are consumed before the seventh T1/T2 AI is allowed
    // to reuse a valid model. Repeated CarIDs are values in distinct
    // participant records, not aliases for a CarN object or AI controller.
    struct ParticipantFixture {
        unsigned slot;
        int physical_id;
        int class_id;
        unsigned driver_id;
        unsigned controller_cookie;
    };
    const auto verify_repeated_class = [&](Policy policy, int class_id, int player_id,
                                           const std::vector<Vehicle>& class_pool) {
        std::vector<int> prior_ids;
        std::vector<ParticipantFixture> participants;
        for (unsigned slot = 1; slot <= 7; ++slot) {
            const auto class_choice = choose_class(policy, true, 7, class_id, player_id,
                class_pool, prior_ids, nullptr, [](int) { return 0; }, true);
            check(class_choice.kind == ClassSelectionKind::SelectedClass &&
                  class_choice.class_id == class_id,
                  "duplicate fallback preserves strict T1/T2 class eligibility");
            check(class_choice.duplicates_needed == (slot == 7),
                  "duplicate marker is emitted only after every eligible physical ID was used");
            const auto vehicle_choice = choose_vehicle(policy, true, 7, class_id, player_id,
                class_pool, prior_ids, nullptr, [](int) { return 0; }, true);
            check(vehicle_choice.kind == SelectionKind::SelectedId &&
                  vehicle_choice.class_id == class_id,
                  "native-selector policy model returns a valid same-class physical ID");
            prior_ids.push_back(vehicle_choice.physical_id);
            participants.push_back({slot, vehicle_choice.physical_id, class_id,
                                    100u + slot, 0xA000u + slot});
        }
        std::set<int> physical_ids;
        for (const auto& participant : participants) physical_ids.insert(participant.physical_id);
        check(physical_ids.size() == 6 && participants.front().physical_id == participants.back().physical_id,
              "seventh same-class AI may repeat a valid physical CarID after six unique IDs");
        check(participants.size() == 7 &&
              std::set<unsigned>{participants[0].slot, participants[6].slot}.size() == 2 &&
              participants[0].driver_id != participants[6].driver_id &&
              participants[0].controller_cookie != participants[6].controller_cookie,
              "repeated CarID remains in independent participant, DriverID and controller records");
    };
    std::vector<Vehicle> stock_t2;
    for (int id = 7; id <= 13; ++id) stock_t2.push_back({id, 1, false});
    verify_repeated_class(Policy::T1, 0, 0, stock_t1);
    verify_repeated_class(Policy::T2, 1, 7, stock_t2);
}

#if defined(RMOD3_G2_PLAYER_OVERRIDE)
void test_g2_player_vehicle_policy() {
    const auto stock_pool = eligible_vehicles(GameMode::QuickRace);
    const std::string common =
        "[General]\nConfigVersion=3\n[Randomizer]\nQuickRace=4\nRallyeCup=0\n"
        "MasterRallye=0\nInvitation=0\nChallenge=0\nDuplicates=1\n"
        "[Opponents]\nMaxOpponents=3\n[Addons]\nInclude=0\n[Logging]\nEnabled=0\n";
    const auto make_config = [&](const std::string& player) {
        return parse_ini(common + "[Player]\n" + player).config;
    };
    const auto v3 = parse_ini(common + "[Player]\nMode=2\nForcedCarID=9\nRandomPolicy=1\n");
    check(v3.accepted && v3.config.config_version == 3 &&
          v3.config.player_vehicle_mode == PlayerVehicleMode::Random &&
          v3.config.forced_player_car_id == 9 &&
          v3.config.player_random_policy == Policy::T1,
          "ConfigVersion=3 parses player mode and V2-compatible policy IDs");
    const auto v2 = parse_ini(
        "[General]\nConfigVersion=2\n[Randomizer]\nQuickRace=4\nRallyeCup=0\n"
        "MasterRallye=0\nInvitation=0\nChallenge=0\nDuplicates=1\n"
        "[Opponents]\nMaxOpponents=3\n[Addons]\nInclude=0\n[Logging]\nEnabled=0\n");
    check(v2.accepted && v2.config.config_version == 2 &&
          v2.config.mode_policies[0] == Policy::Full,
          "G2 build preserves ConfigVersion=2 numeric Full=4 semantics");
    check(!parse_ini(common).accepted,
          "ConfigVersion=3 fails closed when the required Player section is missing");
    check(!parse_ini(common + "[Player]\nMode=1\nForcedCarID=25\nRandomPolicy=4\n").accepted,
          "ConfigVersion=3 rejects reserved, non-stock ForcedCarID values");
    check(!parse_ini(common + "[Player]\nMode=3\nForcedCarID=0\nRandomPolicy=4\n").accepted,
          "ConfigVersion=3 rejects unknown player modes");

    unsigned stock_draws = 0;
    auto stock_cfg = make_config("Mode=0\nForcedCarID=0\nRandomPolicy=4\n");
    const auto stock = choose_player_vehicle(stock_cfg, 8, stock_pool,
        [&](int) { ++stock_draws; return 0; });
    check(stock.kind == PlayerVehicleDecisionKind::PreserveNative && stock.physical_id == 8 &&
          stock.class_id == 1 && stock_draws == 0,
          "Stock player mode preserves native CarID and never draws");

    auto forced_cfg = make_config("Mode=1\nForcedCarID=3\nRandomPolicy=4\n");
    const auto forced = choose_player_vehicle(forced_cfg, 8, stock_pool,
        [&](int) { return 0; });
    check(forced.kind == PlayerVehicleDecisionKind::Selected &&
          forced.physical_id == 3 && forced.class_id == 0,
          "Forced mode selects the configured physical CarID independent of original class");
    forced_cfg.forced_player_car_id = 25;
    const auto unavailable = choose_player_vehicle(forced_cfg, 8, stock_pool,
        [&](int) { return 0; });
    check(unavailable.kind == PlayerVehicleDecisionKind::Refused && unavailable.physical_id == 8,
          "unavailable/non-stock forced identity refuses to native selection");

    const std::array<std::pair<unsigned, Policy>, 7> policy_cases{{
        {0, Policy::Stock}, {1, Policy::T1}, {2, Policy::T2}, {3, Policy::T3},
        {4, Policy::Full}, {5, Policy::Mixed}, {6, Policy::Diverse}}};
    for (const auto& item : policy_cases) {
        auto config = make_config("Mode=2\nForcedCarID=0\nRandomPolicy=" + std::to_string(item.first) + "\n");
        unsigned draws = 0;
        const auto decision = choose_player_vehicle(config, 8, stock_pool,
            [&](int upper) { ++draws; return upper > 0 ? 0 : -1; });
        if (item.second == Policy::Stock) {
            check(decision.kind == PlayerVehicleDecisionKind::PreserveNative &&
                  decision.physical_id == 8 && draws == 0,
                  "RandomPolicy=Stock leaves the native player car unchanged");
        } else {
            check(decision.kind == PlayerVehicleDecisionKind::Selected &&
                  decision.physical_id >= 0 && decision.physical_id <= 24 &&
                  decision.class_id == stock_class_for_physical_id(decision.physical_id),
                  "random policy selects a valid stock physical identity");
            if (item.second == Policy::T1 || item.second == Policy::T2 || item.second == Policy::T3)
                check(decision.class_id == policy_class(item.second),
                      "T1/T2/T3 player restriction remains strict");
        }
    }

    auto player_t1 = make_config("Mode=2\nForcedCarID=0\nRandomPolicy=1\n");
    check(policy_for_mode(player_t1, GameMode::QuickRace) == Policy::Full,
          "player random policy is independent from the Quick Race AI policy");

    PreparedPlayerVehicle prepared;
    unsigned random_draws = 0;
    const auto first = prepare_player_vehicle(prepared, player_t1, GameMode::QuickRace, 0, 8,
        stock_pool, [&](int upper) { ++random_draws; return upper > 0 ? 0 : -1; });
    const int entry_id = first.physical_id;
    const unsigned entry_generation = prepared.generation;
    auto edited = make_config("Mode=1\nForcedCarID=12\nRandomPolicy=4\n");
    const int setup_id = consume_prepared_player_vehicle(prepared, GameMode::QuickRace, 0, 8);
    const int restart_id = consume_prepared_player_vehicle(prepared, GameMode::QuickRace, 0, setup_id);
    check(first.kind == PlayerVehicleDecisionKind::Selected && setup_id == entry_id &&
          restart_id == entry_id && prepared.generation == entry_generation && random_draws == 1 &&
          edited.forced_player_car_id == 12,
          "Start, restart and live INI edits retain one prepared identity without reroll");

    const auto reentry = prepare_player_vehicle(prepared, edited, GameMode::QuickRace, 0,
        entry_id, stock_pool, [&](int) { ++random_draws; return 0; });
    check(reentry.kind == PlayerVehicleDecisionKind::Selected && reentry.physical_id == 12 &&
          prepared.generation == entry_generation + 1,
          "new Vehicle Select generation applies the latest accepted configuration");

    const auto wrong_slot = prepare_player_vehicle(prepared, player_t1, GameMode::QuickRace, 1, 7,
        stock_pool, [&](int) { ++random_draws; return 0; });
    check(wrong_slot.kind == PlayerVehicleDecisionKind::PreserveNative &&
          wrong_slot.physical_id == 7 && wrong_slot.class_id == 1,
          "unsupported second frontend player remains native and independent");
}
#endif

void test_participant_and_grid_gate() {
    Config config;
    config.opponents_enabled = true;
    config.max_opponents = 7;
    config.experimental_extended_ai = true;
    for (unsigned selected = 1; selected <= 3; ++selected) {
        const auto plan = plan_quick_race(2, selected, false, config);
        check(plan.allowed && !plan.use_extension && plan.total == selected + 1,
              "native one-to-three Quick Race counts remain unchanged; actual topology is deferred to Race state");
    }
    for (unsigned selected = 4; selected <= 7; ++selected) {
        const auto extended = plan_quick_race(2, selected, false, config);
        check(extended.allowed && extended.use_extension && extended.total == selected + 1 &&
              extended.total <= kMaximumTotalCars,
              "experimental extended selection reaches its bounded native participant count");
    }
    const auto split_three = plan_quick_race(2, 3, true, config);
    check(split_three.allowed && split_three.total == 4 && split_three.humans == 0 && split_three.ai == 0,
          "raw SplitScreen is diagnostic only before native Race topology exists");
    const auto split_four = plan_quick_race(2, 4, true, config);
    check(split_four.allowed && split_four.total == 5,
          "previous v11 four-AI topology is not vetoed by raw SplitScreen=1");
    const auto raw_split_five = plan_quick_race(2, 5, true, config);
    check(raw_split_five.allowed && raw_split_five.total == 6 &&
          raw_split_five.reason.find("diagnostic only") != std::string::npos,
          "raw SplitScreen=1 does not veto five AI before authoritative Race topology exists");
    const auto raw_split_seven = plan_quick_race(2, 7, true, config);
    check(raw_split_seven.allowed && raw_split_seven.total == 8,
          "raw SplitScreen=1 does not veto seven AI; total remains bounded to eight");
    const auto actual_two_human_race = analyze_native_roster(6, 2, {
        {1, 7, 1}, {1, 8, 1}, {2, 0, 0}, {2, 9, 1}, {2, 14, 2}, {2, 10, 1}});
    check(!experimental_extended_roster_matches(actual_two_human_race, raw_split_five, 5),
          "authoritative two-human Race roster fails the one-human v13 qualification oracle");
    check(!plan_quick_race(2, 0, false, config).allowed,
          "zero selected count is rejected");
    check(!plan_quick_race(2, 8, false, config).allowed &&
          !plan_quick_race(2, 9, false, config).allowed,
          "no selected count may address participant Car8 or exceed the seven-AI UI");
    const auto non_quick_race = plan_quick_race(5, 7, false, config);
    check(non_quick_race.allowed && !non_quick_race.use_extension && non_quick_race.total == 0 &&
          non_quick_race.reason == "Native mode passthrough; no Quick Race opponent extension applied.",
          "non-mode-2 native Start paths pass through without applying stale Quick Race counts");
    Config disabled;
    disabled.opponents_enabled = true;
    disabled.max_opponents = 7;
    check(!plan_quick_race(2, 4, false, disabled).allowed,
          "extended AI is disabled by default without Experimental.ExtendedAI");
    config.experimental_extended_ai = false;
    check(!plan_quick_race(2, 4, false, config).allowed,
          "the four-AI path requires explicit experimental opt-in");
    config.experimental_extended_ai = true;
    config.max_opponents = 3;
    check(!plan_quick_race(2, 4, false, config).allowed,
          "extended selection cannot exceed configured MaxOpponents");
    config.max_opponents = 5;
    check(plan_quick_race(2, 5, false, config).allowed &&
          !plan_quick_race(2, 6, false, config).allowed,
          "progressive MaxOpponents gate admits only the currently qualified test ceiling");

    config.max_opponents = 7;
    for (unsigned ai = 4; ai <= 7; ++ai) {
        const auto decision = plan_quick_race(2, ai, false, config);
        std::vector<NativeParticipantRecord> records;
        records.push_back({1, 0, 0});
        for (unsigned slot = 0; slot < ai; ++slot) {
            const int id = slot < 6 ? static_cast<int>(slot + 1) : 1;
            records.push_back({2, id, 0});
        }
        const auto roster = analyze_native_roster(static_cast<int>(ai + 1), 1, records);
        check(experimental_extended_roster_matches(roster, decision, ai),
              "extended one-human topology accepts independent slots with a native repeated CarID");
    }
}

void test_native_start_gate_callback_path() {
    Config config;
    config.config_version = 2;
    config.mode_policies[0] = Policy::T1;
    config.opponents_enabled = true;
    config.max_opponents = 7;
    config.experimental_extended_ai = true;

    // These are opaque non-2 sentinels, not claims about Practice, Checkpoint,
    // or any other native mode's numeric identifier. The production exported
    // callback delegates its decision to this same function.
    for (const int opaque_mode : {-1, 0, 1, 3, 4, 5, 6, 8, 42}) {
        const auto result = evaluate_native_start_gate(opaque_mode, 7, true, config);
        check(result.decision.allowed && !result.decision.use_extension &&
              result.selected_count == 0 && result.topology.num_cars == 0 &&
              result.decision.reason == "Native mode passthrough; no Quick Race opponent extension applied.",
              "native Start-gate callback passes through unknown non-mode-2 contexts without reading stale count");
    }

    const auto quick_three = evaluate_native_start_gate(2, 3, false, config);
    check(quick_three.decision.allowed && !quick_three.decision.use_extension &&
          quick_three.selected_count == 3 && quick_three.decision.total == 4,
          "native Start-gate callback preserves stock three-AI Quick Race setup");
    for (int ai = 4; ai <= 7; ++ai) {
        const auto quick_extended = evaluate_native_start_gate(2, ai, false, config);
        check(quick_extended.decision.allowed && quick_extended.decision.use_extension &&
              quick_extended.selected_count == static_cast<unsigned>(ai) &&
              quick_extended.decision.total == static_cast<unsigned>(ai + 1),
              "native Start-gate callback retains configured four-to-seven-AI Quick Race path");
    }
    const auto quick_invalid = evaluate_native_start_gate(2, 8, false, config);
    check(!quick_invalid.decision.allowed && quick_invalid.selected_count == 0,
          "native Start-gate callback rejects a count above the Car0..Car7 limit");

    const auto stock_pool = eligible_vehicles(GameMode::QuickRace);
    check(quick_race_unique_capacity(Policy::T1, 0, 0, stock_pool) == 6 &&
          quick_race_unique_capacity(Policy::T1, 1, 7, stock_pool) == 7 &&
          quick_race_unique_capacity(Policy::T2, 1, 7, stock_pool) == 6 &&
          quick_race_unique_capacity(Policy::T2, 0, 0, stock_pool) == 7,
          "strict T1/T2 capacity accounts for the player only when their physical ID is in the pool");
    config.duplicates_when_needed = false;
    const auto never_t1_same = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 7, false, config).decision, 2, 7, true, false,
        Policy::T1, 0, 0, stock_pool);
    const auto never_t1_outside = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 7, false, config).decision, 2, 7, true, false,
        Policy::T1, 1, 7, stock_pool);
    const auto never_t2_same = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 7, false, config).decision, 2, 7, true, false,
        Policy::T2, 1, 7, stock_pool);
    const auto never_t2_outside = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 7, false, config).decision, 2, 7, true, false,
        Policy::T2, 0, 0, stock_pool);
    check(!never_t1_same.allowed && never_t1_same.reason.find("only 6") != std::string::npos &&
          never_t1_outside.allowed && !never_t2_same.allowed && never_t2_outside.allowed,
          "Duplicates=Never refuses only Quick Races whose requested count exceeds the distinct policy pool");
    const auto never_six_t1 = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 6, false, config).decision, 2, 6, true, false,
        Policy::T1, 0, 0, stock_pool);
    const auto never_full_seven = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 7, false, config).decision, 2, 7, true, false,
        Policy::Full, 0, 0, stock_pool);
    const auto never_non_quick = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(5, 7, false, config).decision, 5, 7, true, false,
        Policy::T1, 0, 0, stock_pool);
    const auto never_without_selector = enforce_quickrace_duplicate_capacity(
        evaluate_native_start_gate(2, 7, false, config).decision, 2, 7, false, false,
        Policy::T1, 0, 0, stock_pool);
    check(never_six_t1.allowed && never_full_seven.allowed && never_non_quick.allowed &&
          !never_non_quick.use_extension && never_without_selector.allowed,
          "Never allows sufficient pools and does not guard native modes or an inactive selector");

    config.max_opponents = 3;
    const auto native_ceiling = evaluate_native_start_gate(2, 3, false, config);
    const auto over_native_ceiling = evaluate_native_start_gate(2, 4, false, config);
    check(native_ceiling.decision.allowed && !native_ceiling.decision.use_extension &&
          !over_native_ceiling.decision.allowed,
          "MaxOpponents=3 keeps stock selection and blocks a count above its configured ceiling");
}
void test_exception_report_layout() {
    check(sizeof(ExceptionRecordV1) == 436, "AV diagnostic wire record remains fixed-size");
    check(offsetof(ExceptionRecordV1, eip) == 104, "AV diagnostic context offset remains stable");
    check(offsetof(ExceptionRecordV1, frames) == 308, "AV diagnostic EBP-frame offset remains stable");
    check(std::string(kExceptionRecordMagicV1, sizeof(kExceptionRecordMagicV1)) == "RMCRASH1",
          "AV diagnostic signature is stable");
    check(static_cast<std::uint32_t>(StartPhaseV1::NativeSetupEntered) == 4u &&
          static_cast<std::uint32_t>(StartPhaseV1::PreparedValidationEntered) == 6u,
          "start phase identifiers remain decodable");
}

void test_runtime_operation_feature_isolation() {
    constexpr std::uint32_t bootstrap = 4;
    const std::array<std::pair<const char*, std::uint32_t>, 3> operations{{
        {"bootstrap", bootstrap}, {"randomizer", 1}, {"opponents", 2},
    }};
    const auto selected = [&](std::uint32_t requested, bool diagnostics) {
        std::vector<std::string> ids;
        for (const auto& operation : operations)
            if (runtime_operation_selected(operation.second, requested, bootstrap, diagnostics))
                ids.emplace_back(operation.first);
        return ids;
    };
    check(selected(0, false).empty(), "both gameplay features off and diagnostics off install no code");
    check(selected(0, true) == std::vector<std::string>{"bootstrap"},
          "diagnostics-only mode installs bootstrap without gameplay hooks");
    check(selected(1, false) == (std::vector<std::string>{"bootstrap", "randomizer"}),
          "randomizer-only mode excludes opponent UI and start hooks");
    check(selected(2, false) == (std::vector<std::string>{"bootstrap", "opponents"}),
          "opponent-only mode excludes randomizer selectors");
    check(selected(3, false) == (std::vector<std::string>{"bootstrap", "randomizer", "opponents"}),
          "combined mode selects both independent feature sets");
}

void test_challenge_preview_identity_lifecycle() {
    ChallengeSelection selection;
    check(!selection.ready && selection.consume(2, 3, 8) == -1,
          "unprepared Challenge cannot replace the authored opponent at race construction");
    selection.prepare(2, 3, 8, 41, Policy::T2, "config-before-edit");
    selection.selected_opponent_id = 12;
    check(selection.preview_identity() == 12 && selection.consume(2, 3, 8) == 12,
          "Challenge preview and race consume share one prepared absolute physical ID");

    // A later INI edit is intentionally not an input to this prepared state.
    const unsigned frozen_generation = selection.generation_id;
    const std::string frozen_hash = selection.config_hash;
    check(selection.matches(2, 3, 8) && selection.consume(2, 3, 8) == 12 &&
          selection.generation_id == frozen_generation && selection.config_hash == frozen_hash,
          "redraw and Start preserve the visible Challenge identity across a live policy edit");
    check(!selection.matches(3, 3, 8) && !selection.matches(2, 4, 8) &&
          !selection.matches(2, 3, 9) && selection.consume(3, 3, 8) == -1,
          "event or authored participant change cannot consume a stale Challenge preview");

    selection.clear();
    check(!selection.ready && selection.preview_identity() == -1,
          "Back/reentry reset invalidates the prior preview cache");
    selection.prepare(3, 4, 9, 42, Policy::Stock, "new-stock-snapshot");
    check(selection.preview_identity() == 9 && selection.consume(3, 4, 9) == -1,
          "Stock Challenge keeps authored preview identity and native authored race matchup");
}

void test_observed_native_roster_gate() {
    const auto five_topology = derive_quick_race_topology(2, 4, false);
    Config config;
    config.opponents_enabled = true;
    config.max_opponents = 7;
    config.experimental_extended_ai = true;
    const auto four_ai_decision = plan_quick_race(2, 4, false, config);
    const std::vector<NativeParticipantRecord> mixed_class_roster{
        {1, 7, 1}, {2, 1, 0}, {2, 8, 1}, {2, 14, 2}, {2, 9, 1}};
    const auto valid = analyze_native_roster(5, 1, mixed_class_roster);
    check(native_roster_matches_topology(valid, five_topology) &&
          experimental_extended_roster_matches(valid, four_ai_decision, 4),
          "post-setup oracle accepts actual NumCars5/NumPlayers1 and four class-correct AI without T1/player-ID0 restrictions");
    const auto two_human_three_ai = analyze_native_roster(5, 2, {
        {1, 7, 1}, {1, 8, 1}, {2, 0, 0}, {2, 9, 1}, {2, 14, 2}});
    check(native_roster_matches_topology(two_human_three_ai, five_topology) &&
          !experimental_extended_roster_matches(two_human_three_ai, four_ai_decision, 4),
          "authoritative two-human Race roster fails the one-human experimental qualification oracle");
    const std::vector<NativeParticipantRecord> repeated_roster{
        {1, 7, 1}, {2, 8, 1}, {2, 8, 1}, {2, 9, 1}, {2, 10, 1}};
    const auto repeated = analyze_native_roster(5, 1, repeated_roster);
    check(native_roster_matches_topology(repeated, five_topology) && !repeated.unique_ai_ids,
          "WhenNeeded can accept distinct AI participant slots with repeated physical CarIDs");
    auto wrong_count = analyze_native_roster(4, 1, {
        {1, 7, 1}, {2, 8, 1}, {2, 9, 1}, {2, 10, 1}});
    check(!native_roster_matches_topology(wrong_count, five_topology),
          "actual Race/NumCars mismatch rejects before transitioning to race");
    auto wrong_players = analyze_native_roster(5, 2, mixed_class_roster);
    check(!native_roster_matches_topology(wrong_players, five_topology),
          "actual Race/NumPlayers mismatch rejects the assumed topology");
    auto invalid_type = analyze_native_roster(5, 1, {
        {1, 7, 1}, {2, 1, 0}, {0, 8, 1}, {2, 14, 2}, {2, 9, 1}});
    check(!native_roster_matches_topology(invalid_type, five_topology),
          "invalid PlayerType in an active CarN slot is rejected");
    auto wrong_class = analyze_native_roster(5, 1, {
        {1, 7, 0}, {2, 1, 0}, {2, 8, 1}, {2, 14, 2}, {2, 9, 1}});
    check(!native_roster_matches_topology(wrong_class, five_topology),
          "physical CarID and registered CarClass divergence is rejected");
    auto out_of_bound = analyze_native_roster(9, 1, {});
    check(!out_of_bound.bounds_valid,
          "native Race/NumCars9 is rejected before any Car8 access");
    const auto eight_slots = analyze_native_roster(8, 1, {
        {1, 0, 0}, {2, 1, 0}, {2, 2, 0}, {2, 3, 0},
        {2, 7, 1}, {2, 8, 1}, {2, 14, 2}, {2, 15, 2}});
    check(eight_slots.bounds_valid && eight_slots.participants == 8,
          "bounded roster analyzer represents exactly Car0..Car7 without a ninth record");
}
void test_duplicates_never_roster_gate() {
    check(unique_ai_physical_ids({1, 2, 3}, {0}),
          "Duplicates=Never accepts distinct known AI IDs that exclude the human ID");
    check(!unique_ai_physical_ids({1, 2, 2}, {0}),
          "Duplicates=Never rejects repeated AI physical IDs");
    check(!unique_ai_physical_ids({0, 2}, {0}),
          "Duplicates=Never rejects an AI ID reused from the human participant");
    check(!unique_ai_physical_ids({1, -1}, {0}),
          "Duplicates=Never rejects an unknown AI physical ID");
    check(!unique_ai_physical_ids({1}, {-1}),
          "Duplicates=Never rejects an unknown human identity");
}

PatchOperation feature_operation(const std::string& id, std::uint32_t rva) {
    PatchOperation operation;
    operation.id = id;
    operation.owner = "test-feature-owner";
    operation.semantic = "test-only feature operation";
    operation.rva_or_offset = rva;
    operation.expected = {0x90};
    operation.replacement = {0x91};
    return operation;
}

InstallablePatchPlan feature_plan(std::vector<InstallFeature> features) {
    InstallablePatchPlan plan;
    plan.enabled_features = std::move(features);
    std::uint32_t rva = 0x1100;
    auto bind = [&](InstallFeature feature, const char* role, const char* id) {
        plan.patch_bundle.operations.push_back(feature_operation(id, rva));
        rva += 0x10;
        plan.coverage.push_back({feature, role, id});
    };
    if (std::find(plan.enabled_features.begin(), plan.enabled_features.end(), InstallFeature::Randomizer) != plan.enabled_features.end()) {
        bind(InstallFeature::Randomizer, "shared_semantic_core", "randomizer-core");
        bind(InstallFeature::Randomizer, "quickrace_ai_selection", "randomizer-choice");
    }
    if (std::find(plan.enabled_features.begin(), plan.enabled_features.end(), InstallFeature::OpponentExtender) != plan.enabled_features.end()) {
        bind(InstallFeature::OpponentExtender, "opponent_selector_ui", "opponent-ui");
        bind(InstallFeature::OpponentExtender, "participant_count_publication", "participant-count");
        bind(InstallFeature::OpponentExtender, "participant_setup", "participant-setup");
    }
    return plan;
}

void test_installable_feature_coverage() {
    const auto image = good_image();
    InstallablePatchPlan empty;
    check(!has_error(validate_patch_bundle(image, empty.patch_bundle)),
          "generic zero-operation bundle remains usable for explicit no-op diagnostics");
    check(has_error(validate_installable_patch_plan(image, empty)),
          "empty installable plan is rejected without enabled features or native operations");

    auto randomizer = feature_plan({InstallFeature::Randomizer});
    check(randomizer.patch_bundle.operations.size() == 2 &&
          !has_error(validate_installable_patch_plan(image, randomizer)),
          "Randomizer-only installable plan covers semantic core and Quick Race chooser");

    auto extender = feature_plan({InstallFeature::OpponentExtender});
    check(extender.patch_bundle.operations.size() == 3 &&
          !has_error(validate_installable_patch_plan(image, extender)),
          "Extender-only installable plan covers UI, count publication and participant setup");

    auto combined = feature_plan({InstallFeature::Randomizer, InstallFeature::OpponentExtender});
    check(combined.patch_bundle.operations.size() == 5 &&
          !has_error(validate_installable_patch_plan(image, combined)),
          "combined installable plan independently covers both features");

    auto missing = randomizer;
    missing.coverage.pop_back();
    check(has_error(validate_installable_patch_plan(image, missing)),
          "incomplete feature-to-operation coverage is rejected");
    auto dangling = extender;
    dangling.coverage[0].operation_id = "missing-ui-hook";
    check(has_error(validate_installable_patch_plan(image, dangling)),
          "feature role cannot claim an operation absent from the native bundle");
    auto disabled = randomizer;
    disabled.coverage.push_back({InstallFeature::OpponentExtender, "participant_setup", "randomizer-choice"});
    check(has_error(validate_installable_patch_plan(image, disabled)),
          "coverage cannot smuggle an unenabled feature into an installable plan");
}

void test_identity_and_patch_preflight() {
    auto image = good_image();
    check(!has_error(verify_image_identity(image)), "exact pristine PE32 identity passes");
    image.disk_sha256 = "00";
    check(has_error(verify_image_identity(image)), "wrong executable SHA rejects");
    image = good_image();
    image.pe_machine = 0x8664;
    check(has_error(verify_image_identity(image)), "wrong architecture rejects");
    image = good_image();
    image.mapped_image_matches_disk = false;
    check(has_error(verify_image_identity(image)), "unverified mapped image rejects");
    image = good_image();
    std::uintptr_t address = 0;
    check(rva_to_runtime_address(image, 0x201d00, 6, address) && address == 0x50201d00,
          "RVA resolves through actual mapped base");
    check(!rva_to_runtime_address(image, 0x310ffe, 8, address), "RVA bounds fail closed");

    FakeMemory memory;
    memory.bytes[{PatchTargetKind::ImageRva, ""}][0x1000] = 0x8b;
    memory.bytes[{PatchTargetKind::ImageRva, ""}][0x1001] = 0x45;
    memory.bytes[{PatchTargetKind::ImageRva, ""}][0x1002] = 0x08;
    auto valid = one_patch();
    check(!has_error(validate_patch_bundle(image, valid, &memory)), "exact patch preimage passes read-only preflight");
    const auto prepared = preflight_and_materialize_patch_bundle(image, valid, memory, {});
    check(prepared.accepted && prepared.operations.size() == 1,
          "single preflight entry point validates all preimages before materializing writes");

    auto mismatch = valid;
    mismatch.operations[0].expected[0] = 0x90;
    check(has_error(validate_patch_bundle(image, mismatch, &memory)), "preimage mismatch rejects before writes");
    check(!preflight_and_materialize_patch_bundle(image, mismatch, memory, {}).accepted,
          "preimage mismatch blocks the complete materialized bundle");
    auto overlap = valid;
    auto second = overlap.operations[0];
    second.id = "overlap";
    second.rva_or_offset += 1;
    overlap.operations.push_back(second);
    check(has_error(validate_patch_bundle(image, overlap, &memory)), "overlapping native operations reject");
    auto invalid_rva = valid;
    invalid_rva.operations[0].rva_or_offset = image.mapped_image_size - 1;
    check(has_error(validate_patch_bundle(image, invalid_rva)), "out-of-image RVA rejects");
    auto invalid_region = valid;
    invalid_region.regions.push_back({"code", 64, RegionPermission::ReadWrite, RegionPermission::ReadWrite, true});
    check(has_error(validate_patch_bundle(image, invalid_region)), "writable-executable final region is not accepted");
    auto cycle = valid;
    cycle.operations[0].depends_on = {"other"};
    auto other = cycle.operations[0];
    other.id = "other";
    other.rva_or_offset = 0x1100;
    other.depends_on = {"quickrace-count-owner"};
    cycle.operations.push_back(other);
    check(has_error(validate_patch_bundle(image, cycle)), "cyclic dependencies reject");

    PatchBundle relocated;
    relocated.regions.push_back({"hook-code", 64, RegionPermission::ReadWrite, RegionPermission::ReadExecute, true});
    PatchOperation trampoline;
    trampoline.id = "entry-trampoline";
    trampoline.owner = "quickrace-randomizer";
    trampoline.semantic = "jump to code allocated before process entry";
    trampoline.rva_or_offset = 0x2000;
    trampoline.expected = {0x55, 0x8b, 0xec, 0x83, 0xec};
    trampoline.replacement = {0xe9, 0, 0, 0, 0};
    trampoline.relative32_fixups.push_back({1, 5, PatchTargetKind::AllocatedRegion, "hook-code", 0});
    relocated.operations.push_back(trampoline);
    const auto materialized = materialize_patch_bundle(image, relocated, {{"hook-code", 0x60000000u}});
    check(materialized.accepted && materialized.operations.size() == 1,
          "relative branch materializes against the actual allocated code address");
    if (materialized.accepted) {
        const auto& bytes = materialized.operations[0].bytes;
        const std::uint32_t displacement = static_cast<std::uint32_t>(bytes[1]) |
            (static_cast<std::uint32_t>(bytes[2]) << 8) |
            (static_cast<std::uint32_t>(bytes[3]) << 16) |
            (static_cast<std::uint32_t>(bytes[4]) << 24);
        const auto signed_displacement = static_cast<std::int32_t>(displacement);
        check(materialized.operations[0].address == image.mapped_base + 0x2000 &&
              materialized.operations[0].address + 5 + signed_displacement == 0x60000000,
              "emitted rel32 displacement targets the correct mapped address");
    }
    check(!materialize_patch_bundle(image, relocated, {}).accepted,
          "missing allocation mapping prevents patch materialization");
    check(!materialize_patch_bundle(image, relocated, {{"hook-code", image.mapped_base + 0x1000}}).accepted,
          "allocation overlapping the mapped image is rejected");
}

struct MockMappedImage {
    rmod1::image_mapping::Layout layout;
    std::vector<std::uint8_t> source;
    std::vector<std::uint8_t> mapped;
    std::vector<rmod1::image_mapping::Region> regions;

    bool query(std::uintptr_t address, rmod1::image_mapping::Region& output) const {
        for (const auto& region : regions) {
            if (address >= region.base_address && address - region.base_address < region.size) {
                output = region;
                return true;
            }
        }
        return false;
    }

    bool read(std::uintptr_t address, std::uint8_t* output, std::size_t size) const {
        if (address < layout.image_base) return false;
        const auto offset = address - layout.image_base;
        if (offset > mapped.size() || size > mapped.size() - offset) return false;
        std::copy(mapped.begin() + static_cast<std::ptrdiff_t>(offset),
                  mapped.begin() + static_cast<std::ptrdiff_t>(offset + size), output);
        return true;
    }
};

MockMappedImage good_mapped_image() {
    using namespace rmod1::image_mapping;
    MockMappedImage fixture;
    fixture.layout = {0x00400000u, 0x3000u, 0x1000u,
                      {{0x1000u, 0x800u, 0x800u, 0x1000u, true, false}}};
    fixture.source.resize(0x2000u);
    for (std::size_t i = 0; i < fixture.source.size(); ++i)
        fixture.source[i] = static_cast<std::uint8_t>((i * 17u + 3u) & 0xffu);
    fixture.mapped.resize(fixture.layout.image_size);
    std::copy(fixture.source.begin(), fixture.source.begin() + 0x1000, fixture.mapped.begin());
    std::copy(fixture.source.begin() + 0x1000, fixture.source.begin() + 0x1800,
              fixture.mapped.begin() + 0x1000);
    fixture.regions.push_back({fixture.layout.image_base, fixture.layout.image_size,
        fixture.layout.image_base, State::Committed, Type::Image});
    return fixture;
}

bool verify_mock_image(const MockMappedImage& fixture, std::string& error) {
    const auto query = [&](std::uintptr_t address, rmod1::image_mapping::Region& region) {
        return fixture.query(address, region);
    };
    const auto read = [&](std::uintptr_t address, std::uint8_t* output, std::size_t size) {
        return fixture.read(address, output, size);
    };
    return rmod1::image_mapping::verify(fixture.layout, fixture.source, query, read, error);
}

void test_suspended_image_mapping_validation() {
    using namespace rmod1::image_mapping;
    std::string error;
    const auto valid = good_mapped_image();
    check(verify_mock_image(valid, error), "MEM_IMAGE extent, headers and executable section pass");

    auto absent = valid;
    absent.regions.clear();
    check(!verify_mock_image(absent, error), "absent suspended image mapping rejects");

    auto misplaced = valid;
    misplaced.regions[0].allocation_base += 0x1000u;
    check(!verify_mock_image(misplaced, error), "misplaced image allocation base rejects");

    auto wrong_type = valid;
    wrong_type.regions[0].type = Type::Private;
    check(!verify_mock_image(wrong_type, error), "non-MEM_IMAGE allocation rejects");

    auto uncommitted = valid;
    uncommitted.regions.clear();
    uncommitted.regions.push_back({uncommitted.layout.image_base, 0x1000u,
        uncommitted.layout.image_base, State::Committed, Type::Image});
    uncommitted.regions.push_back({uncommitted.layout.image_base + 0x1000u, 0x2000u,
        uncommitted.layout.image_base, State::Reserved, Type::Image});
    check(!verify_mock_image(uncommitted, error), "uncommitted image extent rejects");

    auto changed_headers = valid;
    changed_headers.mapped[0x20] ^= 1u;
    check(!verify_mock_image(changed_headers, error), "modified mapped PE headers reject");

    auto changed_code = valid;
    changed_code.mapped[0x1100] ^= 1u;
    check(!verify_mock_image(changed_code, error), "mismatched mapped executable section rejects");
}
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: core_tests <public-ini-path>\n";
        return 2;
    }
    test_config(argv[1]);
    test_exception_report_layout();
    test_runtime_operation_feature_isolation();
    test_challenge_preview_identity_lifecycle();
    test_vehicle_pools_and_selection();
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
    test_g2_player_vehicle_policy();
#endif
    test_participant_and_grid_gate();
    test_native_start_gate_callback_path();
    test_observed_native_roster_gate();
    test_duplicates_never_roster_gate();
    test_installable_feature_coverage();
    test_identity_and_patch_preflight();
    test_suspended_image_mapping_validation();
    std::cout << "checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
