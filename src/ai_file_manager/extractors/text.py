import csv
from pathlib import Path

from .base import ContentUnit, ExtractionResult, normalize_text


class PlainTextExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        value = normalize_text(path.read_text(encoding="utf-8-sig"))
        units: list[ContentUnit] = []
        for number, line in enumerate(value.splitlines(), 1):
            if line.strip():
                kind = "heading" if path.suffix.lower() == ".md" and line.lstrip().startswith("#") else "paragraph"
                units.append(ContentUnit(kind, len(units), line, f"line:{number}", {"line": number}))
        return ExtractionResult(value, tuple(units), {"format": path.suffix.lower().lstrip(".")})


class CsvExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        with path.open(encoding="utf-8-sig", newline="") as source:
            rows = ["\t".join(row) for row in csv.reader(source)]
        units = tuple(ContentUnit("row", index, value, f"row:{index + 1}", {"row": index + 1}) for index, value in enumerate(rows))
        return ExtractionResult(normalize_text("\n".join(rows)), units, {"format": "csv", "row_count": len(rows)})
