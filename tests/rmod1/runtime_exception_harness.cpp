#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "../../src/native/rmod1/exception_report.hpp"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

namespace {

using Configure = DWORD (WINAPI*)(const void*);

int trigger_caught_access_violation() {
    ULONG_PTR information[2] = {1u, 0x00ABCDEFu};
    __try {
        RaiseException(EXCEPTION_ACCESS_VIOLATION, 0, 2, information);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 1;
    }
    return 0;
}

std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream input(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    HMODULE module = LoadLibraryA(argv[1]);
    if (!module) return 3;
    const auto configure = reinterpret_cast<Configure>(GetProcAddress(module, "MRConfigureBlobV1"));
    if (!configure) return 4;

    constexpr char ini[] = "[General]\nConfigVersion=1\n[Logging]\nEnabled=true\n";
    const std::uint32_t size = static_cast<std::uint32_t>(sizeof(ini) - 1);
    std::vector<std::uint8_t> blob(sizeof(size) + size);
    std::memcpy(blob.data(), &size, sizeof(size));
    std::memcpy(blob.data() + sizeof(size), ini, size);
    if (!configure(blob.data())) return 5;

    if (!trigger_caught_access_violation()) return 6;
    const auto log = read_file("MRallyeRandomizer-crash-v1.bin");
    if (log.size() != 2 * sizeof(rmod1::ExceptionRecordV1)) return 7;
    rmod1::ExceptionRecordV1 session{};
    rmod1::ExceptionRecordV1 access_violation{};
    std::memcpy(&session, log.data(), sizeof(session));
    std::memcpy(&access_violation, log.data() + sizeof(session), sizeof(access_violation));
    if (std::memcmp(session.magic, rmod1::kExceptionRecordMagicV1, sizeof(session.magic)) != 0 ||
        session.kind != static_cast<std::uint32_t>(rmod1::ExceptionRecordKindV1::Session) ||
        session.record_size != sizeof(session)) return 8;
    if (std::memcmp(access_violation.magic, rmod1::kExceptionRecordMagicV1,
                    sizeof(access_violation.magic)) != 0 ||
        access_violation.kind != static_cast<std::uint32_t>(rmod1::ExceptionRecordKindV1::AccessViolationFirstChance) ||
        access_violation.exception_code != EXCEPTION_ACCESS_VIOLATION ||
        access_violation.parameter_count != 2 || access_violation.exception_information[0] != 1u ||
        access_violation.exception_information[1] != 0x00ABCDEFu ||
        access_violation.config_flags != rmod1::kExceptionConfigLogging ||
        access_violation.record_size != sizeof(access_violation)) return 9;

    std::cout << "RMDIAG_CAPTURE_PASS records=2 first_chance_av=preserved code=0xC0000005"
              << " config=logging-only\n";
    return 0;
}
