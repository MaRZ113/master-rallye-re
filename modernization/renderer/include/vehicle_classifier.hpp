#pragma once
#include "state_tracker.hpp"
namespace gfx2 {
inline constexpr uint32_t SHARED_WORLD_RETURN_RVA=0x0017707E;
inline constexpr size_t MAX_TRANSFORM_GROUPS=128,MAX_GROUP_SIGNATURES=64,MAX_NEAR_WHEELS=8;
enum class ObjectClass {Unknown,Body,Wheel};
enum ConstellationReason : uint32_t {DYNAMIC_CHASSIS=1,BODY_CLUSTER=2,WHEEL_SIGNATURE=4,
 FOUR_WHEELS=8,BILATERAL=16,AXLE_PAIRING=32,UNIQUE_ASSIGNMENT=64};
struct Classification {
 uint64_t track=0;uint32_t age=0;bool dynamic=false,ambiguous=false;
 ObjectClass object=ObjectClass::Unknown;uint64_t constellation=0;uint32_t vehicle_reasons=0;
 std::array<uint64_t,4> wheels{};float symmetry_error=0;
};
struct GroupDraw {uint32_t fvf=0,reasons=0,triangles=0;};
struct TransformGroup {
 D3DMATRIX world{};std::array<uint64_t,MAX_GROUP_SIGNATURES> signatures{};size_t size=0;
 Classification result{};uint32_t motion=0;bool saturated=false;
 uint32_t draws=0,body_draws=0,body_env_draws=0,wheel_draws=0,triangles=0;
};
struct LocalWheel {float x=0,y=0,z=0;};
struct ConstellationProposal {bool accepted=false,ambiguous=false;std::array<uint32_t,4> wheels{};float error=0;};
// Same bounded geometric predicate is used by native tracking and offline fixtures.
bool wheel_rectangle(const std::array<LocalWheel,4>& points,float& error) noexcept;
void classify_constellations(TransformGroup* groups,size_t count) noexcept;
struct ClassifierStats {uint64_t dynamic=0,chassis=0,constellations=0,body_draws=0,wheel_draws=0,ambiguities=0;};
class TransformTracker {
public:
 uint32_t observe(const D3DMATRIX& world,uint64_t signature,GroupDraw draw={}) noexcept;
 void next_frame() noexcept {current_size_=0;overflow_=false;}
 void finish_frame() noexcept;
 void reset() noexcept;
 const Classification* result(uint32_t group) const noexcept;
 // Only a previous complete-frame constellation may authorize the current draw.
 Classification predict(const D3DMATRIX& world,uint64_t signature) const noexcept;
 uint64_t epoch() const noexcept {return epoch_;}
 bool overflowed() const noexcept {return overflow_;}
 size_t size() const noexcept {return current_size_;}
 ClassifierStats stats() const noexcept;
private:
 std::array<TransformGroup,MAX_TRANSFORM_GROUPS> current_{},previous_{};
 size_t current_size_=0,previous_size_=0;uint64_t next_id_=0,epoch_=1;bool overflow_=false;
};
struct DrawClassification {
 uint32_t group=UINT32_MAX;uint64_t signature=0,epoch=0;Classification transform{};
 uint32_t reasons=0,fvf=0;bool alpha_blended=false;
};
enum ClassificationReason : uint32_t {EXACT_BUILD=1,RACE_PROJECTION=2,SHARED_OWNER=4,
 KNOWN_GEOMETRY=8,RIGID_WORLD=16,NORMAL_FVF=32,ENV_STAGE=64,CL_OPAQUE=128};
uint64_t geometry_signature(const Shadow& s,const ResourceRegistry& resources,const Args& args,uint32_t rva) noexcept;
uint32_t draw_reasons(const Shadow& s,bool known,bool race,bool owner) noexcept;
const char* object_classification(const DrawClassification& c) noexcept;
const char* material_classification(const DrawClassification& c) noexcept;
const char* reflection_exclusion(const DrawClassification& c) noexcept;
}
