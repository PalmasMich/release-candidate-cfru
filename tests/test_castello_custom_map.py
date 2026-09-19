from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
CELL_COMPILER=ROOT/"scripts"/"compile_rc_map_cells.py"
SCRIPT_COMPILER=ROOT/"scripts"/"compile_rc_event_scripts.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"
CASTELLO=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CASTELLO_ASCENT.json"
MARINA_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CAGLIARI_MARINA.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestCastelloCustomMap(unittest.TestCase):
    def test_castello_layout_and_cells_compile(self):
        map_comp=load(MAP_COMPILER,"map_comp")
        cell_comp=load(CELL_COMPILER,"cell_comp")
        ir=map_comp.compile_file(CASTELLO)
        cells=cell_comp.compile_file(CASTELLO)

        self.assertEqual(ir["id"],"RC_CASTELLO_ASCENT")
        self.assertEqual(ir["dimensions"],{"width":20,"height":18})
        self.assertEqual(cells["map_bytes"],20*18*2)
        self.assertEqual(cells["profile"],"RC_CASTELLO_GENERAL_BOOTSTRAP")
        self.assertIn("stairs",cells["role_counts"])

    def test_marina_gate_checks_unlock_flag_and_warps_to_castello(self):
        comp=load(SCRIPT_COMPILER,"scripts")
        ir=comp.compile_file(MARINA_SCRIPTS)
        gate=next(x for x in ir["scripts"] if x["id"]=="RC_SCRIPT_CASTELLO_GATE")
        raw=bytes.fromhex(gate["bytes_hex"])

        check=raw.index(bytes([comp.OP_CHECKFLAG]))
        self.assertEqual(int.from_bytes(raw[check+1:check+3],"little"),0x0B6)

        warp=raw.index(bytes([comp.OP_WARP]))
        self.assertEqual(raw[warp+3],0xFF)
        self.assertEqual(int.from_bytes(raw[warp+4:warp+6],"little"),10)
        self.assertEqual(int.from_bytes(raw[warp+6:warp+8],"little"),15)

        linked=comp.link_script(
            gate,
            0x08950000,
            {"RC_DIALOGUE_CASTELLO_LOCKED":0x08960000},
            {"RC_CASTELLO_ASCENT":(3,50)},
        )
        warp=linked.index(bytes([comp.OP_WARP]))
        self.assertEqual(linked[warp+1:warp+3],bytes([3,50]))

    def test_castello_payload_returns_to_marina(self):
        comp=load(PAYLOAD_COMPILER,"payload")
        p=comp.compile_payload(
            map_spec_path=CASTELLO,
            script_spec_path=None,
            base_address=0x08970000,
            primary_tileset_ptr=0x08120000,
            secondary_tileset_ptr=0x08130000,
        )
        warp_off=p["offsets"]["warp_events"]
        warp=p["bytes"][warp_off:warp_off+8]
        self.assertEqual(warp[6:8],bytes([52,3]))

if __name__=="__main__": unittest.main()
