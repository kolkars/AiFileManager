# AI File Manager — Milestone 3

A local-first, domain-agnostic file index. On Windows, every first-level folder inside `D:\domains` is discovered as a domain at runtime. Adding a domain requires only creating its folder and adding supported files; no source-code or configuration change is needed.

Milestone 2 production ingestion and Milestone 3 rich extraction are available. See [Architecture](docs/ARCHITECTURE.md) and [Milestones](docs/MILESTONES.md).

Milestone 1 supports PDF, TXT, Markdown, CSV, XLSX, and DOCX. It stores metadata and extracted text locally in SQLite, detects new/changed/unchanged/deleted files, and provides SQLite FTS5 keyword search. It does not include embeddings, Ollama, MCP, or domain-specific behavior. Source files are opened read-only and are never modified.

## Windows 11 setup

1. Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/windows/) and enable **Add Python to PATH**.
2. Install `uv` in PowerShell:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. From this repository, install the project and development dependencies:

   ```powershell
   uv sync --dev
   ```

4. Create the external root and any domains, then add files:

   ```powershell
   New-Item -ItemType Directory -Force D:\domains\Investments
   Set-Content D:\domains\Investments\notes.txt "local-first research"
   ```

The source root can be overridden before running commands:

```powershell
$env:AI_FILE_MANAGER_DOMAINS_ROOT = "E:\my-domains"
```

The local index is written to `.ai-file-manager/index.db` in the repository and can be deleted and rebuilt from the original files at any time.

## CLI

Run commands from the repository root so `knowledge/` is resolved consistently:

```powershell
uv run ai-files scan
uv run ai-files domains
uv run ai-files files Investments
uv run ai-files show 1
uv run ai-files units 1
uv run ai-files search Investments "local-first"
uv run ai-files search Investments "local-first" --extension pdf
uv run ai-files health
uv run ai-files watch
uv run ai-files schedule --interval 3600
```

`scan` reports counts for `new`, `changed`, `unchanged`, `deleted`, and extraction `errors`. An extraction error is recorded on that document while the rest of the scan continues.

`watch` performs an initial scan and then debounces filesystem events. `schedule` runs scans at a fixed interval. Both stop cleanly with Ctrl+C. Files that change while being read are deferred to the next scan, and extraction failures are retried once by default (`--retries` controls this).

Scan summaries, extraction attempts, and content versions are retained in SQLite. `health` reports the latest scan and active extraction-error count as JSON. Operational scan completion logs are emitted as structured JSON.

Back up both `knowledge/` and `.ai-file-manager/index.db` together when a point-in-time operational snapshot is required. The database is derived state and can always be rebuilt with `scan`; the original files remain authoritative.

Search input is treated as literal text, so punctuation such as hyphens does not require SQLite FTS5 escaping.

## Tests

```powershell
uv run pytest
```

## Design

- `discovery.py` derives all domains from the filesystem.
- `extractors/` provides a replaceable registry and one extractor per format family.
- `ingestion.py` owns idempotent reconciliation but has no format or domain logic.
- `repository.py` isolates SQLAlchemy persistence and SQLite FTS5 synchronization.
- Deleted source records are retained as tombstones, excluded from listing/search, and revived with the same ID if the path returns.

## Migrating from the Milestone 1/2 source folder

If an earlier checkout contains `knowledge/`, migrate its domain folders before the first Milestone 3 scan:

```powershell
New-Item -ItemType Directory -Force D:\domains
Move-Item .\knowledge\* D:\domains\
```

Review the destination before removing the empty `knowledge` directory. The application never moves or modifies source files itself. To use another location, set `AI_FILE_MANAGER_DOMAINS_ROOT` before running the CLI.
