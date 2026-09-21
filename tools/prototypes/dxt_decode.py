#!/usr/bin/env python3
"""Decode the observed 20-byte, uncompressed Master Rallye .dxt texture."""
from __future__ import annotations
import argparse, struct, zlib
from pathlib import Path
MAGIC=0x0000FEED

def parse_dxt(path):
    data=path.read_bytes()
    if len(data)<20:raise ValueError('file too short')
    magic,word04,word08,width,height=struct.unpack_from('<5I',data)
    if magic!=MAGIC:raise ValueError(f'bad magic 0x{magic:08X}')
    expected=20+width*height*4
    if len(data)!=expected:raise ValueError(f'size mismatch: expected {expected}, got {len(data)}')
    return {"magic":magic,"word_0x04":word04,"word_0x08":word08,"width":width,"height":height},data[20:]

def png_chunk(kind,payload):
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)

def write_png(path,width,height,pixels,order):
    rows=[]
    for y in range(height):
        row=bytearray([0]); src=pixels[y*width*4:(y+1)*width*4]
        for i in range(0,len(src),4):
            c0,c1,c2,a=src[i:i+4]
            row.extend((c2,c1,c0,a) if order=='bgra' else (c0,c1,c2,a))
        rows.append(bytes(row))
    ihdr=struct.pack('>IIBBBBB',width,height,8,6,0,0,0)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',ihdr)+png_chunk(b'IDAT',zlib.compress(b''.join(rows),9))+png_chunk(b'IEND',b''))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--order',choices=('bgra','rgba'),default='bgra')
    args=ap.parse_args();header,pixels=parse_dxt(args.input);write_png(args.output,header['width'],header['height'],pixels,args.order)
    print(f"decoded {header['width']}x{header['height']} {args.order} -> {args.output}")
if __name__=='__main__':main()
