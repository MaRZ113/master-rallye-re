#pragma once
#include "visual_policy.hpp"
#include <array>
#include <cstdint>
namespace gfx2 {
inline constexpr uint32_t SUBMIT_CALL_RVA=0x002532DD, SUBMIT_OWNER_RVA=0x00109680;
inline constexpr uint32_t CAMERA_MANAGER_RVA=0x002F94DC, RENDERER_HOLDER_RVA=0x002F9CF0;
inline constexpr std::array<unsigned char,5> SUBMIT_CALL_BYTES={0xe8,0x9e,0x63,0xeb,0xff};
// No generic detour decoder: this exact instruction is one relative CALL.
struct PatchMemory {
 virtual bool read(void*,const void*,size_t) noexcept=0;
 virtual bool write(void*,const void*,size_t) noexcept=0;
 virtual bool protect(void*,size_t,DWORD,DWORD&) noexcept=0;
 virtual bool flush(void*,size_t) noexcept=0;
 virtual ~PatchMemory()=default;
};
class CallPatch {
 void* site_=nullptr;std::array<unsigned char,5> before_{},after_{};bool installed_=false;
 bool exchange(PatchMemory&,const std::array<unsigned char,5>&,const std::array<unsigned char,5>&) noexcept;
public:
 bool install(PatchMemory&,void* site,uintptr_t destination,const std::array<unsigned char,5>& expected) noexcept;
 bool remove(PatchMemory&) noexcept;
 bool installed() const noexcept{return installed_;}
 bool intact(PatchMemory& m) const noexcept {std::array<unsigned char,5> seen{};return installed_&&m.read(seen.data(),site_,5)&&seen==after_;}
};
struct CameraFrame {
 float source_angle=0;uint32_t flags=0;std::array<float,12> planes{};
 std::array<float,16> previous_pose{};
 int32_t x=0,y=0,width=0,height=0;
 std::array<float,16> pose{};uint32_t snap_frames=0;
};
static_assert(sizeof(CameraFrame)==0xcc&&offsetof(CameraFrame,planes)==8&&offsetof(CameraFrame,pose)==0x88,"pristine camera layout");
struct CameraSubmissionSnapshot {
 uintptr_t camera_pointer=0;uint32_t index=UINT32_MAX;CameraFrame camera{};
 bool available=false;const char* status="not_captured";
};
inline bool camera_submission_matches(const CameraSubmissionSnapshot& snapshot,uintptr_t camera) noexcept {
 return snapshot.available&&camera!=0&&snapshot.camera_pointer==camera;
}
struct FovCullStatus {
 bool installed=false,synchronized=false,restored=true;
 uint32_t width=0,height=0;float source=0,vfov=0,hfov=0;
 uint64_t synchronized_frames=0,failures=0;const char* reason="disabled";
};
// Outward normals in the game's camera convention (forward is -pose row 2).
bool effective_side_planes(const CameraFrame&,float vfov,std::array<float,12>& out,float& hfov) noexcept;
class FrustumFrame {
 CameraFrame* camera_=nullptr;CameraFrame snapshot_{};std::array<float,12> effective_{};
 std::array<float,16> effective_pose_{};bool owns_pose_=false;
public:
 FovCullStatus status;
 bool begin(CameraFrame*,float vfov,const std::array<float,16>* pose=nullptr) noexcept;
 bool matches(const CameraFrame*,const D3DMATRIX&) const noexcept;
 bool restore() noexcept;
 void abandon() noexcept {camera_=nullptr;status.synchronized=false;status.restored=false;++status.failures;status.reason="camera_identity_lost_no_stale_dereference";}
};
struct FlightState;
class GameFov {
 uintptr_t base_=0;DWORD thread_=0;float vfov_=0;bool enabled_=false;
 CallPatch patch_;FrustumFrame frame_;
 CallPatch completion_;FlightState* flight_=nullptr;unsigned scheduler_depth_=0;bool fov_enabled_=false;
 CameraSubmissionSnapshot submission_{};
public:
 GameFov()=default;~GameFov();GameFov(const GameFov&)=delete;GameFov& operator=(const GameFov&)=delete;
 bool install(bool exact,const VisualConfig&,HWND window=nullptr,bool exact_retail=false) noexcept;
 void disable(const char* reason) noexcept;
 void before_submit(unsigned index) noexcept;
 void submission_snapshot(uintptr_t expected_camera,CameraSubmissionSnapshot& out) const noexcept;
 bool allows(const D3DMATRIX&) const noexcept;
 void finish_frame() noexcept;
 void cancel_frame() noexcept;
 void cancel_lifecycle(const char* reason) noexcept;
 void scheduler_begin() noexcept;
 void scheduler_end() noexcept;
 void stock_view(const D3DMATRIX&) noexcept;
 bool free_camera_configured() const noexcept;
 bool free_camera_active() const noexcept;
 std::string camera_json() const;
 FovCullStatus status() const noexcept{return frame_.status;}
};
namespace camera_bridge {
 struct Saved {uint32_t edi,esi,ebp,esp,ebx,edx,ecx,eax,flags,return_pc,args[1];};
 using Callback=void(__stdcall*)(uint32_t,const Saved*);
 extern Callback callback;extern uintptr_t scheduler_original;void scheduler();
}
std::string free_camera_snapshot_json();
}
