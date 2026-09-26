import copy
import json
import unittest

from tests.build_system.support import Workspace
from tool.auto_define_config.editor import ProjectEditor
from tool.auto_define_config.errors import ConfigError
from tool.auto_define_config.expression_tree import ExpressionTree, expression_text
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.preview import preview_header
from tool.auto_define_config.probes import collect_facts
from tool.auto_define_config.sync import Synchronizer


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace()
        self.addCleanup(self.w.close)
        self.registration = self.w.module("define/options")
        self.inventory = load_inventory(self.w.root)
        Synchronizer(self.inventory).apply()
        self.editor = ProjectEditor(self.inventory)

    def test_field_save_preserves_code_and_option_roundtrip(self):
        document = self.editor.fields("define/options")
        probe = document.path.with_name("probe.py")
        original = probe.read_bytes()
        data = copy.deepcopy(document.data)
        data["fields"] = [
            {
                "id": "use_fast",
                "type": "boolean",
                "kind": "option",
                "default": False,
                "macro": "DESTINY_DEFINE_CMAKE_USE_FAST",
                "description": "Enable the fast implementation",
            }
        ]
        self.editor.save_fields(document, data)
        self.assertEqual(probe.read_bytes(), original)
        options = self.editor.options()
        self.editor.save_options(options, {"use_fast": True})
        self.assertEqual(self.editor.options().data, {"use_fast": True})
        facts = collect_facts(self.inventory, options=options.data)
        self.assertTrue(facts["modules"]["define/options"]["use_fast"]["value"])
        header = preview_header(self.inventory, "define/options", facts)
        self.assertIn("#define DESTINY_DEFINE_CMAKE_USE_FAST 1", header)

    def test_external_rule_edit_is_not_overwritten(self):
        document = self.editor.rules("define/options")
        document.path.write_text('{"new":"outside"}')
        with self.assertRaisesRegex(ConfigError, "changed outside"):
            self.editor.save_rules(document, document.data)
        self.assertEqual(document.path.read_text(), '{"new":"outside"}')

    def test_global_macro_collision_is_validated_before_save(self):
        first = self.editor.fields("define/options")
        data = copy.deepcopy(first.data)
        data["fields"] = [
            {
                "id": "one",
                "type": "boolean",
                "macro": "DESTINY_DEFINE_CMAKE_ONE",
                "description": "One",
            }
        ]
        self.editor.save_fields(first, data)
        self.w.module("define/other")
        inventory = load_inventory(self.w.root)
        Synchronizer(inventory).apply()
        editor = ProjectEditor(inventory)
        second = editor.fields("define/other")
        proposed = copy.deepcopy(second.data)
        proposed["fields"] = [dict(data["fields"][0], id="two")]
        before = second.path.read_bytes()
        with self.assertRaisesRegex(ConfigError, "Duplicate generated macro"):
            editor.save_fields(second, proposed)
        self.assertEqual(second.path.read_bytes(), before)

    def test_explicit_counterpart_migration_preserves_handwritten_python(self):
        old = self.editor.fields("define/options").path.parent
        original = (old / "probe.py").read_bytes()
        self.registration.unlink()
        self.w.module("define/renamed")
        service = Synchronizer(load_inventory(self.w.root))
        plan = service.rename("define/options", "define/renamed", dry_run=True)
        self.assertTrue(old.exists())
        self.assertFalse((service.root / "renamed").exists())
        service.rename("define/options", "define/renamed", dry_run=False)
        self.assertFalse(old.exists())
        self.assertEqual((service.root / "renamed/probe.py").read_bytes(), original)
        service.check()
        self.assertEqual(
            json.loads((service.root / "renamed/fields.json").read_text())["module"],
            "define/renamed",
        )

    def test_migration_rejects_existing_destination_and_nested_modules(self):
        self.registration.unlink()
        self.w.module("define/renamed")
        service = Synchronizer(load_inventory(self.w.root))
        service.apply()
        with self.assertRaisesRegex(ConfigError, "must not exist"):
            service.rename("define/options", "define/renamed")

    def test_condition_tree_reordering_and_roundtrip(self):
        model = ExpressionTree({"all": [{"ref": "windows"}, True]})
        model.replace((1,), {"not": False})
        model.append((), {"ref": "avx2"})
        model.move((2,), -1)
        self.assertEqual(model.root, {"all": [{"ref": "windows"}, {"ref": "avx2"}, {"not": False}]})
        self.assertIn("AND", expression_text(model.root))
        model.remove((2,))
        self.assertEqual(len(model.root["all"]), 2)
        with self.assertRaises(ConfigError):
            model.remove(())

    def test_semantic_rule_errors_do_not_replace_saved_rules(self):
        self.w.module("iso/cpu")
        self.editor = ProjectEditor(load_inventory(self.w.root))
        document = self.editor.rules("iso/cpu")
        self.editor.save_rules(document, document.data)
        before = document.path.read_bytes()
        for aliases in ({"bad": {"ref": "typo"}}, {"a": {"ref": "b"}, "b": {"ref": "a"}}):
            proposal = dict(document.data, aliases=aliases)
            with self.assertRaises(ConfigError):
                self.editor.save_rules(document, proposal)
            self.assertEqual(before, document.path.read_bytes())

    def test_rules_can_be_saved_without_hardware_matching_a_required_group(self):
        self.w.module("iso/platform")
        self.w.write("source/iso/platform/src/platform.cpp", "int platform();")
        self.editor = ProjectEditor(load_inventory(self.w.root))
        document = self.editor.rules("iso/platform")
        rules = {
            "schema_version": 1,
            "aliases": {},
            "groups": [
                {
                    "name": "platform",
                    "candidates": [
                        {"name": "none", "when": False, "sources": ["src/platform.cpp"]}
                    ],
                }
            ],
        }
        self.editor.save_rules(document, rules)
        self.assertEqual(self.editor.rules("iso/platform").data, rules)

    def test_removing_a_referenced_field_is_rejected_before_writing(self):
        field_document = self.editor.fields("define/options")
        data = copy.deepcopy(field_document.data)
        data["fields"] = [
            {
                "id": "enabled",
                "type": "boolean",
                "macro": "DESTINY_DEFINE_CMAKE_ENABLED",
                "description": "Enabled",
            }
        ]
        self.editor.save_fields(field_document, data)
        self.w.module("iso/cpu")
        self.editor = ProjectEditor(load_inventory(self.w.root))
        rules = self.editor.rules("iso/cpu")
        self.editor.save_rules(
            rules, {"schema_version": 1, "aliases": {"use": {"ref": "enabled"}}, "groups": []}
        )
        before = field_document.path.read_bytes()
        with self.assertRaises(ConfigError):
            self.editor.save_fields(field_document, dict(data, fields=[]))
        self.assertEqual(before, field_document.path.read_bytes())

    def test_cancelled_validation_does_not_publish_a_rule_file(self):
        import threading

        document = self.editor.rules("define/options")
        stop = threading.Event()
        stop.set()
        with self.assertRaisesRegex(ConfigError, "cancelled"):
            self.editor.save_rules(document, document.data, cancel=stop)
        self.assertFalse(document.path.exists())
