/* Exact-retail SDK supplemental SFX. No CRT, OS headers, physics writes or
   shared stock effect ownership. All mutable state is caller-owned RW/NX. */
typedef unsigned int U;
typedef unsigned char B;
typedef struct { U owner,voice[3],tick; float spool,load,cooldown; U events; float active; U public_state; } Slot;
typedef struct { U flags; const char *name[3]; float wh[7],sp[9],bov[8]; } Profile;
typedef struct { U key,actor; } Map;
typedef struct { U cursor; Map map[64]; Slot slot[64]; } State;
typedef void * (__cdecl *Alloc)(U);
typedef void (__cdecl *Free)(void *);
typedef void * (__thiscall *Ctor)(void *,U *);
typedef void (__thiscall *Intern)(U *,const char *);
typedef void (__thiscall *Dtor)(void *);
static float clamp(float x,float a,float b) { return x<a?a:(x>b?b:x); }
static Slot *find(State *s,U owner,int create) {
 U i; Slot *empty=0; for(i=0;i<64;i++){ if(s->slot[i].owner==owner)return &s->slot[i]; if(!s->slot[i].owner&&!empty)empty=&s->slot[i]; }
 if(create&&empty){empty->owner=owner;return empty;} return 0;
}
extern "C" void __cdecl layers_destroy(U owner,State *s) {
 Slot *v=find(s,owner,0);U i,others=0;if(!v)return;
 for(i=0;i<3;i++)if(v->voice[i]){((Dtor)0x4f64a0)((void*)v->voice[i]);((Free)0x5b4c00)((void*)v->voice[i]);v->voice[i]=0;}
 for(i=0;i<64;i++)if(s->slot[i].owner&&s->slot[i].owner!=owner)others++;
 for(i=0;i<64;i++)if(!others||(v->public_state&&s->map[i].key==v->public_state)){s->map[i].key=0;s->map[i].actor=0;}
 if(!others)s->cursor=0;
 v->public_state=0;
 v->owner=v->tick=v->events=0;v->spool=v->load=v->cooldown=v->active=0;
}
extern "C" void __cdecl layers_construct(U owner,Profile *p,State *s) {
 Slot *v; U i,h,others=0; void *a; layers_destroy(owner,s);
 for(i=0;i<64;i++)if(s->slot[i].owner)others++;
 if(!others){for(i=0;i<64;i++){s->map[i].key=0;s->map[i].actor=0;}s->cursor=0;}
 v=find(s,owner,1);if(!v)return;
 for(i=0;i<3;i++)if(p->flags&(1u<<i)){
  a=((Alloc)0x5c1cb4)(0x5c);if(!a)continue;
  ((Intern)0x4d0580)(&h,p->name[i]);((Ctor)0x4f63d0)(a,&h);v->voice[i]=(U)a;
  *(float*)((B*)a+0x10)=0;*(float*)((B*)a+0x18)=10;*(float*)((B*)a+0x1c)=200;
  *((B*)a+0xe)=(B)(i!=2);*((B*)a+0xf)=(B)(i!=2);
 }
}
/* now is original imported timeGetTime milliseconds, modulo-safe subtraction.
   Long gaps are capped; paused/menu time must not produce a spool jump. */
extern "C" void __cdecl layers_update(U owner,Profile *p,State *s,U now,float volume,int finished,U public_state) {
 Slot *v=find(s,owner,0);U i,actor=0,engine,entity,elapsed;float rpm,load,dt,target,tau,pitch,gain,fall,old;
 if(!v)return;
 v->public_state=public_state;
 elapsed=now-v->tick;dt=v->tick?clamp((float)elapsed*.001f,0,.1f):0;v->tick=now;
 entity=*(U*)(owner+0xc);entity=entity?*(U*)(entity+0x28):0;
 for(i=0;i<3;i++)if(v->voice[i]){*(float*)(v->voice[i]+0x10)=0;*(U*)(v->voice[i]+0x24)=entity;*(B*)(v->voice[i]+4)=1;}
 for(i=0;i<64;i++)if(s->map[i].key==public_state){actor=s->map[i].actor;break;}
 if(!actor)return;engine=*(U*)(actor+0x10);if(!engine)return;
 rpm=*(float*)(engine+0x28);rpm=rpm<0?-rpm:rpm;rpm*=9.5492966f;
 if(!(rpm>=0&&rpm<=30000))return;
 load=*(float*)(engine+0x50);if(!(load>=1&&load<=100000))return;
 target=*(float*)(engine+0x94);if(!(target>=-10000000&&target<=10000000&&volume>=0&&volume<=100))return;
 load=clamp(target/load,0,1);volume=clamp(volume,0,1);
 old=v->spool;target=clamp((load-p->sp[5])/(1-p->sp[5]),0,1)*clamp(rpm/p->sp[4],0,1);
 if(finished||(p->sp[8]!=0&&*(U*)(engine+0x78)==1))target=0;
 if(v->cooldown>0)v->cooldown=clamp(v->cooldown-dt,0,100);
 fall=dt>0?(v->load-load)/dt:0;v->load=load;
 if(v->voice[2]&&!finished&&(p->bov[7]==0||*(U*)(engine+0x78)!=1)&&rpm>=p->bov[6]&&old>=p->bov[1]&&fall>=p->bov[0]&&v->cooldown==0&&*(B*)(v->voice[2]+0xe)==0){
  v->events++;v->cooldown=p->bov[4];v->active=p->bov[2]*old;
  pitch=1+p->bov[3]*((float)((v->events*1664525u+1013904223u)&65535)/32767.5f-1);
  *(float*)(v->voice[2]+0x14)=pitch;*(B*)(v->voice[2]+0xe)=1;
 }
 tau=target>old?p->sp[6]:((v->voice[2]&&*(B*)(v->voice[2]+0xe))?p->bov[5]:p->sp[7]);v->spool+=dt/(tau+dt)*(target-v->spool);
 if(v->voice[0]){
  pitch=clamp(rpm/p->wh[0],p->wh[1],p->wh[2]);gain=(p->wh[4]+(p->wh[3]-p->wh[4])*load)*clamp(rpm/p->wh[5],0,1)*volume;
  if(finished||(p->wh[6]!=0&&*(U*)(engine+0x78)==1))gain=0;
  *(float*)(v->voice[0]+0x14)=pitch;*(float*)(v->voice[0]+0x10)=gain;
 }
 if(v->voice[1]){
  *(float*)(v->voice[1]+0x14)=clamp(rpm/p->sp[0],p->sp[1],p->sp[2]);
  *(float*)(v->voice[1]+0x10)=finished?0:p->sp[3]*v->spool*volume;
 }
 if(v->voice[2])*(float*)(v->voice[2]+0x10)=finished?0:v->active*volume;
}
