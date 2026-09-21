from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"

EXPECTED = {
    "RCTartrek": [(1, "MOVE_TACKLE"), (1, "MOVE_WITHDRAW"), (5, "MOVE_VINEWHIP"), (7, "MOVE_MUDSLAP")],
    "RCFrobyte": [(1, "MOVE_POUND"), (1, "MOVE_GROWL"), (5, "MOVE_WATERGUN"), (7, "MOVE_THUNDERSHOCK")],
    "RCEmberfox": [(1, "MOVE_SCRATCH"), (1, "MOVE_TAILWHIP"), (5, "MOVE_EMBER"), (7, "MOVE_BITE")],
    "RCMistrillo": [(1, "MOVE_GUST"), (1, "MOVE_GROWL"), (4, "MOVE_QUICKATTACK"), (7, "MOVE_SANDATTACK")],
}

SPECIES_BINDINGS = {
    "SPECIES_RC_TURTLE_01": "sRCTartrekLevelUpLearnset",
    "SPECIES_RC_FROG_01": "sRCFrobyteLevelUpLearnset",
    "SPECIES_RC_FIREFOX_01": "sRCEmberfoxLevelUpLearnset",
    "SPECIES_RC_CAGLIARI_WILD_01": "sRCMistrilloLevelUpLearnset",
}


class RCRuntimeLearnsetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = LEARNSETS.read_text(encoding="utf-8")

    def test_preview_species_have_expected_starting_moves(self):
        for name, expected in EXPECTED.items():
            match = re.search(
                rf"static const struct LevelUpMove s{name}LevelUpLearnset\[\] = \{{(.*?)\n\}};",
                self.source,
                re.S,
            )
            self.assertIsNotNone(match, f"missing CFRU learnset for {name}")
            moves = [
                (int(level), move)
                for level, move in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_[A-Z0-9_]+)\)", match.group(1))
            ]
            self.assertEqual(moves, expected, f"unexpected runtime learnset for {name}")

    def test_preview_species_are_bound_in_runtime_pointer_table(self):
        for species, learnset in SPECIES_BINDINGS.items():
            self.assertRegex(
                self.source,
                rf"\[{species}\]\s*=\s*{learnset}\s*,",
                f"{species} would fall through to an invalid/empty CFRU learnset",
            )

    def test_level_five_starters_enter_first_rival_battle_with_two_moves(self):
        for name in ("RCTartrek", "RCFrobyte", "RCEmberfox"):
            starting = [move for level, move in EXPECTED[name] if level <= 5]
            self.assertGreaterEqual(len(starting), 2, f"{name} needs at least two usable moves by level 5")

    def test_first_custom_wild_encounter_has_level_one_moves(self):
        starting = [move for level, move in EXPECTED["RCMistrillo"] if level <= 3]
        self.assertGreaterEqual(len(starting), 2, "level-3 Mistrillo must enter battle with usable moves")


if __name__ == "__main__":
    unittest.main()
