#include "compatibility.hpp"
#include "provenance.hpp"
#include "quality.hpp"
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <fstream>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
std::vector<CodeSection> fixture(const FeatureFingerprint& f,uint32_t start=0x1100){
 CodeSection s;s.name=".text";s.rva=0x1000;s.bytes.resize(8192,0x90);
 std::memcpy(s.bytes.data()+start-s.rva,f.bytes.data(),f.bytes.size());
 unsigned ordinal=0;
 for(const auto& ins:f.instructions)if(ins.relative_call){
  uint32_t callee=0x2000+ordinal++*64;int32_t delta=static_cast<int32_t>(callee-start-ins.offset-5);
  std::memcpy(s.bytes.data()+start-s.rva+ins.offset+1,&delta,4);
  std::memcpy(s.bytes.data()+callee-s.rva,ins.callee_prefix.data(),ins.callee_prefix.size());
 }
 return {s};
}
void fingerprints(){
 for(auto f:{freeze_fingerprint(),ui_fingerprint()}){
  f.known_rva=0x1100;auto sections=fixture(f);
  auto c=verify_feature(sections,f,true);CHECK(c.supported()&&c.method=="known_profile"&&c.fast_path&&c.matches==1&&c.instructions_valid);
  c=verify_feature(sections,f,false);CHECK(c.supported()&&c.method=="fingerprint"&&!c.fast_path);
  sections[0].bytes.back()^=1;CHECK(verify_feature(sections,f,false).supported()); // unrelated mutation
  auto missing=sections;missing[0].bytes[0x100]=0xcc;CHECK(!verify_feature(missing,f,false).supported());
  auto shifted=fixture(f,0x1200);CHECK(!verify_feature(shifted,f,true).supported()&&verify_feature(shifted,f,false).supported());
  auto duplicate=sections;std::memcpy(duplicate[0].bytes.data()+0x500,sections[0].bytes.data()+0x100,f.bytes.size());
  c=verify_feature(duplicate,f,true);CHECK(!c.supported()&&c.matches==2&&c.reason=="ambiguous_owner");
  auto changed=sections;changed[0].bytes[0x100+f.bytes.size()-1]^=1;
  c=verify_feature(changed,f,true);CHECK(!c.supported()&&c.reason=="known_owner_local_validation_failed"&&!c.bytes_valid); // known hash never overrides memory checks
  auto outside=sections;outside[0].name=".rdata";CHECK(!verify_feature(outside,f,false).supported());
  auto bad_call=sections;for(const auto& ins:f.instructions)if(ins.relative_call){int32_t bad=INT32_MAX;std::memcpy(bad_call[0].bytes.data()+0x100+ins.offset+1,&bad,4);break;}
  c=verify_feature(bad_call,f,false);CHECK(!c.supported()&&c.bytes_valid&&!c.instructions_valid);
  auto bad_callee=sections;bad_callee[0].bytes[0x1000]^=1;CHECK(!verify_feature(bad_callee,f,false).supported());
  auto bad_decode=f;bad_decode.instructions[0].length=1;CHECK(!verify_feature(sections,bad_decode,false).supported());
  if(f.freeze_branch){auto patched=sections;patched[0].bytes[0x103]=0;c=verify_feature(patched,f,false);CHECK(c.status=="ALREADY_PATCHED"&&c.supported());patched[0].bytes[0x103]=0x10;CHECK(!verify_feature(patched,f,false).supported());}
 }
 auto f=ui_fingerprint();CHECK(f.known_rva+f.target_offset==0x161ed3);auto c=verify_feature(fixture(f),f,false);
 CHECK(ui_owner(c,true,c.candidate_rva)&&!ui_owner(c,false,c.candidate_rva)&&!ui_owner(c,true,0x13fa75));
 D3DMATRIX p{},out{};p._11=2.f/640;p._22=2.f/480;p._33=-.0005f;p._41=p._42=-1;p._43=.5;p._44=1;
 CHECK(ui_projection(p,4./3,out)&&!std::memcmp(&p,&out,sizeof(p)));CHECK(ui_projection(p,16./9,out)&&p._22==out._22&&p._11!=out._11);
 p._41=0;CHECK(!ui_projection(p,16./9,out));
 auto c2=verify_feature(fixture(freeze_fingerprint()),freeze_fingerprint(),false);CHECK(c2.supported());
 std::cout<<"Unique decoded known/unknown/ambiguous/missing/changed/callee/already owners + UI caller semantics: PASS\n";
}
std::vector<CodeSection> read_sections(const char* path){
 std::ifstream file(path,std::ios::binary);CHECK(file.good());std::vector<unsigned char> data((std::istreambuf_iterator<char>(file)),{});
 CHECK(data.size()>=sizeof(IMAGE_DOS_HEADER));auto* dos=reinterpret_cast<const IMAGE_DOS_HEADER*>(data.data());CHECK(dos->e_magic==IMAGE_DOS_SIGNATURE&&dos->e_lfanew>0);
 CHECK(uint64_t(dos->e_lfanew)+sizeof(IMAGE_NT_HEADERS32)<=data.size());auto* nt=reinterpret_cast<const IMAGE_NT_HEADERS32*>(data.data()+dos->e_lfanew);
 CHECK(nt->Signature==IMAGE_NT_SIGNATURE&&nt->FileHeader.Machine==IMAGE_FILE_MACHINE_I386&&nt->OptionalHeader.Magic==IMAGE_NT_OPTIONAL_HDR32_MAGIC&&nt->OptionalHeader.ImageBase==0x400000);
 std::vector<CodeSection> sections;size_t table=dos->e_lfanew+24+nt->FileHeader.SizeOfOptionalHeader;
 for(unsigned i=0;i<nt->FileHeader.NumberOfSections;++i){CHECK(table+(i+1)*sizeof(IMAGE_SECTION_HEADER)<=data.size());auto* s=reinterpret_cast<const IMAGE_SECTION_HEADER*>(data.data()+table+i*sizeof(IMAGE_SECTION_HEADER));
  if(std::memcmp(s->Name,".text\0\0\0",8))continue;CHECK(uint64_t(s->PointerToRawData)+s->SizeOfRawData<=data.size());CodeSection c;c.name=".text";c.rva=s->VirtualAddress;
  c.bytes.assign(data.begin()+s->PointerToRawData,data.begin()+s->PointerToRawData+std::min(s->SizeOfRawData,s->Misc.VirtualSize));sections.push_back(std::move(c));
 }return sections;
}
int main(int argc,char** argv){try{
 fingerprints();
 if(argc==2){auto s=read_sections(argv[1]);std::cout<<"{\"freeze\":"<<verify_feature(s,freeze_fingerprint(),false).json()<<",\"ui\":"<<verify_feature(s,ui_fingerprint(),false).json()<<"}\n";}
 return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
