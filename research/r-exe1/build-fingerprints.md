# R-EXE1 executable build fingerprints

All four corpus executables were read in place. No binary was copied or modified.

## Summary

| Build | Size | SHA-256 | PE | Image base | Entry point | Timestamp (UTC) | Hash gate |
|---|---:|---|---|---:|---:|---|---|
| 8.4.1 | 2,084,926 | `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` | PE32 i386 | `0x00400000` | `0x004D10F2` | 2001-09-11T18:45:24+00:00 | PASS |
| 9.3.1 | 2,637,886 | `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` | PE32 i386 | `0x00400000` | `0x0057A582` | 2001-10-09T15:32:38+00:00 | PASS |
| 9.10.0 | 2,883,646 | `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78` | PE32 i386 | `0x00400000` | `0x005A8D52` | 2001-10-23T15:51:08+00:00 | PASS |
| retail | 3,121,214 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | PE32 i386 | `0x00400000` | `0x005C4602` | 2001-11-26T16:10:05+00:00 | PASS |

## 8.4.1

- Source: `demo-8.4.1/MRallye.exe`
- Expected hash match: **True**
- Subsystem: Windows GUI; linker field: 6.0; file/section alignment: 4096/4096
- Toolchain clues: no recognizable dynamic MSVC CRT import; static/runtime model unresolved; Rich header records=0; debug directory entries=1; RTTI-like string candidates=21.
- DirectX-related imported DLLs: d3d8.dll, dsound.dll, dinput8.dll.
- Imported DLLs: kernel32.dll, user32.dll, winmm.dll, d3d8.dll, dsound.dll, dinput8.dll, ws2_32.dll, gdi32.dll, comdlg32.dll, ole32.dll, comctl32.dll
- Exports: 0; debug information present: True.

### Sections

| Name | RVA | Virtual size | Raw offset | Raw size | Flags |
|---|---:|---:|---:|---:|---|
| `.text` | `0x00001000` | 1,889,812 | `0x00001000` | 1,892,352 | CODE, EXECUTE, READ |
| `.rdata` | `0x001CF000` | 82,744 | `0x001CF000` | 86,016 | INITIALIZED_DATA, READ |
| `.data` | `0x001E4000` | 158,392 | `0x001E4000` | 86,016 | INITIALIZED_DATA, READ, WRITE |
| `.rsrc` | `0x0020B000` | 14,984 | `0x001F9000` | 16,384 | INITIALIZED_DATA, READ |

### Debug directory

- `{"format": "NB10", "pdb_path": "D:\\Projects\\MRallyeTNG\\Release\\MRallyeTNG.pdb", "size": 62, "timestamp": 1000233924, "type": 2, "version": "0.0"}`

## 9.3.1

- Source: `demo-9.3.1/MRallye.exe`
- Expected hash match: **True**
- Subsystem: Windows GUI; linker field: 6.0; file/section alignment: 4096/4096
- Toolchain clues: no recognizable dynamic MSVC CRT import; static/runtime model unresolved; Rich header records=0; debug directory entries=1; RTTI-like string candidates=167.
- DirectX-related imported DLLs: d3d8.dll, dinput8.dll, dsound.dll.
- Imported DLLs: kernel32.dll, winmm.dll, d3d8.dll, dinput8.dll, user32.dll, gdi32.dll, dsound.dll, ws2_32.dll, comdlg32.dll, ole32.dll, comctl32.dll
- Exports: 0; debug information present: True.

### Sections

| Name | RVA | Virtual size | Raw offset | Raw size | Flags |
|---|---:|---:|---:|---:|---|
| `.text` | `0x00001000` | 2,379,580 | `0x00001000` | 2,379,776 | CODE, EXECUTE, READ |
| `.rdata` | `0x00246000` | 108,272 | `0x00246000` | 110,592 | INITIALIZED_DATA, READ |
| `.data` | `0x00261000` | 200,392 | `0x00261000` | 126,976 | INITIALIZED_DATA, READ, WRITE |
| `.rsrc` | `0x00292000` | 15,032 | `0x00280000` | 16,384 | INITIALIZED_DATA, READ |

### Debug directory

- `{"format": "NB10", "pdb_path": "C:\\Projects\\MRallyeTNG\\Release\\MRallyeTNG.pdb", "size": 62, "timestamp": 1002641558, "type": 2, "version": "0.0"}`

## 9.10.0

- Source: `demo-9.10.0/MRallye.exe`
- Expected hash match: **True**
- Subsystem: Windows GUI; linker field: 6.0; file/section alignment: 4096/4096
- Toolchain clues: no recognizable dynamic MSVC CRT import; static/runtime model unresolved; Rich header records=0; debug directory entries=1; RTTI-like string candidates=187.
- DirectX-related imported DLLs: ddraw.dll, d3d8.dll, dinput8.dll, dsound.dll.
- Imported DLLs: kernel32.dll, ddraw.dll, winmm.dll, d3d8.dll, dinput8.dll, user32.dll, gdi32.dll, ole32.dll, oleaut32.dll, dsound.dll, ws2_32.dll, comdlg32.dll, comctl32.dll
- Exports: 0; debug information present: True.

### Sections

| Name | RVA | Virtual size | Raw offset | Raw size | Flags |
|---|---:|---:|---:|---:|---|
| `.text` | `0x00001000` | 2,585,868 | `0x00001000` | 2,588,672 | CODE, EXECUTE, READ |
| `.rdata` | `0x00279000` | 119,030 | `0x00279000` | 122,880 | INITIALIZED_DATA, READ |
| `.data` | `0x00297000` | 241,992 | `0x00297000` | 151,552 | INITIALIZED_DATA, READ, WRITE |
| `.rsrc` | `0x002D3000` | 15,032 | `0x002BC000` | 16,384 | INITIALIZED_DATA, READ |

### Debug directory

- `{"format": "NB10", "pdb_path": "D:\\Projects\\MRallyeTNG\\Release\\MRallyeTNG.pdb", "size": 62, "timestamp": 1003852268, "type": 2, "version": "0.0"}`

## retail

- Source: `retail/MRallye.exe`
- Expected hash match: **True**
- Subsystem: Windows GUI; linker field: 6.0; file/section alignment: 4096/4096
- Toolchain clues: no recognizable dynamic MSVC CRT import; static/runtime model unresolved; Rich header records=0; debug directory entries=1; RTTI-like string candidates=463.
- DirectX-related imported DLLs: ddraw.dll, d3d8.dll, dsound.dll, dinput8.dll.
- Imported DLLs: kernel32.dll, ddraw.dll, winmm.dll, d3d8.dll, dsound.dll, dinput8.dll, user32.dll, gdi32.dll, advapi32.dll, ole32.dll, oleaut32.dll, ws2_32.dll, comdlg32.dll, comctl32.dll
- Exports: 0; debug information present: True.

### Sections

| Name | RVA | Virtual size | Raw offset | Raw size | Flags |
|---|---:|---:|---:|---:|---|
| `.text` | `0x00001000` | 2,675,348 | `0x00001000` | 2,678,784 | CODE, EXECUTE, READ |
| `.rdata` | `0x0028F000` | 123,954 | `0x0028F000` | 126,976 | INITIALIZED_DATA, READ |
| `.data` | `0x002AE000` | 386,568 | `0x002AE000` | 294,912 | INITIALIZED_DATA, READ, WRITE |
| `.rsrc` | `0x0030D000` | 15,032 | `0x002F6000` | 16,384 | INITIALIZED_DATA, READ |

### Debug directory

- `{"format": "NB10", "pdb_path": "D:\\Projects\\MRallyeTNG\\Release\\MRallyeTNG.pdb", "size": 62, "timestamp": 1006791005, "type": 2, "version": "0.0"}`

## Cross-build interpretation

PE timestamps, linker version fields, import sets, section geometry, debug records, Rich headers, and RTTI markers are fingerprints, not stand-alone proof of a compiler release. DirectX generation is reported only from imports and executable evidence; missing imports do not establish absence of dynamically loaded APIs.
