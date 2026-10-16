#include "grass_pilot.hpp"
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>
using namespace gfx2;using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
namespace {
D3DMATRIX identity(){D3DMATRIX m{};m._11=m._22=m._33=m._44=1;return m;}
bool close(float a,float b,float tolerance=.00001f){return std::abs(a-b)<=tolerance;}
void put_hash(std::vector<uint8_t>& data,size_t start,const char* text){
    for(size_t i=0;i<32;++i){auto digit=[](char c){return c>='a'?c-'a'+10:c-'0';};data[start+i]=uint8_t((digit(text[i*2])<<4)|digit(text[i*2+1]));}
}
std::vector<uint8_t> synthetic_pack(){
    std::vector<uint8_t> data(128+16+24+4096);std::memcpy(data.data(),"PS2GRS01",8);
    const uint32_t fields[6]={1,2,1,32,32,4096};std::memcpy(data.data()+8,fields,sizeof(fields));
    put_hash(data,32,kTurkey3PsmSha);put_hash(data,64,kTurkey3GrassGxiSha);put_hash(data,96,kTurkey3GrassPcDxSha);
    const GrassBin bin{0,0,0,2};const GrassPoint points[2]={{1,.33f,2},{1,.33f,2}};
    std::memcpy(data.data()+128,&bin,sizeof(bin));std::memcpy(data.data()+144,points,sizeof(points));
    data[168]=12;data[169]=34;data[170]=56;data[171]=78;return data;
}
void format(){
    auto bytes=synthetic_pack();GrassAsset asset;
    CHECK(decode_grass_asset_layout(bytes.data(),bytes.size(),asset));
    CHECK(asset.points.size()==2&&asset.bins.size()==1&&asset.texture_bgra.size()==1024);
    CHECK(asset.texture_bgra[0]==0x4e0c2238u); // Original RGBA channels, alpha retained.
    CHECK(!decode_grass_asset(bytes.data(),bytes.size(),"wrong",asset)&&asset.points.empty());
    CHECK(!decode_grass_asset(nullptr,bytes.size(),kTurkey3GrassArtifactSha,asset));
    CHECK(!decode_grass_asset_layout(bytes.data(),bytes.size()-1,asset));
    for(size_t offset:{size_t(0),size_t(8),size_t(32),size_t(64),size_t(96)}){auto bad=bytes;bad[offset]^=1;
        CHECK(!decode_grass_asset_layout(bad.data(),bad.size(),asset)&&asset.points.empty());}
    for(size_t field:{size_t(12),size_t(16),size_t(20),size_t(24),size_t(28)}){auto bad=bytes;std::memset(bad.data()+field,0,4);
        CHECK(!decode_grass_asset_layout(bad.data(),bad.size(),asset));}
    {auto bad=bytes;const int32_t wrong=1;std::memcpy(bad.data()+128,&wrong,4);CHECK(!decode_grass_asset_layout(bad.data(),bad.size(),asset));}
    {auto bad=bytes;const uint32_t wrong=1;std::memcpy(bad.data()+136,&wrong,4);CHECK(!decode_grass_asset_layout(bad.data(),bad.size(),asset));}
    {auto bad=bytes;const float wrong=std::numeric_limits<float>::quiet_NaN();std::memcpy(bad.data()+144,&wrong,4);CHECK(!decode_grass_asset_layout(bad.data(),bad.size(),asset));}
    {auto bad=bytes;const float wrong=1000001.f;std::memcpy(bad.data()+148,&wrong,4);CHECK(!decode_grass_asset_layout(bad.data(),bad.size(),asset));}
}
void floor_camera_fade(){
    int32_t i=99;CHECK(grass_ee_floor(1.99f,i)&&i==1);CHECK(grass_ee_floor(-1.01f,i)&&i==-2);
    CHECK(grass_ee_floor(-2.f,i)&&i==-2);CHECK(grass_ee_floor(-.5f,i)&&i==0);
    CHECK(grass_ee_floor(-.25f,i)&&i==0);CHECK(grass_ee_floor(-.75f,i)&&i==-1);
    CHECK(!grass_ee_floor(std::numeric_limits<float>::infinity(),i));CHECK(!grass_ee_floor(2147483648.f,i));
    auto view=identity();view._41=-5;view._42=-2;view._43=-9;
    std::array<float,3> camera{};std::array<float,2> center{};
    CHECK(grass_camera_center(view,camera,center));CHECK(camera[0]==5&&camera[1]==2&&camera[2]==9);
    CHECK(close(center[0],2.66f)&&close(center[1],7.98f));
    auto rotated=identity();rotated._11=rotated._33=0;rotated._13=-1;rotated._31=1;
    rotated._41=-4;rotated._42=-3;rotated._43=2;
    CHECK(grass_camera_center(rotated,camera,center));CHECK(camera[0]==2&&camera[1]==3&&camera[2]==4);
    auto invalid=identity();invalid._11=-1;CHECK(grass_camera_center(invalid,camera,center));
    invalid=identity();invalid._22=2;CHECK(!grass_camera_center(invalid,camera,center));
    invalid=identity();invalid._14=.1f;CHECK(!grass_camera_center(invalid,camera,center));
    invalid=identity();invalid._43=std::numeric_limits<float>::quiet_NaN();CHECK(!grass_camera_center(invalid,camera,center));
    uint32_t q=999;float alpha=0;
    CHECK(grass_distance_alpha({0,.33f,0},{0,0},q,alpha)&&q==0&&alpha==128);
    CHECK(grass_distance_alpha({0,.33f,2},{0,0},q,alpha)&&q==3);
    CHECK(close(alpha,float((1-std::sqrt(3.0/1024))*128)));
    CHECK(!grass_distance_alpha({33,.33f,0},{0,0},q,alpha));
    CHECK(!grass_distance_alpha({0,std::numeric_limits<float>::quiet_NaN(),0},{0,0},q,alpha));
}
void captured_gameplay_view(){
    // Original float32 VIEW words: frame-20476-d1-00005663, sequence5.
    const uint32_t words[16]={3164293257,1060182458,1060686488,0,0,1060688665,3207668192,0,
        1065350200,1012327269,1012938844,0,3282495603,3302871040,3302836326,1065353216};
    D3DMATRIX view{};std::memcpy(&view,words,64);
    std::array<float,3> camera{};std::array<float,2> center{};
    CHECK(grass_camera_center(view,camera,center));
    CHECK(close(camera[0],2499.11795f,.001f)&&close(camera[1],56.25215f,.001f)&&close(camera[2],381.25647f,.001f));
    // Synthetic point five units in front of that camera, using measured basis.
    GrassAsset asset;const GrassPoint point{camera[0]+5*view._13,camera[1]+5*view._23,camera[2]+5*view._33};
    asset.points={point};asset.bins={{static_cast<int32_t>(std::floor(point.x/8)),static_cast<int32_t>(std::floor(point.z/8)),0,1}};
    std::vector<ObjectVertex> vertices;const char* reason=nullptr;
    CHECK(grass_preview_vertices(asset,view,.33f,vertices,reason)&&vertices.size()==6);
    CHECK(close(vertices[0].z,5,.001f));
    auto shear=view;shear._11+=.2f;CHECK(!grass_camera_center(shear,camera,center));
}
void vertices(){
    GrassAsset asset;asset.points={{1,.33f,2},{1,.33f,2}};asset.bins={{0,0,0,2}};
    std::vector<ObjectVertex> vertices;const char* reason=nullptr;auto view=identity();
    CHECK(grass_preview_vertices(asset,view,.33f,vertices,reason));CHECK(vertices.size()==12);
    CHECK(close(vertices[0].x,.67f)&&close(vertices[0].y,0)&&vertices[0].z==2);
    CHECK(close(vertices[2].x,1.33f)&&close(vertices[2].y,.66f));
    CHECK(vertices[0].u==0&&vertices[0].v==1&&vertices[1].v==0&&vertices[2].u==1);
    CHECK(!std::memcmp(vertices.data(),vertices.data()+6,sizeof(ObjectVertex)*6)); // Source duplicates retained.
    CHECK((vertices[0].color&0x00ffffffu)==0x00ffffffu&&(vertices[0].color>>24)<255);
    const auto first=vertices;CHECK(grass_preview_vertices(asset,view,.33f,vertices,reason));
    CHECK(first.size()==vertices.size()&&!std::memcmp(first.data(),vertices.data(),first.size()*sizeof(ObjectVertex)));
    CHECK(!grass_preview_vertices(asset,view,0,vertices,reason)&&vertices.empty());
    CHECK(!grass_preview_vertices(asset,view,2.1f,vertices,reason));
    auto wrong=identity();wrong._11=2;CHECK(!grass_preview_vertices(asset,wrong,.33f,vertices,reason));
    asset.points={{31,.33f,2},{0,.33f,-1},{0,.33f,0}};asset.bins={{0,-1,1,1},{0,0,2,1},{3,0,0,1}};
    CHECK(grass_preview_vertices(asset,view,.33f,vertices,reason)&&vertices.empty());
    asset.points.assign(kGrassMaximumVisiblePoints+1,{1,.33f,2});asset.bins={{0,0,0,uint32_t(asset.points.size())}};
    CHECK(!grass_preview_vertices(asset,view,.33f,vertices,reason)&&vertices.empty());
    CHECK(!std::strcmp(reason,"grass_visible_point_limit_no_thinning"));
    asset.points.resize(1);asset.bins={{0,0,0,2}};CHECK(!grass_preview_vertices(asset,view,.33f,vertices,reason));
}
class Texture:public IDirect3DTexture8{
public:ULONG refs=1;DWORD pixels[1024]{};bool failed_lock=false,failed_unlock=false,bad_pitch=false;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** o)override{*o=this;AddRef();return S_OK;}
 ULONG STDMETHODCALLTYPE AddRef()override{return ++refs;}ULONG STDMETHODCALLTYPE Release()override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID)override{return E_NOTIMPL;}
 DWORD STDMETHODCALLTYPE SetPriority(DWORD)override{return 0;}DWORD STDMETHODCALLTYPE GetPriority()override{return 0;}
 void STDMETHODCALLTYPE PreLoad()override{}D3DRESOURCETYPE STDMETHODCALLTYPE GetType()override{return D3DRTYPE_TEXTURE;}
 DWORD STDMETHODCALLTYPE SetLOD(DWORD)override{return 0;}DWORD STDMETHODCALLTYPE GetLOD()override{return 0;}
 DWORD STDMETHODCALLTYPE GetLevelCount()override{return 1;}
 HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC*)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* p,const RECT*,DWORD)override{p->Pitch=bad_pitch?127:128;p->pBits=pixels;return failed_lock?E_FAIL:S_OK;}
 HRESULT STDMETHODCALLTYPE UnlockRect(UINT)override{return failed_unlock?E_FAIL:S_OK;}
 HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*)override{return S_OK;}
};
struct Native:MockDeviceBase{
 Texture image,bush;int creates=0;bool fail_creation=false,insufficient_caps=false;
 HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* caps)override{*caps={};caps->MaxTextureWidth=caps->MaxTextureHeight=insufficient_caps?16:32;caps->MaxPrimitiveCount=32768;return S_OK;}
 HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT f,D3DPOOL pool,IDirect3DTexture8** o)override{
    CHECK(w==32&&h==32&&levels==1&&!usage&&f==D3DFMT_A8R8G8B8&&pool==D3DPOOL_MANAGED);
    ++creates;if(fail_creation){*o=nullptr;return E_FAIL;}
    // Separate simultaneous category textures; existing single-pool reset
    // fixtures still reuse image after its previous reference is released.
    auto& selected=creates==1||!image.refs?image:bush;selected.refs=1;*o=&selected;return S_OK;}
};
void configuration_resource_reset(){
    Native n;GrassPilot unsupported(false,L"");CHECK(!unsupported.requested()&&!unsupported.initialize(n)&&!n.creates);
    wchar_t directory[MAX_PATH]{},ini[MAX_PATH]{},asset[32768]{};CHECK(GetTempPathW(MAX_PATH,directory));CHECK(GetTempFileNameW(directory,L"grs",0,ini));
    GrassPilot stock(true,ini);CHECK(!stock.requested()&&!stock.active()&&!stock.initialize(n)&&!n.creates);
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"1garbage",ini));GrassPilot bad(true,ini);CHECK(!bad.requested());
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"1",ini));
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassConfigVersion",L"2",ini));GrassPilot unknown(true,ini);CHECK(!unknown.requested());
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassConfigVersion",L"1",ini));
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassSpriteHalfSize",L"nan",ini));GrassPilot size_nan(true,ini);CHECK(!size_nan.requested());
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassSpriteHalfSize",L".33garbage",ini));GrassPilot size_trailing(true,ini);CHECK(!size_trailing.requested());
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassSpriteHalfSize",L".33",ini));
    GrassPilot missing(true,ini);CHECK(missing.requested()&&!missing.identity_requested()&&!missing.initialize(n)&&!n.creates);
    const auto length=GetEnvironmentVariableW(L"MRR_GRASS_TEST_ASSET",asset,32768);
    if(length&&length<32768){
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassAsset",asset,ini));
        GrassPilot enabled(true,ini);CHECK(enabled.requested()&&enabled.identity_requested()&&enabled.initialize(n)&&enabled.active());
        CHECK(enabled.asset().points.size()==64900&&enabled.asset().bins.size()==3456);
        CHECK(n.image.pixels[0]==enabled.asset().texture_bgra[0]);CHECK(enabled.consume_boundary(1,2,3)&&!enabled.consume_boundary(1,2,3)&&enabled.consume_boundary(2,2,3));
        CHECK(!enabled.claim_log(true));enabled.before_reset();CHECK(n.image.refs==0&&!enabled.active());
        enabled.after_reset(n,true,false);CHECK(!enabled.active());const int count=n.creates;
        enabled.after_reset(n,false,true);CHECK(!enabled.active()&&n.creates==count);
        enabled.after_reset(n,true,true);CHECK(enabled.active()&&n.creates==count+1);
        enabled.shutdown();CHECK(n.image.refs==0&&!enabled.active());
        {Native incapable;incapable.insufficient_caps=true;GrassPilot p(true,ini);CHECK(!p.initialize(incapable)&&!incapable.creates);}
        {Native failed;failed.fail_creation=true;GrassPilot p(true,ini);CHECK(!p.initialize(failed)&&failed.creates==1&&!p.active());}
        {Native failed;failed.image.failed_lock=true;GrassPilot p(true,ini);CHECK(!p.initialize(failed)&&failed.image.refs==0&&!p.active());}
        {Native failed;failed.image.failed_unlock=true;GrassPilot p(true,ini);CHECK(!p.initialize(failed)&&failed.image.refs==0&&!p.active());}
        {Native failed;failed.image.bad_pitch=true;GrassPilot p(true,ini);CHECK(!p.initialize(failed)&&failed.image.refs==0&&!p.active());}
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassDiagnostics",L"1",ini));GrassPilot logs(true,ini);
        CHECK(logs.claim_log(true)&&!logs.claim_log(true)&&logs.claim_log(false)&&!logs.claim_log(false));
        CHECK(logs.claim_build_log()&&!logs.claim_build_log()); // Menu rejection cannot suppress build failure evidence.
        std::cout<<"Canonical private grass asset/upload/reset: PASS\n";
    }else{CHECK(length==0);std::cout<<"Canonical private grass asset integration: NOT_PERFORMED (set MRR_GRASS_TEST_ASSET)\n";}
    CHECK(DeleteFileW(ini));
}
void shrub_category_and_independence(){
    auto data=synthetic_pack();GrassAsset decoded;
    CHECK(!decode_grass_asset_layout(data.data(),data.size(),decoded,GroundDetailKind::Shrubs));
    put_hash(data,64,kTurkey3BushGxiSha);
    CHECK(decode_grass_asset_layout(data.data(),data.size(),decoded,GroundDetailKind::Shrubs));
    CHECK(!decode_grass_asset_layout(data.data(),data.size(),decoded,GroundDetailKind::Grass));
    CHECK(!decode_grass_asset_layout(data.data(),data.size(),decoded,static_cast<GroundDetailKind>(99)));
    CHECK(!decode_grass_asset(data.data(),data.size(),kTurkey3GrassArtifactSha,decoded,GroundDetailKind::Shrubs));
    wchar_t directory[MAX_PATH]{},ini[MAX_PATH]{},grass_path[32768]{},shrub_path[32768]{};
    CHECK(GetTempPathW(MAX_PATH,directory));CHECK(GetTempFileNameW(directory,L"shb",0,ini));
    Native n;GrassPilot stock(true,ini,GroundDetailKind::Shrubs);
    CHECK(!stock.requested()&&!stock.initialize(n)&&!n.creates);
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"1",ini));
    GrassPilot isolated(true,ini,GroundDetailKind::Shrubs);CHECK(!isolated.requested());
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"0",ini));
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"ShrubsMode",L"1",ini));
    GrassPilot grass_stock(true,ini);CHECK(!grass_stock.requested());
    GrassPilot missing(true,ini,GroundDetailKind::Shrubs);CHECK(missing.requested()&&!missing.active());
    const auto gl=GetEnvironmentVariableW(L"MRR_GRASS_TEST_ASSET",grass_path,32768);
    const auto sl=GetEnvironmentVariableW(L"MRR_SHRUB_TEST_ASSET",shrub_path,32768);
    if(gl&&gl<32768&&sl&&sl<32768){
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"1",ini));
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassAsset",grass_path,ini));
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"ShrubsAsset",shrub_path,ini));
        Native both;GrassPilot grass(true,ini),shrubs(true,ini,GroundDetailKind::Shrubs);
        CHECK(grass.initialize(both)&&shrubs.initialize(both)&&both.creates==2);
        CHECK(grass.active()&&shrubs.active()&&grass.texture()!=shrubs.texture());
        CHECK(grass.asset().points.size()==64900&&shrubs.asset().points.size()==146498);
        CHECK(!grass.select_course("RaceTest/France1",both)); // Legacy mode1 stays Turkey3-only.
        CHECK(close(grass.sprite_half_size(),.33f)&&close(shrubs.sprite_half_size(),.4f));
        CHECK(grass.consume_boundary(41,2,3)&&!shrubs.boundary_consumed(41,2,3));
        CHECK(shrubs.consume_boundary(41,2,3)&&!shrubs.consume_boundary(41,2,3));
        shrubs.disable("synthetic_one_category_failure");CHECK(!shrubs.active()&&grass.active());
        grass.before_reset();grass.after_reset(both,false,true);CHECK(!grass.active());
        grass.after_reset(both,true,false);CHECK(!grass.active());grass.after_reset(both,true,true);CHECK(grass.active());
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"ShrubsAsset",grass_path,ini));
        GrassPilot swapped(true,ini,GroundDetailKind::Shrubs);CHECK(!swapped.identity_requested());
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"ShrubsAsset",shrub_path,ini));
        {Native reset;GrassPilot p(true,ini,GroundDetailKind::Shrubs);CHECK(p.initialize(reset));
         p.proof.frame=41;p.proof.world_draw=true;p.before_reset();CHECK(p.proof.frame==UINT64_MAX&&!p.proof.world_draw&&!p.active());
         p.after_reset(reset,false,true);CHECK(!p.active()&&reset.creates==1);
         p.after_reset(reset,true,false);CHECK(!p.active());p.after_reset(reset,true,true);CHECK(p.active()&&reset.creates==2);}
        std::cout<<"Both canonical category assets, isolation, hash rejection, reset: PASS\n";
        wchar_t directory[32768]{};
        if(GetEnvironmentVariableW(L"MRR_GRASS_MULTI_DIRECTORY",directory,32768)){
            CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"2",ini));
            CHECK(WritePrivateProfileStringW(L"PS2Port",L"ShrubsMode",L"2",ini));
            CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassAssetDirectory",directory,ini));
            Native multi;GrassPilot g(true,ini),s(true,ini,GroundDetailKind::Shrubs);
            CHECK(g.initialize(multi)&&s.initialize(multi));
            CHECK(g.select_course("RaceTest/France1",multi)&&s.select_course("RaceTest/France1",multi));
            CHECK(g.asset().points.size()==197680&&s.asset().points.size()==169932);
            const auto creates=multi.creates;
            CHECK(g.select_course("RaceTest/France1",multi)&&multi.creates==creates);
            CHECK(!g.select_course("RaceTest/Unknown",multi)&&!g.select_course("RaceTest/Italy_S1",multi));
            CHECK(g.select_course("RaceTest/ItalyS1",multi)&&s.select_course("RaceTest/ItalyS1",multi));
            CHECK(g.asset().points.size()==125524&&s.asset().points.size()==75253);
            g.proof.frame=1;g.before_reset();CHECK(!g.active()&&g.proof.frame==UINT64_MAX);
            g.after_reset(multi,false,true);CHECK(!g.active());
            g.after_reset(multi,true,true);CHECK(g.active()&&g.asset().points.size()==125524);
            CHECK(g.select_course("RaceTest/Turkey3",multi)&&g.asset().points.size()==64900);
            CHECK(s.select_course("RaceTest/Turkey3",multi)&&s.asset().points.size()==146498);
            for(const auto& contract:kGrassSources){
                CHECK(g.select_course(contract.course,multi)&&s.select_course(contract.course,multi));
                CHECK(g.asset().points.size()<=300000&&s.asset().points.size()<=300000);
                const auto count=multi.creates;CHECK(g.select_course(contract.course,multi)&&multi.creates==count);
                g.before_reset();g.after_reset(multi,false,true);CHECK(!g.active());
                g.after_reset(multi,true,true);CHECK(g.active());
            }
            std::cout<<"Canonical 36-course admission, switch/restart/reset, unchanged legacy counts: PASS\n";
        }else std::cout<<"Multi-course private asset integration: NOT_PERFORMED (MRR_GRASS_MULTI_DIRECTORY)\n";
    }else std::cout<<"Shrub private asset integration: NOT_PERFORMED (set MRR_SHRUB_TEST_ASSET and MRR_GRASS_TEST_ASSET)\n";
    CHECK(DeleteFileW(ini));
}
}
void v2_grass_value_one_is_all_courses(){wchar_t directory[MAX_PATH]{},ini[MAX_PATH]{};CHECK(GetTempPathW(MAX_PATH,directory));CHECK(GetTempFileNameW(directory,L"gv2",0,ini));CHECK(WritePrivateProfileStringW(L"PS2Port",L"Grass",L"1",ini));GrassPilot v2(true,ini);CHECK(v2.multi_course());CHECK(WritePrivateProfileStringW(L"PS2Port",L"Grass",nullptr,ini));CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"1",ini));GrassPilot legacy(true,ini);CHECK(!legacy.multi_course());CHECK(WritePrivateProfileStringW(L"PS2Port",L"GrassMode",L"2",ini));GrassPilot legacy_all(true,ini);CHECK(legacy_all.multi_course());DeleteFileW(ini);}
int main(){v2_grass_value_one_is_all_courses();format();floor_camera_fade();captured_gameplay_view();vertices();configuration_resource_reset();shrub_category_and_independence();
    if(failures)return 1;std::cout<<"Grass source format, float32 camera/fade, billboard preview, defaults, lifecycle: PASS\n";return 0;}
