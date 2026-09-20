from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
CELL_COMPILER=ROOT/"scripts"/"compile_rc_map_cells.py"
SCRIPT_COMPILER=ROOT/"scripts"/"compile_rc_event_scripts.py"
EVENTS_COMPILER=ROOT/"scripts"/"compile_rc_map_events.py"
PAYLOAD_COMPILER=ROOT/"scripts"/"compile_rc_map_payload.py"
CASTELLO=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CASTELLO_ASCENT.json"
MARINA=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CAGLIARI_MARINA.json"
MARINA_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CAGLIARI_MARINA.json"
CASTELLO_SCRIPTS=ROOT/"content"/"cagliari_preview"/"script_specs"/"RC_CASTELLO_ASCENT.json"

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

    def test_marina_gate_uses_flagged_blocker_and_real_warp(self):
        events=load(EVENTS_COMPILER,"events")
        ir=events.compile_file(MARINA)
        objects=bytes.fromhex(ir["object_events"]["bytes_hex"])
        gate=objects[5*0x18:6*0x18]
        self.assertEqual(gate[0],6)
        self.assertEqual(int.from_bytes(gate[20:22],"little"),0x0B6)

        linked=events.link_map_id_relocations(ir["warp_events"],events.load_map_ids())
        warp=linked[2*8:3*8]
        self.assertEqual(warp[5],0)
        self.assertEqual(warp[6:8],bytes([50,3]))

    def test_castello_payload_returns_to_marina(self):
        comp=load(PAYLOAD_COMPILER,"payload")
        p=comp.compile_payload(
            map_spec_path=CASTELLO,
            script_spec_path=CASTELLO_SCRIPTS,
            base_address=0x08970000,
            primary_tileset_ptr=0x08120000,
            secondary_tileset_ptr=0x08130000,
        )
        warp_off=p["offsets"]["warp_events"]
        warp=p["bytes"][warp_off:warp_off+8]
        self.assertEqual(warp[5],2)
        self.assertEqual(warp[6:8],bytes([52,3]))

if __name__=="__main__": unittest.main()
