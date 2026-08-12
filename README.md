# AI File Manager — Milestone 1

A local-first, domain-agnostic file index. Every first-level folder inside `knowledge/` is discovered as a domain at runtime. Adding a domain requires only creating its folder and adding supported files; no source-code or configuration change is needed.

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

4. Create any domains and add files:

   ```powershell
   New-Item -ItemType Directory -Force knowledge\Investments
   Set-Content knowledge\Investments\notes.txt "local-first research"
   ```

The local index is written to `.ai-file-manager/index.db` and can be deleted and rebuilt from the original files at any time.

## CLI

Run commands from the repository root so `knowledge/` is resolved consistently:

```powershell
uv run ai-files scan
uv run ai-files domains
uv run ai-files files Investments
uv run ai-files show 1
uv run ai-files search Investments "local-first"
```

`scan` reports counts for `new`, `changed`, `unchanged`, `deleted`, and extraction `errors`. An extraction error is recorded on that document while the rest of the scan continues.

FTS5 accepts SQLite FTS query syntax. For literal punctuation-heavy text, quote or simplify the query.

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

