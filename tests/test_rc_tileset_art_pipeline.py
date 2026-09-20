from pathlib import Path
import copy
import importlib.util
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_rc_tileset_pipeline.py"
MANIFEST = ROOT / "content" / "cagliari_preview" / "tileset_art_manifest.json"
MAPS = ROOT / "content" / "cagliari_preview" / "map_specs"


def load_validator():
    spec = importlib.util.spec_from_file_location("rc_tileset_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RCTilesetArtPipelineTest(unittest.TestCase):
    def test_manifest_covers_every_map_and_declared_tileset(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        contracts = {item["id"]: item for item in manifest["tilesets"]}
        covered_maps = {
            map_id
            for item in contracts.values()
            for map_id in item["maps"]
        }
        specs = [json.loads(path.read_text(encoding="utf-8")) for path in MAPS.glob("RC_*.json")]
        self.assertEqual(covered_maps, {spec["id"] for spec in specs})
        for spec in specs:
            self.assertIn(spec["art_contract"]["tileset"], contracts)

    def test_current_pipeline_is_valid_but_bootstrap(self):
        validator = load_validator()
        manifest = validator.load_manifest(MANIFEST)
        self.assertEqual(validator.validate(manifest), [])
        self.assertEqual(validator.overall_status(manifest), "BOOTSTRAP")

    def test_bootstrap_profiles_cannot_be_claimed_as_production_ready(self):
        validator = load_validator()
        manifest = validator.load_manifest(MANIFEST)
        broken = copy.deepcopy(manifest)
        broken["tilesets"][0]["production_ready"] = True
        errors = validator.validate(broken)
        self.assertIn("production_ready requires every stage approved", "\n".join(errors))

    def test_strict_approval_gate_rejects_current_bootstrap(self):
        validator = load_validator()
        self.assertEqual(validator.run(MANIFEST, require_approved=True), 1)


if __name__ == "__main__":
    unittest.main()
