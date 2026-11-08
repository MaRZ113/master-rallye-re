#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include "runtime_log.hpp"

#include <cstring>
#include <iostream>
#include <string>

int main() {
    char temporary_directory[MAX_PATH]{};
    const DWORD directory_length = GetTempPathA(MAX_PATH, temporary_directory);
    if (!directory_length || directory_length >= MAX_PATH) {
        std::cerr << "temporary directory unavailable\n";
        return 1;
    }
    char log_path[MAX_PATH]{};
    if (!GetTempFileNameA(temporary_directory, "rml", 0, log_path)) {
        std::cerr << "temporary log path unavailable\n";
        return 1;
    }
    if (!DeleteFileA(log_path)) {
        std::cerr << "cannot initialize empty log fixture\n";
        return 1;
    }

    if (!rmod1::append_runtime_log_record_to_path(log_path, "CONFIG randomizer=1" ) ||
        !rmod1::append_runtime_log_record_to_path(log_path, "START ADMITTED requested_ai=4") ||
        !rmod1::append_runtime_log_record_to_path(log_path, "ROSTER OBSERVED race_numcars=5")) {
        DeleteFileA(log_path);
        std::cerr << "append API failed\n";
        return 1;
    }

    HANDLE file = CreateFileA(log_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
                              nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        DeleteFileA(log_path);
        std::cerr << "cannot reopen log fixture\n";
        return 1;
    }
    LARGE_INTEGER size{};
    if (!GetFileSizeEx(file, &size) || size.QuadPart < 0 || size.QuadPart > 4096) {
        CloseHandle(file);
        DeleteFileA(log_path);
        std::cerr << "unexpected log fixture size\n";
        return 1;
    }
    std::string actual(static_cast<std::size_t>(size.QuadPart), '\0');
    DWORD read = 0;
    const BOOL read_ok = ReadFile(file, actual.data(), static_cast<DWORD>(actual.size()), &read, nullptr);
    CloseHandle(file);
    const std::string expected =
        "CONFIG randomizer=1\r\n"
        "START ADMITTED requested_ai=4\r\n"
        "ROSTER OBSERVED race_numcars=5\r\n";
    DeleteFileA(log_path);
    char rotated_path[MAX_PATH]{};
    const std::size_t path_length = std::strlen(log_path);
    if (path_length + 3 < MAX_PATH) {
        std::memcpy(rotated_path, log_path, path_length);
        std::memcpy(rotated_path + path_length, ".1", 3);
        DeleteFileA(rotated_path);
    }
    if (!read_ok || read != actual.size() || actual != expected) {
        std::cerr << "append records were overwritten, truncated or reordered\n";
        return 1;
    }
    std::cout << "RMOD1_APPEND_LOG_PASS records=3 chronological=1 intact=1\n";
    return 0;
}
