from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = frozenset({".pdf", ".txt", ".md", ".csv", ".xlsx", ".docx"})


@dataclass(frozen=True)
class DiscoveredFile:
    domain: str
    path: Path
    relative_path: str


def discover_domains(knowledge_root: Path) -> list[str]:
    if not knowledge_root.is_dir():
        return []
    return sorted((p.name for p in knowledge_root.iterdir() if p.is_dir()), key=str.casefold)


def discover_files(knowledge_root: Path) -> list[DiscoveredFile]:
    found: list[DiscoveredFile] = []
    for domain in discover_domains(knowledge_root):
        domain_root = knowledge_root / domain
        for path in domain_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                found.append(DiscoveredFile(domain, path, path.relative_to(domain_root).as_posix()))
    return sorted(found, key=lambda item: (item.domain.casefold(), item.relative_path.casefold()))

