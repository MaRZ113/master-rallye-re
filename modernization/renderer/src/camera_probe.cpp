#include "camera_probe.hpp"
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <iomanip>
#include <sstream>

namespace gfx2 {
namespace {
template<size_t N> void float_array(std::ostream& out,const std::array<float,N>& values) {
 out<<'[';
 for(size_t i=0;i<N;++i){if(i)out<<',';if(std::isfinite(values[i]))out<<std::setprecision(9)<<values[i];else out<<"null";}
 out<<']';
}
void matrix(std::ostream& out,const float* values) {
 out<<"{\"values\":[";
 for(int i=0;i<16;++i){if(i)out<<',';if(std::isfinite(values[i]))out<<std::setprecision(9)<<values[i];else out<<"null";}
 out<<"],\"bits\":[";
 for(int i=0;i<16;++i){uint32_t bits=0;std::memcpy(&bits,values+i,sizeof(bits));if(i)out<<',';out<<bits;}
 out<<"]}";
}
void matrix(std::ostream& out,const D3DMATRIX& value){matrix(out,&value.m[0][0]);}
void optional_pointer(std::ostream& out,bool known,uintptr_t value){if(known)out<<value;else out<<"null";}
std::string hex_rva(uint32_t rva){std::ostringstream out;out<<"0x"<<std::hex<<std::setw(8)<<std::setfill('0')<<rva;return out.str();}
}

CameraProbeGateResult camera_probe_gate(const CameraProbeGateInput& input) noexcept {
 CameraProbeGateResult out{};
 out.gameplay_view_site=input.transform_type==D3DTS_VIEW&&input.exe_caller&&input.caller_rva==GAMEPLAY_VIEW_RETURN_RVA;
 if(!out.gameplay_view_site)return out;
 if(FAILED(input.native_result))out.status=CameraProbeStatus::NativeSetTransformFailed;
 else if(!input.trace_enabled)out.status=CameraProbeStatus::TraceDisabled;
 else if(!input.profile_supported)out.status=CameraProbeStatus::ExecutableProfileUnsupported;
 else if(!input.capture_active)out.status=CameraProbeStatus::CaptureInactive;
 else if(!input.requested_projection_known||!input.effective_projection_known)out.status=CameraProbeStatus::ProjectionUnavailable;
 else if(!symmetric_lh(input.requested_projection)||!symmetric_lh(input.effective_projection))out.status=CameraProbeStatus::ProjectionIneligible;
 else if(input.observation_already_claimed)out.status=CameraProbeStatus::DuplicateSuppressed;
 else out.status=CameraProbeStatus::ReadyForObservation;
 return out;
}

const char* camera_probe_status_name(CameraProbeStatus status) noexcept {
 switch(status){
  case CameraProbeStatus::NoVerifiedGameplayViewSite:return "no_verified_gameplay_view_site_observed";
  case CameraProbeStatus::NativeSetTransformFailed:return "native_set_transform_failed";
  case CameraProbeStatus::TraceDisabled:return "trace_disabled";
  case CameraProbeStatus::ExecutableProfileUnsupported:return "executable_profile_unsupported";
  case CameraProbeStatus::CaptureInactive:return "gameplay_view_observed_capture_inactive";
  case CameraProbeStatus::ProjectionUnavailable:return "projection_state_unavailable";
  case CameraProbeStatus::ProjectionIneligible:return "projection_ineligible";
  case CameraProbeStatus::DuplicateSuppressed:return "duplicate_observation_suppressed";
  case CameraProbeStatus::ReadyForObservation:return "ready_for_observation";
  case CameraProbeStatus::ViewMatrixReadIncomplete:return "view_matrix_read_incomplete";
  case CameraProbeStatus::OwnerReadIncomplete:return "camera_owner_read_incomplete";
  case CameraProbeStatus::ObservationEmitted:return "observation_emitted";
  case CameraProbeStatus::SerializationFailure:return "serialization_failure";
  case CameraProbeStatus::SessionWriteFailed:return "session_write_failed";
 }
 return "unknown";
}

void CameraProbeFrameDiagnostic::record_gate(const CameraProbeGateResult& result,uint32_t rva) noexcept {
 if(!result.gameplay_view_site)return;
 gameplay_view_site_seen=true;caller_rva=rva;status=result.status;
 if(result.status==CameraProbeStatus::DuplicateSuppressed&&duplicate_suppressed!=UINT32_MAX)++duplicate_suppressed;
}
bool CameraProbeFrameDiagnostic::claim_observation() noexcept {
 if(observation_claimed)return false;
 observation_claimed=true;return true;
}
void CameraProbeFrameDiagnostic::record_outcome(CameraProbeStatus value,bool emitted,bool reads_known,bool reads_complete) noexcept {
 status=value;observation_emitted=emitted;owner_reads_known=reads_known;owner_reads_complete=reads_known&&reads_complete;
}
std::string camera_probe_frame_summary_json(const CameraProbeFrameDiagnostic& diagnostic) {
 std::ostringstream out;
 out<<"{\"status\":"<<quote(camera_probe_status_name(diagnostic.status))
    <<",\"gameplay_view_site_seen\":"<<(diagnostic.gameplay_view_site_seen?"true":"false")
    <<",\"caller_rva\":"<<(diagnostic.gameplay_view_site_seen?quote(hex_rva(diagnostic.caller_rva)):"null")
    <<",\"observation_claimed\":"<<(diagnostic.observation_claimed?"true":"false")
    <<",\"observation_emitted\":"<<(diagnostic.observation_emitted?"true":"false")
    <<",\"owner_reads_complete\":";
 if(diagnostic.owner_reads_known)out<<(diagnostic.owner_reads_complete?"true":"false");else out<<"null";
 out<<",\"duplicate_suppressed\":"<<diagnostic.duplicate_suppressed<<'}';
 return out.str();
}

bool camera_owner_reads_complete(const CameraOwnerObservation& owner) noexcept {
 if(!owner.manager_pointer_read||!owner.manager_count_read||!owner.manager_count_valid||
    !owner.renderer_pointer_read||!owner.renderer_holder_read||!owner.current_camera_read||!owner.camera_read)return false;
 for(int32_t i=0;i<owner.manager_count;++i)if(!owner.manager_camera_read[static_cast<size_t>(i)])return false;
 return true;
}

bool read_camera_owner_observation(uintptr_t base,CameraOwnerObservation& out) noexcept {
 out=CameraOwnerObservation{};
 if(!base)return false;
 out.manager_pointer_read=safe_copy(&out.manager_pointer,reinterpret_cast<const void*>(base+CAMERA_MANAGER_RVA),sizeof(uint32_t));
 if(out.manager_pointer_read&&out.manager_pointer){
  out.manager_count_read=safe_copy(&out.manager_count,reinterpret_cast<const void*>(out.manager_pointer+0x10),sizeof(out.manager_count));
  out.manager_count_valid=out.manager_count_read&&out.manager_count>=0&&out.manager_count<=static_cast<int32_t>(out.manager_cameras.size());
  if(out.manager_count_valid){
   for(int32_t i=0;i<out.manager_count;++i){const auto index=static_cast<size_t>(i);
    out.manager_camera_read[index]=safe_copy(&out.manager_cameras[index],reinterpret_cast<const void*>(out.manager_pointer+static_cast<uintptr_t>(i)*4),sizeof(uint32_t));}
  }
 }
 uintptr_t global_renderer=0;
 out.renderer_pointer_read=safe_copy(&global_renderer,reinterpret_cast<const void*>(base+RENDERER_HOLDER_RVA),sizeof(uint32_t));
 if(out.renderer_pointer_read)out.renderer_pointer=global_renderer;
 if(out.renderer_pointer_read&&global_renderer){
  out.renderer_holder_read=safe_copy(&out.renderer_holder,reinterpret_cast<const void*>(global_renderer+0x38),sizeof(uint32_t));
  if(out.renderer_holder_read&&out.renderer_holder)
   out.current_camera_read=safe_copy(&out.current_camera,reinterpret_cast<const void*>(out.renderer_holder+4),sizeof(uint32_t));
 }
 if(out.current_camera_read&&out.current_camera&&out.manager_count_valid){
  for(int32_t i=0;i<out.manager_count;++i)if(out.manager_cameras[static_cast<size_t>(i)]==out.current_camera){out.camera_index=i;break;}
 }
 if(out.current_camera_read&&out.current_camera)
  out.camera_read=safe_copy(&out.camera,reinterpret_cast<const void*>(out.current_camera),sizeof(out.camera));
 return out.camera_read;
}

const char* camera_projection_family(const D3DMATRIX& projection) noexcept {
 if(!symmetric_lh(projection))return "non_perspective_or_unknown";
 const double angle=source_camera_angle(projection);
 if(std::abs(angle-45.0)<=SOURCE_CAMERA_TOLERANCE_DEGREES)return "source45";
 if(std::abs(angle-90.0)<=SOURCE_CAMERA_TOLERANCE_DEGREES)return "source90";
 return "other_perspective";
}

std::string camera_owner_observation_json(const CameraOwnerObservation& owner,uint64_t device,uint64_t frame,
 uint32_t caller_rva,const D3DMATRIX& requested_projection,const D3DMATRIX& effective_projection,
 const D3DMATRIX& view) {
 std::ostringstream out;
 out<<"{\"type\":\"camera_owner_observation\",\"schema\":1,\"read_only\":true,\"device\":"<<device
    <<",\"frame\":"<<frame<<",\"caller_va\":"<<quote([&](){std::ostringstream h;h<<"0x"<<std::hex<<std::setw(8)<<std::setfill('0')<<(0x00400000u+caller_rva);return h.str();}())
    <<",\"caller_rva\":"<<quote([&](){std::ostringstream h;h<<"0x"<<std::hex<<std::setw(8)<<std::setfill('0')<<caller_rva;return h.str();}())
    <<",\"projection_family\":"<<quote(camera_projection_family(requested_projection))
    <<",\"effective_projection_family\":"<<quote(camera_projection_family(effective_projection))
    <<",\"camera_manager\":{\"pointer\":";
 optional_pointer(out,owner.manager_pointer_read,owner.manager_pointer);
 out<<",\"pointer_read\":"<<(owner.manager_pointer_read?"true":"false")<<",\"count\":";if(owner.manager_count_read)out<<owner.manager_count;else out<<"null";
 out<<",\"count_read\":"<<(owner.manager_count_read?"true":"false")<<",\"count_valid\":"<<(owner.manager_count_valid?"true":"false")<<",\"cameras\":[";
 for(size_t i=0;i<owner.manager_cameras.size();++i){if(i)out<<',';if(owner.manager_camera_read[i])optional_pointer(out,true,owner.manager_cameras[i]);else out<<"null";}
 out<<"],\"camera_pointer_reads\":[";for(size_t i=0;i<owner.manager_camera_read.size();++i){if(i)out<<',';out<<(owner.manager_camera_read[i]?"true":"false");}out<<"]}"
    <<",\"renderer\":{\"singleton\":";optional_pointer(out,owner.renderer_pointer_read,owner.renderer_pointer);
 out<<",\"singleton_read\":"<<(owner.renderer_pointer_read?"true":"false");
 out<<",\"holder\":";optional_pointer(out,owner.renderer_holder_read,owner.renderer_holder);
 out<<",\"holder_read\":"<<(owner.renderer_holder_read?"true":"false");
 out<<",\"current_camera\":";optional_pointer(out,owner.current_camera_read,owner.current_camera);
 out<<",\"current_camera_read\":"<<(owner.current_camera_read?"true":"false")<<",\"camera_index\":"<<owner.camera_index
    <<",\"owner_match\":"<<(owner.camera_index>=0?"true":"false")<<",\"camera_read\":"<<(owner.camera_read?"true":"false")<<"}"
    <<",\"camera\":";
 if(owner.camera_read){
  out<<"{\"pointer\":"<<owner.current_camera<<",\"source_angle\":";
  if(std::isfinite(owner.camera.source_angle))out<<std::setprecision(9)<<owner.camera.source_angle;
  else out<<"null";
  out<<",\"flags\":"<<owner.camera.flags<<",\"viewport\":["<<owner.camera.x<<','<<owner.camera.y<<','<<owner.camera.width<<','<<owner.camera.height
     <<"],\"planes\":";float_array(out,owner.camera.planes);
  out<<",\"previous_pose\":";matrix(out,owner.camera.previous_pose.data());
  out<<",\"current_pose\":";matrix(out,owner.camera.pose.data());out<<",\"snap_frames\":"<<owner.camera.snap_frames<<'}';
 }else out<<"null";
 out<<",\"d3d_requested_projection\":";matrix(out,requested_projection);
 out<<",\"d3d_projection\":";matrix(out,effective_projection);out<<",\"d3d_view\":";matrix(out,view);
 out<<",\"projection_is_effective_native_state\":true,\"camera_memory_written\":false,\"new_game_hook_installed\":false}";
 return out.str();
}

}
