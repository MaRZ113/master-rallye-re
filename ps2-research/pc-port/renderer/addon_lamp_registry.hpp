#pragma once
// SDK-generated draw bindings, not a compiled vehicle/texture allowlist.
// Geometry/UV digests associate the current draw with an authored lamp role;
// native owner, material and buffer lifetime checks remain mandatory.
#include <istream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <set>
#include <utility>
namespace gfx2::ps2port {
// v3 body scope: a model with different PS2/PC bodies carries both lamp sets; each set is drawn only while
// its own body is (PS2: a same-owner PS2 body was submitted; PC: none was), the other set is suppressed.
enum class AddonLampBody {Any,Ps2,Pc};
struct AddonLampRecord {std::string family;unsigned layer=0,vertices=0,triangles=0;std::string geometry,positionUv;bool ps2ModelOnly=false;AddonLampBody body=AddonLampBody::Any;};
inline std::vector<AddonLampRecord> read_addon_lamps(std::istream& in){
 std::string line;if(!std::getline(in,line)||(line!="MR-ADDON-LAMPS 1"&&line!="MR-ADDON-LAMPS 2"&&line!="MR-ADDON-LAMPS 3"))throw std::runtime_error("addon_lamp_version");const bool v3=line=="MR-ADDON-LAMPS 3",v2=v3||line=="MR-ADDON-LAMPS 2";
 std::vector<AddonLampRecord> out;std::set<std::string> seen;size_t bytes=line.size();
 auto digest=[](const std::string& s){return s.size()==64&&s.find_first_not_of("0123456789abcdef")==std::string::npos;};
 while(std::getline(in,line)){
  bytes+=line.size();if(bytes>2*1024*1024||line.size()>512||out.size()>=4096)throw std::runtime_error("addon_lamp_budget");
  if(line.empty()||line[0]=='#')continue;
  std::istringstream row(line);AddonLampRecord p;std::string tail;
  std::string policy;if(!(row>>p.family>>p.layer>>p.vertices>>p.triangles>>p.geometry>>p.positionUv)||(v2&&(!(row>>policy)||(policy!="ANY_MODEL"&&policy!="PS2_MODEL_ONLY"&&!(v3&&(policy=="PS2_BODY_ONLY"||policy=="PC_BODY_ONLY")))))||(row>>tail)||p.family.size()>96||p.family.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")!=std::string::npos||p.layer>2||!p.vertices||p.vertices>65536||!p.triangles||p.triangles>8192||!digest(p.geometry)||!digest(p.positionUv))throw std::runtime_error("addon_lamp_record");
  p.ps2ModelOnly=policy=="PS2_MODEL_ONLY"||policy=="PS2_BODY_ONLY";p.body=policy=="PS2_BODY_ONLY"?AddonLampBody::Ps2:policy=="PC_BODY_ONLY"?AddonLampBody::Pc:AddonLampBody::Any;
  // Layer 2 = the OFF lamp of a body-scoped set: selected with its body, never given lamp art.
  if(p.layer==2&&p.body==AddonLampBody::Any)throw std::runtime_error("addon_lamp_record");
  const auto identity=std::to_string(p.vertices)+":"+std::to_string(p.triangles)+":"+p.geometry+":"+p.positionUv;
  if(!seen.insert(identity).second)throw std::runtime_error("addon_lamp_ambiguous_binding");
  out.push_back(std::move(p));
 }
 return out;
}
}
