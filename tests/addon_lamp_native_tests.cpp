// Actual SDK-generated native draw fixtures; no game process or GPU required.
#include "../ps2-research/pc-port/renderer/addon_lamp_identity.hpp"
#include "../ps2-research/pc-port/renderer/addon_lamp_registry.hpp"
#include "../ps2-research/pc-port/renderer/addon_lamp_owners.hpp"
#include "../ps2-research/pc-port/renderer/brake_glow.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <cassert>
#include <chrono>
using namespace gfx2::ps2port;
int main(int argc,char** argv){
 if(argc!=4)return 2;
 std::ifstream registry(argv[1]),fixture(argv[2],std::ios::binary);auto profiles=read_addon_lamps(registry);
 // Exercise the accepted Renderer constructor against real assets and a v3
 // config. No game, GPU, or mutation of the owner's config is involved.
 const auto host=std::filesystem::absolute(argv[3]);
 for(int mode=0;mode<=1;++mode){
  const auto dir=std::filesystem::path(argv[2]).parent_path()/("config-mode-"+std::to_string(mode));
  std::filesystem::create_directories(dir);const auto ini=dir/"PS2Port.ini";
  {std::ofstream f(ini);f<<"[General]\nConfigVersion=3\n[Vehicles]\nModelChoice=1\nBrakeGlow="<<mode
    <<"\nBrakeGlowAsset="<<(host/"PS2Grass/PS2BrakeGlow.gxi").string()
    <<"\nAddonBrakeRegistry="<<std::filesystem::absolute(argv[1]).string()<<"\n";}
  {BrakeGlow glow(true,ini.wstring());assert(glow.requested()==bool(mode));
   // The catalog is read without lamp art too: body-scoped sets still choose PS2/PC geometry.
   assert(glow.addon_lamps.size()==profiles.size());}
  {BrakeGlow unsupported(false,ini.wstring());assert(!unsupported.requested()&&unsupported.addon_lamps.empty());}
 }
 std::cout<<"Actual Renderer v3 config: BrakeGlow=0 no lamp art (catalog kept for body scope); 1 PS2 art; unsupported build disabled\n";
 auto number=[&](){uint32_t value=0;fixture.read(reinterpret_cast<char*>(&value),4);assert(fixture);return value;};
 assert(number()==profiles.size());std::vector<DrawSnapshot> draws;
 for(const auto& p:profiles){
  DrawSnapshot g;g.supported_build=true;g.device_id=1;g.reset_generation=1;g.vertex_resource=16+draws.size()*32;g.index_resource=32+draws.size()*32;g.vertex_generation=g.index_generation=g.vertex_revision=g.index_revision=1;g.complete_mirror_coverage=true;
  g.fvf=0x112;g.stride=32;g.vertex_count=p.vertices;g.primitive_count=p.triangles;g.primitive_type=D3DPT_TRIANGLELIST;g.index_format=D3DFMT_INDEX16;
  g.vertex_bytes.resize(number());fixture.read(reinterpret_cast<char*>(g.vertex_bytes.data()),g.vertex_bytes.size());g.index_bytes.resize(number());fixture.read(reinterpret_cast<char*>(g.index_bytes.data()),g.index_bytes.size());assert(fixture);
  assert(exact_native_lamp(g,p.vertices,p.triangles,p.geometry.c_str(),p.positionUv.c_str()));
  assert(cached_addon_lamp_identity(profiles,g)==draws.size());
  const unsigned kind=p.layer<2?p.layer:2u;LampOwnerContext owner{1,2,3,4,16,32,48,64,80,96,true,false};NativeLampContinuity continuity;const char* why=nullptr;
  assert(continuity.match_source(kind,g,owner,true,why,p.vertices,p.triangles));
  auto changed=g;float position=0;std::memcpy(&position,changed.vertex_bytes.data(),4);position+=.015f;std::memcpy(changed.vertex_bytes.data(),&position,4);
  assert(!exact_native_lamp(changed,p.vertices,p.triangles,p.geometry.c_str(),p.positionUv.c_str()));
  changed.vertex_revision++;assert(cached_addon_lamp_identity(profiles,changed)==UINT_MAX);
  auto unavailable=g;unavailable.complete_mirror_coverage=false;assert(cached_addon_lamp_identity(profiles,unavailable)==UINT_MAX);
  assert(!continuity.match_source(kind,changed,owner,false,why,p.vertices,p.triangles));
  owner.private_tree=true;assert(continuity.match_source(kind,changed,owner,false,why,p.vertices,p.triangles));
  auto wrong=owner;wrong.texture_generation++;
  assert(!continuity.match_source(kind,changed,wrong,false,why,p.vertices,p.triangles));
  changed.vertex_bytes[24]^=1;
  assert(!continuity.match_source(kind,changed,owner,false,why,p.vertices,p.triangles));
  wrong=owner;wrong.instance++;
  assert(!continuity.match_source(kind,g,wrong,false,why,p.vertices,p.triangles));
  AddonLampOwners participants;owner.private_tree=false;
  assert(participants.find(0,owner,1,true)->match_source(kind,g,owner,true,why,p.vertices,p.triangles));
  auto duplicate=owner;duplicate.instance++;duplicate.packet++;duplicate.model++;duplicate.lifetime++;
  assert(participants.find(0,duplicate,1,true)->match_source(kind,g,duplicate,true,why,p.vertices,p.triangles));
  owner.private_tree=true;
  assert(participants.find(0,owner,1,false)->match_source(kind,g,owner,false,why,p.vertices,p.triangles));
  assert(participants.find(0,owner,2,false)==nullptr); // reset invalidates witnesses
  auto other_race=owner;other_race.race++;assert(participants.find(0,other_race,2,false)==nullptr);
  draws.push_back(std::move(g));
 }
 constexpr unsigned repeats=100;unsigned matches=0;const auto start=std::chrono::steady_clock::now();
 for(unsigned n=0;n<repeats;++n)for(unsigned i=0;i<profiles.size();++i){const auto& p=profiles[i];matches+=exact_native_lamp(draws[i],p.vertices,p.triangles,p.geometry.c_str(),p.positionUv.c_str());}
 const auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-start).count();assert(matches==repeats*profiles.size());
 std::cout<<"Actual native layers="<<profiles.size()<<"; owner/damage/UV rejection checks passed\n";
 std::cout<<"Uncached exact-match mean microseconds="<<double(us)/matches<<"; offline CPU benchmark, not game frame time\n";
 matches=0;const auto warm=std::chrono::steady_clock::now();
 for(unsigned n=0;n<repeats*10;++n)for(unsigned i=0;i<profiles.size();++i)matches+=cached_addon_lamp_identity(profiles,draws[i])==i;
 const auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-warm).count();assert(matches==repeats*10*profiles.size());
 std::cout<<"Warm catalog-match mean microseconds="<<double(ns)/matches/1000.0<<"; owner/material proof remains per draw\n";
}
