from pathlib import Path
import importlib.util, unittest

ROOT=Path(__file__).resolve().parents[1]
PATCHER=ROOT/"scripts"/"patch_rc_custom_maps.py"
HUB_DISC=ROOT/"scripts"/"discover_delivery_hub_map_slot.py"
MARINA_DISC=ROOT/"scripts"/"discover_marina_map_slot.py"
PORT_DISC=ROOT/"scripts"/"discover_port_link_map_slot.py"
ENTRY=ROOT/"scripts"/"patch_pallet_lab_entry_to_delivery_hub.py"
WILD=ROOT/"scripts"/"patch_port_link_wild_header.py"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class TestCustomMapsPatch(unittest.TestCase):
    def fixture(self):
        hub=load(HUB_DISC,"hub")
        marina=load(MARINA_DISC,"marina")
        port=load(PORT_DISC,"port")
        entry=load(ENTRY,"entry")
        wild=load(WILD,"wild")
        rom=bytearray(b"\x00"*0x10000)
        ptr=lambda o:(0x08000000+o).to_bytes(4,"little")

        rom[0x500:0x500+len(entry.SOURCE)]=entry.SOURCE
        rom[0x600:0x600+len(entry.SOURCE)]=entry.SOURCE

        # Preview-patched Route 1 encounter chain: mons -> info -> header.
        mon_offset=0x700
        info_offset=0x780
        wild_header_offset=0x7A0
        rom[mon_offset:mon_offset+len(wild.ROUTE1_PATCHED_WILD_SIGNATURE)]=wild.ROUTE1_PATCHED_WILD_SIGNATURE
        rom[info_offset:info_offset+4]=bytes([wild.ROUTE1_ENCOUNTER_RATE,0,0,0])
        rom[info_offset+4:info_offset+8]=ptr(mon_offset)
        rom[wild_header_offset]=wild.ROUTE1_GROUP
        rom[wild_header_offset+1]=wild.ROUTE1_MAP
        rom[wild_header_offset+2:wild_header_offset+4]=b"\x00\x00"
        rom[wild_header_offset+4:wild_header_offset+8]=ptr(info_offset)
        rom[wild_header_offset+8:wild_header_offset+20]=b"\x00"*12

        # Delivery Hub reserved source slot.
        hl=bytearray(b"\x00"*0x1C)
        hl[0:4]=(11).to_bytes(4,"little",signed=True)
        hl[4:8]=(9).to_bytes(4,"little",signed=True)
        hl[8:12]=ptr(0x3000);hl[12:16]=ptr(0x3200)
        hl[16:20]=ptr(0x3400);hl[20:24]=ptr(0x3600)
        hl[24]=2;hl[25]=2
        rom[0x2000:0x201C]=hl

        hh=bytearray(b"\x00"*0x1C)
        hh[0:4]=ptr(0x2000);hh[4:8]=ptr(0x2400);hh[8:12]=ptr(0x2500)
        hh[12:16]=(0).to_bytes(4,"little")
        hh[16:18]=hub.MUSIC_ROUTE3.to_bytes(2,"little")
        hh[18:20]=(0x1111).to_bytes(2,"little")
        hh[20]=hub.MAPSEC_ROUTE19;hh[21]=0;hh[22]=hub.WEATHER_NONE;hh[23]=hub.MAP_TYPE_INDOOR
        hh[24]=0;hh[25]=0;hh[26]=0;hh[27]=hub.BATTLE_SCENE_NORMAL
        rom[0x1000:0x101C]=hh

        # Marina reserved source slot.
        ml=bytearray(b"\x00"*0x1C)
        ml[0:4]=(84).to_bytes(4,"little",signed=True)
        ml[4:8]=(20).to_bytes(4,"little",signed=True)
        ml[8:12]=ptr(0x3800);ml[12:16]=ptr(0x3A00)
        ml[16:20]=ptr(0x3C00);ml[20:24]=ptr(0x3E00)
        ml[24]=2;ml[25]=2
        rom[0x2200:0x221C]=ml

        mh=bytearray(b"\x00"*0x1C)
        mh[0:4]=ptr(0x2200);mh[4:8]=ptr(0x2600);mh[8:12]=ptr(0x2700)
        mh[12:16]=(0).to_bytes(4,"little")
        mh[16:18]=marina.MUSIC_SEVII_ROUTE.to_bytes(2,"little")
        mh[18:20]=(0x2222).to_bytes(2,"little")
        mh[20]=marina.MAPSEC_SEVII_ISLE_8;mh[21]=0;mh[22]=marina.WEATHER_SUNNY;mh[23]=marina.MAP_TYPE_ROUTE
        mh[24]=1;mh[25]=marina.HEADER_FLAGS;mh[26]=0;mh[27]=0
        rom[0x1100:0x111C]=mh

        # Port Link reserved source slot.
        pl=bytearray(b"\x00"*0x1C)
        pl[0:4]=(24).to_bytes(4,"little",signed=True)
        pl[4:8]=(60).to_bytes(4,"little",signed=True)
        pl[8:12]=ptr(0x4000);pl[12:16]=ptr(0x4200)
        pl[16:20]=ptr(0x4400);pl[20:24]=ptr(0x4600)
        pl[24]=2;pl[25]=2
        rom[0x2800:0x281C]=pl

        ph=bytearray(b"\x00"*0x1C)
        ph[0:4]=ptr(0x2800);ph[4:8]=ptr(0x2A00);ph[8:12]=ptr(0x2B00)
        ph[12:16]=(0).to_bytes(4,"little")
        ph[16:18]=port.MUSIC_SEVII_ROUTE.to_bytes(2,"little")
        ph[18:20]=(0x3333).to_bytes(2,"little")
        ph[20]=port.MAPSEC_SEVII_ISLE_9;ph[21]=0;ph[22]=port.WEATHER_SUNNY;ph[23]=port.MAP_TYPE_ROUTE
        ph[24]=1;ph[25]=port.HEADER_FLAGS;ph[26]=0;ph[27]=0
        rom[0x1200:0x121C]=ph

        rom[0xC000:]=b"\xFF"*(len(rom)-0xC000)
        return bytes(rom)

    def test_installs_three_maps_and_repoints_entry_atomically(self):
        patcher=load(PATCHER,"patcher")
        entry=load(ENTRY,"entry")
        original=self.fixture()
        patched,e=patcher.patch_bytes(original)

        self.assertEqual(len(patched),len(original))
        self.assertEqual(patched.count(entry.SOURCE),0)
        self.assertEqual(patched.count(entry.TARGET),2)
        self.assertEqual(patched[e["wild_header_offset"]],3)
        self.assertEqual(patched[e["wild_header_offset"]+1],53)

        self.assertEqual(int.from_bytes(patched[0x1000:0x1004],"little"),e["hub_layout_ptr"])
        self.assertEqual(int.from_bytes(patched[0x1004:0x1008],"little"),e["hub_events_ptr"])
        self.assertEqual(int.from_bytes(patched[0x1100:0x1104],"little"),e["marina_layout_ptr"])
        self.assertEqual(int.from_bytes(patched[0x1104:0x1108],"little"),e["marina_events_ptr"])
        self.assertEqual(int.from_bytes(patched[0x1200:0x1204],"little"),e["port_layout_ptr"])
        self.assertEqual(int.from_bytes(patched[0x1204:0x1208],"little"),e["port_events_ptr"])

        self.assertGreaterEqual(e["hub_payload_offset"],0xC000)
        self.assertGreater(e["marina_payload_offset"],e["hub_payload_offset"])
        self.assertGreater(e["port_payload_offset"],e["marina_payload_offset"])

    def test_blocks_without_guarded_tail_space(self):
        patcher=load(PATCHER,"patcher")
        data=bytearray(self.fixture())
        data[0xC000:]=b"\x00"*(len(data)-0xC000)
        with self.assertRaisesRegex(ValueError,"trailing ROM space"):
            patcher.patch_bytes(bytes(data))

if __name__=="__main__": unittest.main()
