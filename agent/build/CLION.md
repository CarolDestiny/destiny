# CLion Workflow

Validated on Windows 11 with CLion 2026.2.2 on 2026-09-26. This document describes the supported IDE workflow; it does not configure global IDE settings automatically.

## Import

1. Open the repository root in CLion.
2. Let CLion load the shared `CMakePresets.json` and any locally generated `CMakeUserPresets.json`.
3. Choose a validated configure preset. Each compiler/architecture/configuration has its own binary directory.
4. Reload CMake after changing fields, probe code, source rules or local option overrides.

The generated preset identity includes compiler family/version, target architecture, target triple, options and content fingerprints of both driver executables. Re-scan after upgrading a toolchain; old reports without fingerprints cannot be exported. Do not switch compilers inside an existing incompatible build directory; choose a fresh preset/build directory instead.

## Bind an IDE toolchain and debugger

Presets select native build tools but do not fully specify CLion's debugger. Create a project-specific toolchain under **Settings / Build, Execution, Deployment / Toolchains**; do not change unrelated toolchains or make it the global default.

1. For GCC, add a MinGW toolchain and select the validated installation rather than accepting a different bundled compiler. For the LLVM-MinGW installation, use a custom MinGW or System toolchain and explicitly select its clang/clang++ executables. MSVC and clang-cl remain outside this project's supported compiler set.
2. Check CMake (3.25 or newer), Ninja, both compiler paths and target architecture against the find_compiler result. The tool's successful compile/link/run check is not a debugger-compatibility test.
3. For MinGW debugging, select CLion's bundled GDB or a suitable installed custom GDB in the toolchain's Debugger field. The debugger must support the selected target/debug information. A Debug build is the starting point for breakpoint work; the project does not install or choose a debugger automatically.
4. Imported preset profiles are read-only and initially may be disabled. In **Settings / Build, Execution, Deployment / CMake**, enable the required one. If it is bound to the wrong IDE toolchain, copy the imported profile and select the project-specific toolchain in that editable copy. Keep the verified compiler/options and assign a fresh binary directory. Do not switch compilers inside an existing cache.
5. Select that CMake profile for the application or Google Test configuration. Use the working-directory settings below. To verify debugging on a new machine, set a breakpoint in its own demo/test source and check that Debug stops there. No breakpoint session is claimed by the recorded run-only evidence.

Copying the IDE profile avoids hand-editing tool-owned generated preset entries that may be replaced on the next export. A hand-maintained configure preset can alternatively use CLion's `jetbrains.com/clion` vendor toolchain name; preserve the find_compiler ownership metadata rather than repurposing its generated entries. Test presets are usable with native `ctest --preset`; do not assume every CTest preset becomes an IDE Google Test configuration.

## Working directory

CMake/CTest properties set the project root for registered tests. CLion run configurations are separate from CMake test properties and must also set their Working directory:

```text
$PROJECT_DIR$
```

For a CMake Application configuration, set this in the application run configuration. For a Google Test configuration, set it in the Google Test run configuration. The validated application and Google Test configurations in the isolated fixture both recorded the absolute project root and passed root-relative resource assertions.

For new configurations, open Run / Edit Configurations and edit the **CMake Application** and **Google Test** configuration templates. Set Working directory to `$PROJECT_DIR$` in each. Template changes do not repair existing configurations: select every existing project run/test configuration and check the same field. Leave unrelated projects, debugger choices and environment settings unchanged. The exact menu placement may differ between IDE versions; the required property is the run configuration's Working directory.

The observed Windows run configurations are recorded in GUI_VALIDATION.md. Template setup is a maintenance instruction, not a claim that every user's IDE template has been modified or validated.

Executable paths remain in the build tree; working directory and executable location are intentionally different values.

## Test/demo/bench behavior

- Build compiles enabled targets but does not run them.
- CTest runs both deferred discovery and tests from the project root. Discovery is PRE_TEST, never part of Build. With CMake 3.29+, a native `cmake -E chdir` test launcher preserves the program cwd while CMake writes discovery metadata under `reports/discovery/<target>`. Older supported CMake uses the root discovery directory without that newer metadata behavior. Actual test WORKING_DIRECTORY is explicitly the root on both paths.
- CLion Google Test runs the selected test executable with the project-root working directory.
- CLion CMake Application runs a selected demo with the project-root working directory.
- Runtime DLL staging is attached to Windows program links; the staged directory is not the project root.

## WSL toolchain binding

These are documented setup steps, not a claim that the WSL IDE route was exercised. Windows CLion can use an existing WSL distribution without launching a second IDE inside Linux. No distribution/package installation is performed by the project tools.

1. Add a **WSL** toolchain in Toolchains, name it for this project, and select the intended installed distribution in Toolset. Wait for detection and verify the Linux CMake, Ninja, C/C++ compiler and debugger paths. Do not use a Windows `.exe` as a WSL compiler or debugger.
2. Create a separate editable CMake profile bound to that WSL toolchain. Select Ninja, Debug and a new binary directory (for example `build/clion-wsl-gcc-x64-debug`). Leave Windows profiles unchanged. Generated Linux presets remain useful from a WSL shell; their host conditions need not make them visible as Windows-hosted IDE profiles.
3. Use the paths verified in the active distribution. The tested Ubuntu setup uses the following CMake options for GCC x64:

```text
-DCMAKE_C_COMPILER=/usr/bin/gcc -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DPython3_EXECUTABLE=/usr/bin/python3
```

For an already validated multilib x86 pair, use another binary directory and add `-DCMAKE_C_FLAGS=-m32 -DCMAKE_CXX_FLAGS=-m32`. For Clang, use the validated Linux clang/clang++ pair instead. This is not an instruction to install missing multilib packages automatically.

4. Reload and inspect the CMake cache: compiler/Python paths must be Linux paths and the root must map to the WSL checkout (here `/mnt/d/project/destiny-compat`). Do not reuse a Windows build cache or Windows observation files.
5. Select the WSL CMake profile in a CMake Application or Google Test run configuration and apply the root working-directory policy. Check actual cwd and root-relative resource access on its first run. A debugger belongs to this WSL toolchain, not the Windows one; verify a Debug breakpoint separately before claiming debugger support.

The matrix proves native Linux configure/build/run and CTest behavior. It does not prove IDE debugger binding; that distinction remains recorded in VALIDATION.md.

## Explicit terminal execution

Use the active OS's absolute paths. For example, in PowerShell after a program has been built:

```powershell
$project = (Get-Location).Path
$binary = Join-Path $project 'build/<profile>/<configuration>/iso/buffer/demo/show.exe'
cmake -E chdir "$project" "$binary"
```

In a WSL/Linux shell opened at the project root:

```sh
project="$PWD"
binary="$project/build/<profile>/<configuration>/iso/buffer/demo/show"
cmake -E chdir "$project" "$binary"
```

Replace the profile/configuration with the configured binary directory or copy the absolute Executable path from the source-selection report. The module example and its actual terminal runs are documented in EXTENDING.md and VALIDATION.md. These commands run a program explicitly; `cmake --build` never does so. A direct launch from another terminal or a file manager inherits that launcher's cwd, not a universal property embedded in the binary.

Windows application/Google Test IDE launches were observed. WSL native configure/build, CTest and terminal execution were exercised; CLion's WSL debugger/run binding was **not** observed and remains explicitly unverified.

## Troubleshooting

- If a preset has the wrong compiler or architecture, delete/recreate only its build directory; do not mutate the compiler in-place.
- If a source rule or generated header appears stale, reload CMake and inspect `build/<profile>/<config>/generated` and `reports`.
- If a program cannot find a root-relative resource, inspect the run configuration's Working directory before changing the program.
- If a Google Test discovery failure occurs on 32-bit Linux, verify `_FILE_OFFSET_BITS=64` is present for the project and vendored GoogleTest targets.

## Maintained-header navigation

Physical headers stay under the module's short `include` directory. A long public include may first open a generated forwarding header under the active binary directory. Its one literal include points to the maintained file; follow that include or open the short path in the project tree. Edit the maintained file, not the forwarder. Regeneration removes obsolete forwarders, and real native tests cover nested/relative includes and paths with spaces or non-ASCII characters.

## Upstream setup references

The IDE setup instructions were checked against JetBrains' official documentation on 2026-09-26. These references explain the IDE controls; they do not replace the project's recorded runtime evidence.

- CMake presets, read-only imports, profile copies and toolchain association: `https://www.jetbrains.com/help/clion/cmake-presets.html`
- Windows MinGW/System toolchains and debugger selection: `https://www.jetbrains.com/help/clion/quick-tutorial-on-configuring-clion-on-windows.html`
- WSL distribution/toolchain/profile binding: `https://www.jetbrains.com/help/clion/how-to-use-wsl-development-environment-in-product.html`
