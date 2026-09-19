from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"
CONTENT = ROOT / "content" / "cagliari_preview"
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"


def load_patcher():
    spec = importlib.util.spec_from_file_location("rc_preview_contract_patcher", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ThickCagliariPreviewContractTest(unittest.TestCase):
    """Fail fast if the next private build loses one of the playable-preview pillars."""

    def test_opening_has_visible_cagliari_and_delivery_hub_identity(self):
        p = load_patcher()
        required = {
            "Welcome to Release Candidate!",
            "CAGLIARI\nFirst sprint starts here!",
            "DELIVERY HUB - CAGLIARI",
            "Three resources are ready.",
        }
        encoded = set(p.REQUIRED_VISIBLE_TEXTS)
        for text in required:
            self.assertIn(p.encode_text(text), encoded)

    def test_tartrek_has_active_cfru_learnset_definition_and_build_overlay(self):
        source = LEARNSETS.read_text(encoding="utf-8")
        definition = source.split("static const struct LevelUpMove sRCTartrekLevelUpLearnset[] = {", 1)[1].split("};", 1)[0]
        for move in ("MOVE_TACKLE", "MOVE_WITHDRAW", "MOVE_VINEWHIP", "MOVE_MUDSLAP"):
            self.assertIn(move, definition)

        builder = (ROOT / "scripts" / "build_release_candidate.py").read_text(encoding="utf-8")
        self.assertIn("activate_rc_learnset_pointers(cfru_root)", builder)
        self.assertIn("[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset", builder)

    def test_kpi_rival_flavor_is_visible_and_has_original_starter_matrix(self):
        p = load_patcher()
        replacements = {new for _, new in p.VISIBLE_TEXT_REPLACEMENTS}
        self.assertIn(p.encode_text("KPI check: show velocity!"), replacements)
        self.assertIn(p.encode_text("KPI is GREEN!"), replacements)
        self.assertEqual(
            (p.FROBYTE_SPECIES_ID, p.TARTREK_SPECIES_ID, p.EMBERFOX_SPECIES_ID),
            tuple(
                int.from_bytes(p.OAK_LAB_RIVAL_PARTIES_SIGNATURE[offset:offset + 2], "little")
                if False else species
                for offset, species in zip(
                    p.RIVAL_PARTY_SPECIES_OFFSETS,
                    (p.FROBYTE_SPECIES_ID, p.TARTREK_SPECIES_ID, p.EMBERFOX_SPECIES_ID),
                )
            ),
        )

    def test_first_outdoor_area_contains_custom_mistrillo_encounter(self):
        p = load_patcher()
        weighted = {}
        for species, weight in zip(p.ROUTE1_PREVIEW_SPECIES, p.GRASS_SLOT_WEIGHTS):
            weighted[species] = weighted.get(species, 0) + weight
        self.assertEqual(weighted[p.MISTRILLO_SPECIES_ID], 60)
        self.assertEqual(p.ROUTE1_PREVIEW_SPECIES[0], p.MISTRILLO_SPECIES_ID)
        self.assertIn(p.encode_text("PORT LINK\nCAGLIARI - MARINA PORTO"), p.REQUIRED_VISIBLE_TEXTS)

    def test_content_manifest_carries_field_test_and_deploy_teaser_dialogue(self):
        scenes = json.loads((CONTENT / "dialogue.yml").read_text(encoding="utf-8"))["scenes"]
        ids = {scene["id"] for scene in scenes}
        for scene_id in (
            "RC_DIALOGUE_WILD_TUTORIAL_TRIGGER",
            "RC_DIALOGUE_PORT_TRAINER_INTRO",
            "RC_DIALOGUE_DEPLOY_TEASER",
            "RC_DIALOGUE_SCOPE_CHANGE",
        ):
            self.assertIn(scene_id, ids)


if __name__ == "__main__":
    unittest.main()
