/* Tokyo Xtreme Racer 3 / Shutokou Battle 01 (PS2, SLPM-65308) BUILD.TOC + BUILD.DAT unpacker.
   TOC: 0x38-based records of five u32 (sector, packed size, sectors, 0, unpacked size).
   Payload: uclpack container, magic 00 E9 55 43 4C FF 01 1A, method 0x2B decoded as
   NRV2B with a 32-bit little-endian bit buffer (verified on the corpus).
   usage: genki_unpack <game dir> <out dir> [first] [last]  -> out/NNNNN.bin + index.tsv */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static uint32_t be32(const uint8_t*p){return (uint32_t)p[0]<<24|p[1]<<16|p[2]<<8|p[3];}
static long nrv2b_le32(const uint8_t*src,size_t ilen,uint8_t*dst,size_t olen){
  size_t ip=0,op=0;uint32_t bb=0;int bc=0;uint32_t last=1;
#define BIT() (bc==0?(ip+4>ilen?-1:(bb=src[ip]|src[ip+1]<<8|src[ip+2]<<16|(uint32_t)src[ip+3]<<24,ip+=4,bc=32,(int)((bb>>--bc)&1))):(int)((bb>>--bc)&1))
  for(;;){int b;
    while((b=BIT())==1){if(ip>=ilen||op>=olen)return -1;dst[op++]=src[ip++];}
    if(b<0)return -1;
    uint32_t m_off=1;
    for(;;){b=BIT();if(b<0)return -1;m_off=m_off*2+b;b=BIT();if(b<0)return -1;if(b)break;if(m_off>0x1000000)return -1;}
    if(m_off==2)m_off=last;
    else{if(ip>=ilen)return -1;m_off=(m_off-3)*256+src[ip++];if(m_off==0xffffffffu)break;last=++m_off;}
    uint32_t m_len=BIT();m_len=m_len*2+BIT();
    if(m_len==0){m_len=1;for(;;){b=BIT();if(b<0)return -1;m_len=m_len*2+b;b=BIT();if(b<0)return -1;if(b)break;}m_len+=2;}
    m_len+=(m_off>0xd00);
    if(m_off>op||op+m_len+1>olen)return -1;
    for(uint32_t k=0;k<=m_len;k++){dst[op]=dst[op-m_off];op++;}
  }
  return (long)op;
}
int main(int c,char**v){
  if(c<3){fprintf(stderr,"usage\n");return 2;}
  char p[1024];snprintf(p,sizeof p,"%s/BUILD.TOC",v[1]);FILE*t=fopen(p,"rb");if(!t)return 3;
  fseek(t,0,SEEK_END);long tl=ftell(t);fseek(t,0,SEEK_SET);uint8_t*T=malloc(tl);fread(T,1,tl,t);fclose(t);
  snprintf(p,sizeof p,"%s/BUILD.DAT",v[1]);FILE*d=fopen(p,"rb");if(!d)return 4;
  int n=(int)((tl-0x38)/20),first=c>3?atoi(v[3]):0,last=c>4?atoi(v[4]):n-1;
  snprintf(p,sizeof p,"%s/index.tsv",v[2]);FILE*ix=fopen(p,first?"ab":"wb");
  for(int i=first;i<=last&&i<n;i++){uint32_t r[5];memcpy(r,T+0x38+20*i,20);
    uint8_t*raw=malloc(r[1]?r[1]:1);_fseeki64(d,(long long)r[0]*2048,SEEK_SET);fread(raw,1,r[1],d);
    uint8_t*out=raw;size_t ol=r[1];const char*st="raw";
    if(r[1]>=26&&!memcmp(raw,"\x00\xe9UCL\xff\x01\x1a",8)){
      size_t total=r[4]?r[4]:16u<<20;out=malloc(total+16);size_t o=18;ol=0;st="ucl";
      for(;;){if(o+4>r[1]){st="trunc";break;}uint32_t bl=be32(raw+o);o+=4;if(!bl)break;uint32_t il=be32(raw+o);o+=4;
        if(o+il>r[1]||ol+bl>total){st="bad";break;}
        if(il==bl)memcpy(out+ol,raw+o,il);else if(nrv2b_le32(raw+o,il,out+ol,bl)!=(long)bl){st="bad";break;}
        ol+=bl;o+=il;}
    }
    snprintf(p,sizeof p,"%s/%05d.bin",v[2],i);FILE*f=fopen(p,"wb");fwrite(out,1,ol,f);fclose(f);
    fprintf(ix,"%d\t%u\t%u\t%u\t%zu\t%s\t%.4s\n",i,r[0],r[1],r[4],ol,st,ol>=4?(char*)out:"");
    if(out!=raw)free(out);free(raw);
  }
  fclose(ix);return 0;}
