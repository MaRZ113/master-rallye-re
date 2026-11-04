#pragma once
#include "atmosphere_scene.hpp"
// Reused read-only retail offsets from renderer-stable-material evidence.
namespace gfx2::atmosphere {
inline std::string canonical_binding(std::string s){
 for(auto& c:s)c=char(std::tolower(static_cast<unsigned char>(c)));
 const auto slash=s.find_last_of("/\\");if(slash!=std::string::npos)s.erase(0,slash+1);
 if(s.size()>4&&(s.substr(s.size()-4)==".dxt"||s.substr(s.size()-4)==".gxi"))s.resize(s.size()-4);
 if(s.size()>4&&s.substr(s.size()-4)==".tga")s.replace(s.size()-4,4,"-tga");
 if(s.rfind("mr-ref-",0)==0){auto dash=s.find('-',7);if(dash!=std::string::npos&&dash>7&&s.find_first_not_of("0123456789abcdef",7)>=dash)s.erase(0,dash+1);}
 return s;
}
// All offsets are verified retail native data flow, NOT inferred D3D state:
// 576970 leaf +38 material list, material +18 byte stage->slot map,
// leaf +2c texture handles; 54acd0/53d2f0 texture pool; 4d0570/4d4cd0
// interned resource name. Reads have no allocation/load side effects in game.
struct NativeMaterialBinding {
 uintptr_t material=0,texture_records[2]{},textures[2]{};
 uint32_t handles[2]{},name_ids[2]{};
 std::string names[2];

};
template<class Read> bool native_name(uintptr_t base,uint32_t id,Read read,std::string& out){
 uint32_t global=0,table=0,begin=0,end=0,text=0;
 if(!read(base+0x2f93d4,global)||!global||!read(global+4,table)||!table||!read(table+4,begin)||!read(table+8,end)||!begin||end<begin||(end-begin)%4||id>=(end-begin)/4||!read(begin+id*4,text)||!text)return false;
 out.clear();out.reserve(64);uintptr_t previous=UINTPTR_MAX;uint32_t word=0;for(unsigned i=0;i<256;++i){const auto at=(text+i)&~uintptr_t(3);if(at!=previous){if(!read(at,word))return false;previous=at;}char ch=char(word>>(((text+i)&3)*8));if(!ch)return !out.empty();if(static_cast<unsigned char>(ch)<32||static_cast<unsigned char>(ch)>126)return false;out+=ch;}
 return false;
}
template<class Read> bool native_material_binding(uintptr_t base,uintptr_t leaf,Read read,NativeMaterialBinding& out){
 out={};uint32_t list=0,begin=0,end=0,material=0,stages=0,slots=0,global=0,manager=0,pool=0,table=0,tbegin=0,tend=0;
 if(!read(leaf+0x38,list)||!list||!read(list+4,begin)||!read(list+8,end)||end!=begin+4||!read(begin,material)||!material||!read(material+4,stages)||!stages||stages>8||!read(leaf+0x2c,slots)||!slots||!read(base+0x2f9cf0,global)||!global||!read(global+4,manager)||!manager||!read(manager+0x14,pool)||!pool||!read(pool,table)||!table||!read(table+8,tbegin)||!read(table+12,tend)||!tbegin||tend<tbegin||(tend-tbegin)%12||(tend-tbegin)/12>1048576)return false;
 out.material=material;out.names[0]=out.names[1]="null";
 for(unsigned stage=0;stage<2&&stage<stages;++stage){uint32_t packed=0,handle=0,record=0,texture_object=0,name=0;
  if(!read(material+0x18+(stage&~3u),packed))return false;const unsigned index=(packed>>((stage&3)*8))&255;
  if(index>=32||!read(slots+index*4,handle))return false;if(!handle)continue;
  if(handle>=(tend-tbegin)/12||!read(tbegin+handle*12,record)||!record||!read(record,texture_object)||!read(record+4,name)||!native_name(base,name,read,out.names[stage]))return false;
  packed=0;if(texture_object&&!read(texture_object,packed))return false;
  out.handles[stage]=handle;out.name_ids[stage]=name;out.texture_records[stage]=record;out.textures[stage]=packed;out.names[stage]=canonical_binding(out.names[stage]);
 }
 return true;
}

}
