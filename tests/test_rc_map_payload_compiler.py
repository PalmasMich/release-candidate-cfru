from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"compile_rc_map_payload.py"
HUB=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DELIVERY_HUB.json"
HUB_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DELIVERY_HUB.json"
MARINA=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CAGLIARI_MARINA.json"
MARINA_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CAGLIARI_MARINA.json"

def load():
    s=importlib.util.spec_from_file_location("payload",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestPayload(unittest.TestCase):
    def test_hub_payload_links_layout_events_scripts_and_dialogue(self):
        m=load()
        base=0x08900000
        p=m.compile_payload(
            map_spec_path=HUB,script_spec_path=HUB_SCRIPTS,base_address=base,
            primary_tileset_ptr=0x08100000,secondary_tileset_ptr=0x08110000
        )
        self.assertEqual(p["map"],"RC_DELIVERY_HUB")
        self.assertGreater(p["size"],432)
        self.assertGreater(len(p["script_addresses"]),0)
        self.assertGreater(len(p["dialogue_addresses"]),0)
        self.assertEqual(p["map_layout_address"],base+p["offsets"]["map_layout"])
        self.assertEqual(p["map_events_address"],base+p["offsets"]["map_events"])
        self.assertEqual(p["map_cell_profile"],"RC_DELIVERY_HUB_HOUSE2_BOOTSTRAP")

        layout_off=p["offsets"]["map_layout"]
        layout=p["bytes"][layout_off:layout_off+0x1C]
        self.assertEqual(int.from_bytes(layout[0:4],"little",signed=True),18)
        self.assertEqual(int.from_bytes(layout[4:8],"little",signed=True),12)
        self.assertEqual(int.from_bytes(layout[16:20],"little"),0x08100000)
        self.assertEqual(int.from_bytes(layout[20:24],"little"),0x08110000)

    def test_marina_payload_links_story_script_and_return_warp(self):
        m=load()
        base=0x08910000
        p=m.compile_payload(
            map_spec_path=MARINA,script_spec_path=MARINA_SCRIPTS,base_address=base,
            primary_tileset_ptr=0x08120000,secondary_tileset_ptr=0x08130000
        )
        self.assertEqual(p["map"],"RC_CAGLIARI_MARINA")
        self.assertIn("RC_SCRIPT_MARINA_DELIVERY_LEAD",p["script_addresses"])
        self.assertIn("RC_DIALOGUE_SCOPE_CHANGE",p["dialogue_addresses"])
        self.assertEqual(p["map_cell_profile"],"RC_CAGLIARI_MARINA_GENERAL_BOOTSTRAP")

        warp_off=p["offsets"]["warp_events"]
        warp=p["bytes"][warp_off:warp_off+8]
        self.assertEqual(warp[6:8],bytes([0,27]))

    def test_hub_warp_resolves_to_marina_slot(self):
        m=load()
        p=m.compile_payload(
            map_spec_path=HUB,script_spec_path=HUB_SCRIPTS,base_address=0x08920000,
            primary_tileset_ptr=0x08100000,secondary_tileset_ptr=0x08110000
        )
        warp_off=p["offsets"]["warp_events"]
        warp=p["bytes"][warp_off:warp_off+8]
        self.assertEqual(warp[6:8],bytes([52,3]))

if __name__=="__main__": unittest.main()
