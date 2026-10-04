#include <cstdio>
#include <cstring>
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "../../src/native/randomizer/policy.h"
static unsigned seed=1,calls;
static int rng(void*,int upper) {++calls;seed=seed*1664525u+1013904223u;return int(seed%unsigned(upper));}
static int failures,cases;
// Model a retail byte-return getter with deliberately nonzero upper EAX bits.
__declspec(naked) bool __stdcall falseFlag() {
    __asm {
        mov eax,12345600h
        ret
    }
}
__declspec(naked) bool __stdcall trueFlag() {
    __asm {
        mov eax,12345601h
        ret
    }
}
static void check(bool pass) {++cases;if(!pass){++failures;std::printf("FAILED case %d\n",cases);}}
static mr::Config parse(const char* s,bool* okay=0) {
    char buffer[4097];unsigned n=unsigned(std::strlen(s));std::memcpy(buffer,s,n);
    mr::Config c;bool p=mr::parse(buffer,n,c);if(okay)*okay=p;return c;
}
int main(int argc,char** argv) {
    check(!falseFlag());check(trueFlag());
    const char* invalid[]={"","[OpponentRandomizer]\nQuickRace=Mixed",
        "[OpponentRandomizer]\nConfigVersion=2\nQuickRace=Mixed",
        "[OpponentRandomizer]\nConfigVersion=1\nConfigVersion=1\nQuickRace=Mixed",
        "[OpponentRandomizer]\nConfigVersion=1\nQuickRace=Mixed\nQUICKRACE=Diverse",
        "[OpponentRandomizer]\nConfigVersion=1\nQuickRace=Mixed\nBrokenLine",
        "[OpponentRandomizer]\nConfigVersion=1\nUnknownKey=Mixed",
        "[Other]\nConfigVersion=1\nQuickRace=Mixed",
        "[OpponentRandomizer]\nConfigVersion:1\nQuickRace=Mixed",
        "[OpponentRandomizer]\nConfigVersion=1\nQuickRace=Mixed\n  continued",
        "[OpponentRandomizer]\nConfigVersion=1\v\nQuickRace=Mixed"};
    for(const char* s:invalid){mr::Config c=parse(s);for(auto p:c.modes)check(p==mr::Stock);}
    mr::Config config=parse("[opponentrandomizer]\nConfigVersion=1\nQuickRace=mIxEd\nChallenge=bad\nInvitation=Diverse");
    check(config.modes[mr::QuickRace]==mr::Mixed);check(config.modes[mr::Challenge]==mr::Stock);
    check(config.modes[mr::Invitation]==mr::Diverse);check(config.modes[mr::MasterRallye]==mr::Stock);
    char huge[4098]={};mr::Config c;check(!mr::parse(huge,4097,c));
    char nul[]={ '[',0,']',0 };check(!mr::parse(nul,3,c));
    char nonAscii[]={char(-1),0};check(!mr::parse(nonAscii,1,c));
    for(int mode=0;mode<5;++mode) {
        const int hints[]={0,1,2,2,4},types[]={2,7,6,8,5};
        check(mr::mode(hints[mode],types[mode])==mode);
        check(mr::mode(hints[mode],99)==-1);
        for(int count=0;count<=4;++count)for(int policy=0;policy<3;++policy)for(unsigned mask=1;mask<=7;++mask) {
            mr::Cycle cycle;cycle.begin(mr::Policy(policy),count);calls=0;
            unsigned seen=0;int perCycle=0,eligibleCount=0;
            for(int i=0;i<3;++i)if(mask&(1u<<i))++eligibleCount;
            for(int slot=1;slot<=count;++slot) {
                int selected=cycle.next(mask,rng,0);
                if(policy==mr::Stock)check(selected==-1);
                else {
                    check(selected>=0&&selected<3&&(mask&(1u<<selected)));
                    if(policy==mr::Diverse) {
                        if(perCycle==eligibleCount){seen=0;perCycle=0;}
                        check(!(seen&(1u<<selected)));seen|=1u<<selected;++perCycle;
                    }
                }
            }
            if(policy==mr::Stock||count==0)check(calls==0);
            if(policy==mr::Mixed&&count)check(calls==unsigned(count));
            check(cycle.next(mask,rng,0)==-1);
        }
    }
    check(!mr::context(1,0,1,false,false,false,false));
    check(!mr::context(1,4,5,false,false,false,false)); // no active Car5
    check(!mr::context(2,2,2,true,false,false,false));
    check(!mr::context(1,3,1,false,true,false,false));
    check(!mr::context(1,3,1,false,false,true,false));
    check(!mr::context(1,3,1,false,false,false,true));
    for(int count=1;count<=4;++count)for(int slot=1;slot<=count;++slot)
        check(mr::context(1,count,slot,false,false,false,false));
    mr::Cycle cycle;cycle.begin(mr::Diverse,4);check(cycle.next(0,rng,0)==-1);
    bool unlocks[15]={};
    for(int mode=0;mode<5;++mode)for(int id=0;id<25;++id)
        check(mr::eligible(id,mode,unlocks)==(id<=20));
    unlocks[11]=true;check(mr::eligible(21,mr::MasterRallye,unlocks));
    check(!mr::eligible(21,mr::Invitation,unlocks));
    if(argc>1) {
        HMODULE dll=LoadLibraryA(argv[1]);check(dll!=0);
        if(dll) {
            typedef int (__stdcall *Callback)(int,int,int,int);
            Callback choose=reinterpret_cast<Callback>(GetProcAddress(dll,"MRChooseV1"));
            Callback challenge=reinterpret_cast<Callback>(GetProcAddress(dll,"MRChallengeV1"));
            check(choose!=0);check(challenge!=0);
            if(choose)check(choose(0,1,3,1)==-1); // this executable is NOT a supported game
            if(challenge)check(challenge(1,1,1,1)==-1);
            check(!!FreeLibrary(dll));
        }
    }
    std::printf("{\"cases\":%d,\"passed\":%d,\"failed\":%d,\"skipped\":0}\n",cases,cases-failures,failures);
    return failures?1:0;
}
