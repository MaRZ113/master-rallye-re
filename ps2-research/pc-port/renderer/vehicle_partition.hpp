#pragma once
#include "reflection_pilot.hpp"
#include "ps2_port_extension.hpp"
#include <array>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {
struct PartitionFace { const char* hash; uint32_t multiplicity; bool shiny; };
struct PartitionMaterial {
    const char* vehicle; const char* geometry_sha;
    uint32_t vertices, triangles;
    const PartitionFace* faces; size_t face_count;
};
struct PartitionRun { uint32_t first=0, count=0; bool shiny=false; };
struct PartitionPlan {
    bool accepted=false;
    const char* reason="not_classified";
    const PartitionMaterial* material=nullptr;
    std::vector<PartitionRun> runs;
};
bool vehicle_partition_layout(uint32_t triangles,uint32_t vertices) noexcept;
// These are exact current upload positions, not source ordinals or texture IDs.
std::vector<std::string> vehicle_face_hashes(const DrawSnapshot&);
PartitionPlan partition_ordered_faces(const std::vector<std::string>&,
                                      const PartitionMaterial&);
bool partition_context_valid(const ReflectionSnapshot&,uint64_t generation) noexcept;
constexpr bool vehicle_partition_opt_in(std::wstring_view mode,std::wstring_view version,
                                        bool supported) noexcept {
    return supported && mode==L"1" && version==L"1";
}
class VehiclePartitionPilot {
    struct Cache {
        std::array<uint64_t,15> key{};
        PartitionPlan plan;
        bool valid=false;
    };
    std::array<Cache,64> cache_{};
    size_t next_=0;
    std::array<bool,9> logged_{};
    bool requested_=false, diagnostics_=false;
public:
    VehiclePartitionPilot(bool supported,const std::wstring& ini) noexcept;
    bool requested() const noexcept { return requested_; }
    PartitionPlan classify(const ReflectionSnapshot&,uint64_t generation) noexcept;
    bool claim_diagnostic(const PartitionMaterial*) noexcept;
};
// Preserve the original IB order/ranges. There is no replay or second pass.
// The first native failure is returned; no whole original draw may follow it.
template<class Submit>
HRESULT submit_partition(const PartitionPlan& plan,uint32_t start,Submit&& submit) noexcept {
    if(!plan.accepted || !plan.material || plan.runs.empty())return E_INVALIDARG;
    uint64_t cursor=0;
    for(const auto& run:plan.runs) {
        if(!run.count || run.first!=cursor)return E_INVALIDARG;
        cursor+=run.count;
        if(cursor>plan.material->triangles || uint64_t(start)+cursor*3>UINT32_MAX)return E_INVALIDARG;
    }
    if(cursor!=plan.material->triangles)return E_INVALIDARG;
    HRESULT result=S_OK;
    for(const auto& run:plan.runs) {
        result=submit(run,start+run.first*3);
        if(FAILED(result))return result;
    }
    return result;
}
} // namespace gfx2::ps2port
