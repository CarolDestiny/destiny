# Validation Evidence

Updated: 2026-09-26
Status: V1 acceptance complete within PLAN.md scope and the environment limits recorded below.

## Current source and durable evidence

`EVIDENCE.json` records the exact source fingerprint, regression outcomes/skips, all 16 matrix profiles, toolchain identities and hashes of the local reports. The fingerprint includes implementation, tests, vendored sources and the runnable EXTENDING.md recipe.

Current fingerprint: `06e94a96b816a91b9820432b505f8ac72a89f1e13a7fa342d9d5bce96c6a1582` (339 files).

Every closure report below has identical before/after fingerprints matching this tree. Reports from earlier increments are historical, not substitutes for these results.

## Regression results

| Environment | Report | Collected | Passed | Skipped | Failures/errors |
| --- | --- | --- | --- | --- | --- |
| Windows 11, Python 3.14.7, CMake 4.4.2 | build/regression-windows-closure.json | 129 | 129 | 0 | 0/0 |
| WSL Ubuntu, Python 3.14.4, CMake 4.2.3 | build/regression-linux-closure.json | 129 | 127 | 2 Windows-only cases | 0/0 |
| Windows compatibility, Python 3.10.11, CMake 3.25.2 | build/regression-minimum-closure.json | 129 | 119 | 10 Tk cases; embedded Python lacks Tk | 0/0 |

The WSL skipped cases are executable DLL staging and missing CPU-helper runtime handling. Tk cases ran under Windows and under WSLg with a privately cached Tk runtime. The minimum-version skips are not GUI pass claims. The actual cached CMake/Python version commands were checked again at closure.

Reproduction:

```text
python -B -m tests.build_system.verify --report build/regression-windows-closure.json
```

Minimum version, PowerShell (only the current process environment changes):

```powershell
$env:PATH="D:\project\destiny-compat\cache\cmake-3.25\cmake\data\bin;$env:PATH"
.\cache\python-3.10\python.exe -B -m tests.build_system.verify --report build/regression-minimum-closure.json
```

WSLg, from the repository root:

```text
wsl -d Ubuntu -- env PYTHONPATH=/mnt/d/project/destiny-compat/cache/wsl-tk/runtime/usr/lib/python3.14:/mnt/d/project/destiny-compat/cache/wsl-tk/runtime/usr/lib/python3.14/lib-dynload LD_LIBRARY_PATH=/mnt/d/project/destiny-compat/cache/wsl-tk/runtime/usr/lib/x86_64-linux-gnu TCL_LIBRARY=/mnt/d/project/destiny-compat/cache/wsl-tk/runtime/usr/share/tcltk/tcl8.6 TK_LIBRARY=/mnt/d/project/destiny-compat/cache/wsl-tk/runtime/usr/share/tcltk/tk8.6 python3 -B -m tests.build_system.verify --report build/regression-linux-closure.json
```

The cache paths are local verification aids, not delivered runtime requirements. All delivered Python uses the standard library; interactive GUI use requires a Python installation with Tk.

## Real native compiler matrix

All eight Windows and eight WSL profiles passed independently: GCC/Clang x86/x64, each Debug/Release. Windows used MinGW GCC 16.2.0 and LLVM-MinGW Clang 22.1.8; WSL used GCC 15.2.0 and Clang 21.1.8.

```text
python -B -m tests.build_system.matrix --compiler-report build/compiler-scan-context-audit.json --report build/matrix-windows-closure.json
wsl -d Ubuntu -- python3 -B -m tests.build_system.matrix --report build/matrix-linux-closure.json
```

The shared scenario compiles and links real platform/CPU/memory modules, generates headers, selects intrinsic implementations, inspects output architecture, runs CTest/demo/bench, asserts project-root resources/current directory, and verifies a no-op build does not reconfigure, rewrite headers or rebuild objects. Ordinary Build is checked not to execute project programs or test discovery. Windows programs also run with compiler directories removed from PATH.

The WSL x86 acceptance previously exposed mounted-filesystem stat inode overflow; `_FILE_OFFSET_BITS=64` is applied consistently to project targets and vendored GoogleTest. Only required multilib packages were installed for the authorized validation; no system upgrade was performed. Delivered tools do not install dependencies.

## New closure checks and repairs

- Per-module resolved standard contexts are compile-checked before selection and cached by compiler content, architecture, minimum, configuration and relevant options; contexts remain separate from shared hardware macros.
- GUI `--cmake` now reaches inventory, save validation, source preview, probe subprocesses and header preview.
- Compiler identity includes driver content, preventing same-version replacement from silently reusing a preset directory. Actual local four-slot preset export passed after fixing a mixed available/failed-candidate export regression.
- Directory discovery respects cancellation; completion-handler exceptions no longer stop GUI worker polling.
- Missing Windows CPU-helper DLLs produce unavailable observations, not a disguised provider programming error. Malformed output and unexpected implementation exceptions still fail.
- Ordinary maintained source/header content edits rebuild actual consumers. A selected-source compile failure does not select a fallback or print the post-build selection summary.
- `test_extension_recipe.py` builds the exact nine file blocks from EXTENDING.md, probes real memory, validates facts/header/selection, runs from the root with `cmake -E chdir`, then verifies a declared option switches to the explicit fallback.
- Vendored GoogleTest provenance, license and every recorded file hash pass. Configuration/build uses local sources, not downloads or a package manager.

A 124-test Windows handoff run failed when obsolete Tk test windows were collected on a worker thread. A deterministic weak-reference test reproduced the ownership issue. Test teardown now releases Tcl objects on the owning thread; ten repeated GUI suites then passed without unraisable exceptions, and the final 129-test full Windows run passed. The failed historical report was retained rather than relabeled successful.

## GUI and IDE boundaries

The user requested minimal final interactive work. `build/gui-quick-closure.json` records the final short actual Windows GUI check at the current fingerprint:

1. Accepted the existing condition and saved rules successfully.
2. Ran define/memory through the GUI.
3. Observed read-only JSON and CMake macro preview with matching value `33959055360` bytes and availability `1`.
4. Closed the tool window and confirmed it was absent from the window inventory.

The earlier interactive record covers editing the numeric threshold, source preview and manual compiler validation/export. Windows CLion CMake Application and Google Test both used `$PROJECT_DIR$`; the recorded application succeeded and all three tests passed. See GUI_VALIDATION.md, `build/gui-interaction-evidence.json`, and `build/clion-validation-evidence.json` for their own observation/version boundaries.

CLion WSL toolchain/debugger launches were not observed. Native WSL configure/build, CTest and terminal execution were exercised separately. Real macOS hardware remains deferred; adapters and unsupported-target behavior have fixtures. No direct arbitrary file-manager launch is claimed to inherit a CMake-controlled cwd.

## Cleaned root and source hygiene

Both `build/clean-closure-windows.json` and `build/clean-closure-linux.json` record successful clean-root configure/build/check with the current fingerprint. Windows also configured/built the newly generated LLVM-MinGW x86 preset. `source/` and maintained define-counterpart directories contain no temporary module files. `build/verification` is empty after fixture cleanup.

The isolated old IDE fixture remains under ignored `build/clion-validation` as evidence; it is not part of the maintained source tree. The GUI is closed. No historical `D:/project/destiny` files were inspected or modified. Build/cache/local presets are ignored while agent/build documents remain included. Black checks passed for all 60 Python files. No commit was requested or created; the initially empty repository's implementation files remain untracked.

## Final acceptance audit

On 2026-09-26 the current fingerprint and every referenced closure-report hash were rechecked against EVIDENCE.json. All 19 PLAN.md acceptance items and six implementation phase gates are accounted for in ACCEPTANCE.md. The formerly open native regressions, exact documentation example, cleanup and short GUI check are included in the current evidence.

The final work changed only maintenance documents: reconciled statuses/checklists and added operational CLion toolchain/debugger/WSL instructions verified against official JetBrains documentation. Those instructions are clearly separated from observed run/debug results. Source behavior did not change, so repeating the same matrix or GUI interactions was unnecessary.

HANDOFF.md is the delivered entrypoint for future work. Reuse this evidence only while its input fingerprint matches; report any new change or defect with its own tests and boundaries. No unfinished v1 implementation task is hidden under the original scope exclusions.
