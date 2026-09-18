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
FREE_DISCOVERY=ROOT/"scripts"/"discover_rc_tail_free_space.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"
ENTRY_PATCHER=ROOT/"scripts"/"patch_pallet_lab_entry_to_delivery_hub.py"

HUB_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DELIVERY_HUB.json"
HUB_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DELIVERY_HUB.json"
MARINA_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CAGLIARI_MARINA.json"
MARINA_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CAGLIARI_MARINA.json"
PORT_LINK_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_PORT_CONNECTION.json"
PORT_LINK_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_PORT_CONNECTION.json"

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
    }
    for key in current:
        if current[key]!=header[key]:
            raise ValueError(
                f"map header changed after discovery at 0x{o:X}: "
                f"{key} expected 0x{header[key]:08X}, got 0x{current[key]:08X}"
            )

def repoint_header(data:bytearray,header:dict,*,layout_ptr:int,events_ptr:int)->None:
    verify_header_unchanged(bytes(data),header)
    o=header["offset"]
    data[o:o+4]=int(layout_ptr).to_bytes(4,"little")
    data[o+4:o+8]=int(events_ptr).to_bytes(4,"little")

def build_payloads(data:bytes)->dict:
    hub_discovery=load(HUB_DISCOVERY,"hub_slot")
    marina_discovery=load(MARINA_DISCOVERY,"marina_slot")
    port_discovery=load(PORT_LINK_DISCOVERY,"port_link_slot")
    free=load(FREE_DISCOVERY,"tail_free")
    payload_comp=load(PAYLOAD_COMPILER,"payload_compiler")

    hub_report=hub_discovery.analyze_rom(data)
    marina_report=marina_discovery.analyze_rom(data)
    port_report=port_discovery.analyze_rom(data)
    if not hub_report["safe_to_repoint"]:
        raise ValueError(f"Delivery Hub slot not uniquely safe: {hub_report['candidate_count']}")
    if not marina_report["safe_to_repoint"]:
        raise ValueError(f"Marina slot not uniquely safe: {marina_report['candidate_count']}")
    if not port_report["safe_to_repoint"]:
        raise ValueError(f"Port Link slot not uniquely safe: {port_report['candidate_count']}")

    hub_header=hub_report["candidates"][0]
    marina_header=marina_report["candidates"][0]
    port_header=port_report["candidates"][0]

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

    required=hub_probe["size"]+3+marina_probe["size"]+3+port_probe["size"]
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

    allocation_end=port_file_offset+port["size"]
    if allocation_end+free.MIN_GUARD>len(data):
        raise ValueError("linked map payloads exceed guarded trailing ROM allocation")

    return {
      "hub_header":hub_header,
      "marina_header":marina_header,
      "port_header":port_header,
      "hub":hub,
      "marina":marina,
      "port":port,
      "hub_file_offset":hub_file_offset,
      "marina_file_offset":marina_file_offset,
      "port_file_offset":port_file_offset,
      "allocation_end":allocation_end,
      "space":space,
    }

def patch_bytes(data:bytes)->tuple[bytes,dict]:
    plan=build_payloads(data)
    entry=load(ENTRY_PATCHER,"entry_patcher")

    out=bytearray(data)

    h=plan["hub"]; ho=plan["hub_file_offset"]
    m=plan["marina"]; mo=plan["marina_file_offset"]
    p=plan["port"]; po=plan["port_file_offset"]

    # Data first.
    out[ho:ho+h["size"]]=h["bytes"]
    out[mo:mo+m["size"]]=m["bytes"]
    out[po:po+p["size"]]=p["bytes"]

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
    )
    repoint_header(
        out,plan["port_header"],
        layout_ptr=p["map_layout_address"],
        events_ptr=p["map_events_address"],
    )

    # Finally redirect the two story warps from Oak Lab to the new Hub slot.
    out2,entry_offsets=entry.patch_bytes(bytes(out))
    if len(out2)!=len(data):
        raise RuntimeError("custom-map patch changed ROM size")

    evidence={
      "hub_header_offset":plan["hub_header"]["offset"],
      "marina_header_offset":plan["marina_header"]["offset"],
      "port_header_offset":plan["port_header"]["offset"],
      "hub_payload_offset":ho,
      "hub_payload_size":h["size"],
      "marina_payload_offset":mo,
      "marina_payload_size":m["size"],
      "port_payload_offset":po,
      "port_payload_size":p["size"],
      "allocation_end":plan["allocation_end"],
      "entry_warp_offsets":entry_offsets,
      "hub_layout_ptr":h["map_layout_address"],
      "hub_events_ptr":h["map_events_address"],
      "marina_layout_ptr":m["map_layout_address"],
      "marina_events_ptr":m["map_events_address"],
      "port_layout_ptr":p["map_layout_address"],
      "port_events_ptr":p["map_events_address"],
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
    print("RC_CUSTOM_MAPS=DELIVERY_HUB+MARINA+PORT_LINK")
    print(f"RC_HUB_HEADER_OFFSET=0x{e['hub_header_offset']:X}")
    print(f"RC_MARINA_HEADER_OFFSET=0x{e['marina_header_offset']:X}")
    print(f"RC_PORT_LINK_HEADER_OFFSET=0x{e['port_header_offset']:X}")
    print(f"RC_HUB_PAYLOAD_OFFSET=0x{e['hub_payload_offset']:X}")
    print(f"RC_MARINA_PAYLOAD_OFFSET=0x{e['marina_payload_offset']:X}")
    print(f"RC_PORT_LINK_PAYLOAD_OFFSET=0x{e['port_payload_offset']:X}")
    print("RC_ENTRY_WARP_OFFSETS="+",".join(f"0x{x:X}" for x in e["entry_warp_offsets"]))
    print(f"RC_CUSTOM_MAPS_OUTPUT={output}")
    return output

def main():
    p=argparse.ArgumentParser(description="Atomically install Release Candidate Delivery Hub, Marina and Port Link custom maps.")
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    try: patch_rom(a.source,a.output)
    except (FileNotFoundError,ValueError,RuntimeError) as e:
        print(f"RC_CUSTOM_MAPS=BLOCKED: {e}"); return 1
    return 0

if __name__=="__main__": raise SystemExit(main())
