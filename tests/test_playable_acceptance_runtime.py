from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"


def load_patcher():
    spec = importlib.util.spec_from_file_location("rc_preview_patcher_acceptance", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlayableAcceptanceRuntimeTest(unittest.TestCase):
    def test_acceptance_critical_path_is_backed_by_runtime_contract(self):
        p = load_patcher()
        acceptance = json.loads((CONTENT / "playable_acceptance.json").read_text(encoding="utf-8"))
        critical = {item["id"]: item for item in acceptance["critical_path"]}
        self.assertEqual(
            set(critical),
            {"opening_identity", "starter_runtime", "kpi_rival", "first_field_test", "preview_endpoint"},
        )
        self.assertTrue(all(item["status"] == "implemented_pending_private_smoke" for item in critical.values()))

        required_text = set(p.REQUIRED_VISIBLE_TEXTS)
        for text in (
            "Welcome to Release Candidate!",
            "CAGLIARI\nFirst sprint starts here!",
            "DELIVERY HUB - CAGLIARI",
            "KPI check: show velocity!",
            "PORT LINK\nCAGLIARI - MARINA PORTO",
            "MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE",
        ):
            self.assertIn(p.encode_text(text), required_text)

        self.assertEqual(
            (p.TARTREK_SPECIES_ID, p.FROBYTE_SPECIES_ID, p.EMBERFOX_SPECIES_ID, p.MISTRILLO_SPECIES_ID),
            (0x050E, 0x050F, 0x0510, 0x0511),
        )

        weighted = {}
        for species, weight in zip(p.ROUTE1_PREVIEW_SPECIES, p.GRASS_SLOT_WEIGHTS):
            weighted[species] = weighted.get(species, 0) + weight
        self.assertEqual(weighted[p.MISTRILLO_SPECIES_ID], 60)
        self.assertEqual(weighted[p.WINGULL_SPECIES_ID], 25)
        self.assertEqual(weighted[p.MEOWTH_SPECIES_ID], 15)

    def test_manual_smoke_route_covers_every_preview_pillar(self):
        acceptance = json.loads((CONTENT / "playable_acceptance.json").read_text(encoding="utf-8"))
        route = " | ".join(acceptance["next_private_smoke"]["minimum_route"])
        for token in ("Release Candidate", "Delivery Hub", "Tartrek", "KPI rival", "Port Link", "Mistrillo", "Marina Porto"):
            self.assertIn(token, route)


if __name__ == "__main__":
    unittest.main()
