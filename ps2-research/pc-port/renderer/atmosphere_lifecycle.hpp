#pragma once
#include <array>
#include <cstdint>
namespace gfx2::atmosphere {
// Overlay-owned read-only snapshot. Unlike the F10 capture function this never
// rejects/poisons the race observer when called by a loading thread.
struct Lifecycle {
    bool installed=false,same_thread=false,initializing=false;
    uint64_t race=0,request=0,job=0,owner_lifetime=0;
    uint32_t scene=0,actor=0,ai=0,thread=0;
    std::array<char,192> scene_name{};
};
Lifecycle lifecycle() noexcept;
}
