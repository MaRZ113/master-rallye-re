#pragma once
// COLLISION-DEBUG1 round 3: read-only access to the game's Data.sma (a ZIP of local file headers; the retail archive
// has no usable central directory, so entries are indexed by walking the local headers). Methods: stored (0) and
// deflate (8, RFC 1951, decoder below). Every extracted member is checked against its CRC-32 and size.
// Portable: no D3D, no Windows (tests/collision_debug_tests.cpp compares it with Data.sma_unpacked).
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace gfx2::sma {

inline uint32_t crc32(const uint8_t* p,size_t n) noexcept {
    static const auto table=[]{std::array<uint32_t,256> t{};for(uint32_t i=0;i<256;++i){uint32_t c=i;for(int k=0;k<8;++k)c=c&1?0xedb88320u^(c>>1):c>>1;t[i]=c;}return t;}();
    uint32_t c=0xffffffffu;for(size_t i=0;i<n;++i)c=table[(c^p[i])&0xff]^(c>>8);return c^0xffffffffu;
}

// Raw DEFLATE (RFC 1951) into `out` (pre-sized to the expected length). Returns false on any malformed input.
class Inflater {
    const uint8_t* in_;size_t n_,pos_=0;uint32_t bits_=0;int count_=0;
    std::vector<uint8_t>& out_;size_t at_=0;
    struct Huffman { std::array<uint16_t,16> counts{}; std::array<uint16_t,320> symbols{}; };
    bool need(int k) noexcept {while(count_<k){if(pos_>=n_)return false;bits_|=uint32_t(in_[pos_++])<<count_;count_+=8;}return true;}
    bool get(int k,uint32_t& v) noexcept {if(!k){v=0;return true;}if(!need(k))return false;v=bits_&((1u<<k)-1);bits_>>=k;count_-=k;return true;}
    static bool build(Huffman& h,const uint8_t* lengths,int n) noexcept {
        h.counts.fill(0);for(int i=0;i<n;++i)++h.counts[lengths[i]];
        h.counts[0]=0;int left=1;for(int l=1;l<16;++l){left<<=1;left-=h.counts[l];if(left<0)return false;}
        std::array<uint16_t,16> offs{};for(int l=1;l<15;++l)offs[l+1]=static_cast<uint16_t>(offs[l]+h.counts[l]);
        for(int i=0;i<n;++i)if(lengths[i])h.symbols[offs[lengths[i]]++]=static_cast<uint16_t>(i);
        return true;
    }
    bool decode(const Huffman& h,int& symbol) noexcept {
        int code=0,first=0,index=0;
        for(int l=1;l<16;++l){uint32_t b;if(!get(1,b))return false;code|=int(b);const int c=h.counts[l];
            if(code-c<first){symbol=h.symbols[index+(code-first)];return true;}
            index+=c;first+=c;first<<=1;code<<=1;}
        return false;
    }
    bool put(uint8_t b) noexcept {if(at_>=out_.size())return false;out_[at_++]=b;return true;}
    bool codes(const Huffman& lit,const Huffman& dist) noexcept {
        static constexpr uint16_t lbase[29]={3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258};
        static constexpr uint8_t lextra[29]={0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0};
        static constexpr uint16_t dbase[30]={1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577};
        static constexpr uint8_t dextra[30]={0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13};
        for(;;){
            int s;if(!decode(lit,s))return false;
            if(s<256){if(!put(static_cast<uint8_t>(s)))return false;continue;}
            if(s==256)return true;
            s-=257;if(s>=29)return false;
            uint32_t e;if(!get(lextra[s],e))return false;const size_t len=lbase[s]+e;
            int ds;if(!decode(dist,ds)||ds>=30)return false;
            if(!get(dextra[ds],e))return false;const size_t d=dbase[ds]+e;
            if(d>at_||len>out_.size()-at_)return false;
            for(size_t i=0;i<len;++i){out_[at_]=out_[at_-d];++at_;}
        }
    }
public:
    Inflater(const uint8_t* in,size_t n,std::vector<uint8_t>& out) noexcept:in_(in),n_(n),out_(out){}
    bool run() noexcept {
        static Huffman fixed_lit,fixed_dist;static bool fixed_ready=false;
        if(!fixed_ready){uint8_t l[288];int i=0;for(;i<144;++i)l[i]=8;for(;i<256;++i)l[i]=9;for(;i<280;++i)l[i]=7;for(;i<288;++i)l[i]=8;
            build(fixed_lit,l,288);uint8_t d[30];std::fill(d,d+30,uint8_t(5));build(fixed_dist,d,30);fixed_ready=true;}
        uint32_t last=0;
        do{
            uint32_t type;if(!get(1,last)||!get(2,type))return false;
            if(type==0){
                bits_=0;count_=0;if(n_-pos_<4)return false;
                const uint16_t len=uint16_t(in_[pos_]|in_[pos_+1]<<8),nlen=uint16_t(in_[pos_+2]|in_[pos_+3]<<8);pos_+=4;
                if(uint16_t(~nlen)!=len||n_-pos_<len||out_.size()-at_<len)return false;
                std::memcpy(out_.data()+at_,in_+pos_,len);pos_+=len;at_+=len;
            }else if(type==1){if(!codes(fixed_lit,fixed_dist))return false;}
            else if(type==2){
                uint32_t hlit,hdist,hclen;if(!get(5,hlit)||!get(5,hdist)||!get(4,hclen))return false;
                hlit+=257;hdist+=1;hclen+=4;if(hlit>286||hdist>30)return false;
                static constexpr uint8_t order[19]={16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15};
                uint8_t lengths[320]{};for(uint32_t i=0;i<hclen;++i){uint32_t v;if(!get(3,v))return false;lengths[order[i]]=uint8_t(v);}
                Huffman lencode;if(!build(lencode,lengths,19))return false;
                std::fill(lengths,lengths+320,uint8_t(0));uint32_t index=0;
                while(index<hlit+hdist){
                    int s;if(!decode(lencode,s))return false;
                    if(s<16){lengths[index++]=uint8_t(s);continue;}
                    uint8_t value=0;uint32_t repeat=0,e=0;
                    if(s==16){if(!index||!get(2,e))return false;value=lengths[index-1];repeat=3+e;}
                    else if(s==17){if(!get(3,e))return false;repeat=3+e;}
                    else{if(!get(7,e))return false;repeat=11+e;}
                    if(index+repeat>hlit+hdist)return false;
                    while(repeat--)lengths[index++]=value;
                }
                if(!lengths[256])return false;
                Huffman lit,dist;if(!build(lit,lengths,int(hlit))||!build(dist,lengths+hlit,int(hdist)))return false;
                if(!codes(lit,dist))return false;
            }else return false;
        }while(!last);
        return at_==out_.size();
    }
};

struct Entry { uint64_t data=0; uint32_t method=0,compressed=0,size=0,crc=0; };

inline std::string key_of(std::string_view name) {
    std::string k(name);for(auto& c:k){if(c=='\\')c='/';else if(c>='A'&&c<='Z')c=static_cast<char>(c-'A'+'a');}return k;
}

class Archive {
    std::wstring path_;
    std::unordered_map<std::string,Entry> index_;
    bool open_=false;
public:
    // Walks the local headers once (names only, no data read).
    bool open(const std::wstring& path) {
        index_.clear();open_=false;path_=path;
        std::ifstream f(path,std::ios::binary);if(!f)return false;
        uint64_t at=0;uint8_t h[30];
        for(int guard=0;guard<2000000;++guard){
            f.seekg(static_cast<std::streamoff>(at));if(!f.read(reinterpret_cast<char*>(h),30))break;
            uint32_t sig;std::memcpy(&sig,h,4);if(sig!=0x04034b50u)break;
            uint16_t flags,method,nlen,xlen;uint32_t crc,csize,usize;
            std::memcpy(&flags,h+6,2);std::memcpy(&method,h+8,2);std::memcpy(&crc,h+14,4);std::memcpy(&csize,h+18,4);std::memcpy(&usize,h+22,4);
            std::memcpy(&nlen,h+26,2);std::memcpy(&xlen,h+28,2);
            if(flags&0x8)return false;   // data descriptors are not used by Data.sma
            std::string name(nlen,'\0');if(!f.read(name.data(),nlen))return false;
            Entry e;e.data=at+30+nlen+xlen;e.method=method;e.compressed=csize;e.size=usize;e.crc=crc;
            index_[key_of(name)]=e;
            at=e.data+csize;
        }
        open_=!index_.empty();return open_;
    }
    bool is_open()const noexcept{return open_;}
    size_t size()const noexcept{return index_.size();}
    const Entry* find(std::string_view name)const {const auto it=index_.find(key_of(name));return it==index_.end()?nullptr:&it->second;}
    // Extracts and CRC-checks one member. Returns false (out empty) on any mismatch.
    bool read(std::string_view name,std::vector<uint8_t>& out,uint64_t limit=512ull*1024*1024)const {
        out.clear();const Entry* e=find(name);if(!e||e->size>limit||(e->method!=0&&e->method!=8))return false;
        std::ifstream f(path_,std::ios::binary);if(!f)return false;
        std::vector<uint8_t> packed(e->compressed);f.seekg(static_cast<std::streamoff>(e->data));
        if(e->compressed&&!f.read(reinterpret_cast<char*>(packed.data()),e->compressed))return false;
        out.resize(e->size);
        if(e->method==0){if(e->compressed!=e->size){out.clear();return false;}std::memcpy(out.data(),packed.data(),e->size);}
        else{Inflater inflate(packed.data(),packed.size(),out);if(!inflate.run()){out.clear();return false;}}
        if(crc32(out.data(),out.size())!=e->crc){out.clear();return false;}
        return true;
    }
};
} // namespace gfx2::sma
