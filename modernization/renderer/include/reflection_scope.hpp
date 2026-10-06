#pragma once
#include "trace.hpp"
namespace gfx2 {
// Owns the native-only temporary setter, independent of tracing/capture success.
class ReflectionScope {
 IDirect3DDevice8& native_;Trace& trace_;VisualPolicy& policy_;uintptr_t pc_;uint32_t triangles_;
 DWORD original_=0;bool changed_=false;ReflectionOutcome outcome_;
public:
 ReflectionScope(IDirect3DDevice8& native,Trace& trace,VisualPolicy& policy,
                 const DrawClassification& draw,uintptr_t pc,uint32_t triangles) noexcept;
 ~ReflectionScope() noexcept;
 ReflectionScope(const ReflectionScope&)=delete;
};
}
