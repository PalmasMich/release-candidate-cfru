from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_release_candidate.py"
EXPECTED_SHA1 = "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"


def load_builder():
    spec = importlib.util.spec_from_file_location("rc_builder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_fake_workspace(tmp):
    root, dpe = Path(tmp) / "cfru", Path(tmp) / "dpe"
    (root / "scripts").mkdir(parents=True)
    (dpe / "scripts").mkdir(parents=True)
    (root / "scripts" / "make.py").write_text("# test fixture\n", encoding="utf-8")
    (dpe / "scripts" / "make.py").write_text("# test fixture\n", encoding="utf-8")
    table = root / "src/Tables/level_up_learnsets.c"
    table.parent.mkdir(parents=True)
    table.write_text(
        "\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n};\n*/\n"
        "\t[SPECIES_RC_CAGLIARI_WILD_01] = sRCMistrilloLevelUpLearnset,\n"
        "\t[SPECIES_RC_FROG_01] = sRCFrobyteLevelUpLearnset,\n"
        "\t[SPECIES_RC_FIREFOX_01] = sRCEmberfoxLevelUpLearnset,\n};\n",
        encoding="utf-8",
    )
    return root, dpe


class ReleaseCandidateBuildPipelineTest(unittest.TestCase):
    def test_validates_expected_pristine_rom_hash(self):
        self.assertEqual(load_builder().EXPECTED_SHA1, EXPECTED_SHA1)

    def test_pipeline_order(self):
        self.assertEqual(load_builder().PIPELINE, ("CHAPTER1_PREFLIGHT", "DPE", "CFRU", "RC_STARTER_RUNTIME", "RC_PREVIEW_PATCH", "RC_OPENING_AUDIT", "PORT_LINK_DISCOVERY", "PORT_LINK_TRAINER_PATCH", "DELIVERY_HUB_MAP_PLAN", "RC_CUSTOM_MAPS_PATCH"))

    def test_dpe_sync_targets_preview_branch(self):
        self.assertEqual(load_builder().DPE_BRANCH, "feature/cagliari-preview-0.1")

    def test_rc_learnset_pointer_overlay_activates_tartrek(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = make_fake_workspace(tmp)
            table = root / builder.RC_LEARNSET_TABLE
            original = table.read_bytes()
            returned = builder.activate_rc_learnset_pointers(root)
            self.assertEqual(returned, original)
            text = table.read_text(encoding="utf-8")
            self.assertIn("*/\n\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n\t[SPECIES_RC_CAGLIARI_WILD_01]", text)

    def test_dpe_preview_symbol_gate_requires_all_rc_assets(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            dpe = Path(tmp)
            names = []
            for slot, name in ((1294, "RCTartrek"), (1295, "RCFrobyte"), (1296, "RCEmberfox"), (1297, "RCMistrillo")):
                names += [f"gFrontSprite{slot}{name}Tiles", f"gBackShinySprite{slot}{name}Tiles", f"gIconSprite{slot}{name}Tiles", f"gFrontSprite{slot}{name}Pal", f"gBackShinySprite{slot}{name}Pal"]
            (dpe / "offsets.ini").write_text("\n".join(f"{n}: 09900000" for n in names), encoding="utf-8")
            builder.verify_dpe_tartrek_symbols(dpe)

    def test_dpe_symbol_gate_rejects_stale_build(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            dpe = Path(tmp); (dpe / "offsets.ini").write_text("gFrontSprite001BulbasaurTiles: 09900000\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "RC preview"):
                builder.verify_dpe_tartrek_symbols(dpe)

    def test_private_rom_guard_rejects_wrong_hash(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / "BPRE0.gba"; rom.write_bytes(b"not-a-fire-red-rom")
            with self.assertRaisesRegex(ValueError, "SHA-1"):
                builder.verify_pristine_rom(rom)

    def _run_fake_pipeline(self, tmp, *, fail_cfru=False, discovery=2, trainer=1, hub=2, custom=1):
        builder = load_builder(); root, dpe = make_fake_workspace(tmp)
        base = root / "BPRE0.gba"; base.write_bytes(b"pristine")
        output = root / "release_candidate_test.gba"
        original_table = (root / builder.RC_LEARNSET_TABLE).read_bytes()
        validated_dpe_roots = []
        def fake_run(label, cwd):
            if label == "DPE": (cwd / "test.gba").write_bytes(b"dpe-expanded")
            else:
                active = (cwd / builder.RC_LEARNSET_TABLE).read_text(encoding="utf-8")
                self.assertIn("*/\n\t[SPECIES_RC_TURTLE_01]", active)
                (cwd / "test.gba").write_bytes(b"dpe-plus-cfru")
                if fail_cfru: raise RuntimeError("forced CFRU failure")
        def patch(source, destination): destination.write_bytes(source.read_bytes() + b"-preview")
        def trainer_patch(source, destination):
            if trainer == 0: destination.write_bytes(source.read_bytes() + b"-trainer")
            return trainer
        def custom_patch(source, destination):
            if custom == 0: destination.write_bytes(source.read_bytes() + b"-maps")
            return custom
        kwargs = dict(cfru_root=root, dpe_root=dpe, output_path=output,
                      run_preflight=lambda: None, run_build=fake_run,
                      verify_rom=lambda _p: "test", sync_dpe=lambda _p: None, verify_dpe_symbols=lambda _p: None,
                      validate_starter_runtime=lambda selected: validated_dpe_roots.append(selected), apply_preview_patch=patch, audit_opening=lambda _p: None, discover_port_link=lambda _p: discovery,
                      apply_port_link_trainer=trainer_patch, prepare_delivery_hub_map=lambda _p: hub,
                      apply_custom_maps=custom_patch)
        if fail_cfru:
            with self.assertRaisesRegex(RuntimeError, "forced CFRU failure"): builder.run_pipeline(**kwargs)
        else: builder.run_pipeline(**kwargs)
        self.assertEqual(base.read_bytes(), b"pristine")
        self.assertEqual((root / builder.RC_LEARNSET_TABLE).read_bytes(), original_table)
        self.assertFalse((dpe / "BPRE0.gba").exists())
        self.assertEqual(validated_dpe_roots, [dpe.resolve()])
        return output

    def test_preflight_runs_before_dpe_build(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root, dpe = make_fake_workspace(tmp)
            (root / "BPRE0.gba").write_bytes(b"pristine")
            output = root / "release_candidate_test.gba"
            order = []

            def preflight():
                order.append("preflight")

            def fake_run(label, cwd):
                order.append(label)
                if label == "DPE":
                    (cwd / "test.gba").write_bytes(b"dpe-expanded")
                else:
                    (cwd / "test.gba").write_bytes(b"dpe-plus-cfru")

            builder.run_pipeline(
                cfru_root=root,
                dpe_root=dpe,
                output_path=output,
                run_preflight=preflight,
                run_build=fake_run,
                verify_rom=lambda _p: "test",
                sync_dpe=lambda _p: None,
                verify_dpe_symbols=lambda _p: None,
                validate_starter_runtime=lambda _dpe: None,
                apply_preview_patch=lambda source, destination: destination.write_bytes(
                    source.read_bytes() + b"-preview"
                ),
                audit_opening=lambda _p: None,
                discover_port_link=lambda _p: 2,
                apply_port_link_trainer=lambda _s, _d: 1,
                prepare_delivery_hub_map=lambda _p: 2,
                apply_custom_maps=lambda _s, _d: 1,
            )

            self.assertGreaterEqual(len(order), 3)
            self.assertEqual(order[0:3], ["preflight", "DPE", "CFRU"])

    def test_pipeline_restores_rom_and_learnset_table_after_failure(self):
        with tempfile.TemporaryDirectory() as tmp: self._run_fake_pipeline(tmp, fail_cfru=True)

    def test_pipeline_applies_preview_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self._run_fake_pipeline(tmp)
            self.assertEqual(output.read_bytes(), b"dpe-plus-cfru-preview")

    def test_pipeline_applies_port_link_trainer_when_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self._run_fake_pipeline(tmp, discovery=0, trainer=0, hub=0)
            self.assertEqual(output.read_bytes(), b"dpe-plus-cfru-preview-trainer")

    def test_pipeline_applies_custom_maps_when_plan_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self._run_fake_pipeline(tmp, hub=0, custom=0)
            self.assertEqual(output.read_bytes(), b"dpe-plus-cfru-preview-maps")

    def test_pipeline_keeps_previous_output_when_custom_maps_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self._run_fake_pipeline(tmp, discovery=0, trainer=0, hub=0, custom=1)
            self.assertEqual(output.read_bytes(), b"dpe-plus-cfru-preview-trainer")

    def test_default_output_is_git_ignored_gba(self):
        builder = load_builder(); self.assertEqual(builder.DEFAULT_OUTPUT_NAME, "release_candidate_test.gba")
        self.assertIn("*.gba", (ROOT / ".gitignore").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
