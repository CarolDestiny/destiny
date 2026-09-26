"""Read PE architecture/import metadata without loading or executing binaries.

Layout reference: Microsoft PE/COFF specification. Normal and delay-import
names are resolved from checked section RVAs; executable code is never loaded.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct

from .errors import BuildError


@dataclass(frozen=True)
class PeImage:
    architecture: str
    imports: tuple[str, ...]


def read_pe(path: Path) -> PeImage:
    try:
        return _Reader(path.read_bytes()).image()
    except (OSError, ValueError, struct.error, UnicodeError) as exc:
        raise BuildError(f"Cannot inspect PE image {path}: {exc}") from exc


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.sections: list[tuple[int, int, int]] = []
        self.header_size = 0

    def unpack(self, fmt: str, offset: int) -> tuple:
        size = struct.calcsize(fmt)
        if offset < 0 or offset + size > len(self.data):
            raise ValueError("Truncated or invalid image offset")
        return struct.unpack_from(fmt, self.data, offset)

    def offset(self, rva: int, size: int = 1) -> int:
        if 0 <= rva and rva + size <= self.header_size:
            result = rva
        else:
            matches = [
                raw + rva - address
                for address, raw_size, raw in self.sections
                if address <= rva and rva + size <= address + raw_size
            ]
            if len(matches) != 1:
                raise ValueError(f"RVA {rva:#x} is outside a unique file-backed section")
            result = matches[0]
        if result < 0 or result + size > len(self.data):
            raise ValueError("RVA references bytes outside the file")
        return result

    def dll_name(self, rva: int) -> str:
        start = self.offset(rva)
        end = self.data.find(b"\0", start, min(start + 512, len(self.data)))
        if end < 0:
            raise ValueError("Unterminated DLL name")
        self.offset(rva, end - start + 1)
        name = self.data[start:end].decode("ascii")
        if (
            not name
            or not name.lower().endswith(".dll")
            or any(c in name for c in "/\\:;")
            or any(ord(c) < 32 for c in name)
        ):
            raise ValueError(f"Invalid imported DLL basename: {name!r}")
        return name.lower()

    def image(self) -> PeImage:
        if self.data[:2] != b"MZ":
            raise ValueError("Missing DOS signature")
        (pe,) = self.unpack("<I", 0x3C)
        if self.data[pe : pe + 4] != b"PE\0\0":
            raise ValueError("Missing PE signature")
        machine, count = self.unpack("<HH", pe + 4)
        (optional_size,) = self.unpack("<H", pe + 20)
        optional = pe + 24
        (magic,) = self.unpack("<H", optional)
        architecture = {0x14C: "x86", 0x8664: "x64", 0xAA64: "arm64"}.get(machine)
        if architecture is None or magic not in (0x10B, 0x20B):
            raise ValueError(f"Unsupported machine/optional header: {machine:#x}/{magic:#x}")
        if (architecture == "x86") != (magic == 0x10B):
            raise ValueError("Machine and PE32/PE32+ format disagree")
        directories = optional + (96 if magic == 0x10B else 112)
        (number,) = self.unpack("<I", directories - 4)
        if number > 16 or directories + number * 8 > optional + optional_size:
            raise ValueError("Invalid optional-header directory count")
        (self.header_size,) = self.unpack("<I", optional + 60)
        if not 0 < self.header_size <= len(self.data) or not 0 < count <= 96:
            raise ValueError("Invalid header or section count")
        (base,) = self.unpack(
            "<I" if magic == 0x10B else "<Q", optional + (28 if magic == 0x10B else 24)
        )
        for index in range(count):
            section = optional + optional_size + 40 * index
            virtual, address, raw_size, raw = self.unpack("<IIII", section + 8)
            self.sections.append((address, raw_size, raw))
        names = set()
        for directory_index, stride in ((1, 20), (13, 32)):
            if directory_index >= number:
                continue
            rva, size = self.unpack("<II", directories + directory_index * 8)
            if rva == 0 and size == 0:
                continue
            if not rva or size < stride:
                raise ValueError("Invalid import-directory location/size")
            terminated = False
            for offset in range(0, min(size, 1024 * 1024), stride):
                if offset + stride > size:
                    break
                descriptor = self.unpack(
                    "<" + "I" * (stride // 4), self.offset(rva + offset, stride)
                )
                if not any(descriptor):
                    terminated = True
                    break
                if directory_index == 1:
                    name_rva = descriptor[3]
                else:
                    attributes, name_rva = descriptor[:2]
                    if attributes not in (0, 1):
                        raise ValueError("Unsupported delay-import attributes")
                    if not attributes:
                        name_rva -= base
                names.add(self.dll_name(name_rva))
            if not terminated:
                raise ValueError("Unterminated or oversized import directory")
        return PeImage(architecture, tuple(sorted(names)))
