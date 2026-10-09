#include "camera_probe.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <string>

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
}
int main(int argc,char** argv){
 const auto race=perspective(90.,16./9.);const auto preview=perspective(45.,4./3.);const auto other=perspective(70.,16./9.);
 CHECK(std::strcmp(camera_projection_family(race),"source90")==0);
 CHECK(std::strcmp(camera_projection_family(preview),"source45")==0);
 CHECK(std::strcmp(camera_projection_family(other),"other_perspective")==0);
 D3DMATRIX ortho{};ortho._11=2.f/640;ortho._22=2.f/480;ortho._44=1;
 CHECK(std::strcmp(camera_projection_family(ortho),"non_perspective_or_unknown")==0);

 CameraOwnerObservation owner{};owner.manager_pointer_read=owner.manager_count_read=owner.manager_count_valid=true;owner.manager_pointer=0x10001000;owner.manager_count=1;
 owner.manager_cameras[0]=0x12345678;owner.renderer_pointer_read=owner.renderer_holder_read=owner.current_camera_read=true;
 owner.renderer_pointer=0x20002000;owner.renderer_holder=0x30003000;owner.current_camera=owner.manager_cameras[0];
 owner.camera_index=0;owner.camera_read=true;owner.camera.source_angle=90.f;owner.camera.flags=1;
 owner.camera.x=0;owner.camera.y=0;owner.camera.width=1920;owner.camera.height=1080;identity(owner.camera.pose);identity(owner.camera.previous_pose);
 std::array<float,12> planes{};planes={0,1,0,0,-1,0,1,0,0,-1,0,0};owner.camera.planes=planes;
 D3DMATRIX view{};view._11=view._22=view._33=view._44=1.f;
 const auto effective_fov=perspective(75.,16./9.);
 const auto json=camera_owner_observation_json(owner,7,42,GAMEPLAY_PROJECTION_RETURN_RVA,race,effective_fov,view);
 CHECK(json.find("\"type\":\"camera_owner_observation\"")!=std::string::npos);
 CHECK(json.find("\"projection_family\":\"source90\"")!=std::string::npos);
 CHECK(json.find("\"effective_projection_family\":\"other_perspective\"")!=std::string::npos);
 CHECK(json.find("\"d3d_requested_projection\":{\"values\"")!=std::string::npos);
 CHECK(json.find("\"caller_va\":\"0x0053fa75\"")!=std::string::npos);
 CHECK(json.find("\"owner_match\":true")!=std::string::npos);
 CHECK(json.find("\"count_valid\":true")!=std::string::npos);
 CHECK(json.find("\"singleton_read\":true")!=std::string::npos);
 CHECK(json.find("\"camera_index\":0")!=std::string::npos);
 CHECK(json.find("\"camera_memory_written\":false")!=std::string::npos);
 CHECK(json.find("\"new_game_hook_installed\":false")!=std::string::npos);
 CHECK(json.find("\"projection_is_effective_native_state\":true")!=std::string::npos);
 CHECK(json.find("\"frame\":42")!=std::string::npos&&json.find("\"device\":7")!=std::string::npos);
 CHECK(json.find("\"caller_rva\":\"0x0013fa75\"")!=std::string::npos);

 owner.camera_index=-1;const auto unmatched=camera_owner_observation_json(owner,7,43,GAMEPLAY_PROJECTION_RETURN_RVA,race,race,view);
 CHECK(unmatched.find("\"owner_match\":false")!=std::string::npos);
 owner.manager_count=7;owner.manager_count_valid=false;
 const auto invalid_count=camera_owner_observation_json(owner,7,44,GAMEPLAY_PROJECTION_RETURN_RVA,race,race,view);
 CHECK(invalid_count.find("\"count\":7")!=std::string::npos);
 CHECK(invalid_count.find("\"count_valid\":false")!=std::string::npos);
 owner.camera.source_angle=NAN;
 const auto nonfinite_angle=camera_owner_observation_json(owner,7,45,GAMEPLAY_PROJECTION_RETURN_RVA,race,race,view);
 CHECK(nonfinite_angle.find("\"source_angle\":null")!=std::string::npos);
 view._41=NAN;const auto nonfinite=camera_owner_observation_json(owner,7,46,GAMEPLAY_PROJECTION_RETURN_RVA,race,race,view);
 CHECK(nonfinite.find("nan")==std::string::npos&&nonfinite.find("\"d3d_view\":{\"values\":[1,0,0,0,0,1,0,0,0,0,1,0,null")!=std::string::npos);
 if(failures){std::cerr<<failures<<" camera probe contract(s) failed\n";return 1;}
 if(argc==2&&std::string(argv[1])=="--emit-json"){std::cout<<json<<'\n';return 0;}
 std::cout<<"camera probe contracts passed\n";return 0;
}
