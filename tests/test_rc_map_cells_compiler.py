from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"compile_rc_map_cells.py"
SPEC=ROOT/"content"/"cagliari_preview"/"map_specs"/"RC_DELIVERY_HUB.json"

def load():
    spec=importlib.util.spec_from_file_location("cells",SCRIPT)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class TestCells(unittest.TestCase):
    def test_compiles_18x12_cells(self):
        m=load(); ir=m.compile_file(SPEC)
        self.assertEqual(ir["map_bytes"],18*12*2)
        self.assertEqual(ir["border_bytes"],8)
        self.assertEqual(ir["format"],"RC_MAP_CELLS_IR_V1")

    def test_floor_and_wall_encoding(self):
        m=load()
        self.assertEqual(m.encode_cell(0x001,0,3),0x3001)
        self.assertEqual(m.encode_cell(0x020,1,0),0x0420)

    def test_profile_covers_all_roles(self):
        m=load(); ir=m.compile_file(SPEC)
        self.assertEqual(sum(ir["role_counts"].values()),216)
        self.assertIn("walkable_floor",ir["role_counts"])
        self.assertIn("wall",ir["role_counts"])

if __name__=="__main__": unittest.main()
