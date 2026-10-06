#pragma once
#include "../randomizer/policy.h"

namespace preview {
// Process-local identity only; native Race/Car1 owns the actual driver/class.
struct Roster {
    bool ready=false;
    int event=-1,human=-1,authored=-1,chosen=-1;
    unsigned serial=0;
    mr::Policy policy=mr::Stock;
    void clear() { ready=false;event=human=authored=chosen=-1;policy=mr::Stock; }
    bool matches(int e,int h,int a) const {
        return ready&&e==event&&h==human&&a==authored;
    }
    static bool valid(int e,int h,int a) { return e>=0&&e<=10&&h>=0&&h<=24&&a>=0&&a<=24; }
    template<class Generate> int prepare(int e,int h,int a,bool safe,Generate generate) {
        if(!safe||!valid(e,h,a)){clear();return -1;}
        if(matches(e,h,a))return chosen;
        clear();event=e;human=h;authored=a;ready=true;++serial;
        chosen=generate(policy);
        if(policy==mr::Stock||chosen<0||chosen>24||chosen==human)chosen=-1;
        return chosen;
    }
    int consume(int e,int h,int a,bool safe) const {
        return safe&&matches(e,h,a)?chosen:-1;
    }
};
}
