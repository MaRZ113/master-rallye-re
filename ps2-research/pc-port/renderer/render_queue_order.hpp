#pragma once
// COURSE-RENDER-FIX1: order of the opaque draw queue of the original renderer (MRallye.exe 0x562810).
//
// The scene walk submits one 24-byte record per draw into a vector (renderer object + 0x24 .. +0x28):
//
//     +0x00 owner (instance)   +0x04 mesh   +0x08 sub-mesh index   +0x10 key low   +0x14 key high
//
// The flush (0x562810, called once per pass from 0x56ba70) sorts the records ascending by the 64-bit key
// (high word first) and draws them in that order. For the opaque list the key is built by 0x583820:
//
//     high = 0
//     low  = (sub-mesh index & 7) << 29 | (material id & 0x1fff) << 16 | (texture id & 0xffff)
//
// The material id is a slot of the engine's resource pool (allocated at load, recycled through a free list), so it
// says nothing about what a draw is. Where the cars land between the course draws is therefore decided by pool
// slots: on the stock courses the terrain happens to sort before the cars, on the converted SpainS2 it does not
// (the cars are drawn first, and the PS2 environment capture at the first car draw sees an empty ground).
//
// The PS2 draws the course before the cars. This header moves the records of the race cars behind every other opaque
// record by raising their key high word from 0 to 1 right before the flush sorts them. Nothing else about the queue
// changes (the order inside the two groups is the engine's own, the alpha list is untouched). Portable: memory access
// is injected, so the contract is testable without the game.
#include <array>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace gfx2::ps2port {

inline constexpr uint32_t kQueueOpaqueBeginOffset = 0x24, kQueueOpaqueEndOffset = 0x28;
inline constexpr uint32_t kQueueRecordSize = 24, kQueueMaxRecords = 4096;
inline constexpr uint32_t kQueueFlushCallRva = 0x16bab8, kQueueFlushRva = 0x162810;

struct RenderQueueStats {
    uint64_t flushes = 0, records = 0, vehicle_records = 0, promoted = 0, rejected = 0, unreadable = 0;
    uint32_t last_records = 0, last_vehicles = 0, last_promoted = 0;
    const char* last_reason = "not_run";
};

// One group of the submission vector: all records of one owner with one material id, in submission order.
struct RenderQueueRun {
    uint32_t owner = 0, material = 0, count = 0, texture_min = 0xffff, texture_max = 0, sub = 0;
    bool vehicle = false;
};

struct RenderQueueSnapshot {
    uint32_t records = 0, vehicles = 0, promoted = 0;
    std::vector<RenderQueueRun> runs;      // bounded
    std::vector<uint32_t> owners;          // distinct owners in order of first appearance (bounded)
    bool truncated = false;
};

// read(address, uint32_t&) -> bool, write(address, uint32_t) -> bool, is_vehicle(owner) -> bool.
// Returns false when the vector is not in the expected shape (nothing is modified in that case).
template<class Read, class Write, class IsVehicle>
bool prioritize_vehicle_records(uintptr_t queue, Read read, Write write, IsVehicle is_vehicle, RenderQueueStats& stats,
                                RenderQueueSnapshot* snapshot = nullptr, bool modify = true, size_t max_runs = 160) {
    ++stats.flushes;
    stats.last_records = stats.last_vehicles = stats.last_promoted = 0;
    uint32_t begin = 0, end = 0;
    if (queue < 0x10000 || (queue & 3) || !read(queue + kQueueOpaqueBeginOffset, begin) || !read(queue + kQueueOpaqueEndOffset, end)) {
        ++stats.unreadable; stats.last_reason = "queue_unreadable"; return false;
    }
    if (!begin && !end) { stats.last_reason = "empty"; return true; }
    if (begin < 0x10000 || (begin & 3) || (end & 3) || end < begin || (end - begin) % kQueueRecordSize ||
        (end - begin) / kQueueRecordSize > kQueueMaxRecords) {
        ++stats.rejected; stats.last_reason = "queue_shape_rejected"; return false;
    }
    const uint32_t count = (end - begin) / kQueueRecordSize;
    // First pass reads and validates every record; only then keys are written.
    struct Item { uint32_t owner = 0, high = 0, low = 0, sub = 0; bool vehicle = false; };
    std::vector<Item> items;
    items.reserve(count);
    for (uint32_t i = 0; i < count; ++i) {
        const uint32_t record = begin + i * kQueueRecordSize;
        Item item;
        if (!read(record, item.owner) || !read(record + 8, item.sub) || !read(record + 0x10, item.low) || !read(record + 0x14, item.high)) {
            ++stats.unreadable; stats.last_reason = "record_unreadable"; return false;
        }
        item.vehicle = item.owner >= 0x10000 && is_vehicle(item.owner);
        items.push_back(item);
    }
    uint32_t vehicles = 0, promoted = 0;
    for (uint32_t i = 0; i < count; ++i) {
        const Item& item = items[i];
        if (!item.vehicle) continue;
        ++vehicles;
        if (item.high == 0 && modify) {
            if (!write(begin + i * kQueueRecordSize + 0x14, 1u)) { ++stats.unreadable; stats.last_reason = "key_write_failed"; return false; }
            ++promoted;
        }
    }
    if (snapshot) {
        snapshot->records = count; snapshot->vehicles = vehicles; snapshot->promoted = promoted;
        snapshot->runs.clear(); snapshot->owners.clear(); snapshot->truncated = false;
        for (const Item& item : items) {
            size_t owner_index = snapshot->owners.size();
            for (size_t k = 0; k < snapshot->owners.size(); ++k) if (snapshot->owners[k] == item.owner) { owner_index = k; break; }
            if (owner_index == snapshot->owners.size()) {
                if (snapshot->owners.size() >= 64) { snapshot->truncated = true; continue; }
                snapshot->owners.push_back(item.owner);
            }
            const uint32_t material = (item.low >> 16) & 0x1fff, texture = item.low & 0xffff, sub = item.low >> 29;
            RenderQueueRun* run = nullptr;
            for (auto& r : snapshot->runs) if (r.owner == item.owner && r.material == material && r.sub == sub) { run = &r; break; }
            if (!run) {
                if (snapshot->runs.size() >= max_runs) { snapshot->truncated = true; continue; }
                snapshot->runs.push_back({item.owner, material, 0, 0xffff, 0, sub, item.vehicle});
                run = &snapshot->runs.back();
            }
            ++run->count;
            if (texture < run->texture_min) run->texture_min = texture;
            if (texture > run->texture_max) run->texture_max = texture;
        }
    }
    stats.records += count; stats.vehicle_records += vehicles; stats.promoted += promoted;
    stats.last_records = count; stats.last_vehicles = vehicles; stats.last_promoted = promoted;
    stats.last_reason = vehicles ? (promoted ? "vehicles_moved_last" : "vehicles_already_last") : "no_vehicle_records";
    return true;
}

// Diagnostic record of one flush (ReflectionStageDiag): the submitted records grouped by owner and material id.
inline std::string render_queue_json(const RenderQueueSnapshot& s, uint64_t frame, unsigned flush, bool enabled) {
    std::string out = "{\"type\":\"ps2_render_queue\",\"frame\":" + std::to_string(frame) + ",\"flush\":" + std::to_string(flush) +
        ",\"vehicles_last\":" + (enabled ? "true" : "false") + ",\"records\":" + std::to_string(s.records) +
        ",\"vehicle_records\":" + std::to_string(s.vehicles) + ",\"promoted\":" + std::to_string(s.promoted) +
        ",\"truncated\":" + (s.truncated ? "true" : "false") + ",\"owners\":[";
    char buffer[24];
    for (size_t i = 0; i < s.owners.size(); ++i) {
        std::snprintf(buffer, sizeof(buffer), "%s\"%08x\"", i ? "," : "", s.owners[i]);
        out += buffer;
    }
    out += "],\"runs\":[";
    for (size_t i = 0; i < s.runs.size(); ++i) {
        const auto& r = s.runs[i];
        size_t owner_index = 0;
        for (size_t k = 0; k < s.owners.size(); ++k) if (s.owners[k] == r.owner) { owner_index = k; break; }
        // [owner index, vehicle, sub-mesh index, material id, records, texture id min, texture id max]
        out += std::string(i ? "," : "") + "[" + std::to_string(owner_index) + "," + (r.vehicle ? "1" : "0") + "," + std::to_string(r.sub) + "," +
            std::to_string(r.material) + "," + std::to_string(r.count) + "," + std::to_string(r.texture_min) + "," + std::to_string(r.texture_max) + "]";
    }
    return out + "]}";
}

} // namespace gfx2::ps2port
