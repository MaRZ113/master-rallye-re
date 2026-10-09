#include "camera_probe.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

using namespace gfx2;
namespace {
int failures=0;
#define CHECK(x) do {if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "<<#x<<'\n';++failures;}} while(0)
D3DMATRIX perspective(double authored,double aspect) {
 D3DMATRIX p{};const double vfov=authored/std::max(1.0,aspect);
 p._22=static_cast<float>(1.0/std::tan(vfov*3.14159265358979323846/360.));
 p._11=static_cast<float>(p._22/aspect);p._33=1.0002f;p._34=1.f;p._43=-.20004f;return p;
}
void identity(std::array<float,16>& m){m={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};}
CameraProbeGateInput eligible_input(D3DTRANSFORMSTATETYPE type=D3DTS_VIEW,uint32_t rva=GAMEPLAY_VIEW_RETURN_RVA) {
 CameraProbeGateInput in{};in.transform_type=type;in.exe_caller=true;in.caller_rva=rva;in.native_result=S_OK;
 in.trace_enabled=true;in.capture_active=true;in.profile_supported=true;
 in.requested_projection_known=in.effective_projection_known=true;
 in.requested_projection=in.effective_projection=perspective(90.,16./9.);return in;
}
struct NativeRecorder {
 unsigned calls=0,scene_draws=0;D3DTRANSFORMSTATETYPE last_type=D3DTS_WORLD;const D3DMATRIX* last_matrix=nullptr;HRESULT result=S_OK;
 HRESULT set_transform(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* matrix){++calls;last_type=type;last_matrix=matrix;return result;}
 void draw_scene(){++scene_draws;}
};
}
int main(int argc,char** argv){
 const auto race=perspective(90.,16./9.);const auto preview=perspective(45.,4./3.);const auto other=perspective(70.,16./9.);
 CHECK(std::strcmp(camera_projection_family(race),"source90")==0);
 CHECK(std::strcmp(camera_projection_family(preview),"source45")==0);
 CHECK(std::strcmp(camera_projection_family(other),"other_perspective")==0);
 D3DMATRIX ortho{};ortho._11=2.f/640;ortho._22=2.f/480;ortho._44=1;
 CHECK(std::strcmp(camera_projection_family(ortho),"non_perspective_or_unknown")==0);

 // Exercise the production eligibility helper against the distinct captured sites.
 auto in=eligible_input(D3DTS_PROJECTION,GAMEPLAY_PROJECTION_RETURN_RVA);
 auto gate=camera_probe_gate(in);CHECK(!gate.gameplay_view_site&&gate.status==CameraProbeStatus::NoVerifiedGameplayViewSite);
 in=eligible_input(D3DTS_VIEW,GAMEPLAY_PROJECTION_RETURN_RVA); // Regression: VIEW at the old projection RVA is never required.
 gate=camera_probe_gate(in);CHECK(!gate.gameplay_view_site&&gate.status==CameraProbeStatus::NoVerifiedGameplayViewSite);
 in=eligible_input();gate=camera_probe_gate(in);CHECK(gate.gameplay_view_site&&gate.status==CameraProbeStatus::ReadyForObservation);
 in.requested_projection=in.effective_projection=preview;gate=camera_probe_gate(in);
 CHECK(gate.gameplay_view_site&&gate.status==CameraProbeStatus::ReadyForObservation);
 in=eligible_input(D3DTS_VIEW,0x00161FDC);in.requested_projection=in.effective_projection=ortho;
 gate=camera_probe_gate(in);CHECK(!gate.gameplay_view_site&&gate.status==CameraProbeStatus::NoVerifiedGameplayViewSite);
 in=eligible_input(D3DTS_PROJECTION,0x00161ED3);gate=camera_probe_gate(in);CHECK(!gate.gameplay_view_site);
 in=eligible_input();in.exe_caller=false;gate=camera_probe_gate(in);CHECK(!gate.gameplay_view_site);
 in=eligible_input();in.caller_rva=0x00161A27;gate=camera_probe_gate(in);CHECK(!gate.gameplay_view_site);
 in=eligible_input();in.native_result=D3DERR_INVALIDCALL;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::NativeSetTransformFailed);
 in=eligible_input();in.capture_active=false;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::CaptureInactive);
 in=eligible_input();in.trace_enabled=false;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::TraceDisabled);
 in=eligible_input();in.profile_supported=false;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::ExecutableProfileUnsupported);
 in=eligible_input();in.requested_projection_known=false;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::ProjectionUnavailable);
 in=eligible_input();in.effective_projection_known=false;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::ProjectionUnavailable);
 in=eligible_input();in.requested_projection=ortho;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::ProjectionIneligible);
 in=eligible_input();in.observation_already_claimed=true;gate=camera_probe_gate(in);CHECK(gate.status==CameraProbeStatus::DuplicateSuppressed);

 CameraOwnerObservation owner{};owner.manager_pointer_read=owner.manager_count_read=owner.manager_count_valid=true;owner.manager_pointer=0x10001000;owner.manager_count=1;
 owner.manager_cameras[0]=0x12345678;owner.manager_camera_read[0]=true;owner.renderer_pointer_read=owner.renderer_holder_read=owner.current_camera_read=true;
 owner.renderer_pointer=0x20002000;owner.renderer_holder=0x30003000;owner.current_camera=owner.manager_cameras[0];
 owner.camera_index=0;owner.camera_read=true;owner.camera.source_angle=90.f;owner.camera.flags=1;
 owner.camera.x=0;owner.camera.y=0;owner.camera.width=1920;owner.camera.height=1080;identity(owner.camera.pose);identity(owner.camera.previous_pose);
 std::array<float,12> planes{};planes={0,1,0,0,-1,0,1,0,0,-1,0,0};owner.camera.planes=planes;
 D3DMATRIX view{};view._11=view._22=view._33=view._44=1.f;
 const auto effective_fov=perspective(75.,16./9.);
 const auto json=camera_owner_observation_json(owner,7,42,GAMEPLAY_VIEW_RETURN_RVA,race,effective_fov,view);
 CHECK(json.find("\"type\":\"camera_owner_observation\"")!=std::string::npos);
 CHECK(json.find("\"projection_family\":\"source90\"")!=std::string::npos);
 CHECK(json.find("\"effective_projection_family\":\"other_perspective\"")!=std::string::npos);
 CHECK(json.find("\"d3d_requested_projection\":{\"values\"")!=std::string::npos);
 CHECK(json.find("\"caller_va\":\"0x00561a26\"")!=std::string::npos);
 CHECK(json.find("\"owner_match\":true")!=std::string::npos);
 CHECK(json.find("\"count_valid\":true")!=std::string::npos);
 CHECK(json.find("\"singleton_read\":true")!=std::string::npos);
 CHECK(json.find("\"camera_index\":0")!=std::string::npos);
 CHECK(json.find("\"camera_memory_written\":false")!=std::string::npos);
 CHECK(json.find("\"new_game_hook_installed\":false")!=std::string::npos);
 CHECK(json.find("\"projection_is_effective_native_state\":true")!=std::string::npos);
 CHECK(json.find("\"frame\":42")!=std::string::npos&&json.find("\"device\":7")!=std::string::npos);
 CHECK(json.find("\"caller_rva\":\"0x00161a26\"")!=std::string::npos);
 CHECK(camera_owner_reads_complete(owner));
 const auto preview_json=camera_owner_observation_json(owner,7,42,GAMEPLAY_VIEW_RETURN_RVA,preview,preview,view);
 CHECK(preview_json.find("\"projection_family\":\"source45\"")!=std::string::npos);

 // Synthetic captured order: game projection, game VIEW, scene, UI projection, UI VIEW.
 NativeRecorder native;CameraProbeFrameDiagnostic diagnostic;std::vector<std::string> observations;
 const auto submit=[&](D3DTRANSFORMSTATETYPE type,uint32_t rva,const D3DMATRIX* matrix,const D3DMATRIX& logical,const D3DMATRIX& effective){
  const HRESULT hr=native.set_transform(type,matrix);auto event=eligible_input(type,rva);event.native_result=hr;
  event.requested_projection=logical;event.effective_projection=effective;
  event.observation_already_claimed=diagnostic.observation_claimed;
  const auto decision=camera_probe_gate(event);diagnostic.record_gate(decision,rva);
  if(decision.status==CameraProbeStatus::ReadyForObservation&&diagnostic.claim_observation()){
   CameraOwnerObservation partial{};CHECK(!read_camera_owner_observation(0,partial));
   const bool reads_complete=camera_owner_reads_complete(partial);
   observations.push_back(camera_owner_observation_json(partial,3,99,rva,logical,effective,*matrix));
   diagnostic.record_outcome(CameraProbeStatus::OwnerReadIncomplete,true,true,reads_complete);
  }
 };
 D3DMATRIX game_view=view,ui_view=view;
 submit(D3DTS_PROJECTION,GAMEPLAY_PROJECTION_RETURN_RVA,&race,race,race);
 submit(D3DTS_VIEW,GAMEPLAY_VIEW_RETURN_RVA,&game_view,race,race);
 submit(D3DTS_VIEW,GAMEPLAY_VIEW_RETURN_RVA,&game_view,race,race); // duplicate in the same device/frame
 native.draw_scene(); // Scene draws separate the gameplay camera from the UI transforms.
 submit(D3DTS_PROJECTION,0x00161ED3,&ortho,ortho,ortho);
 submit(D3DTS_VIEW,0x00161FDC,&ui_view,ortho,ortho);
 CHECK(native.calls==5&&native.scene_draws==1&&native.last_type==D3DTS_VIEW&&native.last_matrix==&ui_view);
 CHECK(observations.size()==1);
 CHECK(observations[0].find("\"caller_rva\":\"0x00161a26\"")!=std::string::npos);
 CHECK(observations[0].find("\"projection_family\":\"source90\"")!=std::string::npos);
 CHECK(observations[0].find("\"device\":3")!=std::string::npos&&observations[0].find("\"frame\":99")!=std::string::npos);
 CHECK(observations[0].find("\"owner_match\":false")!=std::string::npos);
 CHECK(observations[0].find("\"camera\":null")!=std::string::npos);
 CHECK(diagnostic.gameplay_view_site_seen&&diagnostic.observation_claimed&&diagnostic.observation_emitted);
 CHECK(diagnostic.status==CameraProbeStatus::DuplicateSuppressed&&diagnostic.duplicate_suppressed==1);
 const auto status_json=camera_probe_frame_summary_json(diagnostic);
 CHECK(status_json.find("\"status\":\"duplicate_observation_suppressed\"")!=std::string::npos);
 CHECK(status_json.find("\"owner_reads_complete\":false")!=std::string::npos);

 // Synthetic D3D forwarding remains one-for-one for the captured sequence.
 NativeRecorder failed_native;failed_native.result=D3DERR_INVALIDCALL;
 CHECK(failed_native.set_transform(D3DTS_VIEW,&view)==D3DERR_INVALIDCALL);
 CHECK(failed_native.calls==1&&failed_native.last_matrix==&view&&failed_native.last_type==D3DTS_VIEW);

 owner.camera_index=-1;const auto unmatched=camera_owner_observation_json(owner,7,43,GAMEPLAY_VIEW_RETURN_RVA,race,race,view);
 CHECK(unmatched.find("\"owner_match\":false")!=std::string::npos);
 owner.manager_count=7;owner.manager_count_valid=false;
 const auto invalid_count=camera_owner_observation_json(owner,7,44,GAMEPLAY_VIEW_RETURN_RVA,race,race,view);
 CHECK(invalid_count.find("\"count\":7")!=std::string::npos);
 CHECK(invalid_count.find("\"count_valid\":false")!=std::string::npos);
 owner.camera.source_angle=NAN;
 const auto nonfinite_angle=camera_owner_observation_json(owner,7,45,GAMEPLAY_VIEW_RETURN_RVA,race,race,view);
 CHECK(nonfinite_angle.find("\"source_angle\":null")!=std::string::npos);
 view._41=NAN;const auto nonfinite=camera_owner_observation_json(owner,7,46,GAMEPLAY_VIEW_RETURN_RVA,race,race,view);
 CHECK(nonfinite.find("nan")==std::string::npos&&nonfinite.find("\"d3d_view\":{\"values\":[1,0,0,0,0,1,0,0,0,0,1,0,null")!=std::string::npos);
 if(failures){std::cerr<<failures<<" camera probe contract(s) failed\n";return 1;}
 if(argc==2&&std::string(argv[1])=="--emit-sequence-json"){std::cout<<observations.front()<<'\n';return 0;}
 if(argc==2&&std::string(argv[1])=="--emit-json"){std::cout<<json<<'\n';return 0;}
 std::cout<<"camera probe contracts passed\n";return 0;
}
