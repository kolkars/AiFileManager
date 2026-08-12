from pathlib import Path
from typing import Protocol


class Extractor(Protocol):
    def extract(self, path: Path) -> str: ...

