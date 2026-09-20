from pathlib import Path
import copy
import importlib.util
import json
import io
import unittest
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "preflight_chapter1.py"
MAPS = ROOT / "content" / "cagliari_preview" / "map_specs"


def load_preflight():
    spec = importlib.util.spec_from_file_location("rc_chapter1_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_map_specs():
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in MAPS.glob("RC_*.json")
    }


class Chapter1PreflightTest(unittest.TestCase):
    def test_all_warp_indices_land_on_the_declared_target_anchor(self):
        load_preflight().validate_warp_contracts(load_map_specs())

    def test_rejects_target_warp_index_anchor_mismatch(self):
        specs = load_map_specs()
        broken = copy.deepcopy(specs)
        broken["RC_PORT_CONNECTION"]["warps"][0]["warp_id"] = 0
        with self.assertRaisesRegex(ValueError, "target anchor"):
            load_preflight().validate_warp_contracts(broken)

    def test_preflight_reports_non_final_tileset_art_status(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = load_preflight().main()
        self.assertEqual(result, 0)
        self.assertIn("RC_TILESET_ART_STATUS=BOOTSTRAP", output.getvalue())


if __name__ == "__main__":
    unittest.main()
