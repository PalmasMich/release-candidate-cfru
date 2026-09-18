from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compile_rc_event_scripts.py"
SPEC = ROOT / "content" / "cagliari_preview" / "script_specs" / "RC_DELIVERY_HUB.json"


def load_compiler():
    spec = importlib.util.spec_from_file_location("rc_event_compiler", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RcEventScriptCompilerTest(unittest.TestCase):
    def setUp(self):
        self.compiler = load_compiler()
        self.spec = json.loads(SPEC.read_text(encoding="utf-8"))
        self.ir = self.compiler.compile_spec(self.spec)
        self.by_id = {script["id"]: script for script in self.ir["scripts"]}

    def test_compiles_all_delivery_hub_scripts(self):
        self.assertEqual(self.ir["format"], "RC_EVENT_SCRIPT_IR_V1")
        self.assertEqual(self.ir["map"], "RC_DELIVERY_HUB")
        self.assertEqual(
            set(self.by_id),
            {
                "RC_SCRIPT_DELIVERY_LEAD",
                "RC_SCRIPT_STARTER_TARTREK",
                "RC_SCRIPT_STARTER_FROBYTE",
                "RC_SCRIPT_STARTER_EMBERFOX",
                "RC_SCRIPT_KPI_RIVAL",
            },
        )

    def test_uses_verified_fire_red_lock_release_opcodes(self):
        lead = bytes.fromhex(self.by_id["RC_SCRIPT_DELIVERY_LEAD"]["bytes_hex"])
        self.assertEqual(lead[0], 0x6A)
        self.assertEqual(lead[1], 0x5A)
        self.assertEqual(lead[-2], 0x6C)
        self.assertEqual(lead[-1], 0x02)

    def test_tartrek_script_gives_species_and_sets_story_flag(self):
        script = bytes.fromhex(self.by_id["RC_SCRIPT_STARTER_TARTREK"]["bytes_hex"])

        give_pos = script.index(bytes([self.compiler.OP_GIVEMON]))
        species = int.from_bytes(script[give_pos + 1:give_pos + 3], "little")
        level = script[give_pos + 3]

        self.assertEqual(species, 0x050E)
        self.assertEqual(level, 5)

        setflag_pos = script.index(bytes([self.compiler.OP_SETFLAG]))
        flag = int.from_bytes(script[setflag_pos + 1:setflag_pos + 3], "little")
        self.assertEqual(flag, 0x0B0)

    def test_each_starter_uses_distinct_original_species(self):
        expected = {
            "RC_SCRIPT_STARTER_TARTREK": 0x050E,
            "RC_SCRIPT_STARTER_FROBYTE": 0x050F,
            "RC_SCRIPT_STARTER_EMBERFOX": 0x0510,
        }

        for script_id, species_id in expected.items():
            script = bytes.fromhex(self.by_id[script_id]["bytes_hex"])
            pos = script.index(bytes([self.compiler.OP_GIVEMON]))
            self.assertEqual(
                int.from_bytes(script[pos + 1:pos + 3], "little"),
                species_id,
            )

    def test_starter_branch_targets_already_label_after_linking(self):
        ir = self.by_id["RC_SCRIPT_STARTER_TARTREK"]
        base = 0x08900000
        dialogue_addresses = {
            relocation["symbol"]: 0x08910000 + i * 0x100
            for i, relocation in enumerate(ir["relocations"])
            if relocation["kind"] == "dialogue"
        }

        linked = self.compiler.link_script(ir, base, dialogue_addresses)
        branch = next(
            relocation
            for relocation in ir["relocations"]
            if relocation["kind"] == "internal_label"
        )
        pointer = int.from_bytes(
            linked[branch["offset"]:branch["offset"] + 4],
            "little",
        )
        self.assertEqual(pointer, base + ir["labels"]["already"])

    def test_rival_sets_intro_done_flag(self):
        script = bytes.fromhex(self.by_id["RC_SCRIPT_KPI_RIVAL"]["bytes_hex"])
        occurrences = []
        start = 0
        while True:
            pos = script.find(bytes([self.compiler.OP_SETFLAG]), start)
            if pos < 0:
                break
            occurrences.append(
                int.from_bytes(script[pos + 1:pos + 3], "little")
            )
            start = pos + 1
        self.assertEqual(occurrences, [0x0B1])

    def test_dialogue_relocations_must_be_resolved(self):
        ir = self.by_id["RC_SCRIPT_DELIVERY_LEAD"]
        with self.assertRaisesRegex(ValueError, "missing dialogue address"):
            self.compiler.link_script(ir, 0x08900000, {})


if __name__ == "__main__":
    unittest.main()
