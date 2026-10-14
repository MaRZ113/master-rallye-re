#pragma once
// Exact original PC normal values checked against original PS2 root.14.
// Position hashes are not geometry arrays; current UV/diffuse must also match.
#include <array>
#include <cstdint>
namespace gfx2::ps2port {
struct XtrailDecalNormal {const char* position_sha;std::array<uint32_t,3> normal_bits;std::array<uint32_t,2> uv_bits;uint32_t diffuse;};
inline constexpr char kXtrailDecalGeometrySha[]="e580100f2670ba7bd87589727e194026f3f28d9b54b42eda325d51e47aa136b3";
inline constexpr XtrailDecalNormal kXtrailDecalNormals[]={
    {"173ed77cc7b9d13a27119d09efd1583765dbdde575988de4ffb60996b84f286e",{0xbf62eb1bu,0x3eed03e3u,0x378456f5u},{0x3a030a00u,0x3f7fdf44u},0xff9a9a9au},
    {"2a887eb85a2af89b4efb2089f6b2a2f05b35cf85038257d7429bb9b70d82d1d1",{0xbf7db2a1u,0x3e090561u,0xba16b478u},{0x3ba8fe40u,0x3a259000u},0xff828282u},
    {"36732e484edc8f93fc6e535f4ed5894bca0dcdca5ded89af60961a49a0c6e548",{0x3f7df99cu,0x3e008a82u,0xb98a5610u},{0x3c57bc00u,0x3a02f400u},0xff818181u},
    {"36fb95f35f5abfd60c19e086103014cc8ca14c3c120ea01ca7299fe9abe411cb",{0xbf716cb0u,0x3eaa4bc5u,0xb9219addu},{0x3bbd0680u,0x3f51b0f4u},0xff929292u},
    {"370903c1defec6fa1bbb4523afc8803e71daa6ebef09dc9d8da638fb8bc9db06",{0x3f7b8320u,0x3e3ee214u,0x3b140c32u},{0x3b52df00u,0x3ecef8bdu},0xff878787u},
    {"411c1a750e68d2b176602aba570e8ca6c47b74245789b98b21d7597c799e73aa",{0xbf7b54b2u,0x3e42aa9du,0x3b1b9a51u},{0x3f7f2d22u,0x3ecf927bu},0xff878787u},
    {"5a1234028d913584873fb83da29f36492fbb1d0a731110cb744565b44b8b9a3d",{0x3f7bb011u,0x3e3b2831u,0xba3f5a7du},{0x3f7ec23du,0x3ecd1007u},0xff878787u},
    {"611ae1173ba6f49d8c9f48819acfabd648979a82fae75fa1f16242373c2df076",{0x3f62eb11u,0x3eed0408u,0x378314adu},{0x3f7fdf46u,0x3f7fdf44u},0xff9a9a9au},
    {"65a7dae913a8227d4e6b2678d46e9ee8c3a35f03ed795d99c68facd508cae1a2",{0xbf7b707cu,0x3e406cd8u,0xba033050u},{0x3bf152c0u,0x3ecdbb54u},0xff878787u},
    {"6c6434d835f704b4ee45a6b89336b349bfaf4e72c6524d8046b613dbfe8af7e0",{0x3f6f9c64u,0x3eb43fe9u,0x3ab8a56eu},{0x3b7bdd00u,0x3f5198f0u},0xff939393u},
    {"6c6704270b5ac59ee349a3ccb0a975328dba4c355a4138b48808ea6b72a858af",{0x3cd25d0eu,0x3f7fe9c8u,0x3b8d0b43u},{0x3a02f000u,0x3f7fdeb8u},0xffb2b2b2u},
    {"712b53d445584c6722a102254f220b877c4d5be7f293f7e6f1851da06deb9ab6",{0xbf7dac37u,0x3e09c309u,0x39c07298u},{0x3f7c75a0u,0x3a02f000u},0xff828282u},
    {"778d876c68ffef12bb1da61b286e32bcb72a546e698968021523a376b50bf0d7",{0x3f7e1a85u,0x3df8cd70u,0xbabe8696u},{0x3f7e2467u,0x3b350180u},0xff818181u},
    {"77d385a20f6334c1d2e5c8607cdaa818d21aa24d2c1c210e347b8a28f1355f1f",{0xbf62d6b9u,0x3eed51dfu,0x39129439u},{0x3f7fdf46u,0x3f7fdef1u},0xff9a9a9au},
    {"8e7b12fa9bf6b7e3113553ae9b2dc96855a3fadd1b7bdb27bb4cc0939ed987c3",{0x3f716d4bu,0x3eaa4855u,0xb927060bu},{0x3f7ef380u,0x3f51999fu},0xff929292u},
    {"b1db30562b225c604de5f0a48ae8e9ff3244a32db47242d0a3be2f2b17bb9092",{0x3f62d6b4u,0x3eed51f4u,0x3912c3a5u},{0x3a02fa00u,0x3f7fdef9u},0xff9a9a9au},
    {"bd4b703254adb774ed3b877640cd10ddf6d1c76bef83437ed1e4cc98a0ad28c0",{0xbf6f9c66u,0x3eb43fe0u,0x3ab89e76u},{0x3f7f041fu,0x3f51b042u},0xff939393u},
    {"ed1b4b7cc0f9d55b5c403e6e48a63bab80dbdf7701a6ceca3bd48b9a4297ef4e",{0xbc9f0ca6u,0x3f7ff344u,0x3b5f5ba0u},{0x3f7fdf43u,0x3f7fdf3fu},0xffb2b2b2u},
    {"f3ad7088c2b438332bf6e46b764857a19981d1362c239e39a09dcc1514399c3a",{0xbca29962u,0x3f7feef2u,0x3c3830c2u},{0x3f7fd206u,0x3a02e000u},0xffb2b2b2u},
    {"f8652e232c8cbc240c4cf5694cc828e0436c9f93f89e7f3d62ab623c9873b7d3",{0x3c982d45u,0x3f7ff222u,0x3c10c3bcu},{0x3b5b0c00u,0x3c8e1480u},0xffb2b2b2u},
};
} // namespace gfx2::ps2port
