# Build Interfaces and Data Contracts

Updated: 2026-09-26
Status: Accepted v1 interfaces. See ACCEPTANCE.md and VALIDATION.md for evidence and environment limits.

## 1. Architecture and ownership

CMake owns module declarations, dependency/standard resolution, condition evaluation, target construction and C++ configuration-header generation. Python owns discovery, typed observations, safe declaration edits and GUI coordination. Neither GUI implements a second selection evaluator.

| Module | Interface and responsibility |
| --- | --- |
| cmake/DestinyRegistry.cmake | Collect declarations, validate layer graph, resolve public/private minimum standards, export modules.json |
| cmake/DestinyExpressions.cmake / DestinySelection.cmake | Typed expressions, local aliases, ordered candidates; also usable in script mode |
| cmake/DestinyTargets.cmake / DestinyPrograms.cmake | Native target construction from resolved module data |
| cmake/DestinyConfigHeader.cmake | Shared native-build/header-preview generator |
| tool/build_support | Bounded subprocesses, guarded JSON storage, compiler metadata, PE/runtime inspection, Tk worker coordination |
| tool/find_compiler | Discovery, real validation, local preset ownership and GUI |
| tool/auto_define_config | Inventory adapter, declarations/probes, synchronization, editor transactions, rule/header preview and GUI |

The CMake inventory script evaluates the same declarations as a real configure. Python does not parse CMake text or maintain an independent import list. Presentation modules depend on headless services; headless commands never initialize Tk.

Maintained files are registrations, fields.json, probe.py and source_rules.json. CMake configure reads them without editing them. Facts, generated headers, runtime receipts and reports are disposable binary-directory output. GUI-local option overrides are not hardware observations and are stored outside maintained source.

## 2. Native module interface

A module is a directory below source with a CMakeLists.txt containing declarative calls. Grouping directories need no registration. Register default layer order in cmake/DestinyLayers.cmake:

```cmake
destiny_register_layers(define iso core)
```

Module example:

```cmake
destiny_add_module(CXX_STANDARD 23 PUBLIC_CXX_STANDARD 20)
destiny_depends(PUBLIC define/platform)
destiny_depends(PRIVATE define/compiler)
```

Each destiny_depends call accepts exactly one scope.

- destiny_add_module optionally begins with AUTO, STATIC or INTERFACE. AUTO uses selected implementation presence; STATIC without selected sources fails; INTERFACE with implementation sources fails.
- Omitted CXX_STANDARD is 20. PUBLIC_CXX_STANDARD defaults to it. Values are minima, not forced exact compiler dialects. Accepted identifiers: 98, 11, 14, 17, 20, 23, 26, subject to actual CMake/compiler support.
- Public requirements propagate. Private requirements can raise implementation compilation without raising downstream consumers. Header-only modules expose one public requirement and reject explicitly inconsistent minima.
- Dependencies identify registered module paths and must point to strictly lower layers. Discovery order cannot legalize a missing, same-layer, self or upward edge.
- Registration runs in script mode too: use the declarative interface, not arbitrary add_library/target commands in module registration files.
- Alias target iso/hardware/cpu is destiny::iso::hardware::cpu. Concrete target names contain a readable path and a short path hash.
- Physical include/cpu.hpp maps to <destiny/iso/hardware/cpu/cpu.hpp> through module-specific forwarding headers. Relative includes inside the maintained header continue to work. Include roots propagate only through declared dependencies.
- Generated define headers are <destiny/define/<module>/cmake_config.hpp>. Maintained include/cmake_config.hpp is reserved to prevent collisions.
- Linux x86 targets use _FILE_OFFSET_BITS=64 consistently, including vendored GoogleTest. This avoids 32-bit stat inode overflow on WSL/mounted filesystems and is a file-ABI requirement, not an optimization flag.

### Compilation contexts

`cmake/DestinyCompileContext.cmake` runs after dependency/minimum-standard resolution and before facts or source selection. Each distinct context compile-checks the required C++ mode without executing a program. A rejected or unadvertised mode fails configuration; it cannot select an older standard as a fallback. The native-CPU and platform ABI options come from the same policy functions used by project targets.

The CMake check cache key covers the C++ driver content hash, compiler identity/path/target, architecture, minimum standard, configuration flags, project options, relevant environment and SDK settings. Identical contexts can share a check within one binary directory; changed contexts get a different cache entry. The source check tests the minimum `__cplusplus` mode, not complete language/library conformance or an exact actual dialect.

`generated/probe-context.json` contains `compilation_contexts`, keyed by registered module path. Probe implementations can inspect `context.target["compilation_contexts"]` when a build context is supplied. The same optional member is preserved in `facts.json`, separately from declared hardware/option fields. Reports attach each module's context and cache key. It does not become a global C++-standard macro or a source-condition field. CLI probes without a build context do not fabricate this data.

Shared ISA observations describe CPU/OS support intersected with the selected compiler's project-wide ISA flags. The probe helper itself deliberately uses a baseline dialect and no native instruction optimization. Per-module dialect checks remain separate: neither acceptance of a mode nor a shared ISA flag claims support for arbitrary feature/library snippets.

## 3. Program declarations and execution

All three category switches default ON:

```text
DESTINY_BUILD_TESTS
DESTINY_BUILD_BENCHMARKS
DESTINY_BUILD_DEMOS
```

Each direct category .cpp normally creates one executable. For multiple files:

```cmake
destiny_add_program(demo sample
    SOURCES demo/main.cpp demo/support.cpp
    DEPENDS define/platform
    CXX_STANDARD 23)

destiny_add_program(test suite CUSTOM_MAIN
    SOURCES test/main.cpp test/cases.cpp)
```

Explicit sources are excluded from automatic standalone-program discovery. Source paths are canonical module-relative paths below that category. Additional module dependencies must point down the layer graph. Programs inherit at least the owner's effective implementation minimum; additional requirements may raise it.

GoogleTest sources are vendored at thirdLib/googletest, with provenance and per-file hashes in thirdLib/googletest.provenance.json. Default tests link gtest_main; CUSTOM_MAIN links gtest. No configure-time network download or package manager is used. Discovery is PRE_TEST; ordinary Build never launches project programs.

Outputs remain under <binary>/<module>/{test,bench,demo}, libraries under <binary>/lib/<module>, intermediates under <binary>/.obj, and generated data/reports under <binary>/generated and <binary>/reports. Custom CLion binary directories are respected.

CTest and explicit root-directory terminal launches run in the project root. CLion CMake Application and Google Test launchers require their own Working directory setting; use $PROJECT_DIR$ when this checkout is the IDE project. See CLION.md. Printing a working-directory field in a report does not force arbitrary direct execution.

On Windows each link stages only the transitive non-system DLLs required by the executable. Search tiers are the selected target-triple bin, the compiler driver bin, then explicitly supplied DESTINY_RUNTIME_DIRS. Wrong architectures are excluded; conflicting candidates within a tier fail. Receipts protect modified/unmanaged destination DLLs and shared ownership. No system PATH changes or full-directory copying.

## 4. Compiler tool CLI

Run from the checkout root:

```text
python -B -m tool.find_compiler gui
python -B -m tool.find_compiler scan --root <toolchain-directory> --output build/compilers.json
python -B -m tool.find_compiler validate --c <gcc-or-clang> --cxx <g++-or-clang++> --arch x86 --output build/manual.json
python -B -m tool.find_compiler write-presets --input build/compilers.json --select <identity>
```

scan includes PATH/default locations unless --no-defaults is supplied. Bounded directory scans never search every disk. Compiler families come from predefines, not driver filenames. Each result separates startup/identity, C compilation, C++20 compilation, linking, architecture, runtime staging and execution failures.

A scan lists the four requested family/architecture slots plus individual candidates. Summary states distinguish available, failed/unavailable, not found by a completed scan, and unchecked by a manual validation. A rescan replaces its old observations rather than retaining stale availability. Missing combinations do not block available ones. --select can repeat; without selections write-presets exports all available report candidates. Export revalidates the executable pair and rejects changed identities.

CMakePresets.json contains the shared hidden destiny-base. CMakeUserPresets.json is local and ignored. Generated entries include stable compiler identities, separate binary directories, compiler flags, Python/Ninja paths, environment isolation and host conditions. Updating managed entries preserves user entries and other-platform configurations; incompatible schema versions or unowned name collisions fail instead of overwriting.

CLI exits: 0 success/at least one available compiler; 1 completed validation with no usable combination; 2 malformed configuration or operational failure. Delivered tools never install compilers or system packages.

## 5. auto_define_config CLI and correspondence

Global options precede the subcommand:

```text
python -B -m tool.auto_define_config inventory
python -B -m tool.auto_define_config sync --dry-run
python -B -m tool.auto_define_config sync
python -B -m tool.auto_define_config check
python -B -m tool.auto_define_config probe --context <probe-context.json> --output <facts.json>
python -B -m tool.auto_define_config preview --module iso/hardware/cpu --facts <facts.json>
python -B -m tool.auto_define_config rename define/old define/new --dry-run
python -B -m tool.auto_define_config gui
```

Global options: --root <project>, --inventory <manifest>, --cmake <executable>. Probe accepts --module and --options. Rename without --dry-run performs the explicitly reviewed migration. CLI exits 0 on success and 2 on a configuration/operation error.

Registered source/define/hardware/cpu corresponds to tool/auto_define_config/define/hardware/cpu/{probe.py,fields.json}. Grouping-only folders do not create probes. Sync creates only missing files; repeated sync preserves existing bytes. Check/configure never scaffold maintained files. Removed-module counterparts stay reported as inactive orphans. Explicit rename requires the old module to be unregistered, the new one registered, and a conflict-free destination; handwritten code is moved unchanged while only declaration identity is updated. Nested module migrations must be explicit rather than guessed.

## 6. Field and observation contracts

fields.json v1:

```json
{
  "schema_version": 1,
  "module": "define/platform",
  "fields": [
    {
      "id": "windows",
      "type": "boolean",
      "macro": "DESTINY_DEFINE_CMAKE_PLATFORM_WINDOWS",
      "alias": "DESTINY_DEFINE_PLATFORM_WINDOWS",
      "description": "Selected target is Windows"
    }
  ]
}
```

IDs are globally unique dotted identifiers. Supported types are boolean, signed 64-bit integer and string; booleans are not accepted as integers. unit is an optional nonempty string for integer fields only. Generated names begin DESTINY_DEFINE_CMAKE_; optional public aliases begin DESTINY_DEFINE_ but not DESTINY_DEFINE_CMAKE_. Each field additionally reserves the matching _AVAILABLE names. All IDs and exported macro names are collision-checked.

kind defaults to observation. kind=option requires a correctly typed default. Observations cannot declare user defaults. Unknown schema members/versions, duplicate JSON keys and non-finite JSON numbers fail.

probe.py for this one-field declaration:

```python
from tool.auto_define_config.providers.platform import platform_facts


def probe(context):
    return {"windows": platform_facts(context)["windows"]}
```

A probe exports probe(context) and returns exactly the declared observation IDs, not options. Observation.available(value, provider=...) represents known data. Observation.unavailable(reason, status=..., provider=...) has no value. Statuses: unavailable, denied, unsupported, unimplemented and timeout. Wrong fields/types, implementation exceptions or unexpected stdout are errors, not unavailable hardware. Imports must be side-effect-free. Probe source is trusted project code, not an untrusted-code sandbox.

ProbeContext carries project_root, module, fields and read-only target data. Current target context includes system, processor, compiler ID/version/path, pointer_bytes, compiler_flags and a build-local probe_cache. Do not infer output bitness from the Python interpreter.

Facts JSON v1 is grouped by module then field ID. Entries preserve type, unit, status, value, provider, reason, macro, alias and kind. Integer values cross the JSON boundary as canonical decimal strings under type=integer to prevent CMake JSON rounding above 2^53; that does not make them string fields.

Strict binary failure semantics are intentional: unavailable boolean -> false/0; NOT then -> true. Comparisons against unavailable data -> false; their negation -> true. Status remains diagnostic. Generated unavailable integers/strings use 0LL/empty string with _AVAILABLE=0. Available integers use LL literals, including a safe minimum-int64 expression. Macro generation and header preview share the same CMake implementation.

Local declared-option overrides live at cache/auto_define_config/options.json by default, or the CMake DESTINY_OPTIONS_FILE path. GUI edits only declared options; actual hardware remains read-only. Reload CMake after saving. Unknown override names/types fail; GUI simulations never replace production observations.

## 7. Reusable initial providers

Maintained module probes may import these functions without editing a central registry:

| Provider | Observations |
| --- | --- |
| providers.platform.platform_facts(context) | windows, linux, macos; x86/x64 from selected target pointer width |
| providers.cpu.cpu_facts(context) | cpuIntel, cpuAMD, avx2, avx512f, avx512bw |
| providers.memory.memory_facts() | memory.total_bytes, OS-visible memory in bytes |

The CPU provider compiles a small non-optimized CPUID helper in an isolated cache, checks OSXSAVE/XCR0 state before allowing AVX features, and intersects those capabilities with enabled compiler predefines. Hardware observations refresh each configure; cached helper binaries are keyed by compiler identity, architecture and source. Intrinsic or language feature checks beyond the initial capability set belong in additional providers, not ad hoc GUI logic.

Windows memory uses GlobalMemoryStatusEx, Linux reads MemTotal, and macOS uses sysctl hw.memsize. macOS paths have fixtures but no real-machine validation. WSL observations describe guest-visible resources. Cache size, memory transfer rates and GPU data are extension points, not claimed implemented fields.

## 8. source_rules.json v1

```json
{
  "schema_version": 1,
  "aliases": {
    "wide": {"all": [{"ref": "windows"}, {"ref": "avx512f"}]},
    "large": {"compare": {"field": "memory.total_bytes", "op": "ge", "value": "34359738368", "unit": "bytes"}}
  },
  "groups": [
    {
      "name": "backend",
      "candidates": [
        {"name": "wide", "when": {"ref": "wide"}, "sources": ["src/entry_while_wide.cpp", "src/helper.cpp"]},
        {"name": "scalar", "when": true, "sources": ["src/scalar.cpp"]}
      ]
    }
  ]
}
```

Expressions are a boolean literal or an object with one ref/all/any/not/compare member. all/any require nonempty child arrays. compare uses field/op/value and unit when the field declares one. Operators eq/ne apply to strings; eq/ne/lt/le/gt/ge apply to integers. Comparison values are strings; integer comparison uses validated canonical signed decimal text and exact ordering, not floating-point conversion.

Aliases are module-local, cannot shadow global fields, and cannot cycle. Both branches of a logical expression are validated even if one would decide its truth. Source suffix name_while_<condition>.cpp references one boolean field or local alias; no long filename expression grammar exists.

Groups are required, ordered first-match selectors. Each candidate must list existing canonical src-relative .cpp files. Candidate eligibility includes every member file's suffix condition. Files are selected together, cannot belong to multiple candidates, and cannot escape src through a symlink. A fallback is explicit true; no eligible candidate fails configure. Compile failure never triggers a different candidate.

Ungrouped ordinary sources always participate; ungrouped conditional sources follow their condition. Rules affect src only, not public-header availability or test/demo entrypoint suffixes.

## 9. Reports, previews and GUI workflow

Source selection reports print at configure completion and after a successful default full build. Text and JSON files are in reports/source-selection-<configuration>.*. destiny_source_report prints without compiling. Reports show selected/excluded sources, reasons, group winners, language requirements and absolute executable/working-directory paths. A single-target build need not run the global summary; selected does not mean recompiled.

The Source Rules GUI page edits aliases with a tree dialog, displays a read-only expression, associates multiple files with a candidate and reorders candidates. Preview invokes the actual CMake selector with the unsaved rule document in temporary storage and a selected facts file, explicitly labeled preview/simulation.

The Define / Probes page edits declarations, preserves handwritten probe code, runs one probe asynchronously, previews the CMake-generated header, and edits only declared user options. Refresh/check is read-only; Sync missing is explicit. Existing source edits are protected by content fingerprints. Before saving rules or field changes, the editor invokes the same CMake semantic validator using declaration-only facts: missing fields, type/unit mismatches, cycles and invalid file ownership fail without overwriting the file. In this validation-only mode an unmet hardware candidate group is allowed; a real build still requires a matching candidate. Empty invalid groups can exist while editing but cannot be saved.

Both GUIs keep long subprocess work off the Tk thread, bound subprocess duration/output, provide cancellation and route completion back to Tk. Closing requests cancellation. CLI imports do not depend on Tk; environments without Tk can still build and use all headless services.

## 10. Verification entrypoints

```text
python -B -m tests.build_system.verify --report build/regression.json
python -B -m tests.build_system.matrix --compiler-report build/compilers.json --report build/matrix.json
```

The matrix is a test harness, not a new user build launcher. On Linux it can validate gcc/g++ and clang/clang++ from PATH when --compiler-report is omitted. It builds an isolated representative module graph in Debug/Release, checks generated macros and intrinsic implementations, runs CTest/demos/benchmarks, verifies binary architecture and no-op incremental behavior, and cleans its fixtures. Optional --family, --arch and --config narrow a diagnostic run; narrowed results must not be reported as full-matrix acceptance.

Full regression native fixtures use DESTINY_TEST_CC/DESTINY_TEST_CXX or gcc/g++ on PATH and the test-driver Python interpreter. Evidence distinguishes real passes, skipped GUI tests, unsupported hosts and missing requirements. Formatting uses Black 25.1.0 only as a local development tool; delivered runtime dependencies remain standard-library-only.

## 11. Context and identity changes recorded on 2026-09-26

- The optional `compilation_contexts` diagnostic member is additive to facts schema 1. The `modules` field table and macro-generation/selection interpretation are unchanged.
- Compiler results now include `compiler_fingerprint`: a SHA-256 signature of both supplied driver paths and executable contents. Identity also includes family, version, target, architecture and flags. Validation checks for driver changes during the operation; preset publication rejects a stale signature. A replaced same-version driver produces new preset names/binary directories rather than reusing an incompatible cache.
- Old local compiler reports without a fingerprint must be regenerated with scan/validate before preset export. This is explicit rejection of disposable stale evidence, not a silent maintained-file migration. Existing unrelated presets and other-platform entries remain untouched. Driver signatures are not a checksum of an entire SDK or every system library; after changing those dependencies, revalidate and use a fresh build directory.
- `auto_define_config --cmake <executable> gui` propagates the selected CMake to inventory, semantic saves, source preview, probe subprocesses and header preview. CLI operations remain display-independent.
- Discovery cancellation is checked during directory enumeration. Completion-callback failures are delivered to the GUI error handler without stopping worker polling.

See EXTENDING.md for an end-to-end module/provider/rule recipe and ACCEPTANCE.md for requirement-to-evidence mapping.
