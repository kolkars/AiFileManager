from ai_file_manager.hashing import sha256_file


def test_sha256(tmp_path):
    path = tmp_path / "source.txt"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

