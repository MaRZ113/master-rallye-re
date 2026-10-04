#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wincrypt.h>
#include "policy.h"
#include "profiles.h" // generated only after exact candidate verification

// Research DLL does not install process hooks, use WPM, alter game files/saves,
// create participants or publish CarClass. EXE bridge supplies audited seams.
static char directory[MAX_PATH];
static int identity; // zero=unchecked, 1=supported, -1=reject
static mr::Cycle cycle;
static int activeMode=-1,expectedSlot;
static unsigned generation;
static char configHash[65];

template<class T> static T fn(unsigned address) { return reinterpret_cast<T>(address); }
typedef void* (__cdecl *Singleton)();
typedef int (__thiscall *Get)(void*);
typedef bool (__thiscall *GetBool)(void*); // retail Bool getter returns AL, not full EAX
typedef int (__thiscall *GetSlot)(void*,int);
typedef bool (__thiscall *Unlocked)(void*,int);
static void* race() { return fn<Singleton>(0x4ADA50)(); }
static void* competition() { return fn<Singleton>(0x4B0AF0)(); }
static int car(int mode,int slot) {
    return mode==mr::QuickRace||mode==mr::Challenge ?
        fn<GetSlot>(0x4AC660)(race(),slot):fn<GetSlot>(0x4B0630)(competition(),slot);
}
static int draw(void*,int upper) {
    typedef int (__thiscall *Range)(void*,int,int);
    return fn<Range>(0x4D1DF0)(fn<Singleton>(0x4D1E90)(),0,upper);
}
static bool path(char* out,const char* name) {
    unsigned n=0;while(directory[n]) {if(n+1>=MAX_PATH)return false;out[n]=directory[n];++n;}
    while(*name){if(n+1>=MAX_PATH)return false;out[n++]=*name++;}out[n]=0;return true;
}
static bool digest(HANDLE file,const BYTE* data,DWORD count,char* hex) {
    HCRYPTPROV provider=0;HCRYPTHASH hash=0;bool okay=false;BYTE result[32];
    if(!CryptAcquireContextA(&provider,0,0,PROV_RSA_AES,CRYPT_VERIFYCONTEXT))return false;
    if(CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)) {
        okay=true;
        if(file!=INVALID_HANDLE_VALUE) {
            BYTE buffer[4096];DWORD size;
            do {
                if(!ReadFile(file,buffer,sizeof(buffer),&size,0)||!CryptHashData(hash,buffer,size,0)){okay=false;break;}
            }while(size);
        }else okay=!!CryptHashData(hash,data,count,0);
        DWORD size=sizeof(result);
        okay=okay&&!!CryptGetHashParam(hash,HP_HASHVAL,result,&size,0)&&size==32;
        if(okay) {
            const char* digits="0123456789abcdef";
            for(unsigned i=0;i<32;++i){hex[2*i]=digits[result[i]>>4];hex[2*i+1]=digits[result[i]&15];}
            hex[64]=0;
        }
        CryptDestroyHash(hash);
    }
    CryptReleaseContext(provider,0);return okay;
}
static bool verify() {
    if(identity)return identity==1;
    identity=-1;
    HMODULE game=GetModuleHandleA(0);if(game!=reinterpret_cast<HMODULE>(0x400000))return false;
    char file[MAX_PATH];DWORD n=GetModuleFileNameA(game,file,MAX_PATH);
    if(!n||n>=MAX_PATH)return false;
    unsigned slash=n;while(slash&&file[slash-1]!='\\'&&file[slash-1]!='/')--slash;
    if(!slash)return false;for(unsigned i=0;i<slash;++i)directory[i]=file[i];directory[slash]=0;
    HANDLE input=CreateFileA(file,GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,0);
    if(input==INVALID_HANDLE_VALUE)return false;
    DWORD high=0,size=GetFileSize(input,&high);
    char hash[65];bool okay=!high&&size==3121214&&digest(input,0,0,hash);
    CloseHandle(input);
    if(!okay||(!mr::eq(hash,MR_FOUR_SHA)&&!mr::eq(hash,MR_FIVE_SHA)))return false;
    // Independently verify the live bridge and immutable stock entry bytes.
    for(unsigned i=0;i<MR_MEMORY_PIN_COUNT;++i) {
        const MemoryPin& p=MR_MEMORY_PINS[i];
        for(unsigned j=0;j<p.size;++j)
            if(*reinterpret_cast<const BYTE*>(p.address+j)!=p.bytes[j])return false;
    }
    identity=1;return true;
}
static mr::Config loadConfig() {
    mr::Config config;mr::defaults(config);configHash[0]=0;
    char name[MAX_PATH];if(!path(name,"MRallyeRandomizer.ini"))return config;
    HANDLE input=CreateFileA(name,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,0,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,0);
    if(input==INVALID_HANDLE_VALUE)return config;
    DWORD high=0,size=GetFileSize(input,&high),got=0;char buffer[4097];
    if(!high&&size<=4096&&ReadFile(input,buffer,size,&got,0)&&got==size) {
        digest(INVALID_HANDLE_VALUE,reinterpret_cast<BYTE*>(buffer),size,configHash);
        mr::parse(buffer,size,config);
    }
    CloseHandle(input);return config;
}
static unsigned eligibility(int mode,int slot,bool* unlocked) {
    for(int k=0;k<15;++k)unlocked[k]=false;
    if(mode!=mr::Invitation)for(int k=11;k<=14;++k)
        unlocked[k]=!!fn<Unlocked>(0x4AFB70)(fn<Singleton>(0x4B0310)(),k);
    unsigned mask=0;
    for(int id=0;id<25;++id)if(mr::eligible(id,mode,unlocked)) {
        bool used=false;for(int n=0;n<slot;++n)if(car(mode,n)==id)used=true;
        if(!used)mask|=1u<<(id<7?0:id<14?1:2);
    }
    return mask;
}
// Logging is optional, bounded, once per participant/generation; never per frame.
static void log(int mode,int count,int slot,int selected) {
    char filename[MAX_PATH];if(!path(filename,"MRallyeRandomizer.log"))return;
    HANDLE file=CreateFileA(filename,GENERIC_READ|FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
    if(file==INVALID_HANDLE_VALUE)return;
    // Stop writing at the cap; never truncate existing diagnostic evidence.
    DWORD high=0,logSize=GetFileSize(file,&high);
    char buffer[256];unsigned n=0;
    const char* text=mr::names[mode];while(*text&&n<80)buffer[n++]=*text++;
    const char* policy=cycle.policy==mr::Mixed?" Mixed":cycle.policy==mr::Diverse?" Diverse":" Stock";
    while(*policy)buffer[n++]=*policy++;
    buffer[n++]=' ';buffer[n++]=char('0'+count);buffer[n++]=' ';buffer[n++]=char('0'+slot);
    buffer[n++]=' ';buffer[n++]=selected<0?'-':char('0'+selected);
    buffer[n++]=' ';for(unsigned i=0;configHash[i]&&i<64;++i)buffer[n++]=configHash[i];
    buffer[n++]='\r';buffer[n++]='\n';DWORD written;
    if(!high&&logSize!=INVALID_FILE_SIZE&&logSize<=131072-n)WriteFile(file,buffer,n,&written,0);
    CloseHandle(file);
}
extern "C" int __stdcall MRChooseV1(int hint,int first,int count,int slot) {
    if(!verify())return -1;
    int mode=mr::mode(hint,fn<Get>(0x4ABE90)(race()));
    bool split=fn<GetBool>(0x4AE2D0)(fn<Singleton>(0x4AE700)());
    // Replay and Attract have no callers of these creation seams. Type and
    // first/count guards additionally reject their independent setup owners.
    bool network=fn<Get>(0x4AC0A0)(race())!=0;
    if(mode<0||!mr::context(first,count,slot,split,false,false,network))return -1;
    if(slot==first) {
        mr::Config config=loadConfig();cycle.begin(config.modes[mode],count);
        activeMode=mode;expectedSlot=first;++generation;
    }
    if(mode!=activeMode||slot!=expectedSlot||count!=cycle.count)return -1;
    ++expectedSlot;
    if(cycle.policy==mr::Stock){log(mode,count,slot,-1);return -1;}
    bool unlocked[15];unsigned mask=eligibility(mode,slot,unlocked);
    int selected=cycle.next(mask,draw,0);
    log(mode,count,slot,selected);return selected;
}
extern "C" int __stdcall MRChallengeV1(int hint,int first,int count,int slot) {
    int cls=MRChooseV1(hint,first,count,slot);if(cls<0)return -1;
    bool unlocked[15];eligibility(mr::Challenge,slot,unlocked);
    int pool[25],size=0;
    for(int id=0;id<25;++id)if((id<7?0:id<14?1:2)==cls&&
        mr::eligible(id,mr::Challenge,unlocked)&&id!=car(mr::Challenge,0))pool[size++]=id;
    if(!size)return -1;
    int index=draw(0,size);return index>=0&&index<size?pool[index]:-1;
}
extern "C" BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID) { return TRUE; }
