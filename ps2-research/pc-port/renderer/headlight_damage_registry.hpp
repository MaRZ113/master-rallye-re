#pragma once
#include <cstdint>
// INDEX-ONLY DRAFT; NO ORIGINAL VERTEX OR UV BYTES.
namespace gfx2::ps2port::headlight_damage_draft {
struct Mapping { uint32_t vertex,first,count; };
inline constexpr uint16_t candidates[]={3u,0u,2u,1u,7u,8u,4u,9u,5u,10u,4u,5u,6u,14u,13u,11u,12u,18u,19u,17u,20u,16u,21u,15u,16u,17u};
inline constexpr Mapping mapping[]={{3144u,0u,1u},{3145u,1u,1u},{3146u,2u,1u},{3147u,3u,1u},{3148u,4u,1u},{3149u,5u,1u},{3150u,6u,1u},{3151u,7u,1u},{3152u,8u,1u},{3153u,9u,1u},{3154u,10u,1u},{3155u,11u,1u},{3156u,12u,1u},{3157u,13u,1u},{3158u,14u,1u},{3159u,15u,1u},{3160u,16u,1u},{3161u,17u,1u},{3162u,18u,1u},{3163u,19u,1u},{3164u,20u,1u},{3165u,21u,1u},{3166u,22u,1u},{3167u,23u,1u},{3168u,24u,1u},{3169u,25u,1u}};
inline constexpr const char* ordered_xyz_sha256="652134fe64548713907696003bf64728983bcf6b01fa4a9e32aeb69ec328efd3";
inline constexpr const char* ordered_uv_winding_sha256="502345f8abbf60ba1016ab1f29d98f74ea35c9c3e85fc260c405cf28a475f24d";
inline constexpr const char* original_geometry_sha256="fad797c65838c39d359767a9ef06d0d5579d847fa2b23a9ee8febe8c171b361c";
}
