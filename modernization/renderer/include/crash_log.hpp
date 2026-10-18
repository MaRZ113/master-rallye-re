#pragma once
#include <string>

namespace gfx2 {
// Development diagnostic: when [Diagnostics] CrashLog=1, a vectored exception handler writes a text report
// (code, address, module+rva, registers, stack, EBP chain) for severe exceptions raised inside MRallye.exe
// to MRRRenderer\logs\crash-<pid>.txt next to the config file. Default OFF; it never changes the exception flow.
void install_crash_log(const std::wstring& config_path) noexcept;
}
