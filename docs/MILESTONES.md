# AI File Manager Milestones

The invariant across all milestones is: **folder names define domains, files are authoritative sources, and core code contains no domain-specific knowledge.**

## M1 — Local ingestion and keyword search (complete)

Discover domains/files; extract PDF, TXT, Markdown, CSV, XLSX, and DOCX; calculate checksums; persist metadata/text in SQLite; reconcile new, changed, unchanged, and deleted files; provide an idempotent CLI and FTS5 search.

## M2 — Production-grade ingestion

Automate ingestion with filesystem watching and scheduled scans; add extraction retries, stable-file safeguards, scan history, immutable document versions, structured logs, and health reporting. Keep document-level failures isolated.

## M3 — Rich document processing

Preserve headings, pages, sheets, tables, and source locations; support optional OCR; normalize extraction; expand parser plugins and metadata filters.

## M4 — Semantic search

Add traceable chunking, replaceable embedding providers, a local vector index, incremental re-embedding, metadata filters, and hybrid keyword/vector ranking.

## M5 — Local model integration

Add a replaceable model interface, Ollama integration, grounded question answering, citations, context controls, and explicit insufficient-evidence behavior.

## M6 — Service and access layer

Expose shared core services through REST and MCP while retaining the CLI; add configuration and access controls without duplicating retrieval or ingestion logic.

## M7 — Local web application

Provide domain/file browsing, scan status, search, document inspection, error visibility, cited answers, source-file opening, and local configuration.

## M8 — Structured knowledge

Introduce generic entities, attributes, relationships, observations, and timelines with provenance; permit schemas outside the core package.

## M9 — Agents and workflows

Build research, comparison, requirements, and timeline agents from common tools; support optional skills, confirmations, and auditable source evidence.

## M10 — Security, extensibility, and operations

Add encryption/access options, backup/restore/migrations, metrics/auditing, stable plugin APIs, deployment guidance, and recovery/privacy/upgrade testing.
