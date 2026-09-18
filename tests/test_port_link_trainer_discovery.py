from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "discover_port_link_trainer_script.py"


def load_module():
    spec = importlib.util.spec_from_file_location("port_link_discovery", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortLinkTrainerDiscoveryTest(unittest.TestCase):
    def build_dialogue_script_fixture(self, module, text, *, text_offset=128, script_offset=300):
        payload = bytearray(b"\x00" * 700)
        payload[text_offset:text_offset + len(text)] = text

        script = bytes([
            module.CMD_LOCK,
            module.CMD_FACEPLAYER,
            module.CMD_LOADPOINTER,
            0x00,
        ]) + module.gba_pointer_bytes(text_offset) + bytes([
            module.CMD_MSGBOX_NORMAL,
            module.CMD_RELEASE,
            module.CMD_END,
        ])
        payload[script_offset:script_offset + len(script)] = script
        xref_offset = script_offset + 4
        return payload, xref_offset

    def test_finds_unique_patched_text_and_classifies_event_script(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_TEXT)
        payload, xref_offset = self.build_dialogue_script_fixture(module, text)

        report = module.analyze_rom(bytes(payload))

        self.assertEqual(report["target"], "patched_port_link_delivery_npc")
        self.assertTrue(report["safe_to_patch"])
        self.assertEqual(report["classified_script_xrefs"], 1)
        context = report["candidate_contexts"][0]
        self.assertEqual(context["xref_offset"], xref_offset)
        self.assertEqual(context["classification"], "event_dialogue_script")
        self.assertTrue(context["markers"]["loadpointer_prefix"])
        self.assertTrue(context["markers"]["has_lock_before"])
        self.assertTrue(context["markers"]["has_faceplayer_before"])
        self.assertIsNotNone(context["patch_plan"])
        self.assertEqual(
            context["patch_plan"]["script_start_candidate"],
            xref_offset - 4,
        )
        self.assertFalse(context["patch_plan"]["mutation_allowed"])
        self.assertGreater(
            context["patch_plan"]["verification_signature_length"],
            0,
        )

    def test_falls_back_to_source_route1_text(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_SOURCE_TEXT)
        payload, _ = self.build_dialogue_script_fixture(module, text)

        report = module.analyze_rom(bytes(payload))

        self.assertEqual(report["target"], "source_route1_mart_npc")
        self.assertTrue(report["safe_to_patch"])

    def test_pointer_without_script_signature_is_not_safe_to_patch(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_TEXT)
        text_offset = 128
        payload = bytearray(b"\x00" * 512)
        payload[text_offset:text_offset + len(text)] = text
        xref_offset = 320
        payload[xref_offset:xref_offset + 4] = module.gba_pointer_bytes(text_offset)

        report = module.analyze_rom(bytes(payload))

        self.assertFalse(report["safe_to_patch"])
        self.assertEqual(
            report["candidate_contexts"][0]["classification"],
            "data_or_unknown_reference",
        )
        self.assertIsNone(report["candidate_contexts"][0]["patch_plan"])

    def test_duplicate_target_text_is_not_safe_to_patch(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_TEXT)
        payload = bytearray(b"\x00" * 900)
        offsets = [100, 200]

        for i, offset in enumerate(offsets):
            payload[offset:offset + len(text)] = text
            script_offset = 400 + (i * 100)
            script = bytes([
                module.CMD_LOCK,
                module.CMD_FACEPLAYER,
                module.CMD_LOADPOINTER,
                0x00,
            ]) + module.gba_pointer_bytes(offset) + bytes([
                module.CMD_MSGBOX_NORMAL,
                module.CMD_RELEASE,
                module.CMD_END,
            ])
            payload[script_offset:script_offset + len(script)] = script

        report = module.analyze_rom(bytes(payload))

        self.assertFalse(report["safe_to_patch"])
        self.assertEqual(report["patched_text"]["text_offsets"], offsets)

    def test_context_contains_xref_location(self):
        module = load_module()
        payload = bytes(range(128))
        context = module.script_context(payload, 64, radius=8)

        self.assertEqual(context["start"], 56)
        self.assertEqual(context["xref_offset"], 64)
        self.assertEqual(context["xref_index"], 8)
        self.assertEqual(context["end"], 76)


if __name__ == "__main__":
    unittest.main()
