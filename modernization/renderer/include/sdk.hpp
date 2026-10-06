#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#ifndef __MSABI_LONG
#define __MSABI_LONG(x) x##L
#endif
typedef BOOL WINBOOL;
#if defined(_M_IX86) && !defined(__i386__)
#define __i386__ 1
#endif
#include <d3d8.h>
static_assert(sizeof(void*) == 4, "This proxy requires x86");
static_assert(sizeof(D3DMATRIX) == 64, "D3D8 matrix ABI");
static_assert(sizeof(D3DPRESENT_PARAMETERS) == 52, "D3D8 presentation ABI");
static_assert(sizeof(D3DVIEWPORT8) == 24, "D3D8 viewport ABI");
