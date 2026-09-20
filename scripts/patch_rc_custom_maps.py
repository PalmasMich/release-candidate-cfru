#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GBA_ROM_BASE=0x08000000

HUB_DISCOVERY=ROOT/"scripts"/"discover_delivery_hub_map_slot.py"
MARINA_DISCOVERY=ROOT/"scripts"/"discover_marina_map_slot.py"
PORT_LINK_DISCOVERY=ROOT/"scripts"/"discover_port_link_map_slot.py"
CASTELLO_DISCOVERY=ROOT/"scripts"/"discover_castello_map_slot.py"
DEPLOY_DISTRICT_DISCOVERY=ROOT/"scripts"/"discover_deploy_district_map_slot.py"
DEPLOY_ROOM_DISCOVERY=ROOT/"scripts"/"discover_deploy_room_map_slot.py"
FREE_DISCOVERY=ROOT/"scripts"/"discover_rc_tail_free_space.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"
ENTRY_PATCHER=ROOT/"scripts"/"patch_pallet_lab_entry_to_delivery_hub.py"
WILD_HEADER_PATCHER=ROOT/"scripts"/"patch_port_link_wild_header.py"

HUB_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DELIVERY_HUB.json"
HUB_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DELIVERY_HUB.json"
MARINA_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CAGLIARI_MARINA.json"
MARINA_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CAGLIARI_MARINA.json"
PORT_LINK_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_PORT_CONNECTION.json"
PORT_LINK_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_PORT_CONNECTION.json"
CASTELLO_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CASTELLO_ASCENT.json"
CASTELLO_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CASTELLO_ASCENT.json"
DEPLOY_DISTRICT_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DEPLOY_DISTRICT.json"
DEPLOY_DISTRICT_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DEPLOY_DISTRICT.json"
DEPLOY_ROOM_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DEPLOY_ROOM.json"
DEPLOY_ROOM_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DEPLOY_ROOM.json"

def load(path:Path,name:str):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def align(v:int,a:int=4)->int:
    return (v+a-1)&~(a-1)

def verify_header_unchanged(data:bytes,header:dict)->None:
    o=header["offset"]
    current={
      "layout_ptr":int.from_bytes(data[o:o+4],"little"),
      "events_ptr":int.from_bytes(data[o+4:o+8],"little"),
      "scripts_ptr":int.from_bytes(data[o+8:o+12],"little"),
      "connections_ptr":int.from_bytes(data[o+12:o+16],"little"),
      "music":int.from_bytes(data[o+16:o+18],"little"),
      "layout_id":int.from_bytes(data[o+18:o+20],"little"),
      "mapsec":data[o+20],
      "cave":data[o+21],
      "weather":data[o+22],
      "map_type":data[o+23],
      "biking":data[o+24],
      "flags":data[o+25],
      "floor":int.from_bytes(data[o+26:o+27],"little",signed=True),
      "battle":data[o+27],
    }
    expected={
      **header,
      "biking":header.get("biking",header.get("biking_allowed")),
      "floor":header.get("floor",header.get("floor_num")),
      "battle":header.get("battle",header.get("battle_type")),
    }
    for key in current:
        if current[key]!=expected[key]:
            raise ValueError(
                f"map header changed after discovery at 0x{o:X}: "
                f"{key} expected 0x{expected[key]:08X}, got 0x{current[key]:08X}"
            )

def repoint_header(
    data:bytearray,
    header:dict,
    *,
    layout_ptr:int,
    events_ptr:int,
    clear_connections:bool=False,
    suppress_map_name:bool=False,
)->None:
    verify_header_unchanged(bytes(data),header)
    o=header["offset"]
    data[o:o+4]=int(layout_ptr).to_bytes(4,"little")
    data[o+4:o+8]=int(events_ptr).to_bytes(4,"little")
    if clear_connections:
        data[o+12:o+16]=b"\x00\x00\x00\x00"
    if suppress_map_name:
        # Preserve escape/run bits while clearing the map-name popup field.
        data[o+25]=header["flags"] & 0x03

def build_payloads(data:bytes)->dict:
    hub_discovery=load(HUB_DISCOVERY,"hub_slot")
    marina_discovery=load(MARINA_DISCOVERY,"marina_slot")
    port_discovery=load(PORT_LINK_DISCOVERY,"port_link_slot")
    castello_discovery=load(CASTELLO_DISCOVERY,"castello_slot")
    deploy_discovery=load(DEPLOY_DISTRICT_DISCOVERY,"deploy_district_slot")
    room_discovery=load(DEPLOY_ROOM_DISCOVERY,"deploy_room_slot")
    free=load(FREE_DISCOVERY,"tail_free")
    payload_comp=load(PAYLOAD_COMPILER,"payload_compiler")

    hub_report=hub_discovery.analyze_rom(data)
    marina_report=marina_discovery.analyze_rom(data)
    port_report=port_discovery.analyze_rom(data)
    castello_report=castello_discovery.analyze_rom(data)
    deploy_report=deploy_discovery.analyze_rom(data)
    room_report=room_discovery.analyze_rom(data)
    if not hub_report["safe_to_repoint"]:
        raise ValueError(f"Delivery Hub slot not uniquely safe: {hub_report['candidate_count']}")
    if not marina_report["safe_to_repoint"]:
        raise ValueError(f"Marina slot not uniquely safe: {marina_report['candidate_count']}")
    if not port_report["safe_to_repoint"]:
        raise ValueError(f"Port Link slot not uniquely safe: {port_report['candidate_count']}")
    if not castello_report["safe_to_repoint"]:
        raise ValueError(f"Castello slot not uniquely safe: {castello_report['candidate_count']}")
    if not deploy_report["safe_to_repoint"]:
        raise ValueError(f"Deploy District slot not uniquely safe: {deploy_report['candidate_count']}")
    if not room_report["safe_to_repoint"]:
        raise ValueError(f"Deploy Room slot not uniquely safe: {room_report['candidate_count']}")

    hub_header=hub_report["candidates"][0]
    marina_header=marina_report["candidates"][0]
    port_header=port_report["candidates"][0]
    castello_header=castello_report["candidates"][0]
    deploy_header=deploy_report["candidates"][0]
    room_header=room_report["candidates"][0]

    # Compile once with dummy but valid ROM addresses to obtain stable sizes.
    hub_probe=payload_comp.compile_payload(
        map_spec_path=HUB_SPEC,
        script_spec_path=HUB_SCRIPTS,
        base_address=GBA_ROM_BASE,
        primary_tileset_ptr=hub_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=hub_header["layout"]["secondary_tileset_ptr"],
    )
    marina_probe=payload_comp.compile_payload(
        map_spec_path=MARINA_SPEC,
        script_spec_path=MARINA_SCRIPTS,
        base_address=GBA_ROM_BASE,
        primary_tileset_ptr=marina_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=marina_header["layout"]["secondary_tileset_ptr"],
    )
    port_probe=payload_comp.compile_payload(
        map_spec_path=PORT_LINK_SPEC,
        script_spec_path=PORT_LINK_SCRIPTS,
        base_address=GBA_ROM_BASE,
        primary_tileset_ptr=port_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=port_header["layout"]["secondary_tileset_ptr"],
    )
    castello_probe=payload_comp.compile_payload(
        map_spec_path=CASTELLO_SPEC,
        script_spec_path=CASTELLO_SCRIPTS,
        base_address=GBA_ROM_BASE,
        primary_tileset_ptr=castello_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=castello_header["layout"]["secondary_tileset_ptr"],
    )
    deploy_probe=payload_comp.compile_payload(
        map_spec_path=DEPLOY_DISTRICT_SPEC,
        script_spec_path=DEPLOY_DISTRICT_SCRIPTS,
        base_address=GBA_ROM_BASE,
        primary_tileset_ptr=deploy_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=deploy_header["layout"]["secondary_tileset_ptr"],
    )
    room_probe=payload_comp.compile_payload(
        map_spec_path=DEPLOY_ROOM_SPEC,
        script_spec_path=DEPLOY_ROOM_SCRIPTS,
        base_address=GBA_ROM_BASE,
        primary_tileset_ptr=room_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=room_header["layout"]["secondary_tileset_ptr"],
    )

    required=hub_probe["size"]+3+marina_probe["size"]+3+port_probe["size"]+3+castello_probe["size"]+3+deploy_probe["size"]+3+room_probe["size"]
    space=free.discover_tail(data,required)
    if not space["safe_to_allocate"]:
        raise ValueError(
            f"not enough guarded trailing ROM space: need {required}, "
            f"have {space['available_bytes']} including guard"
        )

    hub_file_offset=space["aligned_start"]
    hub_base=GBA_ROM_BASE+hub_file_offset
    hub=payload_comp.compile_payload(
        map_spec_path=HUB_SPEC,
        script_spec_path=HUB_SCRIPTS,
        base_address=hub_base,
        primary_tileset_ptr=hub_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=hub_header["layout"]["secondary_tileset_ptr"],
    )

    marina_file_offset=align(hub_file_offset+hub["size"],4)
    marina_base=GBA_ROM_BASE+marina_file_offset
    marina=payload_comp.compile_payload(
        map_spec_path=MARINA_SPEC,
        script_spec_path=MARINA_SCRIPTS,
        base_address=marina_base,
        primary_tileset_ptr=marina_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=marina_header["layout"]["secondary_tileset_ptr"],
    )

    port_file_offset=align(marina_file_offset+marina["size"],4)
    port_base=GBA_ROM_BASE+port_file_offset
    port=payload_comp.compile_payload(
        map_spec_path=PORT_LINK_SPEC,
        script_spec_path=PORT_LINK_SCRIPTS,
        base_address=port_base,
        primary_tileset_ptr=port_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=port_header["layout"]["secondary_tileset_ptr"],
    )

    castello_file_offset=align(port_file_offset+port["size"],4)
    castello_base=GBA_ROM_BASE+castello_file_offset
    castello=payload_comp.compile_payload(
        map_spec_path=CASTELLO_SPEC,
        script_spec_path=CASTELLO_SCRIPTS,
        base_address=castello_base,
        primary_tileset_ptr=castello_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=castello_header["layout"]["secondary_tileset_ptr"],
    )

    deploy_file_offset=align(castello_file_offset+castello["size"],4)
    deploy_base=GBA_ROM_BASE+deploy_file_offset
    deploy=payload_comp.compile_payload(
        map_spec_path=DEPLOY_DISTRICT_SPEC,
        script_spec_path=DEPLOY_DISTRICT_SCRIPTS,
        base_address=deploy_base,
        primary_tileset_ptr=deploy_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=deploy_header["layout"]["secondary_tileset_ptr"],
    )

    room_file_offset=align(deploy_file_offset+deploy["size"],4)
    room_base=GBA_ROM_BASE+room_file_offset
    room=payload_comp.compile_payload(
        map_spec_path=DEPLOY_ROOM_SPEC,
        script_spec_path=DEPLOY_ROOM_SCRIPTS,
        base_address=room_base,
        primary_tileset_ptr=room_header["layout"]["primary_tileset_ptr"],
        secondary_tileset_ptr=room_header["layout"]["secondary_tileset_ptr"],
    )

    allocation_end=room_file_offset+room["size"]
    if allocation_end+free.MIN_GUARD>len(data):
        raise ValueError("linked map payloads exceed guarded trailing ROM allocation")

    return {
      "hub_header":hub_header,
      "marina_header":marina_header,
      "port_header":port_header,
      "castello_header":castello_header,
      "deploy_header":deploy_header,
      "room_header":room_header,
      "hub":hub,
      "marina":marina,
      "port":port,
      "castello":castello,
      "deploy":deploy,
      "room":room,
      "hub_file_offset":hub_file_offset,
      "marina_file_offset":marina_file_offset,
      "port_file_offset":port_file_offset,
      "castello_file_offset":castello_file_offset,
      "deploy_file_offset":deploy_file_offset,
      "room_file_offset":room_file_offset,
      "allocation_end":allocation_end,
      "space":space,
    }

def patch_bytes(data:bytes)->tuple[bytes,dict]:
    plan=build_payloads(data)
    entry=load(ENTRY_PATCHER,"entry_patcher")
    wild=load(WILD_HEADER_PATCHER,"wild_header_patcher")

    out=bytearray(data)

    h=plan["hub"]; ho=plan["hub_file_offset"]
    m=plan["marina"]; mo=plan["marina_file_offset"]
    p=plan["port"]; po=plan["port_file_offset"]
    cst=plan["castello"]; co=plan["castello_file_offset"]
    dep=plan["deploy"]; do=plan["deploy_file_offset"]
    room=plan["room"]; ro=plan["room_file_offset"]

    # Data first.
    out[ho:ho+h["size"]]=h["bytes"]
    out[mo:mo+m["size"]]=m["bytes"]
    out[po:po+p["size"]]=p["bytes"]
    out[co:co+cst["size"]]=cst["bytes"]
    out[do:do+dep["size"]]=dep["bytes"]
    out[ro:ro+room["size"]]=room["bytes"]

    # Repoint headers only after all pointed-to payload bytes are present.
    repoint_header(
        out,plan["hub_header"],
        layout_ptr=h["map_layout_address"],
        events_ptr=h["map_events_address"],
    )
    repoint_header(
        out,plan["marina_header"],
        layout_ptr=m["map_layout_address"],
        events_ptr=m["map_events_address"],
        suppress_map_name=True,
    )
    repoint_header(
        out,plan["port_header"],
        layout_ptr=p["map_layout_address"],
        events_ptr=p["map_events_address"],
        suppress_map_name=True,
    )
    repoint_header(
        out,plan["castello_header"],
        layout_ptr=cst["map_layout_address"],
        events_ptr=cst["map_events_address"],
        clear_connections=True,
        suppress_map_name=True,
    )
    repoint_header(
        out,plan["deploy_header"],
        layout_ptr=dep["map_layout_address"],
        events_ptr=dep["map_events_address"],
        clear_connections=True,
        suppress_map_name=True,
    )
    repoint_header(
        out,plan["room_header"],
        layout_ptr=room["map_layout_address"],
        events_ptr=room["map_events_address"],
    )

    # Move the already-patched Route 1 wild header to the custom Port Link.
    out_wild,wild_report=wild.patch_bytes(bytes(out))

    # Finally redirect the two story warps from Oak Lab to the new Hub slot.
    out2,entry_offsets=entry.patch_bytes(out_wild)
    if len(out2)!=len(data):
        raise RuntimeError("custom-map patch changed ROM size")

    evidence={
      "hub_header_offset":plan["hub_header"]["offset"],
      "marina_header_offset":plan["marina_header"]["offset"],
      "port_header_offset":plan["port_header"]["offset"],
      "castello_header_offset":plan["castello_header"]["offset"],
      "deploy_header_offset":plan["deploy_header"]["offset"],
      "room_header_offset":plan["room_header"]["offset"],
      "hub_payload_offset":ho,
      "hub_payload_size":h["size"],
      "marina_payload_offset":mo,
      "marina_payload_size":m["size"],
      "port_payload_offset":po,
      "port_payload_size":p["size"],
      "castello_payload_offset":co,
      "castello_payload_size":cst["size"],
      "deploy_payload_offset":do,
      "deploy_payload_size":dep["size"],
      "room_payload_offset":ro,
      "room_payload_size":room["size"],
      "allocation_end":plan["allocation_end"],
      "entry_warp_offsets":entry_offsets,
      "wild_header_offset":wild_report["header_offset"],
      "wild_info_offset":wild_report["info_offset"],
      "wild_mons_offset":wild_report["mon_offset"],
      "hub_layout_ptr":h["map_layout_address"],
      "hub_events_ptr":h["map_events_address"],
      "marina_layout_ptr":m["map_layout_address"],
      "marina_events_ptr":m["map_events_address"],
      "port_layout_ptr":p["map_layout_address"],
      "port_events_ptr":p["map_events_address"],
      "castello_layout_ptr":cst["map_layout_address"],
      "castello_events_ptr":cst["map_events_address"],
      "deploy_layout_ptr":dep["map_layout_address"],
      "deploy_events_ptr":dep["map_events_address"],
      "room_layout_ptr":room["map_layout_address"],
      "room_events_ptr":room["map_events_address"],
      "exterior_map_name_popups":"disabled_until_authored_names",
    }
    return out2,evidence

def patch_rom(source:Path,output:Path)->Path:
    if not source.is_file(): raise FileNotFoundError(f"input ROM not found: {source}")
    original=source.read_bytes()
    patched,e=patch_bytes(original)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(patched)
    if output.stat().st_size!=source.stat().st_size:
        raise RuntimeError("custom-map output size mismatch")
    print("RC_CUSTOM_MAPS=DELIVERY_HUB+MARINA+PORT_LINK+CASTELLO+DEPLOY_DISTRICT+DEPLOY_ROOM")
    print(f"RC_HUB_HEADER_OFFSET=0x{e['hub_header_offset']:X}")
    print(f"RC_MARINA_HEADER_OFFSET=0x{e['marina_header_offset']:X}")
    print(f"RC_PORT_LINK_HEADER_OFFSET=0x{e['port_header_offset']:X}")
    print(f"RC_CASTELLO_HEADER_OFFSET=0x{e['castello_header_offset']:X}")
    print(f"RC_DEPLOY_DISTRICT_HEADER_OFFSET=0x{e['deploy_header_offset']:X}")
    print(f"RC_DEPLOY_ROOM_HEADER_OFFSET=0x{e['room_header_offset']:X}")
    print(f"RC_HUB_PAYLOAD_OFFSET=0x{e['hub_payload_offset']:X}")
    print(f"RC_MARINA_PAYLOAD_OFFSET=0x{e['marina_payload_offset']:X}")
    print(f"RC_PORT_LINK_PAYLOAD_OFFSET=0x{e['port_payload_offset']:X}")
    print(f"RC_CASTELLO_PAYLOAD_OFFSET=0x{e['castello_payload_offset']:X}")
    print(f"RC_DEPLOY_DISTRICT_PAYLOAD_OFFSET=0x{e['deploy_payload_offset']:X}")
    print(f"RC_DEPLOY_ROOM_PAYLOAD_OFFSET=0x{e['room_payload_offset']:X}")
    print("RC_ENTRY_WARP_OFFSETS="+",".join(f"0x{x:X}" for x in e["entry_warp_offsets"]))
    print(f"RC_PORT_LINK_WILD_HEADER_OFFSET=0x{e['wild_header_offset']:X}")
    print("RC_EXTERIOR_MAP_NAME_POPUPS=DISABLED_UNTIL_AUTHORED_NAMES")
    print(f"RC_CUSTOM_MAPS_OUTPUT={output}")
    return output

def main():
    p=argparse.ArgumentParser(description="Atomically install Release Candidate Delivery Hub, Marina, Port Link, Castello, Deploy District and Deploy Room custom maps.")
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    try: patch_rom(a.source,a.output)
    except (FileNotFoundError,ValueError,RuntimeError) as e:
        print(f"RC_CUSTOM_MAPS=BLOCKED: {e}"); return 1
    return 0

if __name__=="__main__": raise SystemExit(main())
