#pragma once
#include "road_teleport_model.hpp"
#include "physics_transaction_model.hpp"

namespace gfx2::road_teleport {
struct ConsumerEvent {
    uint64_t race_generation=0, owner_lifetime=0, identity_generation=0;
    uint32_t thread=0, controller=0, backing=0, actor=0;
    bool race_current=false, owner_current=false, human=false;
    bool flag_readable=false, matrix_readable=false, chassis_readable=false;
    uint8_t flag=0;
    std::array<uint32_t,16> matrix{};
    road_target::Vec3 chassis_after{};
    uint64_t active_consumer_calls=0;
    uint64_t transaction_candidate=0;
};
// Shared production routing; ABI integration tests feed these through the
// production x86 bridges, rather than manually advancing request states.
void handle_transaction_event(Request&, const physics_probe::TransactionRecord&) noexcept;
void handle_consumer_event(Request&, const ConsumerEvent&) noexcept;
void handle_settled_event(Request&, const ConsumerEvent&) noexcept;
}
