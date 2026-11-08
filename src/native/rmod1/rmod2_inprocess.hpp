#pragma once
#include <cstddef>
#include <cstdint>

namespace rmod2_boot {
// Called only from a forwarded DirectInput export, outside DllMain/loader lock.
// The caller provides process-wide once-only serialization.
bool initialize(char* error, unsigned error_capacity);

// One verified image write for an Extra Options module (expected -> replacement, equal size).
struct NativeWrite {
    std::uintptr_t address;
    const std::uint8_t* expected;
    const std::uint8_t* replacement;
    std::size_t size;
    const char* id;
};
// Same startup transaction as the F3 plan: every target must be pristine PAGE_EXECUTE_READ image
// code holding its expected bytes; other threads are suspended (none may execute inside a target),
// all writes are read back, and any failure restores every original byte before returning false.
bool apply_native_writes(const NativeWrite* writes, std::size_t count, char* error, unsigned error_capacity);
}
