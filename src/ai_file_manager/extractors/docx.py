from pathlib import Path

from docx import Document


class DocxExtractor:
    def extract(self, path: Path) -> str:
        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

