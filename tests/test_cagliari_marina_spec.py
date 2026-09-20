from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
MAP_COMPILER=ROOT/"scripts"/"compile_rc_map.py"
EVENT_COMPILER=ROOT/"scripts"/"compile_rc_map_events.py"
SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_CAGLIARI_MARINA.json"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestMarina(unittest.TestCase):
    def test_marina_spec_is_permanent_and_rectangular(self):
        m=load(MAP_COMPILER,"map_compiler")
        ir=m.compile_file(SPEC)
        self.assertEqual(ir["id"],"RC_CAGLIARI_MARINA")
        self.assertEqual(ir["dimensions"],{"width":24,"height":16})
        self.assertEqual(ir["tileset_contract"],"RC_TILESET_CAGLIARI_EXTERIORS_01")

    def test_marina_return_warp_resolves_to_delivery_hub(self):
        m=load(EVENT_COMPILER,"events")
        ir=m.compile_file(SPEC)
        self.assertEqual(ir["warp_events"]["count"],3)
        linked=m.link_map_id_relocations(ir["warp_events"],m.load_map_ids())
        rel=next(
            item for item in ir["warp_events"]["relocations"]
            if item["owner"] == "RC_WARP_MARINA_TO_DELIVERY"
        )
        self.assertEqual(linked[rel["offset"]:rel["offset"]+2],bytes([0,27]))

if __name__=="__main__": unittest.main()
