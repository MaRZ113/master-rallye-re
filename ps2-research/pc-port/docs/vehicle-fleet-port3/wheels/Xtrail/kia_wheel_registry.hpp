#pragma once
#include "race_fleet_registry.hpp"
namespace gfx2::ps2port {
inline constexpr FleetRaceSource kPort3XtrailWheelSources[]={
 {"2f4938e041122fb29ecc25c7ebcf53a535c33bcacc1e49268e158722677af698","193608464d1ef23d4b90f13ee76dd92338ba03830633609a37d70ad1a6d565dc","65ad613c309360e4b9bc9b7a19ca3e7446566092824b73f87bddf41c43989442","cbd585a2718ff47724436f4f492350877d71256ace5c7972dfcc33f7aae25537",54u,72u,false},
 {"a57e255404ce0f61f76b3985a44d870f4eddfe03222760c7f36a9380894cd875","c2558fb69201975bfdf2cb770ab90985985e6689d4dcd43b4e8e4b1bf4b17f10","41d0988fbc58dfdd933d3c19252221d9fd68db2e650f2798692219c6781551ad","956c39dcf73bb0efd0725e3ad83f936b9418dbad474d8c41265871e0ea7946b6",38u,36u,false},
 {"a7066b168c5330f1a2458fc08e671ec06ce634d2936983a09e06238fee35778d","60da21e2579654ac4a4f4e713eacaccb43b30c9c9ad7f27693cf683d4f66d62d","7e655768acf13b8d2c1cb603f106475b6d6d64303dcb549af688c4d7499d777e","b50a88ae374a5daef5916efea9ee5cd85ddecc7441b5f74419749622efc138cb",37u,54u,false},
 {"283ca0c3a366146405df4d3fc18755abbe09376d11a7c326ebd25979c4b06c35","afce3bf66b8a244c8da4d3e84d96180ef7743a11003ec668689f52aee44d0152","6f3d81770e96cdeece57ab6a94ddf8bcd74e542bfbb0d1a36e2cfe611ab9193e","cd832582d70a6d9718874c08426168fa984c7034b947c4d954ace2a794bd000b",91u,90u,false},
};
inline constexpr bool kPort3XtrailWheelMixed[]={false,false,true};
inline constexpr bool kPort3XtrailWheelWrapU[]={false,true,false};
inline constexpr FleetRaceProfile kPort3XtrailWheelProfile={"Xtrail","XTRAIL","port3-XTRAIL-WHEEL-FLEET.ps2model","3e2ee4c25635e3ecd99113e1b679285c9a95f09ca7f0cdc05e19b1c23f0d369b",60867u,300u,756u,5u,3u,4u,4u,kPort3XtrailWheelSources,kPort3XtrailWheelMixed,kPort3XtrailWheelWrapU};
}
