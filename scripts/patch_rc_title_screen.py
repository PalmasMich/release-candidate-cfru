#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROM_BASE = 0x08000000
PAL_LITERAL_OFFSET = 0x00078A94
TILES_LITERAL_OFFSET = 0x00078A98
MAP_LITERAL_OFFSET = 0x00078A9C
EXPECTED_PAL_PTR = 0x08EAB6C4
EXPECTED_TILES_PTR = 0x08EAB8C4
EXPECTED_MAP_PTR = 0x08EAD390
SCREEN_W = 256
SCREEN_H = 160
VISIBLE_W = 240
PALETTE_ENTRIES = 208
GUARD = 32

FONT = {
"A":("01110","10001","10001","11111","10001","10001","10001"),
"B":("11110","10001","10001","11110","10001","10001","11110"),
"C":("01111","10000","10000","10000","10000","10000","01111"),
"D":("11110","10001","10001","10001","10001","10001","11110"),
"E":("11111","10000","10000","11110","10000","10000","11111"),
"F":("11111","10000","10000","11110","10000","10000","10000"),
"G":("01111","10000","10000","10111","10001","10001","01111"),
"H":("10001","10001","10001","11111","10001","10001","10001"),
"I":("11111","00100","00100","00100","00100","00100","11111"),
"J":("00111","00010","00010","00010","10010","10010","01100"),
"K":("10001","10010","10100","11000","10100","10010","10001"),
"L":("10000","10000","10000","10000","10000","10000","11111"),
"M":("10001","11011","10101","10101","10001","10001","10001"),
"N":("10001","11001","10101","10011","10001","10001","10001"),
"O":("01110","10001","10001","10001","10001","10001","01110"),
"P":("11110","10001","10001","11110","10000","10000","10000"),
"Q":("01110","10001","10001","10001","10101","10010","01101"),
"R":("11110","10001","10001","11110","10100","10010","10001"),
"S":("01111","10000","10000","01110","00001","00001","11110"),
"T":("11111","00100","00100","00100","00100","00100","00100"),
"U":("10001","10001","10001","10001","10001","10001","01110"),
"V":("10001","10001","10001","10001","10001","01010","00100"),
"W":("10001","10001","10001","10101","10101","11011","10001"),
"X":("10001","10001","01010","00100","01010","10001","10001"),
"Y":("10001","10001","01010","00100","00100","00100","00100"),
"Z":("11111","00001","00010","00100","01000","10000","11111"),
"0":("01110","10001","10011","10101","11001","10001","01110"),
"1":("00100","01100","00100","00100","00100","00100","01110"),
"2":("01110","10001","00001","00010","00100","01000","11111"),
".":("00000","00000","00000","00000","00000","00110","00110"),
"-":("00000","00000","00000","11111","00000","00000","00000"),
" ":("00000","00000","00000","00000","00000","00000","00000"),
}

def align4(v:int)->int:
    return (v + 3) & ~3

def rgb555(r:int,g:int,b:int)->int:
    return (r//8) | ((g//8)<<5) | ((b//8)<<10)

def palette_bytes()->bytes:
    colors = [
        (4,14,28),       # 0 transparent/fallback dark navy
        (7,20,38),       # 1 navy background
        (235,225,197),   # 2 limestone
        (45,184,176),    # 3 teal
        (210,67,63),     # 4 release red
        (35,91,122),     # 5 sea
        (120,203,197),   # 6 light teal
        (24,44,61),      # 7 skyline
        (246,241,225),   # 8 highlight
    ]
    vals=[rgb555(*c) for c in colors]
    vals += [0] * (PALETTE_ENTRIES-len(vals))
    return b"".join(v.to_bytes(2,"little") for v in vals)

def set_px(img:list[bytearray],x:int,y:int,c:int)->None:
    if 0 <= x < SCREEN_W and 0 <= y < SCREEN_H:
        img[y][x]=c

def rect(img,x0,y0,x1,y1,c):
    for y in range(max(0,y0),min(SCREEN_H,y1)):
        img[y][max(0,x0):min(SCREEN_W,x1)] = bytes([c]) * max(0,min(SCREEN_W,x1)-max(0,x0))

def text_width(text:str,scale:int)->int:
    return sum((6*scale) for _ in text)-scale if text else 0

def draw_text(img,text:str,y:int,scale:int,color:int)->None:
    text=text.upper()
    x=max(0,(VISIBLE_W-text_width(text,scale))//2)
    for ch in text:
        glyph=FONT.get(ch,FONT[" "])
        for gy,row in enumerate(glyph):
            for gx,bit in enumerate(row):
                if bit=="1":
                    rect(img,x+gx*scale,y+gy*scale,x+(gx+1)*scale,y+(gy+1)*scale,color)
        x += 6*scale

def build_canvas()->list[bytearray]:
    img=[bytearray([1])*SCREEN_W for _ in range(SCREEN_H)]
    # understated project status stripe
    rect(img,0,0,VISIBLE_W,4,4)
    rect(img,0,4,VISIBLE_W,6,3)
    # title
    draw_text(img,"RELEASE",28,3,8)
    draw_text(img,"CANDIDATE",54,3,2)
    rect(img,40,82,200,84,3)
    draw_text(img,"CAGLIARI VERTICAL SLICE",91,1,6)
    draw_text(img,"PREVIEW 0.2",105,1,4)
    # Mediterranean horizon / stylized Cagliari skyline
    rect(img,0,122,VISIBLE_W,160,5)
    # limestone skyline blocks
    blocks=[(8,112,28,122),(31,106,50,122),(53,114,70,122),(74,101,96,122),
            (99,109,117,122),(121,104,143,122),(147,112,167,122),(171,99,197,122),(201,108,229,122)]
    for x0,y0,x1,y1 in blocks:
        rect(img,x0,y0,x1,y1,7)
    # tower / bastion accents
    rect(img,79,94,91,101,7)
    rect(img,177,91,191,99,7)
    # wave highlights
    for x in range(0,VISIBLE_W,24):
        rect(img,x+3,132,x+15,134,6)
        rect(img,x+10,144,x+22,146,3)
    return img

def tiles_and_map(img:list[bytearray])->tuple[bytes,bytes,int]:
    tiles=[]
    lookup={}
    entries=[]
    for ty in range(20):
        for tx in range(32):
            tile=bytes(
                img[ty*8+py][tx*8+px]
                for py in range(8)
                for px in range(8)
            )
            idx=lookup.get(tile)
            if idx is None:
                idx=len(tiles)
                if idx >= 256:
                    raise RuntimeError("custom title exceeds 256 8bpp tiles")
                lookup[tile]=idx
                tiles.append(tile)
            entries.append(idx)
    tile_data=b"".join(tiles)
    tilemap=b"".join(e.to_bytes(2,"little") for e in entries)
    return tile_data,tilemap,len(tiles)

def lz77_literal(data:bytes)->bytes:
    size=len(data)
    out=bytearray([0x10,size&0xFF,(size>>8)&0xFF,(size>>16)&0xFF])
    for i in range(0,size,8):
        out.append(0)
        out.extend(data[i:i+8])
    while len(out)%4:
        out.append(0)
    return bytes(out)

def build_assets()->tuple[bytes,bytes,bytes,int]:
    tiles,tilemap,count=tiles_and_map(build_canvas())
    return palette_bytes(),lz77_literal(tiles),lz77_literal(tilemap),count

def tail_start(data:bytes)->int:
    p=len(data)
    while p>0 and data[p-1]==0xFF:
        p-=1
    return align4(p)

def verify_original_literals(data:bytes)->None:
    expected=[
        (PAL_LITERAL_OFFSET,EXPECTED_PAL_PTR,"palette"),
        (TILES_LITERAL_OFFSET,EXPECTED_TILES_PTR,"tiles"),
        (MAP_LITERAL_OFFSET,EXPECTED_MAP_PTR,"map"),
    ]
    for off,want,label in expected:
        got=int.from_bytes(data[off:off+4],"little")
        if got!=want:
            raise RuntimeError(f"title {label} literal changed: expected 0x{want:08X}, got 0x{got:08X}")

def apply_title_screen(data:bytes)->tuple[bytes,dict]:
    verify_original_literals(data)
    pal,tiles,tilemap,tile_count=build_assets()
    start=tail_start(data)
    cursor=start
    placements={}
    payloads=[("palette",pal),("tiles",tiles),("map",tilemap)]
    needed=sum(align4(len(p)) for _,p in payloads)+GUARD
    if len(data)-start < needed:
        raise RuntimeError(f"not enough FF tail space for title screen: need {needed}, have {len(data)-start}")
    out=bytearray(data)
    for name,payload in payloads:
        cursor=align4(cursor)
        out[cursor:cursor+len(payload)]=payload
        placements[name]=(cursor,len(payload))
        cursor+=len(payload)
    ptrs={
        PAL_LITERAL_OFFSET:ROM_BASE+placements["palette"][0],
        TILES_LITERAL_OFFSET:ROM_BASE+placements["tiles"][0],
        MAP_LITERAL_OFFSET:ROM_BASE+placements["map"][0],
    }
    for off,ptr in ptrs.items():
        out[off:off+4]=ptr.to_bytes(4,"little")
    report={
        "tail_start":start,
        "allocation_end":cursor,
        "tile_count":tile_count,
        "palette_offset":placements["palette"][0],
        "tiles_offset":placements["tiles"][0],
        "map_offset":placements["map"][0],
        "palette_size":placements["palette"][1],
        "tiles_size":placements["tiles"][1],
        "map_size":placements["map"][1],
    }
    return bytes(out),report

def verify_patched(data:bytes)->dict:
    ptrs=[
        int.from_bytes(data[PAL_LITERAL_OFFSET:PAL_LITERAL_OFFSET+4],"little"),
        int.from_bytes(data[TILES_LITERAL_OFFSET:TILES_LITERAL_OFFSET+4],"little"),
        int.from_bytes(data[MAP_LITERAL_OFFSET:MAP_LITERAL_OFFSET+4],"little"),
    ]
    if ptrs==[EXPECTED_PAL_PTR,EXPECTED_TILES_PTR,EXPECTED_MAP_PTR]:
        raise RuntimeError("title screen is still using vanilla asset pointers")
    for p in ptrs:
        off=p-ROM_BASE
        if off<0 or off>=len(data):
            raise RuntimeError(f"title screen pointer out of ROM: 0x{p:08X}")
    return {"palette_ptr":ptrs[0],"tiles_ptr":ptrs[1],"map_ptr":ptrs[2]}

def main()->int:
    ap=argparse.ArgumentParser(description="Replace the FireRed title logo layer with the Release Candidate title screen.")
    ap.add_argument("source",type=Path)
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    try:
        patched,report=apply_title_screen(args.source.read_bytes())
        args.output.write_bytes(patched)
        verify_patched(patched)
    except (OSError,RuntimeError) as exc:
        print(f"RC_TITLE_SCREEN=BLOCKED:{exc}")
        return 2
    print("RC_TITLE_SCREEN=APPLIED")
    print(f"RC_TITLE_TILES={report['tile_count']}")
    print(f"RC_TITLE_ALLOC=0x{report['tail_start']:08X}-0x{report['allocation_end']:08X}")
    print(f"RC_TITLE_PALETTE_OFFSET=0x{report['palette_offset']:08X}")
    print(f"RC_TITLE_TILES_OFFSET=0x{report['tiles_offset']:08X}")
    print(f"RC_TITLE_MAP_OFFSET=0x{report['map_offset']:08X}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
