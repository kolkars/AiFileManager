from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from .discovery import discover_files
from .extractors import ExtractorRegistry
from .extractors.base import ContentUnit
from .hashing import sha256_file
from .models import Document, ExtractionAttempt, ScanRun
from .repository import DocumentRepository


@dataclass
class ScanResult:
    new: int = 0
    changed: int = 0
    unchanged: int = 0
    deleted: int = 0
    errors: int = 0
    deferred: int = 0


class IngestionService:
    def __init__(self, knowledge_root: Path, sessions: sessionmaker, extractors: ExtractorRegistry, extraction_retries: int = 1) -> None:
        self.knowledge_root = knowledge_root
        self.sessions = sessions
        self.extractors = extractors
        self.extraction_retries = max(0, extraction_retries)

    def _extract(self, session, scan_run: ScanRun, found) -> tuple[str, tuple[ContentUnit, ...], dict[str, object], str | None]:
        for attempt_number in range(1, self.extraction_retries + 2):
            try:
                extracted = self.extractors.extract_rich(found.path)
                session.add(ExtractionAttempt(scan_run_id=scan_run.id, domain=found.domain, relative_path=found.relative_path, attempt_number=attempt_number, attempted_time=datetime.now(timezone.utc), succeeded=True))
                return extracted.text, extracted.units, extracted.metadata, None
            except Exception as error:  # retry locally, then isolate the failed source
                message = f"{type(error).__name__}: {error}"
                session.add(ExtractionAttempt(scan_run_id=scan_run.id, domain=found.domain, relative_path=found.relative_path, attempt_number=attempt_number, attempted_time=datetime.now(timezone.utc), succeeded=False, error=message))
        return "", (), {}, message

    def scan(self) -> ScanResult:
        result = ScanResult()
        with self.sessions.begin() as session:
            repository = DocumentRepository(session)
            scan_run = ScanRun(started_time=datetime.now(timezone.utc), status="running")
            session.add(scan_run)
            session.flush()
            remaining = repository.all_active_keys()
            for found in discover_files(self.knowledge_root):
                key = (found.domain, found.relative_path)
                existing = repository.by_key(*key)
                remaining.pop(key, None)
                try:
                    before = found.path.stat()
                    checksum = sha256_file(found.path)
                except OSError:
                    result.deferred += 1
                    continue
                if existing is not None and not existing.is_deleted and existing.checksum == checksum:
                    result.unchanged += 1
                    continue
                extracted_text, content_units, extraction_metadata, extraction_error = self._extract(session, scan_run, found)
                try:
                    after = found.path.stat()
                except OSError:
                    result.deferred += 1
                    continue
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    result.deferred += 1
                    continue
                if extraction_error is not None:
                    result.errors += 1
                stat = after
                now = datetime.now(timezone.utc)
                document = existing or Document(domain=found.domain, relative_path=found.relative_path)
                was_existing = existing is not None and not existing.is_deleted
                document.filename = found.path.name
                document.extension = found.path.suffix.lower()
                document.size = stat.st_size
                document.checksum = checksum
                document.modified_time = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                document.indexed_time = now
                document.text = extracted_text
                document.extraction_error = extraction_error
                document.is_deleted = False
                if existing is None:
                    session.add(document)
                repository.sync_fts(document)
                repository.replace_units(document, content_units)
                repository.replace_extraction_metadata(document, extraction_metadata)
                repository.record_version(document)
                if was_existing:
                    result.changed += 1
                else:
                    result.new += 1
            for document in remaining.values():
                document.is_deleted = True
                repository.sync_fts(document)
                result.deleted += 1
            scan_run.completed_time = datetime.now(timezone.utc)
            scan_run.status = "completed_with_errors" if result.errors or result.deferred else "completed"
            scan_run.new_count = result.new
            scan_run.changed_count = result.changed
            scan_run.unchanged_count = result.unchanged
            scan_run.deleted_count = result.deleted
            scan_run.error_count = result.errors
            scan_run.deferred_count = result.deferred
        return result
