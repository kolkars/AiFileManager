from pathlib import Path

from .base import ExtractionResult, Extractor
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

    def extract_rich(self, path: Path) -> ExtractionResult:
        try:
            extractor = self._extractors[path.suffix.lower()]
        except KeyError as error:
            raise ValueError(f"No extractor for {path.suffix}") from error
        return extractor.extract(path)

    def extract(self, path: Path) -> str:
        """Compatibility API returning normalized full document text."""
        return self.extract_rich(path).text


def default_registry() -> ExtractorRegistry:
    registry = ExtractorRegistry()
    registry.register((".txt", ".md"), PlainTextExtractor())
    registry.register((".csv",), CsvExtractor())
    registry.register((".pdf",), PdfExtractor())
    registry.register((".docx",), DocxExtractor())
    registry.register((".xlsx",), XlsxExtractor())
    return registry
