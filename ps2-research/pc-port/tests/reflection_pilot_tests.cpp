#include "reflection_pilot.hpp"
#include "ps2_port_extension.hpp"
#include "wrappers.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <vector>

using namespace gfx2::ps2port;
using namespace gfx2;
int failures=0;
#define CHECK(x) do { if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;} } while(0)
#include "mock_interfaces.hpp"
namespace {

class Texture final : public IDirect3DTexture8 {
public:
    ULONG refs=1, releases=0; int locks=0, unlocks=0;
    HRESULT lock_hr=S_OK, unlock_hr=S_OK; std::vector<DWORD> pixels=std::vector<DWORD>(4096);
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** out) override { if(!out)return E_POINTER;*out=this;AddRef();return S_OK; }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++refs; }
    ULONG STDMETHODCALLTYPE Release() override { ++releases;return --refs; }
    HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override { return E_NOTIMPL; }
    HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override { return E_NOTIMPL; }
    HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override { return E_NOTIMPL; }
    HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override { return E_NOTIMPL; }
    DWORD STDMETHODCALLTYPE SetPriority(DWORD) override { return 0; }
    DWORD STDMETHODCALLTYPE GetPriority() override { return 0; }
    void STDMETHODCALLTYPE PreLoad() override {}
    D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override { return D3DRTYPE_TEXTURE; }
    DWORD STDMETHODCALLTYPE SetLOD(DWORD) override { return 0; }
    DWORD STDMETHODCALLTYPE GetLOD() override { return 0; }
    DWORD STDMETHODCALLTYPE GetLevelCount() override { return 1; }
    HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC*) override { return E_NOTIMPL; }
    HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**) override { return E_NOTIMPL; }
    HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* p,const RECT*,DWORD) override {
        ++locks;if(FAILED(lock_hr))return lock_hr;p->Pitch=256;p->pBits=pixels.data();return S_OK;
    }
    HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override { ++unlocks;return unlock_hr; }
    HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override { return S_OK; }
};

struct Native : MockDeviceBase {
    Texture old, replacement;
    IDirect3DBaseTexture8* bound=&old;
    DWORD color=D3DTOP_MODULATEALPHA_ADDCOLOR;
    int writes=0, texture_writes=0, color_writes=0, color_reads=0, texture_reads=0;
    int fail_write=0, fail_write2=0, draws=0, creates=0, render_target_writes=0;
    HRESULT draw_hr=D3DERR_INVALIDCALL, create_hr=S_OK;
    HRESULT color_read_hr=S_OK, texture_read_hr=S_OK;
    bool mutate_on_failure=false;
    bool caps_add=true; DWORD color_at_draw=0;
    IDirect3DBaseTexture8* texture_at_draw=nullptr;
    HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* c) override {
        *c={};c->MaxSimultaneousTextures=2;c->MaxTextureWidth=c->MaxTextureHeight=64;
        c->TextureOpCaps=caps_add?D3DTEXOPCAPS_ADD:0;return S_OK;
    }
    HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT fmt,
                                           D3DPOOL pool,IDirect3DTexture8** out) override {
        CHECK(w==64&&h==64&&levels==1&&usage==0&&fmt==D3DFMT_A8R8G8B8&&pool==D3DPOOL_MANAGED);
        ++creates;if(FAILED(create_hr))return create_hr;
        replacement.refs=1;*out=&replacement;return S_OK;
    }
    HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD* out) override {
        CHECK(stage==1&&key==D3DTSS_COLOROP);++color_reads;
        if(FAILED(color_read_hr))return color_read_hr;*out=color;return S_OK;
    }
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD value) override {
        CHECK(stage==1&&key==D3DTSS_COLOROP);++color_writes;
        const bool fail=++writes==fail_write||writes==fail_write2;
        if(!fail||mutate_on_failure)color=value;return fail?D3DERR_INVALIDCALL:S_OK;
    }
    HRESULT STDMETHODCALLTYPE GetTexture(DWORD stage,IDirect3DBaseTexture8** out) override {
        CHECK(stage==1);++texture_reads;
        if(FAILED(texture_read_hr))return texture_read_hr;*out=bound;bound->AddRef();return S_OK;
    }
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD stage,IDirect3DBaseTexture8* value) override {
        CHECK(stage==1);++texture_writes;
        const bool fail=++writes==fail_write||writes==fail_write2;
        // The synthetic device mimics native binding ownership.
        if(!fail||mutate_on_failure) {
            if(value)value->AddRef();if(bound)bound->Release();bound=value;
        }
        return fail?D3DERR_INVALIDCALL:S_OK;
    }
    HRESULT STDMETHODCALLTYPE SetRenderTarget(IDirect3DSurface8*,IDirect3DSurface8*) override {
        ++render_target_writes;return S_OK;
    }
    HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE,UINT,UINT,UINT,UINT) override {
        ++draws;color_at_draw=color;texture_at_draw=bound;return draw_hr;
    }
};

ReflectionSnapshot valid(DrawSnapshot& g) {
    g.supported_build=true;g.device_id=1;g.primitive_type=D3DPT_TRIANGLELIST;
    g.primitive_count=55;g.vertex_count=48;g.fvf=0x152;g.stride=36;
    g.vertex_resource=11;g.index_resource=12;g.vertex_generation=1;g.index_generation=2;
    g.vertex_revision=1;g.index_revision=1;g.complete_mirror_coverage=true;
    ReflectionSnapshot s;s.geometry=&g;s.live_race_verified=s.vehicle_body_verified=true;
    s.stock_coordinate_policy=s.native_states_complete=s.native_matches_effective=s.texture_matrix_known=true;
    s.race_generation=1;s.owner_lifetime=1;s.textures_are_2d=true;
    s.textures[0]=13;s.textures[1]=14;s.texture_generations[0]=3;s.texture_generations[1]=4;
    s.render_states={FALSE,FALSE,TRUE,FALSE};
    s.stages[0]={4,2,0,4,2,0,0,0};
    s.stages[1]={18,1,2,4,1,2,D3DTSS_TCI_CAMERASPACENORMAL,D3DTTFF_COUNT2};
    return s;
}

void identity() {
    DrawSnapshot g;auto s=valid(g);
    {DrawSnapshot kia;auto k=valid(kia);kia.primitive_count=206;kia.vertex_count=234;
     CHECK(!reflection_identity_for_hash(k,kKiaBonnetGeometrySha,0).accepted);
     const auto admitted=reflection_identity_for_hash(k,kKiaBonnetGeometrySha,0,true);
     CHECK(admitted.accepted&&std::strcmp(admitted.vehicle,"KiaSportage")==0);
     CHECK(!reflection_identity_for_hash(k,kTataBonnetGeometrySha,0,true).accepted);
     kia.reset_generation=2;CHECK(!reflection_identity_for_hash(k,kKiaBonnetGeometrySha,0,true).accepted);
     kia.reset_generation=0;k.texture_generations[1]=0;
     CHECK(!reflection_identity_for_hash(k,kKiaBonnetGeometrySha,0,true).accepted);
     k.texture_generations[1]=4;k.stages[1][0]=D3DTOP_SELECTARG1;
     CHECK(!reflection_identity_for_hash(k,kKiaBonnetGeometrySha,0,true).accepted);}
    CHECK(reflection_identity_for_hash(s,kTataBonnetGeometrySha,0).accepted);
    CHECK(!reflection_identity_for_hash(s,"same texture, different geometry",0).accepted);
    CHECK(!classify_reflection(s,0).accepted); // No actual source geometry supplied by this synthetic fixture.
    for(int condition=0;condition<13;++condition) {
        DrawSnapshot bad;auto b=valid(bad);
        switch(condition) {
        case 0:bad.supported_build=false;break;
        case 1:bad.reset_generation=1;break;
        case 2:bad.vertex_revision=0;break;
        case 3:bad.index_generation=0;break;
        case 4:b.live_race_verified=false;break;
        case 5:b.vehicle_body_verified=false;break;
        case 6:b.stock_coordinate_policy=false;break;
        case 7:b.render_states[1]=TRUE;break;
        case 8:b.stages[1][6]=D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR;break;
        case 9:b.texture_generations[0]=0;break;
        case 10:bad.primitive_count=54;break;
        case 11:b.native_matches_effective=false;break;
        case 12:b.texture_matrix_known=false;break;
        }
        CHECK(!reflection_identity_for_hash(b,kTataBonnetGeometrySha,0).accepted);
    }
    ReflectionPilot cache(false,L"");
    cache.classify(s,0);const uint64_t first=cache.geometry_evaluations();
    cache.classify(s,0);CHECK(cache.geometry_evaluations()==first);
    ++g.vertex_revision;cache.classify(s,0);CHECK(cache.geometry_evaluations()==first+1);
    cache.before_reset();cache.classify(s,0);CHECK(cache.geometry_evaluations()==first+2);
}

void transaction() {
    for(uint32_t mask : {1u,2u,3u}) for(int failure : {0,1,2}) {
        if(mask!=3&&failure==2)continue;
        Native n;n.fail_write=failure;n.mutate_on_failure=true;
        ReflectionTransaction t;
        ReflectionRequest request{true,(mask&2u)?&n.replacement:nullptr,D3DTOP_ADD,mask};
        bool applied=false;
        auto color=[&](DWORD v){return n.SetTextureStageState(1,D3DTSS_COLOROP,v);};
        auto texture=[&](IDirect3DBaseTexture8* v){return n.SetTexture(1,v);};
        const HRESULT setup=apply_reflection_transaction(request,t,
            [&](DWORD& v){return n.GetTextureStageState(1,D3DTSS_COLOROP,&v);},
            [&](IDirect3DBaseTexture8*& v){return n.GetTexture(1,&v);},color,texture,applied);
        CHECK((failure==0)==SUCCEEDED(setup));CHECK(applied==(failure==0));
        CHECK(n.color_reads==((mask&1u)?1:0)&&n.texture_reads==((mask&2u)?1:0));
        CHECK((mask&1u)||n.color_writes==0);CHECK((mask&2u)||n.texture_writes==0);
        const HRESULT draw=n.DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,48,0,55);
        CHECK(draw==n.draw_hr&&n.draws==1);
        CHECK(n.color_at_draw==((applied&&(mask&1u))?D3DTOP_ADD:D3DTOP_MODULATEALPHA_ADDCOLOR));
        CHECK(n.texture_at_draw==((applied&&(mask&2u))?static_cast<IDirect3DBaseTexture8*>(&n.replacement):&n.old));
        CHECK(SUCCEEDED(restore_reflection_transaction(t,color,texture)));
        CHECK(t.changed_mask==0&&t.original_texture==nullptr);
        CHECK(n.bound==&n.old&&n.color==D3DTOP_MODULATEALPHA_ADDCOLOR&&n.old.refs==1);
        CHECK(n.render_target_writes==0);
        CHECK((mask&1u)||n.color_writes==0);CHECK((mask&2u)||n.texture_writes==0);
    }
    Native n;ReflectionTransaction t;bool applied=false;
    auto c=[&](DWORD v){return n.SetTextureStageState(1,D3DTSS_COLOROP,v);};
    auto x=[&](IDirect3DBaseTexture8* v){return n.SetTexture(1,v);};
    CHECK(SUCCEEDED(apply_reflection_transaction({true,&n.replacement,D3DTOP_ADD,3},t,
        [&](DWORD& v){v=n.color;return S_OK;},[&](IDirect3DBaseTexture8*& v){v=n.bound;v->AddRef();return S_OK;},c,x,applied)));
    n.fail_write=3;CHECK(FAILED(restore_reflection_transaction(t,c,x)));
    CHECK(t.changed_mask==2&&t.original_texture==&n.old); // Retain old GetTexture reference for repair.
    n.fail_write=0;CHECK(SUCCEEDED(restore_reflection_transaction(t,c,x)));
    CHECK(n.bound==&n.old&&n.old.refs==1);
    int reads=0;
    CHECK(FAILED(apply_reflection_transaction({},t,[&](DWORD&){++reads;return S_OK;},
        [&](IDirect3DBaseTexture8*&){++reads;return S_OK;},c,x,applied)));
    CHECK(reads==0&&!applied);
    CHECK(FAILED(apply_reflection_transaction({true,&n.replacement,999,3},t,
        [&](DWORD&){++reads;return S_OK;},[&](IDirect3DBaseTexture8*&){++reads;return S_OK;},c,x,applied)));
    CHECK(reads==0);

    // Invalid, inactive and empty requests never touch a native reader or writer.
    for(const ReflectionRequest bad : {
        ReflectionRequest{}, ReflectionRequest{true,&n.replacement,D3DTOP_ADD,0},
        ReflectionRequest{true,&n.replacement,D3DTOP_ADD,4},
        ReflectionRequest{false,&n.replacement,D3DTOP_ADD,3},
        ReflectionRequest{true,nullptr,D3DTOP_ADD,2}}) {
        const int old_writes=n.writes;
        CHECK(FAILED(apply_reflection_transaction(bad,t,[&](DWORD&){++reads;return S_OK;},
            [&](IDirect3DBaseTexture8*&){++reads;return S_OK;},c,x,applied)));
        CHECK(reads==0&&!applied&&n.writes==old_writes);
    }
    const int before_invalid_restore=n.writes;
    t.changed_mask=4;CHECK(FAILED(restore_reflection_transaction(t,c,x)));
    CHECK(n.writes==before_invalid_restore);t.changed_mask=0;

    // Unselected states cannot make setup fail; their readers are never called.
    for(uint32_t mask : {1u,2u}) {
        Native isolated;ReflectionTransaction selected;
        isolated.color_read_hr=(mask==2)?E_FAIL:S_OK;
        isolated.texture_read_hr=(mask==1)?E_FAIL:S_OK;
        auto cw=[&](DWORD v){return isolated.SetTextureStageState(1,D3DTSS_COLOROP,v);};
        auto tw=[&](IDirect3DBaseTexture8* v){return isolated.SetTexture(1,v);};
        CHECK(SUCCEEDED(apply_reflection_transaction({true,(mask&2)?&isolated.replacement:nullptr,D3DTOP_ADD,mask},selected,
            [&](DWORD& v){return isolated.GetTextureStageState(1,D3DTSS_COLOROP,&v);},
            [&](IDirect3DBaseTexture8*& v){return isolated.GetTexture(1,&v);},cw,tw,applied)));
        CHECK(applied&&SUCCEEDED(restore_reflection_transaction(selected,cw,tw)));
        CHECK(isolated.color_reads==((mask&1)?1:0)&&isolated.texture_reads==((mask&2)?1:0));
    }
    // A selected reader failure is detected before the first mutation.
    for(uint32_t mask : {1u,2u,3u}) {
        Native unavailable;ReflectionTransaction unread;
        unavailable.color_read_hr=(mask&1u)?E_FAIL:S_OK;
        unavailable.texture_read_hr=(mask&1u)?S_OK:E_FAIL;
        auto cw=[&](DWORD v){return unavailable.SetTextureStageState(1,D3DTSS_COLOROP,v);};
        auto tw=[&](IDirect3DBaseTexture8* v){return unavailable.SetTexture(1,v);};
        CHECK(apply_reflection_transaction({true,&unavailable.replacement,D3DTOP_ADD,mask},unread,
            [&](DWORD& v){return unavailable.GetTextureStageState(1,D3DTSS_COLOROP,&v);},
            [&](IDirect3DBaseTexture8*& v){return unavailable.GetTexture(1,&v);},cw,tw,applied)==E_FAIL);
        CHECK(!applied&&unread.changed_mask==0&&unavailable.writes==0&&unavailable.old.refs==1);
    }
    // Preserve the original failing setup HRESULT even if rollback also fails.
    Native partial;partial.fail_write=2;partial.fail_write2=3;partial.mutate_on_failure=true;
    ReflectionTransaction pending;
    auto pc=[&](DWORD v){return partial.SetTextureStageState(1,D3DTSS_COLOROP,v);};
    auto px=[&](IDirect3DBaseTexture8* v){return partial.SetTexture(1,v);};
    const auto setup=apply_reflection_transaction({true,&partial.replacement,D3DTOP_ADD,3},pending,
        [&](DWORD& v){return partial.GetTextureStageState(1,D3DTSS_COLOROP,&v);},
        [&](IDirect3DBaseTexture8*& v){return partial.GetTexture(1,&v);},pc,px,applied);
    CHECK(setup==D3DERR_INVALIDCALL&&!applied&&pending.changed_mask==2);
    CHECK(pending.original_texture==&partial.old&&partial.old.refs==2);
    partial.fail_write=partial.fail_write2=0;
    CHECK(SUCCEEDED(restore_reflection_transaction(pending,pc,px)));
    CHECK(partial.bound==&partial.old&&partial.color==D3DTOP_MODULATEALPHA_ADDCOLOR&&partial.old.refs==1);
}

void resource_and_reset() {
    Native n;std::vector<DWORD> pixels(4096,0xff112233);
    {
        StaticEnvTexture texture;
        CHECK(SUCCEEDED(texture.upload(n,pixels)));
        CHECK(texture.get()==&n.replacement&&n.replacement.pixels==pixels);
        CHECK(n.replacement.locks==1&&n.replacement.unlocks==1);
        texture.release();CHECK(n.replacement.refs==0);
        n.replacement.lock_hr=E_FAIL;
        CHECK(FAILED(texture.upload(n,pixels)));CHECK(texture.get()==nullptr&&n.replacement.refs==0);
        n.replacement.lock_hr=S_OK;n.replacement.unlock_hr=E_FAIL;
        CHECK(FAILED(texture.upload(n,pixels)));CHECK(texture.get()==nullptr&&n.replacement.refs==0);
        n.replacement.unlock_hr=S_OK;n.caps_add=false;
        const int before=n.creates;CHECK(FAILED(texture.upload(n,pixels)));CHECK(n.creates==before);
        CHECK(SUCCEEDED(texture.upload(n,pixels,false))); // Texture-only does not select the ADD operation.
        texture.release();CHECK(n.replacement.refs==0);
    }
    ReflectionPilot pilot(false,L"");
    CHECK(!pilot.active()&&!pilot.requested()&&!pilot.mirroring_required());CHECK(!pilot.initialize(n));
    pilot.before_reset();pilot.after_reset(n,true,false);
    CHECK(!pilot.blocked()&&!pilot.active()); // A disabled pilot preserves Stock after failed Reset.
    auto& t=pilot.transaction();t.original_texture=&n.old;n.old.AddRef();t.changed_mask=2;
    pilot.before_reset();CHECK(pilot.blocked()&&t.changed_mask==0&&n.old.refs==1);
    pilot.after_reset(n,false,true);CHECK(pilot.blocked()); // No native reset: do not clear a pending recovery.
    pilot.after_reset(n,true,false);CHECK(pilot.blocked());
    pilot.after_reset(n,true,true);CHECK(!pilot.blocked()&&!pilot.active());
    t.original_texture=&n.old;n.old.AddRef();t.changed_mask=2;
    pilot.shutdown();CHECK(n.old.refs==1&&t.changed_mask==0&&!pilot.active());
    CHECK(n.render_target_writes==0);
}

void config_and_conversion() {
    CHECK(reflection_mode(0,1,true)==ReflectionMode::Stock);
    CHECK(reflection_mode(1,1,true)==ReflectionMode::TataBonnetPS2StaticContribution);
    CHECK(reflection_mode(2,1,true)==ReflectionMode::TataBodyPS2TextureOnly);
    CHECK(reflection_mode(3,1,true)==ReflectionMode::TataBodyNativeTextureAddOnly);
    CHECK(reflection_mode(4,1,true)==ReflectionMode::TataBodyPS2MixedContribution);
    CHECK(reflection_mode(5,1,true)==ReflectionMode::Stock);
    CHECK(reflection_mode(1,2,true)==ReflectionMode::Stock);
    CHECK(reflection_mode(1,1,false)==ReflectionMode::Stock);
    CHECK(reflection_mode(L"1",L"1",true)==ReflectionMode::TataBonnetPS2StaticContribution);
    CHECK(reflection_mode(L"1garbage",L"1",true)==ReflectionMode::Stock);
    CHECK(reflection_mode(L"1",L"1garbage",true)==ReflectionMode::Stock);
    CHECK(reflection_mode(L"",L"1",true)==ReflectionMode::Stock);
    CHECK(reflection_mode(L"01",L"1",true)==ReflectionMode::Stock);
    const std::array<uint32_t,5> expected_masks={0,3,2,1,3};
    for(uint32_t mode=0;mode<=4;++mode) {
        const std::wstring text=std::to_wstring(mode);
        CHECK(static_cast<uint32_t>(reflection_mode(text,L"1",true))==mode);
        CHECK(reflection_override_mask(static_cast<ReflectionMode>(mode))==expected_masks[mode]);
    }
    CHECK(reflection_override_mask(static_cast<ReflectionMode>(5))==0);
    std::vector<uint8_t> rgba(64*64*4);
    rgba[0]=160;rgba[1]=80;rgba[2]=40;rgba[3]=0;
    std::vector<DWORD> bgra;CHECK(convert_static_env(rgba.data(),rgba.size(),bgra));
    CHECK(bgra[0]==0xff643219u); // Original alpha is intentionally ignored in this RGB static term.
    CHECK(!convert_static_env(rgba.data(),4,bgra));
    std::vector<uint8_t> gxi(16392);uint32_t magic=0x13039;uint16_t wh=64;
    std::memcpy(gxi.data(),&magic,4);std::memcpy(gxi.data()+4,&wh,2);std::memcpy(gxi.data()+6,&wh,2);
    CHECK(canonical_env_identity(gxi.data(),gxi.size(),kPS2EnvSourceSha)); // Header gate only; digest is supplied separately.
    CHECK(!canonical_env_identity(gxi.data(),gxi.size(),"wrong hash"));
    CHECK(!canonical_env_identity(gxi.data(),gxi.size()-1,kPS2EnvSourceSha));
    gxi[4]=32;CHECK(!canonical_env_identity(gxi.data(),gxi.size(),kPS2EnvSourceSha));
}
void diagnostic_color_policy() {
    // Synthetic documented D3D8 combiner oracle, not a PS2 pixel-parity model.
    // CURRENT is Arg1, ENV is Arg2: op18=current+current.alpha*env; op7=current+env.
    const auto evaluate=[](DWORD op,float current,float alpha,float environment) {
        return current+(op==D3DTOP_MODULATEALPHA_ADDCOLOR?alpha:1.0f)*environment;
    };
    CHECK(D3DTOP_MODULATEALPHA_ADDCOLOR==18&&D3DTOP_ADD==7);
    CHECK(evaluate(18,.2f,1.f,.4f)==evaluate(7,.2f,1.f,.4f));
    CHECK(std::fabs(evaluate(18,.2f,.25f,.4f)-.3f)<1.e-6f);
    CHECK(std::fabs(evaluate(7,.2f,.25f,.4f)-.6f)<1.e-6f);
    // COLOROP-only switches this operation; texture-only leaves it unchanged.
    for(uint32_t mask : {1u,2u}) {
        Native n;ReflectionTransaction t;bool applied=false;
        auto c=[&](DWORD v){return n.SetTextureStageState(1,D3DTSS_COLOROP,v);};
        auto x=[&](IDirect3DBaseTexture8* v){return n.SetTexture(1,v);};
        CHECK(SUCCEEDED(apply_reflection_transaction({true,(mask&2)?&n.replacement:nullptr,D3DTOP_ADD,mask},t,
            [&](DWORD& v){return n.GetTextureStageState(1,D3DTSS_COLOROP,&v);},
            [&](IDirect3DBaseTexture8*& v){return n.GetTexture(1,&v);},c,x,applied)));
        CHECK(n.DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,48,0,55)==n.draw_hr);
        const float sampled=evaluate(n.color_at_draw,.2f,.25f,.4f);
        CHECK(std::fabs(sampled-(mask==1?.6f:.3f))<1.e-6f);
        CHECK(SUCCEEDED(restore_reflection_transaction(t,c,x)));
    }
    // D3D8's byte diffuse multiplier is documented as an approximation to GS FIX48/128.
    CHECK(80.f/128.f==.625f);
    CHECK(std::fabs(96.f/255.f-48.f/128.f)>.001f);
    CHECK(std::fabs(96.f/255.f-48.f/128.f)<.002f);
}
void enabled_reset() {
    wchar_t directory[MAX_PATH]{}, ini[MAX_PATH]{}, asset[32768]{};
    CHECK(GetTempPathW(MAX_PATH,directory)>0);
    CHECK(GetTempFileNameW(directory,L"ps2",0,ini)!=0);
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionMode",L"1",ini));
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionSourceGXI",L"missing-reset-test.gxi",ini));
    Native missing_native;ReflectionPilot missing(true,ini);
    CHECK(missing.requested()&&!missing.active()&&!missing.mirroring_required());
    missing.before_reset();missing.after_reset(missing_native,true,false);
    CHECK(!missing.blocked()&&!missing.active());
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionMode",L"3",ini));
    {
        Native control_native;ReflectionPilot control(true,ini);
        CHECK(control.mode_value()==3&&control.active()&&control.mirroring_required());
        CHECK(control.initialize(control_native)&&control_native.creates==0&&control.static_texture()==nullptr);
        ReflectionIdentity target;target.accepted=true;
        const auto request=control.request(target);
        CHECK(request.requested&&request.override_mask==1&&request.texture==nullptr);
        target.accepted=false;CHECK(!control.request(target).requested);
        control.before_reset();control.after_reset(control_native,true,false);
        CHECK(!control.active()&&control.mirroring_required()&&!control.blocked());
        control.after_reset(control_native,false,true);CHECK(!control.active());
        control.after_reset(control_native,true,true);
        CHECK(control.active()&&control_native.creates==0);
        control.shutdown();CHECK(!control.active()&&!control.mirroring_required());
    }
    {
        Native unsupported;unsupported.caps_add=false;ReflectionPilot control(true,ini);
        CHECK(!control.initialize(unsupported)&&unsupported.creates==0&&!control.active()&&!control.mirroring_required());
    }
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionMode",L"1",ini));
    const DWORD length=GetEnvironmentVariableW(L"MRR_REFLECTION_TEST_GXI",asset,32768);
    if(length && length<32768) {
        CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionSourceGXI",asset,ini));
        Native native;ReflectionPilot enabled(true,ini);
        CHECK(enabled.requested()&&enabled.active()&&enabled.mirroring_required());
        CHECK(enabled.initialize(native));CHECK(native.creates==1);
        enabled.before_reset();CHECK(native.replacement.refs==0);
        enabled.after_reset(native,true,false);
        CHECK(!enabled.blocked()&&!enabled.active()&&enabled.mirroring_required());
        const int creates=native.creates;
        enabled.after_reset(native,false,true); // Reset echo cannot resume a failed native Reset.
        CHECK(!enabled.active()&&enabled.mirroring_required()&&native.creates==creates);
        enabled.after_reset(native,true,true);
        CHECK(enabled.active()&&enabled.mirroring_required()&&native.creates==creates+1);
        enabled.shutdown();CHECK(!enabled.active()&&!enabled.mirroring_required());
        CHECK(native.replacement.refs==0&&native.render_target_writes==0);
        for(uint32_t mode : {1u,2u,4u}) {
            CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionMode",std::to_wstring(mode).c_str(),ini));
            Native selected;ReflectionPilot selected_pilot(true,ini);
            CHECK(selected_pilot.active()&&selected_pilot.mirroring_required()&&selected_pilot.initialize(selected));
            ReflectionIdentity target;target.accepted=true;
            const auto request=selected_pilot.request(target);
            if(mode==4) {
                CHECK(!request.requested&&request.override_mask==0&&selected_pilot.needs_mixed_source());
                const auto mixed=selected_pilot.request(target,&selected.old);
                CHECK(mixed.requested&&mixed.override_mask==3&&mixed.texture==&selected.old);
            } else CHECK(request.requested&&request.override_mask==(mode==2?2u:3u)&&request.texture==&selected.replacement);
            target.accepted=false;
            CHECK(!selected_pilot.request(target,&selected.old).requested);
            selected_pilot.shutdown();CHECK(selected.replacement.refs==0);
        }
        std::cout<<"Verified local GXI enabled Reset/suspension/mirroring: PASS\n";
    } else {
        CHECK(length==0);
        std::cout<<"Verified local GXI enabled Reset integration: NOT_PERFORMED (set MRR_REFLECTION_TEST_GXI)\n";
    }
    CHECK(DeleteFileW(ini));
}
void stock_wrapper_draw() {
    MockRootBase parent_native;Root8 root(&parent_native);Native native;
    Device8 device(&native,&root);
    const auto result=device.draw_indexed_at(D3DPT_TRIANGLELIST,0,48,0,55,0);
    CHECK(result==native.draw_hr&&native.draws==1);
    CHECK(native.color==D3DTOP_MODULATEALPHA_ADDCOLOR&&native.bound==&native.old);
    CHECK(native.writes==0&&native.creates==0&&native.render_target_writes==0);
    if(device.ps2_port()&&device.ps2_port()->reflection()) {
        device.ps2_port()->reflection()->before_reset();
        device.ps2_port()->reflection()->after_reset(native,true,false);
        CHECK(device.draw_indexed_at(D3DPT_TRIANGLELIST,0,48,0,55,0)==native.draw_hr);
        CHECK(native.draws==2&&native.writes==0&&native.creates==0);
    }
}
}
int main() {
    identity();transaction();resource_and_reset();config_and_conversion();diagnostic_color_policy();enabled_reset();stock_wrapper_draw();
    if(failures)return 1;
    std::cout<<"PS2 reflection identity, stock, native transactions, texture lifetime and reset: PASS\n";
    return 0;
}
