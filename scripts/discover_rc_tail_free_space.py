#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

ALIGNMENT=4
FILL=0xFF
MIN_GUARD=32

def align_up(v:int,a:int=ALIGNMENT)->int:
    return (v+a-1)&~(a-1)

def discover_tail(data:bytes, required:int)->dict:
    end=len(data)
    start=end
    while start>0 and data[start-1]==FILL:
        start-=1
    aligned=align_up(start)
    available=end-aligned
    safe=required>=0 and available>=required+MIN_GUARD
    return {
      "rom_size":end,
      "raw_tail_start":start,
      "aligned_start":aligned,
      "available_bytes":available,
      "required_bytes":required,
      "guard_bytes":MIN_GUARD,
      "safe_to_allocate":safe,
      "allocation_end":aligned+required if safe else None
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("rom",type=Path); p.add_argument("required",type=int)
    p.add_argument("--json-out",type=Path)
    a=p.parse_args()
    if not a.rom.is_file():
        print(f"ERROR: ROM not found: {a.rom}"); return 1
    report=discover_tail(a.rom.read_bytes(),a.required)
    rendered=json.dumps(report,indent=2); print(rendered)
    if a.json_out:
        a.json_out.parent.mkdir(parents=True,exist_ok=True); a.json_out.write_text(rendered+"\n")
    print("RC_TAIL_FREE_SPACE="+("READY" if report["safe_to_allocate"] else "BLOCKED"))
    return 0 if report["safe_to_allocate"] else 2
if __name__=="__main__": raise SystemExit(main())
