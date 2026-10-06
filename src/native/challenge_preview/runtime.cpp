// Reuse the closed R-AI1.2 implementation without editing its source or policy.
#define MRChallengeV1 MRChallengeLegacyV1
#include "../randomizer/runtime.cpp"
#undef MRChallengeV1
#include "roster.h"
#include <cstdio>

static preview::Roster selected;
static char selectedConfigHash[65];
static bool safeChallenge() {
    return !fn<GetBool>(0x4AE2D0)(fn<Singleton>(0x4AE700)())&&
        fn<Get>(0x4AC0A0)(race())==0;
}
static bool authored(int event,int human,int opponent) {
    if(!preview::Roster::valid(event,human,opponent))return false;
    BYTE* registry=reinterpret_cast<BYTE*>(fn<Singleton>(0x45A3C0)());
    return registry&&*reinterpret_cast<int*>(registry+0x570+(event+25)*0x2c)==human&&
        *reinterpret_cast<int*>(registry+0x574+(event+25)*0x2c)==opponent;
}
// Separate event/identity diagnostics. Not a Broker Dump or visual proof.
static void trace(const char* action) {
    char filename[MAX_PATH];if(!path(filename,"MRallyeRandomizer.log"))return;
    HANDLE file=CreateFileA(filename,GENERIC_READ|FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
    if(file==INVALID_HANDLE_VALUE)return;
    char buffer[256];
    const char* policy=selected.policy==mr::Mixed?"Mixed":selected.policy==mr::Diverse?"Diverse":"Stock";
    int id=selected.chosen<0?selected.authored:selected.chosen;
    int cls=id<7?0:id<14?1:2;
    int n=std::snprintf(buffer,sizeof(buffer),"PreviewV1 %s %u %d %s %d %d %s %lu\r\n",action,selected.serial,selected.event,policy,id,cls,selectedConfigHash,GetCurrentProcessId());
    DWORD high=0,size=GetFileSize(file,&high),written;
    if(n>0&&n<int(sizeof(buffer))&&!high&&size!=INVALID_FILE_SIZE&&size<=131072-DWORD(n))
        WriteFile(file,buffer,DWORD(n),&written,0);
    CloseHandle(file);
}
extern "C" int __stdcall MRChallengeV1(int hint,int first,int count,int slot) {
    if(!verify()||hint!=mr::Challenge)return -1;
    if(first==-100){selected.clear();return -1;} // audited screen entry / Back
    if(first>=100&&first<=110) {
        int event=first-100,human=count,opponent=slot;
        bool safe=safeChallenge()&&authored(event,human,opponent);
        bool cached=safe&&selected.matches(event,human,opponent);
        int result=selected.prepare(event,human,opponent,safe,[&](mr::Policy& policy) {
            mr::Config config=loadConfig();policy=config.modes[mr::Challenge];
            for(unsigned n=0;n<65;++n)selectedConfigHash[n]=configHash[n];
            mr::Cycle local;local.begin(policy,1);
            bool unlocked[15]={};
            for(int k=11;k<=14;++k)unlocked[k]=fn<Unlocked>(0x4AFB70)(fn<Singleton>(0x4B0310)(),k);
            unsigned mask=0;
            for(int id=0;id<25;++id)if(id!=human&&mr::eligible(id,mr::Challenge,unlocked))
                mask|=1u<<(id<7?0:id<14?1:2);
            int cls=local.next(mask,draw,0);
            // Keep the V1 diagnostic generation format; no general cycle mutation.
            mr::Cycle saved=cycle;cycle.policy=policy;log(mr::Challenge,1,1,cls);cycle=saved;
            if(cls<0)return -1;
            int pool[25],size=0;
            for(int id=0;id<25;++id)if(id!=human&&(id<7?0:id<14?1:2)==cls&&mr::eligible(id,mr::Challenge,unlocked))pool[size++]=id;
            if(!size)return -1;
            int index=draw(0,size);
            return index>=0&&index<size?pool[index]:-1;
        });
        if(safe&&!cached)trace("Begin");
        return result;
    }
    if(first!=1||count!=1||slot!=1||!safeChallenge()||fn<Get>(0x4ABE90)(race())!=7)return -1;
    int event=fn<Get>(0x4ABF20)(race())-25,human=car(mr::Challenge,0);
    if(!selected.ready||!authored(event,human,selected.authored))return -1;
    int result=selected.consume(event,human,selected.authored,true);
    if(selected.matches(event,human,selected.authored))trace("Use");
    // NO config read / class or vehicle RNG at Start; missed preview fails Stock.
    return result;
}
