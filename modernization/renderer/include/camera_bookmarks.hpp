#pragma once
#include "free_camera.hpp"
#include <array>
#include <string>
#include <string_view>

namespace gfx2 {
inline constexpr size_t CAMERA_BOOKMARK_SLOT_COUNT=3;
inline constexpr unsigned CAMERA_BOOKMARK_SCHEMA_VERSION=1;
inline constexpr char CAMERA_BOOKMARK_BUILD_SHA256[]="bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4";
inline constexpr char CAMERA_BOOKMARK_COURSE_ID[]="RaceTest/France1";

struct CameraBookmark {
 bool present=false;
 unsigned slot=0;
 std::string label,saved_at_utc;
 FlightBookmarkPose camera{};
};
struct CameraBookmarkSet {std::array<CameraBookmark,CAMERA_BOOKMARK_SLOT_COUNT> slots{};};
enum class CameraBookmarkIo {ok,missing,invalid,identity_mismatch,io_error,path_unavailable};

bool valid_camera_bookmark(const CameraBookmark&,unsigned expected_slot) noexcept;
bool serialize_camera_bookmarks(const CameraBookmarkSet&,std::string&) noexcept;
bool parse_camera_bookmarks(std::string_view,CameraBookmarkSet&) noexcept;
CameraBookmarkIo read_camera_bookmarks(const std::wstring& path,CameraBookmarkSet&) noexcept;
CameraBookmarkIo save_camera_bookmark(const std::wstring& path,unsigned slot,const CameraBookmark&,CameraBookmarkSet&) noexcept;
std::wstring default_camera_bookmark_path() noexcept;
bool ensure_camera_bookmark_directory() noexcept;
bool current_utc_timestamp(std::string&) noexcept;
const char* camera_bookmark_io_name(CameraBookmarkIo) noexcept;
}
