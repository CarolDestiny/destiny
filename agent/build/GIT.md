# Git Ownership and Publication

Updated: 2026-09-27

## Repository

Remote: `https://github.com/CarolDestiny/destiny.git`. Local branch and upstream: `compat` -> `origin/compat`.

The user explicitly approved replacing the failed legacy implementation with the current project. The publication is based on remote commit `8c13cb1704a5a911a22f08e20a1e1cd7ac2cafca`: old files are removed from the new tree while existing commits remain in history. This is a normal fast-forward update, not a force push or a merge that retains obsolete production modules. No local historical project directory is used.

## What git add -A includes

- Root shared CMake files, Git policies and README.
- Maintained cmake/, tool/, tests/, source/ modules, and project data/docs when added.
- Module CMake registrations, source_rules.json, probe.py and fields.json.
- Vendored third-party source, licenses and provenance manifests.
- AGENTS.md and agent/build maintenance and acceptance records.

The ignore policy is exclusion-based so a future source/module file is included without editing an allowlist. It does not blanket-ignore directories named build: only the root /build/ is ignored, leaving agent/build tracked.

## What remains local

Root build/, cache/, out/, cmake-build-* and vcpkg_installed/ directories; root CMake/Ninja generated state; CMakeUserPresets files; local IDE state; Python environments/caches; operating-system metadata. Ignoring a path never deletes it. Ignore rules do not untrack a previously committed file automatically.

Use an ignored build directory for any custom binary output. If another generated output location is introduced, add a specific rule before staging. Do not broadly ignore all JSON, headers, libraries or executables: deliberate source fixtures and vendored artifacts may legitimately use those extensions. Do not use git add -f for generated/local files.

## Byte preservation

The accepted evidence and vendored provenance hash file bytes. Existing inputs include both LF and CRLF. The repository-level `* -text` attribute preserves those exact bytes on add/checkout despite a machine's core.autocrlf setting. Normal text diff/merge remains available. No global Git setting is changed.

If a future change deliberately normalizes line endings, review it as a source change and refresh affected fingerprints/provenance/evidence; never silently normalize a pinned vendor tree.

## Routine workflow

```text
git status --short --branch
git add -A
git diff --cached --stat
git diff --cached --check
git commit -m "Describe the maintained change"
git push
```

The branch is configured for origin/compat with repository-local push.default=simple; plain git push targets that branch after publication. On a non-fast-forward rejection, fetch and inspect remote changes; do not force-push. Author identity and authentication come from the user's existing Git configuration, not secrets stored in this repository.

The initial Git setup checks staged paths against ignored-output boundaries, preserves every pinned GoogleTest file, scans for obvious credential patterns without printing values, and compares staged source bytes with the verified working tree.
