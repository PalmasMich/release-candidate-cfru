from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"patch_port_link_wild_header.py"

def load():
    s=importlib.util.spec_from_file_location("wild_header",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestPortLinkWildHeader(unittest.TestCase):
    def fixture(self, *, patched=True, duplicate_header=False):
        m=load()
        data=bytearray(b"\x00"*0x1000)
        mon_offset=0x300
        info_offset=0x200
        header_offset=0x100

        signature=m.ROUTE1_PATCHED_WILD_SIGNATURE if patched else m.ROUTE1_WILD_SIGNATURE
        data[mon_offset:mon_offset+len(signature)]=signature
        data[info_offset:info_offset+4]=bytes([m.ROUTE1_ENCOUNTER_RATE,0,0,0])
        data[info_offset+4:info_offset+8]=(m.GBA_ROM_BASE+mon_offset).to_bytes(4,"little")

        def write_header(offset):
            data[offset]=m.ROUTE1_GROUP
            data[offset+1]=m.ROUTE1_MAP
            data[offset+2:offset+4]=b"\x00\x00"
            data[offset+4:offset+8]=(m.GBA_ROM_BASE+info_offset).to_bytes(4,"little")
            data[offset+8:offset+20]=b"\x00"*12

        write_header(header_offset)
        if duplicate_header:
            write_header(0x180)
        return bytes(data),header_offset

    def test_repoints_patched_preview_header_to_port_link(self):
        m=load()
        original,h=self.fixture(patched=True)
        patched,report=m.patch_bytes(original)
        self.assertTrue(report["safe"])
        self.assertEqual(report["signature_state"],"patched")
        self.assertEqual(patched[h],3)
        self.assertEqual(patched[h+1],53)
        self.assertEqual(len(patched),len(original))

    def test_supports_vanilla_signature_for_diagnostics(self):
        m=load()
        original,h=self.fixture(patched=False)
        patched,report=m.patch_bytes(original)
        self.assertEqual(report["signature_state"],"vanilla")
        self.assertEqual(patched[h+1],53)

    def test_blocks_ambiguous_headers(self):
        m=load()
        original,_=self.fixture(duplicate_header=True)
        with self.assertRaisesRegex(ValueError,"expected one Route 1 WildPokemonHeader"):
            m.patch_bytes(original)

if __name__=="__main__":
    unittest.main()
