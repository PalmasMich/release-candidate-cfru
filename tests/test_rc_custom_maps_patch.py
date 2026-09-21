from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
PATCHER=ROOT/"scripts"/"patch_rc_custom_maps.py"
HUB_DISC=ROOT/"scripts"/"discover_delivery_hub_map_slot.py"
MARINA_DISC=ROOT/"scripts"/"discover_marina_map_slot.py"
PORT_DISC=ROOT/"scripts"/"discover_port_link_map_slot.py"
CASTELLO_DISC=ROOT/"scripts"/"discover_castello_map_slot.py"
DEPLOY_DISC=ROOT/"scripts"/"discover_deploy_district_map_slot.py"
ROOM_DISC=ROOT/"scripts"/"discover_deploy_room_map_slot.py"
ENTRY=ROOT/"scripts"/"patch_pallet_lab_entry_to_delivery_hub.py"
WILD=ROOT/"scripts"/"patch_port_link_wild_header.py"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestCustomMapsPatch(unittest.TestCase):
    def fixture(self):
        hub=load(HUB_DISC,"hub"); marina=load(MARINA_DISC,"marina"); port=load(PORT_DISC,"port"); castello=load(CASTELLO_DISC,"castello"); deploy=load(DEPLOY_DISC,"deploy"); room=load(ROOM_DISC,"room"); entry=load(ENTRY,"entry"); wild=load(WILD,"wild")
        rom=bytearray(b"\x00"*0x10000); ptr=lambda o:(0x08000000+o).to_bytes(4,"little")
        rom[0x500:0x500+len(entry.SOURCE)]=entry.SOURCE; rom[0x600:0x600+len(entry.SOURCE)]=entry.SOURCE
        mon_offset=0x700; info_offset=0x780; wild_header_offset=0x7A0
        rom[mon_offset:mon_offset+len(wild.ROUTE1_PATCHED_WILD_SIGNATURE)]=wild.ROUTE1_PATCHED_WILD_SIGNATURE; rom[info_offset:info_offset+4]=bytes([wild.ROUTE1_ENCOUNTER_RATE,0,0,0]); rom[info_offset+4:info_offset+8]=ptr(mon_offset); rom[wild_header_offset]=wild.ROUTE1_GROUP; rom[wild_header_offset+1]=wild.ROUTE1_MAP; rom[wild_header_offset+2:wild_header_offset+4]=b"\x00\x00"; rom[wild_header_offset+4:wild_header_offset+8]=ptr(info_offset); rom[wild_header_offset+8:wild_header_offset+20]=b"\x00"*12
        def layout(off,w,h,border,mapdata,primary,secondary):
            b=bytearray(b"\x00"*0x1C); b[0:4]=w.to_bytes(4,"little",signed=True); b[4:8]=h.to_bytes(4,"little",signed=True); b[8:12]=ptr(border); b[12:16]=ptr(mapdata); b[16:20]=ptr(primary); b[20:24]=ptr(secondary); b[24]=2;b[25]=2; rom[off:off+0x1C]=b
        def header(off,layout_off,events,scripts,connections,music,layout_id,mapsec,weather,maptype,flags=0,battle=0):
            b=bytearray(b"\x00"*0x1C); b[0:4]=ptr(layout_off); b[4:8]=ptr(events); b[8:12]=ptr(scripts); b[12:16]=(ptr(connections) if connections else 0).to_bytes(4,"little"); b[16:18]=music.to_bytes(2,"little"); b[18:20]=layout_id.to_bytes(2,"little"); b[20]=mapsec;b[21]=0;b[22]=weather;b[23]=maptype;b[24]=1 if maptype!=hub.MAP_TYPE_INDOOR else 0;b[25]=flags;b[26]=0;b[27]=battle; rom[off:off+0x1C]=b
        layout(0x2000,11,9,0x3000,0x3200,0x3400,0x3600); header(0x1000,0x2000,0x2400,0x2500,0,hub.MUSIC_ROUTE3,0x1111,hub.MAPSEC_ROUTE19,hub.WEATHER_NONE,hub.MAP_TYPE_INDOOR,0,hub.BATTLE_SCENE_NORMAL)
        layout(0x2200,84,20,0x3800,0x3A00,0x3C00,0x3E00); header(0x1100,0x2200,0x2600,0x2700,0,marina.MUSIC_SEVII_ROUTE,0x2222,marina.MAPSEC_SEVII_ISLE_8,marina.WEATHER_SUNNY,marina.MAP_TYPE_ROUTE,marina.HEADER_FLAGS)
        layout(0x2800,24,60,0x4000,0x4200,0x4400,0x4600); header(0x1200,0x2800,0x2A00,0x2B00,0,port.MUSIC_SEVII_ROUTE,0x3333,port.MAPSEC_SEVII_ISLE_9,port.WEATHER_SUNNY,port.MAP_TYPE_ROUTE,port.HEADER_FLAGS)
        layout(0x2C00,1,1,0x4800,0x4820,0x4840,0x4860); header(0x1300,0x2C00,0x2D00,0x2E00,0x2F00,castello.MUSIC_SEVII_ROUTE,0x4444,castello.MAPSEC_SEVII_ISLE_6,castello.WEATHER_SUNNY,castello.MAP_TYPE_ROUTE,castello.HEADER_FLAGS)
        layout(0x3000,1,1,0x4880,0x48A0,0x48C0,0x48E0); header(0x1400,0x3000,0x3100,0x3200,0x3300,deploy.MUSIC_SEVII_ROUTE,0x5555,deploy.MAPSEC_SEVII_ISLE_7,deploy.WEATHER_SUNNY,deploy.MAP_TYPE_ROUTE,deploy.HEADER_FLAGS)
        layout(0x3400,11,9,0x4900,0x4920,0x4940,0x4960); header(0x1500,0x3400,0x3500,0x3600,0,room.MUSIC_ROUTE3,0x6666,room.MAPSEC_ROUTE6,room.WEATHER_NONE,room.MAP_TYPE_INDOOR,0,room.BATTLE_SCENE_NORMAL)
        rom[0xC000:]=b"\xFF"*(len(rom)-0xC000); return bytes(rom)

    def test_installs_six_maps_and_repoints_entry_atomically(self):
        patcher=load(PATCHER,"patcher"); entry=load(ENTRY,"entry"); original=self.fixture(); patched,e=patcher.patch_bytes(original)
        self.assertEqual(len(patched),len(original)); self.assertEqual(patched.count(entry.SOURCE),0); self.assertEqual(patched.count(entry.TARGET),2); self.assertEqual(patched[e["wild_header_offset"]],3); self.assertEqual(patched[e["wild_header_offset"]+1],53)
        for off,key in ((0x1000,"hub"),(0x1100,"marina"),(0x1200,"port"),(0x1300,"castello"),(0x1400,"deploy"),(0x1500,"room")):
            self.assertEqual(int.from_bytes(patched[off:off+4],"little"),e[f"{key}_layout_ptr"]); self.assertEqual(int.from_bytes(patched[off+4:off+8],"little"),e[f"{key}_events_ptr"])
        self.assertEqual(patched[0x130C:0x1310],b"\x00"*4); self.assertEqual(patched[0x140C:0x1410],b"\x00"*4)
        self.assertGreaterEqual(e["hub_payload_offset"],0xC000); self.assertGreater(e["marina_payload_offset"],e["hub_payload_offset"]); self.assertGreater(e["port_payload_offset"],e["marina_payload_offset"]); self.assertGreater(e["castello_payload_offset"],e["port_payload_offset"]); self.assertGreater(e["deploy_payload_offset"],e["castello_payload_offset"]); self.assertGreater(e["room_payload_offset"],e["deploy_payload_offset"])

    def test_playable_preview_payloads_link_story_battle_and_field_test_scripts(self):
        patcher=load(PATCHER,"patcher"); plan=patcher.build_payloads(self.fixture())
        hub=plan["hub"]; port=plan["port"]
        for script in ("RC_SCRIPT_STARTER_TARTREK","RC_SCRIPT_STARTER_FROBYTE","RC_SCRIPT_STARTER_EMBERFOX","RC_SCRIPT_KPI_RIVAL"):
            self.assertIn(script,hub["script_addresses"])
        self.assertEqual(hub["event_counts"]["bg"],3); self.assertEqual(hub["event_counts"]["objects"],2)
        self.assertIn("RC_SCRIPT_WILD_TUTORIAL_TRIGGER",port["script_addresses"]); self.assertIn("RC_SCRIPT_PORT_TRAINER",port["script_addresses"]); self.assertEqual(port["event_counts"]["coords"],1); self.assertEqual(port["event_counts"]["objects"],1)
        # The forced first field test is materially playable, not just content metadata.
        wild_script=port["script_addresses"]["RC_SCRIPT_WILD_TUTORIAL_TRIGGER"]-port["base_address"]
        self.assertIn(bytes([0xB6,0x11,0x05,0x03,0x00,0x00,0xB7]),port["bytes"][wild_script:wild_script+96])
        # The custom Port trainer uses trainerbattle and is reachable through its object event.
        trainer_script=port["script_addresses"]["RC_SCRIPT_PORT_TRAINER"]-port["base_address"]
        self.assertEqual(port["bytes"][trainer_script],0x6A); self.assertIn(0x5C,port["bytes"][trainer_script:trainer_script+48])

    def test_blocks_without_guarded_tail_space(self):
        patcher=load(PATCHER,"patcher"); data=bytearray(self.fixture()); data[0xC000:]=b"\x00"*(len(data)-0xC000)
        with self.assertRaisesRegex(ValueError,"trailing ROM space"): patcher.patch_bytes(bytes(data))

if __name__=="__main__": unittest.main()
