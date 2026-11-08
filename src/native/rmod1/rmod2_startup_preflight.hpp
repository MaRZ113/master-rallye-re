#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <string>
#include <vector>

namespace rmod2_boot {

inline bool allocation_offset(std::uint32_t base, std::uint32_t address,
                              std::size_t allocation_size, std::size_t& offset) {
    if (address < base) return false;
    offset = static_cast<std::size_t>(address - base);
    return offset <= allocation_size && allocation_size - offset >= sizeof(std::uint32_t);
}

inline bool write_u32_address(std::vector<std::uint8_t>& allocation,
                              std::uint32_t base, std::uint32_t address,
                              std::uint32_t value) {
    std::size_t offset = 0;
    if (!allocation_offset(base, address, allocation.size(), offset)) return false;
    std::memcpy(allocation.data() + offset, &value, sizeof(value));
    return true;
}

inline bool copy_generated_template(std::vector<std::uint8_t>& destination,
                                    const std::uint8_t* source,
                                    std::size_t source_size,
                                    std::size_t declared_used) {
    if ((!source && source_size) || source_size != declared_used || source_size > destination.size())
        return false;
    std::fill(destination.begin(), destination.end(), std::uint8_t{0});
    if (source_size) std::memcpy(destination.data(), source, source_size);
    return true;
}

struct OperationSpan {
    std::uint32_t rva;
    std::size_t expected_size;
    std::size_t replacement_size;
    const char* id;
};

inline bool validate_operation_spans(const OperationSpan* operations, std::size_t count,
                                     std::size_t image_size, std::string& error) {
    if (!operations && count) { error = "native operation list is null"; return false; }
    for (std::size_t i = 0; i < count; ++i) {
        const auto& op = operations[i];
        if (!op.id || !op.expected_size || op.expected_size != op.replacement_size ||
            op.rva > image_size || op.expected_size > image_size - op.rva) {
            error = std::string("invalid native operation range: ") + (op.id ? op.id : "<null>");
            return false;
        }
        const std::size_t end = static_cast<std::size_t>(op.rva) + op.replacement_size;
        for (std::size_t j = 0; j < i; ++j) {
            const auto& prior = operations[j];
            const std::size_t prior_end = static_cast<std::size_t>(prior.rva) + prior.replacement_size;
            if (op.rva < prior_end && prior.rva < end) {
                error = std::string("overlapping native operations: ") + prior.id + " / " + op.id;
                return false;
            }
        }
    }
    error.clear();
    return true;
}

struct NativePreimage {
    std::uintptr_t address;
    const std::uint8_t* expected;
    std::size_t size;
    const char* id;
};

template <class Reader>
inline bool verify_native_preimages(const NativePreimage* preimages, std::size_t count,
                                    Reader&& reader, std::string& error) {
    if (!preimages && count) { error = "native preimage list is null"; return false; }
    std::vector<std::uint8_t> actual;
    for (std::size_t i = 0; i < count; ++i) {
        const auto& item = preimages[i];
        if (!item.expected || !item.size || !item.id) {
            error = "invalid native preimage descriptor";
            return false;
        }
        actual.resize(item.size);
        if (!reader(item.address, actual.data(), actual.size()) ||
            std::memcmp(actual.data(), item.expected, item.size) != 0) {
            error = std::string("native preimage mismatch: ") + item.id;
            return false;
        }
    }
    error.clear();
    return true;
}

} // namespace rmod2_boot
