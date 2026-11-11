#pragma once
#include <cstdint>
namespace rmod1 {
// Published by the SDK binding only after its in-process profile matches.
// Class-local display ordering is deliberately absent: IDs remain physical.
struct SdkVehicleV1 {int physical_id;int class_id;std::uint32_t mode_mask;};
struct SdkRosterV1 {std::uint32_t size,version,count,challenge_human_offset;const SdkVehicleV1* vehicles;};
}
