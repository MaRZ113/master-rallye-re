#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace rmod2_boot {

struct NativeRange {
    std::string_view id;
    std::uint32_t rva{};
    std::uint32_t size{};
};

struct ImageDifference {
    bool found{};
    std::uint32_t offset{};
    std::uint8_t expected{};
    std::uint8_t actual{};
    std::string_view operation;
};

struct ImageScanResult {
    ImageDifference first;
    ImageDifference first_planned_overlap;
};

// Compare only the section's mapped virtual extent. File alignment padding is
// deliberately outside this view and must never be treated as mapped code.
inline ImageScanResult scan_mapped_section(
    const std::uint8_t* disk_bytes, std::size_t raw_size,
    const std::uint8_t* mapped_bytes, std::size_t virtual_size,
    std::uint32_t section_rva, const std::vector<NativeRange>& planned) {
    ImageScanResult result{};
    for (std::size_t i = 0; i < virtual_size; ++i) {
        const auto expected = i < raw_size ? disk_bytes[i] : std::uint8_t{0};
        const auto actual = mapped_bytes[i];
        if (expected == actual) continue;
        const auto mismatch_rva = section_rva + static_cast<std::uint32_t>(i);
        std::string_view owner{};
        for (const auto& range : planned) {
            if (mismatch_rva >= range.rva && mismatch_rva - range.rva < range.size) {
                owner = range.id;
                break;
            }
        }
        const ImageDifference difference{true, static_cast<std::uint32_t>(i), expected, actual, owner};
        if (!result.first.found) result.first = difference;
        if (!owner.empty() && !result.first_planned_overlap.found)
            result.first_planned_overlap = difference;
    }
    return result;
}

} // namespace rmod2_boot
