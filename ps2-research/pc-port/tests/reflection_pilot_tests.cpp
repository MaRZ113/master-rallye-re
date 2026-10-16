#include "reflection_pilot.hpp"
#include "damage_identity.hpp"
#include "brake_glow.hpp"
#include "fleet_lamp_identity.hpp"
#include "race_fleet_registry.hpp"
#include "fleet_lamp_fixture_families.hpp"
#include <limits>
#include <fstream>
#include <cstdlib>
#include "ps2_port_extension.hpp"
#include "wrappers.hpp"
#include "buffer_reset_policy.hpp"
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
    {
        DrawClassification c;c.fvf=0x152;
        c.reasons=VEHICLE_SEMANTICS_CAPABILITY|RACE_PROJECTION|SHARED_OWNER|KNOWN_GEOMETRY|
            RIGID_WORLD|NORMAL_FVF|ENV_STAGE|CL_OPAQUE;
        CHECK(c.transform.object==ObjectClass::Unknown);
        CHECK(std::strcmp(reflection_exclusion(c),"eligible")!=0);
        CHECK(source_material_context(c,true)); // Original UFO has no four-wheel proof.
        CHECK(!source_material_context(c,false));
        for(auto bit:{VEHICLE_SEMANTICS_CAPABILITY,RACE_PROJECTION,SHARED_OWNER,KNOWN_GEOMETRY,RIGID_WORLD,NORMAL_FVF,ENV_STAGE,CL_OPAQUE}){
            auto bad=c;bad.reasons&=~bit;CHECK(!source_material_context(bad,true));
        }
        auto wrong=c;wrong.fvf=0x142;CHECK(!source_material_context(wrong,true));
        wrong=c;wrong.alpha_blended=true;CHECK(!source_material_context(wrong,true));
        DrawSnapshot registered;auto independent=valid(registered);independent.vehicle_body_verified=false;
        independent.source_material_context_verified=true;
        CHECK(reflection_identity_for_hash(independent,kTataBonnetGeometrySha,0).accepted);
        CHECK(!reflection_identity_for_hash(independent,"unknown geometry same texture",0).accepted);
        independent.live_race_verified=false;CHECK(!reflection_identity_for_hash(independent,kTataBonnetGeometrySha,0).accepted);
        independent.live_race_verified=true;registered.vertex_revision=0;
        CHECK(!reflection_identity_for_hash(independent,kTataBonnetGeometrySha,0).accepted);
    }
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
    // Every verified source registry entry still requires current native ownership/state.
    for(const auto& m:kReflectionMaterials){
        DrawSnapshot full;auto state=valid(full);full.primitive_count=m.triangles;full.vertex_count=m.vertices;
        CHECK(reflection_layout(m.triangles,m.vertices,true));
        const auto accepted=reflection_identity_for_hash(state,m.geometry_sha,0,true);
        state.requested_mode=3;
        CHECK(reflection_identity_for_hash(state,m.geometry_sha,0,true).accepted==!m.mode4_only);
        state.requested_mode=4;
        CHECK(accepted.accepted&&!std::strcmp(accepted.vehicle,m.vehicle));
        state.vehicle_body_verified=false;state.source_material_context_verified=true;
        CHECK(reflection_identity_for_hash(state,m.geometry_sha,0,true).accepted==affected_source_material_vehicle(m.vehicle));
        state.source_material_context_verified=false;
        state.vehicle_body_verified=false;CHECK(!reflection_identity_for_hash(state,m.geometry_sha,0,true).accepted);
        state.vehicle_body_verified=true;full.vertex_revision=0;CHECK(!reflection_identity_for_hash(state,m.geometry_sha,0,true).accepted);
    }
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
    CHECK(WritePrivateProfileStringW(L"PS2Port",L"ReflectionDiagnostics",L"1",ini));
    {
        Native control_native;ReflectionPilot control(true,ini);
        CHECK(control.mode_value()==3&&control.active()&&control.mirroring_required());
        CHECK(control.initialize(control_native)&&control_native.creates==0&&control.static_texture()==nullptr);
        CHECK(control.claim_diagnostic(true,"Tata"));CHECK(!control.claim_diagnostic(true,"Tata"));
        ReflectionIdentity target;target.accepted=true;
        const auto request=control.request(target);
        CHECK(request.requested&&request.override_mask==1&&request.texture==nullptr);
        target.accepted=false;CHECK(!control.request(target).requested);
        control.before_reset();control.after_reset(control_native,true,false);
        CHECK(!control.active()&&control.mirroring_required()&&!control.blocked());
        control.after_reset(control_native,false,true);CHECK(!control.active());
        CHECK(!control.claim_diagnostic(true,"Tata")); // Echo cannot rearm or resume a failed Reset.
        control.after_reset(control_native,true,true);
        CHECK(control.active()&&control_native.creates==0);
        CHECK(control.claim_diagnostic(true,"Tata"));CHECK(!control.claim_diagnostic(true,"Tata"));
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
void managed_reset_retention() {
    BufferMirror m;m.pool=D3DPOOL_MANAGED;m.available=true;m.generation=8;m.revision=3;
    m.data={1,2,3,4};m.initialized={{0,4}};
    CHECK(retain_managed_mirror_on_reset(true,true,m,8,8));
    CHECK(m.data==std::vector<BYTE>({1,2,3,4})&&m.revision==3&&m.initialized.size()==1);
    CHECK(!retain_managed_mirror_on_reset(false,true,m,8,8)); // Stock unchanged.
    CHECK(!retain_managed_mirror_on_reset(true,false,m,8,8)); // Raw-escape is not Reset.
    CHECK(!retain_managed_mirror_on_reset(true,true,m,9,8));
    CHECK(!retain_managed_mirror_on_reset(true,true,m,8,9));
    CHECK(!retain_managed_mirror_on_reset(true,true,m,8,0));
    m.pool=D3DPOOL_DEFAULT;CHECK(!retain_managed_mirror_on_reset(true,true,m,8,8));
    m.pool=D3DPOOL_SYSTEMMEM;CHECK(retain_managed_mirror_on_reset(true,true,m,8,8));
    m.pool=D3DPOOL_MANAGED;m.poisoned=true;CHECK(!retain_managed_mirror_on_reset(true,true,m,8,8));
    m.poisoned=false;m.available=false;CHECK(!retain_managed_mirror_on_reset(true,true,m,8,8));
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
void damage_identity_tests(){
 DrawSnapshot g;auto s=valid(g);g.primitive_count=324;g.vertex_count=330;s.requested_mode=4;
 auto accepted=damage_compatible_identity(s,"deformed_unknown_positions",kTerranoBumperUvTopology,0,true);CHECK(accepted.accepted);CHECK(accepted.current_geometry_sha256=="deformed_unknown_positions");
 CHECK(!damage_compatible_identity(s,"unknown","wrong",0,true).accepted);s.vehicle_body_verified=false;s.source_material_context_verified=true;CHECK(!damage_compatible_identity(s,"unknown",kTerranoBumperUvTopology,0,true).accepted);s.vehicle_body_verified=true;g.index_generation=0;CHECK(!damage_compatible_identity(s,"unknown",kTerranoBumperUvTopology,0,true).accepted);g.index_generation=2;CHECK(!damage_compatible_identity(s,"unknown",kTerranoBumperUvTopology,1,true).accepted);
 g.primitive_count=1;g.vertex_count=3;g.index_format=D3DFMT_INDEX16;g.vertex_bytes.resize(108);g.index_bytes.resize(6);for(unsigned i=0;i<3;++i){float xyz[3]={float(i),0,0},uv[2]={float(i)*.1f,.5f};std::memcpy(g.vertex_bytes.data()+i*36,xyz,12);std::memcpy(g.vertex_bytes.data()+i*36+28,uv,8);uint16_t ix=static_cast<uint16_t>(i);std::memcpy(g.index_bytes.data()+i*2,&ix,2);}
 const auto corner=position_uv_corner_sha(g);CHECK(!corner.empty());const auto stable=damage_uv_topology_sha(g);CHECK(!stable.empty());float deformed=100.f;std::memcpy(g.vertex_bytes.data(),&deformed,4);CHECK(damage_uv_topology_sha(g)==stable);CHECK(position_uv_corner_sha(g)!=corner);g.vertex_bytes[28]^=1;CHECK(damage_uv_topology_sha(g)!=stable);g.vertex_bytes[28]^=1;uint16_t bad=3;std::memcpy(g.index_bytes.data(),&bad,2);CHECK(damage_uv_topology_sha(g).empty());
}
void original_lamp_fixtures(){
 const auto* path=std::getenv("MRR_NATIVE_LAMP_FIXTURES");if(!path)return;std::ifstream file(path,std::ios::binary);std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)),{});CHECK(sha256_bytes(data.data(),data.size())=="e4444fff10111aac15a34a1c8c50236ee8b95dc10a90069511959cb10dd3c07c");size_t at=8;auto word=[&](){uint32_t v=0;if(at+4>data.size()){CHECK(false);return v;}std::memcpy(&v,data.data()+at,4);at+=4;return v;};CHECK(data.size()>12&&std::memcmp(data.data(),"PS2LMP01",8)==0);const auto cases=word();CHECK(cases==22);unsigned glows=0,off=0,on=0;
 for(unsigned c=0;c<cases;++c){const auto kind=word(),vertices=word(),triangles=word(),stride=word();DrawSnapshot g;auto s=valid(g);s.requested_mode=4;g.vertex_count=vertices;g.primitive_count=triangles;g.fvf=stride==32?0x112:0x152;g.stride=stride;g.index_format=D3DFMT_INDEX32;const auto end=at+uint64_t(vertices)*stride+uint64_t(triangles)*12;CHECK(end<=data.size());if(end>data.size())return;g.vertex_bytes.assign(data.begin()+at,data.begin()+at+vertices*stride);at+=vertices*stride;g.index_bytes.assign(data.begin()+at,data.begin()+end);at=end;
 if(kind==2){const auto* p=fleet_glow_identity(g);CHECK(p);++glows;auto bad=g;bad.vertex_bytes[24]^=1;CHECK(!fleet_glow_identity(bad));bad=g;bad.vertex_bytes[0]^=1;CHECK(!fleet_glow_identity(bad));bad=g;bad.index_generation=0;CHECK(!fleet_glow_identity(bad));bad=g;bad.complete_mirror_coverage=false;CHECK(!fleet_glow_identity(bad));}
 else{const auto hash=reflection_geometry_sha(g);auto identity=reflection_identity_for_hash(s,hash,0,true);if(kind==0){++off;CHECK(identity.accepted&&identity.vehicle=="Xtrail");CHECK(position_uv_corner_sha(g)==kXtrailLampOffPositionUv);auto bad=g;bad.vertex_bytes[28]^=1;s.geometry=&bad;CHECK(!reflection_identity_for_hash(s,hash,0,true).accepted);s.geometry=&g;s.requested_mode=1;CHECK(!reflection_identity_for_hash(s,hash,0,true).accepted);s.requested_mode=4;CHECK(!reflection_identity_for_hash(s,hash,1,true).accepted);}else{++on;CHECK(!identity.accepted);}}
 }CHECK(at==data.size()&&glows==20&&off==1&&on==1);
}
void fleet_glow_fixtures(){
 const auto* path=std::getenv("MRR_FLEET_GLOW_FIXTURES");if(!path)return;std::ifstream file(path,std::ios::binary);std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)),{});CHECK(sha256_bytes(data.data(),data.size())=="c7bf3d6f7607c27858f02362d8ad8f2d8d431891348c24c961ff7d10fb06c347");size_t at=8;auto word=[&](){uint32_t v=0;if(at+4>data.size()){CHECK(false);return v;}std::memcpy(&v,data.data()+at,4);at+=4;return v;};CHECK(data.size()>12&&std::memcmp(data.data(),"PS2LMP01",8)==0);const auto cases=word();CHECK(cases==774);unsigned positives=0,negatives=0;
 for(unsigned c=0;c<cases;++c){const auto kind=word(),vertices=word(),triangles=word(),stride=word();DrawSnapshot g;auto settings=valid(g);g.vertex_count=vertices;g.primitive_count=triangles;g.fvf=stride==32?0x112:0x152;g.stride=stride;g.index_format=D3DFMT_INDEX32;const auto end=at+uint64_t(vertices)*stride+uint64_t(triangles)*12;CHECK(end<=data.size());if(end>data.size())return;g.vertex_bytes.assign(data.begin()+at,data.begin()+at+vertices*stride);at+=vertices*stride;g.index_bytes.assign(data.begin()+at,data.begin()+end);at=end;if(kind==2){const auto* identified=fleet_glow_identity(g);CHECK(identified);++positives;auto compact=g;compact.fvf=0x102;compact.stride=20;compact.vertex_bytes.assign(uint64_t(vertices)*20,0);for(unsigned i=0;i<vertices;++i){std::memcpy(compact.vertex_bytes.data()+i*20,g.vertex_bytes.data()+i*32,12);std::memcpy(compact.vertex_bytes.data()+i*20+12,g.vertex_bytes.data()+i*32+24,8);}const auto* compact_profile=fleet_glow_identity(compact);if(identified&&std::string_view(identified->family)!="Terrano")CHECK(compact_profile==identified);else CHECK(!compact_profile);auto compact_bad=compact;compact_bad.vertex_bytes[12]^=1;CHECK(!fleet_glow_identity(compact_bad));compact_bad=compact;compact_bad.vertex_generation=0;CHECK(!fleet_glow_identity(compact_bad));auto bad=g;bad.vertex_bytes[0]^=1;CHECK(!fleet_glow_identity(bad));bad=g;bad.vertex_bytes[stride-8]^=1;CHECK(!fleet_glow_identity(bad));bad=g;bad.index_generation=0;CHECK(!fleet_glow_identity(bad));}else{CHECK(kind==3&&!fleet_glow_identity(g));++negatives;}}
 CHECK(at==data.size()&&positives==25&&negatives==749);
}
void kia_lamp_fixtures(){const char* path=std::getenv("MRR_KIA_LAMP_FIXTURES");if(!path)return;std::ifstream f(path,std::ios::binary);std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),{});CHECK(sha256_bytes(data.data(),data.size())=="96dd25e7ed86bb88242d839c2b44d4145a49304b839eada641d6a938b4bf9720");size_t at=8;auto word=[&](){uint32_t v=0;CHECK(at+4<=data.size());if(at+4>data.size())return v;std::memcpy(&v,data.data()+at,4);at+=4;return v;};CHECK(data.size()>12&&!std::memcmp(data.data(),"PS2LMP01",8));CHECK(word()==3);for(unsigned i=0;i<3;++i){const auto kind=word(),vertices=word(),triangles=word(),stride=word();DrawSnapshot g;auto settings=valid(g);settings.requested_mode=4;g.vertex_count=vertices;g.primitive_count=triangles;g.fvf=stride==36?0x152:0x102;g.stride=stride;g.index_format=D3DFMT_INDEX32;const auto end=at+uint64_t(vertices)*stride+uint64_t(triangles)*12;CHECK(end<=data.size());if(end>data.size())return;g.vertex_bytes.assign(data.begin()+at,data.begin()+at+vertices*stride);at+=vertices*stride;g.index_bytes.assign(data.begin()+at,data.begin()+end);at=end;if(kind==1){CHECK(KiaLampContinuity::exact_on(g));auto altered=g;altered.vertex_bytes[12]^=1;CHECK(!KiaLampContinuity::exact_on(altered));}const auto hash=reflection_geometry_sha(g);auto identity=reflection_identity_for_hash(settings,hash,0,true);CHECK(identity.accepted==(kind==0));if(kind==0){CHECK(identity.vehicle=="KiaSportage");auto bad=g;bad.vertex_bytes[28]^=1;settings.geometry=&bad;CHECK(!reflection_identity_for_hash(settings,hash,0,true).accepted);settings.geometry=&g;settings.requested_mode=1;CHECK(!reflection_identity_for_hash(settings,hash,0,true).accepted);settings.requested_mode=4;CHECK(!reflection_identity_for_hash(settings,hash,1,true).accepted);}}CHECK(at==data.size());}
void fleet_off_fixtures(){
 const auto* path=std::getenv("MRR_FLEET_OFF_LAMP_FIXTURES");if(!path)return;std::ifstream file(path,std::ios::binary);std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)),{});CHECK(sha256_bytes(data.data(),data.size())=="bf03e11485f7b09d043b8819d3cc8c181ac1612aaee302b8c7350d5837b33875");size_t at=8;auto word=[&](){uint32_t v=0;if(at+4>data.size()){CHECK(false);return v;}std::memcpy(&v,data.data()+at,4);at+=4;return v;};CHECK(data.size()>12&&std::memcmp(data.data(),"PS2LMP01",8)==0);const auto cases=word();CHECK(cases==774);unsigned positives=0,negatives=0;
 for(unsigned c=0;c<cases;++c){const auto kind=word(),vertices=word(),triangles=word(),stride=word();DrawSnapshot g;auto settings=valid(g);g.vertex_count=vertices;g.primitive_count=triangles;g.fvf=stride==32?0x112:0x152;g.stride=stride;g.index_format=D3DFMT_INDEX32;const auto end=at+uint64_t(vertices)*stride+uint64_t(triangles)*12;CHECK(end<=data.size());if(end>data.size())return;g.vertex_bytes.assign(data.begin()+at,data.begin()+at+vertices*stride);at+=vertices*stride;g.index_bytes.assign(data.begin()+at,data.begin()+end);at=end;if(kind==0){const auto hash=reflection_geometry_sha(g);const auto* profile=fleet_off_lamp_identity_for_hash(g,hash);CHECK(profile);if(profile){auto settings=valid(g);settings.requested_mode=4;g.vertex_count=vertices;g.primitive_count=triangles;g.fvf=0x152;g.stride=36;g.index_format=D3DFMT_INDEX32;CHECK(owned_off_lamp_identity(settings,*profile,true,true,0).accepted);CHECK(!owned_off_lamp_identity(settings,*profile,false,true,0).accepted);CHECK(!owned_off_lamp_identity(settings,*profile,true,false,0).accepted);settings.native_matches_effective=false;CHECK(!owned_off_lamp_identity(settings,*profile,true,true,0).accepted);}++positives;auto bad=g;bad.vertex_bytes[28]^=1;CHECK(!fleet_off_lamp_identity_for_hash(bad,hash));bad=g;bad.index_generation=0;CHECK(!fleet_off_lamp_identity_for_hash(bad,hash));}else{CHECK(kind==3&&!fleet_off_lamp_identity_for_hash(g,reflection_geometry_sha(g)));++negatives;}}

 CHECK(at==data.size()&&positives==21&&negatives==753);
}

void kia_damage_glow_pair(){
 const char* healthy=std::getenv("MRR_KIA_GLOW_HEALTHY");const char* damaged=std::getenv("MRR_KIA_GLOW_DAMAGED");if(!healthy||!damaged)return;
 auto load=[](const char* path,const char* sha){std::ifstream f(path,std::ios::binary);std::vector<uint8_t>b((std::istreambuf_iterator<char>(f)),{});CHECK(sha256_bytes(b.data(),b.size())==sha);CHECK(b.size()==848);DrawSnapshot g;valid(g);if(b.size()!=848)return g;uint32_t h[4];std::memcpy(h,b.data(),16);g.fvf=h[0];g.stride=h[1];g.min_index=h[2];g.index_format=h[3];g.vertex_byte_offset=uint64_t(g.min_index)*g.stride;g.vertex_count=32;g.primitive_count=32;g.vertex_bytes.assign(b.begin()+16,b.begin()+656);g.index_bytes.assign(b.begin()+656,b.end());return g;};
 auto a=load(healthy,"1ad468d652ed1d7a2408a00cc7da5fb5ccd198f54218f1726decabeecb87480b"),b=load(damaged,"8bf1bca8413dc0f5116eb3dd500edf1eb00d63c0d28901ee98863a592dfc42d7");CHECK(fleet_glow_identity(a)&&std::string_view(fleet_glow_identity(a)->family)=="KiaSportage");CHECK(!fleet_glow_identity(b));CHECK(KiaLampContinuity::topology(a)=="4a075be51521d4e13fceefe349870b474996abfb90ea3a3b957b449b755c1c43"&&KiaLampContinuity::topology(a)==KiaLampContinuity::topology(b));KiaLampContext context{1,2,3,4,0x10000,0x20000,0x30000,0x40000,5,0x50000,true,false};KiaLampContinuity state;const char* reason=nullptr;CHECK(state.match(1,a,context,true,reason));context.private_tree=true;CHECK(state.match(1,b,context,false,reason));CHECK(std::string_view(reason)=="damaged_owned_clone_uv_index_match");
 KiaLampContinuity cold;CHECK(!cold.match(1,b,context,false,reason)&&std::string_view(reason)=="damaged_branch_without_healthy_reference");auto bad=context;bad.owner_verified=false;CHECK(!state.match(1,b,bad,false,reason));bad=context;bad.material_token++;CHECK(!state.match(1,b,bad,false,reason));bad=context;bad.material_vector+=4;CHECK(!state.match(1,b,bad,false,reason));bad=context;bad.texture_generation++;CHECK(!state.match(1,b,bad,false,reason));auto changed=b;changed.vertex_bytes[12]^=1;CHECK(!state.match(1,changed,context,false,reason));changed=b;changed.index_bytes[0]^=1;CHECK(!state.match(1,changed,context,false,reason));changed=b;changed.index_generation=0;CHECK(!state.match(1,changed,context,false,reason));changed=b;const float nan=std::numeric_limits<float>::quiet_NaN();std::memcpy(changed.vertex_bytes.data(),&nan,4);CHECK(!state.match(1,changed,context,false,reason));bad=context;bad.lifetime++;CHECK(!state.match(1,b,bad,false,reason));
}
void port3_lamp_corpus(){const auto* path=std::getenv("MRR_PORT3_LAMP_FIXTURES");if(!path)return;std::ifstream file(path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});CHECK(sha256_bytes(bytes.data(),bytes.size())=="a4dc10a543de1bdfea558f84570c739ee3cb7880a6a0647158eb4356cf223ff0");size_t at=8;auto word=[&](){uint32_t v=0;CHECK(at+4<=bytes.size());if(at+4<=bytes.size()){std::memcpy(&v,bytes.data()+at,4);at+=4;}return v;};CHECK(bytes.size()>12&&!std::memcmp(bytes.data(),"PS2LMP01",8));const auto cases=word();CHECK(cases==774&&cases==std::size(kFleetLampFixtureFamily));unsigned ons=0,glows=0;for(unsigned row=0;row<cases;++row){const auto kind=word(),nv=word(),nf=word(),stride=word();DrawSnapshot g;valid(g);g.vertex_count=nv;g.primitive_count=nf;g.fvf=0x102;g.stride=stride;g.index_format=D3DFMT_INDEX32;const auto end=at+uint64_t(nv)*stride+uint64_t(nf)*12;CHECK(end<=bytes.size());if(end>bytes.size())return;g.vertex_bytes.assign(bytes.begin()+at,bytes.begin()+at+nv*stride);at+=nv*stride;g.index_bytes.assign(bytes.begin()+at,bytes.begin()+end);at=end;const auto* family=kRaceFleetProfiles[kFleetLampFixtureFamily[row]].family;const FleetOnProfile* on=nullptr;const BrakeGlowProfile* glow=nullptr;for(const auto& p:kFleetOnProfiles)if(!std::strcmp(p.family,family))on=&p;for(const auto& p:kBrakeGlowProfiles)if(!std::strcmp(p.family,family))glow=&p;CHECK(on&&glow);const bool on_match=on&&exact_native_lamp(g,on->vertices,on->triangles,on->geometry,on->positionUv),glow_match=glow&&exact_native_lamp(g,glow->vertices,glow->triangles,glow->geometry,glow->positionUv);CHECK(on_match==(kind==1));CHECK(glow_match==(kind==2));ons+=on_match;glows+=glow_match;if(on_match||glow_match){const unsigned layer=on_match?0:1;const unsigned v=on_match?on->vertices:glow->vertices,t=on_match?on->triangles:glow->triangles;NativeLampContinuity state;KiaLampContext c{1,2,3,4,0x10000,0x20000,0x30000,0x40000,5,0x50000,true,false};const char* reason=nullptr;CHECK(state.match_source(layer,g,c,true,reason,v,t));auto damaged=g;for(unsigned i=0;i<g.vertex_count;++i){float x;std::memcpy(&x,damaged.vertex_bytes.data()+i*stride,4);x+=.125f;std::memcpy(damaged.vertex_bytes.data()+i*stride,&x,4);}c.private_tree=true;CHECK(state.match_source(layer,damaged,c,false,reason,v,t));auto bad=damaged;bad.vertex_bytes[stride-8]^=1;CHECK(!state.match_source(layer,bad,c,false,reason,v,t));c.material_token++;CHECK(!state.match_source(layer,damaged,c,false,reason,v,t));}}
 CHECK(at==bytes.size()&&ons==25&&glows==25);}
int main() {port3_lamp_corpus();kia_damage_glow_pair();fleet_off_fixtures();kia_lamp_fixtures();
    fleet_glow_fixtures();original_lamp_fixtures();
    damage_identity_tests();
    identity();transaction();resource_and_reset();config_and_conversion();diagnostic_color_policy();enabled_reset();managed_reset_retention();stock_wrapper_draw();
    if(failures)return 1;
    std::cout<<"PS2 reflection identity, stock, native transactions, texture lifetime and reset: PASS\n";
    return 0;
}
