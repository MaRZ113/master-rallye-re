#pragma once
#include "core.hpp"
#include <unordered_set>
#include <stdexcept>

namespace rmod1 {
// Retail 00450580 is Sattolo, not Fisher-Yates: its last source item can
// never be the first item popped. A rebuilt-per-slot pool needs a uniform
// permutation BEFORE that unchanged native cycle is applied.
template<class Draw> void unbias_rebuilt_ai_pool(std::vector<int>& ids,Draw draw) {
    for(size_t n=ids.size();n>1;--n) {
        const int at=draw(static_cast<int>(n));
        if(at<0||size_t(at)>=n)throw std::runtime_error("invalid AI shuffle draw");
        std::swap(ids[n-1],ids[size_t(at)]);
    }
}
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
