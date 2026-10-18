#pragma once

#include "road_target_model.hpp"
#include "race_epoch.hpp"
#include <cstdint>
#include <string>

namespace gfx2 {

struct FreeCameraConfig;

struct PhysicsProbeSettings {
    bool enabled = false;
    bool road_target_preview_enabled = false;
    bool road_teleport_requested = false;
    bool road_teleport_enabled = false;
    bool road_teleport_road_only = true;
    bool valid = true;
    double road_target_preview_radius = 60.0;
    double road_teleport_max_distance = 20.0;
    uint32_t road_teleport_arm_timeout_seconds = 60;
    std::string raw_value = "0";
};

struct RoadTeleportStatus {
    uint64_t sequence = 0;
    const char* state = "disabled";
    const char* reason = "disabled_by_config";
};

PhysicsProbeSettings read_physics_probe_settings(const std::wstring& path) noexcept;
PhysicsProbeSettings forward_free_camera_teleport_settings(
    PhysicsProbeSettings settings, const FreeCameraConfig& camera) noexcept;
bool attach_physics_probe(bool exact_retail, const PhysicsProbeSettings& settings) noexcept;
void release_physics_probe() noexcept;
void publish_physics_probe_race_context(bool valid, uint64_t race_generation,
                                        uint64_t owner_lifetime) noexcept;
void publish_physics_probe_pause_state(bool known, bool paused,
                                       uint64_t sampled_tick_ms) noexcept;
// Development-only probe relocation (see ProbeTeleport in MRRRenderer.ini.example).
const char* physics_probe_dev_teleport_request(float x, float y, float z, float yaw_degrees) noexcept;
void physics_probe_dev_teleport_tick() noexcept;
bool arm_physics_probe_road_teleport(float camera_x, float camera_y, float camera_z,
                                     bool freecam_active, bool pause_known, bool paused,
                                     const RaceCertificate& certificate,
                                     uint32_t timeout_seconds, double maximum_distance) noexcept;
RoadTeleportStatus physics_probe_road_teleport_status() noexcept;
std::string physics_probe_road_teleport_status_json() noexcept;
std::string physics_probe_road_target_preview_json(float camera_x, float camera_y,
                                                   float camera_z, bool freecam_active,
                                                   uint64_t race_generation,
                                                   uint64_t owner_lifetime) noexcept;

} // namespace gfx2
