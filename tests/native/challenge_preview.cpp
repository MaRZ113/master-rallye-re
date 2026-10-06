#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include "../../src/native/challenge_preview/roster.h"
static unsigned passed=0;
static void check(bool okay){if(!okay){std::fprintf(stderr,"case %u failed\n",passed+1);std::exit(1);}++passed;}
int main() {
    for(int event=0;event<=10;++event)for(mr::Policy policy:{mr::Stock,mr::Mixed,mr::Diverse}) {
        preview::Roster r;int calls=0;
        auto generate=[&](mr::Policy& p){++calls;p=policy;return 14;};
        check(r.prepare(event,0,23,true,generate)==(policy==mr::Stock?-1:14));
        check(calls==1&&r.serial==1);
        check(r.prepare(event,0,23,true,generate)==r.chosen&&calls==1);
        check(r.consume(event,0,23,true)==r.chosen&&calls==1);
        check(r.consume(event,0,23,true)==r.chosen&&calls==1);
        check(r.prepare(event,0,23,true,[&](mr::Policy& p){++calls;p=mr::Stock;return -1;})==r.chosen&&calls==1);
        check(r.consume((event+1)%11,0,23,true)==-1&&calls==1);
        check(r.prepare((event+1)%11,0,23,true,generate)==(policy==mr::Stock?-1:14)&&calls==2);
        r.clear();check(!r.ready);
        check(r.prepare(event,0,23,true,[&](mr::Policy& p){++calls;p=mr::Stock;return -1;})==-1&&calls==3);
    }
    for(int event:{-1,11,100}) {preview::Roster r;int calls=0;
        check(r.prepare(event,0,23,true,[&](mr::Policy&){++calls;return 14;})==-1&&!r.ready&&calls==0);}
    for(int human:{-1,25}) {preview::Roster r;
        check(r.prepare(10,human,23,true,[](mr::Policy&){return 14;})==-1&&!r.ready);}
    for(int opponent:{-1,25}) {preview::Roster r;
        check(r.prepare(10,0,opponent,true,[](mr::Policy&){return 14;})==-1&&!r.ready);}
    for(int chosen:{-1,0,25}) {preview::Roster r;
        check(r.prepare(10,0,23,true,[&](mr::Policy& p){p=mr::Mixed;return chosen;})==-1);}
    preview::Roster r;
    check(r.consume(10,0,23,true)==-1);
    check(r.prepare(10,0,23,false,[](mr::Policy&){return 14;})==-1&&!r.ready);
    r.prepare(10,0,23,true,[](mr::Policy& p){p=mr::Mixed;return 14;});
    check(r.consume(10,0,23,false)==-1);
    check(r.consume(10,1,23,true)==-1);
    check(r.consume(10,0,22,true)==-1);
    std::printf("{\"cases\":%u,\"passed\":%u,\"failed\":0,\"skipped\":0}\n",passed,passed);
}
