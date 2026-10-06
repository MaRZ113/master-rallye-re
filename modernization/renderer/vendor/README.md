# Pinned D3D8 declarations

The three files in `d3d8/` are unmodified Wine-derived mingw-w64 headers copied
from the installed MSYS2 UCRT64 include directory on 2026-10-05. SHA256 values
are recorded in [header-provenance.json](../data/header-provenance.json).
Their original copyright and LGPL-2.1-or-later notices are retained; the full
LGPL 2.1 text is in `licenses/LGPL-2.1.txt`. The installed mingw-w64 package's
general notices are also retained. No Wine renderer implementation is included.

[Upstream declarations](https://github.com/mingw-w64/mingw-w64/blob/master/mingw-w64-headers/include/d3d8.h)
define the 16/97-slot ABI. `include/sdk.hpp` supplies the small MSVC compatibility
definitions outside these unmodified headers. They are types/interfaces only;
there is no dependency on an MSYS2 DLL or a D3D8 import library.

The header's SDK constant is 220. The proxy always forwards the incoming SDK
argument. The pristine game uses 120; the header constant never replaces it.
