from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"


class ReleaseCandidateLearnsetContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = LEARNSETS.read_text(encoding="utf-8")

    def _body(self, symbol):
        match = re.search(
            rf"static const struct LevelUpMove {symbol}\[\] = \{{(?P<body>.*?)\n\}};",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match, f"missing {symbol}")
        return match.group("body")

    def test_tartrek_has_real_level_five_battle_moves(self):
        body = self._body("sRCTartrekLevelUpLearnset")
        self.assertIn("LEVEL_UP_MOVE( 1, MOVE_TACKLE)", body)
        self.assertIn("LEVEL_UP_MOVE( 1, MOVE_GROWL)", body)
        self.assertIn("LEVEL_UP_MOVE( 5, MOVE_VINEWHIP)", body)
        self.assertIn("LEVEL_UP_END", body)

    def test_other_preview_starters_are_not_empty(self):
        expectations = {
            "sRCFrobyteLevelUpLearnset": ("MOVE_POUND", "MOVE_GROWL", "MOVE_WATERGUN"),
            "sRCEmberfoxLevelUpLearnset": ("MOVE_SCRATCH", "MOVE_TAILWHIP", "MOVE_EMBER"),
        }
        for symbol, moves in expectations.items():
            body = self._body(symbol)
            for move in moves:
                self.assertIn(move, body)
            self.assertIn("LEVEL_UP_END", body)

    def test_rc_species_are_wired_to_custom_learnsets(self):
        pointers = {
            "SPECIES_RC_TURTLE_01": "sRCTartrekLevelUpLearnset",
            "SPECIES_RC_FROG_01": "sRCFrobyteLevelUpLearnset",
            "SPECIES_RC_FIREFOX_01": "sRCEmberfoxLevelUpLearnset",
        }
        for species, learnset in pointers.items():
            self.assertRegex(
                self.source,
                rf"\[{species}\]\s*=\s*{learnset}",
                f"{species} must not fall through to the CFRU empty moveset",
            )


if __name__ == "__main__":
    unittest.main()
