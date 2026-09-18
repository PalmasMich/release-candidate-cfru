from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
CELL_COMPILER=ROOT/"scripts"/"compile_rc_map_cells.py"
EVENTS_COMPILER=ROOT/"scripts"/"compile_rc_map_events.py"
SCRIPT_COMPILER=ROOT/"scripts"/"compile_rc_event_scripts.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"
MAP_SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_PORT_CONNECTION.json"
SCRIPT_SPEC=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_PORT_CONNECTION.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestPortLinkCustomMap(unittest.TestCase):
    def test_map_and_cells_compile(self):
        map_comp=load(MAP_COMPILER,"map_comp")
        cell_comp=load(CELL_COMPILER,"cell_comp")
        map_ir=map_comp.compile_file(MAP_SPEC)
        cells=cell_comp.compile_file(MAP_SPEC)
        self.assertEqual(map_ir["id"],"RC_PORT_CONNECTION")
        self.assertEqual(map_ir["dimensions"],{"width":28,"height":12})
        self.assertEqual(cells["map_bytes"],28*12*2)
        self.assertEqual(cells["profile"],"RC_PORT_LINK_GENERAL_BOOTSTRAP")
        self.assertIn("wild_grass",cells["role_counts"])

    def test_coord_trigger_and_trainer_are_binary_events(self):
        events=load(EVENTS_COMPILER,"events")
        ir=events.compile_file(MAP_SPEC)
        self.assertEqual(ir["object_events"]["count"],1)
        self.assertEqual(ir["warp_events"]["count"],1)
        self.assertEqual(ir["coord_events"]["count"],1)
        self.assertEqual(ir["coord_events"]["size"],16)
        coord=bytes.fromhex(ir["coord_events"]["bytes_hex"])
        self.assertEqual(int.from_bytes(coord[6:8],"little"),0x4001)
        self.assertEqual(int.from_bytes(coord[8:10],"little"),0)
        self.assertEqual(ir["coord_events"]["relocations"][0]["symbol"],"RC_SCRIPT_WILD_TUTORIAL_TRIGGER")

    def test_scripts_force_first_mistrillo_then_set_tutorial_flag(self):
        comp=load(SCRIPT_COMPILER,"scripts")
        ir=comp.compile_file(SCRIPT_SPEC)
        by_id={x["id"]:x for x in ir["scripts"]}
        tutorial=bytes.fromhex(by_id["RC_SCRIPT_WILD_TUTORIAL_TRIGGER"]["bytes_hex"])

        wild=tutorial.index(bytes([comp.OP_SETWILDBATTLE]))
        self.assertEqual(int.from_bytes(tutorial[wild+1:wild+3],"little"),0x0511)
        self.assertEqual(tutorial[wild+3],3)
        self.assertEqual(int.from_bytes(tutorial[wild+4:wild+6],"little"),0)
        self.assertEqual(tutorial[wild+6],comp.OP_DOWILDBATTLE)

        setflag=tutorial.index(bytes([comp.OP_SETFLAG]),wild+7)
        self.assertEqual(int.from_bytes(tutorial[setflag+1:setflag+3],"little"),0x0B2)

        trainer=bytes.fromhex(by_id["RC_SCRIPT_PORT_TRAINER"]["bytes_hex"])
        battle=trainer.index(bytes([comp.OP_TRAINERBATTLE]))
        self.assertEqual(trainer[battle+1],0)
        self.assertEqual(int.from_bytes(trainer[battle+2:battle+4],"little"),37)
        flag_offsets=[]; start=0
        while True:
            pos=trainer.find(bytes([comp.OP_SETFLAG]),start)
            if pos<0: break
            flag_offsets.append(int.from_bytes(trainer[pos+1:pos+3],"little")); start=pos+1
        self.assertIn(0x0B3,flag_offsets)

    def test_payload_links_trigger_trainer_and_marina_warp(self):
        comp=load(PAYLOAD_COMPILER,"payload")
        base=0x08940000
        p=comp.compile_payload(map_spec_path=MAP_SPEC,script_spec_path=SCRIPT_SPEC,base_address=base,primary_tileset_ptr=0x08120000,secondary_tileset_ptr=0x08130000)
        self.assertIn("RC_SCRIPT_WILD_TUTORIAL_TRIGGER",p["script_addresses"])
        self.assertIn("RC_SCRIPT_PORT_TRAINER",p["script_addresses"])
        self.assertIn("RC_DIALOGUE_WILD_TUTORIAL_TRIGGER",p["dialogue_addresses"])
        self.assertIn("RC_DIALOGUE_PORT_TRAINER_INTRO",p["dialogue_addresses"])
        warp_off=p["offsets"]["warp_events"]
        warp=p["bytes"][warp_off:warp_off+8]
        self.assertEqual(warp[6:8],bytes([52,3]))
        coord_off=p["offsets"]["coord_events"]
        coord=p["bytes"][coord_off:coord_off+16]
        script_ptr=int.from_bytes(coord[12:16],"little")
        self.assertEqual(script_ptr,p["script_addresses"]["RC_SCRIPT_WILD_TUTORIAL_TRIGGER"])

if __name__=="__main__":
    unittest.main()
