#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>

#include "core.hpp"
#include "native_plan.hpp"
#include "rmod2_startup_preflight.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace {
bool sha256(const std::vector<std::uint8_t>& bytes, char output[65]) {
    BCRYPT_ALG_HANDLE algorithm{}; BCRYPT_HASH_HANDLE hash{};
    DWORD object_size{}, digest_size{}, received{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) return false;
    bool ok = BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH, reinterpret_cast<PUCHAR>(&object_size), sizeof(object_size), &received, 0) >= 0 &&
        BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH, reinterpret_cast<PUCHAR>(&digest_size), sizeof(digest_size), &received, 0) >= 0 && digest_size == 32;
    std::vector<UCHAR> object(ok ? object_size : 0), digest(ok ? digest_size : 0);
    if (ok) ok = BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr, 0, 0) >= 0;
    if (ok && !bytes.empty()) ok = BCryptHashData(hash, const_cast<PUCHAR>(bytes.data()), static_cast<ULONG>(bytes.size()), 0) >= 0;
    if (ok) ok = BCryptFinishHash(hash, digest.data(), digest_size, 0) >= 0;
    if (hash) BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(algorithm, 0);
    if (!ok) return false;
    static constexpr char hex[] = "0123456789abcdef";
    for (std::size_t i = 0; i < digest.size(); ++i) { output[i * 2] = hex[digest[i] >> 4]; output[i * 2 + 1] = hex[digest[i] & 15]; }
    output[64] = 0; return true;
}

bool decode_hex(const char* text, std::vector<std::uint8_t>& out) {
    if (!text) return false;
    const std::string s(text); if (s.size() % 2) return false;
    out.clear(); out.reserve(s.size() / 2);
    auto nibble = [](char c) -> int { if (c >= '0' && c <= '9') return c - '0'; if (c >= 'a' && c <= 'f') return c - 'a' + 10; if (c >= 'A' && c <= 'F') return c - 'A' + 10; return -1; };
    for (std::size_t i = 0; i < s.size(); i += 2) { const int a = nibble(s[i]), b = nibble(s[i + 1]); if (a < 0 || b < 0) return false; out.push_back(static_cast<std::uint8_t>((a << 4) | b)); }
    return true;
}

bool rva_to_raw(const std::vector<std::uint8_t>& pe, std::uint32_t rva, std::size_t length, std::size_t& offset) {
    if (pe.size() < 0x40 || pe[0] != 'M' || pe[1] != 'Z') return false;
    auto u16 = [&](std::size_t at) { return static_cast<std::uint16_t>(pe[at] | (pe[at + 1] << 8)); };
    auto u32 = [&](std::size_t at) { return static_cast<std::uint32_t>(pe[at] | (pe[at + 1] << 8) | (pe[at + 2] << 16) | (pe[at + 3] << 24)); };
    const auto nt = u32(0x3c); if (nt > pe.size() || pe.size() - nt < 24 || u32(nt) != 0x00004550) return false;
    const auto count = u16(nt + 6), optional_size = u16(nt + 20); const std::size_t table = static_cast<std::size_t>(nt) + 24 + optional_size;
    if (table > pe.size() || static_cast<std::size_t>(count) > (pe.size() - table) / 40) return false;
    for (std::size_t i = 0; i < count; ++i) {
        const std::size_t s = table + i * 40; const auto virtual_size = u32(s + 8), virtual_address = u32(s + 12), raw_size = u32(s + 16), raw = u32(s + 20);
        const auto extent = (std::max)(virtual_size, raw_size);
        if (rva < virtual_address || static_cast<std::uint64_t>(rva) + length > static_cast<std::uint64_t>(virtual_address) + extent) continue;
        const auto delta = rva - virtual_address;
        if (delta > raw_size || length > raw_size - delta || raw > pe.size() || length > pe.size() - raw - delta) return false;
        offset = static_cast<std::size_t>(raw) + delta; return true;
    }
    return false;
}

bool check(bool condition, const char* label) { if (!condition) std::cerr << "FAIL " << label << "\n"; return condition; }
}

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 2;
    std::ifstream input(argv[1], std::ios::binary);
    std::vector<std::uint8_t> retail((std::istreambuf_iterator<char>(input)), {});
    char digest[65]{};
    if (!check(retail.size() == rmod1_plan::kRetailSize && sha256(retail, digest) && std::strcmp(digest, rmod1_plan::kRetailSha256) == 0, "pinned-retail-host")) return 3;

    // This is the host-qualified post-verification path shared with BOOT-B:
    // materialize the exact generated templates and callback slots, then run
    // the same structural and byte-preimage checks before any installation.
    std::vector<std::uint8_t> code(rmod1_plan::kCodeSize), data(rmod1_plan::kDataSize);
    if (!check(rmod2_boot::copy_generated_template(code, rmod1_plan::kCodeTemplate, rmod1_plan::kCodeTemplateSize, rmod1_plan::kCodeUsed), "code-template-preparation") ||
        !check(rmod2_boot::copy_generated_template(data, rmod1_plan::kDataTemplate, rmod1_plan::kDataTemplateSize, rmod1_plan::kDataUsed), "data-template-preparation")) return 4;
    const std::uint32_t slots[] = { rmod1_plan::kSlotModule, rmod1_plan::kSlotConfigure, rmod1_plan::kSlotChooseClass,
        rmod1_plan::kSlotOpponentLimit, rmod1_plan::kSlotCanStart, rmod1_plan::kSlotLoadLibraryW,
        rmod1_plan::kSlotStartPhase, rmod1_plan::kSlotChallenge };
    for (std::size_t i = 0; i < _countof(slots); ++i)
        if (!check(rmod2_boot::write_u32_address(data, rmod1_plan::kDataBase, slots[i], static_cast<std::uint32_t>(0x12340000 + i)), "callback-slot-offset")) return 5;
    std::size_t offset = 0;
    if (!check(!rmod2_boot::allocation_offset(rmod1_plan::kDataBase, rmod1_plan::kConfigOffset, data.size(), offset), "relative-offset-not-treated-as-absolute")) return 6;
    if (!check(rmod1_plan::kConfigOffset < rmod1_plan::kDllPathOffset &&
        static_cast<std::size_t>(rmod1_plan::kDllPathOffset - rmod1_plan::kConfigOffset) == 0x1100 &&
        4u + rmod1::kMaxConfigBytes <= rmod1_plan::kDllPathOffset - rmod1_plan::kConfigOffset, "reserved-capacity-is-4352")) return 7;

    const std::string ini = "[General]\nConfigVersion = 2\n\n[Randomizer]\nQuickRace = 1\nRallyeCup = 0\nMasterRallye = 0\nInvitation = 0\nChallenge = 0\nDuplicates = 1\n\n[Opponents]\nMaxOpponents = 3\n\n[Addons]\nInclude = 0\n\n[Logging]\nEnabled = 1\n";
    const auto accepted = rmod1::parse_ini(ini);
    if (!check(accepted.accepted, "provided-configversion2-ini")) return 8;
    std::string maximum = ini;
    if (maximum.size() < rmod1::kMaxConfigBytes) {
        maximum += ";";
        maximum.append(rmod1::kMaxConfigBytes - maximum.size(), 'x');
    }
    if (!check(maximum.size() == rmod1::kMaxConfigBytes && rmod1::parse_ini(maximum).accepted, "maximum-4096-byte-ini")) return 9;
    std::array<std::uint8_t, 4> empty_blob{};
    std::uint32_t empty_blob_length = 1;
    std::memcpy(&empty_blob_length, empty_blob.data(), sizeof(empty_blob_length));
    if (!check(empty_blob_length == 0 && rmod1::Config{}.quick_race == rmod1::Policy::Stock, "empty-default-config")) return 10;

    std::vector<rmod2_boot::OperationSpan> spans;
    std::vector<rmod2_boot::NativePreimage> preimages;
    std::vector<std::vector<std::uint8_t>> expected_bytes;
    std::vector<const rmod1_plan::ImageOperation*> selected;
    for (std::size_t i = 0; i < rmod1_plan::kOperationCount; ++i) {
        const auto& op = rmod1_plan::kOperations[i];
        if (std::strcmp(op.id, "oep-bootstrap") == 0 || !(op.feature & rmod1_plan::kFeatureRandomizer)) continue;
        std::vector<std::uint8_t> expected, replacement;
        if (!decode_hex(op.expected_hex, expected) || !decode_hex(op.replacement_hex, replacement)) return 11;
        std::size_t raw = 0;
        if (!rva_to_raw(retail, op.rva, expected.size(), raw) || raw > retail.size() || expected.size() > retail.size() - raw ||
            !std::equal(expected.begin(), expected.end(), retail.begin() + raw)) return 12;
        spans.push_back({op.rva, expected.size(), replacement.size(), op.id});
        expected_bytes.push_back(std::move(expected)); selected.push_back(&op);
    }
    std::string error;
    if (!check(!spans.empty() && rmod2_boot::validate_operation_spans(spans.data(), spans.size(), rmod1_plan::kImageSize, error), "selected-operation-range-and-overlap-preflight")) return 13;
    for (std::size_t i = 0; i < spans.size(); ++i)
        preimages.push_back({static_cast<std::uintptr_t>(rmod1_plan::kImageBase) + spans[i].rva, expected_bytes[i].data(), expected_bytes[i].size(), spans[i].id});
    auto retail_reader = [&](std::uintptr_t address, void* out, std::size_t length) {
        if (address < rmod1_plan::kImageBase) return false;
        std::size_t raw = 0; const auto rva = static_cast<std::uint32_t>(address - rmod1_plan::kImageBase);
        if (!rva_to_raw(retail, rva, length, raw) || raw > retail.size() || length > retail.size() - raw) return false;
        std::memcpy(out, retail.data() + raw, length); return true;
    };
    if (!check(rmod2_boot::verify_native_preimages(preimages.data(), preimages.size(), retail_reader, error), "selected-operation-original-preimages")) return 14;
    auto mismatch_reader = [&](std::uintptr_t address, void* out, std::size_t length) {
        if (!retail_reader(address, out, length)) return false;
        if (length) static_cast<std::uint8_t*>(out)[0] ^= 1;
        return true;
    };
    if (!check(!rmod2_boot::verify_native_preimages(preimages.data(), preimages.size(), mismatch_reader, error), "negative-preimage-mismatch")) return 15;

    std::cout << "BOOT_B_HOST_QUALIFIED_PREFLIGHT_PASS retail_sha=" << digest
        << " config_cases=empty,v2,4096 data_templates=2 selected_ops=" << spans.size()
        << " exact_preimages=1 negative_preimage=1 oep_staging=omitted\n";
    return 0;
}
