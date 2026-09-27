"""A representative throwaway module graph used by the native compiler matrix."""

from __future__ import annotations

import json
import shutil

from .support import ROOT, Workspace
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer


def prepare_scenario(workspace: Workspace) -> None:
    w = workspace
    shutil.copytree(ROOT / "thirdLib/googletest", w.root / "thirdLib/googletest")
    for module in ("define/platform", "define/cpu", "define/memory"):
        w.module(module, "destiny_add_module(INTERFACE CXX_STANDARD 17)")
    Synchronizer(load_inventory(w.root)).apply()
    providers = {
        "platform": (
            "platform",
            "platform_facts(context)",
            [(name, "boolean", None) for name in ("windows", "linux", "macos", "x86", "x64")],
        ),
        "cpu": (
            "cpu",
            "cpu_facts(context)",
            [
                (name, "boolean", None)
                for name in ("cpuIntel", "cpuAMD", "avx2", "avx512f", "avx512bw")
            ],
        ),
        "memory": ("memory", "memory_facts()", [("memory.total_bytes", "integer", "bytes")]),
    }
    for name, (provider, expression, definitions) in providers.items():
        fields = []
        for identifier, kind, unit in definitions:
            macro = identifier.upper().replace(".", "_")
            item = {
                "id": identifier,
                "type": kind,
                "macro": "DESTINY_DEFINE_CMAKE_" + macro,
                "alias": "DESTINY_DEFINE_" + macro,
                "description": "Validation observation: " + identifier,
            }
            if unit:
                item["unit"] = unit
            fields.append(item)
        w.write(
            f"tool/auto_define_config/define/{name}/fields.json",
            json.dumps({"schema_version": 1, "module": "define/" + name, "fields": fields}),
        )
        function = expression.split("(")[0]
        w.write(
            f"tool/auto_define_config/define/{name}/probe.py",
            f"from tool.auto_define_config.providers.{provider} import {function}\n"
            f"def probe(context):\n    return {expression}\n",
        )
    w.module(
        "iso/hardware/cpu",
        "destiny_add_module(CXX_STANDARD 20)\n"
        "destiny_depends(PUBLIC define/platform define/cpu define/memory)",
    )
    w.write(
        "source/iso/hardware/cpu/include/cpu.hpp",
        "#pragma once\nint selected_width();\nint selected_platform();\n",
    )
    prefix = "source/iso/hardware/cpu/"
    w.write(prefix + "src/scalar_while_portable.cpp", "int selected_width() { return 0; }\n")
    w.write(
        prefix + "src/narrow_while_narrow.cpp",
        "#include <immintrin.h>\nint selected_width() { __m256i v=_mm256_set1_epi32(256); return _mm256_extract_epi32(v,0); }\n",
    )
    w.write(
        prefix + "src/wide_while_wide.cpp",
        "#include <immintrin.h>\nint selected_width() { __m512i v=_mm512_set1_epi32(512); return _mm_cvtsi128_si32(_mm512_castsi512_si128(v)); }\n",
    )
    for name, value in (("windows", 1), ("linux", 2), ("macos", 3)):
        w.write(
            prefix + f"src/process_while_{name}.cpp",
            f"int selected_platform() {{ return {value}; }}\n",
        )
    rules = {
        "schema_version": 1,
        "aliases": {
            "wide": {"ref": "avx512f"},
            "narrow": {"ref": "avx2"},
            "portable": True,
            "large": {
                "compare": {
                    "field": "memory.total_bytes",
                    "op": "ge",
                    "value": "1073741824",
                    "unit": "bytes",
                }
            },
        },
        "groups": [
            {
                "name": "cpu_backend",
                "candidates": [
                    {
                        "name": "wide",
                        "when": {"ref": "wide"},
                        "sources": ["src/wide_while_wide.cpp"],
                    },
                    {
                        "name": "narrow",
                        "when": {"ref": "narrow"},
                        "sources": ["src/narrow_while_narrow.cpp"],
                    },
                    {"name": "scalar", "when": True, "sources": ["src/scalar_while_portable.cpp"]},
                ],
            },
            {
                "name": "process_backend",
                "candidates": [
                    {
                        "name": name,
                        "when": {"ref": name},
                        "sources": [f"src/process_while_{name}.cpp"],
                    }
                    for name in ("windows", "linux", "macos")
                ],
            },
        ],
    }
    w.write(prefix + "source_rules.json", json.dumps(rules))
    w.write(prefix + "src/capacity_while_large.cpp", "int capacity_feature() { return 1; }\n")
    w.module(
        "core/api",
        "destiny_add_module(CXX_STANDARD 23 PUBLIC_CXX_STANDARD 20)\n"
        "destiny_depends(PUBLIC iso/hardware/cpu)\n"
        "destiny_add_program(demo sample SOURCES demo/main.cpp demo/helper.cpp)",
    )
    w.write("source/core/api/include/api.hpp", "#pragma once\nint api();\n")
    w.write(
        "source/core/api/src/api.cpp",
        "#include <destiny/iso/hardware/cpu/cpu.hpp>\n"
        "static_assert(__cplusplus > 202002L);\nint api() { return selected_width(); }\n",
    )
    w.write(
        "source/core/api/demo/main.cpp",
        "#include <iostream>\n#include <destiny/core/api/api.hpp>\n"
        "int helper();\nint main() { if (helper()!=7) return 2; std::cout << api(); }\n",
    )
    w.write("source/core/api/demo/helper.cpp", "int helper() { return 7; }\n")
    w.write(
        "source/core/api/bench/basic.cpp",
        "#include <destiny/core/api/api.hpp>\nint main() { return api()<0; }\n",
    )
    w.write("matrix-resource.txt", "Project root resource\n")
    w.write(
        "source/core/api/test/matrix.cpp",
        r"""#include <gtest/gtest.h>
#include <filesystem>
#include <fstream>
#if defined(__linux__)
#include <sys/stat.h>
#endif
#include <destiny/core/api/api.hpp>
#include <destiny/iso/hardware/cpu/cpu.hpp>
#include <destiny/define/platform/cmake_config.hpp>
#include <destiny/define/cpu/cmake_config.hpp>
#include <destiny/define/memory/cmake_config.hpp>
struct Startup {
    Startup() { std::ofstream("runtime-started.txt",std::ios::app) << std::filesystem::current_path().string() << '\n'; }
};
Startup startup;
TEST(Matrix, SelectedImplementationMatchesMacros) {
    EXPECT_EQ(api(), DESTINY_DEFINE_AVX512F ? 512 : DESTINY_DEFINE_AVX2 ? 256 : 0);
    EXPECT_EQ(selected_platform(), DESTINY_DEFINE_WINDOWS ? 1 : DESTINY_DEFINE_LINUX ? 2 : 3);
    EXPECT_GT(DESTINY_DEFINE_MEMORY_TOTAL_BYTES,0LL);
}
TEST(Matrix, FileMetadataAbi) {
#if defined(__linux__)
    struct stat info {};
    EXPECT_EQ(stat(".",&info),0);
    if (sizeof(void*)==4) EXPECT_GE(sizeof(info.st_ino),8u);
#endif
}
TEST(Matrix, WorkingDirectoryAndTargetWidth) {
    EXPECT_TRUE(std::filesystem::exists("matrix-resource.txt"));
    EXPECT_EQ(sizeof(void*)*8,DESTINY_DEFINE_X86 ? 32u : 64u);
}
""",
    )
