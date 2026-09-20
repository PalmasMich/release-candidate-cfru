#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

TARTREK_SPECIES_ID = 0x050E
FROBYTE_SPECIES_ID = 0x050F
EMBERFOX_SPECIES_ID = 0x0510
MISTRILLO_SPECIES_ID = 0x0511
WINGULL_SPECIES_ID = 0x0135
MEOWTH_SPECIES_ID = 0x0034

BULBASAUR_STARTER_SIGNATURE = bytes.fromhex("16 01 40 00 00 16 02 40 01 00 16 03 40 04 00 16 04 40 07 00")
SQUIRTLE_STARTER_SIGNATURE = bytes.fromhex("16 01 40 01 00 16 02 40 07 00 16 03 40 01 00")
CHARMANDER_STARTER_SIGNATURE = bytes.fromhex("16 01 40 02 00 16 02 40 04 00 16 03 40 07 00")
PLAYER_SPECIES_VALUE_OFFSET = 8
RIVAL_SPECIES_VALUE_OFFSET = 13
OAK_LAB_RIVAL_PARTIES_SIGNATURE = bytes.fromhex("00 00 05 00 07 00 00 00 05 00 01 00 00 00 05 00 04 00")
RIVAL_PARTY_SPECIES_OFFSETS = (4, 10, 16)
ROUTE1_WILD_SIGNATURE = bytes.fromhex("03 03 10 00 03 03 13 00 03 03 10 00 03 03 13 00 02 02 10 00 02 02 13 00 03 03 10 00 03 03 13 00 04 04 10 00 04 04 13 00 05 05 10 00 04 04 13 00")
GRASS_SLOT_WEIGHTS = (20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1)
ROUTE1_PREVIEW_SPECIES = (MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, WINGULL_SPECIES_ID, WINGULL_SPECIES_ID, WINGULL_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID)
ROUTE1_PREVIEW_LEVELS = ((3, 3), (4, 4), (3, 3), (5, 5), (3, 3), (4, 4), (3, 3), (4, 4), (3, 3), (4, 4), (3, 3), (4, 4))

CHARMAP = {**{chr(ord("A") + i): 0xBB + i for i in range(26)}, **{chr(ord("a") + i): 0xD5 + i for i in range(26)}, **{str(i): 0xA1 + i for i in range(10)}, " ": 0x00, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE, ",": 0xB8, "/": 0xBA, ":": 0xF0, "'": 0xB4, "é": 0x1B, "\n": 0xFE}
PLACEHOLDERS = {"{PLAYER}": b"\xFD\x01", "{RIVAL}": b"\xFD\x06"}

def encode_text(text: str) -> bytes:
    out = bytearray(); i = 0
    while i < len(text):
        for token, encoded in PLACEHOLDERS.items():
            if text.startswith(token, i): out.extend(encoded); i += len(token); break
        else: out.append(CHARMAP[text[i]]); i += 1
    return bytes(out)

VISIBLE_TEXT_REPLACEMENTS = (
    (encode_text("Welcome to the world of POKéMON!"), encode_text("Welcome to Release Candidate!")),
    (encode_text("My name is OAK."), encode_text("I'm your Lead.")),
    (encode_text("People affectionately refer to me"), encode_text("They call me Delivery Lead")),
    (encode_text("This is my grandson."), encode_text("Meet your teammate.")),
    (encode_text("He's been your rival since you both"), encode_text("He's tracked your KPI since day one")),
    (encode_text("were babies."), encode_text("onboarding.")),
    (encode_text("as the POKéMON PROFESSOR."), encode_text("on this project.")),
    (encode_text("YOUR NAME?"), encode_text("YOUR ID?")),
    (encode_text("RIVAL's NAME?"), encode_text("TEAMMATE ID?")),
    (encode_text("OAK: Hey! Wait!\nDon't go out!"), encode_text("LEAD: Hey! Wait!\nNo field test yet!")),
    (encode_text("OAK: It's unsafe!\nWild POKéMON live in tall grass!"), encode_text("LEAD: Scope changed!\nField checks start today!")),
    (encode_text("You need your own POKéMON for\nyour protection."), encode_text("You need a resource for\nthe Port Link test.")),
    (encode_text("I know!\nHere, come with me!"), encode_text("Come on!\nDelivery Hub, now!")),
    (encode_text("There are three POKéMON here."), encode_text("Three resources are ready.")),
    (encode_text("You can have one.\nGo on, choose!"), encode_text("Pick one now.\nFirst task starts!")),
    (encode_text("OAK: Now, {PLAYER}."), encode_text("LEAD: Hi, {PLAYER}.")),
    (encode_text("Which one will you choose for\nyourself?"), encode_text("Which resource joins your\nfirst sprint?")),
    (encode_text("I see! BULBASAUR is your choice."), encode_text("TARTREK is your new partner!")),
    (encode_text("Hm! SQUIRTLE is your choice."), encode_text("FROBYTE is your new partner!")),
    (encode_text("Ah! CHARMANDER is your choice."), encode_text("EMBERFOX is your new partner!")),
    (encode_text("It's very easy to raise."), encode_text("First task starts now!")),
    (encode_text("the GRASS POKéMON BULBASAUR?"), encode_text("the GRASS/GROUND TARTREK?")),
    (encode_text("the WATER POKéMON SQUIRTLE?"), encode_text("the WATER/ELECTRIC FROBYTE?")),
    (encode_text("FIRE POKéMON CHARMANDER?"), encode_text("FIRE/DARK EMBERFOX?")),
    (encode_text("{RIVAL}: Heh, I don't need to be\ngreedy like you. I'm mature!"), encode_text("{RIVAL}: I don't chase metrics.\nI just happen to lead them.")),
    (encode_text("Go ahead and choose, {PLAYER}!"), encode_text("Choose, {PLAYER}. KPI clock is live!")),
    (encode_text("{RIVAL}: I'll take this one, then!"), encode_text("{RIVAL}: Fine. I'll take this one!")),
    (encode_text("{RIVAL}: My POKéMON looks a lot\ntougher than yours."), encode_text("{RIVAL}: My KPI already looks\nbetter than yours.")),
    (encode_text("{RIVAL}: Wait, {PLAYER}!"), encode_text("{RIVAL}: Wait, {PLAYER}!")),
    (encode_text("Let's check out our POKéMON!"), encode_text("Let's benchmark our resources!")),
    (encode_text("Come on, I'll take you on!"), encode_text("KPI check: show velocity!")),
    (encode_text("WHAT?\nUnbelievable!\nI picked the wrong POKéMON!"), encode_text("WHAT?\nKPI variance!\nI need a new baseline!")),
    (encode_text("{RIVAL}: Yeah!\nAm I great or what?"), encode_text("{RIVAL}: Yeah!\nKPI is GREEN!")),
    (encode_text("{RIVAL}: Okay! I'll make my\nPOKéMON battle to toughen it up!"), encode_text("{RIVAL}: Fine! I'll optimize my\nresource before next review!")),
    (encode_text("{PLAYER}! Gramps!\nSmell you later!"), encode_text("{PLAYER}! Lead!\nSee you at stand-up!")),
    (encode_text("PALLET TOWN\nShades of your journey await!"), encode_text("CAGLIARI\nFirst sprint starts here!")),
    (encode_text("Technology is incredible!"), encode_text("Delivery is incredible!")),
    (encode_text("You can now store and recall items"), encode_text("We can now track every task")),
    (encode_text("and POKéMON as data via PC."), encode_text("and blocker on one dashboard.")),
    (encode_text("I'm raising POKéMON, too."), encode_text("I'm on this project, too.")),
    (encode_text("When they get strong, they can\nprotect me."), encode_text("When scope changes, I just\nupdate the estimate.")),
    (encode_text("OAK POKéMON RESEARCH LAB"), encode_text("DELIVERY HUB - CAGLIARI")),
    (encode_text("Those are POKé BALLS.\nThey contain POKéMON!"), encode_text("Those are team slots.\nResources inside!")),
    (encode_text("Press START to open the MENU!"), encode_text("Press START for your dashboard!")),
    (encode_text("The SAVE option is on the MENU.\nUse it regularly."), encode_text("Save before each release.\nRollback matters.")),
    (encode_text("OAK: If a wild POKéMON appears,"), encode_text("LEAD: Field test starts outside.")),
    (encode_text("your POKéMON can battle it."), encode_text("Use your partner on Port Link.")),
    (encode_text("With it at your side, you should be"), encode_text("Close one check, then report")),
    (encode_text("able to reach the next town."), encode_text("at Marina Porto.")),
    (encode_text("ROUTE 1\nPALLET TOWN - VIRIDIAN CITY"), encode_text("PORT LINK\nCAGLIARI - MARINA PORTO")),
    (encode_text("Hi!\nI work at a POKéMON MART."), encode_text("Hi!\nI work on Delivery.")),
    (encode_text("It's part of a convenient chain\nselling all sorts of items."), encode_text("MISTRILLO is in this grass.\nField test it now.")),
    (encode_text("Please, visit us in VIRIDIAN CITY."), encode_text("Please, report at MARINA PORTO.")),
    (encode_text("I know, I'll give you a sample.\nHere you go!"), encode_text("Quick handoff: take this.\nUse it well!")),
    (encode_text("Please come see us if you need\nPOKé BALLS for catching POKéMON."), encode_text("Ping Delivery if you need\nmore field-test supplies.")),
    (encode_text("See those ledges along the road?"), encode_text("See those shortcuts on Port Link?")),
    (encode_text("It's a bit scary, but you can jump\nfrom them."), encode_text("Use them if the timeline\nstarts slipping.")),
    (encode_text("You can get back to PALLET TOWN\nquicker that way."), encode_text("You can get back to CAGLIARI\nquicker that way.")),
    (encode_text("VIRIDIAN CITY \nThe Eternally Green Paradise"), encode_text("MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE")),
    (encode_text("This POKéMON GYM is always closed."), encode_text("This deploy gate is still closed.")),
    (encode_text("I wonder who the LEADER is?"), encode_text("Stakeholder approval pending.")),
    (encode_text("This is private property!"), encode_text("This scope is out of bounds!")),
    (encode_text("Time is money, and neither should\nbe ill spent…"), encode_text("Time is budget. Keep meetings\nshort and useful.")),
    (encode_text("VIRIDIAN CITY POKéMON GYM"), encode_text("MARINA PORTO DEPLOY GATE")),
    (encode_text("VIRIDIAN GYM's doors are locked…"), encode_text("DEPLOY GATE locked: scope open.")),
)
REQUIRED_VISIBLE_TEXTS = tuple(encode_text(text) for text in ("Welcome to Release Candidate!", "LEAD: Scope changed!\nField checks start today!", "CAGLIARI\nFirst sprint starts here!", "DELIVERY HUB - CAGLIARI", "Three resources are ready.", "Let's benchmark our resources!", "KPI check: show velocity!", "PORT LINK\nCAGLIARI - MARINA PORTO", "MISTRILLO is in this grass.\nField test it now.", "MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE", "MARINA PORTO DEPLOY GATE"))
MAP_NAME_REPLACEMENT = (encode_text("PALLET TOWN") + b"\xFF" + encode_text("VIRIDIAN CITY") + b"\xFF", encode_text("CAGLIARI") + b"\xFF" + (b"\x00" * 3) + encode_text("MARINA PORTO") + b"\x00\xFF")
LAB_SIGN_REPLACEMENT = (b"\xCA\xC9\xC5\x1B\xC9\xC8\x00\xCC\xBF\xCD\xBF\xBB\xCC\xBD\xC2\x00\xC6\xBB\xBC", encode_text("DELIVERY HUB"))

def _find_exactly_one(data, signature, label):
    positions=[]; start=0
    while True:
        pos=data.find(signature,start)
        if pos<0: break
        positions.append(pos); start=pos+1
    if len(positions)!=1: raise ValueError(f"Expected exactly one {label} signature, found {len(positions)}.")
    return positions[0]

def patch_preview_starters(data):
    for signature,label,player_species,rival_species in ((BULBASAUR_STARTER_SIGNATURE,"Bulbasaur starter",TARTREK_SPECIES_ID,EMBERFOX_SPECIES_ID),(SQUIRTLE_STARTER_SIGNATURE,"Squirtle starter",FROBYTE_SPECIES_ID,TARTREK_SPECIES_ID),(CHARMANDER_STARTER_SIGNATURE,"Charmander starter",EMBERFOX_SPECIES_ID,FROBYTE_SPECIES_ID)):
        pos=_find_exactly_one(data,signature,label); data[pos+PLAYER_SPECIES_VALUE_OFFSET:pos+PLAYER_SPECIES_VALUE_OFFSET+2]=player_species.to_bytes(2,"little"); data[pos+RIVAL_SPECIES_VALUE_OFFSET:pos+RIVAL_SPECIES_VALUE_OFFSET+2]=rival_species.to_bytes(2,"little")
    return data

def patched_starter_signature(signature, player_species, rival_species):
    patched=bytearray(signature); patched[PLAYER_SPECIES_VALUE_OFFSET:PLAYER_SPECIES_VALUE_OFFSET+2]=player_species.to_bytes(2,"little"); patched[RIVAL_SPECIES_VALUE_OFFSET:RIVAL_SPECIES_VALUE_OFFSET+2]=rival_species.to_bytes(2,"little"); return bytes(patched)

def patch_oak_lab_rival_parties(data):
    positions=[]; start=0
    while True:
        pos=data.find(OAK_LAB_RIVAL_PARTIES_SIGNATURE,start)
        if pos<0: break
        positions.append(pos); start=pos+1
    if not positions: print("RC_PREVIEW_KPI_RIVAL_PARTY=PENDING:LEGACY_SIGNATURE_NOT_FOUND"); return data,False
    if len(positions)!=1: raise ValueError(f"Expected at most one Oak Lab rival party signature, found {len(positions)}.")
    pos=positions[0]
    for rel,species in zip(RIVAL_PARTY_SPECIES_OFFSETS,(FROBYTE_SPECIES_ID,TARTREK_SPECIES_ID,EMBERFOX_SPECIES_ID)): data[pos+rel:pos+rel+2]=species.to_bytes(2,"little")
    print("RC_PREVIEW_KPI_RIVAL_PARTY=APPLIED"); return data,True

def _replace_size_preserving(data,old,new,expected=None):
    if len(new)>len(old): raise ValueError("Replacement text cannot exceed the source byte length.")
    positions=[]; start=0
    while True:
        pos=data.find(old,start)
        if pos<0: break
        positions.append(pos); start=pos+1
    if expected is not None and len(positions)!=expected: raise ValueError(f"Expected {expected} occurrence(s), found {len(positions)}.")
    replacement=new+(b"\x00"*(len(old)-len(new)))
    for pos in positions: data[pos:pos+len(old)]=replacement
    return len(positions)

def patch_route1_wild_encounters(data):
    base=_find_exactly_one(data,ROUTE1_WILD_SIGNATURE,"FireRed Route 1 wild encounter")
    for record,(species,levels) in enumerate(zip(ROUTE1_PREVIEW_SPECIES,ROUTE1_PREVIEW_LEVELS)):
        p=base+record*4; data[p:p+2]=bytes(levels); data[p+2:p+4]=species.to_bytes(2,"little")
    return data

def patch_visible_preview_text(data):
    applied=[]
    for index,(old,new) in enumerate(VISIBLE_TEXT_REPLACEMENTS):
        count=_replace_size_preserving(data,old,new)
        if count==0: print(f"RC_PREVIEW_TEXT_{index:02d}=PENDING:LEGACY_SIGNATURE_NOT_FOUND"); continue
        if count!=1: raise ValueError(f"Expected at most one legacy visible-text signature {index}, found {count}.")
        applied.append(new)
    old_city,new_city=MAP_NAME_REPLACEMENT; city_count=_replace_size_preserving(data,old_city,new_city)
    old_lab,new_lab=LAB_SIGN_REPLACEMENT; lab_count=_replace_size_preserving(data,old_lab,new_lab)
    return data,applied,city_count==1,lab_count>=1

def _patched_route1_signature():
    expected=bytearray(ROUTE1_WILD_SIGNATURE)
    for record,(species,levels) in enumerate(zip(ROUTE1_PREVIEW_SPECIES,ROUTE1_PREVIEW_LEVELS)):
        p=record*4; expected[p:p+2]=bytes(levels); expected[p+2:p+4]=species.to_bytes(2,"little")
    return bytes(expected)

def validate_preview_patch(data):
    for signature,player,rival,label in ((BULBASAUR_STARTER_SIGNATURE,TARTREK_SPECIES_ID,EMBERFOX_SPECIES_ID,"Tartrek starter wiring"),(SQUIRTLE_STARTER_SIGNATURE,FROBYTE_SPECIES_ID,TARTREK_SPECIES_ID,"Frobyte starter wiring"),(CHARMANDER_STARTER_SIGNATURE,EMBERFOX_SPECIES_ID,FROBYTE_SPECIES_ID,"Emberfox starter wiring")):
        if data.count(patched_starter_signature(signature,player,rival))!=1: raise RuntimeError(f"Preview validation failed: {label} is missing or duplicated.")
    rival_party=b"".join(b"\x00\x00\x05\x00"+s.to_bytes(2,"little") for s in (FROBYTE_SPECIES_ID,TARTREK_SPECIES_ID,EMBERFOX_SPECIES_ID))
    if data.count(rival_party)!=1: raise RuntimeError("Preview validation failed: KPI-rival party is missing or duplicated.")
    if data.count(_patched_route1_signature())!=1: raise RuntimeError("Preview validation failed: Port Link custom encounter table is missing or duplicated.")
    if any(anchor not in data for anchor in REQUIRED_VISIBLE_TEXTS): raise RuntimeError("Preview validation failed: Core Cagliari preview identity is incomplete.")

def patch_rom(source,output):
    source,output=Path(source),Path(output)
    if not source.is_file(): raise FileNotFoundError(f"Input ROM not found: {source}")
    original=source.read_bytes(); patched=patch_preview_starters(bytearray(original)); patched,_=patch_oak_lab_rival_parties(patched); patched,_,_,_=patch_visible_preview_text(patched); patched=patch_route1_wild_encounters(patched); validate_preview_patch(patched)
    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(patched)
    if output.stat().st_size!=source.stat().st_size: raise RuntimeError("Preview patch changed ROM size unexpectedly.")
    print("RC_PREVIEW_PATCH=THREE_STARTERS+CAGLIARI_IDENTITY+KPI_RIVAL+PORT_LINK_ENCOUNTERS"); print(f"RC_PREVIEW_STARTERS=0x{TARTREK_SPECIES_ID:04X},0x{FROBYTE_SPECIES_ID:04X},0x{EMBERFOX_SPECIES_ID:04X}"); print(f"RC_PREVIEW_WILD_SPECIES_ID=0x{MISTRILLO_SPECIES_ID:04X}"); print(f"RC_PREVIEW_OUTPUT={output}"); return output

def main():
    parser=argparse.ArgumentParser(description="Apply the visible Release Candidate Cagliari preview patch to a private CFRU ROM."); parser.add_argument("source",type=Path); parser.add_argument("output",type=Path); args=parser.parse_args()
    try: patch_rom(args.source,args.output)
    except (FileNotFoundError,ValueError,RuntimeError) as exc: print(f"ERROR: {exc}"); return 1
    return 0

if __name__ == "__main__": raise SystemExit(main())