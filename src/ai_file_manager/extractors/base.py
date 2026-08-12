from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ContentUnit:
    kind: str
    ordinal: int
    text: str
    location: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    units: tuple[ContentUnit, ...]
    metadata: dict[str, object] = field(default_factory=dict)


class Extractor(Protocol):
    def extract(self, path: Path) -> ExtractionResult: ...


class OcrProvider(Protocol):
    def extract_page(self, path: Path, page_number: int) -> str: ...


def normalize_text(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()
