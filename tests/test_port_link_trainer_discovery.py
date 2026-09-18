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
    def test_finds_unique_patched_text_and_pointer_xref(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_TEXT)
        text_offset = 128
        payload = bytearray(b"\x00" * 512)
        payload[text_offset:text_offset + len(text)] = text

        xref_offset = 320
        payload[xref_offset:xref_offset + 4] = module.gba_pointer_bytes(text_offset)

        report = module.analyze_rom(bytes(payload))

        self.assertEqual(report["target"], "patched_port_link_delivery_npc")
        self.assertTrue(report["safe_to_patch"])
        self.assertEqual(report["patched_text"]["text_offsets"], [text_offset])
        self.assertEqual(
            report["patched_text"]["xrefs"][0]["xref_offset"],
            xref_offset,
        )

    def test_falls_back_to_source_route1_text(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_SOURCE_TEXT)
        text_offset = 96
        payload = bytearray(b"\x00" * 384)
        payload[text_offset:text_offset + len(text)] = text
        xref_offset = 256
        payload[xref_offset:xref_offset + 4] = module.gba_pointer_bytes(text_offset)

        report = module.analyze_rom(bytes(payload))

        self.assertEqual(report["target"], "source_route1_mart_npc")
        self.assertTrue(report["safe_to_patch"])

    def test_duplicate_target_text_is_not_safe_to_patch(self):
        module = load_module()
        text = module.encode_text(module.PORT_LINK_NPC_TEXT)
        payload = bytearray(b"\x00" * 700)
        offsets = [100, 200]

        for offset in offsets:
            payload[offset:offset + len(text)] = text

        payload[400:404] = module.gba_pointer_bytes(offsets[0])
        payload[500:504] = module.gba_pointer_bytes(offsets[1])

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
