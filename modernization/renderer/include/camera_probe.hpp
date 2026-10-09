#pragma once
#include "game_fov.hpp"
#include <array>
#include <string>

namespace gfx2 {

struct CameraOwnerObservation {
 uintptr_t manager_pointer=0,renderer_pointer=0,renderer_holder=0,current_camera=0;
 std::array<uintptr_t,4> manager_cameras{};
 std::array<bool,4> manager_camera_read{};
 int32_t manager_count=-1,camera_index=-1;
 bool manager_pointer_read=false,manager_count_read=false,renderer_pointer_read=false;
 bool manager_count_valid=false,renderer_holder_read=false,current_camera_read=false,camera_read=false;
 CameraFrame camera{};
};

bool read_camera_owner_observation(uintptr_t module_base,CameraOwnerObservation& out) noexcept;
const char* camera_projection_family(const D3DMATRIX& projection) noexcept;
std::string camera_owner_observation_json(const CameraOwnerObservation& owner,uint64_t device,uint64_t frame,
 uint32_t caller_rva,const D3DMATRIX& requested_projection,const D3DMATRIX& effective_projection,
 const D3DMATRIX& view);

}
