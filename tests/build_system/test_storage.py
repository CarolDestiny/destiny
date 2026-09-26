import unittest

from tool.auto_define_config.errors import ConfigError
from tool.build_support.storage import (
    contained_path,
    create_missing,
    fingerprint,
    read_json,
    replace_checked,
)
from tests.build_system.support import Workspace


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.addCleanup(self.workspace.close)

    def test_replace_detects_external_edit_and_keeps_newer_file(self):
        path = self.workspace.write("settings.json", "one\n")
        expected = fingerprint(path)
        path.write_text("outside\n", encoding="utf-8")
        with self.assertRaisesRegex(ConfigError, "changed outside"):
            replace_checked(path, "two\n", expected=expected)
        self.assertEqual(path.read_text(), "outside\n")

    def test_unchanged_write_preserves_timestamp(self):
        path = self.workspace.write("settings.json", "one\n")
        before = path.stat().st_mtime_ns
        self.assertFalse(replace_checked(path, "one\n", expected=fingerprint(path)))
        self.assertEqual(before, path.stat().st_mtime_ns)

    def test_create_does_not_overwrite(self):
        path = self.workspace.root / "new/probe.py"
        self.assertTrue(create_missing(path, "original"))
        self.assertFalse(create_missing(path, "replacement"))
        self.assertEqual(path.read_text(), "original")

    def test_json_duplicates_and_nonfinite_numbers_fail(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            path = self.workspace.write("bad.json", text)
            with self.assertRaises(ConfigError):
                read_json(path)

    def test_managed_paths_cannot_escape(self):
        with self.assertRaises(ConfigError):
            contained_path(self.workspace.root, "../outside.txt")

    def test_failed_skeleton_publication_leaves_no_partial_file(self):
        from unittest.mock import patch

        path = self.workspace.root / "new/probe.py"
        with patch("tool.build_support.storage.os.link", side_effect=OSError("failed publication")):
            with self.assertRaises(OSError):
                create_missing(path, "complete content")
        self.assertFalse(path.exists())
        self.assertEqual(list(path.parent.iterdir()), [])
