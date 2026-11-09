#pragma once
#include <cstdint>

// Read-only MRCR v1 descriptor. The launcher supplies its preferred x86 VA in
// MR_COURSE_REGISTRY_DESCRIPTOR. MRVC v1 remains separate and unchanged.
// Pointers are 32-bit target addresses, not host process pointers.
struct MRCourseRegistryV1 {
    uint32_t magic; // little-endian "MRCR"
    uint32_t version, size; // 1, 64
    uint32_t race_count, race_stride; // 44
    uint32_t vehicle_count, race_base, shared_object_bytes;
    uint32_t registry_getter;
    uint32_t menu_counts; // eight uint32 counts
    uint32_t menu_tables; // eight pointers to arrays of RaceID
    uint32_t reverse_group; // race_count uint32 entries
    uint32_t reverse_local; // race_count uint32 entries
    uint32_t progress_suffixes; // RaceID-indexed C strings; original slots zero
    uint32_t stage_schedules; // [count, RaceID ...], repeated schedule_count times
    uint32_t schedule_count;
};
static_assert(sizeof(MRCourseRegistryV1)==64);

// Generated lookup_stage uses stdcall(schedule_index, RaceID):
// EAX=stage ordinal, EDX=next RaceID or UINT32_MAX, ECX=stage count, CF=invalid.
// EBX/ESI/EDI/EBP retained. Its address is in course-build-audit.json; it is an
// internal extension entry, not an exported DLL or a new mandatory dependency.
