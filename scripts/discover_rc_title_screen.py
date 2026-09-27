#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
from pathlib import Path

ROM_BASE = 0x08000000

TITLE_MAP_RAW = base64.b64decode(
    "AAABAAIAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAQABEAEgATABQAFQAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAACAAIQAiACMAJAAlACYAJwAoACkAKgArACwA"
    "LQAuAC8AMAAxADIAMwA0ADUAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEEAQgBD"
    "AEQARQBGAEcASABJAEoASwBMAE0ATgBPAFAAUQBSAFMAVABVAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAYABhAGIAYwBkAGUAZgBnAGgAaQBqAGsAbABtAG4AbwBw"
    "AHEAcgBzAHQAdQAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAgQCCAIMAhACFAIYA"
    "hwCIAIkAigCLAIwAjQCOAI8AkACRAJIAkwCUAJUAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAACgAKEAogCjAKQApQCmAKcAqACpAKoAqwCsAK0ArgCvALAAsQCyALMA"
    "tAC1AAAAAAAAAAAAAAAAAAAAAAAAAAAAwADBAMIAwwDEAMUAxgDHAMgAyQDK"
    "AMsAzADNAM4AzwDQANEA0gDTANQA1QAAAAAAAAAAAAAAAAAAAAAAAAAAAOAA"
    "4QDiAOMA5ADlABYAFwAYABkAGgAbABwAHQAeAB8A8ADxAPIA8wD0APUAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ADcAOAA5ADoAOwA8AD0A"
    "PgA/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAVgBXAFgAWQBaAFsAXABdAF4AXwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAHYAdwB4AHkAegB7AHwAfQB+AH8AAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACWAJcA"
    "mACZAJoAmwCcAJ0AngCfAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAA="
)

def gba_lz77_decompress(data: bytes, offset: int) -> bytes | None:
    if offset + 4 > len(data) or data[offset] != 0x10:
        return None
    size = data[offset+1] | (data[offset+2] << 8) | (data[offset+3] << 16)
    if size <= 0 or size > 0x20000:
        return None
    src = offset + 4
    out = bytearray()
    try:
        while len(out) < size:
            flags = data[src]
            src += 1
            for bit in range(8):
                if len(out) >= size:
                    break
                if flags & (0x80 >> bit):
                    a = data[src]
                    b = data[src+1]
                    src += 2
                    length = (a >> 4) + 3
                    disp = ((a & 0xF) << 8) | b
                    disp += 1
                    if disp > len(out):
                        return None
                    for _ in range(length):
                        out.append(out[-disp])
                        if len(out) >= size:
                            break
                else:
                    out.append(data[src])
                    src += 1
    except IndexError:
        return None
    return bytes(out)

def find_title_map(data: bytes) -> list[int]:
    hits = []
    for i, b in enumerate(data):
        if b != 0x10:
            continue
        dec = gba_lz77_decompress(data, i)
        if dec == TITLE_MAP_RAW:
            hits.append(i)
    return hits

def ptr_refs(data: bytes, rom_offset: int) -> list[int]:
    ptr = (ROM_BASE + rom_offset).to_bytes(4, "little")
    out = []
    start = 0
    while True:
        p = data.find(ptr, start)
        if p < 0:
            return out
        out.append(p)
        start = p + 1

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    args = ap.parse_args()
    data = args.rom.read_bytes()
    hits = find_title_map(data)
    print(f"RC_TITLE_MAP_HITS={len(hits)}")
    if len(hits) != 1:
        candidates = []
        for i, b in enumerate(data):
            if b != 0x10:
                continue
            dec = gba_lz77_decompress(data, i)
            if dec is not None and len(dec) == 1280:
                refs = ptr_refs(data, i)
                similarity = sum(a == b for a,b in zip(dec, TITLE_MAP_RAW))
                candidates.append((similarity, i, dec[:32].hex(), len(refs)))
        candidates.sort(reverse=True)
        print(f"RC_TITLE_1280_CANDIDATES={len(candidates)}")
        for idx,(similarity,off,prefix,refs_count) in enumerate(candidates[:12]):
            print(f"RC_TITLE_1280_{idx}=0x{off:08X}:similar={similarity}:refs={refs_count}:prefix={prefix}")
        if candidates and candidates[0][0] >= 1200 and (len(candidates) == 1 or candidates[0][0] > candidates[1][0]):
            hits = [candidates[0][1]]
            print(f"RC_TITLE_MAP_FUZZY_MATCH=0x{hits[0]:08X}:similar={candidates[0][0]}")
        else:
            return 2
    off = hits[0]
    refs = ptr_refs(data, off)
    print(f"RC_TITLE_MAP_OFFSET=0x{off:08X}")
    print(f"RC_TITLE_MAP_ADDRESS=0x{ROM_BASE+off:08X}")
    print(f"RC_TITLE_MAP_PTR_REFS={len(refs)}")
    for idx, ref in enumerate(refs):
        print(f"RC_TITLE_MAP_PTR_{idx}=0x{ref:08X}")
        lo = max(0, ref - 0x80)
        hi = min(len(data)-3, ref + 0x80)
        vals = []
        for p in range(lo & ~3, hi, 4):
            v = int.from_bytes(data[p:p+4], "little")
            if 0x08000000 <= v <= 0x09FFFFFF:
                vals.append((p, v))
        for j,(p,v) in enumerate(vals[:32]):
            print(f"RC_TITLE_NEAR_PTR_{idx}_{j}=0x{p:08X}->0x{v:08X}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
