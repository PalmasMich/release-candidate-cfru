from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compile_rc_map_events.py"
SPEC = ROOT / "content" / "cagliari_preview" / "map_specs" / "RC_DELIVERY_HUB.json"


def load_compiler():
    spec = importlib.util.spec_from_file_location("rc_map_events_compiler", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RcMapEventsCompilerTest(unittest.TestCase):
    def setUp(self):
        self.compiler = load_compiler()
        self.ir = self.compiler.compile_file(SPEC)

    def test_compiles_expected_fire_red_event_counts_and_sizes(self):
        self.assertEqual(self.ir["format"], "RC_MAP_EVENTS_IR_V1")
        self.assertEqual(self.ir["map"], "RC_DELIVERY_HUB")

        self.assertEqual(self.ir["object_events"]["count"], 6)
        self.assertEqual(self.ir["object_events"]["size"], 6 * 0x18)

        self.assertEqual(self.ir["warp_events"]["count"], 1)
        self.assertEqual(self.ir["warp_events"]["size"], 8)

        self.assertEqual(self.ir["coord_events"]["count"], 1)
        self.assertEqual(self.ir["coord_events"]["size"], 16)
        self.assertEqual(self.ir["bg_events"]["count"], 3)
        self.assertEqual(self.ir["bg_events"]["size"], 3 * 12)

        self.assertEqual(self.ir["map_events_header"]["size"], 20)
        self.assertEqual(self.ir["total_bytes"], 224)

    def test_object_event_scripts_are_relocatable(self):
        relocs = self.ir["object_events"]["relocations"]
        self.assertEqual(len(relocs), 6)
        self.assertEqual(
            {item["symbol"] for item in relocs},
            {
                "RC_SCRIPT_DELIVERY_LEAD",
                "RC_SCRIPT_KPI_RIVAL",
                "RC_SCRIPT_HUB_ANALYST",
                "RC_SCRIPT_HUB_DEVELOPER",
                "RC_SCRIPT_HUB_PM",
                "RC_SCRIPT_HUB_EXIT_GATE",
            },
        )
        self.assertTrue(all(item["size"] == 4 for item in relocs))

    def test_three_starter_bg_events_bind_to_three_scripts(self):
        relocs = self.ir["bg_events"]["relocations"]
        self.assertEqual(
            {item["symbol"] for item in relocs},
            {
                "RC_SCRIPT_STARTER_TARTREK",
                "RC_SCRIPT_STARTER_FROBYTE",
                "RC_SCRIPT_STARTER_EMBERFOX",
            },
        )

    def test_exit_blocker_is_hidden_by_the_rival_intro_flag(self):
        raw = bytes.fromhex(self.ir["object_events"]["bytes_hex"])
        gate = raw[5 * 0x18:6 * 0x18]
        self.assertEqual(gate[0], 6)
        self.assertEqual(int.from_bytes(gate[20:22], "little"), 0x0B1)

    def test_warp_target_resolves_to_reserved_marina_slot(self):
        relocs = self.ir["warp_events"]["relocations"]
        self.assertEqual(len(relocs), 1)
        self.assertEqual(relocs[0]["kind"], "map_id")
        self.assertEqual(relocs[0]["size"], 2)
        self.assertEqual(relocs[0]["symbol"], "RC_CAGLIARI_MARINA")
        self.assertEqual(relocs[0]["target_anchor"], "delivery_hub_entrance")

        linked = self.compiler.link_map_id_relocations(
            self.ir["warp_events"],
            self.compiler.load_map_ids(),
        )
        relocation = relocs[0]
        self.assertEqual(
            linked[relocation["offset"]:relocation["offset"] + 2],
            bytes([52, 3]),
        )

    def test_map_events_header_links_all_populated_event_blocks(self):
        header = bytes.fromhex(self.ir["map_events_header"]["bytes_hex"])
        self.assertEqual(header[0:4], bytes([6, 1, 1, 3]))
        self.assertEqual(header[12:16], b"\x00\x00\x00\x00")
        self.assertEqual(len(self.ir["map_events_header"]["relocations"]), 4)


if __name__ == "__main__":
    unittest.main()
