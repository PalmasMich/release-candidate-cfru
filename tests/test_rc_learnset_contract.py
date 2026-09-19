from pathlib import Path
import importlib.util
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"
BUILDER = ROOT / "scripts" / "build_release_candidate.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("rc_builder_learnsets", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseCandidateLearnsetContractTest(unittest.TestCase):
    """Guard the minimum playable movesets used by the Cagliari preview."""

    def setUp(self):
        self.source = LEARNSETS.read_text(encoding="utf-8")

    def _assert_learnset(self, symbol, moves):
        match = re.search(
            rf"static const struct LevelUpMove {symbol}\[\] = \{{(.*?)\n\}};",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match, f"Missing CFRU learnset {symbol}")
        body = match.group(1)
        for level, move in moves:
            self.assertIn(f"LEVEL_UP_MOVE({level:2d}, {move})", body)
        self.assertIn("LEVEL_UP_END", body)

    def test_tartrek_has_playable_opening_moves(self):
        self._assert_learnset(
            "sRCTartrekLevelUpLearnset",
            [(1, "MOVE_TACKLE"), (1, "MOVE_WITHDRAW"), (5, "MOVE_VINEWHIP"), (7, "MOVE_MUDSLAP")],
        )

    def test_frobyte_has_playable_opening_moves(self):
        self._assert_learnset(
            "sRCFrobyteLevelUpLearnset",
            [(1, "MOVE_POUND"), (1, "MOVE_GROWL"), (5, "MOVE_WATERGUN"), (7, "MOVE_THUNDERSHOCK")],
        )

    def test_emberfox_has_playable_opening_moves(self):
        self._assert_learnset(
            "sRCEmberfoxLevelUpLearnset",
            [(1, "MOVE_SCRATCH"), (1, "MOVE_TAILWHIP"), (5, "MOVE_EMBER"), (7, "MOVE_BITE")],
        )

    def test_mistrillo_has_playable_wild_moves(self):
        self._assert_learnset(
            "sRCMistrilloLevelUpLearnset",
            [(1, "MOVE_GUST"), (1, "MOVE_GROWL"), (4, "MOVE_QUICKATTACK"), (7, "MOVE_SANDATTACK")],
        )

    def test_build_overlay_activates_every_rc_pointer(self):
        """A pointer written inside CFRU's large upstream comment is not active C.

        Exercise the exact transactional overlay used by the private build and
        inspect only the source after the closing block-comment marker.
        """
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / builder.RC_LEARNSET_TABLE
            target.parent.mkdir(parents=True)
            target.write_text(self.source, encoding="utf-8")
            original = builder.activate_rc_learnset_pointers(root)
            self.assertEqual(original.decode("utf-8"), self.source)
            active_tail = target.read_text(encoding="utf-8").split("*/", 1)[1]
            expected = {
                "SPECIES_RC_TURTLE_01": "sRCTartrekLevelUpLearnset",
                "SPECIES_RC_FROG_01": "sRCFrobyteLevelUpLearnset",
                "SPECIES_RC_FIREFOX_01": "sRCEmberfoxLevelUpLearnset",
                "SPECIES_RC_CAGLIARI_WILD_01": "sRCMistrilloLevelUpLearnset",
            }
            for species, learnset in expected.items():
                pointer = f"[{species}] = {learnset}"
                self.assertEqual(active_tail.count(pointer), 1, f"Inactive or duplicate pointer: {pointer}")


if __name__ == "__main__":
    unittest.main()
