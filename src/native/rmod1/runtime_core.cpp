#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <wincrypt.h>

#include "core.hpp"
#include "exception_report.hpp"
#include "runtime_log.hpp"
#if defined(RMOD_EXTRA_OPTIONS)
#include "sdk_roster_abi.hpp"
#include "extra_registry.hpp"
#include "registry_ai_pool.hpp"
#include <unordered_set>
#include <climits>
#endif

#include <array>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

namespace {

using namespace rmod1;

SRWLOCK g_lock = SRWLOCK_INIT;
Config g_config{};
Config g_generation_config{};
ClassCycle g_diverse_cycle{};
bool g_configured = false;
unsigned g_next_slot = 0;
unsigned g_generation_id = 0;
int g_active_mode = -1;
int g_expected_slot = 0;
char g_config_hash[65]{};
char g_generation_hash[65]{};
ChallengeSelection g_challenge;
#if defined(RMOD_EXTRA_OPTIONS)
std::vector<RegisteredAddon> g_registered;
std::vector<uint32_t> g_registry_classes;
std::vector<Vehicle> g_generation_pool;
struct AiPoolObservation { int cls; std::vector<int> before,after; };
std::vector<AiPoolObservation> g_ai_observations;
int g_generation_ai_count=0;
bool g_quick_report_pending=false;
std::uint32_t g_challenge_human_offset=0x570;
#endif
int runtime_class(int id) {
#if defined(RMOD_EXTRA_OPTIONS)
    if(!g_registry_classes.empty())return id>=0&&size_t(id)<g_registry_classes.size()?int(g_registry_classes[size_t(id)]):-1;
    for (const auto& item:g_registered) if(item.physical_id==id) return item.class_id;
#endif
    return rmod1::stock_class_for_physical_id(id);
}
std::vector<Vehicle> runtime_pool(GameMode mode,std::uint8_t rewards,AddonMode addons) {
#if defined(RMOD_EXTRA_OPTIONS)
    return eligible_vehicles(mode,rewards,g_registered,addons);
#else
    return eligible_vehicles(mode,rewards,{},addons);
#endif
}
#if defined(RMOD_EXTRA_OPTIONS)
unsigned runtime_registered_count(){
    return static_cast<unsigned>(g_registered.size());
}
#endif
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
PreparedPlayerVehicle g_prepared_player;
char g_prepared_player_hash[65]{};
#endif
HANDLE g_exception_log = INVALID_HANDLE_VALUE;
PVOID g_exception_handler = nullptr;
LPTOP_LEVEL_EXCEPTION_FILTER g_previous_unhandled_filter = nullptr;
volatile LONG g_exception_capture_enabled = 0;
volatile LONG g_exception_sequence = 0;
volatile LONG g_start_phase = static_cast<LONG>(StartPhaseV1::Idle);
volatile LONG g_config_flags = 0;
volatile LONG g_last_opponent_count = -1;
volatile LONG g_last_track = -1;
volatile LONG g_last_mode = -1;
volatile LONG g_last_ghost = -1;
volatile LONG g_last_split_screen = -1;
volatile LONG g_last_player_id = -1;
volatile LONG g_last_player_class = -1;

struct ExclusiveGuard {
    explicit ExclusiveGuard(SRWLOCK* lock) : lock_(lock) { AcquireSRWLockExclusive(lock_); }
    ~ExclusiveGuard() { ReleaseSRWLockExclusive(lock_); }
    ExclusiveGuard(const ExclusiveGuard&) = delete;
    ExclusiveGuard& operator=(const ExclusiveGuard&) = delete;
    SRWLOCK* lock_;
};

struct SharedGuard {
    explicit SharedGuard(SRWLOCK* lock) : lock_(lock) { AcquireSRWLockShared(lock_); }
    ~SharedGuard() { ReleaseSRWLockShared(lock_); }
    SharedGuard(const SharedGuard&) = delete;
    SharedGuard& operator=(const SharedGuard&) = delete;
    SRWLOCK* lock_;
};

template <typename T>
T native(std::uintptr_t address) {
    return reinterpret_cast<T>(address);
}

using NativeSingleton = void* (__cdecl*)();
using NativeGetSlot = int (__thiscall*)(void*, int);
using NativeGetBoolean = BOOL (__cdecl*)();
using NativeGetObjectBoolean = bool (__thiscall*)(void*);
using NativeGetInteger = int (__cdecl*)();
using NativeGetQuickCar = int (__stdcall*)(int);
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
using NativeSetQuickCar = void (__stdcall*)(int, int);
#endif
using NativeGetObjectInteger = int (__thiscall*)(void*);
using NativeRange = int (__thiscall*)(void*, int, int);
using NativeProgressState = void* (__cdecl*)();
using NativeUnlocked = BOOL (__thiscall*)(void*, int);

void* race_state() {
    return native<NativeSingleton>(0x004ADA50)();
}

void* competition_state() {
    return native<NativeSingleton>(0x004B0AF0)();
}

bool runtime_package_path(const char* filename, char (&path)[MAX_PATH]) {
    HMODULE module = GetModuleHandleA("MRallyeRandomizerRuntime.dll");
    if (!module) return false;
    const DWORD length = GetModuleFileNameA(module, path, MAX_PATH);
    if (!length || length >= MAX_PATH) return false;
    char* slash = path + length;
    while (slash > path && slash[-1] != '\\' && slash[-1] != '/') --slash;
    if (slash == path) return false;
    const std::size_t remaining = static_cast<std::size_t>(path + MAX_PATH - slash);
    const std::size_t name_length = std::strlen(filename);
    if (name_length + 1 > remaining) return false;
    std::memcpy(slash, filename, name_length + 1);
    return true;
}

bool sha256_text(const std::uint8_t* bytes, DWORD count, char (&hex)[65]) {
    HCRYPTPROV provider = 0;
    HCRYPTHASH hash = 0;
    BYTE digest[32]{};
    bool okay = false;
    if (!CryptAcquireContextA(&provider, nullptr, nullptr, PROV_RSA_AES, CRYPT_VERIFYCONTEXT))
        return false;
    if (CryptCreateHash(provider, CALG_SHA_256, 0, 0, &hash)) {
        const BYTE empty_marker[] = "R-MOD1-SAFE-DEFAULT-CONFIG";
        okay = count ? !!CryptHashData(hash, const_cast<BYTE*>(bytes), count, 0)
                     : !!CryptHashData(hash, const_cast<BYTE*>(empty_marker), sizeof(empty_marker) - 1, 0);
        DWORD size = sizeof(digest);
        okay = okay && !!CryptGetHashParam(hash, HP_HASHVAL, digest, &size, 0) && size == sizeof(digest);
        if (okay) {
            constexpr char digits[] = "0123456789abcdef";
            for (std::size_t index = 0; index < sizeof(digest); ++index) {
                hex[index * 2] = digits[digest[index] >> 4];
                hex[index * 2 + 1] = digits[digest[index] & 0x0f];
            }
            hex[64] = '\0';
        }
        CryptDestroyHash(hash);
    }
    CryptReleaseContext(provider, 0);
    return okay;
}

void append_runtime_log(const char* line) {
    if (!g_config.logging_enabled || !line) return;
    char path[MAX_PATH]{};
    if (runtime_package_path("MRallyeRandomizer.log", path))
        append_runtime_log_record_to_path(path, line);
}

void note_effective_configuration() {
    char line[640]{};
    const int size = wsprintfA(line,
#if defined(RMOD_EXTRA_OPTIONS)
        "CONFIG version=%u randomizer_hooks=%u policies=%u:%s,%u:%s,%u:%s,%u:%s,%u:%s duplicates=%u:%s opponents=%u max_ai=%u extended=%u addons=%u:%s registered_addons=%u provider=%s logging=%u config_sha256=%s",
#else
        "CONFIG version=%u randomizer_hooks=%u policies=%u:%s,%u:%s,%u:%s,%u:%s,%u:%s duplicates=%u:%s opponents=%u max_ai=%u extended=%u addons=%u:%s registered_addons=0 provider=none logging=%u config_sha256=%s",
#endif
        g_config.config_version, config_needs_randomizer_hooks(g_config) ? 1u : 0u,
        policy_numeric_id_for_version(policy_for_mode(g_config, GameMode::QuickRace), g_config.config_version), policy_name(policy_for_mode(g_config, GameMode::QuickRace)),
        policy_numeric_id_for_version(policy_for_mode(g_config, GameMode::RallyeCup), g_config.config_version), policy_name(policy_for_mode(g_config, GameMode::RallyeCup)),
        policy_numeric_id_for_version(policy_for_mode(g_config, GameMode::MasterRallye), g_config.config_version), policy_name(policy_for_mode(g_config, GameMode::MasterRallye)),
        policy_numeric_id_for_version(policy_for_mode(g_config, GameMode::Invitation), g_config.config_version), policy_name(policy_for_mode(g_config, GameMode::Invitation)),
        policy_numeric_id_for_version(policy_for_mode(g_config, GameMode::Challenge), g_config.config_version), policy_name(policy_for_mode(g_config, GameMode::Challenge)),
        g_config.duplicates_when_needed ? 1u : 0u,
        g_config.duplicates_when_needed ? "WhenNeeded" : "Never",
        g_config.opponents_enabled ? 1u : 0u, g_config.max_opponents,
        config_allows_extended_ai(g_config) ? 1u : 0u,
        g_config.addons == AddonMode::RegisteredOnly ? 1u : 0u,
        addon_mode_name(g_config.addons),
#if defined(RMOD_EXTRA_OPTIONS)
        runtime_registered_count(),runtime_registered_count()?"sdk-registry":"none",
#endif
        g_config.logging_enabled ? 1u : 0u, g_config_hash);
    if (size > 0 && size < static_cast<int>(sizeof(line))) append_runtime_log(line);
}

int native_draw(int upper) {
    if (upper <= 0) return -1;
    auto singleton = native<NativeSingleton>(0x004D1E90)();
    return native<NativeRange>(0x004D1DF0)(singleton, 0, upper);
}
#if defined(RMOD_EXTRA_OPTIONS)
int (*g_registry_shuffle_draw)(int)=native_draw;
#endif

std::uint8_t reward_mask() {
    std::uint8_t mask = 0;
    auto reward_state = native<NativeProgressState>(0x004B0310);
    auto is_unlocked = native<NativeUnlocked>(0x004AFB70);
    constexpr std::array<int, 4> reward_keys{{11, 12, 13, 14}};
    for (unsigned i = 0; i < reward_keys.size(); ++i) {
        void* object = reward_state();
        if (object && is_unlocked(object, reward_keys[i]))
            mask |= static_cast<std::uint8_t>(1u << i);
    }
    return mask;
}

const char* mode_name(GameMode mode) {
    switch (mode) {
    case GameMode::QuickRace: return "QuickRace";
    case GameMode::RallyeCup: return "RallyeCup";
    case GameMode::MasterRallye: return "MasterRallye";
    case GameMode::Invitation: return "Invitation";
    case GameMode::Challenge: return "Challenge";
    default: return "Unsupported";
    }
}

bool read_stable_runtime_config(Config& parsed_config, char (&hash)[65], const char*& error) {
    error = "runtime config path is unavailable";
    char path[MAX_PATH]{};
    if (!runtime_package_path("MRallyeRandomizer.ini", path)) return false;
    HANDLE file = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, nullptr,
                              OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        error = "runtime config cannot be opened without conflicting writers";
        return false;
    }

    LARGE_INTEGER length{};
    BY_HANDLE_FILE_INFORMATION before{}, after{};
    std::array<char, kMaxConfigBytes + 1> first{};
    std::array<char, kMaxConfigBytes + 1> second{};
    DWORD read_first = 0, read_second = 0;
    bool stable = GetFileInformationByHandle(file, &before) != FALSE &&
        GetFileSizeEx(file, &length) != FALSE && length.QuadPart >= 0 &&
        length.QuadPart <= static_cast<LONGLONG>(kMaxConfigBytes);
    if (!stable) {
        error = "runtime config is unreadable or exceeds the 4096-byte bound";
        CloseHandle(file);
        return false;
    }
    const DWORD size = static_cast<DWORD>(length.QuadPart);
    stable = SetFilePointer(file, 0, nullptr, FILE_BEGIN) != INVALID_SET_FILE_POINTER &&
        ReadFile(file, first.data(), size, &read_first, nullptr) && read_first == size &&
        SetFilePointer(file, 0, nullptr, FILE_BEGIN) != INVALID_SET_FILE_POINTER &&
        ReadFile(file, second.data(), size, &read_second, nullptr) && read_second == size &&
        GetFileInformationByHandle(file, &after) != FALSE;
    CloseHandle(file);
    const bool same_metadata = before.dwVolumeSerialNumber == after.dwVolumeSerialNumber &&
        before.nFileIndexHigh == after.nFileIndexHigh && before.nFileIndexLow == after.nFileIndexLow &&
        before.nFileSizeHigh == after.nFileSizeHigh && before.nFileSizeLow == after.nFileSizeLow &&
        CompareFileTime(&before.ftLastWriteTime, &after.ftLastWriteTime) == 0;
    if (!stable || !same_metadata || first != second || (size && first[size - 1] != '\n')) {
        error = "runtime config changed during the bounded read or is an incomplete editor write";
        return false;
    }
    const auto outcome = parse_ini(std::string_view(first.data(), size));
    if (!outcome.accepted) {
        error = "runtime config failed strict whole-file validation";
        return false;
    }
    if (!sha256_text(reinterpret_cast<const std::uint8_t*>(first.data()), size, hash)) {
        error = "runtime config SHA256 could not be computed";
        return false;
    }
    parsed_config = outcome.config;
    error = nullptr;
    return true;
}

const char* reload_generation_policy_snapshot() {
    Config parsed{};
    char next_hash[65]{};
    const char* error = nullptr;
    if (!read_stable_runtime_config(parsed, next_hash, error)) {
        if (g_config.logging_enabled) {
            char warning[320]{};
            const int size = wsprintfA(warning,
                "WARNING config_reload=retained_last_valid reason=%s",
                error ? error : "unknown");
            if (size > 0 && size < static_cast<int>(sizeof(warning))) append_runtime_log(warning);
        }
        return "retained-invalid-or-unavailable";
    }

    const bool changed = std::strcmp(g_config_hash, next_hash) != 0;
    // Freeze only policy axes here. MaxOpponents and the UI bound are pinned at
    // startup; active native rosters and already prepared Challenge previews
    // never inherit a partial or mid-generation config update.
    g_config.config_version = parsed.config_version;
    g_config.mode_policies = parsed.mode_policies;
    g_config.quick_race = parsed.quick_race;
    g_config.randomizer_enabled = parsed.randomizer_enabled;
    g_config.duplicates_when_needed = parsed.duplicates_when_needed;
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
    g_config.player_vehicle_mode = parsed.player_vehicle_mode;
    g_config.forced_player_car_id = parsed.forced_player_car_id;
    g_config.player_random_policy = parsed.player_random_policy;
#endif
    std::memcpy(g_config_hash, next_hash, sizeof(g_config_hash));
    return changed ? "accepted-new-snapshot" : "accepted-unchanged-snapshot";
}

void begin_generation_snapshot(GameMode mode, int first, const char* reload_status) {
    g_generation_config = g_config;
    ++g_generation_id;
    g_active_mode = static_cast<int>(mode);
    g_expected_slot = first;
    g_next_slot = static_cast<unsigned>(first);
    g_diverse_cycle = ClassCycle{};
    std::memcpy(g_generation_hash, g_config_hash, sizeof(g_generation_hash));
    if (g_generation_config.logging_enabled) {
        char line[320]{};
        const Policy policy = policy_for_mode(g_generation_config, mode);
        const int size = wsprintfA(line,
            "GENERATION config_version=%u generation=%u mode=%s policy=%u:%s config_sha256=%s reload=%s",
            g_generation_config.config_version, g_generation_id, mode_name(mode),
            policy_numeric_id_for_version(policy, g_generation_config.config_version), policy_name(policy), g_generation_hash,
            reload_status ? reload_status : "not-read");
        if (size > 0 && size < static_cast<int>(sizeof(line))) append_runtime_log(line);
    }
}

int native_car_id(GameMode mode, int slot) {
    void* object = nullptr;
    if (mode == GameMode::QuickRace || mode == GameMode::Challenge) {
        object = race_state();
        if (!object) return -1;
        return native<NativeGetSlot>(0x004AC660)(object, slot);
    }
    object = competition_state();
    if (!object) return -1;
    return native<NativeGetSlot>(0x004B0630)(object, slot);
}

#if defined(RMOD_EXTRA_OPTIONS)
bool read_final_quick_roster(int& player,std::vector<int>& ai) {
    void* race=race_state();if(!race)return false;
    const int count=native<NativeGetObjectInteger>(0x004AC040)(race);
    if(count<1||count>8)return false;
    player=native_car_id(GameMode::QuickRace,0);
    for(int i=1;i<count;++i)ai.push_back(native_car_id(GameMode::QuickRace,i));
    return true;
}
bool (*g_final_roster_reader)(int&,std::vector<int>&)=read_final_quick_roster;
void (*g_final_roster_sink)(const char*)=append_runtime_log;
#endif
GameMode resolve_roster_mode(int hint) {
    void* race = race_state();
    if (!race) return GameMode::Unknown;
    const int type = native<NativeGetObjectInteger>(0x004ABE90)(race);
    if (hint == 0 && type == 2) return GameMode::QuickRace;
    if (hint == 2 && type == 6) return GameMode::RallyeCup;
    if (hint == 2 && type == 8) return GameMode::Invitation;
    if (hint == 4 && type == 5) return GameMode::MasterRallye;
    return GameMode::Unknown;
}

bool safe_one_human_roster_context(GameMode mode, int first, int count, int slot) {
    if (first != 1 || count < 1 || slot < first || slot >= first + count) return false;
    if (mode == GameMode::QuickRace) {
        if (count > static_cast<int>(kMaximumAi)) return false;
    } else if (mode == GameMode::RallyeCup || mode == GameMode::MasterRallye ||
               mode == GameMode::Invitation) {
        if (count != 3) return false;
    } else {
        return false;
    }
    void* race = race_state();
    if (!race) return false;
    const bool split = native<NativeGetObjectBoolean>(0x004AE2D0)(
        native<NativeSingleton>(0x004AE700)());
    const int network = native<NativeGetObjectInteger>(0x004AC0A0)(race);
    return !split && network == 0;
}

bool read_player_identity(GameMode mode, int& physical_id, int& class_id) {
    physical_id = native_car_id(mode, 0);
    class_id = runtime_class(physical_id);
    return physical_id >= 0 && class_id >= 0 && class_id <= 2;
}

void note_start_decision(bool admitted, unsigned selected_count, int track, int mode,
                         bool ghost, bool raw_split, int player_id, int player_class,
                         const QuickRaceTopology& topology, const char* reason) {
    char line[640]{};
    const int size = wsprintfA(line,
#if defined(RMOD_EXTRA_OPTIONS)
        "START %s reason=%s randomizer=%u policy=%u:%s opponents_enabled=%u requested_max=%u experimental_extended_ai=%u requested_ai=%u raw_frontend_split=%u effective_mode=%d active_humans=deferred_to_native_roster predicted_numcars=%u spawned_ai=deferred_to_native_roster track=%d ghost=%u player_id=%d player_class=%d addons=%u registered_addons=%u",
#else
        "START %s reason=%s randomizer=%u policy=%u:%s opponents_enabled=%u requested_max=%u experimental_extended_ai=%u requested_ai=%u raw_frontend_split=%u effective_mode=%d active_humans=deferred_to_native_roster predicted_numcars=%u spawned_ai=deferred_to_native_roster track=%d ghost=%u player_id=%d player_class=%d addons=%u registered_addons=0",
#endif
        admitted ? "ADMITTED" : "DENIED", reason ? reason : "unspecified",
        config_requests_randomizer(g_config) ? 1u : 0u,
        policy_numeric_id_for_version(policy_for_mode(g_config, GameMode::QuickRace), g_config.config_version),
        policy_name(g_config.quick_race), g_config.opponents_enabled ? 1u : 0u,
        g_config.max_opponents, g_config.experimental_extended_ai ? 1u : 0u,
        selected_count, raw_split ? 1u : 0u, topology.quick_race ? mode : -1,
        topology.num_cars, track,
        ghost ? 1u : 0u, player_id, player_class,
        g_config.addons == AddonMode::RegisteredOnly ? 1u : 0u
#if defined(RMOD_EXTRA_OPTIONS)
        ,runtime_registered_count()
#endif
        );
    if (size > 0 && size < static_cast<int>(sizeof(line))) append_runtime_log(line);
}

void fill_exception_record(ExceptionRecordV1& record, ExceptionRecordKindV1 kind) {
    std::memcpy(record.magic, kExceptionRecordMagicV1, sizeof(record.magic));
    record.record_size = sizeof(record);
    record.process_id = GetCurrentProcessId();
    record.thread_id = GetCurrentThreadId();
    record.kind = static_cast<std::uint32_t>(kind);
    record.start_phase = static_cast<std::uint32_t>(InterlockedCompareExchange(&g_start_phase, 0, 0));
    record.config_flags = static_cast<std::uint32_t>(InterlockedCompareExchange(&g_config_flags, 0, 0));
    record.opponent_count = InterlockedCompareExchange(&g_last_opponent_count, 0, 0);
    record.track = InterlockedCompareExchange(&g_last_track, 0, 0);
    record.mode = InterlockedCompareExchange(&g_last_mode, 0, 0);
    record.ghost = static_cast<std::uint32_t>(InterlockedCompareExchange(&g_last_ghost, 0, 0));
    record.split_screen = static_cast<std::uint32_t>(InterlockedCompareExchange(&g_last_split_screen, 0, 0));
    record.player_id = InterlockedCompareExchange(&g_last_player_id, 0, 0);
    record.player_class = InterlockedCompareExchange(&g_last_player_class, 0, 0);
}

void write_exception_record(const ExceptionRecordV1& record) {
    if (g_exception_log == INVALID_HANDLE_VALUE) return;
    DWORD written = 0;
    if (WriteFile(g_exception_log, &record, sizeof(record), &written, nullptr) &&
        written == sizeof(record)) {
        FlushFileBuffers(g_exception_log);
    }
}

bool read_exception_memory(const void* address, void* destination, std::size_t size) {
    SIZE_T copied = 0;
    return ReadProcessMemory(GetCurrentProcess(), address, destination, size, &copied) && copied == size;
}

void record_access_violation(PEXCEPTION_POINTERS pointers, ExceptionRecordKindV1 kind) {
    if (InterlockedCompareExchange(&g_exception_capture_enabled, 0, 0) == 0 ||
        !pointers || !pointers->ExceptionRecord || !pointers->ContextRecord ||
        pointers->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION) {
        return;
    }

    const LONG sequence = InterlockedIncrement(&g_exception_sequence);
    if (sequence > 32) return;

    ExceptionRecordV1 record{};
    fill_exception_record(record, kind);
    record.sequence = static_cast<std::uint32_t>(sequence);
    const EXCEPTION_RECORD& exception = *pointers->ExceptionRecord;
    record.exception_code = exception.ExceptionCode;
    record.exception_flags = exception.ExceptionFlags;
    record.exception_address = static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(exception.ExceptionAddress));
    record.parameter_count = (std::min)(static_cast<std::uint32_t>(exception.NumberParameters), 15u);
    for (std::uint32_t i = 0; i < record.parameter_count; ++i)
        record.exception_information[i] = static_cast<std::uint32_t>(exception.ExceptionInformation[i]);

    const CONTEXT& context = *pointers->ContextRecord;
    record.eip = context.Eip;
    record.esp = context.Esp;
    record.ebp = context.Ebp;
    record.eax = context.Eax;
    record.ebx = context.Ebx;
    record.ecx = context.Ecx;
    record.edx = context.Edx;
    record.esi = context.Esi;
    record.edi = context.Edi;
    record.eflags = context.EFlags;
    read_exception_memory(reinterpret_cast<const void*>(static_cast<std::uintptr_t>(record.esp)),
                          record.stack_words, sizeof(record.stack_words));

    std::uint32_t frame = record.ebp;
    for (std::size_t i = 0; i < (std::size(record.frames)); ++i) {
        std::uint32_t words[2]{};
        if (frame < record.esp || !read_exception_memory(reinterpret_cast<const void*>(static_cast<std::uintptr_t>(frame)),
                                                          words, sizeof(words))) break;
        record.frames[i] = {frame, words[1]};
        if (words[0] <= frame || words[0] - frame > 0x00100000u) break;
        frame = words[0];
    }
    write_exception_record(record);
}

LONG CALLBACK capture_access_violation(PEXCEPTION_POINTERS pointers) {
    record_access_violation(pointers, ExceptionRecordKindV1::AccessViolationFirstChance);
    return EXCEPTION_CONTINUE_SEARCH;
}

LONG WINAPI capture_unhandled_exception(PEXCEPTION_POINTERS pointers) {
    record_access_violation(pointers, ExceptionRecordKindV1::AccessViolationUnhandled);
    if (g_previous_unhandled_filter && g_previous_unhandled_filter != capture_unhandled_exception)
        return g_previous_unhandled_filter(pointers);
    return EXCEPTION_CONTINUE_SEARCH;
}

bool enable_exception_capture() {
    if (!g_config.logging_enabled) return true;
    if (g_exception_handler) return true;

    char path[MAX_PATH]{};
    const DWORD length = GetModuleFileNameA(nullptr, path, MAX_PATH);
    if (!length || length >= MAX_PATH) return false;
    char* slash = path + length;
    while (slash > path && slash[-1] != '\\' && slash[-1] != '/') --slash;
    constexpr char filename[] = "MRallyeRandomizer-crash-v1.bin";
    if (static_cast<std::size_t>(path + MAX_PATH - slash) <= sizeof(filename)) return false;
    std::memcpy(slash, filename, sizeof(filename));
    g_exception_log = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                                  nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (g_exception_log == INVALID_HANDLE_VALUE) return false;

    ExceptionRecordV1 session{};
    fill_exception_record(session, ExceptionRecordKindV1::Session);
    write_exception_record(session);
    g_exception_handler = AddVectoredExceptionHandler(1, capture_access_violation);
    if (!g_exception_handler) {
        CloseHandle(g_exception_log);
        g_exception_log = INVALID_HANDLE_VALUE;
        return false;
    }
    g_previous_unhandled_filter = SetUnhandledExceptionFilter(capture_unhandled_exception);
    InterlockedExchange(&g_exception_capture_enabled, 1);
    return true;
}

void update_start_snapshot(int opponents, int track, int mode, bool ghost,
                           bool split, int player_id, int player_class) {
    InterlockedExchange(&g_last_opponent_count, opponents);
    InterlockedExchange(&g_last_track, track);
    InterlockedExchange(&g_last_mode, mode);
    InterlockedExchange(&g_last_ghost, ghost ? 1 : 0);
    InterlockedExchange(&g_last_split_screen, split ? 1 : 0);
    InterlockedExchange(&g_last_player_id, player_id);
    InterlockedExchange(&g_last_player_class, player_class);
}

} // namespace

// Called by the entry-point bootstrap after LoadLibrary has returned, outside
// the loader lock and before the retail CRT/game constructors begin.
extern "C" __declspec(dllexport) DWORD WINAPI MRConfigureBlobV1(const void* blob) {
    if (!blob) return 0;
    const auto* bytes = static_cast<const std::uint8_t*>(blob);
    std::uint32_t size = 0;
    std::memcpy(&size, bytes, sizeof(size));
    if (size > kMaxConfigBytes) return 0;

    try {
        Config next{};
        char initial_hash[65]{};
        if (size == 0) {
            next = Config{}; // missing INI is a safe stock / extender-off default
            if (!sha256_text(nullptr, 0, initial_hash)) return 0;
        } else {
            const std::string_view source(reinterpret_cast<const char*>(bytes + sizeof(size)), size);
            const auto parsed = parse_ini(source);
            if (!parsed.accepted) {
                next = Config{}; // reject the whole malformed file; never partial-apply
                if (!sha256_text(nullptr, 0, initial_hash)) return 0;
            } else {
                next = parsed.config;
                if (!sha256_text(bytes + sizeof(size), size, initial_hash)) return 0;
            }
        }

        {
            ExclusiveGuard guard(&g_lock);
            g_config = next;
            g_generation_config = next;
            g_configured = true;
            g_next_slot = 0;
            g_generation_id = 0;
            g_active_mode = -1;
            g_expected_slot = 0;
            g_diverse_cycle = ClassCycle{};
            g_challenge.clear();
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
            g_prepared_player.clear();
            g_prepared_player.generation = 0;
            g_prepared_player_hash[0] = '\0';
#endif
            std::memcpy(g_config_hash, initial_hash, sizeof(g_config_hash));
            std::memcpy(g_generation_hash, initial_hash, sizeof(g_generation_hash));
            std::uint32_t flags = next.logging_enabled ? kExceptionConfigLogging : 0u;
            if (config_needs_randomizer_hooks(next)) flags |= kExceptionConfigRandomizer;
            if (config_requests_opponent_extension(next)) flags |= kExceptionConfigOpponents;
            InterlockedExchange(&g_config_flags, static_cast<LONG>(flags));
        }
        if (!enable_exception_capture()) return 0;
        note_effective_configuration();
        if (g_config.logging_enabled && g_config.config_version == 1) {
            append_runtime_log("WARNING config_v1_migration=legacy_numeric_mapping_preserved; V2 uses 1=T1 and 4=Full");
        }
        return 1;
    } catch (...) {
        return 0;
    }
}

#if defined(RMOD_EXTRA_OPTIONS)
extern "C" __declspec(dllexport) DWORD WINAPI MRRegisterSdkRosterV1(const SdkRosterV1* profile) {
    SdkRosterV1 header{};SIZE_T bytes_read=0;
    if(!profile||!ReadProcessMemory(GetCurrentProcess(),profile,&header,sizeof(header),&bytes_read)||bytes_read!=sizeof(header)||
       header.size!=sizeof(SdkRosterV1)||header.version!=1||!header.vehicles||
       header.count>SIZE_MAX/sizeof(SdkVehicleV1)||header.challenge_human_offset<0x570||header.challenge_human_offset>INT_MAX)return 0;
    uint32_t registry_count=0,registry_classes=0;wchar_t registry_env[32]{};
    const auto registry_length=GetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",registry_env,32);
    if(registry_length){
        uint32_t address=0;mr_vehicle_registry::DescriptorV1 registry{};
        if(registry_length>=32||!extra_registry::address(registry_env,address)||
           !ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(uintptr_t(address)),&registry,sizeof(registry),&bytes_read)||
           bytes_read!=sizeof(registry)||!extra_registry::descriptor(registry))return 0;
        registry_count=registry.record_count;
        registry_classes=registry.reverse_classes_va;
    }else if(GetLastError()!=ERROR_ENVVAR_NOT_FOUND)return 0;
    if(registry_count&&header.count!=registry_count-26)return 0;
    const size_t bytes=size_t(header.count)*sizeof(SdkVehicleV1);
    if(uint64_t(reinterpret_cast<uintptr_t>(header.vehicles))+bytes>UINT64_C(0x100000000))return 0;
    try {
        std::vector<uint32_t> class_snapshot(registry_count);
        if(registry_count&&(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(uintptr_t(registry_classes)),class_snapshot.data(),size_t(registry_count)*4,&bytes_read)||bytes_read!=size_t(registry_count)*4||
            std::any_of(class_snapshot.begin(),class_snapshot.end(),[](uint32_t c){return c>2;})))return 0;
        std::vector<SdkVehicleV1> source(header.count);
        if(bytes&&(!ReadProcessMemory(GetCurrentProcess(),header.vehicles,source.data(),bytes,&bytes_read)||bytes_read!=bytes))return 0;
        std::vector<RegisteredAddon> next;next.reserve(header.count);std::unordered_set<int> identities;
        for(const auto& row:source){
            if(row.physical_id<26||(registry_count&&unsigned(row.physical_id)>=registry_count)||row.class_id<0||row.class_id>2||row.mode_mask&~31u||!identities.insert(row.physical_id).second)return 0;
            if(registry_count&&class_snapshot[size_t(row.physical_id)]!=unsigned(row.class_id))return 0;
            next.push_back({row.physical_id,row.class_id,true,true,true,(row.mode_mask&1u)!=0,row.mode_mask});
        }
        ExclusiveGuard guard(&g_lock);g_registered=std::move(next);g_registry_classes=std::move(class_snapshot);g_challenge_human_offset=header.challenge_human_offset;return 1;
    }catch(...){return 0;}
}
#endif

extern "C" __declspec(dllexport) int WINAPI MRChooseClassV1(
    int hint, int first, int count, int slot) {
    try {
    ExclusiveGuard guard(&g_lock);
    if (!g_configured || first != 1 || count < 1 ||
        count > static_cast<int>(kMaximumAi) || slot < first || slot >= first + count) {
        return -1;
    }
    const GameMode mode = resolve_roster_mode(hint);
    if (mode == GameMode::Unknown || !safe_one_human_roster_context(mode, first, count, slot))
        return -1;
    int player_id = -1;
    int player_class = -1;
    if (!read_player_identity(mode, player_id, player_class)) {
        return -1;
    }

    if (slot == first) {
        const char* reload = reload_generation_policy_snapshot();
        begin_generation_snapshot(mode, first, reload);
    }
    if (mode != static_cast<GameMode>(g_active_mode) || slot != g_expected_slot) {
        return -1;
    }
    ++g_expected_slot;
    g_next_slot = static_cast<unsigned>(g_expected_slot);

    std::vector<int> prior_ids;
    prior_ids.reserve(static_cast<std::size_t>(slot - first));
    for (int prior = first; prior < slot; ++prior) {
        const int id = native_car_id(mode, prior);
        if (runtime_class(id) < 0) {
            return -1;
        }
        prior_ids.push_back(id);
    }

    const Config snapshot = g_generation_config;
#if defined(RMOD_EXTRA_OPTIONS)
    g_generation_ai_count=count;
#endif
    if (mode == GameMode::QuickRace) {
        const auto count_plan = plan_quick_race(2, static_cast<unsigned>(count), false, snapshot);
        if (!count_plan.allowed) {
            if (snapshot.logging_enabled) append_runtime_log("WARNING roster_selection=retail_stock_fallback reason=count-policy-gate");
            return -1;
        }
    }

    const Policy policy = policy_for_mode(snapshot, mode);
#if defined(RMOD_EXTRA_OPTIONS)
    const auto pool = runtime_pool(mode, reward_mask(), policy==Policy::Stock?AddonMode::RegisteredOnly:snapshot.addons);
    g_generation_pool=pool;
#else
    const auto pool = runtime_pool(mode, reward_mask(),snapshot.addons);
#endif
    ClassCycle* cycle = policy == Policy::Diverse ? &g_diverse_cycle : nullptr;
    if (cycle && slot == first) {
        unsigned mask = 0;
        for (const auto& vehicle : pool) mask |= 1u << vehicle.class_id;
        if (!cycle->begin(mask, [](int upper) { return native_draw(upper); })) return -1;
    }

    // Stock in a three-AI mode is a genuine pass-through. The bounded Stock
    // extension selects the human's class only when its physical pool must be
    // rebuilt; the native chooser still owns physical IDs, DriverIDs and actors.
    const bool use_policy = policy != Policy::Stock ||
        (mode == GameMode::QuickRace && count > static_cast<int>(kNativeAiMaximum));
    const auto selected = choose_class(policy, use_policy,
        static_cast<unsigned>(count), player_class, player_id, pool, prior_ids, cycle,
        [](int upper) { return native_draw(upper); }, snapshot.duplicates_when_needed);
    if (selected.kind != ClassSelectionKind::SelectedClass) return -1;
    // The Quick Race emitted selector consumes this private return extension
    // to stop pruning the native source pool after every eligible CarID has
    // already been used. Campaign selectors retain the historical class-only
    // result and native mode lifecycle.
#if defined(RMOD3_G1_DUPLICATE_REPEAT_FALLBACK)
    // Only the G1 Quick Race selector understands this private high-bit
    // return marker. F3 and campaign selectors retain the historical 0..2
    // class result, keeping their generated bytes and callback contract
    // unchanged.
    if (mode == GameMode::QuickRace && selected.duplicates_needed)
        return selected.class_id | 0x100;
#endif
    return selected.class_id;
    } catch (...) {
        return -1;
    }
}

#if defined(RMOD_EXTRA_OPTIONS)
extern "C" __declspec(dllexport) DWORD WINAPI MRFilterAiPoolV1(int hint,int cls,void* vector) {
    try {
        ExclusiveGuard guard(&g_lock);
        const auto mode=static_cast<GameMode>(g_active_mode);
        const bool owner=(hint==0&&mode==GameMode::QuickRace)||(hint==4&&mode==GameMode::MasterRallye)||
            (hint==2&&(mode==GameMode::RallyeCup||mode==GameMode::Invitation));
        if(!owner||cls<0||cls>2||g_generation_pool.empty())return 0;
        const bool stock=policy_for_mode(g_generation_config,mode)==Policy::Stock;
        const bool rebuild=!stock||(mode==GameMode::QuickRace&&g_generation_ai_count>int(kNativeAiMaximum));
        std::array<uint32_t,4> descriptor{};SIZE_T read=0;
        if(!vector||!ReadProcessMemory(GetCurrentProcess(),vector,descriptor.data(),sizeof(descriptor),&read)||read!=sizeof(descriptor))return 0;
        const uint32_t first=descriptor[1],last=descriptor[2],capacity=descriptor[3];
        if(first>last||last>capacity||(last-first)%4||(capacity-first)%4||
           (last-first)/4>25+g_registered.size())return 0;
        std::vector<int> ids((last-first)/4);
        if(!ids.empty()&&(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(uintptr_t(first)),ids.data(),last-first,&read)||read!=last-first))return 0;
        auto filtered=stock?ids:filter_registry_ai_pool(ids,g_generation_pool,cls);
        if(g_generation_config.logging_enabled&&g_ai_observations.size()<8&&
           std::none_of(g_ai_observations.begin(),g_ai_observations.end(),[&](const AiPoolObservation& p){return p.cls==cls&&p.before==ids&&p.after==filtered;}))g_ai_observations.push_back({cls,ids,filtered});
        if(rebuild)unbias_rebuilt_ai_pool(filtered,g_registry_shuffle_draw);
        SIZE_T written=0;const auto bytes=filtered.size()*sizeof(int);
        if(bytes&&(!WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(uintptr_t(first)),filtered.data(),bytes,&written)||written!=bytes))return 0;
        const uint32_t end=first+static_cast<uint32_t>(bytes);
        auto* end_field=static_cast<unsigned char*>(vector)+8;
        if(!WriteProcessMemory(GetCurrentProcess(),end_field,&end,sizeof(end),&written)||written!=sizeof(end)) {
            if(!ids.empty())WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(uintptr_t(first)),ids.data(),last-first,&written);
            return 0;
        }
        return 1;
    }catch(...){return 0;}
}
#endif

void clear_challenge_selection() {
    g_challenge.clear();
}

bool safe_challenge_frontend() {
    const bool split = native<NativeGetObjectBoolean>(0x004AE2D0)(
        native<NativeSingleton>(0x004AE700)());
    void* race = race_state();
    if (!race) return false;
    const int network = native<NativeGetObjectInteger>(0x004AC0A0)(race);
    return !split && network == 0;
}

bool authored_challenge_identity(int event, int human, int opponent) {
    if (event < 0 || event > 10 || runtime_class(human) < 0 || runtime_class(opponent) < 0)
        return false;
    auto registry = native<NativeSingleton>(0x0045A3C0)();
    if (!registry) return false;
    auto* bytes = static_cast<std::uint8_t*>(registry);
    #if defined(RMOD_EXTRA_OPTIONS)
    const std::size_t record = g_challenge_human_offset + static_cast<std::size_t>(event + 25) * 0x2cu;
#else
    const std::size_t record = 0x570u + static_cast<std::size_t>(event + 25) * 0x2cu;
#endif
    int authored_human = -1, authored_opponent = -1;
    std::memcpy(&authored_human, bytes + record, sizeof(authored_human));
    std::memcpy(&authored_opponent, bytes + record + 4, sizeof(authored_opponent));
    return authored_human == human && authored_opponent == opponent;
}

void note_challenge_selection(const char* action) {
    if (!g_config.logging_enabled) return;
    const int identity = g_challenge.preview_identity();
    const int cls = runtime_class(identity);
    char line[320]{};
    const int size = wsprintfA(line,
        "CHALLENGE_PREVIEW action=%s generation=%u event=%d policy=%u:%s CarID=%d CarClass=%d config_sha256=%s",
        action ? action : "unknown", g_challenge.generation_id, g_challenge.event_id,
        policy_numeric_id_for_version(g_challenge.policy, g_generation_config.config_version), policy_name(g_challenge.policy),
        identity, cls, g_challenge.config_hash.c_str());
    if (size > 0 && size < static_cast<int>(sizeof(line))) append_runtime_log(line);
}

#if defined(RMOD3_G2_PLAYER_OVERRIDE)
const char* player_vehicle_mode_name(PlayerVehicleMode mode) {
    switch (mode) {
    case PlayerVehicleMode::Forced: return "Forced";
    case PlayerVehicleMode::Random: return "Random";
    default: return "Stock";
    }
}

void note_player_vehicle(const char* action, const char* reason, int input_id) {
    if (!g_config.logging_enabled || !action) return;
    char line[512]{};
    const int chosen = g_prepared_player.ready ? g_prepared_player.physical_id : input_id;
    const int cls = g_prepared_player.ready ? g_prepared_player.class_id : runtime_class(input_id);
    const int size = wsprintfA(line,
        "PLAYER_VEHICLE action=%s mode=%s generation=%u input_CarID=%d prepared_CarID=%d CarClass=%d consumed=%u reason=%s config_sha256=%s",
        action, player_vehicle_mode_name(g_prepared_player.mode_snapshot),
        g_prepared_player.generation, input_id, chosen, cls,
        g_prepared_player.consumed ? 1u : 0u,
        reason ? reason : "none", g_prepared_player_hash);
    if (size > 0 && size < static_cast<int>(sizeof(line))) append_runtime_log(line);
}
#endif

extern "C" __declspec(dllexport) int WINAPI MRChallengeV1(
    int hint, int first, int count, int slot) {
    try {
        ExclusiveGuard guard(&g_lock);
        if (!g_configured || hint != 1) return -1;
        if (first == -100) {
            clear_challenge_selection();
            return -1;
        }
        if (first >= 100 && first <= 110) {
            const int event = first - 100;
            const int human = count;
            const int authored = slot;
            if (!safe_challenge_frontend() || !authored_challenge_identity(event, human, authored)) {
                clear_challenge_selection();
                return -1;
            }
            if (g_challenge.matches(event, human, authored))
                return g_challenge.selected_opponent_id;

            clear_challenge_selection();
            const char* reload = reload_generation_policy_snapshot();
            begin_generation_snapshot(GameMode::Challenge, 1, reload);
            g_challenge.prepare(event, human, authored, g_generation_id,
                policy_for_mode(g_generation_config, GameMode::Challenge), g_generation_hash);

            if (g_challenge.policy != Policy::Stock) {
                const auto pool = runtime_pool(GameMode::Challenge, reward_mask(), g_generation_config.addons);
                std::uint8_t class_mask = 0;
                for (const auto& vehicle : pool) {
                    if (vehicle.physical_id != human)
                        class_mask |= static_cast<std::uint8_t>(1u << vehicle.class_id);
                }
                ClassCycle cycle;
                ClassCycle* cycle_ptr = nullptr;
                if (g_challenge.policy == Policy::Diverse) {
                    if (!cycle.begin(class_mask, [](int upper) { return native_draw(upper); }))
                        return -1;
                    cycle_ptr = &cycle;
                }
                const auto selected = choose_vehicle(g_challenge.policy, true, 1,
                    runtime_class(human), human, pool, {}, cycle_ptr,
                    [](int upper) { return native_draw(upper); }, g_generation_config.duplicates_when_needed);
                if (selected.kind == SelectionKind::SelectedId && selected.physical_id != human &&
                    runtime_class(selected.physical_id) >= 0)
                    g_challenge.selected_opponent_id = selected.physical_id;
            }
            note_challenge_selection("Begin");
            return g_challenge.consume(event, human, authored);
        }

        if (first != 1 || count != 1 || slot != 1 || !g_challenge.ready ||
            !safe_challenge_frontend()) return -1;
        void* race = race_state();
        if (!race || native<NativeGetObjectInteger>(0x004ABE90)(race) != 7) return -1;
        const int event = native<NativeGetObjectInteger>(0x004ABF20)(race) - 25;
        const int human = native_car_id(GameMode::Challenge, 0);
        if (!g_challenge.matches(event, human, g_challenge.authored_opponent_id) ||
            !authored_challenge_identity(event, human, g_challenge.authored_opponent_id)) return -1;
        note_challenge_selection("Use");
        return g_challenge.consume(event, human, g_challenge.authored_opponent_id);
    } catch (...) {
        return -1;
    }
}

extern "C" __declspec(dllexport) int WINAPI MROpponentLimitV1() {
    SharedGuard guard(&g_lock);
    const int result = g_configured && config_requests_opponent_extension(g_config)
        ? static_cast<int>(g_config.max_opponents) : static_cast<int>(kNativeAiMaximum);
    return result;
}

#if defined(RMOD3_G2_PLAYER_OVERRIDE)
// phase 0 is the VehicleSetup/VehicleSelect constructor's QuickRace/Car0 read.
// phase 1 is FUN_0047B780's first Car0 read immediately before publishing Race/Car0.
// Both return one physical ID; only phase 0 may draw, and it does so once per
// constructor entry. The setup phase consumes the cached identity, including
// on a native Restart path.
extern "C" __declspec(dllexport) int WINAPI MRQuickRacePlayerCarV1(int current_id, int phase) {
    try {
        ExclusiveGuard guard(&g_lock);
        if (!g_configured || (phase != 0 && phase != 1)) return current_id;
        if (phase == 0) {
            const char* reload = reload_generation_policy_snapshot();
            const Config snapshot = g_config;
            const auto available = eligible_vehicles(GameMode::QuickRace, reward_mask(), {}, AddonMode::StockOnly);
            const auto decision = prepare_player_vehicle(g_prepared_player, snapshot,
                GameMode::QuickRace, 0, current_id, available,
                [](int upper) { return native_draw(upper); });
            std::memcpy(g_prepared_player_hash, g_config_hash, sizeof(g_prepared_player_hash));
            if (decision.kind == PlayerVehicleDecisionKind::Selected) {
                native<NativeSetQuickCar>(0x004ADF50)(0, decision.physical_id);
                const int verified = native<NativeGetQuickCar>(0x004ADFB0)(0);
                if (verified != decision.physical_id ||
                    runtime_class(verified) != decision.class_id) {
                    g_prepared_player.clear();
                    note_player_vehicle("entry-refused", "QuickRace/Car0 setter readback mismatch", current_id);
                    return current_id;
                }
                note_player_vehicle("entry-prepared", decision.reason.c_str(), current_id);
                return decision.physical_id;
            }
            if (decision.kind == PlayerVehicleDecisionKind::Refused) {
                g_prepared_player.clear();
                note_player_vehicle("entry-refused", decision.reason.c_str(), current_id);
                return current_id;
            }
            note_player_vehicle("entry-stock", reload ? decision.reason.c_str() : "no reload status", current_id);
            return current_id;
        }

        const int selected_id = consume_prepared_player_vehicle(
            g_prepared_player, GameMode::QuickRace, 0, current_id);
        if (selected_id != current_id) {
            native<NativeSetQuickCar>(0x004ADF50)(0, selected_id);
            const int verified = native<NativeGetQuickCar>(0x004ADFB0)(0);
            note_player_vehicle("race-setup-consume",
                verified == selected_id ? "prepared CarID consumed by native Quick Race setup"
                                        : "prepared CarID returned to native setup; Broker setter readback differed",
                current_id);
            return selected_id;
        }
        if (g_prepared_player.ready) {
            g_prepared_player.consumed = true;
            note_player_vehicle("race-setup-consume", "native Stock/current CarID consumed", current_id);
        }
        return current_id;
    } catch (...) {
        return current_id;
    }
}
#endif

extern "C" __declspec(dllexport) DWORD WINAPI MRCanStartQuickRaceV1() {
    SharedGuard guard(&g_lock);
    InterlockedExchange(&g_start_phase, static_cast<LONG>(StartPhaseV1::GuardEntered));
    if (!g_configured) {
        InterlockedExchange(&g_start_phase, static_cast<LONG>(StartPhaseV1::StartAllowed));
        return 1; // uninitialized hook falls back to native Stock behavior
    }
    const int raw_count = native<NativeGetInteger>(0x004AE150)();
    const int track = native<NativeGetInteger>(0x004AE030)();
    const int mode = native<NativeGetInteger>(0x004AE090)();
    const bool ghost = native<NativeGetBoolean>(0x004AE0F0)() != FALSE;
    const bool split = native<NativeGetBoolean>(0x004AE2D0)() != FALSE;
    const int player_id = native<NativeGetQuickCar>(0x004ADFB0)(0);
    const int player_class = runtime_class(player_id);
    const auto gate = evaluate_native_start_gate(mode, raw_count, split, g_config);
    const auto selected_count = gate.selected_count;
    const auto& topology = gate.topology;
    auto decision = gate.decision;
    if (mode == 2 && selected_count > kNativeAiMaximum &&
        !g_config.duplicates_when_needed && config_needs_randomizer_hooks(g_config)) {
#if defined(RMOD_EXTRA_OPTIONS)
        const auto pool = runtime_pool(GameMode::QuickRace, reward_mask(),policy_for_mode(g_config,GameMode::QuickRace)==Policy::Stock?AddonMode::RegisteredOnly:g_config.addons);
#else
        const auto pool = runtime_pool(GameMode::QuickRace,reward_mask(),g_config.addons);
#endif
        decision = enforce_quickrace_duplicate_capacity(
            decision, mode, selected_count, true, g_config.duplicates_when_needed,
            policy_for_mode(g_config, GameMode::QuickRace), player_class, player_id, pool);
    }
    update_start_snapshot(static_cast<int>(selected_count), track, mode, ghost, split, player_id, player_class);
    const bool allowed = decision.allowed;
    note_start_decision(allowed, selected_count, track, mode, ghost, split, player_id,
                        player_class, topology, decision.reason.c_str());
    InterlockedExchange(&g_start_phase, static_cast<LONG>(allowed
        ? StartPhaseV1::StartAllowed : StartPhaseV1::StartBlocked));
    return allowed ? 1u : 0u;
}

extern "C" __declspec(dllexport) void WINAPI MRSetStartPhaseV1(DWORD phase) {
    if (phase == static_cast<DWORD>(StartPhaseV1::NativeSetupEntered) ||
        phase == static_cast<DWORD>(StartPhaseV1::NativeSetupReturned)) {
        InterlockedExchange(&g_start_phase, static_cast<LONG>(phase));
#if defined(RMOD_EXTRA_OPTIONS)
        try {
            ExclusiveGuard guard(&g_lock);
            if(phase==static_cast<DWORD>(StartPhaseV1::NativeSetupEntered)) {
                g_quick_report_pending=true;g_ai_observations.clear();
            }else if(g_quick_report_pending) {
                g_quick_report_pending=false;
                if(!g_generation_config.logging_enabled)return;
                int player=-1;std::vector<int> ai;
                if(!g_final_roster_reader(player,ai)){g_final_roster_sink("AI_ROSTER_FINAL unavailable=invalid-native-snapshot");return;}
                const auto policy=policy_for_mode(g_generation_config,GameMode::QuickRace);
                const auto list=[](const std::vector<int>& ids){std::string s="[";for(size_t i=0;i<ids.size()&&i<64;++i)s+=(i?",":"")+std::to_string(ids[i]);if(ids.size()>64)s+=",...count="+std::to_string(ids.size());return s+"]";};
                std::string line="AI_ROSTER_FINAL stage=native-setup-return generation="+std::to_string(g_generation_id)+" policy="+policy_name(policy)+" player="+std::to_string(player)+" ai="+list(ai);
                for(const auto& pool:g_ai_observations)line+=" pool(class="+std::to_string(pool.cls)+",before="+list(pool.before)+",after="+list(pool.after)+")";
                for(const auto& row:g_registered) {
                    bool before=false,after=false;for(const auto& pool:g_ai_observations){before|=std::find(pool.before.begin(),pool.before.end(),row.physical_id)!=pool.before.end();after|=std::find(pool.after.begin(),pool.after.end(),row.physical_id)!=pool.after.end();}
                    const bool chosen=std::find(ai.begin(),ai.end(),row.physical_id)!=ai.end();
                    const char* reason=row.physical_id==player?"human-excluded":chosen?"selected":!before?"outside-observed-native-pool":!after?"policy-ineligible":"eligible-not-drawn";
                    line+=" addon="+std::to_string(row.physical_id)+":"+reason;
                }
                g_final_roster_sink(line.c_str());
            }
        }catch(...){append_runtime_log("AI_ROSTER_FINAL unavailable=read-error");}
#endif
    }
}

BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID) {
    return TRUE; // no work under the Windows loader lock
}
