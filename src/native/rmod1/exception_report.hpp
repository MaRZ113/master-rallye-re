#pragma once

#include <cstddef>
#include <cstdint>

namespace rmod1 {

enum class StartPhaseV1 : std::uint32_t {
    Idle = 0,
    GuardEntered = 1,
    StartBlocked = 2,
    StartAllowed = 3,
    NativeSetupEntered = 4,
    NativeSetupReturned = 5,
    // Values 6..8 are retained as historical v9 diagnostic labels. The
    // start path no longer performs a pre-transition prepared-roster veto.
    PreparedValidationEntered = 6,
    PreparedValidationAccepted = 7,
    PreparedValidationRejected = 8,
};

enum class ExceptionRecordKindV1 : std::uint32_t {
    Session = 1,
    AccessViolationFirstChance = 2,
    AccessViolationUnhandled = 3,
};

struct CrashFrameV1 {
    std::uint32_t frame_pointer;
    std::uint32_t return_address;
};

#pragma pack(push, 1)
struct ExceptionRecordV1 {
    char magic[8];
    std::uint32_t record_size;
    std::uint32_t sequence;
    std::uint32_t process_id;
    std::uint32_t thread_id;
    std::uint32_t kind;
    std::uint32_t exception_code;
    std::uint32_t exception_flags;
    std::uint32_t exception_address;
    std::uint32_t parameter_count;
    std::uint32_t exception_information[15];

    std::uint32_t eip;
    std::uint32_t esp;
    std::uint32_t ebp;
    std::uint32_t eax;
    std::uint32_t ebx;
    std::uint32_t ecx;
    std::uint32_t edx;
    std::uint32_t esi;
    std::uint32_t edi;
    std::uint32_t eflags;

    std::uint32_t start_phase;
    std::uint32_t config_flags;
    std::int32_t opponent_count;
    std::int32_t track;
    std::int32_t mode;
    std::uint32_t ghost;
    std::uint32_t split_screen;
    std::int32_t player_id;
    std::int32_t player_class;

    std::uint32_t stack_words[32];
    CrashFrameV1 frames[16];
};
#pragma pack(pop)

constexpr char kExceptionRecordMagicV1[8] = {'R', 'M', 'C', 'R', 'A', 'S', 'H', '1'};
constexpr std::uint32_t kExceptionConfigRandomizer = 1u << 0;
constexpr std::uint32_t kExceptionConfigOpponents = 1u << 1;
constexpr std::uint32_t kExceptionConfigLogging = 1u << 2;

static_assert(sizeof(ExceptionRecordV1) == 436, "exception record wire size changed");
static_assert(offsetof(ExceptionRecordV1, eip) == 104, "exception record context offset changed");
static_assert(offsetof(ExceptionRecordV1, start_phase) == 144, "exception record phase offset changed");
static_assert(offsetof(ExceptionRecordV1, stack_words) == 180, "exception record stack offset changed");
static_assert(offsetof(ExceptionRecordV1, frames) == 308, "exception record frame offset changed");

} // namespace rmod1
