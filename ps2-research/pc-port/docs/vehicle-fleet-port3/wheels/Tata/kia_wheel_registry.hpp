#pragma once
#include "race_fleet_registry.hpp"
namespace gfx2::ps2port {
inline constexpr FleetRaceSource kPort3TataWheelSources[]={
 {"e9d6a2949b9b1b8e4c881b16a2f9af8a5bed34db3058490ee4f072253f86c8dd","8b5d7513dc501923bbcd4a9f28e8884942ba19acb96205ee0b5fe035600c9d8c","65ad613c309360e4b9bc9b7a19ca3e7446566092824b73f87bddf41c43989442","cbd585a2718ff47724436f4f492350877d71256ace5c7972dfcc33f7aae25537",54u,72u,false},
 {"5895889f696a7042c83e1e6b5806b2af6d9199c201459f99f1938693f723d5a6","ef9431198f41963e43150c2e87e69540b8a17ef0045580997e37826e2afbb1b0","41d0988fbc58dfdd933d3c19252221d9fd68db2e650f2798692219c6781551ad","956c39dcf73bb0efd0725e3ad83f936b9418dbad474d8c41265871e0ea7946b6",38u,36u,false},
 {"fb39b92fcc8597c8c3d9b140037197dab02b55afa41f16affe1e35ed1b12673f","e2ca4e2b42a8fe1a97784b60a10e04ddb8efa629feb8730780be29e99b395f00","7e655768acf13b8d2c1cb603f106475b6d6d64303dcb549af688c4d7499d777e","b50a88ae374a5daef5916efea9ee5cd85ddecc7441b5f74419749622efc138cb",37u,54u,false},
 {"5bbe6a52ed62fe4cca6860c3e601379fcf6ef403ecafcd5b8e3d9db5fa909b1c","9b3e1f3398d0d63805a9fc0edf927df8e37d08475598e1753a8f312bb1457628","6f3d81770e96cdeece57ab6a94ddf8bcd74e542bfbb0d1a36e2cfe611ab9193e","cd832582d70a6d9718874c08426168fa984c7034b947c4d954ace2a794bd000b",91u,90u,false},
};
inline constexpr bool kPort3TataWheelMixed[]={false,false,true};
inline constexpr bool kPort3TataWheelWrapU[]={false,true,false};
inline constexpr FleetRaceProfile kPort3TataWheelProfile={"Tata","TATA","port3-TATA-WHEEL-FLEET.ps2model","3ac622ae2d9f66c55862916526df9b5ea929a173e661d211546ba0b6f3aba65e",60865u,300u,756u,5u,3u,4u,4u,kPort3TataWheelSources,kPort3TataWheelMixed,kPort3TataWheelWrapU};
}
