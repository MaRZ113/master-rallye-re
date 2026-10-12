#pragma once

#include "legacy_attract_guard.hpp"
#include <array>
#include <cstddef>
#include <cstdint>

namespace gfx2 {

enum class BrokerNullSite : uint8_t { StringList, XmlData };

inline constexpr uintptr_t BROKER_STRINGLIST_SITE_VA = 0x0060201E;
inline constexpr uintptr_t BROKER_STRINGLIST_EMPTY_VA = 0x00602040;
inline constexpr uintptr_t BROKER_XMLDATA_SITE_VA = 0x00602153;
inline constexpr uintptr_t BROKER_XMLDATA_CONTINUE_VA = 0x0060215A;
inline constexpr uintptr_t BROKER_XMLDATA_NULL_VA = 0x0060218E;

struct BrokerNullStub {
    std::array<unsigned char, 40> bytes{};
    size_t size = 0;
};

struct BrokerCodeMemory {
    virtual ~BrokerCodeMemory() = default;
    virtual uintptr_t allocate(size_t bytes) noexcept = 0;
    virtual bool seal(uintptr_t address, size_t bytes) noexcept = 0;
    virtual void discard(uintptr_t address) noexcept = 0;
};

struct BrokerNullSiteState {
    bool context_verified = false;
    bool installed = false;
    bool rollback_performed = false;
    bool rollback_verified = true;
    bool original_bytes_restored = false;
    uintptr_t address = 0;
    uintptr_t stub = 0;
    size_t stub_size = 0;
    size_t patch_size = 0;
    std::array<unsigned char, 8> original{};
    std::array<unsigned char, 8> replacement{};
    const char* reason = "not_attempted";
};

struct BrokerNullGuardStatus {
    bool retail_build_verified = false;
    bool stringlist_site_verified = false;
    bool stringlist_guard_installed = false;
    bool xmldata_site_verified = false;
    bool xmldata_guard_installed = false;
    bool rollback_performed = false;
    bool rollback_verified = true;
    bool original_bytes_restored = false;
    bool safe_to_continue = true;
    uint32_t stringlist_null_branches = 0;
    uint32_t xmldata_null_branches = 0;
    const char* install_failure_reason = "none";
};

bool build_broker_null_stub(BrokerNullSite site, uintptr_t stub_address,
                            uintptr_t null_counter, BrokerNullStub& out) noexcept;

// The caller supplies the already hash-verified retail identity. Each native site
// is verified, installed, and rolled back independently.
bool apply_broker_null_guard(PatchMemory& memory, BrokerCodeMemory& code,
                             AttractThreadGate& threads, BrokerNullSite site,
                             uintptr_t image_base, bool exact_retail,
                             uintptr_t null_counter,
                             BrokerNullSiteState& state) noexcept;

bool restore_broker_null_guard(PatchMemory& memory, AttractThreadGate& threads,
                               BrokerNullSiteState& state) noexcept;

// Called at the first exported D3D8 factory entry and final wrapped root release.
// The Broker guard never prevents ordinary D3D forwarding for a safe refusal.
bool install_broker_null_guards(uintptr_t factory_caller) noexcept;
void restore_broker_null_guards() noexcept;
BrokerNullGuardStatus broker_null_guard_status() noexcept;

} // namespace gfx2
