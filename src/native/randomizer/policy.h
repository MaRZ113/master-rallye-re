#pragma once
// No OS, game ABI, heap, persistence or renderer knowledge in this layer.
namespace mr {
enum Policy { Stock, Mixed, Diverse };
enum Mode { QuickRace, Challenge, RallyeCup, Invitation, MasterRallye, ModeCount };
static const char* const names[] = {"QuickRace","Challenge","RallyeCup","Invitation","MasterRallye"};
struct Config { Policy modes[ModeCount]; };
inline char lower(char c) { return c>='A'&&c<='Z' ? char(c+32) : c; }
inline bool eq(const char* a, const char* b) {
    while (*a && *b && lower(*a)==lower(*b)) { ++a; ++b; }
    return *a==*b;
}
inline void defaults(Config& c) { for(int i=0;i<ModeCount;++i)c.modes[i]=Stock; }
inline bool space(char c) { return c==' '||c=='\t'||c=='\r'; }
inline char* trim(char* s) {
    while(space(*s))++s;
    char* e=s;while(*e)++e;
    while(e>s&&space(e[-1]))--e;*e=0;return s;
}
inline bool parse(char* data, unsigned size, Config& output) {
    defaults(output);
    if(!data||size>4096)return false;
    for(unsigned n=0;n<size;++n)
        if(data[n]==0||static_cast<unsigned char>(data[n])>127)return false;
    data[size]=0;
    Config temp;defaults(temp);bool section=false,seenSection=false;
    unsigned seen=0;bool version=false;
    char* cursor=data;
    while(*cursor) {
        char* line=cursor;while(*cursor&&*cursor!='\n')++cursor;
        if(*cursor)*cursor++=0;
        line=trim(line);if(!*line||*line==';'||*line=='#')continue;
        if(*line=='[') {
            char* end=line;while(*end)++end;
            if(end<=line+2||end[-1]!=']')return false;
            end[-1]=0;
            if(!eq(line+1,"OpponentRandomizer")||seenSection)return false;
            section=seenSection=true;continue;
        }
        if(!section)return false;
        char* equal=line;while(*equal&&*equal!='=')++equal;
        if(!*equal)return false;*equal++=0;
        char* key=trim(line);char* value=trim(equal);
        if(eq(key,"ConfigVersion")) {
            if(seen&32)return false;seen|=32;version=eq(value,"1");continue;
        }
        bool known=false;
        for(int i=0;i<ModeCount;++i)if(eq(key,names[i])) {
            known=true;
            if(seen&(1u<<i))return false;seen|=1u<<i;
            temp.modes[i]=eq(value,"Mixed")?Mixed:eq(value,"Diverse")?Diverse:Stock;
        }
        if(!known)return false;
    }
    if(!version)return false;
    output=temp;return true;
}

typedef int (*Draw)(void*, int); // native integer range [0, upper)
struct Cycle {
    Policy policy;int count;int nextSlot;int order[3];int used;int size;
    void begin(Policy p,int n) {policy=p;count=n;nextSlot=1;used=size=0;}
    int next(unsigned mask,Draw draw,void* state) {
        if(policy==Stock||count<1||count>4||nextSlot>count||!mask||mask>7)return -1;
        ++nextSlot;
        int available[3],n=0;
        for(int i=0;i<3;++i)if(mask&(1u<<i))available[n++]=i;
        if(policy==Mixed) {
            int chosen=draw(state,n);return chosen>=0&&chosen<n?available[chosen]:-1;
        }
        // Remove unavailable classes from the unconsumed cycle. Never index
        // an empty vector if eligibility changes between participant choices.
        int tail=used;
        for(int i=used;i<size;++i)if(mask&(1u<<order[i]))order[tail++]=order[i];
        size=tail;
        if(used==size) {
            used=0;size=n;for(int i=0;i<n;++i)order[i]=available[i];
            for(int i=n-1;i>0;--i) {
                int j=draw(state,i+1);if(j<0||j>i)return -1;
                int t=order[i];order[i]=order[j];order[j]=t;
            }
        }
        return order[used++];
    }
};
inline int mode(int hint,int type) {
    if(hint==QuickRace&&type==2)return QuickRace;
    if(hint==Challenge&&type==7)return Challenge;
    if(hint==RallyeCup&&type==6)return RallyeCup;
    if(hint==RallyeCup&&type==8)return Invitation;
    if(hint==MasterRallye&&type==5)return MasterRallye;
    return -1;
}
inline bool context(int first,int count,int slot,bool split,bool replay,bool attract,bool network) {
    return first==1&&count>=1&&count<=4&&slot>=first&&slot<first+count&&
        !split&&!replay&&!attract&&!network;
}
inline bool eligible(int id,int mode,const bool* unlocked) {
    if(id<0||id>24)return false;
    if(id<=20)return true;
    if(mode==Invitation)return false;
    static const int keys[]={11,12,13,14};
    return unlocked[keys[id-21]];
}
}
