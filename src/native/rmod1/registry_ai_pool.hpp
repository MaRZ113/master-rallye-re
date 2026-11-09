#pragma once
#include "core.hpp"
#include <unordered_set>

namespace rmod1 {
// The native builder remains the owner of materializable records. Policy and
// physical selection must use the same registered, mode-qualified snapshot.
inline std::vector<int> filter_registry_ai_pool(const std::vector<int>& native_ids,
                                               const std::vector<Vehicle>& snapshot,int cls) {
    std::unordered_set<int> allowed;
    for(const auto& row:snapshot)if(row.class_id==cls)allowed.insert(row.physical_id);
    std::vector<int> result;result.reserve(native_ids.size());
    for(int id:native_ids)if(allowed.count(id))result.push_back(id);
    return result;
}
}
