# AI Maintenance Guide: Python Build Tools

Status: Active maintenance guide for the accepted v1 implementation.
Updated: 2026-09-26
Primary tool: `auto_define_config`; compiler discovery remains `find_compiler`.

Read this guide when implementing or extending Python field declarations, probes, module synchronization, GUI behavior, preset storage or their CMake integration. Read PLAN.md for product decisions; this guide describes the maintenance procedure, not a second specification.

Read INTERFACES.md for implemented CLI, GUI, schema, probe and explicit migration contracts; read VALIDATION.md and GUI_VALIDATION.md for actual evidence. Command availability and UI operation do not by themselves prove every acceptance requirement. Keep unverified cases explicit.

## 1. Ownership and sources of truth

| Item | Authority and editing rule |
| --- | --- |
| Registered define modules | Use the same module inventory as CMake; never hand-maintain a parallel registry |
| Module fields.json | Declares field IDs, types, units, macro exports and configurable metadata; safe GUI/manual editing |
| Module probe.py | Maintained Python logic; synchronization creates it once and preserves later edits |
| Module source_rules.json | Source-condition and implementation-group declarations; GUI and CMake share it |
| Probe facts JSON | Generated observations in a build/preview directory; never a maintained configuration source |
| Generated header/report | Produced by CMake using registered data; never fix behavior by hand-editing it |
| Shared Python helpers | Platform access, normalization, bounded execution and safe file operations |
| Compiler presets | Merge tool-owned local entries while preserving user/other-platform entries |

Paths under tool/auto_define_config/define mirror registered module paths below source/define. New hardware fields must not require editing an independent central import list, a hardcoded GUI field list and a central macro list. Do not parse maintained Python text to change its functions from the GUI; declarations are the structured editing surface.

## 2. Read before changing

1. Confirm the requested operation and inspect the relevant module registration, declarations, probe, shared helpers and tests. Check local repository guidance and existing user changes.
2. Read the applicable implemented contract from INTERFACES.md. For a behavior change, inspect the corresponding PLAN.md section before choosing a new policy.
3. Identify what owns the value: observed hardware, selected target/compiler context, user option or simulation. Keep those categories distinct.
4. Identify the smallest externally observable test: declaration validation, probe fixture, synchronization operation, generated macro or selected source.
5. State any schema/identifier compatibility impact before editing persistent files. A new declared field is not automatically a new schema version; a changed interpretation may be.

Completion: the change has one authoritative owner, an observable acceptance test and no conflict with approved product policy.

## 3. Adding a define module or field

### New module

1. Register the define module using the existing module interface. Confirm it is an actual module, not only a grouping directory.
2. Run the documented check/dry-run and inspect the proposed counterpart paths.
3. Run sync to scaffold only missing files. Inspect the result; existing source bytes must be unchanged.
4. Declare fields and implement the probe through the public probe interface. Use shared helpers for platform queries; imports must remain side-effect-free.
5. Add deterministic fixtures and an integration example. Verify automatic discovery and GUI availability without editing central lists.
6. Reload CMake and inspect generated facts, configuration header and source report. Update module documentation and evidence.

### New field in an existing module

1. Define its meaning, type, unit, observation scope, export macro and expected unavailable cases. Reuse an existing field only if its meaning really matches.
2. Add the declaration, then implement the provider result. Keep fallback/effective-value conversion centralized rather than reimplementing it differently per probe.
3. Test success, unavailable input and malformed provider output. Add type/range and unit checks where relevant.
4. Verify that the GUI derives its control from the declaration, CMake exports the correct macro, and a rule using the field selects the expected source.
5. Update the reference example and validation record. Check that unchanged values do not rewrite headers.

Completion: module/field discovery, JSON data, GUI representation, CMake evaluation and generated output agree in a repeatable test.

## 4. Implementing a hardware provider

- Accept an explicit probe context; return observations rather than modifying build files, process-global environment or generated headers.
- Prefer injected query/subprocess helpers so tests can supply fixture data without real hardware, administrator access, GUI state or network access.
- Query only necessary metadata, with documented timeouts and bounded output. Invoke executables with structured argument lists rather than interpolated shell commands.
- Record the provider and reason when information is denied, missing or unsupported. Do not silently convert a provider implementation bug into absent hardware.
- Apply PLAN.md's strict binary failure policy centrally. In particular, unavailable false negates to true. Test this deliberately; do not reintroduce three-valued logic as a refactor.
- Distinguish observed values from defaults and simulation. A real zero is different from unavailable numeric data; preserve availability separately even when a generated macro needs a numeric sentinel.
- Preserve units and measurement scope. Installed capacity, OS-visible capacity, configured transfer rate, clock frequency and shared/dedicated GPU memory are not interchangeable.
- Do not infer target architecture from the Python interpreter. Do not merge WSL guest observations with Windows host metadata under one field name.
- Future multi-device providers need stable provider-scoped identities and per-device data, not an assumption that one GPU or memory device represents the whole system.
- Do not add vendor SDKs, privileged queries or runtime code-dispatch mechanisms without updating the approved scope.

Completion: success, denied access, unsupported observation, timeout and invalid output have deterministic tests and distinct diagnostic behavior.

## 5. Synchronization, safe storage and GUI changes

- Check mode is read-only; sync creates only missing managed skeletons. CMake configure validates correspondence without executing sync writes.
- Verify idempotence and byte-for-byte preservation of maintained files. Detect conflicts and outside modifications before replacing declarations or local presets.
- Use staged validation and safe writes so a failed operation leaves the prior valid file intact. Do not execute editable Python to discover declaration metadata.
- Orphaned maintained files are reported and inactive, not automatically removed. Renames require an explicit mapping; verify destination conflicts before moving anything.
- Resolve cleanup/move paths and prove they remain under the intended workspace or managed output root. Never recursively delete a computed or unchecked path, especially on Windows.
- A GUI edits declarations and documented user options, not handwritten probe functions or raw generated facts. Code editing opens the corresponding probe.py.
- Keep GUI controllers thin and business behavior in headless services. Scanning/probing must not block the UI indefinitely; cancellation and errors must leave files valid.
- Selection and macro previews use CMake's evaluator/generator, not a separately implemented Python expression interpreter. Label simulations and isolate their output.

Completion: CLI and GUI share behavior, external edits are protected, read-only operations are non-mutating, and interrupted/failed actions preserve valid source.

## 6. Schema or macro changes

1. Search consumers in Python, CMake, GUI controls, maintained rules, generated-header aliases and test fixtures.
2. Determine whether existing valid files still mean the same thing. Keep the schema version unchanged for compatible additions; version incompatible changes explicitly.
3. Document accepted versions and failure/migration behavior in INTERFACES.md. Unknown versions fail without rewriting the input.
4. Add a golden before/after example and test existing inputs as well as new output. Persistent file migrations require a preview and explicit action, not silent conversion during configure.
5. Update schema documentation and affected examples together. Preserve the separation between shared hardware facts and module-specific compilation capability context.

Completion: every affected reader/writer is accounted for, old-file behavior is explicit and generated macros still describe the data used to select sources.

### Context-sensitive work

Do not infer a consumer's C++ mode from the Python interpreter, a define module, or a process-global flag. CMake resolves each module's minimum and compile-checks its context before running probes; the optional `target["compilation_contexts"]` is keyed by module path. Keep that metadata separate from shared observations and generated global macros. A new capability provider must identify exactly which target/options it measures and test the affected contexts.

Compiler discovery evidence includes both driver content hashes. After changing the executable-identity contract, regenerate local scan reports rather than hand-editing their signatures. Preserve unrelated presets and never reuse an incompatible binary directory. GUI context arguments such as `--cmake` must survive every headless call, including worker subprocesses.

EXTENDING.md contains the complete short-header, numeric-provider and ordered-source example. Its recipe is validated in an isolated build workspace, not left as a production module.

## 7. Required evidence for a Python change

Run the relevant focused tests first, then affected integration checks. Record exact commands and outcomes in VALIDATION.md once it exists.

- Declaration validation and probe success/failure fixtures.
- Headless CLI behavior, meaningful exit status and English diagnostics.
- Sync dry-run, incremental scaffold, repeated sync, partial counterparts and preserved source hashes where affected.
- Facts -> CMake -> generated-header and selected-source assertions.
- GUI load/edit/save/reload plus external-modification protection where affected.
- Effective-content stability and relevant cache separation for compiler/architecture/standard changes.
- At least the applicable real-platform smoke check; fixture-only coverage must be labeled as such.

Do not execute a fixture-selected unsupported instruction set on the real machine. A selection-only simulation does not establish hardware support or a successful native build.

## 8. Implementation reference requirements

Keep INTERFACES.md and its linked EXTENDING.md recipe current with:

- Actual CLI entrypoints, operation syntax, exit statuses and example commands verified from the checkout.
- Probe context/result structures, field/facts/rule schema versions and generated-file ownership.
- Type/unit handling, expected-unavailability versus programming-error policy, and strict binary effective values.
- The module-to-probe mapping and sync/rename/orphan lifecycle.
- One minimal end-to-end define module, one numeric condition and one multi-file ordered implementation group.
- How to add providers without changing the generic GUI/evaluator, and where platform-specific helpers belong.

VALIDATION.md must distinguish real pass, failure, blocked environment, fixture-only coverage and not run. Document limitations and reproduction steps rather than substituting screenshots or assertions for executable evidence.

## 9. V1 handoff checklist (2026-09-26)

- [x] Maintained source, generated output and editable configuration have not been conflated.
- [x] No unrelated user file or historical project was changed.
- [x] Relevant tests and examples cover the actual change and its failure paths.
- [x] Updated commands were executed, or explicitly labeled unverified.
- [x] References and schema examples agree with implementation.
- [x] Temporary fixtures are cleaned without deleting user-created source.
- [x] Final report lists changed files, checks run, remaining limitations and any required user action.

This dated checklist records the initial v1 handoff, supported by ACCEPTANCE.md, VALIDATION.md, EVIDENCE.json and HANDOFF.md. For each future change, reapply these checks to that change; a previously accepted baseline is not proof that new behavior passes.
