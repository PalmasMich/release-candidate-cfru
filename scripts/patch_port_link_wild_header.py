#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

GBA_ROM_BASE = 0x08000000
ROUTE1_GROUP = 3
ROUTE1_MAP = 19
PORT_LINK_GROUP = 3
PORT_LINK_MAP = 53
ROUTE1_ENCOUNTER_RATE = 21

ROUTE1_WILD_SIGNATURE = bytes.fromhex(
    "03 03 10 00 03 03 13 00 03 03 10 00 03 03 13 00 "
    "02 02 10 00 02 02 13 00 03 03 10 00 03 03 13 00 "
    "04 04 10 00 04 04 13 00 05 05 10 00 04 04 13 00"
)

PATCHED_SPECIES = (
    0x0511, 0x0511, 0x0511, 0x0511,
    0x0135, 0x0135, 0x0135,
    0x0034, 0x0034, 0x0034, 0x0034, 0x0034,
)

def build_patched_signature() -> bytes:
    out=bytearray(ROUTE1_WILD_SIGNATURE)
    for record,species in enumerate(PATCHED_SPECIES):
        pos=record*4+2
        out[pos:pos+2]=species.to_bytes(2,"little")
    return bytes(out)

ROUTE1_PATCHED_WILD_SIGNATURE = build_patched_signature()

def find_all(data: bytes, needle: bytes) -> list[int]:
    out=[]
    start=0
    while True:
        pos=data.find(needle,start)
        if pos<0:
            return out
        out.append(pos)
        start=pos+1

def gba_ptr(offset:int)->bytes:
    return (GBA_ROM_BASE+offset).to_bytes(4,"little")

def discover(data:bytes)->dict:
    mon_offsets=find_all(data,ROUTE1_PATCHED_WILD_SIGNATURE)
    signature_state="patched"
    if len(mon_offsets)==0:
        mon_offsets=find_all(data,ROUTE1_WILD_SIGNATURE)
        signature_state="vanilla"
    if len(mon_offsets)!=1:
        return {
            "safe":False,
            "reason":f"expected one Route 1 land-mon array, found {len(mon_offsets)}",
            "mon_offsets":mon_offsets,
            "signature_state":signature_state,
        }

    mon_offset=mon_offsets[0]
    mon_ptr=gba_ptr(mon_offset)

    info_candidates=[]
    for xref in find_all(data,mon_ptr):
        info_offset=xref-4
        if info_offset<0 or info_offset%4:
            continue
        if data[info_offset]!=ROUTE1_ENCOUNTER_RATE:
            continue
        # Compiler-emitted struct padding should be zero.
        if data[info_offset+1:info_offset+4] != b"\x00\x00\x00":
            continue
        info_candidates.append(info_offset)

    if len(info_candidates)!=1:
        return {
            "safe":False,
            "reason":f"expected one Route 1 WildPokemonInfo, found {len(info_candidates)}",
            "mon_offset":mon_offset,
            "info_candidates":info_candidates,
        }

    info_offset=info_candidates[0]
    info_ptr=gba_ptr(info_offset)
    header_candidates=[]

    for xref in find_all(data,info_ptr):
        header_offset=xref-4
        if header_offset<0 or header_offset%4:
            continue
        if data[header_offset] != ROUTE1_GROUP or data[header_offset+1] != ROUTE1_MAP:
            continue
        if data[header_offset+2:header_offset+4] != b"\x00\x00":
            continue
        # Route 1 has land encounters only in FireRed.
        if data[header_offset+8:header_offset+20] != b"\x00"*12:
            continue
        header_candidates.append(header_offset)

    if len(header_candidates)!=1:
        return {
            "safe":False,
            "reason":f"expected one Route 1 WildPokemonHeader, found {len(header_candidates)}",
            "mon_offset":mon_offset,
            "info_offset":info_offset,
            "header_candidates":header_candidates,
        }

    header_offset=header_candidates[0]
    return {
        "safe":True,
        "signature_state":signature_state,
        "mon_offset":mon_offset,
        "info_offset":info_offset,
        "header_offset":header_offset,
        "source_map":[ROUTE1_GROUP,ROUTE1_MAP],
        "target_map":[PORT_LINK_GROUP,PORT_LINK_MAP],
    }

def patch_bytes(data:bytes)->tuple[bytes,dict]:
    report=discover(data)
    if not report["safe"]:
        raise ValueError(report["reason"])

    out=bytearray(data)
    h=report["header_offset"]
    # Keep group 3, change only map number 19 -> 53.
    if out[h] != ROUTE1_GROUP or out[h+1] != ROUTE1_MAP:
        raise ValueError("Route 1 wild header changed after discovery")
    out[h]=PORT_LINK_GROUP
    out[h+1]=PORT_LINK_MAP
    return bytes(out),report

def main()->int:
    p=argparse.ArgumentParser(description="Repoint the patched Route 1 wild encounter header to RC Port Link.")
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()

    if not a.source.is_file():
        print(f"ERROR: source ROM missing: {a.source}")
        return 1
    try:
        patched,report=patch_bytes(a.source.read_bytes())
    except ValueError as exc:
        print(f"RC_PORT_LINK_WILD_HEADER=BLOCKED: {exc}")
        return 2

    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(patched)
    print("RC_PORT_LINK_WILD_HEADER=APPLIED")
    print(f"RC_PORT_LINK_WILD_HEADER_OFFSET=0x{report['header_offset']:X}")
    print(f"RC_PORT_LINK_WILD_INFO_OFFSET=0x{report['info_offset']:X}")
    print(f"RC_PORT_LINK_WILD_MONS_OFFSET=0x{report['mon_offset']:X}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
