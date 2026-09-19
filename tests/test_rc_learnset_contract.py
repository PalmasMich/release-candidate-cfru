from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"


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

    def test_rc_species_are_registered_in_pointer_table(self):
        expected = {
            "SPECIES_RC_TURTLE_01": "sRCTartrekLevelUpLearnset",
            "SPECIES_RC_FROG_01": "sRCFrobyteLevelUpLearnset",
            "SPECIES_RC_FIREFOX_01": "sRCEmberfoxLevelUpLearnset",
            "SPECIES_RC_CAGLIARI_WILD_01": "sRCMistrilloLevelUpLearnset",
        }
        for species, learnset in expected.items():
            self.assertIn(f"[{species}] = {learnset}", self.source)


if __name__ == "__main__":
    unittest.main()
