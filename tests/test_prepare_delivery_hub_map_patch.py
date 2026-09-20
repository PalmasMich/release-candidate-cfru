from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "scripts" / "prepare_delivery_hub_map_patch.py"
DISCOVERY = ROOT / "scripts" / "discover_delivery_hub_map_slot.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrepareDeliveryHubMapPatchTest(unittest.TestCase):
    def build_rom(self, discovery):
        rom = bytearray(b"\x00" * 0x3000)

        def ptr(file_offset):
            return (discovery.GBA_ROM_BASE + file_offset).to_bytes(4, "little")

        layout = bytearray(b"\x00" * 0x1C)
        layout[0x00:0x04] = (11).to_bytes(4, "little", signed=True)
        layout[0x04:0x08] = (9).to_bytes(4, "little", signed=True)
        layout[0x08:0x0C] = ptr(0xB00)
        layout[0x0C:0x10] = ptr(0xC00)
        layout[0x10:0x14] = ptr(0xD00)
        layout[0x14:0x18] = ptr(0xE00)
        layout[0x18] = 2
        layout[0x19] = 2
        rom[0x800:0x800 + len(layout)] = layout

        offset = 0x180
        header = bytearray(b"\x00" * discovery.MAP_HEADER_SIZE)
        header[0x00:0x04] = ptr(0x800)
        header[0x04:0x08] = ptr(0x900)
        header[0x08:0x0C] = ptr(0xA00)
        header[0x0C:0x10] = (0).to_bytes(4, "little")
        header[0x10:0x12] = discovery.MUSIC_ROUTE3.to_bytes(2, "little")
        header[0x12:0x14] = (0x1234).to_bytes(2, "little")
        header[0x14] = discovery.MAPSEC_ROUTE19
        header[0x15] = 0
        header[0x16] = discovery.WEATHER_NONE
        header[0x17] = discovery.MAP_TYPE_INDOOR
        header[0x18] = 0
        header[0x19] = 0
        header[0x1A] = 0
        header[0x1B] = discovery.BATTLE_SCENE_NORMAL
        rom[offset:offset + discovery.MAP_HEADER_SIZE] = header
        return bytes(rom), offset

    def test_builds_non_mutating_plan_for_delivery_hub(self):
        prep = load(PREP, "delivery_hub_plan")
        discovery = load(DISCOVERY, "delivery_hub_discovery")
        rom, offset = self.build_rom(discovery)

        plan = prep.build_plan(rom)

        self.assertEqual(plan["format"], "RC_MAP_PATCH_PLAN_V1")
        self.assertEqual(plan["map_id"], "RC_DELIVERY_HUB")
        self.assertEqual(plan["slot"]["map_header_offset"], offset)
        self.assertEqual(plan["slot"]["map_group"], 27)
        self.assertEqual(plan["slot"]["map_num"], 0)
        self.assertFalse(plan["mutation_allowed"])
        self.assertEqual(plan["rollback"]["header_offset"], offset)
        self.assertIn(
            "RC_TILESET_CAGLIARI_INTERIORS_01",
            plan["required_before_mutation"][0],
        )
        compiled = plan["compiled_content"]
        self.assertEqual(compiled["event_script_format"], "RC_EVENT_SCRIPT_IR_V1")
        self.assertEqual(compiled["event_script_count"], 10)
        self.assertEqual(compiled["map_events_format"], "RC_MAP_EVENTS_IR_V1")
        self.assertEqual(compiled["map_events_bytes"], 224)
        self.assertGreater(compiled["dialogue_bytes"], 0)
        self.assertGreater(compiled["minimum_payload_bytes"], 112)
        self.assertEqual(
            set(compiled["bound_script_ids"]),
            {
                "RC_SCRIPT_DELIVERY_LEAD",
                "RC_SCRIPT_KPI_RIVAL",
                "RC_SCRIPT_STARTER_TARTREK",
                "RC_SCRIPT_STARTER_FROBYTE",
                "RC_SCRIPT_STARTER_EMBERFOX",
                "RC_SCRIPT_HUB_ARRIVAL",
                "RC_SCRIPT_HUB_ANALYST",
                "RC_SCRIPT_HUB_DEVELOPER",
                "RC_SCRIPT_HUB_PM",
                "RC_SCRIPT_HUB_EXIT_GATE",
            },
        )

    def test_plan_carries_original_header_pointers_for_rollback(self):
        prep = load(PREP, "delivery_hub_plan")
        discovery = load(DISCOVERY, "delivery_hub_discovery")
        rom, _ = self.build_rom(discovery)

        plan = prep.build_plan(rom)

        self.assertEqual(
            plan["slot"]["original_layout_ptr"],
            plan["rollback"]["layout_ptr"],
        )
        self.assertEqual(
            plan["slot"]["original_events_ptr"],
            plan["rollback"]["events_ptr"],
        )
        self.assertEqual(
            plan["slot"]["original_scripts_ptr"],
            plan["rollback"]["scripts_ptr"],
        )

    def test_blocks_when_map_header_is_not_unique(self):
        prep = load(PREP, "delivery_hub_plan")
        discovery = load(DISCOVERY, "delivery_hub_discovery")
        rom, offset = self.build_rom(discovery)
        payload = bytearray(rom)
        payload[offset + 0x100:offset + 0x100 + discovery.MAP_HEADER_SIZE] = payload[
            offset:offset + discovery.MAP_HEADER_SIZE
        ]

        with self.assertRaisesRegex(ValueError, "not uniquely safe"):
            prep.build_plan(bytes(payload))


if __name__ == "__main__":
    unittest.main()
