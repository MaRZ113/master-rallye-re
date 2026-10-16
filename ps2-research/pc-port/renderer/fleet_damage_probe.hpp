#pragma once
#include "provenance.hpp"
namespace gfx2::ps2port {
class FleetDamageProbe {
 bool requested_=false,active_=false;unsigned captures_=0;uint64_t frame_=UINT64_MAX;
public:
 void configure(const std::wstring& ini)noexcept{wchar_t value[16]{};GetPrivateProfileStringW(L"PS2Port",L"RacePS2FleetDamageCapture",L"0",value,16,ini.c_str());requested_=!std::wcscmp(value,L"1");}
 bool begin(bool active,uint64_t frame)noexcept{if(!requested_)return false;if(!active){active_=false;return false;}if(active_||captures_>=3)return false;active_=true;frame_=frame;++captures_;return true;}
 bool write(uint64_t device,const std::string& metadata,const std::vector<BYTE>& raw)noexcept{try{if(!requested_||!active_||metadata.size()>32768||raw.size()>512*1024)return false;std::vector<BYTE> bytes(16);std::memcpy(bytes.data(),"FDCAR001",8);const uint32_t sizes[]={uint32_t(metadata.size()),uint32_t(raw.size())};std::memcpy(bytes.data()+8,sizes,8);bytes.insert(bytes.end(),metadata.begin(),metadata.end());bytes.insert(bytes.end(),raw.begin(),raw.end());const auto path=session().directory+L"\\fleet-damage-"+std::to_wstring(GetCurrentProcessId())+L"-d"+std::to_wstring(device)+L"-f"+std::to_wstring(frame_)+L".bin";const auto file=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(file==INVALID_HANDLE_VALUE)return false;DWORD written=0;const bool ok=WriteFile(file,bytes.data(),DWORD(bytes.size()),&written,nullptr)&&written==bytes.size();CloseHandle(file);return ok;}catch(...){return false;}}
};
}
