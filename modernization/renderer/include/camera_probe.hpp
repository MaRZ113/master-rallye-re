#pragma once
#include "game_fov.hpp"
#include <array>
#include <cstdint>
#include <iosfwd>
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
 CameraSubmissionSnapshot pre_submission{};
};

enum class CameraProbeStatus {
 NoVerifiedGameplayViewSite,
 NativeSetTransformFailed,
 TraceDisabled,
 ExecutableProfileUnsupported,
 CaptureInactive,
 ProjectionUnavailable,
 ProjectionIneligible,
 DuplicateSuppressed,
 ReadyForObservation,
 ViewMatrixReadIncomplete,
 OwnerReadIncomplete,
 ObservationEmitted,
 SerializationFailure,
 SessionWriteFailed
};

struct CameraProbeGateInput {
 D3DTRANSFORMSTATETYPE transform_type=D3DTS_WORLD;
 bool exe_caller=false;
 uint32_t caller_rva=0;
 HRESULT native_result=E_FAIL;
 bool trace_enabled=false,capture_active=false,profile_supported=false;
 bool requested_projection_known=false,effective_projection_known=false;
 D3DMATRIX requested_projection{},effective_projection{};
 bool observation_already_claimed=false;
};

struct CameraProbeGateResult {
 CameraProbeStatus status=CameraProbeStatus::NoVerifiedGameplayViewSite;
 bool gameplay_view_site=false;
};

struct CameraProbeFrameDiagnostic {
 CameraProbeStatus status=CameraProbeStatus::NoVerifiedGameplayViewSite;
 uint32_t caller_rva=0,duplicate_suppressed=0;
 bool gameplay_view_site_seen=false,observation_claimed=false,observation_emitted=false;
 bool owner_reads_known=false,owner_reads_complete=false;
 void record_gate(const CameraProbeGateResult& result,uint32_t rva) noexcept;
 bool claim_observation() noexcept;
 void record_outcome(CameraProbeStatus value,bool emitted,bool reads_known=false,bool reads_complete=false) noexcept;
};

CameraProbeGateResult camera_probe_gate(const CameraProbeGateInput& input) noexcept;
const char* camera_probe_status_name(CameraProbeStatus status) noexcept;
std::string camera_probe_frame_summary_json(const CameraProbeFrameDiagnostic& diagnostic);
bool camera_owner_reads_complete(const CameraOwnerObservation& owner) noexcept;
bool read_camera_owner_observation(uintptr_t module_base,CameraOwnerObservation& out) noexcept;
const char* camera_projection_family(const D3DMATRIX& projection) noexcept;
std::string camera_owner_observation_json(const CameraOwnerObservation& owner,uint64_t device,uint64_t frame,
 uint32_t caller_rva,const D3DMATRIX& requested_projection,const D3DMATRIX& effective_projection,
 const D3DMATRIX& view);

}
