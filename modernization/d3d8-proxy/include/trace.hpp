#pragma once
#include "state_tracker.hpp"
#include "provenance.hpp"
#include <mutex>
#include <memory>
#include <atomic>
namespace gfx2 {
inline constexpr size_t MAX_DRAWS=8192,MAX_EVENTS=16384,MAX_BUFFER_BYTES=32*1024*1024;
struct Event {uint32_t slot=0,result=0;Args args;uintptr_t pc=0;uint32_t draw=UINT32_MAX;
 uint32_t payload[32]{};uint32_t payload_words=0;};
struct Draw { Snapshot state;std::array<uint64_t,8> texture_generation{};
 std::array<uint64_t,16> stream_generation{};uint64_t index_generation=0; };
struct FrameBuffer {std::array<Event,MAX_EVENTS> events;std::array<Draw,MAX_DRAWS> draws;
 size_t event_count=0,draw_count=0;bool truncated=false;uint64_t dropped=0;};
static_assert(sizeof(FrameBuffer)<=MAX_BUFFER_BYTES,"hard capture allocation limit");
class Trace {
public:
 Trace() noexcept;
 ~Trace();
 class Guard {
  Trace& t_;bool held_;
 public:explicit Guard(Trace& t) noexcept;~Guard();Guard(const Guard&)=delete;
 };
 Guard guard() noexcept {return Guard(*this);}
 void before(uint32_t slot,const Args& args,uintptr_t pc) noexcept;
 void after(uint32_t slot,const Args& args,uint32_t result,uintptr_t pc) noexcept;
 void shutdown(uint32_t real_refs) noexcept;
 std::atomic<bool> enabled{false};
 Shadow shadow;
 CaptureControl control;
 ResourceRegistry resources;
private:
 CRITICAL_SECTION lock_{};bool lock_ok_=false;
 uint64_t device_=0,frame_=1,primitives_=0;
 std::array<uint64_t,97> counts_{};
 std::unique_ptr<FrameBuffer> capture_;
 uint32_t pending_draw_=UINT32_MAX;
 Known<uint32_t> last_cooperative_;
 Known<D3DPRESENT_PARAMETERS> reset_before_;
 void finish(uint32_t result,bool complete,const char* reason) noexcept;
 void start_capture() noexcept;
 void resource(uint32_t slot,const Args& args,uint32_t result);
};
}
