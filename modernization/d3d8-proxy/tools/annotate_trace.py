"""Annotate return PCs using the exact-build, read-only R-GFX1 callmap."""
import argparse
import json
from pathlib import Path
from trace_common import annotate, read_jsonl, guarded_output, DEFAULT_MAP

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('capture',type=Path)
    ap.add_argument('--callmap',type=Path,default=DEFAULT_MAP);ap.add_argument('--output',type=guarded_output)
    a=ap.parse_args();records=annotate(read_jsonl(a.capture),json.loads(a.callmap.read_text()))
    text=''.join(json.dumps(r,allow_nan=False)+'\n' for r in records)
    if a.output:a.output.write_text(text,encoding='utf-8')
    else:print(text,end='')

if __name__=='__main__':main()
