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
 assert(rejects("MR-ADDON-LAMPS 3\n"));assert(rejects(header+row+row));
 assert(rejects(header+"Example 3 14 10 "+hash+" "+hash+"\n"));
 assert(rejects(header+"../Example 0 14 10 "+hash+" "+hash+"\n"));
 assert(rejects(header+"Example 0 14 999999 "+hash+" "+hash+"\n"));
 assert(rejects(header+"Example 0 14 10 abcd "+hash+"\n"));
 assert(rejects(header+row.substr(0,row.size()-1)+" extra\n"));
 assert(rejects(header+std::string(513,'a')+"\n"));
 {std::istringstream in("MR-ADDON-LAMPS 2\n"+row.substr(0,row.size()-1)+" PS2_MODEL_ONLY\n");auto r=read_addon_lamps(in);assert(r.size()==1&&r[0].ps2ModelOnly);}
 assert(rejects("MR-ADDON-LAMPS 2\n"+row));
 if(argc==2){std::ifstream file(argv[1]);auto r=read_addon_lamps(file);assert(!r.empty());std::cout<<"Accepted actual SDK catalog: "<<r.size()<<" lamp layers\n";}
 std::cout<<"Addon lamp registry acceptance and rejection checks passed\n";
}
