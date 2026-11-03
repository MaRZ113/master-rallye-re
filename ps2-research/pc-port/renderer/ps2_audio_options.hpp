#pragma once
// PS2-AUDIO1 (docs/course-alive4/README.md): two PS2 audio behaviours as separate opt-in code patches of MRallye.exe.
//
// * PS2CheckpointSoundOff=1 - no sample when a checkpoint is passed. PC: gaHudAiCheckPoint (vtable 0x690de8, update
//   0x4a4c30) watches Race/Car%d/SplitPoint, fades the CHECKPOINT text (0xcd) in and plays its sample object (+0x10,
//   0x4f68f0 volume = Sound/SFX/Volume x scale, 0x4f66e0 play) from the single block 0x4a4d2a..0x4a4d66. The PS2 ELF has
//   no gaHudAiCheckPoint at all. Patch: the JZ at 0x4a4d28 that guards the block (74 3d) becomes JMP (eb 3d); the text
//   stays. Second sample of the same event (game test 1: the first patch alone left a checkpoint sound): gaHudAiSplitTime
//   (vtable 0x690f94, update 0x4a9050, authored "Audio Sound" +0x10) shows the split time "%2d:%2d:%2d" when
//   Race/Car%d/SplitPoint changes and plays its sample in 0x4a912e..0x4a9168 (Sound/SFX/Volume x scale, 0x4f68f0 /
//   0x4f66e0; x87 balanced: FLD by 0x4d6650, FSTP before the call). Patch: the PUSH 0x6af8e8 at 0x4a912e (68 e8) becomes
//   JMP 0x4a9169 (eb 39), the epilogue; the split time text stays.
// * PS2FinishMusic=1 - the race music keeps playing after the finish. PC: gaRaceFinishAI (vtable 0x690c4c) creates the
//   object Music/FinishJingle in its init (0x489af0); its update (0x489ec0), when the race is finished, starts the jingle
//   (0x48a394 mov byte [eax+0e],1) and then lowers Sound/Music/Volume every tick (0x48a3ff..0x48a446) until it is 0. The
//   PS2 gaRaceFinishAI update (17ed48) has neither: no jingle string exists in SLES_509.06, Sound/Music/Volume and
//   FinishLoop are not touched (only the result timer 0x546 and the end-of-race transition). Patches: the jingle start
//   becomes 4 NOPs, the fade's JNZ at 0x48a40a (75 3c) becomes JMP (eb 3c) to its FSTP ST0 (x87 stack stays balanced).
//   The volume restore at the end (0x48a4c0.., the saved +0x38) then writes the unchanged value.
//
// Each patch is applied once, only when the image base is 0x400000 and the original bytes are at the site (retail
// MRallye.exe and the derivative builds with the same code; anything else stays untouched and is reported). An opcode
// change writes one byte (the split-time JMP two, at proxy start before any race); the NOP run is one aligned 4-byte write. The patches stay for the process lifetime.
#include "ps2_config.hpp"
#include "ps2_diag.hpp"
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <string>

namespace gfx2::ps2port::audio {

struct BytePatch {
    const char* name;
    uint32_t va;                          // retail virtual address (image base 0x400000)
    uint8_t size;
    std::array<uint8_t,4> original, replacement;
};
inline constexpr uint32_t kImageBase=0x400000;
inline constexpr BytePatch kCheckpointSound{"checkpoint_sound_jz",0x4a4d28,2,{0x74,0x3d,0,0},{0xeb,0x3d,0,0}};
inline constexpr BytePatch kSplitTimeSound{"split_time_sound_jmp",0x4a912e,2,{0x68,0xe8,0,0},{0xeb,0x39,0,0}};
inline constexpr BytePatch kFinishJingle{"finish_jingle_start",0x48a394,4,{0xc6,0x40,0x0e,0x01},{0x90,0x90,0x90,0x90}};
inline constexpr BytePatch kFinishFade{"finish_music_fade_jnz",0x48a40a,2,{0x75,0x3c,0,0},{0xeb,0x3c,0,0}};

enum class Site : uint8_t { Original, Patched, Mismatch };
// Pure: the state of a site from its current bytes.
inline Site classify(const BytePatch& p,const uint8_t* bytes) noexcept {
    if(!bytes||!p.size||p.size>4)return Site::Mismatch;
    if(!std::memcmp(bytes,p.original.data(),p.size))return Site::Original;
    if(!std::memcmp(bytes,p.replacement.data(),p.size))return Site::Patched;
    return Site::Mismatch;
}
// Pure: every site of a group must be original or already patched; otherwise none is written.
template<size_t N> inline bool group_ready(const std::array<const BytePatch*,N>& group,const std::array<const uint8_t*,N>& bytes) noexcept {
    for(size_t i=0;i<N;++i)if(classify(*group[i],bytes[i])==Site::Mismatch)return false;
    return true;
}

struct Status { bool requested=false,applied=false; const char* reason="not_requested"; };
struct State { Status checkpoint_sound, finish_music; bool configured=false; };
inline State& state() noexcept { static State s; return s; }

namespace detail {
inline bool read(uint32_t va,uint8_t* out,size_t n) noexcept {
    __try{std::memcpy(out,reinterpret_cast<const void*>(static_cast<uintptr_t>(va)),n);return true;}
    __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
inline bool write(const BytePatch& p) noexcept {
    auto* target=reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(p.va));
    DWORD old=0;
    if(!VirtualProtect(target,p.size,PAGE_EXECUTE_READWRITE,&old))return false;
    bool ok=true;
    __try{
        if(p.size==4&&!(p.va&3)){uint32_t v=0;std::memcpy(&v,p.replacement.data(),4);
            InterlockedExchange(reinterpret_cast<volatile LONG*>(target),static_cast<LONG>(v));}
        else for(size_t i=0;i<p.size;++i)if(target[i]!=p.replacement[i])*reinterpret_cast<volatile uint8_t*>(target+i)=p.replacement[i];
    }__except(EXCEPTION_EXECUTE_HANDLER){ok=false;}
    DWORD ignored=0;VirtualProtect(target,p.size,old,&ignored);
    FlushInstructionCache(GetCurrentProcess(),target,p.size);
    return ok;
}
template<size_t N> inline Status apply(const std::array<const BytePatch*,N>& group) noexcept {
    Status s;s.requested=true;
    if(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=kImageBase){s.reason="unexpected_image_base";return s;}
    std::array<std::array<uint8_t,4>,N> seen{};std::array<const uint8_t*,N> bytes{};
    for(size_t i=0;i<N;++i){if(!read(group[i]->va,seen[i].data(),group[i]->size)){s.reason="site_unreadable";return s;}bytes[i]=seen[i].data();}
    if(!group_ready(group,bytes)){s.reason="original_bytes_mismatch_untouched";return s;}
    for(size_t i=0;i<N;++i)if(classify(*group[i],bytes[i])==Site::Original&&!write(*group[i])){s.reason="code_write_failed";return s;}
    s.applied=true;s.reason="applied";return s;
}
}  // namespace detail

// Once per process, from the PS2PortExtension constructor (supported builds only).
inline void configure(bool supported,const std::wstring& ini) noexcept {
    auto& st=state();
    if(st.configured)return;
    st.configured=true;
    try{
        const bool sound=supported&&config::read_int(L"PS2CheckpointSoundOff",0,ini.c_str())==1;
        const bool music=supported&&config::read_int(L"PS2FinishMusic",0,ini.c_str())==1;
        if(sound)st.checkpoint_sound=detail::apply(std::array<const BytePatch*,2>{&kCheckpointSound,&kSplitTimeSound});
        if(music)st.finish_music=detail::apply(std::array<const BytePatch*,2>{&kFinishJingle,&kFinishFade});
        if(sound&&!st.checkpoint_sound.applied)ps2diag::disable_log().note("checkpoint_sound_off",st.checkpoint_sound.reason);
        if(music&&!st.finish_music.applied)ps2diag::disable_log().note("finish_music",st.finish_music.reason);
    }catch(...){}
}
inline std::string status_json() {
    const auto& st=state();
    auto one=[](const Status& s){return std::string("{\"requested\":")+(s.requested?"true":"false")+",\"applied\":"+(s.applied?"true":"false")+
        ",\"reason\":"+ps2diag::quote(s.reason)+"}";};
    return "{\"checkpoint_sound_off\":"+one(st.checkpoint_sound)+",\"finish_music\":"+one(st.finish_music)+"}";
}

}  // namespace gfx2::ps2port::audio
