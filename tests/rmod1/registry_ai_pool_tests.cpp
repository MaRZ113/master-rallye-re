#define RMOD_EXTRA_OPTIONS 1
#include "../../src/native/rmod1/runtime_core.cpp"
#include <iostream>
using namespace rmod1;
int main(){
    std::vector<uint32_t> classes(513,1);
    mr_vehicle_registry::DescriptorV1 registry{{'M','R','V','C'},1,44,513,52,3,0x45a3c0,0x1000,0x1010,
        static_cast<uint32_t>(reinterpret_cast<uintptr_t>(classes.data())),0x1020};
    wchar_t address[32]{};swprintf_s(address,L"0x%x",unsigned(reinterpret_cast<uintptr_t>(&registry)));
    SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",address);
    std::vector<SdkVehicleV1> rows;
    for(int id=26;id<513;++id)rows.push_back({id,1,7});
    SdkRosterV1 provider{sizeof(provider),1,static_cast<uint32_t>(rows.size()),0x12000,rows.data()};
    if(!MRRegisterSdkRosterV1(&provider))return 1;
    --provider.count;if(MRRegisterSdkRosterV1(&provider))return 10;++provider.count;
    rows.back().class_id=2;if(MRRegisterSdkRosterV1(&provider))return 2;rows.back().class_id=1;
    g_active_mode=int(GameMode::QuickRace);g_generation_config.logging_enabled=false;g_generation_config.config_version=2;g_generation_config.mode_policies[0]=Policy::Full;
    for(auto mode:{AddonMode::StockOnly,AddonMode::RegisteredOnly}){
        g_generation_pool=runtime_pool(GameMode::QuickRace,0,mode);g_generation_config.addons=mode;
        std::vector<int> storage{7,8,33,34,127,128,254,255,256,512,9999};
        uint32_t native_vector[4]{0,unsigned(reinterpret_cast<uintptr_t>(storage.data())),
            unsigned(reinterpret_cast<uintptr_t>(storage.data()+storage.size())),unsigned(reinterpret_cast<uintptr_t>(storage.data()+storage.size()))};
        if(!MRFilterAiPoolV1(0,1,native_vector))return 3;
        const size_t size=(native_vector[2]-native_vector[1])/4;
        if(mode==AddonMode::StockOnly){if(size!=2)return 4;}
        else {if(size!=10||storage[size-1]!=512||std::find(storage.begin(),storage.begin()+size,33)==storage.begin()+size)return 5;}
        if(native_vector[0]!=0||native_vector[1]!=unsigned(reinterpret_cast<uintptr_t>(storage.data())))return 6;
    }
    g_generation_pool=runtime_pool(GameMode::Invitation,0,AddonMode::RegisteredOnly);
    if(std::any_of(g_generation_pool.begin(),g_generation_pool.end(),[](const Vehicle& v){return v.addon;}))return 7;
    if(MRFilterAiPoolV1(4,1,nullptr))return 8;
    g_generation_config.mode_policies[0]=Policy::Stock;
    std::vector<int> stock{7,33,34};uint32_t v[4]{0,unsigned(reinterpret_cast<uintptr_t>(stock.data())),unsigned(reinterpret_cast<uintptr_t>(stock.data()+3)),unsigned(reinterpret_cast<uintptr_t>(stock.data()+3))};
    if(!MRFilterAiPoolV1(0,1,v)||v[2]-v[1]!=12||stock[1]!=33)return 9;
    SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",nullptr);
    std::cout<<"REGISTRY_AI_POOL_PASS production callback, live class identity, Include0/1, independent IDs33/34 and boundaries127/128/254/255/256/512, Invitation eligibility\n";
    return 0;
}
