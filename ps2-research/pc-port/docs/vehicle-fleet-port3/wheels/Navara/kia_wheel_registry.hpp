#pragma once
#include "race_fleet_registry.hpp"
namespace gfx2::ps2port {
inline constexpr FleetRaceSource kPort3NavaraWheelSources[]={
 {"cd6c0a0ee7555e8c1a89f5d131b0cf99026423b22933c40d61f255526396c66a","e9ba8454d03d2bf4164ec80f89c8e18ecfc7174774fd97afc8079ea2794bf000","2b9b8660952fe50d437e9eec26ec02fb336966f9e407f6e02d9493bee0f64158","34911f21f48f7533a4b66f04f7210d7a03b499a3e530a17978f79a1d4cf4f54c",54u,72u,false},
 {"a658939bc261231da68bd6240f98c2189ba83abb54ed6410051b3523574be00f","2fe6f630b9153bb647e18e92ea8d724a6579328bf6a2d5b2b49f808f96645a54","1281f0664795bef099f5e2e6bddbaf4193b31f3c204ba779f4a2947468b9dc36","415ec54fbfcccb6b283f3261134599902311a230a2a7a3ef95532cfd4292ece8",38u,36u,false},
 {"20dbcf51a5c659d4d83bafc8e7974a9b36e1c762e4eed58a848fc2fa57e43f66","93a16e172eb05e5477f95746e38cda30a5b0472cb19fea79e65849eba031168b","8d7eb3ab7d5645f0abd76f52f51e1016a12f20d01a45a746aa7de9af7a201219","91050cbb51b1794e0c29ed4ef02951d68a0ca1eabbf7f55e61f21ffa441b3749",37u,54u,false},
 {"a6143933de7d02a1cc99cdc09011323a3c3c4c3368abb57ff51f1d6c80ce8d4f","b29c2aff65cfa07fa61bc07138cdb41d78c3bc9695dd8842a9225cf2a7fdc66b","577bf3592fde82cad41505858c9faab58b2c0538364751260632d3a0b43d01bb","4f2be4f7012b2efde6af35e15f7a1618f2168c8c06beb93bf8f9236185536749",91u,90u,false},
};
inline constexpr bool kPort3NavaraWheelMixed[]={false,false,true};
inline constexpr bool kPort3NavaraWheelWrapU[]={false,true,false};
inline constexpr FleetRaceProfile kPort3NavaraWheelProfile={"Navara","NAVARA","port3-NAVARA-WHEEL-FLEET.ps2model","421524c0dee35251433d550363efe88171682f6a1a30a09f190603021381773b",48578u,300u,756u,5u,3u,4u,4u,kPort3NavaraWheelSources,kPort3NavaraWheelMixed,kPort3NavaraWheelWrapU};
}
