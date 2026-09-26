from pathlib import Path
import struct
import unittest

from tests.build_system.support import Workspace
from tool.build_support.errors import BuildError
from tool.build_support.pe import read_pe
from tool.build_support.runtime import resolve_dependencies, stage_runtime


def pe_fixture(path: Path, *, architecture="x64", imports=(), delay_imports=(), marker=0):
    """Construct only PE metadata; fixture executables are never run."""
    data = bytearray(8192)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 128)
    data[128:132] = b"PE\0\0"
    x86 = architecture == "x86"
    optional = 152
    size = 224 if x86 else 240
    struct.pack_into("<HH", data, 132, 0x14C if x86 else 0x8664, 1)
    struct.pack_into("<H", data, 148, size)
    struct.pack_into("<H", data, optional, 0x10B if x86 else 0x20B)
    struct.pack_into("<I" if x86 else "<Q", data, optional + (28 if x86 else 24), 0x400000)
    struct.pack_into("<I", data, optional + 60, 512)
    directories = optional + (96 if x86 else 112)
    struct.pack_into("<I", data, directories - 4, 16)
    section = optional + size
    struct.pack_into("<IIII", data, section + 8, 7680, 4096, 7680, 512)
    text_offset = 2048
    for index, names, stride, start in ((1, imports, 20, 512), (13, delay_imports, 32, 1024)):
        if not names:
            continue
        struct.pack_into(
            "<II", data, directories + 8 * index, start - 512 + 4096, (len(names) + 1) * stride
        )
        for position, name in enumerate(names):
            encoded = name.encode("ascii") + b"\0"
            data[text_offset : text_offset + len(encoded)] = encoded
            rva = text_offset - 512 + 4096
            if index == 1:
                struct.pack_into("<IIIII", data, start + position * stride, 1, 0, 0, rva, 1)
            else:
                struct.pack_into(
                    "<IIIIIIII", data, start + position * stride, 1, rva, 0, 1, 1, 0, 0, 0
                )
            text_offset += len(encoded)
    data[-1] = marker
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace()
        self.addCleanup(self.w.close)
        self.compiler = self.w.write("toolchain/bin/g++.exe", "")
        self.bin = self.compiler.parent
        self.output = self.w.root / "out/program.exe"

    def test_pe_architecture_regular_and_delay_imports(self):
        for architecture in ("x86", "x64"):
            with self.subTest(architecture=architecture):
                pe_fixture(
                    self.output,
                    architecture=architecture,
                    imports=("A.DLL",),
                    delay_imports=("B.dll",),
                )
                self.assertEqual(read_pe(self.output).architecture, architecture)
                self.assertEqual(read_pe(self.output).imports, ("a.dll", "b.dll"))

    def test_invalid_or_truncated_image_is_rejected(self):
        for data in (b"", b"MZ", b"MZ" + bytes(100)):
            self.output.parent.mkdir(exist_ok=True)
            self.output.write_bytes(data)
            with self.assertRaises(BuildError):
                read_pe(self.output)

    def test_transitive_runtime_staging_and_system_exclusion(self):
        pe_fixture(self.output, imports=("a.dll", "kernel32.dll"))
        pe_fixture(self.bin / "a.dll", imports=("b.dll",))
        pe_fixture(self.bin / "b.dll")
        system = self.w.root / "system"
        pe_fixture(system / "kernel32.dll")
        result = stage_runtime(
            self.output, self.compiler, self.w.root / "out", system_roots=(system,)
        )
        self.assertEqual(set(result.files), {"a.dll", "b.dll"})
        self.assertFalse((self.output.parent / "kernel32.dll").exists())
        before = (self.output.parent / "a.dll").stat().st_mtime_ns
        stage_runtime(self.output, self.compiler, self.w.root / "out", system_roots=(system,))
        self.assertEqual(before, (self.output.parent / "a.dll").stat().st_mtime_ns)

    def test_wrong_architecture_and_missing_runtime_fail(self):
        pe_fixture(self.output, imports=("a.dll",))
        with self.assertRaisesRegex(BuildError, "Missing x64"):
            resolve_dependencies(self.output, ((self.bin,),), system_roots=())
        pe_fixture(self.bin / "a.dll", architecture="x86")
        with self.assertRaisesRegex(BuildError, "incompatible candidates"):
            resolve_dependencies(self.output, ((self.bin,),), system_roots=())

    def test_target_runtime_precedence_and_equal_priority_conflicts(self):
        pe_fixture(self.output, imports=("a.dll",))
        pe_fixture(self.bin / "a.dll", marker=1)
        target = self.w.root / "toolchain/x86_64-w64-mingw32/bin"
        chosen = pe_fixture(target / "a.dll", marker=2)
        result = stage_runtime(self.output, self.compiler, self.w.root / "out", system_roots=())
        self.assertEqual(result.files["a.dll"], chosen.resolve())
        with self.assertRaisesRegex(BuildError, "equal-priority"):
            resolve_dependencies(self.output, ((target, self.bin),), system_roots=())

    def test_modified_destination_is_not_overwritten(self):
        pe_fixture(self.output, imports=("a.dll",))
        pe_fixture(self.bin / "a.dll", marker=1)
        pe_fixture(self.output.parent / "a.dll", marker=2)
        original = (self.output.parent / "a.dll").read_bytes()
        with self.assertRaisesRegex(BuildError, "not created by this tool"):
            stage_runtime(self.output, self.compiler, self.w.root / "out", system_roots=())
        self.assertEqual(original, (self.output.parent / "a.dll").read_bytes())

    def test_shared_runtime_is_not_deleted_while_another_program_owns_it(self):
        pe_fixture(self.output, imports=("a.dll",))
        other = pe_fixture(self.output.parent / "other.exe", imports=("a.dll",))
        pe_fixture(self.bin / "a.dll")
        stage_runtime(self.output, self.compiler, self.w.root / "out", system_roots=())
        stage_runtime(other, self.compiler, self.w.root / "out", system_roots=())
        pe_fixture(self.output)
        stage_runtime(self.output, self.compiler, self.w.root / "out", system_roots=())
        self.assertTrue((self.output.parent / "a.dll").exists())
        pe_fixture(other)
        stage_runtime(other, self.compiler, self.w.root / "out", system_roots=())
        self.assertFalse((self.output.parent / "a.dll").exists())
