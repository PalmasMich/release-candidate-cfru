from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "scripts" / "discover_port_link_trainer_script.py"
PATCHER = ROOT / "scripts" / "patch_port_link_trainer.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortLinkTrainerPatchTest(unittest.TestCase):
    def build_fixture(self, discovery, patcher):
        payload = bytearray(b"\x00" * 1600)

        intro = discovery.encode_text(discovery.PORT_LINK_NPC_TEXT)
        intro_offset = 120
        payload[intro_offset:intro_offset + len(intro)] = intro

        defeat = discovery.encode_text("Please, report at MARINA PORTO.")
        defeat_offset = 240
        payload[defeat_offset:defeat_offset + len(defeat)] = defeat

        party_offset = 400
        payload[party_offset:party_offset + len(patcher.YOUNGSTER_BEN_PARTY_SIGNATURE)] = patcher.YOUNGSTER_BEN_PARTY_SIGNATURE

        script_offset = 700
        branch_target = discovery.GBA_ROM_BASE + script_offset + 100
        script = (
            bytes([
                discovery.CMD_LOCK,
                discovery.CMD_FACEPLAYER,
                discovery.CMD_CHECKFLAG,
                0x34,
                0x12,
                discovery.CMD_GOTO_IF,
                0x01,
            ])
            + branch_target.to_bytes(4, "little")
            + bytes([discovery.CMD_LOADPOINTER, 0x00])
            + discovery.gba_pointer_bytes(intro_offset)
            + bytes([
                discovery.CMD_CALLSTD,
                0x04,
                discovery.CMD_RELEASE,
                discovery.CMD_END,
            ])
            + (b"\x00" * 64)
        )
        payload[script_offset:script_offset + len(script)] = script
        return bytes(payload), script_offset, intro_offset, defeat_offset, party_offset

    def test_builds_expected_single_trainerbattle_script(self):
        discovery = load(DISCOVERY, "port_link_discovery")
        patcher = load(PATCHER, "port_link_patcher")
        script = patcher.build_trainer_script(discovery, 0x1234, 0x5678)
        self.assertEqual(script[0], discovery.CMD_LOCK)
        self.assertEqual(script[1], discovery.CMD_FACEPLAYER)
        self.assertEqual(script[2], discovery.CMD_TRAINERBATTLE)
        self.assertEqual(script[3], discovery.TRAINER_BATTLE_SINGLE)
        self.assertEqual(int.from_bytes(script[4:6], "little"), discovery.TRAINER_BOOTSTRAP_ID)
        self.assertEqual(int.from_bytes(script[6:8], "little"), 0)
        self.assertEqual(int.from_bytes(script[8:12], "little"), discovery.GBA_ROM_BASE + 0x1234)
        self.assertEqual(int.from_bytes(script[12:16], "little"), discovery.GBA_ROM_BASE + 0x5678)
        self.assertEqual(script[-2:], bytes([discovery.CMD_RELEASE, discovery.CMD_END]))
        self.assertEqual(len(script), 18)

    def test_patches_guarded_script_and_preview_level_party(self):
        discovery = load(DISCOVERY, "port_link_discovery")
        patcher = load(PATCHER, "port_link_patcher")
        original, script_offset, intro_offset, defeat_offset, party_offset = self.build_fixture(discovery, patcher)
        patched, evidence = patcher.patch_bytes(original)
        self.assertEqual(len(patched), len(original))
        self.assertEqual(evidence["script_start"], script_offset)
        self.assertEqual(evidence["trainer_id"], discovery.TRAINER_BOOTSTRAP_ID)
        self.assertEqual(evidence["intro_text_offset"], intro_offset)
        self.assertEqual(evidence["defeat_text_offset"], defeat_offset)
        self.assertEqual(evidence["party_offset"], party_offset)
        expected = patcher.build_trainer_script(discovery, intro_offset, defeat_offset)
        self.assertEqual(patched[script_offset:script_offset + len(expected)], expected)
        for level_offset in patcher.TRAINER_MON_LEVEL_OFFSETS:
            self.assertEqual(patched[party_offset + level_offset], patcher.PORT_LINK_TRAINER_LEVEL)
        for species_offset in patcher.TRAINER_MON_SPECIES_OFFSETS:
            self.assertEqual(int.from_bytes(patched[party_offset + species_offset:party_offset + species_offset + 2], "little"), patcher.MEOWTH_SPECIES_ID)

    def test_rejects_rom_without_unique_defeat_text(self):
        discovery = load(DISCOVERY, "port_link_discovery")
        patcher = load(PATCHER, "port_link_patcher")
        original, _, _, _, _ = self.build_fixture(discovery, patcher)
        payload = bytearray(original)
        defeat = discovery.encode_text(patcher.TRAINER_DEFEAT_TEXT)
        second = 300
        payload[second:second + len(defeat)] = defeat
        with self.assertRaisesRegex(ValueError, "exactly one"):
            patcher.patch_bytes(bytes(payload))

    def test_rejects_missing_bootstrap_party_signature(self):
        discovery = load(DISCOVERY, "port_link_discovery")
        patcher = load(PATCHER, "port_link_patcher")
        original, _, _, _, party_offset = self.build_fixture(discovery, patcher)
        payload = bytearray(original)
        payload[party_offset:party_offset + len(patcher.YOUNGSTER_BEN_PARTY_SIGNATURE)] = b"\xFF" * len(patcher.YOUNGSTER_BEN_PARTY_SIGNATURE)
        with self.assertRaisesRegex(ValueError, "Youngster Ben bootstrap party"):
            patcher.patch_bytes(bytes(payload))

    def test_rejects_unclassified_pointer(self):
        discovery = load(DISCOVERY, "port_link_discovery")
        patcher = load(PATCHER, "port_link_patcher")
        payload = bytearray(b"\x00" * 900)
        intro = discovery.encode_text(discovery.PORT_LINK_NPC_TEXT)
        intro_offset = 100
        payload[intro_offset:intro_offset + len(intro)] = intro
        payload[500:504] = discovery.gba_pointer_bytes(intro_offset)
        defeat = discovery.encode_text(patcher.TRAINER_DEFEAT_TEXT)
        payload[200:200 + len(defeat)] = defeat
        with self.assertRaisesRegex(ValueError, "not uniquely safe"):
            patcher.patch_bytes(bytes(payload))


if __name__ == "__main__":
    unittest.main()
