#pragma once
#include <cstdint>

// MRVC v1: descriptor in the emitted private capacity allocation, x86 addresses.
// An owning runtime must publish the address after atomic installation.
// A descriptor in a file or an offline report is not runtime qualification.
namespace mr_vehicle_registry {
struct DescriptorV1 {
    char magic[4];                    // MRVC
    std::uint32_t abi_version;        // 1
    std::uint32_t struct_size;        // 44
    std::uint32_t record_count;
    std::uint32_t record_stride;      // 52, owned native strings unchanged
    std::uint32_t class_count;        // original adapter supports 3
    std::uint32_t registry_getter_va; // cdecl, returns native registry pointer
    std::uint32_t class_counts_va;
    std::uint32_t class_tables_va;    // class_count x pointer to uint32 physical IDs
    std::uint32_t reverse_classes_va; // record_count x uint32
    std::uint32_t reverse_locals_va;  // record_count x uint32
};
static_assert(sizeof(DescriptorV1)==44);
// Native registry stays at one stable heap address for a process lifetime.
// No live reallocation or memcpy of records containing owned strings.
}
