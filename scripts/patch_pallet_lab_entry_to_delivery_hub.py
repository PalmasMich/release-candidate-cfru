#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE=bytes.fromhex("39 04 03 FF 06 00 0C 00")
TARGET=bytes.fromhex("39 1B 00 FF 09 00 09 00")
EXPECTED_OCCURRENCES=2

def find_all(data:bytes,needle:bytes)->list[int]:
    out=[]; start=0
    while True:
        p=data.find(needle,start)
        if p<0: return out
        out.append(p); start=p+1

def patch_bytes(data:bytes)->tuple[bytes,list[int]]:
    positions=find_all(data,SOURCE)
    if len(positions)!=EXPECTED_OCCURRENCES:
        raise ValueError(f"expected {EXPECTED_OCCURRENCES} Oak Lab coordinate-warps, found {len(positions)}")
    out=bytearray(data)
    for p in positions: out[p:p+len(SOURCE)]=TARGET
    return bytes(out),positions

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if not a.source.is_file(): print("ERROR: source ROM missing"); return 1
    try: patched,positions=patch_bytes(a.source.read_bytes())
    except ValueError as e: print(f"RC_DELIVERY_HUB_ENTRY=BLOCKED: {e}"); return 2
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(patched)
    print("RC_DELIVERY_HUB_ENTRY=APPLIED")
    print("RC_DELIVERY_HUB_ENTRY_OFFSETS="+",".join(f"0x{x:X}" for x in positions))
    return 0
if __name__=="__main__": raise SystemExit(main())
