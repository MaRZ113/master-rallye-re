#pragma once
#include "visual_policy.hpp"
#include <array>
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
};
struct CameraFrame {
 float source_angle=0;uint32_t flags=0;std::array<float,12> planes{};
 std::array<float,16> previous_pose{};
 int32_t x=0,y=0,width=0,height=0;
 std::array<float,16> pose{};uint32_t snap_frames=0;
};
static_assert(sizeof(CameraFrame)==0xcc&&offsetof(CameraFrame,planes)==8&&offsetof(CameraFrame,pose)==0x88,"pristine camera layout");
struct FovCullStatus {
 bool installed=false,synchronized=false,restored=true;
 uint32_t width=0,height=0;float source=0,vfov=0,hfov=0;
 uint64_t synchronized_frames=0,failures=0;const char* reason="disabled";
};
// Outward normals in the game's camera convention (forward is -pose row 2).
bool effective_side_planes(const CameraFrame&,float vfov,std::array<float,12>& out,float& hfov) noexcept;
class FrustumFrame {
 CameraFrame* camera_=nullptr;CameraFrame snapshot_{};std::array<float,12> effective_{};
public:
 FovCullStatus status;
 bool begin(CameraFrame*,float vfov) noexcept;
 bool matches(const CameraFrame*,const D3DMATRIX&) const noexcept;
 bool restore() noexcept;
};
class GameFov {
 uintptr_t base_=0;DWORD thread_=0;float vfov_=0;bool enabled_=false;
 CallPatch patch_;FrustumFrame frame_;
public:
 GameFov()=default;~GameFov();GameFov(const GameFov&)=delete;GameFov& operator=(const GameFov&)=delete;
 bool install(bool exact,const VisualConfig&) noexcept;
 void disable(const char* reason) noexcept;
 void before_submit(unsigned index) noexcept;
 bool allows(const D3DMATRIX&) const noexcept;
 void finish_frame() noexcept;
 FovCullStatus status() const noexcept{return frame_.status;}
};
}
