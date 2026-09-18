from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
CELL_COMPILER=ROOT/"scripts"/"compile_rc_map_cells.py"
SCRIPT_COMPILER=ROOT/"scripts"/"compile_rc_event_scripts.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"

DEPLOY=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DEPLOY_DISTRICT.json"
DEPLOY_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_DEPLOY_DISTRICT.json"
CASTELLO_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CASTELLO_ASCENT.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestDeployDistrictCustomMap(unittest.TestCase):
    def test_deploy_layout_and_cells_compile(self):
        map_comp=load(MAP_COMPILER,"map_comp")
        cell_comp=load(CELL_COMPILER,"cell_comp")
        ir=map_comp.compile_file(DEPLOY)
        cells=cell_comp.compile_file(DEPLOY)

        self.assertEqual(ir["id"],"RC_DEPLOY_DISTRICT")
        self.assertEqual(ir["dimensions"],{"width":22,"height":16})
        self.assertEqual(cells["map_bytes"],22*16*2)
        self.assertEqual(cells["profile"],"RC_DEPLOY_DISTRICT_GENERAL_BOOTSTRAP")

    def test_castello_gate_warps_to_deploy_district(self):
        comp=load(SCRIPT_COMPILER,"scripts")
        ir=comp.compile_file(CASTELLO_SCRIPTS)
        gate=next(x for x in ir["scripts"] if x["id"]=="RC_SCRIPT_DEPLOY_DISTRICT_GATE")
        linked=comp.link_script(
            gate,
            0x08980000,
            {},
            {"RC_DEPLOY_DISTRICT":(3,51)},
        )
        warp=linked.index(bytes([comp.OP_WARP]))
        self.assertEqual(linked[warp+1:warp+3],bytes([3,51]))
        self.assertEqual(linked[warp+3],0xFF)
        self.assertEqual(int.from_bytes(linked[warp+4:warp+6],"little"),11)
        self.assertEqual(int.from_bytes(linked[warp+6:warp+8],"little"),13)

    def test_go_no_go_trigger_sets_story_flag(self):
        comp=load(SCRIPT_COMPILER,"scripts")
        ir=comp.compile_file(DEPLOY_SCRIPTS)
        script=next(x for x in ir["scripts"] if x["id"]=="RC_SCRIPT_GO_NO_GO_START")
        raw=bytes.fromhex(script["bytes_hex"])
        pos=raw.index(bytes([comp.OP_SETFLAG]))
        self.assertEqual(int.from_bytes(raw[pos+1:pos+3],"little"),0x0B7)

    def test_deploy_payload_links_trigger_and_return_warp(self):
        comp=load(PAYLOAD_COMPILER,"payload")
        p=comp.compile_payload(
            map_spec_path=DEPLOY,
            script_spec_path=DEPLOY_SCRIPTS,
            base_address=0x08990000,
            primary_tileset_ptr=0x08120000,
            secondary_tileset_ptr=0x08130000,
        )
        self.assertIn("RC_SCRIPT_GO_NO_GO_START",p["script_addresses"])
        self.assertIn("RC_DIALOGUE_GO_NO_GO_START",p["dialogue_addresses"])

        warp_off=p["offsets"]["warp_events"]
        warp=p["bytes"][warp_off:warp_off+8]
        self.assertEqual(warp[6:8],bytes([50,3]))

        coord_off=p["offsets"]["coord_events"]
        coord=p["bytes"][coord_off:coord_off+16]
        self.assertEqual(
            int.from_bytes(coord[12:16],"little"),
            p["script_addresses"]["RC_SCRIPT_GO_NO_GO_START"],
        )

if __name__=="__main__": unittest.main()
