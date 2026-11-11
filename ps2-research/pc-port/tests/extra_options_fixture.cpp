#include <windows.h>
#include <cstring>
#include <vector>
namespace {unsigned abi=0x45583201u,kind=2,revision=1,texture_index=0,texture_width=1,texture_height=1;
 std::vector<unsigned char> expected{0x11,0x22,0x33,0x80};}
extern "C" unsigned WINAPI MRExtraOptionsAbi(){return abi;}
extern "C" void WINAPI ExtraFixtureSet(unsigned a,unsigned k,unsigned r){abi=a;kind=k;revision=r;}
extern "C" void WINAPI ExtraFixtureTemplate(unsigned i,unsigned w,unsigned h,const void* data,unsigned bytes){
 texture_index=i;texture_width=w;texture_height=h;const auto* p=static_cast<const unsigned char*>(data);expected.assign(p,p+bytes);
}
extern "C" unsigned WINAPI MRExtraVisualV2(const char* family,int participant,unsigned phase){
 return family&&(!std::strcmp(family,"Tata")||!std::strcmp(family,"Xtrail"))&&(phase==0||(phase==1&&participant==0))?kind:0;
}
extern "C" unsigned WINAPI MRExtraVisualV1(const char* family,int participant,unsigned phase){return MRExtraVisualV2(family,participant,phase)==1?1u:0u;}
extern "C" unsigned WINAPI MRExtraRevisionV1(const char*,int,unsigned){return revision;}
extern "C" BOOL WINAPI MRExtraTextureV1(const char* family,unsigned index,unsigned w,unsigned h,const void* src,void* dst,unsigned bytes,int participant,unsigned phase){
 if(MRExtraVisualV2(family,participant,phase)!=3||index!=texture_index||w!=texture_width||h!=texture_height||bytes!=expected.size()||!bytes||!src||!dst||std::memcmp(src,expected.data(),bytes))return FALSE;
 std::memcpy(dst,src,bytes);static_cast<unsigned char*>(dst)[0]^=0x55;return TRUE;
}
