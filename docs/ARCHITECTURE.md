# AI File Manager Architecture

This diagram distinguishes implemented components from future milestones. The core remains domain-agnostic: every first-level directory under `knowledge/` automatically becomes a domain.

```mermaid
flowchart LR
    F["D:/domains/<any-folder>/**"] --> D["Generic discovery"]
    D --> W["Manual scan / watcher / scheduler"]
    W --> H["Stable-file check + SHA-256"]
    H --> E["Replaceable extractor registry"]
    E --> U["Normalized rich units: pages / headings / tables / rows"]
    U --> I["Idempotent ingestion service"]
    I --> M[("SQLite metadata")]
    I --> T[("Extracted document text")]
    I --> V[("Document versions + scan history")]
    I --> X[("FTS5 keyword index")]
    M --> C["CLI"]
    T --> C
    X --> C
    V --> O["Health + structured logs"]

    X -. "future" .-> S["Chunks + vector index"]
    S -. "future" .-> R["Hybrid retrieval + models"]
    R -. "future" .-> A["REST / MCP / Web / agents"]
```

## Milestone 3 component boundaries

- Files remain authoritative and are never modified.
- Discovery derives domains only from folders; there is no domain registry.
- Extractors are replaceable and isolated from orchestration.
- A checksum identifies document content; unchanged content is not re-extracted.
- Each successfully observed checksum is retained as an immutable version.
- Extraction attempts and scan summaries provide an operational audit trail.
- Files that change during processing are deferred until a later scan.
- FTS5 is rebuildable from stored document text.
- The source root defaults to `D:\domains` on Windows and can be overridden with `AI_FILE_MANAGER_DOMAINS_ROOT`.
- Rich units retain generic source locations and metadata without interpreting domain meaning.
- OCR is represented by an optional provider interface; no OCR engine is required by the core.
