#pragma once
#include <cmath>
#include <cstdint>
#include <limits>

namespace gfx2 {
enum class FlightClockSource : uint8_t { unavailable, qpc, tick_count64 };

struct FlightClockStats {
 uint64_t samples=0,zero_samples=0,clamped_samples=0,invalid_samples=0;
 double last_seconds=0,min_seconds=0,max_seconds=0,mean_seconds=0;
};

// Pure elapsed-time policy. Win32 queries live in FlightWindowInput; keeping
// the arithmetic here injectable makes clock failures and focus boundaries
// deterministic in the native contract tests.
class FlightClock {
 FlightClockSource source_=FlightClockSource::unavailable;
 int64_t frequency_=0,previous_qpc_=0;
 uint64_t previous_tick_=0;
 bool baseline_=false;
 FlightClockStats stats_{};

 static void increment(uint64_t& value) noexcept {
  if(value!=std::numeric_limits<uint64_t>::max())++value;
 }
 double accept(double seconds) noexcept {
  if(!std::isfinite(seconds)||seconds<0){increment(stats_.invalid_samples);return 0;}
  increment(stats_.samples);
  stats_.last_seconds=seconds;
  if(stats_.samples==1)stats_.min_seconds=stats_.max_seconds=stats_.mean_seconds=seconds;
  else {
   if(seconds<stats_.min_seconds)stats_.min_seconds=seconds;
   if(seconds>stats_.max_seconds)stats_.max_seconds=seconds;
   stats_.mean_seconds+=(seconds-stats_.mean_seconds)/static_cast<double>(stats_.samples);
  }
  if(seconds==0)increment(stats_.zero_samples);
  if(seconds>.05)increment(stats_.clamped_samples);
  return seconds;
 }
public:
 void initialize_qpc(bool query_succeeded,int64_t frequency) noexcept {
  source_=query_succeeded&&frequency>0?FlightClockSource::qpc:FlightClockSource::tick_count64;
  frequency_=source_==FlightClockSource::qpc?frequency:1000;
  baseline_=false;previous_qpc_=0;previous_tick_=0;stats_={};
  if(source_!=FlightClockSource::qpc)increment(stats_.invalid_samples);
 }
 void initialize_tick_count64() noexcept {
  source_=FlightClockSource::tick_count64;frequency_=1000;baseline_=false;
  previous_qpc_=0;previous_tick_=0;stats_={};
 }
 void reset_baseline() noexcept {baseline_=false;previous_qpc_=0;previous_tick_=0;}
 FlightClockSource source() const noexcept {return source_;}
 int64_t frequency() const noexcept {return frequency_;}
 const FlightClockStats& stats() const noexcept {return stats_;}

 double sample_qpc(bool query_succeeded,int64_t counter) noexcept {
  if(source_!=FlightClockSource::qpc){increment(stats_.invalid_samples);return 0;}
  if(!query_succeeded){increment(stats_.invalid_samples);source_=FlightClockSource::tick_count64;frequency_=1000;baseline_=false;return 0;}
  if(counter<0){increment(stats_.invalid_samples);baseline_=false;return 0;}
  if(!baseline_){previous_qpc_=counter;baseline_=true;return 0;}
  if(counter<previous_qpc_){increment(stats_.invalid_samples);previous_qpc_=counter;return 0;}
  const uint64_t delta=static_cast<uint64_t>(counter)-static_cast<uint64_t>(previous_qpc_);
  previous_qpc_=counter;
  return accept(static_cast<double>(delta)/static_cast<double>(frequency_));
 }
 // Called only after a failed QPC sample. The current fallback timestamp is a
 // new baseline; no elapsed interval is ever computed across clock domains.
 void establish_tick_count64_baseline(uint64_t tick_ms) noexcept {
  if(source_!=FlightClockSource::tick_count64)return;
  previous_tick_=tick_ms;baseline_=true;
 }
 double sample_tick_count64(uint64_t tick_ms) noexcept {
  if(source_!=FlightClockSource::tick_count64){increment(stats_.invalid_samples);return 0;}
  if(!baseline_){previous_tick_=tick_ms;baseline_=true;return 0;}
  if(tick_ms<previous_tick_){increment(stats_.invalid_samples);previous_tick_=tick_ms;return 0;}
  const uint64_t delta=tick_ms-previous_tick_;previous_tick_=tick_ms;
  return accept(static_cast<double>(delta)/1000.0);
 }
};
}
