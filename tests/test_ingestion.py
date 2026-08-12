from ai_file_manager.database import create_database
from ai_file_manager.extractors import default_registry
from ai_file_manager.ingestion import IngestionService
from ai_file_manager.repository import DocumentRepository


def make_service(tmp_path):
    knowledge = tmp_path / "knowledge"
    _, sessions = create_database(tmp_path / "index.db")
    return knowledge, sessions, IngestionService(knowledge, sessions, default_registry())


def test_scan_is_idempotent_and_detects_change_and_delete(tmp_path):
    root, sessions, service = make_service(tmp_path)
    domain = root / "CreatedAtRuntime"
    domain.mkdir(parents=True)
    source = domain / "notes.txt"
    source.write_text("alpha", encoding="utf-8")
    assert service.scan().new == 1
    second = service.scan()
    assert second.unchanged == 1
    source.write_text("beta", encoding="utf-8")
    assert service.scan().changed == 1
    with sessions() as session:
        assert DocumentRepository(session).search("CreatedAtRuntime", "beta")[0].text == "beta"
    source.unlink()
    assert service.scan().deleted == 1
    with sessions() as session:
        assert DocumentRepository(session).active("CreatedAtRuntime") == []


def test_extraction_error_does_not_stop_other_documents(tmp_path):
    root, sessions, service = make_service(tmp_path)
    domain = root / "Mixed"
    domain.mkdir(parents=True)
    (domain / "bad.pdf").write_bytes(b"not a pdf")
    (domain / "good.txt").write_text("searchable")
    result = service.scan()
    assert result.new == 2
    assert result.errors == 1
    with sessions() as session:
        docs = DocumentRepository(session).active("Mixed")
        assert len(docs) == 2
        assert next(doc for doc in docs if doc.filename == "bad.pdf").extraction_error


def test_search_treats_hyphenated_input_as_literal_text(tmp_path):
    root, sessions, service = make_service(tmp_path)
    domain = root / "Investments"
    domain.mkdir(parents=True)
    (domain / "notes.txt").write_text("local-first research", encoding="utf-8")
    service.scan()
    with sessions() as session:
        repository = DocumentRepository(session)
        assert [doc.filename for doc in repository.search("Investments", "local-first")] == ["notes.txt"]
        assert [doc.filename for doc in repository.search("Investments", '"local-first"')] == ["notes.txt"]
