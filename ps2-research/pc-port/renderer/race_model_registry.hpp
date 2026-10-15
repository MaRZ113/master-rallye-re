#pragma once
#include "frontend_source_registry.hpp"
namespace gfx2::ps2port {
inline constexpr FrontendSource kRaceSources[]={
{"57823f851e6e47457502455cada8d9f3e3da7541cd63ff60be5ff7c301e1f559",362u,265u},
{"16c3cf75f8d9aa9f4a9d96c36fb0c4f70e1046ea324123b51237158a7c12a19f",244u,209u},
{"b0a740c73bb78eff350d6aa9e981dc2cd08366e9ed2cf1e866226f93faf0c615",158u,155u},
{"fbfb12b7cc689359bf694747ef777f736e2b8013261f4887a294bfdc35f1bba1",117u,77u},
{"1b9207f7417710dac3d85a27a54ebe616037367f1d624c53d5d65018f2ceb84b",130u,144u},
{"4fe1e64fe885c9675b9b3ddbe7530d2ccb6d36c341235c2942179e50c26caa09",76u,62u},
{"46b55eac513995bb703f7b8ac2dc205b497368a356be95d979c8d45ba7b96425",6u,4u},
{"708755f5c5e6ec814bf2f1ac93314bf4a51cb467bc2e711cea37a0d2594c4d24",49u,34u},
{"6f2174a662b45cf1cfd3c18ed12ba50f0ef2fe6b8ce942133f61eae64545d335",50u,50u},
{"99ca3a68595600ef18b4a46f8428653493bd8085db4959379ae94cfe5375be78",201u,166u},
{"e580100f2670ba7bd87589727e194026f3f28d9b54b42eda325d51e47aa136b3",20u,14u},
{"505314b112e7fd37b0e352938d6145fe5ed55a2395c8f6e844bc62dbb5c7bef0",145u,110u},
{"28f86c4524b283c51c5d5ed7ef322de7cc328a137cc0403f6bf96eab4866a66a",80u,140u},
};
constexpr bool race_warmup_admitted(uint32_t seen,bool next_frame,bool current_tokens)noexcept{return seen==0x1fffu&&next_frame&&current_tokens;}
inline constexpr unsigned kRaceRoots[]={0,1,3,4,6,7,9,10,12,13,14,16,17};
struct RacePartSource {FrontendSource source;unsigned root;};
inline constexpr RacePartSource kRaceParts[]={
{{"fad797c65838c39d359767a9ef06d0d5579d847fa2b23a9ee8febe8c171b361c",22u,18u},19u},
{{"cb24d664e8af1db40cc4b161c7875e34a2042e709a5783384179b37f0ce5fe63",30u,28u},5u},
{{"7e42aed180591ce5a99972f8766f1d999d59da87c8212183e528f7fd7fd5f838",18u,14u},11u},
{{"7f25050923f02b8e45c1c58e8490fe7d81fd784714ccf7d45df5acd64d03edcf",32u,34u},2u},
{{"c13f3b8ddd5b45c25ba0373b220b6d03c5216437bdcdf8b31685fb6c2c7d6107",12u,8u},2u},
{{"c12103f1583f862fdacf699ebb482b14467d1f54bccfa8edaed35f4ab25dd8f3",62u,42u},15u},
};
inline constexpr unsigned kTrim2Pc1[]={33,28,30,37,29,38,36,34,31,32,35,40,39,41};
inline constexpr unsigned kTrim2Pc2[]={23,22,21,20,16,17,14,15,12,13,18,19,10,11,27,26,25,24,6,7,4,5,2,3,8,9,0,1};
inline constexpr unsigned kTrim2Pc3[]={46,49,48,47,42,45,44,43};
inline constexpr unsigned kTrim15Pc2[]={0,1,4,5,2,3};
inline constexpr unsigned kTrim15Pc17[]={6,7};
inline constexpr unsigned kTrim18Pc17[]={0,1};
inline constexpr const char* kTrim17Removed[]={"beda4bb8f52d5beba393549ea1b18325f4755bda7e1e581549c2698737122870","e3de9705f20ece3b79c988724954f151ea1b37cccb950bc7c32f02d5388ff002","773f2b243d058df7764084685e3bb3fe27d4c256a7a795bfedfc985e060db83e","daa2b87c59110aed9222b2a54fc24bd4c77e588a28309540f499b7305653f9be"};
}
