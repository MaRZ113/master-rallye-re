#pragma once
#include "provenance.hpp"
#include <array>
#include <vector>
namespace gfx2::ps2port {
struct ModelTransitionPolicy {
 bool armed=false,last_ok=true;unsigned count=0;
 bool admit(bool ok)noexcept{if(!armed){if(ok)armed=true;return false;}if(ok==last_ok||count>=64)return false;last_ok=ok;++count;return true;}
};
// Diagnostic only: three F10 activations, one frame each, no persistent GPU state.
class ModelProbe {
 bool requested_=false,was_active_=false;unsigned captures_=0,records_=0;uint64_t frame_=UINT64_MAX,bytes_=0;uint32_t gates_=0;
 HANDLE transition_file_=INVALID_HANDLE_VALUE;ModelTransitionPolicy transitions_;
 HANDLE file_=INVALID_HANDLE_VALUE;std::array<std::array<uint64_t,4>,32> keys_{};
 void close()noexcept{if(file_!=INVALID_HANDLE_VALUE)CloseHandle(file_);file_=INVALID_HANDLE_VALUE;}
public:
 ~ModelProbe(){close();if(transition_file_!=INVALID_HANDLE_VALUE)CloseHandle(transition_file_);}
 void configure(const std::wstring& ini)noexcept{wchar_t v[16]{};GetPrivateProfileStringW(L"PS2Port",L"RacePS2DamageCapture",L"0",v,16,ini.c_str());requested_=!std::wcscmp(v,L"1");}
 bool begin(bool active,uint64_t frame,uint64_t device,const std::array<uint64_t,4>& key)noexcept{try{
  if(!requested_)return false;if(!active){was_active_=false;close();return false;}
  if(!was_active_){was_active_=true;close();frame_=frame;records_=0;bytes_=0;gates_=0;keys_={};if(captures_>=3)return false;++captures_;
   const auto path=session().directory+L"\\race-damage-"+std::to_wstring(GetCurrentProcessId())+L"-d"+std::to_wstring(device)+L"-f"+std::to_wstring(frame)+L".jsonl";
   file_=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
   write("{\"type\":\"race_damage_begin\",\"schema\":1,\"frame\":"+std::to_string(frame)+",\"device\":"+std::to_string(device)+",\"proxy_sha256\":"+quote(session().proxy_sha)+",\"exe_sha256\":"+quote(session().exe_sha)+"}");
  }
  if(frame_!=frame||file_==INVALID_HANDLE_VALUE||records_>=keys_.size())return false;
  for(unsigned i=0;i<records_;++i)if(keys_[i]==key)return false;keys_[records_++]=key;return true;
 }catch(...){close();return false;}}
 bool write(const std::string& value)noexcept{try{if(file_==INVALID_HANDLE_VALUE||value.size()>512*1024||bytes_+value.size()+1>2*1024*1024)return false;DWORD written=0;const auto text=value+"\n";const bool ok=WriteFile(file_,text.data(),DWORD(text.size()),&written,nullptr)&&written==text.size();if(ok)bytes_+=written;else close();return ok;}catch(...){close();return false;}}
 void gate(uint64_t frame,unsigned gate,unsigned context,uint32_t seen,const std::array<uint64_t,4>& key)noexcept{try{if(frame!=frame_||file_==INVALID_HANDLE_VALUE)return;for(unsigned i=0;i<records_;++i)if(keys_[i]==key&&!(gates_&(1u<<i))){gates_|=1u<<i;write("{\"type\":\"race_damage_gate\",\"frame\":"+std::to_string(frame)+",\"gate\":"+std::to_string(gate)+",\"context_gate\":"+std::to_string(context)+",\"seen\":"+std::to_string(seen)+",\"min\":"+std::to_string(key[0])+",\"vertices\":"+std::to_string(key[1])+",\"start\":"+std::to_string(key[2])+",\"triangles\":"+std::to_string(key[3])+"}");break;}}catch(...){}}
 void transition(bool ok,uint64_t frame,uint64_t device,unsigned gate,unsigned context,uint32_t seen,bool certified,bool private_tree,uintptr_t root,unsigned refresh)noexcept{try{
  if(!requested_||!transitions_.admit(ok))return;
  if(transition_file_==INVALID_HANDLE_VALUE){const auto path=session().directory+L"\\race-transition-"+std::to_wstring(GetCurrentProcessId())+L"-d"+std::to_wstring(device)+L".jsonl";transition_file_=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);}
  if(transition_file_==INVALID_HANDLE_VALUE)return;
  const std::string text="{\"type\":\"race_model_transition\",\"schema\":1,\"frame\":"+std::to_string(frame)+",\"private_submitted\":"+(ok?"true":"false")+",\"gate\":"+std::to_string(gate)+",\"context_gate\":"+std::to_string(context)+",\"seen\":"+std::to_string(seen)+",\"certified\":"+(certified?"true":"false")+",\"private_tree\":"+(private_tree?"true":"false")+",\"root\":"+std::to_string(root)+",\"refresh_flags\":"+std::to_string(refresh)+",\"proxy_sha256\":"+quote(session().proxy_sha)+"}\n";
  DWORD written=0;WriteFile(transition_file_,text.data(),DWORD(text.size()),&written,nullptr);
 }catch(...){}}
 static std::string hex(const std::vector<BYTE>& data){static constexpr char digits[]="0123456789abcdef";std::string text(data.size()*2,'0');for(size_t i=0;i<data.size();++i){text[i*2]=digits[data[i]>>4];text[i*2+1]=digits[data[i]&15];}return text;}
};
}
