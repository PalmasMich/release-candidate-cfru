#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
CELL_COMPILER=ROOT/"scripts"/"compile_rc_map_cells.py"
EVENTS_COMPILER=ROOT/"scripts"/"compile_rc_map_events.py"
SCRIPT_COMPILER=ROOT/"scripts"/"compile_rc_event_scripts.py"
DIALOGUE_COMPILER=ROOT/"scripts"/"compile_rc_dialogue.py"

GBA_ROM_BASE=0x08000000

def load_module(path:Path,name:str):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def align(value:int,alignment:int=4)->int:
    return (value+alignment-1)&~(alignment-1)

def put_aligned(blob:bytearray,data:bytes,alignment:int=4)->int:
    offset=align(len(blob),alignment)
    if offset>len(blob): blob.extend(b"\xFF"*(offset-len(blob)))
    blob.extend(data)
    return offset

def ptr(base_address:int,offset:int)->int:
    return base_address+offset

def patch_u32(data:bytearray,offset:int,value:int)->None:
    data[offset:offset+4]=int(value).to_bytes(4,"little")

def build_map_layout(
    *,
    width:int,
    height:int,
    border_address:int,
    map_address:int,
    primary_tileset_ptr:int,
    secondary_tileset_ptr:int,
    border_width:int=2,
    border_height:int=2,
)->bytes:
    b=bytearray()
    b.extend(int(width).to_bytes(4,"little",signed=True))
    b.extend(int(height).to_bytes(4,"little",signed=True))
    b.extend(int(border_address).to_bytes(4,"little"))
    b.extend(int(map_address).to_bytes(4,"little"))
    b.extend(int(primary_tileset_ptr).to_bytes(4,"little"))
    b.extend(int(secondary_tileset_ptr).to_bytes(4,"little"))
    b.extend(bytes([border_width,border_height,0,0]))
    if len(b)!=0x1C: raise AssertionError("MapLayout must be 0x1C bytes")
    return bytes(b)

def compile_payload(
    *,
    map_spec_path:Path,
    base_address:int,
    primary_tileset_ptr:int,
    secondary_tileset_ptr:int,
    script_spec_path:Path|None=None,
)->dict:
    map_comp=load_module(MAP_COMPILER,"rc_map_compiler")
    cell_comp=load_module(CELL_COMPILER,"rc_cell_compiler")
    events_comp=load_module(EVENTS_COMPILER,"rc_events_compiler")

    map_ir=map_comp.compile_file(map_spec_path)
    cells_ir=cell_comp.compile_file(map_spec_path)
    events_ir=events_comp.compile_file(map_spec_path)
    map_ids=events_comp.load_map_ids()

    scripts_ir=None
    dialogue_ir=None
    if script_spec_path is not None:
        script_comp=load_module(SCRIPT_COMPILER,"rc_script_compiler")
        dialogue_comp=load_module(DIALOGUE_COMPILER,"rc_dialogue_compiler")
        scripts_ir=script_comp.compile_file(script_spec_path)
        dialogue_ir=dialogue_comp.compile_file()

    blob=bytearray()
    offsets={}

    offsets["border"]=put_aligned(blob,bytes.fromhex(cells_ir["border_hex"]),2)
    offsets["map_cells"]=put_aligned(blob,bytes.fromhex(cells_ir["map_hex"]),2)

    dialogue_addresses={}
    if scripts_ir is not None:
        dialogue_by_id={x["id"]:x for x in dialogue_ir["scenes"]}
        referenced=sorted({
            rel["symbol"]
            for script in scripts_ir["scripts"]
            for rel in script["relocations"]
            if rel["kind"]=="dialogue"
        })
        for symbol in referenced:
            if symbol not in dialogue_by_id:
                raise ValueError(f"missing compiled dialogue {symbol}")
            off=put_aligned(blob,bytes.fromhex(dialogue_by_id[symbol]["bytes_hex"]),1)
            offsets[f"dialogue:{symbol}"]=off
            dialogue_addresses[symbol]=ptr(base_address,off)

    script_addresses={}
    if scripts_ir is not None:
        script_comp=load_module(SCRIPT_COMPILER,"rc_script_linker")
        # Reserve linked script regions first so internal and cross-structure
        # pointers can use final addresses.
        for script in scripts_ir["scripts"]:
            size=script["size"]
            off=align(len(blob),4)
            if off>len(blob): blob.extend(b"\xFF"*(off-len(blob)))
            offsets[f"script:{script['id']}"]=off
            script_addresses[script["id"]]=ptr(base_address,off)
            blob.extend(b"\x00"*size)
        for script in scripts_ir["scripts"]:
            linked=script_comp.link_script(
                script,
                script_addresses[script["id"]],
                dialogue_addresses,
                map_ids,
            )
            off=offsets[f"script:{script['id']}"]
            blob[off:off+len(linked)]=linked

    def link_script_ptrs(block:dict,raw:bytes)->bytes:
        data=bytearray(raw)
        for rel in block.get("relocations",[]):
            if rel["kind"]!="script_pointer": continue
            symbol=rel["symbol"]
            if symbol not in script_addresses:
                raise ValueError(f"missing compiled script for map event: {symbol}")
            patch_u32(data,rel["offset"],script_addresses[symbol])
        return bytes(data)

    object_raw=link_script_ptrs(
        events_ir["object_events"],
        bytes.fromhex(events_ir["object_events"]["bytes_hex"]),
    )
    warp_raw=events_comp.link_map_id_relocations(events_ir["warp_events"],map_ids)
    coord_raw=link_script_ptrs(
        events_ir["coord_events"],
        bytes.fromhex(events_ir["coord_events"]["bytes_hex"]),
    )
    bg_raw=link_script_ptrs(
        events_ir["bg_events"],
        bytes.fromhex(events_ir["bg_events"]["bytes_hex"]),
    )

    block_addresses={}
    for name,block,raw,alignment in (
        ("object_events",events_ir["object_events"],object_raw,4),
        ("warp_events",events_ir["warp_events"],warp_raw,2),
        ("coord_events",events_ir["coord_events"],coord_raw,4),
        ("bg_events",events_ir["bg_events"],bg_raw,4),
    ):
        if block["count"]==0:
            block_addresses[name]=0
            continue
        off=put_aligned(blob,raw,alignment)
        offsets[name]=off
        block_addresses[name]=ptr(base_address,off)

    header=bytearray.fromhex(events_ir["map_events_header"]["bytes_hex"])
    for rel in events_ir["map_events_header"]["relocations"]:
        symbol=rel["symbol"]
        patch_u32(header,rel["offset"],block_addresses[symbol])
    offsets["map_events"]=put_aligned(blob,bytes(header),4)
    map_events_address=ptr(base_address,offsets["map_events"])

    # MapLayout is written after all pointed-to data so its pointers are final.
    layout=build_map_layout(
        width=map_ir["dimensions"]["width"],
        height=map_ir["dimensions"]["height"],
        border_address=ptr(base_address,offsets["border"]),
        map_address=ptr(base_address,offsets["map_cells"]),
        primary_tileset_ptr=primary_tileset_ptr,
        secondary_tileset_ptr=secondary_tileset_ptr,
        border_width=2,
        border_height=2,
    )
    offsets["map_layout"]=put_aligned(blob,layout,4)
    map_layout_address=ptr(base_address,offsets["map_layout"])

    return {
        "format":"RC_MAP_PAYLOAD_V1",
        "map":map_ir["id"],
        "base_address":base_address,
        "size":len(blob),
        "bytes":bytes(blob),
        "offsets":offsets,
        "map_layout_address":map_layout_address,
        "map_events_address":map_events_address,
        "script_addresses":script_addresses,
        "dialogue_addresses":dialogue_addresses,
        "map_cell_profile":cells_ir["profile"],
    }
