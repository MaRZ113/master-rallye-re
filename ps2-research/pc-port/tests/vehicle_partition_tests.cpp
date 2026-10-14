#include "vehicle_partition.hpp"
#include "lamp_partition_registry.hpp"
#include "vehicle_partition_registry.hpp"
#include "foliage_probe.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <limits>
using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do {if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
int main() {
    CHECK(!vehicle_partition_opt_in(L"0",L"1",true));
    CHECK(!vehicle_partition_opt_in(L"",L"1",true));
    CHECK(!vehicle_partition_opt_in(L"2",L"1",true));
    CHECK(!vehicle_partition_opt_in(L"1",L"2",true));
    CHECK(!vehicle_partition_opt_in(L"1",L"1",false));
    CHECK(vehicle_partition_opt_in(L"1",L"1",true));
    VehiclePartitionPilot absent(true,L"this_config_does_not_exist.ini");
    CHECK(!absent.requested());
    PS2PortExtension default_extension(true,"bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",L"Z:\\nonexistent_renderer.ini");
    CHECK(!default_extension.frontend_geometry_diagnostics());
    CHECK(!default_extension.buffer_mirroring_required());
    for(unsigned n=0;n<128;++n)CHECK(default_extension.claim_frontend_probe_attempt());
    CHECK(!default_extension.claim_frontend_probe_attempt());
    CHECK(default_extension.claim_frontend_geometry(0));CHECK(!default_extension.claim_frontend_geometry(0));
    CHECK(!default_extension.claim_frontend_geometry(41));CHECK(default_extension.claim_frontend_geometry(0,2));CHECK(!default_extension.claim_frontend_geometry(0,3));
    for(const auto& m:kVehiclePartitionMaterials) {
        CHECK(vehicle_partition_layout(m.triangles,m.vertices));
        std::vector<std::string> hashes;
        for(size_t i=0;i<m.face_count;++i)for(uint32_t n=0;n<m.faces[i].multiplicity;++n)hashes.push_back(m.faces[i].hash);
        CHECK(partition_ordered_faces(hashes,m).accepted);
        std::reverse(hashes.begin(),hashes.end());
        CHECK(partition_ordered_faces(hashes,m).accepted);
        hashes[0]=std::string(64,'f');CHECK(!partition_ordered_faces(hashes,m).accepted);
    }
    CHECK(!vehicle_partition_layout(48,28)); // foliage is not a vehicle partition
    std::array<std::string,2> hashes={std::string(64,'a'),std::string(64,'b')};
    PartitionFace entries[]={{hashes[0].c_str(),2,true},{hashes[1].c_str(),1,false}};
    const auto sha=sha256_bytes((hashes[0]+hashes[0]+hashes[1]).data(),192);
    PartitionMaterial m={"SYNTHETIC",sha.c_str(),4,3,entries,2};
    auto plan=partition_ordered_faces({hashes[0],hashes[1],hashes[0]},m);
    CHECK(plan.accepted&&plan.runs.size()==3);
    CHECK(!partition_ordered_faces({hashes[0],hashes[1]},m).accepted);
    CHECK(!partition_ordered_faces({hashes[1],hashes[1],hashes[0]},m).accepted);
    unsigned calls=0,covered=0;
    const auto hr=submit_partition(plan,10,[&](const PartitionRun& r,uint32_t start) noexcept {
        CHECK(start==10+r.first*3);++calls;covered+=r.count;return S_FALSE;
    });
    CHECK(hr==S_FALSE&&calls==3&&covered==3);
    calls=0;
    CHECK(submit_partition(plan,10,[&](const PartitionRun&,uint32_t) noexcept {
        return ++calls==2?D3DERR_INVALIDCALL:S_OK;
    })==D3DERR_INVALIDCALL);
    CHECK(calls==2); // first failure; no original whole draw/replay after partial submission
    auto malformed=plan;malformed.runs.back().first=1;calls=0;
    CHECK(submit_partition(malformed,10,[&](const PartitionRun&,uint32_t) noexcept {++calls;return S_OK;})==E_INVALIDARG);
    CHECK(calls==0);
    CHECK(submit_partition(plan,UINT32_MAX,[&](const PartitionRun&,uint32_t) noexcept {++calls;return S_OK;})==E_INVALIDARG);
    CHECK(calls==0);
    // Real shared native transaction primitives around each synthetic subrange.
    DWORD native_color=D3DTOP_MODULATEALPHA_ADDCOLOR;
    std::vector<DWORD> colors;calls=0;
    CHECK(submit_partition(plan,0,[&](const PartitionRun& r,uint32_t) noexcept {
        ReflectionTransaction t;bool applied=false;
        ReflectionRequest request;request.requested=true;request.override_mask=1;
        if(r.shiny)CHECK(SUCCEEDED(apply_reflection_transaction(request,t,
            [&](DWORD& v){v=native_color;return S_OK;},
            [](IDirect3DBaseTexture8*&){return E_FAIL;},
            [&](DWORD v){native_color=v;return S_OK;},
            [](IDirect3DBaseTexture8*){return E_FAIL;},applied)));
        ++calls;colors.push_back(native_color);
        const HRESULT original=S_FALSE;
        CHECK(SUCCEEDED(restore_reflection_transaction(t,[&](DWORD v){native_color=v;return S_OK;},
            [](IDirect3DBaseTexture8*){return E_FAIL;})));
        CHECK(native_color==D3DTOP_MODULATEALPHA_ADDCOLOR);
        return original;
    })==S_FALSE);
    CHECK(calls==3&&colors==std::vector<DWORD>({D3DTOP_ADD,D3DTOP_MODULATEALPHA_ADDCOLOR,D3DTOP_ADD}));
    ReflectionTransaction failed;ReflectionRequest request;request.requested=true;request.override_mask=1;
    bool applied=false;unsigned writes=0;
    CHECK(FAILED(apply_reflection_transaction(request,failed,[&](DWORD& v){v=native_color;return S_OK;},
        [](IDirect3DBaseTexture8*&){return E_FAIL;},[&](DWORD v){native_color=v;return ++writes==1?E_FAIL:S_OK;},
        [](IDirect3DBaseTexture8*){return E_FAIL;},applied)));
    CHECK(!applied&&!failed.changed_mask&&native_color==D3DTOP_MODULATEALPHA_ADDCOLOR&&writes==2);
    DrawSnapshot g;g.supported_build=true;g.device_id=1;g.reset_generation=3;
    g.complete_mirror_coverage=true;g.vertex_resource=1;g.index_resource=2;
    g.vertex_generation=g.index_generation=g.vertex_revision=g.index_revision=1;
    g.primitive_type=D3DPT_TRIANGLELIST;g.fvf=0x152;g.stride=36;
    ReflectionSnapshot s;s.geometry=&g;s.requested_mode=4;
    s.live_race_verified=s.source_material_context_verified=s.stock_coordinate_policy=true;
    s.native_states_complete=s.native_matches_effective=s.texture_matrix_known=s.textures_are_2d=true;
    s.race_generation=s.owner_lifetime=1;s.textures[0]=1;s.textures[1]=2;
    s.texture_generations[0]=s.texture_generations[1]=1;
    s.render_states={FALSE,FALSE,TRUE,FALSE};
    s.stages[0]={D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,0};
    s.stages[1]={D3DTOP_MODULATEALPHA_ADDCOLOR,D3DTA_CURRENT,D3DTA_TEXTURE,D3DTOP_MODULATE,
        D3DTA_CURRENT,D3DTA_TEXTURE,D3DTSS_TCI_CAMERASPACENORMAL,D3DTTFF_COUNT2};
    CHECK(partition_context_valid(s,3));CHECK(!partition_context_valid(s,4));
    s.live_race_verified=false;CHECK(!partition_context_valid(s,3));s.live_race_verified=true;
    s.stages[1][0]=D3DTOP_ADD;CHECK(!partition_context_valid(s,3));s.stages[1][0]=D3DTOP_MODULATEALPHA_ADDCOLOR;
    g.index_generation=0;CHECK(!partition_context_valid(s,3));g.index_generation=1;
    s.source_material_context_verified=false;CHECK(!partition_context_valid(s,3));s.source_material_context_verified=true;
    CHECK(!absent.classify(s,3).accepted); // default does not evaluate/override
    g.primitive_count=1;g.vertex_count=3;g.min_index=4;g.base_vertex=2;g.vertex_byte_offset=6*36;
    g.index_format=D3DFMT_INDEX16;g.vertex_bytes.resize(108);g.index_bytes.resize(6);
    const float xyz[9]={0,0,0,1,0,0,0,1,0};
    for(unsigned n=0;n<3;++n){std::memcpy(g.vertex_bytes.data()+n*36,xyz+n*3,12);uint16_t i=uint16_t(4+n);std::memcpy(g.index_bytes.data()+n*2,&i,2);}
    CHECK(vehicle_face_hashes(g)==std::vector<std::string>({foliage_face_hash(xyz)}));
    uint16_t invalid=7;std::memcpy(g.index_bytes.data(),&invalid,2);CHECK(vehicle_face_hashes(g).empty());
    invalid=4;std::memcpy(g.index_bytes.data(),&invalid,2);
    const float nonfinite=std::numeric_limits<float>::infinity();std::memcpy(g.vertex_bytes.data(),&nonfinite,4);
    CHECK(vehicle_face_hashes(g).empty());
    {const auto& lamp=kLampPartitionMaterials[0];std::vector<std::string> hashes;unsigned native=0;for(unsigned i=0;i<lamp.face_count;++i){for(unsigned j=0;j<lamp.faces[i].multiplicity;++j)hashes.push_back(lamp.faces[i].hash);if(!lamp.faces[i].shiny)native+=lamp.faces[i].multiplicity;}CHECK(native==22&&lamp.triangles==58);auto plan=partition_ordered_faces(hashes,lamp);CHECK(plan.accepted);std::reverse(hashes.begin(),hashes.end());CHECK(partition_ordered_faces(hashes,lamp).accepted);hashes[0]=std::string(64,'f');CHECK(!partition_ordered_faces(hashes,lamp).accepted);CHECK(vehicle_partition_layout(58,70));CHECK(!vehicle_partition_layout(58,71));}
    std::cout<<"vehicle partition contracts: "<<(failures?"FAIL":"PASS")<<"\n";
    return failures?1:0;
}
