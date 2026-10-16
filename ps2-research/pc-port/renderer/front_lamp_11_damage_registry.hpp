#pragma once
#include <cstdint>
// INDEX-ONLY SOURCE DRAFT; NO ORIGINAL VERTEX OR UV BYTES.
namespace gfx2::ps2port::front_lamp_11_damage_draft {
struct Mapping { uint32_t vertex,first,count; };
inline constexpr uint16_t candidates[]={1u,2u,0u,6u,7u,8u,3u,10u,9u,11u,15u,16u,17u,14u,7u,3u,5u,4u,16u,12u,14u,13u};
inline constexpr Mapping mapping[]={{2420u,0u,1u},{2421u,1u,1u},{2422u,2u,1u},{2423u,3u,1u},{2424u,4u,1u},{2425u,5u,1u},{2426u,6u,1u},{2427u,7u,1u},{2428u,8u,1u},{2429u,9u,1u},{2430u,10u,1u},{2431u,11u,1u},{2432u,12u,1u},{2433u,13u,1u},{2434u,14u,1u},{2435u,15u,1u},{2436u,16u,1u},{2437u,17u,1u},{2438u,18u,1u},{2439u,19u,1u},{2440u,20u,1u},{2441u,21u,1u}};
inline constexpr const char* ordered_xyz_sha256="26f67dcc6388837e8b706f8270592364f7fa351e8812335ec45f09800e14b4bd";
inline constexpr const char* ordered_uv_winding_sha256="e2f30092b892cdc42461afbc8691012f39821fd22fbb9b03bea6a52fe90fc71d";
inline constexpr const char* original_geometry_sha256="7e42aed180591ce5a99972f8766f1d999d59da87c8212183e528f7fd7fd5f838";
}
