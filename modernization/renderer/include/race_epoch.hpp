#pragma once
#include "game_fov.hpp"
#include <array>
#include <cstdint>
#include <string>

namespace gfx2 {
// A3c is a read-only observation pilot. No state in this module authorizes camera writes.
enum class RaceEvent : uint32_t {Request, Queue, ExecuteBegin, Commit, ExecuteEnd,
 OpenError, ReadError, OwnerAttach, OwnerInitialized, OwnerLive, Retire, Destroy,
 Reset, Release, Rejected};
enum class RacePhase {Unknown, Requested, Executing, AwaitingOwner, Failed, Revoked};
struct RaceTransition {
 uint64_t serial=0, generation=0, job_lifetime=0, owner_lifetime=0;
 RaceEvent event=RaceEvent::Rejected;
 uint32_t job=0,actor=0,ai=0,scene=0;
 const char* reason="unknown";
 uint32_t thread=0;
};
struct RaceJob {
 uint32_t pointer=0,scene=0,source=0;
 uint64_t generation=0,lifetime=0;
 bool executing=false,commit_seen=false,commit_success=false,terminal=false,reused=false;
 uint8_t flag21=0,flag22=0;
 std::array<char,192> scene_text{},source_text{};
};
struct RaceOwner {
 uint32_t actor=0,ai=0;
 uint64_t generation=0,lifetime=0,execution_job_lifetime=0;
 bool initialized=false,live=false,retired=false;
};
class RaceEpoch {
public:
 static constexpr size_t MAX_JOBS=64,MAX_EVENTS=128;
 uint64_t generation=0,successful_generation=0,job_serial=0,owner_serial=0,event_serial=0;
 uint32_t requested_scene=0,committed_scene=0,executing_job=0;
 uint32_t observed_thread=0;
 std::array<char,192> request_text{};
 RacePhase phase=RacePhase::Unknown;
 const char* reason="attach_requires_new_request";
 bool poisoned=false;
 RaceOwner owner{};
 std::array<RaceJob,MAX_JOBS> jobs{};
 std::array<RaceTransition,MAX_EVENTS> events{};
 size_t jobs_used=0,events_used=0,event_head=0;
 void request(uint32_t scene,const char* text=nullptr) noexcept;
 void queue(uint32_t job,uint32_t scene,uint32_t source,bool type_ok,uint8_t flag21=0,uint8_t flag22=0,const char* source_text=nullptr) noexcept;
 void begin(uint32_t job,bool type_ok) noexcept;
 void commit(uint32_t scene,bool success) noexcept;
 void end(uint32_t job) noexcept;
 void error(uint32_t job,bool read_error) noexcept;
 void attach(uint32_t actor,uint32_t ai,bool slot_ok) noexcept;
 void initialized(uint32_t actor,uint32_t ai,bool valid) noexcept;
 void admitted(uint32_t actor,bool valid) noexcept;
 void retire(uint32_t actor,bool destroyed) noexcept;
 void cancel(RaceEvent event,const char* why) noexcept;
 void reject(const char* why,bool permanent=false,uint32_t observed_job=0) noexcept;
 const RaceJob* find(uint32_t pointer) const noexcept;
 const RaceTransition& chronological(size_t index) const noexcept;
 bool correlated_owner_candidate() const noexcept;
 bool validate_thread(uint32_t expected,uint32_t actual) noexcept;
 bool authorizes_camera_writes() const noexcept {return false;}
private:
 RaceJob* find_mutable(uint32_t pointer) noexcept;
 void note(RaceEvent event,const char* why,uint32_t job=0) noexcept;
 bool next(uint64_t& counter) noexcept;
};

// All native pointers are PE32 integers. The reader never calls native getters.
class RaceReadMemory {
public:virtual ~RaceReadMemory()=default;
 virtual bool read(uint32_t address,void* output,size_t bytes) noexcept=0;
};
struct RaceScalar {bool present=false;uint32_t tag=UINT32_MAX;int32_t value=0;};
struct RaceOwnerRead {
 uint32_t actor=0,ai=0,registrations=0,live_memberships=0,pending_memberships=0;
 uint32_t count=0;bool retired=false,type_ok=false,arrays_ready=false,participant_states_ready=false;
 bool valid=false;const char* reason="owner_unobserved";
 std::array<int32_t,8> participant_states{};
};
inline constexpr std::array<const char*,9> RACE_CONTEXT_KEYS={
 "Race/Type","Race/NumPlayers","Race/NumNetworkPlayers","Race/NetworkSyncActive",
 "Race/AttractMode","Race/GhostPlayback","Race/PlaybackReplay","Race/FinishingType","Race/NumCars"};
inline constexpr std::array<uint32_t,9> RACE_CONTEXT_TAGS={2,2,2,0,0,0,0,2,2};
bool race_pool_text(RaceReadMemory& m,uint32_t base,uint32_t id,char* text,size_t capacity) noexcept;
bool race_pool_id(RaceReadMemory& m,uint32_t base,const char* text,uint32_t& id) noexcept;
RaceScalar race_broker_scalar(RaceReadMemory& m,uint32_t base,uint32_t id,uint32_t tag) noexcept;
RaceOwnerRead read_race_owner(RaceReadMemory& m,uint32_t base,const RaceOwner& identity,uint64_t current_generation) noexcept;
struct RaceContextCheck {bool supported=false;const char* reason="context_incomplete";};
RaceContextCheck check_race_context(const std::array<RaceScalar,9>& fields,const RaceOwnerRead& owner) noexcept;

struct RacePatchUnit {
 void* address=nullptr;size_t size=0;
 std::array<unsigned char,5> original{},replacement{};
 bool owned=false;
};
struct RaceNativeAnchor {uint32_t va;const char* role;const char* bytes;};
inline constexpr std::array<RaceNativeAnchor,8> RACE_OBSERVER_CONTEXTS={{
 {0x005223bd,"RequestStoredBeforeObservedCall","8b07686c7c6e008d4c2414c744240c00000000894604e8f8edfaff"},
 {0x00522446,"QueueCallerThreeArguments","8b4424188b542414508d44240c5250e8f6b00000"},
 {0x0052d698,"CommitCallerBooleanAndManager","8b4c240c51e89e50ffff8bc8e8d74fffff"},
 {0x0048e70f,"RaceLimitsAttachSlotAndAI","50538bce896c2428e834720600"},
 {0x004f61f3,"PendingActorTransferredToLiveList","0fbe466c8d4e608d1440518b4c952ce8d9000000"},
 {0x004f5846,"RetirementBitBeforeObservedCall","0c025688018d7118e8bd0a0000"},
 {0x004f5780,"DestructorBeforeUnregisterAndArrayFree","53568bf15756e8850b0000"},
 {0x00691b10,"SceneJobClassCallbackTargets","60245200e0d5520000d6520020d65200"}
}};
bool race_observer_context_valid(PatchMemory& memory,uintptr_t base) noexcept;
// Fixed observer sites only. Caller must exclude concurrent execution before exchanging code.
class RacePatchBatch {
public:
 static constexpr size_t MAX_SITES=10;
 std::array<RacePatchUnit,MAX_SITES> sites{};size_t count=0;
 bool rollback_verified=true;
 bool install(PatchMemory& memory) noexcept;
 bool remove(PatchMemory& memory) noexcept;
 bool owned() const noexcept;
private:
 bool exchange(PatchMemory& memory,RacePatchUnit& site,bool installing) noexcept;
};
bool install_race_observer(bool exact_retail,bool trace_enabled) noexcept;
void release_race_observer() noexcept;
void reset_race_observer() noexcept;
// Called only by the existing F10 writer, not a second hotkey controller.
std::string race_epoch_capture_json(uint64_t device,uint64_t frame);
namespace race_bridge {
 struct Saved {uint32_t edi,esi,ebp,esp,ebx,edx,ecx,eax,flags,return_pc,args[3];};
 using Callback=void(__stdcall*)(uint32_t event,const Saved* input);
 extern Callback callback;
 extern uintptr_t request_original,queue_original,commit_original,attach_original,
  live_original,retire_original,destroy_original,open_error_original,read_error_original,execute_original;
 void request();void queue();void commit();void attach();void live();void retire();void destroy();
 void open_error();void read_error();void execute();
}
}
