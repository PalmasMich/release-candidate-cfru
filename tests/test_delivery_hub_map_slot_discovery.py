from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "discover_delivery_hub_map_slot.py"


def load_module():
    spec = importlib.util.spec_from_file_location("delivery_hub_slot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeliveryHubMapSlotDiscoveryTest(unittest.TestCase):
    def build_header(self, module, *, offset=0x100, duplicate=False):
        rom = bytearray(b"\x00" * 0x2000)

        def ptr(file_offset):
            return (module.GBA_ROM_BASE + file_offset).to_bytes(4, "little")

        def write_header(at):
            header = bytearray(b"\x00" * module.MAP_HEADER_SIZE)
            header[0x00:0x04] = ptr(0x800)
            header[0x04:0x08] = ptr(0x900)
            header[0x08:0x0C] = ptr(0xA00)
            header[0x0C:0x10] = (0).to_bytes(4, "little")
            header[0x10:0x12] = module.MUSIC_ROUTE3.to_bytes(2, "little")
            header[0x12:0x14] = (0x1234).to_bytes(2, "little")
            header[0x14] = module.MAPSEC_ROUTE19
            header[0x15] = 0
            header[0x16] = module.WEATHER_NONE
            header[0x17] = module.MAP_TYPE_INDOOR
            header[0x18] = 0
            header[0x19] = 0
            header[0x1A] = 0
            header[0x1B] = module.BATTLE_SCENE_NORMAL
            rom[at:at + module.MAP_HEADER_SIZE] = header

        write_header(offset)
        if duplicate:
            write_header(offset + 0x100)
        return bytes(rom)

    def test_finds_unique_unused_house_header(self):
        module = load_module()
        data = self.build_header(module)

        report = module.analyze_rom(data)

        self.assertTrue(report["safe_to_repoint"])
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["candidates"][0]["offset"], 0x100)
        self.assertEqual(report["map_group"], 27)
        self.assertEqual(report["map_num"], 0)

    def test_rejects_ambiguous_headers(self):
        module = load_module()
        data = self.build_header(module, duplicate=True)

        report = module.analyze_rom(data)

        self.assertFalse(report["safe_to_repoint"])
        self.assertEqual(report["candidate_count"], 2)

    def test_rejects_non_null_connections(self):
        module = load_module()
        payload = bytearray(self.build_header(module))
        payload[0x10C:0x110] = (module.GBA_ROM_BASE + 0xB00).to_bytes(4, "little")

        report = module.analyze_rom(bytes(payload))

        self.assertFalse(report["safe_to_repoint"])
        self.assertEqual(report["candidate_count"], 0)

    def test_rejects_running_enabled_variant(self):
        module = load_module()
        payload = bytearray(self.build_header(module))
        payload[0x119] = 0x02

        report = module.analyze_rom(bytes(payload))

        self.assertEqual(report["candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
