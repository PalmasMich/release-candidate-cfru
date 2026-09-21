import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"
ENCOUNTERS = ROOT / "content" / "cagliari_preview" / "encounters.yml"


def load_patcher():
    spec = importlib.util.spec_from_file_location("rc_preview_patcher_contract", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CagliariPreviewRuntimeContractTest(unittest.TestCase):
    def test_port_link_runtime_mix_matches_source_manifest(self):
        p = load_patcher()
        payload = json.loads(ENCOUNTERS.read_text(encoding="utf-8"))
        table = next(row for row in payload["tables"] if row["id"] == "RC_PORT_CONNECTION_GRASS")
        manifest = {slot["species"]: slot["weight"] for slot in table["slots"]}

        runtime = {}
        names = {
            p.MISTRILLO_SPECIES_ID: "SPECIES_RC_CAGLIARI_WILD_01",
            p.WINGULL_SPECIES_ID: "SPECIES_WINGULL",
            p.MEOWTH_SPECIES_ID: "SPECIES_MEOWTH",
        }
        for species, weight in zip(p.ROUTE1_PREVIEW_SPECIES, p.GRASS_SLOT_WEIGHTS):
            name = names[species]
            runtime[name] = runtime.get(name, 0) + weight

        self.assertEqual(runtime, manifest)

    def test_custom_encounter_owns_the_high_probability_slots(self):
        p = load_patcher()
        weighted_custom = sum(
            weight
            for species, weight in zip(p.ROUTE1_PREVIEW_SPECIES, p.GRASS_SLOT_WEIGHTS)
            if species == p.MISTRILLO_SPECIES_ID
        )
        self.assertEqual(weighted_custom, 60)
        self.assertEqual(p.ROUTE1_PREVIEW_SPECIES[:4], (p.MISTRILLO_SPECIES_ID,) * 4)

    def test_port_link_levels_stay_inside_manifest_bounds(self):
        p = load_patcher()
        payload = json.loads(ENCOUNTERS.read_text(encoding="utf-8"))
        table = next(row for row in payload["tables"] if row["id"] == "RC_PORT_CONNECTION_GRASS")
        bounds = {slot["species"]: (slot["min_level"], slot["max_level"]) for slot in table["slots"]}
        names = {
            p.MISTRILLO_SPECIES_ID: "SPECIES_RC_CAGLIARI_WILD_01",
            p.WINGULL_SPECIES_ID: "SPECIES_WINGULL",
            p.MEOWTH_SPECIES_ID: "SPECIES_MEOWTH",
        }
        for species, (minimum, maximum) in zip(p.ROUTE1_PREVIEW_SPECIES, p.ROUTE1_PREVIEW_LEVELS):
            expected_min, expected_max = bounds[names[species]]
            self.assertGreaterEqual(minimum, expected_min)
            self.assertLessEqual(maximum, expected_max)


if __name__ == "__main__":
    unittest.main()
