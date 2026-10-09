#include "../../src/native/rmod1/core.hpp"

#include <iostream>
#include <map>

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

void test_config() {
    const std::string valid =
        "[General]\r\nConfigVersion=1\r\n"
        "[Randomizer]\r\nEnabled=true\r\nQuickRace=Full\r\nDuplicates=WhenNeeded\r\n"
        "[Opponents]\r\nEnabled=true\r\nMaxOpponents=7\r\n"
        "[Addons]\r\nInclude=Auto\r\n[Logging]\r\nEnabled=false\r\n";
    auto parsed = parse_ini(valid);
    check(parsed.accepted, "valid versioned configuration accepted");
    check(parsed.config.randomizer_enabled && parsed.config.quick_race == Policy::Full, "randomizer settings parsed");
    check(parsed.config.opponents_enabled && parsed.config.max_opponents == 7, "one through seven limit parsed");
    check(parsed.config.duplicates_when_needed && !parsed.config.logging_enabled, "strict duplicate and logging settings parsed");
    check(parsed.config.addons == AddonMode::RegisteredOnly, "Auto means process-registered addon entries only");

    for (const char* policy : {"Stock", "Full", "T1", "T2", "T3", "Mixed", "Diverse"}) {
        const std::string input = std::string("[General]\nConfigVersion=1\n[Randomizer]\nQuickRace=") + policy + "\n";
        check(parse_ini(input).accepted, "every supported policy parses");
    }
    const std::vector<std::string> invalid_inputs = {
            "[General]\nConfigVersion=2\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nMystery=true\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nEnabled=true\nEnabled=false\n",
            "[General]\nConfigVersion=1\n[Opponents]\nMaxOpponents=8\n",
            "[General]\nConfigVersion=1\n[Randomizer]\nQuickRace=Stock;unsafe\n",
            "[General]\nConfigVersion=1\n[Addons]\nInclude=ScanDirectories\n",
            std::string("[General]\nConfigVersion=1\n") + char(0)};
    for (const auto& invalid : invalid_inputs) {
        const auto rejected = parse_ini(invalid);
        check(!rejected.accepted && !rejected.config.randomizer_enabled &&
              rejected.config.max_opponents == 3 && rejected.config.quick_race == Policy::Stock,
              "malformed input rejects whole file and restores safe defaults");
    }
    check(!parse_ini(std::string(kMaxConfigBytes + 1, 'x')).accepted, "oversized config rejected");
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
    check(invitation_pool.empty(), "authored/non-Quick-Race roster owners remain native and untouched");

    RegisteredAddon unverified{27, 1, false, true, true, true};
    RegisteredAddon verified{27, 1, true, true, true, true};
    check(eligible_vehicles(GameMode::QuickRace, 0, {unverified}).size() == 21, "addon directory/manifest alone cannot register an ID");
    check(eligible_vehicles(GameMode::QuickRace, 0, {verified}).size() == 22, "only process-registered materializable addon entry is eligible");

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
    auto mixed = choose_vehicle(Policy::Mixed, true, 3, 0, 0, all, {}, nullptr,
                                [](int) { return 1; });
    check(mixed.kind == SelectionKind::SelectedId && mixed.class_id == 1,
          "Mixed chooses class before physical ID");
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
}

void test_participant_and_grid_gate() {
    Config config;
    config.opponents_enabled = true;
    config.max_opponents = 7;
    for (unsigned ai = 1; ai <= 3; ++ai) {
        const auto plan = plan_quick_race(1, ai, false, 0, 7, 1, false, {}, config);
        check(plan.allowed && !plan.use_extension && plan.total == ai + 1,
              "native one-to-three AI count preserved");
    }
    const auto five = plan_quick_race(1, 4, false, 10, 0, 0, false, {0, 0, 0, 0}, config);
    check(five.allowed && five.use_extension && five.total == 5,
          "only exact historically runtime-qualified five-car profile passes");
    check(!plan_quick_race(1, 4, false, 10, 0, 0, false, {0, 1, 0, 0}, config).allowed,
          "mixed-class five-car grid is not inferred safe from T1-only proof");
    check(!plan_quick_race(1, 4, false, 0, 0, 0, false, {0, 0, 0, 0}, config).allowed,
          "five-car extension does not silently expand to unqualified courses");
    const auto eight = plan_quick_race(1, 7, false, 10, 0, 0, false, {0, 0, 0, 0, 0, 0, 0}, config);
    check(!eight.allowed && eight.total == kMaximumTotalCars,
          "seven-opponent UI request maps to eight total but is blocked until grid clearance");
    check(!plan_quick_race(2, 0, true, 10, 0, 0, false, {}, config).allowed,
          "invalid count is rejected before SplitScreen fallback");
    Config disabled;
    check(!plan_quick_race(1, 4, false, 10, 0, 0, false, {0, 0, 0, 0}, disabled).allowed,
          "opponent-count extension is independent and disabled by default");
    check(!plan_quick_race(2, 7, true, 10, 0, 0, false, {}, config).allowed,
          "SplitScreen never becomes an eight-player experiment");
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
}

int main() {
    test_config();
    test_vehicle_pools_and_selection();
    test_participant_and_grid_gate();
    test_identity_and_patch_preflight();
    std::cout << "checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
