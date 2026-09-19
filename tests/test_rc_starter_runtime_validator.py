from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_rc_starter_runtime.py"
DPE_ROOT = ROOT.parent / "release-candidate-dpe"


def load_validator():
    spec = importlib.util.spec_from_file_location("rc_starter_validator", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_dpe_contract(destination: Path) -> Path:
    for relative in (
        "release_candidate/preview_species.json",
        "include/release_candidate_species.h",
        "include/pokedex.h",
        "scripts/apply_release_candidate_overlay.py",
    ):
        source = DPE_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return destination


class RCStarterRuntimeValidatorTest(unittest.TestCase):
    def test_current_dpe_contract_is_complete(self):
        self.assertEqual(load_validator().validate(DPE_ROOT), [])

    def test_validator_rejects_missing_rc_national_dex_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            dpe = copy_dpe_contract(Path(tmp))
            manifest = dpe / "release_candidate" / "preview_species.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            del data["species"][0]["national_dex"]
            manifest.write_text(json.dumps(data), encoding="utf-8")

            errors = load_validator().validate(dpe)

            self.assertIn("missing National Dex mapping", "\n".join(errors))

    def test_validator_rejects_duplicate_rc_national_dex_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            dpe = copy_dpe_contract(Path(tmp))
            manifest = dpe / "release_candidate" / "preview_species.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["species"][1]["national_dex"] = data["species"][0]["national_dex"]
            manifest.write_text(json.dumps(data), encoding="utf-8")

            errors = load_validator().validate(dpe)

            self.assertIn("National Dex ids are not unique", errors)


if __name__ == "__main__":
    unittest.main()
