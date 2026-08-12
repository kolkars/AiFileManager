from ai_file_manager.database import create_database
from ai_file_manager.extractors import default_registry
from ai_file_manager.ingestion import IngestionService
from ai_file_manager.models import DocumentVersion, ExtractionAttempt, ScanRun
from ai_file_manager.observability import health_report
from sqlalchemy import func, select


def test_scan_records_run_version_and_attempt(tmp_path):
    root = tmp_path / "knowledge"
    domain = root / "DynamicDomain"
    domain.mkdir(parents=True)
    (domain / "note.txt").write_text("version one")
    _, sessions = create_database(tmp_path / "index.db")
    service = IngestionService(root, sessions, default_registry())
    service.scan()
    (domain / "note.txt").write_text("version two")
    service.scan()
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(ScanRun)) == 2
        assert session.scalar(select(func.count()).select_from(DocumentVersion)) == 2
        assert session.scalar(select(func.count()).select_from(ExtractionAttempt)) == 2
    assert health_report(root, sessions)["status"] == "ok"


class AlwaysFailExtractor:
    def extract(self, path):
        raise RuntimeError("temporary failure")


def test_extraction_retries_are_audited(tmp_path):
    root = tmp_path / "knowledge"
    domain = root / "Domain"
    domain.mkdir(parents=True)
    (domain / "note.txt").write_text("content")
    _, sessions = create_database(tmp_path / "index.db")
    registry = default_registry()
    registry.register((".txt",), AlwaysFailExtractor())
    result = IngestionService(root, sessions, registry, extraction_retries=2).scan()
    assert result.errors == 1
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(ExtractionAttempt)) == 3
    assert health_report(root, sessions)["status"] == "degraded"
