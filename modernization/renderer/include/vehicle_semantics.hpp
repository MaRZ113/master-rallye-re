#pragma once
#include "vehicle_classifier.hpp"
namespace gfx2 {
inline constexpr size_t MAX_VEHICLE_SIGNATURES=512,MAX_SEMANTIC_PENDING=1024;
// Full canonical words disambiguate the existing signature hash. WORLD is absent.
struct VehicleSignatureKey {
 uint64_t hash=0;std::array<uint64_t,53> words{};
 std::array<uintptr_t,4> pointers{};std::array<uint64_t,4> generations{};
 bool operator==(const VehicleSignatureKey& other) const noexcept {return hash==other.hash&&words==other.words;}
 bool valid(const ResourceRegistry&) const noexcept;
};
VehicleSignatureKey vehicle_signature_key(const Shadow&,const ResourceRegistry&,const Args&,uint32_t rva) noexcept;
struct VehicleSemanticEntry {
 VehicleSignatureKey key;uint64_t id=0,learned_frame=0,epoch=0;Classification origin;
};
class VehicleSemantics {
 struct Pending {VehicleSignatureKey key;uint32_t group=UINT32_MAX;uint64_t epoch=0;bool successful=false;};
 std::array<VehicleSemanticEntry,MAX_VEHICLE_SIGNATURES> entries_{};
 std::array<Pending,MAX_SEMANTIC_PENDING> pending_{};
 size_t size_=0,pending_size_=0;uint64_t next_id_=0;
public:
 uint64_t promotions=0,invalidations=0,rejections=0;
 const VehicleSemanticEntry* find(const VehicleSignatureKey&,const ResourceRegistry&) noexcept;
 const VehicleSemanticEntry* by_id(uint64_t id) const noexcept;
 uint32_t observe(const VehicleSignatureKey&,const DrawClassification&) noexcept;
 void submitted(uint32_t index,bool success) noexcept;
 void learn(const TransformTracker&,const ResourceRegistry&,uint64_t frame) noexcept;
 void prune(const ResourceRegistry&) noexcept;
 void clear() noexcept; // Conservative Reset/scene policy, even surviving MANAGED assets relearn.
 void next_frame() noexcept {pending_size_=0;promotions=invalidations=rejections=0;}
 size_t size() const noexcept {return size_;}
 const VehicleSemanticEntry& entry(size_t i) const noexcept {return entries_[i];}
};
const char* vehicle_semantic_source(VehicleSemanticSource) noexcept;
}
