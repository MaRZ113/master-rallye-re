#define RMOD_EXTRA_SDK_BINDING 1
#include "../../src/native/rmod1/rmod2_inprocess.cpp"
#include <iostream>

int main(int argc, char** argv) {
    if (argc != 2) return 8;
    auto* memory = static_cast<unsigned char*>(VirtualAlloc(
        reinterpret_cast<void*>(rmod1_plan::kImageBase), rmod1_plan::kImageSize,
        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (memory != reinterpret_cast<unsigned char*>(rmod1_plan::kImageBase)) return 1;
    if (sdk_profile_matches() || any_sdk_hook_present()) return 2;
    for (const auto& item : sdk_binding_profile::checks) {
        const auto bytes = from_hex(item.expected_hex);
        if (bytes.empty() || item.rva + bytes.size() > rmod1_plan::kImageSize) return 3;
        std::memcpy(memory + item.rva, bytes.data(), bytes.size());
    }
    for (const auto& hook : sdk_binding_profile::hooks) {
        const auto bytes = from_hex(hook.mapped_hex);
        std::memcpy(memory + hook.rva, bytes.data(), bytes.size());
    }
    std::ifstream input(argv[1], std::ios::binary);
    std::vector<unsigned char> payload((std::istreambuf_iterator<char>(input)), {});
    if (payload.size() != sdk_binding_profile::extension_size) return 9;
    auto* extension = static_cast<unsigned char*>(VirtualAlloc(
        reinterpret_cast<void*>(sdk_binding_profile::extension_va), payload.size(),
        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (extension != reinterpret_cast<unsigned char*>(sdk_binding_profile::extension_va)) return 10;
    std::memcpy(extension, payload.data(), payload.size());
    SdkSnapshot snapshot;
    if (!sdk_profile_matches(&snapshot) || !sdk_snapshot_matches(snapshot) || !any_sdk_hook_present()) return 4;
    std::vector<Patch> patches;
    for (const auto& operation : rmod1_plan::kOperations) {
        if (std::string_view(operation.id) != "challenge-preview-identity" &&
            std::string_view(operation.id) != "challenge-race-consume") continue;
        Patch p; p.source=&operation; p.address=rmod1_plan::kImageBase+operation.rva;
        p.expected=from_hex(operation.expected_hex); p.replacement=from_hex(operation.replacement_hex);
        patches.push_back(std::move(p));
    }
    if (patches.size()!=2) return 13;
    compose_sdk_challenge(patches);
    for (const auto& p : patches) if (p.expected != from_hex("8bbc38e0060000")) return 14;
    std::vector<std::uint8_t> code(rmod1_plan::kCodeTemplate,
                                   rmod1_plan::kCodeTemplate+rmod1_plan::kCodeTemplateSize);
    compose_sdk_stubs(code);
    for (const auto& hook : sdk_binding_profile::hooks) {
        const auto index=hook.stub_va-rmod1_plan::kCodeBase;
        const auto expected=from_hex("8bbc38e00600009c60");
        if (!std::equal(expected.begin(),expected.end(),code.begin()+index)) return 15;
    }
    bool rejected=false;
    try {compose_sdk_stubs(code);} catch (const std::exception&) {rejected=true;}
    if (!rejected) return 16;
    extension[sdk_binding_profile::rw_offset] ^= 1;
    if (!sdk_profile_matches() || !sdk_snapshot_matches(snapshot)) return 11;
    extension[sdk_binding_profile::rw_offset] ^= 1;
    extension[0] ^= 1;
    if (!sdk_profile_matches() || sdk_snapshot_matches(snapshot)) return 12;
    extension[0] ^= 1;
    const auto& first = sdk_binding_profile::checks[0];
    memory[first.rva] ^= 1;
    if (sdk_profile_matches() || sdk_snapshot_matches(snapshot)) return 5;
    memory[first.rva] ^= 1;
    if (!sdk_profile_matches() || !sdk_snapshot_matches(snapshot)) return 6;
    for (const auto& hook : sdk_binding_profile::hooks) {
        const auto original = from_hex("8bbc3874050000");
        std::memcpy(memory + hook.rva, original.data(), original.size());
    }
    if (sdk_profile_matches() || any_sdk_hook_present()) return 7;
    VirtualFree(extension, 0, MEM_RELEASE);
    VirtualFree(memory, 0, MEM_RELEASE);
    std::cout << "PASS SDK profile/extension, composed live patch/stub helpers, altered/partial inputs, writable state; no game process\n";
}
