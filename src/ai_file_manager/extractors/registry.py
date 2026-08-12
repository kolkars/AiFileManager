from pathlib import Path

from .base import Extractor
from .docx import DocxExtractor
from .pdf import PdfExtractor
from .text import CsvExtractor, PlainTextExtractor
from .xlsx import XlsxExtractor


class ExtractorRegistry:
    def __init__(self) -> None:
        self._extractors: dict[str, Extractor] = {}

    def register(self, extensions: tuple[str, ...], extractor: Extractor) -> None:
        for extension in extensions:
            self._extractors[extension.lower()] = extractor

    def extract(self, path: Path) -> str:
        try:
            extractor = self._extractors[path.suffix.lower()]
        except KeyError as error:
            raise ValueError(f"No extractor for {path.suffix}") from error
        return extractor.extract(path)


def default_registry() -> ExtractorRegistry:
    registry = ExtractorRegistry()
    registry.register((".txt", ".md"), PlainTextExtractor())
    registry.register((".csv",), CsvExtractor())
    registry.register((".pdf",), PdfExtractor())
    registry.register((".docx",), DocxExtractor())
    registry.register((".xlsx",), XlsxExtractor())
    return registry

