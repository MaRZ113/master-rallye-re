#pragma once
#include "provenance.hpp"
namespace gfx2::ps2port {
// F10-only metadata; never authorizes rendering or suppresses a native draw.
class FleetCarProbe {
 bool requested_=false,was_active_=false;unsigned captures_=0,records_=0;uint64_t frame_=UINT64_MAX,bytes_=0;HANDLE file_=INVALID_HANDLE_VALUE;
 std::array<std::array<uintptr_t,4>,128> keys_{};
 void close()noexcept{if(file_!=INVALID_HANDLE_VALUE)CloseHandle(file_);file_=INVALID_HANDLE_VALUE;}
public:
 ~FleetCarProbe(){close();}
 void configure(const std::wstring& ini)noexcept{wchar_t v[16]{};GetPrivateProfileStringW(L"PS2Port",L"RacePS2FleetCapture",L"0",v,16,ini.c_str());requested_=!std::wcscmp(v,L"1");}
 bool active(bool active,uint64_t frame)noexcept{if(!requested_)return false;if(!active){was_active_=false;close();return false;}if(!was_active_){was_active_=true;close();frame_=frame;records_=0;bytes_=0;++captures_;}return captures_<=128&&frame==frame_&&records_<128;}
 void record(uint64_t device,const std::array<uintptr_t,4>& key,const std::string& text)noexcept{try{for(unsigned i=0;i<records_;++i)if(keys_[i]==key)return;if(records_>=128||text.size()>16384||bytes_+text.size()+1>128*1024)return;
 if(file_==INVALID_HANDLE_VALUE){const auto path=session().directory+L"\\race-fleet-"+std::to_wstring(GetCurrentProcessId())+L"-d"+std::to_wstring(device)+L"-f"+std::to_wstring(frame_)+L".jsonl";file_=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);}if(file_==INVALID_HANDLE_VALUE)return;
 const auto line=text+"\n";DWORD written=0;if(WriteFile(file_,line.data(),DWORD(line.size()),&written,nullptr)&&written==line.size()){keys_[records_++]=key;bytes_+=written;}else close();
 }catch(...){close();}}
};
}
