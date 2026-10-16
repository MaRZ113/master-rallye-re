#pragma once
#include "fleet_off_lamp_registry.hpp"
#include "sdk.hpp"
#include "reflection_capture.hpp"
#include "vehicle_classifier.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {
struct DrawSnapshot;

enum class ReflectionMode : uint8_t {
    Stock = 0,
    TataBonnetPS2StaticContribution = 1, // Historical identifier; record 19 includes hood and roof.
    TataBodyPS2TextureOnly = 2,
    TataBodyNativeTextureAddOnly = 3,
    TataBodyPS2MixedContribution = 4
};
constexpr ReflectionMode reflection_mode(uint32_t value, uint32_t version, bool supported) noexcept {
    return supported && version == 1 && value <= 4 ?
        static_cast<ReflectionMode>(value) : ReflectionMode::Stock;
}
constexpr ReflectionMode reflection_mode(std::wstring_view value, std::wstring_view version, bool supported) noexcept {
    return supported && version == L"1" && value.size() == 1 && value[0] >= L'0' && value[0] <= L'4' ?
        static_cast<ReflectionMode>(value[0] - L'0') : ReflectionMode::Stock;
}
constexpr uint32_t reflection_override_mask(ReflectionMode mode) noexcept {
    switch (mode) {
    case ReflectionMode::TataBonnetPS2StaticContribution:
    case ReflectionMode::TataBodyPS2MixedContribution: return 3u;
    case ReflectionMode::TataBodyPS2TextureOnly: return 2u;
    case ReflectionMode::TataBodyNativeTextureAddOnly: return 1u;
    default: return 0u;
    }
}
inline constexpr char kTataBonnetGeometrySha[] =
    "f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669";
inline constexpr char kKiaBonnetGeometrySha[] =
    "03f88e7a81ae783819b1ad64ac54284b0b330a4c488c851411aee0378706d729";
struct ReflectionMaterial {
    const char* vehicle;
    const char* geometry_sha;
    uint32_t triangles, vertices;
    bool mode4_only = false;
};
inline constexpr std::array<ReflectionMaterial,212> kReflectionMaterials = {{
    {"Tata",kTataBonnetGeometrySha,55,48},
    {"KiaSportage",kKiaBonnetGeometrySha,206,234},
    {"Astero","997e58e39b009bd36d815ceba962e1d8c1cb10607b386be66713055cd2924876",452,546},
    {"Astero","c2b275485107944f723953587e8c27e111aedc265483651886bfa3ee590fe202",16,34},
    {"Astero","36e32670690a73983be705a11ee7af7fc1cded60cb2ba1b6140fa6e912cd450e",19,33},
    {"Astero","859250a282a441b0728ec32a802d0b15b5d8c825b6ebdc3f73a24da8d5f524b2",19,33},
    {"Astero","767c2ca5d13c98124c15e35a3e06740bd345074da30718b4bf0e5c0a94481314",167,192},
    {"Astero","50e54731beb9a1ee6ead18f59beaf8ed5d08e0e47461d99f8f38fb91e941fb32",42,80},
    {"Astero","9d6a27592672a963efe6c83c04b778cfa7fa64410bc5fec7a13ff84c3b6118d9",14,26},
    {"Astero","0df22e4bc58fb740fd254cff7fdf67bf79fb1434fdc429001cefd39dc22ed105",18,19},
    {"Bruno","c48b56473f3948542e2848143ec5d7cc87f602cafe15a59b0d0d7998e3adbb45",10,16},
    {"Bruno","3d8fdc7970ec5a9f85ae145110fc66a2da685d009d874522456199c3566c8995",200,267},
    {"Bruno","790d1b1f79e4cced96771a5cde41fd4c1675eff2022ced41d1e62e2723029bfb",36,38},
    {"ChevyBlazer","e269e783dc51b08bfaa611b966e452692dbe6f3c8c9f4f6240fd783718141cd1",16,18},
    {"ChevyBlazer","ec1ad8aab23febc5a69ca9c2152f621f6fe89623a14d75afa6623e6528fa6f97",77,89},
    {"ChevyBlazer","46ce6b742095ae8f10ef03801a63d67e6224407eef4e9e902e27a1a8e4ab3941",112,103},
    {"ChevyBlazer","53e19423690c92974c4998333d3d25b0eab3744cca6c697557face83dc8ea62f",199,232},
    {"ChevyBlazer","4f5f050327a269169e3677c4330d2c50cc1184fe9bdf1465eca06d3261c127c3",10,12},
    {"ChevyBlazer","419cec476a248a478f1a61252c917ec44845be87f040aa7d7a88654b833245e8",10,18},
    {"ChevyBlazer","dc356e0049b5907f1c85dd2811ef8635a40474d64c751e4bf244a17dae0ec1a3",12,18},
    {"Frontera","1f4a4501591bc7306755800f5a77a7f7efa38ea79c3cbb88743bb40b5a1b4cd9",100,148},
    {"Frontera","53fd6f52e511f09dad11deadf92334fed03358f342f985f1105eb0d71a36fa1d",224,361},
    {"Frontera","e8514fd25bf0c241a01a38fa9cee87858c1cc06f660c87ae0e186708f7b86407",54,70},
    {"Frontera","800529ac2c3ad94c0f58cd754a8732cd49ec2fba94f6cf27bd6adcde53ca49cc",4,8},
    {"Frontera","49c4bdc85f290790a4594e47ed5c571825df048fec2363bdd46c1e501470d2d3",14,24},
    {"Frontera","4b3fb3ba005a829ce8080eaaeb10dae4e9fb4aeffe3d96af5aa4bc171a7e5dcc",78,138},
    {"Frontera","2bc10c0ed5ee4f81d8c76e102ee30aa1c474174fef07ff1718a8fb4892f3865d",18,19},
    {"Frontera","f5483a6a60b02f7e987ca7c46c9577d90cf87229c33a41b331ddeb27fb8bc436",37,45},
    {"IceCream","ab4f626cb566f24a301ccf5122205f459e75219402adb6cac65e99cdffe12d05",74,92},
    {"IceCream","c8f6f40ac9858390145334ed2401f6f481ff21d13e3e513508bf4b02231883cc",24,52},
    {"IceCream","28fd34f73304f4dcdd5b1fd5c4c5c8a13b911e08fab1fe033c326806b4eff031",134,126},
    {"IceCream","3f109f76f44f7a31a010c1a23f9bdaa18d68650d880b6a74e78d53a66eb36c24",20,24},
    {"IceCream","f74192bc9be5dddef79ff5311d60340d663086180a4ccc7f3ca627bd32e7ec8b",11,19},
    {"IceCream","db0f3f9ecd35cb6942261417a68a18229a72862bc93bd1fb71fbe02e5d14d40a",27,29},
    {"IceCream","e657c08707b0f4c8b25dd098a2d995cc11cf1326c7a73c7fc588b3a596146ba0",4,6},
    {"IceCream","75795494f99b87e47e9616e31d81e9f03b2dcdeec3036dd50da4460bb7960413",24,40},
    {"Jump","ff02375fe7ed45eba07da4e876b361970ddb8497ed5bde35d8b19952d954d598",362,500},
    {"Jump","03b9ac123c1902f66705940e81a07cccea4754af1b14e4deffd40042457043b4",18,19},
    {"Jump","5a9923793251d47fb3010f96a9bc194a4e932e7bfaaf1021c0896fb4f52ad148",6,12},
    {"Kamaz","b0988eecc7da8c9ed4834324b6d9843d7f91b95a2b95082bf1d7a3e3245eec6d",81,70},
    {"Kamaz","c1bf9fd63135ecc9be70d4e4968a3ee3604ce4b21da865d4d8811c5e06d31ed7",6,12},
    {"Kamaz","b3de284939834eaf44f74c688450c723220a2ade500c7335a15e0814ae8e3495",176,188},
    {"Kamaz","bc5906861078a153bf9ea301091445b9347c1c79e624fac008e0f0123808a443",138,130},
    {"Kamaz","4e24d3d01f8592819e40f09fb95b2e49c8783e85f53b71388b287d520a2658b4",82,91},
    {"Kamaz","b58a7a7787d713748cda9437ddbbb13be628f739c830d78e32d730db4f1ad71e",11,17},
    {"Kamaz","74adbb0b3163a8bb70173dd49018ef925bec0500ed9b9162016439cf2286e505",16,28},
    {"Kamaz","3f0675e14422e3788b5f0b9d28374a85901efbb1f492ff0329b97cf31aa7f262",90,78},
    {"Kamaz","b41cdd2155f2038a7a95deb23cbf302f29a9989a8407f5e7a473ff633782758f",24,26},
    {"Kangoo","f9b6df5d3f8a534b945550c341abd6c1949a10e2016f6b4f520574785625c5fb",630,854},
    {"Kangoo","941263ee80d71f1fd76fbeff1e4279718e026fd2106dd12a92ea1221be6c4fa5",14,24},
    {"Kangoo","1fe30ba832c0f63f144cb408448ae6e9f479cf5a913586e53b9906698220fd66",36,50},
    {"Kangoo","14d5c24f9b312b635131206d4af96b362e810c1f88c50fad9d0cc7912e471604",228,260},
    {"Kangoo","89c5d800268b6d487abf7f08b430325a6fc949d6904b666b1a2b5460109e5d3d",48,96},
    {"Kangoo","f3779509256ab28e120ee5d798a56d923d52af972810b7674ce3b911bae455b5",48,96},
    {"Kangoo","c720df8ea27b0e0171d9921560aa6c4be018086481990ea05e5054b4cd823482",82,86},
    {"Kangoo","8deebcd9bf6a5af2e1260c6113f3b99fd37a457a3011fee20f983d9ee9e97156",32,46},
    {"KiaSportage","bdeca6ef2c9f43ce792d8b07d9fef40e5ee25aa5aea41a1cec7254fdbcdacd3b",442,412},
    {"KiaSportage","b7d25682754f36a15d31227beec9ac008867fe378320598e8810bfe2a88f3c67",14,20},
    {"KiaSportage","89c5a53f92b8c5128995a0018a42c198e41c1d958f60eb76d019a6fb134ee30f",36,42},
    {"KiaSportage","2d60f7f2c02f82524d60bbf1fdf3f9f2efd0a06dc2ddac368b20f10145d0c649",22,29},
    {"KiaSportage","84355a30f61c8989d8bdf219daf186ce4bfadc3e45d0c16b7ede0e7c50f6e0a8",1,3},
    {"KiaSportage","8c653c9e68e2042f19846b9f6d17fb9b793cd7eae5a8ed8846f390df24dc055b",31,28},
    {"LandCruiser","903030711f9637383f29910a2fcbccf8131f9adeb2a0706c8485de2cc55c6375",62,95},
    {"LandCruiser","ace5748214661b22a3466170dec248f6234718dd0b4360d72edf8e7d0117a23e",14,20},
    {"LandCruiser","010459fda3bbd6d0c8ab29979d4242ece4a45acd8a69a5317b425d95e9277ad2",4,6},
    {"LandCruiser","5922b5ae578f3a7a40f88cb666e8b62ab18f5ebea497f893e78863cf2062974b",18,19},
    {"Mattserati","190d97af160dc84e400814db6720f64d823381971a394c33542d83a0c424d032",69,109},
    {"Mattserati","3f768dd1b9046e10daf7508c8e9defcef64c7e02ada541335bac2f5dde420ea2",418,490},
    {"Mattserati","aa6a62b455e8508401a6a8d1256266d9da73bdff032fc9b63bebe51a92b37d83",8,16},
    {"Mattserati","c35aa106a53354801b552c0962d0b0b39acc1cacf3753758953bce1a83579e7c",18,19},
    {"Mattserati","46678f10ef5a0a491ea0f1fd45ca24d5a8fe13709606df1635b2ea5fd8bac50a",72,72},
    {"Mattserati","1c7baa4204f7e5851c29f5243e127ba091fc2247cc9d2c7db21a914cde1228c6",6,12},
    {"Mattserati","0fc12296809a2e188e138e6eeb9bf0e9efb7825ffc3ba578657bbce5e26d5b95",16,18},
    {"megane","cddc5f03c63c39ad2b62f6e33b8dc7957cc182f7bb21ae43023c45021b19ca41",74,68},
    {"megane","18d67b9234b87353d14eadbb132890e379940df3fcfc709cd11a9e07a3d49d34",532,753},
    {"megane","ae4067bf620adf2797a25baa9c45d94240abdb8eb9f7019faf4fb5a2d91d4ba3",141,185},
    {"megane","9ebc46494fccb5505834dc8343130a7a73699ebb6bb36235f4cb90216998eee5",12,18},
    {"megane","92eb2981e8f726609303764786bedfd044fa1c589da91c16eb88feead666134a",22,22},
    {"megane","ca15a3be82862b1e1661161474c9eff0fea0c393a0e65c32e510b8eb877fc2a3",66,80},
    {"megane","43b9d580b3d6cfa4bdb2a4acfc4125709efa6352e2a334aa9886081b036d5859",4,8},
    {"megane","fa1657ee40f08ee4f5c70c0b0e69bec2969cad176fdaf93d27da9bfce762ef7d",10,10},
    {"megane","aa832a879431c401a955a373bebb31da821a583792b3f538724db09437bf5190",32,52},
    {"megane","514cf1c653a0d73e03048005af14f81df7d98003d52ef68dde18fe99b5a750ee",12,20},
    {"Navara","b52ce1370d543e68d4da15d3f44ada77a8e95857e16c8fdd4202484ae7363376",22,24},
    {"Navara","2e466a9a320ee83ce69a6b7f9e05f53b0e9b608fa78147a21b0495ec897287cb",3,5},
    {"Navara","9924d02f99037bae7da42856dcfcbea4be58ea37288f7725d0aa58896a5b7eb3",50,70},
    {"Navara","1a9e4024333a2f4fd80dfc4cb7f6e461b38099ba28dbc28d8f3922e62a4674dd",4,8},
    {"Navara","0660f632faa1c76ba19b8300739e5e6b373df909e5fb3faf87e081ed9878ff9b",16,26},
    {"Navara","b60ce0bba0d07cb3cfd9ec8f319826c31c2dd2008370d9f43213dce9ec9688a8",34,48},
    {"NewRav","3dff4f2f95c6be235b64e74e7611e4674cb1a69583e7c38b07bac11070741cd9",233,383},
    {"NewRav","73f39a6f99e915b3322fa4e6c24f9a1cdbd80ecfae7eda0f481e89165edbf684",168,240},
    {"NewRav","2131ef6f94d06b9dce407fd3384ab733e4e2c301d86a7cf1c78b8e39b219f597",77,105},
    {"NewRav","71c35efa57f98551e8f7dae4c7330719e39035abee76cbc790b9ead0466b959c",14,20},
    {"NewRav","a89f530265416b0a54946943ad2849f314029fe36c7356a0aa7070979240fa25",30,46},
    {"NewRav","3a317bf24de6b2525fa5946cf8162415bfbccf60c796573284f29e67c28351db",83,84},
    {"NewRav","c8680646c7e2a39b484ecf5cc4868b5540861e5cd8e74293f66d4629850c5043",27,32},
    {"Pajero","0275d653855264f615e044f7ea109d8faecda4e55872c29c5157487d70fc9d9a",88,120},
    {"Pajero","1951badb6aec327cc541cefa6db6fd6d6986ba791d50c016bd6c5928d270114c",18,19},
    {"Pajero","1fd2fb18c9562f667688669cc4d46a9e2bced961122afb57b6e16a727f900dcd",24,28},
    {"Pajero","ecd1f557f8c918bdfcaa7db0c2485e69b2345532d12a897d99d406c0f57c9406",588,758},
    {"Pajero","51649f9d49e28285127b2237e09f05379e091b4ac57312e94d5b8161b0958a7d",20,34},
    {"Pajero","1d7992af4274ec82affc931267c506d59b203ff87bddd58f1d2dd10dd7446c59",76,91},
    {"Pajero","af103289e379cc017afcf23dbd5633c3c7f7d883e92a5d08a95ee9b77958a0c5",18,22},
    {"Patrol","85ee3393562608d432ec944ef4ccfdca346e006ca0f90e42e7703583d7008d9a",94,101},
    {"Patrol","e0a981b6164cdb3f7c5e7ed841fbc8f95942f65ec3cae4107346f9f5205e14e7",12,26},
    {"Patrol","75440ef03d17a5b2a314f065106e88f2dfe9cae01ca29546559a0abb2add0945",42,66},
    {"Patrol","45a9730ad79880ec308c126860595c7410b8c011d658033195fd31f1b36a1201",72,84},
    {"Patrol","91af40ef54d91fea42a4bfa88b8a03a9d2d44eafed061760cd0e90757bb1ce1f",14,20},
    {"Patrol","31e160eeb7cee1aa00649a766790a04a56fd50bfe005c2f0ad65ce5c9dbc08bd",42,42},
    {"Patrol","eb2b34bf4c24d12055530beb0d6e7640e65cfa2f0bec7b8a8022f61f7329a94f",18,19},
    {"Patrol","7a96e63c892dc814331731fb4a401ec0d0fa555e3e303ad9118c94b042428124",72,72},
    {"Patrol","06e9dad19e98f7690e97c15fff71245b9fd7996e526323f2591f005e7365c3c9",140,183},
    {"Patrol","e46c7985f0d7269ab92ea0a8818ec560888355ee539e63d498e3bdaac4bf6e09",16,28},
    {"RMonster","e85d1757705c65b6bd257441f3ee8be9ce1606d846d9d1694a6e36a82465778e",346,456},
    {"RMonster","ace0f6a621562de1c8eeb5e33be0451ff1a311217a6230fb17db65c63725d070",175,187},
    {"RMonster","c021eaf1bdabb4bb74916c2d2ccb8eccda8bee8648230aee0b546ef7f5e0ab7e",10,18},
    {"RMonster","b621048a231f8231a57343c8694f353faaef77e40c446c3cae14986bc7bb95ec",18,34},
    {"RMonster","697c13950ec6453f112f254bbbcb131490b5da542a9b5c732e22deb8d57757e6",108,154},
    {"RMonster","a1fdeddfc502b3e25f2555ba5b193792fa45025f35beebff1a41eaab451428ed",8,12},
    {"RMonster","574ad23b6e4de78aab51dd6be3fa0cbb50cd77ed8fcfd3d5d98c1a866131eb57",30,46},
    {"RMonster","091c883ce6b1bd57d7490dc8ec26a8e6940e71dd80f3524fe694afb0b2260d19",48,82},
    {"RMonster","8fc1788b9a5c483b5b4c8455bd6c30cfb9c24baf22da03c3737001a0f70f33b9",64,92},
    {"RMonster","c7bab72349c91fb96db78dd07a2ef5fc476be7b6abb906578414bcc14a28629a",14,24},
    {"SeatBuggy","4238e99bb44f2ff2c81e75b45551d42486d79030700766f0e04e7d71f53501a2",225,251},
    {"SeatBuggy","c49b2aff523729b8288dab8d24241e555b887a000b800bb4ecc54142e896e78a",37,69},
    {"SeatBuggy","0697ea98391fa948e79671b3b847ee8134240b1e079a5f28883bea0e0d90a600",149,191},
    {"SeatBuggy","9da1c5395f0151a8cc9c486fd2400fa653e2b70fab431109a79f07fd18cb6d36",16,22},
    {"SeatBuggy","0c3f62889e4947aaf6d1fb4e3e50955aa91bfc89961adaefc44a3cadf558346a",34,43},
    {"SeatBuggy","ac9dc9840c96bb907ab3d34b9e35e3482dfcf7b830a80d629802bae690c2562a",14,20},
    {"SeatBuggy","41f221e840bbc48f4cf973e44526a74edef44470f28a6e09039d7b0d9c90d9cc",28,30},
    {"Simmbugghini","a0cf0d0091e414cfef5d20532aa8959434313bd98fb4ec27ec094a0918ad577a",50,52},
    {"Simmbugghini","08ff6ac8606e013da3a95053b9dd5944c0bc0e30a1e2415800cca26af1ebf10f",18,19},
    {"Simmbugghini","74ea1b0c7a1779f4dad316a950b753b4fb090d429a367b009f93fa788248d490",6,12},
    {"Simmbugghini","46424414b8028621429a3e173553236706b515f606a08dac555fe12962b145b4",16,18},
    {"Simmbugghini","b05b24d7b27d52ab069d4f9fc2abd75346fb389e24401afb6f0919d81c05343e",169,289},
    {"Simmbugghini","399e38d1168a4a790020dd86355da9c217968d639f579ce128763bc902d071ae",355,445},
    {"Simmbugghini","a6cff1f59f0b9e2f7a7a8775dc64ba00add1b8a0ca181c556dd69af3263cf2a0",28,24},
    {"Tata","6373ace1e6771fcabaaf5e072f8a6e96f4dc8931a795a7c8f7459aa3cd9c31b4",72,54},
    {"Tata","33e329bbd4ae669be77d5907d815a9efc69fa41980d5ccd56173a16013338aa5",54,37},
    {"Tata","c42100dfd11a837b8ea5166c7be63f0d095cd821c6950f941b0f772816cdb3c2",196,174},
    {"Tata","5f7c231cdc8968e2064219c7114c0a87439cc14bce8856a3491fa7f0b7a5874d",54,64},
    {"Tata","12f4a75cae961c3cf55eb5a75e050fd171470bbc61b3009f987bed2d71363ef0",39,50},
    {"Tata","20314d7bd179ab53805bea499534a2d743424167d32c4e0bf5cd1d5de6adb641",40,51},
    {"Tata","23cf0d7ebf0c86463a5c01c078c41182ad940a747acb75086b011ef235491938",68,96},
    {"Tata","07bde161c7f7f4706b1dc175de72d0e8fa29039dd99d0b16ecd90c9006f122dd",6,10},
    {"Tata","476202dfb2992e8d2852962d669889b39968b7a5ffeefa34f7592b6f98ab36b2",6,8},
    {"Tata","0b66c5ba22beb3a6d92d06d24fb942caca10963554bec6bec84d762359bdb544",33,41},
    {"Tata","58a2546ba399032aa458a3bfd1892e72c6eba4e22229fb650267b981f5d12ddc",30,34},
    {"Tata","a6b239a179d9a3d7ead8064e3f899382954ff6beccd60f5ce4fdc81ae9424bbf",11,17},
    {"Terrano","416ff497e11dbdaebb144b05d654584871e52e671750b63ca5a5882e720b2b33",278,426},
    {"Terrano","5c07329920f48f49c26c3b0b1479e5ff0b98bbcbf7d0f88f1e4938f31376b137",34,48},
    {"Terrano","8aa8bebd8a9ea7ee6c35f162d9e014f1976492a8819d97ef5f12a84512c68333",28,48},
    {"Terrano","2c3b7a9925dfbd497de03d444e7586d64e060d24c17018b02a1aa31b8d0d4f09",72,104},
    {"Terrano","c68e0d1ee0fdf2a3e01b5a120009f5b7728dcbfcdd4614aac4c2c02152003973",51,61},
    {"Terrano","460cbf786153cdfc052dfa0ac8a63ceaea931defdcc08deb54345e31bb537677",36,48},
    {"Terrano","858391e764e8092b052e466843b47d406212c4b67b6f00e1a0618b28a9f7a113",40,36},
    {"Terrano","09a26bfc2fa610ecea2c654dbf098477b010201789f935795cc7e3cdf9334cd6",104,116},
    {"Terrano","963d8a41a8551e5911735e795365d456fdedc7d61930ee72dd902ce75d04605d",324,330},
    {"Terrano","7f46a206c472a37c9cb951f0f110f63bb6742ce57466d4adea1ec8896854784e",58,70},
    {"Terrano","b49a3fb8e2f4c0d3b88287dc191056aedbe2fb904e024c83baf697cf422f327e",18,19},
    {"Ufo","5c7f6dad2540a62d93e4d0c6bb3861218f52954317ca0626b347340081175e70",187,283},
    {"Ufo","53b0378998bca0f059935031a14405975eaa46f87023fd48fe70928af43cec62",13,15},
    {"WildCat","cb7b432650076d9d8bf292b1a8db84bf06a1787c8a623b023ab0183ba117340a",16,16},
    {"WildCat","b8dcef1f395d4a052fe39d62ab7ae67427044cea94845de8a7a75a5b16da1c79",571,779},
    {"WildCat","03b76f3bcba935d8c18ccae830459d184107e6026c639c9bccefb2fedff88822",34,50},
    {"WildCat","42a151134d26dddb5314b6255526bdb03a448814339a6b1151cf419c03fadfd9",8,16},
    {"WildCat","57012ef91f0a7d85fa1eab990d57293baf37da9d0bd4367eb7f5e65e98201b33",4,8},
    {"Xtrail","b0a740c73bb78eff350d6aa9e981dc2cd08366e9ed2cf1e866226f93faf0c615",155,158},
    {"Xtrail","fbfb12b7cc689359bf694747ef777f736e2b8013261f4887a294bfdc35f1bba1",77,117},
    {"Xtrail","1b9207f7417710dac3d85a27a54ebe616037367f1d624c53d5d65018f2ceb84b",144,130},
    {"Xtrail","708755f5c5e6ec814bf2f1ac93314bf4a51cb467bc2e711cea37a0d2594c4d24",34,49},
    {"Xtrail","6f2174a662b45cf1cfd3c18ed12ba50f0ef2fe6b8ce942133f61eae64545d335",50,50},
    {"Xtrail","99ca3a68595600ef18b4a46f8428653493bd8085db4959379ae94cfe5375be78",166,201},
    {"Xtrail","505314b112e7fd37b0e352938d6145fe5ed55a2395c8f6e844bc62dbb5c7bef0",110,145},
    {"LandCruiser","fbd7a3fb69d5a778c3e3506401ed3ceb2f91f7c0126af99f012efa5332f99aad",197,305,true},
    {"LandCruiser","e36c4b151978b100ed8494b0013892f114c6651f182b9fbbb2b253c2795a6122",86,118,true},
    {"LandCruiser","e131a178d430924f9d193e30e9a89f16db988eeeb2e8cc72fa63bab44f364f55",104,136,true},
    {"LandCruiser","4822fe76235abab799fffc263871e66e53ea499f37e8442ae2afaee379216d2f",72,72,true},
    {"LandCruiser","4f6da9207adf58905693a984168285dad2314dc21a8a7533d9fa32d13212b0bc",24,26,true},
    {"Tata","f3233d093545d6a9cbc9636e7dcbe5900f5277727db9028a69004a53c14518db",8,12,true},
    {"Tata","3aff543febda265789c47673dd2dac4ad0ab691cd109f2159db6db666dedae94",42,48,true},
    {"Tata","61b6354e0f8ffd477001b95fa87ce06d128b8413362269df4c4835894dc52ae5",262,281,true},
    {"Tata","244165d9ecdbd6c49b8d299f11175e287aa55cd5ea92e029f50b8843f2428347",112,127,true},
    {"Tata","fdca91b5e6ee20b5fb4c738416ea83bfb48121e36a260184f7be70bfba87a54f",20,20,true},
    {"Tata","dfb676b537c04cbddf49836cea6c7184426d63ab8c4b599f1bba951d693abcc1",10,14,true},
    {"ChevyBlazer","2d65b7c9206d4fd31d41a44bd1f047cc3cc409a78084071252d8c8dad52e9c9e",199,243,true},
    {"Xtrail","e580100f2670ba7bd87589727e194026f3f28d9b54b42eda325d51e47aa136b3",14,20,true},
    {"Navara","decf6b9263395df2db727cd1d30f9812892e2cd750ef678047714278d4fbf127",194,342,true},
    {"Navara","7f6073a090e034cee8d5abf6f9b9dc1a4033ab8c801ead3d5a0a7e4768dd22ac",34,30,true},
    {"Navara","b595418684619b32cb4289f5cce347d7c46f60589f0e788e67db60ee218fa80d",48,50,true},
    {"Jump","ef7e117a3dc505ee1319cc429226c54a2674a88d612884c2975f1a2f18afee97",72,72,true},
    {"Patrol","72a9e0d1170e159a7b30cb7c65622a75049eb407f9eec38829e327a78d747ff0",102,106,true},
    {"Bruno","6a1ea21a23e6ef57159a822a5fde1bff180bbc478fa9c5bdb91afbf0899df69a",144,144,true},
    {"SeatBuggy","3b3c62216d984a65653f59ec4b78d90286c4cafa4bd0735ec417e096eb737478",115,152,true},
    {"SeatBuggy","daeb055704500f5c436ac3286b24d752fbfdcb03850d0a3335c31d603b7faa96",4,8,true},
    {"Kamaz","c3b494158a375ace347e22345c70dcd7ee15db7a78a6d684310e388277fb39d5",224,239,true},
    {"Kamaz","fd9d68e789577cb49e4629122ab0f28ee27e82e4dc475fb7b9b604a3e990c487",206,201,true},
    {"Kamaz","074998424ef76b4eb17863e94a77cb6d60f52a48ae27d438c4d318d55e343599",36,42,true},
    {"IceCream","fb22a95cc72744c2d6061a916f343f12dbd87c2d3fded85a3814165462dd2f0d",20,16,true},
    {"IceCream","04c30105f97285e76300c42e97bbcffa47646d813fc1c48d573b76c5bf013308",2,4,true},
    {"Jump","00250001dcff864458edf8ec7146ad51f3cfc45d477a6956d0ec6efd6259386a",168,187,true},
    {"Jump","dddf4abf70d5d640b3097103401377aa5607dbe1e222f63a946fad712596d695",132,182,true},
    {"Bruno","ccd5abae1c3bb625af04bd52c2bb3e9a332d8116fe579b2b111703dff0a619d0",58,78,true},
    {"IceCream","d30592f39b6c05db2e2b8f38ad2ccab4abec4d15815f73987a520a01ecbc213e",502,541,true},
    {"Forester","532ec2bbf56b139d03b7c5bb0bf819dcbe02043312ca18d179d35643708f1158",400,636,true},
    {"Forester","873d4a3e05199eb98cad3ac92c1cedf6f492eb1168c1954d03fd974f2195523a",34,44,true},
    {"Forester","f03b809d450de80c9e01b1b2e67eb643a6fcf355377a55089eedd62060fee065",16,22,true},
    {"Navara","177351f3fc28f71360f8718ab2d14784760ce36588438daa4d2ce0e6aa369f87",677,913,true},
    {"Navara","0bd3d124535e1125357a604a531e0e3d8345801598d3c19547a78cb0da9eb0f0",104,144,true},
    {"Patrol","3db6567e2ab11ab354b8a36da9fd8541b1818c73cef52385f748327d6a45e690",153,208,true},
    {"Patrol","fcb3dc67a4a37ff3c7c1915befe2ffb03c6d6342d9f79f486f812373c9c12387",250,364,true},
    {"Kamaz","a7a0061036bddce3c7eb748fe30aea0bdb9dfd544a6ab8ac02720649dc3c5034",318,264,true},
}};
constexpr bool reflection_layout(uint32_t triangles,uint32_t vertices,bool expanded=true) noexcept {
    if(expanded)for(const auto& source:kFleetOffLampProfiles)if(source.triangles==triangles&&source.vertices==vertices)return true;
    if(expanded&&((triangles==6&&vertices==10)||(triangles==12&&vertices==20)))return true;
    for(size_t i=0;i<(expanded?kReflectionMaterials.size():1);++i)
        if(triangles==kReflectionMaterials[i].triangles&&vertices==kReflectionMaterials[i].vertices)return true;
    return false;
}
inline constexpr char kPS2EnvSourceSha[] =
    "aa15159a5f3f668244dd3b1c5c7b8322d8f41ac626c3a1741222b797252ad1e4";
inline constexpr std::array<D3DRENDERSTATETYPE, 4> kReflectionRenderStates = {
    D3DRS_ALPHATESTENABLE, D3DRS_ALPHABLENDENABLE, D3DRS_ZWRITEENABLE, D3DRS_LIGHTING};
inline constexpr std::array<D3DTEXTURESTAGESTATETYPE, 8> kReflectionStageStates = {
    D3DTSS_COLOROP, D3DTSS_COLORARG1, D3DTSS_COLORARG2, D3DTSS_ALPHAOP,
    D3DTSS_ALPHAARG1, D3DTSS_ALPHAARG2, D3DTSS_TEXCOORDINDEX, D3DTSS_TEXTURETRANSFORMFLAGS};

struct ReflectionSnapshot {
    uint32_t requested_mode = 4; // Explicitly set by native snapshot; synthetic fixtures use Mode4.
    const DrawSnapshot* geometry = nullptr; // Immutable; valid through this synchronous classification.
    bool live_race_verified = false, vehicle_body_verified = false;
    // Independent source-material authority. Requires exact current geometry
    // digest in the explicit registry; does not assert a private physics owner.
    bool source_material_context_verified = false;
    bool stock_coordinate_policy = false, native_states_complete = false;
    bool native_matches_effective = false, texture_matrix_known = false;
    uint64_t race_generation = 0, owner_lifetime = 0;
    uintptr_t textures[2]{};
    uint64_t texture_generations[2]{};
    bool textures_are_2d = false;
    std::array<DWORD, 4> render_states{};
    std::array<std::array<DWORD, 8>, 2> stages{};
};

struct ReflectionIdentity {
    bool accepted = false;
    bool source_material_authority = false;
    const char* reason = "not_classified";
    const char* vehicle = "UNKNOWN";
    std::string geometry_sha256;
    std::string current_geometry_sha256, uv_topology_sha256;
};
constexpr bool affected_source_material_vehicle(std::string_view vehicle) noexcept {
    for(auto name:{"LandCruiser","Tata","ChevyBlazer","Xtrail","Navara","Forester","Jump",
                   "Patrol","Bruno","SeatBuggy","Kamaz","IceCream","Ufo","Terrano"})
        if(vehicle==name)return true;
    return false;
}
// This proves submission context only. Exact current source digest and material
// registry ownership are enforced separately by reflection_identity_for_hash.
inline bool source_material_context(const DrawClassification& draw,bool world_matches) noexcept {
    return world_matches && std::strcmp(reflection_material_exclusion(draw),"eligible") == 0;
}
std::string reflection_geometry_sha(const DrawSnapshot& geometry);
const FleetOffLampProfile* fleet_off_lamp_identity_for_hash(const DrawSnapshot&,std::string_view)noexcept;
ReflectionIdentity reflection_identity_for_hash(const ReflectionSnapshot&, std::string_view, uint64_t reset_generation, bool expanded=false);
ReflectionIdentity classify_reflection(const ReflectionSnapshot&, uint64_t reset_generation) noexcept;

struct ReflectionRequest {
    bool requested = false;
    IDirect3DTexture8* texture = nullptr; // Extension-owned; baseline retains original binding separately.
    DWORD color_op = D3DTOP_ADD;
    uint32_t override_mask = 0; // bit0 COLOROP, bit1 texture stage1; 0 never activates.
};

// Native-only state is owned and applied by the staged baseline integration.
// Retain a failed restoration for repair before any subsequent draw/state block.
struct ReflectionTransaction {
    DWORD original_color_op = 0;
    IDirect3DBaseTexture8* original_texture = nullptr;
    uint32_t changed_mask = 0; // bit0 COLOROP, bit1 texture stage1
    HRESULT last_failure = S_OK;
    ReflectionTransaction() = default;
    ReflectionTransaction(const ReflectionTransaction&) = delete;
    ~ReflectionTransaction() { release(); }
    void release() noexcept {
        if (original_texture) original_texture->Release();
        original_texture = nullptr;
        changed_mask = 0;
    }
};

template<class ColorWriter, class TextureWriter>
HRESULT restore_reflection_transaction(ReflectionTransaction& t, ColorWriter&& color, TextureWriter&& texture) noexcept {
    if (t.changed_mask & ~3u) return E_INVALIDARG;
    HRESULT result = S_OK;
    if (t.changed_mask & 2u) {
        const HRESULT hr = texture(t.original_texture);
        if (SUCCEEDED(hr)) t.changed_mask &= ~2u;
        else result = hr;
    }
    if (t.changed_mask & 1u) {
        const HRESULT hr = color(t.original_color_op);
        if (SUCCEEDED(hr)) t.changed_mask &= ~1u;
        else if (SUCCEEDED(result)) result = hr;
    }
    if (!t.changed_mask) t.release();
    t.last_failure = result;
    return result;
}

template<class ColorReader, class TextureReader, class ColorWriter, class TextureWriter>
HRESULT apply_reflection_transaction(const ReflectionRequest& request, ReflectionTransaction& t,
    ColorReader&& read_color, TextureReader&& read_texture, ColorWriter&& color,
    TextureWriter&& texture, bool& applied) noexcept {
    applied = false;
    const uint32_t mask = request.override_mask;
    if (!request.requested || !mask || (mask & ~3u) || t.changed_mask ||
        ((mask & 1u) && request.color_op != D3DTOP_ADD) || ((mask & 2u) && !request.texture))
        return E_INVALIDARG;
    t.release();
    HRESULT hr = S_OK;
    if (mask & 1u) {
        hr = read_color(t.original_color_op);
        if (FAILED(hr)) return hr;
    }
    if (mask & 2u) {
        hr = read_texture(t.original_texture); // Reader transfers one GetTexture reference.
        if (FAILED(hr) || !t.original_texture) { t.release(); return FAILED(hr) ? hr : E_POINTER; }
    }
    if (mask & 1u) {
        t.changed_mask |= 1u; // A failed native writer can still mutate: repair every attempted write.
        hr = color(request.color_op);
        if (FAILED(hr)) { restore_reflection_transaction(t, color, texture); return hr; }
    }
    if (mask & 2u) {
        t.changed_mask |= 2u;
        hr = texture(request.texture);
        if (FAILED(hr)) { restore_reflection_transaction(t, color, texture); return hr; }
    }
    applied = true;
    return S_OK;
}

bool canonical_env_identity(const uint8_t* bytes, size_t size, std::string_view digest) noexcept;
bool convert_static_env(const uint8_t* rgba, size_t size, std::vector<DWORD>& bgra) noexcept;

class StaticEnvTexture {
    IDirect3DTexture8* texture_ = nullptr;
public:
    ~StaticEnvTexture() { release(); }
    StaticEnvTexture() = default;
    StaticEnvTexture(const StaticEnvTexture&) = delete;
    HRESULT upload(IDirect3DDevice8&, const std::vector<DWORD>& bgra, bool require_add = true) noexcept;
    void release() noexcept { if (texture_) texture_->Release(); texture_ = nullptr; }
    IDirect3DTexture8* get() const noexcept { return texture_; }
};

class ReflectionPilot {
    struct CachedGeometry {
        std::array<uint64_t,15> key{};
        std::string digest, stable;
        bool valid=false;
    };
    std::array<CachedGeometry,256> geometry_cache_{};
    size_t next_cache_=0;
    uint64_t geometry_evaluations_=0;
    bool damage_logged_=false;
    ReflectionMode mode_ = ReflectionMode::Stock;
    bool verified_asset_ = false, disabled_ = false, blocked_ = false, suspended_ = false;
    std::array<uint8_t,kReflectionMaterials.size()+1> logged_{};
    bool diagnostics_ = false;
    bool expanded_ = false;
    const char* reason_ = "stock_default";
    std::vector<DWORD> pixels_;
    StaticEnvTexture texture_;
    ReflectionTransaction transaction_;
    MixedReflectionCapture capture_;
    HRESULT upload_hresult_ = E_PENDING;
public:
    ReflectionPilot(bool supported_build, const std::wstring& port_ini) noexcept;
    bool requested() const noexcept { return mode_ != ReflectionMode::Stock; }
    bool active() const noexcept { return requested() && verified_asset_ && !disabled_ && !blocked_ && !suspended_; }
    // Keep upload provenance and proxy ownership through a temporary Reset
    // suspension; an effect resuming later must not have exposed raw buffers.
    bool mirroring_required() const noexcept { return requested() && verified_asset_ && !disabled_; }
    bool blocked() const noexcept { return blocked_; }
    uint32_t mode_value() const noexcept { return static_cast<uint32_t>(mode_); }
    const char* reason() const noexcept { return reason_; }
    bool diagnostics() const noexcept { return diagnostics_; }
    bool expanded() const noexcept { return expanded_; }
    HRESULT upload_hresult() const noexcept { return upload_hresult_; }
    bool initialize(IDirect3DDevice8&) noexcept;
    ReflectionIdentity classify(const ReflectionSnapshot&, uint64_t reset_generation) noexcept;
    uint64_t geometry_evaluations() const noexcept { return geometry_evaluations_; }
    ReflectionRequest request(const ReflectionIdentity&, IDirect3DTexture8* mixed_texture = nullptr) const noexcept;
    IDirect3DTexture8* static_texture() const noexcept { return texture_.get(); }
    bool needs_mixed_source() const noexcept { return mode_ == ReflectionMode::TataBodyPS2MixedContribution; }
    ReflectionTransaction& transaction() noexcept { return transaction_; }
    MixedReflectionCapture& mixed_capture() noexcept { return capture_; }
    bool claim_damage_diagnostic()noexcept{if(!diagnostics_||damage_logged_)return false;damage_logged_=true;return true;}
    bool claim_diagnostic(bool applied, const char* vehicle="Tata") noexcept;
    void disable(const char* reason) noexcept { disabled_ = true; reason_ = reason; }
    void before_reset() noexcept;
    void after_reset(IDirect3DDevice8&, bool native_reset_called, bool successful) noexcept;
    void shutdown() noexcept { capture_.release(); transaction_.release(); texture_.release(); disabled_=true; }
};
} // namespace gfx2::ps2port
