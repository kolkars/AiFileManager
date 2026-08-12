from pathlib import Path

from pypdf import PdfReader


class PdfExtractor:
    def extract(self, path: Path) -> str:
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)

