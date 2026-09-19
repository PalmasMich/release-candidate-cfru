from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"discover_rc_tail_free_space.py"

def load():
    s=importlib.util.spec_from_file_location("free",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestTailFreeSpace(unittest.TestCase):
    def test_allocates_only_inside_terminal_ff_run(self):
        m=load()
        data=b"ABC"+b"\xFF"*200
        r=m.discover_tail(data,100)
        self.assertTrue(r["safe_to_allocate"])
        self.assertGreaterEqual(r["aligned_start"],3)
        self.assertLessEqual(r["allocation_end"],len(data)-m.MIN_GUARD)

    def test_blocks_when_tail_is_too_small(self):
        m=load()
        r=m.discover_tail(b"ABC"+b"\xFF"*40,16)
        self.assertFalse(r["safe_to_allocate"])

    def test_never_treats_internal_ff_run_as_free_tail(self):
        m=load()
        data=b"A"+b"\xFF"*500+b"B"+b"\xFF"*20
        r=m.discover_tail(data,32)
        self.assertFalse(r["safe_to_allocate"])
        self.assertEqual(r["raw_tail_start"],len(data)-20)

if __name__=="__main__": unittest.main()
