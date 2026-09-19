from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


def load(name):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def load_patcher():
    path = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"
    spec = importlib.util.spec_from_file_location("rc_preview_patcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CagliariPreviewContractTest(unittest.TestCase):
    def test_preview_flow_references_existing_maps_and_dialogue(self):
        maps = {item["id"] for item in load("maps.yml")["maps"]}
        dialogue = {item["id"] for item in load("dialogue.yml")["scenes"]}
        events = load("events.yml")
        flags = set(events["flags"])
        for event in events["flow"]:
            self.assertIn(event["map"], maps, event["id"])
            if "dialogue" in event:
                self.assertIn(event["dialogue"], dialogue, event["id"])
            for flag in event.get("requires", []) + event.get("sets", []):
                self.assertIn(flag, flags, event["id"])

    def test_thick_preview_is_ordered_and_playable_through_deploy_teaser(self):
        preview = [item for item in load("events.yml")["flow"] if item.get("scope") == "preview"]
        self.assertEqual(
            [item["id"] for item in preview],
            [
                "RC_EVENT_ARRIVAL",
                "RC_EVENT_STARTER_ASSIGNMENT",
                "RC_EVENT_RIVAL_INTRO",
                "RC_EVENT_FIRST_WILD",
                "RC_EVENT_PORT_TRAINER",
                "RC_EVENT_DEPLOY_TEASER",
            ],
        )
        produced = set()
        for event in preview:
            self.assertTrue(set(event.get("requires", ())).issubset(produced), event["id"])
            produced.update(event.get("sets", ()))
        self.assertIn("RC_FLAG_DEPLOY_TEASER_SEEN", produced)

    def test_rival_matrix_covers_each_preview_starter_once(self):
        matrix = load("trainers.yml")["rival"]["starter_matrix"]
        starters = {
            "SPECIES_RC_TURTLE_01",
            "SPECIES_RC_FROG_01",
            "SPECIES_RC_FIREFOX_01",
        }
        self.assertEqual(set(matrix), starters)
        self.assertEqual(set(matrix.values()), starters)
        for player, rival in matrix.items():
            self.assertNotEqual(player, rival)

    def test_rival_matrix_matches_rom_patch_species_ids(self):
        patcher = load_patcher()
        self.assertEqual(
            (patcher.TARTREK_SPECIES_ID, patcher.FROBYTE_SPECIES_ID, patcher.EMBERFOX_SPECIES_ID),
            (0x050E, 0x050F, 0x0510),
        )
        matrix = load("trainers.yml")["rival"]["starter_matrix"]
        self.assertEqual(matrix["SPECIES_RC_TURTLE_01"], "SPECIES_RC_FIREFOX_01")
        self.assertEqual(matrix["SPECIES_RC_FROG_01"], "SPECIES_RC_TURTLE_01")
        self.assertEqual(matrix["SPECIES_RC_FIREFOX_01"], "SPECIES_RC_FROG_01")

    def test_first_wild_contract_keeps_mistrillo_primary(self):
        first_wild = next(item for item in load("events.yml")["flow"] if item["id"] == "RC_EVENT_FIRST_WILD")
        self.assertEqual(first_wild["map"], "RC_PORT_CONNECTION")
        self.assertIn("60% Mistrillo", first_wild["preview_contract"])

    def test_port_link_rom_weights_are_exactly_60_25_15(self):
        patcher = load_patcher()
        totals = {}
        for species, weight in zip(patcher.ROUTE1_PREVIEW_SPECIES, patcher.GRASS_SLOT_WEIGHTS):
            totals[species] = totals.get(species, 0) + weight
        self.assertEqual(totals[patcher.MISTRILLO_SPECIES_ID], 60)
        self.assertEqual(totals[patcher.WINGULL_SPECIES_ID], 25)
        self.assertEqual(totals[patcher.MEOWTH_SPECIES_ID], 15)
        self.assertEqual(sum(totals.values()), 100)

    def test_visible_rom_identity_contains_required_preview_beats(self):
        patcher = load_patcher()
        replacements = [new for _, new in patcher.VISIBLE_TEXT_REPLACEMENTS]
        for phrase in (
            "Welcome to Release Candidate!",
            "Three resources are ready.",
            "KPI check: show velocity!",
            "PORT LINK\nCAGLIARI - MARINA PORTO",
            "MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE",
        ):
            self.assertIn(patcher.encode_text(phrase), replacements)


if __name__ == "__main__":
    unittest.main()
