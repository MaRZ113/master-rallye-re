#pragma once
// Read-only, bounded parser for the native Game/Broker/Value save subset.
// No external entities, XML declarations, nested payloads or encoding fallback.
#include <charconv>
#include <cstdint>
#include <map>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace mr_roster_state {
inline void Reject(const std::string& reason) { throw std::runtime_error("PlayerState: "+reason); }
inline std::string Lower(std::string value) {
    for (char& c:value) if (c>='A' && c<='Z') c=char(c-'A'+'a');
    return value;
}
inline bool Space(char c) { return c==' ' || c=='\t' || c=='\r' || c=='\n'; }
inline void Utf8(std::string_view text) {
    for (size_t i=0;i<text.size();) {
        uint32_t c=static_cast<unsigned char>(text[i++]), minimum=0; unsigned more=0;
        if (c<0x80) {if (c<0x20 && !Space(char(c))) Reject("invalid XML control character"); continue;}
        if (c>=0xc2 && c<=0xdf) {more=1;c&=31;minimum=0x80;}
        else if (c>=0xe0 && c<=0xef) {more=2;c&=15;minimum=0x800;}
        else if (c>=0xf0 && c<=0xf4) {more=3;c&=7;minimum=0x10000;}
        else Reject("unsupported UTF-8 encoding");
        while (more--) {if (i==text.size() || (static_cast<unsigned char>(text[i])&0xc0)!=0x80) Reject("malformed UTF-8");c=(c<<6)|(static_cast<unsigned char>(text[i++])&63);}
        if (c<minimum || c>0x10ffff || (c>=0xd800 && c<=0xdfff) || c==0xfffe || c==0xffff) Reject("invalid Unicode scalar");
    }
}
inline std::string Unescape(std::string_view input) {
    std::string out;
    for (size_t i=0;i<input.size();++i) {
        if (input[i]=='<') Reject("unescaped attribute delimiter");
        if (input[i]!='&') {out+=input[i];continue;}
        const size_t end=input.find(';',i+1); if (end==std::string_view::npos || end-i>16) Reject("malformed entity reference");
        const auto token=input.substr(i+1,end-i-1);
        if (token=="amp") out+='&'; else if (token=="lt") out+='<'; else if (token=="gt") out+='>';
        else if (token=="quot") out+='"'; else if (token=="apos") out+='\'';
        else if (!token.empty() && token[0]=='#') {
            uint32_t c=0; auto digits=token.substr(1); int base=10;
            if (!digits.empty() && digits[0]=='x') {base=16;digits.remove_prefix(1);}
            const auto result=std::from_chars(digits.data(),digits.data()+digits.size(),c,base);
            if (digits.empty() || result.ec!=std::errc{} || result.ptr!=digits.data()+digits.size() || c==0 || c>0x10ffff || (c>=0xd800 && c<=0xdfff)) Reject("invalid numeric entity");
            if (c<0x80) out+=char(c);
            else if (c<0x800) {out+=char(0xc0|(c>>6));out+=char(0x80|(c&63));}
            else if (c<0x10000) {out+=char(0xe0|(c>>12));out+=char(0x80|((c>>6)&63));out+=char(0x80|(c&63));}
            else {out+=char(0xf0|(c>>18));out+=char(0x80|((c>>12)&63));out+=char(0x80|((c>>6)&63));out+=char(0x80|(c&63));}
        } else Reject("external or unknown entity reference");
        i=end;
    }
    Utf8(out); return out;
}
struct Field {std::string type,value;};
inline std::map<std::string,Field> Parse(std::string_view text) {
    if (text.empty() || text.size()>4u*1024u*1024u) Reject("save exceeds bounded XML size");
    Utf8(text); if (text.substr(0,3)=="\xef\xbb\xbf") text.remove_prefix(3);
    size_t at=0; std::vector<std::string> stack; bool root=false,broker=false,closed=false;
    std::map<std::string,Field> fields;
    auto whitespace=[&]{while (at<text.size() && Space(text[at])) ++at;};
    auto name=[&]{const auto start=at;while(at<text.size() && ((text[at]>='A'&&text[at]<='Z')||(text[at]>='a'&&text[at]<='z')||(text[at]>='0'&&text[at]<='9')||text[at]=='_')) ++at;if(at==start) Reject("missing XML name");return std::string(text.substr(start,at-start));};
    while (true) {
        whitespace(); if (at==text.size()) break;
        if (text[at++]!='<' || at==text.size()) Reject("unexpected XML content");
        if (text[at]=='!' || text[at]=='?') Reject("declarations, entities and processing instructions unsupported");
        bool ending=text[at]=='/';if(ending) ++at;
        const auto tag=name();std::map<std::string,std::string> attrs;
        if(ending) {whitespace();if(at==text.size()||text[at++]!='>'||stack.empty()||stack.back()!=tag) Reject("mismatched closing tag");stack.pop_back();if(stack.empty()) closed=true;continue;}
        bool self=false;
        while (true) {
            const auto before=at; whitespace();if(at==text.size()) Reject("unfinished tag");
            if(text[at]=='>') {++at;break;}
            if(text[at]=='/' && at+1<text.size() && text[at+1]=='>') {at+=2;self=true;break;}
            if(at==before) Reject("missing attribute separator");
            auto key=name();whitespace();if(at==text.size()||text[at++]!='=') Reject("missing attribute assignment");whitespace();
            if(at==text.size()||(text[at]!='\''&&text[at]!='"')) Reject("unquoted attribute");const char quote=text[at++];
            auto end=text.find(quote,at);if(end==std::string_view::npos) Reject("unfinished attribute");auto value=Unescape(text.substr(at,end-at));at=end+1;
            if(!attrs.emplace(key,value).second) Reject("duplicate XML attribute");
        }
        if(tag=="Game" && stack.empty() && !root && !closed && !self && attrs.empty()) {root=true;stack.push_back(tag);}
        else if(tag=="Broker" && stack==std::vector<std::string>{"Game"} && !broker && !self && attrs.empty()) {broker=true;stack.push_back(tag);}
        else if(tag=="Value" && stack==std::vector<std::string>{"Game","Broker"} && self) {
            for(const auto& [key,value]:attrs) if(key!="Name"&&key!="Type"&&key!="Value"&&key!="SaveOptions"&&key!="SavePlayerState") Reject("unsupported Value attribute: "+key);
            if(!attrs.count("Name")||!attrs.count("Type")||!attrs.count("Value")||attrs["Name"].empty()) Reject("incomplete saved field");
            if(!fields.emplace(Lower(attrs["Name"]),Field{Lower(attrs["Type"]),attrs["Value"]}).second) Reject("duplicate saved key: "+attrs["Name"]);
        } else Reject("unsupported Game/Broker structure");
    }
    if(!root||!broker||!closed||!stack.empty()) Reject("incomplete Game/Broker document");return fields;
}
struct Report {size_t identities=0,activeCompetitions=0;};
inline Report Validate(std::string_view xml,const std::vector<uint32_t>& classes,const std::set<uint32_t>& retired={}) {
    const auto fields=Parse(xml); Report report;
    const std::regex identity("frontend/(quickrace/car[01]|network/car0|network/selectedcar)|(masterrallye|rallyecup)/playert[123]car[01]|masterrallye/car[0-5]/carid");
    const std::regex classField("masterrallye/vehicleclass|rallyecup/currentclass|frontend/rallyecup/currentclass|masterrallye/car[0-5]/carclass");
    auto integer=[](const std::string& key,const Field& field) {int64_t value=0;const auto& text=field.value;auto r=std::from_chars(text.data(),text.data()+text.size(),value);if(field.type!="int"||text.empty()||r.ec!=std::errc{}||r.ptr!=text.data()+text.size()) Reject("invalid integer: "+key);return value;};
    for(const auto& [key,field]:fields) {
        if(key.size()>=10 && key.substr(key.size()-10)=="/gamesaved" && Lower(field.value)!="false" && field.value!="0" && !field.value.empty()) ++report.activeCompetitions;
        if(std::regex_match(key,classField)) {const auto cls=integer(key,field);if(cls<0||cls>2) Reject("unsupported saved class: "+key);continue;}
        if(!std::regex_match(key,identity)) {
            const bool unsupported=key.starts_with("frontend/quickrace/car") || key.starts_with("frontend/network/selectedcar")
                || key.starts_with("frontend/network/car") || key.starts_with("masterrallye/playert") || key.starts_with("rallyecup/playert")
                || (key.starts_with("masterrallye/car") && (key.ends_with("/carid") || key.ends_with("/carclass")));
            if(unsupported) Reject("unsupported vehicle identity field: "+key);
            continue;
        }
        const auto id=integer(key,field);if(id==-1&&key.starts_with("frontend/")) continue;
        if(id<0||uint64_t(id)>=classes.size()||retired.count(uint32_t(id))) Reject("saved vehicle unknown or retired: "+key+"="+field.value);
        ++report.identities; const auto player=key.find("/playert");
        if(player!=std::string::npos && classes[size_t(id)]!=uint32_t(key[player+8]-'1')) Reject("saved player class/CarID mismatch: "+key);
        if(key.starts_with("masterrallye/car")&&key.ends_with("/carid")) {auto paired=key.substr(0,key.size()-5)+"carclass";const auto found=fields.find(paired);if(found!=fields.end()&&classes[size_t(id)]!=uint32_t(integer(paired,found->second))) Reject("saved CarClass/CarID mismatch: "+key);}
    }
    return report;
}
}
