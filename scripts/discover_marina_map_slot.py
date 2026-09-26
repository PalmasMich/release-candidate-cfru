#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

GBA_ROM_BASE=0x08000000
MAP_HEADER_SIZE=0x1C
MUSIC_SEVII_ROUTE=333
MAPSEC_SEVII_ISLE_8=157
WEATHER_SUNNY=2
MAP_TYPE_ROUTE=3
HEADER_FLAGS=0x06

def is_ptr(v:int,size:int,alignment:int=1)->bool:
    return GBA_ROM_BASE<=v<GBA_ROM_BASE+size and (v-GBA_ROM_BASE)%alignment==0

def ptr_off(v:int,size:int)->int:
    if not is_ptr(v,size): raise ValueError("invalid ROM pointer")
    return v-GBA_ROM_BASE

def parse_header(data:bytes,o:int)->dict:
    if o<0 or o+0x1C>len(data): raise ValueError("header out of bounds")
    u32=lambda p:int.from_bytes(data[o+p:o+p+4],"little")
    u16=lambda p:int.from_bytes(data[o+p:o+p+2],"little")
    return {
      "offset":o,"layout_ptr":u32(0),"events_ptr":u32(4),"scripts_ptr":u32(8),"connections_ptr":u32(12),
      "music":u16(16),"layout_id":u16(18),"mapsec":data[o+20],"cave":data[o+21],
      "weather":data[o+22],"map_type":data[o+23],"biking":data[o+24],"flags":data[o+25],
      "floor":int.from_bytes(data[o+26:o+27],"little",signed=True),"battle":data[o+27]
    }

def parse_layout(data:bytes,p:int)->dict:
    o=ptr_off(p,len(data))
    if o+0x1C>len(data): raise ValueError("layout out of bounds")
    u32=lambda q:int.from_bytes(data[o+q:o+q+4],"little")
    return {
      "offset":o,"width":int.from_bytes(data[o:o+4],"little",signed=True),
      "height":int.from_bytes(data[o+4:o+8],"little",signed=True),
      "border_ptr":u32(8),"map_ptr":u32(12),"primary_tileset_ptr":u32(16),"secondary_tileset_ptr":u32(20),
      "border_width":data[o+24],"border_height":data[o+25]
    }

def matches(h:dict,size:int)->bool:
    return all([
      is_ptr(h["layout_ptr"],size,4),is_ptr(h["events_ptr"],size,4),is_ptr(h["scripts_ptr"],size),
      h["connections_ptr"]==0,h["music"]==MUSIC_SEVII_ROUTE,h["mapsec"]==MAPSEC_SEVII_ISLE_8,
      h["cave"]==0,h["weather"]==WEATHER_SUNNY,h["map_type"]==MAP_TYPE_ROUTE,
      h["biking"]==1,h["flags"]==HEADER_FLAGS,h["floor"]==0,h["battle"]==0
    ])

def discover(data:bytes)->list[dict]:
    fixed=bytes([MAPSEC_SEVII_ISLE_8,0,WEATHER_SUNNY,MAP_TYPE_ROUTE,1,HEADER_FLAGS,0,0])
    out=[]; start=0
    while True:
      p=data.find(fixed,start)
      if p<0: break
      start=p+1
      o=p-0x14
      if o<0 or o%4: continue
      if int.from_bytes(data[o+0x10:o+0x12],"little")!=MUSIC_SEVII_ROUTE: continue
      try: h=parse_header(data,o)
      except ValueError: continue
      if not matches(h,len(data)): continue
      try: l=parse_layout(data,h["layout_ptr"])
      except ValueError: continue
      if not (l["width"]==84 and l["height"]==20 and l["border_width"]==2 and l["border_height"]==2): continue
      if not all(is_ptr(l[k],len(data),2 if k in ("border_ptr","map_ptr") else 4) for k in ("border_ptr","map_ptr","primary_tileset_ptr","secondary_tileset_ptr")): continue
      h["layout"]=l; out.append(h)
    return out

def analyze_rom(data:bytes)->dict:
    c=discover(data)
    return {"slot":"MAP_PROTOTYPE_SEVII_ISLE_8","map_group":3,"map_num":52,"candidate_count":len(c),"candidates":c,"safe_to_repoint":len(c)==1}

def main():
    p=argparse.ArgumentParser();p.add_argument("rom",type=Path);a=p.parse_args()
    if not a.rom.is_file(): print("ERROR: ROM not found"); return 1
    r=analyze_rom(a.rom.read_bytes()); print(json.dumps(r,indent=2))
    if r["candidate_count"]==0: print("RC_MARINA_SLOT=NOT_FOUND"); return 2
    if not r["safe_to_repoint"]: print("RC_MARINA_SLOT=AMBIGUOUS"); return 3
    print(f"RC_MARINA_SLOT=READY:0x{r['candidates'][0]['offset']:X}"); return 0
if __name__=="__main__": raise SystemExit(main())
