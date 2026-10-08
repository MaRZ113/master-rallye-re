#include <windows.h>
#include <winternl.h>
#include <bcrypt.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <cwctype>
#include <limits>

#include "trusted_profile.hpp"

#pragma comment(lib, "bcrypt.lib")

namespace fs = std::filesystem;

namespace {

constexpr uint32_t kRetailSize = 3121214;
constexpr uint32_t kExpectedImageBase = 0x00400000;
constexpr uint16_t kMachineI386 = 0x014C;
constexpr uint32_t kRvpHeaderSize = 120;
constexpr uint32_t kRvpOperationHeaderSize = 12;
constexpr uint8_t kFileOnly = 1;
constexpr uint8_t kNoopCanary = 2;
constexpr uint8_t kPageCode = 1;
constexpr uint8_t kPageData = 2;

struct Section {
    std::string name;
    uint32_t virtualSize{};
    uint32_t rva{};
    uint32_t rawSize{};
    uint32_t rawOffset{};
    uint32_t characteristics{};
};

struct PeInfo {
    uint16_t machine{};
    uint16_t characteristics{};
    uint32_t imageBase{};
    uint32_t imageSize{};
    uint32_t headersSize{};
    std::vector<Section> sections;
};

struct Operation {
    uint32_t fileOffset{};
    uint32_t rva{};
    uint16_t length{};
    uint8_t flags{};
    uint8_t pageClass{};
    std::vector<uint8_t> before;
    std::vector<uint8_t> after;
};

struct RuntimePlan {
    PeInfo pe;
    std::vector<uint8_t> source;
    std::vector<uint8_t> reconstructed;
    std::vector<Operation> operations;
};

[[noreturn]] void Fail(const std::string& message) {
    throw std::runtime_error(message);
}

std::wstring Lower(std::wstring value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](wchar_t c) { return static_cast<wchar_t>(towlower(c)); });
    return value;
}

std::string Sha256Bytes(const uint8_t* data, size_t size) {
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    DWORD objectLength{}, hashLength{}, received{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0)
        Fail("BCryptOpenAlgorithmProvider(SHA256) failed");
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&objectLength), sizeof(objectLength), &received, 0) < 0
        || BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                             reinterpret_cast<PUCHAR>(&hashLength), sizeof(hashLength), &received, 0) < 0) {
        BCryptCloseAlgorithmProvider(algorithm, 0);
        Fail("BCryptGetProperty failed");
    }
    std::vector<uint8_t> object(objectLength), output(hashLength);
    NTSTATUS status = BCryptCreateHash(algorithm, &hash, object.data(), objectLength, nullptr, 0, 0);
    if (status >= 0 && size != 0)
        status = BCryptHashData(hash, const_cast<PUCHAR>(data), static_cast<ULONG>(size), 0);
    if (status >= 0)
        status = BCryptFinishHash(hash, output.data(), hashLength, 0);
    if (hash) BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (status < 0) Fail("BCrypt SHA256 computation failed");
    static constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(output.size() * 2);
    for (uint8_t b : output) {
        result.push_back(digits[b >> 4]);
        result.push_back(digits[b & 0x0F]);
    }
    return result;
}

std::vector<uint8_t> ReadFileBytes(const fs::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) Fail("cannot read file: " + path.string());
    file.seekg(0, std::ios::end);
    const auto size = file.tellg();
    if (size < 0) Fail("cannot determine file size: " + path.string());
    file.seekg(0, std::ios::beg);
    std::vector<uint8_t> bytes(static_cast<size_t>(size));
    if (!bytes.empty() && !file.read(reinterpret_cast<char*>(bytes.data()), size))
        Fail("short read: " + path.string());
    return bytes;
}

std::string HashFile(const fs::path& path) {
    HANDLE file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                              FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    if (file == INVALID_HANDLE_VALUE) Fail("cannot open for hash: " + path.string());
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    DWORD objectLength{}, hashLength{}, received{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) {
        CloseHandle(file); Fail("cannot initialize SHA256 provider");
    }
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&objectLength), sizeof(objectLength), &received, 0) < 0
        || BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                             reinterpret_cast<PUCHAR>(&hashLength), sizeof(hashLength), &received, 0) < 0) {
        BCryptCloseAlgorithmProvider(algorithm, 0); CloseHandle(file); Fail("cannot read SHA256 properties");
    }
    std::vector<uint8_t> object(objectLength), output(hashLength), buffer(1024 * 1024);
    NTSTATUS status = BCryptCreateHash(algorithm, &hash, object.data(), objectLength, nullptr, 0, 0);
    DWORD got{};
    bool readError = false;
    while (status >= 0) {
        if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()), &got, nullptr)) {
            readError = true;
            break;
        }
        if (got == 0) break;
        status = BCryptHashData(hash, buffer.data(), got, 0);
    }
    if (status >= 0 && !readError) status = BCryptFinishHash(hash, output.data(), hashLength, 0);
    if (hash) BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    CloseHandle(file);
    if (status < 0 || readError) Fail("SHA256 read/hash failed: " + path.string());
    static constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(output.size() * 2);
    for (uint8_t b : output) { result.push_back(digits[b >> 4]); result.push_back(digits[b & 0x0F]); }
    return result;
}

bool FileHashEquals(const fs::path& path, const char* expected, const char* label) {
    const DWORD attributes = GetFileAttributesW(path.c_str());
    if (!fs::is_regular_file(path) || attributes == INVALID_FILE_ATTRIBUTES
        || (attributes & FILE_ATTRIBUTE_REPARSE_POINT))
        Fail(std::string(label) + " is missing, linked, or not a regular file");
    const auto hash = HashFile(path);
    if (hash != expected)
        Fail(std::string(label) + " SHA256 mismatch");
    return true;
}

uint16_t U16(const std::vector<uint8_t>& bytes, size_t at) {
    if (at + 2 > bytes.size()) Fail("truncated 16-bit value");
    return static_cast<uint16_t>(bytes[at] | (static_cast<uint16_t>(bytes[at + 1]) << 8));
}

uint32_t U32(const std::vector<uint8_t>& bytes, size_t at) {
    if (at + 4 > bytes.size()) Fail("truncated 32-bit value");
    return static_cast<uint32_t>(bytes[at]) | (static_cast<uint32_t>(bytes[at + 1]) << 8)
         | (static_cast<uint32_t>(bytes[at + 2]) << 16) | (static_cast<uint32_t>(bytes[at + 3]) << 24);
}

PeInfo ParsePe(const std::vector<uint8_t>& bytes) {
    if (bytes.size() < 0x100 || bytes[0] != 'M' || bytes[1] != 'Z') Fail("input is not an MZ executable");
    const uint32_t peOffset = U32(bytes, 0x3C);
    if (peOffset + 24 > bytes.size() || std::memcmp(bytes.data() + peOffset, "PE\0\0", 4) != 0)
        Fail("invalid PE signature");
    PeInfo info;
    info.machine = U16(bytes, peOffset + 4);
    const uint16_t sectionCount = U16(bytes, peOffset + 6);
    const uint16_t optionalSize = U16(bytes, peOffset + 20);
    info.characteristics = U16(bytes, peOffset + 22);
    const size_t optional = peOffset + 24;
    if (optional + optionalSize > bytes.size() || U16(bytes, optional) != 0x10B)
        Fail("only PE32 images are supported");
    info.imageBase = U32(bytes, optional + 28);
    info.imageSize = U32(bytes, optional + 56);
    info.headersSize = U32(bytes, optional + 60);
    const size_t sectionTable = optional + optionalSize;
    for (uint16_t index = 0; index < sectionCount; ++index) {
        const size_t at = sectionTable + static_cast<size_t>(index) * 40;
        if (at + 40 > bytes.size()) Fail("truncated PE section table");
        Section section;
        char name[9]{};
        std::memcpy(name, bytes.data() + at, 8);
        section.name = name;
        section.virtualSize = U32(bytes, at + 8);
        section.rva = U32(bytes, at + 12);
        section.rawSize = U32(bytes, at + 16);
        section.rawOffset = U32(bytes, at + 20);
        section.characteristics = U32(bytes, at + 36);
        if (section.rawOffset + section.rawSize > bytes.size()) Fail("PE section exceeds file bounds");
        info.sections.push_back(section);
    }
    if (info.machine != kMachineI386 || info.imageBase != kExpectedImageBase
        || (info.characteristics & IMAGE_FILE_RELOCS_STRIPPED) == 0)
        Fail("unsupported PE machine, preferred base, or relocation profile");
    return info;
}

std::pair<uint32_t, const Section*> FileToRva(const PeInfo& pe, uint32_t offset, uint32_t size) {
    for (const auto& section : pe.sections) {
        if (offset >= section.rawOffset && static_cast<uint64_t>(offset) + size
            <= static_cast<uint64_t>(section.rawOffset) + section.rawSize)
            return {section.rva + offset - section.rawOffset, &section};
    }
    Fail("patch range does not map to one file-backed PE section");
}

RuntimePlan ParsePatchPlan(const fs::path& exePath, const fs::path& opsPath,
                           const fs::path& planPath) {
    FileHashEquals(exePath, MR_RETAIL_SHA256, "retail executable");
    FileHashEquals(planPath, MR_ADDON_PLAN_SHA256, "J.0 addon plan");
    FileHashEquals(opsPath, MR_PATCH_OPS_SHA256, "native operation table");
    auto source = ReadFileBytes(exePath);
    if (source.size() != kRetailSize) Fail("retail executable size mismatch");
    RuntimePlan result;
    result.pe = ParsePe(source);
    result.source = source;
    result.reconstructed = source;
    auto bytes = ReadFileBytes(opsPath);
    if (bytes.size() < kRvpHeaderSize || std::memcmp(bytes.data(), "MRVP", 4) != 0)
        Fail("invalid RVP1 native operation header");
    if (U16(bytes, 4) != 1 || U16(bytes, 6) != kMachineI386
        || U32(bytes, 8) != kExpectedImageBase || U32(bytes, 12) != kRetailSize
        || U32(bytes, 16) != kRetailSize)
        Fail("RVP1 version, architecture, base or image-size mismatch");
    const uint32_t count = U32(bytes, 20);
    if (count != MR_PATCH_OPERATION_COUNT || count > 512) Fail("RVP1 operation count mismatch");
    const auto sourceSha = Sha256Bytes(source.data(), source.size());
    const auto candidateSha = std::string(MR_REFERENCE_IMAGE_SHA256);
    const auto planSha = std::string(MR_ADDON_PLAN_SHA256);
    auto hexAt = [&](size_t at) {
        static constexpr char digits[] = "0123456789abcdef";
        std::string value;
        for (size_t i = 0; i < 32; ++i) {
            const uint8_t b = bytes[at + i];
            value.push_back(digits[b >> 4]); value.push_back(digits[b & 0x0F]);
        }
        return value;
    };
    if (hexAt(24) != sourceSha || sourceSha != MR_RETAIL_SHA256
        || hexAt(56) != candidateSha || hexAt(88) != planSha)
        Fail("RVP1 build identity fields do not match the trusted runtime profile");

    size_t cursor = kRvpHeaderSize;
    std::vector<std::pair<uint32_t, uint32_t>> fileRanges, rvaRanges;
    result.operations.reserve(count);
    for (uint32_t index = 0; index < count; ++index) {
        if (cursor + kRvpOperationHeaderSize > bytes.size()) Fail("truncated RVP1 operation header");
        Operation op;
        op.fileOffset = U32(bytes, cursor);
        op.rva = U32(bytes, cursor + 4);
        op.length = U16(bytes, cursor + 8);
        op.flags = bytes[cursor + 10];
        op.pageClass = bytes[cursor + 11];
        cursor += kRvpOperationHeaderSize;
        if (op.length == 0 || op.length > 8192 || cursor + static_cast<size_t>(op.length) * 2 > bytes.size())
            Fail("invalid or truncated RVP1 operation bytes");
        op.before.assign(bytes.begin() + cursor, bytes.begin() + cursor + op.length);
        cursor += op.length;
        op.after.assign(bytes.begin() + cursor, bytes.begin() + cursor + op.length);
        cursor += op.length;
        if (static_cast<uint64_t>(op.fileOffset) + op.length > result.source.size())
            Fail("RVP1 operation exceeds the retail file");
        if (!std::equal(op.before.begin(), op.before.end(), result.source.begin() + op.fileOffset))
            Fail("RVP1 file preimage differs from the exact retail file");
        for (const auto& range : fileRanges)
            if (op.fileOffset < range.second && range.first < op.fileOffset + op.length)
                Fail("RVP1 file operations overlap");
        fileRanges.emplace_back(op.fileOffset, op.fileOffset + op.length);
        std::copy(op.after.begin(), op.after.end(), result.reconstructed.begin() + op.fileOffset);

        if (op.flags == kFileOnly) {
            if (op.rva != 0xFFFFFFFF || op.pageClass != 0) Fail("invalid file-only RVP1 entry");
        } else {
            if ((op.flags != 0 && op.flags != kNoopCanary)
                || (op.pageClass != kPageCode && op.pageClass != kPageData))
                Fail("unsupported RVP1 memory operation flags");
            if (op.flags == kNoopCanary && op.before != op.after)
                Fail("no-op canary must preserve its exact original bytes");
            const auto [mappedRva, section] = FileToRva(result.pe, op.fileOffset, op.length);
            if (mappedRva != op.rva || op.rva + op.length > result.pe.imageSize)
                Fail("RVP1 RVA does not match PE file mapping");
            if ((section->name == ".text") != (op.pageClass == kPageCode))
                Fail("RVP1 protection class disagrees with PE section owner");
            for (const auto& range : rvaRanges)
                if (op.rva < range.second && range.first < op.rva + op.length)
                    Fail("RVP1 process-memory operations overlap");
            rvaRanges.emplace_back(op.rva, op.rva + op.length);
        }
        result.operations.push_back(std::move(op));
    }
    if (cursor != bytes.size()) Fail("RVP1 contains trailing bytes");
    if (Sha256Bytes(result.reconstructed.data(), result.reconstructed.size()) != candidateSha)
        Fail("RVP1 operations do not reproduce the trusted in-memory image");
    return result;
}

std::string Utf8Path(const fs::path& path) {
    const auto value = path.generic_u8string();
    return std::string(reinterpret_cast<const char*>(value.data()), value.size());
}

std::wstring Utf8Wide(const std::string& value) {
    if (value.empty()) return {};
    const int length = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                                           static_cast<int>(value.size()), nullptr, 0);
    if (length <= 0) Fail("resource index contains invalid UTF-8");
    std::wstring result(static_cast<size_t>(length), L'\0');
    if (MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                            static_cast<int>(value.size()), result.data(), length) != length)
        Fail("resource path UTF-8 conversion failed");
    return result;
}

std::string TrimCR(std::string value) {
    if (!value.empty() && value.back() == '\r') value.pop_back();
    return value;
}

void VerifyResourceRoot(const fs::path& root, const fs::path& indexPath) {
    FileHashEquals(indexPath, MR_RESOURCE_INDEX_SHA256, "resource index");
    const fs::path manifestPath = indexPath.parent_path() / L"resource-manifest.json";
    FileHashEquals(manifestPath, MR_RESOURCE_MANIFEST_SHA256, "resource manifest");
    const DWORD rootAttributes = GetFileAttributesW(root.c_str());
    if (!fs::is_directory(root) || fs::is_symlink(root)
        || rootAttributes == INVALID_FILE_ATTRIBUTES
        || (rootAttributes & FILE_ATTRIBUTE_REPARSE_POINT))
        Fail("resource root is missing or link-backed");
    std::ifstream indexFile(indexPath, std::ios::binary);
    if (!indexFile) Fail("cannot open resource index");
    std::set<std::wstring> expected;
    std::string line;
    uint32_t count = 0;
    while (std::getline(indexFile, line)) {
        line = TrimCR(line);
        const auto first = line.find('\t');
        const auto second = first == std::string::npos ? first : line.find('\t', first + 1);
        if (first != 64 || second == std::string::npos) Fail("malformed resource index row");
        const std::string digest = line.substr(0, first);
        const std::string sizeText = line.substr(first + 1, second - first - 1);
        const std::string relative = line.substr(second + 1);
        if (relative.empty() || relative.find('|') != std::string::npos || relative.find('\0') != std::string::npos)
            Fail("unsafe resource index path");
        const auto utf8 = std::u8string(reinterpret_cast<const char8_t*>(relative.data()), relative.size());
        fs::path rel(utf8);
        if (rel.is_absolute()) Fail("absolute resource path rejected");
        for (const auto& component : rel)
            if (component == L".." || component == L".")
                Fail("resource path traversal rejected");
        uint64_t expectedSize{};
        try {
            size_t parsed{};
            expectedSize = std::stoull(sizeText, &parsed);
            if (parsed != sizeText.size()) Fail("invalid resource size in index");
        }
        catch (...) { Fail("invalid resource size in index"); }
        const auto key = Lower(rel.generic_wstring());
        if (!expected.insert(key).second) Fail("duplicate case-insensitive resource path");
        const fs::path full = root / rel;
        if (!fs::is_regular_file(full) || fs::is_symlink(full)) Fail("indexed resource is missing or linked: " + relative);
        if (fs::file_size(full) != expectedSize) Fail("resource size mismatch: " + relative);
        if (HashFile(full) != digest) Fail("resource SHA256 mismatch: " + relative);
        ++count;
    }
    if (count != MR_RESOURCE_COUNT) Fail("resource count differs from trusted profile");

    std::set<std::wstring> actual;
    const std::set<std::wstring> runtimeState = {
        L"datagame/playerstate.xml", L"datagame/playerstate.xml#", L"datagame/options.xml#"
    };
    for (const auto& entry : fs::recursive_directory_iterator(root)) {
        const DWORD attrs = GetFileAttributesW(entry.path().c_str());
        if (attrs == INVALID_FILE_ATTRIBUTES || (attrs & FILE_ATTRIBUTE_REPARSE_POINT))
            Fail("resource root contains a reparse point");
        if (entry.is_regular_file()) {
            auto relative = Lower(entry.path().lexically_relative(root).generic_wstring());
            if (!runtimeState.contains(relative)) actual.insert(std::move(relative));
        }
    }
    if (actual != expected) Fail("resource-root file set differs from the sealed index");
    if (fs::exists(root / L"MRallye.exe")) Fail("resource root must not contain a replacement executable");
    std::cout << "RESOURCE_ROOT_VERIFIED files=" << count << " index=" << MR_RESOURCE_INDEX_SHA256 << "\n";
}

HANDLE OpenPinnedRetail(const fs::path& path) {
    HANDLE file = CreateFileW(path.c_str(), GENERIC_READ | FILE_READ_ATTRIBUTES, FILE_SHARE_READ,
                              nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) Fail("cannot pin retail executable against writes/replacement");
    BY_HANDLE_FILE_INFORMATION info{};
    if (!GetFileInformationByHandle(file, &info)) { CloseHandle(file); Fail("cannot identify retail file handle"); }
    LARGE_INTEGER size{};
    if (!GetFileSizeEx(file, &size) || size.QuadPart != kRetailSize) {
        CloseHandle(file); Fail("pinned retail executable size mismatch");
    }
    return file;
}

std::string HashHandle(HANDLE file) {
    LARGE_INTEGER start{};
    if (!SetFilePointerEx(file, start, nullptr, FILE_BEGIN)) Fail("cannot rewind pinned retail image");
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    DWORD objectLength{}, hashLength{}, received{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0)
        Fail("cannot initialize SHA256 provider for pinned retail image");
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH, reinterpret_cast<PUCHAR>(&objectLength), sizeof(objectLength), &received, 0) < 0
        || BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH, reinterpret_cast<PUCHAR>(&hashLength), sizeof(hashLength), &received, 0) < 0) {
        BCryptCloseAlgorithmProvider(algorithm, 0); Fail("cannot read SHA256 properties");
    }
    std::vector<uint8_t> object(objectLength), output(hashLength), buffer(65536);
    NTSTATUS status = BCryptCreateHash(algorithm, &hash, object.data(), objectLength, nullptr, 0, 0);
    DWORD got{};
    bool readError = false;
    while (status >= 0) {
        if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()), &got, nullptr)) {
            readError = true;
            break;
        }
        if (got == 0) break;
        status = BCryptHashData(hash, buffer.data(), got, 0);
    }
    if (status >= 0 && !readError) status = BCryptFinishHash(hash, output.data(), hashLength, 0);
    if (hash) BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (status < 0 || readError) Fail("pinned retail hash failed");
    static constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(output.size() * 2);
    for (uint8_t b : output) { result.push_back(digits[b >> 4]); result.push_back(digits[b & 0x0F]); }
    return result;
}

bool SameFileIdentity(HANDLE left, HANDLE right) {
    BY_HANDLE_FILE_INFORMATION a{}, b{};
    return GetFileInformationByHandle(left, &a) && GetFileInformationByHandle(right, &b)
        && a.dwVolumeSerialNumber == b.dwVolumeSerialNumber
        && a.nFileIndexHigh == b.nFileIndexHigh && a.nFileIndexLow == b.nFileIndexLow;
}

uintptr_t ProcessImageBase32(HANDLE process) {
    using NtQueryFn = LONG(NTAPI*)(HANDLE, INT, PVOID, ULONG, PULONG);
    auto query = reinterpret_cast<NtQueryFn>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "NtQueryInformationProcess"));
    if (!query) Fail("NtQueryInformationProcess is unavailable");
    ULONG_PTR peb32{};
    const LONG status = query(process, 26, &peb32, sizeof(peb32), nullptr); // ProcessWow64Information
    if (status < 0 || peb32 == 0) Fail("target process is not a queryable 32-bit WOW64 process");
    uint32_t imageBase{};
    SIZE_T read{};
    if (!ReadProcessMemory(process, reinterpret_cast<LPCVOID>(peb32 + 0x08), &imageBase, sizeof(imageBase), &read)
        || read != sizeof(imageBase)) Fail("cannot read WOW64 PEB32 ImageBaseAddress");
    return imageBase;
}

void VerifyProcessIdentity(const PROCESS_INFORMATION& pi, HANDLE pinnedExe,
                           const RuntimePlan& plan) {
    static_assert(sizeof(void*) == 8, "launcher must be built as x64");
    USHORT processMachine{}, nativeMachine{};
    if (!IsWow64Process2(pi.hProcess, &processMachine, &nativeMachine)
        || processMachine != IMAGE_FILE_MACHINE_I386
        || nativeMachine != IMAGE_FILE_MACHINE_AMD64)
        Fail("mapped process architecture is not the expected 32-bit x86 image");
    std::wstring processPath(32768, L'\0');
    DWORD pathLength = static_cast<DWORD>(processPath.size());
    if (!QueryFullProcessImageNameW(pi.hProcess, 0, processPath.data(), &pathLength))
        Fail("cannot query mapped process image path");
    processPath.resize(pathLength);
    HANDLE mappedFile = CreateFileW(processPath.c_str(), FILE_READ_ATTRIBUTES | GENERIC_READ,
                                    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                    nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (mappedFile == INVALID_HANDLE_VALUE) Fail("cannot reopen mapped image path for file identity check");
    const bool sameFile = SameFileIdentity(pinnedExe, mappedFile);
    CloseHandle(mappedFile);
    if (!sameFile) Fail("mapped process image file identity differs from the pinned executable");
    const uintptr_t imageBase = ProcessImageBase32(pi.hProcess);
    if (imageBase != kExpectedImageBase) Fail("mapped process image base is not 0x00400000");

    std::vector<uint8_t> mappedHeaders(plan.pe.headersSize);
    SIZE_T received{};
    if (!ReadProcessMemory(pi.hProcess, reinterpret_cast<LPCVOID>(imageBase), mappedHeaders.data(),
                           mappedHeaders.size(), &received) || received != mappedHeaders.size())
        Fail("cannot inspect mapped PE headers before first execution");
    if (!std::equal(mappedHeaders.begin(), mappedHeaders.end(), plan.source.begin()))
        Fail("mapped PE headers do not match the exact retail file image");
    const Section* text = nullptr;
    for (const auto& section : plan.pe.sections) if (section.name == ".text") text = &section;
    if (!text) Fail("mapped image has no .text section");
    const size_t sampleSize = std::min<size_t>(64, text->rawSize);
    std::vector<uint8_t> mappedText(sampleSize);
    if (!ReadProcessMemory(pi.hProcess, reinterpret_cast<LPCVOID>(imageBase + text->rva), mappedText.data(), sampleSize, &received)
        || received != sampleSize
        || !std::equal(mappedText.begin(), mappedText.end(), plan.source.begin() + text->rawOffset))
        Fail("mapped executable section sample does not match the exact retail file image");
    std::wcout << L"PROCESS_IMAGE_VERIFIED path=" << processPath << L" base=0x400000 machine=I386\n";
}

void TerminateSuspended(PROCESS_INFORMATION& pi, const std::string& reason) {
    std::string termination = "; suspended child termination is unconfirmed";
    if (pi.hProcess) {
        if (!TerminateProcess(pi.hProcess, 0xE001)) {
            termination += "; TerminateProcess Win32 error " + std::to_string(GetLastError());
        } else {
            const DWORD wait = WaitForSingleObject(pi.hProcess, 10000);
            if (wait == WAIT_OBJECT_0) {
                termination = "; suspended child terminated without resume";
            } else if (wait == WAIT_FAILED) {
                termination += "; termination wait Win32 error " + std::to_string(GetLastError());
            } else {
                termination += "; termination wait timed out";
            }
        }
    }
    if (pi.hThread) { CloseHandle(pi.hThread); pi.hThread = nullptr; }
    if (pi.hProcess) { CloseHandle(pi.hProcess); pi.hProcess = nullptr; }
    Fail(reason + termination);
}

struct Protection {
    void* address{};
    SIZE_T size{};
    DWORD old{};
};

void ValidateAndInstall(PROCESS_INFORMATION& pi, uintptr_t imageBase, const RuntimePlan& plan) {
    for (const auto& op : plan.operations) {
        if (op.flags == kFileOnly) continue;
        MEMORY_BASIC_INFORMATION region{};
        const auto address = reinterpret_cast<LPCVOID>(imageBase + op.rva);
        if (VirtualQueryEx(pi.hProcess, address, &region, sizeof(region)) != sizeof(region)
            || region.State != MEM_COMMIT || region.Type != MEM_IMAGE
            || region.AllocationBase != reinterpret_cast<void*>(imageBase))
            Fail("operation target is not committed inside the mapped retail image");
        const uintptr_t regionStart = reinterpret_cast<uintptr_t>(region.BaseAddress);
        const uintptr_t regionEnd = regionStart + region.RegionSize;
        const uintptr_t targetStart = reinterpret_cast<uintptr_t>(address);
        if (targetStart < regionStart || targetStart + op.length > regionEnd
            || (region.Protect & PAGE_GUARD) != 0)
            Fail("operation target crosses an unmapped, guarded, or differently protected region");
        const DWORD basicProtect = region.Protect & 0xFF;
        const bool executable = basicProtect == PAGE_EXECUTE || basicProtect == PAGE_EXECUTE_READ
            || basicProtect == PAGE_EXECUTE_READWRITE || basicProtect == PAGE_EXECUTE_WRITECOPY;
        const bool readable = basicProtect == PAGE_READONLY || basicProtect == PAGE_READWRITE
            || basicProtect == PAGE_WRITECOPY || basicProtect == PAGE_EXECUTE_READ
            || basicProtect == PAGE_EXECUTE_READWRITE || basicProtect == PAGE_EXECUTE_WRITECOPY;
        if ((op.pageClass == kPageCode && !executable)
            || (op.pageClass == kPageData && !readable))
            Fail("operation target protection does not match the audited section class");
        std::vector<uint8_t> current(op.length);
        SIZE_T received{};
        if (!ReadProcessMemory(pi.hProcess, address, current.data(), current.size(), &received)
            || received != current.size() || current != op.before)
            Fail("mapped-image preimage mismatch at RVA 0x" + std::to_string(op.rva));
    }

    std::vector<Protection> protections;
    protections.reserve(plan.operations.size());
    for (const auto& op : plan.operations) {
        if (op.flags == kFileOnly) continue;
        DWORD old{};
        const DWORD desired = op.pageClass == kPageCode ? PAGE_EXECUTE_READWRITE : PAGE_READWRITE;
        void* address = reinterpret_cast<void*>(imageBase + op.rva);
        if (!VirtualProtectEx(pi.hProcess, address, op.length, desired, &old)) {
            bool restored = true;
            for (auto it = protections.rbegin(); it != protections.rend(); ++it) {
                DWORD ignored{};
                restored = VirtualProtectEx(pi.hProcess, it->address, it->size, it->old, &ignored) && restored;
            }
            if (!restored) TerminateSuspended(pi, "protection preparation and restoration failed");
            Fail("VirtualProtectEx failed before any native bytes were written");
        }
        protections.push_back({address, op.length, old});
    }

    for (const auto& op : plan.operations) {
        if (op.flags == kFileOnly) continue;
        SIZE_T written{};
        void* address = reinterpret_cast<void*>(imageBase + op.rva);
        if (!WriteProcessMemory(pi.hProcess, address, op.after.data(), op.after.size(), &written)
            || written != op.after.size())
            TerminateSuspended(pi, "in-memory installation failed after writes began");
    }
    if (!FlushInstructionCache(pi.hProcess, nullptr, 0))
        TerminateSuspended(pi, "instruction-cache flush failed after installation");
    for (const auto& op : plan.operations) {
        if (op.flags == kFileOnly) continue;
        std::vector<uint8_t> current(op.length);
        SIZE_T received{};
        if (!ReadProcessMemory(pi.hProcess, reinterpret_cast<LPCVOID>(imageBase + op.rva),
                               current.data(), current.size(), &received)
            || received != current.size() || current != op.after)
            TerminateSuspended(pi, "post-install memory verification failed");
    }
    bool restored = true;
    for (auto it = protections.rbegin(); it != protections.rend(); ++it) {
        DWORD ignored{};
        restored = VirtualProtectEx(pi.hProcess, it->address, it->size, it->old, &ignored) && restored;
    }
    if (!restored) TerminateSuspended(pi, "page-protection restoration failed");
}

bool HasUnqualifiedProxy(const fs::path& exePath) {
    static constexpr const wchar_t* names[] = {
        L"d3d8.dll", L"d3d9.dll", L"ddraw.dll", L"dinput8.dll",
        L"dsound.dll", L"winmm.dll", L"version.dll", L"dxgi.dll"
    };
    const auto directory = exePath.parent_path();
    for (const auto* name : names) {
        const auto path = directory / name;
        if (fs::exists(path)) {
            std::wcerr << L"UNQUALIFIED_LOCAL_WRAPPER " << path << L"\n";
            return true;
        }
    }
    return false;
}

void Launch(const fs::path& exePath, const fs::path& workingDirectory,
            const RuntimePlan* plan) {
    HANDLE pinnedExe = OpenPinnedRetail(exePath);
    if (HashHandle(pinnedExe) != MR_RETAIL_SHA256) {
        CloseHandle(pinnedExe); Fail("pinned executable SHA256 mismatch");
    }
    if (plan && HasUnqualifiedProxy(exePath)) {
        CloseHandle(pinnedExe); Fail("graphics/input proxy compatibility is not qualified; refusing modded launch");
    }

    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION pi{};
    std::wstring command = L"\"" + exePath.wstring() + L"\"";
    if (!CreateProcessW(exePath.c_str(), command.data(), nullptr, nullptr, FALSE,
                        CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT,
                        nullptr, workingDirectory.c_str(), &startup, &pi)) {
        CloseHandle(pinnedExe); Fail("CreateProcessW(CREATE_SUSPENDED) failed");
    }
    try {
        auto source = ReadFileBytes(exePath);
        PeInfo pe = ParsePe(source);
        RuntimePlan identityPlan;
        identityPlan.source = source;
        identityPlan.pe = pe;
        VerifyProcessIdentity(pi, pinnedExe, identityPlan);
        if (plan) {
            ValidateAndInstall(pi, ProcessImageBase32(pi.hProcess), *plan);
            if (plan->operations.size() == 1 && plan->operations.front().flags == kNoopCanary)
                std::cout << "IN_MEMORY_CANARY_VERIFIED rva=0x" << std::hex
                          << plan->operations.front().rva << std::dec << " bytes_unchanged=true\n";
            else
                std::cout << "IN_MEMORY_PATCH_SET_VERIFIED operations=" << plan->operations.size()
                          << " reference_reconstruction_sha256=" << MR_REFERENCE_IMAGE_SHA256 << "\n";
        }
        if (ResumeThread(pi.hThread) != 1)
            TerminateSuspended(pi, "ResumeThread failed");
        std::cout << "PROCESS_RESUMED mode=" << (plan ? "integrated" : "bootstrap-only") << "\n";
        if (WaitForSingleObject(pi.hProcess, INFINITE) != WAIT_OBJECT_0)
            Fail("waiting for the game process failed");
        DWORD exitCode{};
        if (!GetExitCodeProcess(pi.hProcess, &exitCode)) Fail("cannot read the game exit code");
        if (HashHandle(pinnedExe) != MR_RETAIL_SHA256)
            Fail("retail executable hash changed while the game was running");
        std::cout << "PROCESS_EXIT exit_code=" << exitCode << " retail_exe_sha256=" << MR_RETAIL_SHA256 << "\n";
        CloseHandle(pi.hThread); CloseHandle(pi.hProcess); CloseHandle(pinnedExe);
    } catch (...) {
        if (pi.hProcess) {
            TerminateProcess(pi.hProcess, 0xE002);
            WaitForSingleObject(pi.hProcess, 10000);
        }
        if (pi.hThread) CloseHandle(pi.hThread);
        if (pi.hProcess) CloseHandle(pi.hProcess);
        CloseHandle(pinnedExe);
        throw;
    }
}

void VerifyBundle(const fs::path& exePath, const fs::path& bundle) {
    const DWORD bundleAttributes = GetFileAttributesW(bundle.c_str());
    if (!fs::is_directory(bundle) || bundleAttributes == INVALID_FILE_ATTRIBUTES
        || (bundleAttributes & FILE_ATTRIBUTE_REPARSE_POINT))
        Fail("runtime bundle root is missing or link-backed");
    FileHashEquals(exePath, MR_RETAIL_SHA256, "retail executable");
    if (fs::file_size(exePath) != kRetailSize) Fail("retail executable size mismatch");
    const fs::path planPath = bundle / L"addon-plan.json";
    const fs::path manifestPath = bundle / L"native-patch-manifest.json";
    const fs::path opsPath = bundle / L"native-patch-ops.rvp";
    const fs::path indexPath = bundle / L"resource-index.tsv";
    FileHashEquals(manifestPath, MR_PATCH_MANIFEST_SHA256, "native patch manifest");
    FileHashEquals(bundle / L"resource-manifest.json", MR_RESOURCE_MANIFEST_SHA256, "resource manifest");
    VerifyResourceRoot(bundle / L"resource-root", indexPath);
    const auto plan = ParsePatchPlan(exePath, opsPath, planPath);
    std::cout << "RUNTIME_BUNDLE_VERIFIED patch_operations=" << plan.operations.size()
              << " plan_sha256=" << MR_ADDON_PLAN_SHA256 << "\n";
}

} // namespace

int wmain(int argc, wchar_t** argv) {
    try {
        if (argc < 3) {
            std::wcerr << L"Usage:\n"
                       << L"  mr-runtime-launcher --verify <retail-exe> <bundle>\n"
                       << L"  mr-runtime-launcher --bootstrap-only <retail-exe>\n"
                       << L"  mr-runtime-launcher --canary-only <retail-exe> <bundle>\n"
                       << L"  mr-runtime-launcher --integrated <retail-exe> <bundle>\n";
            return 2;
        }
        const std::wstring mode = argv[1];
        const fs::path exePath = fs::absolute(argv[2]);
        if (mode == L"--bootstrap-only") {
            if (argc != 3) Fail("--bootstrap-only accepts exactly one executable path");
            FileHashEquals(exePath, MR_RETAIL_SHA256, "retail executable");
            if (fs::file_size(exePath) != kRetailSize) Fail("retail executable size mismatch");
            auto bytes = ReadFileBytes(exePath);
            (void)ParsePe(bytes);
            std::cout << "BOOTSTRAP_PREFLIGHT_PASS retail_exe_sha256=" << MR_RETAIL_SHA256 << "\n";
            Launch(exePath, exePath.parent_path(), nullptr);
            return 0;
        }
        if (argc != 4) Fail("mode requires executable and bundle paths");
        const fs::path bundle = fs::absolute(argv[3]);
        VerifyBundle(exePath, bundle);
        if (mode == L"--verify") return 0;
        if (mode != L"--integrated" && mode != L"--canary-only") Fail("unknown launcher mode");
        auto plan = ParsePatchPlan(exePath, bundle / L"native-patch-ops.rvp", bundle / L"addon-plan.json");
        if (mode == L"--canary-only") {
            plan.operations.erase(std::remove_if(plan.operations.begin(), plan.operations.end(),
                [](const Operation& operation) { return operation.flags != kNoopCanary; }), plan.operations.end());
            if (plan.operations.size() != 1) Fail("bundle must contain exactly one approved no-op canary");
            Launch(exePath, exePath.parent_path(), &plan);
        } else {
            Launch(exePath, bundle / L"resource-root", &plan);
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL_CLOSED: " << error.what() << "\n";
        return 1;
    }
}
