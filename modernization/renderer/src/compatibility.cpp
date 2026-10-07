#include "fingerprint_recipes.hpp"
#include "provenance.hpp"
#include "game_fov.hpp"
#include "ui_margins.hpp"
#include <cstring>
#include <sstream>
#include <algorithm>
namespace gfx2 {
namespace {
const unsigned char* code_at(const std::vector<CodeSection>& sections,uint32_t rva,size_t size) {
 for(const auto& s:sections)if(s.name==".text"&&rva>=s.rva&&uint64_t(rva-s.rva)+size<=s.bytes.size())return s.bytes.data()+rva-s.rva;
 return nullptr;
}
bool match(const unsigned char* p,const FeatureFingerprint& f,size_t n) {
 if(f.fixed_rva)return !std::memcmp(p,f.bytes.data(),n);
 if(n&&p[0]!=f.bytes[0])return false;
 for(size_t k=0;k<n;++k){
  if(f.freeze_branch&&k==3){if(p[k]!=0x11&&p[k]!=0)return false;continue;}
  bool relative=false;for(const auto& i:f.instructions)if(!f.fixed_rva&&i.relative_call&&k>i.offset&&k<size_t(i.offset)+5){relative=true;break;}
  if(!relative&&p[k]!=f.bytes[k])return false;
 }return true;
}
bool structure(const std::vector<CodeSection>& sections,uint32_t start,const FeatureFingerprint& f) {
 const auto* p=code_at(sections,start,f.bytes.size());if(!p)return false;size_t end=0;
 // This decoder deliberately accepts only the exact instruction recipes. Unknown
 // opcodes/ModRM/lengths cannot be guessed or copied into a detour.
 for(const auto& i:f.instructions){
  if(i.offset!=end||!i.length||end+i.length>f.bytes.size())return false;
  if(i.relative_call){
   if(i.length!=5||p[end]!=0xe8||i.callee_prefix.empty())return false;
   int32_t delta=0;std::memcpy(&delta,p+end+1,4);int64_t dest=int64_t(start)+end+5+delta;
   if(dest<0||dest>UINT32_MAX)return false;
   const auto* callee=code_at(sections,static_cast<uint32_t>(dest),i.callee_prefix.size());
   if(!callee||std::memcmp(callee,i.callee_prefix.data(),i.callee_prefix.size()))return false;
  }
  end+=i.length;
 }
 if(end!=f.bytes.size())return false;
 if(f.fixed_rva)return true;
 if(f.freeze_branch)return f.target_offset==2&&p[0]==0x85&&p[1]==0xff&&p[2]==0x75&&
  (p[3]==0||p[3]==0x11)&&p[12]==0xe8&&p[17]==0xff&&p[21]==0x84&&p[22]==0xdb;
 return f.target_offset==end&&end>=6&&!std::memcmp(p+end-6,"\xff\x90\x94\0\0\0",6);
}
FeatureCapability exact(const char* id,bool allowed,const char* reason){FeatureCapability c;c.id=id;c.method=allowed?"known_profile":"unsupported";c.status=allowed?"SUPPORTED":"UNSUPPORTED";c.reason=reason;return c;}
}
FeatureCapability verify_feature(const std::vector<CodeSection>& sections,const FeatureFingerprint& f,bool known) {
 FeatureCapability c;c.id=f.id;if(f.bytes.empty()||!f.anchor_size||f.anchor_size>f.bytes.size()){c.reason="invalid_recipe";return c;}
 if(f.fixed_rva){
  c.fast_path=known;c.candidate_rva=f.known_rva+f.target_offset;
  const auto* p=code_at(sections,f.known_rva,f.bytes.size());c.bytes_valid=p&&match(p,f,f.bytes.size());
  c.instructions_valid=c.bytes_valid&&structure(sections,f.known_rva,f);
  if(c.instructions_valid){c.matches=1;c.method=known?"known_profile":"fingerprint";c.status="SUPPORTED";c.reason="fixed_layout_full_decoded_local_owner_validated";}
  else c.reason="fixed_layout_local_owner_or_callee_changed";
  return c;
 }
 // Validate a known RVA too; a trusted disk hash never authorizes blind memory writes.
 c.fast_path=known&&code_at(sections,f.known_rva,f.bytes.size())!=nullptr;
 if(known){
  const auto* p=code_at(sections,f.known_rva,f.bytes.size());
  if(!p||!match(p,f,f.bytes.size())||!structure(sections,f.known_rva,f)){
   c.candidate_rva=f.known_rva+f.target_offset;c.bytes_valid=p&&match(p,f,f.bytes.size());
   c.reason="known_owner_local_validation_failed";return c;
  }
 }
 uint32_t match_rva=0;
 for(const auto& s:sections){if(s.name!=f.section||s.bytes.size()<f.anchor_size)continue;
  for(size_t k=0;k<=s.bytes.size()-f.anchor_size;++k)if(match(s.bytes.data()+k,f,f.anchor_size)){++c.matches;match_rva=s.rva+static_cast<uint32_t>(k);}
 }
 if(c.matches!=1){c.reason=c.matches?"ambiguous_owner":"owner_not_found";return c;}
 c.candidate_rva=match_rva+f.target_offset;
 const auto* p=code_at(sections,match_rva,f.bytes.size());
 c.bytes_valid=p&&match(p,f,f.bytes.size());
 if(!c.bytes_valid){c.reason="instruction_bytes_mismatch";return c;}
 c.instructions_valid=structure(sections,match_rva,f);
 if(!c.instructions_valid){c.reason="decoded_control_flow_or_callee_mismatch";return c;}
 c.method=known&&match_rva==f.known_rva?"known_profile":"fingerprint";
 c.status=f.freeze_branch&&p[3]==0?"ALREADY_PATCHED":"SUPPORTED";c.reason="unique_decoded_owner_validated";return c;
}
FeatureCapability verify_owner_group(const std::vector<CodeSection>& sections,const std::vector<FeatureFingerprint>& owners,const char* id,bool known){
 auto c=exact(id,false,"empty_owner_group");if(owners.empty())return c;
 for(const auto& f:owners){auto part=verify_feature(sections,f,known);if(!part.supported()){c.reason=f.id+":"+part.reason;c.candidate_rva=part.candidate_rva;return c;}c.validated_owner_rvas.push_back(f.known_rva);}
 c.status="SUPPORTED";c.method=known?"known_profile":"fingerprint";c.bytes_valid=c.instructions_valid=true;c.fast_path=known;c.reason="all_required_fixed_layout_owners_globals_and_calls_validated";return c;
}
std::string FeatureCapability::json() const {
 std::ostringstream o;o<<"{\"feature_id\":"<<quote(id)<<",\"compatibility_method\":"<<quote(method)<<",\"status\":"<<quote(status)<<",\"reason\":"<<quote(reason)<<",\"fast_path_candidate\":"<<(fast_path?"true":"false")<<",\"scan_matches\":"<<matches<<",\"candidate_rva\":"<<candidate_rva<<",\"bytes_valid\":"<<(bytes_valid?"true":"false")<<",\"instruction_shape_valid\":"<<(instructions_valid?"true":"false")<<",\"normalized_fingerprint_valid\":null,\"validated_owner_rvas\":[";bool first=true;for(auto rva:validated_owner_rvas){if(!first)o<<',';first=false;o<<rva;}o<<"]}";return o.str();
}
std::string Compatibility::json(const std::string& sha,bool known) const {
 auto generic=[](const char* id){auto c=exact(id,true,"D3D_Win32_generic_no_game_owner");c.method="generic";return c.json();};
 return "{\"type\":\"compatibility_capabilities\",\"image_sha256\":"+quote(sha)+",\"known_build\":"+(known?"true":"false")+",\"features\":["+generic("GenericDisplay")+","+generic("MSAA")+","+generic("AF")+","+freeze.json()+","+ui.json()+","+margins.json()+","+fov.json()+","+shadow.json()+","+vehicle.json()+","+preview.json()+"]}";
}
bool ui_owner(const FeatureCapability& c,bool exe,uint32_t rva) noexcept {return exe&&c.supported()&&c.candidate_rva&&rva==c.candidate_rva;}
Compatibility inspect_compatibility(bool known) noexcept {
 Compatibility result;result.freeze.id="MenuFreezeFix";result.ui.id="WidescreenUI";
 result.fov=exact("GameplayFOVCulling",false,"exact_profile_and_camera_globals_required");
 result.margins=exact("PreserveMargins",false,"exact_profile_and_packet_layout_required");
 result.shadow=exact("StockShadow",known,"exact_profile_required");result.vehicle=exact("VehicleSemantics",false,"required_local_owners_unavailable");result.preview=exact("FrontendPreviewAspectCorrection",false,"required_camera_owners_unavailable");
 try {
  uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS32 nt{};
  if(!safe_copy(&dos,reinterpret_cast<void*>(base),sizeof(dos))||dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<0||dos.e_lfanew>1048576||
     !safe_copy(&nt,reinterpret_cast<void*>(base+dos.e_lfanew),sizeof(nt))||nt.Signature!=IMAGE_NT_SIGNATURE||nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_I386||nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC||nt.FileHeader.SizeOfOptionalHeader!=sizeof(IMAGE_OPTIONAL_HEADER32)||nt.FileHeader.NumberOfSections>96)return result;
  std::vector<CodeSection> sections;unsigned writable_globals=0;
  for(unsigned n=0;n<nt.FileHeader.NumberOfSections;++n){IMAGE_SECTION_HEADER h{};auto at=base+dos.e_lfanew+sizeof(DWORD)+sizeof(IMAGE_FILE_HEADER)+nt.FileHeader.SizeOfOptionalHeader+n*sizeof(h);
   if(!safe_copy(&h,reinterpret_cast<void*>(at),sizeof(h)))return result;
   if((h.Characteristics&(IMAGE_SCN_MEM_READ|IMAGE_SCN_MEM_WRITE))==(IMAGE_SCN_MEM_READ|IMAGE_SCN_MEM_WRITE)&&!(h.Characteristics&IMAGE_SCN_MEM_EXECUTE)){
    for(unsigned g=0;g<2;++g){uint32_t rva=g?RENDERER_HOLDER_RVA:CAMERA_MANAGER_RVA;if(rva>=h.VirtualAddress&&uint64_t(rva)+4<=uint64_t(h.VirtualAddress)+h.Misc.VirtualSize&&uint64_t(rva)+4<=nt.OptionalHeader.SizeOfImage)writable_globals|=1u<<g;}
   }
   if(std::memcmp(h.Name,".text\0\0\0",8)||!(h.Characteristics&IMAGE_SCN_MEM_EXECUTE))continue;
   if(!h.Misc.VirtualSize||h.Misc.VirtualSize>64*1024*1024||uint64_t(h.VirtualAddress)+h.Misc.VirtualSize>nt.OptionalHeader.SizeOfImage)return result;
   CodeSection s;s.name=".text";s.rva=h.VirtualAddress;s.bytes.resize(h.Misc.VirtualSize);
   if(!safe_copy(s.bytes.data(),reinterpret_cast<void*>(base+s.rva),s.bytes.size()))return result;sections.push_back(std::move(s));
  }
  // Recipes retain absolute global operands. Rebased owners are intentionally unsupported.
  if(base!=0x400000)return result;
  result.freeze=verify_feature(sections,freeze_fingerprint(),known);result.ui=verify_feature(sections,ui_fingerprint(),known);
  result.preview=verify_owner_group(sections,camera_owner_recipes(),"FrontendPreviewAspectCorrection",known);
  result.margins=verify_owner_group(sections,margin_owner_recipes(),"PreserveMargins",known);
  result.fov=verify_owner_group(sections,fov_owner_recipes(),"GameplayFOVCulling",known);
  result.vehicle=verify_owner_group(sections,vehicle_owner_recipes(),"VehicleSemantics",known);
  if(writable_globals!=3){for(auto* c:{&result.fov,&result.vehicle,&result.preview}){c->status="UNSUPPORTED";c->reason="camera_or_renderer_global_not_in_writable_image_data";}}


 }catch(...) {for(auto* c:{&result.freeze,&result.ui,&result.preview,&result.margins,&result.fov,&result.vehicle}){c->status="UNSUPPORTED";c->reason="image_validation_exception";}}
 return result;
}
}
