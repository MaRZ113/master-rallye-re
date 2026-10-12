#include "camera_bookmarks.hpp"
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;

namespace {
std::array<float,16> pose_at(float x,float y,float z){return {1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1};}
std::array<float,16> banked_pose(float x,float y,float z,double degrees){double a=degrees*3.14159265358979323846/180.;float c=static_cast<float>(std::cos(a)),s=static_cast<float>(std::sin(a));return {c,s,0,0,-s,c,0,0,0,0,1,0,x,y,z,1};}
FreeCameraConfig config(){return parse_free_camera_config({{"FreeCamera.Enabled","1"},{"FreeCamera.InheritStockFOVOnToggle","0"},{"FreeCamera.CinematicVerticalFOVDegrees","60"},{"FreeCamera.FOVSmoothSeconds","0"},{"FreeCamera.RollSmoothSeconds","0"},{"FreeCamera.MovementSmoothSeconds","0"}});}
void activate(FlightController& c,const FreeCameraConfig& cfg,const std::array<float,16>& p){FlightInput i;i.focused=true;CHECK(!c.update(cfg,i,true,&p));i.toggle=true;CHECK(c.update(cfg,i,true,&p));}
CameraBookmark record(unsigned slot,const FlightBookmarkPose& pose){CameraBookmark b;b.present=true;b.slot=slot;b.label="Bookmark "+std::to_string(slot);b.saved_at_utc="2026-10-11T12:34:56.789Z";b.camera=pose;return b;}
std::string read_bytes(const std::wstring& path){HANDLE h=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);CHECK(h!=INVALID_HANDLE_VALUE);LARGE_INTEGER n{};CHECK(GetFileSizeEx(h,&n)&&n.QuadPart>=0&&n.QuadPart<=32768);std::string b(static_cast<size_t>(n.QuadPart),'\0');DWORD got=0;bool okay=ReadFile(h,b.data(),static_cast<DWORD>(b.size()),&got,nullptr)&&got==b.size();CloseHandle(h);CHECK(okay);return b;}
void write_bytes(const std::wstring& path,const std::string& bytes){HANDLE h=CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);CHECK(h!=INVALID_HANDLE_VALUE);DWORD put=0;bool okay=WriteFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),&put,nullptr)&&put==bytes.size();CloseHandle(h);CHECK(okay);}

void controller_roundtrip(FlightBookmarkPose& pose){
 auto cfg=config();auto stock=pose_at(10,20,30);FlightController source;activate(source,cfg,stock);
 FlightInput i;i.focused=true;i.seconds=.05;i.roll_left=true;i.fov_increase=true;i.keys[0]=true;i.mouse_x=5;i.mouse_y=-2;
 CHECK(source.update(cfg,i,true,&stock));i.roll_left=false;i.fov_increase=false;i.mouse_x=0;i.mouse_y=0;i.keys={};CHECK(source.update(cfg,i,true,&stock));
 CHECK(source.manual_roll_degrees>0);CHECK(source.current_vertical_fov()==65);CHECK(source.pose[14]<stock[14]);
 CHECK(source.capture_bookmark(pose,cfg));CHECK(pose.visible_pose==source.pose&&pose.orientation!=pose.visible_pose);

 FlightController restored;auto unrelated=pose_at(-100,7,42);activate(restored,cfg,unrelated);FlightInput increase;increase.focused=true;increase.speed_increase=true;CHECK(restored.update(cfg,increase,true,&unrelated));double selected_speed=restored.current_speed();
 CHECK(restored.restore_bookmark(pose,cfg));CHECK(restored.pose==pose.visible_pose&&std::abs(restored.current_vertical_fov()-pose.current_vfov)<1e-9);
 CHECK(std::abs(restored.manual_roll_degrees-pose.manual_roll)<1e-4&&std::abs(restored.manual_roll_target_degrees-pose.manual_roll_target)<1e-4);
 CHECK(restored.velocity_magnitude()==0&&restored.current_speed()==selected_speed);
 FlightBookmarkPose immediate{};CHECK(restored.capture_bookmark(immediate,cfg));CHECK(immediate.visible_pose==pose.visible_pose&&immediate.orientation==pose.orientation);
 // The first post-load controller sample suppresses stale input and elapsed time.
 FlightInput stale;stale.focused=true;stale.seconds=.05;stale.mouse_x=200;stale.keys[0]=true;stale.roll_right=true;stale.fov_decrease=true;
 CHECK(restored.update(cfg,stale,true,&unrelated));CHECK(restored.pose==pose.visible_pose&&restored.velocity_magnitude()==0);
 CHECK(std::abs(restored.manual_roll_degrees-pose.manual_roll)<1e-4&&std::abs(restored.current_vertical_fov()-pose.current_vfov)<1e-9);
 auto invalid=pose;invalid.visible_pose[0]=2.f;const auto before_invalid=restored.pose;CHECK(!restored.restore_bookmark(invalid,cfg)&&restored.pose==before_invalid);
 auto no_lens=cfg;no_lens.cinematic_fov_enabled=false;FlightController guarded_lens;activate(guarded_lens,no_lens,unrelated);auto before_lens=guarded_lens.pose;CHECK(!guarded_lens.restore_bookmark(pose,no_lens)&&guarded_lens.pose==before_lens);
 auto no_roll=cfg;no_roll.manual_roll_enabled=false;FlightController guarded_roll;activate(guarded_roll,no_roll,unrelated);auto before_roll=guarded_roll.pose;CHECK(!guarded_roll.restore_bookmark(pose,no_roll)&&guarded_roll.pose==before_roll);
}
void roll_signs_and_vertical(){
 auto cfg=config();cfg.roll_smooth_seconds=0;cfg.auto_level_horizon=false;
 auto stock=pose_at(1,2,3);FlightController negative;activate(negative,cfg,stock);FlightInput roll;roll.focused=true;roll.seconds=.1;roll.roll_right=true;CHECK(negative.update(cfg,roll,true,&stock));
 CHECK(negative.manual_roll_degrees<0);FlightBookmarkPose saved{};CHECK(negative.capture_bookmark(saved,cfg)&&saved.manual_roll<0);
 FlightController restored;auto other=pose_at(-20,0,40);activate(restored,cfg,other);CHECK(restored.restore_bookmark(saved,cfg));CHECK(restored.manual_roll_degrees<0);
 FlightController vertical;activate(vertical,cfg,stock);FlightInput look;look.focused=true;look.seconds=.016;look.mouse_y=1000;CHECK(vertical.update(cfg,look,true,&stock));
 CHECK(vertical.capture_bookmark(saved,cfg));FlightController vertical_restore;activate(vertical_restore,cfg,other);CHECK(vertical_restore.restore_bookmark(saved,cfg));
 CHECK(vertical_restore.pose==saved.visible_pose);
}
void settle_transitions(){
 auto cfg=config();cfg.fov_smooth_seconds=.25f;cfg.roll_smooth_seconds=.10f;cfg.horizon_level_seconds=.30f;
 auto stock=banked_pose(4,5,6,32);FlightController source;activate(source,cfg,stock);
 FlightInput moving;moving.focused=true;moving.seconds=.05;moving.roll_left=true;CHECK(source.update(cfg,moving,true,&stock));
 CHECK(source.horizon_leveling_active&&source.fov_transition_active()&&source.manual_roll_transition_active);
 FlightBookmarkPose bookmark{};CHECK(source.capture_bookmark(bookmark,cfg));
 CHECK(!bookmark.horizon_leveling_active&&bookmark.horizon_level_progress==1.f&&bookmark.previous_horizon_progress==1.);
 CHECK(bookmark.manual_roll==bookmark.manual_roll_target&&bookmark.current_vfov==bookmark.target_vfov);
 FlightController restored;auto unrelated=pose_at(-100,7,42);activate(restored,cfg,unrelated);CHECK(restored.restore_bookmark(bookmark,cfg));
 const auto exact_pose=restored.pose;const auto exact_fov=restored.current_vertical_fov();const auto exact_roll=restored.manual_roll_degrees;
 FlightInput idle;idle.focused=true;idle.seconds=.05;CHECK(restored.update(cfg,idle,true,&unrelated));
 idle.seconds=.016;CHECK(restored.update(cfg,idle,true,&unrelated));
 CHECK(restored.pose==exact_pose&&restored.current_vertical_fov()==exact_fov&&restored.manual_roll_degrees==exact_roll);
}
void serialization(){
 FlightBookmarkPose pose{};controller_roundtrip(pose);
 CameraBookmarkSet input;input.slots[0]=record(1,pose);auto second=record(2,pose);second.camera.visible_pose[12]+=3;second.camera.orientation[12]+=3;input.slots[1]=second;
 std::string text;CHECK(serialize_camera_bookmarks(input,text));CHECK(text.size()<16*1024);CHECK(text.find(CAMERA_BOOKMARK_BUILD_SHA256)!=std::string::npos&&text.find(CAMERA_BOOKMARK_COURSE_ID)!=std::string::npos);
 CHECK(text.find("CameraFrame")==std::string::npos&&text.find("scheduler_generation")==std::string::npos&&text.find("owner_lifetime")==std::string::npos&&text.find("process_id")==std::string::npos);
 CameraBookmarkSet parsed;CHECK(parse_camera_bookmarks(text,parsed));CHECK(parsed.slots[0].present&&parsed.slots[1].present&&!parsed.slots[2].present);
 CHECK(parsed.slots[0].camera.visible_pose==pose.visible_pose&&parsed.slots[0].camera.orientation==pose.orientation);
 CHECK(parsed.slots[0].camera.horizon_right==pose.horizon_right&&parsed.slots[0].camera.manual_roll==pose.manual_roll&&parsed.slots[0].camera.target_vfov==pose.target_vfov);
 CHECK(parsed.slots[1].camera.visible_pose[12]==pose.visible_pose[12]+3);
 std::string bad=text;auto schema=bad.find("\"schema_version\":1");CHECK(schema!=std::string::npos);bad.replace(schema,std::strlen("\"schema_version\":1"),"\"schema_version\":2");CHECK(!parse_camera_bookmarks(bad,parsed));
 bad=text;auto course=bad.find(CAMERA_BOOKMARK_COURSE_ID);CHECK(course!=std::string::npos);bad.replace(course,std::strlen(CAMERA_BOOKMARK_COURSE_ID),"RaceTest/Other");CHECK(!parse_camera_bookmarks(bad,parsed));
 bad=text;bad.insert(bad.find("\"format\""),"\"unexpected\":true,");CHECK(!parse_camera_bookmarks(bad,parsed));
 bad=text;auto matrix=bad.find("\"visible_pose\":[");CHECK(matrix!=std::string::npos);auto first_value=matrix+std::strlen("\"visible_pose\":[");auto value_end=bad.find(',',first_value);CHECK(value_end!=std::string::npos);bad.replace(first_value,value_end-first_value,"NaN");CHECK(!parse_camera_bookmarks(bad,parsed));
 auto invalid=input;invalid.slots[0].camera.visible_pose[0]=std::numeric_limits<float>::quiet_NaN();CHECK(!serialize_camera_bookmarks(invalid,bad));
}
void persistent_store(){
 wchar_t dir[MAX_PATH]{},name[MAX_PATH]{};CHECK(GetTempPathW(MAX_PATH,dir)&&GetTempFileNameW(dir,L"mrb",0,name));CHECK(DeleteFileW(name));std::wstring path=name;
 struct Cleanup{std::wstring path;~Cleanup(){DeleteFileW(path.c_str());}} cleanup{path};
 FlightBookmarkPose pose{};controller_roundtrip(pose);CameraBookmarkSet in_memory;
 CameraBookmarkSet absent;absent.slots[0].present=true;CHECK(read_camera_bookmarks(path,absent)==CameraBookmarkIo::missing&&!absent.slots[0].present);
 auto one=record(1,pose);CHECK(save_camera_bookmark(path,1,one,in_memory)==CameraBookmarkIo::ok);
 CameraBookmarkSet fresh_process;CHECK(read_camera_bookmarks(path,fresh_process)==CameraBookmarkIo::ok&&fresh_process.slots[0].present&&!fresh_process.slots[1].present);
 auto two=record(2,pose);two.camera.visible_pose[12]+=5;two.camera.orientation[12]+=5;CHECK(save_camera_bookmark(path,2,two,in_memory)==CameraBookmarkIo::ok);
 auto three=record(3,pose);three.camera.visible_pose[14]-=8;three.camera.orientation[14]-=8;CHECK(save_camera_bookmark(path,3,three,in_memory)==CameraBookmarkIo::ok);
 CameraBookmarkSet cross_restart;CHECK(read_camera_bookmarks(path,cross_restart)==CameraBookmarkIo::ok&&cross_restart.slots[0].present&&cross_restart.slots[1].present&&cross_restart.slots[2].present);
 auto update=record(2,pose);update.camera.visible_pose[12]+=11;update.camera.orientation[12]+=11;CHECK(save_camera_bookmark(path,2,update,in_memory)==CameraBookmarkIo::ok);
 CameraBookmarkSet merged;CHECK(read_camera_bookmarks(path,merged)==CameraBookmarkIo::ok&&merged.slots[0].present&&merged.slots[2].present&&merged.slots[1].camera.visible_pose[12]==pose.visible_pose[12]+11);
 const auto original=read_bytes(path);write_bytes(path,"{malformed");const auto malformed=read_bytes(path);CHECK(save_camera_bookmark(path,1,one,in_memory)==CameraBookmarkIo::invalid);CHECK(read_bytes(path)==malformed);CHECK(original!=malformed);
 write_bytes(path,std::string(16*1024+1,'x'));const auto oversized=read_bytes(path);CameraBookmarkSet rejected;CHECK(read_camera_bookmarks(path,rejected)==CameraBookmarkIo::invalid);CHECK(save_camera_bookmark(path,1,one,in_memory)==CameraBookmarkIo::invalid);CHECK(read_bytes(path)==oversized);
 std::wstring blocked=path+L".blocked";write_bytes(blocked,"parent-file");struct CleanupBlocked{std::wstring path;~CleanupBlocked(){DeleteFileW(path.c_str());}} cleanup_blocked{blocked};
 CHECK(save_camera_bookmark(blocked+L"\\child.json",1,one,in_memory)==CameraBookmarkIo::path_unavailable);CHECK(read_bytes(blocked)=="parent-file");
}
}
int main(){try{serialization();settle_transitions();roll_signs_and_vertical();persistent_store();std::cout<<"camera bookmark controller, roll signs, vertical pose, stable transitions, schema, identity, and persistence contracts passed\n";return 0;}catch(const std::exception& e){std::cerr<<"camera bookmark contract failure: "<<e.what()<<'\n';return 1;}}
