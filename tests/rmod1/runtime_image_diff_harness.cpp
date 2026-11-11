#include "runtime_image_diff.hpp"

#include <cstdint>
#include <iostream>
#include <vector>

int main() {
    using namespace rmod2_boot;
    constexpr std::uint32_t kTextRva=0x1000;
    constexpr std::size_t kVirtualSize=0x1000;
    constexpr std::size_t kRawSize=0x1100; // includes 0x100 bytes of file padding
    std::vector<std::uint8_t> disk(kRawSize,0x90), mapped(kVirtualSize,0x90);
    std::vector<NativeRange> hooks{{"quickrace-hook",kTextRva+0x40,5}};

    // File-alignment padding beyond VirtualSize is intentionally not presented
    // to the mapped-section scanner, so it cannot create a false rejection.
    disk[kVirtualSize]=0xCC;
    auto scan=scan_mapped_section(disk.data(),disk.size(),mapped.data(),mapped.size(),kTextRva,hooks);
    if(scan.first.found) return 1;

    // A live image difference outside selected operations is diagnosed but is
    // not itself a hook conflict.
    mapped[0x20]=0xCC;
    scan=scan_mapped_section(disk.data(),disk.size(),mapped.data(),mapped.size(),kTextRva,hooks);
    if(!scan.first.found||scan.first.offset!=0x20||!scan.first.operation.empty()||scan.first_planned_overlap.found) return 2;

    // Any changed byte within an actually selected native operation is a hard
    // conflict, independently of the surrounding section differences.
    mapped[0x42]=0xCC;
    scan=scan_mapped_section(disk.data(),disk.size(),mapped.data(),mapped.size(),kTextRva,hooks);
    if(!scan.first_planned_overlap.found||scan.first_planned_overlap.offset!=0x42||scan.first_planned_overlap.operation!="quickrace-hook") return 3;

    // When VirtualSize exceeds raw data, the mapped remainder is zero-filled.
    std::vector<std::uint8_t> short_raw(8,0x90), zero_fill(12,0x90);
    zero_fill[8]=zero_fill[9]=zero_fill[10]=zero_fill[11]=0;
    scan=scan_mapped_section(short_raw.data(),short_raw.size(),zero_fill.data(),zero_fill.size(),0x2000,{});
    if(scan.first.found) return 4;
    zero_fill[10]=0xCC;
    scan=scan_mapped_section(short_raw.data(),short_raw.size(),zero_fill.data(),zero_fill.size(),0x2000,{});
    if(!scan.first.found||scan.first.offset!=10||scan.first.expected!=0||scan.first.actual!=0xCC) return 5;

    std::cout << "RUNTIME_IMAGE_DIFF_PASS virtual_extent_only=1 padding_ignored=1 non_hook_diagnostic=1 selected_hook_conflict=1 zero_fill=1\n";
    return 0;
}
