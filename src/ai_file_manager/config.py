from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    knowledge_root: Path
    database_path: Path

    @classmethod
    def from_cwd(cls, cwd: Path | None = None) -> "Settings":
        root = (cwd or Path.cwd()).resolve()
        return cls(root / "knowledge", root / ".ai-file-manager" / "index.db")

