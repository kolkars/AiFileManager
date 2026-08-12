from ai_file_manager.discovery import discover_domains, discover_files


def test_discovers_domains_and_supported_nested_files(tmp_path):
    root = tmp_path / "knowledge"
    (root / "AnyFutureTopic" / "nested").mkdir(parents=True)
    (root / "Investments").mkdir()
    (root / "AnyFutureTopic" / "nested" / "note.md").write_text("hello")
    (root / "AnyFutureTopic" / "ignored.bin").write_bytes(b"x")
    assert discover_domains(root) == ["AnyFutureTopic", "Investments"]
    files = discover_files(root)
    assert [(item.domain, item.relative_path) for item in files] == [("AnyFutureTopic", "nested/note.md")]

