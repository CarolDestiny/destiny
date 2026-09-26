# destiny-compat

Native CMake/Ninja build infrastructure for a modular C++ project. The maintained source tree starts empty; add modules using the documented interfaces rather than copying legacy business code.

## Entry points

Requirements: CMake 3.25+, Ninja and Python 3.10+. Interactive GUIs require Tk. Windows supports MinGW GCC / LLVM-MinGW Clang and Linux supports GCC / Clang, targeting x86/x64; real macOS validation is deferred.

```text
python -B -m tool.find_compiler gui
python -B -m tool.auto_define_config gui
```

The compiler tool validates local compiler pairs and writes ignored local presets. Use the selected presets directly with CMake or CLion. auto_define_config manages define-module counterparts and field/source-rule declarations; CMake generates headers and selects translation units.

## Documentation

- [Build guide](agent/build/README.md)
- [Runnable module-extension recipe](agent/build/EXTENDING.md)
- [CMake, Python and JSON contracts](agent/build/INTERFACES.md)
- [CLion and working-directory setup](agent/build/CLION.md)
- [Acceptance and validation evidence](agent/build/VALIDATION.md)
- [Git ownership and publication workflow](agent/build/GIT.md)

Tests, vendored GoogleTest sources/license/provenance, shared presets and AI maintenance documentation belong in Git. Local compiler presets, caches, IDE state and generated build output do not. Empty directories are not stored by Git; module registration creates the maintained source paths when they are needed.

## Verification

```text
python -B -m tests.build_system.verify --report build/regression.json
```

The existing accepted baseline is described in agent/build/EVIDENCE.json. Re-run affected checks after changing behavior; do not infer a new pass from historical reports.
