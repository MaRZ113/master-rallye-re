#pragma once
#include "physics_probe_model.hpp"

namespace gfx2::physics_probe {
// Included in the probe's anonymous namespace; all state uses probe.lock.
struct TransactionSample {
    uint64_t sequence = 0, candidate = 0, qpc = 0, race = 0, lifetime = 0, identity_generation = 0;
    uint32_t site = 0, thread = 0, backing = 0, controller = 0, manager = 0, writer_owner = 0;
    int32_t participant = -1;
    uint8_t flag = 0, store_operand = 0;
    bool readable = false, owner_current = false, human = false, race_valid = false;
    bool unknown_transition = false, paused_known = false, paused = false;
    std::array<uint32_t,16> matrix{};
};
struct TransactionRecord { TransactionSample before{}, after{}; uint32_t kind = 0; };
struct TransactionIdentity {
    uint32_t backing = 0; uint64_t race = 0, lifetime = 0, candidate = 0;
    uint8_t flag = 0; bool known = false, zero_recorded = false;
};
struct TransactionCapture {
    std::array<TransactionRecord,128> important{};
    std::array<TransactionRecord,16> diagnostics{};
    std::array<TransactionIdentity,MAX_TRACKS> identities{};
    size_t count = 0, diagnostic_count = 0, pending_observations = 0;
    uint64_t sequence = 0, candidate_sequence = 0, overflow = 0, diagnostic_overflow = 0;
    uint64_t zero_stores = 0, repeated_stores = 0, unknown_transitions = 0, pairing_failures = 0;
};
struct TransactionPending { bool active = false; TransactionSample sample{}; };
inline uint64_t matrix_digest(const std::array<uint32_t,16>& matrix) noexcept {
    uint64_t h = 14695981039346656037ull;
    for (auto word : matrix) for (unsigned shift=0;shift<32;shift+=8) {
        h ^= (word >> shift) & 255u; h *= 1099511628211ull;
    }
    return h;
}
inline TransactionIdentity* transaction_identity(TransactionCapture& transaction, const TransactionSample& sample) noexcept {
    if (!sample.readable || !sample.race_valid) return nullptr;
    for (auto& id : transaction.identities) if (id.backing == sample.backing) {
        if (id.race != sample.race || id.lifetime != sample.lifetime) id = {};
        id.backing=sample.backing; id.race=sample.race; id.lifetime=sample.lifetime;
        return &id;
    }
    for (auto& id : transaction.identities) if (!id.backing) {
        id.backing=sample.backing; id.race=sample.race; id.lifetime=sample.lifetime; return &id;
    }
    ++transaction.overflow; return nullptr;
}
inline TransactionRecord transaction_retain(TransactionCapture& transaction, TransactionRecord record) noexcept {
    auto* id = transaction_identity(transaction,record.before);
    if (id) {
        if ((id->known && record.before.flag != id->flag) ||
            (!id->known && record.before.flag && record.before.site != PUBLISH_PATCH_VA)) {
            record.before.unknown_transition=true; ++transaction.unknown_transitions;
        }
        if (record.before.site == PUBLISH_PATCH_VA ||
            (record.kind==0 && record.after.flag &&
             ((!record.before.flag && record.before.site==INPUT_FLAG_PATCH_VA) || record.before.site==RESTORE_FLAG_PATCH_VA))) {
            // An invocation ID, never itself a causal proof or controller ownership certificate.
            id->candidate=++transaction.candidate_sequence; id->zero_recorded=false;
        }
        record.before.candidate=record.after.candidate=id->candidate;
        id->known=record.after.readable; id->flag=record.after.flag;
    }
    record.before.sequence=record.after.sequence=++transaction.sequence;
    const bool store = record.kind == 0 && record.before.site != MATRIX_COMPLETE_PATCH_VA;
    if (store && record.before.readable && record.after.readable &&
        record.before.flag == record.after.flag && record.before.site != PUBLISH_PATCH_VA &&
        !record.before.unknown_transition) {
        if (!record.before.flag) { ++transaction.zero_stores; return record; }
        ++transaction.repeated_stores;
        if (transaction.diagnostic_count < transaction.diagnostics.size())
            transaction.diagnostics[transaction.diagnostic_count++]=record;
        else ++transaction.diagnostic_overflow;
        return record;
    }
    if (record.kind == 1 && !record.before.flag && !record.before.unknown_transition) {
        if (!id || !id->candidate || id->zero_recorded) return record;
        id->zero_recorded=true;
    }
    if (transaction.count < transaction.important.size()) transaction.important[transaction.count++]=record;
    else ++transaction.overflow;
    return record;
}

}
