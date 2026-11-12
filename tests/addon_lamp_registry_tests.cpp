#include "../ps2-research/pc-port/renderer/addon_lamp_registry.hpp"
#include <fstream>
#include <iostream>
#include <cassert>
using namespace gfx2::ps2port;
static bool rejects(const std::string& text){try{std::istringstream input(text);read_addon_lamps(input);return false;}catch(const std::runtime_error&){return true;}}
int main(int argc,char** argv){
 const std::string header="MR-ADDON-LAMPS 1\n",hash(64,'a');
 const std::string row="Example 0 14 10 "+hash+" "+hash+"\n";
 {std::istringstream in(header+row);auto r=read_addon_lamps(in);assert(r.size()==1&&r[0].family=="Example"&&r[0].layer==0);}
 assert(rejects("MR-ADDON-LAMPS 4\n"));assert(rejects(header+row+row));
 assert(rejects(header+"Example 3 14 10 "+hash+" "+hash+"\n"));
 assert(rejects(header+"../Example 0 14 10 "+hash+" "+hash+"\n"));
 assert(rejects(header+"Example 0 14 999999 "+hash+" "+hash+"\n"));
 assert(rejects(header+"Example 0 14 10 abcd "+hash+"\n"));
 assert(rejects(header+row.substr(0,row.size()-1)+" extra\n"));
 assert(rejects(header+std::string(513,'a')+"\n"));
 {std::istringstream in("MR-ADDON-LAMPS 2\n"+row.substr(0,row.size()-1)+" PS2_MODEL_ONLY\n");auto r=read_addon_lamps(in);assert(r.size()==1&&r[0].ps2ModelOnly);}
 assert(rejects("MR-ADDON-LAMPS 2\n"+row));
 // v3 body scope: one model, PS2 and PC lamp sets; layer 2 (OFF lamp) only inside a body-scoped set.
 {const std::string base=row.substr(0,row.size()-1),other="Example 0 14 10 "+std::string(64,'b')+" "+hash,off="Example 2 14 10 "+std::string(64,'c')+" "+hash;
  std::istringstream in("MR-ADDON-LAMPS 3\n"+base+" PS2_BODY_ONLY\n"+other+" PC_BODY_ONLY\n"+off+" PS2_BODY_ONLY\n");auto r=read_addon_lamps(in);
  assert(r.size()==3&&r[0].body==AddonLampBody::Ps2&&r[0].ps2ModelOnly&&r[1].body==AddonLampBody::Pc&&!r[1].ps2ModelOnly&&r[2].layer==2);
  {std::istringstream v2("MR-ADDON-LAMPS 3\n"+base+" ANY_MODEL\n");assert(read_addon_lamps(v2)[0].body==AddonLampBody::Any);}
  assert(rejects("MR-ADDON-LAMPS 2\n"+base+" PS2_BODY_ONLY\n"));assert(rejects("MR-ADDON-LAMPS 3\n"+off+" ANY_MODEL\n"));
  assert(rejects("MR-ADDON-LAMPS 3\n"+off+" PS2_MODEL_ONLY\n"));assert(rejects("MR-ADDON-LAMPS 3\n"+base+" PC_MODEL_ONLY\n"));
  assert(rejects("MR-ADDON-LAMPS 3\nExample 3 14 10 "+hash+" "+hash+" PS2_BODY_ONLY\n"));}
 if(argc==2){std::ifstream file(argv[1]);auto r=read_addon_lamps(file);assert(!r.empty());std::cout<<"Accepted actual SDK catalog: "<<r.size()<<" lamp layers\n";}
 std::cout<<"Addon lamp registry acceptance and rejection checks passed\n";
}
