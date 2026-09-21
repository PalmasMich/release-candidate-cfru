#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"


class CagliariPlayablePreviewContractTests(unittest.TestCase):
    def _json(self, name):
        return json.loads((CONTENT / name).read_text(encoding="utf-8"))

    def test_dialogue_covers_the_playable_vertical_slice(self):
        scenes = {scene["id"]: scene for scene in self._json("dialogue.yml")["scenes"]}
        required = {
            "RC_DIALOGUE_OPENING",
            "RC_DIALOGUE_STARTER",
            "RC_DIALOGUE_RIVAL_INTRO",
            "RC_DIALOGUE_WILD_TUTORIAL_TRIGGER",
            "RC_DIALOGUE_PORT_TRAINER_INTRO",
            "RC_DIALOGUE_PORT_TRAINER_OUTRO",
            "RC_DIALOGUE_DEPLOY_TEASER",
        }
        self.assertTrue(required.issubset(scenes))
        rival_text = " ".join(scenes["RC_DIALOGUE_RIVAL_INTRO"]["lines"]).lower()
        self.assertIn("kpi", rival_text)
        self.assertIn("velocity", rival_text)

    def test_port_link_has_custom_encounter_and_weights_sum_to_100(self):
        tables = self._json("encounters.yml")["tables"]
        port = next(table for table in tables if table["id"] == "RC_PORT_CONNECTION_GRASS")
        self.assertEqual(sum(slot["weight"] for slot in port["slots"]), 100)
        custom = next(slot for slot in port["slots"] if slot["species"] == "SPECIES_RC_CAGLIARI_WILD_01")
        self.assertEqual(custom["weight"], 60)
        self.assertGreaterEqual(custom["min_level"], 3)

    def test_binary_preview_patch_exposes_required_identity_beats(self):
        source = PATCHER.read_text(encoding="utf-8")
        for visible_beat in (
            "Welcome to Release Candidate!",
            "DELIVERY HUB - CAGLIARI",
            "KPI check: show velocity!",
            "PORT LINK\\nCAGLIARI - MARINA PORTO",
            "MISTRILLO is in this grass.",
            "DEPLOY BLOCKED - CHECK SCOPE",
        ):
            self.assertIn(visible_beat, source)

    def test_preview_patch_wires_three_original_starters(self):
        source = PATCHER.read_text(encoding="utf-8")
        for species in (
            "TARTREK_SPECIES_ID",
            "FROBYTE_SPECIES_ID",
            "EMBERFOX_SPECIES_ID",
        ):
            self.assertIn(species, source)
        self.assertIn("patch_preview_starters", source)
        self.assertIn("patch_oak_lab_rival_parties", source)


if __name__ == "__main__":
    unittest.main()
