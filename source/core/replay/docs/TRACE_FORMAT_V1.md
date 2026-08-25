# Destiny Replay Trace Format v1

Status: architecture decision, implementation not started  
Format version: 1.0  
File family: `.dtrace` runtime trace + `.dmap` build map

## 1. Decision

`core/replay` exposes a small capture interface and writes runtime facts. It
does not parse source code, symbolize addresses, infer variable names, or
render a user-facing timeline. Those responsibilities belong to an offline
reconstructor.

The stable seam between both sides is a pair of versioned files:

- `<session>.dtrace`: append-only, crash-tolerant binary event stream written
  at runtime.
- `<build-id>.dmap`: immutable binary source/build map generated outside
  `core/replay` from the exact linked image, debug information, compile
  database, and source snapshot.

The two files bind through an exact `build_id`. A trace remains valid without
a map, but its source locations stay unresolved. A map may serve any number of
sessions produced by the same build.

The default root-relative storage layout is:

```text
cache/replay/maps/<build-id>.dmap
cache/replay/sessions/<session-id>.dtrace
```

JSON is permitted only as an optional diagnostic export. It is not the v1
storage contract: a very large project can have millions of sites, so both
authoritative files use an indexed binary container.

## 2. Non-negotiable feasibility rule

An object address (or project handle) plus a function pointer and source code
is not enough to reconstruct variable-level events.

It can identify, at best, the containing image/function. It cannot distinguish
two writes in the same function, loop iterations, inlined functions, optimized
variables, aliases, or concurrent invocations. Source alone also cannot map a
runtime address reliably after ASLR, optimization, inlining, thunk generation,
identical-code folding, or link-time optimization.

Every granular event must therefore contain one of these source-site keys,
listed from strongest to weakest:

1. a build-generated `site_id` embedded by instrumentation;
2. an instruction address normalized as `(image_instance_id, rva)`;
3. `(function_ref, event_ordinal)` where the ordinal is emitted by
   instrumentation and is stable within the exact build.

A bare function pointer is valid only for function enter/exit events. If the
runtime cannot provide any of the three keys above, v1 must report the event as
function-scoped and must not claim variable-level reconstruction.

Likewise, an object address without explicit lifetime-begin/lifetime-end
observations cannot be a stable variable identity: stack and heap addresses are
reused. If lifetime is unknown, the event carries an opaque observation ID and
the reconstructor must not merge separate observations into one variable.

Exact reconstruction also requires the matching PDB/DWARF/linker information
or precomputed `.dmap`; a source checkout alone is a degraded fallback.

## 3. Guarantees and exclusions

v1 guarantees:

- exact per-thread event order;
- explicit ordering semantics across threads;
- stable call, frame, object-lifetime, image, and source-site identities;
- exact matching to a build and source snapshot;
- explicit representation of missing, redacted, unavailable, and lost data;
- recovery of every complete chunk before a truncated/crashed tail;
- forward skipping of unknown optional chunks and records.

v1 does not, by itself, guarantee deterministic process re-execution. That
would additionally require capture and control of scheduling, system calls,
I/O, time, randomness, signals, devices, and all other nondeterministic input.
The module name is `replay`; the v1 artifact is specifically an observation
trace from which a detailed timeline can be reconstructed.

## 4. Identity model

Raw addresses are observations, never persistent identities.

| Entity | Persistent identity |
| --- | --- |
| Project | 128-bit `project_id`, assigned once to the repository |
| Source snapshot | VCS revision plus a digest of every participating file |
| Build | SHA-256 `build_id` from the canonical manifest and image hashes |
| Loaded image | session-local `image_instance_id` + exact image build ID |
| Code location | `image_instance_id` + RVA, or exact-build `site_id` |
| Thread | session-local monotonically allocated `thread_id` |
| Function call | session-unique `call_id` + optional `parent_call_id` |
| Variable declaration | exact-build `variable_id` from `.dmap` |
| Runtime object | session-unique `object_id` for one lifetime |
| Variable instance | `variable_id` + `call_id` + `object_id` |
| Large value | session-local `blob_id` |

An address may be reused after a lifetime ends. Reuse never reuses the old
`object_id`. For a subobject, the reference is `(object_id, byte_offset,
subobject_site_id)` rather than a new identity unless it has an independent
lifetime.

Function and data pointers inside a known image are normalized to an image RVA.
Heap/stack pointers are normalized to `(object_id, byte_offset)` when possible.
Other addresses are recorded according to the session address policy:
`none`, `hashed`, or explicitly opted-in `raw`.

C++ pointer-to-member representations are ABI-specific and may contain more
than an address. v1 does not accept their raw bytes as function identity. The
instrumentation layer must resolve a callable entry/site or mark it opaque.

## 5. Common binary container

All fixed-width integers use little-endian encoding. Payload IDs, counts, and
deltas use unsigned LEB128; signed deltas use signed LEB128. Strings are UTF-8
and are referenced through a string table. Source paths use `/`, are relative
to a declared source root, and include a content digest.

### 5.1 File header (64 bytes)

| Offset | Size | Field | Rule |
| ---: | ---: | --- | --- |
| 0 | 8 | `magic` | ASCII `DREPLAYT` for trace, `DREPLAYM` for map |
| 8 | 2 | `major` | `1` |
| 10 | 2 | `minor` | `0` |
| 12 | 2 | `header_bytes` | `64` |
| 14 | 1 | `byte_order` | `1` means little-endian |
| 15 | 1 | `address_bytes` | `4` or `8` for the producing build |
| 16 | 8 | `required_features` | reader must understand every set bit |
| 24 | 16 | `file_id` | random UUID; session ID for `.dtrace` |
| 40 | 8 | `created_unix_ns` | UTC Unix nanoseconds |
| 48 | 8 | `first_chunk_offset` | `64` in v1 |
| 56 | 8 | reserved | all zero; readers ignore |

`byte_order` describes the container, not the traced program's native object
representation. v1 writers emit only little-endian containers.

### 5.2 Chunk header (40 bytes)

| Offset | Size | Field | Rule |
| ---: | ---: | --- | --- |
| 0 | 4 | `chunk_magic` | ASCII `CHNK` |
| 4 | 2 | `chunk_type` | file-specific type |
| 6 | 2 | `chunk_flags` | compression/optional flags |
| 8 | 4 | `header_bytes` | at least `40` |
| 12 | 4 | reserved | all zero |
| 16 | 8 | `payload_bytes` | stored payload length |
| 24 | 8 | `chunk_sequence` | starts at 0, strictly increases |
| 32 | 4 | `header_crc32c` | header CRC with both CRC fields zeroed |
| 36 | 4 | `payload_crc32c` | stored payload CRC |

Chunks are append-only. A writer never goes back to repair earlier chunks.
Readers accept all complete, valid chunks and discard an incomplete final
chunk. A final index and end marker improve random access but are optional
after a crash.

Compression is per chunk, never across chunk boundaries. Core metadata and
loss records are uncompressed. v1 reserves flag bit 0 for Zstandard payloads;
a writer may use it only when required-feature bit 0 (`zstd_chunks`) is also
declared. All other v1 required-feature and chunk-flag bits are zero.

### 5.3 Common wire values

The following nested values have one canonical encoding:

| Value | Encoding |
| --- | --- |
| `CodeRef` | `image_instance_id: ULEB128`, then `rva: ULEB128` |
| `FunctionRef` | a `CodeRef` naming the callable entry |
| `SiteRef` | tag u8: 1 = `site_id`, 2 = `CodeRef`, 3 = `FunctionRef` + `event_ordinal` |
| `ObjectRef` | `object_id: ULEB128`, `byte_offset: ULEB128`, `subobject_site_id: ULEB128` |
| `VariableRef` | tag u8: 0 = unresolved, 1 = exact-build `variable_id` |
| `StringRef` | table-local `string_id: ULEB128`; zero means absent |
| `BlobRef` | session-local `blob_id: ULEB128` |
| `Bytes` | byte length as ULEB128 followed by exactly that many bytes |

`event_ordinal`, IDs, and RVAs are unsigned LEB128 values. A zero
`subobject_site_id` means no statically identified subobject. Runtime capture
may use an unresolved `VariableRef`; the reconstructor resolves it only when
the exact `SiteRef` maps uniquely. The module never fabricates a variable ID.

## 6. Runtime trace: `.dtrace`

### 6.1 Chunk types

| ID | Name | Cardinality | Purpose |
| ---: | --- | --- | --- |
| 1 | `SESSION` | exactly one, first | Project/build binding, policies, clocks |
| 2 | `STRING_TABLE` | zero or more deltas | Runtime-only strings such as thread names |
| 3 | `BLOB_BLOCK` | zero or more | Large value payloads keyed by `blob_id` |
| 4 | `EVENT_BLOCK` | one or more | Length-delimited runtime events |
| 5 | `LOSS_BLOCK` | zero or more | Explicit dropped/corrupt event ranges |
| 6 | `CHECKPOINT` | zero or more | Last durable sequences and dictionary state |
| 7 | `INDEX` | zero or one | Optional offsets by thread/time/sequence |
| 8 | `END` | zero or one, last | Clean-close counts and SHA-256 of all bytes before `END` |

`SESSION` includes:

- `project_id`, root executable `build_id`, and every initially known image
  build ID;
- process ID, parent process ID, executable name, target triple, ABI tag, and
  pointer width;
- wall-clock start plus monotonic clock kind, origin, and frequency;
- ordering mode: `thread_causal` or `global_total`;
- value policy and address policy;
- recorder schema/build version and enabled optional features.

Absolute source-root and executable paths are optional diagnostics and must not
be used for identity.

### 6.2 Event block

Each event block belongs to one thread. Its fixed logical prefix is:

| Field | Encoding | Meaning |
| --- | --- | --- |
| `thread_id` | u32 | owning thread |
| `block_flags` | u32 | ordering/compression details |
| `first_thread_seq` | u64 | sequence of first record |
| `first_global_seq` | u64 | zero outside `global_total` mode |
| `base_ticks` | u64 | monotonic timestamp base |
| `event_count` | u32 | complete records in payload |
| `event_schema_minor` | u16 | event payload schema |
| reserved | u16 | zero |

Every record then uses this envelope:

```text
record_bytes: ULEB128
kind:         ULEB128
flags:        ULEB128
tick_delta:   ULEB128
seq_delta:    ULEB128
payload:      kind-specific bytes
```

In `global_total` mode, `global_seq_delta` follows `seq_delta`. Record length
allows a reader to skip an unknown optional event. Block flush order has no
timeline meaning; sequences and timestamps carry the meaning.

### 6.3 Core events

| ID | Event | Required logical fields in wire order |
| ---: | --- | --- |
| 1 | `ImageLoad` | image instance, image build ID, normalized load base token, size |
| 2 | `ImageUnload` | image instance |
| 3 | `ThreadStart` | thread, parent thread, optional name |
| 4 | `ThreadEnd` | thread, outcome |
| 10 | `FunctionEnter` | call ID, parent call ID, function code ref, call-site ref |
| 11 | `FunctionExit` | call ID, return-site ref, optional return value |
| 12 | `FunctionUnwind` | call ID, throw/cancel reason, site ref |
| 20 | `VariableLifetimeBegin` | object ref, variable ref, frame call ID, site, storage, size |
| 21 | `VariableRead` | object ref, variable ref, frame call ID, site, value ref |
| 22 | `VariableWrite` | object ref, variable ref, frame call ID, site, before/after refs |
| 23 | `VariableLifetimeEnd` | object ref, variable ref, frame call ID, site, reason |
| 30 | `Allocation` | object ID, allocator kind, size, alignment, site |
| 31 | `Free` | object ID, site, reason |
| 40 | `Synchronization` | operation, synchronization object ID, acquire/release token |
| 50 | `Marker` | category ID, site, optional value/string ref |

Required fields are encoded left-to-right. IDs, sizes, enums, and flags inside
an event payload use ULEB128 unless a common wire value above says otherwise.
An optional-field bitmap is the first payload value whenever the record flags
declare optional fields. IDs 0 and 5-9, 13-19, 24-29, 32-39, and 41-49 are
reserved; writers do not use them.

A code reference is `(image_instance_id, rva)`. A site reference is tagged as
`site_id`, code reference, or `(function_ref, event_ordinal)`. Event payloads
must not contain native C++ struct dumps; their padding, enum size, and ABI are
not a file format.

`FunctionExit` is not emitted for an exceptional exit; `FunctionUnwind` is.
Every entered call ends in exactly one of those events unless a `LOSS_BLOCK` or
unclean process termination explicitly makes the interval incomplete.

### 6.4 Ordering modes

`thread_causal` is the default. Each thread is totally ordered by
`thread_seq`; `Synchronization` events provide cross-thread happens-before
edges. Events without a causal edge remain concurrent. The reconstructor must
not invent a total order from close timestamps.

`global_total` adds a session-wide monotonically increasing `global_seq` to
every event. It records recorder-observation order at additional synchronization
cost. It still does not prove language-level memory order for a data race.

### 6.5 Values

A value reference contains a `type_id`, capture status, and one encoding:

| Encoding | Meaning |
| --- | --- |
| `canonical_scalar` | fixed-width integer/float/bool bytes in container byte order |
| `utf8` | length-prefixed UTF-8 text |
| `object_bytes` | target-native bytes; valid only with exact ABI/build map |
| `inline_bytes` | at most 32 uninterpreted bytes |
| `blob_ref` | large bytes stored in a `BLOB_BLOCK` |
| `sha256` | value intentionally represented by digest only |
| `redacted` | policy withheld the value and records a reason code |
| `unavailable` | optimized out, unreadable, torn, or unsupported |
| `none` | event does not request a value |

Floating-point values use their bit pattern; no decimal conversion occurs in
the writer. Non-trivial C++ objects require an explicit serializer description
in `.dmap`; blindly copying their storage is never presented as a semantic
value. The session declares whether before-values, after-values, reads, and
pointer addresses were captured.

### 6.6 Loss and failure

Loss is data, not a log message. `LOSS_BLOCK` records:

- affected thread or all threads;
- first known missing per-thread/global sequence and count when known;
- time interval;
- cause (`buffer_full`, `allocation_failure`, `io_failure`, `unsupported`,
  `corrupt_block`, `process_crash`, or extension value);
- last durable checkpoint.

The reconstructor marks all affected frames/objects as incomplete. It never
joins values across a loss interval as though continuity were proven.
If the file has no valid `END` chunk, the reader additionally synthesizes an
unclean-termination gap after the last durable checkpoint. A hard-crashed
process is not expected to append its own `process_crash` loss record.

## 7. Build map: `.dmap`

The map is generated for one exact build. It uses the same file/chunk framing
with these chunk types:

| ID | Name | Contents |
| ---: | --- | --- |
| 1 | `MANIFEST` | project, build, source, compiler, linker, ABI identities |
| 2 | `STRING_TABLE` | deduplicated UTF-8 strings |
| 3 | `IMAGE_TABLE` | image IDs, exact hashes, preferred bases, sections |
| 4 | `FILE_TABLE` | root-relative paths and SHA-256 content hashes |
| 5 | `TYPE_TABLE` | type IDs, names, size/alignment, encoding/serializer |
| 6 | `FUNCTION_TABLE` | function IDs, names, image/RVA ranges, source spans |
| 7 | `SITE_TABLE` | site IDs, event kinds, function IDs, source locations |
| 8 | `VARIABLE_TABLE` | declaration IDs, scopes, types, storage and locations |
| 9 | `INLINE_TABLE` | inline call chains and discriminators |
| 10 | `INDEX` | lookup by ID, RVA range, file, function, and site |
| 11 | `END` | table counts and SHA-256 of all bytes before `END` |

Table entries are length-delimited records. IDs are dense unsigned integers
local to the build map. Tables may be split across multiple same-type chunks;
the index resolves their byte ranges.

### 7.1 Required manifest evidence

The manifest contains at least:

- `project_id` and SHA-256 `build_id`;
- repository revision and dirty-state digest;
- target triple, architecture, endianness, ABI, compiler ID/version;
- complete compile-option and definition digest;
- linker identity/options, optimization, LTO, and identical-code-folding state;
- exact hashes of executable/library images and PDB/DWARF/linker artifacts;
- compile database digest;
- every participating source file's root-relative path and content hash;
- map-generator name/version and generation timestamp.

Git commit alone is insufficient because generated files, dirty changes,
toolchains, flags, and link order can change addresses and optimization.

`build_id` is computed without recursion as SHA-256 over the canonical
manifest with its `build_id` field omitted, followed by the ordered exact image
and debug-artifact hashes. The same canonicalization algorithm and its version
are recorded in the manifest.

### 7.2 Site and mapping quality

Every site record includes:

- `site_id`, owning `function_id`, and expected event kind;
- file ID, line, UTF-8 column, lexical scope, and discriminator;
- zero or more instruction RVA ranges;
- inline chain ID;
- mapping quality: `exact`, `range`, `ambiguous`, or `unavailable`;
- optional candidate IDs when mapping is ambiguous.

Optimized code can merge, move, or remove operations. The map records that
fact. The offline reconstructor may show candidates and confidence, but must
never silently choose a source variable or line.

## 8. Reconstruction pipeline

```text
exact executable + debug artifacts + compile database + source snapshot
                              |
                              v
                     map generator -> .dmap
                                           \
instrumented process -> core/replay -> .dtrace -> reconstructor -> views
```

The reconstructor performs these gates in order:

1. validate header, feature bits, chunk CRCs, and sequence continuity;
2. require exact project/build/image IDs before source symbolization;
3. verify source content hashes, not only paths;
4. resolve code/site refs through map indexes;
5. pair calls and variable lifetimes without crossing loss intervals;
6. build per-thread order and declared cross-thread causal edges;
7. decode values only when type, ABI, serializer, and capture policy allow it;
8. label every unresolved or ambiguous result explicitly.

Derived timelines, JSON, flame graphs, and source annotations are disposable
views. They are not written back into the authoritative trace.

## 9. Compatibility rules

- A major version changes only for incompatible framing or semantics.
- A minor version may add optional chunks, events, fields, encodings, or flags.
- Unknown length-delimited optional records are skipped.
- Unknown `required_features` bits cause a hard read failure.
- Existing numeric IDs and meanings are never reused.
- Writers emit the oldest minor version that represents all enabled features.
- Readers preserve unknown bytes when performing container-level copying.
- `.dtrace` and `.dmap` versions advance independently after v1 if necessary;
  their manifest declares the accepted counterpart range.

## 10. Security and privacy

Extreme-granularity traces can contain credentials, personal data, proprietary
source structure, and exploitable addresses. Full value capture and raw address
capture are opt-in policies, not defaults. Every trace records its policy so a
consumer cannot confuse redaction with an empty value.

v1 provides integrity checks, not encryption. Storage encryption belongs below
the container or in a future required feature. Access control and retention are
deployment responsibilities. Diagnostic absolute paths, command lines, and
environment variables are excluded unless explicitly enabled.

## 11. Ownership seam

`core/replay` owns:

- session/thread/call/object ID allocation;
- normalized runtime event acceptance;
- per-thread buffering, chunk framing, checksums, checkpoints, and explicit
  loss accounting;
- `.dtrace` conformance.

Instrumentation owns producing valid site/function/object/value observations.
It may be compiler-, macro-, wrapper-, or platform-based, but those mechanisms
are not exposed as part of the replay module interface.

The offline toolchain owns:

- exact-build map generation and `.dmap` conformance;
- debug/source parsing, symbolization, ambiguity reporting, reconstruction,
  querying, and visualization.

This seam keeps source parsers, compiler-specific debug readers, and UI models
out of the runtime module. The file contract is the shared interface.

## 12. Conformance gates before implementation is accepted

An implementation is not v1-conformant until tests demonstrate:

- golden byte-for-byte headers, chunks, and core event records;
- read recovery after truncation at every byte of the last chunk;
- CRC failure isolation and explicit loss reporting;
- ASLR normalization and repeated image load/unload identity;
- address reuse without `object_id` reuse;
- recursion, exceptions, inlining, overloads, and ambiguous optimized sites;
- per-thread and causal/global ordering behavior under concurrency;
- source/build/hash mismatch rejection;
- redacted, unavailable, hash-only, inline, and blob values;
- unknown optional record skipping and unknown required-feature rejection;
- multi-gigabyte traces with bounded reader and writer memory.

These gates validate the file seam. Internal buffering and instrumentation
implementations may change without changing consumers.
