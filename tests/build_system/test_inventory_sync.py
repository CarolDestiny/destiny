import importlib.util
import unittest
from pathlib import Path

from tool.auto_define_config.errors import ConfigError
from tool.auto_define_config.inventory import load_inventory
from tool.build_support.storage import fingerprint
from tool.auto_define_config.sync import Synchronizer
from tests.build_system.support import Workspace


class InventorySyncTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.addCleanup(self.workspace.close)

    def test_registry_orders_layers_and_resolves_standards(self):
        self.workspace.module(
            "core/top", "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PRIVATE iso/cpu)"
        )
        self.workspace.module(
            "iso/cpu",
            "destiny_add_module(CXX_STANDARD 23 PUBLIC_CXX_STANDARD 20)\ndestiny_depends(PUBLIC define/platform)",
        )
        self.workspace.module("define/platform", "destiny_add_module(INTERFACE CXX_STANDARD 17)")
        inventory = load_inventory(self.workspace.root)
        self.assertEqual(
            [m.path for m in inventory.modules], ["define/platform", "iso/cpu", "core/top"]
        )
        top = inventory.modules[-1]
        self.assertEqual(top.effective_cxx_standard, 20)
        self.assertEqual(top.effective_public_cxx_standard, 17)

    def test_same_layer_dependency_fails(self):
        self.workspace.module("iso/a", "destiny_add_module()\ndestiny_depends(PUBLIC iso/b)")
        self.workspace.module("iso/b")
        with self.assertRaisesRegex(ConfigError, "strictly lower layer"):
            load_inventory(self.workspace.root)

    def test_unknown_dependency_fails(self):
        self.workspace.module(
            "core/a", "destiny_add_module()\ndestiny_depends(PUBLIC define/missing)"
        )
        with self.assertRaisesRegex(ConfigError, "Unknown dependency"):
            load_inventory(self.workspace.root)

    def test_sync_incremental_and_preserves_written_logic(self):
        self.workspace.module("define/hardware/cpu")
        self.workspace.module("iso/cpu")
        service = Synchronizer(load_inventory(self.workspace.root))
        self.assertEqual([item.status for item in service.inspect()], ["missing", "missing"])
        self.assertFalse(service.root.exists())
        with self.assertRaisesRegex(ConfigError, "Run auto_define_config sync"):
            service.check()
        self.assertEqual([item.status for item in service.apply()], ["created", "created"])
        probe = service.root / "hardware/cpu/probe.py"
        source = probe.read_text(encoding="utf-8")
        self.assertIn("def probe(context: ProbeContext)", source)
        probe.write_text(
            source + "\n# Maintained code must survive synchronization.\n", encoding="utf-8"
        )
        before = fingerprint(probe)
        self.assertTrue(all(item.status == "unchanged" for item in service.apply()))
        self.assertEqual(before, fingerprint(probe))
        fields = probe.with_name("fields.json")
        fields.unlink()
        self.assertEqual([item.status for item in service.apply()], ["unchanged", "created"])
        self.assertEqual(before, fingerprint(probe))
        service.check()

    def test_orphans_are_preserved_and_inactive(self):
        registration = self.workspace.module("define/platform")
        service = Synchronizer(load_inventory(self.workspace.root))
        service.apply()
        registration.unlink()
        orphaned = Synchronizer(load_inventory(self.workspace.root))
        self.assertTrue(all(item.status == "orphaned" for item in orphaned.check()))
        self.assertEqual(orphaned.declarations(), ())
        self.assertEqual(len(list(orphaned.root.rglob("*.py"))), 1)

    def test_conflict_prevents_partial_sync(self):
        self.workspace.module("define/cpu")
        service = Synchronizer(load_inventory(self.workspace.root))
        (service.root / "cpu/probe.py").mkdir(parents=True)
        with self.assertRaisesRegex(ConfigError, "conflicts"):
            service.apply()
        self.assertFalse((service.root / "cpu/fields.json").exists())

    def test_layers_can_be_extended_in_one_place(self):
        self.workspace.write(
            "cmake/DestinyLayers.cmake", "destiny_register_layers(define iso core app)\n"
        )
        self.workspace.module(
            "app/program", "destiny_add_module()\ndestiny_depends(PUBLIC core/base)"
        )
        self.workspace.module("core/base")
        inventory = load_inventory(self.workspace.root)
        self.assertEqual(inventory.layers[-1], "app")

    def test_duplicate_registration_fails(self):
        self.workspace.module("define/cpu", "destiny_add_module()\ndestiny_add_module()")
        with self.assertRaisesRegex(ConfigError, "registered twice"):
            load_inventory(self.workspace.root)

    def test_file_in_parent_path_prevents_partial_scaffolding(self):
        self.workspace.module("define/a")
        self.workspace.module("define/hardware/cpu")
        service = Synchronizer(load_inventory(self.workspace.root))
        self.workspace.write("tool/auto_define_config/define/hardware", "not a directory")
        with self.assertRaisesRegex(ConfigError, "conflicts"):
            service.apply()
        self.assertFalse((service.root / "a/probe.py").exists())

    def test_upward_self_and_unknown_layer_fail(self):
        path = self.workspace.module("iso/a")
        self.workspace.module("core/upper")
        for dependency in ("core/upper", "iso/a"):
            path.write_text(f"destiny_add_module()\ndestiny_depends(PRIVATE {dependency})\n")
            with self.assertRaisesRegex(ConfigError, "strictly lower layer"):
                load_inventory(self.workspace.root)
        path.write_text("destiny_add_module()\n")
        self.workspace.module("unregistered/a")
        with self.assertRaisesRegex(ConfigError, "Unknown layer"):
            load_inventory(self.workspace.root)
