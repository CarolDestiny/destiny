# GUI Interaction Evidence

Date: 2026-09-26
Scope: The project's own Tk windows operating on the isolated `build/clion-validation` fixture. No production module or historical project was edited.

## Computer-use observations

### auto_define_config

1. Selected `iso/hardware/cpu` and opened its `large` alias as a structured comparison tree.
2. Changed the memory threshold from `1073741824` to `2147483648`, applied the node and saved the rule file.
3. Read back `source_rules.json` and verified the exact new integer text.
4. Selected the fixture's generated facts file and ran the CMake-backed preview. It selected `narrow` and `windows`, and the capacity condition used `2147483648`.
5. Opened `define/memory`, ran the actual Windows memory provider from the GUI, and inspected the read-only CMake header preview. The preview reported the same integer observation and `_AVAILABLE=1`.
6. Restarted after the dialog-positioning fix; the condition editor opened over its owning window on the same monitor, and the saved threshold loaded correctly.

### find_compiler

1. Entered the installed GCC x64 C and C++ executable paths manually.
2. Started actual compile/link/architecture/run validation from the GUI and observed an available result.
3. Exported the selected result to the isolated project's `CMakeUserPresets.json`.
4. Used native `cmake --list-presets -S build/clion-validation` to verify the generated Debug and Release configurations. Export did not build the project.

## Defects found and fixed

- Modal editors used default desktop placement, putting the popup away from its owner on multi-monitor setups. Shared `tk_layout.show_dialog` now positions condition, candidate and field editors relative to their top-level owner; a geometry regression test covers a secondary-monitor origin.
- Alias-list refresh discarded selection while leaving the old expression summary visible. Refresh now retains a surviving selection and regenerates its expression, or clears the summary when no selection remains.
- Manual validation called untested slots unavailable. The shared compiler summary now distinguishes `unchecked`, `not-found`, `unavailable` and `available`.
- A full rescan merged into old candidate data, potentially retaining a stale available result. Full scans now replace observations; manual revalidation supersedes an old result for the same C/C++ paths and architecture.

Regression tests live in `test_gui.py` and `test_compiler_tools.py`. The compiler status changes were tested through the same GUI model callbacks; the manual-path/export interaction was observed in the prior version, before that display-only repair.

## Current closure evidence

- `build/regression-windows-closure.json`: 129 tests, no failures/errors/skips.
- `build/regression-linux-closure.json`: 129 tests, no failures/errors, two Windows-only skips. All ten Tk cases ran under WSLg using the private cache.
- `build/regression-minimum-closure.json`: 129 tests, no failures/errors; ten GUI cases skipped because embedded Python 3.10.11 has no Tk.
- All 16 Windows/WSL compiler profiles were rerun at the closure fingerprint; see EVIDENCE.json and VALIDATION.md.

The earlier actual edit/compiler-export sequence above is historical interactive evidence. The current automated suite exercises the repaired GUI/headless paths, including asynchronous saves and explicit CMake routing.

## Final short actual UI check

At the user's request, the final interactive check was deliberately small. `build/gui-quick-closure.json` records it at fingerprint `06e94a96b816a91b9820432b505f8ac72a89f1e13a7fa342d9d5bce96c6a1582`:

- Accepted the existing 2147483648-byte alias without changing it; Save rules reported successful completion.
- Selected define/memory and ran the real provider.
- Read JSON observation 33959055360 bytes, status available, and the matching CMake header value 33959055360LL with availability 1.
- Closed the tool window and verified it was absent from the window list.

This check used the current project GUI with explicitly selected cached CMake 3.25.2 against the isolated fixture. It did not repeat the compiler GUI, CLion or every editing path. No production source module was changed. Do not redo broad manual GUI coverage on resume unless a specific new regression requires it.
