#include "camera_bookmarks.hpp"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <iomanip>
#include <limits>
#include <locale>
#include <sstream>
#include <vector>

namespace gfx2 {
namespace {
constexpr size_t MAX_BOOKMARK_FILE=16*1024;
struct Handle {HANDLE value=INVALID_HANDLE_VALUE;~Handle(){if(value!=INVALID_HANDLE_VALUE)CloseHandle(value);}void close() noexcept {if(value!=INVALID_HANDLE_VALUE){CloseHandle(value);value=INVALID_HANDLE_VALUE;}}};

enum class JsonType {null_value,boolean,number,string,array,object};
struct JsonValue {
 JsonType type=JsonType::null_value;bool boolean=false;std::string scalar;std::vector<JsonValue> array;std::vector<std::pair<std::string,JsonValue>> object;
};
class JsonReader {
 std::string_view text_;size_t at_=0,nodes_=0;
 void space() noexcept {while(at_<text_.size()&&(text_[at_]==' '||text_[at_]=='\t'||text_[at_]=='\r'||text_[at_]=='\n'))++at_;}
 bool string(std::string& out,size_t limit) {
  if(at_>=text_.size()||text_[at_++]!='"')return false;out.clear();
  while(at_<text_.size()){
   unsigned char c=static_cast<unsigned char>(text_[at_++]);if(c=='"')return true;if(c<0x20)return false;
   if(c=='\\'){
    if(at_>=text_.size())return false;char e=text_[at_++];
    switch(e){case '"':case '\\':case '/':out.push_back(e);break;case 'b':out.push_back('\b');break;case 'f':out.push_back('\f');break;case 'n':out.push_back('\n');break;case 'r':out.push_back('\r');break;case 't':out.push_back('\t');break;
     case 'u':{if(at_+4>text_.size())return false;unsigned value=0;for(int i=0;i<4;++i){char h=text_[at_++];unsigned d=h>='0'&&h<='9'?unsigned(h-'0'):h>='a'&&h<='f'?unsigned(h-'a'+10):h>='A'&&h<='F'?unsigned(h-'A'+10):16;if(d>15)return false;value=(value<<4)|d;}if(value>0x7f)return false;out.push_back(static_cast<char>(value));break;}
     default:return false;
    }
   }else out.push_back(static_cast<char>(c));
   if(out.size()>limit)return false;
  }
  return false;
 }
 bool number(std::string& out) {
  const size_t start=at_;if(at_<text_.size()&&text_[at_]=='-')++at_;
  if(at_>=text_.size())return false;if(text_[at_]=='0')++at_;else {if(text_[at_]<'1'||text_[at_]>'9')return false;while(at_<text_.size()&&text_[at_]>='0'&&text_[at_]<='9')++at_;}
  if(at_<text_.size()&&text_[at_]=='.'){++at_;size_t digits=at_;while(at_<text_.size()&&text_[at_]>='0'&&text_[at_]<='9')++at_;if(at_==digits)return false;}
  if(at_<text_.size()&&(text_[at_]=='e'||text_[at_]=='E')){++at_;if(at_<text_.size()&&(text_[at_]=='+'||text_[at_]=='-'))++at_;size_t digits=at_;while(at_<text_.size()&&text_[at_]>='0'&&text_[at_]<='9')++at_;if(at_==digits)return false;}
  if(at_-start>64)return false;out.assign(text_.substr(start,at_-start));return true;
 }
 bool value(JsonValue& out,unsigned depth) {
  if(depth>8||++nodes_>512)return false;space();if(at_>=text_.size())return false;
  char c=text_[at_];
  if(c=='{'){
   ++at_;out.type=JsonType::object;space();if(at_<text_.size()&&text_[at_]=='}'){++at_;return true;}
   for(;;){space();std::string key;if(!string(key,64))return false;for(const auto& p:out.object)if(p.first==key)return false;space();if(at_>=text_.size()||text_[at_++]!=':')return false;JsonValue child;if(!value(child,depth+1))return false;out.object.emplace_back(std::move(key),std::move(child));if(out.object.size()>32)return false;space();if(at_>=text_.size())return false;char delimiter=text_[at_++];if(delimiter=='}')return true;if(delimiter!=',')return false;}
  }
  if(c=='['){++at_;out.type=JsonType::array;space();if(at_<text_.size()&&text_[at_]==']'){++at_;return true;}for(;;){JsonValue child;if(!value(child,depth+1))return false;out.array.push_back(std::move(child));if(out.array.size()>64)return false;space();if(at_>=text_.size())return false;char delimiter=text_[at_++];if(delimiter==']')return true;if(delimiter!=',')return false;}}
  if(c=='"'){out.type=JsonType::string;return string(out.scalar,128);}
  if(text_.substr(at_,4)=="null"){at_+=4;out.type=JsonType::null_value;return true;}
  if(text_.substr(at_,4)=="true"){at_+=4;out.type=JsonType::boolean;out.boolean=true;return true;}
  if(text_.substr(at_,5)=="false"){at_+=5;out.type=JsonType::boolean;out.boolean=false;return true;}
  out.type=JsonType::number;return number(out.scalar);
 }
public:
 explicit JsonReader(std::string_view text):text_(text){}
 bool parse(JsonValue& root){if(!value(root,0))return false;space();return at_==text_.size();}
};

const JsonValue* member(const JsonValue& v,const char* key){if(v.type!=JsonType::object)return nullptr;for(const auto& p:v.object)if(p.first==key)return &p.second;return nullptr;}
bool exact_keys(const JsonValue& v,std::initializer_list<const char*> names){if(v.type!=JsonType::object||v.object.size()!=names.size())return false;for(auto name:names)if(!member(v,name))return false;return true;}
bool numeric(const JsonValue* v,double& out){if(!v||v->type!=JsonType::number)return false;std::istringstream in(v->scalar);in.imbue(std::locale::classic());in>>out;in>>std::ws;return in.eof()&&std::isfinite(out);}
bool integer(const JsonValue* v,unsigned& out){double n=0;if(!numeric(v,n)||n<0||n>UINT32_MAX||std::floor(n)!=n)return false;out=static_cast<unsigned>(n);return true;}
bool boolean(const JsonValue* v,bool& out){if(!v||v->type!=JsonType::boolean)return false;out=v->boolean;return true;}
bool string_value(const JsonValue* v,std::string& out){if(!v||v->type!=JsonType::string)return false;out=v->scalar;return true;}
bool number_array(const JsonValue* v,float* out,size_t count){if(!v||v->type!=JsonType::array||v->array.size()!=count)return false;for(size_t i=0;i<count;++i){double n=0;if(!numeric(&v->array[i],n)||std::abs(n)>1.0e9)return false;float f=static_cast<float>(n);if(!std::isfinite(f))return false;out[i]=f;}return true;}
void quote(std::ostream& o,const std::string& s){o<<'"';for(unsigned char c:s){switch(c){case '"':o<<"\\\"";break;case '\\':o<<"\\\\";break;case '\b':o<<"\\b";break;case '\f':o<<"\\f";break;case '\n':o<<"\\n";break;case '\r':o<<"\\r";break;case '\t':o<<"\\t";break;default:if(c<0x20)o<<"\\u00"<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(c)<<std::dec<<std::setfill(' ');else o<<static_cast<char>(c);}}o<<'"';}
template<class T,size_t N>void floats(std::ostream& o,const std::array<T,N>& values){o<<'[';for(size_t i=0;i<N;++i){if(i)o<<',';o<<std::setprecision(std::numeric_limits<T>::max_digits10)<<values[i];}o<<']';}
void rotate(float* v,const float* axis,double angle){double c=std::cos(angle),s=std::sin(angle),dot=0;float old[3]={v[0],v[1],v[2]};for(unsigned j=0;j<3;++j)dot+=old[j]*axis[j];for(unsigned j=0;j<3;++j)v[j]=static_cast<float>(old[j]*c+(axis[(j+1)%3]*old[(j+2)%3]-axis[(j+2)%3]*old[(j+1)%3])*s+axis[j]*dot*(1-c));}
void orthogonalize(std::array<float,16>& p){auto norm=[](float* v){double n=std::sqrt(double(v[0])*v[0]+double(v[1])*v[1]+double(v[2])*v[2]);for(unsigned j=0;j<3;++j)v[j]=static_cast<float>(v[j]/n);};norm(p.data()+8);double dot=0;for(unsigned j=0;j<3;++j)dot+=p[j]*p[8+j];for(unsigned j=0;j<3;++j)p[j]-=static_cast<float>(dot*p[8+j]);norm(p.data());for(unsigned j=0;j<3;++j)p[4+j]=p[8+(j+1)%3]*p[(j+2)%3]-p[8+(j+2)%3]*p[(j+1)%3];norm(p.data()+4);}
bool rigid(const std::array<float,16>& p){for(float f:p)if(!std::isfinite(f))return false;if(p[3]||p[7]||p[11]||p[15]!=1)return false;for(unsigned i=0;i<3;++i){double length=0;for(unsigned j=0;j<3;++j)length+=double(p[i*4+j])*p[i*4+j];if(std::abs(length-1)>.002)return false;for(unsigned k=0;k<i;++k){double dot=0;for(unsigned j=0;j<3;++j)dot+=double(p[i*4+j])*p[k*4+j];if(std::abs(dot)>.002)return false;}}double det=p[0]*(p[5]*p[10]-p[6]*p[9])-p[1]*(p[4]*p[10]-p[6]*p[8])+p[2]*(p[4]*p[9]-p[5]*p[8]);return det>.998&&det<1.002;}
bool valid_timestamp(const std::string& s){if(s.size()!=24||s[4]!='-'||s[7]!='-'||s[10]!='T'||s[13]!=':'||s[16]!=':'||s[19]!='.'||s[23]!='Z')return false;for(size_t i=0;i<s.size();++i)if(i!=4&&i!=7&&i!=10&&i!=13&&i!=16&&i!=19&&i!=23&&(s[i]<'0'||s[i]>'9'))return false;return true;}
bool parse_bookmark(const JsonValue& v,unsigned index,CameraBookmark& out){
 if(v.type==JsonType::null_value){out={};return true;}
 if(!exact_keys(v,{"slot","label","saved_at_utc","visible_pose","orientation","horizon_right","horizon_elapsed","previous_horizon_progress","manual_roll_degrees","manual_roll_target_degrees","current_vfov","target_vfov","current_roll_degrees","target_roll_degrees","horizon_level_progress","horizon_leveling_active","auto_level_horizon","cinematic_fov_enabled"}))return false;
 CameraBookmark b;b.present=true;double n=0;
 if(!integer(member(v,"slot"),b.slot)||b.slot!=index+1||!string_value(member(v,"label"),b.label)||b.label.empty()||b.label.size()>48||
    !string_value(member(v,"saved_at_utc"),b.saved_at_utc)||!valid_timestamp(b.saved_at_utc)||
    !number_array(member(v,"visible_pose"),b.camera.visible_pose.data(),16)||!number_array(member(v,"orientation"),b.camera.orientation.data(),16)||
    !number_array(member(v,"horizon_right"),b.camera.horizon_right.data(),3))return false;
 double* fields[]={&b.camera.horizon_elapsed,&b.camera.previous_horizon_progress,&b.camera.manual_roll,&b.camera.manual_roll_target,&b.camera.current_vfov,&b.camera.target_vfov};
 const char* names[]={"horizon_elapsed","previous_horizon_progress","manual_roll_degrees","manual_roll_target_degrees","current_vfov","target_vfov"};
 for(size_t i=0;i<6;++i){if(!numeric(member(v,names[i]),n))return false;*fields[i]=n;}
 float* float_fields[]={&b.camera.current_roll_degrees,&b.camera.target_roll_degrees,&b.camera.horizon_level_progress};
 const char* float_names[]={"current_roll_degrees","target_roll_degrees","horizon_level_progress"};
 for(size_t i=0;i<3;++i){if(!numeric(member(v,float_names[i]),n)||std::abs(n)>1000)return false;*float_fields[i]=static_cast<float>(n);}
 return boolean(member(v,"horizon_leveling_active"),b.camera.horizon_leveling_active)&&boolean(member(v,"auto_level_horizon"),b.camera.auto_level_horizon)&&
  boolean(member(v,"cinematic_fov_enabled"),b.camera.cinematic_fov_enabled)&&valid_camera_bookmark(b,index+1)?(out=std::move(b),true):false;
}
enum class ParseResult {ok,invalid,identity_mismatch};
ParseResult parse_data(std::string_view text,CameraBookmarkSet& out){
 if(text.empty()||text.size()>MAX_BOOKMARK_FILE)return ParseResult::invalid;JsonValue root;if(!JsonReader(text).parse(root)||!exact_keys(root,{"format","schema_version","retail_exe_sha256","course_id","slots"}))return ParseResult::invalid;
 std::string format,build,course;if(!string_value(member(root,"format"),format)||format!="MRR-Freecam-Bookmarks"||!string_value(member(root,"retail_exe_sha256"),build)||!string_value(member(root,"course_id"),course))return ParseResult::invalid;
 unsigned version=0;if(!integer(member(root,"schema_version"),version))return ParseResult::invalid;if(version!=CAMERA_BOOKMARK_SCHEMA_VERSION||build!=CAMERA_BOOKMARK_BUILD_SHA256||course!=CAMERA_BOOKMARK_COURSE_ID)return ParseResult::identity_mismatch;
 const auto* slots=member(root,"slots");if(!slots||slots->type!=JsonType::array||slots->array.size()!=CAMERA_BOOKMARK_SLOT_COUNT)return ParseResult::invalid;
 CameraBookmarkSet parsed;for(size_t i=0;i<CAMERA_BOOKMARK_SLOT_COUNT;++i)if(!parse_bookmark(slots->array[i],static_cast<unsigned>(i),parsed.slots[i]))return ParseResult::invalid;
 out=std::move(parsed);return ParseResult::ok;
}
bool read_file(const std::wstring& path,std::string& bytes,CameraBookmarkIo& error){
 HANDLE raw=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_SEQUENTIAL_SCAN,nullptr);
 if(raw==INVALID_HANDLE_VALUE){DWORD e=GetLastError();error=(e==ERROR_FILE_NOT_FOUND||e==ERROR_PATH_NOT_FOUND)?CameraBookmarkIo::missing:CameraBookmarkIo::io_error;return false;}
 Handle file{raw};LARGE_INTEGER size{};if(!GetFileSizeEx(raw,&size)||size.QuadPart<2||size.QuadPart>static_cast<LONGLONG>(MAX_BOOKMARK_FILE)){error=CameraBookmarkIo::invalid;return false;}
 bytes.resize(static_cast<size_t>(size.QuadPart));DWORD got=0;if(!ReadFile(raw,bytes.data(),static_cast<DWORD>(bytes.size()),&got,nullptr)||got!=bytes.size()){error=CameraBookmarkIo::io_error;return false;}error=CameraBookmarkIo::ok;return true;
}
bool create_directory(const std::wstring& path){if(CreateDirectoryW(path.c_str(),nullptr))return true;DWORD e=GetLastError();if(e!=ERROR_ALREADY_EXISTS)return false;DWORD a=GetFileAttributesW(path.c_str());return a!=INVALID_FILE_ATTRIBUTES&&(a&FILE_ATTRIBUTE_DIRECTORY)!=0;}
bool atomic_write(const std::wstring& path,const std::string& bytes){
 static std::atomic<uint32_t> serial{0};std::wstring temp;
 for(unsigned attempt=0;attempt<8;++attempt){temp=path+L".tmp-"+std::to_wstring(GetCurrentProcessId())+L"-"+std::to_wstring(GetTickCount64())+L"-"+std::to_wstring(serial.fetch_add(1,std::memory_order_relaxed));HANDLE h=CreateFileW(temp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY,nullptr);if(h==INVALID_HANDLE_VALUE){if(GetLastError()==ERROR_FILE_EXISTS)continue;return false;}
  Handle file{h};DWORD written=0;bool okay=bytes.size()<=MAX_BOOKMARK_FILE&&WriteFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),&written,nullptr)&&written==bytes.size()&&FlushFileBuffers(h)!=FALSE;file.close();
  if(okay&&MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))return true;DeleteFileW(temp.c_str());return false;
 }
 return false;
}
}

bool valid_camera_bookmark(const CameraBookmark& b,unsigned expected_slot) noexcept {
 const auto& c=b.camera;if(!b.present||expected_slot<1||expected_slot>CAMERA_BOOKMARK_SLOT_COUNT||b.slot!=expected_slot||b.label.empty()||b.label.size()>48||!valid_timestamp(b.saved_at_utc))return false;
 for(unsigned char ch:b.label)if(ch<0x20||ch>0x7e)return false;
 if(!rigid(c.visible_pose)||!rigid(c.orientation)||!std::isfinite(c.horizon_elapsed)||c.horizon_elapsed<0||c.horizon_elapsed>5.1||
    !std::isfinite(c.previous_horizon_progress)||c.previous_horizon_progress<0||c.previous_horizon_progress>1||
    !std::isfinite(c.manual_roll)||!std::isfinite(c.manual_roll_target)||std::abs(c.manual_roll)>180||std::abs(c.manual_roll_target)>180||
    !std::isfinite(c.current_vfov)||!std::isfinite(c.target_vfov)||!std::isfinite(c.current_roll_degrees)||!std::isfinite(c.target_roll_degrees)||
    !std::isfinite(c.horizon_level_progress)||c.horizon_level_progress<0||c.horizon_level_progress>1)return false;
 double right_length=0;for(float v:c.horizon_right){if(!std::isfinite(v))return false;right_length+=double(v)*v;}if(right_length<.90||right_length>1.10)return false;
 if(c.cinematic_fov_enabled){if(c.current_vfov<30||c.current_vfov>110||c.target_vfov<30||c.target_vfov>110)return false;}
 else if(c.current_vfov!=0||c.target_vfov!=0)return false;
 for(unsigned j=0;j<3;++j)if(std::abs(double(c.visible_pose[12+j])-c.orientation[12+j])>.001)return false;
 auto expected=c.orientation;float back[3]={expected[8],expected[9],expected[10]};double angle=c.manual_roll*3.14159265358979323846/180.;if(std::abs(angle)>1e-12){rotate(expected.data(),back,angle);rotate(expected.data()+4,back,angle);orthogonalize(expected);}
 for(unsigned i=0;i<16;++i)if(std::abs(double(expected[i])-c.visible_pose[i])>.002)return false;
 if(!c.auto_level_horizon&&c.horizon_leveling_active)return false;
 return true;
}
bool serialize_camera_bookmarks(const CameraBookmarkSet& set,std::string& output) noexcept {
 try{std::ostringstream o;o.imbue(std::locale::classic());o<<"{\n  \"format\":\"MRR-Freecam-Bookmarks\",\n  \"schema_version\":"<<CAMERA_BOOKMARK_SCHEMA_VERSION<<",\n  \"retail_exe_sha256\":\""<<CAMERA_BOOKMARK_BUILD_SHA256<<"\",\n  \"course_id\":\""<<CAMERA_BOOKMARK_COURSE_ID<<"\",\n  \"slots\":[\n";
  for(size_t i=0;i<CAMERA_BOOKMARK_SLOT_COUNT;++i){if(i)o<<",\n";const auto& b=set.slots[i];if(!b.present){o<<"    null";continue;}if(!valid_camera_bookmark(b,static_cast<unsigned>(i+1)))return false;const auto& c=b.camera;
   o<<"    {\"slot\":"<<b.slot<<",\"label\":";quote(o,b.label);o<<",\"saved_at_utc\":";quote(o,b.saved_at_utc);o<<",\"visible_pose\":";floats(o,c.visible_pose);o<<",\"orientation\":";floats(o,c.orientation);o<<",\"horizon_right\":";floats(o,c.horizon_right);
   o<<",\"horizon_elapsed\":"<<std::setprecision(17)<<c.horizon_elapsed<<",\"previous_horizon_progress\":"<<c.previous_horizon_progress<<",\"manual_roll_degrees\":"<<c.manual_roll<<",\"manual_roll_target_degrees\":"<<c.manual_roll_target<<",\"current_vfov\":"<<c.current_vfov<<",\"target_vfov\":"<<c.target_vfov
    <<",\"current_roll_degrees\":"<<std::setprecision(9)<<c.current_roll_degrees<<",\"target_roll_degrees\":"<<c.target_roll_degrees<<",\"horizon_level_progress\":"<<c.horizon_level_progress<<",\"horizon_leveling_active\":"<<(c.horizon_leveling_active?"true":"false")<<",\"auto_level_horizon\":"<<(c.auto_level_horizon?"true":"false")<<",\"cinematic_fov_enabled\":"<<(c.cinematic_fov_enabled?"true":"false")<<'}';
  }
  o<<"\n  ]\n}\n";auto text=o.str();if(text.size()>MAX_BOOKMARK_FILE)return false;output=std::move(text);return true;
 }catch(...){return false;}
}
bool parse_camera_bookmarks(std::string_view text,CameraBookmarkSet& out) noexcept {try{return parse_data(text,out)==ParseResult::ok;}catch(...){return false;}}
CameraBookmarkIo read_camera_bookmarks(const std::wstring& path,CameraBookmarkSet& out) noexcept {
 try{std::string bytes;CameraBookmarkIo error;if(!read_file(path,bytes,error)){if(error==CameraBookmarkIo::missing)out=CameraBookmarkSet{};return error;}CameraBookmarkSet parsed;auto result=parse_data(bytes,parsed);if(result==ParseResult::ok){out=std::move(parsed);return CameraBookmarkIo::ok;}return result==ParseResult::identity_mismatch?CameraBookmarkIo::identity_mismatch:CameraBookmarkIo::invalid;}catch(...){return CameraBookmarkIo::io_error;}
}
CameraBookmarkIo save_camera_bookmark(const std::wstring& path,unsigned slot,const CameraBookmark& bookmark,CameraBookmarkSet& out) noexcept {
 try{if(path.empty()||slot<1||slot>CAMERA_BOOKMARK_SLOT_COUNT||!valid_camera_bookmark(bookmark,slot))return CameraBookmarkIo::invalid;
  CameraBookmarkSet merged;auto existing=read_camera_bookmarks(path,merged);if(existing!=CameraBookmarkIo::ok&&existing!=CameraBookmarkIo::missing)return existing;merged.slots[slot-1]=bookmark;
  std::string bytes;if(!serialize_camera_bookmarks(merged,bytes))return CameraBookmarkIo::invalid;auto slash=path.find_last_of(L"\\/");if(slash==std::wstring::npos||!create_directory(path.substr(0,slash)))return CameraBookmarkIo::path_unavailable;
  if(!atomic_write(path,bytes))return CameraBookmarkIo::io_error;out=std::move(merged);return CameraBookmarkIo::ok;
 }catch(...){return CameraBookmarkIo::io_error;}
}
std::wstring default_camera_bookmark_path() noexcept {
 try{wchar_t local[MAX_PATH]{};DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",local,MAX_PATH);if(!n||n>=MAX_PATH)return {};std::wstring root(local,n);return root+L"\\Master Rallye\\MRRRenderer\\camera-bookmarks.json";}catch(...){return {};}
}
bool ensure_camera_bookmark_directory() noexcept {
 try{wchar_t local[MAX_PATH]{};DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",local,MAX_PATH);if(!n||n>=MAX_PATH)return false;std::wstring root(local,n);return create_directory(root+L"\\Master Rallye")&&create_directory(root+L"\\Master Rallye\\MRRRenderer");}catch(...){return false;}
}
bool current_utc_timestamp(std::string& out) noexcept {
 try{SYSTEMTIME t{};GetSystemTime(&t);char value[32]{};int n=std::snprintf(value,sizeof(value),"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds);if(n!=24)return false;out.assign(value,static_cast<size_t>(n));return true;}catch(...){return false;}
}
const char* camera_bookmark_io_name(CameraBookmarkIo s) noexcept {switch(s){case CameraBookmarkIo::ok:return "ok";case CameraBookmarkIo::missing:return "missing_file";case CameraBookmarkIo::invalid:return "invalid_file_or_bookmark";case CameraBookmarkIo::identity_mismatch:return "unsupported_schema_build_or_course";case CameraBookmarkIo::io_error:return "io_error";case CameraBookmarkIo::path_unavailable:return "local_appdata_unavailable";default:return "unknown";}}
}
