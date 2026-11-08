#pragma once

// Testable validation for an already mapped PE image. The Win32 launcher
// supplies VirtualQueryEx/ReadProcessMemory adapters; native tests supply
// bounded synthetic adapters. This deliberately does not consult loader lists.

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <limits>
#include <string>
#include <vector>

namespace rmod1::image_mapping {

enum class State { Committed, Reserved, Free, Unknown };
enum class Type { Image, Mapped, Private, Unknown };

struct Region {
    std::uintptr_t base_address{};
    std::size_t size{};
    std::uintptr_t allocation_base{};
    State state = State::Unknown;
    Type type = Type::Unknown;
};

struct Section {
    std::uint32_t rva{};
    std::uint32_t virtual_size{};
    std::uint32_t raw_size{};
    std::uint32_t raw_offset{};
    bool executable = false;
    bool writable = false;
};

struct Layout {
    std::uintptr_t image_base{};
    std::uint32_t image_size{};
    std::uint32_t headers_size{};
    std::vector<Section> sections;
};

using QueryRegion = std::function<bool(std::uintptr_t, Region&)>;
using ReadMemory = std::function<bool(std::uintptr_t, std::uint8_t*, std::size_t)>;

inline bool verify(const Layout& image, const std::vector<std::uint8_t>& source,
                   const QueryRegion& query, const ReadMemory& read,
                   std::string& error) {
    error.clear();
    auto reject = [&](const char* reason) {
        error = reason;
        return false;
    };
    if (!image.image_base || !image.image_size || !image.headers_size ||
        image.headers_size > source.size() ||
        image.image_size > std::numeric_limits<std::uintptr_t>::max() - image.image_base)
        return reject("invalid expected image extent or header size");
    if (!query || !read) return reject("mapped-image query/read adapter is missing");

    const std::uintptr_t image_end = image.image_base + image.image_size;
    std::uintptr_t cursor = image.image_base;
    while (cursor < image_end) {
        Region region;
        if (!query(cursor, region)) return reject("VirtualQueryEx could not cover the expected image extent");
        if (!region.size || region.base_address > cursor ||
            region.size > std::numeric_limits<std::uintptr_t>::max() - region.base_address)
            return reject("mapped-image region has invalid bounds");
        const std::uintptr_t region_end = region.base_address + region.size;
        if (region_end <= cursor) return reject("mapped-image region does not advance the image extent");
        if (region.allocation_base != image.image_base)
            return reject("mapped-image allocation base differs from the audited image base");
        if (region.type != Type::Image)
            return reject("expected executable mapping is not MEM_IMAGE");
        if (region.state != State::Committed)
            return reject("expected image extent contains a non-MEM_COMMIT region");
        cursor = std::min(region_end, image_end);
    }

    std::vector<std::uint8_t> headers(image.headers_size);
    if (!read(image.image_base, headers.data(), headers.size()))
        return reject("mapped PE headers are not readable");
    if (!std::equal(headers.begin(), headers.end(), source.begin()))
        return reject("mapped PE headers differ from the pinned retail file");

    bool executable_section_found = false;
    for (const auto& section : image.sections) {
        if (!section.executable) continue;
        if (section.writable || !section.virtual_size ||
            section.virtual_size > section.raw_size ||
            section.rva > image.image_size ||
            section.virtual_size > image.image_size - section.rva ||
            section.raw_offset > source.size() ||
            section.virtual_size > source.size() - section.raw_offset)
            return reject("executable section layout is outside the audited retail image");
        std::vector<std::uint8_t> mapped(section.virtual_size);
        if (!read(image.image_base + section.rva, mapped.data(), mapped.size()))
            return reject("complete mapped executable section is not readable");
        if (!std::equal(mapped.begin(), mapped.end(), source.begin() + section.raw_offset))
            return reject("mapped executable section differs from the pinned retail file");
        executable_section_found = true;
    }
    if (!executable_section_found) return reject("retail image has no verified executable section");
    return true;
}

} // namespace rmod1::image_mapping
