from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
CELL_COMPILER=ROOT/"scripts"/"compile_rc_map_cells.py"
SCRIPT_COMPILER=ROOT/"scripts"/"compile_rc_event_scripts.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"
ROOM=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DEPLOY_ROOM.json"
ROOM_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DEPLOY_ROOM.json"
DISTRICT_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DEPLOY_DISTRICT.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestDeployRoomBoss(unittest.TestCase):
    def test_room_layout_and_payload_compile(self):
        map_comp=load(MAP_COMPILER,"map_comp")
        cell_comp=load(CELL_COMPILER,"cell_comp")
        payload=load(PAYLOAD_COMPILER,"payload")

        ir=map_comp.compile_file(ROOM)
        cells=cell_comp.compile_file(ROOM)
        self.assertEqual(ir["dimensions"],{"width":16,"height":12})
        self.assertEqual(cells["map_bytes"],16*12*2)
        self.assertEqual(cells["profile"],"RC_DEPLOY_ROOM_HOUSE2_BOOTSTRAP")

        p=payload.compile_payload(
            map_spec_path=ROOM,
            script_spec_path=ROOM_SCRIPTS,
            base_address=0x089A0000,
            primary_tileset_ptr=0x08100000,
            secondary_tileset_ptr=0x08110000,
        )
        self.assertIn("RC_SCRIPT_RELEASE_MANAGER",p["script_addresses"])
        self.assertIn("RC_DIALOGUE_RELEASE_MANAGER_INTRO",p["dialogue_addresses"])
        self.assertIn("RC_DIALOGUE_DEPLOY_COMPLETE",p["dialogue_addresses"])

    def test_release_manager_sets_both_completion_flags(self):
        comp=load(SCRIPT_COMPILER,"scripts")
        ir=comp.compile_file(ROOM_SCRIPTS)
        boss=next(x for x in ir["scripts"] if x["id"]=="RC_SCRIPT_RELEASE_MANAGER")
        raw=bytes.fromhex(boss["bytes_hex"])

        battle=raw.index(bytes([comp.OP_TRAINERBATTLE]))
        self.assertEqual(int.from_bytes(raw[battle+2:battle+4],"little"),38)

        flags=[]
        start=0
        while True:
            pos=raw.find(bytes([comp.OP_SETFLAG]),start)
            if pos<0: break
            flags.append(int.from_bytes(raw[pos+1:pos+3],"little"))
            start=pos+1

        self.assertEqual(flags,[0x0B8,0x0B9])

    def test_release_gate_requires_go_no_go_and_warps_to_room(self):
        comp=load(SCRIPT_COMPILER,"scripts")
        ir=comp.compile_file(DISTRICT_SCRIPTS)
        gate=next(x for x in ir["scripts"] if x["id"]=="RC_SCRIPT_RELEASE_GATE")
        raw=bytes.fromhex(gate["bytes_hex"])

        check=raw.index(bytes([comp.OP_CHECKFLAG]))
        self.assertEqual(int.from_bytes(raw[check+1:check+3],"little"),0x0B7)

        linked=comp.link_script(
            gate,
            0x089B0000,
            {"RC_DIALOGUE_DEPLOY_ROOM_LOCKED":0x089C0000},
            {"RC_DEPLOY_ROOM":(18,1)},
        )
        warp=linked.index(bytes([comp.OP_WARP]))
        self.assertEqual(linked[warp+1:warp+3],bytes([18,1]))
        self.assertEqual(int.from_bytes(linked[warp+4:warp+6],"little"),8)
        self.assertEqual(int.from_bytes(linked[warp+6:warp+8],"little"),9)

if __name__=="__main__": unittest.main()
