from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"discover_deploy_district_map_slot.py"

def load():
    s=importlib.util.spec_from_file_location("deploy_slot",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestDeployDistrictSlot(unittest.TestCase):
    def build_rom(self,m,duplicate=False):
        rom=bytearray(b"\x00"*0x5000)
        ptr=lambda o:(m.GBA_ROM_BASE+o).to_bytes(4,"little")

        layout=bytearray(b"\x00"*0x1C)
        layout[0:4]=(1).to_bytes(4,"little",signed=True)
        layout[4:8]=(1).to_bytes(4,"little",signed=True)
        layout[8:12]=ptr(0x1800);layout[12:16]=ptr(0x1A00)
        layout[16:20]=ptr(0x1C00);layout[20:24]=ptr(0x1E00)
        layout[24]=2;layout[25]=2
        rom[0x1000:0x101C]=layout

        def write(o):
            h=bytearray(b"\x00"*0x1C)
            h[0:4]=ptr(0x1000);h[4:8]=ptr(0x1200);h[8:12]=ptr(0x1300);h[12:16]=ptr(0x1400)
            h[16:18]=m.MUSIC_SEVII_ROUTE.to_bytes(2,"little")
            h[18:20]=(0x1234).to_bytes(2,"little")
            h[20]=m.MAPSEC_SEVII_ISLE_7;h[21]=0;h[22]=m.WEATHER_SUNNY;h[23]=m.MAP_TYPE_ROUTE
            h[24]=1;h[25]=m.HEADER_FLAGS;h[26]=0;h[27]=0
            rom[o:o+0x1C]=h

        write(0x400)
        if duplicate: write(0x500)
        return bytes(rom)

    def test_unique(self):
        m=load();r=m.analyze_rom(self.build_rom(m))
        self.assertTrue(r["safe_to_repoint"])
        self.assertEqual((r["map_group"],r["map_num"]),(3,51))
        self.assertNotEqual(r["candidates"][0]["connections_ptr"],0)

    def test_ambiguous(self):
        m=load();r=m.analyze_rom(self.build_rom(m,True))
        self.assertFalse(r["safe_to_repoint"])
        self.assertEqual(r["candidate_count"],2)

if __name__=="__main__": unittest.main()
