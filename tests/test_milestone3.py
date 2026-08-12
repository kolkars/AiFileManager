from sqlalchemy import select

from ai_file_manager.config import Settings
from ai_file_manager.database import create_database
from ai_file_manager.extractors import default_registry
from ai_file_manager.ingestion import IngestionService
from ai_file_manager.models import DocumentExtraction, DocumentUnit
from ai_file_manager.repository import DocumentRepository


def test_domains_root_can_live_outside_repository(tmp_path, monkeypatch):
    external = tmp_path / "external" / "domains"
    monkeypatch.setenv("AI_FILE_MANAGER_DOMAINS_ROOT", str(external))
    settings = Settings.from_cwd(tmp_path / "repository")
    assert settings.knowledge_root == external.resolve()
    assert settings.database_path == (tmp_path / "repository" / ".ai-file-manager" / "index.db").resolve()


def test_markdown_units_preserve_kind_and_line_location(tmp_path):
    root = tmp_path / "domains"
    domain = root / "AnyFutureTopic"
    domain.mkdir(parents=True)
    (domain / "notes.md").write_text("# Heading\n\nParagraph", encoding="utf-8")
    _, sessions = create_database(tmp_path / "index.db")
    IngestionService(root, sessions, default_registry()).scan()
    with sessions() as session:
        units = list(session.scalars(select(DocumentUnit).order_by(DocumentUnit.ordinal)))
        metadata = session.scalar(select(DocumentExtraction))
    assert [(unit.kind, unit.location) for unit in units] == [("heading", "line:1"), ("paragraph", "line:3")]
    assert '"format": "md"' in metadata.metadata_json


def test_csv_units_are_source_addressable(tmp_path):
    path = tmp_path / "values.csv"
    path.write_text("name,value\nalpha,1", encoding="utf-8")
    result = default_registry().extract_rich(path)
    assert result.metadata["row_count"] == 2
    assert [unit.location for unit in result.units] == ["row:1", "row:2"]


def test_search_can_filter_by_generic_file_metadata(tmp_path):
    root = tmp_path / "domains"
    domain = root / "Topic"
    domain.mkdir(parents=True)
    (domain / "one.txt").write_text("shared phrase")
    (domain / "two.md").write_text("shared phrase")
    _, sessions = create_database(tmp_path / "index.db")
    IngestionService(root, sessions, default_registry()).scan()
    with sessions() as session:
        matches = DocumentRepository(session).search("Topic", "shared phrase", ".md")
    assert [document.filename for document in matches] == ["two.md"]
