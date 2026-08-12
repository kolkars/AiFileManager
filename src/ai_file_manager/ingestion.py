from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from .discovery import discover_files
from .extractors import ExtractorRegistry
from .hashing import sha256_file
from .models import Document
from .repository import DocumentRepository


@dataclass
class ScanResult:
    new: int = 0
    changed: int = 0
    unchanged: int = 0
    deleted: int = 0
    errors: int = 0


class IngestionService:
    def __init__(self, knowledge_root: Path, sessions: sessionmaker, extractors: ExtractorRegistry) -> None:
        self.knowledge_root = knowledge_root
        self.sessions = sessions
        self.extractors = extractors

    def scan(self) -> ScanResult:
        result = ScanResult()
        with self.sessions.begin() as session:
            repository = DocumentRepository(session)
            remaining = repository.all_active_keys()
            for found in discover_files(self.knowledge_root):
                key = (found.domain, found.relative_path)
                existing = repository.by_key(*key)
                remaining.pop(key, None)
                checksum = sha256_file(found.path)
                if existing is not None and not existing.is_deleted and existing.checksum == checksum:
                    result.unchanged += 1
                    continue
                try:
                    extracted_text = self.extractors.extract(found.path)
                    extraction_error = None
                except Exception as error:  # one bad source must not abort the scan
                    extracted_text = ""
                    extraction_error = f"{type(error).__name__}: {error}"
                    result.errors += 1
                stat = found.path.stat()
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
                if was_existing:
                    result.changed += 1
                else:
                    result.new += 1
            for document in remaining.values():
                document.is_deleted = True
                repository.sync_fts(document)
                result.deleted += 1
        return result

