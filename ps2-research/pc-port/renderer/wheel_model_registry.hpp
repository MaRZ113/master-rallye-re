#pragma once
#include "frontend_source_registry.hpp"
namespace gfx2::ps2port {
inline constexpr FrontendSource kWheelSources[]={
{"2f4938e041122fb29ecc25c7ebcf53a535c33bcacc1e49268e158722677af698",54u,72u},
{"a57e255404ce0f61f76b3985a44d870f4eddfe03222760c7f36a9380894cd875",38u,36u},
{"a7066b168c5330f1a2458fc08e671ec06ce634d2936983a09e06238fee35778d",37u,54u},
{"283ca0c3a366146405df4d3fc18755abbe09376d11a7c326ebd25979c4b06c35",91u,90u},
};
constexpr bool wheel_certificate_scope(bool current,bool single,uint32_t participants,bool chassis)noexcept{return current&&single&&participants==1&&chassis;}
}
