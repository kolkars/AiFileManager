from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    knowledge_root: Path
    database_path: Path

    @classmethod
    def from_cwd(cls, cwd: Path | None = None) -> "Settings":
        root = (cwd or Path.cwd()).resolve()
        configured = os.environ.get("AI_FILE_MANAGER_DOMAINS_ROOT")
        if configured:
            domains_root = Path(configured).expanduser().resolve()
        elif os.name == "nt":
            domains_root = Path("D:/domains")
        else:
            domains_root = root / "domains"
        return cls(domains_root, root / ".ai-file-manager" / "index.db")
