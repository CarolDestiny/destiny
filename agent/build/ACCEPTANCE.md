# Requirement-to-Evidence Audit

Updated: 2026-09-26
Status: V1 acceptance audit complete within the approved scope and recorded environment limits.

Read PLAN.md first. Test names below refer to tests/build_system. A passing report is usable only if its source_before/source_after fingerprint matches the current implementation/test tree. Generated reports remain local under build; VALIDATION.md records outcomes and reproduction commands. Source inspection complements tests but does not turn a simulated observation into a real hardware pass.

## Numbered acceptance checklist

| PLAN.md section 11 item | Implementation and inspected evidence | Audit state |
| --- | --- | --- |
| 1. Windows four slots, both configurations | matrix.py/prepare_scenario compiles, links, inspects PE architecture, runs CTest/demo/bench and checks no-op builds; matrix-windows-closure.json records each profile | Verified in closure reports; see EVIDENCE.json |
| 2. WSL equivalent matrix | Same harness, native Linux paths/toolchains and target widths; matrix-linux-closure.json; dependency installation history is in VALIDATION.md | Verified in closure reports; see EVIDENCE.json |
| 3. macOS adapters | HardwareTests macOS sysctl/platform fixtures; AcceptanceEdgeTests rejects x86 macOS before pretending to build | Fixture pass; real hardware explicitly deferred |
| 4. Discovery and presets | CompilerToolsTests, ToolContextTests, current compiler-scan-context-audit.json and actual local preset export. Aliases, failed candidates, architecture/runtime failures, manual entries, ownership and same-version replacement are covered. Unicode/space driver argument transport is a fixture, not a relocated live toolchain claim | Verified in closure reports; see EVIDENCE.json; evidence types distinguished |
| 5. Modules and regeneration | NativeBuildTests, InventorySyncTests, AcceptanceEdgeTests and clean-closure-windows.json and clean-closure-linux.json cover AUTO/STATIC/INTERFACE, graph errors, add/remove, visibility, collisions and empty source | Verified: the new content-edit regression executes changed consumers |
| 6. Mixed minimum standards | NativeBuildTests compile real 17/20/23 code and inspect flags; CompileContextTests separates dependency-raised contexts, cache keys and rejected modes; AcceptanceEdgeTests verifies GoogleTest raises only the test | Verified in closure reports; see EVIDENCE.json |
| 7. Synchronization | InventorySyncTests and EditorTests cover grouping, nested modules, partial counterparts, conflicts, byte preservation, orphan inactivity and explicit migration; configure read-only tests | Verified in closure reports; see EVIDENCE.json |
| 8. Probe outcomes | ContractTests, HardwareTests and ProbeTests cover real/absent observations, denied/unsupported/unimplemented, timeout-to-facts/header, malformed native JSON, wrong types/units and implementation defects; subprocess timeout is exercised separately | Verified in closure reports; see EVIDENCE.json |
| 9. Incremental define/field chain | NativeBuildTests generated facts/macros/selection; declaration-driven GUI and config.hpp.in; the complete EXTENDING.md recipe is executed on Windows and WSL | Verified by test_extension_recipe in all three regression environments |
| 10. Source conditions | SelectionTests and RuleStructureTests cover nested binary logic, all branches, alias cycles, exact signed-64/string comparisons, simultaneous/ordered groups, multi-file membership, duplicates, explicit fallback and missing platform; native rule changes change actual compile commands | Verified in closure reports; see EVIDENCE.json |
| 11. GUI/CLI ownership and preview | EditorTests/GuiSmokeTests/ToolContextTests plus GUI_VALIDATION.md actual operations; CMake is the sole selector/header generator; external edits, asynchronous snapshots, custom CMake routing and probe preservation | Current automated closure passed; interactive evidence has its own version boundary |
| 12. Build-only and switches | NativeBuildTests marker/discovery assertions, matrix startup records, AcceptanceEdgeTests independent test/bench/demo switches, ProgramTests custom main/multiple entry points | Verified in closure reports; see EVIDENCE.json |
| 13. Working directory | NativeBuildTests asserts actual cwd and CTest JSON property; matrix asserts root resources; EXTENDING.md runs cmake -E chdir from the binary directory; Windows CLion application/Google Test observations recorded separately | Windows IDE observed; WSL native runs tested; WSL IDE binding unverified as explicitly permitted by the plan |
| 14. Runtime DLLs | RuntimeTests PE imports/architecture/conflict/receipt coverage; ProgramTests clean-PATH real launch; every Windows matrix program runs with only System32 in PATH | Verified in closure reports; see EVIDENCE.json |
| 15. Truthful hierarchy/reports | DestinyReport.cmake and native tests prove four-space hierarchy, selected sources, group reasons, per-module contexts and absolute executable/cwd paths; ALL summary depends on every enabled target | Verified: the new compile-failure regression asserts no fallback and no summary |
| 16. Incremental stability and context isolation | Matrix object/header mtime assertions, facts/header stability tests, CompileContextTests standard/flags/configuration cache separation and compiler digests; different binary directories per verified preset | Verified in closure reports; see EVIDENCE.json |
| 17. Vendored/offline GoogleTest | AcceptanceEdgeTests verifies every recorded upstream file hash/license. Fresh fixtures copy all sources locally; active CMake path contains no download/package-manager invocation. Tests use vendored targets and PRE_TEST discovery | Verified in closure reports; see EVIDENCE.json; no claim of a system-wide network firewall test |
| 18. Cleanup and final inspection | Workspace owns/guards disposable fixtures under build/verification; source has no files; clean-closure-windows.json and clean-closure-linux.json checks real root configure/build/check. Historical destiny was not accessed | Both OS clean builds passed at the closure fingerprint; maintained source is empty |
| 19. AI handoff documents | PLAN/INTERFACES/PYTHON_MAINTENANCE/CLION/EXTENDING/GUI_VALIDATION/VALIDATION plus this map; root AGENTS.md points to them | Verified: contracts, executable recipe, current evidence and final handoff agree |

## Requirements outside the checklist wording

| Scope/contract | Evidence or ownership |
| --- | --- |
| Native CMake/Ninja, no custom build scheduler, no buffered compiler log rewriting | Root CMakeLists/Presets, DestinyTargets/Programs/Report; native commands in every integration fixture. Verification scripts are test harnesses only |
| Layer extension without parent module lists | DestinyLayers and Registry; test_layers_can_be_extended_in_one_place; grouping folders do not create targets/probes |
| Public headers remain platform-independent and physically short | DestinyHeaders forwards only each module's maintained include tree; target-scoped usage; source selection operates on src only; relative/special-character includes compile |
| Header-only/private standards and initialization order | Registry resolves the graph before CompileContext, Facts, Selection and target materialization; public/private tests inspect actual downstream flags |
| Hardware/target/compiler context separation | Providers use CMake pointer width rather than Python width; CPU CPUID plus OSXSAVE/XCR0 and compiler ISA predefines; per-module dialect metadata is separate from shared fields/macros |
| No hidden source writes or generated-output editing | Synchronizer check/apply separation, guarded storage, generated/config cleanup confined to the build tree; source ownership/hash tests |
| English product text; Chinese conversational summaries | Project-owned source/GUI/report/document text is English. Raw compiler diagnostics are not rewritten |
| No implicit installers, system upgrades or PATH edits | Delivered Python uses child-process environments only. Missing WSL multilib packages were installed only for authorized validation; tools never install them |
| GUI has exactly two independent tool entrypoints | find_compiler and auto_define_config; the latter owns Source Rules and Define / Probes tabs and reuses headless editing/preview contracts |
| Initial probe scope vs future data models | Platform, target width, CPU vendor/AVX2/AVX512F/BW and OS-visible memory are implemented. GPU/cache/rate inventories, external consumption and production modules remain explicitly excluded |
| Run policy does not move binaries or embed hidden chdir | CTest/CLion/terminal configure the launcher cwd; artifacts/DLLs remain in module/category binary directories. Direct arbitrary launches inherit their caller's cwd |
| Parallel test output isolation | GoogleTest XML path is module/stem scoped; discovery metadata is target scoped on newer CMake; scenario startup records use unique process records |
| Minimum supported versions | Separate real CMake 3.25.2/Python 3.10.11 regression. Tk is absent in that embedded interpreter; current Windows/WSLg Tk runs are separate evidence |

## Implementation phase gates

| Phase | Inspected gate evidence | Result |
| --- | --- | --- |
| 1. Contracts and fixtures | Contract/storage/rule error cases; clean Windows/WSL root configure; implemented CLI/schema reference | Passed |
| 2. Native module builds | Actual mixed-dialect translation units/compile commands, dependency errors, target visibility, vendored tests and output paths | Passed |
| 3. Probes and synchronization | Incremental/partial/orphan/rename cases, maintained-file hashes, numeric end-to-end documented recipe, generated header cleanup | Passed |
| 4. Conditional selection | Native selector shared by GUI/CLI, exact comparisons and strict unavailable negation, ordered multi-file candidates and real compile-command changes | Passed |
| 5. GUIs and native integration | Current Tk regressions and short actual UI check; earlier manual compiler/IDE runs; presets and clean-PATH DLL launches | Passed within the recorded IDE/environment limits |
| 6. Matrix, handoff and cleanup | Current 16-profile matrix, three regressions, runnable extension recipe, current report hashes and both cleaned-root builds | Passed |

## Final disposition

On 2026-09-26 the implementation/test/recipe fingerprint was recomputed and matched all current closure reports and the durable EVIDENCE.json summary. The two formerly missing native regressions now prove ordinary maintained-file content edits and failed-selected-implementation behavior. The current documentation recipe runs as a regression rather than as a separately copied example. The short actual GUI check passed and the tool window was closed.

The final pass changed maintenance documentation only: the plan/checklist, reference index, handoff, and CLion debugger/WSL instructions. It did not change tested build behavior, reopen the GUI or rerun unchanged matrices. PLAN.md section 11 is checked against the rows above, not against the existence of binaries or intended behavior.

Acceptance does not erase the agreed limitations: macOS is fixture-only; CLion WSL run/debug binding is unobserved; the embedded minimum Python lacks Tk. Windows IDE run evidence, native WSL runs, both current Tk environments and the minimum headless/build path are separate evidence. No debugger breakpoint session or universal file-manager cwd is claimed. The plan explicitly permits recording unavailable IDE launch checks instead of inferring them from CTest.

All required v1 artifacts and phase gates are accounted for. Installation/export/external consumers, production modules, full GPU/cache/rate inventory and real macOS runs remain original exclusions, not deferred unfinished implementation. HANDOFF.md lists the delivered entrypoints and maintenance procedure for future changes.
