#pragma once

namespace rmod2_boot {
// Called only from a forwarded DirectInput export, outside DllMain/loader lock.
// The caller provides process-wide once-only serialization.
bool initialize(char* error, unsigned error_capacity);
}
