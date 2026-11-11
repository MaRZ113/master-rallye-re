#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _WIN32_WINNT 0x0A00
#include <windows.h>
#include <bcrypt.h>

#include "core.hpp"
#include "image_mapping.hpp"
#include "native_plan.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cwctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace fs = std::filesystem;

namespace {

using namespace rmod1;

constexpr std::uint32_t kExpectedImageEntry = 0x001C4602u;
constexpr std::uint32_t kExpectedHeadersSize = 0x1000u;
constexpr std::uint32_t kImageExecute = 0x20000000u;
constexpr std::uint32_t kImageRead = 0x40000000u;
constexpr std::uint32_t kImageWrite = 0x80000000u;
constexpr std::uint32_t kImageRelocsStripped = 0x0001u;
constexpr std::uint32_t kDirectoryCountOffset = 96u;
constexpr std::uint32_t kMaxIniBytes = static_cast<std::uint32_t>(kMaxConfigBytes);

struct Section {
    std::string name;
    std::uint32_t virtual_size{};
    std::uint32_t rva{};
    std::uint32_t raw_size{};
    std::uint32_t raw_offset{};
    std::uint32_t characteristics{};
};

struct PeInfo {
    std::uint16_t machine{};
    std::uint16_t file_characteristics{};
    std::uint32_t image_base{};
    std::uint32_t image_size{};
    std::uint32_t headers_size{};
    std::uint32_t entry_rva{};
    std::uint32_t section_alignment{};
    std::vector<Section> sections;
};

[[noreturn]] void fail(const std::string& message);
std::string win_error(const char* context, DWORD code = GetLastError());

struct Files {
    fs::path runtime_dir;
    fs::path game_dir;
    fs::path executable;
    fs::path runtime_dll;
    fs::path ini;
    std::vector<std::uint8_t> executable_bytes;
    std::vector<std::uint8_t> runtime_bytes;
    std::vector<std::uint8_t> ini_bytes;
    Config config{};
    bool ini_present = false;
    bool ini_accepted = false;
    std::string ini_diagnostic;
};

std::string config_summary(const Config& config) {
    std::ostringstream text;
    text << "effective_numeric_config=";
    if (config.config_version == 1) {
        // Preserve the exact V1 diagnostic spelling consumed by existing
        // v11-v13 package verifiers and owner-facing logs.
        text << "randomizer=" << (config.randomizer_enabled ? 1 : 0)
             << ",quickrace=" << policy_numeric_id(config.quick_race) << ':' << policy_name(config.quick_race);
    } else {
        text << "config_version=2,randomizer=" << (config_requests_randomizer(config) ? 1 : 0)
             << ",quickrace=" << policy_numeric_id_for_version(policy_for_mode(config, GameMode::QuickRace), 2) << ':'
             << policy_name(policy_for_mode(config, GameMode::QuickRace)) << ",modes=";
        for (std::size_t index = 0; index < config.mode_policies.size(); ++index) {
            if (index) text << ',';
            text << policy_numeric_id_for_version(config.mode_policies[index], 2) << ':' << policy_name(config.mode_policies[index]);
        }
    }
    text << ",duplicates=" << (config.duplicates_when_needed ? 1 : 0) << ':'
         << (config.duplicates_when_needed ? "WhenNeeded" : "Never")
         << ",opponents=" << (config_requests_opponent_extension(config) ? 1 : 0)
         << ",max_ai=" << config.max_opponents
         << ",experimental_extended_ai=" << (config_allows_extended_ai(config) ? 1 : 0)
         << ",addons=" << (config.addons == AddonMode::RegisteredOnly ? 1 : 0) << ':'
         << addon_mode_name(config.addons)
         << ",logging=" << (config.logging_enabled ? 1 : 0);
    return text.str();
}

struct ProcessHandles {
    HANDLE process = nullptr;
    HANDLE thread = nullptr;
    bool resumed = false;
    bool exited = false;
    ~ProcessHandles() {
        if (process && !resumed && !exited) {
            TerminateProcess(process, 0xE013u);
            WaitForSingleObject(process, 5000);
        }
        if (thread) CloseHandle(thread);
        if (process) CloseHandle(process);
    }
};

struct FilePin {
    HANDLE handle = INVALID_HANDLE_VALUE;
    explicit FilePin(const fs::path& path) {
        handle = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                             FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
        if (handle == INVALID_HANDLE_VALUE)
            fail(win_error("cannot pin verified input against replacement or modification"));
    }
    ~FilePin() { if (handle != INVALID_HANDLE_VALUE) CloseHandle(handle); }
    FilePin(const FilePin&) = delete;
    FilePin& operator=(const FilePin&) = delete;
};

struct ImageOperation {
    const rmod1_plan::ImageOperation* source{};
    std::vector<std::uint8_t> replacement;
    std::uintptr_t address{};
    DWORD original_protection{};
};

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error(message);
}

std::string win_error(const char* context, DWORD code) {
    LPSTR message = nullptr;
    const DWORD flags = FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
                        FORMAT_MESSAGE_IGNORE_INSERTS;
    const DWORD size = FormatMessageA(flags, nullptr, code, 0,
        reinterpret_cast<LPSTR>(&message), 0, nullptr);
    std::string result(context);
    result += " (Windows error ";
    result += std::to_string(code);
    result += ")";
    if (size && message) {
        result += ": ";
        result.append(message, size);
        LocalFree(message);
    }
    return result;
}

std::uint16_t read_u16(const std::vector<std::uint8_t>& bytes, std::size_t at) {
    if (at > bytes.size() || bytes.size() - at < 2) fail("truncated PE uint16");
    return static_cast<std::uint16_t>(bytes[at] | (static_cast<unsigned>(bytes[at + 1]) << 8));
}

std::uint32_t read_u32(const std::vector<std::uint8_t>& bytes, std::size_t at) {
    if (at > bytes.size() || bytes.size() - at < 4) fail("truncated PE uint32");
    return static_cast<std::uint32_t>(bytes[at]) |
        (static_cast<std::uint32_t>(bytes[at + 1]) << 8) |
        (static_cast<std::uint32_t>(bytes[at + 2]) << 16) |
        (static_cast<std::uint32_t>(bytes[at + 3]) << 24);
}

std::vector<std::uint8_t> read_file(const fs::path& path, std::size_t maximum = 64u * 1024u * 1024u) {
    std::ifstream input(path, std::ios::binary);
    if (!input) fail("cannot read file: " + path.string());
    input.seekg(0, std::ios::end);
    const auto end = input.tellg();
    if (end < 0 || static_cast<std::uint64_t>(end) > maximum)
        fail("file size is invalid or exceeds the safety limit: " + path.string());
    input.seekg(0, std::ios::beg);
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(end));
    if (!bytes.empty() && !input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size())))
        fail("short read: " + path.string());
    return bytes;
}

std::vector<std::uint8_t> read_handle(HANDLE handle, std::size_t maximum) {
    LARGE_INTEGER size{};
    if (!GetFileSizeEx(handle, &size) || size.QuadPart < 0 ||
        static_cast<std::uint64_t>(size.QuadPart) > maximum)
        fail(win_error("pinned input has an invalid size"));
    LARGE_INTEGER zero{};
    if (!SetFilePointerEx(handle, zero, nullptr, FILE_BEGIN))
        fail(win_error("cannot seek pinned input"));
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size.QuadPart));
    std::size_t offset = 0;
    while (offset < bytes.size()) {
        const DWORD request = static_cast<DWORD>(std::min<std::size_t>(bytes.size() - offset, 1u << 20));
        DWORD received = 0;
        if (!ReadFile(handle, bytes.data() + offset, request, &received, nullptr) || received != request)
            fail(win_error("cannot read pinned input"));
        offset += received;
    }
    return bytes;
}

std::string sha256(const std::uint8_t* data, std::size_t size) {
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    DWORD object_length{}, digest_length{}, received{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0)
        fail("cannot open Windows SHA256 provider");
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_length), sizeof(object_length), &received, 0) < 0 ||
        BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                          reinterpret_cast<PUCHAR>(&digest_length), sizeof(digest_length), &received, 0) < 0) {
        BCryptCloseAlgorithmProvider(algorithm, 0);
        fail("cannot query Windows SHA256 provider");
    }
    std::vector<UCHAR> object(object_length), digest(digest_length);
    NTSTATUS status = BCryptCreateHash(algorithm, &hash, object.data(), object_length, nullptr, 0, 0);
    if (status >= 0 && size) status = BCryptHashData(hash, const_cast<PUCHAR>(data), static_cast<ULONG>(size), 0);
    if (status >= 0) status = BCryptFinishHash(hash, digest.data(), digest_length, 0);
    if (hash) BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (status < 0) fail("Windows SHA256 operation failed");
    static constexpr char digits[] = "0123456789abcdef";
    std::string output;
    output.reserve(digest.size() * 2);
    for (const auto byte : digest) {
        output.push_back(digits[byte >> 4]);
        output.push_back(digits[byte & 0x0f]);
    }
    return output;
}

std::string sha256(const std::vector<std::uint8_t>& bytes) {
    return sha256(bytes.data(), bytes.size());
}

fs::path absolute_path(const fs::path& path) {
    std::error_code error;
    const fs::path absolute = fs::absolute(path, error);
    if (error) fail("cannot make path absolute: " + path.string());
    return absolute.lexically_normal();
}

fs::path module_directory() {
    std::vector<wchar_t> buffer(32768);
    const DWORD length = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!length || length >= buffer.size()) fail(win_error("cannot resolve launcher path"));
    return fs::path(std::wstring(buffer.data(), length)).parent_path();
}

bool plain_file(const fs::path& path) {
    const DWORD attributes = GetFileAttributesW(path.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES && !(attributes & FILE_ATTRIBUTE_DIRECTORY) &&
           !(attributes & FILE_ATTRIBUTE_REPARSE_POINT);
}

std::wstring normalized_path(const fs::path& path) {
    std::wstring result = absolute_path(path).wstring();
    std::replace(result.begin(), result.end(), L'/', L'\\');
    if (result.rfind(L"\\\\?\\", 0) == 0) result.erase(0, 4);
    std::transform(result.begin(), result.end(), result.begin(),
        [](wchar_t c) { return static_cast<wchar_t>(std::towlower(c)); });
    return result;
}

PeInfo parse_pe(const std::vector<std::uint8_t>& bytes) {
    if (bytes.size() < 0x100 || bytes[0] != 'M' || bytes[1] != 'Z') fail("game file is not an MZ image");
    const std::uint32_t pe_offset = read_u32(bytes, 0x3c);
    if (pe_offset > bytes.size() || bytes.size() - pe_offset < 24 ||
        std::memcmp(bytes.data() + pe_offset, "PE\0\0", 4) != 0)
        fail("game image has an invalid PE header");
    PeInfo pe;
    pe.machine = read_u16(bytes, pe_offset + 4);
    const std::uint16_t count = read_u16(bytes, pe_offset + 6);
    pe.file_characteristics = read_u16(bytes, pe_offset + 22);
    const std::uint16_t optional_size = read_u16(bytes, pe_offset + 20);
    const std::size_t optional = pe_offset + 24;
    if (optional > bytes.size() || bytes.size() - optional < optional_size || read_u16(bytes, optional) != 0x10b)
        fail("game image is not a complete PE32 executable");
    pe.image_base = read_u32(bytes, optional + 28);
    pe.section_alignment = read_u32(bytes, optional + 32);
    pe.entry_rva = read_u32(bytes, optional + 16);
    pe.image_size = read_u32(bytes, optional + 56);
    pe.headers_size = read_u32(bytes, optional + 60);
    const std::size_t table = optional + optional_size;
    if (table > bytes.size() || static_cast<std::size_t>(count) > (bytes.size() - table) / 40)
        fail("game section table is truncated");
    for (std::uint16_t i = 0; i < count; ++i) {
        const std::size_t at = table + static_cast<std::size_t>(i) * 40;
        char name[9]{};
        std::memcpy(name, bytes.data() + at, 8);
        Section section;
        section.name = name;
        section.virtual_size = read_u32(bytes, at + 8);
        section.rva = read_u32(bytes, at + 12);
        section.raw_size = read_u32(bytes, at + 16);
        section.raw_offset = read_u32(bytes, at + 20);
        section.characteristics = read_u32(bytes, at + 36);
        if (section.raw_offset > bytes.size() || section.raw_size > bytes.size() - section.raw_offset ||
            section.rva > pe.image_size || std::max(section.virtual_size, section.raw_size) > pe.image_size - section.rva)
            fail("game section lies outside the source file or mapped image");
        pe.sections.push_back(std::move(section));
    }
    if (pe.machine != IMAGE_FILE_MACHINE_I386 || pe.image_base != rmod1_plan::kImageBase ||
        pe.image_size != rmod1_plan::kImageSize || pe.entry_rva != kExpectedImageEntry ||
        pe.headers_size != kExpectedHeadersSize || pe.section_alignment == 0 ||
        (pe.file_characteristics & kImageRelocsStripped) == 0)
        fail("retail PE layout does not match the pinned no-relocation profile");
    return pe;
}

void verify_regular_path(const fs::path& path, const char* label) {
    if (!plain_file(path)) fail(std::string(label) + " is missing, linked, or not a regular file");
}

std::vector<std::uint8_t> decode_hex(const char* hex) {
    if (!hex) fail("missing generated operation hex");
    const std::string_view value(hex);
    if ((value.size() & 1u) != 0) fail("generated operation hex has odd length");
    auto nibble = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    };
    std::vector<std::uint8_t> result;
    result.reserve(value.size() / 2);
    for (std::size_t i = 0; i < value.size(); i += 2) {
        const int high = nibble(value[i]), low = nibble(value[i + 1]);
        if (high < 0 || low < 0) fail("generated operation contains invalid hex");
        result.push_back(static_cast<std::uint8_t>((high << 4) | low));
    }
    return result;
}

std::vector<std::uint8_t> decode_template(const std::uint8_t* bytes, std::size_t size,
                                         std::size_t used, const char* expected_hash,
                                         std::size_t allocation_size) {
    if (size != used || used > allocation_size) fail("generated remote template size mismatch");
    if (sha256(bytes, size) != expected_hash) fail("generated remote template SHA256 mismatch");
    std::vector<std::uint8_t> output(allocation_size, 0);
    if (size) std::memcpy(output.data(), bytes, size);
    return output;
}

Files verify_files(const fs::path& runtime_dir, const fs::path& game_dir) {
    Files files;
    files.runtime_dir = absolute_path(runtime_dir);
    files.game_dir = absolute_path(game_dir);
    files.executable = files.game_dir / L"MRallye.exe";
    files.runtime_dll = files.runtime_dir / L"MRallyeRandomizerRuntime.dll";
    files.ini = files.runtime_dir / L"MRallyeRandomizer.ini";
    verify_regular_path(files.executable, "retail executable");
    verify_regular_path(files.runtime_dll, "R-MOD1 runtime core");
    files.executable_bytes = read_file(files.executable, rmod1_plan::kRetailSize);
    files.runtime_bytes = read_file(files.runtime_dll, 32u * 1024u * 1024u);
    if (files.executable_bytes.size() != rmod1_plan::kRetailSize ||
        sha256(files.executable_bytes) != rmod1_plan::kRetailSha256)
        fail("unsupported MRallye.exe: exact retail SHA256/size required");
    const PeInfo retail = parse_pe(files.executable_bytes);
    (void)retail;
    if (sha256(files.runtime_bytes) != rmod1_plan::kRuntimeCoreSha256)
        fail("runtime core DLL SHA256 differs from the build-pinned artifact");
    if (files.runtime_bytes.size() < 0x100 || files.runtime_bytes[0] != 'M' || files.runtime_bytes[1] != 'Z')
        fail("runtime core is not a PE image");
    const std::uint32_t dll_pe_offset = read_u32(files.runtime_bytes, 0x3c);
    if (read_u16(files.runtime_bytes, dll_pe_offset + 4) != IMAGE_FILE_MACHINE_I386 ||
        read_u16(files.runtime_bytes, dll_pe_offset + 24) != 0x10b)
        fail("runtime core must be an x86 PE32 DLL");

    std::error_code error;
    files.ini_present = fs::exists(files.ini, error);
    if (error) fail("cannot inspect the INI configuration path");
    if (files.ini_present) {
        verify_regular_path(files.ini, "configuration file");
        const auto ini_size = fs::file_size(files.ini, error);
        if (error) fail("cannot determine configuration file size");
        if (ini_size > kMaxIniBytes) {
            files.ini_diagnostic = "INI exceeds 4096 bytes; both features disabled and retail Stock will launch.";
        } else {
            files.ini_bytes = read_file(files.ini, kMaxIniBytes);
            const std::string_view content(reinterpret_cast<const char*>(files.ini_bytes.data()), files.ini_bytes.size());
            const auto parsed = parse_ini(content);
            if (parsed.accepted) {
                files.config = parsed.config;
                files.ini_accepted = true;
                files.ini_diagnostic = "INI accepted.";
            } else {
                files.ini_diagnostic = parsed.diagnostics.empty() ? "INI invalid; safe retail defaults selected."
                    : parsed.diagnostics.front().code + ": " + parsed.diagnostics.front().message;
            }
        }
    } else {
        files.ini_diagnostic = "INI missing; safe retail Stock defaults selected.";
    }
    if (!files.ini_accepted) {
        files.config = Config{};
        files.ini_bytes.clear();
    }
    return files;
}

bool read_process(HANDLE process, std::uintptr_t address, void* destination, std::size_t size) {
    SIZE_T received = 0;
    return ReadProcessMemory(process, reinterpret_cast<LPCVOID>(address), destination, size, &received) && received == size;
}

bool write_process(HANDLE process, std::uintptr_t address, const void* source, std::size_t size) {
    SIZE_T written = 0;
    return WriteProcessMemory(process, reinterpret_cast<LPVOID>(address), source, size, &written) && written == size;
}

DWORD require_x86_target(HANDLE process) {
    USHORT process_machine = 0, native_machine = 0;
    if (!IsWow64Process2(process, &process_machine, &native_machine))
        fail(win_error("IsWow64Process2 failed"));
    if (process_machine != IMAGE_FILE_MACHINE_I386 ||
        (native_machine != IMAGE_FILE_MACHINE_AMD64 && native_machine != IMAGE_FILE_MACHINE_ARM64))
        fail("target is not the supported x86 process on a 64-bit Windows host");
    return process_machine;
}

std::uintptr_t verify_module_mapping(HANDLE process,
                                     const std::vector<std::uint8_t>& source, const PeInfo& pe) {
    const std::uintptr_t base = pe.image_base;
    if (!base || pe.image_size > std::numeric_limits<std::uintptr_t>::max() - base)
        fail("audited retail image extent overflows the process address space");

    image_mapping::Layout layout;
    layout.image_base = base;
    layout.image_size = pe.image_size;
    layout.headers_size = pe.headers_size;
    for (const auto& section : pe.sections) {
        layout.sections.push_back({section.rva, section.virtual_size, section.raw_size,
            section.raw_offset, (section.characteristics & kImageExecute) != 0,
            (section.characteristics & kImageWrite) != 0});
    }

    DWORD query_error = ERROR_SUCCESS;
    const auto query = [&](std::uintptr_t address, image_mapping::Region& output) {
        MEMORY_BASIC_INFORMATION memory{};
        const SIZE_T received = VirtualQueryEx(process, reinterpret_cast<LPCVOID>(address),
                                                &memory, sizeof(memory));
        if (received != sizeof(memory)) {
            query_error = GetLastError();
            return false;
        }
        output.base_address = reinterpret_cast<std::uintptr_t>(memory.BaseAddress);
        output.size = memory.RegionSize;
        output.allocation_base = reinterpret_cast<std::uintptr_t>(memory.AllocationBase);
        output.state = memory.State == MEM_COMMIT ? image_mapping::State::Committed
            : memory.State == MEM_RESERVE ? image_mapping::State::Reserved
            : memory.State == MEM_FREE ? image_mapping::State::Free
            : image_mapping::State::Unknown;
        output.type = memory.Type == MEM_IMAGE ? image_mapping::Type::Image
            : memory.Type == MEM_MAPPED ? image_mapping::Type::Mapped
            : memory.Type == MEM_PRIVATE ? image_mapping::Type::Private
            : image_mapping::Type::Unknown;
        return true;
    };
    const auto read = [&](std::uintptr_t address, std::uint8_t* output, std::size_t size) {
        return read_process(process, address, output, size);
    };
    std::string mapping_error;
    if (!image_mapping::verify(layout, source, query, read, mapping_error)) {
        if (query_error != ERROR_SUCCESS)
            fail(win_error("VirtualQueryEx could not verify the suspended retail image extent", query_error));
        fail("mapped retail image verification failed: " + mapping_error);
    }
    std::cout << "mapped_image=verified base=0x" << std::hex << base << std::dec
              << " size=" << pe.image_size << " type=MEM_IMAGE state=MEM_COMMIT"
              << " allocation_base=verified executable_sections=retail-match\n";
    return base;
}

void verify_all_preimages(HANDLE process, std::uintptr_t image_base,
                          const PeInfo& pe, std::vector<ImageOperation>& operations) {
    std::vector<std::pair<std::uintptr_t, std::uintptr_t>> ranges;
    for (auto& operation : operations) {
        const auto& source = *operation.source;
        const auto expected = decode_hex(source.expected_hex);
        if (operation.replacement.empty())
            operation.replacement = decode_hex(source.replacement_hex);
        if (expected.empty() || expected.size() != operation.replacement.size() ||
            source.rva > pe.image_size || expected.size() > pe.image_size - source.rva)
            fail(std::string("invalid bounded patch operation: ") + source.id);
        operation.address = image_base + source.rva;
        ranges.emplace_back(operation.address, operation.address + expected.size());

        MEMORY_BASIC_INFORMATION region{};
        if (VirtualQueryEx(process, reinterpret_cast<LPCVOID>(operation.address), &region, sizeof(region)) != sizeof(region) ||
            region.State != MEM_COMMIT || region.Type != MEM_IMAGE ||
            region.Protect != PAGE_EXECUTE_READ ||
            operation.address + expected.size() > reinterpret_cast<std::uintptr_t>(region.BaseAddress) + region.RegionSize)
            fail(std::string("native hook page has an unexpected mapping/protection: ") + source.id);
        std::vector<std::uint8_t> actual(expected.size());
        if (!read_process(process, operation.address, actual.data(), actual.size()) || actual != expected)
            fail(std::string("native patch preimage mismatch: ") + source.id);
        operation.original_protection = region.Protect;
    }
    std::sort(ranges.begin(), ranges.end());
    for (std::size_t index = 1; index < ranges.size(); ++index)
        if (ranges[index - 1].second > ranges[index].first)
            fail("selected native operations overlap");
}

std::vector<ImageOperation> selected_operations(const Config& config) {
    const std::uint32_t requested =
        (config_needs_randomizer_hooks(config) ? rmod1_plan::kFeatureRandomizer : 0u) |
        (config_requests_opponent_extension(config) ? rmod1_plan::kFeatureOpponents : 0u);
    std::vector<ImageOperation> result;
    const bool diagnostic_bootstrap = config.logging_enabled;
    if (requested == 0 && !diagnostic_bootstrap) return result;
    for (std::size_t index = 0; index < rmod1_plan::kOperationCount; ++index) {
        const auto& op = rmod1_plan::kOperations[index];
        if (runtime_operation_selected(op.feature, requested, rmod1_plan::kFeatureBootstrap,
                                       config.logging_enabled))
            result.push_back({&op, {}, 0, 0});
    }
    if (config_requests_opponent_extension(config)) {
        bool arrow_found = false;
        for (auto& operation : result) {
            if (std::string_view(operation.source->id) == "opponent-arrow-bound") {
                operation.replacement = decode_hex(operation.source->replacement_hex);
                if (operation.replacement.size() != 3) fail("opponent arrow patch template has the wrong length");
                operation.replacement[2] = static_cast<std::uint8_t>(config.max_opponents - 1);
                arrow_found = true;
            }
        }
        if (!arrow_found) fail("opponent feature plan has no arrow-bound operation");
    }
    return result;
}

void verify_remote_allocation_is_free(HANDLE process, std::uintptr_t address, std::size_t size) {
    MEMORY_BASIC_INFORMATION region{};
    if (VirtualQueryEx(process, reinterpret_cast<LPCVOID>(address), &region, sizeof(region)) != sizeof(region) ||
        region.State != MEM_FREE || reinterpret_cast<std::uintptr_t>(region.BaseAddress) > address ||
        address + size > reinterpret_cast<std::uintptr_t>(region.BaseAddress) + region.RegionSize)
        fail("fixed R-MOD1 remote address is unavailable; refusing to choose an unverified relocation");
}

std::vector<std::uint8_t> make_remote_data(const Files& files) {
    auto data = decode_template(rmod1_plan::kDataTemplate, rmod1_plan::kDataTemplateSize,
        rmod1_plan::kDataUsed, rmod1_plan::kDataTemplateSha256, rmod1_plan::kDataSize);
    const std::wstring dll_path = absolute_path(files.runtime_dll).wstring();
    if (dll_path.empty() || dll_path.size() > 259)
        fail("runtime DLL path exceeds the supported absolute-path limit (259 UTF-16 characters)");
    const std::size_t path_offset = rmod1_plan::kDllPathOffset;
    const std::size_t path_bytes = (dll_path.size() + 1) * sizeof(wchar_t);
    if (path_offset > data.size() || path_bytes > data.size() - path_offset ||
        path_offset + path_bytes > 0x2200)
        fail("runtime DLL path overlaps the generated export-name table");
    std::memcpy(data.data() + path_offset, dll_path.c_str(), path_bytes);

    std::vector<std::uint8_t> config(4 + files.ini_bytes.size(), 0);
    if (files.ini_bytes.size() > kMaxIniBytes) fail("validated INI unexpectedly exceeds its bound");
    const auto length = static_cast<std::uint32_t>(files.ini_bytes.size());
    config[0] = static_cast<std::uint8_t>(length & 0xffu);
    config[1] = static_cast<std::uint8_t>((length >> 8) & 0xffu);
    config[2] = static_cast<std::uint8_t>((length >> 16) & 0xffu);
    config[3] = static_cast<std::uint8_t>((length >> 24) & 0xffu);
    if (length) std::copy(files.ini_bytes.begin(), files.ini_bytes.end(), config.begin() + 4);
    const std::size_t config_offset = rmod1_plan::kConfigOffset;
    if (config_offset > data.size() || config.size() > data.size() - config_offset ||
        config_offset + config.size() > rmod1_plan::kDllPathOffset)
        fail("INI blob overlaps another remote data object");
    std::copy(config.begin(), config.end(), data.begin() + static_cast<std::ptrdiff_t>(config_offset));
    return data;
}

void install_runtime(HANDLE process, std::uintptr_t image_base, const PeInfo& pe,
                     const Files& files, std::vector<ImageOperation>& operations) {
    verify_remote_allocation_is_free(process, rmod1_plan::kCodeBase, rmod1_plan::kCodeSize);
    verify_remote_allocation_is_free(process, rmod1_plan::kDataBase, rmod1_plan::kDataSize);
    verify_all_preimages(process, image_base, pe, operations);

    auto code = decode_template(rmod1_plan::kCodeTemplate, rmod1_plan::kCodeTemplateSize,
        rmod1_plan::kCodeUsed, rmod1_plan::kCodeTemplateSha256, rmod1_plan::kCodeSize);
    auto data = make_remote_data(files);
    auto* remote_code = VirtualAllocEx(process, reinterpret_cast<LPVOID>(static_cast<std::uintptr_t>(rmod1_plan::kCodeBase)),
        rmod1_plan::kCodeSize, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (remote_code != reinterpret_cast<LPVOID>(static_cast<std::uintptr_t>(rmod1_plan::kCodeBase)))
        fail(win_error("cannot reserve the exact R-MOD1 code region"));
    auto* remote_data = VirtualAllocEx(process, reinterpret_cast<LPVOID>(static_cast<std::uintptr_t>(rmod1_plan::kDataBase)),
        rmod1_plan::kDataSize, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (remote_data != reinterpret_cast<LPVOID>(static_cast<std::uintptr_t>(rmod1_plan::kDataBase)))
        fail(win_error("cannot reserve the exact R-MOD1 data region"));
    if (!write_process(process, rmod1_plan::kCodeBase, code.data(), code.size()) ||
        !write_process(process, rmod1_plan::kDataBase, data.data(), data.size()))
        fail(win_error("cannot write complete R-MOD1 remote templates"));
    std::vector<std::uint8_t> readback(code.size());
    if (!read_process(process, rmod1_plan::kCodeBase, readback.data(), readback.size()) || readback != code)
        fail("remote code allocation read-back differs from the generated template");
    readback.resize(data.size());
    if (!read_process(process, rmod1_plan::kDataBase, readback.data(), readback.size()) || readback != data)
        fail("remote data allocation read-back differs from the generated runtime values");

    DWORD old_code_protection = 0;
    if (!VirtualProtectEx(process, remote_code, rmod1_plan::kCodeSize, PAGE_EXECUTE_READ, &old_code_protection))
        fail(win_error("cannot make verified code region read/execute"));
    if (old_code_protection != PAGE_READWRITE)
        fail("remote code region had an unexpected pre-protection");

    for (auto& operation : operations) {
        if (std::string_view(operation.source->id) != "opponent-arrow-bound")
            operation.replacement = decode_hex(operation.source->replacement_hex);
        DWORD old_protection = 0;
        if (!VirtualProtectEx(process, reinterpret_cast<LPVOID>(operation.address),
                              operation.replacement.size(), PAGE_READWRITE, &old_protection))
            fail(win_error((std::string("cannot open native patch page for ") + operation.source->id).c_str()));
        if (old_protection != operation.original_protection)
            fail("native patch page protection changed after complete preflight");
        const bool written = write_process(process, operation.address,
                                            operation.replacement.data(), operation.replacement.size());
        std::vector<std::uint8_t> check(operation.replacement.size());
        const bool read = written && read_process(process, operation.address, check.data(), check.size());
        const bool matched = read && check == operation.replacement;
        DWORD ignored = 0;
        const bool restored = VirtualProtectEx(process, reinterpret_cast<LPVOID>(operation.address),
            operation.replacement.size(), operation.original_protection, &ignored) != FALSE;
        if (!written || !read || !matched || !restored)
            fail(std::string("partial native patch installation at ") + operation.source->id +
                 "; suspended process will be terminated");
        if (!FlushInstructionCache(process, reinterpret_cast<LPCVOID>(operation.address),
                                   operation.replacement.size()))
            fail(win_error("FlushInstructionCache failed after a native patch"));
    }
    if (!FlushInstructionCache(process, remote_code, code.size()))
        fail(win_error("FlushInstructionCache failed for R-MOD1 code"));
    std::cout << "runtime_install=verified operations=" << operations.size()
              << " remote_code=0x" << std::hex << rmod1_plan::kCodeBase
              << " remote_data=0x" << rmod1_plan::kDataBase << std::dec << "\n";
}

std::wstring quote_argument(const std::wstring& value) {
    std::wstring result = L"\"";
    unsigned slashes = 0;
    for (wchar_t c : value) {
        if (c == L'\\') { ++slashes; continue; }
        if (c == L'"') {
            result.append(slashes * 2 + 1, L'\\');
            result.push_back(c);
            slashes = 0;
            continue;
        }
        result.append(slashes, L'\\');
        slashes = 0;
        result.push_back(c);
    }
    result.append(slashes * 2, L'\\');
    result.push_back(L'"');
    return result;
}

int suspended_preflight(const fs::path& runtime_dir, const fs::path& game_dir) {
    Files files = verify_files(runtime_dir, game_dir);
    FilePin executable_pin(files.executable);
    FilePin runtime_pin(files.runtime_dll);
    if (read_handle(executable_pin.handle, rmod1_plan::kRetailSize) != files.executable_bytes ||
        read_handle(runtime_pin.handle, 32u * 1024u * 1024u) != files.runtime_bytes)
        fail("a pinned runtime input changed before suspended-process preflight");
    const PeInfo pe = parse_pe(files.executable_bytes);

    ProcessHandles child;
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process_info{};
    std::wstring command = quote_argument(files.executable.wstring());
    std::vector<wchar_t> command_line(command.begin(), command.end());
    command_line.push_back(L'\0');
    if (!CreateProcessW(files.executable.c_str(), command_line.data(), nullptr, nullptr, FALSE,
        CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT, nullptr, files.game_dir.c_str(), &startup, &process_info))
        fail(win_error("cannot create original game suspended for preflight"));
    child.process = process_info.hProcess;
    child.thread = process_info.hThread;

    wchar_t image_path[32768]{};
    DWORD image_path_length = static_cast<DWORD>(std::size(image_path));
    if (!QueryFullProcessImageNameW(child.process, 0, image_path, &image_path_length) ||
        normalized_path(fs::path(std::wstring(image_path, image_path_length))) != normalized_path(files.executable))
        fail("suspended preflight image path is not the exact requested retail executable");
    require_x86_target(child.process);
    const std::uintptr_t image_base = verify_module_mapping(child.process, files.executable_bytes, pe);
    if (image_base != pe.image_base)
        fail("suspended preflight mapping did not use the audited fixed image base");

    if (!TerminateProcess(child.process, 0xE014u))
        fail(win_error("cannot terminate verified suspended preflight child"));
    if (WaitForSingleObject(child.process, 5000) != WAIT_OBJECT_0)
        fail(win_error("verified suspended preflight child did not terminate"));
    child.exited = true;
    const auto after = read_handle(executable_pin.handle, rmod1_plan::kRetailSize);
    if (after.size() != rmod1_plan::kRetailSize || sha256(after) != rmod1_plan::kRetailSha256)
        fail("on-disk retail executable changed during suspended preflight");
    std::cout << "suspended_process_preflight=verified native_writes=0"
              << " child_terminated_before_resume=1 on_disk_exe=unchanged\n"
              << "SUSPENDED_PREFLIGHT_PASS base=0x" << std::hex << image_base << std::dec
              << " size=" << pe.image_size << "\n";
    return 0;
}

int launch(const fs::path& runtime_dir, const fs::path& game_dir) {
    Files files = verify_files(runtime_dir, game_dir);
    FilePin executable_pin(files.executable);
    FilePin runtime_pin(files.runtime_dll);
    if (read_handle(executable_pin.handle, rmod1_plan::kRetailSize) != files.executable_bytes ||
        read_handle(runtime_pin.handle, 32u * 1024u * 1024u) != files.runtime_bytes)
        fail("a pinned runtime input changed between verification and process creation");
    const PeInfo pe = parse_pe(files.executable_bytes);
    std::cout << "retail_sha256=" << rmod1_plan::kRetailSha256 << " size="
              << rmod1_plan::kRetailSize << "\n";
    std::cout << "runtime_core_sha256=" << rmod1_plan::kRuntimeCoreSha256
              << " plan_sha256=" << rmod1_plan::kPlanSha256 << "\n";
    std::cout << "configuration=" << files.ini_diagnostic << "\n";
    std::cout << config_summary(files.config) << "\n";

    const bool enable_mod = config_needs_randomizer_hooks(files.config) ||
                            config_requests_opponent_extension(files.config) ||
                            files.config.logging_enabled;
    ProcessHandles child;
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process_info{};
    std::wstring command = quote_argument(files.executable.wstring());
    std::vector<wchar_t> command_line(command.begin(), command.end());
    command_line.push_back(L'\0');
    if (!CreateProcessW(files.executable.c_str(), command_line.data(), nullptr, nullptr, FALSE,
        CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT, nullptr, files.game_dir.c_str(), &startup, &process_info))
        fail(win_error("cannot create original game suspended"));
    child.process = process_info.hProcess;
    child.thread = process_info.hThread;

    wchar_t image_path[32768]{};
    DWORD image_path_length = static_cast<DWORD>(std::size(image_path));
    if (!QueryFullProcessImageNameW(child.process, 0, image_path, &image_path_length) ||
        normalized_path(fs::path(std::wstring(image_path, image_path_length))) != normalized_path(files.executable))
        fail("suspended process image path is not the exact requested retail executable");
    require_x86_target(child.process);
    const std::uintptr_t image_base = verify_module_mapping(child.process, files.executable_bytes, pe);
    auto operations = selected_operations(files.config);
    if (enable_mod) {
        if (operations.empty()) fail("enabled feature configuration produced no native operations");
        install_runtime(child.process, image_base, pe, files, operations);
    } else {
        std::cout << "runtime_install=disabled; launching original retail process without native writes\n";
    }

    const DWORD previous_suspend_count = ResumeThread(child.thread);
    if (previous_suspend_count != 1) {
        TerminateProcess(child.process, 0xE012u);
        WaitForSingleObject(child.process, 5000);
        fail("primary thread suspend count was not exactly one; process terminated before startup");
    }
    child.resumed = true;
    std::cout << "process_resumed=1 external_d3d8_proxy=untouched\n";
    const DWORD wait = WaitForSingleObject(child.process, INFINITE);
    if (wait != WAIT_OBJECT_0) fail(win_error("waiting for game process failed"));
    DWORD game_exit_code = 0;
    if (!GetExitCodeProcess(child.process, &game_exit_code)) fail(win_error("cannot read game exit code"));
    const auto after = read_handle(executable_pin.handle, rmod1_plan::kRetailSize);
    if (after.size() != rmod1_plan::kRetailSize || sha256(after) != rmod1_plan::kRetailSha256)
        fail("on-disk retail executable changed during the game session");
    if (game_exit_code == 0xE011u)
        fail("OEP bootstrap failed closed: runtime core load, ABI resolution or configuration failed");
    std::cout << "on_disk_exe_after_exit=unchanged game_exit_code=" << game_exit_code << "\n";
    return static_cast<int>(game_exit_code & 0xffu);
}

void print_usage() {
    std::cout << "R-MOD1 external suspended-process launcher (static candidate)\n"
              << "Usage: MRallyeRandomizerLauncher.exe [--verify|--preflight] [--game-dir PATH]\n"
              << "Place launcher, runtime DLL and INI in the mod directory. The exact retail\n"
              << "MRallye.exe is resolved from --game-dir, or from this directory by default.\n"
              << "--preflight creates the exact retail process suspended, verifies its mapped\n"
              << "image without installing patches, then terminates it before resume.\n";
}

} // namespace

int wmain(int argc, wchar_t** argv) {
    try {
        bool verify_only = false;
        bool preflight_only = false;
        fs::path game_dir;
        for (int index = 1; index < argc; ++index) {
            const std::wstring_view arg(argv[index]);
            if (arg == L"--verify") {
                verify_only = true;
            } else if (arg == L"--preflight") {
                preflight_only = true;
            } else if (arg == L"--game-dir" && index + 1 < argc) {
                game_dir = argv[++index];
            } else if (arg == L"--help" || arg == L"-h") {
                print_usage();
                return 0;
            } else {
                print_usage();
                fail("unknown or incomplete launcher argument");
            }
        }
        const fs::path runtime_dir = module_directory();
        if (game_dir.empty()) game_dir = runtime_dir;
        game_dir = absolute_path(game_dir);
        if (verify_only && preflight_only)
            fail("--verify and --preflight are separate modes");
        if (verify_only) {
            const auto files = verify_files(runtime_dir, game_dir);
            std::cout << "VERIFY_PASS retail_sha256=" << rmod1_plan::kRetailSha256
                      << " runtime_core_sha256=" << rmod1_plan::kRuntimeCoreSha256
                      << " plan_sha256=" << rmod1_plan::kPlanSha256 << "\n"
                      << "configuration=" << files.ini_diagnostic << "\n"
                      << config_summary(files.config) << "\n"
                      << "features=randomizer:" << (config_needs_randomizer_hooks(files.config) ? "on" : "off")
                      << ",opponents:" << (config_requests_opponent_extension(files.config) ? "on" : "off")
                      << ",max_ai=" << files.config.max_opponents << "\n";
            return 0;
        }
        if (preflight_only) return suspended_preflight(runtime_dir, game_dir);
        return launch(runtime_dir, game_dir);
    } catch (const std::exception& error) {
        std::cerr << "R-MOD1 FAIL-CLOSED: " << error.what() << "\n";
        return 2;
    }
}
