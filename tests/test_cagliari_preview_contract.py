from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


def load(name):
    return json.loads((CONTENT / name).read_text())


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

    def test_thick_preview_contains_required_playable_beats(self):
        events = {item["id"]: item for item in load("events.yml")["flow"]}
        required = (
            "RC_EVENT_ARRIVAL",
            "RC_EVENT_STARTER_ASSIGNMENT",
            "RC_EVENT_RIVAL_INTRO",
            "RC_EVENT_FIRST_WILD",
            "RC_EVENT_PORT_TRAINER",
            "RC_EVENT_DEPLOY_TEASER",
        )
        for event_id in required:
            self.assertIn(event_id, events)
            self.assertEqual(events[event_id]["scope"], "preview")

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

    def test_first_wild_contract_keeps_mistrillo_primary(self):
        first_wild = next(item for item in load("events.yml")["flow"] if item["id"] == "RC_EVENT_FIRST_WILD")
        self.assertEqual(first_wild["map"], "RC_PORT_CONNECTION")
        self.assertIn("60% Mistrillo", first_wild["preview_contract"])


if __name__ == "__main__":
    unittest.main()
