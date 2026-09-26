# Extending the Build Without Central Registries

Updated: 2026-09-26

This recipe assumes the empty business-source tree, or that the example module/field names are unused. Paths are repository-relative. Do not overwrite a real module with the example. The validation runner recreates these files only in an isolated build workspace and removes them afterward; they are not shipped as production modules.

## 1. Register a define module and scaffold its counterpart

File: `source/define/memory/CMakeLists.txt`

```cmake
destiny_add_module(INTERFACE CXX_STANDARD 17)
```

Run from the project root:

```text
python -B -m tool.auto_define_config inventory
python -B -m tool.auto_define_config sync --dry-run
python -B -m tool.auto_define_config sync
```

The registered module creates exactly `tool/auto_define_config/define/memory/probe.py` and `fields.json`. Intermediate grouping folders need no registration. Synchronization creates missing files only; it will not replace the following maintained implementation once you write it.

File: `tool/auto_define_config/define/memory/fields.json`

```json
{
  "schema_version": 1,
  "module": "define/memory",
  "fields": [
    {
      "id": "memory.total_bytes",
      "type": "integer",
      "unit": "bytes",
      "macro": "DESTINY_DEFINE_CMAKE_MEMORY_TOTAL_BYTES",
      "alias": "DESTINY_DEFINE_MEMORY_TOTAL_BYTES",
      "description": "Memory visible to the current operating system"
    },
    {
      "id": "fast_buffers",
      "type": "boolean",
      "kind": "option",
      "default": true,
      "macro": "DESTINY_DEFINE_CMAKE_FAST_BUFFERS",
      "description": "Allow the large-buffer implementation"
    }
  ]
}
```

File: `tool/auto_define_config/define/memory/probe.py`

```python
from tool.auto_define_config.contracts import ProbeContext
from tool.auto_define_config.providers.memory import memory_facts


def probe(context: ProbeContext):
    observations = memory_facts()
    return {
        field.id: observations[field.id]
        for field in context.fields
        if field.kind == "observation"
    }
```

Options are supplied by the generic runner, not fabricated by this provider. The provider returns an Observation with a status/reason; unavailable memory is not a real zero. WSL observes guest-visible memory. A future provider can import another shared helper here without a central import-list change.

## 2. Register the consuming module with short public headers

File: `source/iso/buffer/CMakeLists.txt`

```cmake
destiny_add_module(CXX_STANDARD 20 PUBLIC_CXX_STANDARD 17)
destiny_depends(PRIVATE define/memory)
```

File: `source/iso/buffer/include/buffer.hpp`

```cpp
#pragma once
const char* buffer_strategy();
```

The maintained include tree is short. Consumers include `<destiny/iso/buffer/buffer.hpp>` through generated forwarding headers. They inherit only the public C++17 requirement; implementation files use at least C++20. Generated memory headers are private here because the public header does not expose them.

File: `source/iso/buffer/src/large_while_enough_memory.cpp`

```cpp
#include <destiny/iso/buffer/buffer.hpp>
#include <destiny/define/memory/cmake_config.hpp>
static_assert(__cplusplus >= 202002L);
static_assert(DESTINY_DEFINE_MEMORY_TOTAL_BYTES_AVAILABLE);
static_assert(DESTINY_DEFINE_MEMORY_TOTAL_BYTES >= 1073741824);
const char* buffer_strategy() { return "large"; }
```

File: `source/iso/buffer/src/small.cpp`

```cpp
#include <destiny/iso/buffer/buffer.hpp>
const char* buffer_strategy() { return "small"; }
```

File: `source/iso/buffer/source_rules.json`

```json
{
  "schema_version": 1,
  "aliases": {
    "enough_memory": {
      "compare": {
        "field": "memory.total_bytes",
        "op": "ge",
        "value": "1073741824",
        "unit": "bytes"
      }
    }
  },
  "groups": [
    {
      "name": "buffer_strategy",
      "candidates": [
        {
          "name": "large",
          "when": {"all": [{"ref": "enough_memory"}, {"ref": "fast_buffers"}]},
          "sources": ["src/large_while_enough_memory.cpp"]
        },
        {
          "name": "small",
          "when": true,
          "sources": ["src/small.cpp"]
        }
      ]
    }
  ]
}
```

The numeric comparison uses canonical decimal text and an explicit unit. Unknown or unavailable memory makes the comparison false, so the explicitly declared fallback wins. Candidate ordering is meaningful. To extend an implementation across files, put its entry and helper `.cpp` paths in the same candidate; do not also assign them to another candidate. Public headers stay available regardless of the winner.

File: `source/iso/buffer/demo/show.cpp`

```cpp
#include <destiny/iso/buffer/buffer.hpp>
#include <filesystem>
#include <iostream>
int main() {
    std::cout << buffer_strategy() << '\n'
              << std::filesystem::current_path().string() << '\n';
    return std::filesystem::is_regular_file("source/iso/buffer/include/buffer.hpp") ? 0 : 1;
}
```

This direct `.cpp` creates one demo automatically. For multiple translation units, replace automatic entry detection with `destiny_add_program(demo show SOURCES demo/show.cpp demo/helper.cpp)`. Tests use the same declaration, optionally CUSTOM_MAIN; benches impose no benchmark framework. All three categories are independently switchable.

## 3. Configure, inspect, build and run explicitly

Generate a verified local compiler preset using find_compiler, or supply absolute C/C++/Python/Ninja paths to native CMake. No wrapper is required. With a selected preset:

```text
python -B -m tool.auto_define_config check
cmake --preset <configure-preset>
cmake --build --preset <build-preset>
cmake --build <binary-directory> --target destiny_source_report
cmake -E chdir <absolute-project-root> <absolute-binary-directory>/iso/buffer/demo/show[.exe]
```

Inspect `generated/facts.json`, the memory `cmake_config.hpp` under `generated/config`, and `reports/source-selection-<configuration>.json`. The same measured integer must appear in the facts and header; exactly one implementation must be selected. Context-sensitive mode checks appear in `compilation_contexts`, not as a misleading shared standard macro. Build does not run the demo. CLION.md documents run templates and native CTest working directories.

Run a probe or preview without editing maintained files:

```text
python -B -m tool.auto_define_config probe --module define/memory --context <binary-directory>/generated/probe-context.json
python -B -m tool.auto_define_config preview --module iso/buffer --facts <binary-directory>/generated/facts.json
python -B -m tool.auto_define_config gui
```

In the GUI, select define/memory to inspect observations or edit the declared `fast_buffers` option. Select iso/buffer to edit/preview rules. Save persistent declarations/options, then reload CMake. Hardware facts and macro previews are read-only; simulations never replace build facts. The project-local option override is `cache/auto_define_config/options.json`, not fields.json or a generated header.

## 4. Safe incremental changes

- **Add a field:** declare an unused global ID, type/unit, generated macro and optional alias; implement only its observation; add available/unavailable/error fixtures. Reload CMake and assert facts, macros and source selection. No central GUI or macro-template edits are needed.
- **Add a layer:** edit the single `destiny_register_layers(define iso core ...)` declaration in cmake/DestinyLayers.cmake. Edges must still point strictly downward. Do not circumvent the registry with raw target mutations in module registrations.
- **Remove a module:** remove its registration and dependencies intentionally. Check reports its counterpart as orphaned, does not execute it, and removes obsolete generated macros at configure. Maintained orphaned files are not deleted automatically.
- **Rename a define module:** change the source registration/dependencies explicitly first. Inspect inventory and the old-orphan/new-missing state. Do not sync the new counterpart before migration. Run `python -B -m tool.auto_define_config rename define/old define/new --dry-run`, review conflicts, then repeat without --dry-run. Only the counterpart is migrated and fields.json's module identity changes; handwritten probe code is preserved. Review any identifiers or references inside that code separately.
- **Change schema/macros:** follow PYTHON_MAINTENANCE.md section 6. Invalid references or exported-name collisions must fail before overwriting a maintained file. Never hand-edit generated output to hide drift.

Validate focused tests first, then the full regression and applicable real compiler profiles. Record actual outcomes, source fingerprints and skips in VALIDATION.md. Code under source remains user-owned: cleanup must name only the temporary fixture that was created.

## 5. Re-run the exact documentation example

The regression reads the nine `File:` code blocks above, scaffolds the missing define counterpart, builds those exact files, checks observations/macros/selection, and executes the demo with `cmake -E chdir` from the binary directory. It then disables the declared user option and verifies the fallback. Nothing is added to the checkout's maintained source tree.

```text
python -B -m unittest tests.build_system.test_extension_recipe -v
```

The full verification command also includes this test. Source fingerprints include this recipe document so the recorded result refers to the actual example, not merely similar test code.
