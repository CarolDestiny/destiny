# Build Implementation and Maintenance

Status: V1 build infrastructure delivered; acceptance complete with documented environment limits.
Updated: 2026-09-26

## Read in this order

1. [PLAN.md](PLAN.md): full scope, phase gates and acceptance checklist.
2. [INTERFACES.md](INTERFACES.md): implemented CMake/Python/JSON/GUI contracts.
3. [PYTHON_MAINTENANCE.md](PYTHON_MAINTENANCE.md): AI maintenance and safe-edit workflow.
4. [CLION.md](CLION.md): validated IDE import and project-root working-directory setup.
5. [VALIDATION.md](VALIDATION.md): current evidence, reproduction and environment limits.
6. [EXTENDING.md](EXTENDING.md): complete module/provider/source-rule extension recipe.
7. [ACCEPTANCE.md](ACCEPTANCE.md): completed requirement-level audit and limits.
8. [GUI_VALIDATION.md](GUI_VALIDATION.md): observed computer-use workflows, UI fixes and GUI regressions.
9. [EVIDENCE.json](EVIDENCE.json): source fingerprint and exact report identities.
10. [HANDOFF.md](HANDOFF.md): delivered status and future-change workflow.
11. [GIT.md](GIT.md): maintained-file ownership, ignore rules and publication workflow.

## Confirmed tools

- `tool/find_compiler/`: compiler discovery, real validation, manual compiler paths, GUI/CLI and local preset merge.
- `tool/auto_define_config/`: synchronized define probes, fields, observations, source-rule preview/editing and GUI/CLI.

CMake remains the source of truth for module construction, source selection and generated headers. Python collects/validates observations and provides editing/discovery services; it does not generate C++ macros directly.

## Delivered implementation

Implemented and exercised:

- Strict `define < iso < core` module registration, lower-layer-only dependencies, module-specific minimum C++ standards and public/private propagation.
- Short physical include trees mapped to long `<destiny/...>` public includes.
- Boolean/integer/string facts, generated per-module macros/headers, strict binary effective values, local option overrides and exact integer comparisons.
- Ordered multi-file implementation groups, local aliases, fail-closed source selection, source/rule preview and four-space hierarchical reports.
- Vendored GoogleTest, PRE_TEST discovery, explicit multi-file programs/custom test main, project-root CTest/CLion working directories and Windows runtime staging.
- Compiler discovery/validation for all Windows GCC/Clang x86/x64 slots, local presets, asynchronous GUI/manual paths, and auto_define_config editor/GUI pages.
- AI-oriented contract and validation documents.

The source tree intentionally contains no production business modules. Test scenarios are temporary and cleaned under `build/verification`.

## Commands

```text
python -B -m tool.find_compiler scan --root D:/cpp/toolchains --no-defaults --output build/compiler-scan.json
python -B -m tool.find_compiler write-presets --input build/compiler-scan.json --select <identity>
python -B -m tool.auto_define_config inventory
python -B -m tool.auto_define_config sync --dry-run
python -B -m tool.auto_define_config check
python -B -m tests.build_system.verify --report build/regression.json
python -B -m tests.build_system.matrix --compiler-report build/compiler-scan.json --report build/matrix.json
```

Use the GUI subcommands only on a Python installation with Tk. Headless inventory/probe/rule/compiler operations remain available without a display.

## Acceptance and limits

The final source fingerprint matches the Windows 129/129 regression, WSL 127 passes plus two Windows-only skips, the minimum-version 119 passes plus ten missing-Tk skips, all 16 real compiler profiles, and clean Windows/WSL builds. The short final actual GUI check also passed. No repeated manual GUI or full-matrix rerun is needed merely to read this handoff.

Real macOS validation, installation/export, complete GPU/cache/rate inventory, external-project consumption and production business modules remain approved v1 exclusions. CLion WSL debugger/run binding is explicitly unverified, not inferred from native WSL/CTest. PLAN.md preserves the complete scope; ACCEPTANCE.md maps each requirement to evidence.
