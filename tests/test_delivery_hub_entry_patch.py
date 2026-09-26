from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"patch_pallet_lab_entry_to_delivery_hub.py"

def load():
    s=importlib.util.spec_from_file_location("entry",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestEntry(unittest.TestCase):
    def test_repoints_exactly_two_coordinate_warps(self):
        m=load()
        data=b"A"+m.SOURCE+b"B"+m.SOURCE+b"C"
        patched,pos=m.patch_bytes(data)
        self.assertEqual(pos,[1,1+len(m.SOURCE)+1])
        self.assertEqual(patched.count(m.TARGET),2)
        self.assertEqual(patched.count(m.SOURCE),0)
        self.assertEqual(len(patched),len(data))

    def test_blocks_single_match(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"expected 2"):
            m.patch_bytes(m.SOURCE)

    def test_blocks_ambiguous_extra_match(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"found 3"):
            m.patch_bytes(m.SOURCE*3)

if __name__=="__main__": unittest.main()
