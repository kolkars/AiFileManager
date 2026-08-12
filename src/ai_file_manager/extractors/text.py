import csv
from pathlib import Path


class PlainTextExtractor:
    def extract(self, path: Path) -> str:
        return path.read_text(encoding="utf-8-sig")


class CsvExtractor:
    def extract(self, path: Path) -> str:
        with path.open(encoding="utf-8-sig", newline="") as source:
            return "\n".join("\t".join(row) for row in csv.reader(source))

