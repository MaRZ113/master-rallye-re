#pragma once

// Source-derived point preview, not the PS2 camera-history placement lifecycle
// or a claim of live VU/GS parity. All coordinates remain game-source world XYZ.
#include "course_objects.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {
inline constexpr char kTurkey3GrassGxiSha[]="519908ac79ca57591a8a38d3629286e25ffc51539705342864a5056785427eb6";
inline constexpr char kTurkey3GrassPcDxSha[]="724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8";
inline constexpr char kTurkey3GrassArtifactSha[]="6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad";
inline constexpr char kTurkey3BushGxiSha[]="2e4178614fbcbb3dbc3eaf5931001d2a566e76d59ef6adf7e66cd372556d40e9";
inline constexpr char kTurkey3ShrubsArtifactSha[]="688947a32776ffab67c553b4adc95e4597c399f2d70ece37534fd682044752b4";
enum class GroundDetailKind { Grass, Shrubs };
struct GrassSourceContract {
    const char* course;
    const char* psm;
    const char* pc;
    const char* grass_artifact;
    const char* shrubs_artifact;
    const wchar_t* stem;
};
inline constexpr std::array<GrassSourceContract,36> kGrassSources={{
    {"RaceTest/Turkey3","dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc","724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8","6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad","688947a32776ffab67c553b4adc95e4597c399f2d70ece37534fd682044752b4",L"Turkey3"},
    {"RaceTest/France1","d0b9845218ddd1ff4f12b3b16e77eff43aa182ac73992b5cbea8d81be04f935d","a6bfcef97684f41154596f91fdfaa9522a8fdf6b65d181f4d1ac327b9caf07d5","354cb84c7238e8a1a4959c95fc7e265587f32a3f26dcb29b98aa818c1096f961","69e64191810c4f3ce5b9b06862e9afe8d4ea2a69940ee7d4449cb71430fc2802",L"France1"},
    {"RaceTest/France2","5fb751c283dc81501dc94e2234a006da8698a50e72de8f2ce4d44f74429469fe","fe9085d681994329c0fbdb3570f5153cc2240028a5644acd3fe12dcddb9e2d4e","99904d27286c4ce24a47904e3e642858d82d4c629dbbcb072e1ad8de5dd8c542","f1c6b294c5c17b97766e2cceb5e2beff44da771c56f1e3ed1ea6eb0f7cc7a137",L"France2"},
    {"RaceTest/FranceM","b0446f47c90a98684b020c39cdb650c2ae975286b4f99924d5e0c1c4999d17c9","50e76cf51d279531f9e5188145657aaa12bed30d8f88d27e7614eec0a97b56ce","16f3b727f8cd190abd77c43ef4dc1353099bdfa682ed76797f7ea5af04d37605","58a3c341f94a1c11b34f9ddd0c54c18d167e053b242b605788db81300978c629",L"FranceM"},
    {"RaceTest/FranceS1","c475ec2e26a1085714acae7d64ef30df0f0e0ec0d564c0e2df0a02c0a6404bac","19d1c7073f610fe050f281c07188f52b263a430332c5a3519013a1ee1568b2d4","57f6891c0367d900b95a5d24cefe5d21ba2d7b98b8ad0e31bdd9c738977b80bc","9c2e4d9a8ef700e3c32e73cee827d5dcdbff38b7a6c2c15bb1d2848edbc9f357",L"FranceS1"},
    {"RaceTest/FranceS2","2f857d96823bf324d6a9154664b8f1fefaa7ae0e4407ed109d09ef0fd51f7127","26664bd12844fd179ac0ef61379f65a301f2da7b0c234d671b670407ee396809","5c300c40b817bf864079e155f9dc689a12a2caf0219df06b787900fdd2412f0b","6aa19d3bced7dcca0110ec9f2d1bd4167dc8060a1ddaaa4f5e4bbc84f8c24798",L"FranceS2"},
    {"RaceTest/FranceW","b2b056ddb4e959d535de1e5ca201f5e5ae566eae32c80e3a75d8642c3b0f076c","8c5392b7583760828ae1a4d5780aa67f3612fd7a13dfaba9fe540a2300f46f88","04fac61da8dffc1898c0d152203306513d74436e4913dd43269f6536006b3e7f","e368df311564dd802d47951e7568f0c7a6ccfab7dd7e3f0020dde45aa513c4c7",L"FranceW"},
    {"RaceTest/FranceWFlip","a75100a6ae1daee435a008db7ec9e0acc0178c5a961761aecbfaabd95079012c","9ed7bfdf16eef35ce3e46aeb38ed87b980005dab11639c6dd116421997368779","c4da6585b6a55fb30ca8f11728bcfd0e0dff6e02f3c094af133098dcda6dd7d6","9175317f510f898d95ebc1560ff3e0ff1e250f256f84fe7c5bd031f623e5b727",L"FranceWFlip"},
    {"RaceTest/Italy1","ba743c0c9f43694dc38337b325ecffad6ee2b438193eb999294f1e3c4377d234","971b44ab0f1543e457245731789dad2439259b37d206b6ca588f0130d84911e2","8e87a7e10197e66f4b8a5ec91e490993d17fd94e95188c268909c777ac07dbc9","ab525d79fda43eef5de25ef3d1376e1c08b948bb188ae9922157cdd1abb42736",L"Italy1"},
    {"RaceTest/Italy2","15be471a3c19afef2e7cf3f694fd1c6c50d18c40ffca840357047c0a74e68396","0614f6c933f751d07be0fb7ea5b97d1099ebf6873120b93c506922efc38f8a31","f4867edd6c7b8ad84daca8764dc50955945266d407fa6ef4a317fc88ca40a6be","7b68529aa6145493bc568b9d10ce924f07fb215f93c5b53be9ffea4eeeaf4458",L"Italy2"},
    {"RaceTest/Italy3","1652475e683f1f1a0df9fa05d614c6187600128e11dd44122bca80325bb124a2","4c97fc6faf743adb2c356da8c04851cd25fe91e5951be536b673c589819d3daa","b4ff78abd309d8081869ba15e6597b25cb3f7bee4da18aae51f4ee9654ae5df2","548596823aae07919df0ad1b5c82f34d4f7e8313924e286cad534b4a536e7d74",L"Italy3"},
    {"RaceTest/ItalyM1","1f4f057988a6ba484a353e80c2070e413f54b84d460e4292cd34514fc42ae3c8","7e7c3bef5f1beb44b9840ce9688a496166a368e2884d09e1c262098a9d723d9f","b97661a94b05b565e7b42eec190660383e260bc5bfcd2e337275c53a34951a5c","7d0a804e29511bb6ab82c89e3a43fb1c5286d5d23ebfe237ef5de6541b39dd2c",L"ItalyM1"},
    {"RaceTest/ItalyM1Flip","5ae9dd2ec50c3c5e6d33cd8e610ad32a6ead0c5e686781756fb6fd76cd3cf0de","d1cd24612c31fa39a0de79313257cb4017605ac4b4cc3c484e661c2b65db8935","0dc6630efc00ddeec8163e4c74b6e777ba6a35bb346e79518746d9023b2f78ae","6f00d277e1ab8875de9e65e92a7a9e6c0d4912255f203b613d83e646e8ea0247",L"ItalyM1Flip"},
    {"RaceTest/ItalyM2","779cd74d7704e2383183eb185243baa498e4f607e01551ebc68c27b5512a0cfc","f2ce72188a183c3a5a267c5bfbc7eebb3a8992b357d09eca51b9047a60893291","4380655de546d6a48759b9c00131272533ae5745382eb92748db88035729859f","a3f9e824608df20605f7123f597159ecbf8bf40ede95da6f149fe47ad37a9549",L"ItalyM2"},
    {"RaceTest/ItalyS1","f74854a0789c1d3bb416cef8d70a02c65141a2d7afc5a150068c047b94bc30a0","5cd86704667cbdc95d4a3b1ff1444c885431fcdd0313cc0f15eca980e3965e8a","e764d52060bc87c797e43459d743ec3dc6a4cd1aff67f239a62c59e82863c1ae","e2d08cfc56f7f3ea8e91b5225ba1b4a228ec40062b361c697426694c0f88234d",L"ItalyS1"},
    {"RaceTest/ItalyS2","c52e5dfefd62774797e4daabd13b09af9bcf2067676e6d19a3bb2c6a96cc46b7","c3f3d6b7fc579d17852afae66dcb915562741657cfbf0d84a78cdf15c525b4cf","c2679d4418ce35aacc5a26461ceeee73913a5d544d4e4b92efd4e80816ee9c84","60626a7ceaa6545b55e8868e0e6f5d53e59dc1f9cdb275542df3b6f96b214d58",L"ItalyS2"},
    {"RaceTest/ItalyS3","8025b5f11377778d2c414c066d9c4d4d7289701529432f783cf5c33c53b79871","fccd6344d5c9c4bd1d3b25c2d1d4da6375e049e7d5a188e0c9f7c6cf194940df","f0bfbfe0681e0a3b8714cc0b46d4f226b0d9a273ff1b30d8f8d440c2f91f22d4","740c0714fc982968a2c7aafeb48731bb1820c227f81cdbc511944dcc2b23e617",L"ItalyS3"},
    {"RaceTest/ItalyS3Flip","816531cedfcffbe5e1d66fd164300304514d91ef79e611e0d2b6c16a9e447db1","f6c534feae3498b2943663573001a87f5096af060bd7cda4c9e2a3a14bf7644a","96993a8094f3bcbeae84375fbaeb0e958926033262b2117bd002ff41acfc48c2","9fdfcba7ec085a36b1d4ce1967571c198ee86c463adc348fe6c94e8af7360096",L"ItalyS3Flip"},
    {"RaceTest/ItalyS4","1d6d578bdf6f86784e8f9ee2b75d902359e3a83e5233ad25434fd6ceb1294fc6","bde1528ff5cdd7c4d831f6b31b4065170b98de06ab06db26f29ccfd38920aba9","0bbfa484fe8857adf87c7fe87f25f78c38d87787fa16f257327474072ac85cf4","8033a25c9e8827613ca53d3e243a4ce9a185ca2bc5968b71f2d75d67f1176aa5",L"ItalyS4"},
    {"RaceTest/ItalyW1","1e80a99d84d7a99cccb114c89070c583934a85c094e94459374935593f158f7a","fcad9da53b7d436d79e9d9322276e98aa5039376e091a487b85d30ac1b3ae7d2","58bdc2ac8f5898f6608f21a4366ccaea4cbecacb7f3a3c0e053f86e8b126066a","cbb9b36c46029721489282188dabe3495b9f719bbe4f131cf3784817994abab7",L"ItalyW1"},
    {"RaceTest/ItalyW2","6da44f1680e0f8eff1805aac71245a220094e083670e7cde34205b54b7a6c45b","c66e8f0cff376b0f535c0cdc4fcd0bf53ad46d157b5aab4ca2648cf9cb9998d7","5a2fb55f301ff17c1faff77bc6cab9f7fb027c4f6e5ff61db60bef5809d117f9","575cec36c7b307080194e2890181c72b9a3cde6fcf6bd4db94be8b003f315246",L"ItalyW2"},
    {"RaceTest/Spain1","ae465c2636b34957cbca8a62eb3906b5e39b8db3667097fc365700ee1533a0c7","847c4074e9d1af1d89d484e7332a69b5601920a0ab3b14c082d69060b24db4aa","572a0fd6e942b5bac7b974d9a39e23173ac48f055f9fcaad8bee0bb0f01438e2","2a8b8f7412e913f59eb06a2a34b7a419a39e9b7f5659b3ba5279371e68b28cea",L"Spain1"},
    {"RaceTest/Spain2","77f645f2ac0b9eed7a57088453d068f4474b8a4889507f1f5101eea4671afd63","a427351031cdb8936033176c7793982860cd5214f60e7bd2a99bf0d49d0d1f9c","054c4b5c0fc88b46d22507b155e1394267557956bf26e3d7de4157f8bf297e8f","71fce2f22b1dd662210a10c3f8978f7470e506f13d89c30052721a9e560e75e5",L"Spain2"},
    {"RaceTest/SpainM","52f139a72f509b6df67c81b43e2417551a58732b01b2f31f3c288956349085be","77b5124f2bdc777252c93412e06c0728f05483df6898feb7420e668feb591b1f","abb04847d10c744f321d12a235e5b1013dda2b2c14f39bc77f151b0f6c207852","cb61a11cc0e4d760a1a030d45d0c079ad2f4a8fc90aee45fe5d61c29e8de1210",L"SpainM"},
    {"RaceTest/SpainS1","51ee09ca3b9269b72aabb1c4b4f096070de4c175907f1bf40df550d5973371b4","8e547d6732b57e75a6eb2ab45a3cb471bd9683796ceef60b4c1870aef029095a","ff4090ff7b80fc05f86a644975ced3b7d4ad11b0ec8a0dba90073069e48c1b0d","45b375b689cc6e848a07e95e36b4b13e15afc7a9328fbaf461c0208cf46dbd5d",L"SpainS1"},
    {"RaceTest/SpainS1Flip","242a740edb948b1062b2be9b2716dbcd43dd326daff85212d7d5a168913aea2b","199cf8d8bc05ffd68ed04c58435cceb2dc2712dfc4ecda4ab564a7eb974c7136","fffc504fea37fcbe0995533732955c1d69b6daa78059d7d129f860bf5c8ef2d2","eaffdf6e506bc520ffac847606d305a3aa5f87a0878e692e06198abde622fc67",L"SpainS1Flip"},
    {"RaceTest/SpainS2","4821ebadd9f85deffed2451f5a92fd839191fdf0c85c9c512acb66209d1559a1","37a8be02cd18c1ad2a3f72043924103ed8279d4b2d3237f54a23f8143301986b","a141c2ed1eecaf85f446b57e388902cfabfa2ce8c91bfcb39ba12602b4428337","f8f450f208b737cb0977a3cb383dcf540789ff17752b762bb4777fa167bb930e",L"SpainS2"},
    {"RaceTest/SpainW","5e4f5bf41c8443d85ae74275b03c8e6a549611d6875014ff293057238ff15d6d","109644f89549d35dcdac92d63881815010266e2a2d1dc6e89d112e02cdb63424","018b17029800efe2e01c750a013d48dc64ccc9733dba3075d581f41f7efb0b26","8ccab834b28fa8090dda13866260b1dd2af222319597db95783126b71185169e",L"SpainW"},
    {"RaceTest/SpainWFlip","dfe5a3dc208c5d5c37f6fa7105e59592f0aa4ca26f80ff66f93a4c7c2ba53c9b","74132a218e36a09543fee55993a99575155461fb249a9dd4795d5d3764fe1729","47724697e39a1905c22669e1c97c0de31e0a59ee6791a410463aabc724dac3c0","5e4eab517a757fd136b487d50e3956c5a3075b304259920f2cec8403963abb53",L"SpainWFlip"},
    {"RaceTest/Turkey1","0f0cae4de41e4dec855acbeb15943462af3c9fff09e0444e10990d00c85bcd1e","653da3a7b2191ff3f3aaaff8dac4d38286e4c281d2cb4ae34f3e47258a81fecb","cf64762d8d386b937254520c9529f54a579dffe6067e1075548e435cda94e55f","b5df6f28e4b8d63418f3c09dafbec78a9e75e69dea9dc2781c0113a4e24fa6ab",L"Turkey1"},
    {"RaceTest/Turkey2","80a2b1d8d1e5df771e57e1fe5753c711b75523d4e89fd14335745645446f28df","0c238c152543a37f4b9c2a5f9e4573b70b868d263762679612031216d19e1194","a96b3e1a4a0bc5a86cbc52bbbdade945070f016c071f47101b81bf047970c08c","6261249501192bad19132aaaec4a9dd580eb607cf2fa914373812ee9bdef2f24",L"Turkey2"},
    {"RaceTest/TurkeyM","7bf0c7022db8c7d6d1cf21b00a614f47d2235d14f1cd9434858121e1fb5ee0d9","f304938bbf4f93b45333fa7fa0661d05217a51f43e26403bf981aa2721b0a2f9","c155a9166dbe7fa18ee5913ce63fbebc4d09b2d7ce3924f2199740bb19c77b6f","f50dace263bbd6cf24bc92c5de77e7e06ab2b475154dc0e2f5cbcd08ed69830b",L"TurkeyM"},
    {"RaceTest/TurkeyS1","e431d2c3e64cf9e803013b4faf1f116bd2bce9e4d9a55140b74c42f2b8ca2198","fbf4e3c2358b5ed41c55be9d0f781793388d67783d9ca44e152337ac621065c0","782f6f6007ca819b2cd6774d3bc1c02bb817f30f9553a7a613c3775e50faa5a6","c21b3bc265c3f61d6bdf3b9b6368ca39ae79ebe66f9c324b7234bf3ba4720814",L"TurkeyS1"},
    {"RaceTest/TurkeyS2","e61e1fda314e6113e4f6be2fb0770ec2ac95c699ba3a0cd9a9124bad80aae6ba","de286e3fde3378133c9f43117c3564480dd12cce5f369ed6dd17ee9b595cbde5","e37fe87e4fc8d2d2081fa14b0db57ceb1c711152641fcbefe817db2a0727f102","14f358613de80a39ec91ab75676fae6f645fae3f2396b2260ecc07e7c4a1b656",L"TurkeyS2"},
    {"RaceTest/TurkeyS2Flip","c913f6cfc37a30173c8fc43fcca6c40641ae4115fb692acd6a77ced41253db70","d4ac39f98215d38df18a976f27f9ddc4dc233c89d95e1940348ae3b5ff5f3ddd","7419cb7c810f815147565c3816d5be95ca1b3acf0ef13188d50ac0d0dfc060b4","81e230e142394eb544cf6e564373593985c261649767e86edc346b799d02bf1a",L"TurkeyS2Flip"},
    {"RaceTest/TurkeyW","6d0c774caf4598e58f848dcd1938e0512cb6ddb8c0185e18b47d6fa8bad5cb27","d180cb0e0ea801438a39e54a5d683472d3ded30ff09db0a6ffd987d06d5f2a00","c1d563f58431b59cb09cd0cf326541e28a21c15c743a22a343f51e93ded82ded","fc959aaa59fef1a5fd9c9e4ff4b0df7519211dda235010951547f7882d202807",L"TurkeyW"},
}};
inline constexpr size_t kGrassMaximumVisiblePoints=16384;
inline constexpr size_t kGrassMaximumAssetBytes=64u*1024u*1024u;
inline constexpr float kGrassBinWidth=8.f;
struct GrassPoint {float x,y,z;};
static_assert(sizeof(GrassPoint)==12);
struct GrassBin {int32_t x,z;uint32_t first,count;};
static_assert(sizeof(GrassBin)==16);
struct GrassAsset {
    std::vector<GrassPoint> points;
    std::vector<GrassBin> bins;
    std::vector<DWORD> texture_bgra;
};

// Layout-only reader exists for synthetic tests. Runtime MUST use the digest
// admission reader below with the independently pinned complete artifact SHA.
bool decode_grass_asset_layout(const uint8_t*,size_t,GrassAsset&,GroundDetailKind=GroundDetailKind::Grass,
                             const GrassSourceContract* source=nullptr) noexcept;
bool decode_grass_asset(const uint8_t*,size_t,std::string_view digest,GrassAsset&,GroundDetailKind=GroundDetailKind::Grass) noexcept;
bool decode_course_grass_asset(const uint8_t*,size_t,std::string_view,GrassAsset&,GroundDetailKind,const GrassSourceContract&) noexcept;
bool grass_ee_floor(float,int32_t&) noexcept;
bool grass_camera_center(const D3DMATRIX&,std::array<float,3>& world_camera,
                         std::array<float,2>& snapped_xz) noexcept;
bool grass_distance_alpha(const GrassPoint&,const std::array<float,2>&,
                          uint32_t& lut_index,float& alpha_128) noexcept;
bool grass_preview_vertices(const GrassAsset&,const D3DMATRIX&,float sprite_half_size,
                            std::vector<ObjectVertex>&,const char*& reason) noexcept;

class GrassPilot {
    GroundDetailKind kind_=GroundDetailKind::Grass;
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false;
    bool diagnostics_=false,logged_rejection_=false,logged_draw_=false,logged_build_=false;
    const char* reason_="stock_default";
    float sprite_half_size_=.33f;
    GrassAsset asset_;
    std::array<GrassAsset,kGrassSources.size()-1> extra_assets_;
    std::array<bool,kGrassSources.size()> course_ready_{};
    bool multi_course_=false;
    size_t selected_course_=0;
    IDirect3DTexture8* texture_=nullptr;
    uint64_t consumed_frame_=UINT64_MAX,consumed_race_=0,consumed_reset_=0;
public:
    bool multi_course() const noexcept { return multi_course_; }
    CourseWorldProof proof;
    CourseObjectTransaction transaction;
    GrassPilot(bool supported,const std::wstring& ini,GroundDetailKind=GroundDetailKind::Grass) noexcept;
    ~GrassPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&verified_&&!disabled_&&!suspended_&&!blocked_&&texture_;}
    bool identity_requested()const noexcept{return requested_&&verified_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    const char* reason()const noexcept{return reason_;}
    float sprite_half_size()const noexcept{return sprite_half_size_;}
    GroundDetailKind kind()const noexcept{return kind_;}
    const char* category()const noexcept{return kind_==GroundDetailKind::Shrubs?"shrubs":"grass";}
    const char* artifact_sha()const noexcept{return kind_==GroundDetailKind::Shrubs?kGrassSources[selected_course_].shrubs_artifact:kGrassSources[selected_course_].grass_artifact;}
    const char* course()const noexcept{return kGrassSources[selected_course_].course;}
    const GrassAsset& asset()const noexcept{return selected_course_?extra_assets_[selected_course_-1]:asset_;}
    bool select_course(std::string_view,IDirect3DDevice8&) noexcept;
    IDirect3DTexture8* texture()const noexcept{return texture_;}
    bool initialize(IDirect3DDevice8&)noexcept;
    bool build_vertices(const D3DMATRIX&,std::vector<ObjectVertex>&)noexcept;
    bool consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept;
    bool boundary_consumed(uint64_t frame,uint64_t race,uint64_t reset)const noexcept {
        return consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset;
    }
    bool claim_log(bool draw)noexcept;
    bool claim_build_log()noexcept {if(!diagnostics_||logged_build_)return false;logged_build_=true;return true;}
    void disable(const char* reason)noexcept{disabled_=true;reason_=reason;proof.clear();}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
