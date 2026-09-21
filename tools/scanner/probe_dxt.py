#!/usr/bin/env python3
"""Validate the observed 20-byte Master Rallye .dxt header using inventory data."""
from __future__ import annotations
import argparse, json, struct
from collections import Counter
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("inventory",type=Path); ap.add_argument("--output",type=Path)
    args=ap.parse_args(); inv=json.loads(args.inventory.read_text(encoding="utf-8")); rows=[]
    for record in inv["files"]:
        if record["extension"] != ".dxt": continue
        head=bytes.fromhex(record["first_64_hex"])
        if len(head) < 20: continue
        magic,version,word2,width,height=struct.unpack_from("<5I",head)
        expected=20+width*height*4
        alpha=head[23::4] if len(head)>=24 else b""
        rows.append({"path":record["path"],"size":record["size"],"magic":f"0x{magic:08X}","version":version,
                     "word_0x08":f"0x{word2:08X}","width":width,"height":height,
                     "rgba32_size_match":record["size"]==expected,
                     "first_sample_alpha_values":sorted(set(alpha))})
    summary={"file_count":len(rows),"magic_counts":dict(Counter(r["magic"] for r in rows)),
             "version_counts":dict(Counter(str(r["version"]) for r in rows)),
             "dimension_counts":dict(Counter(f"{r['width']}x{r['height']}" for r in rows)),
             "rgba32_size_matches":sum(r["rgba32_size_match"] for r in rows),
             "nonmatching_files":[r for r in rows if not r["rgba32_size_match"]]}
    payload=json.dumps({"schema_version":1,"summary":summary,"representative_records":[r for r in rows if "Vehicles/Astero/" in r["path"]][:12]},indent=2)+"\n"
    if args.output: args.output.write_text(payload,encoding="utf-8")
    else: print(payload,end="")
if __name__=="__main__":main()
