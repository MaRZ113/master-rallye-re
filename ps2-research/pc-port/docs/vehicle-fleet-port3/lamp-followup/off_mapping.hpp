#pragma once
namespace gfx2::ps2port::off_followup {
struct Mapping { unsigned first,count; };
inline constexpr unsigned NEWRAV_candidates[]={7u,5u,6u,8u,15u,16u,14u,17u,0u,2u,1u,3u,4u,9u,10u,11u,12u,13u};
inline constexpr Mapping NEWRAV_mapping[]={{0u,1u},{1u,1u},{2u,1u},{3u,1u},{4u,1u},{5u,1u},{6u,1u},{7u,1u},{8u,1u},{9u,1u},{10u,1u},{11u,1u},{12u,1u},{13u,1u},{14u,1u},{15u,1u},{16u,1u},{17u,1u}};
inline constexpr unsigned BRUNO_candidates[]={0u,2u,1u,6u,4u,5u,3u,12u,13u,11u,17u,14u,16u,15u,9u,7u,8u,10u,20u,18u,19u,21u};
inline constexpr Mapping BRUNO_mapping[]={{0u,1u},{1u,1u},{2u,2u},{4u,1u},{5u,1u},{6u,1u},{7u,1u},{8u,1u},{9u,2u},{11u,1u},{12u,1u},{13u,1u},{14u,1u},{15u,1u},{16u,1u},{17u,1u},{18u,1u},{19u,1u},{20u,1u},{21u,1u}};
inline constexpr unsigned MATTSERATI_candidates[]={1u,2u,0u,3u,5u,6u,4u,7u,9u,10u,8u,11u,13u,14u,12u,15u,17u,18u,16u,19u,22u,20u,21u,23u,26u,24u,25u,27u,30u,28u,29u,31u,34u,32u,33u,35u,38u,36u,37u,39u};
inline constexpr Mapping MATTSERATI_mapping[]={{0u,1u},{1u,1u},{2u,1u},{3u,1u},{4u,1u},{5u,1u},{6u,1u},{7u,1u},{8u,1u},{9u,1u},{10u,1u},{11u,1u},{12u,1u},{13u,1u},{14u,1u},{15u,1u},{16u,1u},{17u,1u},{18u,1u},{19u,1u},{20u,1u},{21u,1u},{22u,1u},{23u,1u},{24u,1u},{25u,1u},{26u,1u},{27u,1u},{28u,1u},{29u,1u},{30u,1u},{31u,1u},{32u,1u},{33u,1u},{34u,1u},{35u,1u},{36u,1u},{37u,1u},{38u,1u},{39u,1u}};
struct Profile { const char* family; unsigned nativeVertices,triangles; const char *geometry,*positionUv,*orderedXyz,*uvIndices; const Mapping* mapping; const unsigned* candidates; unsigned mappingCount,candidateCount; FleetProfile loader; };
inline constexpr Profile profiles[]={
 {"NewRav",18u,10u,"267c20819afd7c28d0a02fe503106f86000f5edf96678b3008627c12a6ed8029","bde667f4f095d7a8ebcf613c50aaa527d0292330559effd081c7d205adea60c9","ddef2a7c10cd544b5a501b045687bdd9d9b8fbc6144468ae066e54246d2ed53d","b501db59321f979b1c0354c631792da63d6a19c4bf6d629ed372fa3df217d9cd",NEWRAV_mapping,NEWRAV_candidates,18u,18u,{"NewRav","NEWRAV","port3-NEWRAV-OFF.ps2model","35245ca4139cbb1d20d5cc80971d74f8c4396972929fa68ef78e6d88a5abafbc",10810u,18u,30u,2u,1u,0u,nullptr,nullptr,nullptr}},
 {"Bruno",22u,12u,"934f66cfc21795ab284eec8af86c74fecd468bc62a539eb3b713a086c77798c1","651739a00b77755ca182a90b42c03fdcf76e3c94dd7770a2c88a04d65fb76d0e","f3d7bfaabaa0ea05749f74e4f5cb19e8c5e07d7e750e55980574fd7aa9d0f7cd","f6d99e8b8d03bf3cb066bc00f8ea3a3b63f469a5f578f87b79eee78fee8c0224",BRUNO_mapping,BRUNO_candidates,20u,22u,{"Bruno","BRUNO","port3-BRUNO-OFF.ps2model","919cd6636c968e232e6876a0c5afa192e8cb447eed5db02977fee4636b762ac4",10957u,20u,36u,2u,1u,0u,nullptr,nullptr,nullptr}},
 {"Mattserati",40u,20u,"f5de1db8bf54e75cdb06379864647bfa2bf7769c83af6c2a30dd8bceecf488e2","2d27cd48cbd98d66d87617e07f313c357f205d7da900dd7338ed98de4329e57c","76b06bc7c32c46943db3488450a3c060a4290f4a658af1f3e6e257dae8006004","eadef27a2dbdfb716fbe604b0f5a2e4c44b3bc85da89822a53e44a0cba467d2b",MATTSERATI_mapping,MATTSERATI_candidates,40u,40u,{"Mattserati","MATTSERATI","port3-MATTSERATI-OFF.ps2model","e7ae8b3806c8ea6571b508c24af4b8aa7aed4d31c423840ebc55e772b847c194",73496u,40u,60u,2u,1u,0u,nullptr,nullptr,nullptr}},
};
}
