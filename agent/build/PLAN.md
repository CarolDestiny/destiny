# destiny-compat Build System Plan

Status: V1 implementation and acceptance complete within the agreed scope; environment limits are recorded.
Updated: 2026-09-26
Workspace: `D:\project\destiny-compat`
Configuration tool name: `auto_define_config`

This is the consolidated implementation plan, including per-module C++ standards and synchronized define-module Python probes. It replaces earlier conversational drafts. The user authorized staged execution through the active implementation goal on 2026-09-25. See ACCEPTANCE.md for the completed audit and VALIDATION.md/EVIDENCE.json for evidence and limitations. The implementation covers native CMake, probes, selection, compiler tools, GUIs, runtime staging and the Windows/WSL matrix. The final audit confirmed that closure evidence matches the current implementation/test/recipe fingerprint. Section 1 exclusions are not unfinished v1 requirements.

Paths below are repository-relative unless absolute. Read `README.md` for navigation. Before implementing or extending Python probes, synchronization, declarations, or the GUI, read `PYTHON_MAINTENANCE.md`. These files are planning documents, not evidence of implemented functionality.

## 1. Scope and defaults

- Build from the empty destiny-compat skeleton. Do not inspect, modify, or migrate `D:\project\destiny`.
- Primary workflow: CLion and native CMake. This version has no independent build launcher, whole-build log buffering, or replacement build scheduler.
- Baseline: CMake 3.25+, Ninja, Python 3.10+, and C++20 as the overridable module default. Use Python's standard library and Tkinter; CLI operations must not require a display or initialize Tkinter.
- Windows: MinGW GCC and LLVM-MinGW Clang, each producing x86/x64 executables. Exclude MSVC and clang-cl. Linux: GCC/Clang x86/x64, verified through WSL Ubuntu.
- Keep macOS platform/discovery adapters and fixture coverage, but defer real-machine acceptance. Report unsupported targets honestly; do not promise four runnable macOS combinations or silently substitute ARM for x86. Apple Silicon build targets are not a v1 acceptance requirement.
- Optimize project-owned code for the actual build machine, preserving Debug/Release behavior. No runtime implementation dispatch, aggressive floating-point defaults, or global project-only flags imposed on third-party targets. Binaries are not promised portable to other CPUs.
- Project-internal use only: no installation/export, find_package, external add_subdirectory support, packaging, complete GPU inventory, GPU kernels, or production business modules in v1.
- Project-authored GUI text, diagnostics, reports, generated content, and documentation use English. Preserve raw compiler diagnostics rather than rewriting them.
- Implementation may create temporary validation modules under source and install only missing WSL x86 development dependencies. Remove the temporary validation modules at completion. No system upgrade, system PATH changes, or automatic installers in the delivered tools.

## 2. Deliverables and naming

| Location | Responsibility |
| --- | --- |
| Root CMake files and `cmake/` | Native targets, module discovery, layers, standards, selection, generated headers, outputs, reports |
| `tool/find_compiler/` | Independent compiler discovery GUI and CLI; machine-local presets |
| `tool/auto_define_config/` | Unified project configuration tool: probes, synchronization, declarations, rule editing, GUI and CLI |
| `tool/auto_define_config/define/<module-relative-path>/` | A maintained probe.py and fields.json for each registered define module |
| `thirdLib/googletest/` | Vendored GoogleTest source, license and pinned provenance |
| Build directories | Facts JSON, generated headers, selection reports, intermediates and binaries |
| `agent/build/` | Plan, AI maintenance instructions, implementation references and validation evidence |

There are two GUI entrypoints: find_compiler and auto_define_config. The latter contains both Source Rules and Define / Probes pages; do not introduce a third standalone probe or rule-editor application. Earlier tentative tool directory names are superseded.

Commit maintained source, declarations, module rules, shared presets, vendored dependencies and documentation. Ignore local compiler presets, facts, caches, GUI preferences and build output. Ignore rules must retain agent/build documentation. Favor small public interfaces and cohesive shared services over monolithic scripts or duplicated frameworks; comments explain constraints, not obscure code structure.

## 3. Modules, dependencies and public headers

Module-facing usage:

```cmake
# Lowest to highest:
destiny_register_layers(define iso core)

# In a module:
destiny_add_module()
destiny_depends(PUBLIC define/platform)

# Optional language requirements:
destiny_add_module(CXX_STANDARD 23 PUBLIC_CXX_STANDARD 20)
```

- Modules are explicitly registered through a minimal local CMake file. Discover entries automatically without maintaining parent-directory lists. Directory grouping alone does not create a library.
- Discover ordinary headers and implementation files automatically; source/header additions and removals trigger regeneration under the supported Ninja workflow.
- AUTO selects a static library when implementation sources remain after selection, otherwise an interface library. Also accept explicit STATIC and INTERFACE modes. STATIC without selected implementation sources is an error. An unsatisfied required implementation group never silently becomes an interface library.
- Support include, src, test, bench, demo and docs. No documentation generator is introduced by default.
- Dependencies identify module paths and preserve PUBLIC/PRIVATE/INTERFACE semantics. Collect registrations before resolving edges so correctness is independent of discovery order.
- Only strictly lower layers may be dependencies: core can directly depend on define; same-layer, upward, self and nonexistent dependencies fail. Layer order is centrally extensible; remove basicType and moreType from the default model.
- Keep physical headers short: source/iso/hardware/cpu/include/cpu.hpp is consumed as <destiny/iso/hardware/cpu/cpu.hpp>.
- Generate forwarding headers in per-module build include roots. Do not require symlink privileges or maintain copied header bodies. Preserve nested paths, detect collisions, and propagate include roots only through declared targets; no global include root that bypasses dependency policy.
- Public headers are platform-independent. Conditional selection applies to src, not public header availability. Validate header edits/additions/deletions, relative sibling includes, special-character paths and practical IDE navigation.

## 4. Per-module minimum C++ standards

- CXX_STANDARD defaults to 20 only when omitted. PUBLIC_CXX_STANDARD defaults to the implementation minimum. The former governs implementation; the latter governs the public headers' consumer requirements.
- Treat both as minimum requirements. Higher dependency requirements raise the consumer; unsupported requirements fail rather than falling back to older modes.
- Use target_compile_features and target-level PRIVATE/PUBLIC/INTERFACE usage requirements, with required standards and language extensions disabled for compiled project targets. Do not inject global -std flags or impose an unconditional C++20 infrastructure target.
- Header-only modules have a public requirement only; CXX_STANDARD is shorthand. Two explicitly inconsistent values on such a module fail configuration.
- A private dependency can raise the current implementation requirement without leaking it to unrelated consumers. Publicly exposed requirements propagate. A C++23 implementation may expose C++20 headers without requiring C++23 of its consumers.
- test/bench/demo default to their module implementation minimum and satisfy their own dependencies. A test framework may raise the test executable's requirement without raising the library's public requirement.
- Resolve declarations, dependencies and minimum-standard contexts before condition evaluation. Conditions do not mutate standards, module kind or dependencies.
- Cache compilation capability checks by compiler, target architecture, standard context and relevant options. A global current-C++-standard macro cannot describe all independently configured modules.
- Reports distinguish declared and dependency-raised minima from an exact actual dialect. Verify real compile commands and representative source features; accepting a standard mode does not prove full language/library support.

## 5. Compiler discovery and local presets

- GUI and CLI share discovery, validation and storage services. Search PATH, common roots and user-specified directories, not every disk. Allow manual C/C++ executable paths and candidate selection.
- Detect compiler identity rather than trusting executable names. Four slots mean GCC/Clang times output x86/x64, not four required installations. Recognize Clang drivers named gcc.
- Validate startup, compatible C/C++ drivers, default C++20 compilation, linking, output architecture and execution. Module-specific standard requirements receive separate CMake checks.
- Set only subprocess environments; isolate toolchain runtime paths and avoid GCC/Clang or x86/x64 DLL contamination. Explain startup, compilation, linkage, architecture and execution failures separately.
- Display all four slots. Generate Debug/Release configure/build/test presets only for verified combinations; missing combinations stay visible with reasons and manual correction controls.
- Keep shared CMakePresets.json separate from local CMakeUserPresets.json and local companions. Preserve unmanaged entries and other platforms' entries, detect naming/external-edit conflicts, and never overwrite blindly.
- Preset identities distinguish compiler installations and output architectures. An incompatible existing cache needs a fresh build directory, not an unsafe compiler switch.
- Use the Python and subprocess environment for the active OS. Windows paths must not be reused as WSL tool paths. Document CLion debugger and WSL binding steps instead of claiming presets fully configure the IDE.
- Delivered tools never install missing dependencies or modify the system PATH.

## 6. auto_define_config: module probes and synchronization

### 6.1 One-to-one correspondence

The registered define module set is authoritative. Preserve its path hierarchy:

```text
source/define/platform/
    <-> tool/auto_define_config/define/platform/probe.py
    <-> tool/auto_define_config/define/platform/fields.json

source/define/hardware/cpu/
    <-> tool/auto_define_config/define/hardware/cpu/probe.py
    <-> tool/auto_define_config/define/hardware/cpu/fields.json
```

- A grouping directory does not receive a probe unless registered as a module. Use the same module inventory as the build, not a separately maintained import list or GUI module registry.
- Each probe handles its module's fields. Shared helpers provide platform queries, normalization, subprocess handling and diagnostics. Importing a probe must not execute detection, edit files or initialize a GUI.
- Automatic scaffolding creates a callable skeleton and field-declaration structure. It does not guess hardware behavior. Distinguish an intentionally empty field set from declared but unimplemented probes.
- Future probe logic and declarations are expected to be maintained by AI. Their interface and extension recipes are required deliverables, not optional explanatory comments.

### 6.2 Synchronization and source ownership

| Change | Required behavior |
| --- | --- |
| New registered define module | GUI refresh/sync or explicit CLI sync creates missing probe.py and fields.json skeletons |
| Existing counterpart | Preserve handwritten code and declaration contents exactly |
| Partially missing counterpart | Create only the missing file, retaining the existing file |
| Removed module | Report its counterpart as orphaned; exclude it from active detection without deleting it |
| Renamed/moved module | Require an explicit old-to-new mapping and conflict review; do not infer renames |
| Changed field declaration | Validate probe output, macro names/types and rule references against it |
| CMake configure | Check synchronization; do not create or rewrite tracked source files |

- Provide a read-only check/dry-run command. Missing counterparts during configuration report the required sync action and fail clearly rather than producing silent partial configuration.
- Synchronization is idempotent and reports created, unchanged, missing, orphaned and conflicting items. Failed writes must not truncate valid source.
- Retain orphaned maintained files until explicit cleanup. Remove obsolete generated facts/headers only within the tool-owned build generation area so inactive macros do not remain live.
- Fields and rules are hand-editable, GUI-editable declarations; probe.py is maintained source; JSON observations and generated headers are disposable output. Each has a different write policy.

### 6.3 Facts and macro generation

```text
Registered define modules
    -> synchronization validation
    -> fields.json declarations + Python probe implementations
    -> per-build typed facts JSON, grouped by module
    -> CMake conditions and source selection
    -> per-module configuration headers + selection reports
```

- fields.json owns names, types, units, descriptions, exported macro names and declared configurable defaults. Python, CMake and the GUI consume this source instead of duplicating field tables.
- Python obtains observations; CMake decides sources, sets build behavior and expands hpp.in. Do not reverse-parse arbitrary business header macros.
- A single runner may load all module probes; avoid launching Python separately for every field. Refresh on every CMake configuration/reload, not on ordinary incremental builds unless they legitimately reconfigure.
- Save facts per build directory. Separate host hardware, selected compiler, output architecture and per-module compilation capabilities. Python interpreter bitness does not determine target bitness.
- A fact preserves its value, status, provider/source and reason. Distinguish known absence, permission denial, unsupported queries and unimplemented observations from malformed output and programming defects.
- Initial probes cover platform, x86/x64 target architecture, CPU vendor, AVX2, AVX512F/BW and OS-visible memory capacity. Instruction availability incorporates CPU support, OS-enabled state, and selected compiler/flags.
- Support booleans, integers and strings with explicit units. Preserve extensibility for cache, memory-rate and per-device GPU data, but do not implement a complete inventory in v1. Keep installed versus guest-visible memory and clock versus transfer rate distinct.
- STRICT TWO-VALUED POLICY: unavailable boolean capability becomes false/0; NOT then becomes true. Comparing unavailable numeric/string data returns false; negating that result follows normal binary logic. Status explains the result but does not introduce a third logical value. Export availability alongside unavailable numeric macro values so a sentinel is not mistaken for an actual measurement.
- Expected unavailability follows the above policy. Invalid schemas, duplicate macros, wrong result types and unexpected implementation exceptions fail with diagnostic context rather than masquerading as unsupported hardware.
- Generate configuration headers per define module from one template mechanism driven by declarations; adding a field requires no new entry in a central macro template. Support declared public DESTINY_DEFINE_* aliases of generated DESTINY_DEFINE_CMAKE_* macros.
- Compile-context-dependent facts cannot be represented by a misleading global standard macro. Keep that context isolated from shared hardware facts and visible in selection reports.
- Rewrite headers and semantic reports only when effective contents change. Exclude timestamps and volatile probe metadata from semantic build inputs.
- Probes run unprivileged, with bounded operations and the active platform environment. WSL describes the guest unless a future separately named host provider is added; do not elevate privileges to obtain optional facts.

## 7. auto_define_config: source rules and GUI

### 7.1 Local conditions and implementation groups

- Conditional filenames apply only to src: name_while_<condition>.cpp. A suffix names one registered boolean condition or module-local alias, not a second long expression grammar.
- A versioned module-owned source_rules.json contains aliases, expression trees, implementation groups and ordered candidates. CMake reads it directly; there is no second generated CMake rules file to maintain.
- V1 expressions support boolean literals/references, AND/OR/NOT, integer comparisons and string equality/inequality. Validate types and declared units. Arbitrary executable expressions and generic version-expression parsing are out of scope.
- Aliases compose registered data and local aliases. Reject unknown fields, reserved-name shadowing, alias cycles and malformed/type-invalid expressions.
- Ungrouped ordinary sources are included. Ungrouped conditional sources are included only when their condition is true.
- A group selects the first matching candidate in its ordered list. Each candidate can own multiple files; selection is all-or-nothing. Include declared conditions of member files in candidate eligibility so a group cannot force an incompatible file into the build.
- Each source belongs to at most one candidate. Reject nonexistent files, duplicate ownership and ambiguous declarations.
- Priority is local to the implementation group, not a universal ranking of CPU capabilities. Selecting AVX512 does not make the AVX2 capability false or exclude independent AVX2 code.
- Required groups with no eligible candidate fail configuration. A portable implementation is an explicit TRUE fallback; no automatic fallback is invented. A process abstraction can therefore require one supported platform with no generic implementation.
- After selection, a compilation error is a build failure. Do not mask it by trying a lower-preference implementation.

### 7.2 Unified project GUI

Provide two pages within auto_define_config, sharing headless services with its CLI. Keep the separate find_compiler entrypoint unchanged.

**Source Rules**

- Browse registered modules and sources; edit alias condition trees, candidate file membership and group order.
- Display read-only expression previews. Generate field controls from declarations rather than hardcoding hardware names.
- Read/save the same rules file that can be edited by hand. Detect external modifications and unsupported schema versions; invalid edits preserve the last valid file.
- Preview by invoking the same CMake evaluation engine with a selected build context or clearly labeled simulation. Do not create a second Python interpretation of source-selection semantics.

**Define / Probes**

- Browse the define tree and counterpart sync states. Refresh/sync can scaffold missing files; check-only operation stays non-mutating.
- Edit declared fields, units, types, macro names and configurable parameters. Open the corresponding probe.py for editing; the GUI need not become a general Python IDE or synthesize real hardware logic.
- Run one module probe, inspect values/status/reasons, and preview JSON plus CMake-generated macros in an isolated preview directory.
- Actual hardware observations are read-only. Editable actual settings must be declared user options. Simulated observations remain visibly labeled and separate from production build facts.
- Save persistent declarations/options, not generated macro output. Explain that CMake must be reloaded to apply changes; do not silently build the project.

Neither page creates business modules/C++ code or silently renames, moves, deletes or overwrites existing handwritten source. Share safe file updates and external-modification checks between GUI and CLI.

## 8. Programs, outputs and reporting

### 8.1 Tests, benchmarks and demos

All three independent switches default to ON:

```cmake
DESTINY_BUILD_TESTS
DESTINY_BUILD_BENCHMARKS
DESTINY_BUILD_DEMOS
```

- A direct .cpp in each category normally creates one same-stem executable. Preserve module/category namespacing to prevent target and output collisions.
- Provide a concise explicit executable declaration for multi-file programs, supporting files, additional dependencies and a custom test main. Explicitly assigned sources are excluded from automatic standalone entry detection.
- Vendor GoogleTest v1.18.0 source under thirdLib/googletest; verify and record the upstream commit/content hash and retain its license when acquiring it. No vcpkg, submodule or configure-time automatic download.
- Add GoogleTest only when enabled tests need it. Disable its own tests, samples, installation and GoogleMock by default. Each compiler/architecture/configuration builds compatible binaries from the sources.
- Tests normally link the supplied GoogleTest main and register with CTest. Use PRE_TEST discovery: ordinary Build must not start a test executable even just to enumerate test cases.
- Build only compiles test/bench/demo; explicit test or validation actions may run them. Small compiler/environment probe executables are separately labeled and are not project tests, demos or benchmarks.
- No benchmark framework is automatically imposed. Different module language standards still use the same compatible compiler/standard-library/runtime family in one build configuration.

### 8.2 Output paths and Windows runtime dependencies

Default output organization:

```text
build/<os>-<arch>-<compiler-id>/<configuration>/
    <module-path>/test/<stem>[.exe]
    <module-path>/bench/<stem>[.exe]
    <module-path>/demo/<stem>[.exe]
    lib/<module-path>/
    .obj/
    generated/
    reports/
```

Respect a custom CMake binary directory from CLion as the output root while preserving module/category grouping. Reports print absolute artifact paths.

After linking on Windows, inspect executable dependencies, including transitive dependencies, and copy only required non-system runtime DLLs from selected toolchain/known runtime roots. Verify architecture and report unresolved or conflicting dependencies. Do not copy the entire toolchain bin directory or alter global PATH. Validate launch with compiler paths removed from the environment. This is local runtime staging, not a promise of portable redistributable packaging.

### 8.3 Runtime working directory

The requested execution directory means the process working directory, not the executable output directory. All project test/bench/demo executables launched through the supported project run/test configurations start in the destiny-compat project source root. Their binary and DLL locations remain as specified in section 8.2.

- Capture the destiny-compat root once in the root CMake configuration, for example as DESTINY_PROJECT_ROOT. Use the active environment's absolute source path, not a hardcoded Windows path, a module's current source directory, or its binary directory.
- Explicitly set CTest WORKING_DIRECTORY to that root for every registered project test and retain DISCOVERY_MODE PRE_TEST. Both deferred discovery and test execution must run the executable at the root, without starting project programs during ordinary Build. CMake may keep discovery metadata in a separate build-tree directory, using its native test launcher to preserve the executable cwd.
- In CLion, set Working directory for CMake Application and Google Test run/debug configurations to the project root. Use $PROJECT_DIR$ when destiny-compat is the opened IDE project. Include template setup for new configurations and a check of existing configurations; preserve unrelated IDE settings.
- CMake test properties are not a universal setting for CLion's independent application/Google Test launchers. Document and verify those launch routes separately instead of relying on debugger properties that may be generator-, version-, or IDE-specific. Keep the CMake 3.25 baseline.
- For explicit terminal execution, document either changing to the project root before invoking the binary or using cmake -E chdir with the root and absolute executable path. This needs no new Python launcher and does not add execution to Build.
- Direct execution from another terminal or a file manager is controlled by that launcher. Do not claim that a compiled binary carries a universal forced working directory. Do not inject hidden startup chdir calls, hardcode the developer checkout into program behavior, or relocate binaries to simulate this requirement.
- Validate the active root mapping for Windows and WSL. Compiler and hardware probe subprocesses retain their isolated scratch directories; the project-program runtime policy does not move probe output into the source root.
- Relative resource paths are resolved from the root during supported execution. Framework-generated XML, logs and mutable test fixtures use explicit per-target/per-test paths under the build tree so parallel tests do not overwrite shared root files.
- Reports distinguish Executable path from Working directory. Both values are absolute and describe different properties.

### 8.4 Truthful hierarchical reports

- At configure completion, print and save Source selection report in text and machine-readable form.
- Root the tree at destiny and indent four spaces per deeper module-path level. Include selected ordinary/conditional .cpp files, group winners, exclusion reasons, effective probe failures, language minimums, executable paths and runtime working directories.
- Provide a native destiny_source_report target. An ALL summary target depends on enabled project targets and prints after a successful full build, without serializing compilation.
- Individual target builds need not trigger the global report. Build failure must not print a misleading success summary; preserve native diagnostics.
- Selected means included in the current configuration, not recompiled in the latest incremental build. An existing artifact alone is not proof of success.
- Do not implement buffered/reordered compiler logs or change native parallel scheduling to obtain pretty output.

## 9. AI maintenance deliverables

AI will maintain future Python implementations, fields, synchronization and GUIs. Deliver operational instructions and verifiable examples, not only architectural prose.

- README.md is the navigation entrypoint. PYTHON_MAINTENANCE.md owns extension and change procedures; update it with verified real commands as implementation lands.
- During implementation create INTERFACES.md documenting CMake interfaces, probe context/results, field/facts/rule schema versions, units, macro exports, CLI operations/exit codes and GUI file ownership. Include one complete minimal define-module example and one numeric-field condition example.
- Create VALIDATION.md recording commands, versions, platform/compiler/architecture/configuration outcomes, GUI checks, runtime working-directory checks and known limitations. Include CLion application/Google Test template setup and terminal launch examples in the interface documentation. Use passed, failed, blocked, fixture-only and unverified accurately; no intended behavior counts as evidence.
- Document how to add a define module, add a field/provider, change a macro/schema, resolve synchronization drift and validate the JSON -> CMake -> header -> source-selection chain.
- New behavior updates its tests, reference examples and relevant documentation in the same phase. A probe function without fixtures and integration checks is not a completed feature.
- During implementation provide a short repository-guidance pointer so later AI tasks discover these documents; keep full references out of always-loaded guidance.
- Keep product decisions in this plan and operational contracts in their dedicated references. State interface/schema changes explicitly; do not silently reinterpret existing files or add duplicated sources of truth.

## 10. Implementation sequence and phase gates

The user has authorized the implementation goal. Advance each phase using its gate; do not treat an early increment as completion of the full plan.

1. **Contracts and fixtures:** establish discovery, schemas, probe interfaces, CLI shape, ownership and deterministic fixtures. Document v1 contracts before independent GUI/CMake consumers rely on them. Gate: malformed inputs fail in focused tests and an empty business tree configures.
2. **Native module builds:** implement layers, targets, header forwarding, mixed standards, vendored tests and output layout. Gate: temporary modules compile and invalid dependency/standard requirements fail as specified.
3. **auto_define_config probes and synchronization:** implement idempotent scaffolding, read-only configure checks, initial observations, effective-value mapping and generated headers. Gate: adding a define module requires no central import-list edit; repeat sync preserves source bytes and configure does not mutate maintained files.
4. **Conditional selection:** implement typed expressions, aliases, ordered multi-file groups, consistent macros and reports. Gate: fixture outcomes agree with selected translation units, including strict binary NOT and mandatory-group failures.
5. **GUIs and native integration:** complete find_compiler and auto_define_config GUI/CLI surfaces, previews, safe presets, DLL staging and final reports. Gate: GUI/CLI round-trips agree, headless commands work, and CLion/native builds need no custom launcher.
6. **Matrix verification and cleanup:** run Windows/WSL validation, document evidence and extension recipes, then remove temporary source modules. Gate: all requirements are evidenced or explicitly reported as blocked/deferred; cleaned source state still configures and builds.

## 11. Acceptance checklist

All items below were checked on 2026-09-26 against ACCEPTANCE.md and EVIDENCE.json. Checked means accepted within the stated scope, not that skipped, fixture-only or unavailable real-machine checks became passes. A version printout, simulated observation, existing binary or written plan alone is not acceptance evidence.

- [x] Windows GCC and LLVM-MinGW Clang, x86/x64, configure/build/explicitly run representative programs in Debug and Release. Record each combination separately.
- [x] WSL GCC/Clang x86/x64 complete equivalent checks. Install only missing required x86 development packages when needed; record remaining environment limitations honestly.
- [x] macOS adapters and unsupported-target behavior have fixture coverage; real macOS validation remains explicitly unverified.
- [x] Compiler discovery covers aliases, multiple installations, manual paths, unavailable candidates, missing DLLs, incorrect architecture, spaces/non-ASCII paths and preservation of unrelated presets.
- [x] Module tests cover AUTO/STATIC/INTERFACE, invalid layer edges, source/header add/remove/edit regeneration, target-local include visibility, collisions and an empty business-source tree.
- [x] Mixed C++17/20/23 tests verify actual compile commands and representative source features: public raising, private non-leakage, header-only requirements, unsupported requests and test-framework-only raising. Minimal C++17 coverage excludes any higher-requirement test framework.
- [x] Synchronization covers nested modules, grouping-only folders, repeated operations, partial counterparts, exact preservation of maintained files, orphans, explicit renames/conflicts and no source writes during configure.
- [x] Probe tests cover success, confirmed absence, permission denial, unsupported/unimplemented observations, timeout, malformed output, wrong types/units and implementation exceptions. Host/Python bitness must not determine target bitness.
- [x] Adding a define module and a numeric field requires no centralized import-list edit, hardcoded GUI field, or manual central macro-template entry. Verify the complete JSON -> CMake -> header -> source-selection chain.
- [x] Selection tests cover nested logic, alias cycles, integer/string comparisons, strict NOT false == true after unavailable observations, simultaneous candidates, ordering changes, multi-file groups, duplicate membership, standard fallback and missing platform implementations.
- [x] GUI/CLI round-trip declarations/rules, detect outside edits, preserve handwritten probes and isolate simulations. Preview agrees with CMake selection. CLI works without GUI/display initialization.
- [x] Build never starts project test/bench/demo, including test discovery. Explicit CTest actions discover and execute GoogleTest. All three switches independently create or remove the corresponding targets.
- [x] CTest, CLion CMake Application, CLion Google Test and the documented terminal command start project programs in the project source root on Windows/WSL. Assert the actual current directory and root-relative resource access; preserve output locations and build-only behavior, and keep parallel test output isolated. Record unavailable IDE launch checks as unverified rather than inferring them from CTest.
- [x] Windows executables start without compiler bin directories in PATH after correct non-system DLL staging. Wrong-architecture runtime contamination is diagnosed.
- [x] Four-space reports list selected .cpp files and absolute artifacts, explain standard requirements, distinguish selection from recompilation and appear after successful full builds.
- [x] Unchanged semantic facts/rules do not rewrite headers or cause unnecessary recompilation. Different configurations do not share incompatible facts or compiler-probe caches.
- [x] GoogleTest provenance/license and offline configuration/build are verified; no configure-time download or package manager is required.
- [x] Keep reproducible validation fixtures outside source; remove all temporary validation modules from source without touching unrelated user files. Inspect final changes and configure/build the cleaned project.
- [x] Complete AI extension instructions, contract examples and validation evidence. Separate real passes, fixture-only coverage, failures, environment blocks and deferred features.

## 12. Review control

This plan is the scope for user review. Internal implementation organization may evolve while preserving its requirements. Changes to failure policy, ownership, public module behavior, side effects or supported scope require an explicit plan amendment.

Implementation was authorized by the user and the v1 acceptance checklist is now complete. Future changes must retain the full scope and update the affected evidence. Preserve the dependency-installation and source-cleanup boundaries in section 1.

### Implementation-detail reconciliation (2026-09-26)

The discovery requirement in section 8.3 is phrased in terms of the executable's actual working directory. Newer CMake can write GoogleTest discovery metadata in its discovery working directory; keeping that metadata out of maintained source requires a build-tree discovery directory plus native `TEST_LAUNCHER` (CMake 3.29+). The final per-test WORKING_DIRECTORY remains the project root. The CMake 3.25 path is retained. This corrects the earlier instruction to pass the root directly in every version without changing the user's runtime policy, minimum version, build-only behavior or filesystem ownership.
