from pathlib import Path
import copy
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compile_rc_map.py"
SPEC = ROOT / "content" / "cagliari_preview" / "map_specs" / "RC_DELIVERY_HUB.json"


def load_compiler():
    spec = importlib.util.spec_from_file_location("rc_map_compiler", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RcMapCompilerTest(unittest.TestCase):
    def setUp(self):
        self.compiler = load_compiler()
        self.source = json.loads(SPEC.read_text(encoding="utf-8"))

    def test_delivery_hub_compiles_to_deterministic_ir(self):
        ir_a = self.compiler.compile_spec(copy.deepcopy(self.source))
        ir_b = self.compiler.compile_spec(copy.deepcopy(self.source))

        self.assertEqual(ir_a, ir_b)
        self.assertEqual(ir_a["format"], "RC_MAP_IR_V1")
        self.assertEqual(ir_a["id"], "RC_DELIVERY_HUB")
        self.assertEqual(ir_a["dimensions"], {"width": 18, "height": 12})
        self.assertFalse(ir_a["rom_ready"])
        self.assertEqual(len(ir_a["role_grid"]), 12)
        self.assertEqual(len(ir_a["role_grid"][0]), 18)

    def test_spawn_and_story_anchors_are_walkable(self):
        ir = self.compiler.compile_spec(copy.deepcopy(self.source))
        anchors = ir["anchors"]
        collision = ir["collision_grid"]

        for name in (
            "player_spawn",
            "delivery_lead",
            "rival",
            "starter_tartrek",
            "starter_frobyte",
            "starter_emberfox",
            "exit_marina",
        ):
            point = anchors[name]
            self.assertEqual(collision[point["y"]][point["x"]], 0, name)

    def test_three_starter_interactions_are_explicit(self):
        ir = self.compiler.compile_spec(copy.deepcopy(self.source))
        choices = {item["choice"] for item in ir["interactions"]}
        self.assertEqual(
            choices,
            {
                "SPECIES_RC_TURTLE_01",
                "SPECIES_RC_FROG_01",
                "SPECIES_RC_FIREFOX_01",
            },
        )

    def test_exit_is_story_gated(self):
        ir = self.compiler.compile_spec(copy.deepcopy(self.source))
        self.assertEqual(len(ir["warps"]), 1)
        warp = ir["warps"][0]
        self.assertEqual(warp["target_map"], "RC_CAGLIARI_MARINA")
        self.assertIn("RC_FLAG_RIVAL_INTRO_DONE", warp["requires"])

    def test_rejects_non_rectangular_layout(self):
        broken = copy.deepcopy(self.source)
        broken["layout"][2] = broken["layout"][2][:-1]
        with self.assertRaisesRegex(ValueError, "row 2 width"):
            self.compiler.compile_spec(broken)

    def test_rejects_anchor_on_blocked_tile(self):
        broken = copy.deepcopy(self.source)
        broken["anchors"]["player_spawn"] = {"x": 0, "y": 0}
        with self.assertRaisesRegex(ValueError, "blocked role"):
            self.compiler.compile_spec(broken)

    def test_requires_custom_tileset_contract(self):
        broken = copy.deepcopy(self.source)
        broken["art_contract"]["tileset"] = "VANILLA_OAK_LAB"
        with self.assertRaisesRegex(ValueError, "custom RC tileset"):
            self.compiler.compile_spec(broken)


if __name__ == "__main__":
    unittest.main()
