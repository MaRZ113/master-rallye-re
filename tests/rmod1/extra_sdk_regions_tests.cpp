#define RMOD_EXTRA_SDK_BINDING 1
#include "../../src/native/rmod1/rmod2_inprocess.cpp"
#include <iostream>

int main(){
    using namespace rmod2_boot;
    SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",nullptr);
    auto* memory=static_cast<unsigned char*>(VirtualAlloc(reinterpret_cast<void*>(sdk_binding_profile::extension_va),
        sdk_binding_profile::extension_size,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    if(memory!=reinterpret_cast<void*>(sdk_binding_profile::extension_va))return 1;
    std::memset(memory,0xAA,sdk_binding_profile::extension_size);
    SdkSnapshot snapshot;
    if(!sdk_profile_matches(&snapshot)||snapshot.code.size()!=16384)return 2;
    for(const auto& region:sdk_binding_profile::writable_ranges)std::memset(memory+region.offset,0x55,region.size);
    if(!sdk_snapshot_matches(snapshot))return 3;
    memory[8192]=0x00;
    if(sdk_snapshot_matches(snapshot))return 4;
    memory[8192]=0xAA;
    if(!sdk_snapshot_matches(snapshot))return 5;
    VirtualFree(memory,0,MEM_RELEASE);
    std::cout<<"SDK_REGIONS_PASS two mutable pages excluded; immutable middle region changes rejected\n";
    return 0;
}
