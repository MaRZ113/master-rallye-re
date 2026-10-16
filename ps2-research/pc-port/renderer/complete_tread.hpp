#pragma once
#include <cstdint>
#include <cstring>
namespace gfx2::ps2port {
inline uint32_t complete_tread_u_mask(const char* sha)noexcept{
 if(!sha)return 0;
 if(!std::strcmp(sha,"23e274aa87ed9e855c1e64da3a121bc53f1e85e1b3355c0c053d2111f6610214"))return 8192u;
 if(!std::strcmp(sha,"423890a58b834aa3cc083461c3b68eb821c782b40801ccd730a0ee6cbc29db77"))return 1024u;
 if(!std::strcmp(sha,"567fe02dfa617797000659a5644908d9d96e1a097793a6d46b9658d32be3cf2b"))return 4u;
 if(!std::strcmp(sha,"7cb18a6a53e3b5d7b7295de9d0570a76e2be2be38381d9f4c212df6b1ae3208b"))return 2u;
 if(!std::strcmp(sha,"83f21a0b5c0b43713aebeef457ae538efebeb198dd48284c2cae5969d532ecbf"))return 4096u;
 if(!std::strcmp(sha,"a7797542b0fabfe513ad1bac8d906fc09f3fc79daaad93db7b6e4d490698b8e2"))return 8192u;
 if(!std::strcmp(sha,"491ed6e8b61214fbb3e816c4fdd97142a24ab1413076da676f079a15b0131ca8"))return 1024u;
 if(!std::strcmp(sha,"df3d58336f6596cc4915b055820c5d0008b116b33091cca6915abdf971d3826c"))return 262144u;
 if(!std::strcmp(sha,"6ecc4c5dcbe31802e4772b21f97cbe5eada279a78dbe11414edae852eff111c7"))return 16384u;
 if(!std::strcmp(sha,"e2cb00f367bf91ee68eb7443792f0f029be13db4593e9179596275130af2efb7"))return 4096u;
 if(!std::strcmp(sha,"9a3049a5819f31d05316754f803f26c969b6eda66b05b7b09249db545e7cb1cc"))return 4096u;
 if(!std::strcmp(sha,"d9eebc0f6831a29552dfab612e0804b35a353259b647935ae255a0cba932d63b"))return 1024u;
 if(!std::strcmp(sha,"3d083ac40dce84877b842757b99471670ac7b8dd5d20a623b8160fd73ff0bd7e"))return 1024u;
 if(!std::strcmp(sha,"69966f861ef742a990d6b7511bc455a9a1fc00d439b722a86f33b8234ecdc28e"))return 262144u;
 if(!std::strcmp(sha,"7272d6ceb2982b9064c9ec38628fa04188b0eddd779a9edfaa2ff498ddd1b7b4"))return 2097152u;
 if(!std::strcmp(sha,"dcff642f00076545705e7565bbba67aa5e18280752d386135fa961a21e75cc7f"))return 32768u;
 if(!std::strcmp(sha,"20bd065ecbd2b339ec97e804a6c320c20b72c15abccd9e9bdf59d9fefec68315"))return 65536u;
 if(!std::strcmp(sha,"0026bf54d4e88149a32cfcfd51ee606053cd16f0cf03eec09739f146bcfb4624"))return 32768u;
 if(!std::strcmp(sha,"e3018aaf0eecc1566471ba575b3e4fd40b2e13a5039ebdf06e91c896df6623cf"))return 65536u;
 if(!std::strcmp(sha,"1f3f6e7fb84aa4d4cde3136ef38576059986706dd30c90e398cd2e4ce42f4fd5"))return 65536u;
 if(!std::strcmp(sha,"5add1b293c2881cc5ab8c754b9ed1f90a56e4a52d6895ad58ed3901d377331f9"))return 2048u;
 if(!std::strcmp(sha,"553189dd2b55fd39b3210bb7c6936523a815cf8a8b75df71954f59438d634d4f"))return 33554432u;
 if(!std::strcmp(sha,"6fdbe60af4544fb5fb97a33bee5c94412aa284a53dc3e05307f1af3ca02c0611"))return 33554432u;
 if(!std::strcmp(sha,"6401b2e3c16121b6397399725b94c176f19c385d85d302db85fed512e3d5e3dc"))return 8192u;
 if(!std::strcmp(sha,"310c10ee1030188a7741973bef45c568096f549055c3d6c5b721cbd5540b10cf"))return 0u;
 if(!std::strcmp(sha,"1d413c38c44dce3b29bfd008c8f67ab29614b79b285c96fdd9a7d96351805d1f"))return 0u;
 if(!std::strcmp(sha,"4192fda7741e5beea01f6222e0ec9b18148ce68cc3a6def4a01672aa578f7b5d"))return 32768u;
 if(!std::strcmp(sha,"9cc3fc4d7c4690ab7dd3876b809a20cc80c97d97198fd9dbed069c06acdd84f5"))return 8192u;
 if(!std::strcmp(sha,"9e74e64b26e2f58122461bf99cde9f8c19fe81f54e8038b4baa5c5315a7f633e"))return 8192u;
 if(!std::strcmp(sha,"6444198f7ea60e60e174ec6fa587483cec4e10b8a6dfc9b4f35673748eae9cbe"))return 524288u;
 if(!std::strcmp(sha,"ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b"))return 524288u;
 if(!std::strcmp(sha,"641406d6ff45e028bb26d38bf69ea53dd48afd3d0fe420284e8055ca5f5809cc"))return 524288u;
 if(!std::strcmp(sha,"ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b"))return 524288u;
 return 0;
}
}
