#pragma once
#include "state_tracker.hpp"
namespace gfx2 {
inline constexpr uint32_t SHARED_WORLD_RETURN_RVA=0x0017707E;
inline constexpr size_t MAX_TRANSFORM_GROUPS=128,MAX_GROUP_SIGNATURES=64;
struct Classification {
 uint64_t track=0;uint32_t age=0;bool dynamic=false,ambiguous=false;
};
struct TransformGroup {
 D3DMATRIX world{};std::array<uint64_t,MAX_GROUP_SIGNATURES> signatures{};size_t size=0;
 Classification result{};uint32_t motion=0;bool saturated=false;
};
class TransformTracker {
public:
 // Fixed capacities, no heap allocation or GPU getters. Full frame association is order-independent.
 uint32_t observe(const D3DMATRIX& world,uint64_t signature) noexcept;
 void next_frame() noexcept {current_size_=0;overflow_=false;}
 void finish_frame() noexcept;
 void reset() noexcept;
 const Classification* result(uint32_t group) const noexcept;
 uint64_t epoch() const noexcept {return epoch_;}
 bool overflowed() const noexcept {return overflow_;}
private:
 std::array<TransformGroup,MAX_TRANSFORM_GROUPS> current_{},previous_{};
 size_t current_size_=0,previous_size_=0;uint64_t next_id_=0,epoch_=1;bool overflow_=false;
};
struct DrawClassification {
 uint32_t group=UINT32_MAX;uint64_t signature=0,epoch=0;Classification transform{};
 uint32_t reasons=0;
};
enum ClassificationReason : uint32_t {EXACT_BUILD=1,RACE_PROJECTION=2,SHARED_OWNER=4,
 KNOWN_GEOMETRY=8,RIGID_WORLD=16,NORMAL_FVF=32,ENV_STAGE=64,CL_OPAQUE=128};
uint64_t geometry_signature(const Shadow& s,const ResourceRegistry& resources,const Args& args,uint32_t rva) noexcept;
uint32_t draw_reasons(const Shadow& s,bool known,bool race,bool owner) noexcept;
const char* object_classification(const DrawClassification& c) noexcept;
}
