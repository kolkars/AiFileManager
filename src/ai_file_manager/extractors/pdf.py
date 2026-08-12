from pathlib import Path

from pypdf import PdfReader

from .base import ContentUnit, ExtractionResult, OcrProvider, normalize_text


class PdfExtractor:
    def __init__(self, ocr: OcrProvider | None = None) -> None:
        self.ocr = ocr

    def extract(self, path: Path) -> ExtractionResult:
        pages: list[str] = []
        units: list[ContentUnit] = []
        for page_number, page in enumerate(PdfReader(path).pages, 1):
            value = normalize_text(page.extract_text() or "")
            used_ocr = False
            if not value and self.ocr is not None:
                value = normalize_text(self.ocr.extract_page(path, page_number))
                used_ocr = True
            pages.append(value)
            units.append(ContentUnit("page", page_number - 1, value, f"page:{page_number}", {"page": page_number, "ocr": used_ocr}))
        return ExtractionResult(normalize_text("\n\n".join(pages)), tuple(units), {"format": "pdf", "page_count": len(pages)})
