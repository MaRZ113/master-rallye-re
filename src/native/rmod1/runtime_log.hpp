#pragma once

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <cstddef>
#include <cstring>

namespace rmod1 {

inline constexpr std::size_t kRuntimeLogMaxRecordBytes = 1024;
inline constexpr LONGLONG kRuntimeLogMaxFileBytes = 64 * 1024;
inline SRWLOCK g_runtime_log_lock = SRWLOCK_INIT;

class RuntimeLogGuard {
public:
    RuntimeLogGuard() { AcquireSRWLockExclusive(&g_runtime_log_lock); }
    ~RuntimeLogGuard() { ReleaseSRWLockExclusive(&g_runtime_log_lock); }
    RuntimeLogGuard(const RuntimeLogGuard&) = delete;
    RuntimeLogGuard& operator=(const RuntimeLogGuard&) = delete;
};

// The single WriteFile call uses FILE_APPEND_DATA only, so every complete
// record is appended at EOF regardless of the handle's initial file pointer.
// The process-local lock serializes writers and the rotation boundary.
inline bool append_runtime_log_record_to_path(const char* path, const char* line) {
    if (!path || !*path || !line) return false;
    const std::size_t path_length = std::strlen(path);
    const std::size_t line_length = std::strlen(line);
    if (path_length + 3 >= MAX_PATH || line_length == 0 ||
        line_length + 2 > kRuntimeLogMaxRecordBytes) return false;
    for (std::size_t i = 0; i < line_length; ++i)
        if (line[i] == '\r' || line[i] == '\n') return false;

    char record[kRuntimeLogMaxRecordBytes]{};
    std::memcpy(record, line, line_length);
    record[line_length] = '\r';
    record[line_length + 1] = '\n';
    const DWORD record_size = static_cast<DWORD>(line_length + 2);

    RuntimeLogGuard guard;
    HANDLE file = CreateFileA(path, FILE_APPEND_DATA | FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
        OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;

    LARGE_INTEGER current_size{};
    if (!GetFileSizeEx(file, &current_size)) {
        CloseHandle(file);
        return false;
    }
    if (current_size.QuadPart + record_size > kRuntimeLogMaxFileBytes) {
        CloseHandle(file);
        char rotated_path[MAX_PATH]{};
        std::memcpy(rotated_path, path, path_length);
        std::memcpy(rotated_path + path_length, ".1", 3);
        if (!MoveFileExA(path, rotated_path,
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) return false;
        file = CreateFileA(path, FILE_APPEND_DATA | FILE_READ_ATTRIBUTES,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
            OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (file == INVALID_HANDLE_VALUE) return false;
    }

    DWORD written = 0;
    const BOOL complete = WriteFile(file, record, record_size, &written, nullptr) &&
        written == record_size;
    CloseHandle(file);
    return complete != FALSE;
}

} // namespace rmod1
