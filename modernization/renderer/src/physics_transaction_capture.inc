TransactionCapture transaction{};
thread_local TransactionPending transaction_pending{};
void transaction_owner(TransactionSample& out) noexcept {
    out.race_valid=probe.route_context_valid; out.race=probe.route_context_race_generation;
    out.lifetime=probe.route_context_owner_lifetime;
    size_t matches=0;
    for (const auto& track : probe.tracks) if (track.used && track.identity.backing == out.backing) {
        ++matches; NativeLinks now{};
        out.owner_current=read_native_links(track.identity.controller,now) && same_identity(track.identity,now);
        out.controller=track.identity.controller; out.identity_generation=track.identity_generation;
        out.human=track.identity.player_type==1;
    }
    if (matches!=1) {out.owner_current=false;out.controller=0;out.identity_generation=0;out.human=false;}
    const auto pause=pause_state_at({probe.pause_state_known,probe.pause_paused,probe.pause_sample_tick_ms},GetTickCount64(),500);
    out.paused_known=pause.known;out.paused=pause.paused;
}
void transaction_memory(TransactionSample& out) noexcept {
    LARGE_INTEGER clock{}; QueryPerformanceCounter(&clock);out.qpc=static_cast<uint64_t>(clock.QuadPart);
    out.readable=pointer_shape(out.backing) && read_u8(out.backing,0x33,out.flag) &&
        read_bytes(out.backing,0x34,out.matrix.data(),sizeof(out.matrix));
}
uint64_t transaction_consumer(const Snapshot& before, const Snapshot& after, bool after_valid) noexcept {
    TransactionRecord record{};record.kind=1;
    auto set=[](TransactionSample& out,const Snapshot& in) {
        out.site=CONTROLLER_CALL_VA;out.thread=in.thread_id;out.backing=in.links.backing;
        out.qpc=in.qpc;out.flag=in.apply_flag;out.matrix=in.transform_bits;
        out.readable=(in.valid_mask & 5u)==5u;
        transaction_owner(out);
    };
    set(record.before,before); set(record.after,after);
    record.after.readable=record.after.readable && after_valid;
    record = transaction_retain(transaction,record);
    return record.before.candidate;
}
void transaction_inline(const uint32_t* saved, uint32_t site, bool after) noexcept {
    if (!saved || !InterlockedCompareExchange(&probe.enabled,0,0)) return;
    // Saved PUSHAD order: EDI ESI EBP savedESP EBX EDX ECX EAX, followed by FLAGS.
    AcquireSRWLockExclusive(&probe.lock);
    if (!InterlockedCompareExchange(&probe.enabled,0,0) || !probe.installed || !batch_intact()) {
        if (InterlockedCompareExchange(&probe.enabled,0,0) && probe.installed) disable_after_ownership_loss();
        ReleaseSRWLockExclusive(&probe.lock);return;
    }
    if (!after) {
        if (transaction_pending.active) ++transaction.pairing_failures;
        else ++transaction.pending_observations;
        transaction_pending={};transaction_pending.active=true;
        auto& sample=transaction_pending.sample;sample.site=site;sample.thread=GetCurrentThreadId();
        if (site==PUBLISH_PATCH_VA || site==MATRIX_COMPLETE_PATCH_VA) {
            sample.backing=saved[2]; sample.manager=saved[1];
            if (!(saved[4]&3u) && saved[4]/4 < MAX_TRACKS) sample.participant=static_cast<int32_t>(saved[4]/4);
        } else if (site==INPUT_FLAG_PATCH_VA) {sample.backing=saved[7];sample.writer_owner=saved[6];}
        else if (site==RESTORE_FLAG_PATCH_VA) {sample.backing=saved[1];sample.writer_owner=saved[1];}
        else { read_u32(saved[7],8,sample.backing); sample.manager=saved[1]; }
        sample.store_operand=site==PUBLISH_PATCH_VA ? 1 : site==INPUT_FLAG_PATCH_VA ? static_cast<uint8_t>(saved[5]) :
            site==RESTORE_FLAG_PATCH_VA ? static_cast<uint8_t>(saved[7]) : site==CLEAR_TIMER_STORE_VA ? static_cast<uint8_t>(saved[6]) : 0;
        transaction_memory(sample);transaction_owner(sample);
    } else if (!transaction_pending.active || transaction_pending.sample.site!=site ||
               transaction_pending.sample.thread!=GetCurrentThreadId()) {
        ++transaction.pairing_failures;
        if(transaction_pending.active && transaction.pending_observations) --transaction.pending_observations;
        transaction_pending={};
    } else {
        TransactionRecord record{};record.before=transaction_pending.sample; record.after=record.before;
        transaction_memory(record.after);transaction_owner(record.after);
        transaction_pending={};
        if(transaction.pending_observations) --transaction.pending_observations;
        record = transaction_retain(transaction,record);
        if (probe.road_teleport_enabled)
            road_teleport::handle_transaction_event(probe.road_teleport, record);
    }
    ReleaseSRWLockExclusive(&probe.lock);
}
