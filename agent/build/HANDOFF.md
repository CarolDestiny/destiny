# V1 Build-System Handoff

Completed: 2026-09-26
Scope: The approved PLAN.md, including its original exclusions and explicit environment-verification limits.

## Delivered

- Native CMake/Ninja module discovery, extensible strict layer graph, per-module public/implementation C++ minima, short maintained include trees and target-local forwarding.
- Typed define-module probes, safe incremental counterparts, declaration-driven configuration headers, source conditions and ordered multi-file implementation groups.
- Independent find_compiler and auto_define_config CLI/Tk GUIs; manual compiler paths, validated local presets, safe edits, shared CMake previews and cancellation.
- Vendored GoogleTest, independent test/bench/demo switches, native PRE_TEST discovery, module/category output directories, Windows DLL staging and truthful hierarchical reports.
- Project-root execution through native CTest, documented terminal commands and separately configured IDE launchers; no hidden chdir in project executables.
- AI maintenance contracts, exact runnable extension recipe, evidence summary and requirement/phase-gate audit under agent/build.

## Acceptance snapshot

Implementation/test/recipe fingerprint: `06e94a96b816a91b9820432b505f8ac72a89f1e13a7fa342d9d5bce96c6a1582` (339 files).

| Check | Outcome |
| --- | --- |
| Windows regression | 129 passed; no failures/errors/skips |
| WSL regression | 127 passed; two Windows-only skips; no failures/errors |
| CMake 3.25.2/Python 3.10.11 | 119 passed; ten missing-Tk skips; no failures/errors |
| Native compiler matrix | All 16 GCC/Clang x86/x64 Debug/Release profiles passed across Windows/WSL |
| Clean business-source tree | Windows/WSL configure/build/check passed; no maintained validation modules remain |
| Final short actual GUI check | Rule save, real memory observation and matching CMake header preview passed; window closed |

EVIDENCE.json records report hashes and exact skip reasons. VALIDATION.md retains reproduction commands, repair history and the boundary between current automated, earlier interactive and fixture-only results. ACCEPTANCE.md maps all 19 checklist items and six phase gates. The final pass verified those files and changed documentation only; no unchanged GUI or matrix rerun was needed.

## Start using the project

Run from the repository root with Python 3.10+ (Tk is needed only for GUIs):

```text
python -B -m tool.find_compiler gui
python -B -m tool.auto_define_config gui
python -B -m tool.auto_define_config inventory
python -B -m tool.auto_define_config sync --dry-run
python -B -m tool.auto_define_config check
```

Use a verified local configure/build preset with native CMake, or import it into CLion. CLION.md covers explicit IDE toolchain/debugger binding, read-only imported profiles, new run-configuration templates and `$PROJECT_DIR$`. Follow EXTENDING.md to add actual modules; it requires no central Python import list or macro-template edits.

The source tree intentionally contains no business modules. Configuring/building it therefore proves infrastructure readiness, not the existence of an application binary. Adding registered modules/programs creates the corresponding targets and paths.

## Limitations, not hidden passes

- Real macOS validation is deferred; platform/discovery/unsupported-target adapters have fixture coverage.
- Windows CLion application/Google Test launches were observed. WSL native launches passed, but WSL IDE binding and debugger breakpoint sessions were not observed. Setup instructions are not runtime evidence.
- Embedded Python 3.10.11 provides no Tk. GUI cases were exercised separately on current Windows Python and WSLg.
- Native optimization targets the build machine; no portable CPU distribution or runtime dispatch is promised.
- Installation/export/find_package, external consumers, production business modules, complete GPU/cache/rate inventories remain original exclusions.

## Workspace and future maintenance

After the build-system handoff, the user requested Git publication to CarolDestiny/destiny, branch compat, and explicitly approved replacing its failed legacy file tree. GIT.md records the maintained-file policy, byte preservation and normal-history publication workflow. Keep the maintained CMake/Python/tests/vendor/docs files. Local presets, build output and verification caches are ignored. The old isolated IDE fixture remains under ignored build/clion-validation as evidence, not production source. No GUI/validation worker was left running.

For future work, read AGENTS.md, PLAN.md, PYTHON_MAINTENANCE.md and INTERFACES.md. Recompute the fingerprint before reusing this evidence. Run affected tests for actual changes, update the acceptance record, and avoid broad repeated manual GUI validation unless a concrete defect warrants it. Preserve handwritten probes and unrelated user files. Never inspect or modify D:/project/destiny.

Conversational reports use Chinese. Code, product UI/output and maintenance documents use English.
